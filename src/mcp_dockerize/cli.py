#!/usr/bin/env python3
"""CLI interface for mcplibrarian."""

import json
import sys
from pathlib import Path

import click

from .detectors.python import PythonDetector
from .generators.dockerfile import DockerfileGenerator


@click.group()
@click.version_option()
def cli():
    """mcplibrarian — Containerize MCP servers for on-demand loading."""
    pass


@cli.command("wrap")
@click.argument("server_path", type=click.Path(exists=True))
@click.option("-o", "--output", default="./docker-configs", help="Output directory for Docker configs")
@click.option("-n", "--name", default=None, help="Container name (auto-detected if not provided)")
@click.option("--platform", default="claude_code",
              help="Target platform (claude_code, cursor, vscode, goose, codex, opencode)")
@click.option("--build", is_flag=True, help="Build Docker image after generation")
@click.option("--test", is_flag=True, help="Test container after building")
@click.option("--no-health-check", is_flag=True, help="Skip health check after build")
@click.option("--no-register", is_flag=True, help="Skip registry registration")
@click.option("--force", is_flag=True, help="Force re-wrap even if already registered")
@click.option("--dry-run", is_flag=True, help="Show what would be done without doing it")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
def wrap(server_path, output, name, platform, build, test, no_health_check, no_register, force, dry_run, verbose):
    """Containerize an MCP server for on-demand loading.

    Auto-detects runtime, generates Docker configs, builds container,
    and registers with the target AI platform.

    Example:
        mcplibrarian wrap /home/user/my-mcp-server
        mcplibrarian wrap /home/user/my-mcp-server --platform cursor
    """
    if dry_run:
        click.echo(f"[DRY RUN] Would wrap: {server_path}")
        click.echo(f"[DRY RUN] Output dir: {Path(output) / (name or Path(server_path).name)}")
        click.echo(f"[DRY RUN] Platform: {platform}")
        return

    click.echo(f"🔍 Analyzing MCP server at: {server_path}")

    detector = PythonDetector()

    if not detector.can_detect(server_path):
        click.echo("[ERROR] Not a recognised MCP server", err=True)
        click.echo("  → Currently supported: Python (pyproject.toml) and Node.js (package.json)", err=True)
        sys.exit(1)

    try:
        metadata = detector.detect(server_path)

        if verbose:
            click.echo(f"\n📊 Server Metadata:")
            click.echo(f"   Type: {metadata.server_type}")
            click.echo(f"   Entry: {metadata.entry_point}")
            click.echo(f"   Python: {metadata.python_version}")
            click.echo(f"   Dependencies: {len(metadata.dependencies)} packages")

        generator = DockerfileGenerator()
        output_dir = Path(output) / (name or metadata.name)
        output_dir.mkdir(parents=True, exist_ok=True)

        server_path_abs = Path(server_path).resolve()

        dockerfile_path = generator.generate(metadata, output_dir, server_path_abs)
        click.echo(f"\n✅ Generated Dockerfile: {dockerfile_path}")

        if build:
            click.echo("\n🐳 Building Docker image...")
            try:
                from .builders.docker_builder import DockerBuildError, DockerBuilder

                builder = DockerBuilder(verbose=verbose)
                image_id = builder.build_image(output_dir, metadata)
                click.echo(f"   ✅ Image built: {image_id[:12]}")

            except DockerBuildError as e:
                click.echo(f"[ERROR] Build failed: {e}", err=True)
                click.echo("  → Check Dockerfile and dependencies", err=True)
                if not test:
                    sys.exit(1)

        if test:
            click.echo("\n🧪 Testing container...")
            try:
                from .testers.mcp_tester import MCPTestError, MCPTester

                tester = MCPTester(verbose=verbose)
                result = tester.test_container(output_dir, metadata, timeout_seconds=30)

                if result.success:
                    click.echo(f"   ✅ Test passed ({result.duration_ms:.0f}ms)")
                    if verbose and result.response:
                        click.echo(f"   Response: {json.dumps(result.response, indent=2)}")
                else:
                    click.echo(f"[ERROR] Test failed: {result.message}", err=True)
                    click.echo(f"  → {result.error}", err=True)
                    sys.exit(1)

            except MCPTestError as e:
                click.echo(f"[ERROR] Test setup failed: {e}", err=True)
                sys.exit(1)

        click.echo(f"\n🎉 Done! Docker configs in: {output_dir}")

    except Exception as e:
        click.echo(f"[ERROR] {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Legacy entry point — delegates to cli group."""
    cli()


if __name__ == "__main__":
    cli()
