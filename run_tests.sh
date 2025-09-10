#!/bin/bash

# Test runner script for Kleptocracy Timeline project

echo "🧪 Kleptocracy Timeline Test Runner"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not found${NC}"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade test dependencies
echo "Checking test dependencies..."
pip install -q --upgrade pytest pytest-cov flask sqlalchemy 2>/dev/null

# Parse command line arguments
TEST_TYPE=${1:-"all"}
COVERAGE=${2:-"yes"}

case $TEST_TYPE in
    "unit")
        echo -e "\n${GREEN}Running Unit Tests...${NC}"
        if [ "$COVERAGE" = "yes" ]; then
            python -m pytest tests/test_validation_functions.py tests/test_utils.py -v --cov=research_monitor --cov=api
        else
            python -m pytest tests/test_validation_functions.py tests/test_utils.py -v
        fi
        ;;
    
    "integration")
        echo -e "\n${GREEN}Running Integration Tests...${NC}"
        if [ "$COVERAGE" = "yes" ]; then
            python -m pytest tests/test_api_integration.py tests/test_event_submission_pipeline.py -v --cov=api --cov=research_monitor
        else
            python -m pytest tests/test_api_integration.py tests/test_event_submission_pipeline.py -v
        fi
        ;;
    
    "validation")
        echo -e "\n${GREEN}Running Validation Tests...${NC}"
        python -m pytest tests/test_validation_functions.py tests/test_timeline_validation.py -v
        ;;
    
    "quick")
        echo -e "\n${GREEN}Running Quick Test Suite (Unit tests only)...${NC}"
        python -m pytest tests/test_validation_functions.py tests/test_utils.py -q
        ;;
    
    "coverage")
        echo -e "\n${GREEN}Running Full Test Suite with Coverage Report...${NC}"
        python -m pytest tests/ --cov=api --cov=research_monitor --cov-report=term --cov-report=html
        echo -e "\n${YELLOW}Coverage HTML report generated in htmlcov/index.html${NC}"
        ;;
    
    "all"|*)
        echo -e "\n${GREEN}Running All Tests...${NC}"
        if [ "$COVERAGE" = "yes" ]; then
            python -m pytest tests/ -v --cov=api --cov=research_monitor --cov-report=term-missing:skip-covered
        else
            python -m pytest tests/ -v
        fi
        ;;
esac

# Get test results
TEST_RESULT=$?

# Summary
echo ""
echo "===================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo "Run with 'coverage' option for detailed report:"
    echo "  ./run_tests.sh coverage"
fi

echo ""
echo "Usage:"
echo "  ./run_tests.sh [test_type] [coverage]"
echo ""
echo "Test types:"
echo "  all         - Run all tests (default)"
echo "  unit        - Run unit tests only"
echo "  integration - Run integration tests only" 
echo "  validation  - Run validation tests only"
echo "  quick       - Run quick unit test suite"
echo "  coverage    - Run all tests with HTML coverage report"
echo ""
echo "Coverage options:"
echo "  yes - Include coverage report (default)"
echo "  no  - Skip coverage report"

exit $TEST_RESULT