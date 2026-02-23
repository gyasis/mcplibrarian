"""Registry data models for MCP server containerization.

HealthStatus and HealthCheckResult are imported from health.states
(canonical definition) to avoid duplication and circular imports.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from mcp_dockerize.health.states import HealthCheckResult, HealthStatus

__all__ = [
    "Runtime",
    "DeploymentPattern",
    "ServerStatus",
    "HealthStatus",
    "CredentialType",
    "EnvVar",
    "HealthCheckResult",
    "HealthSummary",
    "ContainerConfig",
    "RegistryEntry",
]


class Runtime(Enum):
    python_uv = "python_uv"
    python_direct = "python_direct"
    node_npm = "node_npm"
    unknown = "unknown"


class DeploymentPattern(Enum):
    volume_mounted = "volume_mounted"
    self_contained = "self_contained"


class ServerStatus(Enum):
    unwrapped = "unwrapped"
    wrapping = "wrapping"
    wrapped_active = "wrapped_active"
    wrapped_stopped = "wrapped_stopped"
    error = "error"
    source_missing = "source_missing"


class CredentialType(Enum):
    env_var = "env_var"
    file_mount = "file_mount"
    none = "none"


@dataclass
class EnvVar:
    name: str
    description: str
    required: bool = True
    example: str = ""


@dataclass
class HealthSummary:
    last_check: Optional[str] = None
    last_status: HealthStatus = field(default_factory=lambda: HealthStatus.unknown)
    consecutive_failures: int = 0
    total_checks: int = 0


@dataclass
class ContainerConfig:
    compose_path: str
    dockerfile_path: str
    image_name: str
    build_context: str


@dataclass
class RegistryEntry:
    name: str
    source_path: str
    runtime: Runtime
    status: ServerStatus
    registered_platforms: List[str] = field(default_factory=list)
    container_config: Optional[ContainerConfig] = None
    health: HealthSummary = field(default_factory=HealthSummary)
    health_history: List[HealthCheckResult] = field(default_factory=list)
    registered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_seen: str = ""
