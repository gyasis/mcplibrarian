"""Canonical health status types for MCP server health monitoring.

Defined here so registry.models can import without circular dependency.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class HealthStatus(Enum):
    """Operational health state of a wrapped MCP server."""

    healthy = "healthy"
    unhealthy = "unhealthy"
    stopped = "stopped"
    unknown = "unknown"
    source_missing = "source_missing"


@dataclass
class HealthCheckResult:
    """Result of a single 4-level MCP health check.

    L1 – Docker container running state
    L2 – MCP protocol responds to ``initialize``
    L3 – ``tools/list`` returns a non-empty array
    L4 – Response time measurement (ms)
    """

    server_name: str
    container_running: bool
    protocol_responds: bool
    tools_available: bool
    response_time_ms: float
    status: HealthStatus
    error_message: str = ""
    check_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
