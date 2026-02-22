"""OpenAI Codex platform config integration (YAML + shell wrapper)."""

import shutil
import stat
from pathlib import Path
from typing import Any

import yaml

from mcp_dockerize.platforms.base import AbstractPlatform
from mcp_dockerize.registry.models import RegistryEntry


class CodexPlatform(AbstractPlatform):
    """Writes MCP server entries to OpenAI Codex's ``config.yaml``.

    Codex uses YAML for its config and a shell-wrapper script per tool.
    ``_read_config`` / ``_write_config`` are overridden for YAML I/O.

    ``add_server`` workflow:

    1. Generate ``~/.codex/tools/<name>.sh`` — a bash wrapper that invokes
       the server via ``docker compose run``.
    2. Make the wrapper executable (``chmod 0o755``).
    3. Append an entry to the ``tools`` list in ``~/.codex/config.yaml``.

    ``remove_server`` deletes the ``tools`` list entry *and* the ``.sh``
    wrapper file.
    """

    @property
    def platform_id(self) -> str:
        return "codex"

    @property
    def config_path(self) -> Path:
        return Path.home() / ".codex" / "config.yaml"

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
    # Helper
    # ------------------------------------------------------------------

    def _wrapper_path(self, name: str) -> Path:
        """Return the canonical path for the shell wrapper script."""
        return Path.home() / ".codex" / "tools" / f"{name}.sh"

    def _create_wrapper(self, name: str, compose_path: Path) -> Path:
        """Create (or overwrite) an executable bash wrapper for *name*.

        The wrapper passes through all positional arguments so that Codex can
        supply additional flags when invoking the tool.

        Returns the absolute path of the created wrapper.
        """
        wrapper_path = self._wrapper_path(name)
        wrapper_path.parent.mkdir(parents=True, exist_ok=True)

        abs_compose = str(compose_path.resolve())
        script_content = (
            "#!/bin/bash\n"
            f'docker compose -f "{abs_compose}" run --rm "{name}" "$@"\n'
        )
        wrapper_path.write_text(script_content)
        wrapper_path.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        return wrapper_path

    # ------------------------------------------------------------------
    # AbstractPlatform implementation
    # ------------------------------------------------------------------

    def add_server(self, entry: RegistryEntry, compose_path: Path) -> None:
        """Create a shell wrapper and register the tool in Codex config.

        Steps:

        1. Write ``~/.codex/tools/<name>.sh`` and ``chmod 0o755`` it.
        2. Load YAML config (default ``{}`` if missing).
        3. Ensure ``tools`` list exists; check for duplicate *name*.
        4. Append ``{name, type, script, description}`` entry.
        5. Write config back atomically.

        Skips silently if a tool with the same name already exists.
        """
        wrapper_path = self._create_wrapper(entry.name, compose_path)

        config = self._read_config()
        if not isinstance(config, dict):
            config = {}

        tools: list[dict] = config.setdefault("tools", [])

        # Check for duplicates by name — skip if already registered.
        for item in tools:
            if isinstance(item, dict) and item.get("name") == entry.name:
                return

        tools.append(
            {
                "name": entry.name,
                "type": "shell",
                "script": str(wrapper_path),
                "description": f"MCP server: {entry.name}",
            }
        )
        self._write_config(config)

    def remove_server(self, name: str) -> None:
        """Remove the tool entry from Codex config and delete its wrapper.

        Silently skips missing config or missing entry.  Always attempts to
        delete the ``.sh`` wrapper if it exists, regardless of whether a
        config entry was found.
        """
        config = self._read_config()
        if isinstance(config, dict) and "tools" in config:
            config["tools"] = [
                item
                for item in config["tools"]
                if not (isinstance(item, dict) and item.get("name") == name)
            ]
            self._write_config(config)

        # Always clean up the wrapper script.
        wrapper_path = self._wrapper_path(name)
        if wrapper_path.exists():
            wrapper_path.unlink()
