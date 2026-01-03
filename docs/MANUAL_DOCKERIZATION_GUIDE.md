# Manual MCP Server Dockerization - Complete Step-by-Step Guide

## When to Use Manual vs Automated

### ✅ Use Manual Process When:
- Learning how the system works
- Need full control over every detail
- Server has complex/unusual structure
- mcp-dockerize script fails
- Custom volume/network requirements
- Educational purposes
- Debugging issues

### ✅ Use Automated (mcp-dockerize.py) When:
- Standard Python/Node.js server
- Want quick setup (5 min vs 2 hours)
- Have 10+ servers to dockerize
- Server follows common patterns

**Both paths are fully supported and documented!**

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Analyze Server Structure](#step-1-analyze-server-structure)
3. [Step 2: Create Dockerfile](#step-2-create-dockerfile)
4. [Step 3: Create docker-compose.yml](#step-3-create-docker-composeyml)
5. [Step 4: Extract Tool Schemas](#step-4-extract-tool-schemas)
6. [Step 5: Create Manifest](#step-5-create-manifest)
7. [Step 6: Update Registry](#step-6-update-registry)
8. [Step 7: Add Routing Rules](#step-7-add-routing-rules)
9. [Step 8: Build and Test](#step-8-build-and-test)
10. [Step 9: Integrate with Claude Code](#step-9-integrate-with-claude-code)
11. [Troubleshooting](#troubleshooting)
12. [Real-World Examples](#real-world-examples)

---

## Prerequisites

### Required Tools:
```bash
# Check Docker is installed
docker --version
docker compose version

# Check Python (for Python servers)
python3 --version
uv --version  # Or: pip install uv

# Check Node.js (for Node servers)
node --version
npm --version
```

### Directory Structure Setup:
```bash
# Create working directories
mkdir -p ~/mcp-dockerize/docker-configs
mkdir -p ~/.claude/mcp-manifests

# Verify registry exists
ls ~/.claude/mcp-docker-registry.json

# If not, create it:
cat > ~/.claude/mcp-docker-registry.json << 'EOF'
{
  "servers": {},
  "permanent": ["context7-mcp"],
  "settings": {
    "checkInterval": 60,
    "defaultStopDelay": 300,
    "maxConcurrentContainers": 3
  }
}
EOF
```

---

## Step 1: Analyze Server Structure

### 1.1 Identify Server Type

```bash
# Navigate to server directory
cd ~/path/to/mcp-server

# Check for Python indicators
ls pyproject.toml requirements.txt setup.py *.py

# Check for Node.js indicators
ls package.json *.js *.ts

# Check for other languages
ls go.mod Cargo.toml Gemfile
```

### 1.2 Find Entry Point

**For Python Servers**:
```bash
# Check pyproject.toml
cat pyproject.toml | grep -A 5 "\[project.scripts\]"
# OR
cat pyproject.toml | grep -A 5 "\[tool.poetry.scripts\]"

# Example output:
# [project.scripts]
# my-server = "my_server.main:main"

# Check for __main__.py
ls __main__.py

# Check for common entry points
ls server.py main.py index.py app.py
```

**For Node.js Servers**:
```bash
# Check package.json
cat package.json | jq '.bin'
cat package.json | jq '.main'
cat package.json | jq '.scripts.start'

# Example output:
# "bin": {
#   "my-server": "./dist/index.js"
# }
```

### 1.3 List Dependencies

**Python**:
```bash
# From pyproject.toml
cat pyproject.toml | grep -A 20 "dependencies"

# From requirements.txt
cat requirements.txt

# Example:
# fastmcp>=0.1.0
# httpx>=0.25.0
# pydantic>=2.0.0
```

**Node.js**:
```bash
# From package.json
cat package.json | jq '.dependencies'

# Example:
# {
#   "@modelcontextprotocol/sdk": "^0.4.0",
#   "dotenv": "^16.0.0"
# }
```

### 1.4 Detect Required Files/Volumes

```bash
# Look for data directories
find . -type d -name "data" -o -name "db" -o -name "storage"

# Look for config files
find . -name ".env*" -o -name "config.*"

# Check for hardcoded paths in code
grep -r "\/.*\/" *.py *.js 2>/dev/null | grep -v "http"

# Example output:
# server.py:    DB_PATH = "/var/lib/myserver/db.sqlite"
# server.py:    DATA_DIR = "/opt/data/files"
```

### 1.5 Detect Environment Variables

```bash
# For Python
grep -r "os.getenv\|os.environ" . --include="*.py" | cut -d'"' -f2 | sort -u

# For Node.js
grep -r "process.env" . --include="*.js" --include="*.ts" | \
  sed 's/.*process\.env\.\([A-Z_]*\).*/\1/' | sort -u

# Example output:
# API_KEY
# DATABASE_URL
# LOG_LEVEL
```

### 1.6 Document Your Findings

Create a notes file:
```bash
cat > server-analysis.txt << 'EOF'
SERVER ANALYSIS NOTES
=====================

Name: my-awesome-server
Type: Python
Entry Point: python -m my_server.main

Dependencies:
- fastmcp>=0.1.0
- httpx>=0.25.0
- sqlite3 (built-in)

Required Volumes:
- /var/lib/myserver/db.sqlite (database)
- ./config.json (configuration)

Environment Variables:
- API_KEY (required)
- DATABASE_URL (optional, defaults to sqlite)
- LOG_LEVEL (optional, defaults to INFO)

Notes:
- Server expects database at /var/lib/myserver/db.sqlite
- Will create database if missing
- Config file is optional
EOF
```

---

## Step 2: Create Dockerfile

### 2.1 Choose Base Image

**Python Servers**:
```dockerfile
# Python 3.11 slim (recommended for most cases)
FROM python:3.11-slim

# Python 3.11 full (if you need build tools)
FROM python:3.11

# Alpine (smallest, but may have compatibility issues)
FROM python:3.11-alpine
```

**Node.js Servers**:
```dockerfile
# Node 20 slim (recommended)
FROM node:20-slim

# Node 20 full
FROM node:20

# Node 20 alpine (smallest)
FROM node:20-alpine
```

### 2.2 Create Dockerfile for Python Server

```bash
# Navigate to output directory
mkdir -p ~/mcp-dockerize/docker-configs/my-server
cd ~/mcp-dockerize/docker-configs/my-server

# Create Dockerfile
cat > Dockerfile << 'EOF'
# Dockerfile for my-awesome-server
# Created: 2026-01-03
# Type: Python MCP Server

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install UV for fast package management
RUN pip install --no-cache-dir uv

# Copy dependency files first (for better caching)
COPY pyproject.toml ./
# COPY requirements.txt ./  # Uncomment if using requirements.txt

# Install Python dependencies
RUN uv pip install --system -e .
# RUN uv pip install --system -r requirements.txt  # Alternative

# Copy application code
COPY . .

# Create volume mount points
RUN mkdir -p /var/lib/myserver

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Entry point (adjust based on your server)
CMD ["python", "-m", "my_server.main"]

# Alternative entry points:
# CMD ["python", "server.py"]
# CMD ["uv", "run", "my-server"]
EOF
```

### 2.3 Create Dockerfile for Node.js Server

```bash
cat > Dockerfile << 'EOF'
# Dockerfile for my-awesome-server
# Created: 2026-01-03
# Type: Node.js MCP Server

FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy package files first (for better caching)
COPY package*.json ./

# Install dependencies (production only)
RUN npm ci --only=production

# Copy application code
COPY . .

# Build TypeScript if needed
# RUN npm run build

# Create volume mount points
RUN mkdir -p /var/lib/myserver

# Entry point (adjust based on package.json)
CMD ["node", "dist/index.js"]

# Alternative entry points:
# CMD ["npm", "start"]
# CMD ["node", "server.js"]
EOF
```

### 2.4 Add .dockerignore

```bash
cat > .dockerignore << 'EOF'
# Node.js
node_modules/
npm-debug.log
yarn-error.log

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Git
.git/
.gitignore

# Docker
Dockerfile
docker-compose.yml
.dockerignore

# Testing
.pytest_cache/
.coverage
htmlcov/

# Build artifacts
dist/
build/
*.egg-info/
EOF
```

---

## Step 3: Create docker-compose.yml

### 3.1 Basic Structure

```bash
cat > docker-compose.yml << 'EOF'
# docker-compose.yml for my-awesome-server
version: '3.8'

services:
  my-server:
    # Build configuration
    build:
      context: .
      dockerfile: Dockerfile

    # Container name
    container_name: mcp-my-server

    # Keep stdin open for MCP protocol
    stdin_open: true
    tty: true

    # Restart policy
    restart: unless-stopped

    # Volume mounts
    volumes:
      - ./data:/var/lib/myserver:rw        # Database directory
      - ./config.json:/app/config.json:ro  # Config file (read-only)
      # - ${HOME}/.env:/app/.env:ro        # Environment file

    # Environment variables
    environment:
      - API_KEY=${API_KEY}                 # IMPORTANT: Add actual value!
      - DATABASE_URL=${DATABASE_URL:-sqlite:///var/lib/myserver/db.sqlite}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - NODE_ENV=production                # For Node.js servers

    # Resource limits (optional but recommended)
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

    # Health check (optional)
    healthcheck:
      test: ["CMD", "echo", '{"jsonrpc":"2.0","id":1,"method":"ping"}']
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
EOF
```

### 3.2 Volume Mount Patterns

**Pattern 1: Read-Only Config Files**
```yaml
volumes:
  - ./config.json:/app/config.json:ro
  - ${HOME}/.env:/app/.env:ro
```

**Pattern 2: Read-Write Data Directories**
```yaml
volumes:
  - ./data:/var/lib/myserver/data:rw
  - ./logs:/var/log/myserver:rw
```

**Pattern 3: Absolute Path Mounts (when server expects specific paths)**
```yaml
volumes:
  - /media/data/storage:/media/data/storage:ro
  - /opt/myserver/db:/opt/myserver/db:rw
```

**Pattern 4: Named Volumes (persistent across container recreations)**
```yaml
volumes:
  - myserver-data:/var/lib/myserver
  - myserver-logs:/var/log/myserver

# At bottom of file:
volumes:
  myserver-data:
  myserver-logs:
```

### 3.3 Environment Variable Patterns

**Pattern 1: Direct Values (simple)**
```yaml
environment:
  - API_KEY=sk-your-key-here
  - DATABASE_URL=postgres://localhost/db
```

**Pattern 2: From .env File (recommended)**
```yaml
env_file:
  - .env

# Create .env file:
# API_KEY=sk-your-key-here
# DATABASE_URL=postgres://localhost/db
```

**Pattern 3: Shell Variables with Defaults**
```yaml
environment:
  - API_KEY=${API_KEY}                               # Required (fail if missing)
  - DATABASE_URL=${DATABASE_URL:-sqlite://db.sqlite}  # Optional with default
  - LOG_LEVEL=${LOG_LEVEL:-INFO}                     # Optional with default
```

### 3.4 Create .env Template

```bash
cat > .env.template << 'EOF'
# Environment variables for my-awesome-server
# Copy this to .env and fill in your values

# REQUIRED: Your API key
API_KEY=your-api-key-here

# OPTIONAL: Database connection
DATABASE_URL=sqlite:///var/lib/myserver/db.sqlite

# OPTIONAL: Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# OPTIONAL: Custom settings
# CUSTOM_SETTING=value
EOF

# Copy to .env for actual use
cp .env.template .env
nano .env  # Edit with your actual values
```

---

## Step 4: Extract Tool Schemas

### 4.1 Manual Method - Run Server Locally

```bash
# Navigate to server source
cd ~/original/server/path

# For Python with UV
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | \
uv run python -m my_server.main 2>/dev/null | grep "tools"

# For Python without UV
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | \
python server.py 2>/dev/null | grep "tools"

# For Node.js
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | \
node dist/index.js 2>/dev/null | grep "tools"
```

### 4.2 Extract and Format Output

```bash
# Save to file
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | \
uv run python server.py 2>/dev/null > tools-output.json

# Extract just the tools array
cat tools-output.json | jq '.result.tools' > tools-extracted.json

# Pretty print
cat tools-extracted.json | jq '.'
```

### 4.3 Manual Method - Read Source Code

If server won't run, extract from source:

```bash
# For Python with @mcp.tool decorator
grep -A 20 "@.*tool" *.py

# Example:
# @server.tool()
# async def search_data(query: str) -> dict:
#     """Search the database for matching records."""
#     ...

# For Node with server.tool()
grep -A 20 "server\.tool" *.js *.ts
```

Create schemas manually:
```json
{
  "name": "search_data",
  "description": "Search the database for matching records",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      }
    },
    "required": ["query"]
  }
}
```

---

## Step 5: Create Manifest

### 5.1 Create Manifest JSON

```bash
# Create manifest file
cat > ~/.claude/mcp-manifests/my-server.json << 'EOF'
{
  "name": "my-server",
  "version": "1.0.0",
  "type": "python",
  "description": "My awesome MCP server for data operations",
  "tools": [
    {
      "name": "search_data",
      "description": "Search the database for matching records. Returns top N results sorted by relevance.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Search query string"
          },
          "limit": {
            "type": "integer",
            "description": "Maximum number of results to return",
            "default": 10
          }
        },
        "required": ["query"]
      }
    },
    {
      "name": "get_record",
      "description": "Retrieve a specific record by ID",
      "inputSchema": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "description": "Record ID"
          }
        },
        "required": ["id"]
      }
    },
    {
      "name": "list_recent",
      "description": "List recently added or modified records",
      "inputSchema": {
        "type": "object",
        "properties": {
          "limit": {
            "type": "integer",
            "description": "Number of records to return",
            "default": 20
          },
          "since": {
            "type": "string",
            "description": "ISO timestamp to filter from (optional)"
          }
        }
      }
    }
  ]
}
EOF
```

### 5.2 Validate Manifest

```bash
# Check JSON syntax
jq '.' ~/.claude/mcp-manifests/my-server.json

# Verify structure
jq '.tools | length' ~/.claude/mcp-manifests/my-server.json
# Should output: 3

# List tool names
jq '.tools[].name' ~/.claude/mcp-manifests/my-server.json
# Should output:
# "search_data"
# "get_record"
# "list_recent"
```

---

## Step 6: Update Registry

### 6.1 Choose Trigger Keywords

Think about how users will activate this server:
```
What words describe this server's function?
- "search" - for search_data tool
- "data" - general purpose
- "records" - for database records
- "recent" - for list_recent tool
- "myserver" - explicit name

Server name variations:
- "my-server" (full name)
- "myserver" (no hyphen)
- "my server" (with space)
```

### 6.2 Add Registry Entry

```bash
# Backup existing registry first
cp ~/.claude/mcp-docker-registry.json ~/.claude/mcp-docker-registry.json.backup

# Edit registry
nano ~/.claude/mcp-docker-registry.json
```

Add your server entry:
```json
{
  "servers": {
    "deeplake-rag": {
      "...": "... existing servers ..."
    },
    "my-server": {
      "friendly_name": "myserver",
      "image": "my-server-my-server:latest",
      "container_name": "mcp-my-server",
      "compose_file": "/home/gyasis/mcp-dockerize/docker-configs/my-server/docker-compose.yml",
      "category": "data",
      "meta_tool_name": "use_myserver_tools",
      "manifest_path": "/home/gyasis/.claude/mcp-manifests/my-server.json",
      "triggers": [
        "search",
        "data",
        "records",
        "recent",
        "myserver",
        "my server",
        "database",
        "query"
      ],
      "autoStop": true,
      "autoStopDelay": 300,
      "tokenCost": 1500,
      "actualToolCount": 3,
      "description": "My awesome MCP server for data operations"
    }
  },
  "permanent": ["context7-mcp"],
  "settings": {
    "checkInterval": 60,
    "defaultStopDelay": 300,
    "maxConcurrentContainers": 3
  }
}
```

### 6.3 Validate Registry

```bash
# Check JSON syntax
jq '.' ~/.claude/mcp-docker-registry.json

# Verify your server was added
jq '.servers["my-server"]' ~/.claude/mcp-docker-registry.json

# List all servers
jq '.servers | keys' ~/.claude/mcp-docker-registry.json
```

---

## Step 7: Add Routing Rules

### 7.1 Analyze Tool Names for Keywords

```
Tools:
- search_data → keywords: "search", "find", "query"
- get_record → keywords: "get", "record", "retrieve", "fetch"
- list_recent → keywords: "recent", "list", "latest"
```

### 7.2 Create Routing Logic

```bash
nano ~/claude-scripts/mcp-proxy.py
```

Find the `_route_polymorphic_call` method (around line 301) and add your routing rules:

```python
def _route_polymorphic_call(self, server_name: str, query: str) -> dict:
    """Route natural language query to specific tool call."""
    query_lower = query.lower()
    tool_name = None
    params = {}

    # Existing deeplake-rag rules...
    if server_name == "deeplake-rag":
        # ... existing code ...

    # ADD YOUR NEW SERVER RULES HERE
    elif server_name == "my-server":
        # Rule 1: Search/Find/Query → search_data
        if "search" in query_lower or \
           "find" in query_lower or \
           "query" in query_lower:
            tool_name = "search_data"
            params = {"query": query, "limit": 10}

        # Rule 2: Get/Retrieve/Fetch + Record → get_record
        elif ("get" in query_lower or "retrieve" in query_lower or "fetch" in query_lower) and \
             "record" in query_lower:
            # Try to extract ID from query
            # Simple pattern: "get record ABC123"
            import re
            id_match = re.search(r'\b([A-Z0-9]{6,})\b', query)
            if id_match:
                tool_name = "get_record"
                params = {"id": id_match.group(1)}
            else:
                # Couldn't extract ID, ask for whole query as ID
                tool_name = "get_record"
                params = {"id": query}

        # Rule 3: Recent/Latest/List → list_recent
        elif "recent" in query_lower or \
             "latest" in query_lower or \
             "list" in query_lower:
            tool_name = "list_recent"
            params = {"limit": 20}

        # Default: search_data
        else:
            tool_name = "search_data"
            params = {"query": query, "limit": 10}

    # Original code continues...
    print(f"🔀 Routing '{query}' → {server_name}.{tool_name}", file=sys.stderr)

    # Start container if not running
    if not self.manager.is_container_running(server_name):
        print(f"Starting container for {server_name}...", file=sys.stderr)
        self.manager.start_container(server_name)

    # Update activity
    self.manager.update_activity(server_name)

    # Call actual tool via container
    return self._call_container_tool(server_name, tool_name, params)
```

### 7.3 Test Routing Logic Manually

```python
# Test routing logic in Python REPL
python3

>>> query = "search for python articles"
>>> query_lower = query.lower()
>>>
>>> # Test Rule 1
>>> if "search" in query_lower:
...     print("Matched: search_data")
...
Matched: search_data

>>> # Test Rule 2
>>> query2 = "get record ABC123"
>>> import re
>>> id_match = re.search(r'\b([A-Z0-9]{6,})\b', query2)
>>> if id_match:
...     print(f"Matched: get_record with ID={id_match.group(1)}")
...
Matched: get_record with ID=ABC123
```

---

## Step 8: Build and Test

### 8.1 Copy Source Code

```bash
# Navigate to docker config directory
cd ~/mcp-dockerize/docker-configs/my-server

# Copy server source code
cp -r ~/original/server/path/* .

# Verify files are present
ls -la
# Should see:
# Dockerfile
# docker-compose.yml
# .env
# pyproject.toml (or package.json)
# server.py (or index.js)
# ... etc
```

### 8.2 Build Container

```bash
# Build the Docker image
docker compose build

# Watch for errors
# Common issues:
# - Missing dependencies in requirements.txt
# - Wrong Python version
# - Missing system packages (gcc, g++)

# If build fails, check logs and fix Dockerfile
```

### 8.3 Test MCP Protocol Handshake

```bash
# Test initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | \
docker compose run --rm my-server

# Expected output (look for "result"):
# {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05",...}}

# Test tools/list
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | \
docker compose run --rm my-server

# Expected output: JSON with tools array
# {"jsonrpc":"2.0","id":2,"result":{"tools":[...]}}
```

### 8.4 Test Individual Tools

```bash
# Test search_data tool
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_data","arguments":{"query":"test"}}}' | \
docker compose run --rm my-server

# Should see results from search

# Test get_record tool
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_record","arguments":{"id":"ABC123"}}}' | \
docker compose run --rm my-server
```

### 8.5 Start Container in Background

```bash
# Start the container
docker compose up -d

# Check it's running
docker ps | grep mcp-my-server

# Check logs
docker compose logs -f

# Stop when done testing
docker compose down
```

---

## Step 9: Integrate with Claude Code

### 9.1 Verify Files in Place

```bash
# Check registry entry exists
jq '.servers["my-server"]' ~/.claude/mcp-docker-registry.json

# Check manifest exists
cat ~/.claude/mcp-manifests/my-server.json

# Check routing rules in mcp-proxy.py
grep -A 10 'server_name == "my-server"' ~/claude-scripts/mcp-proxy.py

# Check proxy is configured in Claude Code
cat ~/.claude/mcp.json | jq '.mcpServers["docker-mcp-proxy"]'
```

### 9.2 Restart Claude Code

```bash
# Exit current Claude Code session
exit

# Start new session
claude

# OR restart in same terminal
exec bash
claude
```

### 9.3 Test Dot Notation

```
In Claude Code session:

"use .myserver to search for test data"
```

Expected behavior:
1. Container starts (first time only, ~5-10 seconds)
2. Query routes to search_data tool
3. Results returned

### 9.4 Test Keyword Triggers

```
In Claude Code session:

"search my data for python articles"
```

Expected behavior:
1. "search" + "data" triggers my-server
2. Container starts automatically
3. Routes to search_data
4. Results returned

### 9.5 Test Documentation Tool

```
In Claude Code session:

"What tools does my-server have?"
```

Expected: Claude calls `get_server_documentation("my-server")` and shows all 3 tools with full schemas.

### 9.6 Verify Token Savings

```
In Claude Code session:

"List all tools from docker-mcp-proxy"
```

Expected output:
```
I see 4 tools:
1. deeplake_rag_query
2. my_server_query           ← Your new polymorphic tool
3. get_server_documentation
```

**NOT seeing**: search_data, get_record, list_recent (those are hidden behind polymorphic tool)

Token cost:
- Before: 3 tools × 500 tokens = 1,500 tokens
- After: 1 tool × 100 tokens = 100 tokens
- **Savings: 93%** 🎉

---

## Step 10: Production Deployment (Optional)

### 10.1 Create Systemd Service (Auto-Start)

```bash
# Create systemd service file
sudo nano /etc/systemd/system/mcp-my-server.service
```

Add:
```ini
[Unit]
Description=MCP My Server Container
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/gyasis/mcp-dockerize/docker-configs/my-server
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=gyasis

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-my-server
sudo systemctl start mcp-my-server
sudo systemctl status mcp-my-server
```

### 10.2 Setup Logging

```bash
# Create log directory
mkdir -p ~/mcp-dockerize/docker-configs/my-server/logs

# Add to docker-compose.yml
nano docker-compose.yml
```

Add:
```yaml
    volumes:
      - ./logs:/var/log/myserver:rw
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

View logs:
```bash
docker compose logs -f
# OR
tail -f logs/server.log
```

### 10.3 Setup Monitoring

```bash
# Check container health
docker inspect mcp-my-server | jq '.[0].State.Health'

# Monitor resource usage
docker stats mcp-my-server

# Setup alerts (optional)
# Use Portainer, Grafana, or custom scripts
```

---

## Troubleshooting

### Issue 1: Container Won't Build

**Error**: `failed to solve: process "/bin/sh -c pip install..." did not complete successfully`

**Solutions**:
```bash
# 1. Check system dependencies
# Add to Dockerfile before pip install:
RUN apt-get update && apt-get install -y gcc g++ make

# 2. Check Python version
# Change FROM line:
FROM python:3.11-slim  # Instead of 3.12 or 3.9

# 3. Pin dependency versions
# In requirements.txt:
fastmcp==0.1.0  # Instead of fastmcp>=0.1.0

# 4. Check build logs
docker compose build --no-cache --progress=plain
```

### Issue 2: Tools Not Appearing

**Symptom**: `tools/list` returns empty array

**Solutions**:
```bash
# 1. Test server locally first
uv run python server.py
# Paste initialize + tools/list requests

# 2. Check entry point is correct
docker compose run --rm my-server --help
# Should show server starting

# 3. Check server logs
docker compose logs

# 4. Verify MCP protocol version
# Change to "2024-11-05" if using older version
```

### Issue 3: Volume Mounts Not Working

**Symptom**: Server can't find data files

**Solutions**:
```bash
# 1. Check absolute paths
# In docker-compose.yml:
volumes:
  - /full/absolute/path:/container/path

# 2. Check permissions
chmod -R 755 ./data
chown -R $(id -u):$(id -g) ./data

# 3. Test mount is working
docker compose run --rm my-server ls -la /var/lib/myserver
# Should see your files

# 4. Use bind mounts with type
volumes:
  - type: bind
    source: /absolute/path
    target: /container/path
```

### Issue 4: Environment Variables Not Set

**Symptom**: Server errors about missing API keys

**Solutions**:
```bash
# 1. Check .env file exists and has values
cat .env
# Should show: API_KEY=actual-key-here

# 2. Test env vars inside container
docker compose run --rm my-server env | grep API_KEY
# Should show: API_KEY=actual-key-here

# 3. Use explicit values in docker-compose.yml
environment:
  - API_KEY=sk-actual-key-here  # Hard-coded

# 4. Pass from shell
API_KEY=sk-key docker compose up
```

### Issue 5: Routing Not Working

**Symptom**: Polymorphic call routes to wrong tool

**Solutions**:
```bash
# 1. Check routing rules order (first match wins)
# In mcp-proxy.py, order matters:
if "search" in query_lower:  # This runs BEFORE next rule
    tool_name = "search_data"
elif "find" in query_lower:  # This only runs if "search" didn't match
    tool_name = "find_data"

# 2. Add debug logging
print(f"DEBUG: query_lower = {query_lower}", file=sys.stderr)
print(f"DEBUG: routing to {tool_name}", file=sys.stderr)

# 3. Test routing manually
python3 -c "
query = 'search for data'
if 'search' in query.lower():
    print('Matched: search_data')
"

# 4. Check for keyword conflicts
# If multiple servers use "search", make rules more specific:
if server_name == "my-server":
    if "search" in query_lower and "data" in query_lower:
        tool_name = "search_data"
```

### Issue 6: Container Starts But Doesn't Respond

**Symptom**: Container running but tool calls timeout

**Solutions**:
```bash
# 1. Check container logs for errors
docker compose logs -f

# 2. Test with simple ping
echo '{"jsonrpc":"2.0","id":1,"method":"ping"}' | \
docker exec -i mcp-my-server cat

# 3. Check if server is actually listening on stdin
docker exec mcp-my-server ps aux
# Should see your server process

# 4. Increase timeout in mcp-proxy.py
# Find subprocess.run() calls and add:
timeout=30  # Instead of 10

# 5. Check server startup time
docker compose up
# Time how long until "Server ready" message
# May need to add startup delay in routing
```

---

## Real-World Examples

### Example 1: Gemini MCP Server (Python)

```bash
# Step 1: Clone and analyze
git clone https://github.com/user/gemini-mcp-server
cd gemini-mcp-server
cat pyproject.toml  # Entry point: gemini-server
cat README.md       # Needs GEMINI_API_KEY

# Step 2: Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml ./
RUN uv pip install --system -e .
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["gemini-server"]
EOF

# Step 3: Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  gemini:
    build: .
    container_name: mcp-gemini
    stdin_open: true
    tty: true
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
EOF

# Step 4: Extract tools
echo '...' | uv run gemini-server > tools.json

# Tools found:
# - ask_gemini
# - gemini_code_review
# - gemini_brainstorm
# - gemini_debug
# - gemini_research
# - interpret_image

# Step 5: Create manifest
cat > ~/.claude/mcp-manifests/gemini.json << 'EOF'
{
  "name": "gemini",
  "tools": [...]
}
EOF

# Step 6: Add to registry
# Triggers: ["gemini", "ai", "analyze", "code review", "research"]

# Step 7: Add routing rules
# if "analyze" or "review": → gemini_code_review
# if "research" or "search": → gemini_research
# if "brainstorm" or "ideas": → gemini_brainstorm
# if "debug" or "fix": → gemini_debug
# default: → ask_gemini

# Step 8: Test
docker compose build
docker compose up -d
```

---

### Example 2: Playwright MCP Server (Node.js)

```bash
# Step 1: Clone and analyze
git clone https://github.com/user/playwright-mcp
cd playwright-mcp
cat package.json  # Entry point: dist/index.js

# Step 2: Create Dockerfile
cat > Dockerfile << 'EOF'
FROM node:20-slim

# Install Playwright dependencies
RUN apt-get update && apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
RUN npx playwright install chromium
COPY . .
CMD ["node", "dist/index.js"]
EOF

# Step 3: Create docker-compose.yml with display
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  playwright:
    build: .
    container_name: mcp-playwright
    stdin_open: true
    tty: true
    shm_size: 2gb  # Required for Chromium
    environment:
      - DISPLAY=:99  # Virtual display
EOF

# Step 4-8: Same as Example 1
# Triggers: ["browser", "playwright", "screenshot", "automation"]
# Routing: "screenshot" → browser_screenshot
#          "click" → browser_click
#          "navigate" → browser_navigate
```

---

## Summary Checklist

Use this checklist for each new server:

### Analysis Phase:
- [ ] Identify server type (Python/Node.js)
- [ ] Find entry point
- [ ] List dependencies
- [ ] Detect required volumes
- [ ] Detect environment variables
- [ ] Document findings

### Docker Phase:
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml
- [ ] Create .env template
- [ ] Copy source code
- [ ] Build container (`docker compose build`)
- [ ] Test MCP handshake

### Integration Phase:
- [ ] Extract tool schemas
- [ ] Create manifest JSON
- [ ] Choose trigger keywords
- [ ] Add registry entry
- [ ] Add routing rules to mcp-proxy.py
- [ ] Test routing logic

### Testing Phase:
- [ ] Test container starts
- [ ] Test tools/list
- [ ] Test individual tools
- [ ] Test dot notation (`.servername`)
- [ ] Test keyword triggers
- [ ] Verify token savings

### Production Phase:
- [ ] Setup logging
- [ ] Setup auto-start (systemd)
- [ ] Setup monitoring
- [ ] Document for team

---

## Time Estimates

| Phase | Manual Time | Notes |
|-------|-------------|-------|
| Analysis | 30 min | Depends on server complexity |
| Dockerfile | 20 min | Add system deps if needed |
| docker-compose.yml | 15 min | More if complex volumes |
| Tool Extraction | 30 min | Faster if server runs easily |
| Manifest Creation | 10 min | Copy/paste from extraction |
| Registry Update | 10 min | Careful with JSON syntax |
| Routing Rules | 20 min | Think through keywords |
| Testing | 20 min | More if issues found |
| **TOTAL** | **~2.5 hours** | For first server, faster after practice |

**With mcp-dockerize.py**: ~5 minutes + 10 minutes manual = **15 minutes total**

---

## Next Steps

After manually dockerizing your first server:

1. **Learn the Pattern**: Understanding manual process helps debug automated process
2. **Use mcp-dockerize.py**: For subsequent servers, use automation
3. **Customize**: Modify generated files as needed for special cases
4. **Document**: Keep notes on any edge cases or custom solutions
5. **Share**: Help others by documenting your specific server setup

---

**Both paths are fully supported!**
- **Manual**: Full control, educational, debugging
- **Automated**: Fast, consistent, scalable

**Choose based on your needs!** 🚀
