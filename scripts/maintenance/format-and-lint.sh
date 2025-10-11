#!/bin/bash
# =============================================================================
# Vértice Platform - Code Formatting & Linting Script
# =============================================================================
# Purpose: Format and lint Python codebase with Black, isort, flake8
# Usage: ./scripts/maintenance/format-and-lint.sh [check|fix] [path]
# Author: MAXIMUS Team
# Date: 2025-10-11
# =============================================================================

set -e
set -u

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Defaults
MODE="${1:-fix}"
TARGET="${2:-backend/}"

print_header() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Vértice Platform - Code Quality Tools${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_section() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

check_tool() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 not found. Install with: pip install $1"
        return 1
    fi
    return 0
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    print_header
    
    echo "Mode: ${MODE}"
    echo "Target: ${TARGET}"
    echo ""
    
    # Check if tools are installed
    print_section "Checking tools..."
    check_tool black || exit 1
    check_tool isort || exit 1
    check_tool flake8 || exit 1
    check_tool mypy || print_warning "mypy not found (optional)"
    print_success "All required tools found"
    echo ""
    
    # Exit code tracking
    EXIT_CODE=0
    
    # =======================================================================
    # 1. BLACK - Code Formatting
    # =======================================================================
    print_section "1. Black - Code Formatter"
    
    if [ "$MODE" = "check" ]; then
        echo "Checking format (no changes)..."
        if black --check --diff "$TARGET" 2>&1; then
            print_success "Black: All files formatted correctly"
        else
            print_error "Black: Formatting issues found"
            EXIT_CODE=1
        fi
    else
        echo "Formatting code..."
        if black "$TARGET" 2>&1; then
            print_success "Black: Code formatted"
        else
            print_error "Black: Formatting failed"
            EXIT_CODE=1
        fi
    fi
    echo ""
    
    # =======================================================================
    # 2. ISORT - Import Sorting
    # =======================================================================
    print_section "2. isort - Import Sorter"
    
    if [ "$MODE" = "check" ]; then
        echo "Checking imports (no changes)..."
        if isort --check-only --diff "$TARGET" 2>&1; then
            print_success "isort: All imports sorted correctly"
        else
            print_error "isort: Import sorting issues found"
            EXIT_CODE=1
        fi
    else
        echo "Sorting imports..."
        if isort "$TARGET" 2>&1; then
            print_success "isort: Imports sorted"
        else
            print_error "isort: Sorting failed"
            EXIT_CODE=1
        fi
    fi
    echo ""
    
    # =======================================================================
    # 3. FLAKE8 - Linting
    # =======================================================================
    print_section "3. Flake8 - Code Linter"
    
    echo "Running linter..."
    if flake8 "$TARGET" 2>&1; then
        print_success "Flake8: No issues found"
    else
        print_error "Flake8: Linting issues found (see above)"
        EXIT_CODE=1
    fi
    echo ""
    
    # =======================================================================
    # 4. MYPY - Type Checking (Optional)
    # =======================================================================
    if command -v mypy &> /dev/null && [ "$MODE" != "quick" ]; then
        print_section "4. mypy - Type Checker"
        
        echo "Checking types..."
        if mypy "$TARGET" 2>&1 | head -50; then
            print_success "mypy: Type checking passed"
        else
            print_warning "mypy: Type issues found (non-blocking)"
        fi
        echo ""
    fi
    
    # =======================================================================
    # 5. BANDIT - Security Linter (Optional)
    # =======================================================================
    if command -v bandit &> /dev/null && [ "$MODE" != "quick" ]; then
        print_section "5. Bandit - Security Scanner"
        
        echo "Scanning for security issues..."
        if bandit -c pyproject.toml -r "$TARGET" -ll 2>&1 | tail -20; then
            print_success "Bandit: No security issues found"
        else
            print_warning "Bandit: Potential security issues (review)"
        fi
        echo ""
    fi
    
    # =======================================================================
    # Summary
    # =======================================================================
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    if [ $EXIT_CODE -eq 0 ]; then
        print_success "All checks passed!"
        echo ""
        if [ "$MODE" = "check" ]; then
            echo "Code is properly formatted and linted."
        else
            echo "Code has been formatted and is ready to commit."
        fi
    else
        print_error "Some checks failed!"
        echo ""
        echo "Fix issues and run again, or run in fix mode:"
        echo "  ./scripts/maintenance/format-and-lint.sh fix"
    fi
    echo ""
    
    exit $EXIT_CODE
}

# Show usage
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    cat << EOF
Vértice Platform - Code Formatting & Linting

Usage:
  ./scripts/maintenance/format-and-lint.sh [MODE] [PATH]

Modes:
  check    - Check formatting/linting without making changes
  fix      - Format and fix issues automatically (default)
  quick    - Fast mode (skip mypy and bandit)

Path:
  Target directory or file (default: backend/)

Examples:
  # Format entire backend
  ./scripts/maintenance/format-and-lint.sh fix

  # Check specific service
  ./scripts/maintenance/format-and-lint.sh check backend/services/maximus_core_service/

  # Quick check (no type checking)
  ./scripts/maintenance/format-and-lint.sh quick backend/shared/

Tools Used:
  • Black      - Opinionated code formatter (88 char line length)
  • isort      - Import statement organizer (Black-compatible)
  • Flake8     - Style guide enforcement
  • mypy       - Static type checker (optional)
  • Bandit     - Security issue scanner (optional)

Configuration:
  - pyproject.toml  - Black, isort, pytest, mypy config
  - .flake8         - Flake8 configuration
  - .pre-commit-config.yaml - Pre-commit hooks

Install Tools:
  pip install black isort flake8 mypy bandit

Setup Pre-commit Hooks:
  pre-commit install
  pre-commit run --all-files

EOF
    exit 0
fi

# Run main
main
