"""
Multi-Stage Reranking System

Orchestrates multiple reranking stages to optimize retrieval results
for research-grade quality and relevance.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from collections import defaultdict

from ..retrieval.hybrid import RetrievalResult
from ..query.processor import ProcessedQuery
from .stages import (
    SemanticReranker,
    RelevanceReranker, 
    DiversityReranker,
    QualityReranker
)

logger = logging.getLogger(__name__)


@dataclass
class RerankingConfig:
    """Configuration for multi-stage reranking."""
    # Reranking stages to apply (in order)
    enabled_stages: List[str] = field(default_factory=lambda: [
        'semantic', 'relevance', 'quality', 'diversity'
    ])
    
    # Stage-specific configurations
    semantic_weight: float = 0.3
    relevance_weight: float = 0.4
    quality_weight: float = 0.2
    diversity_weight: float = 0.1
    
    # Filtering thresholds
    min_semantic_threshold: float = 0.2
    min_relevance_threshold: float = 0.15
    quality_threshold: float = 0.25
    
    # Diversity settings
    diversity_field: str = 'actors'  # Field to use for diversity
    max_similar_results: int = 3     # Max results from same group
    
    # Research optimizations
    boost_high_importance: bool = True
    boost_recent_events: bool = True
    boost_verified_sources: bool = True
    
    # Performance settings
    max_candidates_per_stage: int = 50
    final_result_limit: int = 20


class MultiStageReranker:
    """
    Multi-stage reranking system for research-grade result optimization.
    
    Applies sequential reranking stages:
    1. Semantic reranking - deeper semantic analysis
    2. Relevance reranking - query-specific relevance scoring
    3. Quality reranking - source quality and importance boosting
    4. Diversity reranking - result diversity optimization
    """
    
    def __init__(self, config: Optional[RerankingConfig] = None):
        """
        Initialize multi-stage reranker.
        
        Args:
            config: Reranking configuration
        """
        self.config = config or RerankingConfig()
        
        # Initialize reranking stages
        self.stages = {}
        if 'semantic' in self.config.enabled_stages:
            self.stages['semantic'] = SemanticReranker()
        if 'relevance' in self.config.enabled_stages:
            self.stages['relevance'] = RelevanceReranker()
        if 'quality' in self.config.enabled_stages:
            self.stages['quality'] = QualityReranker()
        if 'diversity' in self.config.enabled_stages:
            self.stages['diversity'] = DiversityReranker(
                diversity_field=self.config.diversity_field,
                max_similar=self.config.max_similar_results
            )
        
        # Performance tracking
        self.reranking_stats = defaultdict(int)
        
        logger.info(f"Initialized MultiStageReranker with stages: {list(self.stages.keys())}")
    
    def rerank(self, 
               results: List[RetrievalResult],
               processed_query: ProcessedQuery) -> List[RetrievalResult]:
        """
        Apply multi-stage reranking to retrieval results.
        
        Args:
            results: Initial retrieval results
            processed_query: Processed query with expansion and filters
            
        Returns:
            Reranked and optimized results
        """
        start_time = datetime.now()
        
        if not results:
            return results
        
        # Track original order for comparison
        original_order = [r.event_id for r in results]
        
        try:
            # Apply each reranking stage in sequence
            current_results = list(results)
            stage_history = {}
            
            for stage_name in self.config.enabled_stages:
                if stage_name in self.stages:
                    logger.debug(f"Applying {stage_name} reranking stage")
                    
                    # Limit candidates per stage for performance
                    if len(current_results) > self.config.max_candidates_per_stage:
                        current_results = current_results[:self.config.max_candidates_per_stage]
                    
                    # Apply stage
                    stage_start = datetime.now()
                    current_results = self._apply_reranking_stage(
                        current_results, processed_query, stage_name
                    )
                    stage_time = (datetime.now() - stage_start).total_seconds()
                    
                    # Track stage performance
                    self.reranking_stats[f'{stage_name}_applications'] += 1
                    self.reranking_stats[f'{stage_name}_avg_time'] = (
                        (self.reranking_stats[f'{stage_name}_avg_time'] * 
                         (self.reranking_stats[f'{stage_name}_applications'] - 1) + 
                         stage_time) / self.reranking_stats[f'{stage_name}_applications']
                    )
                    
                    # Store stage results for analysis
                    stage_history[stage_name] = [r.event_id for r in current_results[:10]]
                    
                    logger.debug(f"{stage_name} stage completed in {stage_time:.3f}s, "
                               f"{len(current_results)} results remaining")
            
            # Apply final research optimizations
            final_results = self._apply_research_optimizations(current_results, processed_query)
            
            # Limit to final result count
            final_results = final_results[:self.config.final_result_limit]
            
            # Update performance stats
            total_time = (datetime.now() - start_time).total_seconds()
            self.reranking_stats['total_reranks'] += 1
            self.reranking_stats['avg_rerank_time'] = (
                (self.reranking_stats['avg_rerank_time'] * 
                 (self.reranking_stats['total_reranks'] - 1) + 
                 total_time) / self.reranking_stats['total_reranks']
            )
            
            # Log reranking summary
            rerank_changes = sum(1 for i, result in enumerate(final_results[:10]) 
                               if i >= len(original_order) or result.event_id != original_order[i])
            
            logger.info(f"Reranking completed: {len(final_results)} final results, "
                       f"{rerank_changes}/10 top results changed, {total_time:.3f}s")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            self.reranking_stats['reranking_errors'] += 1
            return results  # Return original results on error
    
    def _apply_reranking_stage(self,
                              results: List[RetrievalResult],
                              processed_query: ProcessedQuery,
                              stage_name: str) -> List[RetrievalResult]:
        """Apply a single reranking stage."""
        
        stage = self.stages[stage_name]
        
        try:
            # Apply the reranking stage
            reranked_results = stage.rerank(results, processed_query, self.config)
            
            # Apply stage-specific filtering if configured
            if stage_name == 'semantic' and self.config.min_semantic_threshold > 0:
                reranked_results = [
                    r for r in reranked_results 
                    if r.semantic_score >= self.config.min_semantic_threshold
                ]
            elif stage_name == 'relevance' and self.config.min_relevance_threshold > 0:
                reranked_results = [
                    r for r in reranked_results
                    if r.fusion_score >= self.config.min_relevance_threshold
                ]
            elif stage_name == 'quality' and self.config.quality_threshold > 0:
                reranked_results = [
                    r for r in reranked_results
                    if r.fusion_score >= self.config.quality_threshold
                ]
            
            return reranked_results
            
        except Exception as e:
            logger.error(f"Stage {stage_name} failed: {e}")
            return results  # Return unchanged on error
    
    def _apply_research_optimizations(self, 
                                    results: List[RetrievalResult],
                                    processed_query: ProcessedQuery) -> List[RetrievalResult]:
        """Apply final research-specific optimizations."""
        
        if not results:
            return results
        
        optimized_results = list(results)
        
        # Research optimization 1: Importance boosting
        if self.config.boost_high_importance:
            for result in optimized_results:
                if result.importance.lower() in ['critical', 'major', 'high']:
                    boost_factor = 1.1 if 'critical' in result.importance.lower() else 1.05
                    result.fusion_score *= boost_factor
                    if 'importance_boost' not in result.retrieval_reasons:
                        result.retrieval_reasons.append('importance_boost')
        
        # Research optimization 2: Recent events boosting
        if self.config.boost_recent_events:
            current_year = datetime.now().year
            for result in optimized_results:
                # Simple year-based recency (would need proper date parsing)
                if str(current_year) in result.date or str(current_year - 1) in result.date:
                    result.fusion_score *= 1.05
                    if 'recency_boost' not in result.retrieval_reasons:
                        result.retrieval_reasons.append('recency_boost')
        
        # Research optimization 3: Multi-actor events boosting
        for result in optimized_results:
            if len(result.actors) > 2:  # Events with multiple actors often more significant
                result.fusion_score *= 1.03
                if 'multi_actor_boost' not in result.retrieval_reasons:
                    result.retrieval_reasons.append('multi_actor_boost')
        
        # Research optimization 4: Query intent alignment
        intent_boost = self._get_intent_alignment_boost(processed_query.intent)
        if intent_boost > 1.0:
            for result in optimized_results:
                if self._result_aligns_with_intent(result, processed_query.intent):
                    result.fusion_score *= intent_boost
                    if 'intent_alignment' not in result.retrieval_reasons:
                        result.retrieval_reasons.append('intent_alignment')
        
        # Re-sort after optimizations
        optimized_results.sort(key=lambda x: x.fusion_score, reverse=True)
        
        return optimized_results
    
    def _get_intent_alignment_boost(self, intent) -> float:
        """Get boost factor for intent alignment."""
        from ..query.intent import ResearchIntent
        
        intent_boosts = {
            ResearchIntent.COMPREHENSIVE_SEARCH: 1.05,
            ResearchIntent.TIMELINE_ANALYSIS: 1.08,
            ResearchIntent.ACTOR_NETWORK: 1.1,
            ResearchIntent.IMPORTANCE_FILTER: 1.12,
            ResearchIntent.PATTERN_DETECTION: 1.06,
            ResearchIntent.CAUSAL_ANALYSIS: 1.07
        }
        
        return intent_boosts.get(intent, 1.0)
    
    def _result_aligns_with_intent(self, result: RetrievalResult, intent) -> bool:
        """Check if result aligns with query intent."""
        from ..query.intent import ResearchIntent
        
        text = f"{result.title} {result.summary}".lower()
        
        if intent == ResearchIntent.TIMELINE_ANALYSIS:
            timeline_words = ['timeline', 'chronology', 'sequence', 'progression', 'development']
            return any(word in text for word in timeline_words)
        
        elif intent == ResearchIntent.ACTOR_NETWORK:
            network_words = ['connection', 'relationship', 'network', 'link', 'ties']
            return any(word in text for word in network_words) or len(result.actors) > 1
        
        elif intent == ResearchIntent.IMPORTANCE_FILTER:
            return result.importance.lower() in ['critical', 'major', 'high']
        
        elif intent == ResearchIntent.CAUSAL_ANALYSIS:
            causal_words = ['caused', 'led to', 'resulted', 'because', 'due to']
            return any(word in text for word in causal_words)
        
        return True  # Default to aligned
    
    def analyze_reranking_impact(self, 
                                original_results: List[RetrievalResult],
                                reranked_results: List[RetrievalResult]) -> Dict[str, Any]:
        """
        Analyze the impact of reranking on result ordering.
        
        Args:
            original_results: Results before reranking
            reranked_results: Results after reranking
            
        Returns:
            Dictionary of impact metrics
        """
        if not original_results or not reranked_results:
            return {}
        
        # Create mappings for analysis
        original_order = {r.event_id: i for i, r in enumerate(original_results)}
        reranked_order = {r.event_id: i for i, r in enumerate(reranked_results)}
        
        # Calculate metrics
        analysis = {
            'original_count': len(original_results),
            'reranked_count': len(reranked_results),
            'top_10_changes': 0,
            'top_5_changes': 0,
            'position_changes': [],
            'score_improvements': [],
            'new_top_results': []
        }
        
        # Analyze top-k changes
        top_10_original = set(r.event_id for r in original_results[:10])
        top_10_reranked = set(r.event_id for r in reranked_results[:10])
        analysis['top_10_changes'] = len(top_10_original.symmetric_difference(top_10_reranked))
        
        top_5_original = set(r.event_id for r in original_results[:5])
        top_5_reranked = set(r.event_id for r in reranked_results[:5])
        analysis['top_5_changes'] = len(top_5_original.symmetric_difference(top_5_reranked))
        
        # Analyze position changes
        for event_id in original_order:
            if event_id in reranked_order:
                original_pos = original_order[event_id]
                reranked_pos = reranked_order[event_id]
                position_change = original_pos - reranked_pos  # Positive = moved up
                analysis['position_changes'].append(position_change)
        
        # Find results that entered top 10
        new_top_10 = top_10_reranked - top_10_original
        analysis['new_top_results'] = list(new_top_10)
        
        # Summary statistics
        if analysis['position_changes']:
            analysis['avg_position_change'] = np.mean(analysis['position_changes'])
            analysis['max_position_improvement'] = max(analysis['position_changes'])
            analysis['position_change_std'] = np.std(analysis['position_changes'])
        
        return analysis
    
    def get_reranking_stats(self) -> Dict[str, Any]:
        """Get reranking performance statistics."""
        return dict(self.reranking_stats)
    
    def reset_stats(self):
        """Reset reranking statistics."""
        self.reranking_stats.clear()