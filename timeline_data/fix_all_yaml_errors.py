#!/usr/bin/env python3
"""
Fix common YAML errors in timeline event files
"""

import os
import yaml
import re
from typing import Dict, Any

def fix_yaml_quotes(content: str) -> str:
    """Fix common quote issues in YAML content"""
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Skip lines that are already properly quoted
        if line.strip().startswith('#') or not line.strip():
            fixed_lines.append(line)
            continue
            
        # Fix colons inside unquoted strings in summaries/notes
        if ('summary:' in line or 'notes:' in line or 'title:' in line) and ': "' in line:
            # Replace : " with - " to avoid YAML parsing issues
            line = line.replace(': "', ' - "')
            
        # Fix quotes in the middle of strings that aren't properly escaped
        if 'title:' in line and '"' in line and not (line.strip().startswith('title: "') or line.strip().startswith('title: \'')):
            # Find quotes that need escaping
            parts = line.split('title:', 1)
            if len(parts) == 2:
                title_part = parts[1]
                # If there are quotes but the whole thing isn't quoted
                if '"' in title_part and not (title_part.strip().startswith('"') and title_part.strip().endswith('"')):
                    title_part = title_part.replace('"', "'")
                    line = parts[0] + 'title:' + title_part
                    
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def validate_and_fix_file(filepath: str) -> tuple[bool, str]:
    """Validate and attempt to fix a YAML file"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # First try to parse as-is
    try:
        data = yaml.safe_load(original_content)
        return True, "Already valid"
    except yaml.YAMLError as e:
        error_msg = str(e)
    
    # Try to fix common issues
    fixed_content = fix_yaml_quotes(original_content)
    
    # Test if fixes worked
    try:
        data = yaml.safe_load(fixed_content)
        # Save the fixed version
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        return True, "Fixed quote issues"
    except yaml.YAMLError:
        pass
    
    # If still broken, try more aggressive fixes
    # Look for specific error patterns
    if "mapping values are not allowed here" in error_msg:
        # This usually means there's a colon where it shouldn't be
        lines = fixed_content.split('\n')
        for i, line in enumerate(lines):
            # Skip field definitions
            if re.match(r'^[a-z_]+:', line):
                continue
            # Fix colons in values that aren't quoted
            if ':' in line and not line.strip().startswith('-') and not line.strip().startswith('#'):
                # Check if this line is part of a multi-line string
                if i > 0 and lines[i-1].strip().endswith(':'):
                    continue
                # Replace problematic colons
                if '": ' in line or ':"' in line or ': ' in line:
                    # This line has a colon that might be breaking YAML
                    line = line.replace('": ', '" - ')
                    line = line.replace(':"', '" - "')
                    lines[i] = line
        
        fixed_content = '\n'.join(lines)
        
        # Test again
        try:
            data = yaml.safe_load(fixed_content)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True, "Fixed mapping/colon issues"
        except yaml.YAMLError as e2:
            return False, f"Could not auto-fix: {str(e2)[:100]}"
    
    return False, f"Could not auto-fix: {error_msg[:100]}"

def main():
    """Fix all YAML files with errors"""
    
    # List of files with known errors
    error_files = [
        '2016-08-01--stone-guccifer-communications.yaml',
        '2016-08-21--stone-podesta-tweet.yaml',
        '2024-06-28--scotus_loper_bright_overrules_chevron.yaml',
        '2025-01-21--energy-emergency.yaml',
        '2025-01-24--time-project2025-analysis.yaml',
        '2025-01-31--eo_14171_schedule_f.yaml',
        '2025-02-06--ambassadors_and_nasa_nomination.yaml',
        '2025-02-07--politico_tro_denied.yaml',
        '2025-02-07--to_02-21_doge_treasury_injunctions.yaml',
        '2025-02-09--bead_policy_shift_starlink.yaml',
        '2025-02-17--18_chutkan_comments_doge_disorder.yaml',
        '2025-02-19--cfpb_shutdown_orders.yaml',
        '2025-03-10--civicus-watchlist-us-democracy.yaml',
        '2025-03-11--wapo_38b_support.yaml',
        '2025-03-19--lutnick_tesla_remarks_ethics_complaints.yaml',
        '2025-03-24--epa_tce_delay_and_july_eto_rollback.yaml',
        '2025-04-04--spacex_59b_space-force_nssl.yaml',
        '2025-04-17--fedscoop_apa_challenge_ok.yaml',
        '2025-04-27--senate_psi_memo_liabilities.yaml',
        '2025-05-02--abu-dhabi-2-billion-crypto.yaml',
        '2025-05-02--tigta_snapshot_irs_reductions.yaml',
        '2025-05-15--bondi-briefs-trump-name-in-files.yaml',
        '2025-06-01--federal-layoffs-275000.yaml',
        '2025-06-09--cote_opm_injunction.yaml',
        '2025-07-01--doj-blocks-epstein-releases.yaml',
        '2025-07-14--dod_frontier_ai_contracts_xai.yaml',
        '2025-07-14--dod_xai_ceiling.yaml',
        '2025-07-18--tigta_snapshot_update.yaml',
        '2025-07-23--house-oversight-subpoenas-doj.yaml',
        '2025-07-31--senate_psi_21_7b_waste.yaml',
        '2025-08-01--court-defiance-35-percent-pattern.yaml',
        '2025-08-01--gsa-northwest-90-percent-fired.yaml'
    ]
    
    events_dir = 'events'
    fixed = 0
    failed = 0
    already_valid = 0
    
    print("Fixing YAML files with errors...")
    print("=" * 60)
    
    for filename in error_files:
        filepath = os.path.join(events_dir, filename)
        if not os.path.exists(filepath):
            print(f"❌ {filename} - File not found")
            failed += 1
            continue
            
        success, message = validate_and_fix_file(filepath)
        
        if success:
            if "Already valid" in message:
                print(f"✅ {filename} - {message}")
                already_valid += 1
            else:
                print(f"✅ {filename} - {message}")
                fixed += 1
        else:
            print(f"❌ {filename} - {message}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results:")
    print(f"  Already valid: {already_valid}")
    print(f"  Fixed: {fixed}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(error_files)}")
    
    if failed > 0:
        print(f"\n{failed} files need manual fixing")
        print("Run 'python3 validate_yaml.py' to see specific errors")

if __name__ == "__main__":
    main()