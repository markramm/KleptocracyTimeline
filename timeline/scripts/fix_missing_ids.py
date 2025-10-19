#!/usr/bin/env python3
"""
Fix missing 'id' fields in timeline events.
Adds 'id' field matching the filename (without .json extension).
"""

import json
from pathlib import Path

# Events that are missing 'id' field according to tests
MISSING_ID_FILES = [
    "2011-05-11--meredith-baker-fcc-comcast-revolving-door.json",
    "2013-05-02--tom-wheeler-fcc-chairman-nomination-telecom-lobbyist.json",
    "clarence_thomas_harlan_crow_scandal_2023.json",
    "1995-12-20_fda_oxycontin_approval.json",
    "citizens_united_2010.json",
    "2009-12-21_julie_gerberding_merck_revolving_door.json",
    "1996-02-08--telecommunications-act-corporate-capture-deregulation.json",
    "samuel_alito_paul_singer_scandal_2023.json",
    "2003-06-02--fcc-media-ownership-deregulation-attempt-michael-powell.json",
    "2019-06-27_scott_gottlieb_pfizer_board.json",
    "bush_v_gore_2000.json",
    "2017-12-14--fcc-repeals-net-neutrality-ajit-pai-verizon.json",
    "2004-11-18_david_graham_vioxx_testimony.json"
]

def fix_missing_ids():
    """Add missing 'id' fields to events."""
    events_dir = Path('timeline_data/events')
    fixed_count = 0

    for filename in MISSING_ID_FILES:
        filepath = events_dir / filename

        if not filepath.exists():
            print(f"⚠️  File not found: {filename}")
            continue

        # Read event
        with open(filepath, 'r', encoding='utf-8') as f:
            event = json.load(f)

        # Check if id is actually missing
        if 'id' in event and event['id']:
            print(f"✓  {filename} already has 'id' field: {event['id']}")
            continue

        # Add id field matching filename (without .json)
        event_id = filepath.stem
        event['id'] = event_id

        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(event, f, indent=2, ensure_ascii=False)

        print(f"✅ Fixed {filename} → added id: {event_id}")
        fixed_count += 1

    print(f"\n🎉 Fixed {fixed_count} events")
    return fixed_count

if __name__ == '__main__':
    fix_missing_ids()
