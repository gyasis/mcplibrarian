# Research: MCP Librarian — Phase 0 Findings

**Date**: 2026-02-21
**Branch**: `001-mcp-librarian`
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## R-001: Node.js MCP Server Detection

**Decision**: Detect Node.js MCP servers by scanning for `package.json` containing `@modelcontextprotocol/sdk` or `@modelcontextprotocol/server` in dependencies. Fall back to presence of `package.json` + any `.js`/`.ts` entry point file.

**Rationale**: The official MCP SDK for Node.js (`@modelcontextprotocol/sdk`) is the near-universal dependency for Node.js MCP servers. Secondary signal: presence of `package.json` plus a main entry point (from `"main"` or `"bin"` fields, or conventional `index.js`/`server.js`). Node version is extracted from the `engines.node` field, `.nvmrc`, or `.node-version`; default is Node 20 (LTS as of 2026).

**Alternatives considered**:
- Scan all `.js`/`.ts` files for `import { McpServer }` — too slow, too many false positives in large repos
- Require explicit `mcp-server: true` flag in `package.json` — requires users to modify source, violates non-invasive principle

**Implementation notes**:
```
can_detect(path) → True if:
  - package.json exists AND
  - @modelcontextprotocol/sdk OR @modelcontextprotocol/server in dependencies/devDependencies

detect(path) → NodeServerMetadata:
  - name: package.json "name" field
  - version: package.json "version" field
  - node_version: engines.node || .nvmrc || .node-version || "20"
  - entry_point: "main" field || "bin" field || first of [index.js, server.js, src/index.js]
  - has_package_lock: Path("package-lock.json").exists()
  - dependencies: package.json "dependencies" keys
  - env_vars: scan entry_point file for process.env.* patterns
```

---

## R-002: Auto-Fix — Missing package-lock.json

**Decision**: Generate `package-lock.json` by running `npm install --package-lock-only` inside a temporary Node container matched to the detected Node version. The fix runs in an isolated environment — never on the host.

**Rationale**: Running npm on the host risks polluting the host's node_modules and may use the wrong Node version. Running in a container guarantees isolation and version correctness. The `--package-lock-only` flag generates the lock file without installing `node_modules`, keeping the server directory clean.

**Alternatives considered**:
- Run `npm install --package-lock-only` on host — risks host contamination, version mismatch
- Generate a stub lock file — would cause non-reproducible builds
- Skip lock file and use `npm install` at build time — slower container builds, non-reproducible

**Shell equivalent (Option B)**:
```bash
docker run --rm \
  -v "$(pwd):/app" \
  -w /app \
  "node:${NODE_VERSION}" \
  npm install --package-lock-only
```

**Python SDK equivalent (Option A)**:
```python
client.containers.run(
    image=f"node:{node_version}-slim",
    command="npm install --package-lock-only",
    volumes={str(server_path): {"bind": "/app", "mode": "rw"}},
    working_dir="/app",
    remove=True,
)
```

---

## R-003: Health Check Protocol — JSON-RPC 2.0

**Decision**: Four-level health check via MCP JSON-RPC 2.0 protocol, executed by piping requests to the container via `docker exec`. Healthy threshold: all levels pass and `initialize` responds within 5 seconds.

**Rationale**: The MCP protocol specifies JSON-RPC 2.0 as its transport. The `initialize` method is the mandatory first handshake — if it fails, the server is non-functional regardless of whether the container is running. The `tools/list` method validates that the server has tools registered. Both are cheap, stateless calls suitable for monitoring.

**Health levels**:
| Level | Check | Pass Condition |
|-------|-------|---------------|
| L1 | Container state | `State.Running == true` |
| L2 | MCP initialize | Valid JSON-RPC response with `protocolVersion` |
| L3 | Tools available | `tools/list` returns non-empty `tools` array |
| L4 | Response time | L2 completes in < 5 000 ms (degraded if 5–15 s) |

**Health states**:
- `healthy` — all 4 levels pass
- `degraded` — L1–L3 pass, L4 between 5–15 s
- `unhealthy` — L2 or L3 fail
- `stopped` — L1 fails (container not running)
- `unknown` — cannot communicate with Docker daemon

**Recovery strategy**: On `unhealthy`, attempt container restart once; if still unhealthy after 30 s, mark `unrecoverable` and alert user.

---

## R-004: Platform Config File Locations

**Decision**: Six platforms are supported. Each has a known default config file location. The tool auto-discovers the location, falls back to a user-configured override. Two platforms (Block's Goose, OpenAI Codex) use YAML rather than JSON; OpenAI Codex also uses a non-standard MCP integration pattern that requires a platform-specific adapter.

| Platform | Linux/macOS Config Path | Format | Notes |
|----------|------------------------|--------|-------|
| Claude Code | `~/.config/Claude/claude_desktop_config.json` | JSON | Standard stdio MCP |
| Cursor IDE | `~/.cursor/mcp.json` | JSON | Standard stdio MCP |
| VS Code Copilot | `~/.config/Code/User/settings.json` (key: `mcp.servers`) | JSON | Standard stdio MCP |
| Block's Goose | `~/.config/goose/config.yaml` (key: `extensions`) | YAML | YAML extension system; different entry shape |
| OpenAI Codex | `~/.codex/config.yaml` | YAML | Non-standard; uses wrapper script pattern |
| opencode (SST) | `~/.config/opencode/config.json` | JSON | Standard stdio MCP; eager-loads all tools |

**Claude Code entry format** (containerized, stdio mode):
```json
{
  "mcpServers": {
    "server-name": {
      "command": "docker",
      "args": ["compose", "-f", "/abs/path/docker-compose.yml", "run", "--rm", "server-name"]
    }
  }
}
```

**Cursor IDE entry format**:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "docker",
      "args": ["compose", "-f", "/abs/path/docker-compose.yml", "run", "--rm", "server-name"]
    }
  }
}
```

**VS Code Copilot entry format** (inside `settings.json`):
```json
{
  "mcp": {
    "servers": {
      "server-name": {
        "type": "stdio",
        "command": "docker",
        "args": ["compose", "-f", "/abs/path/docker-compose.yml", "run", "--rm", "server-name"]
      }
    }
  }
}
```

**Block's Goose entry format** (YAML extension, stdio type):
```yaml
extensions:
  - name: server-name
    type: stdio
    cmd: docker
    args:
      - compose
      - -f
      - /abs/path/docker-compose.yml
      - run
      - --rm
      - server-name
    description: "MCP server managed by mcplibrarian"
    enabled: true
```
> Block's Goose uses a YAML-based extension system. The tool must read/write `~/.config/goose/config.yaml` using a YAML library (add `pyyaml` dependency). Merging must preserve existing YAML structure and comments where possible.

**OpenAI Codex entry format** (wrapper script pattern):
Codex CLI does not support the same stdio MCP JSON config format as Claude/Cursor. The integration requires generating a wrapper shell script that Codex can invoke as a tool, placed in `~/.codex/tools/`:
```yaml
# ~/.codex/config.yaml — reference to tool wrapper
tools:
  - name: server-name
    type: shell
    script: ~/.codex/tools/server-name.sh
    description: "MCP server managed by mcplibrarian"
```
Generated wrapper (`~/.codex/tools/server-name.sh`):
```bash
#!/bin/bash
docker compose -f /abs/path/docker-compose.yml run --rm server-name
```
> This is a best-effort integration. Codex's MCP support (via AGENTS.md/Skills) uses a different protocol than stdio JSON-RPC; the shell wrapper bridges the gap. Full parity with Claude Code is not guaranteed for this platform.

**opencode (SST) entry format**:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "docker",
      "args": ["compose", "-f", "/abs/path/docker-compose.yml", "run", "--rm", "server-name"]
    }
  }
}
```

**Alternatives considered**:
- Provide a universal proxy config format — would require users to install a proxy daemon
- Generate platform-specific scripts instead of editing config files — less seamless UX

**New dependency required**: `pyyaml` — needed for reading/writing Block's Goose and OpenAI Codex YAML configs. Add to `pyproject.toml`.

**Safe write strategy**: Always read → validate (JSON with `json.loads()` or YAML with `yaml.safe_load()`) → merge → write to `.bak` → rename. Never overwrite a config file without first validating its structure is parseable. Error out clearly if the file has syntax errors.

---

## R-005: Docker Dockerfile Templates — Node.js

**Decision**: Two Node.js Dockerfile templates: `node-npm.Dockerfile.j2` (npm, standard) and `node-npm-volume.Dockerfile.j2` (volume-mounted, no COPY). Template selection based on `deployment_pattern` detected by Smart-Scan.

**Rationale**: Node.js MCP servers typically don't have a separate `node_modules` inside the container when using volume mounts. But for self-contained images (servers that ship all dependencies), a COPY+RUN pattern is cleaner. The Smart-Scan engine decides which pattern fits each server.

**node-npm.Dockerfile.j2** (volume-mounted — default):
```dockerfile
FROM node:{{ node_version }}-slim
WORKDIR /app
# Dependencies installed from mounted source at runtime
ENV NODE_ENV=production
CMD ["node", "{{ entry_point }}"]
```

**node-npm-selfcontained.Dockerfile.j2** (self-contained — when no external data volumes):
```dockerfile
FROM node:{{ node_version }}-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production
COPY . .
ENV NODE_ENV=production
CMD ["node", "{{ entry_point }}"]
```

---

## R-006: Registry Data Format

**Decision**: JSON file at `~/.config/mcp-librarian/registry.json`. No new dependencies. Atomic writes (write to `.tmp` then rename). Schema versioned for future migration to SQLite.

**Rationale**: A JSON file requires zero new dependencies (Python's `json` stdlib), is human-readable for debugging, and is sufficient for up to ~500 registered servers. SQLite migration is scoped to the Option A full-CLI phase and will read the same schema.

**Schema**:
```json
{
  "version": "1",
  "servers": [
    {
      "id": "uuid-v4",
      "name": "playwright-mcp",
      "source_path": "/home/user/playwright-mcp",
      "runtime": "node",
      "config_path": "/home/user/.config/mcp-librarian/playwright-mcp/docker-compose.yml",
      "deployment_pattern": "volume",
      "registered_platforms": ["claude_code", "cursor"],
      "status": "active",
      "triggers": ["playwright", "browser", "screenshot"],
      "created_at": "2026-02-20T10:00:00Z",
      "updated_at": "2026-02-20T10:00:00Z",
      "health": {
        "last_check": "2026-02-20T10:05:00Z",
        "status": "healthy",
        "response_time_ms": 420
      }
    }
  ]
}
```

**Atomic write pattern**:
```python
import json, os, tempfile
def save_registry(path, data):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, path)   # atomic on POSIX
```

---

## R-007: Credential Detection Strategy

**Decision**: Scan only the server's main entry point file(s) for `process.env.VAR_NAME` (Node.js) and `os.getenv("VAR_NAME")` / `os.environ["VAR_NAME"]` (Python) patterns using regex. Cross-reference with any `.env.example` file. Output a required-vs-optional classification based on presence of null-coalescing operators or default values.

**Rationale**: Scanning only the entry point file(s) avoids false positives from scanning `node_modules` or `.venv`. The regex is fast (< 10 ms for typical server files). A variable with a default value in code (`process.env.TIMEOUT || "30"`) is classified as optional; one with no default is required.

**Required**: `os.getenv("OPENAI_API_KEY")` — no fallback → `required: true`
**Optional**: `os.getenv("TIMEOUT", "30")` — has fallback → `required: false`

---

## R-008: Batch Concurrency Limit

**Decision**: Cap concurrent Docker builds at 4. Use Python's `concurrent.futures.ThreadPoolExecutor(max_workers=4)`. Each worker runs one `docker compose build` + health check sequentially.

**Rationale**: Docker builds are CPU and I/O intensive. Beyond 4 concurrent builds, most developer machines (4–8 cores, NVMe storage) see diminishing returns and may run out of Docker build cache space. 4 workers allows 10 servers to complete in roughly 2–3 "waves" well under the 60-second target.

**Alternatives considered**:
- `asyncio` — Docker SDK blocking calls would require `run_in_executor` anyway; ThreadPoolExecutor is simpler
- Configurable via CLI flag `--workers N` — added to `wrap-all` command signature for power users

---

## R-009: Shell Wrapper (Option B) — Dependency Requirements

**Decision**: Option B shell wrappers require only: `bash` (POSIX), `jq` (JSON manipulation), `docker` (v2 plugin). No Python required for Option B. These are present on virtually all Linux developer machines.

**Rationale**: Making Option B Python-free means it works even if the user's Python environment is broken (a common scenario for developers new to MCP tooling). It also ships as a simple `curl | bash` or `git clone` install.

**jq operations used**:
- Read/write registry JSON
- Merge new server entry into `mcpServers` object in platform config files
- Validate JSON syntax before writing (`jq . < file`)

---

## Resolution Summary

| Unknown | Resolved | Key Decision |
|---------|----------|-------------|
| Node.js detection | YES | `@modelcontextprotocol/sdk` in `package.json` dependencies |
| package-lock auto-fix | YES | `npm install --package-lock-only` in isolated Node container |
| Health check protocol | YES | 4-level JSON-RPC 2.0 check; healthy = all levels pass < 5 s |
| Platform config locations | YES | 6 platforms documented: Claude Code, Cursor, VS Code Copilot, Block's Goose (YAML), OpenAI Codex (wrapper script), opencode |
| Node.js Dockerfile templates | YES | 2 templates: volume-mounted (default) + self-contained |
| Registry format | YES | JSON file, stdlib only, atomic writes, versioned schema |
| Credential detection | YES | Regex on entry point files only; required vs optional classified |
| Batch concurrency | YES | ThreadPoolExecutor, max 4 workers |
| Option B dependencies | YES | bash + jq + docker only — no Python needed |
