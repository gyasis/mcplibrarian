# Data Model: MCP Librarian

**Date**: 2026-02-21
**Branch**: `001-mcp-librarian`
**Source**: Entities extracted from `spec.md` + registry schema from `research.md`

---

## Entity Overview

```
MCPServer (source on disk)
  │
  ├── detected by ──► SmartScanResult
  │                     └── contains ──► Issue[]
  │                                       └── resolved by ──► Fix[]
  │
  ├── produces ──────► ContainerConfig (files on disk)
  │
  ├── registered as ─► RegistryEntry
  │                     ├── health ──► HealthCheckResult[]
  │                     └── platforms ──► PlatformConfig[]
  │
  └── connected to ──► Trigger[]
```

---

## Entities

### MCPServer

Represents an MCP server source directory on the user's disk, before containerization.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_path` | `Path` | YES | Absolute path to the server directory on disk |
| `name` | `str` | YES | Derived from directory name or package.json/pyproject.toml `name` field |
| `runtime` | `Runtime` | YES | `python` \| `node` \| `rust` \| `unknown` |
| `runtime_version` | `str` | YES | e.g. `"3.10"`, `"20"`, `"1.75"` |
| `entry_point` | `str` | YES | Relative path to main file (e.g. `"server.py"`, `"index.js"`) |
| `package_manager` | `str` | NO | `pip` \| `uv` \| `npm` \| `cargo` |
| `dependencies` | `list[str]` | NO | Package names from manifest |
| `env_vars` | `list[EnvVar]` | NO | Environment variables detected in source |
| `data_volumes` | `list[Path]` | NO | External data paths detected (e.g. large datasets) |
| `deployment_pattern` | `DeploymentPattern` | NO | `volume` (default) \| `self_contained` |

**State transitions**: `undetected → detected → wrapping → wrapped`

**Validation rules**:
- `source_path` must exist and be a directory
- `name` must be non-empty and contain only `[a-z0-9-_]`
- `runtime` must not be `unknown` before wrapping proceeds

---

### EnvVar

Represents a single environment variable required or used by an MCPServer.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | YES | Variable name, e.g. `OPENAI_API_KEY` |
| `required` | `bool` | YES | `True` if no default value found in source |
| `credential_type` | `CredentialType` | NO | `api_key` \| `oauth_token` \| `password` \| `generic` |
| `description` | `str` | NO | Human-readable purpose, if inferrable |
| `masked_example` | `str` | NO | e.g. `"sk-proj-..."` for `.env.example` |

---

### SmartScanResult

The output of running the Smart-Scan engine against one MCPServer. Captures everything detected and all issues found.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `server` | `MCPServer` | YES | The server that was scanned |
| `issues` | `list[Issue]` | YES | Problems found (may be empty) |
| `fixes_applied` | `list[Fix]` | YES | Auto-fixes that were applied (may be empty) |
| `scan_duration_ms` | `int` | YES | How long the scan took |
| `ready_to_build` | `bool` | YES | `True` once all blocking issues resolved |

---

### Issue

A specific problem detected by Smart-Scan that may block a successful container build.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `issue_type` | `IssueType` | YES | Enum: see below |
| `severity` | `Severity` | YES | `blocking` \| `warning` \| `info` |
| `description` | `str` | YES | Human-readable explanation |
| `auto_fixable` | `bool` | YES | Whether the tool can fix this without user input |
| `fix_instruction` | `str` | NO | Manual fix instruction if `auto_fixable` is `False` |

**IssueType enum**:
- `missing_package_lock` — `package-lock.json` absent (Node.js)
- `runtime_version_mismatch` — detected version differs from declared version
- `path_has_spaces` — server path or data volume path contains spaces
- `missing_env_var` — required env var not found in user's environment
- `missing_entry_point` — no recognisable main file found
- `invalid_json_manifest` — `package.json` or `pyproject.toml` is malformed
- `volume_path_not_found` — a data volume path does not exist on disk
- `unknown_runtime` — cannot determine Python/Node/Rust

**Severity**:
- `blocking` — build will definitely fail; must be fixed before proceeding
- `warning` — build may succeed, but behaviour may be unexpected
- `info` — informational; no action required

---

### Fix

Describes one auto-fix action applied by Smart-Scan.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `issue_type` | `IssueType` | YES | The issue this fix addresses |
| `description` | `str` | YES | What was changed, e.g. "Generated package-lock.json using node:20-slim" |
| `files_modified` | `list[Path]` | YES | Files created or changed |
| `reversible` | `bool` | YES | Whether the fix can be undone |

---

### ContainerConfig

The set of generated files that define how an MCPServer runs as a container.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `config_dir` | `Path` | YES | Absolute path to the generated config directory (e.g. `~/.config/mcp-librarian/<name>/`) |
| `dockerfile_path` | `Path` | YES | Path to generated Dockerfile |
| `compose_path` | `Path` | YES | Path to generated `docker-compose.yml` |
| `env_example_path` | `Path` | YES | Path to generated `.env.example` |
| `template_used` | `str` | YES | e.g. `"node-npm.Dockerfile.j2"` |
| `created_at` | `datetime` | YES | Generation timestamp |

**Notes**:
- Config files are stored in `~/.config/mcp-librarian/<server-name>/`, not inside the server's source directory.
- The user must never need to edit these files directly under normal usage.

---

### RegistryEntry

The persistent record of a wrapped server, stored in the local registry.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | YES | UUIDv4, generated at registration time |
| `name` | `str` | YES | Unique server name within the registry |
| `source_path` | `Path` | YES | Original server source directory |
| `runtime` | `str` | YES | `python` \| `node` \| `rust` |
| `config_path` | `Path` | YES | Path to generated `docker-compose.yml` |
| `deployment_pattern` | `str` | YES | `volume` \| `self_contained` |
| `registered_platforms` | `list[str]` | YES | Platform IDs this server is registered with |
| `status` | `ServerStatus` | YES | Enum: see below |
| `triggers` | `list[str]` | NO | Keywords that identify this server |
| `created_at` | `datetime` | YES | First registration timestamp |
| `updated_at` | `datetime` | YES | Last modification timestamp |
| `health` | `HealthSummary` | NO | Last health check result (denormalised for fast listing) |

**ServerStatus enum**:
- `active` — container is running and healthy
- `stopped` — user explicitly stopped the container
- `unhealthy` — container running but MCP protocol not responding
- `error` — last build or start attempt failed
- `source_missing` — source_path no longer exists on disk

**Uniqueness constraint**: `name` must be unique within the registry. `source_path` should be unique but is not enforced (same server could theoretically be registered twice with different names).

---

### HealthCheckResult

A point-in-time snapshot of a server's health, stored in the health history.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `server_id` | `str` | YES | References `RegistryEntry.id` |
| `check_time` | `datetime` | YES | When the check was performed |
| `container_running` | `bool` | YES | L1: container state |
| `protocol_responds` | `bool` | YES | L2: MCP initialize response received |
| `tools_available` | `bool` | YES | L3: tools/list returns non-empty list |
| `response_time_ms` | `int` | NO | L4: time for L2 to complete; `None` if L2 failed |
| `status` | `HealthStatus` | YES | Computed overall status |
| `error_message` | `str` | NO | Raw error if any level failed |

**HealthStatus enum**:
- `healthy` — all levels pass, response < 5 000 ms
- `degraded` — all levels pass, response 5 000–15 000 ms
- `unhealthy` — L2 or L3 failed
- `stopped` — L1 failed (container not running)
- `unknown` — Docker daemon unreachable

**Retention**: Health records are kept for 7 days, then pruned. Implemented as a JSON array within `registry.json` under each server entry, limited to the 168 most recent records (one per hour for 7 days).

---

### HealthSummary

Denormalised snapshot embedded in `RegistryEntry.health` for fast listing without scanning health history.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `last_check` | `datetime` | YES | Timestamp of most recent check |
| `status` | `HealthStatus` | YES | Status at last check |
| `response_time_ms` | `int` | NO | Response time at last check |

---

### PlatformConfig

Represents the configuration file of one AI coding platform, for updating MCP server registrations.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `platform_id` | `str` | YES | `claude_code` \| `cursor` \| `vscode` \| `goose` \| `codex` \| `opencode` |
| `config_path` | `Path` | YES | Absolute path to the platform's config file |
| `format` | `str` | YES | `json` (Claude Code, Cursor, VS Code, opencode) or `yaml` (Block's Goose, OpenAI Codex) |
| `servers_key` | `str` | YES | Key path to the MCP servers section (e.g. `"mcpServers"`, `"mcp.servers"`, `"extensions"`) |
| `entry_format` | `str` | YES | `stdio_docker` \| `goose_extension` \| `codex_wrapper_script` |

---

### Trigger

A keyword associated with a server, used for on-demand activation by the AI platform.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `server_id` | `str` | YES | References `RegistryEntry.id` |
| `word` | `str` | YES | Keyword, e.g. `"playwright"`, `"browser"`, `"screenshot"` |
| `priority` | `int` | NO | Lower = higher priority; default `1` |

---

## Enumerations Reference

```python
class Runtime(str, Enum):
    PYTHON = "python"
    NODE = "node"
    RUST = "rust"
    UNKNOWN = "unknown"

class DeploymentPattern(str, Enum):
    VOLUME = "volume"          # source mounted from host
    SELF_CONTAINED = "self_contained"  # all files copied into image

class Severity(str, Enum):
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"

class ServerStatus(str, Enum):
    ACTIVE = "active"
    STOPPED = "stopped"
    UNHEALTHY = "unhealthy"
    ERROR = "error"
    SOURCE_MISSING = "source_missing"

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"
    UNKNOWN = "unknown"

class CredentialType(str, Enum):
    API_KEY = "api_key"
    OAUTH_TOKEN = "oauth_token"
    PASSWORD = "password"
    GENERIC = "generic"
```

---

## State Transition Diagrams

### Server Wrap Lifecycle

```
[Source on disk]
      │
      ▼
  can_detect?
  ├── NO ──► ERROR "Unsupported runtime"
  └── YES
        │
        ▼
  SmartScan runs
      │
      ▼
  blocking issues?
  ├── YES & auto_fixable ──► Fix applied ──► re-check
  ├── YES & not fixable ──► ERROR with manual instructions
  └── NO (or all fixed)
        │
        ▼
  ContainerConfig generated
        │
        ▼
  docker compose build
  ├── FAIL ──► ERROR with human-readable message
  └── PASS
        │
        ▼
  HealthCheck runs (L1→L4)
  ├── FAIL ──► attempt restart ──► re-check
  │             └── still FAIL ──► ERROR "Server unhealthy"
  └── PASS
        │
        ▼
  RegistryEntry created (status: active)
        │
        ▼
  PlatformConfig updated for each target platform
        │
        ▼
  SUCCESS reported to user
```

### Server Status Transitions

```
        ┌──────────────────────────────────────┐
        ▼                                      │
    [active] ──user stop──► [stopped]           │
        │                      │               │
        │               user start             │
        │                      │               │
        │                      ▼               │
        │                  [active] ───────────┘
        │
        ├──health check fails──► [unhealthy]
        │                           │
        │                    auto-recovery
        │                    succeeds │ fails
        │                           ▼   ▼
        │                      [active] [error]
        │
        └──source deleted──► [source_missing]
```
