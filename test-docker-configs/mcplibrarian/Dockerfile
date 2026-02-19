# Python UV-based Dockerfile Template
# For self-contained MCP servers (snowflake, mariadb, etc.)
# Code is copied into container, dependencies installed with uv

FROM python:3.10-slim AS builder

WORKDIR /build

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml ./

COPY mcplibrarian ./mcplibrarian

# Install dependencies with uv
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install --no-cache .

# Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy source code

COPY mcplibrarian ./mcplibrarian

# Create non-root user for security
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app

# Environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER mcp

# Entry point (console script from pyproject.toml)
ENTRYPOINT ["mcplibrarian"]