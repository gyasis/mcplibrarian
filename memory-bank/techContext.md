# Technical Context: MCP Librarian

## Technology Stack

### Core Technologies

**Language:** Python 3.10+
- **Rationale:** Native ecosystem for MCP servers, rich tooling for CLI, Docker SDK
- **Version Constraint:** >=3.10 (for structural pattern matching, typing improvements)

**CLI Framework:** Click 8.1.0+
- **Purpose:** Command-line interface, argument parsing, colored output
- **Why Click:** Industry standard, excellent documentation, decorator-based API

**Template Engine:** Jinja2 3.1.0+
- **Purpose:** Generate Dockerfile, README from templates
- **Why Jinja2:** Familiar syntax, powerful, widely used in Docker/K8s ecosystems

**Configuration Parser:** toml 0.10.2+
- **Purpose:** Parse pyproject.toml for project metadata
- **Why TOML:** Native format for Python packaging (PEP 621)

**Docker Integration:** docker 7.0.0+
- **Purpose:** Python SDK for Docker API (future: build automation)
- **Why Official SDK:** Type-safe, well-maintained, feature-complete

**Environment Variables:** python-dotenv 1.0.0+
- **Purpose:** Parse .env files for credential detection
- **Why dotenv:** Standard for 12-factor app configuration

### Development Tools

**Package Manager:** uv (Astral)
- **Purpose:** Fast Python package manager, virtual environments
- **Why uv:** 10-100x faster than pip, native lock file support

**Build System:** Hatchling
- **Purpose:** Build Python packages (PEP 517 compliant)
- **Why Hatchling:** Modern, minimal, recommended by PyPA

**Entry Point:** Console Scripts
- **Command:** `mcp-dockerize` (defined in pyproject.toml)
- **Module:** `mcp_dockerize.cli:main`

## Project Structure

```
mcplibrarian/
├── src/
│   └── mcp_dockerize/
│       ├── __init__.py
│       ├── cli.py                  # Main CLI entry point
│       ├── detectors/
│       │   ├── __init__.py
│       │   └── python.py           # Python FastMCP detector
│       ├── generators/
│       │   ├── __init__.py
│       │   └── dockerfile.py       # Dockerfile/compose generator
│       └── templates/              # Jinja2 templates (to be created)
│           ├── python-uv.Dockerfile.j2
│           ├── python-direct.Dockerfile.j2
│           └── README.md.j2
├── docker-configs/                 # Generated output examples
│   └── deeplake-rag/
│       ├── Dockerfile
│       ├── docker-compose.yml
│       ├── .env.example
│       └── README.md
├── prd/                            # Product requirements
│   └── MCP_LIBRARIAN_AUTOMATION_PRD.md
├── memory-bank/                    # Institutional memory
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── activeContext.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   └── progress.md
├── pyproject.toml                  # Project metadata
├── uv.lock                         # Locked dependencies
├── README.md                       # User documentation
├── LICENSE                         # MIT License
└── .venv/                          # Virtual environment (local)
```

## Development Environment

### System Requirements

**Operating System:** Linux (primary)
- Current: Linux 5.15.0-164-generic
- Platform: linux
- Architecture: x86_64 (assumed)

**Docker:** Required for generated containers
- Version: Docker 20.10+ or Docker Desktop
- Note: Docker Desktop MCP Toolkit is macOS/Windows only (Linux needs custom CLI)

**Python:** 3.10 or later
- Installed via: system package manager or pyenv
- Virtual env: .venv/ (managed by uv)

### Local Setup

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
cd /home/gyasis/Documents/code/AIdomaincertification/mcplibrarian

# Install dependencies
uv sync

# Run CLI (development mode)
uv run mcp-dockerize /path/to/mcp-server

# Install globally (editable)
uv pip install -e .
```

### Configuration Files

**pyproject.toml:**
```toml
[project]
name = "mcp-dockerize"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "click>=8.1.0",
    "jinja2>=3.1.0",
    "toml>=0.10.2",
    "docker>=7.0.0",
    "python-dotenv>=1.0.0",
]

[project.scripts]
mcp-dockerize = "mcp_dockerize.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**uv.lock:** 57KB lockfile (generated automatically)

## Technical Constraints

### Platform Limitations

**Linux Focus:**
- Docker Desktop MCP Toolkit unavailable on Linux
- Must use custom Docker CLI solutions for MCP lazy loading
- Volume mounting behavior may differ from macOS/Windows

**Path Handling:**
- Must support spaces in paths (e.g., "/media/gyasis/Drive 2/...")
- Use `type: bind` syntax for docker-compose.yml (not short-hand)
- Absolute paths required (relative paths break volume mounts)

**Docker Requirements:**
- Docker daemon must be running
- User must have Docker permissions (docker group or sudo)
- docker-compose v2 (not docker-compose v1)

### Language-Specific Constraints

**Python Detection:**
- Requires pyproject.toml (PEP 621 standard)
- Cannot detect legacy setup.py-only projects (out of scope)
- Assumes FastMCP or similar modern MCP server framework

**Node.js Detection (Future):**
- Will require package.json
- Must handle package-lock.json generation (common issue)
- Node version detection from engines field or .nvmrc

### Security Constraints

**Credential Handling:**
- NEVER copy .env files into Docker images
- NEVER bake secrets into Dockerfile ENV statements
- ALWAYS use volume mounts for credential files (.pem, .key)
- ALWAYS generate .env.example with masked values

**File Permissions:**
- Check SSH key permissions (must be 600)
- Warn if loose permissions detected
- Read-only mounts for source code and data volumes

### Performance Constraints

**File Scanning:**
- Only scan main server files (main.py, server.py, src/server.py)
- Do NOT scan node_modules, .venv, __pycache__ (false positives)
- Limit regex scanning to avoid long processing times

**Volume Detection:**
- Exclude system paths (/usr, /etc, /var, /sys, /proc, /dev, /tmp, etc.)
- Only include user data paths (/media/, /mnt/, "Drive", "Storage")
- Avoid mounting entire filesystems (security risk)

## Build & Deployment

### Package Distribution

**Current:** Development-only (not published)
**Installation Method:** `uv pip install -e .` (editable mode)

**Future Distribution:**
- PyPI package: `pip install mcp-librarian`
- GitHub releases: Binary distributions (PyInstaller/Nuitka)
- Homebrew formula: `brew install mcp-librarian` (macOS)
- APT/YUM packages: `apt install mcp-librarian` (Linux)

### Docker Image Generation

**Output Format:** docker-compose.yml + Dockerfile
**Build Command:** `docker compose build` (user-executed)
**Runtime:** `docker compose run --rm {service}` (stdio mode for MCP)

**Generated Dockerfile (Python-Direct Example):**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
VOLUME ["/app", "/data"]
CMD ["python", "main.py"]
```

**Generated docker-compose.yml (Volume-Mounted Example):**
```yaml
version: '3.8'
services:
  deeplake-rag:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: mcp-deeplake-rag
    stdin_open: true
    tty: false
    volumes:
      - type: bind
        source: /path/to/server
        target: /app
        read_only: true
      - type: bind
        source: /media/gyasis/Drive 2/Deeplake_Storage
        target: /media/gyasis/Drive 2/Deeplake_Storage
        read_only: true
    env_file:
      - .env
```

## Dependencies & Licensing

### Direct Dependencies

| Package | Version | License | Purpose |
|---------|---------|---------|---------|
| click | >=8.1.0 | BSD-3-Clause | CLI framework |
| jinja2 | >=3.1.0 | BSD-3-Clause | Template rendering |
| toml | >=0.10.2 | MIT | TOML parsing |
| docker | >=7.0.0 | Apache-2.0 | Docker API |
| python-dotenv | >=1.0.0 | BSD-3-Clause | .env file parsing |

### Transitive Dependencies (Notable)

- markupsafe (Jinja2 dependency)
- urllib3, requests (docker SDK dependencies)

**License:** MIT (project license)
**Compatibility:** All dependencies are permissive licenses (BSD, MIT, Apache)

## Testing Strategy (Future)

### Planned Test Structure

```
tests/
├── unit/
│   ├── test_python_detector.py
│   ├── test_dockerfile_generator.py
│   └── test_cli.py
├── integration/
│   ├── test_python_fastmcp_server.py
│   ├── test_nodejs_mcp_server.py
│   └── test_end_to_end.py
└── fixtures/
    ├── sample-python-server/
    └── sample-nodejs-server/
```

### Test Framework

**Framework:** pytest
**Coverage:** pytest-cov
**Mocking:** pytest-mock, unittest.mock

### Test Categories

1. **Unit Tests:** Detector logic, generator logic, CLI argument parsing
2. **Integration Tests:** Full workflow (detect → generate → build)
3. **Smoke Tests:** Generated docker-compose.yml syntax validity
4. **Security Tests:** Credential detection, permission checks

## Known Technical Issues

### Issue 1: Missing Jinja2 Templates

**Symptom:** FileNotFoundError when generator tries to load templates
**Cause:** Templates directory exists but template files not yet created
**Status:** :x: Templates need to be created
**Priority:** HIGH (blocks usage)

**Required Templates:**
- `templates/python-uv.Dockerfile.j2`
- `templates/python-direct.Dockerfile.j2`
- `templates/README.md.j2` (optional, currently generated programmatically)

### Issue 2: Build/Test Flags Not Implemented

**Symptom:** `--build` and `--test` flags print "not yet implemented"
**Cause:** Placeholder TODOs in cli.py (lines 84-85, 88-89)
**Status:** :x: Needs implementation
**Priority:** MEDIUM (user can manually run docker compose build)

**Implementation Required:**
```python
if build:
    import subprocess
    result = subprocess.run(
        ["docker", "compose", "-f", str(output_dir / "docker-compose.yml"), "build"],
        cwd=output_dir
    )
    if result.returncode != 0:
        click.echo("❌ Build failed", err=True)
        sys.exit(1)
```

### Issue 3: No Node.js Support

**Symptom:** Fails on Node.js MCP SDK servers
**Cause:** Only PythonDetector implemented
**Status:** :x: Needs NodeDetector class
**Priority:** HIGH (50% of MCP servers use Node.js)

### Issue 4: Path Escaping

**Symptom:** Spaces in paths may break some workflows
**Cause:** docker-compose.yml uses type: bind (works), but future features may fail
**Status:** :warning: Partial workaround, not comprehensive
**Priority:** MEDIUM (affects 30% of users with /media/Drive 2/... paths)

## Environment Variables

### User-Configurable (Future)

```bash
# Output directory default
MCP_DOCKERIZE_OUTPUT_DIR=./docker-configs

# Template directory override
MCP_DOCKERIZE_TEMPLATES=/custom/templates

# Docker socket location (auto-detected)
DOCKER_HOST=unix:///var/run/docker.sock

# Verbose mode default
MCP_DOCKERIZE_VERBOSE=0
```

### System Detection

```bash
# Current working directory
PWD=/home/gyasis/Documents/code/AIdomaincertification/mcplibrarian

# User home directory
HOME=/home/gyasis

# Claude desktop config
CLAUDE_CONFIG=~/.config/Claude/claude_desktop_config.json
```

## Future Technology Additions (Planned)

### Smart-Scan Engine

**Language:** Rust or Go (for performance, static binary)
**Why:** Faster file scanning, better error handling, cross-platform binary
**Integration:** Python CLI calls libra binary via subprocess

### MCP Registry Database

**Database:** SQLite 3
**Schema:** servers, volumes, credentials, health_checks tables
**Location:** ~/.config/mcp-librarian/registry.db

### Health Check System

**Protocol:** JSON-RPC 2.0 (MCP protocol)
**Test:** Send initialize request, validate response
**Timeout:** 5 seconds
**Retry:** 3 attempts with exponential backoff

### Web Dashboard (Long-term)

**Framework:** FastAPI (Python) or Actix (Rust)
**Frontend:** HTMX or React
**Purpose:** Manage 100+ MCP servers via web UI
**Port:** localhost:8080 (local-only by default)
