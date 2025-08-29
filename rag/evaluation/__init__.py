"""
RAG Evaluation Framework for Research-Grade Quality Assessment

This module provides comprehensive evaluation tools for the Kleptocracy Timeline RAG system,
focusing on research quality metrics including recall, precision, consistency, and completeness.
"""

# from .evaluator import RAGEvaluator  # Commented out for ground truth building
from .metrics import (
    calculate_precision_at_k,
    calculate_recall_at_k,
    calculate_ndcg_at_k,
    calculate_mrr,
    calculate_f1_at_k,
    calculate_consistency_score,
    calculate_completeness_score
)
from .test_queries import TEST_QUERIES, load_test_queries
from .ground_truth import GroundTruthManager
from .reports import EvaluationReportGenerator

__all__ = [
    # 'RAGEvaluator',
    'calculate_precision_at_k',
    'calculate_recall_at_k', 
    'calculate_ndcg_at_k',
    'calculate_mrr',
    'calculate_f1_at_k',
    'calculate_consistency_score',
    'calculate_completeness_score',
    'TEST_QUERIES',
    'load_test_queries',
    'GroundTruthManager',
    'EvaluationReportGenerator'
]