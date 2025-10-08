#!/bin/bash

# vCLI-Go Installation Script
# Installs vcli-go binary and creates aliases

set -e

VCLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VCLI_BIN="$VCLI_DIR/bin/vcli"

echo "🚀 Installing vCLI-Go..."
echo ""

# Check if binary exists
if [ ! -f "$VCLI_BIN" ]; then
    echo "❌ Error: Binary not found at $VCLI_BIN"
    echo "   Run: go build -o bin/vcli ./cmd/"
    exit 1
fi

# Make binary executable
chmod +x "$VCLI_BIN"
echo "✅ Binary is executable"

# Add to PATH via symlink
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

if [ -L "$INSTALL_DIR/vcli-go" ]; then
    rm "$INSTALL_DIR/vcli-go"
fi

ln -s "$VCLI_BIN" "$INSTALL_DIR/vcli-go"
echo "✅ Symlink created: $INSTALL_DIR/vcli-go"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "⚠️  ~/.local/bin is not in your PATH"
    echo "   Add this to your ~/.bashrc or ~/.zshrc:"
    echo ""
    echo '   export PATH="$HOME/.local/bin:$PATH"'
    echo ""
else
    echo "✅ ~/.local/bin is in PATH"
fi

# Create aliases helper
cat > "$INSTALL_DIR/vcli-go-aliases.sh" << 'EOF'
# vCLI-Go aliases
alias vcli-go='vcli-go'
alias vgo='vcli-go'
EOF

echo "✅ Aliases helper created: $INSTALL_DIR/vcli-go-aliases.sh"

echo ""
echo "📋 To enable aliases, add to your ~/.bashrc or ~/.zshrc:"
echo ""
echo "   source ~/.local/bin/vcli-go-aliases.sh"
echo ""
echo "🎉 Installation complete!"
echo ""
echo "Usage:"
echo "  vcli-go --help          # Show help"
echo "  vcli-go shell           # Interactive shell (requires terminal)"
echo "  vcli-go k8s get pods    # Direct commands"
echo ""
echo "Note: Shell requires a real terminal (TTY)"
echo "      Won't work via: pipes, Claude Code terminal, SSH without -t"
echo ""
