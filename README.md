# mcplibrarian

**One-command MCP server containerization — works across every AI coding assistant**

## The Problem

Every AI coding assistant (Cursor, VS Code Copilot, Windsurf, Goose, Continue.dev) loads all MCP tool definitions into context at startup. With 10+ servers, that's 30–100k tokens consumed before you type a single prompt.

Claude Code solved this natively in January 2026 with `defer_loading`. **Everyone else is still waiting.**

mcplibrarian gives Cursor, VS Code, Windsurf, and other platform users what Claude Code users now get natively — lazy-loaded, containerized MCP servers with a single command.

## Platform Support Matrix

| Platform | Native Lazy Loading | mcplibrarian Helps? |
|----------|--------------------|--------------------|
| Claude Code | ✅ Native (`defer_loading`) | For security & portability |
| **Cursor IDE** | ❌ None | **Yes — primary use case** |
| **VS Code Copilot** | ❌ None | **Yes — primary use case** |
| **Windsurf** | ❌ None | **Yes — primary use case** |
| **Continue.dev** | ❌ None (client-side) | **Yes — primary use case** |
| **Block's Goose** | Partial (own paradigm) | **Yes** |
| **opencode (SST)** | ❌ None (Issue #9350 open) | **Yes — primary use case** |
| **OpenAI Codex** | Alternative (Skills/AGENTS.md) | **Yes** |

## What It Does

- **Auto-detects** MCP server type (Python FastMCP, Node.js MCP SDK)
- **Generates** optimized Dockerfiles, `docker-compose.yml`, and README configs
- **Handles credentials securely** — no secrets baked into images, mounts via env_file
- **Handles edge cases** — paths with spaces, hardcoded paths in server code
- **Works with any platform** — outputs standard Docker configs, not platform-specific

## Installation

```bash
cd mcplibrarian
uv pip install -e .
```

## Usage

```bash
# Containerize an MCP server
mcplibrarian /path/to/mcp-server

# With build automation
mcplibrarian --output ./docker-configs --build /path/to/mcp-server
```

## Why Docker Containers?

Even on platforms with native lazy loading, containerized MCP servers provide:

1. **Security isolation** — servers can't access your host filesystem unless explicitly allowed
2. **Reproducibility** — same container works on any machine, any platform
3. **Team portability** — share one `docker-compose.yml` instead of per-developer setup
4. **Resource control** — stop idle containers, limit CPU/RAM per server

## Token Savings (Cursor, VS Code, Windsurf)

Using mcplibrarian with a Docker proxy pattern:

| Before | After | Savings |
|--------|-------|---------|
| All 10 servers loaded at startup (~50k tokens) | Proxy index only (~1.5k tokens) | ~97% |

## Part of a Broader Token Strategy

1. ✅ Disable unused MCP servers (~30k tokens saved)
2. ✅ Skills progressive disclosure (~37k tokens saved)
3. 🚧 Docker lazy loading (~13.5k tokens saved) ← This tool

## Project Structure

```
mcplibrarian/
├── src/mcp_dockerize/
│   ├── cli.py              # Main CLI
│   ├── detectors/
│   │   └── python.py       # Python FastMCP detector
│   ├── generators/
│   │   └── dockerfile.py   # Dockerfile generator
│   └── templates/          # Jinja2 templates (in progress)
├── pyproject.toml
└── README.md
```

## Status

**Current:** Python FastMCP servers fully supported. Node.js support in progress.

See [progress tracker](memory-bank/progress.md) for full milestone status.

## License

MIT
