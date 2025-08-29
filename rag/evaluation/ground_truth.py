"""
Ground Truth Data Management for RAG Evaluation

Manages ground truth annotations for evaluation, including
relevant event mappings, expected results, and validation data.
"""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from datetime import datetime
import hashlib


class GroundTruthManager:
    """
    Manages ground truth data for research-grade RAG evaluation.
    """
    
    def __init__(self, ground_truth_path: str = None, events_dir: str = None):
        """
        Initialize ground truth manager.
        
        Args:
            ground_truth_path: Path to ground truth JSON file
            events_dir: Path to timeline events directory
        """
        self.ground_truth_path = Path(ground_truth_path or 'ground_truth.json')
        self.events_dir = Path(events_dir or '../../timeline_data/events')
        
        # Load or initialize ground truth data
        if self.ground_truth_path.exists():
            self.ground_truth = self.load_ground_truth()
        else:
            self.ground_truth = self.initialize_ground_truth()
        
        # Cache event data for quick lookup
        self.events_cache = {}
        self.load_events_cache()
    
    def initialize_ground_truth(self) -> Dict[str, Any]:
        """
        Initialize empty ground truth structure.
        
        Returns:
            Initial ground truth dictionary
        """
        return {
            'version': '1.0.0',
            'created': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'query_annotations': {},
            'event_relationships': {},
            'critical_events': [],
            'metadata': {
                'total_events': 0,
                'annotated_queries': 0,
                'coverage_percentage': 0.0
            }
        }
    
    def load_ground_truth(self) -> Dict[str, Any]:
        """
        Load ground truth from file.
        
        Returns:
            Ground truth dictionary
        """
        with open(self.ground_truth_path, 'r') as f:
            return json.load(f)
    
    def save_ground_truth(self):
        """Save ground truth to file."""
        self.ground_truth['last_updated'] = datetime.now().isoformat()
        self.ground_truth['metadata']['annotated_queries'] = len(self.ground_truth['query_annotations'])
        
        with open(self.ground_truth_path, 'w') as f:
            json.dump(self.ground_truth, f, indent=2)
    
    def load_events_cache(self):
        """Load all events into cache for quick lookup."""
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
        
        self.ground_truth['metadata']['total_events'] = len(self.events_cache)
    
    def add_query_annotation(self, query_id: str, query_text: str,
                            relevant_event_ids: List[str],
                            irrelevant_event_ids: List[str] = None,
                            metadata: Dict[str, Any] = None):
        """
        Add or update ground truth annotation for a query.
        
        Args:
            query_id: Unique identifier for the query
            query_text: The actual query text
            relevant_event_ids: List of relevant event IDs
            irrelevant_event_ids: Optional list of explicitly irrelevant IDs
            metadata: Optional metadata about the annotation
        """
        annotation = {
            'query_id': query_id,
            'query_text': query_text,
            'relevant_events': relevant_event_ids,
            'irrelevant_events': irrelevant_event_ids or [],
            'annotated_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        # Validate event IDs exist
        for event_id in relevant_event_ids:
            if event_id not in self.events_cache:
                print(f"Warning: Event {event_id} not found in events cache")
        
        self.ground_truth['query_annotations'][query_id] = annotation
        self.save_ground_truth()
    
    def get_relevant_events(self, query_id: str) -> List[str]:
        """
        Get list of relevant event IDs for a query.
        
        Args:
            query_id: Query identifier
            
        Returns:
            List of relevant event IDs
        """
        annotation = self.ground_truth['query_annotations'].get(query_id, {})
        return annotation.get('relevant_events', [])
    
    def get_irrelevant_events(self, query_id: str) -> List[str]:
        """
        Get list of explicitly irrelevant event IDs for a query.
        
        Args:
            query_id: Query identifier
            
        Returns:
            List of irrelevant event IDs
        """
        annotation = self.ground_truth['query_annotations'].get(query_id, {})
        return annotation.get('irrelevant_events', [])
    
    def add_event_relationship(self, event_id1: str, event_id2: str,
                              relationship_type: str, strength: float = 1.0):
        """
        Add relationship between two events.
        
        Args:
            event_id1: First event ID
            event_id2: Second event ID
            relationship_type: Type of relationship (e.g., 'related', 'causal', 'temporal')
            strength: Relationship strength (0-1)
        """
        if 'relationships' not in self.ground_truth['event_relationships']:
            self.ground_truth['event_relationships']['relationships'] = []
        
        relationship = {
            'event_id1': event_id1,
            'event_id2': event_id2,
            'type': relationship_type,
            'strength': strength,
            'added_at': datetime.now().isoformat()
        }
        
        self.ground_truth['event_relationships']['relationships'].append(relationship)
        self.save_ground_truth()
    
    def mark_critical_event(self, event_id: str, reason: str = None):
        """
        Mark an event as critical (must never be missed).
        
        Args:
            event_id: Event ID to mark as critical
            reason: Optional reason for criticality
        """
        critical_entry = {
            'event_id': event_id,
            'reason': reason,
            'marked_at': datetime.now().isoformat()
        }
        
        # Avoid duplicates
        existing_ids = [e['event_id'] for e in self.ground_truth['critical_events']]
        if event_id not in existing_ids:
            self.ground_truth['critical_events'].append(critical_entry)
            self.save_ground_truth()
    
    def get_critical_events(self) -> List[str]:
        """
        Get list of critical event IDs.
        
        Returns:
            List of critical event IDs
        """
        return [e['event_id'] for e in self.ground_truth['critical_events']]
    
    def calculate_coverage_stats(self) -> Dict[str, Any]:
        """
        Calculate coverage statistics for ground truth.
        
        Returns:
            Dictionary with coverage statistics
        """
        all_annotated_events = set()
        for annotation in self.ground_truth['query_annotations'].values():
            all_annotated_events.update(annotation.get('relevant_events', []))
        
        coverage_percentage = (len(all_annotated_events) / len(self.events_cache) * 100
                             if self.events_cache else 0)
        
        stats = {
            'total_events': len(self.events_cache),
            'annotated_events': len(all_annotated_events),
            'coverage_percentage': coverage_percentage,
            'total_queries': len(self.ground_truth['query_annotations']),
            'critical_events': len(self.ground_truth['critical_events']),
            'relationships': len(self.ground_truth['event_relationships'].get('relationships', []))
        }
        
        return stats
    
    def auto_annotate_by_tags(self, query_id: str, query_text: str,
                             required_tags: List[str], optional_tags: List[str] = None):
        """
        Automatically annotate query based on event tags.
        
        Args:
            query_id: Query identifier
            query_text: Query text
            required_tags: Tags that must be present
            optional_tags: Additional tags that increase relevance
        """
        relevant_events = []
        
        for event_id, event in self.events_cache.items():
            event_tags = set(event.get('tags', []))
            
            # Check if all required tags are present
            if all(tag in event_tags for tag in required_tags):
                relevant_events.append(event_id)
            # Or if any optional tags with at least one required tag
            elif optional_tags and any(tag in event_tags for tag in required_tags):
                if any(tag in event_tags for tag in optional_tags):
                    relevant_events.append(event_id)
        
        self.add_query_annotation(
            query_id=query_id,
            query_text=query_text,
            relevant_event_ids=relevant_events,
            metadata={'auto_annotated': True, 'method': 'tags'}
        )
    
    def auto_annotate_by_actors(self, query_id: str, query_text: str,
                               actors: List[str]):
        """
        Automatically annotate query based on actors.
        
        Args:
            query_id: Query identifier
            query_text: Query text
            actors: List of actors that should be present
        """
        relevant_events = []
        
        for event_id, event in self.events_cache.items():
            event_actors = event.get('actors', [])
            if isinstance(event_actors, str):
                event_actors = [event_actors]
            
            if any(actor in event_actors for actor in actors):
                relevant_events.append(event_id)
        
        self.add_query_annotation(
            query_id=query_id,
            query_text=query_text,
            relevant_event_ids=relevant_events,
            metadata={'auto_annotated': True, 'method': 'actors'}
        )
    
    def auto_annotate_by_date_range(self, query_id: str, query_text: str,
                                   start_date: str, end_date: str,
                                   additional_filters: Dict[str, Any] = None):
        """
        Automatically annotate query based on date range.
        
        Args:
            query_id: Query identifier
            query_text: Query text
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            additional_filters: Optional additional filters
        """
        relevant_events = []
        
        for event_id, event in self.events_cache.items():
            event_date = event.get('date', '')
            
            if start_date <= event_date <= end_date:
                # Apply additional filters if provided
                if additional_filters:
                    match = True
                    for key, value in additional_filters.items():
                        if key == 'tags':
                            event_tags = set(event.get('tags', []))
                            if not any(tag in event_tags for tag in value):
                                match = False
                        elif key == 'status':
                            if event.get('status') not in value:
                                match = False
                        elif key == 'min_importance':
                            if event.get('importance', 0) < value:
                                match = False
                    
                    if match:
                        relevant_events.append(event_id)
                else:
                    relevant_events.append(event_id)
        
        self.add_query_annotation(
            query_id=query_id,
            query_text=query_text,
            relevant_event_ids=relevant_events,
            metadata={'auto_annotated': True, 'method': 'date_range'}
        )
    
    def validate_annotations(self) -> Dict[str, List[str]]:
        """
        Validate ground truth annotations for issues.
        
        Returns:
            Dictionary of validation issues
        """
        issues = {
            'missing_events': [],
            'duplicate_annotations': [],
            'empty_annotations': [],
            'invalid_relationships': []
        }
        
        # Check for missing events in annotations
        for query_id, annotation in self.ground_truth['query_annotations'].items():
            for event_id in annotation.get('relevant_events', []):
                if event_id not in self.events_cache:
                    issues['missing_events'].append(f"{query_id}: {event_id}")
            
            if not annotation.get('relevant_events'):
                issues['empty_annotations'].append(query_id)
        
        # Check for invalid relationships
        for relationship in self.ground_truth['event_relationships'].get('relationships', []):
            if relationship['event_id1'] not in self.events_cache:
                issues['invalid_relationships'].append(f"Missing: {relationship['event_id1']}")
            if relationship['event_id2'] not in self.events_cache:
                issues['invalid_relationships'].append(f"Missing: {relationship['event_id2']}")
        
        return issues
    
    def export_for_training(self, output_path: str = None) -> Dict[str, Any]:
        """
        Export ground truth in format suitable for model training.
        
        Args:
            output_path: Optional path to save export
            
        Returns:
            Training data dictionary
        """
        training_data = {
            'queries': [],
            'metadata': self.calculate_coverage_stats()
        }
        
        for query_id, annotation in self.ground_truth['query_annotations'].items():
            query_data = {
                'id': query_id,
                'text': annotation['query_text'],
                'relevant_docs': annotation['relevant_events'],
                'irrelevant_docs': annotation.get('irrelevant_events', [])
            }
            training_data['queries'].append(query_data)
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(training_data, f, indent=2)
        
        return training_data
    
    def import_from_test_queries(self, test_queries: List[Dict[str, Any]]):
        """
        Import ground truth from test queries dataset.
        
        Args:
            test_queries: List of test query dictionaries
        """
        for query in test_queries:
            if 'expected_event_ids' in query and query['expected_event_ids']:
                self.add_query_annotation(
                    query_id=query['id'],
                    query_text=query['query'],
                    relevant_event_ids=query['expected_event_ids'],
                    metadata={
                        'type': query.get('type'),
                        'difficulty': query.get('difficulty'),
                        'priority': query.get('priority')
                    }
                )
    
    def get_annotation_summary(self) -> str:
        """
        Get human-readable summary of ground truth annotations.
        
        Returns:
            Summary string
        """
        stats = self.calculate_coverage_stats()
        
        summary = f"""
Ground Truth Summary
====================
Total Events in Timeline: {stats['total_events']}
Annotated Events: {stats['annotated_events']} ({stats['coverage_percentage']:.1f}% coverage)
Total Queries: {stats['total_queries']}
Critical Events: {stats['critical_events']}
Event Relationships: {stats['relationships']}

Last Updated: {self.ground_truth['last_updated']}
        """
        
        return summary


if __name__ == '__main__':
    # Example usage
    manager = GroundTruthManager()
    
    # Import from test queries
    from test_queries import TEST_QUERIES
    manager.import_from_test_queries(TEST_QUERIES)
    
    # Auto-annotate some queries
    manager.auto_annotate_by_tags(
        'auto_democracy',
        'Find all events threatening democracy',
        required_tags=['democracy']
    )
    
    manager.auto_annotate_by_date_range(
        'auto_jan_2025',
        'Events in January 2025',
        '2025-01-01',
        '2025-01-31'
    )
    
    # Mark critical events
    critical_events = [
        '2025-01-20--trump-memecoin-launch',
        '2025-01-23--trump-signs-order-ending-dei-programs',
        '2025-01-01--epstein-files-release-cancelled'
    ]
    
    for event_id in critical_events:
        manager.mark_critical_event(event_id, "High importance for democracy timeline")
    
    # Print summary
    print(manager.get_annotation_summary())
    
    # Validate
    issues = manager.validate_annotations()
    if any(issues.values()):
        print("\nValidation Issues Found:")
        for issue_type, issue_list in issues.items():
            if issue_list:
                print(f"  {issue_type}: {len(issue_list)} issues")