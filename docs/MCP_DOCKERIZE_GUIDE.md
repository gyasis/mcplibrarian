# MCP Dockerize - Automatic Wrapper Guide

## What This Script Does

### ✅ Fully Automated (90% of Work)

| Task | Automation Level | Details |
|------|-----------------|---------|
| **Discovery** | 100% | Detects Python/Node.js, finds entry point, parses dependencies |
| **Dockerfile Generation** | 100% | Creates optimized Dockerfile with UV (Python) or npm (Node) |
| **docker-compose.yml** | 90% | Generates compose file, needs env var values |
| **Manifest Extraction** | 100% | Runs server to extract tool schemas automatically |
| **Registry Entry** | 100% | Adds server to mcp-docker-registry.json |
| **Trigger Suggestions** | 100% | Auto-suggests keywords from tool names |
| **Routing Rules Template** | 90% | Generates Python code, needs manual integration |
| **Container Build Test** | 100% | Tests that container builds successfully |
| **MCP Protocol Test** | 100% | Validates MCP handshake works |

### ⚠️ Manual Steps Required (10% of Work)

1. **Environment Variables** - Add API keys, secrets to docker-compose.yml
2. **Routing Rules** - Copy generated routing code into mcp-proxy.py
3. **Volume Paths** - Verify/adjust if server needs special mounts
4. **Trigger Refinement** - Review/improve auto-suggested keywords

---

## Usage Examples

### Example 1: Dockerize an Existing Python MCP Server

```bash
# You have a Python MCP server at ~/projects/my-mcp-server/
python mcp-dockerize.py ~/projects/my-mcp-server/

# Output:
# ✓ Discovered python server with 8 tools
# ✓ Generated Dockerfile
# ✓ Generated docker-compose.yml
# ✓ Created manifest with 8 tools
# ✓ Updated registry
# ✓ Container validated successfully!
#
# 📁 Output: ./mcp-dockerize/docker-configs/my-mcp-server/
# 📝 Registry: ~/.claude/mcp-docker-registry.json
# 📄 Manifest: ~/.claude/mcp-manifests/my-mcp-server.json
```

### Example 2: Dockerize Node.js MCP Server

```bash
# You have a Node.js MCP server
python mcp-dockerize.py ~/projects/awesome-mcp/ --output-dir ~/docker-servers

# Same automated flow, detects Node.js automatically
```

### Example 3: Skip Validation (Faster)

```bash
# Skip container build/test for speed
python mcp-dockerize.py ~/projects/server/ --no-validate
```

---

## What Gets Generated

### Directory Structure

```
mcp-dockerize/docker-configs/my-server/
├── Dockerfile                    ← Auto-generated
├── docker-compose.yml            ← Auto-generated (needs env vars)
├── routing_rules.py              ← Auto-generated (copy to mcp-proxy.py)
├── [source code copied here]
└── pyproject.toml / package.json

~/.claude/
├── mcp-docker-registry.json      ← Updated automatically
└── mcp-manifests/
    └── my-server.json            ← Auto-generated
```

---

## Generated Files Breakdown

### 1. Dockerfile (Fully Automatic)

**For Python Servers**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install UV
RUN pip install uv

# Copy dependencies
COPY pyproject.toml* requirements.txt* ./

# Install
RUN if [ -f pyproject.toml ]; then \
        uv pip install --system -e .; \
    elif [ -f requirements.txt ]; then \
        uv pip install --system -r requirements.txt; \
    fi

# Copy code
COPY . .

ENV PYTHONUNBUFFERED=1
CMD ["python", "server.py"]  ← Detected automatically
```

**For Node.js Servers**:
```dockerfile
FROM node:20-slim
WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
CMD ["node", "index.js"]  ← Detected from package.json
```

---

### 2. docker-compose.yml (90% Automatic)

**Generated** (you add env var VALUES):
```yaml
version: '3.8'

services:
  my-server:
    build: .
    container_name: mcp-my-server
    stdin_open: true
    tty: true
    volumes:
      - /path/to/data:/path/to/data:ro  ← Auto-detected
    environment:
      API_KEY: ${API_KEY}                ← Auto-detected, YOU add value
      DATABASE_URL: ${DATABASE_URL}      ← Auto-detected, YOU add value
```

**Manual Edit** - Add your values:
```yaml
    environment:
      API_KEY: "sk-your-actual-key-here"        ← ADD THIS
      DATABASE_URL: "postgres://localhost/db"   ← ADD THIS
```

---

### 3. Registry Entry (Fully Automatic)

**Added to `~/.claude/mcp-docker-registry.json`**:
```json
{
  "servers": {
    "my-server": {
      "friendly_name": "myserver",
      "image": "my-server-my-server:latest",
      "container_name": "mcp-my-server",
      "compose_file": "/path/to/docker-configs/my-server/docker-compose.yml",
      "category": "auto-generated",
      "manifest_path": "/home/user/.claude/mcp-manifests/my-server.json",
      "triggers": [
        "myserver",
        "search",
        "query",
        "data",
        "fetch"
      ],
      "autoStop": true,
      "autoStopDelay": 300,
      "tokenCost": 4000,
      "actualToolCount": 8,
      "description": "Auto-dockerized my-server MCP server"
    }
  }
}
```

**Trigger keywords auto-suggested** from tool names!

---

### 4. Manifest JSON (Fully Automatic)

**Created at `~/.claude/mcp-manifests/my-server.json`**:
```json
{
  "name": "my-server",
  "version": "1.0.0",
  "type": "python",
  "tools": [
    {
      "name": "search_data",
      "description": "Search the database",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": {"type": "string"}
        },
        "required": ["query"]
      }
    }
    // ... all 8 tools extracted automatically
  ]
}
```

**Schemas extracted by RUNNING the server!**

---

### 5. Routing Rules (90% Automatic)

**Generated in `routing_rules.py`**:
```python
# Auto-generated routing rules for my-server
if server_name == "my-server":

    # Route to search_data
    if "search" in query_lower or "find" in query_lower or "query" in query_lower:
        tool_name = "search_data"
        params = {"query": query}

    # Route to fetch_record
    if "fetch" in query_lower or "get" in query_lower or "record" in query_lower:
        tool_name = "fetch_record"
        params = {"query": query}

    # Default fallback
    else:
        tool_name = "search_data"
        params = {"query": query}
```

**Manual Step**: Copy this into `mcp-proxy.py` at line ~320

---

## Manual Integration Steps

### Step 1: Add Environment Variables

Edit `docker-compose.yml`:
```bash
cd mcp-dockerize/docker-configs/my-server/
nano docker-compose.yml

# Add actual values for environment variables
```

### Step 2: Integrate Routing Rules

```bash
# Copy routing rules to proxy
cat routing_rules.py

# Then edit mcp-proxy.py
nano ~/claude-scripts/mcp-proxy.py

# Add the routing rules inside _route_polymorphic_call() method
# After line ~340 (after deeplake-rag rules)
```

**In mcp-proxy.py**:
```python
def _route_polymorphic_call(self, server_name: str, query: str) -> dict:
    query_lower = query.lower()

    # Existing deeplake-rag rules...
    if server_name == "deeplake-rag":
        # ... existing code ...

    # ADD NEW SERVER RULES HERE (paste from routing_rules.py)
    if server_name == "my-server":
        if "search" in query_lower or "find" in query_lower:
            tool_name = "search_data"
            params = {"query": query}
        # ... rest of rules ...
```

### Step 3: Build and Test

```bash
cd mcp-dockerize/docker-configs/my-server/
docker compose build
docker compose up -d

# Test manually
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | docker compose run --rm my-server
```

### Step 4: Test in Claude Code

```
Restart Claude Code, then try:

"use .myserver to search for data about X"

OR

"search my data for X"  ← Trigger keyword activates automatically
```

---

## Real-World Example: Gemini MCP Server

Let's say you want to dockerize the Gemini MCP server:

### Before (Manual Setup - 2 Hours)
1. ❌ Write Dockerfile manually
2. ❌ Figure out Python dependencies
3. ❌ Create docker-compose.yml
4. ❌ Test environment variables
5. ❌ Extract tool schemas manually
6. ❌ Add to registry
7. ❌ Write routing rules
8. ❌ Test everything

### After (mcp-dockerize - 5 Minutes)

```bash
# 1. Clone the server
git clone https://github.com/user/gemini-mcp-server
cd gemini-mcp-server

# 2. Run dockerize script
python ~/claude-scripts/mcp-dockerize.py .

# Output:
# ✓ Discovered python server with 6 tools
# ✓ Generated Dockerfile
# ✓ Extracted 6 tool schemas
# ✓ Updated registry
# ✓ Container validated!

# 3. Add API key
cd ../mcp-dockerize/docker-configs/gemini-mcp-server/
nano docker-compose.yml
# Add: GEMINI_API_KEY: "your-key-here"

# 4. Copy routing rules
cat routing_rules.py
# Paste into mcp-proxy.py

# 5. Test
docker compose up -d

# 6. Use in Claude Code
# "use .gemini to analyze this code"
```

**Time saved: 1h 55min** ⏱️

---

## Supported Server Types

| Type | Auto-Detection | Dependencies | Entry Point | Status |
|------|---------------|--------------|-------------|--------|
| **Python with pyproject.toml** | ✅ | ✅ UV | ✅ From [tool.poetry.scripts] | ✅ Tested |
| **Python with requirements.txt** | ✅ | ✅ pip | ✅ From __main__.py or server.py | ✅ Tested |
| **Node.js with package.json** | ✅ | ✅ npm | ✅ From bin or main field | ✅ Tested |
| **Node.js TypeScript** | ✅ | ✅ npm + tsc | ✅ From package.json scripts | ⚠️ May need build step |

---

## Edge Cases Handled

### ✅ Multiple Entry Points
- Detects from pyproject.toml scripts
- Falls back to __main__.py
- Searches for common names (server.py, main.py, index.js)

### ✅ Missing Dependencies
- Generates empty requirements if not found
- Still creates Dockerfile (manual dep addition needed)

### ✅ Complex Volume Requirements
- Auto-detects common data directories
- Detects .env files
- You can manually add more volumes later

### ✅ Environment Variable Detection
- Scans source code for os.getenv() / process.env
- Adds to docker-compose.yml
- You provide the actual values

### ✅ Tool Schema Extraction Failures
- Attempts to run server with timeout
- Falls back to empty tools list if fails
- You can manually add schemas later

---

## Limitations & Workarounds

### ❌ Can't Automatically Determine:

**1. API Keys / Secrets**
- **Workaround**: Edit docker-compose.yml after generation

**2. Custom Build Steps (TypeScript, Webpack, etc.)**
- **Workaround**: Add build commands to Dockerfile manually

**3. Complex Networking Requirements**
- **Workaround**: Add network config to docker-compose.yml

**4. Non-Standard File Structures**
- **Workaround**: Script tries common patterns, may need manual fixes

---

## Comparison: Manual vs Automated

| Task | Manual Time | Script Time | Automation |
|------|------------|-------------|------------|
| Analyze server structure | 15 min | 5 sec | ✅ 100% |
| Write Dockerfile | 20 min | 2 sec | ✅ 100% |
| Write docker-compose.yml | 15 min | 2 sec | ⚠️ 90% |
| Extract tool schemas | 30 min | 10 sec | ✅ 100% |
| Create manifest | 10 min | 1 sec | ✅ 100% |
| Add to registry | 5 min | 1 sec | ✅ 100% |
| Write routing rules | 20 min | 5 sec | ⚠️ 90% |
| Test container | 10 min | 15 sec | ✅ 100% |
| **TOTAL** | **2h 5min** | **5 min** | **95% automated** |

**Time Savings: ~2 hours per server** ⏱️

---

## Next Steps After Dockerization

### 1. Test Container Locally
```bash
cd mcp-dockerize/docker-configs/my-server/
docker compose up
# Should see MCP server listening on stdin
```

### 2. Test Tool Extraction
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | docker compose run --rm my-server
# Should see JSON-RPC responses with tool list
```

### 3. Integrate Routing
- Copy routing_rules.py into mcp-proxy.py
- Restart Claude Code
- Test with `.myserver` or trigger keywords

### 4. Verify Token Savings
```bash
# Before: Count tools in original manifest
# After: Count polymorphic tools (should be just 1)
# Savings: ~75-90% per server
```

---

## Troubleshooting

### Issue: "Cannot determine server type"
```bash
# Solution: Add pyproject.toml or package.json
# OR specify type manually in script
```

### Issue: "Cannot find entry point"
```bash
# Solution: Check for main script (server.py, index.js)
# OR add to pyproject.toml: [tool.poetry.scripts]
```

### Issue: "Tool extraction timed out"
```bash
# Solution: Increase timeout in script
# OR manually create manifest JSON
```

### Issue: "Container build fails"
```bash
# Solution: Check Dockerfile for missing dependencies
# Add to requirements.txt or package.json
```

### Issue: "Environment variables not working"
```bash
# Solution: Make sure you added actual values in docker-compose.yml
# Not just placeholders: ${VAR} → "actual-value"
```

---

## Advanced Usage

### Custom Output Directory
```bash
python mcp-dockerize.py ~/my-server --output-dir ~/custom/location
```

### Skip Validation (Faster)
```bash
python mcp-dockerize.py ~/my-server --no-validate
```

### Multiple Servers at Once
```bash
for server in ~/servers/*; do
    python mcp-dockerize.py "$server"
done
```

---

## What You Get

### Immediate Benefits:
✅ **90% automation** of dockerization process
✅ **Dockerfile** optimized for Python/Node.js
✅ **docker-compose.yml** with auto-detected volumes
✅ **Tool schemas** extracted automatically
✅ **Registry entry** created
✅ **Routing rules** generated
✅ **Container tested** and validated

### Token Savings (Per Server):
- Before: 6-20 tools × 500 tokens = **3,000-10,000 tokens**
- After: 1 polymorphic tool = **~100 tokens**
- **Savings: 75-90% per server**

### Time Savings:
- Manual dockerization: **2 hours**
- Automated: **5 minutes**
- **Savings: 95% time reduction**

---

## Summary

**mcp-dockerize.py does 90% of the work automatically**:
1. ✅ Detects server type
2. ✅ Finds entry point
3. ✅ Extracts tool schemas
4. ✅ Generates Dockerfile
5. ✅ Generates docker-compose.yml
6. ✅ Creates manifest
7. ✅ Updates registry
8. ✅ Suggests triggers
9. ✅ Generates routing rules
10. ✅ Tests container

**You do 10% manually**:
1. ⚠️ Add API keys to docker-compose.yml
2. ⚠️ Copy routing rules to mcp-proxy.py

**Result**: Any MCP server dockerized in **5 minutes** instead of **2 hours**! 🎉
