#!/usr/bin/env python3
"""
Advanced RAG System with Learning-to-Rank and Temporal Reasoning

Advanced features:
1. Learning-to-rank with multiple features
2. Temporal reasoning and date understanding
3. Iterative retrieval with pseudo-relevance feedback
4. Query intent detection and routing
5. Advanced filtering and negation handling
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import re
from collections import Counter, defaultdict
import math

import numpy as np
from sentence_transformers import SentenceTransformer, util
import chromadb

from real_rag_system import Event


@dataclass
class RankingFeatures:
    """Features for learning-to-rank."""
    
    # Text similarity features
    title_exact_match: float = 0.0
    title_partial_match: float = 0.0
    summary_match: float = 0.0
    semantic_similarity: float = 0.0
    keyword_overlap: float = 0.0
    
    # Metadata features
    importance_score: float = 0.0
    recency_score: float = 0.0
    source_quality: float = 0.0
    source_count: float = 0.0
    
    # Temporal features
    date_match: float = 0.0
    date_proximity: float = 0.0
    temporal_relevance: float = 0.0
    
    # Entity features
    actor_match: float = 0.0
    tag_match: float = 0.0
    tag_overlap: float = 0.0
    
    # Query-document features
    query_length_ratio: float = 0.0
    doc_length: float = 0.0
    query_doc_similarity: float = 0.0
    
    def to_vector(self) -> np.ndarray:
        """Convert features to numpy vector."""
        return np.array([
            self.title_exact_match,
            self.title_partial_match,
            self.summary_match,
            self.semantic_similarity,
            self.keyword_overlap,
            self.importance_score,
            self.recency_score,
            self.source_quality,
            self.source_count,
            self.date_match,
            self.date_proximity,
            self.temporal_relevance,
            self.actor_match,
            self.tag_match,
            self.tag_overlap,
            self.query_length_ratio,
            self.doc_length,
            self.query_doc_similarity
        ])


class TemporalReasoner:
    """Handles temporal reasoning and date understanding."""
    
    def __init__(self):
        """Initialize temporal reasoner."""
        self.month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        self.temporal_keywords = {
            'recent': 90,  # days
            'latest': 30,
            'current': 30,
            'this year': 365,
            'last year': -365,
            'past month': 30,
            'past week': 7
        }
    
    def extract_date_range(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Extract date range from query.
        
        Args:
            query: Query text
            
        Returns:
            Tuple of (start_date, end_date) or None
        """
        query_lower = query.lower()
        
        # Check for year mentions
        year_pattern = r'\b(20\d{2})\b'
        years = re.findall(year_pattern, query)
        
        if years:
            year = years[0]
            
            # Check for month
            for month_name, month_num in self.month_map.items():
                if month_name in query_lower:
                    # Specific month and year
                    start = f"{year}-{month_num:02d}-01"
                    if month_num == 12:
                        end = f"{year}-12-31"
                    else:
                        end = f"{year}-{month_num+1:02d}-01"
                    return (start, end)
            
            # Just year
            return (f"{year}-01-01", f"{year}-12-31")
        
        # Check for temporal keywords
        for keyword, days in self.temporal_keywords.items():
            if keyword in query_lower:
                today = datetime.now()
                if days > 0:
                    start = (today - timedelta(days=days)).strftime("%Y-%m-%d")
                    end = today.strftime("%Y-%m-%d")
                else:
                    start = (today + timedelta(days=days)).strftime("%Y-%m-%d")
                    end = today.strftime("%Y-%m-%d")
                return (start, end)
        
        return None
    
    def calculate_temporal_relevance(self, event_date: str, query_date_range: Optional[Tuple[str, str]]) -> float:
        """
        Calculate temporal relevance score.
        
        Args:
            event_date: Event date
            query_date_range: Query date range if any
            
        Returns:
            Relevance score between 0 and 1
        """
        if not query_date_range:
            return 0.5  # Neutral score if no temporal component
        
        start, end = query_date_range
        
        # Check if event is within range
        if start <= event_date <= end:
            return 1.0
        
        # Calculate proximity
        try:
            event_dt = datetime.strptime(event_date[:10], "%Y-%m-%d")
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            end_dt = datetime.strptime(end, "%Y-%m-%d")
            
            # Days outside range
            if event_dt < start_dt:
                days_diff = (start_dt - event_dt).days
            else:
                days_diff = (event_dt - end_dt).days
            
            # Decay function
            return max(0, 1.0 - (days_diff / 365))  # Linear decay over a year
        except:
            return 0.5


class QueryIntentDetector:
    """Detects query intent and type."""
    
    def detect_intent(self, query: str) -> Dict[str, Any]:
        """
        Detect query intent and characteristics.
        
        Args:
            query: Query text
            
        Returns:
            Intent information
        """
        query_lower = query.lower()
        words = query_lower.split()
        
        intent = {
            'type': 'general',
            'requires_all': False,
            'requires_exact': False,
            'is_negative': False,
            'is_comparative': False,
            'is_analytical': False,
            'target_entities': [],
            'target_concepts': []
        }
        
        # Question type detection
        if query_lower.startswith('what'):
            intent['type'] = 'factual'
        elif query_lower.startswith('how'):
            intent['type'] = 'procedural'
        elif query_lower.startswith('why'):
            intent['type'] = 'causal'
        elif query_lower.startswith('when'):
            intent['type'] = 'temporal'
        elif query_lower.startswith('who'):
            intent['type'] = 'entity'
        elif 'show' in words or 'find' in words or 'list' in words:
            intent['type'] = 'retrieval'
        
        # Modifiers
        if 'all' in words:
            intent['requires_all'] = True
        if 'exact' in words or 'specific' in words:
            intent['requires_exact'] = True
        if 'not' in words or 'without' in words or 'except' in words:
            intent['is_negative'] = True
        if 'compare' in words or 'versus' in words or 'between' in words:
            intent['is_comparative'] = True
        if 'analyze' in words or 'pattern' in words or 'trend' in words:
            intent['is_analytical'] = True
        
        # Extract entities (simple NER)
        # Look for capitalized words that might be names
        for word in query.split():
            if word[0].isupper() and word.lower() not in ['what', 'when', 'where', 'how', 'why']:
                intent['target_entities'].append(word)
        
        # Extract concepts
        concepts = ['democracy', 'corruption', 'cryptocurrency', 'regulation', 'media', 'judicial']
        for concept in concepts:
            if concept in query_lower:
                intent['target_concepts'].append(concept)
        
        return intent


class LearningToRanker:
    """Learning-to-rank model for result ranking."""
    
    def __init__(self):
        """Initialize ranker."""
        # Feature weights (learned or tuned)
        self.weights = np.array([
            3.0,   # title_exact_match
            2.0,   # title_partial_match
            1.5,   # summary_match
            2.5,   # semantic_similarity
            1.0,   # keyword_overlap
            0.8,   # importance_score
            0.6,   # recency_score
            0.7,   # source_quality
            0.5,   # source_count
            2.0,   # date_match
            1.0,   # date_proximity
            1.5,   # temporal_relevance
            1.8,   # actor_match
            1.5,   # tag_match
            1.2,   # tag_overlap
            0.3,   # query_length_ratio
            0.2,   # doc_length
            1.5    # query_doc_similarity
        ])
    
    def extract_features(self, query: str, event: Dict, 
                        query_embedding: np.ndarray = None,
                        query_date_range: Optional[Tuple[str, str]] = None) -> RankingFeatures:
        """
        Extract ranking features for a query-document pair.
        
        Args:
            query: Query text
            event: Event dictionary
            query_embedding: Pre-computed query embedding
            query_date_range: Date range from query
            
        Returns:
            RankingFeatures object
        """
        features = RankingFeatures()
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        # Title matching
        title_lower = event.get('title', '').lower()
        if query_lower in title_lower:
            features.title_exact_match = 1.0
        else:
            title_words = set(title_lower.split())
            overlap = len(query_words & title_words)
            features.title_partial_match = overlap / len(query_words) if query_words else 0
        
        # Summary matching
        summary_lower = event.get('summary', '').lower()
        summary_words = set(summary_lower.split())
        features.summary_match = len(query_words & summary_words) / len(query_words) if query_words else 0
        
        # Keyword overlap
        doc_words = title_words | summary_words
        features.keyword_overlap = len(query_words & doc_words) / len(query_words | doc_words) if (query_words | doc_words) else 0
        
        # Metadata features
        features.importance_score = event.get('importance', 5) / 10.0
        
        # Date features
        event_date = event.get('date', '')
        if event_date:
            # Recency (assumes 2025 is current)
            if event_date.startswith('2025'):
                features.recency_score = 1.0
            elif event_date.startswith('2024'):
                features.recency_score = 0.7
            else:
                features.recency_score = 0.3
            
            # Date matching
            if any(year in query for year in ['2025', '2024', '2023']):
                if any(year in event_date for year in query.split()):
                    features.date_match = 1.0
        
        # Source features
        sources = event.get('sources', [])
        features.source_count = min(len(sources) / 5.0, 1.0)  # Normalize to max 5
        features.source_quality = 1.0 if len(sources) >= 3 else 0.5
        
        # Actor matching
        actors = event.get('actors', [])
        if actors:
            actor_text = ' '.join(actors).lower()
            if any(word in actor_text for word in query_words):
                features.actor_match = 1.0
        
        # Tag matching
        tags = event.get('tags', [])
        if tags:
            tag_text = ' '.join(tags).lower()
            tag_words = set(tag_text.replace('-', ' ').split())
            features.tag_overlap = len(query_words & tag_words) / len(query_words) if query_words else 0
            if any(tag in query_lower for tag in tags):
                features.tag_match = 1.0
        
        # Length features
        doc_length = len(title_lower.split()) + len(summary_lower.split())
        features.doc_length = min(doc_length / 200.0, 1.0)  # Normalize
        features.query_length_ratio = len(query_words) / (doc_length + 1)
        
        return features
    
    def rank(self, features: RankingFeatures) -> float:
        """
        Calculate ranking score from features.
        
        Args:
            features: RankingFeatures object
            
        Returns:
            Ranking score
        """
        feature_vector = features.to_vector()
        return np.dot(self.weights, feature_vector)


class AdvancedRAGSystem:
    """Advanced RAG system with all sophisticated features."""
    
    def __init__(self, data_path: str = None):
        """Initialize advanced RAG system."""
        self.data_path = Path(data_path or "../timeline_data/timeline_complete.json")
        self.events: List[Event] = []
        self.event_dict: Dict[str, Event] = {}
        
        # Initialize components
        print("Initializing Advanced RAG System...")
        self._load_data()
        
        # Initialize models and indices
        print("Loading models...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._initialize_vector_store()
        self._build_indices()
        
        # Initialize advanced components
        self.temporal_reasoner = TemporalReasoner()
        self.intent_detector = QueryIntentDetector()
        self.ranker = LearningToRanker()
        
        # Caches
        self.embedding_cache = {}
        self.search_cache = {}
    
    def _load_data(self):
        """Load timeline data."""
        print(f"Loading data from {self.data_path}...")
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        with open(self.data_path, 'r') as f:
            raw_data = json.load(f)
        
        self.events = [Event.from_dict(item) for item in raw_data]
        self.event_dict = {event.id: event for event in self.events}
        print(f"Loaded {len(self.events)} events")
    
    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store."""
        print("Initializing vector store...")
        
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db_advanced")
        
        collection_name = "advanced_timeline"
        
        try:
            self.chroma_client.delete_collection(collection_name)
        except:
            pass
        
        self.collection = self.chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"Indexing {len(self.events)} events...")
        batch_size = 100
        
        for i in range(0, len(self.events), batch_size):
            batch = self.events[i:i+batch_size]
            
            ids = [event.id for event in batch]
            documents = [event.to_text() for event in batch]
            metadatas = [
                {
                    'title': event.title,
                    'date': event.date,
                    'importance': event.importance,
                    'actors': json.dumps(event.actors),
                    'tags': json.dumps(event.tags)
                }
                for event in batch
            ]
            
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            if (i + batch_size) % 100 == 0:
                print(f"  Indexed {min(i + batch_size, len(self.events))}/{len(self.events)} events")
    
    def _build_indices(self):
        """Build various indices for fast lookup."""
        print("Building indices...")
        
        # Keyword index
        self.keyword_index = defaultdict(set)
        
        # Date index
        self.date_index = defaultdict(set)
        
        # Actor index
        self.actor_index = defaultdict(set)
        
        # Tag index
        self.tag_index = defaultdict(set)
        
        for event in self.events:
            # Keywords
            words = re.findall(r'\w+', f"{event.title} {event.summary}".lower())
            for word in words:
                if len(word) > 2:
                    self.keyword_index[word].add(event.id)
            
            # Dates
            if event.date:
                year = event.date[:4]
                month = event.date[:7]
                self.date_index[year].add(event.id)
                self.date_index[month].add(event.id)
            
            # Actors
            for actor in event.actors:
                actor_words = re.findall(r'\w+', actor.lower())
                for word in actor_words:
                    self.actor_index[word].add(event.id)
            
            # Tags
            for tag in event.tags:
                self.tag_index[tag].add(event.id)
    
    def iterative_retrieval(self, query: str, initial_results: List[Dict], 
                          iterations: int = 2) -> List[Dict]:
        """
        Perform iterative retrieval with pseudo-relevance feedback.
        
        Args:
            query: Original query
            initial_results: Initial search results
            iterations: Number of feedback iterations
            
        Returns:
            Enhanced results
        """
        if not initial_results or iterations <= 0:
            return initial_results
        
        results = initial_results.copy()
        
        for iteration in range(iterations):
            # Take top results as pseudo-relevant
            top_k = min(3, len(results))
            pseudo_relevant = results[:top_k]
            
            # Extract expansion terms from pseudo-relevant docs
            expansion_terms = Counter()
            
            for result in pseudo_relevant:
                event = result['event']
                
                # Extract keywords from title and summary
                text = f"{event.get('title', '')} {event.get('summary', '')}"
                words = re.findall(r'\w+', text.lower())
                
                for word in words:
                    if len(word) > 3 and word not in query.lower():
                        expansion_terms[word] += 1
                
                # Add important tags
                for tag in event.get('tags', []):
                    expansion_terms[tag] += 2
            
            # Get top expansion terms
            top_terms = [term for term, _ in expansion_terms.most_common(5)]
            
            if not top_terms:
                break
            
            # Create expanded query
            expanded_query = f"{query} {' '.join(top_terms)}"
            
            # Search with expanded query
            expanded_results = self._basic_search(expanded_query, top_k=30)
            
            # Merge results
            seen_ids = {r['event']['id'] for r in results}
            
            for result in expanded_results:
                if result['event']['id'] not in seen_ids:
                    results.append(result)
                    seen_ids.add(result['event']['id'])
        
        return results
    
    def _basic_search(self, query: str, top_k: int = 50) -> List[Dict]:
        """
        Basic search without advanced features.
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            Search results
        """
        # Semantic search
        semantic_results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        results = []
        if semantic_results['ids'] and semantic_results['ids'][0]:
            for i, event_id in enumerate(semantic_results['ids'][0]):
                if event_id in self.event_dict:
                    result = {
                        'event': self.event_dict[event_id].__dict__,
                        'semantic_score': 1.0 - semantic_results['distances'][0][i]
                    }
                    results.append(result)
        
        return results
    
    def apply_negative_filtering(self, results: List[Dict], query: str) -> List[Dict]:
        """
        Apply negative filtering for NOT queries.
        
        Args:
            results: Initial results
            query: Query text
            
        Returns:
            Filtered results
        """
        query_lower = query.lower()
        
        # Extract negative terms
        negative_terms = []
        
        # Pattern: "not X" or "without X"
        not_pattern = r'\bnot\s+(\w+)'
        without_pattern = r'\bwithout\s+(\w+)'
        
        not_matches = re.findall(not_pattern, query_lower)
        without_matches = re.findall(without_pattern, query_lower)
        
        negative_terms.extend(not_matches)
        negative_terms.extend(without_matches)
        
        if not negative_terms:
            return results
        
        # Filter results
        filtered = []
        
        for result in results:
            event = result['event']
            event_text = f"{event.get('title', '')} {event.get('summary', '')}".lower()
            
            # Check if any negative term is present
            contains_negative = any(term in event_text for term in negative_terms)
            
            if not contains_negative:
                filtered.append(result)
        
        return filtered
    
    def search(self, query: str, top_k: int = 20) -> List[Dict]:
        """
        Advanced search with all features.
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            Search results
        """
        start_time = time.time()
        
        # Detect intent
        intent = self.intent_detector.detect_intent(query)
        
        # Extract temporal information
        date_range = self.temporal_reasoner.extract_date_range(query)
        
        # Get query embedding
        query_embedding = self.model.encode(query, convert_to_tensor=False)
        
        # Initial retrieval
        initial_results = self._basic_search(query, top_k * 3)
        
        # Apply iterative retrieval if analytical query
        if intent['is_analytical']:
            initial_results = self.iterative_retrieval(query, initial_results, iterations=2)
        
        # Apply negative filtering if needed
        if intent['is_negative']:
            initial_results = self.apply_negative_filtering(initial_results, query)
        
        # Extract features and rank
        ranked_results = []
        
        for result in initial_results:
            event = result['event']
            
            # Extract ranking features
            features = self.ranker.extract_features(
                query, event, query_embedding, date_range
            )
            
            # Add temporal relevance
            if date_range:
                features.temporal_relevance = self.temporal_reasoner.calculate_temporal_relevance(
                    event.get('date', ''), date_range
                )
            
            # Calculate final score
            score = self.ranker.rank(features)
            
            result['ranking_score'] = score
            result['features'] = features
            ranked_results.append(result)
        
        # Sort by ranking score
        ranked_results.sort(key=lambda x: x['ranking_score'], reverse=True)
        
        # Select top k
        final_results = ranked_results[:top_k]
        
        search_time = time.time() - start_time
        print(f"Advanced search completed in {search_time:.3f}s")
        
        return final_results


def main():
    """Test advanced RAG system."""
    rag = AdvancedRAGSystem("../timeline_data/timeline_complete.json")
    
    test_queries = [
        "What happened in January 2025?",
        "Show recent events about democracy not involving Trump",
        "Compare cryptocurrency events between 2024 and 2025",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = rag.search(query, top_k=5)
        print(f"Results: {len(results)}")
        
        for i, result in enumerate(results[:3]):
            event = result['event']
            print(f"  {i+1}. {event['title'][:80]}")
            print(f"     Score: {result.get('ranking_score', 0):.3f}")
            print(f"     Date: {event.get('date', 'N/A')}")


if __name__ == '__main__':
    main()