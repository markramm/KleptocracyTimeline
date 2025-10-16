#!/usr/bin/env python3
"""
Reapply all validation corrections from logs to ensure event files are properly updated.
This will process all validation logs and reapply their corrections whether they were 
previously applied or not - idempotent operation.
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional

API_BASE = "http://localhost:5558/api"

def get_all_validation_logs() -> List[Dict[str, Any]]:
    """Get all validation logs that have corrections to apply."""
    all_logs = []
    offset = 0
    limit = 50
    
    while True:
        response = requests.get(f"{API_BASE}/validation-logs", params={
            'limit': limit,
            'offset': offset
        })
        
        if response.status_code != 200:
            print(f"Error fetching validation logs: {response.status_code}")
            break
            
        data = response.json()
        logs = data['data']['validation_logs']
        
        if not logs:
            break
            
        all_logs.extend(logs)
        
        if not data['data']['pagination']['has_more']:
            break
            
        offset += limit
        time.sleep(0.1)  # Be gentle with the API
    
    return all_logs

def should_reapply_log(log: Dict[str, Any]) -> bool:
    """Determine if a validation log should be reapplied."""
    # Skip test entries
    if log['event_id'] == 'test-event':
        return False
    
    # Skip flagged or needs_work entries (they didn't validate successfully)
    if log['status'] in ['flagged', 'needs_work']:
        return False
    
    # Skip entries with no corrections made
    corrections = log.get('corrections_made')
    if not corrections or corrections is False:
        return False
    
    # Skip our own retry entries to avoid infinite loops
    if log.get('validator_id') == 'correction-retry':
        return False
    
    return True

def reapply_validation(log: Dict[str, Any]) -> bool:
    """Reapply a validation log's corrections."""
    event_id = log['event_id']
    corrections = log['corrections_made']
    validator_id = log['validator_id'] or 'bulk-retry'
    log_id = log['id']
    
    print(f"Reapplying validation log {log_id} for event {event_id}...")
    
    # Use the same endpoint that worked before
    payload = {
        'event_id': event_id,
        'corrections': corrections,
        'validator_id': f"{validator_id}-retry",
        'validation_log_id': log_id
    }
    
    try:
        # Call the apply_validation_corrections endpoint directly
        response = requests.post(f"{API_BASE}/validation-logs", json={
            'event_id': event_id,
            'validator_id': f"{validator_id}-retry", 
            'status': 'validated',
            'corrections_made': corrections,
            'notes': f"Reapplying validation log {log_id} corrections systematically",
            'validator_type': 'agent'
        })
        
        if response.status_code == 200:
            print(f"  ✓ Successfully reapplied corrections for {event_id}")
            return True
        else:
            print(f"  ✗ Failed to reapply corrections for {event_id}: {response.status_code}")
            print(f"    Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ✗ Exception reapplying corrections for {event_id}: {e}")
        return False

def main():
    """Main function to reapply all validation corrections."""
    print("Fetching all validation logs...")
    logs = get_all_validation_logs()
    print(f"Found {len(logs)} total validation logs")
    
    # Filter logs that should be reapplied
    reapply_logs = [log for log in logs if should_reapply_log(log)]
    print(f"Found {len(reapply_logs)} validation logs with corrections to reapply")
    
    if not reapply_logs:
        print("No validation logs to reapply!")
        return
    
    # Sort by log ID to process in chronological order
    reapply_logs.sort(key=lambda x: x['id'])
    
    success_count = 0
    failure_count = 0
    
    print(f"\nReapplying {len(reapply_logs)} validation corrections...")
    print("=" * 60)
    
    for i, log in enumerate(reapply_logs, 1):
        print(f"\n[{i}/{len(reapply_logs)}] ", end="")
        
        if reapply_validation(log):
            success_count += 1
        else:
            failure_count += 1
        
        # Small delay between requests
        time.sleep(0.2)
    
    print("\n" + "=" * 60)
    print(f"Reapplication complete!")
    print(f"  ✓ Successfully reapplied: {success_count}")
    print(f"  ✗ Failed to reapply: {failure_count}")
    print(f"  📊 Success rate: {success_count/(success_count+failure_count)*100:.1f}%")

if __name__ == "__main__":
    main()