# 🗺️ MCP Librarian Roadmap

## Current Status: Alpha (v0.1.0-alpha)

**Working today**:
- ✅ Claude Code CLI integration
- ✅ Python MCP server support
- ✅ Node.js MCP server support
- ✅ Docker containerization
- ✅ Automated cataloging (90% automation)
- ✅ Manual cataloging guide
- ✅ Token savings: 97% (232,000 tokens for 80 servers)
- ✅ Lazy loading pattern
- ✅ On-demand container startup
- ✅ Auto-stop containers (5 min idle)

---

## Phase 1: Stabilization & Testing (Alpha → Beta)

**Goals**: Validate architecture, gather feedback, fix bugs

**Tasks**:
- [ ] Test with 10+ different MCP servers
- [ ] Gather user feedback on cataloging process
- [ ] Performance benchmarking (container startup latency)
- [ ] Documentation improvements based on user questions
- [ ] Add example catalog configurations
- [ ] Create video walkthrough tutorial
- [ ] Set up GitHub Discussions for community support
- [ ] Add CI/CD for automated testing

**Target**: v0.2.0-beta (Q1 2026)

---

## Phase 2: Multi-Tool Support (Beta → v1.0)

**Goals**: Expand beyond Claude Code to other AI coding assistants

### Gemini Codex Support
- [ ] Test MCP protocol compatibility with Gemini
- [ ] Adapt proxy for Gemini's tool calling format
- [ ] Create Gemini-specific documentation
- [ ] Test with Gemini's token limits

### Goose CLI Support
- [ ] Research Goose CLI's MCP implementation
- [ ] Test lazy loading with Goose workflows
- [ ] Create Goose-specific examples
- [ ] Document Goose integration

### OpenCode Support
- [ ] Research OpenCode's extensibility model
- [ ] Test MCP server integration
- [ ] Create OpenCode cataloging guide
- [ ] Test token optimization benefits

### Blocks Support
- [ ] Investigate Blocks' MCP compatibility
- [ ] Test containerized server integration
- [ ] Create Blocks workflow examples
- [ ] Document setup process

**Target**: v1.0.0 (Q2 2026)

---

## Phase 3: Advanced Features (v1.x)

### Enhanced Routing
- [ ] Add local LLM routing (Ollama integration)
- [ ] Implement semantic routing beyond keywords
- [ ] Multi-server orchestration (call multiple servers)
- [ ] Context-aware tool selection

### Performance Optimization
- [ ] Container warm pools (keep frequently used containers running)
- [ ] Predictive container startup (anticipate needs)
- [ ] Parallel container startup
- [ ] Memory usage optimization

### Developer Experience
- [ ] Web UI for cataloging
- [ ] Visual registry explorer
- [ ] Interactive routing rule builder
- [ ] Real-time token usage dashboard

### Language Support
- [ ] Go MCP server support
- [ ] Rust MCP server support
- [ ] Java MCP server support
- [ ] Generic binary wrapper

**Target**: v1.1.0 - v1.5.0 (Q3-Q4 2026)

---

## Phase 4: Ecosystem Integration (v2.0)

### Official Integrations
- [ ] Submit to Claude Code plugin marketplace (if available)
- [ ] Create Homebrew formula
- [ ] Create pip package
- [ ] Docker Hub official images

### Enterprise Features
- [ ] Multi-user catalog sharing
- [ ] Organization-wide registry
- [ ] Access control and permissions
- [ ] Audit logging
- [ ] Resource quotas and limits

### Cloud Deployment
- [ ] Kubernetes deployment guide
- [ ] AWS ECS/Fargate support
- [ ] Google Cloud Run support
- [ ] Azure Container Instances support

**Target**: v2.0.0 (Q1 2027)

---

## Community Requests

**Submit your feature requests**: [GitHub Issues](https://github.com/gyasis/mcplibrarian/issues)

Popular requests will be prioritized in upcoming releases.

---

## Long-term Vision

**MCP Librarian aims to become**:
1. **The standard** for token-efficient MCP server management
2. **Cross-platform** - works with any AI coding assistant
3. **Zero-config** - automatic cataloging with smart defaults
4. **Community-driven** - catalog sharing and reusable templates
5. **Enterprise-ready** - secure, scalable, auditable

---

## Contributing

Want to help shape the roadmap?

- 🐛 Report bugs
- 💡 Suggest features
- 📖 Improve documentation
- 🧪 Test with new MCP servers
- 🎨 Create example catalogs
- 🚀 Submit pull requests

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Release Schedule

| Version | Target | Focus |
|---------|--------|-------|
| v0.1.0-alpha | ✅ Released | Initial Claude Code support |
| v0.2.0-beta | Q1 2026 | Stabilization, testing, feedback |
| v1.0.0 | Q2 2026 | Multi-tool support (Gemini, Goose, OpenCode, Blocks) |
| v1.5.0 | Q4 2026 | Advanced features, optimization |
| v2.0.0 | Q1 2027 | Ecosystem integration, enterprise features |

**Note**: Timeline is approximate and subject to community feedback and development priorities.

---

## Feedback

Have thoughts on this roadmap?

- 💬 [Start a Discussion](https://github.com/gyasis/mcplibrarian/discussions)
- 📧 Open an issue with the `roadmap` label
- 🗳️ Vote on existing feature requests

---

*Last updated: 2026-01-03*
*Roadmap version: 1.0*
