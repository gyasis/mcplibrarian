#!/usr/bin/env python3
"""
MCP Proxy - Intelligent MCP request router with automatic Docker container lifecycle management.

This proxy sits between Claude Code and MCP servers, automatically starting Docker containers
when conversation triggers are detected and stopping them after inactivity.

Usage:
    uv run /home/gyasis/claude-scripts/mcp-proxy.py

Configuration:
    Registry: ~/.claude/mcp-docker-registry.json

Architecture:
    Claude Code → mcp-proxy.py → Trigger Detection → Container Manager
                       ↓                                    ↓
                  MCP Protocol ← ← ← ← ← ← Docker Container (MCP Server)
                       ↓
                  Response → Claude Code
"""

import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional, List
import os

# Add claude-scripts to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp_container_manager import ContainerManager


class MCPProxy:
    """Intelligent MCP proxy with automatic container lifecycle management."""

    def __init__(self, registry_path: str):
        """Initialize the MCP proxy.

        Args:
            registry_path: Path to the MCP registry JSON file
        """
        # Initialize container manager with callback for container lifecycle events
        self.manager = ContainerManager(
            registry_path,
            on_container_change=self._send_tools_list_changed_notification
        )
        self.request_count = 0

        # Track which servers are handling which requests
        self.active_servers: Dict[str, str] = {}  # request_id -> server_name

        # Build tool-to-server mapping from manifests
        self.tool_to_server: Dict[str, str] = {}  # tool_name -> server_name
        self._build_tool_mapping()

        print("MCP Proxy initialized", file=sys.stderr)
        print(f"Registry loaded from: {registry_path}", file=sys.stderr)
        print(f"Tool mapping loaded: {len(self.tool_to_server)} tools from {len(self.manager.registry['servers'])} servers", file=sys.stderr)

    def _send_tools_list_changed_notification(self):
        """Send notification that tools list has changed.

        This triggers Claude Code to re-query tools/list, allowing dynamic
        tool loading/unloading based on container lifecycle.
        """
        notification = {
            "jsonrpc": "2.0",
            "method": "notifications/tools/list_changed"
        }
        sys.stdout.write(json.dumps(notification) + "\n")
        sys.stdout.flush()
        print("Sent tools/list_changed notification", file=sys.stderr)

    def _build_tool_mapping(self):
        """Build mapping from tool names to server names by reading manifests."""
        for server_name, config in self.manager.registry["servers"].items():
            manifest_path = config.get("manifest_path")

            if not manifest_path or not Path(manifest_path).exists():
                continue

            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)

                for tool in manifest.get("tools", []):
                    tool_name = tool.get("name")
                    if tool_name:
                        self.tool_to_server[tool_name] = server_name

            except Exception as e:
                print(f"Warning: Failed to load manifest for {server_name}: {e}", file=sys.stderr)

    def _detect_triggers(self, request: dict) -> List[str]:
        """Detect trigger keywords in an MCP request.

        Args:
            request: The JSON-RPC request

        Returns:
            List of server names that should be started
        """
        # Convert request to string for trigger detection
        request_str = json.dumps(request).lower()

        # Check for triggers
        return self.manager.should_start_container(request_str)

    def _forward_to_container(self, server_name: str, request: dict) -> Optional[dict]:
        """Forward MCP request to container using ephemeral run.

        Args:
            server_name: Name of the server to forward to
            request: The JSON-RPC request

        Returns:
            The JSON-RPC response from the container, or None on error
        """
        config = self.manager.registry["servers"].get(server_name)
        if not config:
            return None

        image = config.get("image")
        compose_file = config.get("compose_file")

        if not image:
            print(f"No image specified for {server_name}", file=sys.stderr)
            return None

        try:
            # MCP protocol requires initialize before any other request
            # Send both initialize and actual request in one stream
            initialize_request = {
                "jsonrpc": "2.0",
                "id": "init",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-docker-proxy",
                        "version": "0.1.0"
                    }
                }
            }

            # Build input stream: initialize + actual request (newline-delimited)
            input_stream = json.dumps(initialize_request) + "\n" + json.dumps(request) + "\n"

            # Build docker run command with same volumes/env as compose
            docker_args = [
                "docker", "run", "--rm", "-i",
                "--env-file", "/home/gyasis/Documents/code/hello-World/.env",
                "-v", "/home/gyasis/Documents/code/hello-World:/app:ro",
                "-v", "/media/gyasis/Drive 2/Deeplake_Storage/memory_lane_v4:/media/gyasis/Drive 2/Deeplake_Storage/memory_lane_v4:ro",
                image
            ]

            print(f"Running ephemeral container for {server_name}...", file=sys.stderr)

            result = subprocess.run(
                docker_args,
                input=input_stream,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                # Update activity tracker
                self.manager.update_activity(server_name)

                # Parse responses (we sent 2 requests, expect 2 responses)
                response_lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

                # The second response is for our actual request (first is initialize response)
                if len(response_lines) >= 2:
                    return json.loads(response_lines[1])
                elif len(response_lines) == 1:
                    # Maybe it only sent one response
                    return json.loads(response_lines[0])
                else:
                    print(f"No response from container", file=sys.stderr)
                    return None
            else:
                print(f"Error from container: {result.stderr}", file=sys.stderr)
                return None

        except subprocess.TimeoutExpired:
            print(f"Timeout running container", file=sys.stderr)
            return None
        except json.JSONDecodeError as e:
            print(f"Invalid JSON response: {e}", file=sys.stderr)
            print(f"Response was: {result.stdout}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"Error running container: {e}", file=sys.stderr)
            return None

    def _handle_initialize(self, request: dict) -> dict:
        """Handle MCP initialize request.

        Args:
            request: The initialize request

        Returns:
            Initialize response with proxy capabilities
        """
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "mcp-docker-proxy",
                    "version": "0.1.0"
                }
            }
        }

    def _handle_tools_list(self, request: dict) -> dict:
        """Handle tools/list request.

        Toolhost Pattern (Production-Proven):
        - Expose 1 polymorphic tool per server (~25 tokens each)
        - Each tool accepts natural language queries
        - Proxy routes queries to actual tools via keyword matching
        - Add 1 documentation tool for transparency

        This achieves 96-99% token savings vs exposing all tools.
        Pattern validated in: Momentum FHIR, MarkItDown, Elastic Path, Moncoder.

        Args:
            request: The tools/list request

        Returns:
            Tools list with polymorphic tools + documentation tool
        """
        toolhost_tools = []

        # 1. Create polymorphic tool for each server
        for server_name, config in self.manager.registry["servers"].items():
            friendly_name = config.get("friendly_name", server_name)
            description = config.get("description", f"{server_name} server")

            polymorphic_tool = {
                "name": f"{server_name.replace('-', '_')}_query",
                "description": f"Query {friendly_name} using natural language. {description}",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language query (e.g., 'search for X', 'find recent Y', 'get document Z')"
                        }
                    },
                    "required": ["query"]
                }
            }
            toolhost_tools.append(polymorphic_tool)
            print(f"Added polymorphic tool: {polymorphic_tool['name']}", file=sys.stderr)

        # 2. Add documentation tool for transparency
        doc_tool = {
            "name": "get_server_documentation",
            "description": "Get detailed capabilities and available operations for a specific MCP server",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "server_name": {
                        "type": "string",
                        "enum": list(self.manager.registry["servers"].keys()),
                        "description": "Server to get documentation for"
                    }
                },
                "required": ["server_name"]
            }
        }
        toolhost_tools.append(doc_tool)

        server_count = len(self.manager.registry["servers"])
        print(f"🎯 Toolhost Pattern: Returning {len(toolhost_tools)} tools ({server_count} polymorphic + 1 doc)", file=sys.stderr)
        print(f"   Token savings: ~96% vs Lazy Init (exposing {server_count} vs {server_count * 6} tools)", file=sys.stderr)

        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {
                "tools": toolhost_tools
            }
        }

    def _route_polymorphic_call(self, server_name: str, query: str) -> dict:
        """Route natural language query to specific tool call.

        Implements keyword matching router (80% accuracy per research).
        For deeplake-rag server, routes to appropriate retrieval tools.

        Args:
            server_name: Server to route query to
            query: Natural language query from user

        Returns:
            Tool call result
        """
        query_lower = query.lower()
        tool_name = None
        params = {}

        # Keyword-based routing for deeplake-rag
        if server_name == "deeplake-rag":
            if "search" in query_lower or "find" in query_lower or "retrieve" in query_lower:
                tool_name = "retrieve_context"
                params = {"query": query, "n_results": 5}
            elif "recent" in query_lower:
                tool_name = "search_recent"
                params = {"query": query}
            elif "summary" in query_lower:
                tool_name = "get_summary"
                params = {"query": query}
            elif "document" in query_lower and "get" in query_lower:
                tool_name = "get_document"
                params = {"query": query}
            elif "fuzzy" in query_lower or "title" in query_lower:
                tool_name = "get_fuzzy_matching_titles"
                params = {"query": query}
            else:
                # Default to general context retrieval
                tool_name = "retrieve_context"
                params = {"query": query, "n_results": 5}

        print(f"🔀 Routing '{query}' → {server_name}.{tool_name}", file=sys.stderr)

        # Start container if not running
        if not self.manager.is_container_running(server_name):
            print(f"Starting container for {server_name}...", file=sys.stderr)
            self.manager.start_container(server_name)

        # Update activity
        self.manager.update_activity(server_name)

        # Call actual tool via container
        return self._call_container_tool(server_name, tool_name, params)

    def _call_container_tool(self, server_name: str, tool_name: str, params: dict) -> dict:
        """Execute a specific tool on a container.

        Constructs a JSON-RPC tools/call request and forwards to container.

        Args:
            server_name: Name of the server
            tool_name: Name of the tool to call
            params: Tool parameters

        Returns:
            Tool execution result
        """
        # Construct JSON-RPC tools/call request
        tool_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        }

        print(f"📞 Calling {server_name}.{tool_name} with params: {params}", file=sys.stderr)

        # Forward to container
        response = self._forward_to_container(server_name, tool_request)

        if not response:
            raise Exception(f"Failed to get response from {server_name}")

        # Extract result or error
        if "result" in response:
            return response["result"]
        elif "error" in response:
            raise Exception(f"Tool call failed: {response['error']}")
        else:
            raise Exception(f"Invalid response from {server_name}: {response}")

    def _handle_get_server_documentation(self, server_name: str) -> dict:
        """Return detailed tool capabilities for a server.

        Provides transparency by exposing actual tool schemas when requested.
        Implements best practice from Toolhost pattern research.

        Args:
            server_name: Server to get documentation for

        Returns:
            Formatted documentation with tool schemas
        """
        config = self.manager.registry["servers"].get(server_name)
        if not config:
            return {
                "error": f"Unknown server: {server_name}",
                "available_servers": list(self.manager.registry["servers"].keys())
            }

        manifest_path = config.get("manifest_path")
        if not manifest_path or not Path(manifest_path).exists():
            return {
                "error": f"No manifest found for {server_name}",
                "manifest_path": manifest_path
            }

        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            tools = manifest.get("tools", [])
            doc_text = f"# {server_name} Server Documentation\n\n"
            doc_text += f"**Friendly Name**: {config.get('friendly_name', server_name)}\n"
            doc_text += f"**Description**: {config.get('description', 'N/A')}\n"
            doc_text += f"**Category**: {config.get('category', 'N/A')}\n"
            doc_text += f"**Tool Count**: {len(tools)}\n\n"
            doc_text += "## Available Tools\n\n"

            for tool in tools:
                doc_text += f"### `{tool['name']}`\n"
                doc_text += f"{tool.get('description', 'No description')}\n\n"
                doc_text += f"**Schema**:\n```json\n{json.dumps(tool.get('inputSchema', {}), indent=2)}\n```\n\n"

            return {"documentation": doc_text, "tools": tools}

        except Exception as e:
            return {"error": f"Failed to load manifest: {str(e)}"}

    def _handle_meta_tool_call(self, request: dict) -> Optional[dict]:
        """Handle meta-tool calls (load_tools or check_status).

        Args:
            request: The tools/call request for a meta-tool

        Returns:
            Response with actual tools or status, or None if not a meta-tool
        """
        params = request.get("params", {})
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        # Find which server this meta-tool belongs to
        server_name = None
        for name, config in self.manager.registry["servers"].items():
            if config.get("meta_tool_name") == tool_name:
                server_name = name
                break

        if not server_name:
            # Not a meta-tool call
            return None

        print(f"Meta-tool call detected: {tool_name} for server {server_name}", file=sys.stderr)

        action = arguments.get("action", "load_tools")

        if action == "check_status":
            # Return container status
            status = self.manager.get_status()
            is_running = server_name in status["running"]

            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "server": server_name,
                            "status": "running" if is_running else "stopped",
                            "tools_loaded": is_running
                        }, indent=2)
                    }]
                }
            }

        elif action == "load_tools":
            # Start container if not running
            if not self.manager.is_container_running(server_name):
                print(f"Starting container for {server_name} (triggered by meta-tool)", file=sys.stderr)
                if self.manager.start_container(server_name):
                    print(f"✓ Container started, notification sent", file=sys.stderr)
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"Failed to start container for {server_name}"
                        }
                    }

            # Load actual tools from manifest
            config = self.manager.registry["servers"][server_name]
            manifest_path = config.get("manifest_path")

            if not manifest_path or not Path(manifest_path).exists():
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32603,
                        "message": f"Manifest not found for {server_name} at {manifest_path}"
                    }
                }

            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)

                tools = manifest.get("tools", [])
                print(f"Loaded {len(tools)} tools from manifest for {server_name}", file=sys.stderr)

                # Return confirmation - real tools now available via notification
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": f"✅ Enabled {len(tools)} {config.get('category', '')} tools from {server_name}\n\n"
                                   f"Available tools: {', '.join(t['name'] for t in tools)}\n\n"
                                   f"Tools are now ready to use."
                        }]
                    }
                }

            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32603,
                        "message": f"Error loading manifest: {str(e)}"
                    }
                }

        return None

    def process_request(self, request: dict) -> Optional[dict]:
        """Process a single MCP request.

        Args:
            request: The JSON-RPC request

        Returns:
            The JSON-RPC response, or None to pass through
        """
        self.request_count += 1
        method = request.get("method", "")

        # Handle initialize specially
        if method == "initialize":
            return self._handle_initialize(request)

        # Handle tools/list by returning meta-tools (Switchboard pattern)
        if method == "tools/list":
            return self._handle_tools_list(request)

        # Handle tools/call - Toolhost pattern routing
        if method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            # 1. Check for get_server_documentation calls
            if tool_name == "get_server_documentation":
                server_name = arguments.get("server_name")
                print(f"📖 Documentation request for {server_name}", file=sys.stderr)
                doc_result = self._handle_get_server_documentation(server_name)

                if "error" in doc_result:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": doc_result["error"]
                        }
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {
                            "content": [{
                                "type": "text",
                                "text": doc_result["documentation"]
                            }]
                        }
                    }

            # 2. Check for polymorphic tool calls (server_name_query pattern)
            if tool_name.endswith("_query"):
                # Extract server name from tool name (e.g., deeplake_rag_query → deeplake-rag)
                server_name = tool_name.replace("_query", "").replace("_", "-")
                query = arguments.get("query", "")

                print(f"🎯 Polymorphic call: {tool_name} with query '{query}'", file=sys.stderr)

                # Route query to appropriate tool
                try:
                    result = self._route_polymorphic_call(server_name, query)
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": result
                    }
                except Exception as e:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"Polymorphic routing failed: {str(e)}"
                        }
                    }

            # 3. Legacy: Check for meta-tool calls (for backwards compatibility)
            meta_response = self._handle_meta_tool_call(request)
            if meta_response:
                return meta_response

            # 4. Legacy: Direct tool calls (if tool_to_server mapping exists)
            if tool_name in self.tool_to_server:
                server_name = self.tool_to_server[tool_name]
                print(f"Legacy tool call: '{tool_name}' → server '{server_name}'", file=sys.stderr)

                response = self._forward_to_container(server_name, request)
                if response:
                    return response
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"Failed to execute tool on server {server_name}"
                        }
                    }

        # Detect triggers in request (for other methods)
        triggered_servers = self._detect_triggers(request)

        if triggered_servers:
            print(f"Triggers detected: {triggered_servers}", file=sys.stderr)

            # Start all triggered containers
            for server_name in triggered_servers:
                if self.manager.start_container(server_name):
                    print(f"Started container: {server_name}", file=sys.stderr)
                else:
                    print(f"Failed to start container: {server_name}", file=sys.stderr)

        # If we have active containers, try to forward the request
        running_servers = self.manager.get_status()["running"]

        if running_servers:
            # For now, forward to the first running server
            # TODO: Implement smarter routing based on tool availability
            server_name = running_servers[0]
            response = self._forward_to_container(server_name, request)
            if response:
                return response

        # If no containers or forwarding failed, pass through
        return None

    def run(self):
        """Main event loop - read from stdin, process, write to stdout."""
        print("MCP Proxy running - listening for requests on stdin", file=sys.stderr)

        try:
            while True:
                # Read JSON-RPC request from stdin
                line = sys.stdin.readline()

                if not line:
                    # EOF - exit gracefully
                    print("Received EOF, shutting down", file=sys.stderr)
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    # Parse JSON-RPC request
                    request = json.loads(line)

                    # Process the request
                    response = self.process_request(request)

                    if response:
                        # Send response to stdout
                        sys.stdout.write(json.dumps(response) + "\n")
                        sys.stdout.flush()
                    else:
                        # Pass through - echo the original request
                        # (This allows other MCP servers to handle it)
                        sys.stdout.write(line + "\n")
                        sys.stdout.flush()

                except json.JSONDecodeError as e:
                    print(f"Invalid JSON: {e}", file=sys.stderr)
                    # Pass through non-JSON lines
                    sys.stdout.write(line + "\n")
                    sys.stdout.flush()

                except Exception as e:
                    print(f"Error processing request: {e}", file=sys.stderr)
                    # Send error response
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id") if 'request' in locals() else None,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()

        finally:
            # Cleanup on exit
            print("Cleaning up inactive containers...", file=sys.stderr)
            self.manager.cleanup_inactive()
            print(f"Proxy shutting down. Processed {self.request_count} requests.", file=sys.stderr)


def main():
    """Entry point for the MCP proxy."""
    # Get registry path from environment or use default
    registry_path = os.environ.get(
        "MCP_REGISTRY",
        str(Path.home() / ".claude" / "mcp-docker-registry.json")
    )

    # Create and run proxy
    proxy = MCPProxy(registry_path)
    proxy.run()


if __name__ == "__main__":
    main()
