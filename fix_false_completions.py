#!/usr/bin/env python3
"""
Fix falsely completed research priorities by resetting them to pending status
"""

import json
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_false_completions():
    """Reset research priorities marked completed but with 0 actual events"""
    
    print("🔧 FIXING FALSE COMPLETION TRACKING")
    print("=" * 60)
    
    fixed_count = 0
    already_correct_count = 0
    error_count = 0
    
    # Process all research priorities
    for priority_file in Path("research_priorities").glob("*.json"):
        try:
            with open(priority_file, 'r') as f:
                priority_data = json.load(f)
            
            status = priority_data.get('status', 'unknown')
            actual_events = priority_data.get('actual_events', 0)
            estimated_events = priority_data.get('estimated_events', 0)
            priority_id = priority_data.get('id', priority_file.stem)
            
            # Check if this needs to be fixed
            if status == 'completed' and actual_events == 0:
                # Reset to pending status
                priority_data['status'] = 'pending'
                priority_data['actual_events'] = 0
                priority_data['updated_date'] = '2025-09-06'
                
                # Remove false completion date
                if 'completion_date' in priority_data:
                    del priority_data['completion_date']
                
                # Save the corrected priority
                with open(priority_file, 'w') as f:
                    json.dump(priority_data, f, indent=2, ensure_ascii=False)
                
                fixed_count += 1
                logger.info(f"Fixed {priority_id}: reset to pending (expected {estimated_events} events)")
                
            elif status == 'completed' and actual_events > 0:
                already_correct_count += 1
                
        except Exception as e:
            error_count += 1
            logger.error(f"Error processing {priority_file.name}: {str(e)}")
    
    print(f"\n📊 FIX RESULTS:")
    print(f"🔧 Fixed (reset to pending): {fixed_count}")
    print(f"✅ Already correct: {already_correct_count}")
    print(f"❌ Errors: {error_count}")
    
    if fixed_count > 0:
        print(f"\n✅ SUCCESS: Fixed {fixed_count} falsely completed priorities")
        print(f"✅ These priorities are now available for proper research processing")
        return True
    else:
        print(f"\n⚠️  No false completions found to fix")
        return False

def verify_fix():
    """Verify the fix worked by checking current completion status"""
    
    print(f"\n🔍 VERIFYING FIX...")
    
    total_priorities = 0
    pending_count = 0
    completed_with_events = 0
    completed_without_events = 0
    
    for priority_file in Path("research_priorities").glob("*.json"):
        try:
            with open(priority_file, 'r') as f:
                priority_data = json.load(f)
            
            total_priorities += 1
            status = priority_data.get('status', 'unknown')
            actual_events = priority_data.get('actual_events', 0)
            
            if status == 'pending':
                pending_count += 1
            elif status == 'completed' and actual_events > 0:
                completed_with_events += 1
            elif status == 'completed' and actual_events == 0:
                completed_without_events += 1
                
        except Exception as e:
            logger.error(f"Error verifying {priority_file.name}: {str(e)}")
    
    print(f"\n📊 VERIFICATION RESULTS:")
    print(f"📁 Total Priorities: {total_priorities}")
    print(f"⏳ Pending (ready for research): {pending_count}")
    print(f"✅ Properly Completed (with events): {completed_with_events}")
    print(f"🚨 Still Falsely Completed: {completed_without_events}")
    
    if completed_without_events == 0:
        print(f"\n🎉 FIX SUCCESSFUL!")
        print(f"✅ No more falsely completed priorities")
        print(f"✅ {pending_count} priorities ready for proper research")
        return True
    else:
        print(f"\n⚠️  FIX INCOMPLETE")
        print(f"🚨 {completed_without_events} priorities still falsely marked completed")
        return False

if __name__ == "__main__":
    print("🚀 RESEARCH PRIORITY COMPLETION TRACKING FIX")
    print("=" * 65)
    
    # Fix false completions
    fix_success = fix_false_completions()
    
    # Verify the fix
    verify_success = verify_fix()
    
    if fix_success and verify_success:
        print(f"\n🎉 COMPLETION TRACKING FIXED!")
        print(f"✅ Research priorities now have accurate completion tracking")
        print(f"✅ System ready for proper research processing with event validation")
    else:
        print(f"\n⚠️  ISSUES REMAIN")
        print(f"Some priorities may still need manual attention")