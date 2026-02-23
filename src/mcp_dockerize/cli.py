#!/usr/bin/env python3
"""CLI interface for mcplibrarian."""

import fnmatch
import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import click

from .builders.docker_builder import DockerBuildError, DockerBuilder
from .generators.compose import ComposeGenerator
from .generators.dockerfile import DockerfileGenerator
from .health.checker import MCPHealthChecker
from .health.states import HealthStatus
from .platforms import VALID_PLATFORMS, get_platform
from .registry.models import ContainerConfig, RegistryEntry, Runtime, ServerStatus
from .registry.store import RegistryStore
from .smart_scan.fixer import AutoFixer
from .smart_scan.issues import Severity
from .smart_scan.scanner import SmartScan, discover_servers


@click.group()
@click.version_option()
def cli():
    """mcplibrarian — Containerize MCP servers for on-demand loading."""
    pass


@cli.command("wrap")
@click.argument("server_path", type=click.Path(exists=True))
@click.option("--name", default=None, help="Container name (auto-detected if not provided)")
@click.option(
    "--platform",
    "platforms",
    multiple=True,
    default=["claude_code"],
    help=(
        "Target platform (repeatable). "
        "Valid: claude_code, cursor, vscode, goose, codex, opencode"
    ),
)
@click.option("--no-health-check", is_flag=True, help="Skip health check after build")
@click.option("--no-register", is_flag=True, help="Skip registry registration")
@click.option("--force", is_flag=True, help="Force re-wrap even if already registered")
@click.option("--dry-run", is_flag=True, help="Show what would be done without doing it")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def wrap(
    server_path: str,
    name: str | None,
    platforms: tuple[str, ...],
    no_health_check: bool,
    no_register: bool,
    force: bool,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Containerize an MCP server for on-demand loading.

    Auto-detects runtime, generates Docker configs, builds container,
    and registers with the target AI platform.

    Example:

        mcplibrarian wrap /home/user/my-mcp-server

        mcplibrarian wrap /home/user/my-mcp-server --platform cursor --platform vscode
    """
    server_path_abs = Path(server_path).resolve()

    # Validate platforms up-front (even in dry-run) so we fail fast on typos.
    for pid in platforms:
        if pid not in VALID_PLATFORMS:
            click.echo(
                f"[ERROR] Unknown platform: '{pid}'\n"
                f"  → Valid platforms: {', '.join(VALID_PLATFORMS)}",
                err=True,
            )
            sys.exit(1)

    # ------------------------------------------------------------------
    # Dry-run path — enumerate steps and exit 0.
    # ------------------------------------------------------------------
    if dry_run:
        click.echo(f"[DRY RUN] wrap {server_path_abs}")
        click.echo(f"[DRY RUN]   [Scan]     SmartScan({server_path_abs}).run()")
        click.echo(f"[DRY RUN]   [Fix]      AutoFixer(scan_result).fix_all()")
        effective_name = name or server_path_abs.name
        output_dir = _config_dir(server_path_abs, effective_name)
        click.echo(
            f"[DRY RUN]   [Generate] DockerfileGenerator + ComposeGenerator -> {output_dir}"
        )
        click.echo(f"[DRY RUN]   [Build]    DockerBuilder.build_image({output_dir})")
        if not no_health_check:
            click.echo(f"[DRY RUN]   [Health]   MCPHealthChecker.check(entry)")
        if not no_register:
            click.echo(f"[DRY RUN]   [Register] RegistryStore.add(entry)")
        for pid in platforms:
            click.echo(
                f"[DRY RUN]   [Platform] get_platform('{pid}').add_server(entry, compose_path)"
            )
        return

    server_name = name  # caller-supplied name override
    _server_name, success, error_msg, _ = _wrap_one(
        path=server_path_abs,
        name=server_name,
        platforms=platforms,
        no_health_check=no_health_check,
        no_register=no_register,
        force=force,
        verbose=verbose,
        log=click.echo,
    )
    if not success:
        click.echo(f"[ERROR] {error_msg}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# wrap-all command
# ---------------------------------------------------------------------------


@cli.command("wrap-all")
@click.argument("scan_dir", type=click.Path(exists=True))
@click.option(
    "--workers",
    default=4,
    type=click.IntRange(1, 8),
    help="Max parallel workers (default 4, max 8)",
)
@click.option(
    "--platform",
    "platforms",
    multiple=True,
    default=["claude_code"],
    help=(
        "Target platform (repeatable). "
        "Valid: claude_code, cursor, vscode, goose, codex, opencode"
    ),
)
@click.option(
    "--skip-existing",
    is_flag=True,
    default=True,
    help="Skip already-registered servers (default: True)",
)
@click.option("--force", is_flag=True, help="Force re-wrap even if registered")
@click.option(
    "--filter",
    "filter_glob",
    default=None,
    help="Glob pattern to filter server directory names (e.g. 'my-*')",
)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output per server")
def wrap_all(
    scan_dir: str,
    workers: int,
    platforms: tuple[str, ...],
    skip_existing: bool,
    force: bool,
    filter_glob: str | None,
    yes: bool,
    verbose: bool,
) -> None:
    """Discover and wrap all MCP servers found under SCAN_DIR in parallel.

    Walks SCAN_DIR up to two directory levels deep, detects Python and Node.js
    MCP servers, and runs the same wrap pipeline as the ``wrap`` command for
    each one using a thread pool.

    Example:

        mcplibrarian wrap-all /home/user/mcp-servers --workers 4

        mcplibrarian wrap-all /home/user/mcp-servers --filter 'my-*' --yes
    """
    scan_dir_abs = Path(scan_dir).resolve()

    # Validate platforms up-front.
    for pid in platforms:
        if pid not in VALID_PLATFORMS:
            click.echo(
                f"[ERROR] Unknown platform: '{pid}'\n"
                f"  → Valid platforms: {', '.join(VALID_PLATFORMS)}",
                err=True,
            )
            sys.exit(1)

    # ------------------------------------------------------------------
    # Step 1: Discover servers.
    # ------------------------------------------------------------------
    click.echo(f"[Discover] Scanning {scan_dir_abs} (max_depth=2) ...")
    try:
        discovered: list[Path] = discover_servers(scan_dir_abs, max_depth=2)
    except Exception as exc:
        click.echo(f"[ERROR] Discovery failed: {exc}", err=True)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 2: Apply --filter glob if provided.
    # ------------------------------------------------------------------
    if filter_glob:
        discovered = [p for p in discovered if fnmatch.fnmatch(p.name, filter_glob)]
        click.echo(f"[Filter]   Pattern '{filter_glob}' matched {len(discovered)} server(s).")

    if not discovered:
        click.echo("[Info] No MCP servers found. Nothing to do.")
        sys.exit(0)

    # ------------------------------------------------------------------
    # Step 3: Apply --skip-existing (unless --force overrides).
    # ------------------------------------------------------------------
    if skip_existing and not force:
        store = RegistryStore()
        registered_names = {e.name for e in store.list_all()}
        skipped = [
            p for p in discovered
            if _resolve_server_name(p) in registered_names
        ]
        discovered = [
            p for p in discovered
            if _resolve_server_name(p) not in registered_names
        ]
        if skipped:
            click.echo(
                f"[Skip]     {len(skipped)} already-registered server(s) skipped "
                f"(use --force to re-wrap): "
                + ", ".join(p.name for p in skipped)
            )

    if not discovered:
        click.echo("[Info] All discovered servers are already registered. Nothing to do.")
        sys.exit(0)

    # ------------------------------------------------------------------
    # Step 4: Confirmation prompt.
    # ------------------------------------------------------------------
    click.echo(f"\nFound {len(discovered)} server(s) to wrap:")
    for p in discovered:
        click.echo(f"  {p}")
    click.echo()

    if not yes:
        if not click.confirm(f"Wrap all {len(discovered)} server(s)?", default=True):
            click.echo("Aborted.")
            sys.exit(0)

    # ------------------------------------------------------------------
    # Step 5: Parallel wrap with ThreadPoolExecutor.
    # ------------------------------------------------------------------
    click.echo(f"\n[Wrap-All] Starting {len(discovered)} job(s) with {workers} worker(s)...\n")

    # Results: list of (name, success, error_msg, duration_secs)
    results: list[tuple[str, bool, str, float]] = []

    def _worker(path: Path) -> tuple[str, bool, str, float]:
        """Thread-pool worker: wrap one server and stream prefixed log lines."""
        server_name = _resolve_server_name(path)

        def _log(msg: str) -> None:
            # Prefix every line with the server name so interleaved output
            # from concurrent workers remains readable.
            click.echo(f"[{server_name}] {msg}")

        _log("scanning ...")
        return _wrap_one(
            path=path,
            name=None,
            platforms=platforms,
            no_health_check=False,
            no_register=False,
            force=force,
            verbose=verbose,
            log=_log,
        )

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_path = {executor.submit(_worker, p): p for p in discovered}
        for future in as_completed(future_to_path):
            try:
                result = future.result()
            except Exception as exc:
                path = future_to_path[future]
                result = (_resolve_server_name(path), False, str(exc), 0.0)
            results.append(result)

    # ------------------------------------------------------------------
    # Step 6: Batch summary report (T030).
    # ------------------------------------------------------------------
    _print_summary(results)

    failed = [r for r in results if not r[1]]
    sys.exit(1 if failed else 0)


# ---------------------------------------------------------------------------
# health command
# ---------------------------------------------------------------------------


@cli.command("health")
@click.argument("server_name", required=False, default=None)
@click.option("--recover", is_flag=True, help="Attempt recovery if unhealthy")
@click.option("--history", is_flag=True, help="Show health history")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def health(
    server_name: str | None,
    recover: bool,
    history: bool,
    json_output: bool,
    verbose: bool,
) -> None:
    """Check health of one or all registered MCP servers.

    Runs L1–L4 checks (container running, protocol responds, tools available,
    response time) for each target server and updates the registry.

    When SERVER_NAME is omitted every registered server is checked.

    Example:

        mcplibrarian health my-server

        mcplibrarian health --recover

        mcplibrarian health my-server --history
    """
    store = RegistryStore()

    # ------------------------------------------------------------------ #
    # Resolve target entries.                                              #
    # ------------------------------------------------------------------ #
    if server_name is not None:
        entry = store.get(server_name)
        if entry is None:
            click.echo(
                f"[ERROR] Server '{server_name}' not found in registry.", err=True
            )
            sys.exit(1)
        entries = [entry]
    else:
        entries = store.list_all()
        if not entries:
            click.echo("[Info] No servers registered. Nothing to check.")
            sys.exit(0)

    # ------------------------------------------------------------------ #
    # --history: display stored history then exit.                        #
    # ------------------------------------------------------------------ #
    if history:
        _print_health_history(entries, json_output)
        sys.exit(0)

    # ------------------------------------------------------------------ #
    # Run health checks.                                                   #
    # ------------------------------------------------------------------ #
    checker = MCPHealthChecker()
    results: list[dict] = []
    any_unhealthy = False

    for entry in entries:
        if verbose:
            click.echo(f"[Health] Checking '{entry.name}' ...")

        try:
            result = checker.check(entry)
        except Exception as exc:
            if verbose:
                traceback.print_exc()
            click.echo(
                f"[WARN] Health check raised an exception for '{entry.name}': {exc}",
                err=True,
            )
            continue

        # Persist to registry.
        try:
            store.update_health(entry.name, result)
        except Exception as exc:
            if verbose:
                click.echo(
                    f"[WARN] Could not update registry for '{entry.name}': {exc}",
                    err=True,
                )

        # Collect for JSON output.
        results.append(
            {
                "server": entry.name,
                "status": result.status.value,
                "container_running": result.container_running,
                "protocol_responds": result.protocol_responds,
                "tools_available": result.tools_available,
                "response_time_ms": result.response_time_ms,
                "error_message": result.error_message,
                "check_time": result.check_time,
            }
        )

        if not json_output:
            _print_health_result(entry.name, result, verbose)

        # Auto-recovery on request.
        if recover and result.status == HealthStatus.unhealthy:
            click.echo(f"  [Recover] Attempting recovery for '{entry.name}' ...")
            try:
                recovered = checker.attempt_recovery(entry)
                click.echo(
                    f"  [Recover] {'succeeded' if recovered else 'failed'} "
                    f"for '{entry.name}'"
                )
            except Exception as exc:
                if verbose:
                    traceback.print_exc()
                click.echo(
                    f"  [Recover] Exception during recovery for '{entry.name}': {exc}",
                    err=True,
                )

        if result.status == HealthStatus.unhealthy:
            any_unhealthy = True

    if json_output:
        click.echo(json.dumps(results, indent=2))

    sys.exit(1 if any_unhealthy else 0)


# ---------------------------------------------------------------------------
# list command (T043)
# ---------------------------------------------------------------------------


@cli.command("list")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--status", "status_filter", default=None, help="Filter by status")
def list_servers(json_output: bool, status_filter: str | None) -> None:
    """List all registered MCP servers with status summary.

    Prints a table showing each server's name, runtime, status, registered
    platforms, and last health check timestamp.

    Example:

        mcplibrarian list

        mcplibrarian list --status wrapped_active

        mcplibrarian list --json
    """
    store = RegistryStore()
    entries = store.list_all()

    # Apply status filter when requested.
    if status_filter is not None:
        entries = [e for e in entries if e.status.value == status_filter]

    if json_output:
        data = [
            {
                "name": e.name,
                "runtime": e.runtime.value,
                "status": e.status.value,
                "platforms": e.registered_platforms,
                "last_health_check": e.health.last_check,
                "last_health_status": e.health.last_status.value,
            }
            for e in entries
        ]
        click.echo(json.dumps(data, indent=2))
        sys.exit(0)

    if not entries:
        click.echo("[Info] No servers registered.")
        sys.exit(0)

    # Compute column widths from data.
    name_w = max(len(e.name) for e in entries)
    name_w = max(name_w, 4)  # minimum width for header "NAME"
    runtime_w = max(len(e.runtime.value) for e in entries)
    runtime_w = max(runtime_w, 7)
    status_w = max(len(e.status.value) for e in entries)
    status_w = max(status_w, 6)
    platforms_w = max(len(", ".join(e.registered_platforms)) for e in entries)
    platforms_w = max(platforms_w, 9)

    header = (
        f"  {'NAME':<{name_w}}  {'RUNTIME':<{runtime_w}}  "
        f"{'STATUS':<{status_w}}  {'PLATFORMS':<{platforms_w}}  LAST HEALTH CHECK"
    )
    click.echo(header)
    click.echo("  " + "-" * (len(header) - 2))

    for e in entries:
        platforms_str = ", ".join(e.registered_platforms) if e.registered_platforms else "—"
        last_health = e.health.last_check or "—"
        click.echo(
            f"  {e.name:<{name_w}}  {e.runtime.value:<{runtime_w}}  "
            f"{e.status.value:<{status_w}}  {platforms_str:<{platforms_w}}  {last_health}"
        )

    sys.exit(0)


# ---------------------------------------------------------------------------
# status command (T044)
# ---------------------------------------------------------------------------


@cli.command("status")
@click.argument("server_name")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def server_status(server_name: str, json_output: bool) -> None:
    """Show detailed status for a single registered MCP server.

    Prints source path, config path, registered platforms, status, health
    summary, and registration date for SERVER_NAME.

    Example:

        mcplibrarian status my-server

        mcplibrarian status my-server --json
    """
    store = RegistryStore()
    entry = store.get(server_name)

    if entry is None:
        click.echo(
            f"[ERROR] Server '{server_name}' not found in registry.", err=True
        )
        sys.exit(1)

    compose_path = (
        entry.container_config.compose_path
        if entry.container_config is not None
        else None
    )

    if json_output:
        data = {
            "name": entry.name,
            "runtime": entry.runtime.value,
            "status": entry.status.value,
            "source_path": entry.source_path,
            "compose_path": compose_path,
            "platforms": entry.registered_platforms,
            "health": {
                "last_check": entry.health.last_check,
                "last_status": entry.health.last_status.value,
                "consecutive_failures": entry.health.consecutive_failures,
                "total_checks": entry.health.total_checks,
            },
            "registered_at": entry.registered_at,
            "last_seen": entry.last_seen,
        }
        click.echo(json.dumps(data, indent=2))
        sys.exit(0)

    click.echo(f"\n[{entry.name}]")
    click.echo(f"  Runtime:              {entry.runtime.value}")
    click.echo(f"  Status:               {entry.status.value}")
    click.echo(f"  Source path:          {entry.source_path}")
    click.echo(f"  Compose path:         {compose_path or '—'}")
    click.echo(f"  Platforms:            {', '.join(entry.registered_platforms) or '—'}")
    click.echo(f"  Last health check:    {entry.health.last_check or '—'}")
    click.echo(f"  Last health status:   {entry.health.last_status.value}")
    click.echo(f"  Consecutive failures: {entry.health.consecutive_failures}")
    click.echo(f"  Total checks:         {entry.health.total_checks}")
    click.echo(f"  Registered at:        {entry.registered_at or '—'}")
    click.echo(f"  Last seen:            {entry.last_seen or '—'}")

    sys.exit(0)


# ---------------------------------------------------------------------------
# remove command (T045)
# ---------------------------------------------------------------------------


@cli.command("remove")
@click.argument("server_name")
@click.option("--keep-config", is_flag=True, help="Keep Docker config files on disk")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def remove_server(server_name: str, keep_config: bool, yes: bool) -> None:
    """Remove a registered MCP server from the registry and platform configs.

    Removes SERVER_NAME from the registry, deregisters it from each platform
    it was registered with, and (unless --keep-config) deletes the generated
    Docker config directory. The original server source directory is never
    touched.

    Example:

        mcplibrarian remove my-server

        mcplibrarian remove my-server --yes

        mcplibrarian remove my-server --keep-config --yes
    """
    store = RegistryStore()
    entry = store.get(server_name)

    if entry is None:
        click.echo(
            f"[ERROR] Server '{server_name}' not found in registry.", err=True
        )
        sys.exit(1)

    # Confirmation prompt unless --yes was supplied.
    if not yes:
        platforms_note = (
            f" and deregister from: {', '.join(entry.registered_platforms)}"
            if entry.registered_platforms
            else ""
        )
        config_note = "" if keep_config else " and delete Docker config files"
        if not click.confirm(
            f"Remove '{server_name}' from registry{platforms_note}{config_note}?",
            default=False,
        ):
            click.echo("Aborted.")
            sys.exit(0)

    # Deregister from each platform.
    for pid in entry.registered_platforms:
        try:
            platform_obj = get_platform(pid)
            platform_obj.remove_server(server_name)
            click.echo(f"[Platform] Removed '{server_name}' from '{pid}'.")
        except Exception as exc:
            click.echo(
                f"[WARN] Could not remove '{server_name}' from platform '{pid}': {exc}",
                err=True,
            )

    # Remove from registry.
    store.remove(server_name)
    click.echo(f"[Registry] Removed '{server_name}' from registry.")

    # Delete config directory unless --keep-config.
    if not keep_config:
        config_dir = _config_dir(Path(entry.source_path), server_name)
        if config_dir.exists():
            import shutil

            try:
                shutil.rmtree(config_dir)
                click.echo(f"[Config]   Deleted config directory: {config_dir}")
            except Exception as exc:
                click.echo(
                    f"[WARN] Could not delete config directory '{config_dir}': {exc}",
                    err=True,
                )
        else:
            click.echo(f"[Config]   Config directory not found (skipping): {config_dir}")
    else:
        click.echo("[Config]   Kept config files (--keep-config).")

    sys.exit(0)


# ---------------------------------------------------------------------------
# scan command (T046)
# ---------------------------------------------------------------------------


@cli.command("scan")
@click.argument("path", type=click.Path(exists=True))
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--fix", is_flag=True, help="Apply auto-fixes without building")
def scan_server(path: str, json_output: bool, fix: bool) -> None:
    """Run Smart-Scan analysis on a server directory without building.

    Detects runtime, entry point, environment variables, and data volumes.
    Reports each issue with its severity and fix instruction. Optionally
    applies auto-fixes (--fix) without proceeding to the Docker build step.

    Exits 0 if no blocking issues remain, 1 if blocking issues are present.

    Example:

        mcplibrarian scan /home/user/my-mcp-server

        mcplibrarian scan /home/user/my-mcp-server --fix

        mcplibrarian scan /home/user/my-mcp-server --json
    """
    server_path = Path(path).resolve()

    # Run Smart-Scan.
    try:
        result = SmartScan(server_path).run()
    except FileNotFoundError as exc:
        click.echo(f"[ERROR] {exc}", err=True)
        sys.exit(1)
    except Exception as exc:
        click.echo(f"[ERROR] Scan failed: {exc}", err=True)
        sys.exit(1)

    # Apply auto-fixes when requested, then re-run the scan so issues that
    # were fixed no longer appear in the final output.
    fixes_applied: list[dict] = []
    if fix:
        raw_fixes = AutoFixer(result).fix_all()
        fixes_applied = [
            {
                "issue_type": f.issue_type.value,
                "description": f.description,
                "files_modified": f.files_modified,
                "success": f.success,
                "error": f.error,
            }
            for f in raw_fixes
        ]
        # Re-scan so blocking status reflects the post-fix state.
        try:
            result = SmartScan(server_path).run()
        except Exception:
            pass  # Use the original result if re-scan fails.

    blocking_issues = [i for i in result.issues if i.severity == Severity.blocking]

    if json_output:
        data = {
            "server_path": result.server_path,
            "runtime": result.runtime,
            "runtime_version": result.runtime_version,
            "entry_point": result.entry_point,
            "package_manager": result.package_manager,
            "env_vars": result.env_vars,
            "data_volumes": result.data_volumes,
            "deployment_pattern": result.deployment_pattern,
            "issues": [
                {
                    "issue_type": i.issue_type.value,
                    "severity": i.severity.value,
                    "description": i.description,
                    "auto_fixable": i.auto_fixable,
                    "fix_instruction": i.fix_instruction,
                    "affected_path": i.affected_path,
                }
                for i in result.issues
            ],
            "fixes_applied": fixes_applied,
            "blocking_issues_remain": len(blocking_issues) > 0,
        }
        click.echo(json.dumps(data, indent=2))
        sys.exit(1 if blocking_issues else 0)

    # Human-readable output.
    click.echo(f"\n[Scan] {server_path}")
    click.echo(f"  Runtime:            {result.runtime}")
    click.echo(f"  Runtime version:    {result.runtime_version or '—'}")
    click.echo(f"  Entry point:        {result.entry_point or '—'}")
    click.echo(f"  Package manager:    {result.package_manager or '—'}")
    click.echo(f"  Deployment pattern: {result.deployment_pattern or '—'}")

    if result.env_vars:
        click.echo(f"  Env vars:           {', '.join(result.env_vars)}")
    else:
        click.echo("  Env vars:           (none detected)")

    if result.data_volumes:
        click.echo(f"  Data volumes:       {', '.join(result.data_volumes)}")
    else:
        click.echo("  Data volumes:       (none detected)")

    if result.issues:
        click.echo(f"\n  Issues ({len(result.issues)} found):")
        click.echo(f"  {'SEVERITY':<10}  {'TYPE':<28}  {'FIX':<5}  DESCRIPTION")
        click.echo("  " + "-" * 80)
        for issue in result.issues:
            fixable = "yes" if issue.auto_fixable else "no"
            click.echo(
                f"  {issue.severity.value:<10}  {issue.issue_type.value:<28}  "
                f"{fixable:<5}  {issue.description}"
            )
            if issue.fix_instruction:
                click.echo(f"               -> {issue.fix_instruction}")
    else:
        click.echo("\n  Issues: none")

    if fixes_applied:
        click.echo(f"\n  Fixes applied ({len(fixes_applied)}):")
        for f in fixes_applied:
            status = "ok" if f["success"] else f"FAILED: {f['error']}"
            click.echo(f"    {f['issue_type']}: {status}")
            for modified in f["files_modified"]:
                click.echo(f"      modified: {modified}")

    if blocking_issues:
        click.echo(
            f"\n[WARN] {len(blocking_issues)} blocking issue(s) remain — "
            "resolve before wrapping."
        )

    sys.exit(1 if blocking_issues else 0)


# ---------------------------------------------------------------------------
# health command helpers
# ---------------------------------------------------------------------------


def _print_health_result(name: str, result, verbose: bool) -> None:
    """Print a single server's L1–L4 health result in human-readable form."""
    tick = "\u2713"  # checkmark
    cross = "\u2717"  # cross

    click.echo(f"\n[{name}]")
    click.echo(f"  L1 Container running:  {tick if result.container_running else cross}")
    click.echo(f"  L2 Protocol responds:  {tick if result.protocol_responds else cross}")
    click.echo(f"  L3 Tools available:    {tick if result.tools_available else cross}")
    click.echo(f"  L4 Response time:      {result.response_time_ms:.0f}ms")
    click.echo(f"  Status: {result.status.value}")
    if result.error_message and (not result.container_running or verbose):
        click.echo(f"  Error: {result.error_message}")


def _print_health_history(
    entries: list,
    json_output: bool,
) -> None:
    """Print the last 24 h of health history for each entry (T041).

    For JSON output, emit an array of objects keyed by server name.
    For text output, print a table per server.
    """
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=24)
    json_data: list[dict] = []

    for entry in entries:
        # Filter history to last 24 h (up to 24 entries).
        recent: list = []
        for record in entry.health_history:
            # check_time is stored as an ISO-8601 string.
            try:
                ts_raw: str = record.check_time
                # Handle both aware and naive ISO strings.
                if ts_raw.endswith("Z"):
                    ts_raw = ts_raw[:-1] + "+00:00"
                ts = datetime.fromisoformat(ts_raw)
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= cutoff:
                    recent.append((ts, record))
            except (ValueError, AttributeError):
                # Skip malformed timestamps; include everything else.
                recent.append((None, record))

        # Limit to last 24 entries chronologically.
        recent = recent[-24:]

        if json_output:
            json_data.append(
                {
                    "server": entry.name,
                    "history": [
                        {
                            "timestamp": (
                                ts.isoformat() if ts is not None else record.check_time
                            ),
                            "status": record.status.value,
                            "response_time_ms": record.response_time_ms,
                        }
                        for ts, record in recent
                    ],
                }
            )
        else:
            click.echo(f"\n[{entry.name}] — last 24 h")
            if not recent:
                click.echo("  (no history in last 24 h)")
                continue
            click.echo(f"  {'Timestamp':<20}  {'Status':<14}  {'Response Time':>14}")
            click.echo("  " + "-" * 54)
            for ts, record in recent:
                ts_str = (
                    ts.strftime("%Y-%m-%d %H:%M")
                    if ts is not None
                    else record.check_time[:16]
                )
                rt_str = (
                    f"{record.response_time_ms:.0f}ms"
                    if record.response_time_ms > 0
                    else "—"
                )
                click.echo(
                    f"  {ts_str:<20}  {record.status.value:<14}  {rt_str:>14}"
                )

    if json_output:
        click.echo(json.dumps(json_data, indent=2))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_server_name(path: Path) -> str:
    """Return the effective server name for *path* without running a full scan.

    Mirrors the name-resolution logic in ``_wrap_one``: uses the directory
    name as a cheap stand-in for the skip-existing and display steps.
    The full scan inside ``_wrap_one`` may produce a different name when
    an entry point is found, but for filtering purposes the directory name
    is sufficient.
    """
    return path.name


def _wrap_one(
    path: Path,
    name: str | None,
    platforms: tuple[str, ...],
    no_health_check: bool,
    no_register: bool,
    force: bool,
    verbose: bool,
    log=click.echo,
) -> tuple[str, bool, str, float]:
    """Run the full wrap pipeline for a single server directory.

    This function contains the core logic previously inlined inside the
    ``wrap`` Click command.  Both ``wrap`` and ``wrap-all`` delegate here so
    the behaviour is identical regardless of whether wrapping is performed
    sequentially or in parallel.

    Parameters
    ----------
    path:
        Absolute path to the server directory.
    name:
        Optional name override; mirrors the ``--name`` flag on ``wrap``.
    platforms:
        Tuple of platform IDs to register with.
    no_health_check:
        When ``True``, skip the health-check step.
    no_register:
        When ``True``, skip writing to the registry.
    force:
        When ``True``, proceed past blocking issues and unknown runtimes.
    verbose:
        When ``True``, emit additional diagnostic lines via *log*.
    log:
        Callable used for all output (default: ``click.echo``).  ``wrap-all``
        passes a prefixed version so concurrent output is readable.

    Returns
    -------
    tuple[str, bool, str, float]
        ``(server_name, success, error_message, duration_seconds)``
        On success ``error_message`` is an empty string.
    """
    start = time.monotonic()

    # ------------------------------------------------------------------ #
    # Step 1: [Scan]                                                       #
    # ------------------------------------------------------------------ #
    log(f"[Scan] Analysing {path} ...")
    try:
        scan_result = SmartScan(path).run()
    except FileNotFoundError as exc:
        msg = f"Path not found: {exc}  → Verify the server path exists"
        log(f"[ERROR] {msg}")
        return (name or path.name, False, msg, time.monotonic() - start)
    except Exception as exc:
        msg = f"Scan failed: {exc}"
        if verbose:
            traceback.print_exc()
        return (name or path.name, False, msg, time.monotonic() - start)

    if verbose:
        log(
            f"  runtime={scan_result.runtime}  version={scan_result.runtime_version}"
            f"  entry={scan_result.entry_point}"
        )

    # ------------------------------------------------------------------ #
    # Step 2: Print issues; abort on blocking issues unless --force.       #
    # ------------------------------------------------------------------ #
    blocking_found = False
    for issue in scan_result.issues:
        severity_tag = issue.severity.value.upper()
        log(f"  [{severity_tag}] {issue.description}")
        if issue.fix_instruction:
            log(f"    -> {issue.fix_instruction}")
        if issue.severity == Severity.blocking:
            blocking_found = True

    if blocking_found and not force:
        msg = (
            "Blocking issues found — cannot proceed.  "
            "Fix the issues above, or re-run with --force to skip."
        )
        log(f"[ERROR] {msg}")
        return (name or path.name, False, msg, time.monotonic() - start)

    if scan_result.runtime == "unknown" and not force:
        msg = (
            "Unknown runtime — no recognised MCP server detected.  "
            "Ensure the directory contains pyproject.toml (Python) "
            "or package.json with @modelcontextprotocol/sdk (Node.js)."
        )
        log(f"[ERROR] {msg}")
        return (name or path.name, False, msg, time.monotonic() - start)

    # ------------------------------------------------------------------ #
    # Step 3: [Fix]                                                        #
    # ------------------------------------------------------------------ #
    log("[Fix] Applying auto-fixes ...")
    try:
        fixes = AutoFixer(scan_result).fix_all()
    except Exception as exc:
        msg = f"AutoFixer failed: {exc}"
        if verbose:
            traceback.print_exc()
        return (name or path.name, False, msg, time.monotonic() - start)

    for fix in fixes:
        status = "ok" if fix.success else f"FAILED: {fix.error}"
        log(f"  {fix.issue_type.value}: {status}")
        if fix.files_modified:
            for f in fix.files_modified:
                log(f"    modified: {f}")

    # ------------------------------------------------------------------ #
    # Resolve effective server name and output directory.                  #
    # ------------------------------------------------------------------ #
    effective_name: str = name or scan_result.runtime  # fallback: runtime name
    if scan_result.entry_point:
        effective_name = name or Path(scan_result.entry_point).stem
    if not effective_name:
        effective_name = path.name

    output_dir = _config_dir(path, effective_name)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Step 4: [Generate]                                                   #
    # ------------------------------------------------------------------ #
    log(f"[Generate] Writing Docker configs to {output_dir} ...")
    try:
        from .smart_scan.scanner import _DETECTORS as _REGISTERED_DETECTORS

        metadata = None
        for detector in _REGISTERED_DETECTORS:
            try:
                if detector.can_detect(path):
                    metadata = detector.detect(path)
                    break
            except Exception:
                continue

        if metadata is None:
            from .detectors.base import ServerMetadata

            metadata = ServerMetadata(
                name=effective_name,
                runtime=scan_result.runtime,
                runtime_version=scan_result.runtime_version,
                entry_point=scan_result.entry_point,
                package_manager=scan_result.package_manager,
                env_vars=scan_result.env_vars,
                data_volumes=scan_result.data_volumes,
                deployment_pattern=scan_result.deployment_pattern,
            )

        metadata.name = effective_name

        dockerfile_path = DockerfileGenerator().generate(metadata, output_dir, path)
        compose_path = ComposeGenerator().generate(
            metadata=metadata,
            config_dir=output_dir,
            server_path=path,
        )
    except Exception as exc:
        msg = f"Generation failed: {exc}"
        if verbose:
            traceback.print_exc()
        return (effective_name, False, msg, time.monotonic() - start)

    if verbose:
        log(f"  Dockerfile: {dockerfile_path}")
        log(f"  compose:    {compose_path}")

    # ------------------------------------------------------------------ #
    # Step 5: [Build]                                                      #
    # ------------------------------------------------------------------ #
    log("[Build] Building Docker image ...")
    try:
        builder = DockerBuilder(verbose=verbose)
        image_id = builder.build_image(output_dir, metadata)
        log(f"  image id: {image_id[:12]}")
    except DockerBuildError as exc:
        msg = f"Build failed: {exc}  → Check Dockerfile and dependencies"
        log(f"[ERROR] {msg}")
        return (effective_name, False, msg, time.monotonic() - start)
    except Exception as exc:
        msg = f"Build step failed: {exc}"
        if verbose:
            traceback.print_exc()
        return (effective_name, False, msg, time.monotonic() - start)

    # ------------------------------------------------------------------ #
    # Build the RegistryEntry.                                             #
    # ------------------------------------------------------------------ #
    try:
        runtime_enum = Runtime(scan_result.runtime)
    except ValueError:
        runtime_enum = Runtime.unknown

    entry = RegistryEntry(
        name=effective_name,
        runtime=runtime_enum,
        source_path=str(path),
        status=ServerStatus.wrapped_active,
        registered_platforms=list(platforms),
        container_config=ContainerConfig(
            compose_path=str(compose_path),
            dockerfile_path=str(output_dir / "Dockerfile"),
            image_name=f"mcp-{effective_name}:latest",
            build_context=str(output_dir),
        ),
    )

    # ------------------------------------------------------------------ #
    # Step 6: [Health]                                                     #
    # ------------------------------------------------------------------ #
    if not no_health_check:
        log("[Health] Running health check ...")
        try:
            health_result = MCPHealthChecker().check(entry)
            log(f"  status: {health_result.status.value}")
            if health_result.status == HealthStatus.healthy:
                entry.status = ServerStatus.wrapped_active
            else:
                entry.status = ServerStatus.wrapped_stopped
                if health_result.error_message:
                    log(f"  note: {health_result.error_message}")
        except Exception as exc:
            if verbose:
                traceback.print_exc()
            log(f"[WARN] Health check failed: {exc}  (continuing to registration)")
            entry.status = ServerStatus.wrapped_stopped
    else:
        log("[Health] Skipped (--no-health-check)")

    # ------------------------------------------------------------------ #
    # Step 7: [Register]                                                   #
    # ------------------------------------------------------------------ #
    if not no_register:
        log("[Register] Adding to registry ...")
        try:
            RegistryStore().add(entry)
            log(f"  registered: {effective_name}")
        except Exception as exc:
            msg = f"Registry write failed: {exc}"
            if verbose:
                traceback.print_exc()
            return (effective_name, False, msg, time.monotonic() - start)
    else:
        log("[Register] Skipped (--no-register)")

    # ------------------------------------------------------------------ #
    # Step 8: [Platform]                                                   #
    # ------------------------------------------------------------------ #
    for pid in platforms:
        log(f"[Platform] Registering with '{pid}' ...")
        try:
            platform_obj = get_platform(pid)
            platform_obj.add_server(entry, compose_path)
            log(f"  config updated: {platform_obj.config_path}")
        except ValueError as exc:
            msg = (
                f"Unknown platform: {exc}  "
                f"→ Valid platforms: {', '.join(VALID_PLATFORMS)}"
            )
            log(f"[ERROR] {msg}")
            return (effective_name, False, msg, time.monotonic() - start)
        except Exception as exc:
            msg = f"Platform '{pid}' registration failed: {exc}"
            if verbose:
                traceback.print_exc()
            return (effective_name, False, msg, time.monotonic() - start)

    log(f"[Done] Docker configs in: {output_dir}")
    return (effective_name, True, "", time.monotonic() - start)


def _print_summary(results: list[tuple[str, bool, str, float]]) -> None:
    """Print the batch wrap-all summary table after all workers complete.

    Each row shows: status icon, server name, duration.
    Failures are listed again below the table with their error messages.

    Parameters
    ----------
    results:
        List of ``(server_name, success, error_msg, duration_secs)`` tuples
        returned by ``_wrap_one``.
    """
    click.echo("\n" + "=" * 60)
    click.echo("  Batch wrap-all summary")
    click.echo("=" * 60)

    name_width = max((len(r[0]) for r in results), default=20)
    header = f"  {'Server':<{name_width}}  {'Status':<8}  {'Duration':>10}"
    click.echo(header)
    click.echo("  " + "-" * (name_width + 24))

    failures: list[tuple[str, str]] = []
    for server_name, success, error_msg, duration in sorted(results, key=lambda r: r[0]):
        icon = "v" if success else "x"
        status_label = "ok" if success else "FAILED"
        dur_str = f"{duration:.1f}s"
        click.echo(f"  {icon} {server_name:<{name_width}}  {status_label:<8}  {dur_str:>10}")
        if not success:
            failures.append((server_name, error_msg))

    click.echo("=" * 60)

    total = len(results)
    n_ok = sum(1 for r in results if r[1])
    click.echo(f"  {n_ok}/{total} succeeded")

    if failures:
        click.echo("\nFailures:")
        for server_name, error_msg in failures:
            click.echo(f"  [{server_name}] {error_msg}")

    click.echo()


def _config_dir(server_path_abs: Path, server_name: str) -> Path:
    """Return the output directory for a server's generated Docker configs.

    Stored alongside the registry at:
    ``~/.config/mcp-librarian/servers/<name>/``
    """
    return Path.home() / ".config" / "mcp-librarian" / "servers" / server_name


def _print_error(summary: str, exc: Exception, verbose: bool) -> None:
    """Print a formatted error message, optionally including the full traceback."""
    click.echo(f"[ERROR] {summary}: {exc}\n  → See --verbose for details", err=True)
    if verbose:
        traceback.print_exc()


def main():
    """Legacy entry point — delegates to cli group."""
    cli()


if __name__ == "__main__":
    cli()
