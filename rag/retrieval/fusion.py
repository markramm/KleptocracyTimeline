"""
Score Fusion Component

Advanced score fusion techniques for combining semantic and metadata retrieval results.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


class ScoreFusion:
    """
    Advanced score fusion for hybrid retrieval.
    
    Combines semantic similarity scores with metadata match scores using:
    - Weighted linear combination
    - Reciprocal Rank Fusion (RRF)
    - Concordance boosting
    - Research-specific optimizations
    """
    
    def __init__(self):
        """Initialize score fusion component."""
        self.fusion_stats = defaultdict(int)
    
    def fuse_scores(self, 
                   semantic_scores: Dict[str, float],
                   metadata_scores: Dict[str, float],
                   semantic_weight: float = 0.6,
                   metadata_weight: float = 0.4,
                   fusion_method: str = 'weighted_linear') -> Dict[str, float]:
        """
        Fuse semantic and metadata scores.
        
        Args:
            semantic_scores: Dictionary of {event_id: semantic_score}
            metadata_scores: Dictionary of {event_id: metadata_score}
            semantic_weight: Weight for semantic scores
            metadata_weight: Weight for metadata scores
            fusion_method: Fusion method ('weighted_linear', 'rrf', 'harmonic')
            
        Returns:
            Dictionary of {event_id: fused_score}
        """
        self.fusion_stats[fusion_method] += 1
        
        if fusion_method == 'weighted_linear':
            return self._weighted_linear_fusion(
                semantic_scores, metadata_scores, 
                semantic_weight, metadata_weight
            )
        elif fusion_method == 'rrf':
            return self._reciprocal_rank_fusion(semantic_scores, metadata_scores)
        elif fusion_method == 'harmonic':
            return self._harmonic_fusion(semantic_scores, metadata_scores)
        elif fusion_method == 'research_optimized':
            return self._research_optimized_fusion(
                semantic_scores, metadata_scores,
                semantic_weight, metadata_weight
            )
        else:
            logger.warning(f"Unknown fusion method: {fusion_method}, using weighted_linear")
            return self._weighted_linear_fusion(
                semantic_scores, metadata_scores,
                semantic_weight, metadata_weight
            )
    
    def _weighted_linear_fusion(self,
                               semantic_scores: Dict[str, float],
                               metadata_scores: Dict[str, float],
                               semantic_weight: float,
                               metadata_weight: float) -> Dict[str, float]:
        """
        Simple weighted linear combination of scores.
        
        Formula: fused_score = w1 * semantic + w2 * metadata
        """
        fused_scores = {}
        all_event_ids = set(semantic_scores.keys()) | set(metadata_scores.keys())
        
        for event_id in all_event_ids:
            semantic_score = semantic_scores.get(event_id, 0.0)
            metadata_score = metadata_scores.get(event_id, 0.0)
            
            fused_score = (
                semantic_weight * semantic_score +
                metadata_weight * metadata_score
            )
            
            # Apply concordance boost if found via both methods
            if event_id in semantic_scores and event_id in metadata_scores:
                concordance_boost = 1.1
                fused_score *= concordance_boost
            
            fused_scores[event_id] = fused_score
        
        return fused_scores
    
    def _reciprocal_rank_fusion(self,
                               semantic_scores: Dict[str, float],
                               metadata_scores: Dict[str, float],
                               k: int = 60) -> Dict[str, float]:
        """
        Reciprocal Rank Fusion (RRF) for combining ranked lists.
        
        RRF Score = sum(1 / (k + rank_i)) for all systems
        """
        # Convert scores to rankings
        semantic_rankings = self._scores_to_rankings(semantic_scores)
        metadata_rankings = self._scores_to_rankings(metadata_scores)
        
        fused_scores = {}
        all_event_ids = set(semantic_rankings.keys()) | set(metadata_rankings.keys())
        
        for event_id in all_event_ids:
            rrf_score = 0.0
            
            # Add semantic contribution
            if event_id in semantic_rankings:
                rank = semantic_rankings[event_id]
                rrf_score += 1.0 / (k + rank)
            
            # Add metadata contribution
            if event_id in metadata_rankings:
                rank = metadata_rankings[event_id]
                rrf_score += 1.0 / (k + rank)
            
            fused_scores[event_id] = rrf_score
        
        return fused_scores
    
    def _harmonic_fusion(self,
                        semantic_scores: Dict[str, float],
                        metadata_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Harmonic mean fusion - good for requiring both scores to be high.
        
        Formula: 2 * (s1 * s2) / (s1 + s2)
        """
        fused_scores = {}
        all_event_ids = set(semantic_scores.keys()) | set(metadata_scores.keys())
        
        for event_id in all_event_ids:
            semantic_score = semantic_scores.get(event_id, 0.0)
            metadata_score = metadata_scores.get(event_id, 0.0)
            
            if semantic_score > 0 and metadata_score > 0:
                # True harmonic mean
                fused_score = (2 * semantic_score * metadata_score) / (semantic_score + metadata_score)
            else:
                # Fallback to simple average for single scores
                fused_score = (semantic_score + metadata_score) / 2.0
            
            fused_scores[event_id] = fused_score
        
        return fused_scores
    
    def _research_optimized_fusion(self,
                                  semantic_scores: Dict[str, float],
                                  metadata_scores: Dict[str, float],
                                  semantic_weight: float,
                                  metadata_weight: float) -> Dict[str, float]:
        """
        Research-optimized fusion with recall prioritization and quality thresholds.
        """
        fused_scores = {}
        all_event_ids = set(semantic_scores.keys()) | set(metadata_scores.keys())
        
        # Normalize scores to [0,1] range
        normalized_semantic = self._normalize_scores(semantic_scores)
        normalized_metadata = self._normalize_scores(metadata_scores)
        
        for event_id in all_event_ids:
            semantic_score = normalized_semantic.get(event_id, 0.0)
            metadata_score = normalized_metadata.get(event_id, 0.0)
            
            # Base weighted combination
            base_score = (
                semantic_weight * semantic_score +
                metadata_weight * metadata_score
            )
            
            # Research optimizations
            optimized_score = base_score
            
            # 1. Concordance boost - strong boost for both methods agreeing
            if event_id in semantic_scores and event_id in metadata_scores:
                concordance_boost = 1.15 + 0.1 * min(semantic_score, metadata_score)
                optimized_score *= concordance_boost
            
            # 2. High precision boost - boost very high single scores
            max_single_score = max(semantic_score, metadata_score)
            if max_single_score > 0.8:
                precision_boost = 1.0 + 0.2 * (max_single_score - 0.8)
                optimized_score *= precision_boost
            
            # 3. Research recall boost - small boost for any reasonable match
            if semantic_score > 0.3 or metadata_score > 0.3:
                recall_boost = 1.05
                optimized_score *= recall_boost
            
            # 4. Quality threshold - minimum score for inclusion
            min_quality_threshold = 0.15
            if optimized_score < min_quality_threshold:
                optimized_score = 0.0
            
            fused_scores[event_id] = optimized_score
        
        return fused_scores
    
    def _scores_to_rankings(self, scores: Dict[str, float]) -> Dict[str, int]:
        """Convert scores to rankings (1-based)."""
        if not scores:
            return {}
        
        # Sort by score descending
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Create rankings
        rankings = {}
        for rank, (event_id, score) in enumerate(sorted_items, 1):
            rankings[event_id] = rank
        
        return rankings
    
    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Normalize scores to [0,1] range using min-max normalization."""
        if not scores:
            return {}
        
        values = list(scores.values())
        if not values:
            return {}
        
        min_val = min(values)
        max_val = max(values)
        
        if max_val == min_val:
            # All scores are the same
            return {k: 1.0 for k in scores.keys()}
        
        normalized = {}
        for event_id, score in scores.items():
            normalized[event_id] = (score - min_val) / (max_val - min_val)
        
        return normalized
    
    def fuse_ranked_lists(self,
                         semantic_results: List[Tuple[str, float]],
                         metadata_results: List[Tuple[str, float]],
                         method: str = 'rrf') -> List[Tuple[str, float]]:
        """
        Fuse two ranked lists of (event_id, score) tuples.
        
        Args:
            semantic_results: List of (event_id, semantic_score)
            metadata_results: List of (event_id, metadata_score)
            method: Fusion method
            
        Returns:
            Fused and re-ranked list of (event_id, fused_score)
        """
        # Convert to score dictionaries
        semantic_scores = dict(semantic_results)
        metadata_scores = dict(metadata_results)
        
        # Fuse scores
        if method == 'rrf':
            fused_scores = self._reciprocal_rank_fusion(semantic_scores, metadata_scores)
        else:
            fused_scores = self._weighted_linear_fusion(
                semantic_scores, metadata_scores, 0.6, 0.4
            )
        
        # Convert back to ranked list
        fused_list = [(event_id, score) for event_id, score in fused_scores.items()]
        fused_list.sort(key=lambda x: x[1], reverse=True)
        
        return fused_list
    
    def calculate_diversity_penalty(self,
                                   results: List[Dict],
                                   diversity_field: str = 'actors',
                                   penalty_strength: float = 0.1) -> List[Dict]:
        """
        Apply diversity penalty to reduce clustering of similar results.
        
        Args:
            results: List of result dictionaries
            diversity_field: Field to use for diversity calculation
            penalty_strength: Strength of diversity penalty
            
        Returns:
            Results with diversity penalties applied to fusion scores
        """
        if len(results) <= 3:
            return results  # No penalty for small result sets
        
        # Group results by diversity field
        field_groups = defaultdict(list)
        
        for i, result in enumerate(results):
            field_value = result.get(diversity_field)
            if field_value:
                if isinstance(field_value, list) and field_value:
                    field_value = field_value[0]  # Use first value
                field_groups[str(field_value)].append(i)
        
        # Apply penalties to over-represented groups
        for group_indices in field_groups.values():
            if len(group_indices) > 2:  # Penalize groups with >2 results
                for i, result_idx in enumerate(group_indices):
                    if i >= 2:  # Start penalty from 3rd result
                        penalty = 1.0 - (penalty_strength * (i - 1))
                        results[result_idx]['fusion_score'] *= penalty
        
        return results
    
    def get_fusion_stats(self) -> Dict[str, Any]:
        """Get fusion statistics."""
        return dict(self.fusion_stats)