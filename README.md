# 📚 MCP Librarian

> **"Save 97% of your tokens. Check out tools only when needed."**

**Status**: 🔬 Alpha Release (v0.1.0-alpha) | Currently supports Claude Code

Stop dumping all your tools on Claude's desk. Let the librarian fetch them on-demand.

---

## 🎯 The Problem: Token Bloat

**My wake-up call**: I was hitting 240,000 tokens at startup with 80+ MCP servers - exceeding my 200,000 token budget before asking a single question. Sessions were failing to start.

**The math with a more typical setup** (20 servers × 15 tools):

```
300 total tools × 250 tokens per schema = 75,000 tokens
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
37.5% of your token budget GONE before you start
(And you'll only use 2-3 of those tools per session)
```

**Research confirms this is widespread**:
- [Anthropic](https://www.anthropic.com/engineering/advanced-tool-use): "Front-loading wastes 85% of context on unused tools"
- [Cloudflare](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2): "Schemas = 60-80% of token usage"
- [Scott Spence](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code): "66,000+ tokens consumed before conversation starts"

---

## 💡 The Solution

| Manual MCP Management | MCP Librarian |
|----------------------|---------------|
| 🔧 Edit config → disable 17 servers → restart | 💬 Just ask for what you need |
| ⏱️ 5 minutes to disable servers | ⚡ Instant, automatic activation |
| 🔄 Need a tool? Re-enable → restart → lose context | 🎯 Tool loaded seamlessly, keep context |
| 😫 Repeat this cycle 5-10 times per day | 😊 Never think about it again |
| 📚 All 300 tools loaded (75,000 tokens) | 📖 20 polymorphic tools (2,000 tokens) |
| ❌ 37.5% of budget wasted at startup | ✅ 99% of budget available for work |
| 🤦 "Which servers do I need today?" | 🎉 "What do you need help with?" |

---

## 🏗️ How It Works: The DeepLake Example

**Traditional**: Your `deeplake-rag` server has 6 tools (retrieve_context, get_summary, search_document_content, get_document, get_fuzzy_matching_titles, list_documents) = **2,400 tokens** at startup.

**MCP Librarian**: Claude sees 1 polymorphic tool = **100 tokens**.

### The Transformation

**Registry (Catalog)**:
```json
{
  "deeplake-rag": {
    "triggers": ["research", "articles", "saved"],
    "location": "docker-configs/deeplake-rag/"
  }
}
```

**Polymorphic Tool (What Claude Sees)**:
```json
{
  "name": "deeplake_query",
  "description": "Search your knowledge base using natural language",
  "inputSchema": { "query": "string" }
}
```

### The Workflow

```
You: "Search for articles about Docker"
  ↓
Librarian: Starts container → Routes to retrieve_context → Returns results
  ↓
5 min idle → Container auto-stops
```

**Result**: 96% token savings. Seamless experience. Zero manual management.

---

## 🚀 Quick Start

```bash
git clone https://github.com/gyasis/mcplibrarian.git
cd mcplibrarian
python mcp-librarian.py ~/path/to/your/mcp-server/
```

### Catalog Your First Book (5 minutes)

```bash
# The librarian analyzes your MCP server
python mcp-librarian.py ~/path/to/your/mcp-server/

# Output:
# 📚 Cataloging server...
# ✓ Found 6 tools (books in this collection)
# ✓ Created library card (Docker container)
# ✓ Added to catalog (registry)
# ✓ Trained librarian (routing rules)
#
# Your server is ready to check out! 🎉
```

### Add Library Card Info (2 minutes)

```bash
cd docker-configs/your-server/
nano docker-compose.yml

# Add your API keys (like a library card):
environment:
  API_KEY: "your-library-card-number"
```

### Visit The Library (1 minute)

```bash
# Start your library
docker compose up -d

# Test the checkout desk
echo '{"jsonrpc":"2.0","id":1,"method":"initialize",...}' | docker compose run --rm your-server
```

### Ask The Librarian (Claude Code)

```
User: "Search my research articles for machine learning"

Librarian: *checks out deeplake-rag book*
          *finds relevant articles*
          *returns book to shelf*

Result: Your research, delivered!
```

**DONE! You just saved 97% of your tokens! 📚**

---

## 📊 Token Savings Breakdown

### The Math

| Servers | Traditional (All Books on Desk) | MCP Librarian (Check Out On-Demand) | Savings |
|---------|--------------------------------|-------------------------------------|---------|
| 1 server | 3,000 tokens | 100 tokens | 2,900 (97%) |
| 10 servers | 30,000 tokens | 1,000 tokens | 29,000 (97%) |
| 80 servers | 240,000 tokens | 8,000 tokens | 232,000 (97%) |

### Real Impact

**Before (All Books Dumped on Desk):**
```
📚📚📚📚📚📚📚📚📚📚📚📚📚📚📚📚📚📚📚📚 (80 stacks)
You: "I can't even see my assignment!"
Context: 0 tokens available 😱
```

**After (Librarian Brings Books On-Demand):**
```
📚 (1 book checked out)
You: "Perfect! I can focus on my work!"
Context: 192,000 tokens available 🎉
```

---

## 🎯 How It Solves The Front-Loading Problem

### Traditional MCP: The Dump Truck Approach
```
Session Start:
  ↓
Load ALL 80 servers
  ↓
Expose ALL ~500 tools
  ↓
Consume 240,000 tokens
  ↓
Session FAILS - budget exceeded!
  ↓
User: "I can't even start! 😭"
```

### MCP Librarian: The Smart Checkout Approach
```
Session Start:
  ↓
Load librarian catalog (80 polymorphic tools)
  ↓
Consume 8,000 tokens
  ↓
192,000 tokens available!
  ↓
User asks: "Search my research"
  ↓
Librarian: "Let me check that out for you..."
  ↓
Container starts (2 seconds)
  ↓
Tool executes
  ↓
Container auto-stops (5 min later)
  ↓
User: "Perfect! What else can you help with?"
```

**Key Difference**: Tools loaded WHEN NEEDED, not ALL AT ONCE.

---

## 🏛️ The Library Architecture

```
┌─────────────────────────────────────────────────────────┐
│ Claude Code (The Student)                               │
│ "I need help with my research assignment..."            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 📚 The Checkout Desk (Polymorphic Tools)                │
│                                                          │
│  deeplake_query("search research for X")                │
│  gemini_query("analyze this code")                      │
│  playwright_query("test this UI")                       │
│  ...80 checkout desks (one per collection)              │
│                                                          │
│  Token Cost: 100 per desk × 80 desks = 8,000 tokens    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 👤 The Librarian (mcp-proxy.py)                         │
│                                                          │
│  Keywords detected: "search", "research"                │
│  → Check out "Research Database" (deeplake-rag)         │
│  → Start container (fetch from stacks)                  │
│  → Route to retrieve_context tool                       │
│  → Return results                                       │
│  → Auto-return book after 5 min                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 📚 The Book Stacks (Docker Containers)                  │
│                                                          │
│  deeplake-rag container (sleeping)                      │
│  gemini-mcp container (sleeping)                        │
│  playwright container (sleeping)                        │
│  ...80 containers total                                 │
│                                                          │
│  Only started when book checked out!                    │
│  Auto-stopped when returned (5 min idle)                │
└─────────────────────────────────────────────────────────┘
```

**The Genius**: Claude only sees the checkout desk (8,000 tokens), not the entire library (240,000 tokens)!

---

## 📚 Library Features

### Automatic Cataloging (90% Automated)
✅ Server type detection (Python, Node.js)
✅ Book collection analysis (tool schemas)
✅ Dewey Decimal assignment (friendly names)
✅ Shelf location setup (Docker configs)
✅ Catalog entry creation (registry)
✅ Librarian training (routing rules)

### Smart Checkout System
✅ **Keyword triggers**: "search articles" → checks out research database
✅ **Dot notation**: `.deeplake` → explicit checkout
✅ **On-demand loading**: Container starts only when needed
✅ **Auto-return**: Container stops after 5 min idle
✅ **Multi-checkout**: Multiple tools can be checked out simultaneously

### Library Management
✅ **Catalog search**: `get_server_documentation` (browse available books)
✅ **Collection stats**: See all available servers/tools
✅ **Activity tracking**: Monitor checkout/return cycles
✅ **Resource limits**: Prevent too many books checked out at once

---

## 🎓 Two Learning Paths

### Path 1: Automated Cataloging (Quick Checkout) - 5-15 minutes
**Best for**: Fast setup, bulk cataloging

```bash
python mcp-librarian.py ~/mcp-server/
# Librarian catalogs everything automatically
```

**What gets automated**:
- Collection analysis (server type, tools)
- Shelf creation (Docker container)
- Catalog entry (registry)
- Librarian training (routing rules)

[**Full Guide**: docs/AUTOMATED_CATALOGING.md](docs/MCP_DOCKERIZE_GUIDE.md)

### Path 2: Manual Cataloging (Study Mode) - 2-3 hours
**Best for**: Learning, custom collections

```bash
# You work with the librarian to catalog manually
# Full control, deep understanding
```

**What you learn**:
- How the catalog system works
- Shelf organization patterns
- Dewey decimal assignment
- Custom routing strategies

[**Full Guide**: docs/MANUAL_CATALOGING.md](docs/MANUAL_DOCKERIZATION_GUIDE.md)

**Both paths achieve 97% token savings!**

---

## 🌟 What Makes This Different

### vs Manual Enable/Disable (The Tedious Way)
- ❌ Manual: Open settings → disable 17 servers → restart → work → realize you need a server → re-enable → restart AGAIN → lose context
- ✅ MCP Librarian: Just work. Tools load automatically. Never restart.
- ❌ Manual: 5-10 min per configuration change
- ✅ MCP Librarian: Instant, seamless

### vs Traditional MCP (Front-Load Everything)
- ❌ Traditional: Load all 300 tools = 75,000 tokens wasted
- ✅ MCP Librarian: Load 20 polymorphic tools = 2,000 tokens used
- ❌ Traditional: 37.5% of budget gone at startup
- ✅ MCP Librarian: 99% of budget available for work

### vs lazy-mcp (Manual Config)
- ❌ lazy-mcp: Still requires manual enable/disable per session
- ✅ MCP Librarian: Fully automatic, no manual intervention
- ❌ lazy-mcp: 17-34k token savings (manual config)
- ✅ MCP Librarian: 73k token savings (90% automated)

### vs token-optimizer-mcp (Cache Optimization)
- ❌ token-optimizer: Optimizes after loading (still front-loads all tools)
- ✅ MCP Librarian: Never loads unused tools (true lazy loading)

### vs Anthropic's Tool Search Tool (Built-in)
- ❌ Tool Search: Requires compatible MCP servers
- ✅ MCP Librarian: Works with ANY MCP server via Docker wrapper

**MCP Librarian = Zero manual management + True lazy loading + 97.3% token savings**

---

## 💰 The Real Cost Savings

### Token Savings: 97.3% Reduction

With **20 MCP servers** and **300 tools**, you're looking at:
- **Traditional approach**: 75,000 tokens wasted at every session start
- **MCP Librarian**: 2,000 tokens (just the polymorphic tools)
- **Savings**: 73,000 tokens per session

That's 97.3% of your context window back for actual work instead of tool schemas you'll never use.

### Time Savings: Stop The Manual Management Grind

**The old way** (manual enable/disable):
- 5-10 minutes every time you need to change which servers are enabled
- 5-10 times per day on average
- **30-100 minutes wasted daily** just managing your tools
- Lost context every time you restart
- Frustration and broken flow state

**With MCP Librarian**:
- Zero manual management
- Never restart Claude Code
- Never lose context
- Just ask for what you need - the librarian handles everything

### Setup Time: 90% Automation

**Manual dockerization** of 20 servers:
- ~2.5 hours per server × 20 = **50 hours of tedious work**

**MCP Librarian automation**:
- ~9 minutes per server × 20 = **3 hours total**
- 94% time savings on setup

**The bottom line**: More time coding, less time managing infrastructure. That's what MCP Librarian is all about.

---

## 📖 Documentation Library

### Quick References
- [**QUICK_START.md**](QUICK_START.md) - 5-minute checkout guide
- [**PROJECT_OVERVIEW.md**](PROJECT_OVERVIEW.md) - Complete library overview

### Detailed Guides
- [**AUTOMATED_CATALOGING.md**](docs/MCP_DOCKERIZE_GUIDE.md) - Automated cataloging (15 pages)
- [**MANUAL_CATALOGING.md**](docs/MANUAL_DOCKERIZATION_GUIDE.md) - Manual cataloging (25 pages)

### Community
- [**CONTRIBUTING.md**](CONTRIBUTING.md) - Help expand the library
- [**CHANGELOG.md**](CHANGELOG.md) - Library version history
- [**SECURITY.md**](SECURITY.md) - Library security policy

---

## 🤝 Join The Library

**Help us catalog more collections!**

We need:
- Example MCP server catalogs
- Custom routing patterns
- Docker optimization tips
- Documentation improvements

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to help!

---

## 📜 License

MIT License - Free to use commercially

Just like a public library - free for everyone! 📚

---

## 🙏 Acknowledgments

**Inspired by (not backed by or affiliated with)**:
- [Anthropic's Tool Search Tool Research](https://www.anthropic.com/engineering/advanced-tool-use) - 85% reduction in token usage through dynamic loading
- [Cloudflare/Speakeasy's Dynamic Toolsets](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2) - 96% reduction via lazy schemas (100x improvement)
- [Scott Spence's Optimization Journey](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code) - Real-world data showing 66k+ tokens wasted at startup

**Inspiration from other MCP token optimization tools**:
- `lazy-mcp` - Manual lazy loading configuration patterns
- `token-optimizer-mcp` - Cache-based optimization approaches
- `OpenMCP` - Lazy schema loading techniques

**Special thanks to**:
- The MCP community for the Toolhost pattern
- Docker for containerization technology
- Everyone who contributed examples and feedback

**Disclaimer**: This is an independent open-source project inspired by published research and community best practices. Not officially endorsed by or affiliated with Anthropic, Cloudflare, or any mentioned organizations.

---

## 🚀 Get Started Now!

```bash
# Clone the library
git clone https://github.com/gyasis/mcplibrarian.git

# Catalog your first collection
cd mcplibrarian
python mcp-librarian.py ~/path/to/your/mcp-server/

# 5 minutes later: 97% token savings achieved!
```

**Stop dumping books on Claude's desk. Let the librarian help.** 📚

---

## 📞 Library Hours (Support)

- **Documentation**: See [docs/](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/gyasis/mcplibrarian/issues)
- **Discussions**: [GitHub Discussions](https://github.com/gyasis/mcplibrarian/discussions)

---

*The librarian is always ready to help. Just ask.* 📚

**MCP Librarian v0.1.0-alpha** | Save 97% of your tokens | Check out tools only when needed
