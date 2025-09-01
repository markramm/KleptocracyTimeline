#!/bin/bash
# Quick validation script for newly added events
# Run this after adding events to ensure they're valid

echo "🔍 Validating Timeline Events"
echo "============================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

# Get the most recently modified events (last 20)
echo "📋 Checking recently modified events..."
echo ""

# Find events modified in the last 24 hours
RECENT_FILES=$(find timeline_data/events -name "*.yaml" -mtime -1 2>/dev/null)

if [ -z "$RECENT_FILES" ]; then
    echo "No events modified in the last 24 hours."
    echo "Checking all events instead..."
    echo ""
    
    # Validate all events
    if python3 yaml_tools.py validate 2>&1 | grep -q "✓ All .* events validated successfully"; then
        echo -e "${GREEN}✅ All events are valid!${NC}"
        exit 0
    else
        echo -e "${RED}❌ Validation errors found${NC}"
        python3 yaml_tools.py validate 2>&1 | grep -E "Error|error|Warning|warning"
        exit 1
    fi
else
    echo "Found $(echo "$RECENT_FILES" | wc -l) recently modified event(s):"
    echo "$RECENT_FILES" | while read file; do
        echo "  - $(basename $file)"
    done
    echo ""
    
    # Track if all pass
    ALL_VALID=true
    
    # Validate each recent file
    echo "$RECENT_FILES" | while read file; do
        if [ -n "$file" ]; then
            echo -n "Validating $(basename $file)... "
            
            # Run validation
            OUTPUT=$(python3 yaml_tools.py validate "$file" 2>&1)
            
            if echo "$OUTPUT" | grep -q "✓ Validation passed"; then
                echo -e "${GREEN}✅${NC}"
            else
                echo -e "${RED}❌${NC}"
                echo "$OUTPUT" | grep -E "Error|Warning" | sed 's/^/    /'
                ALL_VALID=false
            fi
        fi
    done
    
    echo ""
    
    # Also check date serialization issue
    echo "🗓️  Checking for date serialization issues..."
    if python3 -c "
import yaml
from pathlib import Path
import datetime
import sys

issues = []
for file in '''$RECENT_FILES'''.strip().split('\n'):
    if not file:
        continue
    with open(file, 'r') as f:
        data = yaml.safe_load(f)
        if isinstance(data.get('date'), (datetime.date, datetime.datetime)):
            issues.append(f'{Path(file).name}: date is object, should be string')

if issues:
    print('❌ Date serialization issues found:')
    for issue in issues:
        print(f'  - {issue}')
    sys.exit(1)
else:
    print('✅ No date serialization issues')
    " 2>&1; then
        echo -e "${GREEN}✅ Date formats are correct${NC}"
    else
        echo -e "${RED}❌ Fix date formats before committing${NC}"
        ALL_VALID=false
    fi
    
    echo ""
    
    # Try API generation
    echo "🔧 Testing API generation..."
    if python3 api/generate_static_api.py > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API generation successful${NC}"
    else
        echo -e "${RED}❌ API generation failed - likely date serialization issue${NC}"
        ALL_VALID=false
    fi
    
    echo ""
    echo "============================="
    
    if [ "$ALL_VALID" = "true" ]; then
        echo -e "${GREEN}✨ All validations passed!${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Run: python3 api/generate_static_api.py"
        echo "2. Update RAG: cd rag && python3 update_rag_index.py"
        echo "3. Commit your changes"
        exit 0
    else
        echo -e "${RED}❌ Some validations failed. Fix issues before committing.${NC}"
        exit 1
    fi
fi