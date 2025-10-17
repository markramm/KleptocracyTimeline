#!/usr/bin/env python3
"""
Fix imports in research-server after restructuring

Changes:
  from research_monitor.X import Y  →  from X import Y
  from research_monitor import X    →  import X
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path: Path) -> int:
    """
    Fix imports in a single Python file
    Returns number of changes made
    """
    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content
    changes = 0

    # Pattern 1: from research_monitor.services.X import Y → from services.X import Y
    pattern1 = r'from research_monitor\.(services\.\w+) import '
    replacement1 = r'from \1 import '
    content, count1 = re.subn(pattern1, replacement1, content)
    changes += count1

    # Pattern 2: from research_monitor.core.X import Y → from core.X import Y
    pattern2 = r'from research_monitor\.(core\.\w+) import '
    replacement2 = r'from \1 import '
    content, count2 = re.subn(pattern2, replacement2, content)
    changes += count2

    # Pattern 3: from research_monitor.X import Y → from X import Y
    pattern3 = r'from research_monitor\.(\w+) import '
    replacement3 = r'from \1 import '
    content, count3 = re.subn(pattern3, replacement3, content)
    changes += count3

    # Pattern 4: from research_monitor import X → import X
    pattern4 = r'from research_monitor import (\w+)'
    replacement4 = r'import \1'
    content, count4 = re.subn(pattern4, replacement4, content)
    changes += count4

    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✓ Fixed {changes} imports in {file_path.relative_to(Path.cwd())}")

    return changes

def main():
    """Main entry point"""
    server_dir = Path(__file__).parent.parent / 'research-server' / 'server'

    if not server_dir.exists():
        print(f"Error: {server_dir} does not exist")
        return

    print(f"Fixing imports in: {server_dir}")
    print()

    total_changes = 0
    files_changed = 0

    # Find all Python files
    for py_file in server_dir.rglob('*.py'):
        # Skip __pycache__ and test files for now
        if '__pycache__' in str(py_file):
            continue

        changes = fix_imports_in_file(py_file)
        if changes > 0:
            total_changes += changes
            files_changed += 1

    print()
    print(f"Summary: Fixed {total_changes} imports in {files_changed} files")


if __name__ == '__main__':
    main()
