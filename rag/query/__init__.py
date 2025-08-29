"""
Advanced Query Processing for Research-Grade RAG

This module provides comprehensive query processing capabilities including
expansion, filtering, intent classification, and rewriting for better results.
"""

from .processor import ResearchQueryProcessor
from .expansion import (
    expand_with_domain_ontology,
    expand_with_co_occurrence_analysis,
    expand_temporal_context_comprehensively,
    expand_with_capture_lane_synonyms,
    expand_for_completeness
)
from .filters import (
    extract_date_filters,
    extract_actor_filters,
    extract_importance_filters,
    extract_metadata_filters
)
from .intent import QueryIntentClassifier, ResearchIntent
from .rewrite import QueryRewriter

__all__ = [
    'ResearchQueryProcessor',
    'expand_with_domain_ontology',
    'expand_with_co_occurrence_analysis', 
    'expand_temporal_context_comprehensively',
    'expand_with_capture_lane_synonyms',
    'expand_for_completeness',
    'extract_date_filters',
    'extract_actor_filters',
    'extract_importance_filters',
    'extract_metadata_filters',
    'QueryIntentClassifier',
    'ResearchIntent',
    'QueryRewriter'
]