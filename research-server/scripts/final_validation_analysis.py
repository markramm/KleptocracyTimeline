#!/usr/bin/env python3
import os
import json
import sys
sys.path.append('/Users/markr/kleptocracy-timeline')
from enhanced_event_validator import validate_and_fix_events

def load_all_timeline_events():
    """Load all timeline events from the events directory"""
    events_dir = '/Users/markr/kleptocracy-timeline/timeline_data/events'
    events = []
    failed_files = []
    total_files = 0
    event_keys_summary = {}
    
    for filename in os.listdir(events_dir):
        if filename.endswith('.json'):
            total_files += 1
            try:
                with open(os.path.join(events_dir, filename), 'r') as f:
                    event = json.load(f)
                    events.append(event)
                    
                    # Track keys across all events
                    for key in event.keys():
                        if key not in event_keys_summary:
                            event_keys_summary[key] = 1
                        else:
                            event_keys_summary[key] += 1
            except (json.JSONDecodeError, IOError) as e:
                print(f"Failed to load file {filename}: {e}")
                failed_files.append(filename)
    
    print(f"Total files: {total_files}")
    print(f"Total events loaded: {len(events)}")
    print(f"Failed files: {failed_files}")
    
    # Detailed key analysis
    print("\nKey Distribution Across Events:")
    for key, count in sorted(event_keys_summary.items(), key=lambda x: x[1], reverse=True):
        print(f"{key}: {count} events ({count/len(events)*100:.2f}%)")
    
    # Comprehensive validation
    mandatory_keys = ['date', 'title', 'summary', 'actors', 'sources', 'tags', 'importance', 'id']
    missing_keys_summary = {}
    
    for i, event in enumerate(events):
        missing_keys = [key for key in mandatory_keys if key not in event]
        if missing_keys:
            missing_keys_summary[i] = missing_keys
    
    print("\nEvents with Missing Mandatory Keys:")
    for event_index, missing_keys in missing_keys_summary.items():
        print(f"Event {event_index}: Missing keys {missing_keys}")
    
    return events

def analyze_validation_results(validation_results):
    """Generate detailed analysis of validation results"""
    summary = validation_results['summary']
    results = validation_results['results']
    fixed_events = validation_results.get('fixed_events', [])
    
    # Categorize fix types
    fix_types = {
        'missing_fields': 0,
        'type_conversions': 0,
        'id_format_fixes': 0,
        'date_format_fixes': 0,
        'importance_score_fixes': 0,
        'source_fixes': 0,
        'actor_fixes': 0,
        'tag_fixes': 0
    }
    
    # Detailed error tracking
    detailed_errors = []
    detailed_missing_fields = {}
    detailed_type_conversion_issues = {}
    
    for i, result in enumerate(results):
        # Track missing fields per event
        missing_fields = [error for error in result['errors'] if 'missing field' in error.lower()]
        if missing_fields:
            detailed_missing_fields[i] = missing_fields
            detailed_errors.extend(missing_fields)
            fix_types['missing_fields'] += len(missing_fields)
        
        # Track type conversion issues
        type_conversion_errors = [error for error in result['errors'] if 'field must be' in error.lower()]
        if type_conversion_errors:
            detailed_type_conversion_issues[i] = type_conversion_errors
            detailed_errors.extend(type_conversion_errors)
            fix_types['type_conversions'] += len(type_conversion_errors)
        
        # Warnings analysis
        warnings = result.get('warnings', [])
        for warning in warnings:
            if 'fixed ID format' in warning:
                fix_types['id_format_fixes'] += 1
            elif 'fixed date format' in warning:
                fix_types['date_format_fixes'] += 1
            elif 'importance score' in warning:
                fix_types['importance_score_fixes'] += 1
            elif 'converted string source' in warning or 'Added missing outlet' in warning:
                fix_types['source_fixes'] += 1
            elif 'Added placeholder actor' in warning:
                fix_types['actor_fixes'] += 1
            elif 'Added placeholder tags' in warning:
                fix_types['tag_fixes'] += 1
    
    # Detailed field analysis
    print("\nDetailed Missing Fields Analysis:")
    for event_index, fields in detailed_missing_fields.items():
        print(f"Event {event_index}: Missing fields - {', '.join(fields)}")
    
    print("\nDetailed Type Conversion Issues:")
    for event_index, errors in detailed_type_conversion_issues.items():
        print(f"Event {event_index}: Type conversion errors - {', '.join(errors)}")
    
    # Prepare detailed report
    report = {
        'total_events': summary['total_events'],
        'valid_events_before': summary['total_events'] - summary['total_errors'],
        'valid_events_after': summary['valid_events'],
        'total_errors': summary['total_errors'],
        'total_warnings': summary['total_warnings'],
        'total_fixes': summary['fixes_applied'],
        'validation_improvement_percentage': (summary['valid_events'] / summary['total_events']) * 100,
        'fix_types_breakdown': fix_types,
        'detailed_errors': detailed_errors,
        'missing_fields_by_event': detailed_missing_fields,
        'type_conversion_issues_by_event': detailed_type_conversion_issues
    }
    
    return report

def main():
    events = load_all_timeline_events()
    validation_results = validate_and_fix_events(events)
    analysis = analyze_validation_results(validation_results)
    
    # Save report to markdown
    with open('/Users/markr/kleptocracy-timeline/FINAL_VALIDATION_REPORT.md', 'w') as f:
        f.write("# Final Validation Report\n\n")
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Events Analyzed**: {analysis['total_events']}\n")
        f.write(f"- **Valid Events Before Validation**: {analysis['valid_events_before']}\n")
        f.write(f"- **Valid Events After Validation**: {analysis['valid_events_after']}\n")
        f.write(f"- **Validation Improvement**: {analysis['validation_improvement_percentage']:.2f}%\n\n")
        
        f.write("## Validation Statistics\n\n")
        f.write(f"- **Total Errors Found**: {analysis['total_errors']}\n")
        f.write(f"- **Total Warnings Generated**: {analysis['total_warnings']}\n")
        f.write(f"- **Total Fixes Applied**: {analysis['total_fixes']}\n\n")
        
        f.write("## Fix Types Breakdown\n\n")
        for fix_type, count in analysis['fix_types_breakdown'].items():
            f.write(f"- **{fix_type.replace('_', ' ').title()}**: {count}\n")
        
        f.write("\n## Recommendations\n\n")
        f.write("1. Implement automated pre-submission validation\n")
        f.write("2. Standardize event entry processes\n")
        f.write("3. Create clear documentation for event field requirements\n")
        f.write("4. Regular data quality audits\n")
        
    print("Validation report generated successfully.")

if __name__ == '__main__':
    main()