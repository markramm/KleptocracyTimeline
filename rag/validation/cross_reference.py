"""
Cross-Reference Validation System

Validates information consistency across multiple sources and events,
ensuring research-grade accuracy and completeness.
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
from collections import defaultdict, Counter
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """Configuration for cross-reference validation."""
    # Validation thresholds
    min_source_agreement: float = 0.7      # Minimum agreement between sources
    min_temporal_consistency: float = 0.8   # Temporal consistency threshold
    min_entity_confidence: float = 0.75     # Entity resolution confidence
    
    # Cross-reference settings
    enable_source_validation: bool = True
    enable_temporal_validation: bool = True
    enable_entity_validation: bool = True
    enable_fact_validation: bool = True
    
    # Conflict resolution
    conflict_resolution_strategy: str = 'weighted_consensus'  # majority, weighted, latest
    weight_by_source_quality: bool = True
    weight_by_temporal_proximity: bool = True
    
    # Research optimizations
    require_multiple_sources: bool = True
    min_source_count: int = 2
    boost_verified_sources: bool = True


@dataclass
class ValidationResult:
    """Result of cross-reference validation."""
    event_id: str
    validation_score: float
    confidence_level: str  # high, medium, low
    
    # Validation details
    source_validation: Dict[str, Any] = field(default_factory=dict)
    temporal_validation: Dict[str, Any] = field(default_factory=dict)
    entity_validation: Dict[str, Any] = field(default_factory=dict)
    fact_validation: Dict[str, Any] = field(default_factory=dict)
    
    # Issues found
    inconsistencies: List[Dict] = field(default_factory=list)
    conflicts: List[Dict] = field(default_factory=list)
    missing_info: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)


class CrossReferenceValidator:
    """
    Advanced cross-reference validation for research-grade accuracy.
    
    Features:
    - Multi-source validation and agreement checking
    - Temporal consistency validation
    - Entity resolution and disambiguation
    - Fact verification across events
    - Conflict detection and resolution
    """
    
    def __init__(self, 
                 events_corpus: List[Dict[str, Any]],
                 config: Optional[ValidationConfig] = None):
        """
        Initialize cross-reference validator.
        
        Args:
            events_corpus: Complete corpus of events for cross-referencing
            config: Validation configuration
        """
        self.events_corpus = events_corpus
        self.config = config or ValidationConfig()
        
        # Build indices for efficient cross-referencing
        self._build_indices()
        
        # Validation statistics
        self.validation_stats = defaultdict(int)
        
        logger.info(f"Initialized CrossReferenceValidator with {len(events_corpus)} events")
    
    def _build_indices(self):
        """Build indices for efficient cross-referencing."""
        # Entity index: entity -> list of event IDs
        self.entity_index = defaultdict(list)
        
        # Date index: date -> list of event IDs
        self.date_index = defaultdict(list)
        
        # Source index: source -> list of event IDs
        self.source_index = defaultdict(list)
        
        # Topic/tag index: tag -> list of event IDs
        self.tag_index = defaultdict(list)
        
        for event in self.events_corpus:
            event_id = event.get('id', str(hash(str(event))))
            
            # Index entities/actors
            actors = event.get('actors', [])
            if isinstance(actors, str):
                actors = [actors]
            for actor in actors:
                if actor:
                    self.entity_index[actor.lower()].append(event_id)
            
            # Index dates
            date = event.get('date', '')
            if date:
                self.date_index[date].append(event_id)
                # Also index by year and month
                if len(date) >= 4:
                    self.date_index[date[:4]].append(event_id)  # Year
                if len(date) >= 7:
                    self.date_index[date[:7]].append(event_id)  # Year-month
            
            # Index sources
            sources = event.get('sources', [])
            for source in sources:
                if isinstance(source, dict):
                    source_id = source.get('url', source.get('title', ''))
                else:
                    source_id = str(source)
                if source_id:
                    self.source_index[source_id].append(event_id)
            
            # Index tags
            tags = event.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            for tag in tags:
                if tag:
                    self.tag_index[tag.lower()].append(event_id)
    
    def validate_event(self, event: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single event through cross-referencing.
        
        Args:
            event: Event to validate
            
        Returns:
            ValidationResult with scores and findings
        """
        event_id = event.get('id', str(hash(str(event))))
        result = ValidationResult(event_id=event_id, validation_score=0.0, confidence_level='low')
        
        # Run validation modules
        validation_scores = []
        
        if self.config.enable_source_validation:
            source_score, source_details = self._validate_sources(event)
            result.source_validation = source_details
            validation_scores.append(source_score)
            self.validation_stats['source_validations'] += 1
        
        if self.config.enable_temporal_validation:
            temporal_score, temporal_details = self._validate_temporal_consistency(event)
            result.temporal_validation = temporal_details
            validation_scores.append(temporal_score)
            self.validation_stats['temporal_validations'] += 1
        
        if self.config.enable_entity_validation:
            entity_score, entity_details = self._validate_entities(event)
            result.entity_validation = entity_details
            validation_scores.append(entity_score)
            self.validation_stats['entity_validations'] += 1
        
        if self.config.enable_fact_validation:
            fact_score, fact_details = self._validate_facts(event)
            result.fact_validation = fact_details
            validation_scores.append(fact_score)
            self.validation_stats['fact_validations'] += 1
        
        # Calculate overall validation score
        if validation_scores:
            result.validation_score = np.mean(validation_scores)
        
        # Determine confidence level
        if result.validation_score >= 0.85:
            result.confidence_level = 'high'
        elif result.validation_score >= 0.65:
            result.confidence_level = 'medium'
        else:
            result.confidence_level = 'low'
        
        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)
        
        return result
    
    def _validate_sources(self, event: Dict[str, Any]) -> Tuple[float, Dict]:
        """Validate event sources and cross-check information."""
        sources = event.get('sources', [])
        
        if not sources:
            return 0.0, {'status': 'no_sources', 'score': 0.0}
        
        # Check source count
        source_count = len(sources)
        if self.config.require_multiple_sources and source_count < self.config.min_source_count:
            return 0.5, {
                'status': 'insufficient_sources',
                'count': source_count,
                'required': self.config.min_source_count,
                'score': 0.5
            }
        
        # Analyze source quality
        source_quality_scores = []
        for source in sources:
            quality_score = self._assess_source_quality(source)
            source_quality_scores.append(quality_score)
        
        avg_quality = np.mean(source_quality_scores) if source_quality_scores else 0.0
        
        # Check for corroborating events
        corroborating_events = self._find_corroborating_events(event)
        corroboration_score = min(1.0, len(corroborating_events) / 3)  # Cap at 3 corroborating events
        
        # Calculate overall source validation score
        validation_score = (avg_quality * 0.6 + corroboration_score * 0.4)
        
        return validation_score, {
            'status': 'validated',
            'source_count': source_count,
            'avg_quality': avg_quality,
            'corroborating_events': len(corroborating_events),
            'corroboration_score': corroboration_score,
            'score': validation_score
        }
    
    def _assess_source_quality(self, source: Any) -> float:
        """Assess quality of a source."""
        if isinstance(source, dict):
            # Check for verified flag
            if source.get('verified', False):
                return 1.0
            
            # Check for reputable domains
            url = source.get('url', '')
            reputable_domains = [
                '.gov', '.edu', 'reuters.com', 'apnews.com', 
                'bbc.com', 'npr.org', 'pbs.org', '.org'
            ]
            
            for domain in reputable_domains:
                if domain in url.lower():
                    return 0.9
            
            # Check for date
            if source.get('date'):
                return 0.7
            
            return 0.5
        
        return 0.3  # Basic source reference
    
    def _find_corroborating_events(self, event: Dict[str, Any]) -> List[str]:
        """Find events that corroborate the given event."""
        corroborating = []
        
        # Find events with similar actors on similar dates
        actors = event.get('actors', [])
        if isinstance(actors, str):
            actors = [actors]
        
        date = event.get('date', '')
        event_id = event.get('id')
        
        for actor in actors:
            if actor:
                related_events = self.entity_index.get(actor.lower(), [])
                for related_id in related_events:
                    if related_id != event_id:
                        related_event = self._get_event_by_id(related_id)
                        if related_event:
                            # Check temporal proximity
                            if self._events_temporally_related(event, related_event):
                                corroborating.append(related_id)
        
        return list(set(corroborating))[:5]  # Return up to 5 corroborating events
    
    def _validate_temporal_consistency(self, event: Dict[str, Any]) -> Tuple[float, Dict]:
        """Validate temporal consistency of event."""
        date = event.get('date', '')
        
        if not date:
            return 0.0, {'status': 'no_date', 'score': 0.0}
        
        # Check for temporal conflicts with related events
        conflicts = []
        related_events = self._find_temporally_related_events(event)
        
        for related_id in related_events:
            related_event = self._get_event_by_id(related_id)
            if related_event:
                conflict = self._check_temporal_conflict(event, related_event)
                if conflict:
                    conflicts.append(conflict)
        
        # Calculate temporal consistency score
        if conflicts:
            consistency_score = max(0.0, 1.0 - (len(conflicts) * 0.2))
        else:
            consistency_score = 1.0
        
        # Check date format validity
        date_valid = self._validate_date_format(date)
        if not date_valid:
            consistency_score *= 0.8
        
        return consistency_score, {
            'status': 'validated',
            'date': date,
            'date_valid': date_valid,
            'conflicts': conflicts,
            'related_events': len(related_events),
            'score': consistency_score
        }
    
    def _validate_entities(self, event: Dict[str, Any]) -> Tuple[float, Dict]:
        """Validate and resolve entities in event."""
        actors = event.get('actors', [])
        if isinstance(actors, str):
            actors = [actors]
        
        if not actors:
            return 0.0, {'status': 'no_entities', 'score': 0.0}
        
        # Entity resolution and disambiguation
        resolved_entities = []
        ambiguous_entities = []
        
        for actor in actors:
            if actor:
                resolution = self._resolve_entity(actor)
                if resolution['confidence'] >= self.config.min_entity_confidence:
                    resolved_entities.append(resolution)
                else:
                    ambiguous_entities.append(resolution)
        
        # Calculate entity validation score
        if resolved_entities:
            avg_confidence = np.mean([r['confidence'] for r in resolved_entities])
            ambiguity_penalty = len(ambiguous_entities) * 0.1
            validation_score = max(0.0, avg_confidence - ambiguity_penalty)
        else:
            validation_score = 0.3
        
        return validation_score, {
            'status': 'validated',
            'total_entities': len(actors),
            'resolved': len(resolved_entities),
            'ambiguous': len(ambiguous_entities),
            'avg_confidence': avg_confidence if resolved_entities else 0.0,
            'score': validation_score
        }
    
    def _resolve_entity(self, entity_name: str) -> Dict[str, Any]:
        """Resolve and disambiguate an entity name."""
        entity_lower = entity_name.lower()
        
        # Check how many events reference this entity
        event_references = self.entity_index.get(entity_lower, [])
        reference_count = len(event_references)
        
        # Look for variations and aliases
        variations = self._find_entity_variations(entity_name)
        
        # Calculate confidence based on consistency
        if reference_count > 5:
            confidence = min(1.0, 0.7 + (reference_count * 0.02))
        elif reference_count > 2:
            confidence = 0.6
        else:
            confidence = 0.4
        
        # Boost confidence for well-known entities
        known_entities = [
            'trump', 'biden', 'musk', 'bezos', 'zuckerberg',
            'department of justice', 'supreme court', 'congress'
        ]
        
        if any(known in entity_lower for known in known_entities):
            confidence = min(1.0, confidence + 0.2)
        
        return {
            'entity': entity_name,
            'canonical_form': self._get_canonical_entity_name(entity_name, variations),
            'confidence': confidence,
            'references': reference_count,
            'variations': variations
        }
    
    def _find_entity_variations(self, entity_name: str) -> List[str]:
        """Find variations of an entity name in the corpus."""
        variations = set()
        entity_lower = entity_name.lower()
        
        # Check for partial matches
        parts = entity_lower.split()
        if len(parts) > 1:
            last_name = parts[-1]
            
            for entity in self.entity_index.keys():
                if last_name in entity and entity != entity_lower:
                    variations.add(entity)
        
        # Check for initials
        if len(parts) == 2 and len(parts[0]) == 1:
            # e.g., "J. Smith"
            for entity in self.entity_index.keys():
                if parts[1] in entity and entity != entity_lower:
                    entity_parts = entity.split()
                    if len(entity_parts) >= 2 and entity_parts[-1] == parts[1]:
                        variations.add(entity)
        
        return list(variations)[:5]
    
    def _get_canonical_entity_name(self, entity_name: str, variations: List[str]) -> str:
        """Get canonical form of entity name."""
        # Use the most complete version
        all_forms = [entity_name] + variations
        
        # Prefer longer, more complete names
        all_forms.sort(key=lambda x: len(x), reverse=True)
        
        # Return the longest form that's not too long
        for form in all_forms:
            if len(form) <= 50:  # Reasonable name length
                return form
        
        return entity_name
    
    def _validate_facts(self, event: Dict[str, Any]) -> Tuple[float, Dict]:
        """Validate factual claims in event."""
        # Extract factual claims from event
        claims = self._extract_factual_claims(event)
        
        if not claims:
            return 0.7, {'status': 'no_explicit_claims', 'score': 0.7}
        
        # Validate each claim
        validated_claims = []
        disputed_claims = []
        unverified_claims = []
        
        for claim in claims:
            validation = self._validate_claim(claim, event)
            
            if validation['status'] == 'validated':
                validated_claims.append(claim)
            elif validation['status'] == 'disputed':
                disputed_claims.append(claim)
            else:
                unverified_claims.append(claim)
        
        # Calculate fact validation score
        total_claims = len(claims)
        if total_claims > 0:
            validation_score = (
                len(validated_claims) / total_claims * 1.0 +
                len(unverified_claims) / total_claims * 0.5 -
                len(disputed_claims) / total_claims * 0.3
            )
            validation_score = max(0.0, min(1.0, validation_score))
        else:
            validation_score = 0.5
        
        return validation_score, {
            'status': 'validated',
            'total_claims': total_claims,
            'validated': len(validated_claims),
            'disputed': len(disputed_claims),
            'unverified': len(unverified_claims),
            'score': validation_score
        }
    
    def _extract_factual_claims(self, event: Dict[str, Any]) -> List[Dict]:
        """Extract factual claims from event text."""
        claims = []
        
        # Extract from summary
        summary = event.get('summary', '')
        
        # Look for specific claim patterns
        claim_patterns = [
            r'(\d+)\s+(percent|%)',  # Percentages
            r'\$[\d,]+\s*(million|billion)?',  # Money amounts
            r'(first|largest|biggest|smallest)',  # Superlatives
            r'(confirmed|verified|proven)',  # Verification claims
            r'(signed|passed|enacted|approved)',  # Action claims
        ]
        
        for pattern in claim_patterns:
            matches = re.findall(pattern, summary, re.IGNORECASE)
            for match in matches:
                claims.append({
                    'type': 'extracted',
                    'pattern': pattern,
                    'text': str(match)
                })
        
        # Extract importance claims
        if event.get('importance', 0) >= 8:
            claims.append({
                'type': 'importance',
                'text': f"High importance event (score: {event.get('importance')})"
            })
        
        return claims
    
    def _validate_claim(self, claim: Dict, event: Dict) -> Dict[str, str]:
        """Validate a specific factual claim."""
        # Simple validation based on corroboration
        corroborating_events = self._find_corroborating_events(event)
        
        if len(corroborating_events) >= 2:
            return {'status': 'validated'}
        elif len(corroborating_events) == 1:
            return {'status': 'unverified'}
        else:
            # Check if claim is disputed by checking for conflicting events
            if self._has_conflicting_claims(claim, event):
                return {'status': 'disputed'}
            return {'status': 'unverified'}
    
    def _has_conflicting_claims(self, claim: Dict, event: Dict) -> bool:
        """Check if claim has conflicts with other events."""
        # This is a simplified check
        # In a real system, this would do semantic comparison
        return False
    
    def _find_temporally_related_events(self, event: Dict[str, Any]) -> List[str]:
        """Find events that are temporally related."""
        date = event.get('date', '')
        if not date or len(date) < 7:
            return []
        
        # Find events in same month
        month_key = date[:7]
        related = self.date_index.get(month_key, [])
        
        # Filter out the event itself
        event_id = event.get('id')
        return [r for r in related if r != event_id]
    
    def _events_temporally_related(self, event1: Dict, event2: Dict) -> bool:
        """Check if two events are temporally related."""
        date1 = event1.get('date', '')
        date2 = event2.get('date', '')
        
        if not date1 or not date2:
            return False
        
        # Check if dates are within 30 days
        # This is simplified - would need proper date parsing
        if date1[:7] == date2[:7]:  # Same month
            return True
        
        return False
    
    def _check_temporal_conflict(self, event1: Dict, event2: Dict) -> Optional[Dict]:
        """Check for temporal conflicts between events."""
        # Look for logical conflicts
        # e.g., same person in two places at same time
        
        actors1 = set(event1.get('actors', []))
        actors2 = set(event2.get('actors', []))
        
        common_actors = actors1.intersection(actors2)
        
        if common_actors and event1.get('date') == event2.get('date'):
            # Check if events are mutually exclusive
            location1 = event1.get('location', '')
            location2 = event2.get('location', '')
            
            if location1 and location2 and location1 != location2:
                return {
                    'type': 'location_conflict',
                    'actor': list(common_actors)[0],
                    'date': event1.get('date'),
                    'locations': [location1, location2]
                }
        
        return None
    
    def _validate_date_format(self, date: str) -> bool:
        """Validate date format."""
        # Check for YYYY-MM-DD format
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        return bool(re.match(date_pattern, date))
    
    def _get_event_by_id(self, event_id: str) -> Optional[Dict]:
        """Get event by ID from corpus."""
        for event in self.events_corpus:
            if event.get('id') == event_id:
                return event
        return None
    
    def _generate_recommendations(self, result: ValidationResult) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Source recommendations
        if result.source_validation.get('status') == 'insufficient_sources':
            recommendations.append("Add more sources to improve verification confidence")
        elif result.source_validation.get('avg_quality', 0) < 0.7:
            recommendations.append("Include more authoritative sources")
        
        # Temporal recommendations
        if not result.temporal_validation.get('date_valid', True):
            recommendations.append("Correct date format to YYYY-MM-DD")
        if result.temporal_validation.get('conflicts'):
            recommendations.append("Review and resolve temporal conflicts with related events")
        
        # Entity recommendations
        if result.entity_validation.get('ambiguous', 0) > 0:
            recommendations.append("Disambiguate entity names for clarity")
        
        # Fact recommendations
        if result.fact_validation.get('disputed', 0) > 0:
            recommendations.append("Review and address disputed claims")
        if result.fact_validation.get('unverified', 0) > result.fact_validation.get('validated', 0):
            recommendations.append("Seek additional verification for factual claims")
        
        # Overall confidence recommendations
        if result.confidence_level == 'low':
            recommendations.append("This event requires additional verification before use")
        elif result.confidence_level == 'medium':
            recommendations.append("Consider corroborating with additional sources")
        
        return recommendations
    
    def validate_batch(self, events: List[Dict[str, Any]]) -> List[ValidationResult]:
        """Validate a batch of events."""
        results = []
        
        for event in events:
            result = self.validate_event(event)
            results.append(result)
            
            # Update statistics
            self.validation_stats['total_validations'] += 1
            if result.confidence_level == 'high':
                self.validation_stats['high_confidence'] += 1
            elif result.confidence_level == 'medium':
                self.validation_stats['medium_confidence'] += 1
            else:
                self.validation_stats['low_confidence'] += 1
        
        return results
    
    def detect_conflicts(self, events: List[Dict[str, Any]]) -> List[Dict]:
        """Detect conflicts across multiple events."""
        conflicts = []
        
        # Check each pair of events
        for i, event1 in enumerate(events):
            for event2 in events[i+1:]:
                # Check temporal conflicts
                temporal_conflict = self._check_temporal_conflict(event1, event2)
                if temporal_conflict:
                    conflicts.append({
                        'type': 'temporal',
                        'events': [event1.get('id'), event2.get('id')],
                        'details': temporal_conflict
                    })
                
                # Check factual conflicts
                factual_conflict = self._check_factual_conflict(event1, event2)
                if factual_conflict:
                    conflicts.append({
                        'type': 'factual',
                        'events': [event1.get('id'), event2.get('id')],
                        'details': factual_conflict
                    })
        
        return conflicts
    
    def _check_factual_conflict(self, event1: Dict, event2: Dict) -> Optional[Dict]:
        """Check for factual conflicts between events."""
        # Simplified factual conflict detection
        # In a real system, this would use semantic analysis
        
        # Check for contradicting importance scores for same event
        if (event1.get('title') == event2.get('title') and 
            abs(event1.get('importance', 0) - event2.get('importance', 0)) > 3):
            return {
                'type': 'importance_mismatch',
                'values': [event1.get('importance'), event2.get('importance')]
            }
        
        return None
    
    def resolve_conflicts(self, conflicts: List[Dict]) -> List[Dict]:
        """Resolve detected conflicts using configured strategy."""
        resolutions = []
        
        for conflict in conflicts:
            if self.config.conflict_resolution_strategy == 'weighted_consensus':
                resolution = self._resolve_by_weighted_consensus(conflict)
            elif self.config.conflict_resolution_strategy == 'majority':
                resolution = self._resolve_by_majority(conflict)
            else:  # latest
                resolution = self._resolve_by_latest(conflict)
            
            resolutions.append(resolution)
        
        return resolutions
    
    def _resolve_by_weighted_consensus(self, conflict: Dict) -> Dict:
        """Resolve conflict using weighted consensus."""
        # Weight by source quality and temporal proximity
        # This is a simplified implementation
        return {
            'conflict': conflict,
            'resolution': 'weighted_consensus',
            'action': 'Use highest quality source information'
        }
    
    def _resolve_by_majority(self, conflict: Dict) -> Dict:
        """Resolve conflict by majority agreement."""
        return {
            'conflict': conflict,
            'resolution': 'majority',
            'action': 'Use information agreed upon by majority of sources'
        }
    
    def _resolve_by_latest(self, conflict: Dict) -> Dict:
        """Resolve conflict by using latest information."""
        return {
            'conflict': conflict,
            'resolution': 'latest',
            'action': 'Use most recent information'
        }
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        total = self.validation_stats['total_validations']
        if total == 0:
            return {}
        
        return {
            'total_validations': total,
            'high_confidence_rate': self.validation_stats['high_confidence'] / total,
            'medium_confidence_rate': self.validation_stats['medium_confidence'] / total,
            'low_confidence_rate': self.validation_stats['low_confidence'] / total,
            'validation_types': {
                'source': self.validation_stats['source_validations'],
                'temporal': self.validation_stats['temporal_validations'],
                'entity': self.validation_stats['entity_validations'],
                'fact': self.validation_stats['fact_validations']
            }
        }