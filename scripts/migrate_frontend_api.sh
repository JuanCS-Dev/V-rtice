#!/bin/bash
# Auto-Migration Script: Frontend API Integration
# Migrates hardcoded localhost URLs to use apiClient
# Governed by: Constituição Vértice v2.7

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[MIGRATE]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; }

FRONTEND_DIR="/home/juan/vertice-dev/frontend"
SRC_DIR="$FRONTEND_DIR/src"
REPORT_FILE="/tmp/migration_report_$(date +%Y%m%d_%H%M%S).txt"

cd "$FRONTEND_DIR"

echo "════════════════════════════════════════════════════════════════" | tee "$REPORT_FILE"
echo " AUTO-MIGRATION: Frontend API Integration" | tee -a "$REPORT_FILE"
echo " Started: $(date)" | tee -a "$REPORT_FILE"
echo "════════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Counters
TOTAL_FILES=0
MIGRATED=0
SKIPPED=0
FAILED=0

# Find all files with hardcoded localhost
log "Scanning for files with hardcoded URLs..."
FILES=$(find "$SRC_DIR/components" "$SRC_DIR/hooks" -type f \( -name "*.js" -o -name "*.jsx" \) -exec grep -l "localhost:8[0-9]" {} \; 2>/dev/null || true)

TOTAL_FILES=$(echo "$FILES" | wc -l)
log "Found $TOTAL_FILES files to process"
echo "" | tee -a "$REPORT_FILE"

# Migration patterns
migrate_file() {
    local file="$1"
    local basename=$(basename "$file")
    local changed=false
    
    log "Processing: $basename"
    
    # Backup
    cp "$file" "${file}.bak"
    
    # Pattern 1: Simple fetch with localhost:8000
    if grep -q "localhost:8000" "$file"; then
        # Add import if not present
        if ! grep -q "import.*apiClient.*from.*@/api/client" "$file" && 
           ! grep -q "import.*apiClient.*from.*'@/api/client'" "$file"; then
            
            # Find the last import line
            last_import=$(grep -n "^import" "$file" | tail -1 | cut -d: -f1)
            if [ -n "$last_import" ]; then
                sed -i "${last_import}a import { apiClient } from '@/api/client';" "$file"
                changed=true
            fi
        fi
        
        # Replace fetch patterns (only for 8000, Gateway endpoints)
        # Pattern: fetch(`http://localhost:8000/endpoint`)
        sed -i "s|fetch(\`http://localhost:8000/\([^'\"]*\)\`)|apiClient.get('/\1')|g" "$file"
        sed -i "s|fetch('http://localhost:8000/\([^'\"]*\)')|apiClient.get('/\1')|g" "$file"
        sed -i 's|fetch("http://localhost:8000/\([^"]*\)")|apiClient.get("/\1")|g' "$file"
        
        # Pattern: fetch with POST
        # This is complex, mark for manual review
        if grep -q "method.*POST.*localhost:8000" "$file"; then
            warn "  → Manual review needed: POST request found"
            echo "  MANUAL: $file (POST request)" >> "$REPORT_FILE"
        fi
        
        changed=true
    fi
    
    # Pattern 2: Other ports (8001, 8099, etc) - mark for review
    if grep -qE "localhost:8[0-9]{3}" "$file" | grep -v "localhost:8000"; then
        warn "  → Non-Gateway port found, needs review"
        echo "  REVIEW: $file (non-8000 port)" >> "$REPORT_FILE"
    fi
    
    if [ "$changed" = true ]; then
        # Validate syntax
        if npx eslint "$file" --fix > /dev/null 2>&1; then
            success "  ✓ Migrated and validated: $basename"
            rm "${file}.bak"
            MIGRATED=$((MIGRATED + 1))
            echo "  OK: $file" >> "$REPORT_FILE"
        else
            fail "  ✗ ESLint failed, reverting: $basename"
            mv "${file}.bak" "$file"
            FAILED=$((FAILED + 1))
            echo "  FAILED: $file" >> "$REPORT_FILE"
        fi
    else
        SKIPPED=$((SKIPPED + 1))
        rm "${file}.bak"
    fi
}

# Process components
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo " MIGRATING COMPONENTS" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"

for file in $FILES; do
    if [[ "$file" == *"/components/"* ]]; then
        migrate_file "$file"
    fi
done

# Process hooks
echo "" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo " MIGRATING HOOKS" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"

for file in $FILES; do
    if [[ "$file" == *"/hooks/"* ]]; then
        migrate_file "$file"
    fi
done

# Summary
echo "" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo " MIGRATION SUMMARY" | tee -a "$REPORT_FILE"
echo "══════════════════════════════════════════════════════════════" | tee -a "$REPORT_FILE"
echo "Total files scanned:  $TOTAL_FILES" | tee -a "$REPORT_FILE"
echo "Successfully migrated: $MIGRATED" | tee -a "$REPORT_FILE"
echo "Skipped (no changes):  $SKIPPED" | tee -a "$REPORT_FILE"
echo "Failed (reverted):     $FAILED" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

if [ $FAILED -eq 0 ]; then
    success "✅ Migration completed successfully!"
    echo "Report: $REPORT_FILE"
    exit 0
else
    warn "⚠️  Migration completed with $FAILED failures"
    echo "Report: $REPORT_FILE"
    exit 1
fi
