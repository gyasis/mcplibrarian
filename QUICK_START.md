# MCP Dockerize - Quick Start

Get started dockerizing your first MCP server in **5 minutes**!

---

## Prerequisites

- Python 3.11+
- Docker installed and running
- An existing MCP server to dockerize

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-dockerize.git
cd mcp-dockerize

# Install dependencies (optional - script is standalone)
pip install -e .
```

---

## 5-Minute Quick Start (Automated Path)

### Step 1: Run the Script

```bash
python mcp-dockerize.py ~/path/to/your/mcp-server/
```

**Example Output**:
```
🔍 Discovering server type...
✓ Found Python server with pyproject.toml
✓ Detected entry point: server.py
✓ Found 6 tools

📦 Generating Docker files...
✓ Created Dockerfile
✓ Created docker-compose.yml

📋 Extracting tool schemas...
✓ Extracted 6 tool schemas

📝 Updating registry...
✓ Added server to mcp-docker-registry.json

✅ Dockerization complete!
📁 Output: ./docker-configs/your-server/
```

### Step 2: Add API Keys (2 minutes)

```bash
cd docker-configs/your-server/
nano docker-compose.yml

# Add your actual API keys:
environment:
  API_KEY: "your-actual-key-here"  # ← Replace placeholder
```

### Step 3: Copy Routing Rules (2 minutes)

```bash
cat routing_rules.py
# Copy the output and paste into your mcp-proxy.py at line ~340
```

### Step 4: Test It! (1 minute)

```bash
docker compose build
docker compose up -d

# Test manually
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | docker compose run --rm your-server
```

### Step 5: Use in Claude Code

Restart Claude Code, then:
```
"use .yourserver to search for data about X"
```

**DONE! You just saved 97% of context tokens! 🎉**

---

## Manual Path (Full Control)

Want to understand every step? See [MANUAL_DOCKERIZATION_GUIDE.md](docs/MANUAL_DOCKERIZATION_GUIDE.md)

**Time**: 2-3 hours first time, 30-60 min after practice
**Control**: 100%
**Learning**: High

---

## What You Get

✅ **Dockerfile** - Optimized for Python/Node.js
✅ **docker-compose.yml** - With volumes and env vars
✅ **Tool Manifest** - All schemas extracted
✅ **Registry Entry** - Auto-registered
✅ **Routing Rules** - Generated Python code
✅ **Token Savings** - 77-97% reduction

---

## Token Savings

**Before**:
- 6 tools × 500 tokens = **3,000 tokens**
- 80 servers × 3,000 = **240,000 tokens** (exceeds budget!)

**After (Toolhost Pattern)**:
- 1 polymorphic tool × 100 tokens = **100 tokens**
- 80 servers × 100 = **8,000 tokens** (97% savings!)

---

## Architecture

```
User Query → Claude Code
                  ↓
            docker-mcp-proxy
                  ↓
         Polymorphic Tool (deeplake_query)
                  ↓
         NLP Keyword Router
                  ↓
         Docker Container (on-demand)
                  ↓
         Real MCP Server (6 tools)
                  ↓
         Results → User
```

---

## Supported Servers

| Type | Auto-Detection | Status |
|------|---------------|--------|
| Python (pyproject.toml) | ✅ | Tested |
| Python (requirements.txt) | ✅ | Tested |
| Node.js (package.json) | ✅ | Tested |
| Node.js TypeScript | ✅ | May need build step |

---

## Next Steps

1. **Test your first server** - Use the 5-minute guide above
2. **Read the full docs** - [README.md](README.md) for decision tree
3. **Learn the manual path** - [MANUAL_DOCKERIZATION_GUIDE.md](docs/MANUAL_DOCKERIZATION_GUIDE.md)
4. **Scale to more servers** - Repeat for 5-10 priority servers

---

## Troubleshooting

### "Cannot determine server type"
```bash
# Add pyproject.toml or package.json
# OR manually specify in script
```

### "Tool extraction timed out"
```bash
# Increase timeout in script
# OR create manifest manually
```

### "Container won't start"
```bash
docker compose logs -f
# Check for missing dependencies or environment variables
```

**Full troubleshooting**: See [MANUAL_DOCKERIZATION_GUIDE.md](docs/MANUAL_DOCKERIZATION_GUIDE.md) Section 11

---

## Help & Support

- 📖 **Documentation**: [docs/](docs/)
- 🐛 **Issues**: GitHub Issues
- 💬 **Discussions**: GitHub Discussions

---

**You're ready to start! Run your first server in 5 minutes! 🚀**
