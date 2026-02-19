# Product Context: MCP Librarian

## Why This Project Exists

### The Core Problem

MCP (Model Context Protocol) servers provide powerful capabilities for AI assistants, but loading all servers upfront consumes massive token budgets (60k-75k tokens before the user even asks a question). Docker lazy loading can reduce this to 1.5k tokens (99% savings), but the setup process is so painful that 60-70% of users abandon it on first attempt.

### The Pain We're Solving

**Current Reality:** Wrapping MCP servers in Docker containers requires manual, error-prone steps:
1. Generate docker-compose.yml (syntax errors, wrong paths, missing env vars)
2. Handle missing package-lock.json files (90% of Node.js MCP servers gitignore this)
3. Debug cryptic Docker build errors without clear guidance
4. Manually update MCP registry (claude_desktop_config.json)
5. No validation that containers actually work after building

**Result:** 30-60 minutes per server, 30-40% build success rate on first attempt, high abandonment.

### Problems We Solve

1. **Missing package-lock.json:** Auto-detect and generate when missing
2. **Node version mismatches:** Detect required version and update Dockerfile accordingly
3. **Path handling issues:** Handle spaces in paths (e.g., "/media/gyasis/Drive 2/Storage")
4. **Credential insecurity:** Detect credentials and mount securely (no baked secrets)
5. **Manual registry updates:** Auto-update claude_desktop_config.json with correct syntax
6. **Silent failures:** Provide health checks to verify MCP protocol responses
7. **Unclear errors:** Replace cryptic Docker messages with actionable guidance
8. **No rollback:** Enable recovery from failed builds

## User Stories Summary

### Story 1: The Frustrated Developer (Sarah)
- **Before:** 1 hour fighting errors, gives up, loads all servers upfront
- **After:** 60 seconds from command to working tool
- **Key Win:** Auto-fixes package-lock.json and Node version issues

### Story 2: The Context-Aware Power User (Marcus)
- **Before:** 4 hours to manually wrap 10 servers, gives up after 2
- **After:** Batch process all 10 servers in parallel
- **Key Win:** Central dashboard, consistent credential handling

### Story 3: The Token Miser (Elena)
- **Before:** 2 hours debugging path issues, still has 75k token overhead
- **After:** Paths with spaces handled automatically, 99% token savings realized
- **Key Win:** Health checks confirm containers actually work

## Business Value

### Immediate Impact
- **Time Savings:** 29+ minutes per MCP server (30 min → <1 min)
- **Success Rate:** 3x improvement (30% → 95% first attempt success)
- **Token Efficiency:** 5x improvement in realized savings (20% → 99%)
- **User Retention:** 6x improvement (40% retention → >90%)

### Strategic Impact
- **Enterprise Adoption:** Enable teams to manage 100+ MCP servers at scale
- **Developer Productivity:** Spend time using AI, not configuring infrastructure
- **Cost Optimization:** API budgets go 10x further with proper token management
- **Ecosystem Growth:** Lower barrier to entry accelerates MCP server adoption

## Market Context

### Competitive Landscape
- **No direct competitors:** First tool to automate MCP containerization with auto-fixes
- **Alternative approaches:** Manual Docker setup, loading all servers upfront (token-inefficient)
- **Differentiation:** Smart-Scan engine that detects and fixes issues automatically

### User Acquisition
- **Target Audience:** Claude Code users seeking token optimization (estimated 10k+ potential users)
- **Distribution:** Open source, GitHub, community-driven
- **Growth Strategy:** Tutorial content, documentation, community showcase

## Product Positioning

**Tagline:** "Make MCP setup painless."

**Elevator Pitch:**
MCP Librarian transforms hours of Docker configuration into a single command. Auto-detect issues, auto-fix problems, auto-update registries. Go from MCP server to working tool in under 60 seconds with 99% token savings.

**Key Differentiators:**
1. **Smart-Scan Engine:** Auto-detects and fixes common issues
2. **Dual-Track Strategy:** Quick wins (shell wrappers) + long-term vision (libra CLI)
3. **Security First:** Never bake credentials, always use secure mounts
4. **Health Checks:** Verify containers actually respond to MCP protocol
5. **Non-Destructive:** Read-only analysis, preserves original code

## Success Criteria

### Phase 1 (Current - Foundation)
- :white_large_square: Basic CLI tool generates working Docker configs
- :white_large_square: Python FastMCP servers fully supported
- :white_large_square: Volume-mounted and self-contained deployment patterns working

### Phase 2 (Option B - Shell Wrappers)
- :white_large_square: Improved DX with auto-fixes in shell scripts
- :white_large_square: Beta user feedback gathered
- :white_large_square: Common pain points documented

### Phase 3 (Option A - Full Automation)
- :white_large_square: "libra" CLI with Smart-Scan engine
- :white_large_square: Auto-fix for all common issues
- :white_large_square: Health monitoring and diagnostics
- :white_large_square: MCP registry auto-update
- :white_large_square: 95%+ first-attempt build success

### Long-term Vision
- Multi-language support (Python, Node.js, Rust, Go)
- Cloud deployment patterns (AWS ECS, GCP Cloud Run)
- Enterprise dashboard for managing 100+ servers
- AI-powered issue detection and resolution
