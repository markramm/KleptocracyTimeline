"""
Confidence Scoring System

Multi-factor confidence scoring for research-grade reliability assessment.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceConfig:
    """Configuration for confidence scoring."""
    # Weight factors for different confidence components
    source_weight: float = 0.25
    validation_weight: float = 0.25
    consistency_weight: float = 0.20
    corroboration_weight: float = 0.20
    temporal_weight: float = 0.10
    
    # Thresholds
    high_confidence_threshold: float = 0.85
    medium_confidence_threshold: float = 0.65
    
    # Penalties and bonuses
    missing_source_penalty: float = 0.3
    disputed_claim_penalty: float = 0.4
    multiple_source_bonus: float = 0.15
    verified_source_bonus: float = 0.20


@dataclass
class ConfidenceScore:
    """Detailed confidence score with component breakdown."""
    overall_score: float
    confidence_level: str  # high, medium, low
    
    # Component scores (0-1)
    source_confidence: float = 0.0
    validation_confidence: float = 0.0
    consistency_confidence: float = 0.0
    corroboration_confidence: float = 0.0
    temporal_confidence: float = 0.0
    
    # Detailed factors
    factors: Dict[str, float] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    
    # Uncertainty quantification
    uncertainty_range: Tuple[float, float] = (0.0, 1.0)
    confidence_interval: float = 0.95


class ConfidenceScorer:
    """
    Multi-factor confidence scoring for information reliability.
    
    Assesses confidence based on:
    - Source quality and quantity
    - Validation results
    - Internal consistency
    - External corroboration
    - Temporal factors
    """
    
    def __init__(self, config: Optional[ConfidenceConfig] = None):
        """
        Initialize confidence scorer.
        
        Args:
            config: Confidence scoring configuration
        """
        self.config = config or ConfidenceConfig()
        self.scoring_stats = defaultdict(int)
        
        logger.info("Initialized ConfidenceScorer")
    
    def score_event(self, 
                   event: Dict[str, Any],
                   validation_result: Optional[Any] = None,
                   fact_check_results: Optional[List[Any]] = None,
                   related_events: Optional[List[Dict]] = None) -> ConfidenceScore:
        """
        Calculate comprehensive confidence score for an event.
        
        Args:
            event: Event to score
            validation_result: Cross-reference validation result
            fact_check_results: Fact-checking results
            related_events: Related events for corroboration
            
        Returns:
            ConfidenceScore with detailed breakdown
        """
        self.scoring_stats['total_scores'] += 1
        
        score = ConfidenceScore(overall_score=0.0, confidence_level='low')
        
        # Calculate component scores
        score.source_confidence = self._score_sources(event)
        score.validation_confidence = self._score_validation(validation_result)
        score.consistency_confidence = self._score_consistency(event, fact_check_results)
        score.corroboration_confidence = self._score_corroboration(event, related_events)
        score.temporal_confidence = self._score_temporal(event)
        
        # Calculate weighted overall score
        score.overall_score = (
            self.config.source_weight * score.source_confidence +
            self.config.validation_weight * score.validation_confidence +
            self.config.consistency_weight * score.consistency_confidence +
            self.config.corroboration_weight * score.corroboration_confidence +
            self.config.temporal_weight * score.temporal_confidence
        )
        
        # Apply penalties and bonuses
        score = self._apply_modifiers(score, event, validation_result, fact_check_results)
        
        # Determine confidence level
        if score.overall_score >= self.config.high_confidence_threshold:
            score.confidence_level = 'high'
            self.scoring_stats['high_confidence'] += 1
        elif score.overall_score >= self.config.medium_confidence_threshold:
            score.confidence_level = 'medium'
            self.scoring_stats['medium_confidence'] += 1
        else:
            score.confidence_level = 'low'
            self.scoring_stats['low_confidence'] += 1
        
        # Calculate uncertainty range
        score.uncertainty_range = self._calculate_uncertainty(score)
        
        # Identify strengths and issues
        self._identify_strengths_and_issues(score, event)
        
        return score
    
    def _score_sources(self, event: Dict[str, Any]) -> float:
        """Score confidence based on sources."""
        sources = event.get('sources', [])
        
        if not sources:
            return 0.0
        
        source_count = len(sources)
        
        # Base score from source count
        if source_count >= 3:
            base_score = 0.9
        elif source_count == 2:
            base_score = 0.7
        else:
            base_score = 0.5
        
        # Adjust for source quality
        quality_scores = []
        for source in sources:
            if isinstance(source, dict):
                if source.get('verified'):
                    quality_scores.append(1.0)
                elif source.get('url'):
                    # Check for reputable domains
                    url = source['url'].lower()
                    if any(domain in url for domain in ['.gov', '.edu', 'reuters', 'apnews']):
                        quality_scores.append(0.9)
                    else:
                        quality_scores.append(0.6)
            else:
                quality_scores.append(0.4)
        
        if quality_scores:
            avg_quality = np.mean(quality_scores)
            return base_score * 0.6 + avg_quality * 0.4
        
        return base_score
    
    def _score_validation(self, validation_result: Optional[Any]) -> float:
        """Score confidence based on validation results."""
        if not validation_result:
            return 0.5  # Neutral if no validation
        
        # Use validation score if available
        if hasattr(validation_result, 'validation_score'):
            return validation_result.validation_score
        
        # Check confidence level
        if hasattr(validation_result, 'confidence_level'):
            confidence_map = {
                'high': 0.9,
                'medium': 0.6,
                'low': 0.3
            }
            return confidence_map.get(validation_result.confidence_level, 0.5)
        
        return 0.5
    
    def _score_consistency(self, event: Dict[str, Any], 
                          fact_check_results: Optional[List[Any]]) -> float:
        """Score internal consistency."""
        consistency_score = 0.7  # Base score
        
        # Check for contradictions in fact checks
        if fact_check_results:
            disputed_count = sum(1 for r in fact_check_results 
                               if hasattr(r, 'verdict') and r.verdict == 'disputed')
            verified_count = sum(1 for r in fact_check_results
                               if hasattr(r, 'verdict') and r.verdict == 'verified')
            
            total_checks = len(fact_check_results)
            if total_checks > 0:
                dispute_ratio = disputed_count / total_checks
                verified_ratio = verified_count / total_checks
                
                consistency_score = 0.5 + (verified_ratio * 0.5) - (dispute_ratio * 0.5)
        
        # Check for internal consistency in event data
        if event.get('status') == 'confirmed':
            consistency_score = min(1.0, consistency_score + 0.1)
        elif event.get('status') == 'disputed':
            consistency_score = max(0.0, consistency_score - 0.2)
        
        return consistency_score
    
    def _score_corroboration(self, event: Dict[str, Any], 
                           related_events: Optional[List[Dict]]) -> float:
        """Score based on external corroboration."""
        if not related_events:
            return 0.5  # Neutral if no related events
        
        corroborating_count = 0
        conflicting_count = 0
        
        for related in related_events:
            # Simple corroboration check
            if self._events_corroborate(event, related):
                corroborating_count += 1
            elif self._events_conflict(event, related):
                conflicting_count += 1
        
        total_related = len(related_events)
        
        if total_related > 0:
            corroboration_ratio = corroborating_count / total_related
            conflict_ratio = conflicting_count / total_related
            
            score = 0.5 + (corroboration_ratio * 0.4) - (conflict_ratio * 0.3)
            return max(0.0, min(1.0, score))
        
        return 0.5
    
    def _events_corroborate(self, event1: Dict, event2: Dict) -> bool:
        """Check if two events corroborate each other."""
        # Simple check based on actors and dates
        actors1 = set(event1.get('actors', []))
        actors2 = set(event2.get('actors', []))
        
        if actors1.intersection(actors2):
            # Same actors involved
            date1 = event1.get('date', '')
            date2 = event2.get('date', '')
            
            # Check if dates are close
            if date1 and date2 and date1[:7] == date2[:7]:  # Same month
                return True
        
        return False
    
    def _events_conflict(self, event1: Dict, event2: Dict) -> bool:
        """Check if two events conflict."""
        # Check for explicit disputes
        if event1.get('status') == 'disputed' or event2.get('status') == 'disputed':
            # Check if they reference same subject
            actors1 = set(event1.get('actors', []))
            actors2 = set(event2.get('actors', []))
            
            if actors1.intersection(actors2):
                return True
        
        return False
    
    def _score_temporal(self, event: Dict[str, Any]) -> float:
        """Score based on temporal factors."""
        date = event.get('date', '')
        
        if not date:
            return 0.3  # Low confidence without date
        
        # Check date format validity
        import re
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date):
            score = 0.9  # Full date
        elif re.match(r'^\d{4}-\d{2}$', date):
            score = 0.7  # Year-month
        elif re.match(r'^\d{4}$', date):
            score = 0.5  # Year only
        else:
            score = 0.3  # Invalid format
        
        # Boost for recent events (more verifiable)
        from datetime import datetime
        current_year = datetime.now().year
        
        if len(date) >= 4:
            try:
                event_year = int(date[:4])
                years_old = current_year - event_year
                
                if years_old <= 1:
                    score = min(1.0, score + 0.1)
                elif years_old > 5:
                    score = max(0.0, score - 0.1)
            except ValueError:
                pass
        
        return score
    
    def _apply_modifiers(self, 
                        score: ConfidenceScore,
                        event: Dict,
                        validation_result: Optional[Any],
                        fact_check_results: Optional[List[Any]]) -> ConfidenceScore:
        """Apply penalties and bonuses to confidence score."""
        
        # Penalty for missing sources
        if not event.get('sources'):
            score.overall_score -= self.config.missing_source_penalty
            score.issues.append("No sources provided")
        
        # Penalty for disputed claims
        if fact_check_results:
            disputed_count = sum(1 for r in fact_check_results
                               if hasattr(r, 'verdict') and r.verdict == 'disputed')
            if disputed_count > 0:
                penalty = min(self.config.disputed_claim_penalty, disputed_count * 0.1)
                score.overall_score -= penalty
                score.issues.append(f"{disputed_count} disputed claims")
        
        # Bonus for multiple sources
        source_count = len(event.get('sources', []))
        if source_count >= 3:
            score.overall_score += self.config.multiple_source_bonus
            score.strengths.append(f"{source_count} sources provided")
        
        # Bonus for verified sources
        if event.get('sources'):
            verified_count = sum(1 for s in event['sources'] 
                                if isinstance(s, dict) and s.get('verified'))
            if verified_count > 0:
                score.overall_score += self.config.verified_source_bonus * (verified_count / source_count)
                score.strengths.append(f"{verified_count} verified sources")
        
        # Ensure score is in valid range
        score.overall_score = max(0.0, min(1.0, score.overall_score))
        
        return score
    
    def _calculate_uncertainty(self, score: ConfidenceScore) -> Tuple[float, float]:
        """Calculate uncertainty range for confidence score."""
        # Base uncertainty from component variance
        components = [
            score.source_confidence,
            score.validation_confidence,
            score.consistency_confidence,
            score.corroboration_confidence,
            score.temporal_confidence
        ]
        
        if components:
            std_dev = np.std(components)
            
            # Calculate confidence interval
            margin = std_dev * 1.96  # 95% confidence interval
            
            lower_bound = max(0.0, score.overall_score - margin)
            upper_bound = min(1.0, score.overall_score + margin)
            
            return (lower_bound, upper_bound)
        
        return (score.overall_score * 0.9, min(1.0, score.overall_score * 1.1))
    
    def _identify_strengths_and_issues(self, score: ConfidenceScore, event: Dict):
        """Identify strengths and issues in confidence assessment."""
        
        # Strengths
        if score.source_confidence >= 0.8:
            score.strengths.append("Strong source documentation")
        
        if score.validation_confidence >= 0.8:
            score.strengths.append("Well-validated information")
        
        if score.consistency_confidence >= 0.8:
            score.strengths.append("High internal consistency")
        
        if score.corroboration_confidence >= 0.8:
            score.strengths.append("Strong external corroboration")
        
        if event.get('importance', 0) >= 8:
            score.strengths.append("High importance event")
        
        # Issues
        if score.source_confidence < 0.5:
            score.issues.append("Weak source documentation")
        
        if score.validation_confidence < 0.5:
            score.issues.append("Limited validation")
        
        if score.consistency_confidence < 0.5:
            score.issues.append("Consistency concerns")
        
        if score.temporal_confidence < 0.5:
            score.issues.append("Temporal uncertainty")
        
        if not event.get('date'):
            score.issues.append("Missing date information")
    
    def score_batch(self, events: List[Dict[str, Any]], 
                   validation_results: Optional[Dict] = None) -> List[ConfidenceScore]:
        """Score confidence for multiple events."""
        scores = []
        
        for event in events:
            event_id = event.get('id')
            validation = validation_results.get(event_id) if validation_results else None
            
            score = self.score_event(event, validation_result=validation)
            scores.append(score)
        
        return scores
    
    def aggregate_confidence(self, scores: List[ConfidenceScore]) -> Dict[str, Any]:
        """Aggregate confidence scores for overall assessment."""
        if not scores:
            return {}
        
        overall_scores = [s.overall_score for s in scores]
        
        return {
            'mean_confidence': np.mean(overall_scores),
            'median_confidence': np.median(overall_scores),
            'std_confidence': np.std(overall_scores),
            'min_confidence': np.min(overall_scores),
            'max_confidence': np.max(overall_scores),
            'high_confidence_rate': sum(1 for s in scores if s.confidence_level == 'high') / len(scores),
            'medium_confidence_rate': sum(1 for s in scores if s.confidence_level == 'medium') / len(scores),
            'low_confidence_rate': sum(1 for s in scores if s.confidence_level == 'low') / len(scores),
            'common_issues': self._aggregate_issues(scores),
            'common_strengths': self._aggregate_strengths(scores)
        }
    
    def _aggregate_issues(self, scores: List[ConfidenceScore]) -> List[Tuple[str, int]]:
        """Aggregate common issues across scores."""
        issue_counter = defaultdict(int)
        
        for score in scores:
            for issue in score.issues:
                issue_counter[issue] += 1
        
        return sorted(issue_counter.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def _aggregate_strengths(self, scores: List[ConfidenceScore]) -> List[Tuple[str, int]]:
        """Aggregate common strengths across scores."""
        strength_counter = defaultdict(int)
        
        for score in scores:
            for strength in score.strengths:
                strength_counter[strength] += 1
        
        return sorted(strength_counter.items(), key=lambda x: x[1], reverse=True)[:5]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get confidence scoring statistics."""
        total = self.scoring_stats['total_scores']
        
        if total == 0:
            return {}
        
        return {
            'total_scores': total,
            'high_confidence_rate': self.scoring_stats['high_confidence'] / total,
            'medium_confidence_rate': self.scoring_stats['medium_confidence'] / total,
            'low_confidence_rate': self.scoring_stats['low_confidence'] / total
        }