#!/bin/bash
# =============================================================================
# Vértice Platform - Enable OpenAPI Documentation
# =============================================================================
# Purpose: Enable /docs endpoints across all services
# Usage: ./scripts/setup/enable-openapi-docs.sh
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

# Counters
TOTAL=0
ENABLED=0
SKIPPED=0

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Vértice Platform - Enable OpenAPI Documentation${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Function to enable OpenAPI in a service
enable_openapi() {
    local service_dir="$1"
    local service_name=$(basename "$service_dir")
    
    TOTAL=$((TOTAL + 1))
    
    # Check if main.py exists
    if [ ! -f "$service_dir/main.py" ]; then
        echo -e "${YELLOW}⚠${NC} $service_name: No main.py found, skipping"
        SKIPPED=$((SKIPPED + 1))
        return
    fi
    
    # Check if already using OpenAPI config
    if grep -q "create_openapi_config" "$service_dir/main.py"; then
        echo -e "${GREEN}✓${NC} $service_name: Already configured"
        ENABLED=$((ENABLED + 1))
        return
    fi
    
    echo -e "${BLUE}▶${NC} $service_name: Enabling OpenAPI..."
    
    # Backup original
    cp "$service_dir/main.py" "$service_dir/main.py.bak"
    
    # Create updated main.py with OpenAPI
    python3 << EOF
import re

# Read original main.py
with open("$service_dir/main.py", "r") as f:
    content = f.read()

# Check if FastAPI is imported
if "from fastapi import FastAPI" not in content:
    print("  ⚠ No FastAPI import found, skipping")
    exit(1)

# Add OpenAPI import if not present
if "create_openapi_config" not in content:
    # Find FastAPI import line
    content = re.sub(
        r"(from fastapi import [^\n]+)",
        r"\1\nfrom backend.shared.openapi_config import create_openapi_config",
        content,
        count=1
    )

# Find FastAPI instantiation and add OpenAPI config
# Pattern: app = FastAPI()
if "app = FastAPI()" in content:
    service_name_clean = "$service_name".replace("_", " ").title()
    content = content.replace(
        "app = FastAPI()",
        f'''app = FastAPI(
    **create_openapi_config(
        service_name="{service_name_clean}",
        service_description="TODO: Add service description",
        version="1.0.0",
        tags=[
            {{
                "name": "health",
                "description": "Health check endpoints"
            }},
            {{
                "name": "core",
                "description": "Core service endpoints"
            }}
        ]
    )
)'''
    )

# Write updated content
with open("$service_dir/main.py", "w") as f:
    f.write(content)

print("  ✓ OpenAPI configuration added")
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $service_name: OpenAPI enabled"
        ENABLED=$((ENABLED + 1))
        rm "$service_dir/main.py.bak"
    else
        echo -e "${RED}✗${NC} $service_name: Failed to enable OpenAPI"
        mv "$service_dir/main.py.bak" "$service_dir/main.py"
        SKIPPED=$((SKIPPED + 1))
    fi
}

# Process all services
for service_dir in backend/services/*/; do
    if [ -d "$service_dir" ]; then
        enable_openapi "$service_dir"
    fi
done

# Summary
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Summary${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Total services:  $TOTAL"
echo -e "${GREEN}Enabled:         $ENABLED${NC}"
echo -e "${YELLOW}Skipped:         $SKIPPED${NC}"
echo ""

if [ $ENABLED -gt 0 ]; then
    echo -e "${GREEN}✓ OpenAPI documentation enabled for $ENABLED services${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Update service descriptions in each main.py"
    echo "2. Add endpoint tags to routes"
    echo "3. Add request/response examples"
    echo "4. Start services and visit http://localhost:{PORT}/docs"
fi
