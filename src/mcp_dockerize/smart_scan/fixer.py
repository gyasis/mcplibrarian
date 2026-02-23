"""Auto-fix strategies for issues detected by SmartScan."""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List

from mcp_dockerize.smart_scan.issues import Fix, IssueType, SmartScanResult

logger = logging.getLogger(__name__)

_DEFAULT_NODE_VERSION = "20"
_SUBPROCESS_TIMEOUT = 120


@dataclass
class AutoFixer:
    """Apply automated fixes to issues found in a SmartScanResult.

    Only issues marked ``auto_fixable=True`` are processed. Issues that
    cannot be fixed automatically are silently skipped so the caller
    receives a list containing only the fixes that were attempted.

    Args:
        result: The ``SmartScanResult`` produced by ``SmartScan.run()``.

    Example::

        from mcp_dockerize.smart_scan.scanner import SmartScan
        from mcp_dockerize.smart_scan.fixer import AutoFixer

        result = SmartScan("/path/to/server").run()
        fixes = AutoFixer(result).fix_all()
        for fix in fixes:
            status = "OK" if fix.success else f"FAILED: {fix.error}"
            print(f"{fix.issue_type.value}: {status}")
    """

    result: SmartScanResult

    def fix_all(self) -> List[Fix]:
        """Attempt all auto-fixable issues and return a list of Fix records.

        Each auto-fixable issue in ``self.result.issues`` gets one Fix entry.
        Issues with ``auto_fixable=False`` are skipped entirely — they do not
        appear in the returned list.

        Returns:
            A list of ``Fix`` dataclass instances, one per attempted fix.
        """
        fixes: List[Fix] = []

        for issue in self.result.issues:
            if not issue.auto_fixable:
                logger.debug(
                    "Skipping non-auto-fixable issue: %s", issue.issue_type.value
                )
                continue

            fix = self._dispatch(issue.issue_type)
            if fix is not None:
                fixes.append(fix)

        return fixes

    # ------------------------------------------------------------------
    # Internal dispatch
    # ------------------------------------------------------------------

    def _dispatch(self, issue_type: IssueType) -> Fix | None:
        """Route an IssueType to the appropriate fix strategy.

        Returns None if no strategy exists for the given type (which should
        not happen for auto-fixable issues in practice, but is safe to handle).
        """
        strategies = {
            IssueType.missing_package_lock: self._fix_missing_package_lock,
            IssueType.path_has_spaces: self._fix_path_has_spaces,
            IssueType.runtime_version_mismatch: self._fix_runtime_version_mismatch,
        }

        strategy = strategies.get(issue_type)
        if strategy is None:
            logger.warning(
                "No fix strategy registered for auto-fixable issue: %s",
                issue_type.value,
            )
            return None

        return strategy()

    # ------------------------------------------------------------------
    # Fix strategies
    # ------------------------------------------------------------------

    def _fix_missing_package_lock(self) -> Fix:
        """Generate a package-lock.json file via a transient Docker container.

        Runs::

            docker run --rm \\
                -v <server_path>:/app \\
                -w /app \\
                node:<ver>-slim \\
                npm install --package-lock-only

        The Node.js version is taken from ``result.runtime_version`` and
        defaults to "20" when the field is empty.

        Returns:
            A Fix recording whether the command succeeded and which files
            were modified.
        """
        server_path = self.result.server_path
        node_version = self.result.runtime_version or _DEFAULT_NODE_VERSION
        image = f"node:{node_version}-slim"
        lock_file = str(Path(server_path) / "package-lock.json")

        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{server_path}:/app",
            "-w",
            "/app",
            image,
            "npm",
            "install",
            "--package-lock-only",
        ]

        logger.info(
            "Generating package-lock.json via Docker (%s): %s",
            image,
            " ".join(cmd),
        )

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=_SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            msg = (
                f"docker run timed out after {_SUBPROCESS_TIMEOUT}s "
                f"while generating package-lock.json"
            )
            logger.error(msg)
            return Fix(
                issue_type=IssueType.missing_package_lock,
                description="Generate package-lock.json via Docker",
                files_modified=[],
                success=False,
                error=msg,
            )
        except FileNotFoundError:
            msg = "docker executable not found; cannot generate package-lock.json"
            logger.error(msg)
            return Fix(
                issue_type=IssueType.missing_package_lock,
                description="Generate package-lock.json via Docker",
                files_modified=[],
                success=False,
                error=msg,
            )
        except OSError as exc:
            msg = f"OS error while running docker: {exc}"
            logger.error(msg)
            return Fix(
                issue_type=IssueType.missing_package_lock,
                description="Generate package-lock.json via Docker",
                files_modified=[],
                success=False,
                error=msg,
            )

        if proc.returncode != 0:
            stderr_snippet = proc.stderr.strip()[:500]
            msg = (
                f"npm install --package-lock-only exited with code "
                f"{proc.returncode}: {stderr_snippet}"
            )
            logger.error(msg)
            return Fix(
                issue_type=IssueType.missing_package_lock,
                description="Generate package-lock.json via Docker",
                files_modified=[],
                success=False,
                error=msg,
            )

        logger.info("package-lock.json generated at %s", lock_file)
        return Fix(
            issue_type=IssueType.missing_package_lock,
            description="Generated package-lock.json via Docker npm install",
            files_modified=[lock_file],
            success=True,
            error="",
        )

    def _fix_path_has_spaces(self) -> Fix:
        """Log advisory instructions for paths that contain spaces.

        Paths with spaces require quoting in volume mount strings. This fix
        cannot rewrite the filesystem path itself, so it records the advisory
        instruction and marks the fix as a metadata-only update. No files are
        modified on disk.

        Returns:
            A Fix with ``files_modified=[]`` and ``success=True`` indicating
            the advisory instruction has been recorded.
        """
        server_path = self.result.server_path
        instruction = (
            f"Path '{server_path}' contains spaces. "
            "Ensure volume mount strings quote or escape the path, e.g. "
            f'"-v \\"{server_path}\\":/app". '
            "Consider moving the server to a path without spaces for "
            "broadest compatibility."
        )

        logger.info(
            "[path_has_spaces] Advisory fix recorded. %s", instruction
        )

        return Fix(
            issue_type=IssueType.path_has_spaces,
            description=instruction,
            files_modified=[],
            success=True,
            error="",
        )

    def _fix_runtime_version_mismatch(self) -> Fix:
        """Acknowledge the detected runtime version in metadata.

        The scanner may report a mismatch between what was specified and what
        was detected. This fix records that the detected version has been
        acknowledged as authoritative for subsequent steps (e.g. template
        rendering). No file changes are required because the SmartScanResult
        already carries the detected version.

        Returns:
            A Fix with ``files_modified=[]`` and ``success=True``.
        """
        detected = self.result.runtime_version or "(unknown)"
        runtime = self.result.runtime or "(unknown)"

        description = (
            f"Runtime version mismatch acknowledged. "
            f"Using detected version '{detected}' for runtime '{runtime}'. "
            "No file changes required; downstream steps will use the "
            "detected version."
        )

        logger.info("[runtime_version_mismatch] %s", description)

        return Fix(
            issue_type=IssueType.runtime_version_mismatch,
            description=description,
            files_modified=[],
            success=True,
            error="",
        )
