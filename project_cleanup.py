#!/usr/bin/env python3
"""
Project Cleanup Script
Clean up completed one-time scripts and organize documentation
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

def cleanup_project():
    """Clean up completed scripts and organize documentation"""
    
    print("=== PROJECT CLEANUP ===\n")
    
    # Create cleanup directories
    cleanup_date = datetime.now().strftime('%Y%m%d_%H%M%S')
    completed_scripts_dir = f"archive/completed_scripts_{cleanup_date}"
    outdated_docs_dir = f"archive/outdated_docs_{cleanup_date}"
    
    os.makedirs(completed_scripts_dir, exist_ok=True)
    os.makedirs(outdated_docs_dir, exist_ok=True)
    
    # One-time duplicate cleanup scripts (completed successfully)
    duplicate_cleanup_scripts = [
        "cleanup_lisa_cook_duplicates.py",
        "cleanup_panama_papers_duplicates.py", 
        "cleanup_id_pattern_duplicates.py",
        "cleanup_same_date_title_duplicates.py",
        "DUPLICATE_DETECTION_ANALYSIS.py",
        "cleanup_completed_priorities.py"
    ]
    
    print("Moving completed duplicate cleanup scripts:")
    for script in duplicate_cleanup_scripts:
        if os.path.exists(script):
            dest = os.path.join(completed_scripts_dir, script)
            shutil.move(script, dest)
            print(f"  Moved: {script} → {dest}")
    
    # One-time analysis and fix scripts
    analysis_scripts = [
        "fix_timeline_events.py",
        "test_id_fix.py",
        "analyze_ttt_batch1.py",
        "detailed_validation_analysis.py",
        "fix_malformed_events.py",
        "validate_timeline_events.py",
        "validate_timeline_integration.py",
        "validate_existing_events.py",
        "enhanced_event_validator.py"
    ]
    
    print("\nMoving completed analysis and fix scripts:")
    for script in analysis_scripts:
        if os.path.exists(script):
            dest = os.path.join(completed_scripts_dir, script)
            shutil.move(script, dest)
            print(f"  Moved: {script} → {dest}")
    
    # Outdated documentation (specific TTT batch reports)
    outdated_docs = [
        "TTT_BATCH1_ANALYSIS_REPORT.md",
        "TTT_Batch2_Analysis_Report.md", 
        "TTT_BATCH3_ANALYSIS_REPORT.md",
        "TTT_BATCH4_ANALYSIS_REPORT.md",
        "TTT_BATCH5_ANALYSIS_REPORT.md",
        "TTT_BATCH6_FINAL_REPORT.md",
        "ttt_batch1_analysis_summary.md",
        "TRUMP_TYRANNY_TRACKER_ANALYSIS.md",
        "TRUMP_TYRANNY_TRACKER_FINAL_SUMMARY.md",
        "TIMELINE_EVENT_VALIDATION_REPORT.md",
        "FINAL_VALIDATION_REPORT.md",
        "INTEGRATION_VALIDATION_REPORT.md", 
        "VALIDATION_ANALYSIS_RUNS_2_AND_3.md",
        "VALIDATION_REPORT.md",
        "QA_BATCH_RESERVATION_BUG_REPORT.md",
        "CONTAMINATION_ARCHIVE_2025-09-11.md",
        "enhanced_research_agent2_report.md",
        "DUPLICATE_CLEANUP_STRATEGY.md",
        "PLACEHOLDER_SOURCE_QA_ANALYSIS.md",
        "SOURCE_VALIDATION_TIMEOUT_GUIDE.md"
    ]
    
    print("\nMoving outdated documentation:")
    for doc in outdated_docs:
        if os.path.exists(doc):
            dest = os.path.join(outdated_docs_dir, doc)
            shutil.move(doc, dest)
            print(f"  Moved: {doc} → {dest}")
    
    # Remove empty backup directories from duplicate cleanup
    backup_dirs = [
        d for d in os.listdir('.') 
        if d.startswith(('duplicates_backup_', 'id_pattern_cleanup_', 
                        'same_date_title_cleanup_', 'lisa_cook_cleanup_'))
    ]
    
    print("\nRemoving empty backup directories:")
    for backup_dir in backup_dirs:
        if os.path.isdir(backup_dir):
            try:
                # Check if directory is empty or only contains empty files
                files = os.listdir(backup_dir)
                if not files or all(os.path.getsize(os.path.join(backup_dir, f)) == 0 for f in files):
                    shutil.rmtree(backup_dir)
                    print(f"  Removed: {backup_dir}")
                else:
                    print(f"  Kept (has content): {backup_dir}")
            except Exception as e:
                print(f"  Error removing {backup_dir}: {e}")
    
    # Clean up temporary files
    temp_files = [
        "tmp_enhanced_event.json",
        "tmp_event_enhancement.json", 
        "enhanced_event.json",
        "enhanced_event_2025-02-04.json",
        "problematic_events.json",
        "qa_enhancement.json",
        "qa_score.json",
        "validation_sample.json",
        "validation_report.json",
        "event_validation_report.txt",
        "ttt_batch4_detailed_analysis.json"
    ]
    
    print("\nRemoving temporary files:")
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            print(f"  Removed: {temp_file}")
    
    print(f"\n=== CLEANUP COMPLETE ===")
    print(f"Completed scripts archived to: {completed_scripts_dir}")
    print(f"Outdated docs archived to: {outdated_docs_dir}")
    print("Project directory cleaned and organized")
    
    return len(duplicate_cleanup_scripts) + len(analysis_scripts), len(outdated_docs)

if __name__ == "__main__":
    cleanup_project()