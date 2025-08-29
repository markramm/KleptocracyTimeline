#!/usr/bin/env python3
"""
Enhanced RAG System with Query Expansion and Re-ranking

Improvements over basic RAG:
1. Query expansion for better recall
2. Multi-stage re-ranking for better precision
3. Hybrid search (semantic + keyword)
4. Semantic query understanding
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import hashlib
import re
from collections import Counter, defaultdict

import numpy as np
from sentence_transformers import SentenceTransformer, util
import chromadb
from chromadb.config import Settings

# Import the base Event class
from real_rag_system import Event


class QueryExpander:
    """Expands queries to improve recall."""
    
    def __init__(self):
        """Initialize query expander with synonym mappings."""
        self.synonyms = {
            'trump': ['donald trump', 'president trump', 'former president'],
            'crypto': ['cryptocurrency', 'bitcoin', 'digital assets', 'blockchain'],
            'schedule f': ['schedule-f', 'civil service', 'federal workforce'],
            'democracy': ['democratic', 'democratic institutions', 'voting rights', 'elections'],
            'corruption': ['corrupt', 'bribery', 'graft', 'kickbacks', 'pay-to-play'],
            'regulatory': ['regulation', 'deregulation', 'regulatory capture'],
            'judicial': ['courts', 'judges', 'judiciary', 'supreme court'],
            'media': ['press', 'journalism', 'news', 'broadcasting'],
            'foreign': ['international', 'saudi', 'russia', 'china', 'overseas'],
            'executive': ['executive order', 'presidential', 'white house'],
        }
        
        self.concept_expansions = {
            'authoritarianism': ['autocracy', 'dictatorship', 'tyranny', 'totalitarian'],
            'kleptocracy': ['theft', 'pillaging', 'looting', 'embezzlement'],
            'oligarchy': ['plutocracy', 'billionaires', 'wealth concentration'],
            'capture': ['control', 'takeover', 'domination', 'influence'],
        }
    
    def expand_query(self, query: str) -> List[str]:
        """
        Expand query with synonyms and related terms.
        
        Args:
            query: Original query text
            
        Returns:
            List of expanded query variations
        """
        expanded_queries = [query]
        query_lower = query.lower()
        
        # Add synonym expansions
        for key, synonyms in self.synonyms.items():
            if key in query_lower:
                for synonym in synonyms:
                    expanded = query_lower.replace(key, synonym)
                    expanded_queries.append(expanded)
        
        # Add concept expansions
        for concept, expansions in self.concept_expansions.items():
            if concept in query_lower:
                for expansion in expansions:
                    expanded_queries.append(f"{query} {expansion}")
        
        # Add temporal variations
        if 'recent' in query_lower:
            expanded_queries.append(query.replace('recent', '2025'))
            expanded_queries.append(query.replace('recent', 'latest'))
        
        # Add question variations
        if query.startswith('What'):
            expanded_queries.append(query.replace('What', 'Show'))
            expanded_queries.append(query.replace('What', 'Find'))
        elif query.startswith('Show'):
            expanded_queries.append(query.replace('Show', 'What'))
            expanded_queries.append(query.replace('Show', 'Find'))
        
        return list(set(expanded_queries))


class SemanticReranker:
    """Re-ranks results using semantic similarity."""
    
    def __init__(self, model: SentenceTransformer):
        """Initialize with embedding model."""
        self.model = model
    
    def rerank(self, query: str, results: List[Dict], top_k: int = 20) -> List[Dict]:
        """
        Re-rank results based on semantic similarity.
        
        Args:
            query: Query text
            results: Initial search results
            top_k: Number of results to return
            
        Returns:
            Re-ranked results
        """
        if not results:
            return results
        
        # Encode query
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        
        # Prepare result texts and encode
        result_texts = []
        for result in results:
            if 'event' in result:
                event = result['event']
                text = f"{event.get('title', '')} {event.get('summary', '')}"
            else:
                text = str(result)
            result_texts.append(text)
        
        result_embeddings = self.model.encode(result_texts, convert_to_tensor=True)
        
        # Calculate similarities
        similarities = util.cos_sim(query_embedding, result_embeddings)[0]
        
        # Sort by similarity
        sorted_indices = similarities.argsort(descending=True)
        
        # Return re-ranked results
        reranked = []
        for idx in sorted_indices[:top_k]:
            result = results[idx.item()].copy()
            result['rerank_score'] = similarities[idx].item()
            reranked.append(result)
        
        return reranked


class MetadataBooster:
    """Boosts results based on metadata signals."""
    
    def boost_scores(self, results: List[Dict], query: str) -> List[Dict]:
        """
        Apply metadata-based boosting to results.
        
        Args:
            results: Search results
            query: Query text
            
        Returns:
            Results with adjusted scores
        """
        query_lower = query.lower()
        boosted_results = []
        
        for result in results:
            boost_factor = 1.0
            
            if 'event' in result:
                event = result['event']
                
                # Boost by importance
                importance = event.get('importance', 5)
                boost_factor *= (1 + importance / 20)
                
                # Boost by date relevance
                if '2025' in query_lower and '2025' in str(event.get('date', '')):
                    boost_factor *= 1.3
                elif 'recent' in query_lower:
                    date_str = event.get('date', '')
                    if date_str.startswith('2025'):
                        boost_factor *= 1.2
                
                # Boost by source count
                sources = event.get('sources', [])
                if len(sources) >= 3:
                    boost_factor *= 1.1
                
                # Boost by tag matching
                tags = event.get('tags', [])
                query_words = set(query_lower.split())
                tag_words = set(' '.join(tags).lower().split('-'))
                if query_words & tag_words:
                    boost_factor *= 1.2
                
                # Apply boost
                result = result.copy()
                original_score = result.get('relevance_score', 0.5)
                result['boosted_score'] = original_score * boost_factor
                result['boost_factor'] = boost_factor
            
            boosted_results.append(result)
        
        # Sort by boosted score
        boosted_results.sort(key=lambda x: x.get('boosted_score', 0), reverse=True)
        return boosted_results


class EnhancedRAGSystem:
    """Enhanced RAG system with multiple improvements."""
    
    def __init__(self, data_path: str = None):
        """Initialize enhanced RAG system."""
        self.data_path = Path(data_path or "../timeline_data/timeline_complete.json")
        self.events: List[Event] = []
        self.event_dict: Dict[str, Event] = {}
        
        # Initialize components
        print("Initializing Enhanced RAG System...")
        self._load_data()
        
        # Initialize embedding model
        print("Loading embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize vector store
        self._initialize_vector_store()
        
        # Initialize enhancement components
        self.query_expander = QueryExpander()
        self.reranker = SemanticReranker(self.model)
        self.metadata_booster = MetadataBooster()
        
        # Build keyword index for hybrid search
        self._build_keyword_index()
    
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
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db_enhanced")
        
        # Create collection
        collection_name = "enhanced_timeline"
        
        # Delete existing collection
        try:
            self.chroma_client.delete_collection(collection_name)
        except:
            pass
        
        self.collection = self.chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Index events
        print(f"Indexing {len(self.events)} events...")
        batch_size = 100
        
        for i in range(0, len(self.events), batch_size):
            batch = self.events[i:i+batch_size]
            
            # Prepare batch data
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
            
            # Add to collection
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
        print("Building keyword index...")
        self.keyword_index = defaultdict(set)
        
        for event in self.events:
            # Index title words
            title_words = re.findall(r'\w+', event.title.lower())
            for word in title_words:
                if len(word) > 2:  # Skip short words
                    self.keyword_index[word].add(event.id)
            
            # Index summary words
            summary_words = re.findall(r'\w+', event.summary.lower())
            for word in summary_words[:50]:  # Limit to first 50 words
                if len(word) > 2:
                    self.keyword_index[word].add(event.id)
            
            # Index tags
            for tag in event.tags:
                tag_words = tag.lower().split('-')
                for word in tag_words:
                    if len(word) > 2:
                        self.keyword_index[word].add(event.id)
            
            # Index actors
            for actor in event.actors:
                actor_words = re.findall(r'\w+', actor.lower())
                for word in actor_words:
                    if len(word) > 2:
                        self.keyword_index[word].add(event.id)
        
        print(f"Built keyword index with {len(self.keyword_index)} terms")
    
    def keyword_search(self, query: str, top_k: int = 50) -> List[str]:
        """
        Perform keyword-based search.
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            List of event IDs
        """
        query_words = re.findall(r'\w+', query.lower())
        query_words = [w for w in query_words if len(w) > 2]
        
        # Count matches for each event
        event_scores = Counter()
        
        for word in query_words:
            # Direct match
            if word in self.keyword_index:
                for event_id in self.keyword_index[word]:
                    event_scores[event_id] += 2
            
            # Prefix match
            for term in self.keyword_index:
                if term.startswith(word) or word.startswith(term):
                    for event_id in self.keyword_index[term]:
                        event_scores[event_id] += 1
        
        # Get top events
        top_events = event_scores.most_common(top_k)
        return [event_id for event_id, _ in top_events]
    
    def semantic_search(self, query: str, top_k: int = 50) -> List[Dict]:
        """
        Perform semantic search using embeddings.
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            Search results
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i, event_id in enumerate(results['ids'][0]):
                result = {
                    'event_id': event_id,
                    'semantic_score': 1.0 - results['distances'][0][i],  # Convert distance to similarity
                    'metadata': results['metadatas'][0][i]
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def hybrid_search(self, query: str, top_k: int = 50) -> List[Dict]:
        """
        Perform hybrid search combining keyword and semantic.
        
        Args:
            query: Query text
            top_k: Number of results
            
        Returns:
            Combined search results
        """
        # Get keyword results
        keyword_ids = self.keyword_search(query, top_k)
        
        # Get semantic results
        semantic_results = self.semantic_search(query, top_k)
        semantic_dict = {r['event_id']: r['semantic_score'] for r in semantic_results}
        
        # Combine scores
        combined_scores = {}
        
        # Add keyword scores
        for i, event_id in enumerate(keyword_ids):
            keyword_score = 1.0 - (i / len(keyword_ids)) if keyword_ids else 0
            combined_scores[event_id] = {
                'keyword_score': keyword_score,
                'semantic_score': semantic_dict.get(event_id, 0),
                'combined_score': 0
            }
        
        # Add semantic scores
        for event_id, semantic_score in semantic_dict.items():
            if event_id not in combined_scores:
                combined_scores[event_id] = {
                    'keyword_score': 0,
                    'semantic_score': semantic_score,
                    'combined_score': 0
                }
            else:
                combined_scores[event_id]['semantic_score'] = semantic_score
        
        # Calculate combined scores (weighted average)
        keyword_weight = 0.3
        semantic_weight = 0.7
        
        for event_id, scores in combined_scores.items():
            scores['combined_score'] = (
                keyword_weight * scores['keyword_score'] +
                semantic_weight * scores['semantic_score']
            )
        
        # Sort by combined score
        sorted_events = sorted(
            combined_scores.items(),
            key=lambda x: x[1]['combined_score'],
            reverse=True
        )[:top_k]
        
        # Format results
        results = []
        for event_id, scores in sorted_events:
            if event_id in self.event_dict:
                result = {
                    'event': self.event_dict[event_id].__dict__,
                    'relevance_score': scores['combined_score'],
                    'keyword_score': scores['keyword_score'],
                    'semantic_score': scores['semantic_score']
                }
                results.append(result)
        
        return results
    
    def search(self, query: str, top_k: int = 20, use_expansion: bool = True,
               use_reranking: bool = True, use_boosting: bool = True) -> List[Dict]:
        """
        Enhanced search with all improvements.
        
        Args:
            query: Query text
            top_k: Number of results to return
            use_expansion: Whether to use query expansion
            use_reranking: Whether to use semantic re-ranking
            use_boosting: Whether to use metadata boosting
            
        Returns:
            Search results
        """
        print(f"\nEnhanced search for: '{query}'")
        start_time = time.time()
        
        # Step 1: Query expansion
        if use_expansion:
            expanded_queries = self.query_expander.expand_query(query)
            print(f"  Expanded to {len(expanded_queries)} query variations")
        else:
            expanded_queries = [query]
        
        # Step 2: Hybrid search for each query
        all_results = []
        seen_ids = set()
        
        for exp_query in expanded_queries[:3]:  # Limit to top 3 expansions
            results = self.hybrid_search(exp_query, top_k * 2)
            for result in results:
                event_id = result['event']['id']
                if event_id not in seen_ids:
                    all_results.append(result)
                    seen_ids.add(event_id)
        
        print(f"  Found {len(all_results)} unique results from hybrid search")
        
        # Step 3: Metadata boosting
        if use_boosting:
            all_results = self.metadata_booster.boost_scores(all_results, query)
            print(f"  Applied metadata boosting")
        
        # Step 4: Semantic re-ranking
        if use_reranking and len(all_results) > 0:
            all_results = self.reranker.rerank(query, all_results, top_k * 2)
            print(f"  Applied semantic re-ranking")
        
        # Step 5: Final scoring and selection
        final_results = all_results[:top_k]
        
        search_time = time.time() - start_time
        print(f"  Completed in {search_time:.3f}s, returning {len(final_results)} results")
        
        return final_results


def main():
    """Test the enhanced RAG system."""
    # Initialize
    rag = EnhancedRAGSystem("../timeline_data/timeline_complete.json")
    
    # Test queries
    test_queries = [
        "What events involve cryptocurrency and Trump?",
        "Show timeline of Schedule F implementation",
        "Events threatening democracy",
    ]
    
    for query in test_queries:
        results = rag.search(query, top_k=5)
        print(f"\nQuery: {query}")
        print(f"Results: {len(results)}")
        for i, result in enumerate(results[:3]):
            event = result['event']
            print(f"  {i+1}. {event['title'][:80]}")
            print(f"     Score: {result.get('boosted_score', result.get('relevance_score', 0)):.3f}")


if __name__ == '__main__':
    main()