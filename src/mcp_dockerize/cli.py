#!/usr/bin/env python3
"""CLI interface for mcplibrarian."""

import click
import json
import os
import sys
from pathlib import Path

from .detectors.python import PythonDetector
from .generators.dockerfile import DockerfileGenerator


@click.command()
@click.argument("server_path", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    default="./docker-configs",
    help="Output directory for Docker configs"
)
@click.option(
    "-n", "--name",
    default=None,
    help="Container name (auto-detected if not provided)"
)
@click.option(
    "--build",
    is_flag=True,
    help="Build Docker image after generation"
)
@click.option(
    "--test",
    is_flag=True,
    help="Test container after building"
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Verbose output"
)
def main(server_path, output, name, build, test, verbose):
    """Auto-dockerize an MCP server.

    Detects server type, generates optimized Dockerfile,
    handles credentials securely, and outputs Claude Code config.

    Example:
        mcplibrarian /home/user/my-mcp-server
    """
    click.echo(f"🔍 Analyzing MCP server at: {server_path}")

    # Detect server type
    detector = PythonDetector()

    if not detector.can_detect(server_path):
        click.echo("❌ Not a Python FastMCP server", err=True)
        click.echo("   Currently only Python FastMCP servers are supported", err=True)
        sys.exit(1)

    try:
        metadata = detector.detect(server_path)

        if verbose:
            click.echo(f"\n📊 Server Metadata:")
            click.echo(f"   Type: {metadata.server_type}")
            click.echo(f"   Entry: {metadata.entry_point}")
            click.echo(f"   Python: {metadata.python_version}")
            click.echo(f"   Dependencies: {len(metadata.dependencies)} packages")

        # Generate Dockerfile
        generator = DockerfileGenerator()
        output_dir = Path(output) / (name or metadata.name)
        output_dir.mkdir(parents=True, exist_ok=True)

        server_path_abs = Path(server_path).resolve()
        if verbose:
            click.echo(f"\n🔍 Server path (absolute): {server_path_abs}")

        dockerfile_path = generator.generate(metadata, output_dir, server_path_abs)

        click.echo(f"\n✅ Generated Dockerfile: {dockerfile_path}")

        if build:
            click.echo(f"\n🐳 Building Docker image...")
            try:
                from .builders.docker_builder import DockerBuilder, DockerBuildError

                builder = DockerBuilder(verbose=verbose)
                image_id = builder.build_image(output_dir, metadata)
                click.echo(f"   ✅ Image built successfully: {image_id[:12]}")

            except DockerBuildError as e:
                click.echo(f"   ❌ Build failed: {e}", err=True)
                if not test:
                    sys.exit(1)

        if test:
            click.echo(f"\n🧪 Testing container...")
            try:
                from .testers.mcp_tester import MCPTester, MCPTestError

                tester = MCPTester(verbose=verbose)
                result = tester.test_container(output_dir, metadata, timeout_seconds=30)

                if result.success:
                    click.echo(f"   ✅ Test passed ({result.duration_ms:.0f}ms)")
                    if verbose and result.response:
                        click.echo(f"   Response: {json.dumps(result.response, indent=2)}")
                else:
                    click.echo(f"   ❌ Test failed: {result.message}", err=True)
                    if result.error:
                        click.echo(f"      Error: {result.error}", err=True)
                    sys.exit(1)

            except MCPTestError as e:
                click.echo(f"   ❌ Test setup failed: {e}", err=True)
                sys.exit(1)

        click.echo(f"\n🎉 Success! Docker configs in: {output_dir}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
