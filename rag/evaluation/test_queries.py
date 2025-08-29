"""
Test Query Dataset for RAG Evaluation

Comprehensive set of 50+ test queries covering different search patterns,
complexity levels, and research scenarios for the Kleptocracy Timeline.
"""

from typing import List, Dict, Any
import json
from pathlib import Path


TEST_QUERIES = [
    # === Entity Retrieval Queries (Easy) ===
    {
        'id': 'entity_crypto_trump',
        'query': 'What events involve cryptocurrency and Trump?',
        'expected_event_ids': [
            '2025-01-20--trump-memecoin-launch',
            '2025-01-18--world-liberty-financial-bitcoin-purchase',
            '2025-01-20--trump-solana-memecoin-creates-potential-conflicts',
            '2025-01-19--melania-trump-launches-melania-memecoin'
        ],
        'expected_actors': ['Donald Trump', 'World Liberty Financial', 'Melania Trump'],
        'expected_tags': ['cryptocurrency', 'conflicts-of-interest'],
        'type': 'entity_retrieval',
        'difficulty': 'easy',
        'priority': 'high'
    },
    {
        'id': 'entity_epstein_2025',
        'query': 'What happened with Epstein files in 2025?',
        'expected_event_ids': [
            '2025-01-01--epstein-files-release-cancelled',
            '2025-01-10--fbi-resists-epstein-files-foia-request'
        ],
        'expected_actors': ['Jeffrey Epstein'],
        'expected_tags': ['transparency', 'justice-obstruction'],
        'type': 'entity_retrieval',
        'difficulty': 'easy',
        'priority': 'high'
    },
    {
        'id': 'entity_elon_musk',
        'query': 'Show me events about Elon Musk and regulatory influence',
        'expected_event_ids': [],  # To be filled based on actual data
        'expected_actors': ['Elon Musk'],
        'expected_tags': ['regulatory-capture', 'corporate-influence'],
        'type': 'entity_retrieval',
        'difficulty': 'medium',
        'priority': 'high'
    },
    
    # === Temporal Queries (Medium) ===
    {
        'id': 'temporal_jan_2025_orders',
        'query': 'What executive orders were signed in January 2025?',
        'expected_event_ids': [
            '2025-01-20--trump-signs-executive-orders-immigration',
            '2025-01-20--executive-order-birthright-citizenship',
            '2025-01-23--trump-signs-order-ending-dei-programs'
        ],
        'expected_tags': ['executive-orders'],
        'date_range': ['2025-01-01', '2025-01-31'],
        'type': 'temporal',
        'difficulty': 'medium',
        'priority': 'high'
    },
    {
        'id': 'temporal_schedule_f',
        'query': 'Show timeline of Schedule F implementation and federal workforce changes',
        'expected_event_ids': [],  # To be filled
        'expected_tags': ['schedule-f', 'federal-workforce'],
        'type': 'temporal_pattern',
        'difficulty': 'hard',
        'priority': 'critical'
    },
    {
        'id': 'temporal_recent',
        'query': 'What are the most recent events related to regulatory capture?',
        'expected_tags': ['regulatory-capture'],
        'type': 'temporal_recent',
        'difficulty': 'medium',
        'priority': 'high'
    },
    
    # === Pattern Analysis Queries (Hard) ===
    {
        'id': 'pattern_capture_lanes',
        'query': 'Show patterns of institutional capture across different government agencies',
        'expected_capture_lanes': ['regulatory', 'judicial', 'legislative'],
        'type': 'pattern_analysis',
        'difficulty': 'hard',
        'priority': 'critical'
    },
    {
        'id': 'pattern_loyalty_tests',
        'query': 'How are loyalty tests being implemented across federal agencies?',
        'expected_tags': ['loyalty-tests', 'federal-workforce'],
        'type': 'pattern_analysis',
        'difficulty': 'hard',
        'priority': 'critical'
    },
    {
        'id': 'pattern_media_control',
        'query': 'What patterns exist in media manipulation and disinformation campaigns?',
        'expected_tags': ['media-manipulation', 'disinformation'],
        'expected_actors': ['Sinclair Broadcasting'],
        'type': 'pattern_analysis',
        'difficulty': 'hard',
        'priority': 'high'
    },
    
    # === Actor Network Queries (Complex) ===
    {
        'id': 'network_trump_associates',
        'query': 'Show all connections between Trump and his business associates in government positions',
        'expected_actors': ['Donald Trump'],
        'relationship_type': 'business_connections',
        'type': 'actor_network',
        'difficulty': 'hard',
        'priority': 'high'
    },
    {
        'id': 'network_tech_oligarchs',
        'query': 'Map relationships between tech billionaires and policy influence',
        'expected_actors': ['Elon Musk', 'Mark Zuckerberg', 'Jeff Bezos'],
        'type': 'actor_network',
        'difficulty': 'hard',
        'priority': 'medium'
    },
    
    # === Multi-faceted Complex Queries ===
    {
        'id': 'complex_democracy_erosion',
        'query': 'Show comprehensive evidence of democratic backsliding including judicial capture, election interference, and media control',
        'expected_tags': ['democracy', 'judicial-capture', 'election-integrity', 'media-manipulation'],
        'type': 'complex_multi_faceted',
        'difficulty': 'very_hard',
        'priority': 'critical'
    },
    {
        'id': 'complex_financial_corruption',
        'query': 'Analyze financial corruption patterns including cryptocurrency, foreign payments, and corporate capture',
        'expected_tags': ['cryptocurrency', 'foreign-influence', 'corporate-capture', 'conflicts-of-interest'],
        'type': 'complex_multi_faceted',
        'difficulty': 'very_hard',
        'priority': 'critical'
    },
    
    # === Negative/Exclusion Queries ===
    {
        'id': 'negative_no_trump',
        'query': 'Show regulatory capture events that do NOT involve Trump directly',
        'expected_tags': ['regulatory-capture'],
        'exclude_actors': ['Donald Trump'],
        'type': 'negative_query',
        'difficulty': 'medium',
        'priority': 'medium'
    },
    {
        'id': 'negative_confirmed_only',
        'query': 'Show only confirmed events about judicial appointments, not reported or developing',
        'expected_tags': ['judicial-appointments'],
        'expected_status': ['confirmed'],
        'type': 'filtered_query',
        'difficulty': 'easy',
        'priority': 'medium'
    },
    
    # === Comparative Queries ===
    {
        'id': 'comparative_administrations',
        'query': 'Compare regulatory capture patterns between Trump first term and second term',
        'date_ranges': [['2017-01-20', '2021-01-20'], ['2025-01-20', '2029-01-20']],
        'type': 'comparative',
        'difficulty': 'very_hard',
        'priority': 'high'
    },
    {
        'id': 'comparative_capture_types',
        'query': 'Compare effectiveness of regulatory capture versus judicial capture strategies',
        'capture_lanes': ['regulatory', 'judicial'],
        'type': 'comparative',
        'difficulty': 'hard',
        'priority': 'medium'
    },
    
    # === Gap Analysis Queries ===
    {
        'id': 'gap_missing_connections',
        'query': 'What connections between cryptocurrency and foreign influence might we be missing?',
        'type': 'gap_analysis',
        'difficulty': 'very_hard',
        'priority': 'high'
    },
    {
        'id': 'gap_underreported',
        'query': 'What aspects of Schedule F implementation are underreported in our timeline?',
        'type': 'gap_analysis',
        'difficulty': 'hard',
        'priority': 'critical'
    },
    
    # === Validation Queries ===
    {
        'id': 'validation_sources',
        'query': 'Show events about EPA regulatory changes with at least 3 credible sources',
        'expected_tags': ['epa', 'regulatory-capture'],
        'min_sources': 3,
        'type': 'validation_query',
        'difficulty': 'medium',
        'priority': 'high'
    },
    {
        'id': 'validation_conflicting',
        'query': 'Find events with conflicting or disputed information about election integrity',
        'expected_tags': ['election-integrity'],
        'expected_status': ['disputed', 'developing'],
        'type': 'validation_query',
        'difficulty': 'medium',
        'priority': 'high'
    },
    
    # === Causal Analysis Queries ===
    {
        'id': 'causal_schedule_f_impact',
        'query': 'What were the consequences of Schedule F implementation on federal agencies?',
        'type': 'causal_analysis',
        'difficulty': 'hard',
        'priority': 'critical'
    },
    {
        'id': 'causal_deregulation',
        'query': 'What led to the deregulation of environmental protections in 2025?',
        'type': 'causal_analysis',
        'difficulty': 'hard',
        'priority': 'high'
    },
    
    # === Escalation Tracking Queries ===
    {
        'id': 'escalation_authoritarianism',
        'query': 'Track escalation of authoritarian measures from January to December 2025',
        'date_range': ['2025-01-01', '2025-12-31'],
        'expected_tags': ['authoritarianism', 'democracy'],
        'type': 'escalation_tracking',
        'difficulty': 'very_hard',
        'priority': 'critical'
    },
    {
        'id': 'escalation_media_control',
        'query': 'How has media control escalated since 2025 inauguration?',
        'date_range': ['2025-01-20', '2025-12-31'],
        'expected_tags': ['media-manipulation', 'press-freedom'],
        'type': 'escalation_tracking',
        'difficulty': 'hard',
        'priority': 'high'
    },
    
    # === Research Workflow Queries ===
    {
        'id': 'research_comprehensive_capture',
        'query': 'Provide comprehensive analysis of all capture lanes with timeline, actors, and impact assessment',
        'type': 'research_comprehensive',
        'difficulty': 'very_hard',
        'priority': 'critical'
    },
    {
        'id': 'research_foreign_influence',
        'query': 'Complete research report on foreign influence operations including Saudi, Russian, and Chinese connections',
        'expected_tags': ['foreign-influence', 'saudi-arabia', 'russia', 'china'],
        'type': 'research_comprehensive',
        'difficulty': 'very_hard',
        'priority': 'critical'
    },
    
    # === Importance-based Queries ===
    {
        'id': 'importance_critical_only',
        'query': 'Show only critical importance events (8+) related to democracy erosion',
        'min_importance': 8,
        'expected_tags': ['democracy'],
        'type': 'importance_filter',
        'difficulty': 'easy',
        'priority': 'high'
    },
    {
        'id': 'importance_major_crypto',
        'query': 'Find major importance cryptocurrency events that pose conflicts of interest',
        'min_importance': 6,
        'expected_tags': ['cryptocurrency', 'conflicts-of-interest'],
        'type': 'importance_filter',
        'difficulty': 'medium',
        'priority': 'medium'
    },
    
    # === Source Quality Queries ===
    {
        'id': 'source_primary_only',
        'query': 'Show events with primary sources about judicial appointments',
        'expected_tags': ['judicial-appointments'],
        'source_type': 'primary',
        'type': 'source_quality',
        'difficulty': 'medium',
        'priority': 'medium'
    },
    {
        'id': 'source_multi_confirmed',
        'query': 'Find events confirmed by multiple major outlets about Schedule F',
        'expected_tags': ['schedule-f'],
        'min_sources': 3,
        'source_quality': 'major_outlet',
        'type': 'source_quality',
        'difficulty': 'medium',
        'priority': 'high'
    },
    
    # === Location-based Queries ===
    {
        'id': 'location_dc',
        'query': 'Events happening in Washington DC related to protests or demonstrations',
        'location': 'Washington, DC',
        'expected_tags': ['protests', 'demonstrations'],
        'type': 'location_based',
        'difficulty': 'medium',
        'priority': 'low'
    },
    {
        'id': 'location_international',
        'query': 'International events affecting US democracy',
        'location_type': 'international',
        'expected_tags': ['foreign-influence', 'democracy'],
        'type': 'location_based',
        'difficulty': 'medium',
        'priority': 'medium'
    },
    
    # === Semantic Understanding Queries ===
    {
        'id': 'semantic_corruption_synonyms',
        'query': 'Find instances of graft, bribery, kickbacks, and pay-to-play schemes',
        'semantic_concepts': ['corruption', 'graft', 'bribery', 'kickbacks', 'pay-to-play'],
        'type': 'semantic_understanding',
        'difficulty': 'hard',
        'priority': 'high'
    },
    {
        'id': 'semantic_democracy_concepts',
        'query': 'Events threatening checks and balances, separation of powers, or rule of law',
        'semantic_concepts': ['checks-and-balances', 'separation-of-powers', 'rule-of-law'],
        'type': 'semantic_understanding',
        'difficulty': 'hard',
        'priority': 'critical'
    },
    
    # === Statistical Queries ===
    {
        'id': 'stats_monthly_frequency',
        'query': 'What months in 2025 had the most democracy-related events?',
        'date_range': ['2025-01-01', '2025-12-31'],
        'expected_tags': ['democracy'],
        'type': 'statistical_analysis',
        'difficulty': 'medium',
        'priority': 'low'
    },
    {
        'id': 'stats_actor_frequency',
        'query': 'Which actors appear most frequently in regulatory capture events?',
        'expected_tags': ['regulatory-capture'],
        'type': 'statistical_analysis',
        'difficulty': 'medium',
        'priority': 'medium'
    }
]


def load_test_queries(filter_by: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Load test queries with optional filtering.
    
    Args:
        filter_by: Optional filters (e.g., {'difficulty': 'easy', 'priority': 'high'})
        
    Returns:
        Filtered list of test queries
    """
    queries = TEST_QUERIES.copy()
    
    if filter_by:
        for key, value in filter_by.items():
            if isinstance(value, list):
                queries = [q for q in queries if q.get(key) in value]
            else:
                queries = [q for q in queries if q.get(key) == value]
    
    return queries


def save_test_queries(filepath: str = None):
    """
    Save test queries to JSON file.
    
    Args:
        filepath: Path to save file (default: test_queries.json)
    """
    if filepath is None:
        filepath = Path(__file__).parent / 'test_queries.json'
    
    with open(filepath, 'w') as f:
        json.dump(TEST_QUERIES, f, indent=2)
    
    print(f"Saved {len(TEST_QUERIES)} test queries to {filepath}")


def load_test_queries_from_file(filepath: str) -> List[Dict[str, Any]]:
    """
    Load test queries from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        List of test queries
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def get_query_categories() -> Dict[str, List[str]]:
    """
    Get categorized query IDs for targeted testing.
    
    Returns:
        Dictionary mapping categories to query IDs
    """
    categories = {}
    
    for query in TEST_QUERIES:
        query_type = query.get('type', 'unknown')
        if query_type not in categories:
            categories[query_type] = []
        categories[query_type].append(query['id'])
    
    return categories


def get_priority_queries(priority: str = 'critical') -> List[Dict[str, Any]]:
    """
    Get queries by priority level.
    
    Args:
        priority: Priority level ('critical', 'high', 'medium', 'low')
        
    Returns:
        List of queries with specified priority
    """
    return [q for q in TEST_QUERIES if q.get('priority') == priority]


def get_research_queries() -> List[Dict[str, Any]]:
    """
    Get queries specifically designed for research workflows.
    
    Returns:
        List of research-oriented queries
    """
    research_types = [
        'research_comprehensive',
        'gap_analysis',
        'pattern_analysis',
        'comparative',
        'causal_analysis',
        'escalation_tracking'
    ]
    
    return [q for q in TEST_QUERIES if q.get('type') in research_types]


if __name__ == '__main__':
    # Save queries to file for easy editing
    save_test_queries()
    
    # Print statistics
    print(f"\nTotal test queries: {len(TEST_QUERIES)}")
    
    categories = get_query_categories()
    print("\nQueries by type:")
    for cat, ids in sorted(categories.items()):
        print(f"  {cat}: {len(ids)} queries")
    
    print("\nQueries by difficulty:")
    for difficulty in ['easy', 'medium', 'hard', 'very_hard']:
        count = len([q for q in TEST_QUERIES if q.get('difficulty') == difficulty])
        print(f"  {difficulty}: {count} queries")
    
    print("\nQueries by priority:")
    for priority in ['critical', 'high', 'medium', 'low']:
        count = len([q for q in TEST_QUERIES if q.get('priority') == priority])
        print(f"  {priority}: {count} queries")