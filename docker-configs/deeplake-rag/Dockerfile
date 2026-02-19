# Python Direct Execution Dockerfile Template
# For volume-mounted MCP servers (deeplake, etc.)
# Code is mounted from host, dependencies installed in container

FROM python:3.10-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# Install pip and dependencies

# Install dependencies from pyproject.toml
RUN pip install --no-cache-dir mcp[cli]>=0.1.0 fastapi>=0.104.0 uvicorn>=0.24.0 pydantic>=2.4.2 deeplake>=4.0.0 openai>=1.0.0 python-dotenv>=1.0.0 numpy>=1.24.0 fuzzywuzzy>=0.18.0 python-levenshtein>=0.27.1 rapidfuzz>=3.14.0 


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
ENTRYPOINT ["python", "main.py"]