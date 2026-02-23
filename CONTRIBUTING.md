# Contributing to MCP Dockerize

Thank you for your interest in contributing to MCP Dockerize! This document provides guidelines and instructions for contributing.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Submitting Changes](#submitting-changes)
8. [Community](#community)

---

## Code of Conduct

This project follows a Code of Conduct. By participating, you agree to:

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the best outcome for the community
- Show empathy towards other contributors

---

## Getting Started

### What Can You Contribute?

- **Bug fixes** - Fix issues in the automation script
- **New features** - Add support for new server types
- **Documentation** - Improve guides and examples
- **Examples** - Add real-world dockerization examples
- **Testing** - Add test cases for edge cases
- **Performance** - Optimize tool extraction or routing

### Current Priorities

See [GitHub Issues](https://github.com/yourusername/mcp-dockerize/issues) for:
- Labeled `good first issue` - Easy entry points
- Labeled `help wanted` - Community contributions needed
- Labeled `enhancement` - New feature ideas

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/mcp-dockerize.git
cd mcp-dockerize
```

### 2. Create Development Environment

```bash
# Using UV (recommended)
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
uv pip install -e ".[dev]"
```

### 3. Verify Setup

```bash
# Run the script
python mcp-dockerize.py --help

# Should show usage information
```

---

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-typescript-support`
- `fix/tool-extraction-timeout`
- `docs/improve-quickstart`

```bash
git checkout -b feature/your-feature-name
```

### Code Style

We use **Black** for code formatting:

```bash
# Format code
black mcp-dockerize.py scripts/

# Check formatting
black --check mcp-dockerize.py
```

### Type Checking

We use **mypy** for type checking:

```bash
mypy mcp-dockerize.py scripts/
```

---

## Testing

### Manual Testing Checklist

Before submitting, test your changes with:

1. **Python server with pyproject.toml**
   ```bash
   python mcp-dockerize.py ~/path/to/python-server/
   ```

2. **Python server with requirements.txt**
   ```bash
   python mcp-dockerize.py ~/path/to/legacy-server/
   ```

3. **Node.js server**
   ```bash
   python mcp-dockerize.py ~/path/to/node-server/
   ```

4. **Validation test**
   ```bash
   python mcp-dockerize.py ~/path/to/server/ --no-validate
   # Should complete without validation
   ```

### Expected Output

✅ Dockerfile generated
✅ docker-compose.yml generated
✅ Manifest with tool schemas created
✅ Registry entry added
✅ Routing rules template created
✅ Container builds successfully
✅ MCP handshake succeeds

### Automated Tests (Future)

```bash
# Run tests (when implemented)
pytest tests/

# With coverage
pytest --cov=mcp_dockerize tests/
```

---

## Documentation

### Documentation Files

- **README.md** - Main documentation with decision tree
- **QUICK_START.md** - 5-minute quickstart guide
- **docs/MCP_DOCKERIZE_GUIDE.md** - Automated path guide
- **docs/MANUAL_DOCKERIZATION_GUIDE.md** - Manual path guide

### Documentation Standards

When updating docs:

1. **Keep both paths equal** - Automated and manual must be equally documented
2. **Use clear examples** - Show real commands and expected output
3. **Add troubleshooting** - Document common issues and solutions
4. **Update token counts** - Keep token savings measurements current

### Adding Examples

Add new examples to `examples/`:

```bash
examples/
├── gemini-server/          # Example: Python server
├── playwright-server/      # Example: Node.js server
└── your-new-example/       # Your contribution
```

Each example should include:
- `README.md` - What this example demonstrates
- Original server code (if shareable)
- Generated Dockerfile
- Generated docker-compose.yml
- Lessons learned

---

## Submitting Changes

### Pull Request Process

1. **Update documentation** - If behavior changes
2. **Test thoroughly** - Manual testing checklist
3. **Format code** - Run Black
4. **Type check** - Run mypy
5. **Write clear commit messages**:
   ```
   Add TypeScript server support

   - Detect tsconfig.json for TypeScript projects
   - Generate Dockerfile with build step
   - Add compilation to docker-compose.yml
   - Update documentation with TypeScript example
   ```

6. **Create pull request** with:
   - Clear title
   - Description of changes
   - Testing performed
   - Screenshots (if applicable)

### PR Checklist

- [ ] Code formatted with Black
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] Examples added (if new feature)
- [ ] Tested manually with 3+ server types
- [ ] Commit messages are descriptive

---

## Community

### Getting Help

- **GitHub Discussions** - Ask questions, share ideas
- **GitHub Issues** - Report bugs, request features
- **Documentation** - Read the guides first

### Recognition

Contributors will be:
- Listed in [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Mentioned in release notes
- Credited in documentation

---

## Areas That Need Help

### High Priority

1. **TypeScript server support** - Detect and build TypeScript servers
2. **Go server support** - Add Go MCP server detection
3. **Rust server support** - Add Rust MCP server detection
4. **Automated testing** - Build pytest test suite
5. **Performance optimization** - Speed up tool extraction

### Medium Priority

1. **CI/CD pipeline** - GitHub Actions for testing
2. **Docker Hub images** - Pre-built base images
3. **Template library** - Common server templates
4. **Migration tool** - Convert existing Docker setups
5. **Monitoring integration** - Add health checks

### Documentation Needs

1. **Video tutorials** - Screen recordings of workflow
2. **Blog posts** - Deep dives into patterns
3. **Migration guides** - From other solutions
4. **Comparison matrix** - vs alternatives
5. **FAQ section** - Common questions

---

## Development Workflow

### Typical Contribution Flow

```bash
# 1. Sync with upstream
git checkout main
git pull upstream main

# 2. Create feature branch
git checkout -b feature/typescript-support

# 3. Make changes
# ... edit files ...

# 4. Format and check
black mcp-dockerize.py
mypy mcp-dockerize.py

# 5. Test manually
python mcp-dockerize.py ~/test-ts-server/

# 6. Commit
git add .
git commit -m "Add TypeScript server support"

# 7. Push and create PR
git push origin feature/typescript-support
# Create PR on GitHub
```

---

## Questions?

- Open a **GitHub Discussion** for general questions
- Open an **Issue** for bugs or feature requests
- Check existing **documentation** first

---

**Thank you for contributing to MCP Dockerize! 🎉**

Every contribution, no matter how small, helps the community save tokens and improve Claude Code workflows!
