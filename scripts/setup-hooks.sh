#!/bin/bash
#
# Setup Git hooks for the project
# This installs the pre-commit hook with ESLint and build validation
#

echo "Setting up Git hooks..."

# Get the repository root directory
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)

if [ -z "$REPO_ROOT" ]; then
    echo "❌ Error: Not in a Git repository"
    exit 1
fi

# Copy the pre-commit hook
if [ -f "$REPO_ROOT/.git/hooks/pre-commit" ]; then
    echo "📝 Backing up existing pre-commit hook to pre-commit.backup"
    cp "$REPO_ROOT/.git/hooks/pre-commit" "$REPO_ROOT/.git/hooks/pre-commit.backup"
fi

# Create the hooks directory if it doesn't exist
mkdir -p "$REPO_ROOT/.git/hooks"

# Copy the current pre-commit hook
cp "$REPO_ROOT/.git/hooks/pre-commit" "$REPO_ROOT/scripts/pre-commit-hook" 2>/dev/null || true

echo "✅ Git hooks setup complete!"
echo ""
echo "The pre-commit hook will now:"
echo "  - Validate YAML event files"
echo "  - Check date logic and ID/filename matching"
echo "  - Run ESLint checks on React code"
echo "  - Test the React build with CI settings"
echo ""
echo "To skip hooks temporarily, use: git commit --no-verify"