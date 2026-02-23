#!/usr/bin/env bash
# list-wrapped.sh — List all wrapped MCP servers and their status
#
# Usage:
#   ./list-wrapped.sh [OPTIONS]
#
# Lookup order:
#   1. mcplibrarian list (if mcplibrarian is installed)
#   2. uv run mcplibrarian list (if uv is available)
#   3. Shell fallback: parse ~/.config/mcp-librarian/registry.json with jq,
#      then fall back to scanning docker-configs/*/docker-compose.yml
#
# Exit codes:
#   0 — success (even if no servers registered)
#   1 — error reading registry or running docker

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

log_error() { printf "${RED}[ERROR]${RESET} %s\n" "$1" >&2; }
log_warn()  { printf "${YELLOW}[WARN]${RESET} %s\n" "$1" >&2; }

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
JSON_OUTPUT=false
STATUS_FILTER=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)         JSON_OUTPUT=true; shift ;;
        --status)       STATUS_FILTER="$2"; shift 2 ;;
        -h|--help)
            cat <<EOF
Usage: $0 [OPTIONS]

List all wrapped MCP servers with their current status.

Options:
  --json             Output as JSON array
  --status FILTER    Filter by status (running, stopped, unknown)
  -h, --help         Show this help message
EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Phase 1: Try installed mcplibrarian
# ---------------------------------------------------------------------------
if command -v mcplibrarian &>/dev/null; then
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        exec mcplibrarian list --json
    elif [[ -n "$STATUS_FILTER" ]]; then
        exec mcplibrarian list --status "$STATUS_FILTER"
    else
        exec mcplibrarian list
    fi
fi

# ---------------------------------------------------------------------------
# Phase 2: Try uv run mcplibrarian
# ---------------------------------------------------------------------------
if command -v uv &>/dev/null; then
    if [[ "$JSON_OUTPUT" == "true" ]]; then
        exec uv run mcplibrarian list --json
    elif [[ -n "$STATUS_FILTER" ]]; then
        exec uv run mcplibrarian list --status "$STATUS_FILTER"
    else
        exec uv run mcplibrarian list
    fi
fi

# ---------------------------------------------------------------------------
# Phase 3: Shell fallback — parse registry.json or scan docker-configs/
# ---------------------------------------------------------------------------
REGISTRY_FILE="${HOME}/.config/mcp-librarian/registry.json"
DOCKER_CONFIGS_DIR="$(pwd)/docker-configs"

# Helper: check container running state for a given compose file
check_container_status() {
    local compose_file="$1"
    local service_name="$2"
    local status="unknown"

    if ! command -v docker &>/dev/null; then
        printf "unknown"
        return
    fi

    if docker compose -f "$compose_file" ps 2>/dev/null | grep -q "Up"; then
        printf "running"
    else
        printf "stopped"
    fi
}

# Helper: status to colored symbol
status_symbol() {
    case "$1" in
        running)  printf "${GREEN}running${RESET}" ;;
        stopped)  printf "${YELLOW}stopped${RESET}" ;;
        healthy)  printf "${GREEN}healthy${RESET}" ;;
        unhealthy) printf "${RED}unhealthy${RESET}" ;;
        *)        printf "${CYAN}unknown${RESET}" ;;
    esac
}

# ---------------------------------------------------------------------------
# Try registry.json first (richer data)
# ---------------------------------------------------------------------------
if [[ -f "$REGISTRY_FILE" ]]; then
    if ! command -v jq &>/dev/null; then
        log_warn "jq not found — cannot parse registry.json. Falling back to docker-configs/ scan."
    else
        SERVER_COUNT="$(jq '.servers | length' "$REGISTRY_FILE" 2>/dev/null || echo "0")"

        if [[ "$SERVER_COUNT" -eq 0 ]]; then
            printf "No servers registered yet.\n"
            exit 0
        fi

        if [[ "$JSON_OUTPUT" == "true" ]]; then
            jq '.servers | to_entries | map({
                name: .key,
                runtime: .value.runtime,
                status: .value.status,
                platforms: .value.registered_platforms,
                last_health: (.value.health.status // "unknown")
            })' "$REGISTRY_FILE"
            exit 0
        fi

        # Print table header
        printf "\n${BOLD}%-30s  %-10s  %-12s  %-20s  %-12s${RESET}\n" \
            "NAME" "RUNTIME" "STATUS" "PLATFORMS" "LAST HEALTH"
        printf "%s\n" "$(printf '%0.s-' {1..90})"

        jq -r '.servers | to_entries[] | [
            .key,
            (.value.runtime // "unknown"),
            (.value.status // "unknown"),
            ((.value.registered_platforms // []) | join(",")),
            (.value.health.status // "unknown")
        ] | @tsv' "$REGISTRY_FILE" 2>/dev/null | \
        while IFS=$'\t' read -r name runtime status platforms last_health; do
            # Apply status filter if set
            if [[ -n "$STATUS_FILTER" && "$status" != "$STATUS_FILTER" ]]; then
                continue
            fi
            printf "%-30s  %-10s  %-12s  %-20s  %s\n" \
                "$name" "$runtime" "$status" "${platforms:-(none)}" "$last_health"
        done

        printf "\n"
        exit 0
    fi
fi

# ---------------------------------------------------------------------------
# Fallback: scan docker-configs/*/docker-compose.yml
# ---------------------------------------------------------------------------
if [[ ! -d "$DOCKER_CONFIGS_DIR" ]]; then
    printf "No servers registered yet.\n"
    printf "\nTip: Run ./wrap-mcp.sh <path> to wrap your first MCP server.\n"
    exit 0
fi

# Collect compose files
mapfile -t COMPOSE_FILES < <(find "$DOCKER_CONFIGS_DIR" -maxdepth 2 -name "docker-compose.yml" 2>/dev/null | sort)

if [[ ${#COMPOSE_FILES[@]} -eq 0 ]]; then
    printf "No servers registered yet.\n"
    printf "\nTip: Run ./wrap-mcp.sh <path> to wrap your first MCP server.\n"
    exit 0
fi

if [[ "$JSON_OUTPUT" == "true" ]]; then
    # Build JSON array
    printf "[\n"
    first=true
    for compose_file in "${COMPOSE_FILES[@]}"; do
        server_name="$(basename "$(dirname "$compose_file")")"
        status="$(check_container_status "$compose_file" "$server_name")"

        if [[ -n "$STATUS_FILTER" && "$status" != "$STATUS_FILTER" ]]; then
            continue
        fi

        if [[ "$first" == "true" ]]; then
            first=false
        else
            printf ",\n"
        fi
        printf '  {"name": "%s", "status": "%s", "compose_file": "%s"}' \
            "$server_name" "$status" "$compose_file"
    done
    printf "\n]\n"
else
    # Print table header
    printf "\n${BOLD}%-30s  %-12s  %-s${RESET}\n" "NAME" "STATUS" "COMPOSE FILE"
    printf "%s\n" "$(printf '%0.s-' {1..80})"

    SHOWN=0
    for compose_file in "${COMPOSE_FILES[@]}"; do
        server_name="$(basename "$(dirname "$compose_file")")"
        status="$(check_container_status "$compose_file" "$server_name")"

        if [[ -n "$STATUS_FILTER" && "$status" != "$STATUS_FILTER" ]]; then
            continue
        fi

        status_display="$(status_symbol "$status")"
        printf "%-30s  %-12b  %s\n" "$server_name" "$status_display" "$compose_file"
        ((SHOWN++)) || true
    done

    if [[ $SHOWN -eq 0 ]]; then
        printf "(no servers match filter: %s)\n" "$STATUS_FILTER"
    fi

    printf "\n"
fi
