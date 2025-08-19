#!/usr/bin/env python3
"""
Fix common YAML quote issues in event files.
"""

import re
from pathlib import Path

def fix_yaml_quotes(content):
    """Fix common YAML quoting issues."""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Check if line contains a YAML key-value pair
        if ':' in line and not line.strip().startswith('#'):
            # Check for problematic patterns in summaries and notes
            if any(key in line for key in ['summary:', 'notes:', 'title:']):
                # Extract the key and value
                match = re.match(r'^(\s*)(summary|notes|title):\s*(.+)$', line)
                if match:
                    indent, key, value = match.groups()
                    
                    # Check if value needs quoting (contains quotes but isn't already quoted)
                    if ('"' in value or "'" in value) and not (value.startswith("'") or value.startswith('"')):
                        # Escape single quotes and wrap in single quotes
                        value = value.replace("'", "''")
                        line = f"{indent}{key}: '{value}'"
            
            # Fix Rep. patterns that break YAML
            line = re.sub(r"Rep\. (\w+) (\w+): \"", r"Rep. \1 \2 said: '", line)
            
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def process_file(filepath):
    """Process a single YAML file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        fixed_content = fix_yaml_quotes(content)
        
        if fixed_content != content:
            with open(filepath, 'w') as f:
                f.write(fixed_content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

# Process problem files
problem_files = [
    '2016-08-21--stone-podesta-tweet.yaml',
    '2025-08-01--court-defiance-35-percent-pattern.yaml',
    '2025-07-23--house-oversight-subpoenas-doj.yaml',
    '2016-08-01--stone-guccifer-communications.yaml',
    '2025-06-01--federal-layoffs-275000.yaml',
    '2025-08-01--gsa-northwest-90-percent-fired.yaml',
    '2025-05-15--bondi-briefs-trump-name-in-files.yaml',
    '2024-06-28--scotus_loper_bright_overrules_chevron.yaml',
    '2025-01-31--eo_14171_schedule_f.yaml',
    '2025-03-10--civicus-watchlist-us-democracy.yaml'
]

for file in problem_files:
    path = Path('events') / file
    if path.exists():
        if process_file(path):
            print(f"Fixed: {file}")
        else:
            print(f"No changes needed: {file}")