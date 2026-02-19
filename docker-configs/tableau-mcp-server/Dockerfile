# Python Direct Execution Dockerfile Template
# For volume-mounted MCP servers (deeplake, etc.)
# Code is mounted from host, dependencies installed in container

FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Install pip and dependencies

# Install dependencies from pyproject.toml
RUN pip install --no-cache-dir fastmcp>=2.0.0 aiohttp>=3.9.0 pydantic>=2.0.0 pyyaml>=6.0 tableauserverclient>=0.30.0 python-dotenv>=1.0.0 json-log-formatter>=0.5.0 pyjwt>=2.8.0 aiofiles>=25.1.0 


# Also install thefuzz (modern replacement for fuzzywuzzy)
RUN pip install --no-cache-dir thefuzz

# Create non-root user for security
RUN useradd -m -u 1000 mcp && \
    mkdir -p /app /data /keys /media /mnt && \
    chown -R mcp:mcp /app /data /keys

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

USER mcp

# Entry point (direct Python execution)
# Code will be mounted at runtime via volume
ENTRYPOINT ["python", "src/server.py"]