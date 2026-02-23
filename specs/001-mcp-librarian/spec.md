# Feature Specification: MCP Librarian — Cross-Platform MCP Server Containerization

**Feature Branch**: `001-mcp-librarian`
**Created**: 2026-02-19
**Status**: Draft
**Input**: User description: PRD at `prd/MCP_LIBRARIAN_AUTOMATION_PRD.md`

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One-Command Server Wrapping (Priority: P1)

A developer with an existing MCP server on disk wants to containerize it so that it runs on-demand rather than consuming resources at all times. They run a single command pointing to the server directory. The tool automatically detects what the server needs (runtime, dependencies, credentials), resolves any known issues, builds a working container, and registers the server — all without requiring Docker expertise.

**Why this priority**: This is the core value proposition. Without reliable single-server wrapping, nothing else matters. Fixing the current 60-70% failure rate to 95%+ success makes the product viable.

**Independent Test**: Run the wrap command against a Node.js MCP server that is missing its `package-lock.json`. The tool should detect the missing file, generate it, build a working container, and confirm the server responds to health checks — all without user intervention. Delivers a fully containerized, registered, operational MCP server.

**Acceptance Scenarios**:

1. **Given** a user has an MCP server directory with a `package.json` but no `package-lock.json`, **When** they run the wrap command on that directory, **Then** the tool generates the missing lock file, builds a working container, registers the server, and reports success — all within 60 seconds with no manual steps required.

2. **Given** the server directory has paths containing spaces or special characters, **When** the wrap command runs, **Then** paths are handled correctly and the container starts successfully.

3. **Given** the server requires specific environment variables (API keys, tokens), **When** the wrap command runs, **Then** the tool identifies which variables are required, prompts the user only for missing ones, and stores them securely for container use.

4. **Given** the wrap command encounters an unrecoverable error, **When** the failure occurs, **Then** the tool displays a human-readable message explaining what went wrong and what the user should do next — never exposing raw container engine errors.

5. **Given** the same server is wrapped a second time, **When** the wrap command runs again, **Then** the tool detects the duplicate and asks the user whether to update, skip, or replace the existing registration.

---

### User Story 2 - Batch Wrapping for Power Users (Priority: P2)

A developer managing 10 or more MCP servers wants to containerize all of them at once. They point the tool at a directory containing multiple servers and let it run. The tool discovers, wraps, and registers all servers in parallel, showing progress and summarizing results when complete.

**Why this priority**: Power users represent early adopters and advocates. Batch processing reduces a multi-day manual effort to minutes, directly addressing the retention problem where users give up after wrapping 1-2 servers.

**Independent Test**: Point the batch command at a directory with 5 MCP servers of mixed runtimes (Node.js and Python). All 5 should be discovered, wrapped, and registered. A summary shows how many succeeded and failed, with failure reasons. Delivers a fully managed multi-server setup in a single operation.

**Acceptance Scenarios**:

1. **Given** a directory with 10 MCP servers, **When** the batch wrap command runs, **Then** all servers are processed in parallel, a live progress indicator shows each server's status, and a summary report is shown upon completion — with the entire batch completing within 60 seconds.

2. **Given** some servers in the batch fail to wrap, **When** batch processing completes, **Then** the tool clearly reports which servers succeeded and which failed (with reasons), and successful servers are registered and operational regardless of failures.

3. **Given** a server in the batch has a recoverable issue (e.g., missing lock file), **When** the batch runs, **Then** the tool auto-fixes the issue and continues without stopping the batch.

---

### User Story 3 - Cross-Platform Configuration (Priority: P2)

A developer using Cursor IDE, VS Code Copilot, Block's Goose, OpenAI Codex, or opencode wants to configure their containerized MCP servers to work with their specific platform. The tool generates and updates the correct configuration file for their platform automatically.

**Why this priority**: The cross-platform market is the primary differentiator from native Claude Code lazy loading. Without working platform configuration updates, users on Cursor, VS Code Copilot, Block's Goose, OpenAI Codex, and opencode cannot actually use the wrapped servers.

**Independent Test**: Wrap a server while specifying Cursor as the target platform. The tool should update Cursor's configuration file correctly. Restart Cursor and verify the server is accessible. Repeat for Block's Goose (YAML config) and opencode (JSON config) to verify the tool handles both config formats. Delivers a fully functional cross-platform integration with no manual config editing.

**Acceptance Scenarios**:

1. **Given** a user specifies Claude Code as their platform, **When** a server is wrapped, **Then** the tool updates the Claude Code configuration file to include the containerized server entry with correct connection parameters.

2. **Given** a user specifies Cursor IDE as their platform, **When** a server is wrapped, **Then** the tool updates Cursor's MCP configuration file and the server is accessible after restarting the IDE.

3. **Given** the target configuration file has JSON syntax errors before the update, **When** the tool tries to write to it, **Then** the tool reports the existing syntax error and does not overwrite the file, preserving the user's configuration.

4. **Given** a user wants to support multiple platforms simultaneously, **When** they configure the tool, **Then** they can register servers across more than one platform without re-wrapping.

---

### User Story 4 - Health Monitoring and Diagnostics (Priority: P3)

A developer with several wrapped MCP servers wants to verify they are running correctly and diagnose issues when something stops working. They can check the health status of individual servers or all servers at once, view recent health history, and get actionable guidance when a server is unhealthy.

**Why this priority**: Without health visibility, users cannot distinguish between "container stopped" and "server broken" — leading to silent failures and lost confidence in the tool.

**Independent Test**: Run a health check against both a healthy and a deliberately stopped server. The tool should report correct status for each, provide historical health data, and suggest next steps for the unhealthy one. Delivers confidence that the tool's status information is trustworthy.

**Acceptance Scenarios**:

1. **Given** a wrapped server is running and responding correctly, **When** a health check is run, **Then** the tool reports the server as healthy with response time, and the result is stored in health history.

2. **Given** a wrapped server's container has stopped, **When** a health check is run, **Then** the tool reports "stopped" (not "unhealthy"), distinguishing user-initiated stops from failures.

3. **Given** a wrapped server's container is running but not responding to MCP protocol requests, **When** a health check is run, **Then** the tool reports "unhealthy", attempts automatic recovery, and notifies the user of the outcome.

4. **Given** a user wants to see the health history of a server, **When** they request historical data, **Then** the tool shows the last 7 days of health checks with timestamps, status, and response times.

---

### User Story 5 - Registry Management (Priority: P3)

A developer wants to see all their wrapped servers in one place — their names, running status, the platform they're registered with, and when they were last active. They can also remove servers they no longer need.

**Why this priority**: Registry visibility is essential for users managing more than 2-3 servers. Without it, users lose track of what's wrapped and the tool feels unmanageable.

**Independent Test**: List all registered servers, remove one, and confirm it no longer appears. Delivers clear visibility and control over the server portfolio.

**Acceptance Scenarios**:

1. **Given** a user has 5 wrapped servers, **When** they list registered servers, **Then** the tool shows each server's name, runtime, status, target platform, and last health check result.

2. **Given** a user wants to remove a server from the registry, **When** they run the remove command, **Then** the registration is removed and the user is informed — but the original MCP server source files are not deleted.

3. **Given** the registry data is corrupted or missing, **When** the tool starts, **Then** it detects the issue, attempts auto-repair, and alerts the user if manual action is needed.

---

### Edge Cases

- What happens when two different MCP servers have the same name? The tool must detect the naming conflict and prompt the user to choose a unique name.
- What happens when the container engine (Docker) is not installed or not running? The tool detects this upfront before any processing and provides a clear installation/startup guide, not a cryptic socket error.
- What happens when a server is running on all platforms (e.g., CPU maxed, no memory) at wrap time? The tool should detect resource constraints and warn the user rather than silently timing out.
- What happens when a server requires a very large data volume (100GB+) that must be mounted? The tool validates that the volume source path exists and warns about storage requirements before proceeding.
- What happens when the target AI platform's configuration file is not in the expected location? The tool prompts the user to specify the path rather than failing silently.
- What happens when a wrapped server's source directory is deleted or moved? The tool detects the missing source at health check time and marks the server as "source not found" rather than "unhealthy."
- What happens when wrapping a monorepo containing multiple MCP servers in subdirectories? The tool should offer to detect and wrap each server individually or let the user select specific ones.

## Requirements *(mandatory)*

### Functional Requirements

**Core Wrapping**

- **FR-001**: The tool MUST accept an MCP server directory path as input and produce a working containerized server without requiring the user to write any container configuration manually.
- **FR-002**: The tool MUST detect the server's runtime environment (Python, Node.js, or Rust) by analyzing its project files, without requiring the user to specify it.
- **FR-003**: The tool MUST automatically generate any missing dependency lock files required for a successful container build, using only isolated environments — not the user's host system.
- **FR-004**: The tool MUST detect required environment variables by scanning the server's source code and configuration files, and prompt the user only for variables that are not already set.
- **FR-005**: The tool MUST validate and correct file paths with special characters (spaces, unicode, symlinks) so they work correctly inside the container environment.
- **FR-006**: The tool MUST display human-readable, actionable error messages when wrapping fails — never raw container engine output alone.
- **FR-007**: The tool MUST verify the container is running AND the MCP server is responding correctly via protocol-level health check before declaring a wrap successful.

**Smart-Scan Auto-Fix**

- **FR-008**: The tool MUST automatically fix the following common issues without user intervention: missing Node.js lock files, mismatched runtime versions in project configuration, paths with spaces in container volume mounts.
- **FR-009**: The tool MUST report each auto-fix applied so users understand what changed and why.
- **FR-010**: When an issue cannot be auto-fixed, the tool MUST provide specific instructions for the user to resolve it manually.

**Registry**

- **FR-011**: The tool MUST maintain a persistent registry of all wrapped servers, including their name, source path, target platform, runtime, and current status.
- **FR-012**: The tool MUST prevent duplicate registrations and alert the user when a server is already registered, offering update or skip options.
- **FR-013**: The tool MUST allow users to list all registered servers with their current status and health information.
- **FR-014**: The tool MUST allow users to remove a server from the registry without deleting the original source files.

**Platform Configuration**

- **FR-015**: The tool MUST support automatic configuration updates for these AI coding platforms: Claude Code, Cursor IDE, VS Code Copilot, Block's Goose, OpenAI Codex, and opencode.
- **FR-016**: The tool MUST validate configuration file syntax before and after writing — and never write a configuration that would break the target platform's startup.
- **FR-017**: The tool MUST support registering a single wrapped server across multiple AI platforms in one operation.

**Health Monitoring**

- **FR-018**: The tool MUST perform a multi-level health check that verifies: (1) container is running, (2) MCP protocol responds correctly, (3) available tools are listed, (4) response time is within acceptable limits.
- **FR-019**: The tool MUST store health check results with timestamps for at least 7 days for each server.
- **FR-020**: The tool MUST distinguish between a user-stopped server and an unhealthily crashed server.
- **FR-021**: When a server is detected as unhealthy, the tool MUST attempt automatic recovery and report whether recovery succeeded or failed.

**Batch Operations**

- **FR-022**: The tool MUST support batch wrapping of all MCP servers found in a specified directory, processing multiple servers concurrently.
- **FR-023**: During batch operations, the tool MUST display live progress for each server and produce a summary report of successes and failures upon completion.
- **FR-024**: A single server failure during batch processing MUST NOT prevent other servers from being wrapped.

**Quick-Start Track (Shell Wrappers)**

- **FR-025**: A lightweight shell-based wrapping path MUST be available as an alternative to the full CLI, requiring only standard tools (a POSIX shell, a JSON processor, and a container engine) — no compiled binaries required.
- **FR-026**: The shell-based path MUST cover the most critical auto-fixes: missing lock file generation and configuration file updates.
- **FR-027**: Any servers wrapped using the shell-based path MUST be importable into the full CLI registry without re-wrapping.

### Key Entities

- **MCP Server**: An AI tool server located at a directory path on disk, characterized by its runtime, dependencies, required credentials, and source files. Can be in states: unwrapped, wrapping, wrapped-active, wrapped-stopped, error.
- **Container Configuration**: The set of files (container spec, composition file, environment template) generated for a specific MCP server. Produced automatically; the user should never need to edit these directly.
- **Registry Entry**: A persistent record linking an MCP server to its containerized form, including name, source path, runtime, target platforms, container reference, and health history.
- **Health Check Result**: A timestamped snapshot of a server's operational status at a point in time — covering container state, protocol responsiveness, available tools, and response time.
- **Platform Configuration**: The configuration file for a specific AI coding platform (Claude Code, Cursor, VS Code Copilot, Block's Goose, OpenAI Codex, opencode) that specifies which MCP servers are available and how to connect to them.
- **Trigger**: A keyword or phrase associated with a wrapped server that causes the platform or tool to start the server on demand when the trigger appears in user input.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 90% of users who run the wrap command on a supported MCP server complete successfully on the first attempt with no manual intervention — up from the current 30-40% baseline.
- **SC-002**: Users complete the entire workflow from running the wrap command to having a working, registered, health-checked server in under 60 seconds for the full CLI path and under 5 minutes for the shell-based path.
- **SC-003**: The tool reduces context window pre-loading overhead by at least 80% on platforms that lack native lazy loading (Cursor, VS Code Copilot, Block's Goose, OpenAI Codex, opencode), as measured by the reduction in tools loaded at session start.
- **SC-004**: 75% of users who wrap their first server go on to wrap at least one more server within 7 days — indicating the experience is worth repeating.
- **SC-005**: 40% of users who wrap their first server manage 5 or more wrapped servers within 30 days — indicating the tool scales to real multi-server workflows.
- **SC-006**: Unhealthy servers are detected and recovery is attempted within 60 seconds of the failure occurring (full CLI path).
- **SC-007**: Automatic recovery succeeds in more than 70% of cases where a server becomes unhealthy due to transient issues.
- **SC-008**: Health check operations produce fewer than 5% false positives (reporting unhealthy for servers that are actually functioning correctly).
- **SC-009**: Batch wrapping of 10 servers completes in under 60 seconds on a standard developer machine.
- **SC-010**: Support ticket volume related to MCP server setup decreases by at least 50% within 30 days of general availability, compared to the baseline period.

## Assumptions

- Users have a working container engine (Docker or compatible) installed and running. The tool provides guidance but does not install the container engine itself.
- MCP servers follow standard project conventions for their runtime (e.g., `package.json` for Node.js, `pyproject.toml` or `requirements.txt` for Python).
- Target AI platform configuration files are accessible on the user's local file system at standard locations.
- Users have sufficient disk space for container images (typically 200MB–2GB per server depending on runtime).
- The tool does not need to handle MCP servers that require GUI access or audio/video hardware.
- Cross-platform CI/CD pipeline deployment of wrapped servers is out of scope for this specification; the tool targets local developer machines.
- The shell-based path (Option B) assumes a POSIX-compatible shell environment; Windows users without WSL are expected to use the full CLI (Option A) instead.
