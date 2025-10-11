#!/bin/bash
# =============================================================================
# Vértice Platform - Configuration Validation Script
# =============================================================================
# Purpose: Validate environment variable configuration across all services
# Usage: ./scripts/maintenance/validate-configs.sh [service_name]
# Author: MAXIMUS Team
# Date: 2025-10-11
# =============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL=0
PASSED=0
FAILED=0
WARNINGS=0

# =============================================================================
# FUNCTIONS
# =============================================================================

print_header() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Vértice Platform - Configuration Validation${NC}"
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

print_info() {
    echo -e "  $1"
}

# Check if .env file exists
check_env_file() {
    local service_dir="$1"
    local service_name="$2"
    
    TOTAL=$((TOTAL + 1))
    
    if [ -f "$service_dir/.env" ]; then
        print_success "$service_name: .env file exists"
        PASSED=$((PASSED + 1))
    else
        print_warning "$service_name: .env file missing"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# Check if .env.example exists
check_env_example() {
    local service_dir="$1"
    local service_name="$2"
    
    TOTAL=$((TOTAL + 1))
    
    if [ -f "$service_dir/.env.example" ]; then
        print_success "$service_name: .env.example exists"
        PASSED=$((PASSED + 1))
    else
        print_error "$service_name: .env.example missing"
        FAILED=$((FAILED + 1))
        print_info "Run: cd $service_dir && python -c \"from backend.shared.base_config import generate_env_example; from config import Config; print(generate_env_example(Config))\" > .env.example"
    fi
}

# Check if config.py exists
check_config_file() {
    local service_dir="$1"
    local service_name="$2"
    
    TOTAL=$((TOTAL + 1))
    
    if [ -f "$service_dir/config.py" ]; then
        print_success "$service_name: config.py exists"
        PASSED=$((PASSED + 1))
        return 0
    else
        print_error "$service_name: config.py missing"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Validate config.py uses BaseServiceConfig
check_base_config_usage() {
    local service_dir="$1"
    local service_name="$2"
    
    TOTAL=$((TOTAL + 1))
    
    if grep -q "BaseServiceConfig" "$service_dir/config.py" 2>/dev/null; then
        print_success "$service_name: Uses BaseServiceConfig"
        PASSED=$((PASSED + 1))
    else
        print_warning "$service_name: Not using BaseServiceConfig"
        WARNINGS=$((WARNINGS + 1))
        print_info "Migrate to: from backend.shared.base_config import BaseServiceConfig"
    fi
}

# Try to import and validate configuration
validate_config_import() {
    local service_dir="$1"
    local service_name="$2"
    
    TOTAL=$((TOTAL + 1))
    
    # Create temporary test script
    local test_script=$(mktemp)
    cat > "$test_script" << EOF
import sys
import os

# Add service directory to path
sys.path.insert(0, '$service_dir')
sys.path.insert(0, '$(pwd)/backend')

# Set minimal required env vars
os.environ.setdefault('SERVICE_NAME', '$service_name')
os.environ.setdefault('SERVICE_PORT', '8999')
os.environ.setdefault('VERTICE_ENV', 'testing')

try:
    from config import *
    print("SUCCESS: Configuration imported successfully")
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
EOF

    # Run validation
    if python3 "$test_script" > /dev/null 2>&1; then
        print_success "$service_name: Configuration validates"
        PASSED=$((PASSED + 1))
    else
        print_error "$service_name: Configuration validation failed"
        FAILED=$((FAILED + 1))
        # Show error
        python3 "$test_script" 2>&1 | head -3 | while read line; do
            print_info "$line"
        done
    fi
    
    rm -f "$test_script"
}

# Check for hardcoded secrets
check_hardcoded_secrets() {
    local service_dir="$1"
    local service_name="$2"
    
    TOTAL=$((TOTAL + 1))
    
    # Patterns that might indicate hardcoded secrets
    local patterns=(
        "password.*=.*['\"].*['\"]"
        "secret.*=.*['\"].*['\"]"
        "api_key.*=.*['\"].*['\"]"
        "token.*=.*['\"].*['\"]"
    )
    
    local found=0
    for pattern in "${patterns[@]}"; do
        if grep -rE "$pattern" "$service_dir"/*.py 2>/dev/null | grep -v "example" | grep -v ".pyc" > /dev/null; then
            found=1
            break
        fi
    done
    
    if [ $found -eq 0 ]; then
        print_success "$service_name: No hardcoded secrets detected"
        PASSED=$((PASSED + 1))
    else
        print_error "$service_name: Potential hardcoded secrets found"
        FAILED=$((FAILED + 1))
        print_info "Search for: password/secret/api_key/token assignments"
    fi
}

# Validate a single service
validate_service() {
    local service_dir="$1"
    local service_name=$(basename "$service_dir")
    
    echo ""
    print_section "Validating: $service_name"
    echo ""
    
    check_env_file "$service_dir" "$service_name"
    check_env_example "$service_dir" "$service_name"
    
    if check_config_file "$service_dir" "$service_name"; then
        check_base_config_usage "$service_dir" "$service_name"
        validate_config_import "$service_dir" "$service_name"
    fi
    
    check_hardcoded_secrets "$service_dir" "$service_name"
}

# Print summary
print_summary() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Validation Summary${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "Total Checks:    $TOTAL"
    echo -e "${GREEN}Passed:          $PASSED${NC}"
    echo -e "${YELLOW}Warnings:        $WARNINGS${NC}"
    echo -e "${RED}Failed:          $FAILED${NC}"
    echo ""
    
    local percentage=$((PASSED * 100 / TOTAL))
    echo -e "Success Rate:    ${percentage}%"
    echo ""
    
    if [ $FAILED -eq 0 ] && [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✓ All validations passed!${NC}"
        return 0
    elif [ $FAILED -eq 0 ]; then
        echo -e "${YELLOW}⚠ Validations passed with warnings${NC}"
        return 0
    else
        echo -e "${RED}✗ Validation failed${NC}"
        return 1
    fi
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    print_header
    
    # Determine services to validate
    if [ $# -eq 1 ]; then
        # Single service specified
        local service_name="$1"
        local service_dir="backend/services/${service_name}"
        
        if [ ! -d "$service_dir" ]; then
            print_error "Service not found: $service_name"
            exit 1
        fi
        
        validate_service "$service_dir"
    else
        # Validate all services
        print_section "Scanning for services..."
        echo ""
        
        local services_found=0
        for service_dir in backend/services/*/; do
            if [ -d "$service_dir" ]; then
                validate_service "$service_dir"
                services_found=$((services_found + 1))
            fi
        done
        
        if [ $services_found -eq 0 ]; then
            print_warning "No services found in backend/services/"
        fi
    fi
    
    # Print summary
    print_summary
}

# Run main
main "$@"
