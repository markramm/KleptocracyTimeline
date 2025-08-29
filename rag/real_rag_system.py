#!/usr/bin/env python3
"""
Real RAG System for Kleptocracy Timeline

This is an ACTUAL working RAG system, not a simulation.
It uses real data, real embeddings, and real retrieval.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib

# We'll use sentence-transformers for embeddings
# and implement a simple vector store (or use ChromaDB if available)
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    print("WARNING: sentence-transformers not installed. Install with:")
    print("pip install sentence-transformers")
    EMBEDDINGS_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    print("WARNING: ChromaDB not installed. Install with:")
    print("pip install chromadb")
    CHROMADB_AVAILABLE = False


@dataclass
class Event:
    """Represents a timeline event."""
    id: str
    date: str
    title: str
    summary: str
    actors: List[str]
    tags: List[str]
    importance: int
    sources: List[Dict[str, str]]
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        return cls(
            id=data.get('id', ''),
            date=data.get('date', ''),
            title=data.get('title', ''),
            summary=data.get('summary', ''),
            actors=data.get('actors', []),
            tags=data.get('tags', []),
            importance=data.get('importance', 5),
            sources=data.get('sources', [])
        )
    
    def to_text(self) -> str:
        """Convert event to searchable text."""
        parts = [
            f"Date: {self.date}",
            f"Title: {self.title}",
            f"Summary: {self.summary}",
            f"Actors: {', '.join(self.actors)}",
            f"Tags: {', '.join(self.tags)}",
            f"Importance: {self.importance}"
        ]
        return '\n'.join(parts)


class RealRAGSystem:
    """A real RAG system with actual retrieval capabilities."""
    
    def __init__(self, data_path: str = None):
        """Initialize the RAG system with real data."""
        self.data_path = Path(data_path or "timeline_data/timeline_complete.json")
        self.events: List[Event] = []
        self.embeddings = None
        self.model = None
        self.chroma_client = None
        self.collection = None
        
        # Initialize components
        self._load_data()
        self._initialize_embeddings()
        self._initialize_vector_store()
    
    def _load_data(self):
        """Load real timeline data from JSON file."""
        print(f"Loading data from {self.data_path}...")
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        with open(self.data_path, 'r') as f:
            raw_data = json.load(f)
        
        # Convert to Event objects
        self.events = [Event.from_dict(item) for item in raw_data]
        print(f"Loaded {len(self.events)} events")
    
    def _initialize_embeddings(self):
        """Initialize the embedding model."""
        if not EMBEDDINGS_AVAILABLE:
            print("Embeddings not available. Using keyword search only.")
            return
        
        print("Initializing embedding model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded successfully")
    
    def _initialize_vector_store(self):
        """Initialize vector store and create embeddings."""
        if not CHROMADB_AVAILABLE or not EMBEDDINGS_AVAILABLE:
            print("Using fallback in-memory search")
            self._create_fallback_index()
            return
        
        print("Initializing ChromaDB...")
        
        # Initialize ChromaDB client (new API)
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        
        # Create or get collection
        collection_name = "kleptocracy_timeline"
        
        # Delete existing collection if it exists (for fresh index)
        try:
            self.chroma_client.delete_collection(collection_name)
        except:
            pass
        
        self.collection = self.chroma_client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"Indexing {len(self.events)} events...")
        
        # Process in batches for efficiency
        batch_size = 100
        for i in range(0, len(self.events), batch_size):
            batch = self.events[i:i+batch_size]
            
            # Prepare batch data
            documents = [event.to_text() for event in batch]
            ids = [event.id for event in batch]
            metadatas = [
                {
                    'date': event.date,
                    'title': event.title,
                    'importance': event.importance,
                    'actors': json.dumps(event.actors),
                    'tags': json.dumps(event.tags)
                }
                for event in batch
            ]
            
            # Generate embeddings
            embeddings = self.model.encode(documents).tolist()
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"  Indexed {min(i+batch_size, len(self.events))}/{len(self.events)} events")
        
        print("Vector store initialized successfully")
    
    def _create_fallback_index(self):
        """Create simple keyword index for fallback search."""
        print("Creating fallback keyword index...")
        self.keyword_index = {}
        
        for event in self.events:
            # Extract keywords from event
            text = event.to_text().lower()
            words = text.split()
            
            for word in words:
                if len(word) > 2:  # Skip short words
                    if word not in self.keyword_index:
                        self.keyword_index[word] = []
                    if event.id not in self.keyword_index[word]:
                        self.keyword_index[word].append(event.id)
        
        print(f"Keyword index created with {len(self.keyword_index)} terms")
    
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Perform actual retrieval on real data.
        
        Returns real results with real relevance scores.
        """
        print(f"\nSearching for: '{query}'")
        start_time = time.time()
        
        if self.collection:
            # Use ChromaDB for semantic search
            results = self._semantic_search(query, top_k)
        else:
            # Use fallback keyword search
            results = self._keyword_search(query, top_k)
        
        search_time = time.time() - start_time
        print(f"Found {len(results)} results in {search_time:.3f}s")
        
        return results
    
    def _semantic_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform semantic search using ChromaDB."""
        # Generate query embedding
        query_embedding = self.model.encode([query])[0].tolist()
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            event_id = results['ids'][0][i]
            event = next((e for e in self.events if e.id == event_id), None)
            
            if event:
                formatted_results.append({
                    'event': event.__dict__,
                    'relevance_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'metadata': results['metadatas'][0][i]
                })
        
        return formatted_results
    
    def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform fallback keyword search."""
        query_words = query.lower().split()
        event_scores = {}
        
        # Score events based on keyword matches
        for word in query_words:
            if word in self.keyword_index:
                for event_id in self.keyword_index[word]:
                    if event_id not in event_scores:
                        event_scores[event_id] = 0
                    event_scores[event_id] += 1
        
        # Sort by score and get top k
        sorted_events = sorted(event_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Format results
        results = []
        for event_id, score in sorted_events:
            event = next((e for e in self.events if e.id == event_id), None)
            if event:
                results.append({
                    'event': event.__dict__,
                    'relevance_score': score / len(query_words),  # Normalize score
                    'metadata': {
                        'match_count': score,
                        'query_terms': len(query_words)
                    }
                })
        
        return results
    
    def evaluate_retrieval(self, test_queries: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Evaluate retrieval performance with real metrics.
        
        test_queries should be a list of dicts with:
        - query: the search query
        - relevant_ids: list of event IDs that are truly relevant
        """
        total_precision_5 = 0
        total_precision_10 = 0
        total_recall = 0
        total_mrr = 0
        
        for test_case in test_queries:
            query = test_case['query']
            relevant_ids = set(test_case['relevant_ids'])
            
            # Perform search
            results = self.search(query, top_k=10)
            retrieved_ids = [r['event']['id'] for r in results]
            
            # Calculate precision@5
            retrieved_5 = retrieved_ids[:5]
            precision_5 = len([r for r in retrieved_5 if r in relevant_ids]) / 5
            total_precision_5 += precision_5
            
            # Calculate precision@10
            precision_10 = len([r for r in retrieved_ids if r in relevant_ids]) / 10
            total_precision_10 += precision_10
            
            # Calculate recall
            if len(relevant_ids) > 0:
                recall = len([r for r in retrieved_ids if r in relevant_ids]) / len(relevant_ids)
                total_recall += recall
            
            # Calculate MRR (Mean Reciprocal Rank)
            for i, rid in enumerate(retrieved_ids, 1):
                if rid in relevant_ids:
                    total_mrr += 1/i
                    break
        
        n = len(test_queries)
        return {
            'precision_at_5': total_precision_5 / n,
            'precision_at_10': total_precision_10 / n,
            'recall': total_recall / n,
            'mrr': total_mrr / n,
            'queries_tested': n
        }


def create_test_dataset() -> List[Dict[str, Any]]:
    """
    Create a test dataset with queries and known relevant events.
    
    This is based on REAL events in the timeline data.
    """
    test_queries = [
        {
            'query': 'Roger Ailes Fox News creation media',
            'relevant_ids': [
                '1970-01-01--ailes-nixon-gop-tv-network-plan',
                # Add more relevant IDs based on actual data
            ]
        },
        {
            'query': 'Trump executive orders Schedule F federal workforce',
            'relevant_ids': [
                # Add IDs of events about Schedule F
            ]
        },
        {
            'query': 'regulatory capture appointments agencies',
            'relevant_ids': [
                # Add IDs of events about regulatory capture
            ]
        }
    ]
    
    return test_queries


def main():
    """Run the real RAG system."""
    print("="*60)
    print("REAL RAG SYSTEM - Not a Simulation!")
    print("="*60)
    
    # Initialize the system with real data
    rag = RealRAGSystem('../timeline_data/timeline_complete.json')
    
    # Run some test queries
    test_queries = [
        "Roger Ailes Fox News media creation",
        "Trump Schedule F federal employees",
        "regulatory capture appointments",
        "democracy threats institutional capture",
        "cryptocurrency launches market manipulation"
    ]
    
    print("\n" + "="*60)
    print("RUNNING TEST SEARCHES")
    print("="*60)
    
    for query in test_queries:
        results = rag.search(query, top_k=5)
        
        print(f"\nQuery: '{query}'")
        print("-" * 40)
        
        for i, result in enumerate(results, 1):
            event = result['event']
            score = result['relevance_score']
            
            print(f"\n{i}. [{score:.3f}] {event['title']}")
            print(f"   Date: {event['date']}")
            print(f"   Tags: {', '.join(event['tags'][:3])}")
            
            # Show snippet of summary
            summary = event['summary']
            if len(summary) > 100:
                summary = summary[:100] + "..."
            print(f"   Summary: {summary}")
    
    # If we have test data, run evaluation
    # test_dataset = create_test_dataset()
    # metrics = rag.evaluate_retrieval(test_dataset)
    # print("\nEvaluation Metrics:")
    # for metric, value in metrics.items():
    #     print(f"  {metric}: {value:.3f}")


if __name__ == "__main__":
    main()