# CLAUDE.md - MCP Librarian Project Intelligence

## Project-Specific Insights

### Critical Implementation Paths

1. **Template-First Development Pattern**
   - ALWAYS create Jinja2 templates BEFORE implementing generators that use them
   - Test template rendering in isolation before integration
   - Templates are referenced but don't exist yet - this is a critical blocker

2. **Volume Mount Path Strategy**
   - Use `type: bind` syntax in docker-compose.yml (never short-hand `./path:/container/path`)
   - Preserve original host paths for /media/, /mnt/ volumes (handles hardcoded paths in MCP server code)
   - Always use absolute paths (relative paths break Docker volume mounts)
   - Mark all volumes as `read_only: true` (security best practice)

3. **Credential Security Pattern**
   - NEVER copy .env files into Docker images
   - NEVER use ENV statements in Dockerfile for secrets
   - ALWAYS use env_file in docker-compose.yml
   - ALWAYS mount credential files (.pem, .key) as volumes
   - Generate .env.example with masked values (e.g., `OPENAI_API_KEY=<YOUR_OPENAI_API_KEY_HERE>`)

4. **Detection Order for Entry Points**
   ```python
   # Python FastMCP servers - check in this order:
   1. project.scripts (console_scripts) → "python-uv" + script name
   2. main.py in root → "python-direct" + "main.py"
   3. src/**/server.py or src/**/__main__.py → "python-fastmcp" + relative path
   ```

5. **File Scanning Limits**
   - ONLY scan main server files: main.py, server.py, src/server.py
   - NEVER scan: node_modules, .venv, __pycache__, site-packages
   - System paths to ALWAYS exclude: /usr, /etc, /var, /sys, /proc, /dev, /tmp, /opt, /root, /lib, /bin, /sbin, /run, /boot, /home

### User Preferences

1. **Progress Tracking Symbols**
   - Use UTF-8 symbols consistently:
     - :white_check_mark: Completed/success
     - :white_large_square: Blank/not started
     - :hourglass_flowing_sand: Ongoing/in process
     - :x: Issue/error/failed
     - :warning: Attention/pending/warning
     - :arrows_counterclockwise: Rework required
     - :clock3: Waiting/delayed
     - :no_entry_sign: Deferred/canceled

2. **Memory Bank System**
   - Memory bank is sacred - ONLY memory-bank-keeper agent can modify
   - All memory bank files must be read BEFORE making updates
   - Document both technical details AND project context
   - Keep activeContext.md current with immediate focus
   - Build comprehensive project intelligence in CLAUDE.md

3. **Documentation Style**
   - Evidence-based approach (reference PRD, code, commit history)
   - Clear hierarchical structure (core files build on each other)
   - Capture decisions AND their rationale
   - Flag blockers and caveats prominently
   - Real-world validation examples (deeplake-rag case study)

### Discovered Patterns

#### Pattern 1: Space-in-Path Handling
**Problem:** Paths like "/media/gyasis/Drive 2/Deeplake_Storage/" break short-hand docker-compose syntax
**Solution:** Use type: bind with explicit source/target fields
```yaml
volumes:
  - type: bind
    source: /media/gyasis/Drive 2/Deeplake_Storage/memory_lane_v4
    target: /media/gyasis/Drive 2/Deeplake_Storage/memory_lane_v4
    read_only: true
```

#### Pattern 2: Hardcoded Path Preservation
**Problem:** MCP servers often have hardcoded paths in code (can't change without modifying source)
**Solution:** Mount volumes at SAME path as host (not translated to /data)
```python
if source.startswith("/media/") or source.startswith("/mnt/"):
    compose_content += f"        target: {source}\n"  # Same as host
else:
    compose_content += f"        target: {dest}\n"    # Translated path
```

#### Pattern 3: Python Version Extraction
**Problem:** requires-python uses various formats: ">=3.10", ">=3.10,<3.13", "^3.11"
**Solution:** Regex extraction of first version number
```python
match = re.search(r"(\d+\.\d+)", requires_python)
return match.group(1) if match else "3.11"  # Default fallback
```

#### Pattern 4: Security-First Volume Detection
**Problem:** Generic path scanning picks up system paths and package dependencies
**Solution:** Explicit inclusion/exclusion lists + file location filtering
```python
# Only scan main server files (not dependencies)
main_files = [path / "main.py", path / "server.py", path / "src" / "server.py"]

# Only include paths with user data indicators
if any(indicator in p for indicator in ["/media/", "/mnt/", "Drive", "Storage"]):
    volumes[p] = f"/data/{Path(p).name}"
```

### Common Pitfalls & How to Avoid

1. **Pitfall: Forgetting to Create Templates**
   - **Symptom:** FileNotFoundError when generator runs
   - **Prevention:** Always create templates before implementing template-using code
   - **Fix:** Create missing templates in src/mcp_dockerize/templates/

2. **Pitfall: Short-Hand Volume Syntax**
   - **Symptom:** docker-compose build fails with "invalid mount config"
   - **Prevention:** Always use type: bind syntax with explicit source/target
   - **Fix:** Update docker-compose.yml generation to use full syntax

3. **Pitfall: Relative Paths in docker-compose.yml**
   - **Symptom:** Volume mount fails, container can't find source code
   - **Prevention:** Always resolve to absolute paths before writing compose file
   - **Fix:** Use Path.resolve() or str(Path(path).absolute())

4. **Pitfall: Scanning node_modules or .venv**
   - **Symptom:** False positive credential detections, slow performance
   - **Prevention:** Limit scanning to main server files only
   - **Fix:** Use explicit file list, not recursive glob

5. **Pitfall: Baking Secrets into Docker Images**
   - **Symptom:** Credentials leaked in Docker layer history
   - **Prevention:** Never COPY .env, never use ENV for secrets
   - **Fix:** Use env_file in docker-compose.yml, mount credential files as volumes

### Project-Specific Quirks

1. **Dual Naming: "mcp-dockerize" vs "mcplibrarian"**
   - **Package name:** mcp-dockerize (in pyproject.toml)
   - **Project name:** mcplibrarian (in memory bank, PRD)
   - **Command:** mcp-dockerize (CLI entry point)
   - **Why:** Project evolved, renaming not yet complete
   - **TODO:** Update README.md and decide on final branding

2. **Template Directory Location**
   - **Expected:** src/mcp_dockerize/templates/
   - **Status:** Directory exists but template files missing
   - **Impact:** Generator code references templates but they don't exist
   - **Priority:** Critical blocker for usage

3. **Docker Compose Version**
   - **Command:** `docker compose` (v2, no hyphen)
   - **Not:** `docker-compose` (v1, deprecated)
   - **Why:** Docker Desktop standardized on v2 plugin syntax
   - **Impact:** Scripts and docs must use correct syntax

4. **Python Detection Only**
   - **Supported:** Python FastMCP servers (via pyproject.toml)
   - **Not Supported:** Node.js MCP SDK servers (yet)
   - **Impact:** Tool fails on 50% of MCP servers
   - **Roadmap:** Node.js support in Milestone 3 (Week 3-4)

### Effective Workflows

#### Workflow 1: Adding New Detector
```
1. Create detectors/{language}.py
2. Implement can_detect(path) -> bool
3. Implement detect(path) -> ServerMetadata
4. Add corresponding Dockerfile template
5. Update CLI to try new detector
6. Test with real MCP server of that type
7. Update documentation (techContext.md, progress.md)
```

#### Workflow 2: Adding Auto-Fix
```
1. Define Issue enum variant (e.g., Issue.MissingPackageLock)
2. Add detection logic in detector (append to metadata.issues)
3. Implement fix logic (e.g., run npm install --package-lock-only)
4. Add fix to auto_fix_issues() method
5. Add user confirmation prompt (if destructive)
6. Test fix with servers that exhibit the issue
7. Document fix in systemPatterns.md
```

#### Workflow 3: Testing Generated Configs
```
1. Generate configs: mcp-dockerize /path/to/server -v
2. Inspect output: cat docker-configs/{name}/docker-compose.yml
3. Check syntax: docker compose -f docker-configs/{name}/docker-compose.yml config
4. Build image: docker compose -f docker-configs/{name}/docker-compose.yml build
5. Test startup: docker compose -f docker-configs/{name}/docker-compose.yml run --rm {name}
6. Test MCP protocol: echo '{"jsonrpc":"2.0","method":"initialize","params":{}}' | docker compose run --rm {name}
7. Verify response: should return JSON-RPC initialize response
```

#### Workflow 4: Updating Memory Bank
```
1. Read ALL existing memory bank files (mandatory)
2. Analyze current project state (git status, code changes, new files)
3. Update activeContext.md (current focus, recent changes)
4. Update progress.md (task status, milestones)
5. Update systemPatterns.md (if architecture changes)
6. Update CLAUDE.md (if new patterns discovered)
7. Commit memory bank changes separately from code
```

### Decision Log

#### Decision 1: Volume-Mounted as Default Deployment Pattern
**Date:** 2026-01-05
**Context:** Need to choose between copying code into container vs mounting from host
**Decision:** Default to volume-mounted (not self-contained)
**Rationale:**
- Preserves existing project structure (no duplication)
- Easy updates (rebuild container without re-copying code)
- Handles large datasets (DeepLake example: 100+ GB)
- No code changes required (works with hardcoded paths)
**Trade-offs:** Less portable (requires host paths to exist)

#### Decision 2: Type: Bind Mount Syntax
**Date:** 2026-01-05
**Context:** Short-hand volume syntax fails with spaces in paths
**Decision:** Always use explicit type: bind with source/target fields
**Rationale:**
- Handles spaces in paths (e.g., "/media/gyasis/Drive 2/...")
- More explicit, easier to debug
- Better cross-platform compatibility
**Trade-offs:** More verbose docker-compose.yml

#### Decision 3: Preserve Host Paths for /media/, /mnt/
**Date:** 2026-01-05
**Context:** MCP servers have hardcoded paths in code (e.g., "/media/gyasis/Drive 2/Deeplake_Storage/")
**Decision:** Mount at same path as host (not translated to /data)
**Rationale:**
- Zero code changes required
- Works immediately with hardcoded paths
- User expects data to be in same location
**Trade-offs:** Less portable (container must run on same host or with same path structure)

#### Decision 4: Python-First Implementation
**Date:** 2026-01-05
**Context:** Need to prioritize Python vs Node.js vs Rust support
**Decision:** Implement Python FastMCP support first, Node.js second
**Rationale:**
- 80% of MCP servers use Python FastMCP (user research)
- Faster time-to-value (one language working vs none)
- Can validate architecture with one language before adding more
**Trade-offs:** Delays Node.js support (affects 50% of servers)

#### Decision 5: Template-Based Generation (Jinja2)
**Date:** 2026-01-05
**Context:** Choose between hardcoded Dockerfile strings vs templates
**Decision:** Use Jinja2 templates for Dockerfile, README generation
**Rationale:**
- Clean separation of logic and output format
- Easy for users to customize (edit template, not Python code)
- Industry standard (familiar to Docker/K8s users)
**Trade-offs:** Additional dependency, slightly more complex

#### Decision 6: Dual-Track Strategy (Option A + Option B)
**Date:** 2026-01-05
**Context:** Should we build full automation immediately or iterate?
**Decision:** Pursue both shell wrappers (Option B) and full CLI (Option A) in parallel
**Rationale:**
- Option B delivers value in 1-2 weeks (early feedback)
- Option A builds long-term infrastructure (4-6 weeks)
- Learnings from B inform A's design
- Different team skillsets (shell vs Rust/Go)
**Trade-offs:** More coordination overhead, potential duplication

### Future Enhancements to Watch

1. **Smart-Scan Engine (Week 5-6)**
   - Auto-detect issues before build failures
   - Auto-fix common problems (package-lock.json, Node version, path escaping)
   - Pre-build validation (will generated config actually work?)

2. **MCP Registry Auto-Update (Week 5-6)**
   - Eliminate manual claude_desktop_config.json editing
   - Safe JSON manipulation (preserve formatting, avoid corruption)
   - Backup before modification

3. **SQLite State Tracking (Week 7-8)**
   - Track which servers are wrapped
   - Store container IDs, image names, build timestamps
   - Enable "libra status" dashboard command

4. **Batch Processing (Week 7-8)**
   - `libra wrap-all --scan ~/mcp-servers/`
   - Parallel containerization of 10+ servers
   - Progress indicators, summary report

5. **libra CLI (Week 9-12)**
   - Rust or Go implementation (performance, static binary)
   - Replace Python CLI with faster, more portable version
   - Cross-platform single-binary distribution

### Known Limitations

1. **No Node.js Support Yet**
   - Impact: 50% of MCP servers unsupported
   - Workaround: None (must implement NodeDetector)
   - Timeline: Milestone 3 (Week 3-4)

2. **No Build Validation**
   - Impact: Generated configs may fail to build (30-40% failure rate)
   - Workaround: User must debug Docker errors manually
   - Timeline: Smart-Scan Phase 1 (Week 5-6)

3. **Manual Registry Updates**
   - Impact: User must copy-paste JSON into claude_desktop_config.json
   - Workaround: Provide clear instructions in generated README
   - Timeline: Registry auto-update (Week 5-6)

4. **No Health Checks**
   - Impact: Container may start but not respond to MCP protocol
   - Workaround: User must test manually with JSON-RPC initialize
   - Timeline: Container testing implementation (Week 2)

5. **No Rollback Mechanism**
   - Impact: If build fails, user must fix and retry manually
   - Workaround: Provide verbose error messages
   - Timeline: Smart-Scan error handling (Week 5-6)

### Success Indicators

**Tool is Working Well When:**
- :white_check_mark: Generated docker-compose.yml builds on first attempt (>95%)
- :white_check_mark: Containers start and respond to MCP initialize within 5 seconds
- :white_check_mark: No manual configuration editing required
- :white_check_mark: Credential handling is secure (no secrets in images)
- :white_check_mark: Time-to-first-tool <60 seconds
- :white_check_mark: User can wrap 10+ servers without frustration

**Tool Needs Improvement When:**
- :x: Build failures >5% (indicates detection or generation issues)
- :x: User must manually fix paths, versions, or dependencies
- :x: Security warnings appear (credentials detected in code)
- :x: Docker errors are cryptic (need better error messages)
- :x: User abandons setup process (indicates UX issues)

### Contact & Collaboration

**Memory Bank Keeper:** This agent (exclusive access to memory-bank folder)
**Other Agents:** Read-only access to memory bank, cannot modify

**Collaboration Pattern:**
1. Other agents read memory bank for project context
2. Other agents report changes, discoveries, issues
3. Memory Bank Keeper updates documentation
4. Memory Bank Keeper maintains consistency across all files

### Version History

**v1.0 (2026-01-05):** Initial CLAUDE.md created
- Documented critical implementation paths
- Captured user preferences and patterns
- Recorded architectural decisions
- Established workflows and pitfalls

**v1.1 (2026-02-19):** Repository organization update
- Project relocated to /home/gyasis/Documents/code/mcplibrarian (was under AIdomaincertification/)
- All stale path references updated across memory bank files
- Git state: 2 commits (8af3991, f92baae), remote https://github.com/gyasis/mcplibrarian.git
- 1 commit ahead of origin/main (f92baae not yet pushed to remote)

---

*This file is continuously updated as new patterns emerge and project intelligence grows.*
