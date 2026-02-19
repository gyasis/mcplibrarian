"""Docker image builder using Docker SDK."""

import docker
from pathlib import Path
from typing import Optional

from ..detectors.python import ServerMetadata


class DockerBuildError(Exception):
    """Raised when Docker build fails."""
    pass


class DockerBuilder:
    """Build Docker images using Docker SDK for Python."""

    def __init__(self, verbose: bool = False):
        """Initialize builder with Docker SDK client.

        Args:
            verbose: Enable verbose output

        Raises:
            DockerBuildError: If Docker daemon is not accessible
        """
        try:
            self.client = docker.from_env()
            self.verbose = verbose
        except docker.errors.DockerException as e:
            raise DockerBuildError(
                f"Cannot connect to Docker daemon. Is Docker running?\n"
                f"Error: {e}"
            )

    def build_image(
        self,
        compose_dir: Path,
        metadata: ServerMetadata,
        tag: Optional[str] = None
    ) -> str:
        """Build Docker image from docker-compose.yml location.

        Args:
            compose_dir: Directory containing docker-compose.yml and Dockerfile
            metadata: Server metadata (for naming)
            tag: Optional custom tag (defaults to mcp-{name}:latest)

        Returns:
            Image ID of built image

        Raises:
            DockerBuildError: If build fails
        """
        # Validate inputs
        dockerfile_path = compose_dir / "Dockerfile"
        if not dockerfile_path.exists():
            raise DockerBuildError(
                f"Dockerfile not found at {dockerfile_path}. "
                f"Run generation first."
            )

        # Determine tag
        if tag is None:
            tag = f"mcp-{metadata.name}:latest"

        try:
            # Build image using Docker SDK
            if self.verbose:
                print(f"Building image: {tag}")
                print(f"Context: {compose_dir}")

            image, build_logs = self.client.images.build(
                path=str(compose_dir),
                tag=tag,
                rm=True,  # Remove intermediate containers
                forcerm=True,  # Always remove intermediate containers
                nocache=False,  # Use cache for faster builds
            )

            # Stream build logs
            if self.verbose:
                for log_entry in build_logs:
                    if 'stream' in log_entry:
                        print(log_entry['stream'], end='')
                    elif 'error' in log_entry:
                        raise DockerBuildError(log_entry['error'])

            return image.id

        except docker.errors.BuildError as e:
            raise DockerBuildError(
                f"Build failed:\n{self._format_build_error(e)}"
            )
        except docker.errors.APIError as e:
            raise DockerBuildError(f"Docker API error: {e}")

    def _format_build_error(self, error: docker.errors.BuildError) -> str:
        """Format build error for user-friendly output.

        Args:
            error: Docker build error

        Returns:
            Formatted error message
        """
        lines = []
        for log_entry in error.build_log:
            if 'stream' in log_entry:
                lines.append(log_entry['stream'].strip())
            elif 'error' in log_entry:
                lines.append(f"ERROR: {log_entry['error']}")

        return "\n".join(lines[-10:])  # Last 10 lines

    def image_exists(self, tag: str) -> bool:
        """Check if image with tag already exists.

        Args:
            tag: Image tag to check

        Returns:
            True if image exists
        """
        try:
            self.client.images.get(tag)
            return True
        except docker.errors.ImageNotFound:
            return False
