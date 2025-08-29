"""
Individual Reranking Stages

Implements specific reranking algorithms for different aspects of result optimization.
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import numpy as np
from collections import defaultdict, Counter
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseReranker(ABC):
    """Base class for reranking stages."""
    
    @abstractmethod
    def rerank(self, results: List, processed_query, config) -> List:
        """Apply reranking to results."""
        pass


class SemanticReranker(BaseReranker):
    """
    Advanced semantic reranking using deeper text analysis.
    
    Performs more sophisticated semantic matching beyond initial embedding similarity:
    - Query term frequency analysis
    - Semantic field matching (actors, locations, topics)
    - Contextual relevance scoring
    """
    
    def __init__(self):
        """Initialize semantic reranker."""
        self.semantic_boosters = {
            # Political/governance terms
            'government': ['administration', 'federal', 'policy', 'regulatory'],
            'corruption': ['bribery', 'kickback', 'quid pro quo', 'graft'],
            'influence': ['lobbying', 'pressure', 'sway', 'control'],
            
            # Kleptocracy domain
            'kleptocracy': ['oligarchy', 'crony capitalism', 'state capture'],
            'capture': ['regulatory capture', 'agency capture', 'institutional'],
            
            # Democracy/elections
            'democracy': ['democratic', 'electoral', 'voting', 'election'],
            'authoritarian': ['autocratic', 'dictatorial', 'tyrannical']
        }
    
    def rerank(self, results: List, processed_query, config) -> List:
        """Apply semantic reranking."""
        if not results:
            return results
        
        # Enhanced semantic scoring
        for result in results:
            semantic_boost = self._calculate_semantic_boost(
                result, processed_query.processed_query, processed_query.expanded_queries
            )
            result.semantic_score *= semantic_boost
            
            # Update fusion score proportionally
            result.fusion_score = (
                config.semantic_weight * result.semantic_score +
                config.relevance_weight * result.metadata_score
            )
        
        # Sort by updated scores
        results.sort(key=lambda x: x.fusion_score, reverse=True)
        return results
    
    def _calculate_semantic_boost(self, result, original_query: str, expanded_queries: List[str]) -> float:
        """Calculate semantic boost factor for a result."""
        boost = 1.0
        
        # Combine all text for analysis
        result_text = f"{result.title} {result.summary}".lower()
        query_lower = original_query.lower()
        
        # 1. Direct term overlap boost
        query_terms = set(re.findall(r'\\b\\w{3,}\\b', query_lower))
        result_terms = set(re.findall(r'\\b\\w{3,}\\b', result_text))
        
        overlap = len(query_terms.intersection(result_terms))
        if overlap > 0:
            overlap_boost = 1.0 + (0.05 * overlap)
            boost *= overlap_boost
        
        # 2. Semantic field boosting
        for base_term, related_terms in self.semantic_boosters.items():
            if base_term in query_lower:
                for related_term in related_terms:
                    if related_term in result_text:
                        boost *= 1.08
                        break
        
        # 3. Actor name matching boost
        if result.actors:
            for actor in result.actors:
                if isinstance(actor, str) and actor.lower() in query_lower:
                    boost *= 1.15
                    break
                # Check partial name matching
                actor_words = actor.lower().split() if isinstance(actor, str) else []
                if any(word in query_lower for word in actor_words if len(word) > 2):
                    boost *= 1.1
                    break
        
        # 4. Tag relevance boost
        if result.tags:
            for tag in result.tags:
                if isinstance(tag, str) and tag.lower() in query_lower:
                    boost *= 1.06
                    break
        
        # 5. Expanded query matching (with decay)
        if expanded_queries:
            for i, expanded_query in enumerate(expanded_queries[:5]):
                expanded_terms = set(re.findall(r'\\b\\w{3,}\\b', expanded_query.lower()))
                expanded_overlap = len(expanded_terms.intersection(result_terms))
                if expanded_overlap > 0:
                    expansion_boost = 1.0 + (0.03 * expanded_overlap * (0.9 ** i))
                    boost *= expansion_boost
                    break
        
        # Cap maximum boost
        return min(boost, 1.4)


class RelevanceReranker(BaseReranker):
    """
    Query-specific relevance reranking.
    
    Optimizes results for query-specific relevance factors:
    - Intent-based relevance scoring  
    - Contextual importance
    - Query complexity matching
    """
    
    def rerank(self, results: List, processed_query, config) -> List:
        """Apply relevance reranking."""
        if not results:
            return results
        
        # Calculate relevance boosts
        for result in results:
            relevance_boost = self._calculate_relevance_boost(result, processed_query)
            
            # Apply boost to fusion score
            result.fusion_score *= relevance_boost
            
            # Track relevance boost in reasons
            if relevance_boost > 1.05:
                if 'relevance_boost' not in result.retrieval_reasons:
                    result.retrieval_reasons.append('relevance_boost')
        
        # Sort by updated fusion scores
        results.sort(key=lambda x: x.fusion_score, reverse=True)
        return results
    
    def _calculate_relevance_boost(self, result, processed_query) -> float:
        """Calculate relevance boost based on query characteristics."""
        boost = 1.0
        
        # Intent-based boosting
        intent_boost = self._get_intent_relevance_boost(result, processed_query.intent)
        boost *= intent_boost
        
        # Filter alignment boosting
        if processed_query.filters:
            filter_boost = self._get_filter_alignment_boost(result, processed_query.filters)
            boost *= filter_boost
        
        # Query complexity alignment
        complexity_boost = self._get_complexity_alignment_boost(result, processed_query)
        boost *= complexity_boost
        
        return min(boost, 1.3)
    
    def _get_intent_relevance_boost(self, result, intent) -> float:
        """Get relevance boost based on query intent."""
        from ..query.intent import ResearchIntent
        
        boost = 1.0
        text = f"{result.title} {result.summary}".lower()
        
        if intent == ResearchIntent.COMPREHENSIVE_SEARCH:
            # Boost high-importance and multi-actor events
            if result.importance.lower() in ['critical', 'major']:
                boost *= 1.1
            if len(result.actors) > 2:
                boost *= 1.05
        
        elif intent == ResearchIntent.TIMELINE_ANALYSIS:
            # Boost events with temporal language
            temporal_terms = ['timeline', 'sequence', 'progression', 'development', 'evolution']
            if any(term in text for term in temporal_terms):
                boost *= 1.15
        
        elif intent == ResearchIntent.ACTOR_NETWORK:
            # Boost multi-actor events and relationship language
            if len(result.actors) > 1:
                boost *= 1.2
            relationship_terms = ['connection', 'relationship', 'network', 'link']
            if any(term in text for term in relationship_terms):
                boost *= 1.1
        
        elif intent == ResearchIntent.IMPORTANCE_FILTER:
            # Strong boost for high-importance events
            if result.importance.lower() == 'critical':
                boost *= 1.25
            elif result.importance.lower() in ['major', 'high']:
                boost *= 1.15
        
        elif intent == ResearchIntent.PATTERN_DETECTION:
            # Boost events with pattern-related language
            pattern_terms = ['pattern', 'trend', 'systematic', 'recurring']
            if any(term in text for term in pattern_terms):
                boost *= 1.12
        
        return boost
    
    def _get_filter_alignment_boost(self, result, filters: Dict) -> float:
        """Get boost for filter alignment."""
        boost = 1.0
        
        # Date filter alignment
        if 'date_filters' in filters and filters['date_filters']:
            if self._result_matches_date_filters(result, filters['date_filters']):
                boost *= 1.08
        
        # Actor filter alignment  
        if 'actor_filters' in filters and filters['actor_filters']:
            if self._result_matches_actor_filters(result, filters['actor_filters']):
                boost *= 1.1
        
        # Importance filter alignment
        if 'importance_filters' in filters and filters['importance_filters']:
            if self._result_matches_importance_filters(result, filters['importance_filters']):
                boost *= 1.12
        
        return boost
    
    def _result_matches_date_filters(self, result, date_filters: Dict) -> bool:
        """Check if result matches date filters."""
        if 'years' in date_filters:
            return any(str(year) in result.date for year in date_filters['years'])
        return False
    
    def _result_matches_actor_filters(self, result, actor_filters: List) -> bool:
        """Check if result matches actor filters."""
        if not result.actors:
            return False
        
        result_actors_text = ' '.join(str(actor) for actor in result.actors).lower()
        return any(actor_filter.lower() in result_actors_text for actor_filter in actor_filters)
    
    def _result_matches_importance_filters(self, result, importance_filters: List) -> bool:
        """Check if result matches importance filters."""
        result_importance = result.importance.lower()
        return any(imp_filter.lower() in result_importance for imp_filter in importance_filters)
    
    def _get_complexity_alignment_boost(self, result, processed_query) -> float:
        """Boost based on query complexity alignment."""
        boost = 1.0
        
        # Complex queries should favor detailed, multi-faceted results
        query_complexity = len(processed_query.processed_query.split())
        
        if query_complexity > 8:  # Complex query
            # Boost results with more actors, tags, or longer summaries
            if len(result.actors) > 2:
                boost *= 1.05
            if len(result.tags) > 3:
                boost *= 1.03
            if len(result.summary) > 200:
                boost *= 1.04
        
        return boost


class QualityReranker(BaseReranker):
    """
    Quality-based reranking focusing on source quality and information completeness.
    
    Considers:
    - Event importance levels
    - Information completeness (actors, dates, details)
    - Source indicators and verification status
    """
    
    def rerank(self, results: List, processed_query, config) -> List:
        """Apply quality reranking."""
        if not results:
            return results
        
        # Calculate quality scores
        for result in results:
            quality_score = self._calculate_quality_score(result)
            
            # Apply quality boost
            quality_boost = 1.0 + (quality_score - 0.5) * 0.2  # Scale quality to boost
            result.fusion_score *= quality_boost
            
            # Track quality boost
            if quality_score > 0.7:
                if 'quality_boost' not in result.retrieval_reasons:
                    result.retrieval_reasons.append('quality_boost')
        
        # Sort by updated scores
        results.sort(key=lambda x: x.fusion_score, reverse=True)
        return results
    
    def _calculate_quality_score(self, result) -> float:
        """Calculate quality score for a result (0-1)."""
        quality_components = []
        
        # 1. Importance score (0-1)
        importance_scores = {
            'critical': 1.0,
            'major': 0.8,
            'high': 0.7,
            'moderate': 0.5,
            'low': 0.3
        }
        importance = result.importance.lower()
        importance_score = 0.5  # Default
        for level, score in importance_scores.items():
            if level in importance:
                importance_score = score
                break
        quality_components.append(importance_score)
        
        # 2. Completeness score (0-1)
        completeness_score = 0.0
        
        # Has title
        if result.title and len(result.title) > 5:
            completeness_score += 0.2
        
        # Has substantial summary  
        if result.summary and len(result.summary) > 50:
            completeness_score += 0.3
        
        # Has date
        if result.date and len(result.date) >= 4:
            completeness_score += 0.2
        
        # Has actors
        if result.actors and len(result.actors) > 0:
            completeness_score += 0.2
        
        # Has tags
        if result.tags and len(result.tags) > 0:
            completeness_score += 0.1
        
        quality_components.append(completeness_score)
        
        # 3. Content quality indicators (0-1)
        content_quality = self._assess_content_quality(result)
        quality_components.append(content_quality)
        
        # Average the components
        return np.mean(quality_components)
    
    def _assess_content_quality(self, result) -> float:
        """Assess content quality based on text characteristics."""
        score = 0.5  # Base score
        
        text = f"{result.title} {result.summary}"
        
        # Length indicators (not too short, not too long)
        text_length = len(text)
        if 100 <= text_length <= 1000:
            score += 0.1
        
        # Structural indicators
        if '.' in text and text.count('.') >= 2:  # Multiple sentences
            score += 0.1
        
        # Specific detail indicators
        if any(char.isdigit() for char in text):  # Contains numbers/dates
            score += 0.1
            
        # Professional language indicators
        professional_terms = [
            'according to', 'reported', 'announced', 'confirmed',
            'investigation', 'analysis', 'study', 'research'
        ]
        if any(term in text.lower() for term in professional_terms):
            score += 0.1
        
        # Avoid very short or empty content
        if text_length < 20:
            score = 0.2
        
        return min(1.0, score)


class DiversityReranker(BaseReranker):
    """
    Diversity-based reranking to avoid clustering of similar results.
    
    Ensures result diversity across:
    - Actors (avoid too many results about same person)
    - Time periods (spread across time)
    - Topics/tags (diverse topic coverage)
    """
    
    def __init__(self, diversity_field: str = 'actors', max_similar: int = 3):
        """
        Initialize diversity reranker.
        
        Args:
            diversity_field: Primary field for diversity calculation
            max_similar: Maximum similar results allowed
        """
        self.diversity_field = diversity_field
        self.max_similar = max_similar
    
    def rerank(self, results: List, processed_query, config) -> List:
        """Apply diversity reranking."""
        if len(results) <= 5:
            return results  # No diversity needed for small result sets
        
        # Group results by diversity criteria
        groups = self._group_results_by_diversity(results)
        
        # Apply diversity penalties
        diversified_results = self._apply_diversity_penalties(results, groups)
        
        # Re-sort after diversity adjustments
        diversified_results.sort(key=lambda x: x.fusion_score, reverse=True)
        
        return diversified_results
    
    def _group_results_by_diversity(self, results: List) -> Dict[str, List]:
        """Group results by diversity criteria."""
        groups = defaultdict(list)
        
        for i, result in enumerate(results):
            # Primary grouping by diversity field
            if self.diversity_field == 'actors':
                group_key = self._get_primary_actor(result)
            elif self.diversity_field == 'tags':
                group_key = self._get_primary_tag(result)
            elif self.diversity_field == 'date':
                group_key = self._get_date_group(result)
            else:
                group_key = 'default'
            
            groups[group_key].append(i)
        
        return dict(groups)
    
    def _get_primary_actor(self, result) -> str:
        """Get primary actor for grouping."""
        if result.actors and len(result.actors) > 0:
            primary_actor = result.actors[0]
            if isinstance(primary_actor, str):
                # Extract last name for grouping similar names
                words = primary_actor.split()
                return words[-1] if words else primary_actor
        return 'no_actor'
    
    def _get_primary_tag(self, result) -> str:
        """Get primary tag for grouping."""
        if result.tags and len(result.tags) > 0:
            return str(result.tags[0])
        return 'no_tag'
    
    def _get_date_group(self, result) -> str:
        """Get date group (year) for temporal diversity."""
        if result.date and len(result.date) >= 4:
            return result.date[:4]  # Year
        return 'no_date'
    
    def _apply_diversity_penalties(self, results: List, groups: Dict[str, List]) -> List:
        """Apply penalties to over-represented groups."""
        results_copy = list(results)
        
        for group_key, result_indices in groups.items():
            if len(result_indices) > self.max_similar:
                # Sort group by original fusion score
                group_results = [(i, results[i].fusion_score) for i in result_indices]
                group_results.sort(key=lambda x: x[1], reverse=True)
                
                # Apply increasing penalties to lower-ranked results in group
                for rank, (result_idx, _) in enumerate(group_results):
                    if rank >= self.max_similar:
                        # Progressive penalty: more penalty for later results
                        penalty = 0.9 ** (rank - self.max_similar + 1)
                        results_copy[result_idx].fusion_score *= penalty
                        
                        # Track diversity penalty
                        if 'diversity_penalty' not in results_copy[result_idx].retrieval_reasons:
                            results_copy[result_idx].retrieval_reasons.append('diversity_penalty')
        
        return results_copy