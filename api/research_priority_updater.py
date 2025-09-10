#!/usr/bin/env python3
"""
Research Priority Updater
Analyzes timeline events to identify completed research priorities and updates their status
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple

class ResearchPriorityUpdater:
    def __init__(self):
        self.timeline_dir = Path("timeline_data/events")
        self.priorities_dir = Path("research_priorities")
        self.completed_mappings = []
        
    def load_events(self) -> Dict[str, dict]:
        """Load all timeline events"""
        events = {}
        for event_file in self.timeline_dir.glob("*.json"):
            try:
                with open(event_file, 'r') as f:
                    event = json.load(f)
                    events[event['id']] = event
            except Exception as e:
                print(f"Error loading {event_file}: {e}")
        return events
    
    def load_priorities(self) -> Dict[str, dict]:
        """Load all research priorities"""
        priorities = {}
        for priority_file in self.priorities_dir.glob("RT-*.json"):
            try:
                with open(priority_file, 'r') as f:
                    priority = json.load(f)
                    priorities[priority['id']] = priority
            except Exception as e:
                print(f"Error loading {priority_file}: {e}")
        return priorities
    
    def match_events_to_priorities(self, events: Dict[str, dict], priorities: Dict[str, dict]) -> Dict[str, List[str]]:
        """Match events to research priorities based on tags, keywords, and content"""
        matches = {}
        
        for priority_id, priority in priorities.items():
            if priority.get('status') == 'completed':
                continue
                
            matched_events = []
            priority_tags = set(priority.get('tags', []))
            priority_keywords = self.extract_keywords(priority)
            
            for event_id, event in events.items():
                event_tags = set(event.get('tags', []))
                event_keywords = self.extract_keywords(event)
                
                # Check tag overlap
                tag_overlap = priority_tags & event_tags
                if len(tag_overlap) >= 2:  # At least 2 matching tags
                    matched_events.append(event_id)
                    continue
                
                # Check keyword overlap
                keyword_overlap = priority_keywords & event_keywords
                if len(keyword_overlap) >= 3:  # At least 3 matching keywords
                    matched_events.append(event_id)
            
            if matched_events:
                matches[priority_id] = matched_events
        
        return matches
    
    def extract_keywords(self, obj: dict) -> Set[str]:
        """Extract keywords from an object"""
        keywords = set()
        
        # Extract from title, summary, description
        for field in ['title', 'summary', 'description']:
            if field in obj:
                text = obj[field].lower()
                # Extract significant words
                words = text.split()
                for word in words:
                    word = word.strip('.,!?";:')
                    if len(word) > 4:  # Skip short words
                        keywords.add(word)
        
        # Add actors as keywords
        for actor in obj.get('actors', []):
            keywords.add(actor.lower().replace(' ', '-'))
        
        return keywords
    
    def analyze_completion(self, priority: dict, event_ids: List[str], events: Dict[str, dict]) -> Tuple[bool, str]:
        """Determine if a priority is completed based on matched events"""
        estimated = priority.get('estimated_events', 3)
        actual = len(event_ids)
        
        # Check if we have enough events
        if actual >= estimated * 0.8:  # 80% threshold
            # Verify event quality
            high_quality_count = 0
            for event_id in event_ids:
                event = events.get(event_id, {})
                if event.get('importance', 0) >= 7 and len(event.get('sources', [])) >= 2:
                    high_quality_count += 1
            
            if high_quality_count >= estimated * 0.6:  # 60% high quality
                return True, f"Completed with {actual} events ({high_quality_count} high quality)"
        
        return False, f"In progress: {actual}/{estimated} events"
    
    def update_priority(self, priority_file: Path, priority: dict, status: str, event_ids: List[str], reason: str):
        """Update a research priority's status"""
        priority['status'] = status
        priority['actual_events'] = len(event_ids)
        priority['updated_date'] = datetime.now().strftime('%Y-%m-%d')
        priority['completion_notes'] = reason
        priority['matched_events'] = event_ids[:10]  # Store up to 10 matching events
        
        # Write updated priority
        with open(priority_file, 'w') as f:
            json.dump(priority, f, indent=2)
        
        self.completed_mappings.append({
            'priority_id': priority['id'],
            'title': priority['title'],
            'status': status,
            'events_count': len(event_ids),
            'reason': reason
        })
    
    def generate_report(self) -> str:
        """Generate a report of updates"""
        report = ["# Research Priority Update Report\n"]
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if self.completed_mappings:
            report.append("## Priorities Updated\n")
            for mapping in self.completed_mappings:
                report.append(f"### {mapping['priority_id']}")
                report.append(f"- **Title**: {mapping['title']}")
                report.append(f"- **Status**: {mapping['status']}")
                report.append(f"- **Events**: {mapping['events_count']}")
                report.append(f"- **Reason**: {mapping['reason']}\n")
        else:
            report.append("No priorities were updated.\n")
        
        return '\n'.join(report)
    
    def run(self):
        """Main execution"""
        print("Loading timeline events...")
        events = self.load_events()
        print(f"Loaded {len(events)} events")
        
        print("Loading research priorities...")
        priorities = self.load_priorities()
        print(f"Loaded {len(priorities)} priorities")
        
        print("Matching events to priorities...")
        matches = self.match_events_to_priorities(events, priorities)
        print(f"Found matches for {len(matches)} priorities")
        
        print("\nAnalyzing completions...")
        for priority_id, event_ids in matches.items():
            priority = priorities[priority_id]
            priority_file = self.priorities_dir / f"{priority_id}.json"
            
            is_complete, reason = self.analyze_completion(priority, event_ids, events)
            
            if is_complete:
                print(f"✅ COMPLETED: {priority_id[:30]}... ({len(event_ids)} events)")
                self.update_priority(priority_file, priority, 'completed', event_ids, reason)
            elif len(event_ids) >= 2:
                print(f"🔄 IN PROGRESS: {priority_id[:30]}... ({len(event_ids)} events)")
                self.update_priority(priority_file, priority, 'in-progress', event_ids, reason)
        
        # Generate and save report
        report = self.generate_report()
        report_file = Path("research_priority_update_report.md")
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📊 Report saved to {report_file}")
        print(f"Updated {len(self.completed_mappings)} priorities")

if __name__ == "__main__":
    updater = ResearchPriorityUpdater()
    updater.run()