#!/usr/bin/env bash
# health-check.sh — Run health checks on wrapped MCP servers
#
# Usage:
#   ./health-check.sh [SERVER_NAME] [OPTIONS]
#
# If SERVER_NAME is given, checks only that server.
# If omitted, checks all registered servers.
#
# Health levels:
#   L1 — Container running state (docker compose ps)
#   L2 — MCP protocol response (initialize JSON-RPC)
#
# Lookup order:
#   1. mcplibrarian health (if installed)
#   2. uv run mcplibrarian health (if uv available)
#   3. Shell fallback: direct docker inspect + JSON-RPC probe
#
# Exit codes:
#   0 — all checked servers are healthy or stopped (not unhealthy)
#   1 — one or more servers are unhealthy
#   2 — server not found in registry or docker-configs/

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
log_fail()  { printf "${RED}[FAIL]${RESET} %s\n" "$1" >&2; }

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
SERVER_NAME=""
RECOVER=false
SHOW_HISTORY=false
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --recover)  RECOVER=true; shift ;;
        --history)  SHOW_HISTORY=true; shift ;;
        --json)     JSON_OUTPUT=true; shift ;;
        -h|--help)
            cat <<EOF
Usage: $0 [SERVER_NAME] [OPTIONS]

Run health checks on wrapped MCP servers.

Arguments:
  SERVER_NAME    (Optional) Name of a specific server to check.
                 If omitted, all registered servers are checked.

Options:
  --recover      Attempt to restart unhealthy containers
  --history      Show last 24h check history (requires mcplibrarian)
  --json         Output results as JSON
  -h, --help     Show this help message

Exit codes:
  0 — all targets healthy (or stopped)
  1 — one or more servers unhealthy
  2 — specified server not found

Examples:
  $0                        # check all servers
  $0 my-mcp-server          # check one server
  $0 my-mcp-server --recover
EOF
            exit 0
            ;;
        -*)
            log_error "Unknown option: $1"
            exit 1
            ;;
        *)
            if [[ -z "$SERVER_NAME" ]]; then
                SERVER_NAME="$1"
            else
                log_error "Unexpected argument: $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Build extra args for delegation
# ---------------------------------------------------------------------------
EXTRA_ARGS=()
[[ "$RECOVER" == "true" ]]      && EXTRA_ARGS+=(--recover)
[[ "$SHOW_HISTORY" == "true" ]] && EXTRA_ARGS+=(--history)
[[ "$JSON_OUTPUT" == "true" ]]  && EXTRA_ARGS+=(--json)

# ---------------------------------------------------------------------------
# Phase 1: Try installed mcplibrarian
# ---------------------------------------------------------------------------
if command -v mcplibrarian &>/dev/null; then
    log_step "Dispatch" "Using installed mcplibrarian health"
    if [[ -n "$SERVER_NAME" ]]; then
        exec mcplibrarian health "$SERVER_NAME" "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"
    else
        exec mcplibrarian health "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"
    fi
fi

# ---------------------------------------------------------------------------
# Phase 2: Try uv run mcplibrarian
# ---------------------------------------------------------------------------
if command -v uv &>/dev/null; then
    log_step "Dispatch" "mcplibrarian not in PATH — falling back to: uv run mcplibrarian"
    if [[ -n "$SERVER_NAME" ]]; then
        exec uv run mcplibrarian health "$SERVER_NAME" "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"
    else
        exec uv run mcplibrarian health "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"
    fi
fi

# ---------------------------------------------------------------------------
# Phase 3: Shell fallback — L1 + L2 health checks via docker directly
# ---------------------------------------------------------------------------
log_warn "mcplibrarian not found — using shell health-check mode (L1 + L2 only)."

DOCKER_CONFIGS_DIR="$(pwd)/docker-configs"

if ! command -v docker &>/dev/null; then
    log_error "docker is required but not found in PATH."
    exit 1
fi

# ---------------------------------------------------------------------------
# Helper: L1 check — container running state
# ---------------------------------------------------------------------------
check_l1() {
    local compose_file="$1"
    local name="$2"

    if docker compose -f "$compose_file" ps 2>/dev/null | grep -q "Up"; then
        printf "running"
    else
        printf "stopped"
    fi
}

# ---------------------------------------------------------------------------
# Helper: L2 check — MCP initialize JSON-RPC probe
# ---------------------------------------------------------------------------
check_l2() {
    local compose_file="$1"
    local name="$2"
    local timeout_sec=10

    local jsonrpc_init='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"health-check","version":"0.1"}}}'

    local response
    if response="$(echo "$jsonrpc_init" | \
        timeout "$timeout_sec" \
        docker compose -f "$compose_file" run --rm --no-TTY "$name" 2>/dev/null)"; then
        if printf '%s' "$response" | grep -q '"jsonrpc"'; then
            printf "responds"
        else
            printf "no-jsonrpc"
        fi
    else
        printf "timeout"
    fi
}

# ---------------------------------------------------------------------------
# Helper: display result for one server
# ---------------------------------------------------------------------------
print_result() {
    local name="$1"
    local l1_status="$2"
    local l2_status="$3"

    local overall_status
    if [[ "$l1_status" == "running" && "$l2_status" == "responds" ]]; then
        overall_status="healthy"
    elif [[ "$l1_status" == "stopped" ]]; then
        overall_status="stopped"
    else
        overall_status="unhealthy"
    fi

    local l1_icon l2_icon
    [[ "$l1_status" == "running" ]] && l1_icon="${GREEN}OK${RESET}" || l1_icon="${YELLOW}--${RESET}"
    [[ "$l2_status" == "responds" ]] && l2_icon="${GREEN}OK${RESET}" || l2_icon="${YELLOW}--${RESET}"

    printf "${BOLD}%s${RESET}\n" "$name"
    printf "  L1 Container state : %b (%s)\n" "$l1_icon" "$l1_status"
    printf "  L2 Protocol probe  : %b (%s)\n" "$l2_icon" "$l2_status"

    case "$overall_status" in
        healthy)  printf "  Overall            : ${GREEN}healthy${RESET}\n\n" ;;
        stopped)  printf "  Overall            : ${YELLOW}stopped${RESET}\n\n" ;;
        unhealthy) printf "  Overall            : ${RED}unhealthy${RESET}\n\n" ;;
    esac

    printf '%s' "$overall_status"
}

# ---------------------------------------------------------------------------
# Resolve target servers
# ---------------------------------------------------------------------------
if [[ -n "$SERVER_NAME" ]]; then
    # Single server
    COMPOSE_FILE="${DOCKER_CONFIGS_DIR}/${SERVER_NAME}/docker-compose.yml"
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        log_error "Server not found: ${SERVER_NAME}"
        log_error "Expected compose file at: $COMPOSE_FILE"
        exit 2
    fi
    TARGET_FILES=("$COMPOSE_FILE")
    TARGET_NAMES=("$SERVER_NAME")
else
    # All servers
    if [[ ! -d "$DOCKER_CONFIGS_DIR" ]]; then
        printf "No servers registered yet.\n"
        printf "Run ./wrap-mcp.sh <path> to wrap your first MCP server.\n"
        exit 0
    fi

    mapfile -t TARGET_FILES < <(find "$DOCKER_CONFIGS_DIR" -maxdepth 2 -name "docker-compose.yml" 2>/dev/null | sort)
    TARGET_NAMES=()
    for f in "${TARGET_FILES[@]}"; do
        TARGET_NAMES+=("$(basename "$(dirname "$f")")")
    done

    if [[ ${#TARGET_FILES[@]} -eq 0 ]]; then
        printf "No servers registered yet.\n"
        printf "Run ./wrap-mcp.sh <path> to wrap your first MCP server.\n"
        exit 0
    fi
fi

# ---------------------------------------------------------------------------
# Run checks
# ---------------------------------------------------------------------------
printf "\n${BOLD}MCP Server Health Check${RESET}\n"
printf "%s\n\n" "$(printf '%0.s-' {1..50})"

OVERALL_EXIT=0

if [[ "$JSON_OUTPUT" == "true" ]]; then
    RESULTS=()
fi

for i in "${!TARGET_FILES[@]}"; do
    compose_file="${TARGET_FILES[$i]}"
    name="${TARGET_NAMES[$i]}"

    log_step "Check" "Checking $name ..."

    l1_status="$(check_l1 "$compose_file" "$name")"

    # Only run L2 if container is running
    if [[ "$l1_status" == "running" ]]; then
        log_step "L2" "Probing MCP protocol ..."
        l2_status="$(check_l2 "$compose_file" "$name")"
    else
        l2_status="skipped"
    fi

    # Capture overall status from print_result output
    result_output="$(print_result "$name" "$l1_status" "$l2_status")"
    # Last line is the overall status string captured separately
    overall_status="$(printf '%s' "$result_output" | tail -n1)"
    # Print everything except the last line (status marker)
    printf '%s' "$result_output" | head -n -1
    printf "\n"

    if [[ "$overall_status" == "unhealthy" ]]; then
        OVERALL_EXIT=1

        # Attempt recovery if requested
        if [[ "$RECOVER" == "true" ]]; then
            log_step "Recover" "Attempting to restart $name ..."
            if docker compose -f "$compose_file" restart "$name" 2>/dev/null; then
                log_step "Recover" "Waiting 5s for container to stabilize ..."
                sleep 5
                new_l1="$(check_l1 "$compose_file" "$name")"
                new_l2="$(check_l2 "$compose_file" "$name")"
                if [[ "$new_l1" == "running" && "$new_l2" == "responds" ]]; then
                    log_ok "Recovery successful — $name is now healthy"
                    OVERALL_EXIT=0
                else
                    log_fail "Recovery failed — $name remains unhealthy"
                fi
            else
                log_fail "docker compose restart failed for $name"
            fi
        fi
    fi
done

if [[ $OVERALL_EXIT -eq 0 ]]; then
    printf "${GREEN}All checks passed.${RESET}\n"
else
    printf "${RED}One or more servers are unhealthy.${RESET}\n"
    printf "Tip: Run with --recover to attempt automatic restart.\n"
fi

exit $OVERALL_EXIT
