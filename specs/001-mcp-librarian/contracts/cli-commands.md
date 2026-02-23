# CLI Contract: mcplibrarian

**Date**: 2026-02-21
**Branch**: `001-mcp-librarian`
**Tool**: `mcplibrarian` (extends existing `src/mcp_dockerize/cli.py`)

This document specifies the complete CLI interface contract. Each command defines its signature, inputs, outputs, exit codes, and observable behaviour. Implementations must conform to this contract; tests must validate it.

---

## Global Flags

These flags apply to all commands:

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--verbose` | `-v` | flag | off | Show step-by-step progress with detailed output |
| `--dry-run` | | flag | off | Show what would happen without making changes |
| `--platform` | `-p` | string | `claude_code` | Target AI platform for config update (`claude_code`, `cursor`, `vscode`, `goose`, `codex`, `opencode`) |
| `--output-dir` | `-o` | path | `~/.config/mcp-librarian/` | Directory for generated container configs |

---

## Command: `wrap`

Containerize a single MCP server end-to-end: detect, smart-scan, fix, generate config, build image, health check, register, update platform config.

### Signature

```
mcplibrarian wrap <SERVER_PATH> [OPTIONS]
```

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `SERVER_PATH` | path | YES | Absolute or relative path to the MCP server source directory |

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--name` | `-n` | string | auto | Override the server name (must match `[a-z0-9-_]+`) |
| `--platform` | `-p` | string | `claude_code` | One or more platforms to register with (repeatable: `-p claude_code -p cursor`). Valid values: `claude_code`, `cursor`, `vscode`, `goose`, `codex`, `opencode` |
| `--no-health-check` | | flag | off | Skip health check after build (faster, not recommended) |
| `--no-register` | | flag | off | Generate config and build but do not add to registry |
| `--force` | `-f` | flag | off | Re-wrap even if server is already registered |
| `--workers` | | int | — | Not applicable to single wrap |

### Behaviour

1. Validate `SERVER_PATH` exists and is a directory
2. Run Smart-Scan:
   - Detect runtime and entry point
   - Detect env vars and data volumes
   - Identify and auto-fix blocking issues
3. Generate `ContainerConfig` files into `~/.config/mcp-librarian/<name>/`
4. Run `docker compose build`
5. Run 4-level health check
6. Add `RegistryEntry` (unless `--no-register`)
7. Update platform config file(s) (unless `--no-register`)
8. Print success summary

### Standard Output (human-readable)

```
[Scan]     Detected Node.js 20 server: playwright-mcp
[Scan]     Found 1 issue: missing package-lock.json (blocking)
[Fix]      Generated package-lock.json using node:20-slim
[Generate] Created container config → ~/.config/mcp-librarian/playwright-mcp/
[Build]    Building image... done (18s)
[Health]   Container: ✓  Protocol: ✓  Tools: ✓  Response: 340ms
[Registry] Registered playwright-mcp
[Platform] Updated ~/.config/Claude/claude_desktop_config.json
✓ playwright-mcp is ready. Restart your AI platform to load it.
```

### Standard Output (`--dry-run`)

```
[DRY RUN] Would generate config at ~/.config/mcp-librarian/playwright-mcp/
[DRY RUN] Would build image: mcplibrarian-playwright-mcp:latest
[DRY RUN] Would register server in registry
[DRY RUN] Would update claude_code config at ~/.config/Claude/claude_desktop_config.json
No changes made.
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Server detection failed (unsupported runtime) |
| 2 | Unresolvable blocking issue (user action required) |
| 3 | Docker build failed |
| 4 | Health check failed after recovery attempt |
| 5 | Registry write failed |
| 6 | Platform config update failed (config file has syntax errors) |
| 7 | Server already registered (use `--force` to override) |

### Errors (stderr)

Errors follow the format: `[ERROR] <short description>\n  → <actionable instruction>`

Examples:
```
[ERROR] package-lock.json could not be generated
  → Ensure Docker is running: docker info
  → Or run manually: npm install --package-lock-only in /path/to/server

[ERROR] claude_desktop_config.json has a JSON syntax error
  → Fix the syntax error in ~/.config/Claude/claude_desktop_config.json
  → Validator: jq . ~/.config/Claude/claude_desktop_config.json
```

---

## Command: `wrap-all`

Batch-wrap all MCP servers found within a directory, processing them concurrently.

### Signature

```
mcplibrarian wrap-all <SCAN_DIR> [OPTIONS]
```

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `SCAN_DIR` | path | YES | Directory to scan for MCP servers |

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--workers` | `-w` | int | 4 | Max concurrent builds (1–8) |
| `--platform` | `-p` | string | `claude_code` | Platform(s) to register with (repeatable) |
| `--skip-existing` | | flag | on | Skip servers already in registry (default) |
| `--force` | `-f` | flag | off | Re-wrap all, including already-registered |
| `--filter` | | string | — | Glob pattern to filter server directories (e.g. `"*-mcp"`) |

### Behaviour

1. Recursively scan `SCAN_DIR` (max depth 2) for server directories containing `package.json` or `pyproject.toml`
2. Filter out directories that are clearly not MCP servers (e.g. `node_modules`, `.venv`)
3. Display discovered servers and prompt for confirmation (skip with `--yes`)
4. Wrap servers concurrently (`--workers` pool)
5. Live progress: one line per server updated in-place
6. On completion, print summary table

### Standard Output

```
Found 10 MCP servers in ~/mcp-servers/

  playwright-mcp     Node 20   [    wrapping...]
  github-mcp         Node 20   [    wrapping...]
  deeplake-rag       Python 3.10 [ pending    ]
  slack-mcp          Node 20   [    pending   ]
  ...

playwright-mcp   ✓ 22s
github-mcp       ✓ 19s
deeplake-rag     ✓ 31s
slack-mcp        ✗ Failed: missing SLACK_TOKEN (blocking, not auto-fixable)

Summary: 9 succeeded, 1 failed
  ✗ slack-mcp — set SLACK_TOKEN in environment or .env file and retry
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All servers wrapped successfully |
| 1 | One or more servers failed (partial success) |
| 2 | No MCP servers found in `SCAN_DIR` |
| 3 | `SCAN_DIR` does not exist |

---

## Command: `list`

Display all servers registered in the local registry.

### Signature

```
mcplibrarian list [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--json` | | flag | off | Output as JSON array instead of table |
| `--status` | | string | — | Filter by status: `active`, `stopped`, `unhealthy`, `error` |

### Standard Output

```
NAME               RUNTIME   STATUS     PLATFORMS          LAST HEALTH
playwright-mcp     node      active     claude_code        ✓ 340ms (2m ago)
github-mcp         node      active     claude_code,cursor ✓ 120ms (5m ago)
deeplake-rag       python    stopped    claude_code        — (stopped)
slack-mcp          node      error      claude_code        ✗ build failed
```

### JSON Output (`--json`)

```json
[
  {
    "name": "playwright-mcp",
    "runtime": "node",
    "status": "active",
    "registered_platforms": ["claude_code"],
    "health": { "status": "healthy", "response_time_ms": 340, "last_check": "2026-02-21T10:03:00Z" }
  }
]
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (even if registry is empty) |
| 1 | Registry file is corrupted |

---

## Command: `status`

Show detailed status for a single registered server.

### Signature

```
mcplibrarian status <SERVER_NAME> [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--history` | | flag | off | Show last 24 h of health check results |
| `--json` | | flag | off | Output as JSON |

### Standard Output

```
playwright-mcp
  Runtime:      Node 20
  Source:       /home/user/playwright-mcp
  Config:       ~/.config/mcp-librarian/playwright-mcp/docker-compose.yml
  Platforms:    claude_code, cursor
  Status:       active
  Health:       ✓ healthy (340ms, checked 2 minutes ago)
  Registered:   2026-02-20 10:00
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Server not found in registry |

---

## Command: `health`

Run a health check against one or all servers and display results.

### Signature

```
mcplibrarian health [SERVER_NAME] [OPTIONS]
```

### Arguments

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `SERVER_NAME` | string | NO | If omitted, checks all registered servers |

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--recover` | | flag | off | Attempt automatic recovery for unhealthy servers |
| `--json` | | flag | off | Output as JSON |

### Standard Output (single server)

```
playwright-mcp health check:
  L1 Container running:   ✓
  L2 MCP initialize:      ✓ (340ms)
  L3 Tools available:     ✓ (12 tools)
  L4 Response time:       ✓ 340ms < 5000ms threshold

Overall: healthy
```

### Standard Output (all servers)

```
NAME               STATUS     RESPONSE
playwright-mcp     healthy    340ms
github-mcp         healthy    120ms
deeplake-rag       stopped    —
slack-mcp          unhealthy  timeout
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checked servers are healthy or stopped |
| 1 | One or more servers are unhealthy |
| 2 | Server not found in registry |

---

## Command: `remove`

Remove a server from the registry and optionally from platform configs.

### Signature

```
mcplibrarian remove <SERVER_NAME> [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--keep-config` | | flag | off | Keep generated container config files on disk |
| `--keep-platform-entry` | | flag | off | Do not remove the entry from platform config files |
| `--yes` | `-y` | flag | off | Skip confirmation prompt |

### Behaviour

1. Confirm with user (unless `--yes`)
2. Remove `RegistryEntry` from registry
3. Remove server entry from platform config files (unless `--keep-platform-entry`)
4. Delete generated config directory `~/.config/mcp-librarian/<name>/` (unless `--keep-config`)
5. **Does NOT touch the original server source directory**

### Standard Output

```
Removing playwright-mcp:
  ✓ Removed from registry
  ✓ Removed from claude_code config
  ✓ Deleted ~/.config/mcp-librarian/playwright-mcp/
playwright-mcp removed. Restart your AI platform to apply changes.
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Server not found in registry |
| 2 | Platform config update failed |

---

## Command: `scan` (Smart-Scan only, no build)

Run Smart-Scan on a server directory and report detected metadata and issues — without building or registering. Useful for previewing what the tool will do.

### Signature

```
mcplibrarian scan <SERVER_PATH> [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--fix` | | flag | off | Apply auto-fixes without building |
| `--json` | | flag | off | Output as JSON |

### Standard Output

```
Scanning /home/user/playwright-mcp...

  Runtime:       Node 20
  Entry point:   index.js
  Dependencies:  14 packages
  Env vars:      PLAYWRIGHT_BROWSERS_PATH (required), DEBUG (optional)

Issues found:
  ✗ [blocking]  package-lock.json missing
      Auto-fixable: Yes (runs npm install --package-lock-only in container)
  ⚠ [warning]   No .env.example found
      Auto-fixable: Yes (generates template with detected env vars)

Run 'mcplibrarian wrap /home/user/playwright-mcp' to fix and build.
Run 'mcplibrarian scan --fix /home/user/playwright-mcp' to apply fixes only.
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Scan complete, no blocking issues |
| 1 | Blocking issues found (not auto-fixed, `--fix` not passed) |
| 2 | Path does not exist or is not a directory |
| 3 | Runtime could not be detected |

---

## Option B: Shell Wrapper Contracts

The shell wrappers at repository root are a simplified subset of the above. They share the same observable UX conventions (same output format, same error message style) but have no registry and no health monitoring.

### `wrap-mcp.sh <SERVER_PATH> [PLATFORM]`

```
Usage: ./wrap-mcp.sh /path/to/server [platform]
  platform: claude_code (default) | cursor | vscode | goose | codex | opencode

Steps: detect → fix missing package-lock.json → generate config → build → update platform config
Exit codes: 0=success, 1=detection failed, 2=build failed, 3=config update failed
```

### `list-wrapped.sh`

```
Usage: ./list-wrapped.sh
Lists all servers with docker-configs/ in the current directory.
```

### `health-check.sh <SERVER_NAME>`

```
Usage: ./health-check.sh playwright-mcp
Runs L1 (container running) and L2 (MCP initialize) checks.
Exit codes: 0=healthy, 1=unhealthy, 2=not found
```

### `unwrap-mcp.sh <SERVER_NAME> [--keep-config]`

```
Usage: ./unwrap-mcp.sh playwright-mcp
Removes docker-configs/<name>/ and the platform config entry.
Does NOT delete the original server source.
```

---

## Error Message Convention

All commands follow this stderr format for errors:

```
[ERROR] <one-line summary of what failed>
  → <specific actionable instruction>
  → <optional second instruction or reference>
```

All commands follow this format for warnings:

```
[WARN] <one-line description>
  → <optional suggestion>
```

No raw Docker errors, Python tracebacks, or JSON blobs should ever reach the user unless `--verbose` is set.
