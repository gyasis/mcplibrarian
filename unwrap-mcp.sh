#!/usr/bin/env bash
# unwrap-mcp.sh — Remove a wrapped MCP server
#
# Usage:
#   ./unwrap-mcp.sh <SERVER_NAME> [OPTIONS]
#
# Actions performed:
#   1. Remove entry from ~/.config/Claude/claude_desktop_config.json (via jq)
#   2. Delete docker-configs/<SERVER_NAME>/ directory (unless --keep-config)
#   3. Never touch original server source files
#
# Lookup order:
#   1. mcplibrarian remove (if installed)
#   2. uv run mcplibrarian remove (if uv available)
#   3. Shell fallback: jq-based JSON edit + directory removal
#
# Exit codes:
#   0 — server successfully removed
#   1 — error during removal
#   2 — usage error (missing required argument)

set -euo pipefail

# ---------------------------------------------------------------------------
# Color output
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
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
Usage: $0 <SERVER_NAME> [OPTIONS]

Remove a wrapped MCP server from the registry and platform config.

Arguments:
  SERVER_NAME      Name of the server to remove (required)

Options:
  --keep-config    Do not delete docker-configs/<SERVER_NAME>/ directory
  --yes            Skip confirmation prompt
  -h, --help       Show this help message

Examples:
  $0 my-mcp-server
  $0 my-mcp-server --keep-config
  $0 my-mcp-server --yes

Note:
  This command NEVER touches your original server source files.
  It only removes the generated docker-configs/ directory and
  the platform configuration entry.
EOF
    exit 2
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
SERVER_NAME=""
KEEP_CONFIG=false
AUTO_YES=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --keep-config)  KEEP_CONFIG=true; shift ;;
        --yes|-y)       AUTO_YES=true; shift ;;
        -h|--help)      usage ;;
        -*)
            log_error "Unknown option: $1"
            usage
            ;;
        *)
            if [[ -z "$SERVER_NAME" ]]; then
                SERVER_NAME="$1"
            else
                log_error "Unexpected argument: $1"
                usage
            fi
            shift
            ;;
    esac
done

# Require SERVER_NAME
if [[ -z "$SERVER_NAME" ]]; then
    log_error "SERVER_NAME is required."
    usage
fi

# ---------------------------------------------------------------------------
# Build extra args for delegation
# ---------------------------------------------------------------------------
EXTRA_ARGS=()
[[ "$KEEP_CONFIG" == "true" ]] && EXTRA_ARGS+=(--keep-config)
[[ "$AUTO_YES" == "true" ]]    && EXTRA_ARGS+=(--yes)

# ---------------------------------------------------------------------------
# Phase 1: Try installed mcplibrarian
# ---------------------------------------------------------------------------
if command -v mcplibrarian &>/dev/null; then
    log_step "Dispatch" "Using installed mcplibrarian remove"
    exec mcplibrarian remove "$SERVER_NAME" "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"
fi

# ---------------------------------------------------------------------------
# Phase 2: Try uv run mcplibrarian
# ---------------------------------------------------------------------------
if command -v uv &>/dev/null; then
    log_step "Dispatch" "mcplibrarian not in PATH — falling back to: uv run mcplibrarian"
    exec uv run mcplibrarian remove "$SERVER_NAME" "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"
fi

# ---------------------------------------------------------------------------
# Phase 3: Shell fallback
# ---------------------------------------------------------------------------
log_warn "mcplibrarian not found — using shell fallback mode."

DOCKER_CONFIGS_DIR="$(pwd)/docker-configs"
CONFIG_DIR="${DOCKER_CONFIGS_DIR}/${SERVER_NAME}"
CLAUDE_CONFIG="${HOME}/.config/Claude/claude_desktop_config.json"
REGISTRY_FILE="${HOME}/.config/mcp-librarian/registry.json"

# Verify the server exists in at least one known location
SERVER_FOUND=false
[[ -d "$CONFIG_DIR" ]] && SERVER_FOUND=true
if [[ -f "$REGISTRY_FILE" ]] && command -v jq &>/dev/null; then
    if jq -e ".servers[\"${SERVER_NAME}\"]" "$REGISTRY_FILE" &>/dev/null; then
        SERVER_FOUND=true
    fi
fi

if [[ "$SERVER_FOUND" == "false" ]]; then
    log_error "Server not found: ${SERVER_NAME}"
    log_error "No entry in docker-configs/ or registry.json"
    exit 1
fi

# ---------------------------------------------------------------------------
# Confirmation prompt
# ---------------------------------------------------------------------------
if [[ "$AUTO_YES" == "false" ]]; then
    printf "\n${BOLD}About to remove:${RESET} %s\n" "$SERVER_NAME"
    if [[ "$KEEP_CONFIG" == "false" && -d "$CONFIG_DIR" ]]; then
        printf "  - Delete directory  : %s\n" "$CONFIG_DIR"
    fi
    if [[ -f "$CLAUDE_CONFIG" ]]; then
        printf "  - Remove from       : %s\n" "$CLAUDE_CONFIG"
    fi
    if [[ -f "$REGISTRY_FILE" ]]; then
        printf "  - Remove from       : %s\n" "$REGISTRY_FILE"
    fi
    printf "\n${YELLOW}Original server source files will NOT be modified.${RESET}\n\n"

    read -r -p "Continue? [y/N] " confirm
    case "$confirm" in
        [yY][eE][sS]|[yY]) ;;
        *)
            printf "Aborted.\n"
            exit 0
            ;;
    esac
fi

EXIT_CODE=0

# ---------------------------------------------------------------------------
# Step 1: Remove from Claude Desktop config via jq
# ---------------------------------------------------------------------------
if [[ -f "$CLAUDE_CONFIG" ]]; then
    log_step "Config" "Removing ${SERVER_NAME} from Claude Desktop config"

    if ! command -v jq &>/dev/null; then
        log_warn "jq not found — cannot update $CLAUDE_CONFIG automatically"
        log_warn "Manually remove the '${SERVER_NAME}' key from mcpServers in:"
        log_warn "  $CLAUDE_CONFIG"
    else
        # Back up before writing
        cp "$CLAUDE_CONFIG" "${CLAUDE_CONFIG}.bak"
        log_step "Config" "Backup saved to ${CLAUDE_CONFIG}.bak"

        if jq -e ".mcpServers[\"${SERVER_NAME}\"]" "$CLAUDE_CONFIG" &>/dev/null; then
            jq "del(.mcpServers[\"${SERVER_NAME}\"])" "$CLAUDE_CONFIG" \
                > "${CLAUDE_CONFIG}.tmp"
            mv "${CLAUDE_CONFIG}.tmp" "$CLAUDE_CONFIG"
            log_ok "Removed ${SERVER_NAME} from Claude Desktop config"
        else
            log_warn "Server '${SERVER_NAME}' not found in mcpServers — nothing to remove"
        fi
    fi
else
    log_warn "Claude Desktop config not found: $CLAUDE_CONFIG (skipping)"
fi

# ---------------------------------------------------------------------------
# Step 2: Remove from mcp-librarian registry
# ---------------------------------------------------------------------------
if [[ -f "$REGISTRY_FILE" ]] && command -v jq &>/dev/null; then
    log_step "Registry" "Removing ${SERVER_NAME} from registry"
    if jq -e ".servers[\"${SERVER_NAME}\"]" "$REGISTRY_FILE" &>/dev/null; then
        cp "$REGISTRY_FILE" "${REGISTRY_FILE}.bak"
        jq "del(.servers[\"${SERVER_NAME}\"])" "$REGISTRY_FILE" \
            > "${REGISTRY_FILE}.tmp"
        mv "${REGISTRY_FILE}.tmp" "$REGISTRY_FILE"
        log_ok "Removed ${SERVER_NAME} from registry"
    else
        log_warn "Server '${SERVER_NAME}' not found in registry — nothing to remove"
    fi
fi

# ---------------------------------------------------------------------------
# Step 3: Delete docker-configs/<SERVER_NAME>/ directory
# ---------------------------------------------------------------------------
if [[ "$KEEP_CONFIG" == "true" ]]; then
    log_warn "--keep-config set — skipping deletion of ${CONFIG_DIR}"
else
    if [[ -d "$CONFIG_DIR" ]]; then
        log_step "Cleanup" "Deleting ${CONFIG_DIR}"
        rm -rf "$CONFIG_DIR"
        log_ok "Deleted ${CONFIG_DIR}"
    else
        log_warn "Config directory not found: ${CONFIG_DIR} (skipping)"
    fi
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
if [[ $EXIT_CODE -eq 0 ]]; then
    printf "\n${GREEN}Done!${RESET} Server '${SERVER_NAME}' has been removed.\n"
    printf "Original source files were not modified.\n\n"
else
    log_error "Removal completed with errors (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
