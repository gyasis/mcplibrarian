"""Cursor platform config integration."""

from pathlib import Path

from mcp_dockerize.platforms.base import AbstractPlatform
from mcp_dockerize.registry.models import RegistryEntry


class CursorPlatform(AbstractPlatform):
    """Writes MCP server entries to Cursor's mcp.json config file.

    Entry format mirrors Claude Code — ``mcpServers.<name>`` with
    ``command`` / ``args`` keys.  The config file is created with an
    empty ``{"mcpServers": {}}`` skeleton when it does not yet exist.
    """

    @property
    def platform_id(self) -> str:
        return "cursor"

    @property
    def config_path(self) -> Path:
        return Path.home() / ".cursor" / "mcp.json"

    def add_server(self, entry: RegistryEntry, compose_path: Path) -> None:
        """Add MCP server entry to Cursor config.

        Entry format:

        .. code-block:: json

            {
              "mcpServers": {
                "<name>": {
                  "command": "docker",
                  "args": ["compose", "-f", "<abs_compose_path>", "run", "--rm", "<name>"]
                }
              }
            }

        Creates ``~/.cursor/mcp.json`` with ``{"mcpServers": {}}`` if the file
        does not exist.
        """
        config = self._read_config()
        if not isinstance(config, dict):
            config = {}
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        config["mcpServers"][entry.name] = {
            "command": "docker",
            "args": [
                "compose",
                "-f", str(compose_path.resolve()),
                "run",
                "--rm",
                entry.name,
            ],
        }
        self._write_config(config)

    def remove_server(self, name: str) -> None:
        """Remove MCP server entry from Cursor config.

        Silently skips if the entry or the ``mcpServers`` key is absent.
        """
        config = self._read_config()
        if isinstance(config, dict) and "mcpServers" in config:
            config["mcpServers"].pop(name, None)
            self._write_config(config)
