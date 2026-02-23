"""VS Code platform config integration."""

from pathlib import Path
from typing import Any

from mcp_dockerize.platforms.base import AbstractPlatform
from mcp_dockerize.registry.models import RegistryEntry


def _set_nested(data: dict, keys: list[str], value: Any) -> None:
    """Set a deeply-nested key in *data*, creating intermediate dicts as needed.

    Example::

        _set_nested(data, ["mcp", "servers", "my-server"], {"type": "stdio"})
        # equivalent to: data["mcp"]["servers"]["my-server"] = {"type": "stdio"}
    """
    node = data
    for key in keys[:-1]:
        if key not in node or not isinstance(node[key], dict):
            node[key] = {}
        node = node[key]
    node[keys[-1]] = value


def _pop_nested(data: dict, keys: list[str]) -> None:
    """Pop a deeply-nested key from *data*.  Silently skips missing paths."""
    node = data
    for key in keys[:-1]:
        if not isinstance(node, dict) or key not in node:
            return
        node = node[key]
    if isinstance(node, dict):
        node.pop(keys[-1], None)


class VSCodePlatform(AbstractPlatform):
    """Writes MCP server entries into VS Code's ``settings.json``.

    The entry is placed at the nested path ``mcp.servers.<name>`` using a
    deep-merge strategy so that all other VS Code settings remain untouched.
    """

    @property
    def platform_id(self) -> str:
        return "vscode"

    @property
    def config_path(self) -> Path:
        return Path.home() / ".config" / "Code" / "User" / "settings.json"

    def add_server(self, entry: RegistryEntry, compose_path: Path) -> None:
        """Add MCP server entry to VS Code settings.json.

        Deep-merges into ``mcp.servers.<name>`` without clobbering any other
        VS Code settings that may exist in the file.

        Entry format:

        .. code-block:: json

            {
              "mcp": {
                "servers": {
                  "<name>": {
                    "type": "stdio",
                    "command": "docker",
                    "args": ["compose", "-f", "<abs_compose_path>", "run", "--rm", "<name>"]
                  }
                }
              }
            }
        """
        config = self._read_config()
        if not isinstance(config, dict):
            config = {}

        server_entry: dict[str, Any] = {
            "type": "stdio",
            "command": "docker",
            "args": [
                "compose",
                "-f", str(compose_path.resolve()),
                "run",
                "--rm",
                entry.name,
            ],
        }
        _set_nested(config, ["mcp", "servers", entry.name], server_entry)
        self._write_config(config)

    def remove_server(self, name: str) -> None:
        """Remove MCP server entry from VS Code settings.json.

        Navigates to ``mcp.servers`` and pops the key.  Silently skips if the
        path does not exist.
        """
        config = self._read_config()
        if not isinstance(config, dict):
            return
        _pop_nested(config, ["mcp", "servers", name])
        self._write_config(config)
