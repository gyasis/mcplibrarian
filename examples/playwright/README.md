# 🎭 Playwright MCP Server Example

This directory contains a complete example of cataloging the Playwright MCP server using MCP Librarian.

## 📁 Files in This Example

| File | Purpose |
|------|---------|
| `package.json` | Node.js project configuration declaring @playwright/mcp dependency |
| `package-lock.json` | Locked dependency versions for reproducible builds |
| `index.js` | Simple wrapper that imports and starts the Playwright MCP server |
| `Dockerfile` | Container build instructions |
| `docker-compose.yml` | Container orchestration configuration |
| `routing_rules.py` | Example routing logic for polymorphic tool pattern |

## 🎯 What This Example Demonstrates

### Token Savings

**Before MCP Librarian**:
- 43 individual Playwright tools
- ~10,650 tokens consumed at startup
- 5.3% of token budget used

**After MCP Librarian**:
- 1 polymorphic `playwright_query` tool
- ~100 tokens consumed at startup
- 99% token savings (10,550 tokens saved)

### The Wrapper Pattern

Playwright is typically run via `npx @playwright/mcp@latest`, which creates a challenge:
- Not a traditional Python server (no `pyproject.toml`)
- Not a traditional Node.js project (no local code)
- An npm package run on-demand

**Solution**: Create a minimal Node.js wrapper that mcp-librarian.py can catalog.

## 🚀 Quick Start

### Option 1: Use These Files Directly

```bash
# Navigate to this directory
cd examples/playwright

# Build the container
docker compose build

# Start the container
docker compose up -d

# Test it
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | docker compose run --rm playwright-mcp-wrapper node /app/index.js
```

### Option 2: Recreate from Scratch

Follow the [Playwright Tutorial](../../docs/PLAYWRIGHT_TUTORIAL.md) to recreate this example step-by-step and understand the complete cataloging workflow.

## 📊 File Breakdown

### package.json

```json
{
  "name": "playwright-mcp",
  "version": "1.0.0",
  "description": "Playwright MCP Server Wrapper",
  "type": "module",
  "dependencies": {
    "@playwright/mcp": "latest"
  },
  "bin": {
    "playwright-mcp": "./index.js"
  }
}
```

**Purpose**: Declares the project as an ES module and specifies the dependency on `@playwright/mcp`.

### index.js

```javascript
#!/usr/bin/env node
import { createServer } from "@playwright/mcp";

const server = createServer();
server.start();
```

**Purpose**: Simple entry point that imports the Playwright MCP server and starts it.

### Dockerfile

```dockerfile
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
CMD ["node", "./index.js"]
```

**Purpose**: Defines how to build the container image.

**Key Points**:
- Uses `node:20-slim` base image for small size
- `npm ci` for reproducible builds (requires package-lock.json)
- Copies source code after dependencies for better caching

### docker-compose.yml

```yaml
version: '3.8'

services:
  playwright-mcp-wrapper:
    build: .
    container_name: mcp-playwright-mcp-wrapper
    stdin_open: true
    tty: true
```

**Purpose**: Orchestrates the container with proper MCP protocol settings.

**Key Points**:
- `stdin_open: true` - Required for MCP stdio communication
- `tty: true` - Allocates pseudo-TTY for proper I/O handling

### routing_rules.py

```python
def route_playwright_query(query: str):
    """Route natural language queries to Playwright tools."""
    query_lower = query.lower()

    # Navigation
    if any(kw in query_lower for kw in ["navigate", "goto", "visit", "open"]):
        url_match = re.search(r'https?://\S+', query)
        if url_match:
            return ("browser_navigate", {"url": url_match.group()})

    # Clicking
    if "click" in query_lower:
        element = extract_element_description(query)
        return ("browser_click", {"element": element})

    # ... more routing logic
```

**Purpose**: Example implementation of natural language query routing.

**Integration**: Copy this logic into your `mcp-proxy.py` to enable the polymorphic tool pattern.

## 🧪 Testing the Container

### Test 1: Verify Container Builds

```bash
docker compose build
```

**Expected**: Build completes successfully with no errors.

### Test 2: Test MCP Protocol

```bash
docker compose up -d
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | docker compose run --rm playwright-mcp-wrapper node /app/index.js
```

**Expected**: JSON-RPC response with server capabilities.

### Test 3: List Available Tools

```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | docker compose run --rm playwright-mcp-wrapper node /app/index.js
```

**Expected**: List of 43 Playwright tools.

## 🎨 The Polymorphic Pattern

This example demonstrates the **Toolhost Pattern** (also known as polymorphic tool pattern):

### Traditional Approach

```
Claude sees 43 tools:
- browser_navigate(url)
- browser_click(element, ref)
- browser_type(element, ref, text)
- browser_screenshot(element?, ref?, filename?)
- browser_wait_for(text?, textGone?, time?)
... (38 more tools with complex parameters)
```

**Result**: 10,650 tokens consumed, complex parameter handling.

### Polymorphic Approach

```
Claude sees 1 tool:
- playwright_query(query: string)
```

**Example Calls**:
```
playwright_query("navigate to example.com")
playwright_query("click the login button")
playwright_query("type 'hello' in the search box")
playwright_query("take a screenshot")
```

**Result**: 100 tokens consumed, simple natural language interface.

## 🎯 How It Works: Dynamic Tool Exposure

**No manual integration needed!** The MCP proxy automatically handles tool exposure:

### When Container is Stopped
```
Claude sees: 1 polymorphic tool
- playwright_query(query: string)
Token cost: ~100 tokens
```

### When Container is Running
```
Claude sees: ALL 43 Playwright tools
- browser_navigate(url)
- browser_click(element, ref)
- browser_screenshot(...)
- ... (40 more tools)
Token cost: ~10,650 tokens (only while running)
```

### The Workflow
1. User: "navigate to example.com"
2. Claude calls: `playwright_query("navigate to example.com")`
3. Proxy starts container → sends `tools/list_changed` notification
4. Claude re-queries tools/list → sees ALL 43 tools
5. Claude picks best tool: `browser_navigate(url="example.com")`
6. Container executes → returns result
7. After 5 min idle → container auto-stops → back to polymorphic tool

**Key Point**: Claude's native tool selection handles routing - no manual code needed!

## 🔧 Integration with mcp-proxy.py

To integrate this example with the MCP proxy:

1. **Update Registry** (`~/.claude/mcp-docker-registry.json`):

```json
{
  "servers": {
    "playwright": {
      "friendly_name": "playwright",
      "image": "playwright-mcp-wrapper-playwright-mcp-wrapper:latest",
      "container_name": "mcp-playwright-mcp-wrapper",
      "compose_file": "/path/to/examples/playwright/docker-compose.yml",
      "polymorphic_tool": {
        "name": "playwright_query",
        "description": "Interact with web browsers using Playwright for automation and testing",
        "input": {"query": "Natural language browser interaction instruction"}
      },
      "triggers": ["playwright", "browser", "web", "automation", "screenshot", "click", "navigate"],
      "autoStop": true,
      "autoStopDelay": 300
    }
  }
}
```

2. **Restart Claude Code** to load the new configuration.

**That's it!** The proxy automatically handles:
- Exposing polymorphic tool when container is stopped
- Starting container on first call
- Sending `tools/list_changed` notification
- Exposing ALL 43 tools when container is running
- Claude's native tool selection does the routing

## 📈 Scaling This Pattern

This Playwright example is just one server. The same pattern works for:

- **DeepLake RAG**: `deeplake_query("search for X")`
- **Gemini MCP**: `gemini_query("analyze this code")`
- **Gmail MCP**: `gmail_query("send email to X")`
- **Any MCP Server**: `server_query("natural language instruction")`

**Token Impact** of 20 servers:
- Traditional: 20 × 15 tools × 250 tokens = 75,000 tokens
- Polymorphic: 20 × 1 tool × 100 tokens = 2,000 tokens
- **Savings**: 73,000 tokens (97.3%)

## 🎓 Learning Resources

- **[Playwright Tutorial](../../docs/PLAYWRIGHT_TUTORIAL.md)**: Complete step-by-step walkthrough
- **[MCP Librarian README](../../README.md)**: Project overview and quick start
- **[Automated Cataloging Guide](../../docs/MCP_DOCKERIZE_GUIDE.md)**: Deep dive into automation
- **[Playwright MCP Documentation](https://github.com/microsoft/playwright)**: Official Playwright docs

## 🐛 Troubleshooting

### Build Fails with "npm ci requires package-lock.json"

**Solution**: Generate it in the source directory:

```bash
npm install --package-lock-only
cp package-lock.json <build-context>/
```

### docker-compose.yml validation errors

**Problem**: Empty `environment:` or `volumes:` sections with comments.

**Solution**: Remove the empty sections entirely:

```yaml
# WRONG
environment:
  # No environment variables

# RIGHT
# (just omit the environment: key)
```

### Container won't accept stdin

**Problem**: MCP protocol requires stdin for communication.

**Solution**: Ensure docker-compose.yml has:

```yaml
stdin_open: true
tty: true
```

## 💡 Key Takeaways

1. **npx Servers Need Wrappers**: Create a minimal Node.js wrapper for npx-based servers
2. **Automation Has Limits**: Auto-generated files may need manual fixes (docker-compose.yml, package-lock.json)
3. **Token Savings Are Real**: 99% reduction (10,550 tokens saved) for this one server
4. **Pattern Is Reusable**: Same workflow works for ANY MCP server
5. **Integration Is Manual**: Routing rules must be integrated into mcp-proxy.py

---

*This example demonstrates the complete MCP Librarian workflow with real files, real issues, and real solutions.* 📚
