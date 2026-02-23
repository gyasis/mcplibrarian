# mcplibrarian

**One-command MCP server containerization — works across every AI coding assistant**

## The Problem

Every AI coding assistant (Cursor, VS Code Copilot, Windsurf, Goose, Continue.dev) loads all MCP tool
definitions into context at startup. With 10+ servers, that's 30-100k tokens consumed before you type
a single prompt.

Claude Code solved this natively in January 2026 with `defer_loading`. **Everyone else is still
waiting.**

mcplibrarian gives Cursor, VS Code, Windsurf, and other platform users what Claude Code users now get
natively — lazy-loaded, containerized MCP servers with a single command.

---

## Quick Start

```bash
# Install
cd mcplibrarian
uv pip install -e .

# Containerize a server (auto-detects Python/Node, builds, health-checks, registers)
mcplibrarian wrap /path/to/my-mcp-server

# Containerize for a specific AI platform
mcplibrarian wrap /path/to/my-mcp-server --platform cursor

# Containerize for multiple platforms at once
mcplibrarian wrap /path/to/my-mcp-server --platform cursor --platform vscode

# Preview what would happen without doing it
mcplibrarian wrap /path/to/my-mcp-server --dry-run

# Batch-containerize all servers in a directory
mcplibrarian wrap-all ~/my-mcp-servers/

# List all registered servers
mcplibrarian list

# Check health of all servers
mcplibrarian health

# Check health of one server and attempt recovery if unhealthy
mcplibrarian health my-server --recover
```

---

## Supported Platforms

| Platform ID  | AI Tool           | Config File                                      | Format |
|-------------|-------------------|--------------------------------------------------|--------|
| `claude_code` | Claude Code (Desktop) | `~/.config/Claude/claude_desktop_config.json` | JSON   |
| `cursor`    | Cursor IDE        | `~/.cursor/mcp.json`                             | JSON   |
| `vscode`    | VS Code Copilot   | `~/.config/Code/User/settings.json`              | JSON   |
| `goose`     | Block's Goose     | `~/.config/goose/config.yaml`                    | YAML   |
| `codex`     | OpenAI Codex      | `~/.codex/config.yaml`                           | YAML   |
| `opencode`  | opencode (SST)    | `~/.config/opencode/config.json`                 | JSON   |

### Platform Support Matrix

| Platform      | Native Lazy Loading              | mcplibrarian Helps? |
|---------------|----------------------------------|---------------------|
| Claude Code   | Native (`defer_loading`)         | For security and portability |
| Cursor IDE    | None                             | Yes — primary use case |
| VS Code Copilot | None                           | Yes — primary use case |
| Windsurf      | None                             | Yes — primary use case |
| Continue.dev  | None (client-side)               | Yes — primary use case |
| Block's Goose | Partial (own paradigm)           | Yes |
| opencode (SST) | None (Issue #9350 open)         | Yes — primary use case |
| OpenAI Codex  | Alternative (Skills/AGENTS.md)   | Yes |

---

## Installation

```bash
cd mcplibrarian
uv pip install -e .
```

Requires Python 3.10+ and Docker (v2 plugin — `docker compose`, not `docker-compose`).

---

## CLI Reference

### `mcplibrarian wrap <SERVER_PATH>`

Containerize a single MCP server. Auto-detects runtime (Python FastMCP or Node.js MCP SDK),
generates a Dockerfile and `docker-compose.yml`, builds the image, runs a 4-level health check,
registers the server in the local registry, and updates the target platform config.

```
Usage: mcplibrarian wrap [OPTIONS] SERVER_PATH

Arguments:
  SERVER_PATH   Path to the MCP server directory (must exist)  [required]

Options:
  -o, --output TEXT        Output directory for Docker configs
                           [default: ./docker-configs]
  -n, --name TEXT          Container name (auto-detected from project if omitted)
  --platform TEXT          Target platform ID. Pass multiple times for
                           multiple platforms.
                           [default: claude_code]
                           Choices: claude_code, cursor, vscode, goose, codex, opencode
  --build                  Build Docker image after generating configs
  --test                   Test container after building
  --no-health-check        Skip the 4-level health check after build
  --no-register            Skip adding the server to the local registry
  --force                  Re-wrap even if this server is already registered
  --dry-run                Print what would be done and exit without making
                           any changes
  -v, --verbose            Show detailed step output including server metadata
                           and full error tracebacks
  --version                Show version and exit
  --help                   Show this message and exit

Exit codes:
  0  Success — server wrapped, health-checked, and registered
  1  Runtime error — scan failed, build failed, or health check failed
  2  Configuration error — invalid platform ID or missing required config
```

**Examples:**

```bash
# Wrap a Python FastMCP server with defaults (claude_code platform)
mcplibrarian wrap ~/projects/my-python-server

# Wrap with a custom container name
mcplibrarian wrap ~/projects/my-python-server --name my-custom-name

# Wrap and register for both Cursor and VS Code
mcplibrarian wrap ~/projects/my-node-server --platform cursor --platform vscode

# See every step in detail without side effects
mcplibrarian wrap ~/projects/my-python-server --dry-run --verbose

# Force re-wrap an already-registered server
mcplibrarian wrap ~/projects/my-python-server --force

# Wrap and skip automatic platform config update
mcplibrarian wrap ~/projects/my-python-server --no-register
```

---

### `mcplibrarian wrap-all <SCAN_DIR>`

Discover and batch-containerize all MCP servers found within a directory tree (up to 2 levels deep).
Runs wraps in parallel. Skips directories that are already registered unless `--force` is passed.
Prints a live status line per server and a final summary table.

```
Usage: mcplibrarian wrap-all [OPTIONS] SCAN_DIR

Arguments:
  SCAN_DIR   Directory to scan for MCP servers  [required]

Options:
  --workers INTEGER        Maximum parallel wrap jobs [default: 4, max: 8]
  --platform TEXT          Target platform ID. Pass multiple times.
                           [default: claude_code]
  --skip-existing          Skip servers already in the registry [default: True]
  --force                  Re-wrap all servers, including already-registered ones
  --filter TEXT            Glob pattern to restrict which server directories are
                           processed (e.g. "my-*")
  --yes                    Skip the confirmation prompt before starting
  --help                   Show this message and exit

Exit codes:
  0  All discovered servers wrapped successfully
  1  One or more servers failed to wrap
```

**Examples:**

```bash
# Wrap all MCP servers found under ~/mcp-servers/
mcplibrarian wrap-all ~/mcp-servers/

# Batch wrap with 8 parallel workers, skipping confirmation
mcplibrarian wrap-all ~/mcp-servers/ --workers 8 --yes

# Wrap only servers whose directory name starts with "fs-"
mcplibrarian wrap-all ~/mcp-servers/ --filter "fs-*"

# Re-wrap everything (including already-registered servers) for VS Code
mcplibrarian wrap-all ~/mcp-servers/ --force --platform vscode

# Dry run across a directory tree (uses wrap --dry-run per server)
mcplibrarian wrap-all ~/mcp-servers/ --yes --workers 1
```

---

### `mcplibrarian health [SERVER_NAME]`

Run a 4-level health check against one server (by name) or all registered servers.

Health levels checked:
- **L1** — Docker container state (`docker inspect`)
- **L2** — MCP protocol responds (`initialize` JSON-RPC handshake)
- **L3** — Tools available (`tools/list` returns non-empty array)
- **L4** — Response time measured (milliseconds for L2)

```
Usage: mcplibrarian health [OPTIONS] [SERVER_NAME]

Arguments:
  SERVER_NAME   Name of a registered server (optional — omit to check all)

Options:
  --recover     Attempt `docker compose restart` and recheck if unhealthy
  --history     Show the last 24 hours of health check results as a table
  --json        Output results as a JSON array
  --help        Show this message and exit

Exit codes:
  0  All checked servers are healthy or stopped
  1  One or more servers are unhealthy
```

**Examples:**

```bash
# Check health of all registered servers
mcplibrarian health

# Check one server and auto-recover if unhealthy
mcplibrarian health my-python-server --recover

# Show health history for the last 24 hours
mcplibrarian health my-python-server --history

# Output health status as JSON (useful for scripting)
mcplibrarian health --json
```

---

### `mcplibrarian list`

List all servers registered in the local registry (`~/.config/mcp-librarian/registry.json`).
Displays name, runtime, status, registered platforms, and last health check result.

```
Usage: mcplibrarian list [OPTIONS]

Options:
  --json        Output as a JSON array of registry entries
  --status TEXT Filter by status (e.g. healthy, stopped, unhealthy)
  --help        Show this message and exit

Exit codes:
  0  Always (even if the registry is empty)
```

**Examples:**

```bash
# List all registered servers in a table
mcplibrarian list

# Output as JSON
mcplibrarian list --json

# Show only healthy servers
mcplibrarian list --status healthy
```

---

### `mcplibrarian status <SERVER_NAME>`

Show detailed information about a single registered server: source path, Docker config path,
registered platforms, current health summary, and registration date.

```
Usage: mcplibrarian status [OPTIONS] SERVER_NAME

Arguments:
  SERVER_NAME   Name of a registered server  [required]

Options:
  --json        Output the full registry entry as JSON
  --help        Show this message and exit

Exit codes:
  0  Server found and status displayed
  1  Server not found in registry
```

**Examples:**

```bash
# Show status of a specific server
mcplibrarian status my-python-server

# Get full registry entry as JSON (useful for scripting)
mcplibrarian status my-python-server --json
```

---

### `mcplibrarian remove <SERVER_NAME>`

Remove a server from the registry, clean up its Docker config files, and remove its entry from all
registered platform configs. Never touches the original MCP server source directory.

```
Usage: mcplibrarian remove [OPTIONS] SERVER_NAME

Arguments:
  SERVER_NAME   Name of a registered server to remove  [required]

Options:
  --keep-config           Keep the generated Docker configs directory
                          (~/.config/mcp-librarian/<name>/)
  --keep-platform-entry   Do not remove the entry from platform config files
  --yes                   Skip the confirmation prompt
  --help                  Show this message and exit

Exit codes:
  0  Server removed successfully (or was not registered)
  1  Removal failed (e.g. permission error)
```

**Examples:**

```bash
# Remove a server with confirmation prompt
mcplibrarian remove my-python-server

# Remove without prompting (useful in scripts)
mcplibrarian remove my-python-server --yes

# Remove from registry but keep the generated Docker configs
mcplibrarian remove my-python-server --keep-config --yes

# Remove from registry but leave platform config files untouched
mcplibrarian remove my-python-server --keep-platform-entry --yes
```

---

### `mcplibrarian scan <SERVER_PATH>`

Analyze an MCP server directory and report what Smart-Scan detects — runtime, entry point,
environment variables, data volumes, and any blocking or warning issues — without building
anything. Optionally apply auto-fixes (e.g. generate a missing `package-lock.json`).

```
Usage: mcplibrarian scan [OPTIONS] SERVER_PATH

Arguments:
  SERVER_PATH   Path to the MCP server directory to analyze  [required]

Options:
  --fix         Apply auto-fixable issues without building a container
  --json        Output detected metadata and issues as JSON
  --help        Show this message and exit

Exit codes:
  0  No blocking issues detected
  1  One or more blocking issues remain after analysis (or after --fix)
```

**Examples:**

```bash
# Analyze a server directory and print a report
mcplibrarian scan ~/projects/my-mcp-server

# Analyze and auto-fix issues (e.g. generate missing package-lock.json)
mcplibrarian scan ~/projects/my-mcp-server --fix

# Get machine-readable output
mcplibrarian scan ~/projects/my-mcp-server --json
```

---

## Shell Wrappers (Planned — Phase 8)

For environments where Python is not available, the following shell wrappers will be provided at
the repo root. They require only `bash`, `jq`, and `docker`.

| Script             | Equivalent CLI Command           | Description                                  |
|--------------------|----------------------------------|----------------------------------------------|
| `wrap-mcp.sh <path>` | `mcplibrarian wrap <path>`     | Containerize one server (shell fallback)     |
| `list-wrapped.sh`  | `mcplibrarian list`              | List all wrapped servers and their status    |
| `health-check.sh [name]` | `mcplibrarian health [name]` | Run L1+L2 health check in pure shell       |
| `unwrap-mcp.sh <name>` | `mcplibrarian remove <name>` | Remove a server from registry and configs   |

**Usage (once available):**

```bash
# Wrap a server using the shell fallback
./wrap-mcp.sh /path/to/my-mcp-server

# Wrap and target a specific platform
./wrap-mcp.sh /path/to/my-mcp-server cursor

# List all wrapped servers with running status
./list-wrapped.sh

# Check health of all servers
./health-check.sh

# Check health of one server
./health-check.sh my-python-server

# Remove a server
./unwrap-mcp.sh my-python-server
```

---

## What It Does

- **Auto-detects** MCP server type (Python FastMCP, Node.js MCP SDK)
- **Generates** optimized Dockerfiles, `docker-compose.yml`, and `.env.example` configs
- **Handles credentials securely** — no secrets baked into images, mounted via `env_file`
- **Handles edge cases** — paths with spaces, missing lock files, hardcoded paths in server code
- **Works with any platform** — outputs standard Docker configs consumed by every AI tool

---

## Why Docker Containers?

Even on platforms with native lazy loading, containerized MCP servers provide:

1. **Security isolation** — servers cannot access your host filesystem unless explicitly allowed
2. **Reproducibility** — the same container works on any machine and any platform
3. **Team portability** — share one `docker-compose.yml` instead of per-developer setup scripts
4. **Resource control** — stop idle containers, limit CPU/RAM per server

---

## Token Savings (Cursor, VS Code, Windsurf)

Using mcplibrarian with a Docker proxy pattern:

| Before | After | Savings |
|--------|-------|---------|
| All 10 servers loaded at startup (~50k tokens) | Proxy index only (~1.5k tokens) | ~97% |

---

## Part of a Broader Token Strategy

1. Disable unused MCP servers (~30k tokens saved)
2. Skills progressive disclosure (~37k tokens saved)
3. Docker lazy loading (~13.5k tokens saved) — this tool

---

## Project Structure

```
mcplibrarian/
├── src/mcp_dockerize/
│   ├── cli.py                      # Click CLI group and all subcommands
│   ├── detectors/
│   │   ├── base.py                 # AbstractDetector interface
│   │   ├── python.py               # Python/FastMCP detector
│   │   └── node.py                 # Node.js/MCP SDK detector
│   ├── generators/
│   │   ├── dockerfile.py           # Dockerfile generator
│   │   └── compose.py              # docker-compose.yml generator
│   ├── templates/                  # Jinja2 templates
│   │   ├── python-uv.Dockerfile.j2
│   │   ├── python-direct.Dockerfile.j2
│   │   ├── node-npm.Dockerfile.j2
│   │   ├── docker-compose.yml.j2
│   │   └── env-example.j2
│   ├── platforms/
│   │   ├── base.py                 # AbstractPlatform interface
│   │   ├── claude_code.py          # Claude Desktop config integration
│   │   ├── cursor.py               # Cursor IDE config integration
│   │   ├── vscode.py               # VS Code settings.json integration
│   │   ├── goose.py                # Block's Goose YAML integration
│   │   ├── codex.py                # OpenAI Codex YAML + shell wrapper
│   │   └── opencode.py             # opencode JSON config integration
│   ├── smart_scan/
│   │   ├── issues.py               # IssueType, Severity, Issue, Fix dataclasses
│   │   ├── scanner.py              # SmartScan orchestrator
│   │   └── fixer.py                # AutoFixer strategies
│   ├── health/
│   │   ├── states.py               # HealthStatus enum and HealthCheckResult
│   │   └── checker.py              # 4-level MCPHealthChecker
│   └── registry/
│       ├── models.py               # RegistryEntry and related dataclasses
│       └── store.py                # RegistryStore (reads/writes ~/.config/mcp-librarian/)
├── tests/
│   ├── fixtures/
│   │   ├── sample-python-server/   # Minimal FastMCP stub for testing
│   │   └── sample-node-server/     # Minimal Node.js MCP stub for testing
│   ├── unit/
│   └── integration/
├── pyproject.toml
└── README.md
```

---

## Status

**Current:** Python FastMCP and Node.js servers detected. Claude Code, Cursor, VS Code, Goose,
Codex, and opencode platforms implemented. Core `wrap` command functional.

See [progress tracker](memory-bank/progress.md) for full milestone status.

---

## License

MIT
