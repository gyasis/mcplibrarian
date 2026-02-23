# MCP Librarian Automation: Product Requirements Document

**Version:** 1.1
**Date:** 2026-02-19
**Status:** REVISED DRAFT
**Owner:** Product Team
**Classification:** Internal

> **v1.1 Strategy Update (2026-02-19):** Claude Code added native MCP lazy loading (`defer_loading`) in January 2026. However, research confirms that **5 out of 7 major AI coding platforms** (Cursor, VS Code Copilot, Windsurf, Continue.dev, Block's Goose) do **not** support native lazy loading. mcplibrarian is now positioned as the **cross-platform MCP containerization standard** — not a Claude-specific tool.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & User Stories](#2-problem-statement--user-stories)
3. [Current State Analysis](#3-current-state-analysis)
4. [Solution Architecture - Dual Track Strategy](#4-solution-architecture---dual-track-strategy)
5. [Feature Requirements & Core Innovations](#5-feature-requirements--core-innovations)
6. [Implementation Roadmap](#6-implementation-roadmap)
7. [Success Metrics & KPIs](#7-success-metrics--kpis)
8. [Creative Innovations & Future Vision](#8-creative-innovations--future-vision)
9. [Risk Assessment & Mitigation](#9-risk-assessment--mitigation)
10. [Appendix](#10-appendix)

---

## 1. Executive Summary

### 1.1 Vision Statement

**"The cross-platform standard for MCP server containerization."**

MCP Librarian transforms the chaotic, error-prone process of wrapping MCP servers in Docker containers into a seamless, one-command experience. While Claude Code now has native MCP lazy loading, **5 out of 7 major AI coding platforms still lack this capability** — and all platforms benefit from the isolation, portability, and security that proper containerization provides.

**The market reality (as of early 2026):**

| Platform | Native Lazy Loading | Needs mcplibrarian? |
|----------|--------------------|--------------------|
| Claude Code | ✅ Yes (`defer_loading`) | For security/portability only |
| Cursor IDE | ❌ No | **Yes — only solution available** |
| VS Code Copilot | ❌ No | **Yes — feature requested, not built** |
| Windsurf | ❌ No | **Yes — eager loading by default** |
| Continue.dev | Partial (middleware) | **Yes — native client has no support** |
| Block's Goose | Architectural only | **Yes — `defer_loading` flag not respected** |
| opencode (SST) | ❌ No (Issue #9350 open) | **Yes — community requesting this exact feature** |
| OpenAI Codex | Alternative (Skills/AGENTS.md) | **Yes — different spec, Docker still needed** |

### 1.2 The North Star

**Goal:** Be the one-command MCP containerization tool that works across every AI coding platform, reducing time-to-first-tool from 30+ minutes to under 60 seconds with a 95%+ build success rate.

**Impact:**
- Developers spend time using AI, not configuring infrastructure
- **Cursor/VS Code/Windsurf users** finally get lazy loading (no native option exists for them)
- Enterprise teams can manage 100+ MCP servers across any platform without context saturation
- Containerized servers are portable, secure, and reproducible across machines and teams

### 1.3 Strategic Approach: Dual-Track Parallel Development

We are pursuing **TWO complementary tracks simultaneously** to balance immediate value delivery with long-term vision:

| Track | Timeframe | Value Proposition |
|-------|-----------|-------------------|
| **Option A: "libra" CLI** | 4-6 weeks | Full automation with Docker socket discovery, smart-scan auto-fixes, health monitoring |
| **Option B: Shell Wrappers** | 1-2 weeks | Improved DX with current scripts, ship faster, gather user feedback |

**WHY BOTH?**
- **Option B** delivers immediate relief to early adopters and validates core assumptions
- **Option A** builds the infrastructure for scale, enterprise features, and platform independence
- **Learnings from B** directly inform **A's** design and priority order
- **Both tracks** share the same Smart-Scan Engine and MCP Registry backend

**Strategic Phasing:**
1. **Week 1-2:** Ship Option B (shell wrappers) to beta users
2. **Week 2-6:** Build Option A (libra CLI) while gathering Option B feedback
3. **Week 6+:** Transition users from B to A with backward compatibility

---

## 2. Problem Statement & User Stories

### 2.1 The Core Problem

**Current Reality:** Wrapping MCP servers in Docker containers requires manual, error-prone steps that violate the principle "make MCP setup painless." This problem is **platform-agnostic** — it affects every AI coding assistant user, not just Claude Code users.

**Pain Point Breakdown:**
- Manual docker-compose.yml generation (syntax errors, wrong paths, missing env vars)
- Missing package-lock.json files trigger npm install failures
- Credentials handling is insecure (hardcoded secrets, wrong mount points)
- Build errors require Docker expertise to debug
- Manual registry updates for every new server
- No health checks to verify containers are actually working

**The Platform Gap (2026 Context):**
Claude Code introduced native `defer_loading` in January 2026 — but this only helps Claude Code users. Cursor IDE, VS Code Copilot, Windsurf, Continue.dev, and Block's Goose have **no native lazy loading**. For these platforms, Docker-based containerization is the **only available solution** for context management and tool isolation. This represents the majority of the AI coding assistant market.

**Business Impact:**
- 30+ minutes per MCP server setup (on any platform)
- 60-70% failure rate on first attempt
- High abandonment (users give up and load all servers upfront)
- Token savings potential remains unrealized on 5 of 7 platforms
- Security risk from non-containerized servers running with host access

### 2.2 User Stories

#### Story 1: "The Frustrated Developer"

**Persona:** Sarah, Full-Stack Developer
**Context:** Watched Playwright MCP tutorial, excited about token savings

**Journey:**
```
11:00 AM - "This looks easy! Let me dockerize the playwright server"
11:05 AM - Runs mcp-dockerize, gets docker-compose.yml
11:10 AM - docker compose up
11:11 AM - ERROR: Missing package-lock.json
11:15 AM - "I'll generate it manually..."
11:20 AM - npm install fails (wrong Node version)
11:30 AM - Googles "docker node version mismatch"
11:45 AM - Tries to fix Dockerfile, breaks volume mounts
12:00 PM - "This is too complicated. I'll just load all servers."
```

**Pain Points:**
1. No automatic package-lock.json generation
2. Node version detection failed
3. Error messages are cryptic
4. No rollback/recovery mechanism
5. 1 hour wasted, zero working tools

**Desired Experience (Option A):**
```
11:00 AM - libra wrap /path/to/playwright-mcp
11:01 AM - [Smart-Scan] Detected Node 18, generating package-lock.json
11:01 AM - [Build] Container built successfully
11:02 AM - [Registry] Added to MCP registry, ready to use
11:02 AM - "Done! Your server is ready."
```

**Desired Experience (Option B):**
```
11:00 AM - ./wrap-mcp.sh /path/to/playwright-mcp
11:01 AM - [Wrapper] Generating docker-compose.yml...
11:01 AM - [Wrapper] Creating package-lock.json...
11:02 AM - [Wrapper] Building container...
11:03 AM - [Wrapper] Run 'docker compose up -d' to start
```

#### Story 2: "The Context-Aware Power User"

**Persona:** Marcus, DevOps Engineer
**Context:** Managing 10+ MCP servers across multiple projects

**Journey:**
```
Day 1: "I need to optimize my Claude Code context window"
       - Reads about Docker lazy loading (99% token savings)
       - Excited to wrap all 10 servers

Day 2: Wraps first server (github-mcp)
       - 25 minutes, works after 3 attempts
       - Manually updates claude_desktop_config.json

Day 3: Wraps second server (slack-mcp)
       - Credentials are different (OAuth vs API key)
       - Dockerfile template doesn't handle this
       - Another 30 minutes

Day 4: "I can't spend 4 hours doing this for all servers"
       - Gives up on remaining 8 servers
       - Token savings: 20% instead of potential 99%
```

**Pain Points:**
1. No batch processing for multiple servers
2. Credential handling varies by server type
3. Manual registry updates for each server
4. No central dashboard to see what's wrapped/active
5. Configuration drift across servers

**Desired Experience (Option A):**
```
libra wrap-all --scan ~/mcp-servers/
[Scanner] Found 10 MCP servers
[Smart-Scan] Analyzing credentials patterns...
[Batch] Wrapping 10 servers (parallel)
[Progress] github-mcp: ✓ | slack-mcp: ✓ | postgres-mcp: ✓ ...
[Registry] All 10 servers added to registry
[CLI] Run 'libra dashboard' to view status
```

#### Story 3: "The Token Miser"

**Persona:** Elena, AI Researcher
**Context:** Working with limited API budget, needs maximum context efficiency

**Journey:**
```
Problem: "My Claude Code uses 75k tokens before I ask a question"
Research: Discovers Docker lazy loading can reduce to 1.5k tokens
Attempt: Tries to wrap deeplake-rag server (research database)

Issues:
1. Large data volume at /media/gyasis/Drive 2/Deeplake_Storage/
   - docker-compose.yml can't handle spaces in paths
   - Bind mount fails with cryptic error

2. Environment variables (.env file)
   - No template provided
   - Unclear which vars are required vs optional

3. After 2 hours:
   - Container built but won't start
   - No health check to diagnose
   - No logs showing what failed

Result: "I wasted 2 hours and still have 75k token overhead"
```

**Pain Points:**
1. Path handling (spaces, special characters)
2. Volume mount configuration for large datasets
3. Environment variable documentation missing
4. No diagnostic tools (health checks, logs)
5. Unclear whether problem is Docker, MCP, or configuration

**Desired Experience (Option A):**
```
libra wrap /path/to/deeplake-rag --data-volume "/media/gyasis/Drive 2/..."
[Smart-Scan] Detected spaces in path, escaping properly
[Smart-Scan] Large data volume detected, using bind mount
[Smart-Scan] Missing .env vars: OPENAI_API_KEY, ACTIVELOOP_TOKEN
[Prompt] Enter OPENAI_API_KEY: ****
[Health] Container started, running health check...
[Health] ✓ Server responding to JSON-RPC initialize
[Registry] Added to registry with 99% token savings
```

#### Story 4: "The Cursor Power User" *(Added v1.1)*

**Persona:** Jordan, senior engineer on Cursor IDE
**Context:** Uses 12 MCP servers in Cursor, no native lazy loading available

**Journey:**
```
Problem: "Cursor loads all my MCP tools at startup. 8GB RAM used before I code."
Research: Finds Claude Code added native defer_loading — but Jordan uses Cursor.
Attempt: Searches for Cursor-native solution, finds nothing.

Discovers mcplibrarian:
→ Wraps all 12 servers in Docker containers
→ Each server starts on-demand, stops after 5min idle
→ RAM drops from 8GB to ~400MB
→ Context window no longer pre-filled with 50k tokens of tool definitions
```

**Why mcplibrarian is the only option for Jordan:**
- Cursor doesn't support `defer_loading` (confirmed, Jan 2026)
- Community proxy `mcp-on-demand` requires manual Docker config (same problem)
- mcplibrarian automates the containerization Jordan would otherwise do by hand

---

### 2.3 Problem Impact Summary

| Metric | Current State | User Impact |
|--------|--------------|-------------|
| Time-to-First-Tool | 30-60 minutes | High abandonment |
| Build Success Rate | 30-40% first attempt | Frustration, context switching |
| Token Savings Realized | 20% of potential | Wasted API budget |
| Servers per User | 1-2 (avg) | Missed optimization opportunities |
| Support Requests | High (setup errors) | Engineering time drain |

---

## 3. Current State Analysis

### 3.1 The Playwright Tutorial Moment

**What Happened:**
During the Playwright MCP tutorial, we discovered the current `mcp-dockerize` tool generates docker-compose.yml files that immediately fail with:

```
ERROR: Missing package-lock.json
```

**Root Cause Analysis:**
1. **package-lock.json** is gitignored by most MCP server repos
2. `mcp-dockerize` generates Dockerfile with `COPY package-lock.json`
3. Build fails because file doesn't exist in source tree
4. User must manually run `npm install --package-lock-only`
5. User must know this is the fix (not documented)

**Cascading Failures:**
- If user generates package-lock.json, Node version might mismatch
- If Node version wrong, dependencies fail to install
- If dependencies fail, no clear error about which step broke
- User tries to fix docker-compose.yml syntax (wrong fix)
- Cycle of trial-and-error begins

**Key Insight:** This single issue exposed a fundamental flaw - **we generate configuration but don't validate it will actually work.**

### 3.1b Competitive Landscape Update (v1.1 — February 2026)

> **Context:** This section was added after Anthropic released native MCP lazy loading for Claude Code in January 2026. The competitive landscape has shifted — but the market opportunity has been clarified, not eliminated.

#### What Changed

**January 2026:** Anthropic introduced `defer_loading: true` flag for MCP servers in Claude Code. Tools marked with this flag are excluded from the initial context and discovered on-demand via a native `ToolSearch` tool using Regex/BM25 search. This achieves ~85-95% token reduction natively — no Docker proxy required.

```json
// Claude Code now handles this natively:
{
  "mcpServers": {
    "github": {
      "command": "...",
      "defer_loading": true
    }
  }
}
```

#### What Did NOT Change

The 5 other major platforms **do not support `defer_loading`**:

| Platform | Status | Evidence |
|----------|--------|----------|
| **Cursor IDE** | No native support | Loads all tools globally at launch from `~/.cursor/mcp.json`; community uses Docker proxies as only workaround |
| **VS Code Copilot** | No native support | GitHub Issue #288310 opened Jan 2026 requesting the feature — not implemented |
| **Windsurf** | No native support | Default eager loading; `~/.codeium/windsurf/mcp_config.json` has no `defer_loading` field |
| **Continue.dev** | Middleware only | Relies on server-side aggregation, not native client-side deferral |
| **Block's Goose** | Architectural workaround | Uses "Summon/Powers" paradigm — `defer_loading` JSON flag not respected |
| **opencode (SST)** | No native support | Eager loads all tools at startup; GitHub Issue #9350 filed but not implemented |

#### Market Opportunity Reframe

The original PRD positioned mcplibrarian as solving a problem for Claude Code users. The revised positioning:

**mcplibrarian = the cross-platform Docker automation layer that gives every AI coding assistant user what Claude Code users now get natively.**

---

### 3.2 Current System Input/Output Flow

**INPUT (User provides):**
```
/path/to/mcp-server/     # MCP server directory
```

**CURRENT PROCESS:**
```
Step 1: mcp-dockerize /path/to/mcp-server
        └─> Scans directory structure
        └─> Detects Python or Node.js
        └─> Generates Dockerfile (template-based)
        └─> Generates docker-compose.yml
        └─> Generates README.md

Step 2: User manually runs:
        docker compose build    # ❌ Often fails here
        docker compose up       # ❌ Or fails here

Step 3: User manually updates:
        ~/.config/Claude/claude_desktop_config.json
```

**OUTPUT (What user gets):**
```
docker-configs/
├── Dockerfile                 # Generated
├── docker-compose.yml          # Generated
├── README.md                   # Generated
└── .env.example                # Generated
```

**GAP ANALYSIS:**

| What's Generated | What Actually Works | Gap |
|-----------------|---------------------|-----|
| Dockerfile with COPY package-lock.json | File doesn't exist | No package-lock.json generation |
| docker-compose.yml with paths | Paths may have spaces/errors | No path validation |
| .env.example | User doesn't know required vars | No env var detection |
| Build commands | Build may fail | No build validation |
| Manual config update | User forgets this step | No registry auto-update |

### 3.3 Pain Points by Phase

#### Phase 1: Detection & Generation
**Current:**
- ✅ Detects Python/Node correctly (works well)
- ✅ Identifies FastMCP vs MCP SDK (works well)
- ❌ Doesn't detect Node version needed
- ❌ Doesn't detect if package-lock.json exists
- ❌ Doesn't detect credentials patterns
- ❌ Doesn't validate volume paths

#### Phase 2: Build
**Current:**
- ❌ No pre-build validation (blind execution)
- ❌ Error messages from Docker (not from our tool)
- ❌ No automatic retry with fixes
- ❌ No rollback if build fails
- ❌ User must debug Docker errors themselves

#### Phase 3: Registry Integration
**Current:**
- ❌ User must manually edit `claude_desktop_config.json`
- ❌ No validation that JSON syntax is correct
- ❌ No automatic registry update
- ❌ No tracking of which servers are wrapped

#### Phase 4: Runtime & Health
**Current:**
- ❌ No health checks
- ❌ No validation server actually responds to MCP protocol
- ❌ Container might start but not work
- ❌ No logs/diagnostics exposed to user

### 3.4 Technical Debt Analysis

**Current Architecture Limitations:**

```python
# Current: Template-based generation (brittle)
def generate_dockerfile(server_type):
    if server_type == "python":
        return PYTHON_TEMPLATE  # Static template
    elif server_type == "node":
        return NODE_TEMPLATE    # Static template
```

**Problems:**
1. **Static templates** can't handle edge cases (missing files, version mismatches)
2. **No validation layer** between generation and execution
3. **No feedback loop** from build failures back to generation
4. **No state tracking** (can't resume failed builds)

**Desired Architecture:**

```python
# Smart-Scan Engine (adaptive)
def generate_dockerfile(server_path):
    context = SmartScan(server_path)
    context.detect_runtime()
    context.detect_dependencies()
    context.validate_paths()
    context.detect_credentials()

    if context.has_issues():
        context.auto_fix_issues()

    dockerfile = context.render_dockerfile()
    dockerfile.validate()
    return dockerfile
```

### 3.5 User Friction Map

**Friction Points Ranked by Impact:**

| Rank | Friction Point | Impact | Frequency | User Abandonment Risk |
|------|---------------|---------|-----------|----------------------|
| 1 | Missing package-lock.json | HIGH | 90% | 60% abandon here |
| 2 | Unclear error messages | HIGH | 80% | 40% abandon here |
| 3 | Manual registry update | MEDIUM | 100% | 20% abandon here |
| 4 | No health checks | MEDIUM | 100% | 30% (silent failure) |
| 5 | Path validation issues | HIGH | 30% | 50% abandon here |
| 6 | Credential setup unclear | MEDIUM | 70% | 25% abandon here |

**Total Abandonment Rate (Current):** ~60-70% of users fail on first attempt

---

## 4. Solution Architecture - Dual Track Strategy

### 4.1 Strategic Rationale

We are building **TWO solutions in parallel** because:

1. **Different timelines** - Option B ships in weeks, Option A ships in months
2. **Risk mitigation** - Option B validates assumptions before heavy Option A investment
3. **User feedback** - Early adopters help shape Option A features
4. **Team capacity** - Different skills (shell scripting vs Rust/Go development)
5. **Migration path** - Option B users can seamlessly upgrade to Option A

**Key Principle:** Both options share the **same backend** (Smart-Scan Engine, MCP Registry), only the CLI interface differs.

---

### 4.2 Option A: "libra" CLI Tool (Vision Track)

#### 4.2.1 Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    libra CLI (Rust)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Command    │  │   Docker     │  │   Health     │      │
│  │   Parser     │  │   Socket     │  │   Monitor    │      │
│  │              │  │   Discovery  │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Smart-Scan Engine (Core)                   │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  • Runtime Detection (Python/Node/Rust)              │   │
│  │  • Dependency Analysis (package.json/pyproject.toml)  │   │
│  │  • Credential Pattern Detection (OAuth/API Keys)      │   │
│  │  • Path Validation (spaces, symlinks, permissions)    │   │
│  │  • Auto-Fix Engine (generate missing files)          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            MCP Registry (SQLite)                      │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  Servers Table:                                       │   │
│  │    - id, name, path, status, health, created_at      │   │
│  │  Triggers Table:                                      │   │
│  │    - server_id, trigger_word, priority               │   │
│  │  Health_Logs Table:                                   │   │
│  │    - server_id, check_time, status, response_time    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   ┌──────────┐        ┌──────────┐        ┌──────────┐
   │  Docker  │        │  Config  │        │  Logs &  │
   │  Engine  │        │  Files   │        │  Metrics │
   └──────────┘        └──────────┘        └──────────┘
```

#### 4.2.2 Core Commands

```bash
# One-command wrapping
libra wrap /path/to/mcp-server
  └─> Smart-scan, build, register, health-check (all automatic)

# Batch processing
libra wrap-all --scan ~/mcp-servers/
  └─> Parallel wrapping of multiple servers

# Registry management
libra list                    # Show all wrapped servers
libra status github-mcp       # Show health & metrics
libra remove github-mcp       # Remove from registry

# Health monitoring
libra health --all            # Check all server health
libra dashboard               # Interactive TUI dashboard

# Configuration
libra config set docker-socket /var/run/docker.sock
libra config set claude-config ~/.config/Claude/claude_desktop_config.json

# Advanced
libra wrap --dry-run /path/to/server     # Preview without building
libra rebuild github-mcp                  # Rebuild specific server
libra logs github-mcp                     # View container logs
```

#### 4.2.3 Smart-Scan Engine Details

**Phase 1: Detection**
```rust
pub struct SmartScan {
    server_path: PathBuf,
    runtime: Runtime,           // Python | Node | Rust | Unknown
    package_manager: PkgMgr,    // npm | pip | cargo
    dependencies: Vec<Dependency>,
    credentials: Vec<Credential>,
    volume_mounts: Vec<VolumeMount>,
    issues: Vec<Issue>,
}

impl SmartScan {
    pub fn new(path: PathBuf) -> Result<Self> {
        let mut scanner = Self::default();
        scanner.detect_runtime()?;
        scanner.detect_dependencies()?;
        scanner.detect_credentials()?;
        scanner.validate_paths()?;
        Ok(scanner)
    }
}
```

**Phase 2: Issue Detection**
```rust
pub enum Issue {
    MissingPackageLock { runtime: Runtime },
    NodeVersionMismatch { required: String, detected: String },
    PathHasSpaces { path: PathBuf },
    MissingEnvVar { var: String },
    CredentialNotSecure { credential: String },
    VolumePathNotFound { path: PathBuf },
}
```

**Phase 3: Auto-Fix**
```rust
impl SmartScan {
    pub fn auto_fix_issues(&mut self) -> Result<Vec<Fix>> {
        let mut fixes = vec![];

        for issue in &self.issues {
            match issue {
                Issue::MissingPackageLock { runtime } => {
                    fixes.push(self.generate_package_lock(runtime)?);
                }
                Issue::NodeVersionMismatch { required, detected } => {
                    fixes.push(self.update_dockerfile_node_version(required)?);
                }
                Issue::PathHasSpaces { path } => {
                    fixes.push(self.escape_path_spaces(path)?);
                }
                // ... other auto-fixes
            }
        }

        Ok(fixes)
    }
}
```

#### 4.2.4 Docker Socket Discovery

**Problem:** Docker socket location varies across platforms:
- Linux: `/var/run/docker.sock`
- macOS (Docker Desktop): `/var/run/docker.sock` (symlink to VM)
- Windows (WSL2): `/mnt/wsl/shared-docker/docker.sock`
- Custom Docker contexts: User-defined

**Solution:** Auto-detect with fallback chain

```rust
pub fn discover_docker_socket() -> Result<PathBuf> {
    // Check common locations
    let locations = vec![
        "/var/run/docker.sock",
        "/mnt/wsl/shared-docker/docker.sock",
        "~/.docker/run/docker.sock",
    ];

    for loc in locations {
        if Path::new(loc).exists() {
            return Ok(PathBuf::from(loc));
        }
    }

    // Check docker context
    let ctx = Command::new("docker")
        .args(&["context", "inspect", "--format", "{{.Endpoints.docker.Host}}"])
        .output()?;

    if ctx.status.success() {
        return parse_docker_host(&ctx.stdout);
    }

    Err(Error::DockerSocketNotFound)
}
```

#### 4.2.5 MCP Registry Schema

```sql
-- servers table
CREATE TABLE servers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL,
    runtime TEXT NOT NULL,           -- 'python' | 'node' | 'rust'
    deployment_pattern TEXT NOT NULL, -- 'volume' | 'self-contained'
    status TEXT NOT NULL,             -- 'active' | 'stopped' | 'error'
    container_id TEXT,
    image_name TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- triggers table (for lazy loading)
CREATE TABLE triggers (
    id INTEGER PRIMARY KEY,
    server_id INTEGER NOT NULL,
    trigger_word TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    FOREIGN KEY (server_id) REFERENCES servers(id)
);

-- health_logs table
CREATE TABLE health_logs (
    id INTEGER PRIMARY KEY,
    server_id INTEGER NOT NULL,
    check_time INTEGER NOT NULL,
    status TEXT NOT NULL,             -- 'healthy' | 'unhealthy' | 'timeout'
    response_time_ms INTEGER,
    error_message TEXT,
    FOREIGN KEY (server_id) REFERENCES servers(id)
);

-- credentials table (encrypted)
CREATE TABLE credentials (
    id INTEGER PRIMARY KEY,
    server_id INTEGER NOT NULL,
    env_var_name TEXT NOT NULL,
    encrypted_value BLOB,
    credential_type TEXT NOT NULL,    -- 'api_key' | 'oauth_token' | 'password'
    FOREIGN KEY (server_id) REFERENCES servers(id)
);
```

#### 4.2.6 Health Check System

**Health Check Protocol:**
```bash
# Test 1: Container is running
docker inspect <container_id> --format '{{.State.Running}}'

# Test 2: MCP protocol responds
echo '{"jsonrpc":"2.0","method":"initialize","params":{}}' | \
  docker exec -i <container_id> /app/entrypoint

# Test 3: Tools are available
echo '{"jsonrpc":"2.0","method":"tools/list","params":{}}' | \
  docker exec -i <container_id> /app/entrypoint

# Test 4: Response time is acceptable
# (Should respond within 5 seconds)
```

**Health States:**
- `healthy`: All checks pass, response time < 5s
- `degraded`: Container running but slow (5-15s)
- `unhealthy`: Checks fail or timeout
- `stopped`: Container not running
- `unknown`: Cannot determine state

**Automated Actions:**
```rust
match health_status {
    HealthStatus::Healthy => {
        // Do nothing, all good
    }
    HealthStatus::Degraded => {
        log::warn!("Server {} is slow", server_name);
        // Optionally restart container
    }
    HealthStatus::Unhealthy => {
        log::error!("Server {} is unhealthy", server_name);
        // Attempt automatic recovery
        attempt_recovery(server_name)?;
    }
    HealthStatus::Stopped => {
        // User explicitly stopped, don't restart
    }
}
```

#### 4.2.7 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| CLI Framework | Rust + clap | Fast, cross-platform, single binary |
| Docker Integration | bollard (Docker SDK) | Type-safe Docker API client |
| Database | SQLite + rusqlite | Embedded, no dependencies, fast |
| Config Parsing | serde + toml/json | Robust serialization |
| Path Handling | camino | Cross-platform path handling |
| Credential Encryption | ring (AES-256-GCM) | Secure local credential storage |
| Terminal UI | ratatui | Beautiful interactive dashboards |
| Testing | Docker test containers | Integration tests with real Docker |

---

### 4.3 Option B: Shell Wrappers (Quick Win Track)

#### 4.3.1 Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│            wrap-mcp.sh (Bash Entry Point)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: /path/to/mcp-server                                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Phase 1: Detection (existing mcp-dockerize)         │   │
│  │  - Calls: uv run mcp-dockerize <path>                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Phase 2: Pre-Build Fixes (NEW shell logic)          │   │
│  │  - Check if package-lock.json exists                 │   │
│  │  - Generate if missing (npm install --package-lock)  │   │
│  │  - Validate docker-compose.yml syntax                │   │
│  │  - Check .env.example has all vars                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Phase 3: Build & Validate (docker commands)         │   │
│  │  - docker compose build                               │   │
│  │  - Capture errors, retry with fixes                  │   │
│  │  - docker compose up -d                               │   │
│  │  - Wait for healthy state                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Phase 4: Registry Update (config file edit)         │   │
│  │  - Detect claude_desktop_config.json location        │   │
│  │  - Add server block with jq                          │   │
│  │  - Validate JSON syntax                              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Output:                                                     │
│  - ✓ Container built and running                            │
│  - ✓ Registry updated                                       │
│  - ✓ Health check passed                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 4.3.2 Implementation Example

**wrap-mcp.sh:**
```bash
#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SERVER_PATH="$1"
SERVER_NAME=$(basename "$SERVER_PATH")
OUTPUT_DIR="docker-configs/$SERVER_NAME"

echo -e "${GREEN}[MCP Wrapper]${NC} Wrapping $SERVER_NAME..."

# Phase 1: Generate config (existing mcp-dockerize)
echo -e "${GREEN}[Generate]${NC} Creating Docker configuration..."
cd /path/to/mcplibrarian
uv run mcp-dockerize "$SERVER_PATH" --output "docker-configs"

# Phase 2: Smart fixes
echo -e "${GREEN}[Smart-Fix]${NC} Checking for common issues..."

# Check for package-lock.json (Node.js servers)
if [ -f "$OUTPUT_DIR/package.json" ] && [ ! -f "$OUTPUT_DIR/package-lock.json" ]; then
    echo -e "${YELLOW}[Fix]${NC} Missing package-lock.json, generating..."
    cd "$OUTPUT_DIR"
    docker run --rm -v "$PWD:/app" -w /app node:18 npm install --package-lock-only
    cd -
fi

# Validate docker-compose.yml syntax
echo -e "${GREEN}[Validate]${NC} Checking docker-compose.yml..."
docker compose -f "$OUTPUT_DIR/docker-compose.yml" config > /dev/null 2>&1 || {
    echo -e "${RED}[Error]${NC} Invalid docker-compose.yml syntax"
    exit 1
}

# Phase 3: Build and start
echo -e "${GREEN}[Build]${NC} Building Docker image..."
cd "$OUTPUT_DIR"
docker compose build || {
    echo -e "${RED}[Error]${NC} Build failed. Check logs above."
    exit 1
}

echo -e "${GREEN}[Start]${NC} Starting container..."
docker compose up -d

# Wait for healthy state
echo -e "${GREEN}[Health]${NC} Waiting for server to become healthy..."
sleep 3

CONTAINER_ID=$(docker compose ps -q)
if docker exec "$CONTAINER_ID" echo '{"jsonrpc":"2.0","method":"initialize","params":{}}' | timeout 5s cat > /dev/null 2>&1; then
    echo -e "${GREEN}[Health]${NC} Server is healthy!"
else
    echo -e "${YELLOW}[Warning]${NC} Server started but health check unclear"
fi

cd -

# Phase 4: Update registry
echo -e "${GREEN}[Registry]${NC} Updating Claude Code configuration..."
CLAUDE_CONFIG="$HOME/.config/Claude/claude_desktop_config.json"

if [ -f "$CLAUDE_CONFIG" ]; then
    # Backup existing config
    cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.backup"

    # Add server using jq
    jq ".mcpServers[\"$SERVER_NAME\"] = {
        \"command\": \"docker\",
        \"args\": [\"compose\", \"-f\", \"$(pwd)/$OUTPUT_DIR/docker-compose.yml\", \"run\", \"--rm\", \"$SERVER_NAME\"]
    }" "$CLAUDE_CONFIG" > "$CLAUDE_CONFIG.tmp"

    mv "$CLAUDE_CONFIG.tmp" "$CLAUDE_CONFIG"
    echo -e "${GREEN}[Registry]${NC} Added $SERVER_NAME to Claude Code config"
else
    echo -e "${YELLOW}[Warning]${NC} Claude config not found at $CLAUDE_CONFIG"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Success!${NC} $SERVER_NAME is ready to use"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Restart Claude Code to load new server"
echo "  2. Test with: echo '{\"jsonrpc\":\"2.0\",\"method\":\"initialize\"}' | docker compose -f $OUTPUT_DIR/docker-compose.yml run --rm $SERVER_NAME"
```

#### 4.3.3 Additional Helper Scripts

**list-wrapped.sh:**
```bash
#!/bin/bash
# List all wrapped MCP servers

CONFIGS_DIR="docker-configs"

echo "Wrapped MCP Servers:"
echo "===================="

for dir in "$CONFIGS_DIR"/*; do
    if [ -d "$dir" ]; then
        SERVER_NAME=$(basename "$dir")
        COMPOSE_FILE="$dir/docker-compose.yml"

        if [ -f "$COMPOSE_FILE" ]; then
            # Check if container is running
            cd "$dir"
            if docker compose ps | grep -q "Up"; then
                STATUS="🟢 Running"
            else
                STATUS="🔴 Stopped"
            fi
            cd - > /dev/null

            echo "  $STATUS $SERVER_NAME"
        fi
    fi
done
```

**health-check.sh:**
```bash
#!/bin/bash
# Check health of wrapped servers

SERVER_NAME="$1"
COMPOSE_FILE="docker-configs/$SERVER_NAME/docker-compose.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Error: Server $SERVER_NAME not found"
    exit 1
fi

cd "docker-configs/$SERVER_NAME"

# Get container ID
CONTAINER_ID=$(docker compose ps -q)

if [ -z "$CONTAINER_ID" ]; then
    echo "Status: 🔴 Stopped"
    exit 0
fi

# Test MCP protocol
echo '{"jsonrpc":"2.0","method":"initialize","params":{}}' | \
    docker exec -i "$CONTAINER_ID" sh -c 'cat' | \
    grep -q "jsonrpc" && {
    echo "Status: 🟢 Healthy"
} || {
    echo "Status: 🟡 Running but not responding"
}
```

#### 4.3.4 Directory Structure

```
mcplibrarian/
├── wrap-mcp.sh              # Main wrapper script
├── list-wrapped.sh          # List all wrapped servers
├── health-check.sh          # Check server health
├── unwrap-mcp.sh            # Remove server from registry
├── src/                     # Existing mcp-dockerize Python code
│   └── mcp_dockerize/
└── docker-configs/          # Generated configs
    ├── playwright-mcp/
    │   ├── docker-compose.yml
    │   ├── Dockerfile
    │   ├── package-lock.json  # Auto-generated!
    │   └── README.md
    └── deeplake-rag/
        ├── docker-compose.yml
        ├── Dockerfile
        └── .env
```

#### 4.3.5 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Wrapper Scripts | Bash | Universal, no dependencies |
| Config Generation | Python (existing) | Already implemented |
| JSON Manipulation | jq | Standard JSON CLI tool |
| Docker Interaction | docker, docker compose | Standard Docker CLI |
| Validation | shellcheck | Linting for shell scripts |

#### 4.3.6 Limitations & Tradeoffs

**Pros:**
- ✅ Ships in 1-2 weeks
- ✅ No new dependencies (bash, jq, docker already available)
- ✅ Easy to debug (shell scripts are readable)
- ✅ Validates assumptions before building full CLI

**Cons:**
- ❌ Less sophisticated error handling than Rust CLI
- ❌ No interactive TUI dashboard
- ❌ Platform-dependent (assumes bash, jq available)
- ❌ No database for registry (uses config file directly)
- ❌ Manual health checks (not automated monitoring)

**Migration Path to Option A:**
```bash
# Option B user has this:
./wrap-mcp.sh /path/to/server

# When Option A ships:
libra import-wrapped ./docker-configs/*
  └─> Migrates all wrapped servers to libra registry
  └─> Backward compatible with existing containers
```

---

### 4.4 Shared Backend Components

**Both Option A and Option B share:**

1. **Smart-Scan Logic:**
   - Option B: Bash functions in `wrap-mcp.sh`
   - Option A: Rust library in `libra`
   - **Migration:** Extract Bash logic, rewrite in Rust, maintain same behavior

2. **MCP Registry Concept:**
   - Option B: JSON file (`~/.mcp-librarian/registry.json`)
   - Option A: SQLite database (`~/.mcp-librarian/registry.db`)
   - **Migration:** JSON → SQLite converter built into Option A

3. **Health Check Protocol:**
   - Same JSON-RPC test across both options
   - Same "healthy/unhealthy" states
   - Option A adds automated monitoring

4. **Configuration Templates:**
   - Same Dockerfile/docker-compose.yml templates
   - Both use same volume mount patterns
   - Both support same credential patterns

---

## 5. Feature Requirements & Core Innovations

### 5.1 Smart-Scan Engine

**Priority:** P0 (Critical)
**Applies To:** Both Option A and Option B

#### 5.1.1 Feature Overview

The Smart-Scan Engine is the intelligence layer that detects issues before they cause build failures. It analyzes the MCP server directory and automatically fixes common problems.

#### 5.1.2 Detection Modules

**Module 1: Runtime Detection**
```yaml
Inputs:
  - Directory structure
  - File extensions (.py, .js, .ts)
  - Config files (pyproject.toml, package.json, Cargo.toml)

Outputs:
  - Runtime: Python | Node | Rust | Go | Unknown
  - Version: "3.10", "18", "1.75", etc.
  - Package Manager: pip | npm | cargo | go

Edge Cases:
  - Multiple runtimes (e.g., Python + Node for build tools)
  - No clear indicators (legacy projects)
  - Monorepo with mixed runtimes
```

**Module 2: Dependency Analysis**
```yaml
For Node.js:
  Check:
    - package.json exists
    - package-lock.json exists (most critical!)
    - Node version specified in engines field

  Auto-Fix:
    - Generate package-lock.json if missing
    - Use Node version from engines or default to 18
    - Warn if dependencies have security vulnerabilities

For Python:
  Check:
    - pyproject.toml or requirements.txt exists
    - Python version specified
    - UV-compatible structure

  Auto-Fix:
    - Generate requirements.txt from pyproject.toml
    - Default to Python 3.10 if unspecified
    - Use UV for faster installs

For Rust:
  Check:
    - Cargo.toml exists
    - Cargo.lock exists

  Auto-Fix:
    - cargo build to generate Cargo.lock
```

**Module 3: Credential Pattern Detection**
```yaml
Scan for:
  - .env files (check .env.example for template)
  - Environment variable references in code (os.getenv, process.env)
  - OAuth patterns (CLIENT_ID, CLIENT_SECRET)
  - API key patterns (*_API_KEY, *_TOKEN)

Output:
  credentials:
    - name: OPENAI_API_KEY
      required: true
      type: api_key
      secure: true
    - name: ACTIVELOOP_TOKEN
      required: false
      type: oauth_token
      secure: true

Auto-Generate:
  - .env.example with placeholder values
  - README section explaining required credentials
```

**Module 4: Path Validation**
```yaml
Check:
  - Absolute vs relative paths
  - Spaces in paths (requires quoting)
  - Symlinks (resolve to real paths)
  - Permissions (read/write/execute)
  - Volume mounts (check source path exists)

Auto-Fix:
  - Escape spaces in docker-compose.yml
  - Resolve symlinks to real paths
  - Warn about permission issues
  - Validate volume mount sources exist
```

#### 5.1.3 Auto-Fix Strategies

**Strategy 1: Generate Missing Files**
```python
# Example: Generate package-lock.json
def auto_fix_missing_package_lock(server_path):
    """
    Run npm install --package-lock-only in container
    to avoid polluting host environment
    """
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{server_path}:/app",
        "-w", "/app",
        "node:18",
        "npm", "install", "--package-lock-only"
    ]
    subprocess.run(docker_cmd, check=True)
```

**Strategy 2: Template Adjustments**
```python
# Example: Adjust Dockerfile for detected Node version
def adjust_dockerfile_node_version(version):
    """
    Replace Node version in Dockerfile template
    """
    template = """
    FROM node:{{ node_version }}
    WORKDIR /app
    COPY package*.json ./
    RUN npm ci --only=production
    """
    return template.replace("{{ node_version }}", version)
```

**Strategy 3: Configuration Patching**
```python
# Example: Fix docker-compose.yml path spaces
def fix_docker_compose_paths(compose_dict):
    """
    Escape spaces in volume mount paths
    """
    for service in compose_dict.get("services", {}).values():
        if "volumes" in service:
            service["volumes"] = [
                escape_path_spaces(vol) for vol in service["volumes"]
            ]
    return compose_dict
```

#### 5.1.4 Success Criteria

- ✅ Detect 100% of missing package-lock.json cases
- ✅ Detect 95%+ of credential patterns
- ✅ Auto-fix 80%+ of path issues
- ✅ Generate correct Dockerfile 90%+ of time
- ✅ Reduce manual fixes from 60% to <10%

---

### 5.2 MCP Registry

**Priority:** P0 (Critical)
**Applies To:** Option A (SQLite), Option B (JSON file)

#### 5.2.1 Feature Overview

The MCP Registry is the central database tracking all wrapped MCP servers, their health status, and trigger words for lazy loading.

#### 5.2.2 Registry Schema (Option A - SQLite)

**Table: servers**
```sql
CREATE TABLE servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,        -- 'github-mcp', 'playwright-mcp'
    path TEXT NOT NULL,                -- '/path/to/mcp-server'
    runtime TEXT NOT NULL,             -- 'python', 'node', 'rust'
    deployment_pattern TEXT NOT NULL,  -- 'volume', 'self-contained'
    status TEXT NOT NULL DEFAULT 'stopped',  -- 'active', 'stopped', 'error'
    container_id TEXT,                 -- Docker container ID
    image_name TEXT,                   -- Docker image name
    config_path TEXT NOT NULL,         -- Path to docker-compose.yml
    created_at INTEGER NOT NULL,       -- Unix timestamp
    updated_at INTEGER NOT NULL,       -- Unix timestamp
    last_health_check INTEGER          -- Unix timestamp
);

CREATE INDEX idx_servers_status ON servers(status);
CREATE INDEX idx_servers_name ON servers(name);
```

**Table: triggers**
```sql
CREATE TABLE triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    trigger_word TEXT NOT NULL,        -- 'github', 'playwright', 'slack'
    priority INTEGER DEFAULT 1,        -- Higher = load first
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE INDEX idx_triggers_word ON triggers(trigger_word);
```

**Table: health_logs**
```sql
CREATE TABLE health_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    check_time INTEGER NOT NULL,       -- Unix timestamp
    status TEXT NOT NULL,               -- 'healthy', 'unhealthy', 'timeout'
    response_time_ms INTEGER,           -- Response time in milliseconds
    error_message TEXT,                 -- Error if unhealthy
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);

CREATE INDEX idx_health_logs_server ON health_logs(server_id);
CREATE INDEX idx_health_logs_time ON health_logs(check_time);
```

**Table: credentials** (encrypted)
```sql
CREATE TABLE credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id INTEGER NOT NULL,
    env_var_name TEXT NOT NULL,        -- 'OPENAI_API_KEY'
    encrypted_value BLOB,               -- AES-256-GCM encrypted
    credential_type TEXT NOT NULL,      -- 'api_key', 'oauth_token', 'password'
    is_required BOOLEAN DEFAULT true,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE
);
```

#### 5.2.3 Registry Operations

**Operation: Add Server**
```rust
pub fn add_server(
    db: &Connection,
    name: &str,
    path: &Path,
    runtime: Runtime,
    deployment: DeploymentPattern,
) -> Result<i64> {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)?
        .as_secs() as i64;

    db.execute(
        "INSERT INTO servers (name, path, runtime, deployment_pattern, created_at, updated_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        params![name, path.to_str(), runtime.to_string(), deployment.to_string(), now, now],
    )?;

    Ok(db.last_insert_rowid())
}
```

**Operation: Query by Trigger**
```rust
pub fn find_servers_by_trigger(db: &Connection, trigger: &str) -> Result<Vec<Server>> {
    let mut stmt = db.prepare(
        "SELECT s.* FROM servers s
         JOIN triggers t ON s.id = t.server_id
         WHERE t.trigger_word LIKE ?1
         ORDER BY t.priority DESC"
    )?;

    let servers = stmt.query_map([trigger], |row| {
        Ok(Server {
            id: row.get(0)?,
            name: row.get(1)?,
            // ... other fields
        })
    })?;

    servers.collect()
}
```

**Operation: Update Health Status**
```rust
pub fn update_health(
    db: &Connection,
    server_id: i64,
    status: HealthStatus,
    response_time: Option<u64>,
) -> Result<()> {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)?
        .as_secs() as i64;

    // Update server status
    db.execute(
        "UPDATE servers SET last_health_check = ?1 WHERE id = ?2",
        params![now, server_id],
    )?;

    // Log health check
    db.execute(
        "INSERT INTO health_logs (server_id, check_time, status, response_time_ms)
         VALUES (?1, ?2, ?3, ?4)",
        params![server_id, now, status.to_string(), response_time.map(|t| t as i64)],
    )?;

    Ok(())
}
```

#### 5.2.4 Registry Schema (Option B - JSON)

```json
{
  "version": "1.0",
  "servers": [
    {
      "name": "github-mcp",
      "path": "/path/to/github-mcp",
      "runtime": "node",
      "deployment_pattern": "self-contained",
      "status": "active",
      "container_id": "abc123",
      "config_path": "docker-configs/github-mcp/docker-compose.yml",
      "created_at": "2026-01-05T12:00:00Z",
      "updated_at": "2026-01-05T13:30:00Z",
      "triggers": ["github", "repository", "commit"],
      "health": {
        "last_check": "2026-01-05T13:30:00Z",
        "status": "healthy",
        "response_time_ms": 120
      }
    }
  ]
}
```

**Operations (Bash + jq):**
```bash
# Add server
jq ".servers += [{
    \"name\": \"$NAME\",
    \"path\": \"$PATH\",
    \"runtime\": \"$RUNTIME\",
    \"status\": \"stopped\",
    \"created_at\": \"$(date -Iseconds)\"
}]" registry.json > registry.tmp && mv registry.tmp registry.json

# Query by trigger
jq ".servers[] | select(.triggers | contains([\"$TRIGGER\"]))" registry.json

# Update health
jq "(.servers[] | select(.name == \"$NAME\") | .health) = {
    \"last_check\": \"$(date -Iseconds)\",
    \"status\": \"$STATUS\",
    \"response_time_ms\": $RESPONSE_TIME
}" registry.json > registry.tmp && mv registry.tmp registry.json
```

#### 5.2.5 Success Criteria

- ✅ Track 100% of wrapped servers
- ✅ Query by trigger in <100ms (SQLite) or <500ms (JSON)
- ✅ Health check history for last 7 days
- ✅ Survive registry corruption (auto-repair)
- ✅ Migration from JSON to SQLite without data loss

---

### 5.3 Health Check System

**Priority:** P1 (High)
**Applies To:** Both Option A and Option B

#### 5.3.1 Feature Overview

Automated health monitoring ensures wrapped MCP servers are actually working, not just containers that start but don't respond.

#### 5.3.2 Health Check Levels

**Level 1: Container Running**
```bash
# Check if container is running
docker inspect <container_id> --format '{{.State.Running}}'
# Expected: true
```

**Level 2: MCP Protocol Response**
```bash
# Test JSON-RPC initialize method
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
  docker exec -i <container_id> sh

# Expected response:
# {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"1.0",...}}
```

**Level 3: Tools Available**
```bash
# Test tools/list method
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | \
  docker exec -i <container_id> sh

# Expected: List of tools with names and descriptions
```

**Level 4: Response Time**
```bash
# Measure response time
start=$(date +%s%N)
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
  docker exec -i <container_id> sh > /dev/null
end=$(date +%s%N)
response_time=$(( (end - start) / 1000000 ))  # Convert to ms

# Healthy: < 5000ms
# Degraded: 5000-15000ms
# Unhealthy: > 15000ms or timeout
```

#### 5.3.3 Health States

```rust
pub enum HealthStatus {
    Healthy,        // All checks pass, response < 5s
    Degraded,       // Container running but slow (5-15s)
    Unhealthy,      // Checks fail or timeout
    Stopped,        // Container not running
    Unknown,        // Cannot determine state
}
```

#### 5.3.4 Automated Health Monitoring (Option A)

**Background Health Check Daemon:**
```rust
pub async fn health_monitor_daemon(registry: Arc<Mutex<Registry>>) {
    let mut interval = tokio::time::interval(Duration::from_secs(60));

    loop {
        interval.tick().await;

        let registry = registry.lock().await;
        let servers = registry.get_active_servers()?;

        for server in servers {
            let health = check_server_health(&server).await;
            registry.update_health(server.id, health)?;

            // Auto-recovery if unhealthy
            if health == HealthStatus::Unhealthy {
                log::warn!("Server {} is unhealthy, attempting recovery", server.name);
                attempt_recovery(&server).await?;
            }
        }
    }
}
```

**Recovery Strategies:**
```rust
async fn attempt_recovery(server: &Server) -> Result<()> {
    // Strategy 1: Restart container
    log::info!("Attempting container restart...");
    restart_container(&server.container_id).await?;

    tokio::time::sleep(Duration::from_secs(5)).await;

    // Recheck health
    let health = check_server_health(server).await;
    if health == HealthStatus::Healthy {
        log::info!("Recovery successful via restart");
        return Ok(());
    }

    // Strategy 2: Rebuild container
    log::info!("Restart failed, attempting rebuild...");
    rebuild_container(server).await?;

    tokio::time::sleep(Duration::from_secs(10)).await;

    // Recheck health
    let health = check_server_health(server).await;
    if health == HealthStatus::Healthy {
        log::info!("Recovery successful via rebuild");
        return Ok(());
    }

    // Strategy 3: Mark as unhealthy, notify user
    log::error!("Recovery failed for server {}", server.name);
    Ok(())
}
```

#### 5.3.5 Manual Health Check (Option B)

```bash
# health-check.sh
SERVER_NAME="$1"
COMPOSE_FILE="docker-configs/$SERVER_NAME/docker-compose.yml"

# Level 1: Container running
CONTAINER_ID=$(docker compose -f "$COMPOSE_FILE" ps -q)
if [ -z "$CONTAINER_ID" ]; then
    echo "Status: 🔴 Stopped"
    exit 1
fi

# Level 2: MCP protocol response
start=$(date +%s%N)
RESPONSE=$(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
    timeout 15s docker exec -i "$CONTAINER_ID" sh 2>&1)
end=$(date +%s%N)

if [ $? -eq 0 ] && echo "$RESPONSE" | grep -q "jsonrpc"; then
    response_time=$(( (end - start) / 1000000 ))

    if [ $response_time -lt 5000 ]; then
        echo "Status: 🟢 Healthy (${response_time}ms)"
    else
        echo "Status: 🟡 Degraded (${response_time}ms)"
    fi
else
    echo "Status: 🔴 Unhealthy"
    echo "Error: $RESPONSE"
fi
```

#### 5.3.6 Success Criteria

- ✅ Detect unhealthy servers within 60 seconds (Option A)
- ✅ Auto-recovery success rate > 70%
- ✅ Health check overhead < 100ms per server
- ✅ False positive rate < 5%
- ✅ Historical health data for last 7 days

---

### 5.4 Batch Processing

**Priority:** P1 (High)
**Applies To:** Option A (full support), Option B (limited)

#### 5.4.1 Feature Overview

Wrap multiple MCP servers in parallel to save time for power users managing 10+ servers.

#### 5.4.2 Implementation (Option A)

```rust
pub async fn wrap_all(scan_dir: &Path) -> Result<Vec<WrapResult>> {
    // Phase 1: Discover all MCP servers
    let servers = discover_mcp_servers(scan_dir)?;
    log::info!("Found {} MCP servers", servers.len());

    // Phase 2: Wrap in parallel (max 4 concurrent)
    let semaphore = Arc::new(Semaphore::new(4));
    let mut tasks = vec![];

    for server_path in servers {
        let sem = semaphore.clone();
        let task = tokio::spawn(async move {
            let _permit = sem.acquire().await.unwrap();
            wrap_server(&server_path).await
        });
        tasks.push(task);
    }

    // Phase 3: Collect results
    let results = futures::future::join_all(tasks).await;

    // Phase 4: Summary report
    let successes = results.iter().filter(|r| r.is_ok()).count();
    let failures = results.len() - successes;

    log::info!("Wrap complete: {} succeeded, {} failed", successes, failures);

    Ok(results)
}
```

#### 5.4.3 Progress Reporting

```rust
pub struct WrapProgress {
    total: usize,
    completed: usize,
    current_server: String,
    status: WrapStatus,
}

pub async fn wrap_all_with_progress(
    scan_dir: &Path,
    progress_callback: impl Fn(WrapProgress),
) -> Result<Vec<WrapResult>> {
    let servers = discover_mcp_servers(scan_dir)?;
    let total = servers.len();

    for (idx, server) in servers.iter().enumerate() {
        progress_callback(WrapProgress {
            total,
            completed: idx,
            current_server: server.name.clone(),
            status: WrapStatus::InProgress,
        });

        let result = wrap_server(server).await?;

        progress_callback(WrapProgress {
            total,
            completed: idx + 1,
            current_server: server.name.clone(),
            status: WrapStatus::Completed(result),
        });
    }

    Ok(())
}
```

**CLI Output:**
```
Wrapping 10 servers...
[1/10] ✓ github-mcp (2.3s)
[2/10] ✓ slack-mcp (3.1s)
[3/10] ✗ postgres-mcp (failed: missing credentials)
[4/10] ✓ playwright-mcp (4.2s)
...
[10/10] ✓ deeplake-rag (8.7s)

Summary:
  ✓ 8 succeeded
  ✗ 2 failed
  ⏱️ Total time: 45.3s (parallel)
```

#### 5.4.4 Success Criteria

- ✅ Wrap 10 servers in < 60 seconds (parallel)
- ✅ Progress reporting shows current server
- ✅ Failures don't block other servers
- ✅ Summary report shows success/failure breakdown

---

## 6. Implementation Roadmap

### 6.1 Option A: "libra" CLI Roadmap

#### Phase 1: Foundation (Weeks 1-2)

**Goals:**
- Core CLI structure
- Smart-Scan Engine (detection only)
- Basic wrapping (single server)

**Deliverables:**
- ✅ `libra wrap <path>` command works
- ✅ Detects Python/Node runtime correctly
- ✅ Generates Dockerfile and docker-compose.yml
- ✅ Auto-generates package-lock.json for Node
- ✅ Basic error handling

**Success Metrics:**
- 80% build success rate (vs 30% current)
- Detection accuracy > 95%
- Time-to-wrap < 30 seconds

**Team:**
- 1 Rust developer (CLI + Smart-Scan)
- 1 QA engineer (testing with real MCP servers)

#### Phase 2: Intelligence (Weeks 3-4)

**Goals:**
- Advanced Smart-Scan (auto-fixes)
- MCP Registry (SQLite)
- Health checks

**Deliverables:**
- ✅ Auto-fix for missing package-lock.json
- ✅ Auto-fix for path spaces
- ✅ Credential pattern detection
- ✅ SQLite registry with servers/triggers tables
- ✅ `libra list`, `libra status` commands
- ✅ Basic health check (container + MCP protocol)

**Success Metrics:**
- 95% build success rate
- Auto-fix success rate > 80%
- Health check false positive rate < 5%

**Team:**
- 1 Rust developer (registry + health checks)
- 1 Rust developer (auto-fix engine)
- 1 QA engineer (integration testing)

#### Phase 3: Scale (Weeks 5-6)

**Goals:**
- Batch processing
- Automated health monitoring
- Recovery mechanisms

**Deliverables:**
- ✅ `libra wrap-all --scan <dir>` command
- ✅ Parallel wrapping (4 concurrent)
- ✅ Progress reporting with TUI
- ✅ Background health monitor daemon
- ✅ Auto-recovery strategies (restart, rebuild)
- ✅ `libra dashboard` interactive TUI

**Success Metrics:**
- Wrap 10 servers in < 60 seconds
- Auto-recovery success rate > 70%
- Dashboard responsive (< 100ms updates)

**Team:**
- 1 Rust developer (batch processing)
- 1 Rust developer (health monitor daemon)
- 1 UI/UX developer (TUI dashboard)
- 1 QA engineer (scale testing)

#### Phase 4: Polish (Weeks 7-8)

**Goals:**
- Documentation
- Error messages
- Edge cases
- Beta release

**Deliverables:**
- ✅ Comprehensive user documentation
- ✅ Error messages with actionable fixes
- ✅ Handle edge cases (monorepos, mixed runtimes)
- ✅ Migration tool from Option B → Option A
- ✅ Beta release to early adopters

**Success Metrics:**
- User satisfaction > 4.5/5
- Time-to-first-tool < 60 seconds
- Build success rate > 95%
- Support requests < 10% of users

**Team:**
- 1 Technical writer (documentation)
- 2 Rust developers (polish + bug fixes)
- 1 DevRel engineer (beta program)

---

### 6.2 Option B: Shell Wrappers Roadmap

#### Phase 1: Core Wrapper (Week 1)

**Goals:**
- Shell script wraps existing mcp-dockerize
- Auto-generates package-lock.json
- Updates Claude Code config

**Deliverables:**
- ✅ `wrap-mcp.sh <path>` script
- ✅ Auto-detects Node.js servers
- ✅ Generates package-lock.json if missing
- ✅ Validates docker-compose.yml syntax
- ✅ Updates `claude_desktop_config.json`

**Success Metrics:**
- 70% build success rate (vs 30% current)
- Time-to-wrap < 5 minutes
- User can wrap a server without Docker knowledge

**Team:**
- 1 DevOps engineer (shell scripting)
- 1 QA engineer (testing)

#### Phase 2: Helper Scripts (Week 2)

**Goals:**
- Additional management scripts
- Health checks
- Documentation

**Deliverables:**
- ✅ `list-wrapped.sh` (show all wrapped servers)
- ✅ `health-check.sh <server>` (manual health check)
- ✅ `unwrap-mcp.sh <server>` (remove from registry)
- ✅ JSON registry file (`registry.json`)
- ✅ README with examples

**Success Metrics:**
- Users can manage 3+ servers easily
- Health check false positive rate < 10%
- Documentation covers 90% of use cases

**Team:**
- 1 DevOps engineer (scripting)
- 1 Technical writer (documentation)

#### Phase 3: Beta Release (Week 2)

**Goals:**
- Ship to early adopters
- Gather feedback
- Iterate based on usage

**Deliverables:**
- ✅ GitHub release with shell scripts
- ✅ Installation guide
- ✅ Video tutorial (5 min)
- ✅ Feedback form

**Success Metrics:**
- 50+ beta users
- 80%+ report success on first attempt
- Feedback informs Option A priorities

**Team:**
- 1 DevRel engineer (beta program)
- 1 Video producer (tutorial)

---

### 6.3 Parallel Track Timeline

```
Week 1:
  Option B: Core wrapper script
  Option A: CLI structure, basic Smart-Scan

Week 2:
  Option B: Helper scripts, beta release 🚀
  Option A: Advanced Smart-Scan, registry

Week 3:
  Option B: Beta feedback → Option A priorities
  Option A: Health checks, auto-fixes

Week 4:
  Option B: Iteration based on feedback
  Option A: Batch processing

Week 5:
  Option A: Health monitoring daemon

Week 6:
  Option A: TUI dashboard, polish

Week 7:
  Option A: Documentation, edge cases

Week 8:
  Option A: Beta release 🚀
  Option B: Migration guide to Option A
```

---

## 7. Success Metrics & KPIs

### 7.1 Primary Metrics

#### Metric 1: Time-to-First-Tool

**Definition:** Time from `libra wrap` command to server responding to MCP requests

**Current Baseline:**
- Manual process: 30-60 minutes
- Current mcp-dockerize: 15-30 minutes (with manual fixes)

**Targets:**
- Option B: < 5 minutes (83% reduction)
- Option A: < 60 seconds (97% reduction)

**Measurement:**
```bash
start=$(date +%s)
libra wrap /path/to/server
end=$(date +%s)
echo "Time-to-first-tool: $((end - start)) seconds"
```

**Success Criteria:**
- 90% of wraps complete under target time
- P95 latency < 2x target
- No timeouts or hangs

---

#### Metric 2: Build Success Rate (First Attempt)

**Definition:** Percentage of wraps that build and start successfully on first attempt (no manual intervention)

**Current Baseline:**
- Manual: 30-40% success rate
- Current mcp-dockerize: 30% (fails on package-lock.json)

**Targets:**
- Option B: 70% (2.3x improvement)
- Option A: 95% (3.2x improvement)

**Measurement:**
```rust
pub struct WrapResult {
    success: bool,
    manual_intervention_required: bool,
    error: Option<String>,
}

fn calculate_success_rate(results: Vec<WrapResult>) -> f64 {
    let successes = results.iter()
        .filter(|r| r.success && !r.manual_intervention_required)
        .count();

    (successes as f64 / results.len() as f64) * 100.0
}
```

**Success Criteria:**
- Achieve target success rate across 100+ test cases
- Common MCP servers (github, slack, playwright) at 100%
- Edge cases (monorepos, mixed runtimes) at > 70%

---

#### Metric 3: User Retention (7-Day)

**Definition:** Percentage of users who wrap at least one more server within 7 days of first wrap

**Current Baseline:**
- Unknown (estimated 20-30% based on abandonment)

**Targets:**
- Option B: 50% retention
- Option A: 75% retention

**Measurement:**
```sql
-- Track user activity
SELECT
    user_id,
    COUNT(DISTINCT server_id) as servers_wrapped,
    MAX(created_at) - MIN(created_at) as days_active
FROM wrap_events
GROUP BY user_id
HAVING days_active <= 7
```

**Success Criteria:**
- 75% of users wrap 2+ servers
- 40% of users wrap 5+ servers
- Average servers per user > 3

---

### 7.2 Secondary Metrics

#### Metric 4: Token Savings Realized

**Definition:** Average token reduction for users who wrap servers vs not wrapping

**Current Baseline:**
- No wrapping: 75,000 tokens (all MCP servers loaded)
- With wrapping: Potential 1,500 tokens (99% savings)

**Targets:**
- Option B: 60,000 tokens saved (80% realized)
- Option A: 73,500 tokens saved (99% realized)

**Measurement:**
```python
def measure_token_savings(user):
    baseline = 75000  # All servers loaded

    if user.has_wrapped_servers:
        # Only proxy registry loaded
        actual = 1500 + (user.active_servers * 200)  # Lazy loading overhead
    else:
        actual = baseline

    savings = baseline - actual
    return savings, (savings / baseline) * 100
```

---

#### Metric 5: Auto-Recovery Success Rate

**Definition:** Percentage of unhealthy servers automatically recovered without manual intervention

**Targets:**
- Option A: 70% auto-recovery success

**Measurement:**
```rust
pub fn calculate_recovery_rate(health_logs: Vec<HealthLog>) -> f64 {
    let unhealthy_events = health_logs.iter()
        .filter(|log| log.status == HealthStatus::Unhealthy)
        .count();

    let auto_recovered = health_logs.iter()
        .filter(|log| log.status == HealthStatus::Unhealthy)
        .filter(|log| {
            // Check if next health check (within 5 min) was healthy
            let next_check = health_logs.iter()
                .find(|l| l.server_id == log.server_id && l.check_time > log.check_time);

            next_check.map_or(false, |l| l.status == HealthStatus::Healthy)
        })
        .count();

    (auto_recovered as f64 / unhealthy_events as f64) * 100.0
}
```

---

#### Metric 6: Support Request Rate

**Definition:** Percentage of users who contact support due to wrapping issues

**Current Baseline:**
- Estimated 40-50% of users need help

**Targets:**
- Option B: < 20% support requests
- Option A: < 5% support requests

**Measurement:**
```python
def support_rate(period_days=30):
    total_users = count_users_who_wrapped(period_days)
    support_tickets = count_support_tickets(period_days, tag="wrapping")

    return (support_tickets / total_users) * 100
```

---

### 7.3 Engagement Metrics

#### Metric 7: Dashboard Usage (Option A)

**Definition:** Percentage of Option A users who use the TUI dashboard at least once per week

**Targets:**
- 60% weekly active users use dashboard

**Measurement:**
```sql
SELECT
    COUNT(DISTINCT user_id) as weekly_active_users,
    COUNT(DISTINCT CASE WHEN event = 'dashboard_view' THEN user_id END) as dashboard_users
FROM events
WHERE created_at >= datetime('now', '-7 days')
```

---

#### Metric 8: Batch Wrapping Adoption

**Definition:** Percentage of users who wrap 3+ servers at once using `wrap-all`

**Targets:**
- 30% of power users (> 5 servers) use batch wrapping

**Measurement:**
```rust
pub fn batch_adoption_rate(wrap_events: Vec<WrapEvent>) -> f64 {
    let batch_wraps = wrap_events.iter()
        .filter(|e| e.is_batch && e.server_count >= 3)
        .count();

    let power_users = wrap_events.iter()
        .filter(|e| e.user_total_servers >= 5)
        .map(|e| e.user_id)
        .collect::<HashSet<_>>()
        .len();

    (batch_wraps as f64 / power_users as f64) * 100.0
}
```

---

### 7.4 Quality Metrics

#### Metric 9: Health Check Accuracy

**Definition:** False positive rate (healthy servers marked unhealthy) and false negative rate (unhealthy servers marked healthy)

**Targets:**
- False positive rate < 5%
- False negative rate < 2%

**Measurement:**
```python
def health_check_accuracy(ground_truth, predictions):
    false_positives = sum(1 for gt, pred in zip(ground_truth, predictions)
                         if gt == 'healthy' and pred == 'unhealthy')

    false_negatives = sum(1 for gt, pred in zip(ground_truth, predictions)
                         if gt == 'unhealthy' and pred == 'healthy')

    total_healthy = sum(1 for gt in ground_truth if gt == 'healthy')
    total_unhealthy = sum(1 for gt in ground_truth if gt == 'unhealthy')

    fpr = (false_positives / total_healthy) * 100
    fnr = (false_negatives / total_unhealthy) * 100

    return fpr, fnr
```

---

#### Metric 10: Error Message Quality

**Definition:** Percentage of error messages that lead to successful user resolution without support

**Targets:**
- 80% self-service resolution from error messages

**Measurement:**
```python
def error_resolution_rate():
    """
    Track users who:
    1. Encounter an error
    2. Do NOT contact support
    3. Successfully wrap server on next attempt (within 1 hour)
    """
    error_events = get_events(type='wrap_error')

    self_resolved = 0
    for error in error_events:
        next_attempt = get_next_wrap_event(error.user_id, after=error.timestamp)
        contacted_support = did_contact_support(error.user_id,
                                               start=error.timestamp,
                                               end=error.timestamp + timedelta(hours=1))

        if next_attempt and next_attempt.success and not contacted_support:
            self_resolved += 1

    return (self_resolved / len(error_events)) * 100
```

---

### 7.5 Business Impact Metrics

#### Metric 11: Enterprise Adoption

**Definition:** Number of enterprise teams (> 10 developers) using MCP Librarian

**Targets:**
- 10 enterprise teams by Month 6
- 50 enterprise teams by Month 12

**Measurement:**
```sql
SELECT
    team_id,
    COUNT(DISTINCT user_id) as team_size,
    COUNT(DISTINCT server_id) as servers_wrapped
FROM wrap_events
GROUP BY team_id
HAVING team_size >= 10
```

---

#### Metric 12: API Cost Savings (Per User)

**Definition:** Average monthly API cost reduction due to token savings

**Measurement:**
```python
def calculate_cost_savings(user):
    # Baseline: 75k tokens per session, 20 sessions/month
    baseline_tokens = 75000 * 20 = 1,500,000 tokens/month

    # With wrapping: 1.5k tokens per session
    optimized_tokens = 1500 * 20 = 30,000 tokens/month

    # Cost at $3/1M tokens (Claude 3.5 Sonnet)
    baseline_cost = (baseline_tokens / 1000000) * 3 = $4.50/month
    optimized_cost = (optimized_tokens / 1000000) * 3 = $0.09/month

    savings = $4.50 - $0.09 = $4.41/month

    return savings
```

**Annual Impact:**
- Per user: $52.92/year
- 1,000 users: $52,920/year
- 10,000 users: $529,200/year

---

### 7.6 KPI Dashboard

**Real-Time Tracking:**

```
┌─────────────────────────────────────────────────────────────┐
│           MCP Librarian - KPI Dashboard                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Time-to-First-Tool                                         │
│  ┌─────────────────────────────────────────────────┐        │
│  │  Current: 58s    Target: 60s    ✅ ON TRACK     │        │
│  │  ████████████████████████████████████░  97%     │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  Build Success Rate                                         │
│  ┌─────────────────────────────────────────────────┐        │
│  │  Current: 93%    Target: 95%    🟡 NEAR         │        │
│  │  █████████████████████████████████░░░  93%      │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  User Retention (7-Day)                                     │
│  ┌─────────────────────────────────────────────────┐        │
│  │  Current: 78%    Target: 75%    ✅ EXCEEDS      │        │
│  │  ████████████████████████████████████████ 104%  │        │
│  └─────────────────────────────────────────────────┘        │
│                                                              │
│  Weekly Active Servers: 1,247                               │
│  Total Wrapped Servers: 3,892                               │
│  Total Token Savings: 285M tokens/week                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Creative Innovations & Future Vision

### 8.1 Shadow Proxy Pattern

**Concept:** Instead of generating static docker-compose.yml files, use a dynamic proxy that intercepts MCP requests and routes to containers on-demand.

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                  Shadow Proxy (Rust)                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Claude Code                                                 │
│      │                                                       │
│      ▼                                                       │
│  ┌──────────────────────────────────────────────────┐       │
│  │  MCP Proxy Server (stdio)                        │       │
│  │  - Accepts JSON-RPC from Claude Code              │       │
│  │  - Parses method name to detect server needed     │       │
│  └──────────────────────────────────────────────────┘       │
│      │                                                       │
│      ▼                                                       │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Request Router                                   │       │
│  │  - Query registry by trigger words                │       │
│  │  - Find matching server                           │       │
│  └──────────────────────────────────────────────────┘       │
│      │                                                       │
│      ▼                                                       │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Container Lifecycle Manager                      │       │
│  │  - Check if container running                     │       │
│  │  - Start container if needed (lazy loading)       │       │
│  │  - Wait for healthy state                         │       │
│  └──────────────────────────────────────────────────┘       │
│      │                                                       │
│      ▼                                                       │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Forward Request to Container                     │       │
│  │  - Exec into container with JSON-RPC              │       │
│  │  - Capture response                               │       │
│  │  - Return to Claude Code                          │       │
│  └──────────────────────────────────────────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Benefits:**
- True zero-token startup (proxy is single server in config)
- Automatic lazy loading (no trigger configuration needed)
- Container lifecycle managed transparently
- Can implement smart caching (response memoization)

**Implementation Sketch:**
```rust
pub struct ShadowProxy {
    registry: Registry,
    container_manager: ContainerManager,
    cache: ResponseCache,
}

impl ShadowProxy {
    pub async fn handle_request(&self, request: JsonRpcRequest) -> JsonRpcResponse {
        // Step 1: Parse request to identify needed server
        let server = self.identify_server(&request)?;

        // Step 2: Ensure container is running
        self.container_manager.ensure_running(&server).await?;

        // Step 3: Check cache
        if let Some(cached) = self.cache.get(&request) {
            return cached;
        }

        // Step 4: Forward to container
        let response = self.forward_to_container(&server, &request).await?;

        // Step 5: Cache response
        self.cache.set(&request, &response);

        Ok(response)
    }
}
```

**Claude Code Configuration:**
```json
{
  "mcpServers": {
    "shadow-proxy": {
      "command": "libra",
      "args": ["proxy", "start"]
    }
  }
}
```

**Result:** User sees ONE MCP server in config, but has access to ALL wrapped servers.

---

### 8.2 Token Dashboard & Analytics

**Concept:** Real-time dashboard showing token usage, savings, and optimization opportunities.

**Features:**

**1. Token Usage Visualization**
```
┌─────────────────────────────────────────────────────────────┐
│              Token Usage - Last 7 Days                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Daily Token Consumption                                    │
│  100k ┤                                                      │
│   75k ┤  ██                                                  │
│   50k ┤  ██ Before wrapping                                  │
│   25k ┤  ██ ██ ██ ██                                         │
│    0k ┤  ██ ██ ██ ██ ░░ ░░ ░░ After wrapping                │
│       └──────────────────────────────────────────           │
│         M   T   W   T   F   S   S                           │
│                                                              │
│  Total Savings: 525,000 tokens ($1.58)                      │
│  Projected Monthly: 2.25M tokens ($6.75)                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**2. Server Usage Heatmap**
```
Server Utilization (Last 30 Days)

github-mcp     ████████████████████ 145 calls
slack-mcp      ████████░░░░░░░░░░░░  42 calls
playwright-mcp ██████████████████░░ 128 calls
postgres-mcp   ███░░░░░░░░░░░░░░░░░  18 calls
deeplake-rag   ███████████░░░░░░░░░  67 calls

💡 Tip: postgres-mcp rarely used, consider unwrapping to reduce overhead
```

**3. Optimization Recommendations**
```
Optimization Opportunities

🎯 High Impact:
  • Wrap 3 unwrapped servers → Save 45k tokens/session
  • Enable Shadow Proxy → Save 1.2k tokens/session

🔧 Medium Impact:
  • Remove postgres-mcp (unused) → Save 0.5k tokens/session
  • Update slack-mcp (new version available) → Save 0.2k tokens/session

📊 Low Impact:
  • Enable response caching → Save 0.1k tokens/session
```

**Implementation:**
```rust
pub struct TokenDashboard {
    registry: Registry,
    usage_tracker: UsageTracker,
}

impl TokenDashboard {
    pub async fn render(&self) -> Result<()> {
        let stats = self.usage_tracker.get_stats(Duration::days(7))?;

        // Calculate token breakdown
        let breakdown = self.calculate_token_breakdown(&stats);

        // Generate recommendations
        let recommendations = self.generate_recommendations(&stats);

        // Render TUI
        self.render_tui(breakdown, recommendations)?;

        Ok(())
    }

    fn calculate_token_breakdown(&self, stats: &UsageStats) -> TokenBreakdown {
        TokenBreakdown {
            baseline: 75000,  // All servers loaded
            current: stats.average_tokens_per_session,
            savings: 75000 - stats.average_tokens_per_session,
            savings_pct: ((75000 - stats.average_tokens_per_session) as f64 / 75000.0) * 100.0,
        }
    }
}
```

---

### 8.3 Portable MCP Containers

**Concept:** Pre-built, versioned MCP containers that can be pulled from a registry (like Docker Hub).

**Vision:**
```bash
# Instead of wrapping from source:
libra wrap /path/to/mcp-server

# Pull pre-built container:
libra pull github-mcp:latest
libra pull slack-mcp:v1.2.3
libra pull playwright-mcp:latest

# Registry of curated MCP containers
libra search "database"
  └─> postgres-mcp:v2.1
  └─> mysql-mcp:v1.0
  └─> mongodb-mcp:v3.2
```

**Registry Structure:**
```yaml
mcplibrarian/github-mcp:latest
  - Built from: github.com/modelcontextprotocol/servers/github
  - Runtime: Node 18
  - Size: 45MB (compressed)
  - Health: ✅ Validated
  - Security: ✅ No known vulnerabilities
  - Last Updated: 2026-01-03

  Tags:
    - latest
    - v1.2.3
    - v1.2
    - v1
```

**Benefits:**
- Zero build time (pre-built)
- Guaranteed working configurations
- Versioning for reproducibility
- Curated, security-scanned containers

**Implementation:**
```rust
pub async fn pull_container(name: &str, tag: &str) -> Result<()> {
    let registry_url = format!("ghcr.io/mcplibrarian/{name}:{tag}");

    // Pull from GitHub Container Registry
    docker::pull_image(&registry_url).await?;

    // Add to local registry
    self.registry.add_server(Server {
        name: name.to_string(),
        image: registry_url,
        deployment: DeploymentPattern::SelfContained,
        status: ServerStatus::Stopped,
    })?;

    Ok(())
}
```

---

### 8.4 Auto-Update System

**Concept:** Automatically detect when MCP servers have updates and prompt user to rebuild/update containers.

**Features:**

**1. Version Detection**
```rust
pub struct VersionChecker {
    registry: Registry,
}

impl VersionChecker {
    pub async fn check_updates(&self) -> Result<Vec<Update>> {
        let mut updates = vec![];

        for server in self.registry.get_all_servers()? {
            // Check if source repo has new commits
            let latest_commit = git::get_latest_commit(&server.source_path).await?;
            let current_commit = self.registry.get_commit_hash(server.id)?;

            if latest_commit != current_commit {
                updates.push(Update {
                    server_name: server.name,
                    current_version: current_commit,
                    latest_version: latest_commit,
                    changelog: git::get_changelog(&server.source_path, &current_commit, &latest_commit).await?,
                });
            }
        }

        Ok(updates)
    }
}
```

**2. User Notification**
```
Updates Available (3):

🆕 github-mcp: v1.2.3 → v1.3.0
   • Added support for GitHub Projects API
   • Fixed issue with rate limiting

🆕 slack-mcp: v2.1.0 → v2.2.0
   • New tool: slack_upload_file
   • Performance improvements

🆕 playwright-mcp: v0.9.0 → v1.0.0
   • Breaking: Renamed tool screenshot → take_screenshot
   • Added mobile device emulation

Run 'libra update --all' to update all servers
Run 'libra update github-mcp' to update specific server
```

**3. Automated Update Workflow**
```bash
libra update --all --auto-restart

[Update] github-mcp
  ✓ Pulled latest source
  ✓ Rebuilt container
  ✓ Restarted container
  ✓ Health check passed

[Update] slack-mcp
  ✓ Pulled latest source
  ✓ Rebuilt container
  ✓ Restarted container
  ✓ Health check passed

[Update] playwright-mcp
  ⚠️ Breaking changes detected
  → Review changelog: libra changelog playwright-mcp
  → Update manually: libra update playwright-mcp --confirm-breaking
```

---

### 8.5 MCP Server Marketplace

**Concept:** Curated marketplace of MCP servers with ratings, reviews, and one-click installation.

**Vision:**
```
┌─────────────────────────────────────────────────────────────┐
│              MCP Server Marketplace                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🔍 Search: [database                                    ]   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  PostgreSQL MCP                          ⭐⭐⭐⭐⭐  │   │
│  │  Full PostgreSQL database access via MCP              │   │
│  │  • 1,247 installs   • v2.1.0   • Node 18              │   │
│  │  [Install]  [View Docs]                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MongoDB MCP                             ⭐⭐⭐⭐☆  │   │
│  │  MongoDB operations with aggregation support          │   │
│  │  • 832 installs   • v3.2.1   • Python 3.10            │   │
│  │  [Install]  [View Docs]                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Categories: [All] [Database] [AI/ML] [DevOps] [Comms]      │
│  Sort by: [Popularity] [Rating] [Recent] [Name]             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**One-Click Install:**
```bash
# User clicks "Install" on postgres-mcp in marketplace
libra install marketplace:postgres-mcp

[Install] postgres-mcp from marketplace
  ✓ Pulled container: ghcr.io/mcplibrarian/postgres-mcp:v2.1.0
  ✓ Added to registry with triggers: [postgres, database, sql]
  ⚠️ Missing credentials: POSTGRES_HOST, POSTGRES_PASSWORD
  → Run 'libra configure postgres-mcp' to add credentials

[Success] postgres-mcp installed and ready to configure
```

---

### 8.6 AI-Powered Server Recommendations

**Concept:** Analyze user's codebase and recommend relevant MCP servers to install.

**Example:**
```bash
libra recommend --scan ~/projects/my-app

[Analysis] Scanning codebase for MCP opportunities...

📊 Detected Technologies:
  • Python (FastAPI)
  • PostgreSQL database
  • GitHub workflows
  • Slack notifications

🎯 Recommended MCP Servers:

  1. postgres-mcp (High Confidence)
     Why: Detected PostgreSQL connection in src/db.py
     Benefit: Query database, run migrations, inspect schema

  2. github-mcp (Medium Confidence)
     Why: Found .github/workflows/ directory
     Benefit: Manage issues, PRs, and workflows

  3. slack-mcp (Medium Confidence)
     Why: Found slack_webhook_url in config
     Benefit: Send notifications, query channels

[Action] Install all recommended:
  libra install postgres-mcp github-mcp slack-mcp
```

---

### 8.7 Team Collaboration Features

**Concept:** Share wrapped MCP configurations across teams.

**Team Registry:**
```bash
# Team lead wraps servers
libra wrap /path/to/github-mcp
libra wrap /path/to/slack-mcp
libra wrap /path/to/postgres-mcp

# Export team configuration
libra export --team-config > team-mcp-config.json

# Team members import
libra import team-mcp-config.json

[Import] Loading team configuration...
  ✓ github-mcp (pulling container)
  ✓ slack-mcp (pulling container)
  ✓ postgres-mcp (pulling container)
  ⚠️ Credentials needed: Add team .env file

[Success] Team configuration imported. 3 servers ready.
```

**Team Config Format:**
```json
{
  "team": "engineering",
  "version": "1.0",
  "servers": [
    {
      "name": "github-mcp",
      "image": "ghcr.io/myorg/github-mcp:v1.2.3",
      "triggers": ["github", "repository", "pr"],
      "env_vars": ["GITHUB_TOKEN"]
    }
  ],
  "shared_credentials": {
    "GITHUB_TOKEN": "use_team_vault"
  }
}
```

---

## 9. Risk Assessment & Mitigation

### 9.1 Technical Risks

#### Risk 1: Docker Compatibility Issues

**Risk Level:** HIGH
**Probability:** 60%
**Impact:** MEDIUM

**Description:**
- Docker socket location varies across platforms (Linux, macOS, Windows WSL)
- Docker Desktop vs Docker Engine differences
- Rootless Docker mode limitations
- Old Docker versions lack features (e.g., compose v2)

**Mitigation Strategy:**
```rust
// Robust Docker detection with fallbacks
pub fn detect_docker_environment() -> Result<DockerEnv> {
    // Strategy 1: Try Docker socket discovery
    if let Ok(socket) = discover_docker_socket() {
        return Ok(DockerEnv::Native(socket));
    }

    // Strategy 2: Try Docker Desktop API
    if is_docker_desktop_running() {
        return Ok(DockerEnv::Desktop);
    }

    // Strategy 3: Try remote Docker (DOCKER_HOST env)
    if let Ok(host) = env::var("DOCKER_HOST") {
        return Ok(DockerEnv::Remote(host));
    }

    // Strategy 4: Fail with actionable error
    Err(Error::DockerNotFound {
        message: "Docker not detected. Install Docker Desktop or Docker Engine.",
        install_url: "https://docs.docker.com/get-docker/",
    })
}
```

**Contingency Plan:**
- Maintain compatibility matrix (Docker versions vs features)
- Graceful degradation (disable features if Docker too old)
- Clear error messages with installation links

---

#### Risk 2: MCP Server Diversity

**Risk Level:** MEDIUM
**Probability:** 80%
**Impact:** MEDIUM

**Description:**
- MCP servers use different runtimes (Python, Node, Rust, Go)
- Different dependency managers (npm, pip, cargo, go mod)
- Custom build steps (some need compilation)
- Monorepos with mixed technologies

**Mitigation Strategy:**
```rust
// Extensible runtime detection system
pub trait RuntimeDetector {
    fn detect(&self, path: &Path) -> Option<Runtime>;
    fn generate_dockerfile(&self, context: &ScanContext) -> String;
}

// Easy to add new runtime support
pub fn register_runtime_detectors() -> Vec<Box<dyn RuntimeDetector>> {
    vec![
        Box::new(PythonDetector),
        Box::new(NodeDetector),
        Box::new(RustDetector),
        Box::new(GoDetector),
        // Add new detectors here
    ]
}
```

**Contingency Plan:**
- Start with Python + Node (covers 90% of MCP servers)
- Add Rust + Go in Phase 2
- Provide "manual mode" for unsupported runtimes (user provides Dockerfile)

---

#### Risk 3: Credential Security

**Risk Level:** HIGH
**Probability:** 40%
**Impact:** HIGH

**Description:**
- User credentials stored locally
- Potential for credential leakage (logs, backups)
- Multi-user systems (shared credentials risk)

**Mitigation Strategy:**
```rust
// Encrypt credentials at rest
pub struct CredentialVault {
    encryption_key: Key,
}

impl CredentialVault {
    pub fn store(&self, env_var: &str, value: &str) -> Result<()> {
        // Encrypt with AES-256-GCM
        let encrypted = aes_gcm::encrypt(&self.encryption_key, value.as_bytes())?;

        // Store in database
        self.db.execute(
            "INSERT INTO credentials (env_var_name, encrypted_value) VALUES (?1, ?2)",
            params![env_var, encrypted],
        )?;

        Ok(())
    }

    pub fn retrieve(&self, env_var: &str) -> Result<String> {
        let encrypted = self.db.query_row(
            "SELECT encrypted_value FROM credentials WHERE env_var_name = ?1",
            [env_var],
            |row| row.get(0),
        )?;

        let decrypted = aes_gcm::decrypt(&self.encryption_key, &encrypted)?;
        Ok(String::from_utf8(decrypted)?)
    }
}

// Never log credentials
pub fn sanitize_logs(log_line: &str) -> String {
    // Regex to detect API keys, tokens, passwords
    let patterns = [
        r"[A-Za-z0-9_-]{40,}",  // API keys
        r"sk-[A-Za-z0-9]{48}",  // OpenAI keys
        r"ghp_[A-Za-z0-9]{36}", // GitHub PATs
    ];

    let mut sanitized = log_line.to_string();
    for pattern in patterns {
        let re = Regex::new(pattern).unwrap();
        sanitized = re.replace_all(&sanitized, "***REDACTED***").to_string();
    }

    sanitized
}
```

**Contingency Plan:**
- Use OS-level credential managers (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- Clear documentation on credential security
- Optional: Integration with HashiCorp Vault, AWS Secrets Manager

---

### 9.2 Product Risks

#### Risk 4: User Adoption (Low Engagement)

**Risk Level:** MEDIUM
**Probability:** 30%
**Impact:** HIGH

**Description:**
- Users don't see value in wrapping servers
- Too complex compared to "just load everything"
- Not enough MCP servers to justify effort

**Mitigation Strategy:**

**Strategy 1: Clear Value Proposition**
```bash
# Show token savings before wrapping
libra estimate-savings

Current Setup:
  • 19 MCP servers loaded
  • ~75,000 tokens consumed at startup
  • ~25 Claude Code sessions before hitting limit
  • Estimated cost: $0.225 per session

With MCP Librarian:
  • Same 19 servers, wrapped and lazy-loaded
  • ~1,500 tokens consumed at startup (98% reduction)
  • ~250 Claude Code sessions before limit (10x increase)
  • Estimated cost: $0.004 per session (98% reduction)

Annual Savings: ~$132 per user

[Action] Wrap all servers now:
  libra wrap-all --scan ~/.mcp-servers/
```

**Strategy 2: Frictionless Onboarding**
```bash
# One-command setup
libra quickstart

[Quickstart] Setting up MCP Librarian...
  ✓ Detected 5 MCP servers in ~/.config/Claude/
  ✓ Wrapping github-mcp (2.3s)
  ✓ Wrapping slack-mcp (3.1s)
  ✓ Wrapping playwright-mcp (4.2s)
  ✓ Wrapping postgres-mcp (3.8s)
  ✓ Wrapping deeplake-rag (8.7s)
  ✓ Updated Claude Code config

[Success] All servers wrapped! Token savings: 73,500 (98%)
          Restart Claude Code to activate.
```

**Strategy 3: Viral Features**
- Team sharing (easy to distribute across team)
- Token dashboard (gamification of savings)
- Marketplace (discovery of new MCP servers)

---

#### Risk 5: Competing Solutions *(Updated v1.1)*

**Risk Level:** MEDIUM (revised from LOW)
**Probability:** 40% (revised upward — Claude Code native support already shipped)
**Impact:** MEDIUM

**Description:**
- ✅ **Claude Code native lazy loading SHIPPED** (January 2026 — `defer_loading` flag)
- Docker MCP Toolkit (official from Docker — macOS/Windows only, not Linux)
- Community tools like `mcp-on-demand` (manual config, no auto-generation)
- Other platforms may add native lazy loading over time

**Updated Assessment (v1.1):**
Claude Code's native `defer_loading` eliminated the token-saving use case **for Claude Code users only**. However:
- Claude Code represents ~30-40% of the AI coding assistant market
- **Cursor, VS Code Copilot, Windsurf, Continue.dev, Goose = ~60-70% of market** — none have native lazy loading
- Even for Claude Code users, containerization still provides security, portability, and isolation value

**Revised Risk Timeline:**
| Platform | Risk of Obsolescence | Timeline |
|----------|---------------------|----------|
| Claude Code | **Already obsolete for token savings** | Shipped Jan 2026 |
| Cursor | Low — no roadmap for `defer_loading` | Unknown |
| VS Code | Medium — feature requested, Microsoft slow | 6-12 months |
| Windsurf | Low — different architectural focus | 12+ months |
| opencode (SST) | Low — Issue #9350 filed, not on roadmap | 12+ months |
| Goose | Low — uses own "Summon" paradigm | N/A |

**Mitigation Strategy:**

**Strategy 1: Cross-Platform Differentiation**
- **vs Docker MCP Toolkit:** Linux support, auto-detection, security-first credential handling
- **vs `mcp-on-demand`:** Automated config generation — users don't write YAML manually
- **vs Native Lazy Loading (Claude only):** Works for every other platform too
- **vs Native Lazy Loading (future platforms):** Containerization benefits persist regardless

**Strategy 2: Expand Value Beyond Token Savings**
- Security isolation (sandboxed containers, no host access)
- Team portability (share configs across developers)
- Cross-machine reproducibility (works identically on any machine)
- Health monitoring (detect when servers silently fail)

**Strategy 3: Open Source & Community**
- Open source from day 1 (MIT license)
- Plugin architecture for community extensions
- Integrate with platform-specific config formats (Cursor mcp.json, etc.)

---

### 9.3 Operational Risks

#### Risk 6: Maintenance Burden

**Risk Level:** MEDIUM
**Probability:** 50%
**Impact:** MEDIUM

**Description:**
- Need to keep up with Docker API changes
- MCP protocol evolves
- Dependency updates (Rust crates, Node packages)
- User support requests

**Mitigation Strategy:**

**Strategy 1: Automated Testing**
```yaml
# CI/CD pipeline (GitHub Actions)
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        docker_version: [24.0, 25.0, 26.0]

    steps:
      - uses: actions/checkout@v3

      - name: Install Docker ${{ matrix.docker_version }}
        run: |
          # Install specific Docker version

      - name: Run integration tests
        run: |
          cargo test --features integration

      - name: Test with real MCP servers
        run: |
          # Test wrapping popular MCP servers
          libra wrap /test-servers/github-mcp
          libra wrap /test-servers/slack-mcp
          libra wrap /test-servers/playwright-mcp

          # Verify all containers healthy
          libra health --all
```

**Strategy 2: Community Support**
- Discord/Slack community for user support
- GitHub Discussions for Q&A
- Comprehensive documentation with search
- Video tutorials for common tasks

**Strategy 3: Telemetry (Opt-In)**
```rust
// Collect anonymous usage data to prioritize fixes
pub struct Telemetry {
    enabled: bool,
}

impl Telemetry {
    pub async fn report_error(&self, error: &Error) {
        if !self.enabled {
            return;
        }

        let event = TelemetryEvent {
            event_type: "error",
            error_kind: error.kind(),
            docker_version: get_docker_version(),
            os: std::env::consts::OS,
            libra_version: env!("CARGO_PKG_VERSION"),
            // No PII or credentials
        };

        self.send_event(event).await;
    }
}
```

---

## 10. Appendix

### 10.1 Glossary

| Term | Definition |
|------|------------|
| **MCP** | Model Context Protocol - standard for connecting AI agents to data sources |
| **MCP Server** | Service that exposes tools via MCP protocol (e.g., GitHub MCP, Slack MCP) |
| **Token** | Unit of text processed by LLM (roughly 4 characters in English) |
| **Lazy Loading** | Loading resources on-demand rather than upfront |
| **Smart-Scan Engine** | Component that detects issues and auto-fixes MCP server configurations |
| **MCP Registry** | Database tracking wrapped servers, triggers, and health status |
| **Health Check** | Automated test to verify MCP server is responding correctly |
| **Shadow Proxy** | Proxy server that routes MCP requests to containers transparently |
| **Deployment Pattern** | How MCP server is deployed (volume-mounted vs self-contained) |

### 10.2 References

**Core Technologies:**
- MCP Protocol: https://spec.modelcontextprotocol.io/
- Docker API: https://docs.docker.com/engine/api/
- Claude Code: https://docs.anthropic.com/claude-code
- SQLite: https://www.sqlite.org/

**Related Research:**
- Token Optimization Strategies: `/home/gyasis/Documents/code/AIdomaincertification/tokenusestrategies/`
- Docker MCP Lazy Loading: `Docker_MCP_Lazy_Loading.md`
- Comprehensive Solutions Synthesis: `Comprehensive_Solutions_Synthesis.md`

**Inspiration:**
- Docker MCP Toolkit: https://www.docker.com/blog/mcp-toolkit/
- Anthropic Code Execution: https://www.anthropic.com/engineering/code-execution-with-mcp
- Cloudflare Code Mode: https://blog.cloudflare.com/code-mode/

### 10.3 Success Stories (Future)

**Template for Case Studies:**

```markdown
## Case Study: [Company Name]

**Challenge:**
- Describe the problem they faced

**Solution:**
- How they used MCP Librarian

**Results:**
- Token savings: XX%
- Time saved: XX hours/month
- API cost reduction: $XX/month

**Quote:**
"[Testimonial from user]"
```

### 10.4 FAQ

**Q: Why do I need to wrap MCP servers in Docker?**
A: Wrapping enables lazy loading, which reduces token consumption from 75k to 1.5k (99% savings). This gives you 50x more context window for actual work.

**Q: Will this work with my existing MCP servers?**
A: Yes! MCP Librarian auto-detects Python and Node.js servers. Support for Rust and Go coming in Phase 2.

**Q: What if my MCP server uses special build steps?**
A: The Smart-Scan Engine handles most common cases. For edge cases, you can provide a custom Dockerfile.

**Q: Is my credential data secure?**
A: Yes. Credentials are encrypted with AES-256-GCM and stored locally. They are never sent to any external service.

**Q: Can I use this with Docker Desktop on macOS/Windows?**
A: Yes! MCP Librarian auto-detects Docker Desktop and uses the correct socket path.

**Q: What if I don't use Docker?**
A: Docker is required for containerization. We recommend Docker Desktop (free for personal use).

**Q: How do I migrate from Option B to Option A?**
A: Run `libra import-wrapped ./docker-configs/*` to migrate all wrapped servers to the libra registry.

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-01-05 | Product Team | Initial draft |
| 1.0 | 2026-01-05 | Product Team | Comprehensive PRD complete |

**Approval:**
- [ ] Product Manager
- [ ] Engineering Lead
- [ ] Design Lead
- [ ] DevRel Lead

**Next Steps:**
1. Review PRD with stakeholders (Week 1)
2. Finalize roadmap priorities (Week 1)
3. Begin Option B development (Week 1)
4. Begin Option A development (Week 2)
5. Launch Option B beta (Week 2)
6. Launch Option A beta (Week 8)

---

*End of Document*
