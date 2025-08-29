# Testing Documentation - Kleptocracy Timeline

## Overview

This project includes comprehensive testing across multiple layers:
- **YAML validation** for timeline event data integrity
- **Python tests** for backend services and tools
- **JavaScript/React tests** for the frontend viewer
- **Pre-commit hooks** for catching issues before commit
- **GitHub Actions** for CI/CD validation

## Test Suites

### 1. YAML Event Validation

#### Basic Validation
```bash
# Validate all timeline events
python timeline_data/validate_yaml.py

# Validate specific event
python timeline_data/validate_yaml.py timeline_data/events/specific-event.yaml
```

#### Enhanced Validation (NEW)
```bash
# Validate with improvement suggestions
python yaml_tools.py validate

# Check specific file
python yaml_tools.py validate timeline_data/events/event.yaml

# Check source quality
python yaml_tools.py sources timeline_data/events/event.yaml --action validate

# Check for broken URLs
python yaml_tools.py sources timeline_data/events/event.yaml --action check-urls
```

#### Date Validation
```bash
# Check for future confirmed events and date logic
python tools/validation/validate_timeline_dates.py
```

### 2. Python Tests

#### YAML Tools Tests (NEW)
```bash
# Run YAML management tools tests
python test_yaml_tools.py

# Run with verbose output
python test_yaml_tools.py -v
```

**Coverage: 22 tests**
- Search functionality (6 tests)
- Edit operations (3 tests)
- Source management (3 tests)
- Validation logic (5 tests)
- Bulk operations (1 test)
- CLI interface (1 test)
- Utility functions (3 tests)

#### Backend Server Tests
```bash
# Run all Python tests with pytest
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_enhanced_server.py

# Run with coverage
python -m pytest tests/ --cov=api --cov-report=html
```

**Available test files:**
- `tests/test_enhanced_server_comprehensive.py` - 12 tests
- `tests/test_monitoring_system.py` - 4 tests
- `tests/test_timeline_server.py`
- `tests/test_server_simple.py`
- `tests/test_static_generation.py`
- `tests/test_scripts.py`
- `tests/test_utils.py`

### 3. JavaScript/React Tests

#### React App Tests
```bash
# Run from viewer directory
cd viewer

# Run tests (interactive)
npm test

# Run tests once (CI mode)
CI=true npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test App.test.js
```

**Coverage: 12 tests in App.test.js**
- Rendering and initialization
- Event loading and display
- Search functionality
- Tag filtering
- Error handling
- Event detail display
- Year navigation
- Statistics display
- Responsive design
- Empty/loading states

### 4. Pre-commit Hooks

#### Current Hook (Basic)
Located at `.git/hooks/pre-commit`
- ✅ YAML schema validation
- ✅ Date validation for timeline events

#### Enhanced Hook (Comprehensive)
Located at `.git/hooks/pre-commit.enhanced`

**To activate the enhanced hook:**
```bash
# Backup current hook
cp .git/hooks/pre-commit .git/hooks/pre-commit.backup

# Use enhanced version
cp .git/hooks/pre-commit.enhanced .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

**Enhanced hook features:**
- ✅ YAML schema validation
- ✅ Date validation
- ✅ Enhanced YAML validation with suggestions
- ✅ Python tests (when .py files modified)
- ✅ YAML tools tests (when yaml_tools.py modified)
- ✅ Pytest suite (when Python files modified)
- ✅ Flake8 critical error checking
- ✅ React app tests (when JS/JSX files modified)
- ✅ Large file warnings
- ✅ Sensitive data detection
- ✅ Colored output for better readability

### 5. GitHub Actions CI/CD

#### Validation Workflow
`.github/workflows/validate.yml`
- Runs on push to main and PRs
- Validates timeline dates
- Checks for future confirmed events
- Verifies ID/filename consistency
- Generates validation report

## Running All Tests

### Quick Test Everything
```bash
# Create a test runner script
cat > run_all_tests.sh << 'EOF'
#!/bin/bash
echo "🧪 Running all tests..."

# YAML validation
echo "1. YAML Validation..."
python timeline_data/validate_yaml.py || exit 1

# Python tests
echo "2. Python Tests..."
python test_yaml_tools.py || exit 1
python -m pytest tests/ -q || exit 1

# React tests
echo "3. React Tests..."
cd viewer && CI=true npm test -- --watchAll=false || exit 1
cd ..

echo "✅ All tests passed!"
EOF

chmod +x run_all_tests.sh
./run_all_tests.sh
```

## Test Coverage Goals

| Component | Current Coverage | Goal |
|-----------|-----------------|------|
| YAML Events | Schema validation | 100% valid |
| YAML Tools | 22/22 tests pass | 100% |
| Python Backend | ~80% (estimated) | 90% |
| React Frontend | 12 core tests | 80% |
| Pre-commit | Enhanced available | Use enhanced |

## Common Issues and Solutions

### Issue: Pre-commit hook not running
```bash
# Make sure it's executable
chmod +x .git/hooks/pre-commit

# Test manually
.git/hooks/pre-commit
```

### Issue: Python tests fail with import errors
```bash
# Ensure virtual environment is active
source venv/bin/activate

# Install test dependencies
pip install pytest pytest-cov
```

### Issue: React tests fail
```bash
# Clear cache and reinstall
cd viewer
rm -rf node_modules package-lock.json
npm install
npm test
```

### Issue: YAML validation too strict
```bash
# Use enhanced validation for suggestions instead of failures
python yaml_tools.py validate --suggest-only
```

## Continuous Improvement

### Adding New Tests

#### For YAML Events
1. Add test cases to `test_yaml_tools.py`
2. Update validation rules in `yaml_tools.py`

#### For Python Code
1. Create test file in `tests/` directory
2. Follow naming convention: `test_*.py`
3. Use pytest framework

#### For React Components
1. Create test file next to component: `Component.test.js`
2. Use React Testing Library
3. Mock external dependencies

### Test Documentation
- Update this file when adding new test suites
- Document test coverage goals
- Add troubleshooting steps for common issues

## Quick Reference

```bash
# Most common test commands
python timeline_data/validate_yaml.py      # Validate events
python test_yaml_tools.py                  # Test YAML tools
python -m pytest tests/ -q                 # Python tests
cd viewer && npm test                      # React tests

# Before committing
.git/hooks/pre-commit                      # Run pre-commit checks
git commit --no-verify                     # Skip hooks (emergency only)
```