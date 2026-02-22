"""Abstract base class for AI platform config integrations."""

import json
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from mcp_dockerize.registry.models import RegistryEntry


class AbstractPlatform(ABC):
    """Interface for writing/removing MCP server entries in platform config files.

    JSON platforms use the default _read_config/_write_config.
    YAML platforms (Goose, Codex) override these methods.
    """

    @property
    @abstractmethod
    def platform_id(self) -> str:
        """Unique identifier string, e.g. 'claude_code', 'cursor'."""

    @property
    @abstractmethod
    def config_path(self) -> Path:
        """Absolute path to the platform's config file."""

    @abstractmethod
    def add_server(self, entry: RegistryEntry, compose_path: Path) -> None:
        """Write the server entry into the platform config."""

    @abstractmethod
    def remove_server(self, name: str) -> None:
        """Remove the server entry from the platform config."""

    # ------------------------------------------------------------------
    # Shared helpers — JSON platforms use these; YAML platforms override
    # ------------------------------------------------------------------

    def _read_config(self) -> Any:
        """Read and parse the config file. Returns {} if missing."""
        path = self.config_path
        if not path.exists():
            return {}
        with open(path) as f:
            return json.load(f)

    def _write_config(self, data: Any) -> None:
        """Write config atomically (backup -> tmp -> os.replace)."""
        import os

        path = self.config_path
        path.parent.mkdir(parents=True, exist_ok=True)
        # Backup
        if path.exists():
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        os.replace(tmp, path)
