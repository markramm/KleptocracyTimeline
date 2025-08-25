#!/bin/bash

# Pre-Launch Validation Script for Kleptocracy Timeline
# Run this before launch to ensure everything is ready

echo "=========================================="
echo "🚀 KLEPTOCRACY TIMELINE PRE-LAUNCH CHECK"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
ISSUES_FOUND=0

# Function to check command exists
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅ $1 is installed${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 is not installed${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        return 1
    fi
}

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅ $1 exists${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 is missing${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅ $1 exists${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 is missing${NC}"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        return 1
    fi
}

echo "1️⃣  Checking Prerequisites..."
echo "------------------------------"
check_command python3
check_command node
check_command npm
check_command git
echo ""

echo "2️⃣  Checking Project Structure..."
echo "-----------------------------------"
check_dir "timeline_data"
check_dir "timeline_data/events"
check_dir "viewer"
check_dir "viewer/src"
check_dir "tools"
check_dir "analysis"
check_dir ".github"
echo ""

echo "3️⃣  Checking Critical Files..."
echo "--------------------------------"
check_file "timeline_data/validate_yaml.py"
check_file "timeline_data/generate_static_api.py"
check_file "viewer/package.json"
check_file "viewer/src/App.js"
check_file "README.md"
check_file "CONTRIBUTING.md"
check_file "CODE_OF_CONDUCT.md"
check_file "LICENSE-MIT"
check_file "FAQ.md"
check_file "AI_INTEGRATION.md"
check_file "RESPONSE_TEMPLATES.md"
echo ""

echo "4️⃣  Validating Timeline Data..."
echo "---------------------------------"
cd timeline_data
if python3 validate_yaml.py > /dev/null 2>&1; then
    VALID_COUNT=$(python3 validate_yaml.py 2>/dev/null | grep "✅ Valid:" | grep -oE '[0-9]+' | head -1)
    echo -e "${GREEN}✅ All $VALID_COUNT YAML files are valid${NC}"
else
    echo -e "${RED}❌ YAML validation failed${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
cd ..
echo ""

echo "5️⃣  Checking Event Files..."
echo "-----------------------------"
EVENT_COUNT=$(find timeline_data/events -name "*.yaml" | wc -l)
echo "📊 Total events: $EVENT_COUNT"
if [ $EVENT_COUNT -gt 300 ]; then
    echo -e "${GREEN}✅ Sufficient events for launch${NC}"
else
    echo -e "${YELLOW}⚠️  Only $EVENT_COUNT events (expected 300+)${NC}"
fi

# Check for underscores in filenames (should be hyphens)
UNDERSCORE_FILES=$(find timeline_data/events -name "*_*.yaml" | wc -l)
if [ $UNDERSCORE_FILES -eq 0 ]; then
    echo -e "${GREEN}✅ No underscore naming issues${NC}"
else
    echo -e "${RED}❌ Found $UNDERSCORE_FILES files with underscores (should use hyphens)${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

echo "6️⃣  Testing React Application..."
echo "---------------------------------"
cd viewer
if npm run build > /dev/null 2>&1; then
    echo -e "${GREEN}✅ React app builds successfully${NC}"
    
    # Check bundle size
    if [ -d "build" ]; then
        BUNDLE_SIZE=$(du -sh build | cut -f1)
        echo "📦 Build size: $BUNDLE_SIZE"
    fi
else
    echo -e "${RED}❌ React build failed${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
cd ..
echo ""

echo "7️⃣  Checking Static API..."
echo "----------------------------"
if [ -f "viewer/public/api/timeline.json" ]; then
    EVENT_COUNT_API=$(python3 -c "import json; print(len(json.load(open('viewer/public/api/timeline.json'))['events']))" 2>/dev/null)
    if [ -n "$EVENT_COUNT_API" ]; then
        echo -e "${GREEN}✅ Static API contains $EVENT_COUNT_API events${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not parse timeline.json${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Static API not generated yet${NC}"
    echo "   Run: cd timeline_data && python3 generate_static_api.py"
fi
echo ""

echo "8️⃣  Checking Documentation..."
echo "-------------------------------"
AGENT_COUNT=$(find . -name "AGENT.md" -not -path "./node_modules/*" -not -path "./viewer/node_modules/*" | wc -l)
echo "📚 AGENT.md files: $AGENT_COUNT"
if [ $AGENT_COUNT -ge 5 ]; then
    echo -e "${GREEN}✅ Documentation comprehensive${NC}"
else
    echo -e "${YELLOW}⚠️  Only $AGENT_COUNT AGENT.md files found${NC}"
fi
echo ""

echo "9️⃣  Checking GitHub Integration..."
echo "------------------------------------"
check_file ".github/ISSUE_TEMPLATE/broken-link.yml"
check_file ".github/ISSUE_TEMPLATE/new-event.yml"
check_file ".github/ISSUE_TEMPLATE/event-correction.yml"
echo ""

echo "🔟 Checking Launch Materials..."
echo "---------------------------------"
check_file "ai-analysis/launch-materials/substack-announcement.md"
check_file "ai-analysis/launch-materials/x-twitter-thread.md"
check_file "LAUNCH_CHECKLIST.md"
check_file "PROJECT_HEALTH.md"
echo ""

echo "=========================================="
echo "📊 PRE-LAUNCH SUMMARY"
echo "=========================================="

if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED! Ready for launch.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Generate fresh static API: cd timeline_data && python3 generate_static_api.py"
    echo "2. Build for production: cd viewer && npm run build:gh-pages"
    echo "3. Test locally: cd viewer && npm start"
    echo "4. Create backup: tar -czf kleptocracy-timeline-backup.tar.gz ."
    echo "5. Review LAUNCH_CHECKLIST.md for final tasks"
else
    echo -e "${RED}❌ Found $ISSUES_FOUND issues that need attention${NC}"
    echo ""
    echo "Please fix the issues above before launching."
    echo "See LAUNCH_CHECKLIST.md for detailed tasks."
fi

echo ""
echo "=========================================="
echo "🚀 Launch URL: https://markramm.github.io/KleptocracyTimeline/"
echo "📝 Substack: https://theramm.substack.com/"
echo "💻 GitHub: https://github.com/markramm/KleptocracyTimeline"
echo "=========================================="

exit $ISSUES_FOUND