#!/usr/bin/env python3
"""
Build Complete Ground Truth Dataset for RAG Evaluation

This script creates a comprehensive ground truth dataset by:
1. Loading all timeline events
2. Processing test queries
3. Auto-annotating based on multiple strategies
4. Manual verification for critical queries
"""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Set
from datetime import datetime
import re
import sys

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from evaluation.ground_truth import GroundTruthManager
from evaluation.test_queries import TEST_QUERIES


class GroundTruthBuilder:
    """Builds comprehensive ground truth annotations."""
    
    def __init__(self):
        """Initialize builder with events and ground truth manager."""
        self.events_dir = Path('../timeline_data/events')
        self.gt_manager = GroundTruthManager(
            ground_truth_path='ground_truth.json',
            events_dir='../timeline_data/events'
        )
        self.events_cache = {}
        self.load_all_events()
    
    def load_all_events(self):
        """Load all events from YAML files."""
        print(f"Loading events from {self.events_dir}...")
        
        if not self.events_dir.exists():
            print(f"Warning: Events directory {self.events_dir} does not exist")
            return
        
        for yaml_file in self.events_dir.glob('*.yaml'):
            try:
                with open(yaml_file, 'r') as f:
                    event = yaml.safe_load(f)
                    if event and 'id' in event:
                        self.events_cache[event['id']] = event
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")
        
        print(f"Loaded {len(self.events_cache)} events")
    
    def find_relevant_events(self, query: Dict[str, Any]) -> List[str]:
        """
        Find relevant events for a query using multiple strategies.
        
        Args:
            query: Test query dictionary
            
        Returns:
            List of relevant event IDs
        """
        relevant = set()
        query_text = query['query'].lower()
        
        # Strategy 1: Expected event IDs (if provided)
        if 'expected_event_ids' in query and query['expected_event_ids']:
            for event_id in query['expected_event_ids']:
                if event_id in self.events_cache:
                    relevant.add(event_id)
        
        # Strategy 2: Tag matching
        if 'expected_tags' in query:
            for event_id, event in self.events_cache.items():
                event_tags = set(event.get('tags', []))
                if any(tag in event_tags for tag in query['expected_tags']):
                    relevant.add(event_id)
        
        # Strategy 3: Actor matching
        if 'expected_actors' in query:
            for event_id, event in self.events_cache.items():
                event_actors = event.get('actors', [])
                if isinstance(event_actors, str):
                    event_actors = [event_actors]
                
                for actor in query['expected_actors']:
                    if any(actor.lower() in str(a).lower() for a in event_actors):
                        relevant.add(event_id)
        
        # Strategy 4: Date range matching
        if 'date_range' in query:
            start_date, end_date = query['date_range']
            # Convert to strings if they're not already
            if not isinstance(start_date, str):
                start_date = str(start_date)
            if not isinstance(end_date, str):
                end_date = str(end_date)
            
            for event_id, event in self.events_cache.items():
                event_date = str(event.get('date', ''))
                if event_date and start_date <= event_date <= end_date:
                    # Apply additional filters
                    if 'expected_tags' not in query or \
                       any(tag in event.get('tags', []) for tag in query.get('expected_tags', [])):
                        relevant.add(event_id)
        
        # Strategy 5: Keyword matching in title and summary
        keywords = self.extract_keywords(query_text)
        for event_id, event in self.events_cache.items():
            event_text = f"{event.get('title', '')} {event.get('summary', '')}".lower()
            
            # Count keyword matches
            match_score = sum(1 for keyword in keywords if keyword in event_text)
            
            # Require at least 2 keyword matches or 1 exact phrase match
            if match_score >= 2:
                relevant.add(event_id)
            elif any(phrase in event_text for phrase in self.extract_phrases(query_text)):
                relevant.add(event_id)
        
        # Strategy 6: Semantic concept matching
        if 'semantic_concepts' in query:
            concept_map = {
                'corruption': ['corrupt', 'bribe', 'kickback', 'graft', 'pay-to-play'],
                'democracy': ['democratic', 'voting', 'election', 'suffrage', 'representation'],
                'authoritarianism': ['authoritarian', 'autocrat', 'dictator', 'tyranny'],
                'regulatory-capture': ['regulatory', 'deregulation', 'industry-friendly'],
                'judicial': ['court', 'judge', 'judicial', 'supreme court', 'appellate'],
            }
            
            for event_id, event in self.events_cache.items():
                event_text = f"{event.get('title', '')} {event.get('summary', '')} {' '.join(event.get('tags', []))}".lower()
                
                for concept in query.get('semantic_concepts', []):
                    if concept in concept_map:
                        if any(term in event_text for term in concept_map[concept]):
                            relevant.add(event_id)
        
        # Strategy 7: Status filtering
        if 'expected_status' in query:
            relevant = {
                eid for eid in relevant 
                if self.events_cache[eid].get('status') in query['expected_status']
            }
        
        # Strategy 8: Importance filtering
        if 'min_importance' in query:
            relevant = {
                eid for eid in relevant 
                if self.events_cache[eid].get('importance', 0) >= query['min_importance']
            }
        
        return list(relevant)
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from query text."""
        # Remove common words
        stopwords = {'what', 'show', 'find', 'get', 'all', 'the', 'of', 'and', 'or', 
                    'in', 'to', 'for', 'with', 'about', 'events', 'related', 'involving'}
        
        words = text.lower().split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        
        return keywords
    
    def extract_phrases(self, text: str) -> List[str]:
        """Extract meaningful phrases from query text."""
        phrases = []
        
        # Common important phrases
        phrase_patterns = [
            'schedule f',
            'regulatory capture',
            'judicial capture',
            'executive order',
            'conflicts of interest',
            'foreign influence',
            'media manipulation',
            'democracy erosion',
            'rule of law',
            'separation of powers'
        ]
        
        text_lower = text.lower()
        for phrase in phrase_patterns:
            if phrase in text_lower:
                phrases.append(phrase)
        
        return phrases
    
    def build_ground_truth(self):
        """Build complete ground truth dataset from test queries."""
        print("\n" + "="*60)
        print("BUILDING GROUND TRUTH DATASET")
        print("="*60)
        
        stats = {
            'total_queries': len(TEST_QUERIES),
            'annotated': 0,
            'total_relevant': 0,
            'coverage': set()
        }
        
        for i, query in enumerate(TEST_QUERIES, 1):
            print(f"\n[{i}/{len(TEST_QUERIES)}] Processing: {query['id']}")
            print(f"  Query: {query['query']}")
            
            # Find relevant events
            relevant_events = self.find_relevant_events(query)
            
            if relevant_events:
                print(f"  Found {len(relevant_events)} relevant events")
                
                # Add annotation
                self.gt_manager.add_query_annotation(
                    query_id=query['id'],
                    query_text=query['query'],
                    relevant_event_ids=relevant_events,
                    metadata={
                        'type': query.get('type'),
                        'difficulty': query.get('difficulty'),
                        'priority': query.get('priority'),
                        'auto_annotated': True,
                        'annotation_strategies': ['expected_ids', 'tags', 'actors', 
                                                'keywords', 'semantic']
                    }
                )
                
                stats['annotated'] += 1
                stats['total_relevant'] += len(relevant_events)
                stats['coverage'].update(relevant_events)
            else:
                print(f"  WARNING: No relevant events found")
        
        # Mark critical events
        print("\n" + "-"*40)
        print("Marking critical events...")
        
        critical_patterns = [
            ('schedule-f', 'Schedule F implementation critical for democracy'),
            ('democracy', 'Direct threat to democratic institutions'),
            ('judicial-capture', 'Judicial independence compromised'),
            ('election-integrity', 'Election integrity concerns'),
            ('executive-orders', 'Major executive action')
        ]
        
        critical_count = 0
        for event_id, event in self.events_cache.items():
            event_tags = event.get('tags', [])
            for tag_pattern, reason in critical_patterns:
                if tag_pattern in event_tags and event.get('importance', 0) >= 7:
                    self.gt_manager.mark_critical_event(event_id, reason)
                    critical_count += 1
                    break
        
        print(f"Marked {critical_count} critical events")
        
        # Print summary statistics
        coverage_pct = len(stats['coverage']) / len(self.events_cache) * 100 if self.events_cache else 0
        
        print("\n" + "="*60)
        print("GROUND TRUTH DATASET COMPLETE")
        print("="*60)
        print(f"Total Queries: {stats['total_queries']}")
        print(f"Annotated Queries: {stats['annotated']}")
        print(f"Total Relevant Events: {stats['total_relevant']}")
        print(f"Average Relevant per Query: {stats['total_relevant']/stats['annotated']:.1f}")
        print(f"Event Coverage: {len(stats['coverage'])}/{len(self.events_cache)} ({coverage_pct:.1f}%)")
        
        # Save validation report
        validation_issues = self.gt_manager.validate_annotations()
        if any(validation_issues.values()):
            print("\nValidation Issues:")
            for issue_type, issues in validation_issues.items():
                if issues:
                    print(f"  {issue_type}: {len(issues)} issues")
        
        # Export for training
        print("\nExporting training data...")
        self.gt_manager.export_for_training('ground_truth_training.json')
        
        print("\n✓ Ground truth dataset saved to ground_truth.json")
        print("✓ Training export saved to ground_truth_training.json")
        
        return stats


def main():
    """Main execution function."""
    builder = GroundTruthBuilder()
    stats = builder.build_ground_truth()
    
    # Print final summary
    print("\n" + "="*60)
    print(builder.gt_manager.get_annotation_summary())
    

if __name__ == '__main__':
    main()