# Memory Bank: MCP Librarian Project

## Overview

This memory bank contains comprehensive institutional memory for the MCP Librarian project. These files ensure continuity across sessions and enable any agent (or human) to quickly understand the project's current state, history, and direction.

## File Structure

### Core Documentation (Read in Order)

1. **projectbrief.md** (3.1KB)
   - Project identity, vision, goals
   - One-line summary and value proposition
   - Target users and success metrics
   - Current stage and key constraints

2. **productContext.md** (5.3KB)
   - Why this project exists (core problem)
   - User stories and pain points
   - Business value and market positioning
   - Success criteria for each phase

3. **activeContext.md** (7.3KB)
   - Current session focus and recent changes
   - What exists now (source code, dependencies)
   - What works vs what doesn't
   - Immediate next steps and priorities

4. **systemPatterns.md** (13KB)
   - Architecture overview and data flow
   - Core components and design patterns
   - Technical decisions and rationale
   - Future architecture plans

5. **techContext.md** (12KB)
   - Technology stack and dependencies
   - Project structure and configuration
   - Platform constraints and requirements
   - Known technical issues

6. **progress.md** (16KB)
   - Milestone tracking with completion status
   - Feature roadmap (Phase 1-4)
   - What's working, what's not
   - Blockers, risks, and success metrics

### Project Intelligence

7. **CLAUDE.md** (15KB)
   - Critical implementation paths
   - Discovered patterns and user preferences
   - Common pitfalls and how to avoid them
   - Decision log with rationale
   - Effective workflows

## Quick Start

### For New Sessions
1. Read projectbrief.md (understand vision)
2. Read activeContext.md (understand current state)
3. Read progress.md (understand what's done/pending)

### For Implementation Work
1. Read systemPatterns.md (understand architecture)
2. Read techContext.md (understand tech stack)
3. Read CLAUDE.md (understand critical patterns)

### For Updates
1. Read ALL files first (mandatory)
2. Update activeContext.md (current focus)
3. Update progress.md (task status)
4. Update CLAUDE.md (if new patterns discovered)

## Statistics

- **Total Files:** 7 (+ this README)
- **Total Lines:** 1,923 lines
- **Total Size:** ~72KB
- **Last Updated:** 2026-01-05
- **Project Phase:** Foundation (Phase 1 of 3)
- **Overall Completion:** ~15%

## Key Information

### Project Identity
- **Name:** MCP Librarian (mcplibrarian)
- **Version:** 0.1.0 (Early Development)
- **Vision:** "Make MCP setup painless"
- **Goal:** Reduce time-to-first-tool from 30+ min to <60 seconds

### Current State
- **Working:** Python FastMCP detection, Dockerfile generation, security checks
- **Blocked:** Missing Jinja2 templates (critical)
- **Missing:** Node.js support, build automation, health checks

### Immediate Priorities
1. Create Jinja2 templates (python-uv.Dockerfile.j2, python-direct.Dockerfile.j2)
2. Update README.md (remove "mcp-dockerize" branding)
3. Implement --build and --test flags

### Critical Patterns
- Always use `type: bind` mounts (handles spaces in paths)
- Preserve /media/, /mnt/ paths at original location (hardcoded path support)
- Never bake secrets into Docker images (use env_file and volume mounts)
- Only scan main server files (not dependencies) for security checks

## Access Control

**Exclusive Write Access:** memory-bank-keeper agent only
**Read Access:** All agents, all humans

**Why:** Ensures consistency and prevents conflicts. Only the specialized memory-bank-keeper agent can modify these files. Other agents read for context and report changes/discoveries to the keeper.

## Maintenance

This memory bank is updated:
- After significant implementation work
- When new patterns are discovered
- When architectural decisions are made
- When milestones are reached
- When user preferences are identified
- When blockers or issues are encountered

---

*Memory Bank System: Ensuring project continuity across session resets since 2026-01-05*
