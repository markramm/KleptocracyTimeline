#!/usr/bin/env python3
"""Populate validation run #13 with all events that have less than 3 sources."""

import json
import os
import sqlite3
from pathlib import Path

def populate_run_13():
    # Connect to database
    db_path = Path("/Users/markr/kleptocracy-timeline/unified_research.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Scan all event files for those with <3 sources
    events_dir = Path("/Users/markr/kleptocracy-timeline/timeline_data/events")
    events_with_low_sources = []

    print("Scanning events directory...")
    for filename in sorted(os.listdir(events_dir)):
        if not filename.endswith('.json'):
            continue

        filepath = events_dir / filename
        try:
            with open(filepath, 'r') as f:
                event = json.load(f)

            event_id = event.get('id')
            sources = event.get('sources', [])
            source_count = len(sources) if isinstance(sources, list) else 0
            importance = event.get('importance', 0)

            # Only include events with less than 3 sources
            if source_count < 3:
                events_with_low_sources.append({
                    'id': event_id,
                    'importance': importance,
                    'source_count': source_count,
                    'date': event.get('date', ''),
                    'title': event.get('title', '')
                })

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

    print(f"\nFound {len(events_with_low_sources)} events with <3 sources")

    # Sort by importance (descending) then date
    events_with_low_sources.sort(key=lambda x: (-x['importance'], x['date']))

    # Insert into validation_run_events table
    print("\nInserting events into validation run #13...")
    inserted = 0
    skipped = 0

    for idx, event_data in enumerate(events_with_low_sources):
        # Calculate priority score (10 = highest, 5 = lowest)
        priority = 10 - (idx / len(events_with_low_sources)) * 5

        # Determine if high priority (importance >= 8)
        high_priority = event_data['importance'] >= 8

        selection_reason = f"Importance {event_data['importance']}, {event_data['source_count']} sources"

        try:
            cursor.execute("""
                INSERT INTO validation_run_events
                (validation_run_id, event_id, validation_status, selection_date,
                 selection_priority, selection_reason, high_priority)
                VALUES (?, ?, 'pending', datetime('now'), ?, ?, ?)
            """, (13, event_data['id'], priority, selection_reason, high_priority))
            inserted += 1

            if inserted % 50 == 0:
                print(f"  Inserted {inserted} events...")

        except sqlite3.IntegrityError as e:
            print(f"  Skipped duplicate: {event_data['id']}")
            skipped += 1
            continue

    # Commit changes
    conn.commit()

    # Update validation_runs table with correct actual_count
    cursor.execute("""
        UPDATE validation_runs
        SET actual_count = ?
        WHERE id = 13
    """, (inserted,))
    conn.commit()

    print(f"\n✅ Successfully inserted {inserted} events into validation run #13")
    print(f"   Skipped {skipped} duplicates")

    # Show breakdown
    print("\nBreakdown by source count:")
    for source_count in range(3):
        count = sum(1 for e in events_with_low_sources if e['source_count'] == source_count)
        print(f"  {source_count} sources: {count} events")

    print("\nBreakdown by importance:")
    importance_counts = {}
    for event in events_with_low_sources:
        imp = event['importance']
        importance_counts[imp] = importance_counts.get(imp, 0) + 1

    for imp in sorted(importance_counts.keys(), reverse=True):
        count = importance_counts[imp]
        print(f"  Importance {imp}: {count} events")

    conn.close()
    print("\n✅ Validation run #13 populated successfully")

if __name__ == "__main__":
    populate_run_13()
