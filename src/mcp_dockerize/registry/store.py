"""Persistent JSON registry store for wrapped MCP servers.

Provides atomic read/write operations backed by
``~/.config/mcp-librarian/registry.json``.
"""

import dataclasses
import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from mcp_dockerize.health.states import HealthCheckResult, HealthStatus
from mcp_dockerize.registry.models import (
    ContainerConfig,
    CredentialType,
    DeploymentPattern,
    EnvVar,
    HealthSummary,
    RegistryEntry,
    Runtime,
    ServerStatus,
)

__all__ = ["RegistryStore"]

_REGISTRY_PATH = Path.home() / ".config" / "mcp-librarian" / "registry.json"

# 7 days of hourly checks
_MAX_HEALTH_HISTORY = 168


def _serialize(obj: Any) -> Any:
    """Recursively serialize an object to a JSON-safe structure.

    Handles:
    - dataclasses  → dict (via ``dataclasses.asdict``-style recursion)
    - Enum         → ``.value``
    - list / tuple → list with each element serialized
    - dict         → dict with each value serialized
    - Everything else passes through as-is.
    """
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {
            field.name: _serialize(getattr(obj, field.name))
            for field in dataclasses.fields(obj)
        }
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, (list, tuple)):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


def _deserialize_health_check_result(data: dict) -> HealthCheckResult:
    """Reconstruct a ``HealthCheckResult`` from a raw dict."""
    return HealthCheckResult(
        server_name=data["server_name"],
        container_running=data["container_running"],
        protocol_responds=data["protocol_responds"],
        tools_available=data["tools_available"],
        response_time_ms=data["response_time_ms"],
        status=HealthStatus(data["status"]),
        error_message=data.get("error_message", ""),
        check_time=data.get("check_time", ""),
    )


def _deserialize_health_summary(data: dict) -> HealthSummary:
    """Reconstruct a ``HealthSummary`` from a raw dict."""
    return HealthSummary(
        last_check=data.get("last_check"),
        last_status=HealthStatus(data["last_status"]),
        consecutive_failures=data.get("consecutive_failures", 0),
        total_checks=data.get("total_checks", 0),
    )


def _deserialize_container_config(data: Optional[dict]) -> Optional[ContainerConfig]:
    """Reconstruct a ``ContainerConfig`` from a raw dict, or return None."""
    if data is None:
        return None
    return ContainerConfig(
        compose_path=data["compose_path"],
        dockerfile_path=data["dockerfile_path"],
        image_name=data["image_name"],
        build_context=data["build_context"],
    )


def _deserialize_registry_entry(data: dict) -> RegistryEntry:
    """Reconstruct a ``RegistryEntry`` from a raw dict."""
    return RegistryEntry(
        name=data["name"],
        source_path=data["source_path"],
        runtime=Runtime(data["runtime"]),
        status=ServerStatus(data["status"]),
        registered_platforms=data.get("registered_platforms", []),
        container_config=_deserialize_container_config(data.get("container_config")),
        health=_deserialize_health_summary(
            data.get("health", {"last_status": HealthStatus.unknown.value})
        ),
        health_history=[
            _deserialize_health_check_result(r)
            for r in data.get("health_history", [])
        ],
        registered_at=data.get("registered_at", ""),
        last_seen=data.get("last_seen", ""),
    )


class RegistryStore:
    """Persistent JSON store for :class:`~mcp_dockerize.registry.models.RegistryEntry` objects.

    Storage layout::

        ~/.config/mcp-librarian/registry.json
        {
            "servers": {
                "<name>": { ... RegistryEntry fields ... }
            }
        }

    All writes are atomic: data is written to a ``.tmp`` file first, then
    renamed over the target path via :func:`os.replace` to prevent partial
    writes from corrupting the registry.

    Example::

        store = RegistryStore()
        store.add(entry)
        fetched = store.get("my-server")
        store.remove("my-server")
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = path or _REGISTRY_PATH

    # ------------------------------------------------------------------
    # Low-level I/O
    # ------------------------------------------------------------------

    def load(self) -> dict:
        """Read and return the raw registry dict.

        Returns an empty dict (``{}``) if the registry file does not exist yet.

        Returns:
            The parsed JSON document, or ``{}`` if the file is absent.

        Raises:
            json.JSONDecodeError: If the file exists but contains invalid JSON.
        """
        if not self._path.exists():
            return {}
        with self._path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def save(self, data: dict) -> None:
        """Atomically persist *data* to the registry file.

        Steps:
        1. Create parent directories if needed.
        2. Serialize *data* to JSON and write to ``<registry>.tmp``.
        3. Use :func:`os.replace` to atomically rename the tmp file over the
           target path — on POSIX systems this is a single syscall and
           therefore cannot leave a half-written file visible.

        Args:
            data: The complete registry document to persist.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_suffix(".tmp")
        try:
            with tmp_path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2, ensure_ascii=False)
            os.replace(tmp_path, self._path)
        except Exception:
            # Best-effort cleanup of the temporary file on failure.
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    def add(self, entry: RegistryEntry) -> None:
        """Add or overwrite a registry entry keyed by ``entry.name``.

        Args:
            entry: The :class:`RegistryEntry` to persist.
        """
        data = self.load()
        servers: dict = data.setdefault("servers", {})
        servers[entry.name] = _serialize(entry)
        self.save(data)

    def get(self, name: str) -> Optional[RegistryEntry]:
        """Return the :class:`RegistryEntry` for *name*, or ``None`` if absent.

        Args:
            name: The server name to look up.

        Returns:
            A fully reconstructed :class:`RegistryEntry`, or ``None``.
        """
        data = self.load()
        raw = data.get("servers", {}).get(name)
        if raw is None:
            return None
        return _deserialize_registry_entry(raw)

    def list_all(self) -> list[RegistryEntry]:
        """Return all stored entries as a list of :class:`RegistryEntry` objects.

        Returns:
            A list of all registry entries (may be empty).
        """
        data = self.load()
        return [
            _deserialize_registry_entry(raw)
            for raw in data.get("servers", {}).values()
        ]

    def remove(self, name: str) -> None:
        """Delete the registry entry for *name*.

        This is a no-op (silently ignored) if *name* does not exist.

        Args:
            name: The server name to remove.
        """
        data = self.load()
        servers: dict = data.get("servers", {})
        if name not in servers:
            return
        del servers[name]
        self.save(data)

    # ------------------------------------------------------------------
    # Health tracking
    # ------------------------------------------------------------------

    def update_health(self, name: str, result: HealthCheckResult) -> None:
        """Append a health check result and update the health summary for *name*.

        Behaviour:
        - Appends *result* to ``health_history`` for the named server.
        - Trims ``health_history`` to the last :data:`_MAX_HEALTH_HISTORY`
          entries (168 = 7 days at an hourly cadence).
        - Updates ``health`` summary fields: ``last_check``, ``last_status``,
          ``consecutive_failures``, and ``total_checks``.
        - Does nothing if *name* is not found in the registry.

        Args:
            name: Server name whose health record should be updated.
            result: The :class:`HealthCheckResult` to append.
        """
        data = self.load()
        servers: dict = data.get("servers", {})
        if name not in servers:
            return

        raw = servers[name]

        # Append the new result to history and trim to the rolling window.
        history: list = raw.setdefault("health_history", [])
        history.append(_serialize(result))
        raw["health_history"] = history[-_MAX_HEALTH_HISTORY:]

        # Recompute the summary from the persisted result.
        serialized_result = _serialize(result)
        summary: dict = raw.setdefault("health", {})
        summary["last_check"] = serialized_result["check_time"]
        summary["last_status"] = serialized_result["status"]
        summary["total_checks"] = summary.get("total_checks", 0) + 1

        # Track consecutive failures.
        if result.status in (HealthStatus.unhealthy, HealthStatus.unknown):
            summary["consecutive_failures"] = summary.get("consecutive_failures", 0) + 1
        else:
            summary["consecutive_failures"] = 0

        self.save(data)
