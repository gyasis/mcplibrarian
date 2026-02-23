# Implementation Plan: MCP Librarian — Cross-Platform MCP Server Containerization

**Branch**: `001-mcp-librarian` | **Date**: 2026-02-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/001-mcp-librarian/spec.md`

## Summary

MCP Librarian automates the containerization of MCP servers so they can run on-demand across any AI coding platform. The existing `mcp_dockerize` Python package (Python/Click/Jinja2/docker-SDK) provides a working foundation for Python server detection and Dockerfile generation. This plan extends that foundation with: Node.js detection, a Smart-Scan auto-fix engine, a local registry, health checks, automatic platform config updates, and a batch-wrapping mode — all within the existing Python codebase, with a parallel lightweight shell-wrapper path for quick delivery.

## Technical Context

**Language/Version**: Python 3.10+ (existing; all new modules extend `src/mcp_dockerize/`)
**Primary Dependencies**: Click 8.1+ (CLI), Jinja2 3.1+ (templates), docker 7.0+ (Python SDK), python-dotenv 1.0+ (env file parsing), toml 0.10.2+ (pyproject.toml parsing) — all already in pyproject.toml. **New addition**: `pyyaml>=6.0` for Block's Goose and OpenAI Codex YAML config files
**Storage**: JSON file (`~/.config/mcp-librarian/registry.json`) — no new dependency needed; SQLite migration deferred to Option A full-CLI phase
**Testing**: pytest + pytest-mock; integration tests against real Docker via docker-SDK; fixture servers at `tests/fixtures/`
**Target Platform**: Linux (primary), macOS (secondary), Windows/WSL (future)
**Project Type**: Single project — extends existing `src/mcp_dockerize/` package; CLI entry point `mcplibrarian`
**Performance Goals**: Single server wrap < 60 seconds end-to-end (detect + build + health check); batch of 10 servers < 60 seconds with concurrent builds
**Constraints**: Docker daemon must be installed and running; credentials must never enter Docker image layers; no internet required at wrap time; existing `mcplibrarian` command must continue to work
**Scale/Scope**: Supports Python and Node.js runtimes; 6 AI platforms (Claude Code, Cursor, VS Code Copilot, Block's Goose, OpenAI Codex, opencode); up to 100+ registered servers per user; single-developer machines (not server clusters)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

> **No constitution.md exists** — `.specify/memory/constitution.md` was not found. Default software engineering principles apply. A `/speckit.constitution` run is recommended before this plan advances to implementation.

**Applying default principles:**

| Gate | Status | Notes |
|------|--------|-------|
| No unnecessary new dependencies | PASS | All new modules use existing deps; JSON registry needs no new dep |
| No credentials in Docker images | PASS | Existing CLAUDE.md rule, enforced in generator code |
| No breaking changes to existing CLI | PASS | New commands and flags added; `mcplibrarian <path>` signature unchanged |
| Tests alongside every new module | PASS | Research phase identified unit + integration test plan |
| Simplicity (no premature abstraction) | PASS | Shell wrappers (Option B) built before full CLI (Option A) |
| Docker v2 command syntax | PASS | `docker compose` (no hyphen) — enforced per project rules |

**No violations requiring justification.**

## Project Structure

### Documentation (this feature)

```text
specs/001-mcp-librarian/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── cli-commands.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created here)
```

### Source Code (repository root)

```text
src/
└── mcp_dockerize/
    ├── __init__.py                  # EXISTS
    ├── cli.py                       # EXISTS → extend with new commands
    ├── detectors/
    │   ├── __init__.py              # EXISTS
    │   ├── base.py                  # NEW: AbstractDetector interface
    │   ├── python.py                # EXISTS: Python FastMCP detector
    │   └── node.py                  # NEW: Node.js MCP SDK detector
    ├── generators/
    │   ├── __init__.py              # EXISTS
    │   ├── dockerfile.py            # EXISTS → extend with Node.js templates
    │   └── compose.py               # NEW: docker-compose.yml generator
    ├── smart_scan/
    │   ├── __init__.py              # NEW
    │   ├── scanner.py               # NEW: orchestrates detection + issue finding
    │   ├── issues.py                # NEW: Issue enum + descriptions
    │   └── fixer.py                 # NEW: auto-fix strategies
    ├── registry/
    │   ├── __init__.py              # NEW
    │   ├── models.py                # NEW: RegistryEntry, HealthRecord dataclasses
    │   └── store.py                 # NEW: JSON-backed registry CRUD
    ├── health/
    │   ├── __init__.py              # NEW
    │   ├── checker.py               # NEW: multi-level MCP health check
    │   └── states.py                # NEW: HealthStatus enum
    ├── platforms/
    │   ├── __init__.py              # NEW
    │   ├── base.py                  # NEW: AbstractPlatform interface (JSON + YAML variants)
    │   ├── claude_code.py           # NEW: Claude Code config updater (JSON)
    │   ├── cursor.py                # NEW: Cursor IDE config updater (JSON)
    │   ├── vscode.py                # NEW: VS Code Copilot config updater (JSON, nested key)
    │   ├── goose.py                 # NEW: Block's Goose config updater (YAML extensions)
    │   ├── codex.py                 # NEW: OpenAI Codex updater (YAML + wrapper script gen)
    │   └── opencode.py              # NEW: opencode (SST) config updater (JSON)
    ├── builders/
    │   ├── __init__.py              # EXISTS
    │   └── docker_builder.py        # EXISTS → integrate with smart_scan
    ├── testers/
    │   ├── __init__.py              # EXISTS
    │   └── mcp_tester.py            # EXISTS → evolve into health/checker.py
    └── templates/
        ├── python-uv.Dockerfile.j2          # NEEDS CREATION (blocked existing usage)
        ├── python-direct.Dockerfile.j2      # NEEDS CREATION
        ├── node-npm.Dockerfile.j2           # NEW
        ├── docker-compose.yml.j2            # NEW
        └── env-example.j2                   # NEW

tests/
├── __init__.py
├── unit/
│   ├── test_python_detector.py      # NEW
│   ├── test_node_detector.py        # NEW
│   ├── test_smart_scan.py           # NEW
│   ├── test_registry.py             # NEW
│   └── test_health_checker.py       # NEW
├── integration/
│   ├── test_wrap_python_server.py   # NEW
│   ├── test_wrap_node_server.py     # NEW
│   └── test_batch_wrap.py           # NEW
└── fixtures/
    ├── sample-python-server/        # NEW: minimal FastMCP server
    └── sample-node-server/          # NEW: minimal @modelcontextprotocol/sdk server

wrap-mcp.sh                          # NEW: Option B shell wrapper
list-wrapped.sh                      # NEW: Option B list script
health-check.sh                      # NEW: Option B health check script
unwrap-mcp.sh                        # NEW: Option B unwrap script
```

**Structure Decision**: Single project. All new features extend the existing `src/mcp_dockerize/` package. No new top-level packages or services. Shell wrapper scripts live at the repository root as the Option B quick-start track. Tests live at `tests/` (new, not yet present).

## Complexity Tracking

> No constitution violations — section not required.
