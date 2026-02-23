"""4-level MCP health checker for containerised MCP servers.

Level checks
------------
L1 – Docker container running state (docker compose ps)
L2 – MCP protocol responds to ``initialize`` JSON-RPC call
L3 – ``tools/list`` JSON-RPC call returns a ``tools`` key
L4 – Response time measurement (ms) captured during L2

All subprocess calls use ``subprocess.run`` with docker compose v2 syntax.
The Docker Python SDK is intentionally **not** used here; compose commands
are only available via the CLI.
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any

from mcp_dockerize.health.states import HealthCheckResult, HealthStatus
from mcp_dockerize.registry.models import RegistryEntry

__all__ = ["MCPHealthChecker"]

logger = logging.getLogger(__name__)

# JSON-RPC message templates
_INITIALIZE_MSG: dict[str, Any] = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "mcp-health-checker", "version": "1.0.0"},
    },
}

_TOOLS_LIST_MSG: dict[str, Any] = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {},
}

# Per-level timeout in seconds
_LEVEL_TIMEOUT: int = 10

# Maximum acceptable response time to be considered healthy (ms)
_MAX_HEALTHY_RESPONSE_MS: float = 5_000.0

# Seconds to wait after restart before re-checking
_RECOVERY_WAIT_SECS: int = 5


class MCPHealthChecker:
    """Run 4-level health checks against a containerised MCP server.

    Usage::

        checker = MCPHealthChecker()
        result = checker.check(registry_entry)
        if result.status == HealthStatus.unhealthy:
            recovered = checker.attempt_recovery(registry_entry)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, entry: RegistryEntry) -> HealthCheckResult:
        """Run L1 → L2 → L3 → L4 in sequence; stop at first failure.

        Parameters
        ----------
        entry:
            Registry entry whose ``container_config`` holds the compose
            file path and whose ``name`` is the service name.

        Returns
        -------
        HealthCheckResult
            Populated result with the final ``HealthStatus``.
        """
        compose_path = self._get_compose_path(entry)
        service_name = entry.name

        # Pre-L1 — source directory still exists on disk?
        if entry.source_path and not Path(entry.source_path).exists():
            logger.debug(
                "source_missing for %s: path not found: %s",
                service_name,
                entry.source_path,
            )
            return HealthCheckResult(
                server_name=service_name,
                container_running=False,
                protocol_responds=False,
                tools_available=False,
                response_time_ms=0.0,
                status=HealthStatus.source_missing,
                error_message=f"Source directory not found: {entry.source_path}",
            )

        result = HealthCheckResult(
            server_name=service_name,
            container_running=False,
            protocol_responds=False,
            tools_available=False,
            response_time_ms=0.0,
            status=HealthStatus.unknown,
        )

        # L1 — container running?
        l1_ok, l1_err = self._check_container_running(compose_path, service_name)
        result.container_running = l1_ok
        if not l1_ok:
            result.status = HealthStatus.stopped
            result.error_message = l1_err
            logger.debug("L1 failed for %s: %s", service_name, l1_err)
            return result

        # L2 — protocol responds?
        l2_ok, l2_err, response_time_ms = self._check_protocol(
            compose_path, service_name
        )
        result.protocol_responds = l2_ok
        result.response_time_ms = response_time_ms
        if not l2_ok:
            result.status = HealthStatus.unhealthy
            result.error_message = l2_err
            logger.debug("L2 failed for %s: %s", service_name, l2_err)
            return result

        # L3 — tools/list works?
        l3_ok, l3_err = self._check_tools_list(compose_path, service_name)
        result.tools_available = l3_ok
        if not l3_ok:
            result.status = HealthStatus.unhealthy
            result.error_message = l3_err
            logger.debug("L3 failed for %s: %s", service_name, l3_err)
            return result

        # L4 — classify by response time
        if result.response_time_ms < _MAX_HEALTHY_RESPONSE_MS:
            result.status = HealthStatus.healthy
        else:
            result.status = HealthStatus.unhealthy
            result.error_message = (
                f"Response time {result.response_time_ms:.0f} ms exceeds "
                f"{_MAX_HEALTHY_RESPONSE_MS:.0f} ms threshold"
            )

        logger.debug(
            "Health check complete for %s: %s (%.0f ms)",
            service_name,
            result.status.value,
            result.response_time_ms,
        )
        return result

    def attempt_recovery(self, entry: RegistryEntry) -> bool:
        """Restart the service and verify it becomes healthy.

        Runs ``docker compose restart``, waits ``_RECOVERY_WAIT_SECS``
        seconds, then re-runs L1 + L2. Returns ``True`` if both pass.

        Parameters
        ----------
        entry:
            Registry entry for the server to recover.

        Returns
        -------
        bool
            ``True`` if the server is healthy after recovery, else ``False``.
        """
        compose_path = self._get_compose_path(entry)
        service_name = entry.name

        logger.info("Attempting recovery for %s", service_name)

        restart_cmd = [
            "docker",
            "compose",
            "-f",
            compose_path,
            "restart",
            service_name,
        ]
        try:
            proc = subprocess.run(
                restart_cmd,
                capture_output=True,
                text=True,
                timeout=_LEVEL_TIMEOUT,
            )
            if proc.returncode != 0:
                logger.warning(
                    "docker compose restart failed for %s: %s",
                    service_name,
                    proc.stderr.strip(),
                )
                return False
        except subprocess.TimeoutExpired:
            logger.warning("docker compose restart timed out for %s", service_name)
            return False
        except OSError as exc:
            logger.warning("Failed to run docker compose restart: %s", exc)
            return False

        logger.debug(
            "Waiting %d s after restart for %s", _RECOVERY_WAIT_SECS, service_name
        )
        time.sleep(_RECOVERY_WAIT_SECS)

        # Re-validate with L1 + L2
        l1_ok, _ = self._check_container_running(compose_path, service_name)
        if not l1_ok:
            logger.info("Recovery failed for %s: container still not running", service_name)
            return False

        l2_ok, _, _ = self._check_protocol(compose_path, service_name)
        if not l2_ok:
            logger.info("Recovery failed for %s: protocol still not responding", service_name)
            return False

        logger.info("Recovery succeeded for %s", service_name)
        return True

    # ------------------------------------------------------------------
    # Level implementations
    # ------------------------------------------------------------------

    def _check_container_running(
        self, compose_path: str, service_name: str
    ) -> tuple[bool, str]:
        """L1: Verify the compose service is in a running state.

        Runs ``docker compose ps --format json`` and inspects the output
        for a service whose name matches *service_name* and whose
        ``State`` or ``Status`` field indicates it is running.

        Returns
        -------
        tuple[bool, str]
            ``(is_running, error_message)`` — error_message is empty on success.
        """
        cmd = [
            "docker",
            "compose",
            "-f",
            compose_path,
            "ps",
            "--format",
            "json",
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=_LEVEL_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return False, "docker compose ps timed out"
        except OSError as exc:
            return False, f"Failed to run docker compose ps: {exc}"

        if proc.returncode != 0:
            return False, f"docker compose ps error: {proc.stderr.strip()}"

        stdout = proc.stdout.strip()
        if not stdout:
            return False, "No containers reported by docker compose ps"

        # docker compose ps --format json may emit one JSON object per line
        # (NDJSON) or a JSON array depending on the compose version.
        services = _parse_compose_ps_output(stdout)
        if services is None:
            return False, f"Could not parse docker compose ps output: {stdout[:200]}"

        for svc in services:
            svc_name: str = (
                svc.get("Service") or svc.get("Name") or svc.get("name") or ""
            )
            # The service name in compose ps output is often the short service
            # name; match either exact or suffix after underscore/dash.
            if _service_name_matches(svc_name, service_name):
                state: str = (
                    svc.get("State") or svc.get("Status") or svc.get("state") or ""
                )
                if state.lower().startswith("up") or state.lower() == "running":
                    return True, ""
                return False, f"Service '{service_name}' state is '{state}'"

        return False, f"Service '{service_name}' not found in docker compose ps output"

    def _check_protocol(
        self, compose_path: str, service_name: str
    ) -> tuple[bool, str, float]:
        """L2: Send ``initialize`` JSON-RPC message and validate response.

        Uses ``docker compose run --rm`` with the message piped via stdin.
        Measures wall-clock time for the full round-trip.

        Returns
        -------
        tuple[bool, str, float]
            ``(success, error_message, response_time_ms)``
        """
        json_msg = json.dumps(_INITIALIZE_MSG) + "\n"
        cmd = [
            "docker",
            "compose",
            "-f",
            compose_path,
            "run",
            "--rm",
            service_name,
        ]
        start = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                input=json_msg,
                capture_output=True,
                text=True,
                timeout=_LEVEL_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            elapsed_ms = (time.monotonic() - start) * 1000
            return False, "Protocol check (initialize) timed out", elapsed_ms
        except OSError as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            return False, f"Failed to run docker compose run: {exc}", elapsed_ms

        elapsed_ms = (time.monotonic() - start) * 1000

        # A non-zero exit is acceptable if the server wrote a valid JSON-RPC
        # response before exiting — some servers exit after one message.
        stdout = proc.stdout.strip()
        if not stdout:
            err = proc.stderr.strip() or "Empty stdout from initialize call"
            return False, err, elapsed_ms

        parsed = _parse_jsonrpc_response(stdout)
        if parsed is None:
            return (
                False,
                f"No valid JSON-RPC response found in stdout: {stdout[:200]}",
                elapsed_ms,
            )

        if "jsonrpc" not in parsed:
            return (
                False,
                f"Response missing 'jsonrpc' field: {stdout[:200]}",
                elapsed_ms,
            )

        return True, "", elapsed_ms

    def _check_tools_list(
        self, compose_path: str, service_name: str
    ) -> tuple[bool, str]:
        """L3: Send ``tools/list`` JSON-RPC message and validate response.

        Checks that the response contains a ``tools`` key whose value is
        a list (which may be empty).

        Returns
        -------
        tuple[bool, str]
            ``(success, error_message)``
        """
        json_msg = json.dumps(_TOOLS_LIST_MSG) + "\n"
        cmd = [
            "docker",
            "compose",
            "-f",
            compose_path,
            "run",
            "--rm",
            service_name,
        ]
        try:
            proc = subprocess.run(
                cmd,
                input=json_msg,
                capture_output=True,
                text=True,
                timeout=_LEVEL_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return False, "tools/list check timed out"
        except OSError as exc:
            return False, f"Failed to run docker compose run for tools/list: {exc}"

        stdout = proc.stdout.strip()
        if not stdout:
            err = proc.stderr.strip() or "Empty stdout from tools/list call"
            return False, err

        parsed = _parse_jsonrpc_response(stdout)
        if parsed is None:
            return (
                False,
                f"No valid JSON-RPC response for tools/list: {stdout[:200]}",
            )

        # The result is nested under parsed["result"]["tools"]
        result_field = parsed.get("result", parsed)
        tools = result_field.get("tools") if isinstance(result_field, dict) else None

        if tools is None:
            return False, f"'tools' key missing from tools/list response: {stdout[:200]}"

        if not isinstance(tools, list):
            return False, f"'tools' field is not a list: {type(tools).__name__}"

        return True, ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_compose_path(entry: RegistryEntry) -> str:
        """Extract the compose file path from a registry entry.

        Raises
        ------
        ValueError
            If ``entry.container_config`` is ``None``.
        """
        if entry.container_config is None:
            raise ValueError(
                f"Registry entry '{entry.name}' has no container_config. "
                "The server may not have been wrapped yet."
            )
        return entry.container_config.compose_path


# ---------------------------------------------------------------------------
# Module-level helpers (not part of the public API)
# ---------------------------------------------------------------------------


def _parse_compose_ps_output(stdout: str) -> list[dict[str, Any]] | None:
    """Parse ``docker compose ps --format json`` output.

    Compose v2 may output:
    - A JSON array:  ``[{...}, {...}]``
    - NDJSON (one JSON object per line): ``{...}\\n{...}``

    Returns ``None`` on unrecoverable parse error.
    """
    stdout = stdout.strip()
    if not stdout:
        return []

    # Try JSON array first
    if stdout.startswith("["):
        try:
            data = json.loads(stdout)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    # Try NDJSON
    services: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                services.append(obj)
        except json.JSONDecodeError:
            # Skip non-JSON lines (headers, blank lines)
            continue

    if services:
        return services

    return None


def _parse_jsonrpc_response(stdout: str) -> dict[str, Any] | None:
    """Find and return the first valid JSON-RPC response object in *stdout*.

    MCP servers may emit log lines or other text before/after the JSON
    response. We scan each line looking for valid JSON containing either
    ``"jsonrpc"`` or ``"result"`` or ``"error"`` keys.

    Returns ``None`` if no valid response is found.
    """
    for line in stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict) and (
                "jsonrpc" in obj or "result" in obj or "error" in obj
            ):
                return obj
        except json.JSONDecodeError:
            continue

    # Fallback: try the whole stdout as a single JSON blob
    try:
        obj = json.loads(stdout)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    return None


def _service_name_matches(reported_name: str, service_name: str) -> bool:
    """Return True if *reported_name* corresponds to *service_name*.

    ``docker compose ps`` can report the service as either the bare
    service name (e.g. ``myserver``) or a compound name that includes
    the project prefix (e.g. ``myproject-myserver-1``). We accept a
    match if any dash/underscore-separated segment equals *service_name*.
    """
    if reported_name == service_name:
        return True
    # Check suffixes after common separators
    for sep in ("-", "_"):
        parts = reported_name.split(sep)
        if service_name in parts:
            return True
    return False
