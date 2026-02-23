#!/bin/bash
# publish-to-github.sh - Initialize and publish MCP Librarian to GitHub

set -e  # Exit on error

echo "🚀 MCP Librarian - GitHub Publisher"
echo "===================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: git is not installed"
    exit 1
fi

# Check if already a git repo
if [ -d .git ]; then
    echo "⚠️  This is already a git repository"
    read -p "Do you want to continue and add a new remote? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
else
    # Initialize git repo
    echo "📦 Initializing git repository..."
    git init
    echo "✓ Git repository initialized"
fi

# Ask for GitHub repository URL
echo ""
echo "Enter your GitHub repository URL (e.g., https://github.com/username/mcp-librarian.git):"
read -r REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ Error: Repository URL cannot be empty"
    exit 1
fi

# Ask for branch name
echo ""
echo "Enter branch name (default: main):"
read -r BRANCH_NAME
BRANCH_NAME=${BRANCH_NAME:-main}

# Create .gitignore if it doesn't exist
if [ ! -f .gitignore ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Docker
docker-configs/
*.env
.env.*

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Registry and manifests (generated)
mcp-docker-registry.json
mcp-manifests/

# Temporary files
tmp/
temp/
EOF
    echo "✓ .gitignore created"
fi

# Stage all files
echo ""
echo "📦 Staging files..."
git add .
echo "✓ Files staged"

# Show what will be committed
echo ""
echo "📋 Files to be committed:"
git status --short

# Ask for confirmation
echo ""
read -p "Do you want to commit and push these files? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelled"
    exit 0
fi

# Commit
echo ""
echo "💾 Creating initial commit..."
git commit -m "Initial commit - MCP Librarian v1.0.0

- Automated dockerization script (mcp-librarian.py)
- Comprehensive documentation (48+ pages)
- Toolhost pattern implementation
- Support for Python and Node.js servers
- 97% token savings demonstrated
- Both automated and manual paths documented

Features:
- 90% automation of dockerization process
- Tool schema extraction
- Registry integration
- Routing rule generation
- Container validation

Documentation:
- README.md - Master guide
- QUICK_START.md - 5-minute guide
- MCP_DOCKERIZE_GUIDE.md - Automated path
- MANUAL_DOCKERIZATION_GUIDE.md - Manual path
- CONTRIBUTING.md - Contribution guidelines
- CHANGELOG.md - Version history"

echo "✓ Initial commit created"

# Set up remote
echo ""
echo "🔗 Setting up remote..."
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
echo "✓ Remote configured: $REPO_URL"

# Create and switch to branch
echo ""
echo "🌿 Creating branch: $BRANCH_NAME..."
git branch -M "$BRANCH_NAME"
echo "✓ Branch created: $BRANCH_NAME"

# Push to GitHub
echo ""
echo "☁️  Pushing to GitHub..."
git push -u origin "$BRANCH_NAME"
echo "✓ Pushed to GitHub"

echo ""
echo "🎉 Success! MCP Librarian published to GitHub!"
echo ""
echo "📋 Next steps:"
echo "   1. Visit $REPO_URL"
echo "   2. Add repository description and topics"
echo "   3. Update README.md with your GitHub username"
echo "   4. Configure GitHub Pages (optional)"
echo "   5. Enable GitHub Discussions"
echo "   6. Add repository topics: mcp, docker, claude, llm, ai"
echo "   7. Create first release (v1.0.0)"
echo ""
echo "📖 Documentation:"
echo "   - README.md for overview"
echo "   - QUICK_START.md for 5-minute guide"
echo "   - docs/ for detailed guides"
echo ""
echo "🤝 Community:"
echo "   - Enable Issues for bug reports"
echo "   - Enable Discussions for Q&A"
echo "   - Update FUNDING.yml for sponsorship"
echo ""
echo "Happy sharing! 🚀"
