#!/usr/bin/env python3
"""
MCP Dockerize - Semi-Automatic MCP Server Wrapper
Automatically wraps existing MCP servers in Docker containers.

Usage:
    python mcp-dockerize.py <server_path> [options]
    python mcp-dockerize.py --npm <package_name> [options]
    python mcp-dockerize.py --git <repo_url> [options]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class MCPDockerizer:
    """Automatically dockerize MCP servers."""

    def __init__(self, output_dir: str = "./mcp-dockerize/docker-configs"):
        self.output_dir = Path(output_dir)
        self.registry_path = Path.home() / ".claude" / "mcp-docker-registry.json"
        self.manifests_dir = Path.home() / ".claude" / "mcp-manifests"

    # =====================================================================
    # PHASE 1: DISCOVERY
    # =====================================================================

    def discover_server(self, server_path: str) -> Dict:
        """Analyze existing MCP server and extract metadata.

        Returns:
            Dict with server metadata: type, entry_point, dependencies, etc.
        """
        server_path = Path(server_path).resolve()

        print(f"🔍 Discovering MCP server at: {server_path}")

        metadata = {
            "name": server_path.name,
            "path": str(server_path),
            "type": self._detect_server_type(server_path),
            "entry_point": None,
            "dependencies": {},
            "tools": [],
            "required_files": [],
            "env_vars": []
        }

        # Detect server type and entry point
        if metadata["type"] == "python":
            metadata["entry_point"] = self._find_python_entry_point(server_path)
            metadata["dependencies"] = self._parse_python_dependencies(server_path)
            metadata["env_vars"] = self._detect_env_vars(server_path, ["*.py"])
        elif metadata["type"] == "node":
            metadata["entry_point"] = self._find_node_entry_point(server_path)
            metadata["dependencies"] = self._parse_node_dependencies(server_path)
            metadata["env_vars"] = self._detect_env_vars(server_path, ["*.js", "*.ts"])

        # Extract tool schemas by running server
        metadata["tools"] = self._extract_tools(metadata)

        # Detect required files/volumes
        metadata["required_files"] = self._detect_required_files(server_path)

        print(f"✓ Discovered {metadata['type']} server with {len(metadata['tools'])} tools")
        return metadata

    def _detect_server_type(self, server_path: Path) -> str:
        """Detect if server is Python, Node.js, or other."""
        if (server_path / "pyproject.toml").exists() or \
           (server_path / "requirements.txt").exists() or \
           (server_path / "setup.py").exists():
            return "python"
        elif (server_path / "package.json").exists():
            return "node"
        else:
            # Try to detect from files
            py_files = list(server_path.glob("**/*.py"))
            js_files = list(server_path.glob("**/*.js")) + list(server_path.glob("**/*.ts"))

            if py_files and not js_files:
                return "python"
            elif js_files and not py_files:
                return "node"
            else:
                raise ValueError(f"Cannot determine server type for {server_path}")

    def _find_python_entry_point(self, server_path: Path) -> str:
        """Find Python entry point (main script or module)."""
        # Check pyproject.toml
        pyproject = server_path / "pyproject.toml"
        if pyproject.exists():
            import tomllib
            with open(pyproject, "rb") as f:
                config = tomllib.load(f)
                scripts = config.get("project", {}).get("scripts", {})
                if scripts:
                    # Return first script entry point
                    entry = list(scripts.values())[0]
                    return entry

        # Check for __main__.py
        main_py = server_path / "__main__.py"
        if main_py.exists():
            return "python -m ."

        # Check for server.py, main.py, index.py
        for name in ["server.py", "main.py", "index.py"]:
            if (server_path / name).exists():
                return f"python {name}"

        # Look for any .py file with MCP server patterns
        for py_file in server_path.glob("*.py"):
            with open(py_file) as f:
                content = f.read()
                if "mcp.server" in content or "stdio_server" in content:
                    return f"python {py_file.name}"

        raise ValueError(f"Cannot find Python entry point in {server_path}")

    def _find_node_entry_point(self, server_path: Path) -> str:
        """Find Node.js entry point from package.json."""
        package_json = server_path / "package.json"
        if not package_json.exists():
            raise ValueError(f"No package.json found in {server_path}")

        with open(package_json) as f:
            config = json.load(f)

            # Check bin entry
            if "bin" in config:
                bin_entry = config["bin"]
                if isinstance(bin_entry, dict):
                    # Take first bin entry
                    bin_script = list(bin_entry.values())[0]
                else:
                    bin_script = bin_entry
                return f"node {bin_script}"

            # Check main
            if "main" in config:
                return f"node {config['main']}"

            # Check scripts.start
            if "scripts" in config and "start" in config["scripts"]:
                return config["scripts"]["start"]

        raise ValueError(f"Cannot find Node.js entry point in {server_path}")

    def _parse_python_dependencies(self, server_path: Path) -> Dict:
        """Parse Python dependencies from pyproject.toml or requirements.txt."""
        deps = {}

        # Try pyproject.toml
        pyproject = server_path / "pyproject.toml"
        if pyproject.exists():
            import tomllib
            with open(pyproject, "rb") as f:
                config = tomllib.load(f)
                deps = config.get("project", {}).get("dependencies", [])
                return {"dependencies": deps}

        # Try requirements.txt
        requirements = server_path / "requirements.txt"
        if requirements.exists():
            with open(requirements) as f:
                deps = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            return {"dependencies": deps}

        return {}

    def _parse_node_dependencies(self, server_path: Path) -> Dict:
        """Parse Node.js dependencies from package.json."""
        package_json = server_path / "package.json"
        if not package_json.exists():
            return {}

        with open(package_json) as f:
            config = json.load(f)
            return {
                "dependencies": config.get("dependencies", {}),
                "devDependencies": config.get("devDependencies", {})
            }

    def _detect_env_vars(self, server_path: Path, patterns: List[str]) -> List[str]:
        """Detect environment variables from source code."""
        env_vars = set()

        for pattern in patterns:
            for file_path in server_path.glob(f"**/{pattern}"):
                try:
                    with open(file_path) as f:
                        content = f.read()
                        # Match os.getenv("VAR"), process.env.VAR, etc.
                        matches = re.findall(r'(?:os\.getenv|process\.env)\[?["\'](\w+)["\']', content)
                        env_vars.update(matches)
                except:
                    continue

        return sorted(list(env_vars))

    def _extract_tools(self, metadata: Dict) -> List[Dict]:
        """Extract tool schemas by running MCP server's tools/list."""
        print("📋 Extracting tool schemas...")

        server_path = Path(metadata["path"])
        entry_point = metadata["entry_point"]

        if not entry_point:
            return []

        try:
            # Build command based on server type
            if metadata["type"] == "python":
                # Use uv run for Python servers
                cmd = ["uv", "run", "--quiet"] + entry_point.split()
            else:
                # Direct execution for Node.js
                cmd = entry_point.split()

            # Send MCP initialize + tools/list
            mcp_requests = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "mcp-dockerize", "version": "1.0"}
                }
            }) + "\n" + json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }) + "\n"

            # Run server with requests
            result = subprocess.run(
                cmd,
                input=mcp_requests,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=server_path
            )

            # Parse JSON-RPC responses
            tools = []
            for line in result.stdout.split("\n"):
                if not line.strip():
                    continue
                try:
                    response = json.loads(line)
                    if "result" in response and "tools" in response["result"]:
                        tools = response["result"]["tools"]
                        break
                except json.JSONDecodeError:
                    continue

            print(f"✓ Extracted {len(tools)} tool schemas")
            return tools

        except subprocess.TimeoutExpired:
            print("⚠️ Warning: Server timed out during tool extraction")
            return []
        except Exception as e:
            print(f"⚠️ Warning: Could not extract tools: {e}")
            return []

    def _detect_required_files(self, server_path: Path) -> List[str]:
        """Detect files that need to be mounted as volumes."""
        required = []

        # Common data directories
        for dir_name in ["data", "db", "storage", "cache"]:
            if (server_path / dir_name).exists():
                required.append(str(server_path / dir_name))

        # Config files
        for file_name in [".env", "config.json", "config.yaml"]:
            if (server_path / file_name).exists():
                required.append(str(server_path / file_name))

        return required

    # =====================================================================
    # PHASE 2: DOCKER GENERATION
    # =====================================================================

    def generate_dockerfile(self, metadata: Dict) -> str:
        """Generate Dockerfile for the MCP server."""
        print("🐳 Generating Dockerfile...")

        if metadata["type"] == "python":
            return self._generate_python_dockerfile(metadata)
        elif metadata["type"] == "node":
            return self._generate_node_dockerfile(metadata)
        else:
            raise ValueError(f"Unsupported server type: {metadata['type']}")

    def _generate_python_dockerfile(self, metadata: Dict) -> str:
        """Generate Dockerfile for Python MCP server."""
        server_path = Path(metadata["path"])

        dockerfile = f"""# Auto-generated Dockerfile for {metadata['name']}
FROM python:3.11-slim

WORKDIR /app

# Install UV for Python package management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml* requirements.txt* ./

# Install dependencies
RUN if [ -f pyproject.toml ]; then \\
        uv pip install --system -e .; \\
    elif [ -f requirements.txt ]; then \\
        uv pip install --system -r requirements.txt; \\
    fi

# Copy application code
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=1

# Entry point
CMD {json.dumps(metadata["entry_point"].split())}
"""
        return dockerfile

    def _generate_node_dockerfile(self, metadata: Dict) -> str:
        """Generate Dockerfile for Node.js MCP server."""
        dockerfile = f"""# Auto-generated Dockerfile for {metadata['name']}
FROM node:20-slim

WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Entry point
CMD {json.dumps(metadata["entry_point"].split())}
"""
        return dockerfile

    def generate_compose(self, metadata: Dict) -> str:
        """Generate docker-compose.yml for the MCP server."""
        print("📦 Generating docker-compose.yml...")

        server_name = metadata["name"].replace("_", "-").lower()
        container_name = f"mcp-{server_name}"

        # Build volume mounts
        volumes = []
        for file_path in metadata["required_files"]:
            volumes.append(f"      - {file_path}:{file_path}:ro")

        volumes_str = "\n".join(volumes) if volumes else "      # No volumes required"

        # Build environment variables
        env_vars = []
        for env_var in metadata["env_vars"]:
            env_vars.append(f"      {env_var}: ${{{env_var}}}")

        env_str = "\n".join(env_vars) if env_vars else "      # No environment variables"

        compose = f"""# Auto-generated docker-compose.yml for {metadata['name']}
version: '3.8'

services:
  {server_name}:
    build: .
    container_name: {container_name}
    stdin_open: true
    tty: true
    volumes:
{volumes_str}
    environment:
{env_str}
"""
        return compose

    # =====================================================================
    # PHASE 3: REGISTRY INTEGRATION
    # =====================================================================

    def generate_registry_entry(self, metadata: Dict) -> Dict:
        """Generate entry for mcp-docker-registry.json."""
        print("📝 Generating registry entry...")

        server_name = metadata["name"].replace("_", "-").lower()
        friendly_name = server_name.replace("-", "")
        container_name = f"mcp-{server_name}"

        # Auto-suggest trigger keywords from tool names
        triggers = self._suggest_triggers(metadata)

        output_path = self.output_dir / server_name

        entry = {
            "friendly_name": friendly_name,
            "image": f"{server_name}-{server_name}:latest",
            "container_name": container_name,
            "compose_file": str(output_path / "docker-compose.yml"),
            "category": "auto-generated",
            "meta_tool_name": f"use_{friendly_name}_tools",
            "manifest_path": str(self.manifests_dir / f"{server_name}.json"),
            "triggers": triggers,
            "autoStop": True,
            "autoStopDelay": 300,
            "tokenCost": len(metadata["tools"]) * 500,  # Rough estimate
            "actualToolCount": len(metadata["tools"]),
            "description": f"Auto-dockerized {metadata['name']} MCP server"
        }

        return {server_name: entry}

    def _suggest_triggers(self, metadata: Dict) -> List[str]:
        """Auto-suggest keyword triggers from tool names and descriptions."""
        triggers = set()

        # Add server name variations
        server_name = metadata["name"].lower()
        triggers.add(server_name)
        triggers.add(server_name.replace("-", " "))
        triggers.add(server_name.replace("_", " "))

        # Extract keywords from tool names
        for tool in metadata["tools"]:
            tool_name = tool["name"]
            # Split camelCase and snake_case
            words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', tool_name)
            triggers.update(word.lower() for word in words if len(word) > 3)

        # Limit to top 10 most relevant
        return sorted(list(triggers))[:10]

    def generate_manifest(self, metadata: Dict) -> Dict:
        """Generate manifest JSON with tool schemas."""
        print("📄 Generating manifest...")

        manifest = {
            "name": metadata["name"],
            "version": "1.0.0",
            "type": metadata["type"],
            "tools": metadata["tools"]
        }

        return manifest

    def generate_routing_rules(self, metadata: Dict) -> str:
        """Generate Python code for routing rules."""
        print("🔀 Generating routing rules...")

        server_name = metadata["name"].replace("_", "-").lower()

        # Build routing rules from tool names
        rules = []
        for tool in metadata["tools"]:
            tool_name = tool["name"]
            description = tool.get("description", "")

            # Extract keywords from tool name
            keywords = self._extract_routing_keywords(tool_name, description)

            if keywords:
                keyword_checks = " or ".join(f'"{kw}" in query_lower' for kw in keywords[:3])
                rules.append(f"""
        # Route to {tool_name}
        if {keyword_checks}:
            tool_name = "{tool_name}"
            params = {{"query": query}}""")

        rules_str = "\n".join(rules)

        routing_code = f"""
    # Auto-generated routing rules for {server_name}
    if server_name == "{server_name}":
{rules_str}

        # Default fallback
        else:
            tool_name = "{metadata['tools'][0]['name'] if metadata['tools'] else 'unknown'}"
            params = {{"query": query}}
"""

        return routing_code

    def _extract_routing_keywords(self, tool_name: str, description: str) -> List[str]:
        """Extract routing keywords from tool name and description."""
        keywords = set()

        # Split camelCase/snake_case tool name
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', tool_name.replace("_", " "))
        keywords.update(word.lower() for word in words if len(word) > 3)

        # Extract from description (common action verbs)
        action_verbs = ["search", "find", "get", "list", "create", "update", "delete", "query"]
        for verb in action_verbs:
            if verb in description.lower():
                keywords.add(verb)

        return list(keywords)[:5]

    # =====================================================================
    # PHASE 4: VALIDATION
    # =====================================================================

    def validate_container(self, metadata: Dict, output_path: Path) -> bool:
        """Test that container builds and MCP protocol works."""
        print("✅ Validating container...")

        server_name = metadata["name"].replace("_", "-").lower()

        try:
            # Build container
            print("  Building Docker image...")
            subprocess.run(
                ["docker", "compose", "build"],
                cwd=output_path,
                check=True,
                capture_output=True
            )

            # Test MCP handshake
            print("  Testing MCP protocol handshake...")
            result = subprocess.run(
                ["docker", "compose", "run", "--rm", server_name],
                input='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n',
                capture_output=True,
                text=True,
                timeout=10,
                cwd=output_path
            )

            # Check for valid JSON-RPC response
            for line in result.stdout.split("\n"):
                if "jsonrpc" in line and "result" in line:
                    print("  ✓ Container validated successfully!")
                    return True

            print("  ⚠️ Warning: Could not validate MCP protocol")
            return False

        except subprocess.CalledProcessError as e:
            print(f"  ❌ Build failed: {e}")
            return False
        except subprocess.TimeoutExpired:
            print("  ⚠️ Warning: Container validation timed out")
            return False

    # =====================================================================
    # MAIN WORKFLOW
    # =====================================================================

    def dockerize(self, server_path: str, validate: bool = True) -> Dict:
        """Complete dockerization workflow."""
        print("=" * 60)
        print("MCP DOCKERIZE - Automatic MCP Server Wrapper")
        print("=" * 60)

        # Phase 1: Discovery
        metadata = self.discover_server(server_path)

        # Create output directory
        server_name = metadata["name"].replace("_", "-").lower()
        output_path = self.output_dir / server_name
        output_path.mkdir(parents=True, exist_ok=True)

        # Phase 2: Generate Docker files
        dockerfile = self.generate_dockerfile(metadata)
        compose = self.generate_compose(metadata)

        # Write files
        (output_path / "Dockerfile").write_text(dockerfile)
        (output_path / "docker-compose.yml").write_text(compose)

        # Copy source code
        print(f"📋 Copying source code to {output_path}...")
        subprocess.run(
            ["cp", "-r", f"{metadata['path']}/.", str(output_path)],
            check=True
        )

        # Phase 3: Generate registry integration
        registry_entry = self.generate_registry_entry(metadata)
        manifest = self.generate_manifest(metadata)
        routing_rules = self.generate_routing_rules(metadata)

        # Write manifest
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.manifests_dir / f"{server_name}.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        # Write routing rules (to be manually added to mcp-proxy.py)
        routing_path = output_path / "routing_rules.py"
        routing_path.write_text(routing_rules)

        # Update registry
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                registry = json.load(f)
        else:
            registry = {"servers": {}, "permanent": [], "settings": {}}

        registry["servers"].update(registry_entry)

        with open(self.registry_path, "w") as f:
            json.dump(registry, f, indent=2)

        # Phase 4: Validation (optional)
        if validate:
            self.validate_container(metadata, output_path)

        # Summary
        print("\n" + "=" * 60)
        print("✅ DOCKERIZATION COMPLETE!")
        print("=" * 60)
        print(f"\n📁 Output directory: {output_path}")
        print(f"📝 Registry updated: {self.registry_path}")
        print(f"📄 Manifest created: {manifest_path}")
        print(f"\n🔧 Manual steps required:")
        print(f"  1. Review and add environment variables to docker-compose.yml")
        print(f"  2. Add routing rules from {routing_path} to mcp-proxy.py")
        print(f"  3. Build and test: cd {output_path} && docker compose up")
        print(f"  4. Test with: .{registry_entry[server_name]['friendly_name']} <query>")

        return {
            "metadata": metadata,
            "output_path": str(output_path),
            "registry_entry": registry_entry,
            "manifest_path": str(manifest_path),
            "routing_rules": routing_rules
        }


def main():
    parser = argparse.ArgumentParser(
        description="Automatically dockerize MCP servers"
    )
    parser.add_argument(
        "server_path",
        help="Path to existing MCP server directory"
    )
    parser.add_argument(
        "--output-dir",
        default="./mcp-dockerize/docker-configs",
        help="Output directory for Docker files"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip container validation"
    )

    args = parser.parse_args()

    dockerizer = MCPDockerizer(output_dir=args.output_dir)
    result = dockerizer.dockerize(
        args.server_path,
        validate=not args.no_validate
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
