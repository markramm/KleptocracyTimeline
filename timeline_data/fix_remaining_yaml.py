#!/usr/bin/env python3
"""
Fix remaining YAML errors by checking each file individually
"""

import os
import yaml
import sys

error_files = [
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

def check_file(filepath):
    """Check a single file for errors and show the error"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        return True, "Valid"
    except yaml.YAMLError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def main():
    events_dir = 'events'
    
    print("Checking files with reported errors...")
    print("=" * 60)
    
    valid_count = 0
    error_count = 0
    
    for filename in error_files:
        filepath = os.path.join(events_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"❌ {filename}")
            print(f"   ERROR: File not found")
            error_count += 1
            continue
            
        is_valid, message = check_file(filepath)
        
        if is_valid:
            print(f"✅ {filename}")
            valid_count += 1
        else:
            print(f"❌ {filename}")
            # Show first 100 chars of error
            error_msg = message.replace('\n', ' ')[:100]
            print(f"   ERROR: {error_msg}")
            
            # Try to identify the specific line
            if 'line' in message:
                # Extract line number
                import re
                match = re.search(r'line (\d+)', message)
                if match:
                    line_num = int(match.group(1))
                    with open(filepath, 'r') as f:
                        lines = f.readlines()
                    if line_num <= len(lines):
                        print(f"   LINE {line_num}: {lines[line_num-1].strip()}")
            
            error_count += 1
    
    print("\n" + "=" * 60)
    print(f"Results:")
    print(f"  Valid: {valid_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total checked: {len(error_files)}")

if __name__ == "__main__":
    main()