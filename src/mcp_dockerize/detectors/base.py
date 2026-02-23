"""Abstract base class for MCP server runtime detectors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ServerMetadata:
    """Unified metadata returned by any detector.

    This replaces the existing ServerMetadata in detectors/python.py —
    python.py will be updated in T020 to return this type instead.
    """

    name: str
    runtime: str  # "python_uv" | "python_direct" | "node_npm"
    runtime_version: str  # e.g. "3.11" or "20"
    entry_point: str  # relative path or script name
    package_manager: str  # "uv" | "pip" | "npm"
    dependencies: List[str] = field(default_factory=list)
    env_vars: List[str] = field(default_factory=list)
    data_volumes: List[str] = field(default_factory=list)
    deployment_pattern: str = "volume_mounted"
    # Node-specific
    has_package_lock: bool = True
    # Python-specific (kept for backward compat)
    server_type: Optional[str] = None
    python_version: Optional[str] = None
    env_file: Optional[str] = None
    volume_mounts: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


class AbstractDetector(ABC):
    """Interface all runtime detectors must implement."""

    @abstractmethod
    def can_detect(self, path: Path) -> bool:
        """Return True if this detector recognises the server at path."""

    @abstractmethod
    def detect(self, path: Path) -> ServerMetadata:
        """Analyse the server and return its metadata.

        Raises:
            ValueError: if the server cannot be properly analysed.
        """
