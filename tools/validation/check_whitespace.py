#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def is_binary(path: Path) -> bool:
    try:
        with path.open('rb') as f:
            chunk = f.read(1024)
            return b'\0' in chunk
    except OSError:
        return False

def check_file(path: Path):
    issues = []
    try:
        # Read in binary mode to detect actual line endings
        with path.open('rb') as f:
            content = f.read()
        # Check for CRLF (Windows line endings)
        if b'\r\n' in content:
            issues.append(f"{path}: CRLF line endings")
    except Exception:
        return issues
    return issues

def should_check(path: Path) -> bool:
    """Determine if a file should be checked for whitespace issues."""
    # Skip paths containing these directories
    skip_dirs = {
        'node_modules',
        '__pycache__',
        '.git',
        'dist',
        'build',
        '.pytest_cache',
        'venv',
        'env',
        '.venv',
        'site-packages'
    }
    
    # Check if any part of the path contains a skip directory
    for part in path.parts:
        if part in skip_dirs:
            return False
    
    # Skip common non-source files
    skip_extensions = {'.pyc', '.pyo', '.so', '.dylib', '.dll', '.class', '.jar'}
    if path.suffix in skip_extensions:
        return False
    
    # Skip .DS_Store files
    if path.name == '.DS_Store':
        return False
    
    return True

def main() -> int:
    result = subprocess.run(['git', 'ls-files'], capture_output=True, text=True, check=True)
    files = [Path(line) for line in result.stdout.splitlines()]
    problems = []
    for path in files:
        if not should_check(path):
            continue
        if is_binary(path):
            continue
        problems.extend(check_file(path))
    if problems:
        print('Whitespace issues found:')
        for p in problems:
            print(p)
        return 1
    print('No whitespace issues found.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
