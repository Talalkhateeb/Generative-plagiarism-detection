#!/usr/bin/env bash
# setup_hooks.sh — Install GitLeaks pre-commit hook locally
# Run once: bash setup_hooks.sh

set -e

echo "📦 Installing GitLeaks pre-commit hook..."

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Write the pre-commit hook
cat > .git/hooks/pre-commit << 'HOOK'
#!/usr/bin/env bash
# Pre-commit hook: scan staged files for secrets using GitLeaks
# Blocks the commit if any secrets are detected.

echo "🔐 Running GitLeaks secret scan..."

# Check if gitleaks is installed
if ! command -v gitleaks &> /dev/null; then
    echo "⚠️  GitLeaks not found. Install it:"
    echo "   brew install gitleaks        (macOS)"
    echo "   choco install gitleaks       (Windows)"
    echo "   pip install gitleaks         (Python wrapper)"
    echo "   Or download from: https://github.com/gitleaks/gitleaks/releases"
    exit 1
fi

# Run gitleaks on staged files only
gitleaks protect --staged --redact -v

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ GitLeaks found secrets in your staged files!"
    echo "   Remove the secrets before committing."
    echo "   If this is a false positive, add it to .gitleaksignore"
    exit 1
fi

echo "✅ No secrets found. Proceeding with commit."
HOOK

chmod +x .git/hooks/pre-commit

echo "✅ Pre-commit hook installed at .git/hooks/pre-commit"
echo ""
echo "Make sure GitLeaks is installed:"
echo "  macOS:   brew install gitleaks"
echo "  Linux:   https://github.com/gitleaks/gitleaks/releases"
