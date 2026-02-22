"""Claude Code platform config integration."""

from pathlib import Path

from mcp_dockerize.platforms.base import AbstractPlatform
from mcp_dockerize.registry.models import RegistryEntry


class ClaudeCodePlatform(AbstractPlatform):

    @property
    def platform_id(self) -> str:
        return "claude_code"

    @property
    def config_path(self) -> Path:
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

    def add_server(self, entry: RegistryEntry, compose_path: Path) -> None:
        """Add MCP server entry to Claude Desktop config.

        Entry format:
        {
          "mcpServers": {
            "<name>": {
              "command": "docker",
              "args": ["compose", "-f", "<abs_compose_path>", "run", "--rm", "<name>"]
            }
          }
        }
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
        """Remove MCP server entry from Claude Desktop config."""
        config = self._read_config()
        if isinstance(config, dict) and "mcpServers" in config:
            config["mcpServers"].pop(name, None)
            self._write_config(config)
