#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# FINAL SECURITY SCAN - PRE-PUBLICATION
# ═══════════════════════════════════════════════════════════════════════════
#
# Comprehensive security scan before making repository public
#
# This script runs multiple security scanners to ensure no secrets,
# credentials, or sensitive information is present in the repository.
#
# ═══════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNINGS=0

# Log file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="security_scan_${TIMESTAMP}.log"

# ═══════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

header() {
    echo ""
    log "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
    log "${BLUE}  $1${NC}"
    log "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
}

success() {
    log "${GREEN}✅ $1${NC}"
    ((PASSED_CHECKS++))
}

error() {
    log "${RED}❌ $1${NC}"
    ((FAILED_CHECKS++))
}

warning() {
    log "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        warning "$1 not found - skipping $2 check"
        return 1
    fi
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════
# Pre-flight Checks
# ═══════════════════════════════════════════════════════════════════════════

header "PRE-FLIGHT CHECKS"

# Check if we're in repository root
if [ ! -d ".git" ]; then
    error "Not in repository root. Please run from /path/to/V-rtice/"
    exit 1
fi
success "Running in repository root"

# Check if repository is clean
if [ -n "$(git status --porcelain)" ]; then
    warning "Repository has uncommitted changes"
    log "    Consider committing or stashing changes before scanning"
else
    success "Repository is clean"
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
log "Current branch: $CURRENT_BRANCH"

# ═══════════════════════════════════════════════════════════════════════════
# Scan 1: Git History for Secrets (git-secrets)
# ═══════════════════════════════════════════════════════════════════════════

header "SCAN 1: Git History Secret Scan (git-secrets)"
((TOTAL_CHECKS++))

if check_command "git-secrets" "git-secrets"; then
    log "Scanning entire git history for secrets..."

    # Install git-secrets hooks if not already installed
    git secrets --install --force > /dev/null 2>&1 || true

    # Add AWS patterns
    git secrets --register-aws > /dev/null 2>&1 || true

    # Scan history
    if git secrets --scan-history > /dev/null 2>&1; then
        success "git-secrets: No secrets found in git history"
    else
        error "git-secrets: Potential secrets detected in git history!"
        log "    Run manually: git secrets --scan-history"
    fi
else
    warning "git-secrets not installed. Install: brew install git-secrets"
    log "    Or: https://github.com/awslabs/git-secrets"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Scan 2: Detect Secrets (Yelp's detect-secrets)
# ═══════════════════════════════════════════════════════════════════════════

header "SCAN 2: Secret Patterns (detect-secrets)"
((TOTAL_CHECKS++))

if check_command "detect-secrets" "detect-secrets"; then
    log "Scanning for secret patterns..."

    # Run detect-secrets scan
    SECRETS_FOUND=$(detect-secrets scan --baseline .secrets.baseline 2>&1 | grep -c "potential secrets" || echo "0")

    if [ "$SECRETS_FOUND" -eq 0 ]; then
        success "detect-secrets: No new secrets detected"
    else
        warning "detect-secrets: $SECRETS_FOUND potential secrets found"
        log "    Review manually: detect-secrets scan"
        log "    Audit findings: detect-secrets audit .secrets.baseline"
    fi
else
    warning "detect-secrets not installed. Install: pip install detect-secrets"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Scan 3: Gitleaks
# ═══════════════════════════════════════════════════════════════════════════

header "SCAN 3: Secret Leaks (gitleaks)"
((TOTAL_CHECKS++))

if check_command "gitleaks" "gitleaks"; then
    log "Scanning for leaked secrets..."

    if gitleaks detect --verbose --no-git > /dev/null 2>&1; then
        success "gitleaks: No secrets detected"
    else
        error "gitleaks: Potential secret leaks detected!"
        log "    Run manually: gitleaks detect --verbose"
        log "    Report: gitleaks detect --report-path gitleaks-report.json"
    fi
else
    warning "gitleaks not installed. Install: brew install gitleaks"
    log "    Or: https://github.com/gitleaks/gitleaks"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Scan 4: Pattern Matching (grep for common secrets)
# ═══════════════════════════════════════════════════════════════════════════

header "SCAN 4: Pattern Matching (manual grep)"
((TOTAL_CHECKS++))

log "Searching for common secret patterns..."

# Patterns to search for
PATTERNS=(
    "AKIA[0-9A-Z]{16}"          # AWS Access Key
    "AIza[0-9A-Za-z\\-_]{35}"   # Google API Key
    "sk-[a-zA-Z0-9]{48}"        # OpenAI API Key
    "sk-ant-[a-zA-Z0-9-]{95}"   # Claude API Key
    "ghp_[a-zA-Z0-9]{36}"       # GitHub Personal Access Token
    "gho_[a-zA-Z0-9]{36}"       # GitHub OAuth Token
    "password\\s*=\\s*['\"][^'\"]{8,}['\"]"  # Hardcoded passwords
    "api_key\\s*=\\s*['\"][^'\"]{8,}['\"]"   # API keys
    "secret\\s*=\\s*['\"][^'\"]{8,}['\"]"    # Secrets
    "token\\s*=\\s*['\"][^'\"]{8,}['\"]"     # Tokens
)

MATCHES_FOUND=0

for pattern in "${PATTERNS[@]}"; do
    MATCHES=$(git grep -E "$pattern" -- ':(exclude).env.example' ':(exclude)*.md' ':(exclude)*.log' ':(exclude)*.txt' 2>/dev/null | wc -l)
    if [ "$MATCHES" -gt 0 ]; then
        warning "Found $MATCHES matches for pattern: $pattern"
        ((MATCHES_FOUND += MATCHES))
    fi
done

if [ "$MATCHES_FOUND" -eq 0 ]; then
    success "Pattern matching: No suspicious patterns found"
else
    warning "Pattern matching: $MATCHES_FOUND potential matches found"
    log "    Review manually with: git grep -E 'pattern'"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Scan 5: File Permissions Check
# ═══════════════════════════════════════════════════════════════════════════

header "SCAN 5: File Permissions"
((TOTAL_CHECKS++))

log "Checking for files with sensitive permissions..."

# Check for world-writable files
WORLD_WRITABLE=$(find . -type f -perm -002 ! -path './.git/*' 2>/dev/null | wc -l)

if [ "$WORLD_WRITABLE" -eq 0 ]; then
    success "File permissions: No world-writable files"
else
    warning "Found $WORLD_WRITABLE world-writable files"
    find . -type f -perm -002 ! -path './.git/*' 2>/dev/null | head -10 | tee -a "$LOG_FILE"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Scan 6: .env File Check
# ═══════════════════════════════════════════════════════════════════════════

header "SCAN 6: Environment File Safety"
((TOTAL_CHECKS++))

log "Checking .env file status..."

# Check if .env is gitignored
if grep -q "^\.env$" .gitignore; then
    success ".env is properly gitignored"
else
    error ".env is NOT in .gitignore!"
fi

# Check if .env exists in git
if git ls-files | grep -q "^\.env$"; then
    error ".env file is tracked by git!"
    log "    CRITICAL: Remove immediately with: git rm --cached .env"
else
    success ".env is not tracked by git"
fi

# Check if .env.example exists
if [ -f ".env.example" ]; then
    success ".env.example exists for reference"

    # Check if .env.example has placeholder values
    if grep -qE "(YOUR_|CHANGE_ME|EXAMPLE_|test123|password123)" .env.example; then
        success ".env.example contains safe placeholder values"
    else
        warning ".env.example may contain real values - verify manually"
    fi
else
    warning ".env.example not found - consider creating one"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Scan 7: Dependency Vulnerabilities
# ═══════════════════════════════════════════════════════════════════════════

header "SCAN 7: Dependency Security"
((TOTAL_CHECKS++))

log "Checking for vulnerable dependencies..."

# npm audit (if package.json exists)
if [ -f "package.json" ]; then
    if check_command "npm" "npm"; then
        VULNS=$(npm audit --json 2>/dev/null | grep -c '"severity"' || echo "0")
        if [ "$VULNS" -eq 0 ]; then
            success "npm audit: No vulnerabilities found"
        else
            warning "npm audit: $VULNS vulnerabilities detected"
            log "    Run: npm audit fix"
        fi
    fi
fi

# pip audit (if requirements.txt exists)
if [ -f "requirements.txt" ]; then
    if check_command "pip-audit" "pip-audit"; then
        if pip-audit -r requirements.txt > /dev/null 2>&1; then
            success "pip-audit: No vulnerabilities found"
        else
            warning "pip-audit: Vulnerabilities detected"
            log "    Run: pip-audit -r requirements.txt"
        fi
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# Scan 8: Docker Security
# ═══════════════════════════════════════════════════════════════════════════

header "SCAN 8: Docker Security"
((TOTAL_CHECKS++))

if [ -f "docker-compose.yml" ]; then
    log "Checking docker-compose.yml for hardcoded secrets..."

    # Check for hardcoded passwords
    if grep -qE "(password|passwd|pwd):\\s*['\"]?[a-zA-Z0-9]{8,}['\"]?" docker-compose.yml; then
        warning "docker-compose.yml may contain hardcoded passwords"
        log "    Ensure these are development-only values"
    else
        success "docker-compose.yml: No obvious hardcoded passwords"
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# Scan 9: Large Files Check
# ═══════════════════════════════════════════════════════════════════════════

header "SCAN 9: Large Files"
((TOTAL_CHECKS++))

log "Checking for large files (>50MB)..."

LARGE_FILES=$(find . -type f -size +50M ! -path './.git/*' 2>/dev/null | wc -l)

if [ "$LARGE_FILES" -eq 0 ]; then
    success "No large files (>50MB) found"
else
    warning "Found $LARGE_FILES files larger than 50MB"
    find . -type f -size +50M ! -path './.git/*' -exec ls -lh {} \; 2>/dev/null | tee -a "$LOG_FILE"
    log "    Consider using Git LFS for large files"
fi

# ═══════════════════════════════════════════════════════════════════════════
# Final Report
# ═══════════════════════════════════════════════════════════════════════════

header "FINAL SECURITY SCAN REPORT"

log ""
log "Summary:"
log "  Total Checks: $TOTAL_CHECKS"
log "  ${GREEN}Passed: $PASSED_CHECKS${NC}"
log "  ${RED}Failed: $FAILED_CHECKS${NC}"
log "  ${YELLOW}Warnings: $WARNINGS${NC}"
log ""

if [ "$FAILED_CHECKS" -eq 0 ]; then
    success "ALL CRITICAL CHECKS PASSED ✅"
    log ""
    log "Repository appears SAFE for public release."
    log ""
    if [ "$WARNINGS" -gt 0 ]; then
        warning "However, there are $WARNINGS warnings to review."
        log "Review the warnings above and address if necessary."
    fi
else
    error "CRITICAL ISSUES FOUND! 🚨"
    log ""
    log "DO NOT make repository public until these issues are resolved:"
    log "1. Review all failed checks above"
    log "2. Remove any secrets/credentials found"
    log "3. Re-run this script"
    log ""
    log "If secrets were found in git history:"
    log "  - Consider using git-filter-repo to rewrite history"
    log "  - Or create a new repository with clean history"
    exit 1
fi

log ""
log "Detailed log saved to: $LOG_FILE"
log ""
log "Next steps:"
log "1. Review this report carefully"
log "2. Address any warnings if applicable"
log "3. If all looks good, proceed with publication plan"
log "4. After making public, enable GitHub secret scanning"
log ""

# ═══════════════════════════════════════════════════════════════════════════
# End of Script
# ═══════════════════════════════════════════════════════════════════════════
