#!/usr/bin/env python3
"""
Event Validation Tracker
Tracks validation status for timeline events and provides a queue for human review
"""

import json
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class ValidationTracker:
    def __init__(self, events_dir: str = "events", tracker_file: str = "validation_status.json"):
        self.events_dir = Path(events_dir)
        self.tracker_file = Path(tracker_file)
        self.status = self.load_status()
        
    def load_status(self) -> Dict:
        """Load existing validation status or create new"""
        if self.tracker_file.exists():
            with open(self.tracker_file, 'r') as f:
                return json.load(f)
        return {
            "validated": {},
            "in_review": {},
            "needs_review": {},
            "problematic": {},
            "stats": {
                "total_events": 0,
                "validated_count": 0,
                "last_updated": None
            }
        }
    
    def save_status(self):
        """Save validation status to file"""
        self.status["stats"]["last_updated"] = datetime.now().isoformat()
        with open(self.tracker_file, 'w') as f:
            json.dump(self.status, f, indent=2)
    
    def scan_events(self) -> List[Dict]:
        """Scan all events and return list with importance and validation status"""
        events = []
        for yaml_file in self.events_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)
                    
                event_id = yaml_file.stem
                importance = data.get('importance', 5)
                
                # Determine validation status
                if event_id in self.status["validated"]:
                    validation_status = "validated"
                elif event_id in self.status["in_review"]:
                    validation_status = "in_review"
                elif event_id in self.status["problematic"]:
                    validation_status = "problematic"
                else:
                    validation_status = "needs_review"
                    
                events.append({
                    "id": event_id,
                    "file": str(yaml_file),
                    "date": data.get('date', ''),
                    "title": data.get('title', ''),
                    "importance": importance,
                    "status": data.get('status', 'unknown'),
                    "validation_status": validation_status,
                    "sources_count": len(data.get('sources', [])),
                    "has_archive": any('archive.org' in str(s.get('url', '')) 
                                     for s in data.get('sources', []))
                })
            except Exception as e:
                print(f"Error reading {yaml_file}: {e}")
                
        # Update total count
        self.status["stats"]["total_events"] = len(events)
        return events
    
    def get_validation_queue(self, limit: int = 20) -> List[Dict]:
        """Get prioritized queue of events to validate"""
        events = self.scan_events()
        
        # Filter to only needs_review
        needs_review = [e for e in events if e["validation_status"] == "needs_review"]
        
        # Sort by importance (desc) then by date
        needs_review.sort(key=lambda x: (-x["importance"], str(x["date"])))
        
        return needs_review[:limit]
    
    def mark_validated(self, event_id: str, validator: str = "unknown", notes: str = ""):
        """Mark an event as validated"""
        self.status["validated"][event_id] = {
            "validator": validator,
            "timestamp": datetime.now().isoformat(),
            "notes": notes
        }
        
        # Remove from other categories if present
        for category in ["in_review", "needs_review", "problematic"]:
            if event_id in self.status[category]:
                del self.status[category][event_id]
                
        self.status["stats"]["validated_count"] = len(self.status["validated"])
        self.save_status()
    
    def mark_problematic(self, event_id: str, issues: List[str], validator: str = "unknown"):
        """Mark an event as having issues"""
        self.status["problematic"][event_id] = {
            "issues": issues,
            "validator": validator,
            "timestamp": datetime.now().isoformat()
        }
        
        # Remove from other categories
        for category in ["validated", "in_review", "needs_review"]:
            if event_id in self.status[category]:
                del self.status[category][event_id]
                
        self.save_status()
    
    def mark_in_review(self, event_id: str, reviewer: str = "unknown"):
        """Mark an event as currently being reviewed"""
        self.status["in_review"][event_id] = {
            "reviewer": reviewer,
            "started": datetime.now().isoformat()
        }
        self.save_status()
    
    def get_stats(self) -> Dict:
        """Get validation statistics"""
        events = self.scan_events()
        
        # Count by validation status
        status_counts = {}
        for event in events:
            status = event["validation_status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by importance
        importance_counts = {}
        for event in events:
            imp = event["importance"]
            importance_counts[imp] = importance_counts.get(imp, 0) + 1
            
        # Count validated by importance
        validated_by_importance = {}
        for event_id in self.status["validated"]:
            event = next((e for e in events if e["id"] == event_id), None)
            if event:
                imp = event["importance"]
                validated_by_importance[imp] = validated_by_importance.get(imp, 0) + 1
        
        return {
            "total_events": len(events),
            "validation_status": status_counts,
            "importance_distribution": importance_counts,
            "validated_by_importance": validated_by_importance,
            "critical_events": len([e for e in events if e["importance"] >= 8]),
            "critical_validated": len([e for e in events 
                                      if e["importance"] >= 8 
                                      and e["validation_status"] == "validated"]),
            "percent_complete": round(status_counts.get("validated", 0) / len(events) * 100, 1)
        }
    
    def export_report(self, filename: str = "validation_report.md"):
        """Export validation report as markdown"""
        stats = self.get_stats()
        events = self.scan_events()
        
        report = f"""# Validation Status Report
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

## Summary
- **Total Events**: {stats['total_events']}
- **Validated**: {stats['validation_status'].get('validated', 0)} ({stats['percent_complete']}%)
- **Needs Review**: {stats['validation_status'].get('needs_review', 0)}
- **Problematic**: {stats['validation_status'].get('problematic', 0)}
- **In Review**: {stats['validation_status'].get('in_review', 0)}

## Critical Events (Importance 8+)
- **Total**: {stats['critical_events']}
- **Validated**: {stats['critical_validated']}
- **Remaining**: {stats['critical_events'] - stats['critical_validated']}

## By Importance Level
"""
        for imp in sorted(stats['importance_distribution'].keys(), reverse=True):
            total = stats['importance_distribution'][imp]
            validated = stats['validated_by_importance'].get(imp, 0)
            percent = round(validated / total * 100, 1) if total > 0 else 0
            report += f"- **Level {imp}**: {validated}/{total} validated ({percent}%)\n"
        
        # Add problematic events
        if self.status["problematic"]:
            report += "\n## Problematic Events\n"
            for event_id, details in self.status["problematic"].items():
                event = next((e for e in events if e["id"] == event_id), None)
                if event:
                    report += f"\n### {event['title']}\n"
                    report += f"- **ID**: {event_id}\n"
                    report += f"- **Issues**: {', '.join(details['issues'])}\n"
                    report += f"- **Reported by**: {details['validator']}\n"
        
        with open(filename, 'w') as f:
            f.write(report)
        
        return report


def main():
    """CLI for validation tracking"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Track event validation status")
    parser.add_argument('command', choices=['stats', 'queue', 'validate', 'problem', 'report'],
                       help='Command to run')
    parser.add_argument('--event-id', help='Event ID for validate/problem commands')
    parser.add_argument('--validator', default='unknown', help='Validator name')
    parser.add_argument('--notes', default='', help='Validation notes')
    parser.add_argument('--issues', nargs='+', help='Issues for problematic events')
    parser.add_argument('--limit', type=int, default=20, help='Queue limit')
    
    args = parser.parse_args()
    
    tracker = ValidationTracker()
    
    if args.command == 'stats':
        stats = tracker.get_stats()
        print(json.dumps(stats, indent=2))
        
    elif args.command == 'queue':
        queue = tracker.get_validation_queue(args.limit)
        print(f"\nValidation Queue (Next {args.limit} events by priority):\n")
        print(f"{'Importance':<12} {'Date':<12} {'ID':<50} {'Sources'}")
        print("-" * 90)
        for event in queue:
            print(f"{event['importance']:<12} {event['date']:<12} {event['id'][:50]:<50} {event['sources_count']}")
            
    elif args.command == 'validate':
        if not args.event_id:
            print("Error: --event-id required for validate command")
            return
        tracker.mark_validated(args.event_id, args.validator, args.notes)
        print(f"Marked {args.event_id} as validated")
        
    elif args.command == 'problem':
        if not args.event_id or not args.issues:
            print("Error: --event-id and --issues required for problem command")
            return
        tracker.mark_problematic(args.event_id, args.issues, args.validator)
        print(f"Marked {args.event_id} as problematic")
        
    elif args.command == 'report':
        report = tracker.export_report()
        print(report)
        print("\nReport saved to validation_report.md")


if __name__ == "__main__":
    main()