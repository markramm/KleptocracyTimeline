"""
Query Intent Classification for Research

Classify research queries into specific intent categories to optimize retrieval strategies.
"""

import re
from enum import Enum
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class ResearchIntent(Enum):
    """Research-specific query intent categories."""
    GENERAL_SEARCH = "general_search"
    COMPREHENSIVE_SEARCH = "comprehensive_search"
    TIMELINE_ANALYSIS = "timeline_analysis"
    ACTOR_NETWORK = "actor_network"
    PATTERN_DETECTION = "pattern_detection"
    GAP_ANALYSIS = "gap_analysis"
    COMPARATIVE_ANALYSIS = "comparative"
    CAUSAL_ANALYSIS = "causal_analysis"
    ESCALATION_TRACKING = "escalation_tracking"
    VALIDATION_QUERY = "validation_query"
    FACTUAL_LOOKUP = "factual_lookup"
    RELATIONSHIP_MAPPING = "relationship_mapping"
    TEMPORAL_SPECIFIC = "temporal_specific"
    IMPORTANCE_FILTER = "importance_filter"


@dataclass
class IntentClassificationResult:
    """Result of intent classification."""
    intent: ResearchIntent
    confidence: float
    evidence: List[str]  # Text patterns that led to classification
    secondary_intents: List[Tuple[ResearchIntent, float]]  # Alternative intents with scores


class QueryIntentClassifier:
    """
    Classify research queries into specific intent categories.
    """
    
    def __init__(self):
        """Initialize classifier with research patterns."""
        self._setup_intent_patterns()
    
    def classify(self, query: str) -> ResearchIntent:
        """
        Classify query intent.
        
        Args:
            query: Natural language query
            
        Returns:
            ResearchIntent enum value
        """
        result = self.classify_detailed(query)
        return result.intent
    
    def classify_detailed(self, query: str) -> IntentClassificationResult:
        """
        Classify query intent with detailed results.
        
        Args:
            query: Natural language query
            
        Returns:
            IntentClassificationResult with confidence and evidence
        """
        query_lower = query.lower()
        
        # Score each intent
        intent_scores = {}
        intent_evidence = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            evidence = []
            
            for pattern, weight in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    score += weight
                    evidence.append(pattern)
            
            if score > 0:
                intent_scores[intent] = score
                intent_evidence[intent] = evidence
        
        # Determine primary intent
        if not intent_scores:
            primary_intent = ResearchIntent.GENERAL_SEARCH
            confidence = 0.5
            evidence = []
        else:
            primary_intent = max(intent_scores.keys(), key=lambda k: intent_scores[k])
            max_score = intent_scores[primary_intent]
            confidence = min(1.0, max_score / 10.0)  # Normalize to 0-1
            evidence = intent_evidence[primary_intent]
        
        # Get secondary intents
        secondary_intents = []
        for intent, score in intent_scores.items():
            if intent != primary_intent and score > 2:
                secondary_confidence = min(1.0, score / 10.0)
                secondary_intents.append((intent, secondary_confidence))
        
        # Sort secondary intents by confidence
        secondary_intents.sort(key=lambda x: x[1], reverse=True)
        secondary_intents = secondary_intents[:3]  # Top 3 alternatives
        
        return IntentClassificationResult(
            intent=primary_intent,
            confidence=confidence,
            evidence=evidence,
            secondary_intents=secondary_intents
        )
    
    def _setup_intent_patterns(self):
        """Setup patterns for each research intent."""
        
        self.intent_patterns = {
            ResearchIntent.COMPREHENSIVE_SEARCH: [
                (r'\b(all|every|complete|comprehensive|entire|full)\b', 3),
                (r'\b(everything about|anything related to|all instances of)\b', 4),
                (r'\b(comprehensive analysis|complete picture|full scope)\b', 5),
                (r'\b(any mention of|all occurrences|complete list)\b', 3),
                (r'\b(exhaustive|thorough|in-depth)\b', 2)
            ],
            
            ResearchIntent.TIMELINE_ANALYSIS: [
                (r'\b(timeline|chronology|sequence|progression|development)\b', 4),
                (r'\b(how .* developed|evolution of|progression of)\b', 5),
                (r'\b(from .* to|between .* and|during the period)\b', 3),
                (r'\b(over time|through time|temporal analysis)\b', 4),
                (r'\b(historical development|sequence of events)\b', 5),
                (r'\b(chronological|temporal order|time series)\b', 3),
                (r'\b(step by step|phase by phase|stage by stage)\b', 2)
            ],
            
            ResearchIntent.ACTOR_NETWORK: [
                (r'\b(connection|relationship|network|association|link)\b', 3),
                (r'\b(between .* and|involving .* and|connecting)\b', 4),
                (r'\b(ties|bonds|relationships|associations)\b', 2),
                (r'\b(network analysis|relationship mapping)\b', 5),
                (r'\b(who is connected to|how .* relates to)\b', 4),
                (r'\b(collaborations?|partnerships?|alliances?)\b', 2)
            ],
            
            ResearchIntent.PATTERN_DETECTION: [
                (r'\b(pattern|trend|recurring|systematic|consistent)\b', 4),
                (r'\b(similarities|differences|comparison|contrast)\b', 3),
                (r'\b(common theme|recurring theme|repeated)\b', 4),
                (r'\b(systematic approach|consistent behavior)\b', 5),
                (r'\b(what patterns|identify trends|detect patterns)\b', 5),
                (r'\b(similar cases|analogous situations)\b', 3)
            ],
            
            ResearchIntent.GAP_ANALYSIS: [
                (r'\b(missing|gap|absent|lacking|overlooked)\b', 4),
                (r'\b(what.*missing|what.*not|what.*absent)\b', 5),
                (r'\b(coverage gap|blind spot|unexplored)\b', 5),
                (r'\b(underreported|underrepresented|neglected)\b', 4),
                (r'\b(might.*missing|could.*missing|potential gaps)\b', 4)
            ],
            
            ResearchIntent.COMPARATIVE_ANALYSIS: [
                (r'\b(compare|comparison|versus|vs\.?|against)\b', 4),
                (r'\b(difference between|similarities between)\b', 5),
                (r'\b(compared to|in contrast to|relative to)\b', 4),
                (r'\b(side by side|head to head|comparative)\b', 4),
                (r'\b(how.*differ|how.*similar|contrast with)\b', 3)
            ],
            
            ResearchIntent.CAUSAL_ANALYSIS: [
                (r'\b(caused by|led to|resulted in|because of)\b', 4),
                (r'\b(what caused|what led to|why did)\b', 5),
                (r'\b(consequences of|impact of|effect of)\b', 4),
                (r'\b(causal|causation|cause and effect)\b', 5),
                (r'\b(root cause|underlying cause|driving factor)\b', 4),
                (r'\b(what were the consequences|what resulted)\b', 3)
            ],
            
            ResearchIntent.ESCALATION_TRACKING: [
                (r'\b(escalat|intensif|worsen|deepen|heighten)\b', 4),
                (r'\b(how.*escalated|degree of escalation)\b', 5),
                (r'\b(increasing|growing|expanding|spreading)\b', 2),
                (r'\b(escalation of|intensification of)\b', 5),
                (r'\b(track.*progress|monitor.*development)\b', 3)
            ],
            
            ResearchIntent.VALIDATION_QUERY: [
                (r'\b(verified|confirmed|validated|authentic)\b', 3),
                (r'\b(fact.check|verify|validate|confirm)\b', 4),
                (r'\b(is it true|is this accurate|can you confirm)\b', 5),
                (r'\b(reliable source|credible|trustworthy)\b', 3),
                (r'\b(evidence for|proof of|documentation of)\b', 4),
                (r'\b(cross-reference|corroborate|substantiate)\b', 4)
            ],
            
            ResearchIntent.FACTUAL_LOOKUP: [
                (r'\b(when did|where did|who was|what was|how many)\b', 4),
                (r'\b(date of|time of|location of|details of)\b', 3),
                (r'\b(specific details|exact information|precise data)\b', 4),
                (r'^\s*(what|when|where|who|how|which)\b', 3),  # Question starters
                (r'\b(facts about|information about|details on)\b', 2)
            ],
            
            ResearchIntent.RELATIONSHIP_MAPPING: [
                (r'\b(related to|connected to|associated with)\b', 2),
                (r'\b(relationship between|connection between)\b', 4),
                (r'\b(how.*related|how.*connected|map.*relationship)\b', 4),
                (r'\b(interdependence|interconnection|correlation)\b', 4),
                (r'\b(web of|network of|matrix of)\b', 3)
            ],
            
            ResearchIntent.TEMPORAL_SPECIFIC: [
                (r'\b(\d{4}|\d{1,2}/\d{1,2}/\d{4})\b', 3),  # Specific dates/years
                (r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}\b', 4),
                (r'\b(recent|recently|current|now|today|yesterday)\b', 2),
                (r'\b(last\s+(week|month|year)|past\s+(week|month|year))\b', 3),
                (r'\b(since|after|before|until|during)\s+\d{4}\b', 4)
            ],
            
            ResearchIntent.IMPORTANCE_FILTER: [
                (r'\b(critical|crucial|vital|essential|key|major)\b', 3),
                (r'\b(most important|highest priority|top priority)\b', 4),
                (r'\b(significant|important|notable|substantial)\b', 2),
                (r'\b(breaking|urgent|emergency|crisis)\b', 4),
                (r'\b(historic|landmark|unprecedented|groundbreaking)\b', 3),
                (r'\b(priority|high.priority|top.tier)\b', 3)
            ]
        }
    
    def get_intent_description(self, intent: ResearchIntent) -> str:
        """Get human-readable description of intent."""
        descriptions = {
            ResearchIntent.GENERAL_SEARCH: "General search for information",
            ResearchIntent.COMPREHENSIVE_SEARCH: "Comprehensive search prioritizing completeness",
            ResearchIntent.TIMELINE_ANALYSIS: "Analysis of events over time",
            ResearchIntent.ACTOR_NETWORK: "Mapping relationships between actors",
            ResearchIntent.PATTERN_DETECTION: "Identifying patterns and trends",
            ResearchIntent.GAP_ANALYSIS: "Finding gaps in coverage or information",
            ResearchIntent.COMPARATIVE_ANALYSIS: "Comparing different entities or situations",
            ResearchIntent.CAUSAL_ANALYSIS: "Understanding causes and effects",
            ResearchIntent.ESCALATION_TRACKING: "Tracking escalation of issues",
            ResearchIntent.VALIDATION_QUERY: "Verifying or validating information",
            ResearchIntent.FACTUAL_LOOKUP: "Looking up specific facts or details",
            ResearchIntent.RELATIONSHIP_MAPPING: "Mapping relationships between entities",
            ResearchIntent.TEMPORAL_SPECIFIC: "Search within specific time periods",
            ResearchIntent.IMPORTANCE_FILTER: "Filtering by importance or priority"
        }
        return descriptions.get(intent, "Unknown intent")
    
    def get_search_strategy_hints(self, intent: ResearchIntent) -> Dict[str, Any]:
        """Get search strategy hints based on intent."""
        strategies = {
            ResearchIntent.COMPREHENSIVE_SEARCH: {
                'expand_aggressively': True,
                'prioritize_recall': True,
                'use_all_synonyms': True,
                'max_results': 50
            },
            ResearchIntent.TIMELINE_ANALYSIS: {
                'sort_by_date': True,
                'include_temporal_context': True,
                'group_by_time': True,
                'max_results': 30
            },
            ResearchIntent.ACTOR_NETWORK: {
                'include_relationship_terms': True,
                'expand_actor_names': True,
                'boost_network_events': True,
                'max_results': 25
            },
            ResearchIntent.PATTERN_DETECTION: {
                'cluster_similar': True,
                'look_for_repetition': True,
                'boost_recurring_themes': True,
                'max_results': 40
            },
            ResearchIntent.FACTUAL_LOOKUP: {
                'prioritize_precision': True,
                'boost_confirmed_events': True,
                'prefer_primary_sources': True,
                'max_results': 10
            },
            ResearchIntent.TEMPORAL_SPECIFIC: {
                'strict_date_filtering': True,
                'sort_by_date': True,
                'include_date_context': True,
                'max_results': 20
            },
            ResearchIntent.IMPORTANCE_FILTER: {
                'boost_high_importance': True,
                'filter_by_significance': True,
                'prioritize_critical_events': True,
                'max_results': 15
            }
        }
        
        # Default strategy
        default_strategy = {
            'expand_moderately': True,
            'balanced_precision_recall': True,
            'max_results': 20
        }
        
        return strategies.get(intent, default_strategy)


if __name__ == '__main__':
    # Test intent classification
    classifier = QueryIntentClassifier()
    
    test_queries = [
        "What events involve cryptocurrency and Trump?",  # General search
        "Show me comprehensive evidence of regulatory capture",  # Comprehensive
        "Timeline of Schedule F implementation",  # Timeline
        "Network analysis of tech oligarchs and policy influence",  # Network
        "What patterns exist in media manipulation campaigns?",  # Pattern
        "Compare regulatory capture under Trump vs Biden",  # Comparative
        "What caused the increase in federal workforce firings?",  # Causal
        "How has media control escalated since 2025?",  # Escalation
        "When did Trump sign the Schedule F executive order?",  # Factual lookup
        "Critical events about judicial capture",  # Importance filter
        "What connections exist between Musk and regulatory agencies?",  # Relationship
        "Events in January 2025",  # Temporal specific
        "Can you verify the Epstein files were released?",  # Validation
        "What aspects of crypto regulation are underreported?"  # Gap analysis
    ]
    
    for query in test_queries:
        result = classifier.classify_detailed(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {result.intent.value} (confidence: {result.confidence:.2f})")
        print(f"Description: {classifier.get_intent_description(result.intent)}")
        print(f"Strategy: {classifier.get_search_strategy_hints(result.intent)}")
        if result.secondary_intents:
            print(f"Secondary: {[(i.value, c) for i, c in result.secondary_intents]}")