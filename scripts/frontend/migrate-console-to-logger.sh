#!/bin/bash
#
# Frontend Console to Logger Migration Script
# ============================================
#
# Purpose: Replace all console.* statements with logger.* equivalents
# Usage: ./migrate-console-to-logger.sh
# Author: MAXIMUS Team
# Date: 2025-10-11

set -e
set -u

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FRONTEND_SRC="/home/juan/vertice-dev/frontend/src"
BACKUP_DIR="/home/juan/vertice-dev/frontend/.migration-backup-$(date +%Y%m%d-%H%M%S)"

echo -e "${BLUE}Console → Logger Migration${NC}"
echo ""

# Step 1: Backup
echo -e "${YELLOW}[1/5] Creating backup...${NC}"
mkdir -p "$BACKUP_DIR"
cp -r "$FRONTEND_SRC" "$BACKUP_DIR/"
echo -e "${GREEN}✓ Backup: $BACKUP_DIR${NC}"
echo ""

# Step 2: Analyze
echo -e "${YELLOW}[2/5] Analyzing...${NC}"
cd "$FRONTEND_SRC"

TOTAL=$(find . -type f \( -name "*.jsx" -o -name "*.js" \) \
  ! -path "*/node_modules/*" ! -path "*/dist/*" ! -path "*/__tests__/*" \
  -exec grep -h "console\." {} \; | wc -l)

echo "  Total console statements: $TOTAL"
echo ""

# Step 3: Add imports
echo -e "${YELLOW}[3/5] Adding logger imports...${NC}"
FILES=$(find . -type f \( -name "*.jsx" -o -name "*.js" \) \
  ! -path "*/node_modules/*" ! -path "*/dist/*" ! -path "*/__tests__/*" \
  -exec grep -l "console\." {} \;)

ADDED=0
for file in $FILES; do
  if ! grep -q "import.*logger" "$file"; then
    # Add import after first import or at top
    if grep -q "^import" "$file"; then
      sed -i "1a import logger from '@/utils/logger';" "$file"
    else
      sed -i "1i import logger from '@/utils/logger';" "$file"
    fi
    ADDED=$((ADDED + 1))
  fi
done

echo -e "${GREEN}✓ Added imports to $ADDED files${NC}"
echo ""

# Step 4: Replace
echo -e "${YELLOW}[4/5] Replacing console statements...${NC}"

for file in $FILES; do
  sed -i 's/console\.log(/logger.debug(/g' "$file"
  sed -i 's/console\.debug(/logger.debug(/g' "$file"
  sed -i 's/console\.info(/logger.info(/g' "$file"
  sed -i 's/console\.warn(/logger.warn(/g' "$file"
  sed -i 's/console\.error(/logger.error(/g' "$file"
  sed -i 's/console\.table(/logger.table(/g' "$file"
done

echo -e "${GREEN}✓ Replacements complete${NC}"
echo ""

# Step 5: Verify
echo -e "${YELLOW}[5/5] Verifying...${NC}"
REMAINING=$(find . -type f \( -name "*.jsx" -o -name "*.js" \) \
  ! -path "*/node_modules/*" ! -path "*/dist/*" ! -path "*/utils/logger.js" \
  -exec grep -h "console\." {} \; | wc -l || echo "0")

echo "  Remaining console.*: $REMAINING"
echo ""

if [ "$REMAINING" -eq 0 ]; then
  echo -e "${GREEN}✓ MIGRATION SUCCESSFUL!${NC}"
else
  echo -e "${YELLOW}⚠ $REMAINING statements need manual review${NC}"
fi

echo ""
echo "Backup: $BACKUP_DIR"
echo ""

exit 0
