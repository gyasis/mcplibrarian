# Tasks: MCP Librarian — Cross-Platform MCP Server Containerization

**Input**: Design documents from `specs/001-mcp-librarian/`
**Branch**: `001-mcp-librarian`
**Generated**: 2026-02-21

**Format**: `- [ ] [TaskID] [P?] [StoryLabel?] Description — file path`
- **[P]**: Parallelizable (different files, no incomplete dependencies)
- **[US1–US5]**: Maps to user story from spec.md
- No test tasks generated (none requested in spec)

---

## Phase 1: Setup

**Purpose**: Create directory structure, install new dependency, and seed fixture servers used throughout all stories.

- [ ] T001 Create `tests/` directory structure: `tests/__init__.py`, `tests/unit/`, `tests/integration/`, `tests/fixtures/sample-python-server/`, `tests/fixtures/sample-node-server/`
- [ ] T002 Add `pyyaml>=6.0` to `pyproject.toml` dependencies and run `uv sync` to update `uv.lock`
- [ ] T003 [P] Create minimal Node.js fixture server — `tests/fixtures/sample-node-server/package.json` (with `@modelcontextprotocol/sdk` dep, `"main": "index.js"`) and `tests/fixtures/sample-node-server/index.js` (stub MCP server that responds to `initialize` and `tools/list`)
- [ ] T004 [P] Create minimal Python fixture server — `tests/fixtures/sample-python-server/pyproject.toml` (FastMCP dep, Python 3.10) and `tests/fixtures/sample-python-server/server.py` (stub FastMCP server)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure every user story depends on. Nothing in Phase 3+ can begin until this phase is complete.

**⚠️ CRITICAL**: All user story work is blocked until this phase completes.

- [ ] T005 Refactor `src/mcp_dockerize/cli.py` to a Click group (`mcplibrarian` as root group); move the existing positional-arg command to a `_legacy_wrap` function kept for backward compatibility; add group entry point
- [ ] T006 [P] Create Jinja2 template `src/mcp_dockerize/templates/python-uv.Dockerfile.j2` — Python/uv server, installs deps via `uv sync`, sets entrypoint from `project.scripts`
- [ ] T007 [P] Create Jinja2 template `src/mcp_dockerize/templates/python-direct.Dockerfile.j2` — Python/pip server, copies `requirements.txt`, sets `CMD` to entry point file
- [ ] T008 [P] Create Jinja2 template `src/mcp_dockerize/templates/node-npm.Dockerfile.j2` — Node.js volume-mounted server; no COPY of source; sets `CMD ["node", "{{ entry_point }}"]`
- [ ] T009 [P] Create Jinja2 template `src/mcp_dockerize/templates/node-npm-selfcontained.Dockerfile.j2` — Node.js self-contained; `COPY package.json package-lock.json ./`, `RUN npm ci --only=production`, `COPY . .`
- [ ] T010 [P] Create Jinja2 template `src/mcp_dockerize/templates/docker-compose.yml.j2` — renders service block with `stdin_open: true`, `tty: false`, volume mounts using `type: bind` syntax for all data volumes, `env_file: [.env]`
- [ ] T011 [P] Create Jinja2 template `src/mcp_dockerize/templates/env-example.j2` — renders one `VAR_NAME=<description>` line per detected env var, marking required vs optional
- [ ] T012 Create `AbstractDetector` interface in `src/mcp_dockerize/detectors/base.py` — defines `can_detect(path: Path) -> bool` and `detect(path: Path) -> ServerMetadata`; `ServerMetadata` dataclass with fields: `name`, `runtime`, `runtime_version`, `entry_point`, `package_manager`, `dependencies`, `env_vars`, `data_volumes`, `deployment_pattern`
- [ ] T013 Create registry models in `src/mcp_dockerize/registry/models.py` — dataclasses: `EnvVar`, `HealthSummary`, `HealthCheckResult`, `RegistryEntry`, `ContainerConfig`; include `Runtime`, `DeploymentPattern`, `ServerStatus`, `HealthStatus`, `CredentialType` enums; all serializable via `dataclasses.asdict()`
- [ ] T014 Create registry store in `src/mcp_dockerize/registry/store.py` — `RegistryStore` class with methods: `load() -> dict`, `save(data)` (atomic write via `.tmp` + `os.replace`), `add(entry: RegistryEntry)`, `get(name: str) -> RegistryEntry | None`, `list_all() -> list[RegistryEntry]`, `remove(name: str)`, `update_health(name, result: HealthCheckResult)`; stores at `~/.config/mcp-librarian/registry.json`; creates parent dirs on first write
- [ ] T015 Create issue types in `src/mcp_dockerize/smart_scan/issues.py` — `IssueType` enum (all 8 variants from data-model: `missing_package_lock`, `runtime_version_mismatch`, `path_has_spaces`, `missing_env_var`, `missing_entry_point`, `invalid_json_manifest`, `volume_path_not_found`, `unknown_runtime`); `Severity` enum (`blocking`, `warning`, `info`); `Issue` and `Fix` dataclasses
- [ ] T016 Create `AbstractPlatform` interface in `src/mcp_dockerize/platforms/base.py` — defines `platform_id: str`, `config_path: Path`, `add_server(entry: RegistryEntry, compose_path: Path)`, `remove_server(name: str)`, `_read_config()`, `_write_config(data)`; implement safe read-validate-backup-write logic shared by all JSON platforms; YAML platforms override with `pyyaml`
- [ ] T017 [P] Create health states in `src/mcp_dockerize/health/states.py` — `HealthStatus` enum, `HealthCheckResult` dataclass (fields: `server_name`, `container_running`, `protocol_responds`, `tools_available`, `response_time_ms`, `status`, `error_message`, `check_time`)
- [ ] T018 Create 4-level MCP health checker in `src/mcp_dockerize/health/checker.py` — `MCPHealthChecker` class; L1: `docker inspect` container state; L2: pipe `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}` via `docker compose run --rm` and parse response; L3: pipe `tools/list` and check non-empty tools array; L4: measure L2 response time; classify into `HealthStatus`; timeout per level = 10 s; uses `docker` SDK (existing dep)

**Checkpoint**: Foundation complete. All user stories can now begin.

---

## Phase 3: User Story 1 — One-Command Server Wrapping (Priority: P1) 🎯 MVP

**Goal**: A developer runs `mcplibrarian wrap <path>` on any Python or Node.js MCP server and gets a working, registered, health-checked container — all within 60 seconds with no manual steps.

**Independent Test**: Run `mcplibrarian wrap tests/fixtures/sample-node-server/` (which has no `package-lock.json`). Verify: lock file auto-generated, container built, `health` check passes, server appears in `mcplibrarian list`, `~/.config/Claude/claude_desktop_config.json` updated — all without manual intervention.

- [ ] T019 [P] [US1] Implement `NodeDetector` in `src/mcp_dockerize/detectors/node.py` — `can_detect`: check `package.json` exists and `@modelcontextprotocol/sdk` or `@modelcontextprotocol/server` in `dependencies`/`devDependencies`; `detect`: extract `name`, `version`, `main`/`bin` entry point, `engines.node` (or `.nvmrc`/`.node-version`, default `"20"`), `dependencies` keys, `process.env.VAR` patterns in entry point file, `has_package_lock` bool
- [ ] T020 [P] [US1] Refactor `PythonDetector` in `src/mcp_dockerize/detectors/python.py` to extend `AbstractDetector`; return `ServerMetadata` instead of existing `metadata` object; preserve all existing detection logic
- [ ] T021 [US1] Implement `SmartScan` orchestrator in `src/mcp_dockerize/smart_scan/scanner.py` — `SmartScan(path).run() -> SmartScanResult`: (1) try each detector, (2) detect env vars, (3) detect data volumes, (4) validate paths for spaces/symlinks, (5) check for missing lock file, (6) compile `Issue[]`; `discover_servers(scan_dir, max_depth=2) -> list[Path]` for batch use
- [ ] T022 [US1] Implement auto-fix strategies in `src/mcp_dockerize/smart_scan/fixer.py` — `AutoFixer(result: SmartScanResult).fix_all() -> list[Fix]`; fix `missing_package_lock`: run `docker run --rm -v <path>:/app -w /app node:<ver>-slim npm install --package-lock-only`; fix `path_has_spaces`: update volume mount strings to quote/escape; fix `runtime_version_mismatch`: update detected version in metadata; each fix records files modified; skip fixes that are not `auto_fixable`
- [ ] T023 [US1] Implement docker-compose.yml generator in `src/mcp_dockerize/generators/compose.py` — `ComposeGenerator(metadata, config_dir).generate() -> Path`; renders `docker-compose.yml.j2` with service name, build context, volumes (using `type: bind` with absolute paths, `read_only: true`), `env_file: [.env]`, `stdin_open: true`, `tty: false`; creates `config_dir` if needed; copies `.env.example` rendered from `env-example.j2`
- [ ] T024 [US1] Implement `ClaudeCodePlatform` in `src/mcp_dockerize/platforms/claude_code.py` — extends `AbstractPlatform`; `config_path` = `~/.config/Claude/claude_desktop_config.json`; `add_server`: read JSON → validate → merge entry under `mcpServers.<name>` with `{"command": "docker", "args": ["compose", "-f", "<abs_compose_path>", "run", "--rm", "<name>"]}` → write atomically; `remove_server`: pop key from `mcpServers`; back up to `.bak` before any write
- [ ] T025 [US1] Implement `wrap` Click subcommand in `src/mcp_dockerize/cli.py` — args: `SERVER_PATH`; options: `--name`, `--platform` (default `claude_code`), `--no-health-check`, `--no-register`, `--force`, `--verbose`, `--dry-run`; orchestration: (1) SmartScan, (2) AutoFixer, (3) `DockerfileGenerator` + `ComposeGenerator`, (4) `DockerBuilder.build_image`, (5) `MCPHealthChecker.check`, (6) `RegistryStore.add`, (7) platform `add_server`; each step prints `[StepName]` prefix line; exit codes per contract
- [ ] T026 [US1] Add human-readable error wrapping to `wrap` in `src/mcp_dockerize/cli.py` — catch `DockerBuildError`, `MCPTestError`, and all custom exceptions; format as `[ERROR] <summary>\n  → <instruction>`; never print raw tracebacks unless `--verbose`; implement `--dry-run` path that prints would-do steps and exits 0

**Checkpoint**: `mcplibrarian wrap <path>` is fully functional for Python and Node.js servers with Claude Code as the target platform. MVP is shippable.

---

## Phase 4: User Story 2 — Batch Wrapping for Power Users (Priority: P2)

**Goal**: `mcplibrarian wrap-all <dir>` discovers all MCP servers in a directory, wraps them in parallel (up to 4 concurrent), shows live progress, and reports a final summary — completing 10 servers in under 60 seconds.

**Independent Test**: Run `mcplibrarian wrap-all tests/fixtures/` (contains sample Python + Node servers). Both wrap successfully in parallel. Summary shows 2 succeeded. Registry has both entries.

- [ ] T027 [US2] Implement MCP server discovery in `src/mcp_dockerize/smart_scan/scanner.py` — `discover_servers(scan_dir: Path, max_depth: int = 2) -> list[Path]`: walk directory tree, skip `node_modules`, `.venv`, `__pycache__`, `.git`, `dist`, `build`; return dirs where any registered detector's `can_detect()` returns True
- [ ] T028 [US2] Implement `wrap-all` Click subcommand in `src/mcp_dockerize/cli.py` — args: `SCAN_DIR`; options: `--workers` (default 4, max 8), `--platform` (repeatable), `--skip-existing` (default True), `--force`, `--filter` (glob), `--yes`; use `concurrent.futures.ThreadPoolExecutor(max_workers)` to call the same wrap logic as the `wrap` command for each discovered server
- [ ] T029 [US2] Add live per-server progress display to `wrap-all` in `src/mcp_dockerize/cli.py` — print one status line per server updated in place (use `\r` overwrite or line-buffered output); show server name + current step (scanning / building / health check / done / failed)
- [ ] T030 [US2] Add batch summary report to `wrap-all` in `src/mcp_dockerize/cli.py` — after all workers complete, print table: server name, status (✓/✗), duration; list each failure with its actionable error message; exit code 0 if all succeed, 1 if any fail

**Checkpoint**: Power users can wrap 10+ servers unattended. Each wrapped server is independently accessible.

---

## Phase 5: User Story 3 — Cross-Platform Configuration (Priority: P2)

**Goal**: Users on Cursor, VS Code Copilot, Block's Goose, OpenAI Codex, or opencode can pass `--platform <id>` (or multiple `--platform` flags) and have the correct config file updated automatically — including YAML formats for Goose and Codex.

**Independent Test**: Wrap `tests/fixtures/sample-node-server/` with `--platform cursor --platform goose`. Verify `~/.cursor/mcp.json` has the new entry (JSON) and `~/.config/goose/config.yaml` has the new extension entry (YAML). Remove the server; both files are clean.

- [ ] T031 [P] [US3] Implement `CursorPlatform` in `src/mcp_dockerize/platforms/cursor.py` — extends `AbstractPlatform`; `config_path` = `~/.cursor/mcp.json`; entry format: `mcpServers.<name>` with `command`/`args` (same as Claude Code); create file with `{"mcpServers": {}}` if missing
- [ ] T032 [P] [US3] Implement `VSCodePlatform` in `src/mcp_dockerize/platforms/vscode.py` — extends `AbstractPlatform`; `config_path` = `~/.config/Code/User/settings.json`; nested key path: `mcp.servers.<name>` with `type: "stdio"`, `command`, `args`; must deep-merge without clobbering other VS Code settings
- [ ] T033 [P] [US3] Implement `GoosePlatform` in `src/mcp_dockerize/platforms/goose.py` — extends `AbstractPlatform` with YAML override; `config_path` = `~/.config/goose/config.yaml`; uses `yaml.safe_load` / `yaml.safe_dump`; entry appended to `extensions` list as `{name, type: "stdio", cmd: "docker", args: [...], description, enabled: true}`; no duplicate names (check before append)
- [ ] T034 [P] [US3] Implement `CodexPlatform` in `src/mcp_dockerize/platforms/codex.py` — extends `AbstractPlatform` with YAML override; `config_path` = `~/.codex/config.yaml`; generates a shell wrapper script at `~/.codex/tools/<name>.sh` (executable, `#!/bin/bash`, `docker compose -f ... run --rm <name>`); adds entry to `tools` list in config YAML as `{name, type: "shell", script: "~/.codex/tools/<name>.sh", description}`; `chmod +x` the wrapper
- [ ] T035 [P] [US3] Implement `OpenCodePlatform` in `src/mcp_dockerize/platforms/opencode.py` — extends `AbstractPlatform`; `config_path` = `~/.config/opencode/config.json`; entry format: `mcpServers.<name>` with `command`/`args`; create file with `{"mcpServers": {}}` if missing
- [ ] T036 [US3] Implement platform factory in `src/mcp_dockerize/platforms/__init__.py` — `get_platform(platform_id: str) -> AbstractPlatform`; map IDs to classes: `claude_code → ClaudeCodePlatform`, `cursor → CursorPlatform`, `vscode → VSCodePlatform`, `goose → GoosePlatform`, `codex → CodexPlatform`, `opencode → OpenCodePlatform`; raise `ValueError` with valid IDs list on unknown ID
- [ ] T037 [US3] Wire `--platform` flag (repeatable via `multiple=True`) into `wrap` and `wrap-all` in `src/mcp_dockerize/cli.py` — call `get_platform(id).add_server(entry, compose_path)` for each specified platform after successful registration; store `registered_platforms` list in `RegistryEntry`

**Checkpoint**: All 6 platforms supported. `--platform` flag works in both `wrap` and `wrap-all`.

---

## Phase 6: User Story 4 — Health Monitoring & Diagnostics (Priority: P3)

**Goal**: Users can run `mcplibrarian health [server]` to check any or all servers, see their 7-day history, and have unhealthy servers auto-recovered where possible.

**Independent Test**: Start a wrapped server, stop its container manually, then run `mcplibrarian health <name>`. Status shows `stopped`. Start container again, run health — shows `healthy`. Run `mcplibrarian health <name> --history` and see the two checks logged.

- [ ] T038 [US4] Add `health` Click subcommand in `src/mcp_dockerize/cli.py` — optional arg `SERVER_NAME` (if omitted, checks all registered servers); options: `--recover` (flag), `--history` (flag), `--json`; calls `MCPHealthChecker.check(entry)` for each target server; prints L1–L4 results with ✓/✗; updates `RegistryStore.update_health` after each check
- [ ] T039 [US4] Implement health history storage in `src/mcp_dockerize/registry/store.py` — add `update_health(name, result: HealthCheckResult)` method: append result to `registry.json` under `servers[name].health_history` (keep last 168 entries — 7 days at hourly rate); update `servers[name].health` summary (last check only); prune entries older than 7 days
- [ ] T040 [US4] Implement auto-recovery logic in `src/mcp_dockerize/health/checker.py` — `attempt_recovery(entry: RegistryEntry) -> bool`: run `docker compose -f <compose_path> restart <name>`; wait 5 s; re-run L1+L2 check; return True if now healthy; log recovery attempt and outcome; called only when `--recover` flag set or status is `unhealthy`
- [ ] T041 [US4] Add `--history` display to health subcommand in `src/mcp_dockerize/cli.py` — when `--history` set, load `health_history` from registry for the target server; print table of last 24 h: timestamp, status, response time; exit 0 if all targets healthy or stopped, 1 if any unhealthy
- [ ] T042 [US4] Add `source_missing` detection to `MCPHealthChecker` in `src/mcp_dockerize/health/checker.py` — before running L1, check if `entry.source_path` still exists on disk; if not, return `HealthStatus.STOPPED` with `error_message="Source directory not found: <path>"`; update registry entry `status` to `source_missing`

**Checkpoint**: Health command fully functional with history and auto-recovery.

---

## Phase 7: User Story 5 — Registry Management (Priority: P3)

**Goal**: Users can list all wrapped servers with status, inspect individual server details, remove servers cleanly, and preview what Smart-Scan would detect before committing to a wrap.

**Independent Test**: After wrapping two servers, run `mcplibrarian list` — both appear with correct status. Run `mcplibrarian status <name>` — full details shown. Run `mcplibrarian remove <name> --yes` — entry gone from list, platform config cleaned, source files untouched. Run `mcplibrarian scan <path>` on a server with a missing lock file — issues reported without building anything.

- [ ] T043 [P] [US5] Add `list` Click subcommand in `src/mcp_dockerize/cli.py` — options: `--json`, `--status` (filter); load all entries from `RegistryStore.list_all()`; print table: NAME, RUNTIME, STATUS, PLATFORMS, LAST HEALTH; `--json` outputs JSON array per contract
- [ ] T044 [P] [US5] Add `status` Click subcommand in `src/mcp_dockerize/cli.py` — required arg `SERVER_NAME`; load entry from registry; print detailed view: source path, config path, platforms, status, health summary, registration date; `--json` outputs full `RegistryEntry` as JSON; exit 1 if not found
- [ ] T045 [US5] Add `remove` Click subcommand in `src/mcp_dockerize/cli.py` — required arg `SERVER_NAME`; options: `--keep-config`, `--keep-platform-entry`, `--yes`; prompt for confirmation unless `--yes`; call `RegistryStore.remove(name)`, call `platform.remove_server(name)` for each registered platform (unless `--keep-platform-entry`), delete `~/.config/mcp-librarian/<name>/` directory (unless `--keep-config`); never touch `source_path`
- [ ] T046 [US5] Add `scan` Click subcommand in `src/mcp_dockerize/cli.py` — required arg `SERVER_PATH`; option: `--fix` (apply auto-fixes without building), `--json`; run `SmartScan.run()` then `AutoFixer.fix_all()` if `--fix`; print detected metadata and issues table (IssueType, Severity, auto_fixable, fix_instruction); exit 0 if no blocking issues, 1 if blocking issues remain

**Checkpoint**: All registry management commands functional. Complete CLI surface area delivered.

---

## Phase 8: Option B — Shell Wrappers

**Purpose**: Deliver the lightweight quick-start track (no Python required) that ships immediately while the full CLI matures. Covers FR-025 through FR-027.

**Independent Test**: On a clean machine with only bash, jq, and docker: run `./wrap-mcp.sh tests/fixtures/sample-node-server/` — generates `docker-configs/sample-node-server/`, builds container, updates `~/.config/Claude/claude_desktop_config.json`.

- [ ] T047 Implement `wrap-mcp.sh` at repo root — phases: (1) call `uv run mcplibrarian scan` or fall back to pure shell detection of `package.json` / `pyproject.toml`; (2) generate `package-lock.json` if missing using `docker run node:<ver>-slim npm install --package-lock-only`; (3) call `uv run mcplibrarian` (existing generator) to produce Dockerfile + docker-compose.yml in `docker-configs/<name>/`; (4) run `docker compose build`; (5) update `~/.config/Claude/claude_desktop_config.json` via jq merge; accept `[PLATFORM]` arg defaulting to `claude_code`; color-coded `[Step]` output matching CLI convention; exit codes 0/1/2/3
- [ ] T048 [P] Implement `list-wrapped.sh` at repo root — iterate `docker-configs/*/docker-compose.yml`; for each, check `docker compose ps | grep -q Up` to determine running state; print NAME + status emoji
- [ ] T049 [P] Implement `health-check.sh` at repo root — accept `<SERVER_NAME>` arg; find `docker-configs/<name>/docker-compose.yml`; run L1 (container state via `docker compose ps`) and L2 (pipe `initialize` JSON-RPC and grep for `jsonrpc` in response); print human-readable status; exit 0 if healthy, 1 if unhealthy, 2 if not found
- [ ] T050 Implement `unwrap-mcp.sh` at repo root — accept `<SERVER_NAME>` and optional `--keep-config`; remove entry from `~/.config/Claude/claude_desktop_config.json` via jq; delete `docker-configs/<name>/` unless `--keep-config`; print confirmation; never touch original server source

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Tie up loose ends that affect multiple stories.

- [ ] T051 [P] Fix `src/mcp_dockerize/generators/dockerfile.py` to use Jinja2 templates (T006–T009) via `jinja2.Environment(loader=FileSystemLoader(templates_dir))` instead of the existing hardcoded string generation — resolves the known `FileNotFoundError` blocker documented in `memory-bank/techContext.md`
- [ ] T052 [P] Add `~/.config/mcp-librarian/` to `.gitignore` and verify `docker-configs/` is already excluded; confirm `tests/fixtures/sample-node-server/package-lock.json` is git-ignored (auto-generated during tests)
- [ ] T053 Update `README.md` with full CLI reference — commands table (wrap, wrap-all, list, status, health, remove, scan), platform support table (6 platforms with config paths), Option B shell wrapper usage, quickstart example from fixture servers
- [ ] T054 Run `quickstart.md` validation end-to-end — execute every command block in `specs/001-mcp-librarian/quickstart.md`; fix any commands that fail; update quickstart if paths or flags changed during implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately; T003 and T004 are parallel
- **Phase 2 (Foundational)**: Requires Phase 1 complete; T005 must run first (CLI refactor); T006–T011 parallel after T005; T012–T018 can run after T005 in any order (different files); T017 parallel with T012–T016
- **Phase 3 (US1)**: Requires Phase 2 complete; T019 and T020 parallel; T021 after T019+T020; T022 after T021; T023 parallel with T022; T024 parallel with T022+T023; T025 after T021–T024; T026 after T025
- **Phase 4 (US2)**: Requires Phase 3 complete (reuses wrap logic); T027 adds to scanner (extend, not replace); T028–T030 sequential in cli.py
- **Phase 5 (US3)**: Requires Phase 2 complete (AbstractPlatform); T031–T035 fully parallel; T036 after T031–T035; T037 after T036
- **Phase 6 (US4)**: Requires Phase 3 complete (health checker used in wrap); T038–T042 mostly sequential within cli.py/health module
- **Phase 7 (US5)**: Requires Phase 2 complete (registry); T043+T044 parallel; T045 after T043; T046 after Phase 3 (SmartScan)
- **Phase 8 (Option B)**: Requires Phase 3 complete (needs working generator); T048+T049 parallel; T047 and T050 sequential
- **Phase 9 (Polish)**: Requires all phases complete; T051+T052 parallel

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2. No dependency on other user stories.
- **US2 (P2)**: Depends on US1 (reuses `wrap` flow for each server in batch).
- **US3 (P2)**: Depends on Phase 2 (AbstractPlatform). Parallel with US1 after Phase 2 completes.
- **US4 (P3)**: Depends on US1 (health checker first used inside `wrap`; extends it for `health` command).
- **US5 (P3)**: Depends on Phase 2 (registry store). Can develop `list`/`status`/`scan` in parallel with US1.

### Within Each Phase

- Templates (T006–T011) before generators that render them (T023, T051)
- AbstractDetector (T012) before concrete detectors (T019, T020)
- Registry models (T013) before registry store (T014)
- AbstractPlatform (T016) before concrete platforms (T024, T031–T035)
- Health states (T017) before health checker (T018)
- SmartScan scanner (T021) before auto-fixer (T022) and wrap command (T025)

---

## Parallel Opportunities Per Story

### Phase 2 (Foundational)
```
After T005: Run simultaneously →
  T006, T007, T008, T009, T010, T011   (all 6 templates, different files)
  T012                                   (detectors/base.py)
  T013, T014                             (registry/models.py then store.py)
  T015                                   (smart_scan/issues.py)
  T016                                   (platforms/base.py)
  T017                                   (health/states.py)
  T018                                   (health/checker.py, after T017)
```

### Phase 3 (US1)
```
Run simultaneously →
  T019  (detectors/node.py)
  T020  (detectors/python.py refactor)

Then simultaneously →
  T021  (smart_scan/scanner.py)    → blocks T022, T025
  T023  (generators/compose.py)   → blocks T025
  T024  (platforms/claude_code.py) → blocks T025
```

### Phase 5 (US3)
```
Run simultaneously →
  T031  (platforms/cursor.py)
  T032  (platforms/vscode.py)
  T033  (platforms/goose.py)
  T034  (platforms/codex.py)
  T035  (platforms/opencode.py)
→ then T036 (platforms/__init__.py) → then T037 (cli.py wire-up)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (**critical — blocks everything**)
3. Complete Phase 3: User Story 1 (T019–T026)
4. **STOP and VALIDATE**: Run `mcplibrarian wrap tests/fixtures/sample-node-server/` end-to-end
5. Ship Option B shell wrappers (Phase 8) in parallel — fast, standalone value

### Incremental Delivery

1. **Phase 1+2+3** → MVP: single-server wrap for Python + Node, Claude Code only
2. **+Phase 4 (US2)** → Batch wrapping, power user ready
3. **+Phase 5 (US3)** → All 6 platforms, full cross-platform value
4. **+Phase 6 (US4)** → Health monitoring, production-grade reliability
5. **+Phase 7 (US5)** → Full registry management UX
6. **+Phase 8** → Option B ships in parallel at any point after Phase 3

### Parallel Team Strategy

With two developers:
- **Dev A**: Phase 1 → Phase 2 (templates T006–T011 + CLI refactor T005) → Phase 3 (US1)
- **Dev B**: Phase 2 (models T013, store T014, health T017–T018) → Phase 5 (US3 platforms T031–T035) → Phase 7 (US5)
- Merge at Phase 9 Polish

---

## Task Count Summary

| Phase | Tasks | Parallelizable |
|-------|-------|---------------|
| Phase 1: Setup | 4 | 2 |
| Phase 2: Foundational | 14 | 8 |
| Phase 3: US1 (P1 MVP) | 8 | 2 |
| Phase 4: US2 (P2) | 4 | 0 |
| Phase 5: US3 (P2) | 7 | 5 |
| Phase 6: US4 (P3) | 5 | 0 |
| Phase 7: US5 (P3) | 4 | 2 |
| Phase 8: Option B | 4 | 2 |
| Phase 9: Polish | 4 | 2 |
| **Total** | **54** | **23** |

---

## Notes

- All file paths are absolute from repo root
- `[P]` tasks modify different files — safe to run concurrently
- Commit after each checkpoint (end of each phase) for clean rollback points
- `--dry-run` on `wrap` lets you validate without making changes — use it first on real servers
- Never modify `tests/fixtures/` contents during implementation; they are controlled test inputs
- `docker compose` (no hyphen) throughout — Docker v2 plugin syntax enforced

- [ ] SENTINEL-W1: Sentinel validation for wave 1 (T001, T002, T003, T004, T005, T006, T007, T010, T011, T012, T013, T014, T015, T016, T017, T018, T020, T021, T022, T023, T024, T031, T032, T033, T034, T035, T036, T051, T052, T053, T054): verify all implementations pass tests
- [ ] SENTINEL-W2: Sentinel validation for wave 2 (T008, T025, T027, T039, T040): verify all implementations pass tests
- [ ] SENTINEL-W3: Sentinel validation for wave 3 (T009, T026, T042): verify all implementations pass tests
- [ ] SENTINEL-W4: Sentinel validation for wave 4 (T019, T028): verify all implementations pass tests
- [ ] SENTINEL-W5: Sentinel validation for wave 5 (T029, T047): verify all implementations pass tests
- [ ] SENTINEL-W6: Sentinel validation for wave 6 (T030, T048, T050): verify all implementations pass tests
- [ ] SENTINEL-W7: Sentinel validation for wave 7 (T037, T049): verify all implementations pass tests
- [ ] SENTINEL-W8: Sentinel validation for wave 8 (T038): verify all implementations pass tests
- [ ] SENTINEL-W9: Sentinel validation for wave 9 (T041): verify all implementations pass tests
- [ ] SENTINEL-W10: Sentinel validation for wave 10 (T043): verify all implementations pass tests
- [ ] SENTINEL-W11: Sentinel validation for wave 11 (T044): verify all implementations pass tests
- [ ] SENTINEL-W12: Sentinel validation for wave 12 (T045): verify all implementations pass tests
- [ ] SENTINEL-W13: Sentinel validation for wave 13 (T046): verify all implementations pass tests

- [ ] SENTINEL-W1: Sentinel validation for wave 1 (T001, T002, T003, T004, T005, T006, T007, T010, T011, T012, T013, T014, T015, T016, T017, T018, T020, T021, T022, T023, T024, T031, T032, T033, T034, T035, T036, T051, T052, T053, T054, T055, T056, T057, T058, T059, T060, T061, T062, T063, T064, T065, T066, T067): verify all implementations pass tests
