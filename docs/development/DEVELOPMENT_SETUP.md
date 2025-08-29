# Development Setup Guide

This guide covers setting up the development environment for the Kleptocracy Timeline project.

## Prerequisites

- Python 3.8+ 
- Node.js 16+
- npm or yarn
- Git

## Python Environment Setup

### 1. Create Virtual Environment

The project uses a Python virtual environment to manage dependencies. The `venv/` folder is gitignored to keep the repository clean.

```bash
# From the repository root
python3 -m venv venv
```

### 2. Activate Virtual Environment

```bash
# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

You'll see `(venv)` in your terminal prompt when activated.

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **Flask** - Web framework for API server
- **PyYAML** - YAML file processing
- **pytest** - Testing framework
- **black** - Code formatting
- **flake8** - Code linting
- And other dependencies

### 4. Deactivate Virtual Environment

When you're done working:

```bash
deactivate
```

## React Viewer Setup

### 1. Install Node Dependencies

```bash
cd viewer
npm install
```

### 2. Start Development Server

```bash
npm start
```

The viewer will be available at `http://localhost:3000`

## Running the API Server

### Option 1: Basic Flask Server

```bash
# Activate virtual environment first
source venv/bin/activate

# Run the server
python api/server.py
```

API will be available at `http://localhost:5000`

### Option 2: Enhanced Server

```bash
source venv/bin/activate
python api/enhanced_server.py
```

### Option 3: Static File Server

For production-like serving:

```bash
source venv/bin/activate
python api/serve_static.py
```

## Running Tests

### Python Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_scripts.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=scripts
```

### React Tests

```bash
cd viewer
npm test
```

## Common Development Tasks

### Validate Timeline Events

```bash
source venv/bin/activate
python scripts/validate.py
```

### Generate Exports

```bash
source venv/bin/activate

# Generate CSV export
python scripts/generate_csv.py

# Generate YAML export  
python scripts/generate_yaml_export.py

# Generate all exports for deployment
python scripts/generate.py --all
```

### Find Duplicate Events

```bash
source venv/bin/activate
python scripts/find_duplicates.py --verbose
```

### Analyze Event Sources

```bash
source venv/bin/activate
python scripts/analyze_sources.py
```

## Build for Production

### Build React App

```bash
cd viewer
npm run build
```

Creates optimized production build in `viewer/build/`

### Deploy to GitHub Pages

```bash
cd viewer
npm run deploy
```

Or use GitHub Actions (automatically triggered on push to main branch).

## Project Structure

```
kleptocracy-timeline/
├── venv/                  # Python virtual environment (gitignored)
├── api/                   # Flask API servers
│   ├── server.py         # Basic server
│   ├── enhanced_server.py # Enhanced features
│   └── static_api/       # Static API files
├── scripts/              # Python scripts for data processing
│   ├── utils/           # Shared utilities library
│   ├── validate.py      # Event validation
│   └── generate_*.py    # Export generators
├── viewer/              # React application
│   ├── src/            # Source code
│   ├── public/         # Static files
│   └── build/          # Production build (gitignored)
├── timeline_data/      # Timeline event data
│   └── events/        # Individual event YAML files
├── tests/             # Test suites
├── archive/           # Archived/old files (gitignored)
└── requirements.txt   # Python dependencies
```

## Troubleshooting

### Import Errors in Tests

If you see `ModuleNotFoundError`:
1. Make sure virtual environment is activated
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Check Python path: `which python` should point to `venv/bin/python`

### Server Won't Start

1. Check port 5000 is not in use: `lsof -i :5000`
2. Verify timeline_data symlink exists: `ls -la api/timeline_data`
3. Check Flask is installed: `pip show flask`

### React App Build Fails

1. Clear cache: `rm -rf node_modules && npm install`
2. Check Node version: `node --version` (should be 16+)
3. Verify all CSV/JSON exports exist in `viewer/public/`

## VS Code Configuration

For the best development experience, add to `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

## Contributing

1. Always use the virtual environment for Python development
2. Run tests before committing
3. Keep generated files out of the repository (they're gitignored)
4. Document any new dependencies in requirements.txt

## Need Help?

- Check existing documentation in `/scripts/README.md`
- Review test files for usage examples
- Open an issue on GitHub for bugs or questions