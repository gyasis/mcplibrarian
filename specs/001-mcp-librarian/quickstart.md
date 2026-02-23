# Quickstart: MCP Librarian Development Setup

**Date**: 2026-02-21
**Branch**: `001-mcp-librarian`

This guide gets a developer up and running to implement and test MCP Librarian features.

---

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.10+ | `python3 --version` |
| uv (Astral) | latest | `uv --version` |
| Docker | 20.10+ (v2 plugin) | `docker compose version` |
| jq | 1.6+ | `jq --version` |
| Git | any | `git --version` |

Install uv if missing:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Clone & Install

```bash
git clone https://github.com/gyasis/mcplibrarian.git
cd mcplibrarian

# Checkout the feature branch
git checkout 001-mcp-librarian

# Install all dependencies into .venv
uv sync

# Verify installation
uv run mcplibrarian --help
```

---

## Repository Layout

```text
mcplibrarian/
│
├── src/mcp_dockerize/          ← All Python source (extend here)
│   ├── cli.py                  ← Entry point: add new Click commands here
│   ├── detectors/              ← Runtime detection (python.py exists; node.py is NEW)
│   ├── generators/             ← File generation (dockerfile.py exists; compose.py is NEW)
│   ├── smart_scan/             ← NEW: issue detection + auto-fix engine
│   ├── registry/               ← NEW: JSON-backed registry CRUD
│   ├── health/                 ← NEW: 4-level MCP health checks
│   ├── platforms/              ← NEW: platform config file updaters
│   ├── builders/               ← Docker image builder (exists)
│   ├── testers/                ← MCP protocol tester (exists, will evolve into health/)
│   └── templates/              ← Jinja2 templates (directory exists, files NEEDED)
│
├── tests/                      ← NEW: create this directory
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│       ├── sample-python-server/
│       └── sample-node-server/
│
├── wrap-mcp.sh                 ← NEW: Option B shell wrapper
├── list-wrapped.sh             ← NEW: Option B list helper
├── health-check.sh             ← NEW: Option B health check
├── unwrap-mcp.sh               ← NEW: Option B unwrap helper
│
├── docker-configs/             ← Generated configs (git-ignored in production)
├── pyproject.toml              ← Add new deps here; use `uv add <pkg>`
└── specs/001-mcp-librarian/    ← This feature's design docs
```

---

## Running the CLI

```bash
# Dry-run first to see what would happen (no changes)
mcplibrarian wrap /path/to/server --dry-run

# Wrap a server (generates Dockerfile + docker-compose.yml, builds, registers)
mcplibrarian wrap /path/to/python-mcp-server

# Wrap with verbose output and specific platform
mcplibrarian wrap /path/to/server --platform cursor --verbose

# Batch wrap all servers in a directory
mcplibrarian wrap-all /path/to/servers/ --yes

# Scan without building (analysis only)
mcplibrarian scan /path/to/server

# List all wrapped servers
mcplibrarian list

# Check health
mcplibrarian health

# Check what's generated
ls ~/.config/mcp-librarian/servers/<server-name>/
```

---

## Running Tests

```bash
# Unit tests (fast, no Docker required)
uv run pytest tests/unit/ -v

# Integration tests (requires Docker daemon running)
uv run pytest tests/integration/ -v

# All tests with coverage
uv run pytest --cov=mcp_dockerize --cov-report=term-missing

# Single test file
uv run pytest tests/unit/test_node_detector.py -v
```

---

## Adding a Dependency

```bash
# Add a runtime dependency
uv add <package-name>

# Add a dev/test dependency
uv add --dev <package-name>

# uv.lock is updated automatically — commit it
git add pyproject.toml uv.lock
```

---

## Key Development Workflows

### Implement a new detector (e.g., Node.js)

1. Create `src/mcp_dockerize/detectors/node.py`
2. Implement `can_detect(path: Path) -> bool`
3. Implement `detect(path: Path) -> NodeServerMetadata`
4. Create fixture: `tests/fixtures/sample-node-server/` with a minimal `package.json`
5. Write unit tests: `tests/unit/test_node_detector.py`
6. Wire into `cli.py`: try `NodeDetector` before existing `PythonDetector`

### Implement a Smart-Scan fix

1. Add new `IssueType` variant to `src/mcp_dockerize/smart_scan/issues.py`
2. Add detection logic in the relevant detector
3. Implement fix in `src/mcp_dockerize/smart_scan/fixer.py`
4. Write unit test with a fixture server that exhibits the issue

### Test the full wrap flow end-to-end

```bash
# Using a real Node.js MCP server
uv run mcplibrarian wrap /path/to/node-mcp-server --verbose

# Dry run first (no changes)
uv run mcplibrarian wrap /path/to/node-mcp-server --dry-run

# Check registry after wrap
uv run mcplibrarian list

# Health check
uv run mcplibrarian health playwright-mcp
```

### Test Option B shell wrappers

```bash
chmod +x wrap-mcp.sh list-wrapped.sh health-check.sh unwrap-mcp.sh

# Wrap a server
./wrap-mcp.sh /path/to/node-mcp-server

# List all wrapped
./list-wrapped.sh

# Check health
./health-check.sh playwright-mcp

# Remove
./unwrap-mcp.sh playwright-mcp
```

---

## Critical Rules (from project CLAUDE.md)

1. **Credentials NEVER in Docker images** — use `env_file:` in docker-compose.yml, never `ENV` for secrets
2. **Type: bind syntax** — always use explicit `source:`/`target:` fields, never short-hand `./path:/container`
3. **Absolute paths** — always resolve paths before writing to docker-compose.yml
4. **`docker compose` (no hyphen)** — Docker v2 plugin syntax only
5. **Scan limits** — only scan named entry point files, never `node_modules`, `.venv`, `__pycache__`
6. **Human-readable errors** — no raw Docker errors to the user; wrap with `[ERROR]` prefix + actionable instruction

---

## Registry Location

The registry is a JSON file at `~/.config/mcp-librarian/registry.json`. During development, inspect it directly:

```bash
cat ~/.config/mcp-librarian/registry.json | jq .
```

Reset for a clean state during testing:

```bash
rm ~/.config/mcp-librarian/registry.json
```

---

## Platform Config Files (for manual inspection)

| Platform | Config Path |
|----------|------------|
| Claude Code | `~/.config/Claude/claude_desktop_config.json` |
| Cursor | `~/.cursor/mcp.json` |
| VS Code Copilot | `~/.config/Code/User/settings.json` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` |
| Continue.dev | `~/.continue/config.json` |

Always validate JSON syntax after editing:
```bash
jq . ~/.config/Claude/claude_desktop_config.json > /dev/null && echo "Valid"
```

---

## Useful Docker Commands

```bash
# Check a generated config is valid
docker compose -f ~/.config/mcp-librarian/<name>/docker-compose.yml config

# Build
docker compose -f ~/.config/mcp-librarian/<name>/docker-compose.yml build

# Run and test MCP protocol
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
  docker compose -f ~/.config/mcp-librarian/<name>/docker-compose.yml run --rm <name>

# List all mcplibrarian images
docker images | grep mcplibrarian
```
