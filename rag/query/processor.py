"""
Research-Oriented Query Processing Pipeline

Advanced query processing that prioritizes recall and completeness for research workflows.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

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

logger = logging.getLogger(__name__)


@dataclass
class ProcessedQuery:
    """Processed query with all enhancements."""
    original: str
    cleaned: str
    expanded: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    intent: ResearchIntent = ResearchIntent.GENERAL_SEARCH
    synonyms: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    temporal_context: Dict[str, Any] = field(default_factory=dict)
    importance_hints: List[str] = field(default_factory=list)
    confidence: float = 1.0


class ResearchQueryProcessor:
    """
    Research-focused query processor that prioritizes completeness and recall.
    """
    
    def __init__(self, events_corpus: Optional[List[Dict[str, Any]]] = None,
                 enable_expansion: bool = True,
                 enable_filtering: bool = True):
        """
        Initialize query processor.
        
        Args:
            events_corpus: Corpus of events for co-occurrence analysis
            enable_expansion: Whether to perform query expansion
            enable_filtering: Whether to extract filters
        """
        self.events_corpus = events_corpus or []
        self.enable_expansion = enable_expansion
        self.enable_filtering = enable_filtering
        
        # Initialize components
        self.intent_classifier = QueryIntentClassifier()
        
        # Build co-occurrence maps from corpus
        self._build_co_occurrence_maps()
        
        # Research-specific patterns
        self._setup_research_patterns()
    
    def process(self, raw_query: str) -> ProcessedQuery:
        """
        Process query with research-focused enhancements.
        
        Args:
            raw_query: Original user query
            
        Returns:
            ProcessedQuery with all enhancements
        """
        logger.debug(f"Processing query: {raw_query}")
        
        # 1. Clean and normalize query
        cleaned = self._clean_query(raw_query)
        
        # 2. Classify research intent
        intent = self.intent_classifier.classify(cleaned)
        
        # 3. Extract filters if enabled
        filters = {}
        if self.enable_filtering:
            filters = self._extract_all_filters(cleaned)
        
        # 4. Expand query if enabled
        expanded = [cleaned]
        synonyms = []
        related_concepts = []
        
        if self.enable_expansion:
            expanded, synonyms, related_concepts = self._expand_comprehensively(cleaned, intent)
        
        # 5. Extract temporal context
        temporal_context = self._extract_temporal_context(cleaned, intent)
        
        # 6. Extract importance hints
        importance_hints = self._extract_importance_hints(cleaned)
        
        # 7. Calculate processing confidence
        confidence = self._calculate_confidence(cleaned, filters, expanded)
        
        processed = ProcessedQuery(
            original=raw_query,
            cleaned=cleaned,
            expanded=expanded,
            filters=filters,
            intent=intent,
            synonyms=synonyms,
            related_concepts=related_concepts,
            temporal_context=temporal_context,
            importance_hints=importance_hints,
            confidence=confidence
        )
        
        logger.debug(f"Processed query: {processed.intent.value}, {len(processed.expanded)} expansions")
        return processed
    
    def _clean_query(self, query: str) -> str:
        """Clean and normalize query text."""
        # Remove extra whitespace
        cleaned = ' '.join(query.strip().split())
        
        # Normalize quotes
        cleaned = re.sub(r'[""]', '"', cleaned)
        
        # Normalize apostrophes
        cleaned = re.sub(r'['']', "'", cleaned)
        
        # Handle common abbreviations
        abbreviations = {
            r'\bUS\b': 'United States',
            r'\bUK\b': 'United Kingdom',
            r'\bEU\b': 'European Union',
            r'\bUSSR\b': 'Soviet Union',
            r'\bGOP\b': 'Republican',
            r'\bDOJ\b': 'Department of Justice',
            r'\bFBI\b': 'Federal Bureau of Investigation',
            r'\bCIA\b': 'Central Intelligence Agency',
            r'\bNSA\b': 'National Security Agency',
            r'\bEPA\b': 'Environmental Protection Agency',
            r'\bSEC\b': 'Securities and Exchange Commission',
            r'\bFTC\b': 'Federal Trade Commission'
        }
        
        for abbr, full in abbreviations.items():
            cleaned = re.sub(abbr, full, cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def _extract_all_filters(self, query: str) -> Dict[str, Any]:
        """Extract all possible filters from query."""
        filters = {}
        
        # Date filters
        date_filters = extract_date_filters(query)
        if date_filters:
            filters.update(date_filters)
        
        # Actor filters
        actor_filters = extract_actor_filters(query, self._get_known_actors())
        if actor_filters:
            filters['actors'] = actor_filters
        
        # Importance filters
        importance_filters = extract_importance_filters(query)
        if importance_filters:
            filters.update(importance_filters)
        
        # Additional metadata filters
        metadata_filters = extract_metadata_filters(query)
        if metadata_filters:
            filters.update(metadata_filters)
        
        return filters
    
    def _expand_comprehensively(self, query: str, intent: ResearchIntent) -> Tuple[List[str], List[str], List[str]]:
        """
        Comprehensively expand query for maximum recall.
        
        Returns:
            Tuple of (expanded_queries, synonyms, related_concepts)
        """
        expanded = [query]
        all_synonyms = []
        all_related = []
        
        # 1. Domain ontology expansion
        domain_expansions = expand_with_domain_ontology(query)
        expanded.extend(domain_expansions)
        
        # 2. Co-occurrence expansion (if corpus available)
        if self.events_corpus:
            cooccurrence_expansions = expand_with_co_occurrence_analysis(query, self.events_corpus)
            expanded.extend(cooccurrence_expansions)
        
        # 3. Temporal context expansion
        temporal_expansions = expand_temporal_context_comprehensively(query)
        expanded.extend(temporal_expansions)
        
        # 4. Capture lane expansion
        capture_expansions = expand_with_capture_lane_synonyms(query)
        expanded.extend(capture_expansions)
        
        # 5. Completeness-focused expansion (research priority)
        completeness_expansions = expand_for_completeness(query)
        expanded.extend(completeness_expansions)
        
        # 6. Intent-specific expansion
        if intent == ResearchIntent.COMPREHENSIVE_SEARCH:
            # More aggressive expansion for comprehensive searches
            expanded.extend(self._expand_for_comprehensiveness(query))
        elif intent == ResearchIntent.TIMELINE_ANALYSIS:
            # Add temporal and causal terms
            expanded.extend(self._expand_for_timeline(query))
        elif intent == ResearchIntent.ACTOR_NETWORK:
            # Add relationship and connection terms
            expanded.extend(self._expand_for_networks(query))
        elif intent == ResearchIntent.PATTERN_DETECTION:
            # Add pattern and trend terms
            expanded.extend(self._expand_for_patterns(query))
        
        # Extract synonyms and related concepts
        all_synonyms = self._extract_synonyms(query)
        all_related = self._extract_related_concepts(query, intent)
        
        # Deduplicate and limit
        expanded = list(dict.fromkeys(expanded))[:20]  # Keep top 20 unique expansions
        
        return expanded, all_synonyms, all_related
    
    def _extract_temporal_context(self, query: str, intent: ResearchIntent) -> Dict[str, Any]:
        """Extract temporal context and hints from query."""
        context = {
            'time_references': [],
            'temporal_scope': 'unspecified',
            'chronological_intent': intent == ResearchIntent.TIMELINE_ANALYSIS,
            'relative_time': None
        }
        
        # Look for time references
        time_patterns = [
            (r'\b(recent|lately|recently)\b', 'recent'),
            (r'\b(current|now|today|present)\b', 'current'),
            (r'\b(past|previous|former|earlier)\b', 'past'),
            (r'\b(future|upcoming|planned)\b', 'future'),
            (r'\b(\d{4})\b', 'year'),
            (r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', 'month'),
            (r'\b(during|since|after|before|until|by)\b', 'temporal_marker')
        ]
        
        for pattern, ref_type in time_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                context['time_references'].extend([(match, ref_type) for match in matches])
        
        # Determine temporal scope
        if any('recent' in ref[0] for ref in context['time_references']):
            context['temporal_scope'] = 'recent'
            context['relative_time'] = datetime.now() - timedelta(days=180)  # 6 months
        elif any('current' in ref[0] for ref in context['time_references']):
            context['temporal_scope'] = 'current'
            context['relative_time'] = datetime.now() - timedelta(days=30)   # 1 month
        elif any(ref[1] == 'year' for ref in context['time_references']):
            context['temporal_scope'] = 'specific_year'
        
        return context
    
    def _extract_importance_hints(self, query: str) -> List[str]:
        """Extract hints about event importance from query."""
        hints = []
        
        importance_patterns = [
            (r'\b(critical|crucial|vital|essential|key|major)\b', 'high_importance'),
            (r'\b(significant|important|notable|substantial)\b', 'medium_importance'),
            (r'\b(minor|small|slight|limited)\b', 'low_importance'),
            (r'\b(breaking|urgent|emergency|crisis)\b', 'urgent'),
            (r'\b(historic|landmark|unprecedented|groundbreaking)\b', 'historic'),
            (r'\b(scandal|controversy|corruption|illegal)\b', 'scandal'),
            (r'\b(primary|main|principal|central)\b', 'primary_focus')
        ]
        
        for pattern, hint_type in importance_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                hints.append(hint_type)
        
        return list(set(hints))  # Remove duplicates
    
    def _calculate_confidence(self, query: str, filters: Dict[str, Any], 
                            expanded: List[str]) -> float:
        """Calculate confidence in query processing."""
        confidence = 1.0
        
        # Penalize very short queries
        if len(query.split()) < 3:
            confidence *= 0.8
        
        # Boost confidence for specific filters
        if filters:
            confidence *= 1.1
        
        # Boost confidence for successful expansion
        if len(expanded) > 3:
            confidence *= 1.05
        
        # Penalize overly complex queries
        if len(query.split()) > 20:
            confidence *= 0.9
        
        return min(confidence, 1.0)
    
    def _build_co_occurrence_maps(self):
        """Build co-occurrence maps from events corpus."""
        self.term_cooccurrence = {}
        
        if not self.events_corpus:
            return
        
        # Extract terms from all events
        all_terms = []
        for event in self.events_corpus:
            # Get text from title, summary, tags, actors
            text_parts = [
                event.get('title', ''),
                event.get('summary', ''),
                ' '.join(event.get('tags', [])),
                ' '.join(event.get('actors', []) if isinstance(event.get('actors', []), list) else [event.get('actors', '')])
            ]
            event_text = ' '.join(text_parts).lower()
            
            # Extract significant terms (3+ chars, not common words)
            terms = re.findall(r'\b[a-zA-Z]{3,}\b', event_text)
            terms = [t for t in terms if t not in self._get_stopwords()]
            all_terms.extend(terms)
        
        # Build co-occurrence matrix (simplified)
        from collections import defaultdict, Counter
        term_counts = Counter(all_terms)
        
        # Keep only terms that appear 3+ times
        significant_terms = {term for term, count in term_counts.items() if count >= 3}
        
        # Build co-occurrence for significant terms
        for event in self.events_corpus:
            text_parts = [
                event.get('title', ''),
                event.get('summary', ''),
                ' '.join(event.get('tags', [])),
                ' '.join(event.get('actors', []) if isinstance(event.get('actors', []), list) else [event.get('actors', '')])
            ]
            event_text = ' '.join(text_parts).lower()
            event_terms = [t for t in re.findall(r'\b[a-zA-Z]{3,}\b', event_text) 
                          if t in significant_terms]
            
            # Record co-occurrences
            for i, term1 in enumerate(event_terms):
                for term2 in event_terms[i+1:]:
                    if term1 != term2:
                        key = tuple(sorted([term1, term2]))
                        if key not in self.term_cooccurrence:
                            self.term_cooccurrence[key] = 0
                        self.term_cooccurrence[key] += 1
    
    def _get_known_actors(self) -> List[str]:
        """Get list of known actors from corpus."""
        if not self.events_corpus:
            return []
        
        actors = set()
        for event in self.events_corpus:
            event_actors = event.get('actors', [])
            if isinstance(event_actors, str):
                actors.add(event_actors)
            elif isinstance(event_actors, list):
                actors.update(event_actors)
        
        return list(actors)
    
    def _setup_research_patterns(self):
        """Setup research-specific patterns and rules."""
        self.research_patterns = {
            'comprehensive_indicators': [
                r'\b(all|every|complete|comprehensive|entire|full)\b',
                r'\b(everything about|anything related to|all instances of)\b'
            ],
            'timeline_indicators': [
                r'\b(timeline|chronology|sequence|progression|development)\b',
                r'\b(how .* developed|evolution of|progression of)\b',
                r'\b(from .* to|between .* and|during the period)\b'
            ],
            'network_indicators': [
                r'\b(connection|relationship|network|association|link)\b',
                r'\b(between .* and|involving .* and|connecting)\b'
            ],
            'pattern_indicators': [
                r'\b(pattern|trend|recurring|systematic|consistent)\b',
                r'\b(similarities|differences|comparison|contrast)\b'
            ]
        }
    
    def _expand_for_comprehensiveness(self, query: str) -> List[str]:
        """Expand query for comprehensive searches."""
        expansions = []
        
        # Add broader terms
        if 'trump' in query.lower():
            expansions.extend(['donald trump', 'president trump', 'trump administration'])
        
        if 'cryptocurrency' in query.lower():
            expansions.extend(['crypto', 'bitcoin', 'digital currency', 'blockchain'])
        
        if 'regulatory' in query.lower():
            expansions.extend(['regulation', 'compliance', 'oversight', 'enforcement'])
        
        return expansions
    
    def _expand_for_timeline(self, query: str) -> List[str]:
        """Expand query for timeline analysis."""
        return [
            f"sequence of {query}",
            f"chronology of {query}", 
            f"development of {query}",
            f"timeline for {query}"
        ]
    
    def _expand_for_networks(self, query: str) -> List[str]:
        """Expand query for network analysis."""
        return [
            f"connections involving {query}",
            f"relationships with {query}",
            f"network of {query}",
            f"associations with {query}"
        ]
    
    def _expand_for_patterns(self, query: str) -> List[str]:
        """Expand query for pattern detection."""
        return [
            f"patterns in {query}",
            f"trends related to {query}",
            f"systematic {query}",
            f"recurring {query}"
        ]
    
    def _extract_synonyms(self, query: str) -> List[str]:
        """Extract domain-specific synonyms."""
        synonyms = []
        
        # Democracy synonyms
        if re.search(r'\b(democracy|democratic)\b', query, re.IGNORECASE):
            synonyms.extend(['democratic institutions', 'democratic process', 'democratic norms'])
        
        # Corruption synonyms
        if re.search(r'\b(corruption|corrupt)\b', query, re.IGNORECASE):
            synonyms.extend(['graft', 'bribery', 'kickbacks', 'pay-to-play', 'quid pro quo'])
        
        # Kleptocracy synonyms
        if re.search(r'\b(kleptocracy|kleptocratic)\b', query, re.IGNORECASE):
            synonyms.extend(['oligarchy', 'crony capitalism', 'rent-seeking', 'state capture'])
        
        return synonyms
    
    def _extract_related_concepts(self, query: str, intent: ResearchIntent) -> List[str]:
        """Extract related concepts based on query and intent."""
        concepts = []
        
        # Use co-occurrence data if available
        query_terms = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        for term in query_terms:
            for (term1, term2), count in self.term_cooccurrence.items():
                if term1 == term and count >= 5:  # Strong co-occurrence
                    concepts.append(term2)
                elif term2 == term and count >= 5:
                    concepts.append(term1)
        
        return list(set(concepts))[:10]  # Top 10 unique concepts
    
    def _get_stopwords(self) -> set:
        """Get stopwords for filtering."""
        return {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall',
            'this', 'that', 'these', 'those', 'a', 'an', 'as', 'if', 'than', 'when', 'where',
            'what', 'who', 'why', 'how', 'which', 'there', 'here', 'then', 'now', 'all', 'any',
            'each', 'every', 'some', 'many', 'much', 'more', 'most', 'other', 'such', 'only'
        }


if __name__ == '__main__':
    # Example usage
    processor = ResearchQueryProcessor()
    
    test_queries = [
        "What events involve cryptocurrency and Trump?",
        "Show me comprehensive evidence of regulatory capture",
        "Timeline of Schedule F implementation",
        "Network analysis of tech oligarchs and policy influence"
    ]
    
    for query in test_queries:
        processed = processor.process(query)
        print(f"\nOriginal: {query}")
        print(f"Intent: {processed.intent.value}")
        print(f"Filters: {processed.filters}")
        print(f"Expansions: {processed.expanded[:3]}...")  # Show first 3
        print(f"Confidence: {processed.confidence:.2f}")