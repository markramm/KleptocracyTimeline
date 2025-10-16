#!/usr/bin/env python3
"""
Reapply validation corrections by creating new validation logs that trigger auto-correction.
"""

import subprocess
import json
import time
import requests

API_BASE = "http://localhost:5558/api"

def run_cli_command(command):
    """Run a CLI command and return the JSON result."""
    try:
        result = subprocess.run(
            ["python3", "research_cli.py"] + command, 
            capture_output=True, 
            text=True,
            cwd="/Users/markr/kleptocracy-timeline"
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"CLI command failed: {' '.join(command)}")
            return None
    except Exception as e:
        print(f"Exception running CLI command: {e}")
        return None

def get_all_validation_logs():
    """Get all validation logs using CLI."""
    all_logs = []
    offset = 0
    limit = 50
    
    while True:
        data = run_cli_command(["validation-logs-list", f"--limit={limit}", f"--offset={offset}"])
        if not data or not data.get('success'):
            break
            
        logs = data['data']['validation_logs']
        if not logs:
            break
            
        all_logs.extend(logs)
        
        if not data['data']['pagination']['has_more']:
            break
            
        offset += limit
        time.sleep(0.1)
    
    return all_logs

def should_reapply_log(log):
    """Determine if a validation log should be reapplied."""
    # Skip test entries
    if log['event_id'] == 'test-event':
        return False
    
    # Skip flagged or needs_work entries
    if log['status'] in ['flagged', 'needs_work']:
        return False
    
    # Skip entries with no corrections made
    corrections = log.get('corrections_made')
    if not corrections or corrections is False:
        return False
    
    # Skip our own retry entries to avoid infinite loops
    validator_id = log.get('validator_id', '')
    if 'retry' in validator_id or validator_id == 'correction-retry':
        return False
    
    return True

def create_validation_log_direct(event_id, corrections, original_log_id, original_validator):
    """Create a validation log directly via API that will trigger auto-correction."""
    
    # Determine the notes based on correction type
    if isinstance(corrections, list) and corrections:
        if 'added_sources' in corrections[0]:
            sources_added = corrections[0]['added_sources']
            notes = f"Bulk reapply log {original_log_id}: Added {len(sources_added)} sources"
        else:
            notes = f"Bulk reapply log {original_log_id}: Applied corrections"
    elif corrections is True:
        notes = f"Bulk reapply log {original_log_id}: Validation confirmed" 
    elif isinstance(corrections, (int, float)):
        notes = f"Bulk reapply log {original_log_id}: Quality score {corrections}"
    else:
        notes = f"Bulk reapply log {original_log_id}: Applied corrections"
    
    payload = {
        'event_id': event_id,
        'validator_id': f"{original_validator}-bulk-retry",
        'status': 'validated',
        'corrections_made': corrections,
        'notes': notes,
        'validator_type': 'agent'
    }
    
    try:
        response = requests.post(f"{API_BASE}/validation-logs", json=payload)
        
        if response.status_code == 200:
            print(f"  ✓ Successfully reapplied corrections for {event_id}")
            return True
        else:
            print(f"  ✗ Failed to reapply corrections for {event_id}: {response.status_code}")
            try:
                error_data = response.json()
                print(f"    Error: {error_data.get('message', 'Unknown error')}")
            except:
                print(f"    Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  ✗ Exception reapplying corrections for {event_id}: {e}")
        return False

def main():
    """Main function."""
    print("Fetching all validation logs...")
    logs = get_all_validation_logs()
    print(f"Found {len(logs)} total validation logs")
    
    # Filter logs that should be reapplied
    reapply_logs = [log for log in logs if should_reapply_log(log)]
    print(f"Found {len(reapply_logs)} validation logs with corrections to reapply")
    
    if not reapply_logs:
        print("No validation logs to reapply!")
        return
    
    # Sort by log ID to process in chronological order (oldest first)
    reapply_logs.sort(key=lambda x: x['id'])
    
    success_count = 0
    failure_count = 0
    
    print(f"\nReapplying {len(reapply_logs)} validation corrections...")
    print("=" * 70)
    
    for i, log in enumerate(reapply_logs, 1):
        event_id = log['event_id']
        corrections = log['corrections_made']
        log_id = log['id']
        validator_id = log.get('validator_id', 'unknown')
        
        print(f"\n[{i}/{len(reapply_logs)}] Log {log_id}: {event_id}")
        
        if create_validation_log_direct(event_id, corrections, log_id, validator_id):
            success_count += 1
        else:
            failure_count += 1
        
        # Small delay between requests
        time.sleep(0.5)
    
    print("\n" + "=" * 70)
    print(f"Bulk reapplication complete!")
    print(f"  ✓ Successfully reapplied: {success_count}")
    print(f"  ✗ Failed to reapply: {failure_count}")
    if success_count + failure_count > 0:
        print(f"  📊 Success rate: {success_count/(success_count+failure_count)*100:.1f}%")
    
    if success_count > 0:
        print(f"\n🔄 {success_count} validation corrections have been reapplied.")
        print("Events should now be updated with their validation improvements.")

if __name__ == "__main__":
    main()