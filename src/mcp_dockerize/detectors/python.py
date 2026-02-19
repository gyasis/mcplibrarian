"""Python FastMCP server detector."""

import os
import re
import toml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ServerMetadata:
    """Metadata about detected MCP server."""
    name: str
    server_type: str  # "python-uv", "python-direct", "python-fastmcp"
    python_version: str
    entry_point: str
    dependencies: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    env_file: Optional[str] = None
    volume_mounts: Dict[str, str] = field(default_factory=dict)  # source:dest
    warnings: List[str] = field(default_factory=list)


class PythonDetector:
    """Detect and analyze Python FastMCP servers."""

    def can_detect(self, path: str) -> bool:
        """Check if path contains a Python MCP server."""
        pyproject = Path(path) / "pyproject.toml"
        return pyproject.exists()

    def detect(self, path: str) -> ServerMetadata:
        """Detect Python MCP server and extract metadata."""
        path = Path(path)
        pyproject_path = path / "pyproject.toml"

        if not pyproject_path.exists():
            raise ValueError(f"No pyproject.toml found at {path}")

        # Parse pyproject.toml
        pyproject = toml.load(pyproject_path)
        project = pyproject.get("project", {})

        # Extract basic info
        name = project.get("name", path.name)
        dependencies = project.get("dependencies", [])

        # Detect Python version
        python_version = self._extract_python_version(project.get("requires-python", ">=3.10"))

        # Detect server type and entry point
        server_type, entry_point = self._detect_server_type(path, pyproject)

        # Create metadata
        metadata = ServerMetadata(
            name=name,
            server_type=server_type,
            python_version=python_version,
            entry_point=entry_point,
            dependencies=dependencies
        )

        # Find .env file
        env_file = path / ".env"
        if env_file.exists():
            metadata.env_file = str(env_file)
            metadata.env_vars = self._parse_env_file(env_file)

        # Detect volume requirements
        metadata.volume_mounts = self._detect_volumes(path, metadata.env_vars)

        # Security checks
        metadata.warnings = self._security_checks(path, metadata.env_vars)

        return metadata

    def _extract_python_version(self, requires_python: str) -> str:
        """Extract Python version from requires-python string."""
        # Examples: ">=3.10", ">=3.10,<3.13", "^3.11"
        match = re.search(r"(\d+\.\d+)", requires_python)
        if match:
            return match.group(1)
        return "3.11"  # Default

    def _detect_server_type(self, path: Path, pyproject: dict) -> tuple:
        """Detect server type (uv, direct, fastmcp) and entry point."""
        project = pyproject.get("project", {})
        scripts = project.get("scripts", {})

        # Check for console script entry point (uv/pip installable)
        if scripts:
            script_name = list(scripts.keys())[0]
            entry_command = script_name
            return "python-uv", entry_command

        # Check for main.py (direct execution)
        main_py = path / "main.py"
        if main_py.exists():
            return "python-direct", "main.py"

        # Check for src/ structure
        src_dir = path / "src"
        if src_dir.exists():
            # Look for server.py or __main__.py
            for pattern in ["**/server.py", "**/__main__.py"]:
                matches = list(src_dir.glob(pattern))
                if matches:
                    rel_path = matches[0].relative_to(path)
                    return "python-fastmcp", str(rel_path)

        raise ValueError(f"Could not determine entry point for {path}")

    def _parse_env_file(self, env_file: Path) -> Dict[str, str]:
        """Parse .env file and extract variables."""
        env_vars = {}

        try:
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        # Remove quotes
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value
        except Exception:
            pass

        return env_vars

    def _detect_volumes(self, path: Path, env_vars: Dict[str, str]) -> Dict[str, str]:
        """Detect required volume mounts from env vars and code."""
        volumes = {}

        # System paths to exclude (never mount these)
        exclude_paths = {
            "/usr", "/etc", "/var", "/sys", "/proc", "/dev", "/tmp",
            "/opt", "/root", "/lib", "/lib64", "/bin", "/sbin",
            "/run", "/boot", "/home"
        }

        # Check for file paths in env vars
        for key, value in env_vars.items():
            # SSH keys, certificates
            if any(ext in value.lower() for ext in [".pem", ".key", ".cert", ".crt"]):
                if Path(value).exists():
                    source_dir = str(Path(value).parent)
                    volumes[source_dir] = "/keys"

            # Database paths (DeepLake, SQLite, etc.)
            if any(db in value.lower() for db in ["database", "storage", ".db"]):
                if Path(value).exists() and Path(value).is_dir():
                    volumes[value] = "/data"

        # Scan ONLY main server files for hardcoded paths (not installed packages)
        main_files = [
            path / "main.py",
            path / "server.py",
            path / "src" / "server.py"
        ]

        for py_file in main_files:
            if not py_file.exists():
                continue

            try:
                content = py_file.read_text()
                # Look for absolute paths in strings
                paths = re.findall(r'["\'](/[^"\']+)["\']', content)
                for p in paths:
                    # Skip if it's a system path
                    if any(p.startswith(excluded) for excluded in exclude_paths):
                        continue

                    # Only include paths that look like user data
                    if any(indicator in p for indicator in ["/media/", "/mnt/", "Drive", "Storage"]):
                        if Path(p).exists() and Path(p).is_dir():
                            volumes[p] = f"/data/{Path(p).name}"
            except Exception:
                continue

        return volumes

    def _security_checks(self, path: Path, env_vars: Dict[str, str]) -> List[str]:
        """Perform security checks and return warnings."""
        warnings = []

        # Check for hardcoded credentials ONLY in main server files
        main_files = [
            path / "main.py",
            path / "server.py",
            path / "src" / "server.py"
        ]

        for py_file in main_files:
            if not py_file.exists():
                continue

            try:
                content = py_file.read_text()
                # Common credential patterns
                if re.search(r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']', content, re.I):
                    warnings.append(
                        f"Potential hardcoded credential in {py_file.name}. "
                        "Use environment variables instead."
                    )
            except Exception:
                continue

        # Check for SSH key permissions
        for key, value in env_vars.items():
            if ".pem" in value.lower() or "private_key" in key.lower():
                if Path(value).exists():
                    stat = Path(value).stat()
                    if stat.st_mode & 0o077:
                        warnings.append(
                            f"SSH key {value} has loose permissions. "
                            f"Run: chmod 600 {value}"
                        )

        return warnings
