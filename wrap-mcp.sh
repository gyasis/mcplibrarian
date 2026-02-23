#!/usr/bin/env bash
# wrap-mcp.sh — Shell wrapper for mcplibrarian wrap
#
# Usage:
#   ./wrap-mcp.sh <SERVER_PATH> [OPTIONS]
#   ./wrap-mcp.sh tests/fixtures/sample-node-server/ --platform cursor
#
# Phases:
#   1. Use installed mcplibrarian if available
#   2. Fall back to uv run mcplibrarian if uv is available
#   3. Fall back to pure shell detection + docker-based generation
#
# Exit codes:
#   0 — success
#   1 — general error (detection failure, build failure)
#   2 — usage error (bad arguments)
#   3 — dependency not found (no mcplibrarian and no uv)

set -euo pipefail

# ---------------------------------------------------------------------------
# Color-coded step output matching CLI convention
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

log_step()  { printf "${CYAN}[%s]${RESET} %s\n" "$1" "$2"; }
log_ok()    { printf "${GREEN}[OK]${RESET} %s\n" "$1"; }
log_warn()  { printf "${YELLOW}[WARN]${RESET} %s\n" "$1" >&2; }
log_error() { printf "${RED}[ERROR]${RESET} %s\n" "$1" >&2; }

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
    cat >&2 <<EOF
Usage: $0 <SERVER_PATH> [OPTIONS]

Wrap an MCP server in a Docker container and register it with a platform.

Arguments:
  SERVER_PATH    Path to the MCP server directory

Options:
  --name NAME          Override the server name (default: directory name)
  --platform PLATFORM  Target platform (default: claude_code)
                       Supported: claude_code, cursor, vscode, goose, codex, opencode
  --no-health-check    Skip health check after build
  --no-register        Skip platform config registration
  --force              Overwrite existing config
  --verbose            Print detailed output
  --dry-run            Print steps without executing
  -h, --help           Show this help message

Examples:
  $0 ./my-mcp-server/
  $0 ./my-mcp-server/ --platform cursor
  $0 ./my-mcp-server/ --name my-server --platform claude_code
EOF
    exit 2
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
if [[ $# -eq 0 ]]; then
    usage
fi

SERVER_PATH=""
EXTRA_ARGS=()

for arg in "$@"; do
    case "$arg" in
        -h|--help) usage ;;
        *) ;;
    esac
done

# Pass the first positional arg as SERVER_PATH, rest as extra args
SERVER_PATH="$1"
shift
EXTRA_ARGS=("$@")

if [[ -z "$SERVER_PATH" ]]; then
    log_error "SERVER_PATH is required."
    usage
fi

# ---------------------------------------------------------------------------
# Phase 1: Try installed mcplibrarian
# ---------------------------------------------------------------------------
if command -v mcplibrarian &>/dev/null; then
    log_step "Dispatch" "Using installed mcplibrarian"
    exec mcplibrarian wrap "$SERVER_PATH" "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"
fi

# ---------------------------------------------------------------------------
# Phase 2: Try uv run mcplibrarian
# ---------------------------------------------------------------------------
if command -v uv &>/dev/null; then
    log_step "Dispatch" "mcplibrarian not in PATH — falling back to: uv run mcplibrarian"
    exec uv run mcplibrarian wrap "$SERVER_PATH" "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"
fi

# ---------------------------------------------------------------------------
# Phase 3: Pure shell fallback — minimal detection + docker-based generation
# ---------------------------------------------------------------------------
log_warn "mcplibrarian not found and uv not available — using shell fallback mode."
log_warn "Install mcplibrarian for full feature support: pip install mcplibrarian"

SERVER_PATH="$(realpath "$SERVER_PATH")"

if [[ ! -d "$SERVER_PATH" ]]; then
    log_error "Directory not found: $SERVER_PATH"
    exit 1
fi

# Determine server name from directory
SERVER_NAME="${SERVER_NAME:-$(basename "$SERVER_PATH")}"
# Sanitize: lowercase, replace non-alphanumeric with hyphens
SERVER_NAME="$(printf '%s' "$SERVER_NAME" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-\+//;s/-\+$//')"

PLATFORM="${PLATFORM:-claude_code}"
CONFIG_DIR="$(pwd)/docker-configs/${SERVER_NAME}"
CLAUDE_CONFIG="${HOME}/.config/Claude/claude_desktop_config.json"

# Detect runtime
RUNTIME=""
ENTRY_POINT=""
NODE_VERSION="20"

if [[ -f "${SERVER_PATH}/pyproject.toml" ]]; then
    RUNTIME="python"
    log_step "Detect" "Detected Python server (pyproject.toml found)"
elif [[ -f "${SERVER_PATH}/requirements.txt" ]]; then
    RUNTIME="python-direct"
    log_step "Detect" "Detected Python server (requirements.txt found)"
elif [[ -f "${SERVER_PATH}/package.json" ]]; then
    RUNTIME="node"
    log_step "Detect" "Detected Node.js server (package.json found)"
    # Try to read node version from .nvmrc or .node-version
    if [[ -f "${SERVER_PATH}/.nvmrc" ]]; then
        NODE_VERSION="$(tr -d 'v\n' < "${SERVER_PATH}/.nvmrc")"
    elif [[ -f "${SERVER_PATH}/.node-version" ]]; then
        NODE_VERSION="$(tr -d 'v\n' < "${SERVER_PATH}/.node-version")"
    fi
    # Extract entry point from package.json
    if command -v jq &>/dev/null; then
        ENTRY_POINT="$(jq -r '.main // empty' "${SERVER_PATH}/package.json" 2>/dev/null || true)"
    fi
    ENTRY_POINT="${ENTRY_POINT:-index.js}"
else
    log_error "Cannot detect runtime in: $SERVER_PATH"
    log_error "Expected package.json, pyproject.toml, or requirements.txt"
    exit 1
fi

# Generate package-lock.json for Node servers if missing
if [[ "$RUNTIME" == "node" && ! -f "${SERVER_PATH}/package-lock.json" ]]; then
    log_step "Fix" "package-lock.json missing — generating via docker run node:${NODE_VERSION}-slim"
    docker run --rm \
        -v "${SERVER_PATH}:/app" \
        -w /app \
        "node:${NODE_VERSION}-slim" \
        npm install --package-lock-only --legacy-peer-deps
    log_ok "package-lock.json generated"
fi

# Create config directory
log_step "Generate" "Creating output directory: $CONFIG_DIR"
mkdir -p "$CONFIG_DIR"

# Write Dockerfile
DOCKERFILE="${CONFIG_DIR}/Dockerfile"
log_step "Generate" "Writing Dockerfile"

if [[ "$RUNTIME" == "node" ]]; then
    cat > "$DOCKERFILE" <<EODF
FROM node:${NODE_VERSION}-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production
COPY . .
CMD ["node", "${ENTRY_POINT}"]
EODF
elif [[ "$RUNTIME" == "python" ]]; then
    cat > "$DOCKERFILE" <<EODF
FROM python:3.11-slim
RUN pip install uv
WORKDIR /app
COPY . .
RUN uv sync --frozen --no-dev
CMD ["uv", "run", "python", "-m", "${SERVER_NAME}"]
EODF
elif [[ "$RUNTIME" == "python-direct" ]]; then
    cat > "$DOCKERFILE" <<EODF
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "server.py"]
EODF
fi

# Write docker-compose.yml
COMPOSE_FILE="${CONFIG_DIR}/docker-compose.yml"
log_step "Generate" "Writing docker-compose.yml"
cat > "$COMPOSE_FILE" <<EODC
version: "3.8"
services:
  ${SERVER_NAME}:
    build:
      context: ${SERVER_PATH}
      dockerfile: ${DOCKERFILE}
    stdin_open: true
    tty: false
    volumes:
      - type: bind
        source: ${SERVER_PATH}
        target: /app
        read_only: true
    env_file:
      - .env
EODC

# Write .env placeholder
if [[ ! -f "${CONFIG_DIR}/.env" ]]; then
    cat > "${CONFIG_DIR}/.env" <<EODE
# Environment variables for ${SERVER_NAME}
# Add your configuration here
EODE
fi

# Build the image
log_step "Build" "Running docker compose build"
docker compose -f "$COMPOSE_FILE" build

log_ok "Container built successfully"

# Update Claude Desktop config
if [[ "$PLATFORM" == "claude_code" ]]; then
    log_step "Register" "Updating Claude Desktop config: $CLAUDE_CONFIG"
    mkdir -p "$(dirname "$CLAUDE_CONFIG")"

    if ! command -v jq &>/dev/null; then
        log_warn "jq not found — cannot update $CLAUDE_CONFIG automatically"
        log_warn "Add the following entry manually:"
        cat >&2 <<EOJSON
{
  "mcpServers": {
    "${SERVER_NAME}": {
      "command": "docker",
      "args": ["compose", "-f", "${COMPOSE_FILE}", "run", "--rm", "${SERVER_NAME}"]
    }
  }
}
EOJSON
    else
        # Initialize config file if missing
        if [[ ! -f "$CLAUDE_CONFIG" ]]; then
            printf '{"mcpServers": {}}' > "$CLAUDE_CONFIG"
        fi

        # Back up before writing
        cp "$CLAUDE_CONFIG" "${CLAUDE_CONFIG}.bak"

        # Merge entry using jq
        NEW_ENTRY="$(jq -n \
            --arg name "$SERVER_NAME" \
            --arg compose "$COMPOSE_FILE" \
            '{($name): {command: "docker", args: ["compose", "-f", $compose, "run", "--rm", $name]}}')"

        jq --argjson entry "$NEW_ENTRY" '.mcpServers += $entry' "$CLAUDE_CONFIG" \
            > "${CLAUDE_CONFIG}.tmp"
        mv "${CLAUDE_CONFIG}.tmp" "$CLAUDE_CONFIG"

        log_ok "Registered ${SERVER_NAME} in Claude Desktop config"
    fi
fi

log_ok "Done! Server '${SERVER_NAME}' is wrapped and ready."
printf "\nConfig directory : %s\n" "$CONFIG_DIR"
printf "Compose file     : %s\n" "$COMPOSE_FILE"
if [[ "$PLATFORM" == "claude_code" ]]; then
    printf "Platform config  : %s\n" "$CLAUDE_CONFIG"
fi
