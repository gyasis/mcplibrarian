"""Goose platform config integration (YAML format)."""

import shutil
from pathlib import Path
from typing import Any

import yaml

from mcp_dockerize.platforms.base import AbstractPlatform
from mcp_dockerize.registry.models import RegistryEntry


class GoosePlatform(AbstractPlatform):
    """Writes MCP server entries to Block's Goose ``config.yaml``.

    Goose uses YAML rather than JSON, so this class overrides
    ``_read_config`` and ``_write_config`` to use ``yaml.safe_load`` /
    ``yaml.safe_dump``.  Entries are appended to the top-level
    ``extensions`` list; duplicate names are rejected silently.
    """

    @property
    def platform_id(self) -> str:
        return "goose"

    @property
    def config_path(self) -> Path:
        return Path.home() / ".config" / "goose" / "config.yaml"

    # ------------------------------------------------------------------
    # YAML overrides
    # ------------------------------------------------------------------

    def _read_config(self) -> Any:
        """Read and parse the YAML config file.  Returns ``{}`` if missing."""
        path = self.config_path
        if not path.exists():
            return {}
        with open(path) as fh:
            data = yaml.safe_load(fh)
        return data if data is not None else {}

    def _write_config(self, data: Any) -> None:
        """Write config atomically (backup -> tmp -> os.replace) as YAML."""
        import os

        path = self.config_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(yaml.safe_dump(data, default_flow_style=False, allow_unicode=True))
        os.replace(tmp, path)

    # ------------------------------------------------------------------
    # AbstractPlatform implementation
    # ------------------------------------------------------------------

    def add_server(self, entry: RegistryEntry, compose_path: Path) -> None:
        """Append an MCP server extension to Goose's ``extensions`` list.

        Skips silently if an extension with the same name already exists.

        Extension format:

        .. code-block:: yaml

            extensions:
              - name: <name>
                type: stdio
                cmd: docker
                args:
                  - compose
                  - -f
                  - <abs_compose_path>
                  - run
                  - --rm
                  - <name>
                description: "MCP server: <name>"
                enabled: true
        """
        config = self._read_config()
        if not isinstance(config, dict):
            config = {}

        extensions: list[dict] = config.setdefault("extensions", [])

        # Check for duplicates by name — skip if already registered.
        for item in extensions:
            if isinstance(item, dict) and item.get("name") == entry.name:
                return

        extensions.append(
            {
                "name": entry.name,
                "type": "stdio",
                "cmd": "docker",
                "args": [
                    "compose",
                    "-f", str(compose_path.resolve()),
                    "run",
                    "--rm",
                    entry.name,
                ],
                "description": f"MCP server: {entry.name}",
                "enabled": True,
            }
        )
        self._write_config(config)

    def remove_server(self, name: str) -> None:
        """Remove the extension with the given *name* from Goose's config.

        Silently skips if the ``extensions`` key is absent or the name is not
        found.
        """
        config = self._read_config()
        if not isinstance(config, dict) or "extensions" not in config:
            return

        config["extensions"] = [
            item
            for item in config["extensions"]
            if not (isinstance(item, dict) and item.get("name") == name)
        ]
        self._write_config(config)
