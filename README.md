# mcplibrarian

**Automatically wrap MCP servers in Docker containers with lazy loading**

## Overview

`mcplibrarian` is a CLI tool that:
- Auto-detects MCP server type (Python FastMCP, Node.js MCP SDK)
- Generates optimized Dockerfiles with security best practices
- Handles credentials securely (volume mounts, no baked secrets)
- Outputs Claude Code-compatible configurations
- Enables automatic lazy loading via Docker containers

## Installation

```bash
cd mcplibrarian
uv pip install -e .
```

## Usage

```bash
# Auto-dockerize an MCP server
mcplibrarian /path/to/mcp-server

# With options
mcplibrarian --output ./docker-configs --build /path/to/mcp-server
```

## Expected Token Savings

When combined with the mcp-proxy system:
- **Before:** 15,000 tokens (all MCP servers loaded)
- **After:** 1,500 tokens (only proxy registry loaded)
- **Savings:** 13,500 tokens (90% reduction)

## Part of Token Optimization Suite

This tool is part of a comprehensive token optimization strategy:

1. ✅ **Phase 1:** Disable unused MCP servers (~30k tokens saved)
2. ✅ **Phase 2:** Skills progressive disclosure (~37k tokens saved)
3. 🚧 **Phase 3:** Docker lazy loading (~13.5k tokens saved) ← You are here

**Total expected savings:** 80,500 tokens (85% reduction)

## Project Structure

```
mcplibrarian/
├── src/mcp_dockerize/
│   ├── cli.py              # Main CLI
│   ├── detectors/
│   │   └── python.py       # Python FastMCP detector
│   ├── generators/
│   │   └── dockerfile.py   # Dockerfile generator
│   └── templates/          # Jinja2 templates
├── pyproject.toml
└── README.md
```

## License

MIT
