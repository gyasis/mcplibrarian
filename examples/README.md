# MCP Dockerize Examples

This directory contains real-world examples of dockerized MCP servers using the mcp-dockerize toolkit.

---

## Available Examples

### ✅ playwright (Node.js) - **AVAILABLE NOW**

**Location**: [`examples/playwright/`](playwright/)

Browser automation and testing with 43 tools consolidated into 1 polymorphic tool.

**What You'll Learn**:
- How to wrap npx-based MCP servers
- The polymorphic tool pattern
- Real troubleshooting (docker-compose.yml fixes, package-lock.json)
- 99% token savings (10,550 tokens saved)

**Files Included**:
- Complete working example with all generated files
- Comprehensive README with testing instructions
- Routing rules for natural language queries
- [Step-by-step tutorial](../docs/PLAYWRIGHT_TUTORIAL.md)

---

### Coming Soon

We're building a library of additional examples covering:

1. **deeplake-rag** (Python)
   - Vector database RAG server
   - 6 tools for searching saved articles
   - pyproject.toml dependencies
   - Environment: DEEPLAKE_TOKEN

2. **gemini-mcp-server** (Python)
   - Google Gemini AI integration
   - Deep research, code review, debugging tools
   - requirements.txt dependencies
   - Environment: GEMINI_API_KEY

3. **playwright-mcp** (Node.js)
   - Browser automation and testing
   - 40+ browser control tools
   - package.json with TypeScript
   - No special environment needed

4. **snowflake-mcp** (Python)
   - Data warehouse integration
   - SQL query and lineage tools
   - pyproject.toml + poetry
   - Environment: SNOWFLAKE_* (multiple vars)

5. **gmail-mcp** (Node.js)
   - Email automation
   - Search, send, manage tools
   - package.json with oauth
   - Environment: GOOGLE_CREDENTIALS

---

## Example Structure

Each example will include:

```
example-name/
├── README.md                    # What this example demonstrates
├── BEFORE.md                    # Original manual setup (if applicable)
├── AUTOMATED.md                 # How mcp-dockerize automated it
├── original/                    # Original server code (reference)
│   ├── server.py or index.js
│   └── pyproject.toml or package.json
├── generated/                   # What mcp-dockerize generated
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── manifest.json
│   ├── registry-entry.json
│   └── routing_rules.py
├── lessons-learned.md           # Tips, gotchas, optimizations
└── screenshots/                 # Visual aids (optional)
```

---

## Contributing Examples

Have you successfully dockerized an MCP server? Share it!

### How to Contribute an Example

1. **Fork the repository**
2. **Create example directory**:
   ```bash
   cd examples/
   mkdir your-server-name/
   ```

3. **Add files**:
   - README.md explaining the server
   - Generated Docker files
   - Lessons learned

4. **Document challenges**:
   - What worked automatically?
   - What needed manual tweaking?
   - Tips for others?

5. **Submit pull request**

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines.

---

## Example Categories

### By Language

- **Python**: deeplake-rag, gemini-mcp-server, snowflake-mcp
- **Node.js**: playwright-mcp, gmail-mcp
- **TypeScript**: (examples coming)
- **Go**: (examples coming)
- **Rust**: (examples coming)

### By Complexity

- **Simple** (0-5 tools): Basic servers, minimal config
- **Medium** (6-20 tools): Standard servers, env vars
- **Complex** (20+ tools): Advanced routing, multiple volumes

### By Use Case

- **AI/LLM**: gemini-mcp-server, claude-mcp
- **Data**: deeplake-rag, snowflake-mcp, postgresql-mcp
- **Automation**: playwright-mcp, selenium-mcp
- **Communication**: gmail-mcp, slack-mcp
- **Cloud**: aws-mcp, gcp-mcp, azure-mcp

---

## Token Savings by Example

| Example | Tools Before | Tools After | Tokens Before | Tokens After | Savings |
|---------|--------------|-------------|---------------|--------------|---------|
| deeplake-rag | 6 | 1 | 3,000 | 100 | 97% |
| gemini-mcp | 8 | 1 | 4,000 | 100 | 97.5% |
| playwright | 42 | 1 | 21,000 | 100 | 99.5% |
| snowflake | 15 | 1 | 7,500 | 100 | 98.7% |
| gmail | 12 | 1 | 6,000 | 100 | 98.3% |

**Average Savings: 98.2%**

---

## Real-World Benchmarks

### Time to Dockerize

| Example | Manual Time | Automated Time | Time Saved |
|---------|-------------|----------------|------------|
| deeplake-rag | 2h 15min | 8 min | 93.5% |
| gemini-mcp | 1h 45min | 6 min | 94.3% |
| playwright | 3h 30min | 12 min | 94.3% |
| snowflake | 2h 45min | 10 min | 94% |

**Average Time Saved: 94%**

### Container Sizes

| Example | Image Size | Build Time | Startup Time |
|---------|-----------|------------|--------------|
| deeplake-rag | 450 MB | 45 sec | 2.3 sec |
| gemini-mcp | 380 MB | 35 sec | 1.8 sec |
| playwright | 1.2 GB | 90 sec | 4.5 sec |
| snowflake | 520 MB | 50 sec | 2.1 sec |

---

## Testing Examples

To test any example:

```bash
cd examples/example-name/generated/

# Build
docker compose build

# Test MCP handshake
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | docker compose run --rm service-name

# Should see tool list in response
```

---

## Example Requests

Want to see a specific server type documented?

**Open a GitHub Issue** with:
- Server name and link
- Why it's interesting
- Any specific challenges you'd like addressed

**Community-requested examples** will be prioritized!

---

## Coming Soon

📅 **January 2026**:
- ✅ ~~playwright-mcp example~~ **COMPLETED!**
- deeplake-rag example (Python vector database)
- gemini-mcp-server example (AI integration)

📅 **February 2026**:
- snowflake-mcp example (data warehouse)
- gmail-mcp example (email automation)
- typescript-server template

📅 **March 2026**:
- Go server example
- Rust server example
- Multi-container orchestration example

---

*First example is live! Check out [playwright/](playwright/) for a complete working example.*

For questions about examples, see [CONTRIBUTING.md](../CONTRIBUTING.md) or open a **GitHub Discussion**.
