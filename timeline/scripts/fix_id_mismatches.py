#!/usr/bin/env python3
"""
Fix ID/filename mismatches in timeline events.
Updates the 'id' field inside events to match their filename.
"""

import json
from pathlib import Path

# Files with ID mismatches (filename → expected ID)
MISMATCHED_FILES = [
    "2025-02-15--example-trump-doj-weaponization-event.json",
    "enhanced_2025-01-20--coordinated-federal-workforce-purge-schedule-f-doj.json",
    "2024-03-22--grok-ai-regulatory-investigation.json",
    "enhanced_2025-03-01--project-2025-authors-fill-key-administration-positions-1757456630.json",
    "2024-08-29--kylian-mbappé-twitter-account-hacked-to-promote-00.json",
    "enhanced_2025-08-26--doge-social-security-data-breach.json",
    "2018-01-07--dan-elwell-becomes-acting-faa-administrator-after-boeing-executive-career-1757458612.json",
    "2014-07-16--eu-and-us-impose-sectoral-sanctions-on-russia-1757457198.json"
]

def fix_id_mismatches():
    """Fix ID/filename mismatches by updating IDs to match filenames."""
    events_dir = Path('data/events')
    fixed_count = 0

    for filename in MISMATCHED_FILES:
        filepath = events_dir / filename

        if not filepath.exists():
            print(f"⚠️  File not found: {filename}")
            continue

        # Read event
        with open(filepath, 'r', encoding='utf-8') as f:
            event = json.load(f)

        # Get expected ID (filename without .json)
        expected_id = filepath.stem
        current_id = event.get('id')

        if current_id == expected_id:
            print(f"✓  {filename} already matches")
            continue

        # Update ID to match filename
        print(f"🔧 Fixing {filename}")
        print(f"   Old ID: {current_id}")
        print(f"   New ID: {expected_id}")

        event['id'] = expected_id

        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(event, f, indent=2, ensure_ascii=False)

        fixed_count += 1

    print(f"\n🎉 Fixed {fixed_count} ID mismatches")
    return fixed_count

if __name__ == '__main__':
    fix_id_mismatches()
