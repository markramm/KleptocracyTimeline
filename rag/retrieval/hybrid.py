"""
Hybrid Semantic + Metadata Retrieval System

Combines semantic similarity with metadata filtering and advanced query processing
for research-grade retrieval with optimized recall and precision.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from collections import defaultdict, Counter

from ..query.processor import ResearchQueryProcessor, ProcessedQuery
from .semantic import SemanticRetriever
from .metadata import MetadataRetriever
from .fusion import ScoreFusion

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Single retrieval result with enhanced metadata."""
    event_id: str
    title: str
    summary: str
    date: str
    actors: List[str]
    tags: List[str]
    importance: str
    semantic_score: float
    metadata_score: float
    fusion_score: float
    retrieval_reasons: List[str]  # Why this was retrieved
    query_match_type: str  # original, expanded, filtered
    
    def __post_init__(self):
        """Ensure actors and tags are lists."""
        if isinstance(self.actors, str):
            self.actors = [self.actors] if self.actors else []
        if isinstance(self.tags, str):
            self.tags = [self.tags] if self.tags else []


@dataclass 
class RetrievalConfig:
    """Configuration for hybrid retrieval."""
    # Retrieval limits
    max_semantic_results: int = 50
    max_metadata_results: int = 30
    max_final_results: int = 20
    
    # Score weights for fusion
    semantic_weight: float = 0.6
    metadata_weight: float = 0.4
    
    # Query expansion
    use_expansion: bool = True
    max_expansions: int = 8
    expansion_boost: float = 0.8  # Boost for original query vs expansions
    
    # Filtering
    apply_smart_filtering: bool = True
    filter_strictness: float = 0.7  # How strict to be with filters
    
    # Quality thresholds
    min_semantic_score: float = 0.3
    min_metadata_score: float = 0.1
    min_fusion_score: float = 0.25
    
    # Research optimizations
    prioritize_recall: bool = True  # Research setting
    diversity_boost: bool = True    # Boost diverse results
    temporal_boost: bool = True     # Boost temporally relevant


class HybridRetriever:
    """
    Research-grade hybrid retrieval system combining semantic and metadata search.
    
    Optimized for kleptocracy/democracy research with:
    - Advanced query processing and expansion
    - Semantic similarity with domain-specific embeddings
    - Smart metadata filtering and boosting
    - Multi-stage score fusion
    - Research-focused recall optimization
    """
    
    def __init__(self, 
                 collection,
                 query_processor: Optional[ResearchQueryProcessor] = None,
                 config: Optional[RetrievalConfig] = None):
        """
        Initialize hybrid retriever.
        
        Args:
            collection: ChromaDB collection
            query_processor: Research query processor
            config: Retrieval configuration
        """
        self.collection = collection
        self.query_processor = query_processor or ResearchQueryProcessor()
        self.config = config or RetrievalConfig()
        
        # Initialize component retrievers
        self.semantic_retriever = SemanticRetriever(collection)
        self.metadata_retriever = MetadataRetriever(collection)
        self.score_fusion = ScoreFusion()
        
        # Performance tracking
        self.retrieval_stats = defaultdict(int)
        
        logger.info(f"Initialized HybridRetriever with config: {self.config}")
    
    def retrieve(self, raw_query: str) -> List[RetrievalResult]:
        """
        Retrieve relevant events using hybrid approach.
        
        Args:
            raw_query: Natural language query
            
        Returns:
            List of RetrievalResult objects ranked by relevance
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Process query with advanced pipeline
            processed_query = self.query_processor.process(raw_query)
            logger.debug(f"Processed query: {processed_query.intent} with {len(processed_query.expanded_queries)} expansions")
            
            # Step 2: Multi-query semantic retrieval
            semantic_results = self._retrieve_semantic_multi_query(processed_query)
            logger.debug(f"Semantic retrieval: {len(semantic_results)} results")
            
            # Step 3: Metadata-based retrieval
            metadata_results = self._retrieve_metadata_filtered(processed_query)
            logger.debug(f"Metadata retrieval: {len(metadata_results)} results")
            
            # Step 4: Fuse and rank results
            fused_results = self._fuse_and_rank(semantic_results, metadata_results, processed_query)
            logger.debug(f"Fused results: {len(fused_results)} final results")
            
            # Step 5: Apply research-specific optimizations
            final_results = self._apply_research_optimizations(fused_results, processed_query)
            
            # Update stats
            retrieval_time = (datetime.now() - start_time).total_seconds()
            self.retrieval_stats['total_retrievals'] += 1
            self.retrieval_stats['avg_retrieval_time'] = (
                (self.retrieval_stats['avg_retrieval_time'] * (self.retrieval_stats['total_retrievals'] - 1) + 
                 retrieval_time) / self.retrieval_stats['total_retrievals']
            )
            
            logger.info(f"Retrieved {len(final_results)} results in {retrieval_time:.3f}s")
            return final_results
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            self.retrieval_stats['retrieval_errors'] += 1
            return []
    
    def _retrieve_semantic_multi_query(self, processed_query: ProcessedQuery) -> Dict[str, Dict]:
        """Retrieve using semantic similarity across multiple query variants."""
        all_results = {}
        
        # Original query with highest boost
        original_results = self.semantic_retriever.retrieve(
            processed_query.processed_query,
            n_results=self.config.max_semantic_results
        )
        
        for result in original_results:
            event_id = result['id']
            if event_id not in all_results:
                result['semantic_score'] *= self.config.expansion_boost
                result['query_match_type'] = 'original'
                result['retrieval_reasons'] = ['semantic_match_original']
                all_results[event_id] = result
        
        # Expanded queries with decay
        if self.config.use_expansion and processed_query.expanded_queries:
            for i, expanded_query in enumerate(processed_query.expanded_queries[:self.config.max_expansions]):
                expansion_results = self.semantic_retriever.retrieve(
                    expanded_query,
                    n_results=max(10, self.config.max_semantic_results // 4)
                )
                
                # Apply expansion decay
                expansion_boost = self.config.expansion_boost * (0.9 ** i)
                
                for result in expansion_results:
                    event_id = result['id']
                    result['semantic_score'] *= expansion_boost
                    
                    if event_id not in all_results:
                        result['query_match_type'] = 'expanded'
                        result['retrieval_reasons'] = [f'semantic_match_expansion_{i}']
                        all_results[event_id] = result
                    else:
                        # Boost existing results found via expansion
                        all_results[event_id]['semantic_score'] = max(
                            all_results[event_id]['semantic_score'],
                            result['semantic_score']
                        )
                        all_results[event_id]['retrieval_reasons'].append(f'semantic_match_expansion_{i}')
        
        return all_results
    
    def _retrieve_metadata_filtered(self, processed_query: ProcessedQuery) -> Dict[str, Dict]:
        """Retrieve using smart metadata filtering."""
        if not self.config.apply_smart_filtering:
            return {}
        
        # Use extracted filters from processed query
        metadata_results = self.metadata_retriever.retrieve_with_filters(
            processed_query.filters,
            n_results=self.config.max_metadata_results
        )
        
        # Enhance with retrieval reasons
        enhanced_results = {}
        for result in metadata_results:
            event_id = result['id']
            result['query_match_type'] = 'filtered'
            result['retrieval_reasons'] = self._determine_filter_reasons(result, processed_query.filters)
            enhanced_results[event_id] = result
        
        return enhanced_results
    
    def _determine_filter_reasons(self, result: Dict, filters: Dict) -> List[str]:
        """Determine why this result matched the filters."""
        reasons = []
        
        # Check date filters
        if filters.get('date_filters'):
            reasons.append('date_filter_match')
        
        # Check actor filters  
        if filters.get('actor_filters'):
            result_actors = result.get('metadata', {}).get('actors', [])
            if isinstance(result_actors, str):
                result_actors = [result_actors]
            
            for actor_filter in filters['actor_filters']:
                if any(actor_filter.lower() in str(actor).lower() for actor in result_actors):
                    reasons.append(f'actor_filter_match_{actor_filter}')
        
        # Check importance filters
        if filters.get('importance_filters'):
            result_importance = result.get('metadata', {}).get('importance', '')
            for imp_filter in filters['importance_filters']:
                if imp_filter.lower() in result_importance.lower():
                    reasons.append(f'importance_filter_match_{imp_filter}')
        
        # Check tag filters
        if filters.get('tag_filters'):
            result_tags = result.get('metadata', {}).get('tags', [])
            if isinstance(result_tags, str):
                result_tags = [result_tags]
            
            for tag_filter in filters['tag_filters']:
                if any(tag_filter.lower() in str(tag).lower() for tag in result_tags):
                    reasons.append(f'tag_filter_match_{tag_filter}')
        
        return reasons or ['metadata_match']
    
    def _fuse_and_rank(self, 
                      semantic_results: Dict[str, Dict],
                      metadata_results: Dict[str, Dict], 
                      processed_query: ProcessedQuery) -> List[RetrievalResult]:
        """Fuse semantic and metadata results with advanced ranking."""
        
        # Collect all unique results
        all_event_ids = set(semantic_results.keys()) | set(metadata_results.keys())
        
        fused_results = []
        
        for event_id in all_event_ids:
            semantic_result = semantic_results.get(event_id)
            metadata_result = metadata_results.get(event_id)
            
            # Get base result data
            if semantic_result:
                base_result = semantic_result
                semantic_score = semantic_result.get('semantic_score', 0.0)
            else:
                base_result = metadata_result
                semantic_score = 0.0
            
            # Get metadata score
            if metadata_result:
                metadata_score = metadata_result.get('metadata_score', 0.8)  # High for filter matches
            else:
                metadata_score = 0.0
            
            # Apply minimum score thresholds
            if (semantic_score < self.config.min_semantic_score and 
                metadata_score < self.config.min_metadata_score):
                continue
            
            # Fuse scores using configuration weights
            fusion_score = (
                self.config.semantic_weight * semantic_score +
                self.config.metadata_weight * metadata_score
            )
            
            # Boost for results found via both methods
            if semantic_result and metadata_result:
                fusion_score *= 1.2  # Concordance boost
            
            # Apply minimum fusion score threshold
            if fusion_score < self.config.min_fusion_score:
                continue
            
            # Determine query match type and reasons
            if semantic_result and metadata_result:
                query_match_type = 'both'
                retrieval_reasons = list(set(
                    semantic_result.get('retrieval_reasons', []) +
                    metadata_result.get('retrieval_reasons', [])
                ))
            elif semantic_result:
                query_match_type = semantic_result.get('query_match_type', 'semantic')
                retrieval_reasons = semantic_result.get('retrieval_reasons', [])
            else:
                query_match_type = metadata_result.get('query_match_type', 'metadata')
                retrieval_reasons = metadata_result.get('retrieval_reasons', [])
            
            # Create RetrievalResult
            metadata = base_result.get('metadata', {})
            
            result = RetrievalResult(
                event_id=event_id,
                title=metadata.get('title', ''),
                summary=metadata.get('summary', ''),
                date=metadata.get('date', ''),
                actors=metadata.get('actors', []),
                tags=metadata.get('tags', []),
                importance=metadata.get('importance', ''),
                semantic_score=semantic_score,
                metadata_score=metadata_score,
                fusion_score=fusion_score,
                retrieval_reasons=retrieval_reasons,
                query_match_type=query_match_type
            )
            
            fused_results.append(result)
        
        # Sort by fusion score (descending)
        fused_results.sort(key=lambda x: x.fusion_score, reverse=True)
        
        # Limit to max results
        return fused_results[:self.config.max_final_results]
    
    def _apply_research_optimizations(self, 
                                    results: List[RetrievalResult],
                                    processed_query: ProcessedQuery) -> List[RetrievalResult]:
        """Apply research-specific optimizations to results."""
        
        if not results:
            return results
        
        optimized_results = list(results)
        
        # Research optimization 1: Intent-based boosting
        intent_boosts = self._get_intent_boosts(processed_query.intent)
        for result in optimized_results:
            for boost_type, boost_factor in intent_boosts.items():
                if self._result_matches_boost_criteria(result, boost_type):
                    result.fusion_score *= boost_factor
        
        # Research optimization 2: Diversity boosting
        if self.config.diversity_boost:
            optimized_results = self._apply_diversity_boost(optimized_results)
        
        # Research optimization 3: Temporal relevance boosting
        if self.config.temporal_boost and processed_query.filters.get('date_filters'):
            optimized_results = self._apply_temporal_boost(optimized_results, processed_query.filters['date_filters'])
        
        # Research optimization 4: Importance boosting
        optimized_results = self._apply_importance_boost(optimized_results)
        
        # Re-sort after optimizations
        optimized_results.sort(key=lambda x: x.fusion_score, reverse=True)
        
        return optimized_results
    
    def _get_intent_boosts(self, intent) -> Dict[str, float]:
        """Get boost factors based on query intent."""
        from ..query.intent import ResearchIntent
        
        intent_boosts = {
            ResearchIntent.COMPREHENSIVE_SEARCH: {
                'high_importance': 1.1,
                'multiple_actors': 1.05,
                'recent': 1.1
            },
            ResearchIntent.TIMELINE_ANALYSIS: {
                'chronological_clusters': 1.2,
                'temporal_keywords': 1.15
            },
            ResearchIntent.ACTOR_NETWORK: {
                'multiple_actors': 1.25,
                'relationship_keywords': 1.2
            },
            ResearchIntent.IMPORTANCE_FILTER: {
                'high_importance': 1.3,
                'critical_events': 1.25
            }
        }
        
        return intent_boosts.get(intent, {})
    
    def _result_matches_boost_criteria(self, result: RetrievalResult, criteria: str) -> bool:
        """Check if result matches boost criteria."""
        if criteria == 'high_importance':
            return result.importance.lower() in ['critical', 'major', 'high']
        elif criteria == 'multiple_actors':
            return len(result.actors) > 1
        elif criteria == 'recent':
            # Simple recency check - would need proper date parsing
            return '2024' in result.date or '2025' in result.date
        elif criteria == 'relationship_keywords':
            text = f"{result.title} {result.summary}".lower()
            relationship_words = ['connection', 'relationship', 'link', 'tie', 'network']
            return any(word in text for word in relationship_words)
        
        return False
    
    def _apply_diversity_boost(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Apply diversity boosting to avoid result clustering."""
        if len(results) <= 5:
            return results
        
        # Group by similar characteristics
        actor_groups = defaultdict(list)
        date_groups = defaultdict(list)
        
        for i, result in enumerate(results):
            # Group by primary actor
            if result.actors:
                primary_actor = result.actors[0]
                actor_groups[primary_actor].append(i)
            
            # Group by year  
            if result.date:
                year = result.date[:4] if len(result.date) >= 4 else 'unknown'
                date_groups[year].append(i)
        
        # Apply diversity penalty to over-represented groups
        for group_indices in actor_groups.values():
            if len(group_indices) > 3:  # More than 3 results from same actor
                penalty = 0.95 ** (len(group_indices) - 3)
                for i in group_indices[3:]:  # Penalize beyond first 3
                    results[i].fusion_score *= penalty
        
        return results
    
    def _apply_temporal_boost(self, results: List[RetrievalResult], date_filters: Dict) -> List[RetrievalResult]:
        """Apply temporal relevance boosting."""
        # This would need proper date parsing and comparison
        # For now, simple keyword-based boosting
        
        target_years = set()
        if 'years' in date_filters:
            target_years.update(str(year) for year in date_filters['years'])
        
        for result in results:
            for target_year in target_years:
                if target_year in result.date:
                    result.fusion_score *= 1.15
                    result.retrieval_reasons.append(f'temporal_boost_{target_year}')
                    break
        
        return results
    
    def _apply_importance_boost(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Apply importance-based boosting."""
        importance_boosts = {
            'critical': 1.3,
            'major': 1.2,
            'high': 1.15,
            'moderate': 1.0,
            'low': 0.95
        }
        
        for result in results:
            importance = result.importance.lower()
            for level, boost in importance_boosts.items():
                if level in importance:
                    result.fusion_score *= boost
                    if boost > 1.0:
                        result.retrieval_reasons.append(f'importance_boost_{level}')
                    break
        
        return results
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval performance statistics."""
        return dict(self.retrieval_stats)
    
    def reset_stats(self):
        """Reset retrieval statistics."""
        self.retrieval_stats.clear()