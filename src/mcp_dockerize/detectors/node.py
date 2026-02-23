"""Node.js MCP server detector."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List

from mcp_dockerize.detectors.base import AbstractDetector, ServerMetadata

# MCP SDK package names that qualify a project as an MCP server
_MCP_PACKAGES = frozenset(
    {
        "@modelcontextprotocol/sdk",
        "@modelcontextprotocol/server",
    }
)

# Regex to extract bare process.env variable names from JS/TS source
_ENV_VAR_PATTERN = re.compile(r"process\.env\.([A-Z_][A-Z0-9_]*)")

# Version-prefix characters to strip from engines.node values
_VERSION_PREFIX = re.compile(r"[>=<^~\s]+")


def _strip_version_prefix(raw: str) -> str:
    """Return the numeric portion of a Node version constraint string.

    Examples
    --------
    >>> _strip_version_prefix(">=20")
    '20'
    >>> _strip_version_prefix("^18.12.0")
    '18.12.0'
    >>> _strip_version_prefix("20")
    '20'
    """
    return _VERSION_PREFIX.sub("", raw).split(" ")[0]


def _scan_env_vars(file_path: Path) -> List[str]:
    """Extract unique process.env variable names from *file_path*.

    Returns an empty list when the file does not exist or cannot be read.
    """
    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    matches = _ENV_VAR_PATTERN.findall(source)
    # Preserve first-seen order while deduplicating
    seen: set[str] = set()
    result: List[str] = []
    for name in matches:
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result


class NodeDetector(AbstractDetector):
    """Detect and analyse Node.js MCP servers.

    A directory is considered a Node.js MCP server when it contains a
    ``package.json`` file that lists ``@modelcontextprotocol/sdk`` or
    ``@modelcontextprotocol/server`` in either ``dependencies`` or
    ``devDependencies``.

    Example
    -------
    >>> from pathlib import Path
    >>> detector = NodeDetector()
    >>> detector.can_detect(Path("tests/fixtures/sample-node-server"))
    True
    """

    # ------------------------------------------------------------------ #
    # AbstractDetector interface                                           #
    # ------------------------------------------------------------------ #

    def can_detect(self, path: Path) -> bool:
        """Return ``True`` when *path* looks like a Node.js MCP server.

        Conditions (both must hold):

        1. ``package.json`` exists inside *path*.
        2. ``dependencies`` or ``devDependencies`` contains at least one
           known MCP SDK package name.
        """
        pkg_path = path / "package.json"
        if not pkg_path.exists():
            return False

        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return False

        all_deps: set[str] = set()
        all_deps.update(pkg.get("dependencies", {}).keys())
        all_deps.update(pkg.get("devDependencies", {}).keys())

        return bool(all_deps & _MCP_PACKAGES)

    def detect(self, path: Path) -> ServerMetadata:
        """Analyse the Node.js MCP server at *path* and return its metadata.

        Parameters
        ----------
        path:
            Directory containing the server's ``package.json``.

        Returns
        -------
        ServerMetadata
            Populated metadata object describing the server.

        Raises
        ------
        ValueError
            When ``package.json`` is present but contains invalid JSON.
        """
        pkg_path = path / "package.json"

        # --- Parse package.json ---------------------------------------- #
        try:
            raw = pkg_path.read_text(encoding="utf-8")
            pkg = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid package.json at {path}") from exc

        # --- name ------------------------------------------------------- #
        name: str = pkg.get("name") or path.name

        # --- runtime_version -------------------------------------------- #
        runtime_version = "20"  # default
        engines_node: str | None = (
            pkg.get("engines", {}).get("node") if isinstance(pkg.get("engines"), dict) else None
        )
        if engines_node:
            runtime_version = _strip_version_prefix(engines_node) or "20"
        else:
            # Fall back to .nvmrc or .node-version files
            for version_file in (".nvmrc", ".node-version"):
                vf_path = path / version_file
                if vf_path.exists():
                    try:
                        content = vf_path.read_text(encoding="utf-8").strip()
                        stripped = _strip_version_prefix(content)
                        if stripped:
                            runtime_version = stripped
                            break
                    except OSError:
                        continue

        # --- entry_point ------------------------------------------------ #
        entry_point = "index.js"  # default
        main: str | None = pkg.get("main")
        if main:
            entry_point = main
        else:
            bin_field = pkg.get("bin")
            if isinstance(bin_field, str):
                entry_point = bin_field
            elif isinstance(bin_field, dict) and bin_field:
                # Take the first value from the bin map
                entry_point = next(iter(bin_field.values()))

        # --- dependencies ----------------------------------------------- #
        deps_dict: dict = pkg.get("dependencies", {})
        dependencies: List[str] = list(deps_dict.keys()) if isinstance(deps_dict, dict) else []

        # --- has_package_lock ------------------------------------------- #
        has_package_lock: bool = (path / "package-lock.json").exists()

        # --- env_vars (scan entry_point file) --------------------------- #
        entry_point_path = path / entry_point
        env_vars: List[str] = _scan_env_vars(entry_point_path)

        return ServerMetadata(
            name=name,
            runtime="node_npm",
            runtime_version=runtime_version,
            entry_point=entry_point,
            package_manager="npm",
            dependencies=dependencies,
            has_package_lock=has_package_lock,
            env_vars=env_vars,
            data_volumes=[],
            deployment_pattern="volume_mounted",
        )
