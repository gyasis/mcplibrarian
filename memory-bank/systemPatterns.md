# System Patterns: MCP Librarian

## Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Librarian CLI                        │
│                   (mcp-dockerize command)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴──────────┐
         │                      │
    ┌────▼────┐          ┌─────▼──────┐
    │Detectors│          │ Generators │
    └────┬────┘          └─────┬──────┘
         │                     │
    ┌────▼────────┐       ┌────▼───────────┐
    │ Python      │       │ Dockerfile     │
    │ Detector    │       │ Generator      │
    └─────────────┘       └────┬───────────┘
                               │
                          ┌────▼───────────┐
                          │ Jinja2         │
                          │ Templates      │
                          └────────────────┘
```

### Data Flow

```
User Input (MCP Server Path)
    │
    ▼
Python Detector
    │ - Reads pyproject.toml
    │ - Extracts metadata
    │ - Detects volumes
    │ - Security checks
    ▼
ServerMetadata Object
    │ - name, server_type
    │ - python_version
    │ - dependencies
    │ - env_vars
    │ - volume_mounts
    │ - warnings
    ▼
Dockerfile Generator
    │ - Choose deployment pattern
    │ - Render Jinja2 templates
    │ - Generate configs
    ▼
Output Directory
    ├── Dockerfile
    ├── docker-compose.yml
    ├── .env.example
    └── README.md
```

## Core Components

### 1. Python Detector (src/mcp_dockerize/detectors/python.py)

**Purpose:** Analyze Python MCP servers and extract metadata

**Key Methods:**
- `can_detect(path)`: Checks if path contains pyproject.toml
- `detect(path)`: Extracts full ServerMetadata
- `_extract_python_version(requires_python)`: Parse version from ">=3.10" syntax
- `_detect_server_type(path, pyproject)`: Determine python-uv | python-direct | python-fastmcp
- `_parse_env_file(env_file)`: Extract environment variables from .env
- `_detect_volumes(path, env_vars)`: Find required volume mounts
- `_security_checks(path, env_vars)`: Validate credential handling

**Detection Logic:**
```python
# Server Type Detection Order
1. Check for project.scripts (console_scripts entry point)
   → Return "python-uv" + script name
2. Check for main.py in root
   → Return "python-direct" + "main.py"
3. Check for src/**/server.py or src/**/__main__.py
   → Return "python-fastmcp" + relative path
4. Else: Raise ValueError (cannot determine)
```

**Volume Detection Heuristics:**
```python
# Paths to ALWAYS exclude (never mount these)
exclude_paths = {
    "/usr", "/etc", "/var", "/sys", "/proc", "/dev", "/tmp",
    "/opt", "/root", "/lib", "/lib64", "/bin", "/sbin",
    "/run", "/boot", "/home"
}

# Auto-detect volume mounts from:
1. .env file entries with .pem, .key, .cert, .crt extensions
2. Database/storage paths in .env (contains "database", "storage", ".db")
3. Hardcoded absolute paths in main server files
   - Only scan: main.py, server.py, src/server.py (not dependencies)
   - Only include paths with: /media/, /mnt/, "Drive", "Storage"
```

**Security Patterns:**
- Scan only main server files (not installed packages) to avoid false positives
- Detect hardcoded credentials using regex: `(password|secret|api_key|token)\s*=\s*["'][^"']+["']`
- Check SSH key permissions (warn if mode & 0o077 != 0)
- Never include secrets in Dockerfile or docker-compose.yml

### 2. Dockerfile Generator (src/mcp_dockerize/generators/dockerfile.py)

**Purpose:** Generate Docker configurations from metadata

**Deployment Pattern Selection:**
```python
def _choose_deployment_pattern(metadata):
    # Volume-mounted if:
    # - Has large volume mounts (/media/, /mnt/, "Drive")
    # - Has database/storage volumes (/data destinations)

    # Self-contained if:
    # - python-uv server type (installable package)
    # - No large external dependencies

    # Default: volume-mounted (preserves existing structure)
```

**Generated Files:**

1. **Dockerfile**
   - Template: `python-uv.Dockerfile.j2` or `python-direct.Dockerfile.j2`
   - Variables: python_version, entry_point, dependencies, server_type

2. **docker-compose.yml**
   - Service name: metadata.name
   - Container name: mcp-{metadata.name}
   - stdin_open: true (required for MCP stdio)
   - tty: false
   - Volumes: type: bind syntax (handles absolute paths)
   - Volume mounting strategy:
     - Source code: mounted at /app (read-only)
     - Data volumes: mounted at original host path if /media/ or /mnt/
     - Other volumes: mounted at /data/{name}

3. **.env.example**
   - Lists all environment variables from .env
   - Masks sensitive values (replaces with <YOUR_KEY_HERE>)

4. **README.md**
   - Server information (type, Python version, entry point)
   - Deployment pattern explanation
   - Quick start commands (build, run, test)
   - Claude Code integration snippet
   - Security warnings (if any)

### 3. CLI (src/mcp_dockerize/cli.py)

**Command Signature:**
```bash
mcp-dockerize [OPTIONS] SERVER_PATH
```

**Options:**
- `-o, --output`: Output directory (default: ./docker-configs)
- `-n, --name`: Container name (auto-detected if not provided)
- `--build`: Build Docker image after generation (NOT IMPLEMENTED)
- `--test`: Test container after building (NOT IMPLEMENTED)
- `-v, --verbose`: Verbose output

**Current Workflow:**
1. Validate server_path exists
2. Try Python detector (only detector implemented)
3. Generate metadata
4. Create output directory: {output}/{name}/
5. Generate all configuration files
6. Print success message with output location

## Design Patterns

### Pattern 1: Non-Destructive Analysis

**Principle:** Never modify source code, only analyze and generate external configs

**Implementation:**
- Read pyproject.toml, .env, main.py (read-only)
- Generate configs in separate output directory
- Use volume mounts (not COPY) to preserve original code
- Mark volumes as read_only: true in docker-compose.yml

### Pattern 2: Security-First Credential Handling

**Principle:** Never bake secrets into images

**Implementation:**
- Detect credentials in .env files
- Generate .env.example with masked values
- Use env_file in docker-compose.yml (not hardcoded env vars)
- Mount credential files as volumes (e.g., SSH keys)
- Warn if credentials detected in source code

### Pattern 3: Adaptive Path Handling

**Principle:** Handle spaces, absolute paths, and special characters gracefully

**Implementation:**
- Use `type: bind` mount syntax (not short-hand)
- Preserve original host paths for /media/, /mnt/ volumes (handles hardcoded paths)
- Escape paths when needed (future: Smart-Scan will auto-fix)

### Pattern 4: Template-Based Generation

**Principle:** Separate logic from output format

**Implementation:**
- Jinja2 templates for Dockerfile, README
- Programmatic generation for docker-compose.yml (complex logic)
- Templates in src/mcp_dockerize/templates/
- Variable injection: {{ python_version }}, {{ entry_point }}, etc.

### Pattern 5: Fail-Fast Validation

**Principle:** Detect issues early, before build failures

**Implementation:**
- Check pyproject.toml exists before processing
- Validate can determine entry point (else raise ValueError)
- Security warnings in generated configs (visible before build)
- Future: Smart-Scan will validate paths, dependencies, versions

## Technical Decisions

### Decision 1: Python-First Support
**Why:** 80% of MCP servers use Python FastMCP
**Trade-off:** Delays Node.js support, but faster time-to-value
**Future:** Add Node.js detector as second priority

### Decision 2: Volume-Mounted Default
**Why:** Preserves existing project structure, no code duplication
**Trade-off:** Slightly more complex docker-compose.yml
**Benefit:** Easy updates (rebuild without re-copying code)

### Decision 3: Type: Bind Mount Syntax
**Why:** Handles absolute paths and spaces better than short-hand
**Trade-off:** More verbose docker-compose.yml
**Benefit:** Reliable cross-platform (Linux, macOS, WSL)

### Decision 4: Original Path Preservation for /media/, /mnt/
**Why:** MCP servers often have hardcoded paths in code
**Trade-off:** Less portable (path must exist on host)
**Benefit:** Zero code changes required, works immediately

### Decision 5: Jinja2 Templates
**Why:** Clean separation of logic and output, easy customization
**Trade-off:** Additional dependency, slight complexity
**Benefit:** Users can customize templates without changing Python code

### Decision 6: CLI-First (No Library Mode)
**Why:** Primary use case is command-line tool
**Trade-off:** Harder to integrate in automated pipelines
**Future:** Add library mode if needed

## Data Models

### ServerMetadata (dataclass)

```python
@dataclass
class ServerMetadata:
    name: str                           # Server name (from pyproject.toml or dirname)
    server_type: str                    # "python-uv" | "python-direct" | "python-fastmcp"
    python_version: str                 # "3.10" | "3.11" | "3.12"
    entry_point: str                    # "main.py" | "server.py" | script name
    dependencies: List[str]             # From project.dependencies
    env_vars: Dict[str, str]            # From .env file
    env_file: Optional[str]             # Path to .env if exists
    volume_mounts: Dict[str, str]       # source_path: destination_path
    warnings: List[str]                 # Security warnings, issues
```

## Error Handling Strategy

### Current Approach
```python
try:
    metadata = detector.detect(server_path)
    generator.generate(metadata, output_dir, server_path)
    click.echo("✅ Success!")
except Exception as e:
    click.echo(f"❌ Error: {e}", err=True)
    if verbose:
        traceback.print_exc()
    sys.exit(1)
```

### Known Limitations
- Generic exception catching (should be more specific)
- Error messages may be cryptic (Docker errors, not our messages)
- No recovery mechanism (user must fix and retry manually)

### Future: Smart-Scan Error Handling
```python
# Planned architecture
try:
    context = SmartScan(server_path)
    context.detect_issues()
    if context.has_fixable_issues():
        context.auto_fix_issues()
    context.validate()
except RecoverableError as e:
    # Auto-fix and retry
except UnrecoverableError as e:
    # Clear guidance on manual fix
```

## Integration Points

### Claude Code Integration

Generated configuration snippet:
```json
{
  "mcpServers": {
    "deeplake-rag": {
      "command": "docker",
      "args": ["compose", "-f", "docker-configs/deeplake-rag/docker-compose.yml", "run", "--rm", "deeplake-rag"]
    }
  }
}
```

**Integration Method:** Manual copy-paste (for now)
**Future:** Auto-update ~/.config/Claude/claude_desktop_config.json

### Docker Integration

**Build:** `docker compose build` (in output directory)
**Run:** `docker compose up -d` (background) or `docker compose run --rm` (stdio)
**Test:** `echo '{"jsonrpc":"2.0","method":"initialize","params":{}}' | docker compose run --rm {name}`

## Performance Considerations

### Current Performance
- Detection: <100ms (read pyproject.toml, .env)
- Generation: <50ms (render templates, write files)
- Total: <200ms for typical MCP server

### Bottlenecks
- File I/O: Reading source files (main.py, server.py) for volume/security detection
- Regex scanning: Credential detection patterns

### Optimizations
- Only scan main server files (not node_modules or .venv)
- Use Path.glob() efficiently (specific patterns, not recursive *)
- Cache pyproject.toml parsing if multiple detectors run

## Future Architecture (Smart-Scan)

### Planned Enhancements
1. **Issue Detection Layer:** Detect problems before generation
2. **Auto-Fix Engine:** Automatically resolve common issues
3. **Validation Layer:** Verify generated configs will work
4. **State Tracking:** SQLite DB to track wrapped servers
5. **Health Checks:** MCP protocol validation after build
6. **Registry Auto-Update:** Modify claude_desktop_config.json safely

### Target Architecture
```
User Input
    │
    ▼
Smart-Scan Engine
    │ - Detect runtime, dependencies
    │ - Detect issues (missing files, version mismatches)
    │ - Auto-fix issues
    │ - Validate configuration
    ▼
Dockerfile Generator
    │ - Build configuration
    │ - Build Docker image
    │ - Run health checks
    ▼
Registry Manager
    │ - Update claude_desktop_config.json
    │ - Track server state in SQLite
    ▼
Success (Server Ready to Use)
```
