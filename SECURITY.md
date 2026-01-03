# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: [your-email@example.com]

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information:
- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the issue
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Security Considerations

### Docker Security
- All containers run with minimal privileges
- No --privileged flag used
- Host mounts are read-only where possible
- Environment variables for secrets (not hardcoded)

### MCP Protocol Security
- stdio communication (not network exposed by default)
- No authentication bypass in proxy
- Container isolation prevents cross-server access

### Dependency Security
- Regular dependency updates
- Use of official Python/Node base images
- Minimal attack surface (slim images)

## Best Practices for Users

1. **Environment Variables**
   - Never commit .env files
   - Use Docker secrets for production
   - Rotate API keys regularly

2. **Container Images**
   - Review Dockerfiles before building
   - Scan images for vulnerabilities
   - Use specific version tags, not :latest

3. **Network Isolation**
   - Don't expose containers to public networks
   - Use Docker networks for inter-container communication
   - Keep MCP proxy on localhost only

4. **Volume Mounts**
   - Mount only necessary directories
   - Use read-only mounts where possible
   - Avoid mounting /

5. **Registry Security**
   - Protect mcp-docker-registry.json
   - Limit write access
   - Validate entries before adding

## Known Security Considerations

### Tool Execution
MCP tools execute code on your system. Always:
- Review tool source code before dockerizing
- Understand what tools do
- Limit permissions where possible
- Use container resource limits

### Proxy Server
The mcp-proxy.py server:
- Runs with your user permissions
- Has access to Docker socket
- Can start/stop containers
- Should not be exposed to network

## Updates and Patches

Security updates will be released as:
- Patch versions (1.0.x) for security fixes
- Announced via GitHub Security Advisories
- Published in CHANGELOG.md

Subscribe to GitHub notifications for security updates.

---

*Last Updated: 2026-01-03*
