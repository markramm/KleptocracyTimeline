#!/usr/bin/env python3
"""
Enhanced PDF Processing Strategy
Focus on timeline event enhancement and research priority generation rather than duplication
"""

import json
import os
from pathlib import Path
from datetime import datetime
import re

class EnhancedPDFProcessor:
    def __init__(self, timeline_dir="timeline_data/events", priorities_dir="research_priorities"):
        self.timeline_dir = Path(timeline_dir)
        self.priorities_dir = Path(priorities_dir)
        self.existing_events = self.load_existing_events()
    
    def load_existing_events(self):
        """Load all existing timeline events for deduplication"""
        events = {}
        for json_file in self.timeline_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    event = json.load(f)
                events[event.get('id', '')] = {
                    'file': json_file,
                    'title': event.get('title', ''),
                    'date': event.get('date', ''),
                    'tags': event.get('tags', []),
                    'actors': event.get('actors', []),
                    'importance': event.get('importance', 0)
                }
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        return events
    
    def find_similar_events(self, proposed_event_info):
        """Find existing events that might be similar to proposed event"""
        similar = []
        proposed_date = proposed_event_info.get('date', '')
        proposed_title = proposed_event_info.get('title', '').lower()
        proposed_actors = set(str(actor).lower() for actor in proposed_event_info.get('actors', []))
        
        for event_id, event_info in self.existing_events.items():
            # Date match
            if event_info['date'] == proposed_date:
                # Title similarity
                existing_title = event_info['title'].lower()
                title_words = set(proposed_title.split())
                existing_words = set(existing_title.split())
                
                if len(title_words.intersection(existing_words)) >= 3:
                    similar.append((event_id, event_info, 'title_similarity'))
                
                # Actor overlap
                existing_actors = set(str(actor).lower() for actor in event_info['actors'])
                if len(proposed_actors.intersection(existing_actors)) >= 1:
                    similar.append((event_id, event_info, 'actor_overlap'))
        
        return similar
    
    def enhance_existing_event(self, event_id, enhancement_data):
        """Enhance an existing event with new information instead of duplicating"""
        event_info = self.existing_events[event_id]
        event_file = event_info['file']
        
        try:
            with open(event_file, 'r') as f:
                event = json.load(f)
            
            # Add constitutional crisis context if missing
            if enhancement_data.get('constitutional_context'):
                if 'constitutional_issues' not in event:
                    event['constitutional_issues'] = []
                for issue in enhancement_data['constitutional_context']:
                    if issue not in event['constitutional_issues']:
                        event['constitutional_issues'].append(issue)
            
            # Upgrade importance if justified
            new_importance = enhancement_data.get('importance', 0)
            if new_importance > event.get('importance', 0):
                event['importance'] = new_importance
                event['_importance_upgraded'] = {
                    'from': event.get('importance', 0),
                    'to': new_importance,
                    'reason': enhancement_data.get('importance_reason', 'Constitutional crisis context'),
                    'date': datetime.now().isoformat()
                }
            
            # Add systematic pattern tags
            new_tags = enhancement_data.get('systematic_tags', [])
            existing_tags = set(event.get('tags', []))
            for tag in new_tags:
                if tag not in existing_tags:
                    event['tags'].append(tag)
            
            # Enhance historical significance
            if enhancement_data.get('systematic_significance'):
                if 'historical_significance' in event:
                    event['historical_significance'] += f" {enhancement_data['systematic_significance']}"
                else:
                    event['historical_significance'] = enhancement_data['systematic_significance']
            
            # Add enhancement note
            event['_enhanced_by_pdf'] = {
                'source': enhancement_data.get('pdf_source', 'PDF analysis'),
                'date': datetime.now().isoformat(),
                'enhancements': list(enhancement_data.keys())
            }
            
            # Write enhanced event
            with open(event_file, 'w') as f:
                json.dump(event, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error enhancing {event_file}: {e}")
            return False
    
    def create_research_priority(self, priority_data):
        """Create a new research priority instead of duplicating events"""
        priority_id = priority_data['id']
        priority_file = self.priorities_dir / f"{priority_id}.json"
        
        try:
            with open(priority_file, 'w') as f:
                json.dump(priority_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error creating research priority {priority_file}: {e}")
            return False
    
    def generate_pdf_processing_strategy(self, pdf_name):
        """Generate strategy for processing a specific PDF"""
        strategy = {
            'pdf_name': pdf_name,
            'focus': 'enhancement_and_priorities',
            'actions': []
        }
        
        # Define strategies for different PDF types
        if 'weaponization' in pdf_name.lower():
            strategy['actions'] = [
                'enhance_existing_government_events_with_weaponization_context',
                'create_systematic_weaponization_research_priorities',
                'identify_missing_institutional_capture_events',
                'upgrade_importance_scores_for_constitutional_violations'
            ]
        
        elif 'intelligence' in pdf_name.lower() or 'privatization' in pdf_name.lower():
            strategy['actions'] = [
                'enhance_existing_intelligence_events_with_privatization_context',
                'create_shadow_intelligence_research_priorities',
                'identify_missing_oversight_bypass_events',
                'upgrade_importance_for_constitutional_intelligence_violations'
            ]
        
        elif 'kleptocracy' in pdf_name.lower():
            strategy['actions'] = [
                'enhance_existing_corruption_events_with_systematic_context',
                'create_systematic_theft_research_priorities',
                'identify_missing_institutional_capture_mechanisms',
                'upgrade_importance_for_democratic_theft_patterns'
            ]
        
        return strategy

def process_pdf_content_intelligently(pdf_content, existing_events, strategy):
    """Process PDF content with intelligence to avoid duplication"""
    
    enhancements_made = 0
    priorities_created = 0
    
    # Extract key information from PDF content
    key_events = extract_key_events_from_pdf(pdf_content)
    systematic_patterns = extract_systematic_patterns(pdf_content)
    research_gaps = identify_research_gaps(pdf_content, existing_events)
    
    processor = EnhancedPDFProcessor()
    
    for event_info in key_events:
        # Check if this event already exists
        similar_events = processor.find_similar_events(event_info)
        
        if similar_events:
            # Enhance existing event instead of creating duplicate
            for event_id, existing_event, similarity_type in similar_events:
                enhancement_data = {
                    'constitutional_context': event_info.get('constitutional_issues', []),
                    'importance': event_info.get('importance', 0),
                    'importance_reason': f"Enhanced by {strategy['pdf_name']} analysis",
                    'systematic_tags': event_info.get('systematic_tags', []),
                    'systematic_significance': event_info.get('systematic_context', ''),
                    'pdf_source': strategy['pdf_name']
                }
                
                if processor.enhance_existing_event(event_id, enhancement_data):
                    enhancements_made += 1
                    print(f"✅ Enhanced existing event: {existing_event['title'][:60]}...")
        else:
            # Only create new event if it's truly missing and significant
            if event_info.get('importance', 0) >= 8:  # Only create high-importance events
                # This would create a new event, but with strict deduplication
                print(f"🆕 Would create new high-importance event: {event_info.get('title', '')[:60]}...")
    
    # Create research priorities for systematic patterns
    for pattern in systematic_patterns:
        priority_data = {
            'id': f"RT-{pattern['id']}",
            'title': pattern['title'],
            'description': pattern['description'],
            'priority': pattern['priority'],
            'status': 'pending',
            'category': pattern['category'],
            'tags': pattern['tags'],
            'estimated_events': pattern['estimated_events'],
            'created_date': datetime.now().date().isoformat(),
            'pdf_source': strategy['pdf_name']
        }
        
        if processor.create_research_priority(priority_data):
            priorities_created += 1
            print(f"🔬 Created research priority: {pattern['title'][:60]}...")
    
    return enhancements_made, priorities_created

def extract_key_events_from_pdf(content):
    """Extract key events from PDF content (placeholder)"""
    # This would analyze PDF content and extract events
    return []

def extract_systematic_patterns(content):
    """Extract systematic patterns for research priorities (placeholder)"""
    # This would analyze PDF content for systematic patterns
    return []

def identify_research_gaps(content, existing_events):
    """Identify research gaps that need investigation (placeholder)"""
    # This would identify what's missing from existing timeline
    return []

if __name__ == "__main__":
    processor = EnhancedPDFProcessor()
    
    print(f"📊 Loaded {len(processor.existing_events)} existing timeline events")
    print("🎯 Enhanced PDF processing focuses on:")
    print("   • Enhancing existing events with constitutional crisis context")
    print("   • Creating research priorities for systematic investigation")
    print("   • Avoiding duplicate event creation")
    print("   • Upgrading importance scores based on systematic analysis")