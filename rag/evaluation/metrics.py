"""
Evaluation Metrics for RAG System

Research-grade metrics implementation focusing on recall (completeness),
precision (accuracy), and consistency for reproducible research.
"""

from typing import List, Dict, Any, Set
import numpy as np
from collections import defaultdict
import hashlib
import json


def calculate_precision_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int) -> float:
    """
    Calculate precision@k metric.
    
    Args:
        retrieved_ids: List of retrieved event IDs in order of relevance
        relevant_ids: List of ground truth relevant event IDs
        k: Number of top results to consider
        
    Returns:
        Precision score between 0 and 1
    """
    if k <= 0:
        return 0.0
    
    retrieved_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    
    if not retrieved_k:
        return 0.0
    
    hits = sum(1 for doc_id in retrieved_k if doc_id in relevant_set)
    return hits / len(retrieved_k)


def calculate_recall_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int) -> float:
    """
    Calculate recall@k metric - critical for research completeness.
    
    Args:
        retrieved_ids: List of retrieved event IDs in order of relevance
        relevant_ids: List of ground truth relevant event IDs
        k: Number of top results to consider
        
    Returns:
        Recall score between 0 and 1
    """
    if not relevant_ids:
        return 1.0  # If no relevant docs exist, we found all of them
    
    if k <= 0:
        return 0.0
    
    retrieved_k = set(retrieved_ids[:k])
    relevant_set = set(relevant_ids)
    
    hits = len(retrieved_k.intersection(relevant_set))
    return hits / len(relevant_set)


def calculate_f1_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int) -> float:
    """
    Calculate F1@k score (harmonic mean of precision and recall).
    
    Args:
        retrieved_ids: List of retrieved event IDs
        relevant_ids: List of ground truth relevant event IDs
        k: Number of top results to consider
        
    Returns:
        F1 score between 0 and 1
    """
    precision = calculate_precision_at_k(retrieved_ids, relevant_ids, k)
    recall = calculate_recall_at_k(retrieved_ids, relevant_ids, k)
    
    if precision + recall == 0:
        return 0.0
    
    return 2 * (precision * recall) / (precision + recall)


def calculate_ndcg_at_k(retrieved_ids: List[str], relevant_ids: List[str], k: int, 
                        relevance_scores: Dict[str, float] = None) -> float:
    """
    Calculate NDCG@k (Normalized Discounted Cumulative Gain) metric.
    
    Args:
        retrieved_ids: List of retrieved event IDs in order
        relevant_ids: List of ground truth relevant event IDs
        k: Number of top results to consider
        relevance_scores: Optional relevance scores for each ID (default: binary)
        
    Returns:
        NDCG score between 0 and 1
    """
    if k <= 0:
        return 0.0
    
    # Use binary relevance if scores not provided
    if relevance_scores is None:
        relevant_set = set(relevant_ids)
        relevance_scores = {doc_id: 1.0 if doc_id in relevant_set else 0.0 
                           for doc_id in retrieved_ids}
    
    # Calculate DCG@k
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        relevance = relevance_scores.get(doc_id, 0.0)
        # Use log2(i+2) for discount factor (i+2 because positions start at 0)
        dcg += relevance / np.log2(i + 2)
    
    # Calculate Ideal DCG@k
    ideal_relevances = sorted([relevance_scores.get(doc_id, 1.0) 
                              for doc_id in relevant_ids], reverse=True)
    idcg = 0.0
    for i, relevance in enumerate(ideal_relevances[:k]):
        idcg += relevance / np.log2(i + 2)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def calculate_mrr(retrieved_ids: List[str], relevant_ids: List[str]) -> float:
    """
    Calculate Mean Reciprocal Rank.
    
    Args:
        retrieved_ids: List of retrieved event IDs in order
        relevant_ids: List of ground truth relevant event IDs
        
    Returns:
        MRR score between 0 and 1
    """
    relevant_set = set(relevant_ids)
    
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_set:
            return 1.0 / (i + 1)
    
    return 0.0


def calculate_consistency_score(results_list: List[List[str]]) -> float:
    """
    Calculate consistency score for multiple runs of the same query.
    Critical for research reproducibility.
    
    Args:
        results_list: List of result sets from multiple runs
        
    Returns:
        Consistency score between 0 and 1
    """
    if len(results_list) < 2:
        return 1.0
    
    # Calculate pairwise Jaccard similarity
    similarities = []
    for i in range(len(results_list)):
        for j in range(i + 1, len(results_list)):
            set_i = set(results_list[i])
            set_j = set(results_list[j])
            
            if not set_i and not set_j:
                similarity = 1.0
            elif not set_i or not set_j:
                similarity = 0.0
            else:
                intersection = len(set_i.intersection(set_j))
                union = len(set_i.union(set_j))
                similarity = intersection / union if union > 0 else 0.0
            
            similarities.append(similarity)
    
    return np.mean(similarities) if similarities else 1.0


def calculate_completeness_score(retrieved_ids: List[str], all_relevant_ids: List[str],
                                critical_ids: List[str] = None) -> Dict[str, float]:
    """
    Calculate completeness metrics for research quality.
    
    Args:
        retrieved_ids: List of retrieved event IDs
        all_relevant_ids: List of all relevant event IDs
        critical_ids: Optional list of critical events that must be found
        
    Returns:
        Dictionary with completeness metrics
    """
    retrieved_set = set(retrieved_ids)
    all_relevant_set = set(all_relevant_ids)
    
    metrics = {
        'overall_completeness': len(retrieved_set.intersection(all_relevant_set)) / len(all_relevant_set)
        if all_relevant_set else 1.0
    }
    
    if critical_ids:
        critical_set = set(critical_ids)
        found_critical = retrieved_set.intersection(critical_set)
        metrics['critical_completeness'] = len(found_critical) / len(critical_set) if critical_set else 1.0
        metrics['missing_critical'] = list(critical_set - found_critical)
    
    # Calculate coverage by position
    coverage_at_positions = []
    for k in [5, 10, 20, 50]:
        if k <= len(retrieved_ids):
            coverage_at_k = calculate_recall_at_k(retrieved_ids, all_relevant_ids, k)
            coverage_at_positions.append((k, coverage_at_k))
    metrics['coverage_curve'] = coverage_at_positions
    
    return metrics


def calculate_diversity_score(retrieved_items: List[Dict[str, Any]], 
                            diversity_fields: List[str] = None) -> float:
    """
    Calculate diversity score for retrieved results.
    Ensures broad coverage across different aspects.
    
    Args:
        retrieved_items: List of retrieved items with metadata
        diversity_fields: Fields to consider for diversity (default: ['tags', 'actors', 'date'])
        
    Returns:
        Diversity score between 0 and 1
    """
    if not retrieved_items:
        return 0.0
    
    if diversity_fields is None:
        diversity_fields = ['tags', 'actors', 'date']
    
    diversity_scores = []
    
    for field in diversity_fields:
        unique_values = set()
        total_values = 0
        
        for item in retrieved_items:
            value = item.get(field)
            if value:
                if isinstance(value, list):
                    unique_values.update(value)
                    total_values += len(value)
                else:
                    unique_values.add(str(value))
                    total_values += 1
        
        if total_values > 0:
            diversity = len(unique_values) / total_values
            diversity_scores.append(diversity)
    
    return np.mean(diversity_scores) if diversity_scores else 0.0


def calculate_temporal_coverage(events: List[Dict[str, Any]], 
                               expected_range: tuple = None) -> Dict[str, Any]:
    """
    Analyze temporal coverage of retrieved events.
    
    Args:
        events: List of events with date fields
        expected_range: Optional (start_date, end_date) tuple
        
    Returns:
        Dictionary with temporal coverage metrics
    """
    if not events:
        return {'coverage': 0.0, 'gaps': [], 'distribution': {}}
    
    dates = sorted([e.get('date', '') for e in events if e.get('date')])
    
    if not dates:
        return {'coverage': 0.0, 'gaps': [], 'distribution': {}}
    
    # Group by month
    month_counts = defaultdict(int)
    for date in dates:
        if len(date) >= 7:  # YYYY-MM format minimum
            month = date[:7]
            month_counts[month] += 1
    
    # Identify gaps (months with no events)
    if len(month_counts) > 1:
        all_months = []
        start_year, start_month = map(int, min(month_counts.keys()).split('-'))
        end_year, end_month = map(int, max(month_counts.keys()).split('-'))
        
        current_year, current_month = start_year, start_month
        while (current_year, current_month) <= (end_year, end_month):
            month_str = f"{current_year:04d}-{current_month:02d}"
            all_months.append(month_str)
            
            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1
        
        gaps = [month for month in all_months if month not in month_counts]
    else:
        gaps = []
    
    coverage_score = len(month_counts) / len(all_months) if len(month_counts) > 1 else 1.0
    
    return {
        'coverage': coverage_score,
        'gaps': gaps,
        'distribution': dict(month_counts),
        'date_range': {'start': dates[0], 'end': dates[-1]},
        'total_months_covered': len(month_counts),
        'total_months_in_range': len(all_months) if len(month_counts) > 1 else 1
    }


def calculate_result_hash(results: List[str]) -> str:
    """
    Calculate deterministic hash of results for consistency tracking.
    
    Args:
        results: List of result IDs
        
    Returns:
        Hash string
    """
    # Sort to ensure consistent hashing
    sorted_results = sorted(results)
    result_string = json.dumps(sorted_results, sort_keys=True)
    return hashlib.sha256(result_string.encode()).hexdigest()


def aggregate_metrics(metric_results: List[Dict[str, float]]) -> Dict[str, Any]:
    """
    Aggregate multiple metric results into summary statistics.
    
    Args:
        metric_results: List of metric dictionaries from multiple queries
        
    Returns:
        Aggregated statistics
    """
    if not metric_results:
        return {}
    
    aggregated = defaultdict(list)
    
    for result in metric_results:
        for key, value in result.items():
            if isinstance(value, (int, float)):
                aggregated[key].append(value)
    
    summary = {}
    for key, values in aggregated.items():
        summary[f'{key}_mean'] = np.mean(values)
        summary[f'{key}_std'] = np.std(values)
        summary[f'{key}_min'] = np.min(values)
        summary[f'{key}_max'] = np.max(values)
        summary[f'{key}_median'] = np.median(values)
    
    return summary