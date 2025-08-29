#!/bin/bash

# Test script to run all pre-commit checks manually
# Run this before committing to catch issues early

echo "🧪 Running pre-commit tests manually..."
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Track overall success
ALL_PASS=1

# Save current directory
ORIG_DIR=$(pwd)

# 1. YAML Schema Validation
echo "📋 Test 1/4: YAML Schema Validation"
echo "-----------------------------------"
cd timeline_data
if python3 validate_yaml.py; then
    echo -e "${GREEN}✅ YAML validation passed${NC}"
else
    echo -e "${RED}❌ YAML validation failed${NC}"
    ALL_PASS=0
fi
cd "$ORIG_DIR"
echo ""

# 2. Date Validation
echo "📅 Test 2/4: Date Logic Validation"
echo "----------------------------------"
if [ -f "tools/validation/validate_timeline_dates.py" ]; then
    if python3 tools/validation/validate_timeline_dates.py; then
        echo -e "${GREEN}✅ Date validation passed${NC}"
    else
        echo -e "${RED}❌ Date validation failed${NC}"
        ALL_PASS=0
    fi
else
    echo -e "${YELLOW}⚠️  Date validation script not found${NC}"
fi
echo ""

# 3. API Generation Test
echo "🔧 Test 3/4: API Generation"
echo "--------------------------"
if python3 timeline_data/generate_static_api.py; then
    # Check if files were created
    if [ -f "viewer/public/api/timeline.json" ]; then
        # Test JSON validity
        if python3 -m json.tool viewer/public/api/timeline.json > /dev/null 2>&1; then
            echo -e "${GREEN}✅ API generation successful${NC}"
        else
            echo -e "${RED}❌ Generated JSON is invalid${NC}"
            ALL_PASS=0
        fi
    else
        echo -e "${RED}❌ API files not created${NC}"
        ALL_PASS=0
    fi
else
    echo -e "${RED}❌ API generation failed${NC}"
    ALL_PASS=0
fi
echo ""

# 4. React Build Test
echo "🏗️  Test 4/4: React Build Test"
echo "-----------------------------"
echo "This will take a moment..."
cd viewer

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies first..."
    npm install
fi

# Test the build
echo "Building with production settings..."
if PUBLIC_URL=/KleptocracyTimeline npm run build 2>&1 | tee /tmp/build-output.txt | grep -E "(Compiled|Failed|Error|Warning)"; then
    if grep -q "Failed to compile" /tmp/build-output.txt; then
        echo -e "${RED}❌ React build failed - see errors above${NC}"
        ALL_PASS=0
    elif [ -d "build" ]; then
        echo -e "${GREEN}✅ React build successful${NC}"
        # Clean up
        rm -rf build
    else
        echo -e "${RED}❌ Build directory not created${NC}"
        ALL_PASS=0
    fi
else
    echo -e "${RED}❌ Build command failed${NC}"
    ALL_PASS=0
fi

cd "$ORIG_DIR"
rm -f /tmp/build-output.txt
echo ""

# Summary
echo "=================================="
if [ "$ALL_PASS" = "1" ]; then
    echo -e "${GREEN}✨ All tests passed! Safe to commit.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Fix issues before committing.${NC}"
    exit 1
fi