#!/usr/bin/env python3
"""
MCP Container Manager
Manages Docker container lifecycle for MCP servers with lazy loading.
"""

import json
import subprocess
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sys


class ContainerManager:
    """Manages Docker containers for MCP servers."""

    def __init__(self, registry_path: str, on_container_change=None):
        """Initialize the container manager.

        Args:
            registry_path: Path to the MCP registry JSON file
            on_container_change: Optional callback function called when containers start/stop
        """
        self.registry_path = Path(registry_path).expanduser()
        self.registry = self._load_registry()
        self.activity_tracker: Dict[str, datetime] = {}
        self.running_containers: Dict[str, str] = {}  # server_name -> container_id
        self.on_container_change = on_container_change  # Callback for container lifecycle events

        # Build friendly name mapping for dot notation
        self.friendly_name_map: Dict[str, str] = {}  # friendly_name -> server_name
        self._build_friendly_name_map()

    def _load_registry(self) -> dict:
        """Load the MCP registry from JSON file."""
        try:
            with open(self.registry_path) as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Registry not found at {self.registry_path}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in registry: {e}", file=sys.stderr)
            sys.exit(1)

    def _build_friendly_name_map(self):
        """Build reverse mapping from friendly names to server names."""
        for server_name, config in self.registry["servers"].items():
            friendly_name = config.get("friendly_name")
            if friendly_name:
                if friendly_name in self.friendly_name_map:
                    print(f"Warning: Duplicate friendly_name '{friendly_name}' found, ignoring", file=sys.stderr)
                else:
                    self.friendly_name_map[friendly_name] = server_name

        if self.friendly_name_map:
            print(f"Friendly name mapping loaded: {self.friendly_name_map}", file=sys.stderr)

    def _parse_dot_notation(self, message: str) -> List[str]:
        """Parse dot notation (.servername) from message.

        Args:
            message: The message to parse

        Returns:
            List of friendly names found (e.g., ['deeplake', 'gemini', 'tableau'])
        """
        # Regex pattern to match .servername
        pattern = r'\.(\w+)'
        matches = re.findall(pattern, message)

        # Deduplicate while preserving order
        seen = set()
        friendly_names = []
        for name in matches:
            if name not in seen:
                seen.add(name)
                friendly_names.append(name)

        return friendly_names

    def _map_friendly_names(self, friendly_names: List[str]) -> List[str]:
        """Map friendly names to server names with validation.

        Args:
            friendly_names: List of friendly names from dot notation

        Returns:
            List of server names (registry keys)
        """
        server_names = []
        for friendly_name in friendly_names:
            server_name = self.friendly_name_map.get(friendly_name)
            if server_name:
                server_names.append(server_name)
                print(f"Dot notation '.{friendly_name}' mapped to server '{server_name}'", file=sys.stderr)
            else:
                print(f"Warning: Server '.{friendly_name}' not found in registry, ignoring", file=sys.stderr)

        return server_names

    def should_start_container(self, message: str) -> List[str]:
        """Check if message contains triggers for any server.

        Supports two activation mechanisms:
        1. Explicit dot notation: .servername (e.g., .deeplake .gemini)
        2. Implicit keyword triggers: Matches against server trigger lists

        Both mechanisms work together - dot notation ensures specific servers
        start, while keyword triggers add additional servers based on heuristics.

        Args:
            message: The message to check for triggers

        Returns:
            List of server names that should be started (union of explicit + implicit)
        """
        containers_to_start = []
        message_lower = message.lower()

        # 1. Check for explicit dot notation (.servername)
        friendly_names = self._parse_dot_notation(message)
        if friendly_names:
            explicit_servers = self._map_friendly_names(friendly_names)
            containers_to_start.extend(explicit_servers)
            print(f"Explicit servers requested via dot notation: {explicit_servers}", file=sys.stderr)

        # 2. Check for implicit keyword triggers
        for server_name, config in self.registry["servers"].items():
            # Skip if already in list from dot notation
            if server_name in containers_to_start:
                continue

            # Skip if already running
            if self.is_container_running(server_name):
                continue

            # Check for triggers
            for trigger in config.get("triggers", []):
                if trigger.lower() in message_lower:
                    containers_to_start.append(server_name)
                    print(f"Keyword trigger '{trigger}' matched server '{server_name}'", file=sys.stderr)
                    break

        return containers_to_start

    def is_container_running(self, server_name: str) -> bool:
        """Check if a container is currently running.

        Args:
            server_name: Name of the server

        Returns:
            True if container is running, False otherwise
        """
        config = self.registry["servers"].get(server_name)
        if not config:
            return False

        container_name = config["container_name"]

        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                check=True
            )
            return container_name in result.stdout
        except subprocess.CalledProcessError:
            return False

    def start_container(self, server_name: str) -> bool:
        """Start a Docker container for the specified server.

        Args:
            server_name: Name of the server to start

        Returns:
            True if started successfully, False otherwise
        """
        config = self.registry["servers"].get(server_name)
        if not config:
            print(f"Error: Server '{server_name}' not found in registry", file=sys.stderr)
            return False

        # Check if already running
        if self.is_container_running(server_name):
            print(f"Container for '{server_name}' is already running", file=sys.stderr)
            self.update_activity(server_name)
            return True

        container_name = config["container_name"]
        compose_file = config.get("compose_file")

        try:
            if compose_file:
                # Start via docker-compose
                print(f"Starting container '{container_name}' via docker-compose...", file=sys.stderr)
                subprocess.run(
                    ["docker", "compose", "-f", compose_file, "up", "-d"],
                    check=True,
                    capture_output=True
                )
            else:
                # Start via docker run
                print(f"Starting container '{container_name}' via docker run...", file=sys.stderr)
                subprocess.run(
                    ["docker", "start", container_name],
                    check=True,
                    capture_output=True
                )

            self.activity_tracker[server_name] = datetime.now()
            self.running_containers[server_name] = container_name
            print(f"✓ Container '{container_name}' started successfully", file=sys.stderr)

            # Notify proxy that tools list has changed
            if self.on_container_change:
                self.on_container_change()

            return True

        except subprocess.CalledProcessError as e:
            print(f"Error starting container '{container_name}': {e}", file=sys.stderr)
            return False

    def stop_container(self, server_name: str) -> bool:
        """Stop a running container.

        Args:
            server_name: Name of the server to stop

        Returns:
            True if stopped successfully, False otherwise
        """
        config = self.registry["servers"].get(server_name)
        if not config:
            return False

        container_name = config["container_name"]
        compose_file = config.get("compose_file")

        try:
            if compose_file:
                subprocess.run(
                    ["docker", "compose", "-f", compose_file, "down"],
                    check=True,
                    capture_output=True
                )
            else:
                subprocess.run(
                    ["docker", "stop", container_name],
                    check=True,
                    capture_output=True
                )

            if server_name in self.activity_tracker:
                del self.activity_tracker[server_name]
            if server_name in self.running_containers:
                del self.running_containers[server_name]

            print(f"✓ Container '{container_name}' stopped", file=sys.stderr)
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error stopping container '{container_name}': {e}", file=sys.stderr)
            return False

    def update_activity(self, server_name: str):
        """Update last activity timestamp for a server.

        Args:
            server_name: Name of the server
        """
        self.activity_tracker[server_name] = datetime.now()

    def cleanup_inactive(self):
        """Stop containers that have been inactive for too long."""
        now = datetime.now()
        servers_to_stop = []

        for server_name, config in self.registry["servers"].items():
            # Skip if auto-stop is disabled
            if not config.get("autoStop", True):
                continue

            # Skip if not running
            if not self.is_container_running(server_name):
                continue

            # Check inactivity
            if server_name not in self.activity_tracker:
                continue

            last_activity = self.activity_tracker[server_name]
            inactive_seconds = (now - last_activity).total_seconds()
            stop_delay = config.get("autoStopDelay", 300)

            if inactive_seconds > stop_delay:
                servers_to_stop.append(server_name)

        # Stop inactive containers
        for server_name in servers_to_stop:
            print(f"Stopping inactive container: {server_name}", file=sys.stderr)
            self.stop_container(server_name)

        # Notify proxy if any containers were stopped
        if servers_to_stop and self.on_container_change:
            self.on_container_change()

    def get_status(self) -> dict:
        """Get status of all containers.

        Returns:
            Dictionary with container status information
        """
        status = {
            "running": [],
            "stopped": [],
            "activity": {}
        }

        for server_name in self.registry["servers"].keys():
            if self.is_container_running(server_name):
                status["running"].append(server_name)
                if server_name in self.activity_tracker:
                    last_activity = self.activity_tracker[server_name]
                    inactive_seconds = (datetime.now() - last_activity).total_seconds()
                    status["activity"][server_name] = {
                        "last_activity": last_activity.isoformat(),
                        "inactive_seconds": inactive_seconds
                    }
            else:
                status["stopped"].append(server_name)

        return status


if __name__ == "__main__":
    # Test the container manager
    manager = ContainerManager("~/.claude/mcp-docker-registry.json")

    # Check status
    status = manager.get_status()
    print(json.dumps(status, indent=2))

    # Test trigger detection
    test_message = "I want to research machine learning in my saved articles"
    triggers = manager.should_start_container(test_message)
    print(f"\nTriggers found: {triggers}")

    # Test cleanup
    manager.cleanup_inactive()
