"""SmartScan orchestrator for MCP server analysis.

Provides:
- ``SmartScan(path).run() -> SmartScanResult``: full analysis of a single server
- ``discover_servers(scan_dir, max_depth) -> list[Path]``: batch discovery
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from mcp_dockerize.detectors.base import AbstractDetector, ServerMetadata
from mcp_dockerize.detectors.node import NodeDetector
from mcp_dockerize.detectors.python import PythonDetector
from mcp_dockerize.smart_scan.issues import (
    Issue,
    IssueType,
    Severity,
    SmartScanResult,
)

# Directories to skip during recursive discovery.
_SKIP_DIRS = frozenset(
    {
        "node_modules",
        ".venv",
        "__pycache__",
        ".git",
        "dist",
        "build",
    }
)

# Registered detectors in priority order.
# PythonDetector first so a directory containing both pyproject.toml and
# package.json is consistently classified as Python.
_DETECTORS: List[AbstractDetector] = [
    PythonDetector(),
    NodeDetector(),
]


def _parse_env_file(env_file: Path) -> List[str]:
    """Return a list of env-var keys found in *env_file*.

    Lines that are empty, start with ``#``, or lack an ``=`` sign are skipped.
    Surrounding quotes are stripped from values (but only keys are returned).
    """
    keys: List[str] = []
    try:
        with env_file.open(encoding="utf-8", errors="replace") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key = line.split("=", 1)[0].strip()
                if key:
                    keys.append(key)
    except OSError:
        pass
    return keys


def _build_issues(path: Path, metadata: ServerMetadata) -> List[Issue]:
    """Compile the ``Issue`` list for *metadata* at *path*.

    Checks performed:
    1. Path has spaces in any component.
    2. Path (or any component) is a symlink.
    3. Missing package-lock.json for Node.js servers.
    """
    issues: List[Issue] = []

    # --- Path-has-spaces check -------------------------------------------
    # Inspect the string representation of every component in the resolved
    # path.  We check each part individually so that a space buried deep in
    # the hierarchy is still caught.
    resolved: Path = path.resolve()
    for part in resolved.parts:
        if " " in part:
            issues.append(
                Issue(
                    issue_type=IssueType.path_has_spaces,
                    severity=Severity.warning,
                    description=(
                        f"Directory path component '{part}' contains spaces, "
                        "which can break Docker volume mounts and shell scripts."
                    ),
                    auto_fixable=True,
                    fix_instruction="Rename directory to remove spaces",
                    affected_path=str(resolved),
                )
            )
            break  # one issue per scan is enough

    # --- Symlink check (informational, folded into path_has_spaces scope) --
    # If any component of the path is a symlink we note it as a warning
    # because Docker bind-mounts of symlinked paths can behave unexpectedly.
    try:
        current = Path(path.parts[0])
        for part in path.parts[1:]:
            current = current / part
            if current.is_symlink():
                issues.append(
                    Issue(
                        issue_type=IssueType.path_has_spaces,
                        severity=Severity.warning,
                        description=(
                            f"Path component '{current}' is a symbolic link. "
                            "Docker volume mounts may not follow symlinks as expected."
                        ),
                        auto_fixable=True,
                        fix_instruction="Rename directory to remove spaces",
                        affected_path=str(current),
                    )
                )
                break
    except (OSError, IndexError):
        pass

    # --- Missing package-lock.json ---------------------------------------
    if not metadata.has_package_lock:
        issues.append(
            Issue(
                issue_type=IssueType.missing_package_lock,
                severity=Severity.warning,
                description=(
                    "No package-lock.json found.  Reproducible builds require "
                    "a lock file so that npm ci can install exact dependency versions."
                ),
                auto_fixable=True,
                fix_instruction="Run npm install --package-lock-only",
                affected_path=str(path),
            )
        )

    return issues


class SmartScan:
    """Orchestrate full Smart-Scan analysis for a single MCP server directory.

    Parameters
    ----------
    path:
        Path to the server directory.  Accepts ``str`` or ``Path``.
    detectors:
        Optional override of the registered detector list.  Defaults to
        ``[PythonDetector(), NodeDetector()]``.

    Examples
    --------
    >>> result = SmartScan("/path/to/my-server").run()
    >>> print(result.runtime, result.issues)
    """

    def __init__(
        self,
        path: str | Path,
        detectors: Optional[List[AbstractDetector]] = None,
    ) -> None:
        self.path: Path = Path(path)
        self._detectors: List[AbstractDetector] = (
            detectors if detectors is not None else list(_DETECTORS)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> SmartScanResult:
        """Analyse the server at ``self.path`` and return a ``SmartScanResult``.

        Steps
        -----
        1. Try each registered detector via ``can_detect()`` / ``detect()``.
        2. Detect env vars from the ``.env`` file when present.
        3. Collect data volumes from ``metadata.data_volumes``.
        4. Validate the path for spaces / symlinks.
        5. Check for a missing package-lock file.
        6. Compile the ``Issue[]`` list.

        Returns
        -------
        SmartScanResult
            Fully populated result.  If no detector recognises the server the
            ``runtime`` field is set to ``"unknown"`` and an
            ``unknown_runtime`` blocking issue is included.

        Raises
        ------
        FileNotFoundError
            If ``self.path`` does not exist on disk.
        """
        if not self.path.exists():
            raise FileNotFoundError(
                f"SmartScan: path does not exist — {self.path}"
            )

        metadata: Optional[ServerMetadata] = self._detect()

        if metadata is None:
            return self._unknown_runtime_result()

        # --- Merge env-var keys: detector + .env file --------------------
        env_vars: List[str] = list(metadata.env_vars)  # already a list of keys
        dot_env = self.path / ".env"
        if dot_env.exists():
            file_keys = _parse_env_file(dot_env)
            # Preserve order; deduplicate without sorting.
            existing = set(env_vars)
            for key in file_keys:
                if key not in existing:
                    env_vars.append(key)
                    existing.add(key)

        # --- Data volumes ------------------------------------------------
        data_volumes: List[str] = list(metadata.data_volumes)

        # --- Compile issues ----------------------------------------------
        issues: List[Issue] = _build_issues(self.path, metadata)

        return SmartScanResult(
            server_path=str(self.path.resolve()),
            runtime=metadata.runtime,
            runtime_version=metadata.runtime_version,
            entry_point=metadata.entry_point,
            package_manager=metadata.package_manager,
            env_vars=env_vars,
            data_volumes=data_volumes,
            issues=issues,
            deployment_pattern=metadata.deployment_pattern,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect(self) -> Optional[ServerMetadata]:
        """Run each detector in order; return the first match or ``None``."""
        for detector in self._detectors:
            try:
                if detector.can_detect(self.path):
                    return detector.detect(self.path)
            except Exception:
                # A broken detector must not abort the whole scan.
                continue
        return None

    def _unknown_runtime_result(self) -> SmartScanResult:
        """Return a result representing a completely unrecognised server."""
        unknown_issue = Issue(
            issue_type=IssueType.unknown_runtime,
            severity=Severity.blocking,
            description=(
                "No recognised runtime detected.  The directory contains "
                "neither a pyproject.toml (Python) nor a package.json with "
                "an @modelcontextprotocol dependency (Node.js)."
            ),
            auto_fixable=False,
            fix_instruction="",
            affected_path=str(self.path),
        )
        return SmartScanResult(
            server_path=str(self.path.resolve()),
            runtime="unknown",
            runtime_version="",
            entry_point="",
            package_manager="",
            env_vars=[],
            data_volumes=[],
            issues=[unknown_issue],
            deployment_pattern="volume_mounted",
        )


# ---------------------------------------------------------------------------
# Batch discovery
# ---------------------------------------------------------------------------


def discover_servers(
    scan_dir: str | Path,
    max_depth: int = 2,
    detectors: Optional[List[AbstractDetector]] = None,
) -> List[Path]:
    """Walk *scan_dir* and return directories that look like MCP servers.

    The walk skips directories whose *name* is in the skip set
    (``node_modules``, ``.venv``, ``__pycache__``, ``.git``, ``dist``,
    ``build``) and stops recursing beyond *max_depth* levels.

    Parameters
    ----------
    scan_dir:
        Root directory to search.
    max_depth:
        Maximum number of directory levels below *scan_dir* to traverse.
        ``0`` means only *scan_dir* itself; ``2`` (default) means two levels
        of sub-directories.
    detectors:
        Optional override of the registered detector list.  Defaults to
        ``[PythonDetector(), NodeDetector()]``.

    Returns
    -------
    list[Path]
        Absolute paths to recognised server directories, in filesystem order.

    Examples
    --------
    >>> servers = discover_servers(Path("tests/fixtures"), max_depth=1)
    >>> [p.name for p in servers]
    ['sample-node-server', 'sample-python-server']
    """
    root = Path(scan_dir).resolve()
    active_detectors: List[AbstractDetector] = (
        detectors if detectors is not None else list(_DETECTORS)
    )

    found: List[Path] = []
    _walk(root, root, max_depth=max_depth, detectors=active_detectors, found=found)
    return found


def _walk(
    current: Path,
    root: Path,
    max_depth: int,
    detectors: List[AbstractDetector],
    found: List[Path],
) -> None:
    """Recursive depth-limited directory walk used by ``discover_servers``."""
    depth = len(current.relative_to(root).parts)
    if depth > max_depth:
        return

    # Check whether *current* is itself a server directory.
    for detector in detectors:
        try:
            if detector.can_detect(current):
                found.append(current)
                # Do not descend into a recognised server — its sub-directories
                # are part of the server, not independent servers.
                return
        except Exception:
            continue

    # Recurse into non-skipped sub-directories.
    try:
        entries = sorted(current.iterdir())
    except PermissionError:
        return

    for entry in entries:
        if not entry.is_dir():
            continue
        if entry.name in _SKIP_DIRS:
            continue
        _walk(
            current=entry,
            root=root,
            max_depth=max_depth,
            detectors=detectors,
            found=found,
        )
