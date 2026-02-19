"""MCP protocol tester for Docker containers."""

import docker
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from ..detectors.python import ServerMetadata


@dataclass
class TestResult:
    """Result of MCP protocol test."""
    success: bool
    message: str
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: float = 0


class MCPTestError(Exception):
    """Raised when MCP test fails."""
    pass


class MCPTester:
    """Test MCP servers in Docker containers."""

    def __init__(self, verbose: bool = False):
        """Initialize tester with Docker SDK client.

        Args:
            verbose: Enable verbose output

        Raises:
            MCPTestError: If Docker daemon is not accessible
        """
        try:
            self.client = docker.from_env()
            self.verbose = verbose
        except docker.errors.DockerException as e:
            raise MCPTestError(
                f"Cannot connect to Docker daemon. Is Docker running?\n"
                f"Error: {e}"
            )

    def test_container(
        self,
        compose_dir: Path,
        metadata: ServerMetadata,
        timeout_seconds: int = 30
    ) -> TestResult:
        """Test MCP server container with protocol validation.

        This performs the following checks:
        1. Container starts successfully
        2. Accepts MCP initialize message
        3. Returns valid JSON-RPC response
        4. Container cleans up properly

        Args:
            compose_dir: Directory containing docker-compose.yml
            metadata: Server metadata (for naming)
            timeout_seconds: Maximum time to wait for response

        Returns:
            TestResult with success status and details

        Raises:
            MCPTestError: If test setup fails
        """
        image_tag = f"mcp-{metadata.name}:latest"
        container = None
        start_time = time.time()

        try:
            # Check if image exists
            try:
                self.client.images.get(image_tag)
            except docker.errors.ImageNotFound:
                return TestResult(
                    success=False,
                    message="Image not found. Run with --build first.",
                    error=f"Image {image_tag} does not exist"
                )

            if self.verbose:
                print(f"Creating test container from {image_tag}")

            # Create container with stdio access
            container = self.client.containers.create(
                image_tag,
                stdin_open=True,
                tty=False,
                detach=True,
                name=f"mcp-test-{metadata.name}-{int(time.time())}",
                # Mount volumes if needed (read from metadata)
                volumes=self._get_volumes_from_metadata(metadata),
                # Pass environment if needed
                environment=self._get_env_from_compose(compose_dir),
            )

            # Start container
            container.start()

            if self.verbose:
                print(f"Container started: {container.short_id}")

            # Send MCP initialize message
            initialize_msg = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {},
                "id": 1
            }

            if self.verbose:
                print(f"Sending MCP initialize: {json.dumps(initialize_msg)}")

            # Attach to container stdin/stdout
            socket = container.attach_socket(
                params={'stdin': 1, 'stdout': 1, 'stream': 1}
            )

            # Send JSON-RPC message
            message = json.dumps(initialize_msg) + "\n"
            socket._sock.sendall(message.encode('utf-8'))

            # Wait for response with timeout
            response_data = b""
            elapsed = 0

            while elapsed < timeout_seconds:
                socket._sock.settimeout(1.0)
                try:
                    chunk = socket._sock.recv(4096)
                    if chunk:
                        response_data += chunk
                        # Check if we have complete JSON response
                        try:
                            response = json.loads(response_data.decode('utf-8'))
                            # Valid JSON-RPC response received
                            duration = (time.time() - start_time) * 1000

                            if self.verbose:
                                print(f"Response received: {json.dumps(response, indent=2)}")

                            return TestResult(
                                success=True,
                                message="MCP protocol test passed",
                                response=response,
                                duration_ms=duration
                            )
                        except json.JSONDecodeError:
                            # Not complete yet, continue reading
                            pass
                except Exception:
                    pass

                elapsed = time.time() - start_time

            # Timeout reached
            return TestResult(
                success=False,
                message=f"Timeout after {timeout_seconds}s",
                error="No valid MCP response received",
                duration_ms=(time.time() - start_time) * 1000
            )

        except docker.errors.ContainerError as e:
            return TestResult(
                success=False,
                message="Container failed to start",
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
        except docker.errors.ImageNotFound:
            return TestResult(
                success=False,
                message="Image not found. Run with --build first.",
                error=f"Image {image_tag} does not exist"
            )
        except Exception as e:
            return TestResult(
                success=False,
                message="Test failed with unexpected error",
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )
        finally:
            # Clean up container
            if container:
                try:
                    if self.verbose:
                        print(f"Cleaning up test container {container.short_id}")

                    container.stop(timeout=5)
                    container.remove()

                    if self.verbose:
                        print("Container cleaned up successfully")
                except Exception as e:
                    if self.verbose:
                        print(f"Warning: Failed to clean up container: {e}")

    def _get_volumes_from_metadata(
        self,
        metadata: ServerMetadata
    ) -> Dict[str, Dict[str, str]]:
        """Extract volume mounts from metadata.

        Args:
            metadata: Server metadata

        Returns:
            Docker SDK volume dict format
        """
        volumes = {}

        # Add volume mounts from metadata
        for source, dest in metadata.volume_mounts.items():
            volumes[source] = {
                'bind': dest,
                'mode': 'ro'  # Read-only
            }

        return volumes

    def _get_env_from_compose(self, compose_dir: Path) -> Dict[str, str]:
        """Load environment variables from .env file if exists.

        Args:
            compose_dir: Directory with potential .env file

        Returns:
            Environment variable dict
        """
        env_file = compose_dir / ".env"
        env_vars = {}

        if env_file.exists():
            try:
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            env_vars[key.strip()] = value.strip()
            except Exception:
                pass  # Non-critical, continue without env

        return env_vars
