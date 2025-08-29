#!/usr/bin/env python3
"""
Optimized RAG System with Tuned Parameters

Key optimizations:
1. Selective query expansion (only for low-recall query types)
2. Balanced hybrid search weights
3. Smart re-ranking based on query intent
4. Caching for performance
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import hashlib
import re
from collections import Counter, defaultdict

import numpy as np
from sentence_transformers import SentenceTransformer, util
import chromadb

from real_rag_system import Event
from enhanced_rag_system import QueryExpander, MetadataBooster


class QueryClassifier:
    """Classifies queries to determine optimal search strategy."""
    
    def classify(self, query: str) -> Dict[str, Any]:
        """
        Classify query and return search parameters.
        
        Args:
            query: Query text
            
        Returns:
            Dictionary with search strategy parameters
        """
        query_lower = query.lower()
        
        # Default parameters
        params = {
            'use_expansion': False,
            'use_reranking': True,
            'use_boosting': True,
            'keyword_weight': 0.3,
            'semantic_weight': 0.7,
            'expansion_limit': 2
        }
        
        # Entity queries - high precision needed
        if any(word in query_lower for word in ['trump', 'elon', 'epstein', 'specific person']):
            params['use_expansion'] = False
            params['keyword_weight'] = 0.5
            params['semantic_weight'] = 0.5
        
        # Temporal queries - date boosting important
        elif any(word in query_lower for word in ['2025', 'january', 'recent', 'timeline', 'when']):
            params['use_expansion'] = False
            params['use_boosting'] = True
            params['keyword_weight'] = 0.4
        
        # Pattern/comprehensive queries - need recall
        elif any(word in query_lower for word in ['pattern', 'comprehensive', 'all', 'analysis']):
            params['use_expansion'] = True
            params['expansion_limit'] = 3
            params['semantic_weight'] = 0.8
        
        # Negative queries - special handling
        elif 'not' in query_lower or 'without' in query_lower:
            params['use_expansion'] = False
            params['use_reranking'] = False
        
        # Complex multi-concept queries
        elif len(query.split()) > 10:
            params['use_expansion'] = True
            params['expansion_limit'] = 2
            params['semantic_weight'] = 0.6
        
        return params


class OptimizedRAGSystem:
    """Optimized RAG system with smart parameter tuning."""
    
    def __init__(self, data_path: str = None):
        """Initialize optimized RAG system."""
        self.data_path = Path(data_path or "../timeline_data/timeline_complete.json")
        self.events: List[Event] = []
        self.event_dict: Dict[str, Event] = {}
        
        # Caches
        self.search_cache = {}
        self.embedding_cache = {}
        
        # Initialize components
        print("Initializing Optimized RAG System...")
        self._load_data()
        
        # Initialize embedding model
        print("Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize vector store
        self._initialize_vector_store()
        
        # Initialize components
        self.query_classifier = QueryClassifier()
        self.query_expander = QueryExpander()
        self.metadata_booster = MetadataBooster()
        
        # Build indices
        self._build_keyword_index()
        self._build_tag_index()
    
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
        
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db_optimized")
        
        collection_name = "optimized_timeline"
        
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
        
        print("Vector store initialized")
    
    def _build_keyword_index(self):
        """Build inverted index for keyword search."""
        self.keyword_index = defaultdict(set)
        
        for event in self.events:
            # Index title with higher weight
            title_words = re.findall(r'\w+', event.title.lower())
            for word in title_words:
                if len(word) > 2:
                    self.keyword_index[word].add(event.id)
            
            # Index summary
            summary_words = re.findall(r'\w+', event.summary.lower())
            for word in summary_words[:30]:
                if len(word) > 2:
                    self.keyword_index[word].add(event.id)
    
    def _build_tag_index(self):
        """Build tag index for fast filtering."""
        self.tag_index = defaultdict(set)
        
        for event in self.events:
            for tag in event.tags:
                self.tag_index[tag].add(event.id)
    
    def keyword_search(self, query: str, top_k: int = 50) -> List[Tuple[str, float]]:
        """
        Perform keyword search with scoring.
        
        Returns:
            List of (event_id, score) tuples
        """
        query_words = re.findall(r'\w+', query.lower())
        query_words = [w for w in query_words if len(w) > 2]
        
        event_scores = Counter()
        
        for word in query_words:
            # Exact matches get higher score
            if word in self.keyword_index:
                for event_id in self.keyword_index[word]:
                    event = self.event_dict[event_id]
                    # Boost score based on word location
                    if word in event.title.lower():
                        event_scores[event_id] += 3
                    else:
                        event_scores[event_id] += 1
        
        # Normalize scores
        if event_scores:
            max_score = max(event_scores.values())
            normalized = [(eid, score/max_score) for eid, score in event_scores.most_common(top_k)]
            return normalized
        
        return []
    
    def semantic_search(self, query: str, top_k: int = 50) -> List[Tuple[str, float]]:
        """
        Perform semantic search.
        
        Returns:
            List of (event_id, score) tuples
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        formatted = []
        if results['ids'] and results['ids'][0]:
            for i, event_id in enumerate(results['ids'][0]):
                score = 1.0 - results['distances'][0][i]
                formatted.append((event_id, score))
        
        return formatted
    
    def smart_rerank(self, query: str, results: List[Dict], top_k: int = 20) -> List[Dict]:
        """
        Smart re-ranking based on query intent.
        
        Args:
            query: Query text
            results: Initial results
            top_k: Number to return
            
        Returns:
            Re-ranked results
        """
        if not results:
            return results
        
        query_lower = query.lower()
        
        # Calculate composite scores
        for result in results:
            event = result['event']
            score = result.get('relevance_score', 0.5)
            
            # Title match boost
            if any(word in event['title'].lower() for word in query_lower.split()):
                score *= 1.3
            
            # Date relevance
            if '2025' in query_lower and '2025' in event.get('date', ''):
                score *= 1.2
            
            # Importance boost (but not too much)
            importance = event.get('importance', 5)
            score *= (1 + importance / 30)
            
            # Source quality
            sources = event.get('sources', [])
            if len(sources) >= 3:
                score *= 1.1
            
            result['final_score'] = score
        
        # Sort by final score
        results.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        return results[:top_k]
    
    def search(self, query: str, top_k: int = 20) -> List[Dict]:
        """
        Optimized search with smart parameter selection.
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            Search results
        """
        # Check cache
        cache_key = hashlib.md5(f"{query}:{top_k}".encode()).hexdigest()
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        start_time = time.time()
        
        # Classify query and get parameters
        params = self.query_classifier.classify(query)
        
        # Query expansion if needed
        if params['use_expansion']:
            expanded = self.query_expander.expand_query(query)
            queries = expanded[:params['expansion_limit']]
        else:
            queries = [query]
        
        # Collect results
        all_results = {}
        
        for q in queries:
            # Keyword search
            keyword_results = self.keyword_search(q, top_k * 2)
            
            # Semantic search
            semantic_results = self.semantic_search(q, top_k * 2)
            
            # Combine scores
            for event_id, k_score in keyword_results:
                if event_id not in all_results:
                    all_results[event_id] = {
                        'keyword_score': 0,
                        'semantic_score': 0
                    }
                all_results[event_id]['keyword_score'] = max(
                    all_results[event_id]['keyword_score'],
                    k_score
                )
            
            for event_id, s_score in semantic_results:
                if event_id not in all_results:
                    all_results[event_id] = {
                        'keyword_score': 0,
                        'semantic_score': 0
                    }
                all_results[event_id]['semantic_score'] = max(
                    all_results[event_id]['semantic_score'],
                    s_score
                )
        
        # Calculate combined scores
        results = []
        for event_id, scores in all_results.items():
            if event_id in self.event_dict:
                combined = (
                    params['keyword_weight'] * scores['keyword_score'] +
                    params['semantic_weight'] * scores['semantic_score']
                )
                
                result = {
                    'event': self.event_dict[event_id].__dict__,
                    'relevance_score': combined,
                    'keyword_score': scores['keyword_score'],
                    'semantic_score': scores['semantic_score']
                }
                results.append(result)
        
        # Apply boosting if needed
        if params['use_boosting']:
            results = self.metadata_booster.boost_scores(results, query)
        
        # Smart re-ranking if needed
        if params['use_reranking']:
            results = self.smart_rerank(query, results, top_k * 2)
        
        # Select top results
        final_results = results[:top_k]
        
        # Cache results
        self.search_cache[cache_key] = final_results
        
        search_time = time.time() - start_time
        print(f"Optimized search completed in {search_time:.3f}s")
        
        return final_results


def main():
    """Test optimized system."""
    rag = OptimizedRAGSystem("../timeline_data/timeline_complete.json")
    
    test_queries = [
        "What events involve cryptocurrency and Trump?",
        "Show timeline of Schedule F implementation",
        "Events threatening democracy",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = rag.search(query, top_k=5)
        print(f"Results: {len(results)}")
        for i, result in enumerate(results[:3]):
            event = result['event']
            print(f"  {i+1}. {event['title'][:80]}")
            print(f"     Score: {result.get('final_score', result.get('relevance_score', 0)):.3f}")


if __name__ == '__main__':
    main()