"""Python FastMCP server detector."""

import re
from pathlib import Path
from typing import Dict, List, Union

import toml

from mcp_dockerize.detectors.base import AbstractDetector, ServerMetadata  # re-exported for backward compat

# Backward-compatible re-export so existing callers that do
#   from mcp_dockerize.detectors.python import ServerMetadata
# continue to resolve without modification.
__all__ = ["PythonDetector", "ServerMetadata"]


# Runtime string mapping from old "python-*" style to new "python_*" style.
_RUNTIME_MAP: Dict[str, str] = {
    "python-uv": "python_uv",
    "python-direct": "python_direct",
    "python-fastmcp": "python_direct",
}


class PythonDetector(AbstractDetector):
    """Detect and analyse Python FastMCP servers.

    Extends ``AbstractDetector`` and returns ``ServerMetadata`` from
    ``detectors.base``.  All existing detection logic is preserved:
    Python version extraction, server-type classification, ``.env``
    parsing, volume detection and security checks.

    Backward Compatibility
    ----------------------
    Both ``can_detect`` and ``detect`` accept ``str | Path`` so existing
    callers (e.g. ``cli.py``) that pass a plain string continue to work
    without modification.

    The ``ServerMetadata`` returned by ``detect`` populates *both* the
    new canonical fields (``runtime``, ``runtime_version``, ``env_vars``
    as a list, ``data_volumes`` as a list) *and* the legacy optional
    fields kept in ``base.ServerMetadata`` for backward compat
    (``server_type``, ``python_version``, ``env_file``,
    ``volume_mounts``, ``warnings``).
    """

    # ------------------------------------------------------------------
    # AbstractDetector interface
    # ------------------------------------------------------------------

    def can_detect(self, path: Union[str, Path]) -> bool:
        """Return True if *path* contains a ``pyproject.toml`` file."""
        return (Path(path) / "pyproject.toml").exists()

    def detect(self, path: Union[str, Path]) -> ServerMetadata:
        """Detect a Python MCP server and return its metadata.

        Args:
            path: Directory containing the server (``str`` or ``Path``).

        Returns:
            A fully populated ``ServerMetadata`` instance.

        Raises:
            ValueError: if ``pyproject.toml`` is missing or the entry
                point cannot be determined.
        """
        path = Path(path)
        pyproject_path = path / "pyproject.toml"

        if not pyproject_path.exists():
            raise ValueError(f"No pyproject.toml found at {path}")

        # --- Parse pyproject.toml ----------------------------------------
        pyproject = toml.load(pyproject_path)
        project = pyproject.get("project", {})

        name: str = project.get("name", path.name)
        dependencies: List[str] = project.get("dependencies", [])

        # --- Core detection ----------------------------------------------
        python_version = self._extract_python_version(
            project.get("requires-python", ">=3.10")
        )
        old_server_type, entry_point = self._detect_server_type(path, pyproject)

        # Map old "python-*" tag to canonical "python_*" runtime slug.
        runtime = _RUNTIME_MAP.get(old_server_type, "python_direct")
        package_manager = "uv" if runtime == "python_uv" else "pip"

        # --- Build canonical metadata ------------------------------------
        metadata = ServerMetadata(
            name=name,
            runtime=runtime,
            runtime_version=python_version,
            entry_point=entry_point,
            package_manager=package_manager,
            dependencies=dependencies,
            # Backward-compat optional fields
            server_type=old_server_type,
            python_version=python_version,
        )

        # --- .env file ---------------------------------------------------
        env_file_path = path / ".env"
        env_vars_dict: Dict[str, str] = {}
        if env_file_path.exists():
            metadata.env_file = str(env_file_path)
            env_vars_dict = self._parse_env_file(env_file_path)

        # Canonical field: list of env var *keys*.
        metadata.env_vars = list(env_vars_dict.keys())

        # --- Volume detection --------------------------------------------
        volume_mounts_dict = self._detect_volumes(path, env_vars_dict)

        # Canonical field: list of source paths (keys of the dict).
        metadata.data_volumes = list(volume_mounts_dict.keys())
        # Backward-compat field: full source→dest mapping.
        metadata.volume_mounts = volume_mounts_dict

        # --- Security checks ---------------------------------------------
        metadata.warnings = self._security_checks(path, env_vars_dict)

        return metadata

    # ------------------------------------------------------------------
    # Private helpers (unchanged logic, minor type annotation updates)
    # ------------------------------------------------------------------

    def _extract_python_version(self, requires_python: str) -> str:
        """Extract the minimum Python version from a *requires-python* string.

        Examples::

            ">=3.10"          → "3.10"
            ">=3.10,<3.13"   → "3.10"
            "^3.11"           → "3.11"
        """
        match = re.search(r"(\d+\.\d+)", requires_python)
        if match:
            return match.group(1)
        return "3.11"  # Sensible default

    def _detect_server_type(self, path: Path, pyproject: dict) -> tuple:
        """Determine the old-style server type tag and the entry point.

        Returns:
            A 2-tuple of ``(server_type_str, entry_point_str)`` where
            *server_type_str* is one of ``"python-uv"``,
            ``"python-direct"``, or ``"python-fastmcp"``.

        Raises:
            ValueError: if the entry point cannot be determined.
        """
        project = pyproject.get("project", {})
        scripts: Dict[str, str] = project.get("scripts", {})

        # Console script → installable via uv/pip.
        if scripts:
            script_name = list(scripts.keys())[0]
            return "python-uv", script_name

        # Direct execution via main.py.
        if (path / "main.py").exists():
            return "python-direct", "main.py"

        # src/ layout — look for server.py or __main__.py.
        src_dir = path / "src"
        if src_dir.exists():
            for pattern in ["**/server.py", "**/__main__.py"]:
                matches = list(src_dir.glob(pattern))
                if matches:
                    rel_path = matches[0].relative_to(path)
                    return "python-fastmcp", str(rel_path)

        raise ValueError(f"Could not determine entry point for {path}")

    def _parse_env_file(self, env_file: Path) -> Dict[str, str]:
        """Parse a ``.env`` file and return a ``{key: value}`` mapping.

        Lines beginning with ``#`` and empty lines are ignored.  Surrounding
        quotes are stripped from values.
        """
        env_vars: Dict[str, str] = {}
        try:
            with open(env_file) as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value
        except Exception:
            pass
        return env_vars

    def _detect_volumes(
        self, path: Path, env_vars: Dict[str, str]
    ) -> Dict[str, str]:
        """Detect required volume mounts from env vars and server source files.

        Returns:
            A ``{source_path: container_path}`` mapping.  System paths
            (``/usr``, ``/etc``, etc.) are never included.
        """
        volumes: Dict[str, str] = {}

        # System paths to exclude — never mount these inside a container.
        exclude_paths = {
            "/usr", "/etc", "/var", "/sys", "/proc", "/dev", "/tmp",
            "/opt", "/root", "/lib", "/lib64", "/bin", "/sbin",
            "/run", "/boot", "/home",
        }

        for key, value in env_vars.items():
            # SSH keys, certificates, PEM files.
            if any(ext in value.lower() for ext in [".pem", ".key", ".cert", ".crt"]):
                if Path(value).exists():
                    source_dir = str(Path(value).parent)
                    volumes[source_dir] = "/keys"

            # Database / storage directories.
            if any(db in value.lower() for db in ["database", "storage", ".db"]):
                if Path(value).exists() and Path(value).is_dir():
                    volumes[value] = "/data"

        # Scan ONLY the main server files for hardcoded absolute paths
        # (installed package trees are intentionally excluded).
        main_files = [
            path / "main.py",
            path / "server.py",
            path / "src" / "server.py",
        ]

        for py_file in main_files:
            if not py_file.exists():
                continue
            try:
                content = py_file.read_text()
                for p in re.findall(r'["\'](/[^"\']+)["\']', content):
                    if any(p.startswith(excl) for excl in exclude_paths):
                        continue
                    if any(
                        indicator in p
                        for indicator in ["/media/", "/mnt/", "Drive", "Storage"]
                    ):
                        if Path(p).exists() and Path(p).is_dir():
                            volumes[p] = f"/data/{Path(p).name}"
            except Exception:
                continue

        return volumes

    def _security_checks(
        self, path: Path, env_vars: Dict[str, str]
    ) -> List[str]:
        """Perform security checks and return a list of human-readable warnings.

        Checks performed:

        * Hardcoded credentials (password / secret / api_key / token)
          in the main server source files.
        * Overly permissive SSH key file permissions.
        """
        warnings: List[str] = []

        main_files = [
            path / "main.py",
            path / "server.py",
            path / "src" / "server.py",
        ]

        for py_file in main_files:
            if not py_file.exists():
                continue
            try:
                content = py_file.read_text()
                if re.search(
                    r'(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']',
                    content,
                    re.I,
                ):
                    warnings.append(
                        f"Potential hardcoded credential in {py_file.name}. "
                        "Use environment variables instead."
                    )
            except Exception:
                continue

        for key, value in env_vars.items():
            if ".pem" in value.lower() or "private_key" in key.lower():
                p = Path(value)
                if p.exists():
                    if p.stat().st_mode & 0o077:
                        warnings.append(
                            f"SSH key {value} has loose permissions. "
                            f"Run: chmod 600 {value}"
                        )

        return warnings
