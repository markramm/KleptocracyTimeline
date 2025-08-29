"""
Temporal Reasoning Engine

Advanced temporal reasoning for understanding event sequences,
causality, and temporal relationships in research data.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TemporalConfig:
    """Configuration for temporal reasoning."""
    # Temporal window settings
    causality_window_days: int = 30    # Max days for causal relationships
    correlation_window_days: int = 90   # Max days for correlations
    
    # Analysis settings
    min_events_for_pattern: int = 3
    min_confidence_for_causality: float = 0.7
    
    # Temporal granularity
    default_granularity: str = 'day'  # day, week, month, year
    
    # Pattern detection
    enable_trend_detection: bool = True
    enable_cycle_detection: bool = True
    enable_anomaly_detection: bool = True


@dataclass
class TemporalRelationship:
    """Represents a temporal relationship between events."""
    event1_id: str
    event2_id: str
    relationship_type: str  # before, after, concurrent, causes, caused_by
    confidence: float
    time_delta: Optional[timedelta] = None
    evidence: List[str] = field(default_factory=list)


@dataclass
class TemporalPattern:
    """Represents a temporal pattern in events."""
    pattern_type: str  # trend, cycle, burst, anomaly
    events: List[str]  # Event IDs involved
    confidence: float
    
    # Pattern characteristics
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    frequency: Optional[float] = None  # Events per time unit
    periodicity: Optional[int] = None  # For cycles, in days
    
    description: str = ''
    evidence: List[str] = field(default_factory=list)


class TemporalReasoner:
    """
    Advanced temporal reasoning for event analysis.
    
    Features:
    - Temporal relationship extraction
    - Causality inference
    - Pattern detection (trends, cycles, anomalies)
    - Timeline reconstruction
    - Temporal consistency checking
    """
    
    def __init__(self, 
                 events_corpus: List[Dict[str, Any]],
                 config: Optional[TemporalConfig] = None):
        """
        Initialize temporal reasoner.
        
        Args:
            events_corpus: Complete corpus of events
            config: Temporal reasoning configuration
        """
        self.events_corpus = events_corpus
        self.config = config or TemporalConfig()
        
        # Build temporal indices
        self._build_temporal_indices()
        
        # Reasoning statistics
        self.reasoning_stats = defaultdict(int)
        
        logger.info(f"Initialized TemporalReasoner with {len(events_corpus)} events")
    
    def _build_temporal_indices(self):
        """Build indices for efficient temporal reasoning."""
        # Chronological index
        self.events_by_date = defaultdict(list)
        
        # Actor timeline index
        self.actor_timelines = defaultdict(list)
        
        # Tag timeline index
        self.tag_timelines = defaultdict(list)
        
        # Build indices
        for event in self.events_corpus:
            date = event.get('date', '')
            if date:
                self.events_by_date[date].append(event)
                
                # Index by actors
                actors = event.get('actors', [])
                if isinstance(actors, str):
                    actors = [actors]
                for actor in actors:
                    if actor:
                        self.actor_timelines[actor.lower()].append({
                            'date': date,
                            'event': event
                        })
                
                # Index by tags
                tags = event.get('tags', [])
                if isinstance(tags, str):
                    tags = [tags]
                for tag in tags:
                    if tag:
                        self.tag_timelines[tag.lower()].append({
                            'date': date,
                            'event': event
                        })
        
        # Sort timelines chronologically
        for timeline in self.actor_timelines.values():
            timeline.sort(key=lambda x: x['date'])
        
        for timeline in self.tag_timelines.values():
            timeline.sort(key=lambda x: x['date'])
    
    def analyze_temporal_relationships(self, 
                                     event1: Dict[str, Any],
                                     event2: Dict[str, Any]) -> Optional[TemporalRelationship]:
        """
        Analyze temporal relationship between two events.
        
        Args:
            event1: First event
            event2: Second event
            
        Returns:
            TemporalRelationship if one exists
        """
        date1 = event1.get('date', '')
        date2 = event2.get('date', '')
        
        if not date1 or not date2:
            return None
        
        # Parse dates
        parsed1 = self._parse_date(date1)
        parsed2 = self._parse_date(date2)
        
        if not parsed1 or not parsed2:
            return None
        
        # Calculate time difference
        time_delta = parsed2 - parsed1
        
        # Determine relationship type
        if abs(time_delta.days) <= 1:
            rel_type = 'concurrent'
            confidence = 0.9
        elif time_delta.days > 0:
            rel_type = 'before'  # event1 before event2
            confidence = 1.0
        else:
            rel_type = 'after'  # event1 after event2
            confidence = 1.0
        
        # Check for potential causality
        causality = self._check_causality(event1, event2, time_delta)
        if causality:
            rel_type = causality['type']
            confidence = causality['confidence']
        
        self.reasoning_stats['relationships_analyzed'] += 1
        
        return TemporalRelationship(
            event1_id=event1.get('id', ''),
            event2_id=event2.get('id', ''),
            relationship_type=rel_type,
            confidence=confidence,
            time_delta=time_delta,
            evidence=[f"Time difference: {time_delta.days} days"]
        )
    
    def _check_causality(self, event1: Dict, event2: Dict, time_delta: timedelta) -> Optional[Dict]:
        """Check for potential causal relationship."""
        # Only consider causality within window
        if abs(time_delta.days) > self.config.causality_window_days:
            return None
        
        # Check if events share actors (increases causality likelihood)
        actors1 = set(event1.get('actors', []))
        actors2 = set(event2.get('actors', []))
        
        common_actors = actors1.intersection(actors2)
        
        if not common_actors:
            return None
        
        # Simple causality heuristics
        confidence = 0.5
        
        # Boost confidence for short time gaps
        if 0 < time_delta.days <= 7:
            confidence += 0.2
        
        # Check for causal keywords
        causal_keywords = ['led to', 'resulted in', 'caused', 'triggered', 'following']
        
        text1 = f"{event1.get('title', '')} {event1.get('summary', '')}".lower()
        text2 = f"{event2.get('title', '')} {event2.get('summary', '')}".lower()
        
        if any(keyword in text2 for keyword in causal_keywords):
            confidence += 0.2
        
        if confidence >= self.config.min_confidence_for_causality:
            if time_delta.days > 0:
                return {'type': 'causes', 'confidence': confidence}
            else:
                return {'type': 'caused_by', 'confidence': confidence}
        
        return None
    
    def detect_temporal_patterns(self, 
                                actor: Optional[str] = None,
                                tag: Optional[str] = None,
                                date_range: Optional[Tuple[str, str]] = None) -> List[TemporalPattern]:
        """
        Detect temporal patterns in event sequences.
        
        Args:
            actor: Specific actor to analyze
            tag: Specific tag to analyze
            date_range: Date range to analyze
            
        Returns:
            List of detected temporal patterns
        """
        patterns = []
        
        # Get relevant events
        if actor:
            timeline = self.actor_timelines.get(actor.lower(), [])
            events = [item['event'] for item in timeline]
        elif tag:
            timeline = self.tag_timelines.get(tag.lower(), [])
            events = [item['event'] for item in timeline]
        else:
            events = self.events_corpus
        
        # Filter by date range if specified
        if date_range:
            events = self._filter_by_date_range(events, date_range)
        
        if len(events) < self.config.min_events_for_pattern:
            return patterns
        
        # Detect different pattern types
        if self.config.enable_trend_detection:
            trend_patterns = self._detect_trends(events)
            patterns.extend(trend_patterns)
        
        if self.config.enable_cycle_detection:
            cycle_patterns = self._detect_cycles(events)
            patterns.extend(cycle_patterns)
        
        if self.config.enable_anomaly_detection:
            anomaly_patterns = self._detect_anomalies(events)
            patterns.extend(anomaly_patterns)
        
        self.reasoning_stats['patterns_detected'] += len(patterns)
        
        return patterns
    
    def _detect_trends(self, events: List[Dict]) -> List[TemporalPattern]:
        """Detect trending patterns in events."""
        patterns = []
        
        # Group events by time period
        events_by_month = defaultdict(list)
        
        for event in events:
            date = event.get('date', '')
            if date and len(date) >= 7:
                month = date[:7]
                events_by_month[month].append(event)
        
        # Sort months
        sorted_months = sorted(events_by_month.keys())
        
        if len(sorted_months) < 3:
            return patterns
        
        # Calculate event frequency per month
        frequencies = [len(events_by_month[month]) for month in sorted_months]
        
        # Simple trend detection using linear regression
        if len(frequencies) >= 3:
            x = np.arange(len(frequencies))
            y = np.array(frequencies)
            
            # Calculate trend
            slope = np.polyfit(x, y, 1)[0]
            
            if abs(slope) > 0.5:  # Significant trend
                trend_type = 'increasing' if slope > 0 else 'decreasing'
                
                pattern = TemporalPattern(
                    pattern_type='trend',
                    events=[e.get('id', '') for month in sorted_months 
                           for e in events_by_month[month]],
                    confidence=min(1.0, abs(slope) / 2),
                    start_date=sorted_months[0],
                    end_date=sorted_months[-1],
                    frequency=np.mean(frequencies),
                    description=f"{trend_type.capitalize()} trend detected with slope {slope:.2f}"
                )
                
                patterns.append(pattern)
        
        return patterns
    
    def _detect_cycles(self, events: List[Dict]) -> List[TemporalPattern]:
        """Detect cyclical patterns in events."""
        patterns = []
        
        # Group events by date
        dates = []
        for event in events:
            date = event.get('date', '')
            if date:
                parsed = self._parse_date(date)
                if parsed:
                    dates.append(parsed)
        
        if len(dates) < 4:
            return patterns
        
        # Sort dates
        dates.sort()
        
        # Calculate intervals between consecutive events
        intervals = []
        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i-1]).days
            if interval > 0:
                intervals.append(interval)
        
        if len(intervals) < 3:
            return patterns
        
        # Look for regular intervals (cycles)
        interval_counts = defaultdict(int)
        for interval in intervals:
            # Group similar intervals (within 3 days)
            key = round(interval / 3) * 3
            interval_counts[key] += 1
        
        # Find most common interval
        if interval_counts:
            most_common_interval = max(interval_counts.keys(), 
                                      key=lambda k: interval_counts[k])
            frequency = interval_counts[most_common_interval]
            
            if frequency >= 2:  # At least 2 occurrences of the pattern
                pattern = TemporalPattern(
                    pattern_type='cycle',
                    events=[e.get('id', '') for e in events],
                    confidence=min(1.0, frequency / len(intervals)),
                    periodicity=most_common_interval,
                    description=f"Cyclical pattern with ~{most_common_interval} day period"
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_anomalies(self, events: List[Dict]) -> List[TemporalPattern]:
        """Detect anomalous temporal patterns."""
        patterns = []
        
        # Group events by date
        events_by_date = defaultdict(list)
        
        for event in events:
            date = event.get('date', '')
            if date:
                events_by_date[date].append(event)
        
        # Find dates with unusual activity
        event_counts = [len(events) for events in events_by_date.values()]
        
        if len(event_counts) < 5:
            return patterns
        
        # Calculate statistics
        mean_count = np.mean(event_counts)
        std_count = np.std(event_counts)
        
        # Detect anomalies (> 2 standard deviations)
        for date, date_events in events_by_date.items():
            count = len(date_events)
            
            if std_count > 0:
                z_score = (count - mean_count) / std_count
                
                if abs(z_score) > 2:
                    pattern = TemporalPattern(
                        pattern_type='anomaly',
                        events=[e.get('id', '') for e in date_events],
                        confidence=min(1.0, abs(z_score) / 3),
                        start_date=date,
                        end_date=date,
                        description=f"Anomalous activity on {date}: {count} events (z-score: {z_score:.2f})"
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def reconstruct_timeline(self, 
                           actor: Optional[str] = None,
                           tag: Optional[str] = None,
                           include_causal: bool = True) -> List[Dict]:
        """
        Reconstruct a complete timeline with relationships.
        
        Args:
            actor: Specific actor timeline
            tag: Specific tag timeline
            include_causal: Include causal relationships
            
        Returns:
            Chronological timeline with relationships
        """
        # Get relevant events
        if actor:
            timeline_data = self.actor_timelines.get(actor.lower(), [])
            events = [item['event'] for item in timeline_data]
        elif tag:
            timeline_data = self.tag_timelines.get(tag.lower(), [])
            events = [item['event'] for item in timeline_data]
        else:
            events = sorted(self.events_corpus, 
                          key=lambda x: x.get('date', ''))
        
        timeline = []
        
        for i, event in enumerate(events):
            timeline_entry = {
                'event': event,
                'position': i,
                'relationships': []
            }
            
            # Find relationships with neighboring events
            if include_causal and i > 0:
                prev_event = events[i-1]
                relationship = self.analyze_temporal_relationships(prev_event, event)
                
                if relationship and relationship.relationship_type in ['causes', 'caused_by']:
                    timeline_entry['relationships'].append({
                        'type': relationship.relationship_type,
                        'with': prev_event.get('id'),
                        'confidence': relationship.confidence
                    })
            
            timeline.append(timeline_entry)
        
        self.reasoning_stats['timelines_reconstructed'] += 1
        
        return timeline
    
    def check_temporal_consistency(self, events: List[Dict[str, Any]]) -> List[Dict]:
        """
        Check for temporal inconsistencies in events.
        
        Args:
            events: Events to check
            
        Returns:
            List of inconsistencies found
        """
        inconsistencies = []
        
        # Check each pair of events
        for i, event1 in enumerate(events):
            for event2 in events[i+1:]:
                # Check for impossible temporal relationships
                issue = self._check_temporal_impossibility(event1, event2)
                if issue:
                    inconsistencies.append(issue)
        
        self.reasoning_stats['consistency_checks'] += 1
        
        return inconsistencies
    
    def _check_temporal_impossibility(self, event1: Dict, event2: Dict) -> Optional[Dict]:
        """Check if two events have impossible temporal relationship."""
        # Check if same actor in two places at same time
        actors1 = set(event1.get('actors', []))
        actors2 = set(event2.get('actors', []))
        
        common_actors = actors1.intersection(actors2)
        
        if common_actors:
            date1 = event1.get('date', '')
            date2 = event2.get('date', '')
            
            if date1 and date2 and date1 == date2:
                location1 = event1.get('location', '')
                location2 = event2.get('location', '')
                
                if location1 and location2 and location1 != location2:
                    return {
                        'type': 'temporal_impossibility',
                        'events': [event1.get('id'), event2.get('id')],
                        'actor': list(common_actors)[0],
                        'date': date1,
                        'locations': [location1, location2],
                        'description': f"Same actor in different locations on same date"
                    }
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        try:
            # Try different date formats
            formats = [
                '%Y-%m-%d',
                '%Y-%m',
                '%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Date parsing failed for {date_str}: {e}")
            return None
    
    def _filter_by_date_range(self, events: List[Dict], 
                            date_range: Tuple[str, str]) -> List[Dict]:
        """Filter events by date range."""
        start_date, end_date = date_range
        
        filtered = []
        for event in events:
            date = event.get('date', '')
            if date and start_date <= date <= end_date:
                filtered.append(event)
        
        return filtered
    
    def get_temporal_summary(self, events: List[Dict]) -> Dict[str, Any]:
        """Get temporal summary of events."""
        if not events:
            return {}
        
        dates = []
        for event in events:
            date = event.get('date', '')
            if date:
                parsed = self._parse_date(date)
                if parsed:
                    dates.append(parsed)
        
        if not dates:
            return {}
        
        dates.sort()
        
        # Calculate temporal statistics
        total_span = (dates[-1] - dates[0]).days
        
        intervals = []
        for i in range(1, len(dates)):
            intervals.append((dates[i] - dates[i-1]).days)
        
        return {
            'total_events': len(events),
            'date_range': {
                'start': dates[0].strftime('%Y-%m-%d'),
                'end': dates[-1].strftime('%Y-%m-%d'),
                'span_days': total_span
            },
            'temporal_density': len(events) / (total_span + 1) if total_span > 0 else 0,
            'interval_stats': {
                'mean': np.mean(intervals) if intervals else 0,
                'median': np.median(intervals) if intervals else 0,
                'std': np.std(intervals) if intervals else 0,
                'min': min(intervals) if intervals else 0,
                'max': max(intervals) if intervals else 0
            }
        }
    
    def get_reasoning_stats(self) -> Dict[str, Any]:
        """Get temporal reasoning statistics."""
        return dict(self.reasoning_stats)