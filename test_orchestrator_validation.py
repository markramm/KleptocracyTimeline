#!/usr/bin/env python3
"""
Test Orchestrator with Validation Handling
Verify the queue-based orchestrator properly handles validation errors
"""

import json
import sqlite3
import time
from pathlib import Path

def test_orchestrator_validation():
    """Test the orchestrator with intentionally malformed data"""
    print("=" * 60)
    print("ORCHESTRATOR VALIDATION TEST")
    print("=" * 60)
    
    # Create test database with intentionally bad data
    conn = sqlite3.connect('test_validation.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS research_priorities (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            priority INTEGER,
            status TEXT,
            category TEXT,
            created_date TEXT,
            data TEXT
        )
    ''')
    
    # Insert test priorities with validation issues
    test_priorities = [
        {
            "id": "bad-id-format",  # Missing RT- prefix
            "title": "Short",  # Too short
            "description": "Too brief",  # Too short
            "priority": "high",  # Wrong type
            "status": "working",  # Invalid enum
            "extra_field": "should be allowed"
        },
        {
            # Missing required fields
            "title": "Test Priority",
            "extra_field": "test"
        },
        {
            "id": "RT-123",
            "title": "Valid Priority for Testing",
            "description": "This priority should validate correctly without issues",
            "priority": 7,
            "status": "pending"
        }
    ]
    
    for priority in test_priorities:
        conn.execute(
            "INSERT OR REPLACE INTO research_priorities (id, data) VALUES (?, ?)",
            (priority.get("id", "auto-" + str(time.time())), json.dumps(priority))
        )
    
    conn.commit()
    conn.close()
    
    print(f"Created test database with {len(test_priorities)} priorities")
    print("Priorities have various validation issues:")
    print("- Invalid ID patterns")
    print("- Too-short titles and descriptions")
    print("- Wrong data types")
    print("- Invalid enum values")
    print("- Missing required fields")
    print()
    
    # Now run the orchestrator on this test data
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    from utils.validation_handler import handle_validation_with_retry
    from utils.logging_system import validate_research_priority
    
    # Process each priority
    conn = sqlite3.connect('test_validation.db')
    cursor = conn.execute("SELECT data FROM research_priorities")
    
    results = []
    for row in cursor:
        data = json.loads(row[0])
        print(f"\nProcessing: {data.get('title', 'Untitled')}")
        print(f"Input: {json.dumps(data, indent=2)}")
        
        is_valid, fixed_data, errors = handle_validation_with_retry(
            data, "research_priority", validate_research_priority
        )
        
        print(f"Valid after fix: {is_valid}")
        if is_valid:
            print(f"Fixed data: {json.dumps(fixed_data, indent=2)}")
        else:
            print(f"Remaining errors: {len(errors)} errors")
            print(f"Partially fixed data: {json.dumps(fixed_data, indent=2)}")
        
        results.append({
            "original": data,
            "fixed": fixed_data,
            "valid": is_valid,
            "errors": errors
        })
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    valid_count = sum(1 for r in results if r["valid"])
    print(f"Total priorities processed: {len(results)}")
    print(f"Successfully validated: {valid_count}/{len(results)}")
    print(f"Partially fixed but still invalid: {len(results) - valid_count}/{len(results)}")
    
    # Clean up test database
    Path('test_validation.db').unlink(missing_ok=True)
    
    return valid_count == len(results) - 1  # Expect one to remain invalid for complex issues

if __name__ == "__main__":
    success = test_orchestrator_validation()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    import sys
    sys.exit(0 if success else 1)