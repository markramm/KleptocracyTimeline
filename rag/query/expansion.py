"""
Comprehensive Query Expansion for Research

Implements multiple expansion strategies prioritizing recall over precision.
"""

import re
from typing import List, Dict, Any, Set
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


def expand_with_domain_ontology(query: str) -> List[str]:
    """
    Expand using kleptocracy/democracy domain ontology.
    
    Args:
        query: Original query
        
    Returns:
        List of expanded query variants
    """
    expansions = []
    query_lower = query.lower()
    
    # Kleptocracy domain ontology
    kleptocracy_expansions = {
        'kleptocracy': ['corruption', 'state capture', 'oligarchy', 'crony capitalism', 'rent-seeking'],
        'corruption': ['graft', 'bribery', 'kickbacks', 'pay-to-play', 'quid pro quo', 'embezzlement'],
        'regulatory capture': ['agency capture', 'revolving door', 'industry influence', 'regulatory compliance'],
        'democracy': ['democratic institutions', 'rule of law', 'checks and balances', 'democratic process'],
        'authoritarian': ['autocratic', 'dictatorial', 'despotic', 'tyrannical', 'totalitarian'],
        'election': ['voting', 'ballot', 'electoral process', 'suffrage', 'franchise'],
        'transparency': ['accountability', 'openness', 'disclosure', 'public records', 'freedom of information'],
        'oligarch': ['tycoon', 'magnate', 'billionaire', 'plutocrat', 'business elite'],
        'propaganda': ['disinformation', 'misinformation', 'media manipulation', 'spin', 'narrative control']
    }
    
    # Cryptocurrency domain ontology  
    crypto_expansions = {
        'cryptocurrency': ['crypto', 'digital currency', 'virtual currency', 'digital assets'],
        'bitcoin': ['BTC', 'digital gold', 'peer-to-peer currency'],
        'blockchain': ['distributed ledger', 'decentralized technology', 'crypto technology'],
        'defi': ['decentralized finance', 'yield farming', 'liquidity mining'],
        'memecoin': ['meme coin', 'joke coin', 'viral coin', 'social token'],
        'stablecoin': ['pegged cryptocurrency', 'dollar-backed crypto', 'fiat-backed token']
    }
    
    # Political domain ontology
    political_expansions = {
        'executive order': ['presidential directive', 'administrative order', 'presidential memorandum'],
        'schedule f': ['federal workforce', 'civil service', 'government employees', 'federal workers'],
        'judicial': ['court', 'legal', 'justice system', 'judiciary'],
        'legislative': ['congress', 'senate', 'house', 'lawmaking', 'legislation'],
        'bureaucracy': ['civil service', 'administrative state', 'federal agencies', 'government departments'],
        'whistleblower': ['informant', 'insider', 'leaker', 'truth-teller'],
        'national security': ['homeland security', 'defense', 'intelligence', 'security apparatus']
    }
    
    # Combine all ontologies
    all_expansions = {**kleptocracy_expansions, **crypto_expansions, **political_expansions}
    
    # Find matches and create expansions
    for term, synonyms in all_expansions.items():
        if term in query_lower:
            # Add synonym-based expansions
            for synonym in synonyms:
                expanded_query = re.sub(re.escape(term), synonym, query, flags=re.IGNORECASE)
                if expanded_query != query:
                    expansions.append(expanded_query)
            
            # Add conjunction expansions (broader search)
            expansions.extend([
                f"{query} OR {synonym}" for synonym in synonyms[:3]  # Top 3 synonyms
            ])
    
    return expansions[:10]  # Limit to top 10 expansions


def expand_with_co_occurrence_analysis(query: str, events_corpus: List[Dict[str, Any]]) -> List[str]:
    """
    Expand using statistical co-occurrence from events corpus.
    
    Args:
        query: Original query
        events_corpus: List of event dictionaries
        
    Returns:
        List of expanded queries based on co-occurrence
    """
    if not events_corpus:
        return []
    
    expansions = []
    query_terms = set(re.findall(r'\b[a-zA-Z]{3,}\b', query.lower()))
    
    # Build term co-occurrence from corpus
    term_pairs = defaultdict(int)
    
    for event in events_corpus:
        # Extract text from event
        text_parts = [
            event.get('title', ''),
            event.get('summary', ''),
            ' '.join(event.get('tags', [])),
            ' '.join(event.get('actors', []) if isinstance(event.get('actors', []), list) 
                    else [event.get('actors', '')])
        ]
        event_text = ' '.join(text_parts).lower()
        event_terms = set(re.findall(r'\b[a-zA-Z]{3,}\b', event_text))
        
        # Find co-occurrences with query terms
        for query_term in query_terms:
            if query_term in event_terms:
                for other_term in event_terms:
                    if other_term != query_term and len(other_term) > 3:
                        term_pairs[(query_term, other_term)] += 1
    
    # Get most frequent co-occurring terms
    for (query_term, cooccur_term), count in term_pairs.most_common(20):
        if count >= 3:  # At least 3 co-occurrences
            # Add terms to query
            if cooccur_term not in query.lower():
                expansions.append(f"{query} {cooccur_term}")
    
    return expansions[:8]  # Limit to top 8


def expand_temporal_context_comprehensively(query: str) -> List[str]:
    """
    Add comprehensive temporal context for research.
    
    Args:
        query: Original query
        
    Returns:
        List of temporally expanded queries
    """
    expansions = []
    
    # Map temporal terms to comprehensive ranges
    temporal_mappings = {
        'recent': [
            'in the last year',
            'in the past 12 months', 
            'since 2024',
            'in 2025'
        ],
        'current': [
            'ongoing',
            'present day',
            'as of 2025',
            'contemporary'
        ],
        'trump era': [
            'during trump presidency',
            'trump administration',
            '2017-2021',
            '2025-present',
            'trump first term',
            'trump second term'
        ],
        'biden era': [
            'during biden presidency',
            'biden administration', 
            '2021-2025'
        ],
        'post-election': [
            'after election',
            'following election',
            'election aftermath',
            'transition period'
        ]
    }
    
    query_lower = query.lower()
    
    # Find temporal terms and expand
    for temporal_term, expansions_list in temporal_mappings.items():
        if temporal_term in query_lower:
            for expansion in expansions_list:
                expanded = query + f" {expansion}"
                expansions.append(expanded)
    
    # Add generic temporal expansions
    generic_temporal = [
        'timeline',
        'chronology',
        'sequence of events',
        'development over time',
        'historical progression'
    ]
    
    # Check if query might benefit from temporal context
    if any(word in query_lower for word in ['how', 'when', 'what happened', 'events', 'develop']):
        for temporal in generic_temporal:
            expansions.append(f"{temporal} of {query}")
    
    return expansions[:10]


def expand_with_capture_lane_synonyms(query: str) -> List[str]:
    """
    Expand using capture lane taxonomy and synonyms.
    
    Args:
        query: Original query
        
    Returns:
        List of capture lane expanded queries
    """
    expansions = []
    
    # Capture lane taxonomy
    capture_lanes = {
        'regulatory': [
            'regulatory capture',
            'agency capture', 
            'industry influence',
            'revolving door',
            'compliance manipulation',
            'rule-making influence',
            'enforcement capture'
        ],
        'judicial': [
            'judicial capture',
            'court capture',
            'legal system manipulation',
            'justice system influence',
            'judicial appointments',
            'court packing',
            'legal precedent manipulation'
        ],
        'legislative': [
            'legislative capture',
            'congressional influence',
            'lawmaking manipulation',
            'lobbying influence',
            'campaign contributions',
            'political donations',
            'policy influence'
        ],
        'media': [
            'media capture',
            'information control',
            'narrative manipulation',
            'propaganda',
            'disinformation',
            'media consolidation',
            'editorial influence'
        ],
        'economic': [
            'economic capture',
            'market manipulation',
            'financial influence',
            'monopolization',
            'cartel behavior',
            'price fixing',
            'economic coercion'
        ],
        'electoral': [
            'electoral manipulation',
            'voting system interference',
            'election influence',
            'voter suppression',
            'gerrymandering',
            'campaign finance manipulation'
        ]
    }
    
    query_lower = query.lower()
    
    # Find relevant capture lanes
    for lane, synonyms in capture_lanes.items():
        if lane in query_lower or any(syn.lower() in query_lower for syn in synonyms):
            # Add related capture lane terms
            for synonym in synonyms:
                if synonym.lower() not in query_lower:
                    expansions.append(f"{query} {synonym}")
    
    # Add general capture terms
    if 'capture' in query_lower:
        general_capture_terms = [
            'institutional capture',
            'state capture', 
            'corporate influence',
            'special interests',
            'rent-seeking',
            'corruption',
            'influence peddling'
        ]
        
        for term in general_capture_terms:
            if term.lower() not in query_lower:
                expansions.append(f"{query} {term}")
    
    return expansions[:8]


def expand_for_completeness(query: str) -> List[str]:
    """
    Aggressive expansion prioritizing recall over precision.
    Research priority: better to have false positives than false negatives.
    
    Args:
        query: Original query
        
    Returns:
        List of comprehensively expanded queries
    """
    expansions = []
    
    # Add comprehensive modifiers
    comprehensive_modifiers = [
        'all aspects of',
        'comprehensive analysis of',
        'complete picture of',
        'full scope of',
        'entire context of',
        'everything related to',
        'any mention of',
        'all instances of'
    ]
    
    for modifier in comprehensive_modifiers:
        expansions.append(f"{modifier} {query}")
    
    # Add investigative terms
    if any(word in query.lower() for word in ['scandal', 'corruption', 'investigation', 'controversy']):
        investigative_terms = [
            'investigation into',
            'probe of',
            'inquiry about', 
            'examination of',
            'allegations of',
            'evidence of',
            'reports of',
            'claims about'
        ]
        
        for term in investigative_terms:
            expansions.append(f"{term} {query}")
    
    # Add relationship expansion
    relationship_terms = [
        'connections to',
        'links with',
        'associations with',
        'relationships involving',
        'ties to',
        'involvement in'
    ]
    
    # Extract main entities for relationship expansion
    entities = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', query)
    for entity in entities:
        for rel_term in relationship_terms:
            expansions.append(f"{rel_term} {entity}")
    
    # Add temporal breadth
    temporal_breadth = [
        'historical context of',
        'background of',
        'origins of',
        'development of',
        'evolution of',
        'consequences of',
        'aftermath of',
        'implications of'
    ]
    
    for temporal in temporal_breadth:
        expansions.append(f"{temporal} {query}")
    
    # Add uncertainty handling (important for research)
    uncertainty_terms = [
        'potential',
        'possible',
        'alleged',
        'suspected',
        'reported',
        'claimed',
        'purported'
    ]
    
    for uncertain in uncertainty_terms:
        expansions.append(f"{uncertain} {query}")
    
    return expansions[:15]  # More expansions for completeness


def expand_with_semantic_similarity(query: str, similarity_threshold: float = 0.7) -> List[str]:
    """
    Expand using semantic similarity (if embedding model available).
    
    Args:
        query: Original query
        similarity_threshold: Minimum similarity for expansion
        
    Returns:
        List of semantically similar expansions
    """
    # This would require access to the embedding model
    # For now, return rule-based semantic expansions
    
    semantic_mappings = {
        # Financial terms
        'money': ['funding', 'finances', 'payments', 'cash', 'capital'],
        'payment': ['transaction', 'transfer', 'remittance', 'compensation'],
        'profit': ['revenue', 'earnings', 'income', 'gains'],
        
        # Political terms  
        'influence': ['power', 'control', 'sway', 'leverage', 'clout'],
        'official': ['politician', 'leader', 'representative', 'authority'],
        'government': ['administration', 'state', 'federal', 'public sector'],
        
        # Action terms
        'control': ['manipulate', 'influence', 'dominate', 'command'],
        'investigate': ['probe', 'examine', 'inquire', 'research', 'study'],
        'reveal': ['expose', 'uncover', 'disclose', 'discover', 'show']
    }
    
    expansions = []
    query_lower = query.lower()
    
    for term, similar_terms in semantic_mappings.items():
        if term in query_lower:
            for similar in similar_terms:
                expanded = re.sub(re.escape(term), similar, query, flags=re.IGNORECASE)
                if expanded != query:
                    expansions.append(expanded)
    
    return expansions


if __name__ == '__main__':
    # Test expansions
    test_queries = [
        "cryptocurrency and Trump",
        "regulatory capture",
        "recent Schedule F events",
        "judicial capture investigation"
    ]
    
    for query in test_queries:
        print(f"\nOriginal: {query}")
        
        domain_exp = expand_with_domain_ontology(query)
        print(f"Domain: {domain_exp[:3]}")
        
        temporal_exp = expand_temporal_context_comprehensively(query)
        print(f"Temporal: {temporal_exp[:3]}")
        
        capture_exp = expand_with_capture_lane_synonyms(query)
        print(f"Capture: {capture_exp[:3]}")
        
        complete_exp = expand_for_completeness(query)
        print(f"Completeness: {complete_exp[:3]}")