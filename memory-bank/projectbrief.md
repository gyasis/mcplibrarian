# Project Brief: MCP Librarian

## Project Identity

**Name:** MCP Librarian (mcplibrarian)
**Version:** 0.1.0 (Early Development)
**Repository:** /home/gyasis/Documents/code/mcplibrarian
**Initial Commit:** 8af3991 (2026-01-05)
**Status:** Active Development - PRD Complete, Implementation Starting

## One-Line Summary

Automatically wrap MCP servers in Docker containers with smart auto-fixes, eliminating the painful manual configuration process and achieving 99% token savings through lazy loading.

## Project Vision

**"Make MCP setup painless."**

Transform the chaotic, error-prone process of containerizing MCP servers into a seamless, one-command experience that reduces time-to-first-tool from 30+ minutes to under 60 seconds with a 95%+ build success rate.

## Core Value Proposition

- **For Developers:** Spend time using AI, not configuring infrastructure
- **For Token Optimization:** Enable 99% token savings without fighting package-lock.json errors or Docker syntax
- **For Enterprise Teams:** Manage 100+ MCP servers without context saturation

## Project Goals

1. **Primary Goal:** Reduce time-to-first-tool from 30+ minutes to <60 seconds
2. **Build Success:** Achieve 95%+ build success rate on first attempt
3. **Token Savings:** Enable 99% token reduction through Docker lazy loading
4. **User Experience:** Eliminate manual docker-compose.yml editing and registry updates
5. **Automation:** Auto-detect and auto-fix common issues (missing package-lock.json, Node version mismatches, path problems)

## Target Users

1. **The Frustrated Developer (Sarah):** Watched tutorials, wants quick setup without Docker expertise
2. **The Context-Aware Power User (Marcus):** Managing 10+ MCP servers, needs batch processing
3. **The Token Miser (Elena):** Limited API budget, needs maximum context efficiency

## Current Stage

**Phase:** Foundation - PRD Complete
**Working Directory:** /home/gyasis/Documents/code/mcplibrarian
**Current Implementation:** Basic CLI tool with Python detector and Dockerfile generator (Phase 1 of dual-track strategy)

## Key Constraints

- Must handle package-lock.json generation automatically
- Must support paths with spaces (e.g., /media/gyasis/Drive 2/...)
- Must detect and secure credentials (no baked secrets)
- Must auto-update MCP registry without manual JSON editing
- Must provide health checks to verify containers actually work
- Linux-focused initially (Docker Desktop MCP Toolkit is macOS/Windows only)

## Success Metrics

- Time-to-first-tool: <60 seconds (vs current 30+ minutes)
- Build success rate: >95% first attempt (vs current 30-40%)
- Token savings realized: 99% (vs current 20%)
- User abandonment: <10% (vs current 60-70%)

## Strategic Approach

**Dual-Track Parallel Development:**
- **Track A (Option A):** Full "libra" CLI with Smart-Scan, auto-fixes, health monitoring (4-6 weeks)
- **Track B (Option B):** Improved shell wrappers for immediate value delivery (1-2 weeks)

**Rationale:** Option B delivers immediate relief and validates assumptions while Option A builds enterprise infrastructure. Learnings from B inform A's design.
