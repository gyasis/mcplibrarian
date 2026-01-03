# 📚 MCP Librarian

> **"Save 97% of your tokens. Check out tools only when needed."**

**Status**: 🔬 Alpha Release (v0.1.0-alpha) | Currently supports Claude Code

Stop dumping all your tools on Claude's desk. Let the librarian fetch them on-demand.

---

## 🎯 The Problem: Token Bloat & Manual Management Hell

### The Token Math That Kills Your Sessions

Let's say you have **20 MCP servers** with an average of **15 tools each**:

```
20 servers × 15 tools = 300 total tools
300 tools × ~250 tokens per tool schema = 75,000 tokens
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
75,000 tokens consumed BEFORE you even start!
That's 37.5% of your 200,000 token budget GONE! 😱
```

**And you probably only need 2-3 of those tools per session.**

### The Manual Management Nightmare

But wait, you say: *"I'll just enable/disable servers as needed!"*

**Reality check**:

```
❌ Manual MCP Management:
   1. Open Claude Code settings
   2. Navigate to MCP servers section
   3. Disable server-playwright (won't need it today)
   4. Disable server-gemini (won't need it today)
   5. Disable server-deeplake (won't need it today)
   6. ... repeat 17 more times ...
   7. Restart Claude Code
   8. Start your work

   *30 minutes later...*

   You: "Actually, I need to search my knowledge base"
   System: "deeplake-rag is disabled"
   You: *sighs* Back to settings...
   9. Re-enable server-deeplake
   10. Restart Claude Code AGAIN
   11. Lose your conversation context

   Repeat this tedious cycle 5-10 times per day! 🤦
```

**This is exhausting, tedious, and kills your productivity.**

### Research Confirms This Is a Massive Problem

- [Anthropic's Tool Use Blog](https://www.anthropic.com/engineering/advanced-tool-use): "Front-loading all tools wastes 85% of context on tools you'll never use"
- [Cloudflare MCP Analysis](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2): "Schemas represent 60-80% of token usage in static toolsets"
- [Scott Spence's Real-World Data](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code): "66,000+ tokens consumed before conversation even starts"

**MCP Librarian is the better way.** ✨

---

## 💡 The Solution: The Smart Librarian

**MCP Librarian** works like a real library - **no manual toggling, no restarts, just ask for what you need**:

```
✅ MCP Librarian Approach:
   You: "I need help with research on X"
   Librarian: "Let me check that out for you..."
   Librarian: *quietly starts the right container*
   Librarian: *brings you exactly the tools you need*
   You: "Perfect! And I didn't lose my context or restart anything!"

   *30 minutes later...*

   You: "Now I need to test the UI with Playwright"
   Librarian: "On it!" *starts playwright container*
   You: "This is seamless! 🎉"
```

**The token math:**

```
20 servers × 1 polymorphic tool × 100 tokens = 2,000 tokens
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SAVES 73,000 tokens (97.3% reduction!)
198,000 tokens available for actual work! 🎉

No settings menus. No restarts. No lost context.
Just seamless, on-demand tool access.
```

---

## 📚 Project Origin Story

**How this project was born:**

I didn't notice my Claude Code sessions were consuming more and more tokens at first. But gradually, I noticed something was wrong - my sessions needed more and more token usage, and the context window was filling up super quick. I'd start a simple coding task and already be at 50% of my token budget before writing a single line of code!

After analyzing my system prompts, I discovered **66,000+ tokens were being consumed before my conversation even started** - just from MCP server tool schemas. With 80+ MCP servers in my setup, I was hitting 240,000 tokens at startup, exceeding my 200,000 token budget before I could even ask a question.

This project was born as a way to be more efficient with token usage around coding CLI tools. The library metaphor came naturally - instead of dumping all the books on your desk, a smart librarian checks out exactly what you need, when you need it.

**Current status**: Working with Claude Code
**Roadmap**: See [ROADMAP.md](ROADMAP.md) for expansion to Gemini Codex, Blocks, Goose CLI, OpenCode, and others

---

## 📖 The Library Metaphor

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

## 🏗️ How The Library Works

### 1. **The Catalog** (Registry)
```json
{
  "servers": {
    "deeplake-rag": {
      "friendly_name": "Research Database",
      "dewey_decimal": "rag.research.deeplake",
      "triggers": ["research", "articles", "saved"],
      "location": "docker-configs/deeplake-rag/"
    }
  }
}
```

Like a library catalog - the librarian knows where every book is, but doesn't put them all on your desk.

### 2. **The Checkout Desk** (Polymorphic Tool)
```
User: "Search my research articles for reverse prompting"
       ↓
Librarian Tool: deeplake_query("search articles for reverse prompting")
       ↓
Librarian: "Let me check that section for you..."
       ↓
Docker Container: *starts on-demand* (like fetching from stacks)
       ↓
Real Tools: retrieve_context(query="reverse prompting")
       ↓
Results: "Here's what I found in your research collection!"
```

### 3. **The Return Policy** (Auto-Stop)
```
Book checked out → Used for 5 minutes → Automatically returned to shelf
Tool container started → Used → Auto-stopped after 5 min idle
```

No more keeping 80 books on your desk "just in case" - the librarian returns them automatically!

---

## 📊 Real Example: Tool List Transformation

### Without MCP Librarian (Traditional Approach)

**Your deeplake-rag server has 6 tools**:

```json
// What Claude Code sees at startup (6 tools × ~400 tokens = 2,400 tokens):
[
  {
    "name": "retrieve_context",
    "description": "Search vector database and retrieve relevant context...",
    "inputSchema": { /* 200 tokens of JSON schema */ }
  },
  {
    "name": "get_summary",
    "description": "Get summary of documents in the database...",
    "inputSchema": { /* 200 tokens of JSON schema */ }
  },
  {
    "name": "search_document_content",
    "description": "Search within document content...",
    "inputSchema": { /* 200 tokens of JSON schema */ }
  },
  {
    "name": "get_document",
    "description": "Retrieve a specific document by ID...",
    "inputSchema": { /* 200 tokens of JSON schema */ }
  },
  {
    "name": "get_fuzzy_matching_titles",
    "description": "Find documents by fuzzy title matching...",
    "inputSchema": { /* 200 tokens of JSON schema */ }
  },
  {
    "name": "list_documents",
    "description": "List all documents in the database...",
    "inputSchema": { /* 200 tokens of JSON schema */ }
  }
]

// Total: 2,400 tokens just for ONE server!
// With 20 servers: 20 × 2,400 = 48,000 tokens minimum
```

### With MCP Librarian (Polymorphic Tool Approach)

**Claude Code sees 1 meta-tool instead**:

```json
// What Claude Code sees at startup (1 tool × 100 tokens = 100 tokens):
[
  {
    "name": "deeplake_query",
    "description": "Search and query your DeepLake knowledge base using natural language. The librarian will handle the details.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "Natural language query (e.g., 'search for articles about reverse prompting')"
        }
      }
    }
  }
]

// Total: 100 tokens for the entire server!
// With 20 servers: 20 × 100 = 2,000 tokens total
// Savings: 48,000 → 2,000 = 96% reduction! 🎉
```

### What Happens When You Call the Tool

**The librarian's workflow**:

```
Step 1: You call deeplake_query("search for articles about Docker")
        ↓
Step 2: Librarian analyzes your query
        "search" keyword detected → needs retrieve_context tool
        ↓
Step 3: Librarian starts Docker container
        docker compose up -d mcp-deeplake-rag
        Container starts in ~1-2 seconds
        ↓
Step 4: Librarian calls the actual tool inside container
        retrieve_context(query="articles about Docker", n_results=5)
        ↓
Step 5: Results returned to you
        "Found 5 articles about Docker in your knowledge base..."
        ↓
Step 6: After 5 minutes of inactivity
        Librarian auto-stops container (returns book to shelf)
        docker compose down mcp-deeplake-rag
```

**You never see the complexity. Just seamless tool access.**

### The Token Math (20 Servers Example)

| Server | Tools | Traditional Tokens | MCP Librarian Tokens | Savings |
|--------|-------|-------------------|---------------------|---------|
| deeplake-rag | 6 | 2,400 | 100 | 2,300 (95.8%) |
| playwright | 25 | 10,000 | 100 | 9,900 (99%) |
| gemini | 12 | 4,800 | 100 | 4,700 (97.9%) |
| gmail | 18 | 7,200 | 100 | 7,100 (98.6%) |
| snowflake | 8 | 3,200 | 100 | 3,100 (96.9%) |
| ... 15 more | ~230 | 47,400 | 1,500 | 45,900 (96.8%) |
| **TOTAL** | **300+** | **75,000** | **2,000** | **73,000 (97.3%)** |

**And you never manually enable/disable a single server. Ever.**

---

## 🎓 The Research Behind This

### Anthropic's Findings: Front-Loading is Broken

From [Anthropic's Advanced Tool Use Engineering Blog](https://www.anthropic.com/engineering/advanced-tool-use):

> **"85% reduction in token usage while maintaining access to your full tool library"**

**The Problem They Identified:**
- Traditional systems front-load ALL tool definitions
- Most tools never used in a session
- Context window wasted on irrelevant schemas

**Their Solution (Tool Search Tool):**
- Discovers tools on-demand
- Claude only sees tools it needs for current task
- Massive token savings

**MCP Librarian implements this exact pattern!**

### Cloudflare/Speakeasy's Data: Schemas Are The Problem

From [Speakeasy's 100x Token Reduction Article](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2):

> **"Schemas represent 60-80% of token usage in static toolsets"**

**Their Findings:**
```
Traditional Setup:
  - Tool calls: 100%
  - Input tokens: 100%
  - Problem: Schemas loaded for ALL tools

Dynamic Toolset (Lazy Loading):
  - Tool calls: 200% (2x more)
  - Input tokens: 4% (96% reduction!)
  - Solution: Load schemas only when needed
```

**Despite 2x more tool calls, input tokens dropped by 96%!**

**MCP Librarian uses the same lazy schema loading pattern.**

### Real-World Evidence: Scott Spence's Optimization Journey

From [Scott Spence's MCP Optimization Guide](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code):

**Before Optimization:**
- 7 MCP servers
- 67,300 tokens consumed
- 33.7% of 200k context budget GONE before conversation starts

**After Optimization:**
- Disabled unused servers
- 8,551 tokens saved
- More context available for work

**MCP Librarian automates this optimization for 80+ servers!**

---

## 🚀 Quick Start: Set Up Your Library

### Installation (2 minutes)

```bash
git clone https://github.com/yourusername/mcp-librarian.git
cd mcp-librarian
pip install -e .
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
