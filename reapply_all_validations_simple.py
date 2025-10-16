#!/usr/bin/env python3
"""
Reapply all validation corrections from logs systematically.
"""

import subprocess
import json
import time

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
            print(f"Error: {result.stderr}")
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

def reapply_validation_direct(event_id, corrections, original_log_id, original_validator):
    """Directly create a new validation log that will trigger auto-correction."""
    
    # Determine the notes based on correction type
    if isinstance(corrections, list) and corrections:
        if 'added_sources' in corrections[0]:
            sources_added = corrections[0]['added_sources']
            notes = f"Reapplying validation log {original_log_id}: Added {len(sources_added)} sources systematically"
        else:
            notes = f"Reapplying validation log {original_log_id}: Applied corrections systematically"
    elif corrections is True:
        notes = f"Reapplying validation log {original_log_id}: Validation confirmed"
    elif isinstance(corrections, (int, float)):
        notes = f"Reapplying validation log {original_log_id}: Quality score {corrections}"
    else:
        notes = f"Reapplying validation log {original_log_id}: Applied corrections"
    
    # Use the CLI to create a new validation log
    data = run_cli_command([
        "validation-logs-create",
        "--event-id", event_id,
        "--validator-id", f"{original_validator}-bulk-retry",
        "--status", "validated", 
        "--notes", notes,
        "--corrections", json.dumps(corrections)
    ])
    
    if data and data.get('success'):
        print(f"  ✓ Successfully reapplied corrections for {event_id}")
        return True
    else:
        print(f"  ✗ Failed to reapply corrections for {event_id}")
        if data:
            print(f"    Error: {data.get('message', 'Unknown error')}")
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
    
    # Sort by log ID to process in chronological order
    reapply_logs.sort(key=lambda x: x['id'])
    
    success_count = 0
    failure_count = 0
    
    print(f"\nReapplying {len(reapply_logs)} validation corrections...")
    print("=" * 60)
    
    for i, log in enumerate(reapply_logs, 1):
        event_id = log['event_id']
        corrections = log['corrections_made']
        log_id = log['id']
        validator_id = log.get('validator_id', 'unknown')
        
        print(f"\n[{i}/{len(reapply_logs)}] Log {log_id}: {event_id}")
        
        if reapply_validation_direct(event_id, corrections, log_id, validator_id):
            success_count += 1
        else:
            failure_count += 1
        
        # Small delay between requests
        time.sleep(0.3)
    
    print("\n" + "=" * 60)
    print(f"Reapplication complete!")
    print(f"  ✓ Successfully reapplied: {success_count}")
    print(f"  ✗ Failed to reapply: {failure_count}")
    if success_count + failure_count > 0:
        print(f"  📊 Success rate: {success_count/(success_count+failure_count)*100:.1f}%")

if __name__ == "__main__":
    main()