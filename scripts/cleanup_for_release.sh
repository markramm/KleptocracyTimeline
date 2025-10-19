#!/bin/bash
#
# Cleanup Script for Release Preparation
#
# This script removes legacy files, temporary artifacts, and cleans up
# the repository for a clean release.
#
# Usage: ./scripts/cleanup_for_release.sh [--dry-run]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DRY_RUN=false

if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
    echo -e "${YELLOW}DRY RUN MODE - No files will be deleted${NC}"
    echo ""
fi

# Get repository root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Kleptocracy Timeline - Release Cleanup ==="
echo "Repository: $REPO_ROOT"
echo ""

# Counter for cleanup actions
DELETED_COUNT=0

# Function to remove file/directory
remove_item() {
    local item="$1"
    if [ -e "$item" ] || [ -d "$item" ]; then
        echo -e "${YELLOW}Removing:${NC} $item"
        if [ "$DRY_RUN" = false ]; then
            rm -rf "$item"
            DELETED_COUNT=$((DELETED_COUNT + 1))
        fi
    fi
}

echo "Phase 1: Removing Legacy Directories"
echo "-------------------------------------"
remove_item "research_monitor"
remove_item "api"
remove_item "research_api.py"
echo ""

echo "Phase 2: Removing Duplicate Databases"
echo "--------------------------------------"
remove_item "unified_research.db"
remove_item "unified_research.db-wal"
remove_item "unified_research.db-shm"
echo ""

echo "Phase 3: Removing Backup Files"
echo "-------------------------------"
find . -name "*.backup" -type f | while read -r file; do
    remove_item "$file"
done
find . -name "*.bak" -type f | while read -r file; do
    remove_item "$file"
done
find . -name "*.old" -type f | while read -r file; do
    remove_item "$file"
done
echo ""

echo "Phase 4: Removing Python Cache"
echo "-------------------------------"
find . -type d -name "__pycache__" | while read -r dir; do
    remove_item "$dir"
done
find . -type f -name "*.pyc" | while read -r file; do
    remove_item "$file"
done
find . -type d -name ".pytest_cache" | while read -r dir; do
    remove_item "$dir"
done
find . -type d -name ".mypy_cache" | while read -r dir; do
    remove_item "$dir"
done
echo ""

echo "Phase 5: Removing Stale Log Files"
echo "----------------------------------"
remove_item "research-server/server/monitor.log"
remove_item "research-server/server/server.log"
remove_item "timeline_data/scrape_output_full.log"
remove_item "timeline_data/archive_slow.log"
remove_item "timeline_data/scrape_output.log"
remove_item "timeline_data/archive.log"
echo ""

echo "Phase 6: Removing Hugo Build Artifacts"
echo "---------------------------------------"
remove_item "timeline/.hugo_build.lock"
remove_item "timeline/public"
remove_item "timeline/archetypes"
echo ""

echo "Phase 7: Removing Node Modules (if needed)"
echo "-------------------------------------------"
if [ -d "timeline/viewer/node_modules" ]; then
    echo -e "${YELLOW}Note:${NC} timeline/viewer/node_modules exists (not removing, run npm install to restore)"
fi
echo ""

echo "=== Cleanup Summary ==="
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN:${NC} Would have removed/cleaned items"
else
    echo -e "${GREEN}Removed:${NC} $DELETED_COUNT items"
fi
echo ""

echo "=== Verification ==="
echo "Checking for remaining issues..."

# Check for remaining backup files
BACKUP_COUNT=$(find . -name "*.backup" -o -name "*.bak" -o -name "*.old" 2>/dev/null | wc -l | tr -d ' ')
if [ "$BACKUP_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Warning:${NC} Found $BACKUP_COUNT backup files still present"
else
    echo -e "${GREEN}✓${NC} No backup files found"
fi

# Check for Python cache
PYCACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PYCACHE_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}Warning:${NC} Found $PYCACHE_COUNT __pycache__ directories"
else
    echo -e "${GREEN}✓${NC} No Python cache directories found"
fi

# Check for legacy directories
if [ -d "research_monitor" ] || [ -d "api" ]; then
    echo -e "${YELLOW}Warning:${NC} Legacy directories still present"
else
    echo -e "${GREEN}✓${NC} Legacy directories removed"
fi

echo ""
echo "=== Next Steps ==="
echo "1. Review changes with: git status"
echo "2. Run tests: cd research-server && pytest tests/"
echo "3. Start server: ./research server-start"
echo "4. Verify functionality: ./research get-stats"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}To actually perform cleanup, run:${NC}"
    echo "  $0"
else
    echo -e "${GREEN}Cleanup complete!${NC}"
fi
