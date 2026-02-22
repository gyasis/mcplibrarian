"""Docker Compose config generator using Jinja2 templates."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from mcp_dockerize.detectors.base import ServerMetadata


class ComposeGenerator:
    """Generate docker-compose.yml and .env.example from Jinja2 templates.

    The generator renders ``docker-compose.yml.j2`` and ``env-example.j2``
    located in the package ``templates/`` directory into *config_dir*.

    Example usage::

        from pathlib import Path
        from mcp_dockerize.generators.compose import ComposeGenerator
        from mcp_dockerize.detectors.base import ServerMetadata

        metadata = ServerMetadata(
            name="my-server",
            runtime="python_uv",
            runtime_version="3.11",
            entry_point="server.py",
            package_manager="uv",
            env_vars=["API_KEY", "DATABASE_URL"],
            data_volumes=["/mnt/data"],
            deployment_pattern="volume_mounted",
        )
        generator = ComposeGenerator()
        compose_path = generator.generate(
            metadata=metadata,
            config_dir=Path("/tmp/my-server-config"),
            server_path=Path("/home/user/my-server"),
        )
    """

    def __init__(self) -> None:
        templates_dir = Path(__file__).parent.parent / "templates"
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(
        self,
        metadata: ServerMetadata,
        config_dir: Path,
        server_path: Path,
    ) -> Path:
        """Render docker-compose.yml and .env.example into *config_dir*.

        Also creates an empty ``.env`` file (if absent) so that the
        ``env_file: [.env]`` directive in docker-compose.yml resolves without
        error on first run.

        Args:
            metadata: Detected server metadata produced by any
                ``AbstractDetector`` implementation.
            config_dir: Directory that will receive the generated files.
                Created (including any missing parents) if it does not exist.
            server_path: Absolute path to the original server source tree.
                Kept as a parameter for forward-compatibility — not currently
                embedded in the compose output, but callers may need it.

        Returns:
            Absolute ``Path`` to the generated ``docker-compose.yml``.
        """
        config_dir.mkdir(parents=True, exist_ok=True)

        compose_path = self._render_compose(metadata, config_dir)
        self._render_env_example(metadata, config_dir)
        self._ensure_env_file(config_dir)

        return compose_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _render_compose(self, metadata: ServerMetadata, config_dir: Path) -> Path:
        """Render docker-compose.yml.j2 and write to config_dir."""
        volumes = [
            {
                "source": vol_path,
                "target": vol_path,  # mirror host path inside container
                "read_only": True,
            }
            for vol_path in metadata.data_volumes
        ]

        compose_tmpl = self._env.get_template("docker-compose.yml.j2")
        compose_content = compose_tmpl.render(
            service_name=metadata.name,
            build_context=".",
            dockerfile_path="Dockerfile",
            volumes=volumes,
            deployment_pattern=metadata.deployment_pattern,
        )

        compose_path = config_dir / "docker-compose.yml"
        compose_path.write_text(compose_content, encoding="utf-8")
        return compose_path

    def _render_env_example(self, metadata: ServerMetadata, config_dir: Path) -> None:
        """Render env-example.j2 and write to config_dir as .env.example."""
        env_vars_data = [
            {
                "name": var_name,
                "description": f"Required by {metadata.name}",
                "required": True,
                "example": "",
            }
            for var_name in metadata.env_vars
        ]

        env_tmpl = self._env.get_template("env-example.j2")
        env_content = env_tmpl.render(
            service_name=metadata.name,
            env_vars=env_vars_data,
        )

        (config_dir / ".env.example").write_text(env_content, encoding="utf-8")

    def _ensure_env_file(self, config_dir: Path) -> None:
        """Create an empty .env stub if one does not already exist.

        docker-compose resolves ``env_file: [.env]`` at start-up; the file
        must exist even when it is intentionally empty.
        """
        env_file = config_dir / ".env"
        if not env_file.exists():
            env_file.write_text(
                "# Fill in your values (copy from .env.example)\n",
                encoding="utf-8",
            )
