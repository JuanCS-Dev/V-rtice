#!/usr/bin/env bash
#
# VÉRTICE CLI - Bash/Zsh Completion Installer
# Automatically detects shell and installs completion scripts
#
# Usage:
#   ./install-completion.sh
#   ./install-completion.sh --uninstall

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPLETIONS_DIR="$SCRIPT_DIR/completions"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Detect shell
detect_shell() {
    if [ -n "$ZSH_VERSION" ]; then
        echo "zsh"
    elif [ -n "$BASH_VERSION" ]; then
        echo "bash"
    else
        # Try to detect from SHELL environment variable
        case "$SHELL" in
            */zsh)
                echo "zsh"
                ;;
            */bash)
                echo "bash"
                ;;
            *)
                echo "unknown"
                ;;
        esac
    fi
}

# Install bash completion
install_bash() {
    info "Installing bash completion..."

    # Try standard locations
    if [ -d "$HOME/.bash_completion.d" ]; then
        DEST="$HOME/.bash_completion.d/vcli"
    else
        mkdir -p "$HOME/.bash_completion.d"
        DEST="$HOME/.bash_completion.d/vcli"
    fi

    # Copy completion script
    cp "$COMPLETIONS_DIR/vcli.bash" "$DEST"
    success "Copied completion script to: $DEST"

    # Add sourcing to .bashrc if not already there
    if ! grep -q "bash_completion.d/vcli" "$HOME/.bashrc" 2>/dev/null; then
        echo "" >> "$HOME/.bashrc"
        echo "# VÉRTICE CLI completion" >> "$HOME/.bashrc"
        echo "[ -f ~/.bash_completion.d/vcli ] && source ~/.bash_completion.d/vcli" >> "$HOME/.bashrc"
        success "Added source line to ~/.bashrc"
    else
        info "Source line already exists in ~/.bashrc"
    fi

    success "Bash completion installed!"
    warning "Run 'source ~/.bashrc' or start a new terminal to enable completions"
}

# Install zsh completion
install_zsh() {
    info "Installing zsh completion..."

    # Create completion directory if it doesn't exist
    ZDOTDIR="${ZDOTDIR:-$HOME}"
    ZSH_COMPLETIONS_DIR="$ZDOTDIR/.zsh/completions"

    mkdir -p "$ZSH_COMPLETIONS_DIR"
    DEST="$ZSH_COMPLETIONS_DIR/_vcli"

    # Copy completion script
    cp "$COMPLETIONS_DIR/vcli.zsh" "$DEST"
    success "Copied completion script to: $DEST"

    # Add fpath to .zshrc if not already there
    ZSHRC="$ZDOTDIR/.zshrc"
    if [ ! -f "$ZSHRC" ]; then
        touch "$ZSHRC"
    fi

    if ! grep -q "fpath.*\.zsh/completions" "$ZSHRC" 2>/dev/null; then
        echo "" >> "$ZSHRC"
        echo "# VÉRTICE CLI completion" >> "$ZSHRC"
        echo "fpath=(~/.zsh/completions \$fpath)" >> "$ZSHRC"
        echo "autoload -Uz compinit && compinit" >> "$ZSHRC"
        success "Added fpath and compinit to ~/.zshrc"
    else
        info "fpath already configured in ~/.zshrc"
    fi

    success "Zsh completion installed!"
    warning "Run 'source ~/.zshrc' or start a new terminal to enable completions"
}

# Uninstall bash completion
uninstall_bash() {
    info "Uninstalling bash completion..."

    if [ -f "$HOME/.bash_completion.d/vcli" ]; then
        rm "$HOME/.bash_completion.d/vcli"
        success "Removed completion script"
    fi

    # Remove source line from .bashrc
    if [ -f "$HOME/.bashrc" ]; then
        sed -i '/# VÉRTICE CLI completion/d' "$HOME/.bashrc"
        sed -i '/bash_completion\.d\/vcli/d' "$HOME/.bashrc"
        success "Removed source line from ~/.bashrc"
    fi

    success "Bash completion uninstalled!"
}

# Uninstall zsh completion
uninstall_zsh() {
    info "Uninstalling zsh completion..."

    ZDOTDIR="${ZDOTDIR:-$HOME}"
    DEST="$ZDOTDIR/.zsh/completions/_vcli"

    if [ -f "$DEST" ]; then
        rm "$DEST"
        success "Removed completion script"
    fi

    # Note: We don't remove fpath from .zshrc as it may be used by other completions

    success "Zsh completion uninstalled!"
    info "Note: fpath configuration in ~/.zshrc was not removed (may be used by other tools)"
}

# Main installation logic
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║     VÉRTICE CLI - Completion Installer                    ║"
    echo "║     Bash/Zsh Shell Completion Setup                       ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""

    # Check if uninstall mode
    if [ "$1" = "--uninstall" ]; then
        SHELL_TYPE=$(detect_shell)
        info "Detected shell: $SHELL_TYPE"

        case "$SHELL_TYPE" in
            bash)
                uninstall_bash
                ;;
            zsh)
                uninstall_zsh
                ;;
            *)
                error "Could not detect shell type. Please specify bash or zsh:"
                echo "  Bash: $0 --uninstall bash"
                echo "  Zsh:  $0 --uninstall zsh"
                exit 1
                ;;
        esac
        exit 0
    fi

    # Detect shell
    SHELL_TYPE=$(detect_shell)

    if [ "$1" != "" ]; then
        SHELL_TYPE="$1"
    fi

    info "Detected shell: $SHELL_TYPE"
    echo ""

    # Install based on shell
    case "$SHELL_TYPE" in
        bash)
            install_bash
            ;;
        zsh)
            install_zsh
            ;;
        *)
            error "Could not auto-detect shell type!"
            echo ""
            echo "Please specify your shell manually:"
            echo "  Bash: $0 bash"
            echo "  Zsh:  $0 zsh"
            exit 1
            ;;
    esac

    echo ""
    success "Installation complete!"
    echo ""
    info "Test completion with: vcli <TAB><TAB>"
    echo ""
}

# Run main
main "$@"
