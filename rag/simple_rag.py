#!/usr/bin/env python3
"""
Simple RAG (Retrieval-Augmented Generation) System for Kleptocracy Timeline
Proof of concept implementation using local embeddings and OpenAI API
"""

import os
import json
import yaml
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

# For embeddings and LLM
try:
    import openai
    from sentence_transformers import SentenceTransformer
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("Please install: pip install openai sentence-transformers chromadb")
    exit(1)

class TimelineRAG:
    """
    Simple RAG system for querying timeline events
    """
    
    def __init__(self, 
                 timeline_dir: str = "../timeline_data/events",
                 use_local_embeddings: bool = True,
                 api_key: Optional[str] = None):
        """
        Initialize RAG system
        
        Args:
            timeline_dir: Path to timeline events
            use_local_embeddings: Use local model vs OpenAI embeddings
            api_key: OpenAI API key (optional)
        """
        self.timeline_dir = Path(timeline_dir)
        self.use_local_embeddings = use_local_embeddings
        
        # Initialize embedding model
        if use_local_embeddings:
            # Use local sentence transformers
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            # Use OpenAI embeddings
            openai.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.embedder = None
        
        # Initialize vector store with new API
        try:
            # Try new API first
            self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        except:
            # Fall back to old API if needed
            self.chroma_client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory="./chroma_db"
            ))
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="timeline_events",
            metadata={"description": "Kleptocracy timeline events"}
        )
        
        # Load events
        self.events = self.load_events()
        print(f"Loaded {len(self.events)} events")
        
        # Build index if empty
        if self.collection.count() == 0:
            print("Building vector index...")
            self.build_index()
    
    def load_events(self) -> List[Dict[str, Any]]:
        """Load all timeline events from YAML files"""
        events = []
        
        for yaml_file in self.timeline_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r') as f:
                    event = yaml.safe_load(f)
                    if event:
                        # Add file path for reference
                        event['_file'] = yaml_file.name
                        events.append(event)
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")
        
        return sorted(events, key=lambda x: str(x.get('date', '')))
    
    def create_event_text(self, event: Dict[str, Any]) -> str:
        """
        Create rich text representation of event for embedding
        """
        parts = []
        
        # Add all relevant fields
        parts.append(f"Date: {event.get('date', 'Unknown')}")
        parts.append(f"Event: {event.get('title', 'Untitled')}")
        
        if event.get('summary'):
            parts.append(f"Summary: {event['summary']}")
        
        if event.get('actors'):
            actors = event['actors'] if isinstance(event['actors'], list) else [event['actors']]
            parts.append(f"Actors: {', '.join(actors)}")
        
        if event.get('tags'):
            tags = event['tags'] if isinstance(event['tags'], list) else [event['tags']]
            parts.append(f"Tags: {', '.join(tags)}")
        
        if event.get('location'):
            parts.append(f"Location: {event['location']}")
        
        if event.get('status'):
            parts.append(f"Verification Status: {event['status']}")
        
        if event.get('notes'):
            parts.append(f"Context: {event['notes']}")
        
        return "\n".join(parts)
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if self.use_local_embeddings:
            # Local model
            embedding = self.embedder.encode(text)
            return embedding.tolist()
        else:
            # OpenAI API
            response = openai.Embedding.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response['data'][0]['embedding']
    
    def build_index(self):
        """Build vector index from all events"""
        
        documents = []
        embeddings = []
        metadatas = []
        ids = []
        
        for i, event in enumerate(self.events):
            # Create text representation
            text = self.create_event_text(event)
            
            # Generate embedding
            embedding = self.generate_embedding(text)
            
            # Prepare metadata
            metadata = {
                "date": str(event.get('date', '')),
                "title": event.get('title', ''),
                "status": event.get('status', 'unknown'),
                "file": event.get('_file', ''),
                "has_sources": len(event.get('sources', [])) > 0
            }
            
            # Add tags and actors as metadata
            if event.get('tags'):
                tags = event['tags'] if isinstance(event['tags'], list) else [event['tags']]
                metadata['tags'] = ', '.join(tags)
            
            if event.get('actors'):
                actors = event['actors'] if isinstance(event['actors'], list) else [event['actors']]
                metadata['actors'] = ', '.join(actors)
            
            documents.append(text)
            embeddings.append(embedding)
            metadatas.append(metadata)
            ids.append(event.get('id', f"event_{i}"))
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Indexed {len(documents)} events")
    
    def search(self, 
               query: str, 
               n_results: int = 10,
               filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant events
        
        Args:
            query: Search query
            n_results: Number of results to return
            filters: Optional metadata filters
        
        Returns:
            List of relevant events with scores
        """
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Search vector store
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            event_id = results['ids'][0][i]
            
            # Find original event
            event = next((e for e in self.events if e.get('id') == event_id), None)
            
            if event:
                formatted_results.append({
                    'event': event,
                    'score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'metadata': results['metadatas'][0][i]
                })
        
        return formatted_results
    
    def answer_question(self, 
                       question: str, 
                       max_events: int = 5,
                       use_llm: bool = True) -> Dict[str, Any]:
        """
        Answer a question using RAG
        
        Args:
            question: User question
            max_events: Maximum events to use as context
            use_llm: Whether to use LLM for answer generation
        
        Returns:
            Answer with sources
        """
        # Search for relevant events
        results = self.search(question, n_results=max_events)
        
        if not results:
            return {
                'answer': "No relevant events found in the timeline.",
                'events': [],
                'sources': []
            }
        
        # Format context
        context_parts = []
        event_ids = []
        sources = []
        
        for r in results:
            event = r['event']
            event_ids.append(event.get('id', 'unknown'))
            
            # Format event for context
            event_text = f"""
Event ID: {event.get('id', 'unknown')}
Date: {event.get('date', 'unknown')}
Title: {event.get('title', 'unknown')}
Summary: {event.get('summary', 'No summary')}
Status: {event.get('status', 'unknown')}
"""
            context_parts.append(event_text)
            
            # Collect sources
            for source in event.get('sources', []):
                if isinstance(source, dict):
                    sources.append(source.get('url', source.get('title', 'Unknown source')))
                else:
                    sources.append(str(source))
        
        context = "\n---\n".join(context_parts)
        
        if use_llm and not self.use_local_embeddings:
            # Generate answer using OpenAI
            prompt = f"""Based on the following verified timeline events, answer the question.
Only use information from the provided events. If the information is not available, say so.
Include specific dates, names, and event IDs in your answer.

Timeline Events:
{context}

Question: {question}

Answer (be specific and cite event IDs):"""
            
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a research assistant helping analyze kleptocracy timeline data. Only use information from the provided events."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                answer = response.choices[0].message.content
            except Exception as e:
                answer = f"LLM generation failed: {e}. See events below for relevant information."
        else:
            # Simple answer without LLM
            answer = f"Found {len(results)} relevant events. See details below."
        
        return {
            'answer': answer,
            'events': event_ids,
            'sources': list(set(sources)),  # Deduplicate
            'context_events': [r['event'] for r in results]
        }
    
    def find_patterns(self, 
                     actor: Optional[str] = None,
                     tag: Optional[str] = None,
                     date_range: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Find patterns in the timeline
        
        Args:
            actor: Specific actor to analyze
            tag: Specific tag to analyze
            date_range: (start_date, end_date) tuple
        
        Returns:
            Pattern analysis
        """
        # Filter events
        filtered_events = self.events
        
        if actor:
            filtered_events = [
                e for e in filtered_events 
                if actor in str(e.get('actors', []))
            ]
        
        if tag:
            filtered_events = [
                e for e in filtered_events 
                if tag in str(e.get('tags', []))
            ]
        
        if date_range:
            start, end = date_range
            filtered_events = [
                e for e in filtered_events 
                if start <= e.get('date', '') <= end
            ]
        
        # Analyze patterns
        patterns = {
            'total_events': len(filtered_events),
            'date_range': {
                'earliest': min((str(e.get('date', '')) for e in filtered_events), default='N/A') if filtered_events else 'N/A',
                'latest': max((str(e.get('date', '')) for e in filtered_events), default='N/A') if filtered_events else 'N/A'
            },
            'top_actors': self._count_field(filtered_events, 'actors'),
            'top_tags': self._count_field(filtered_events, 'tags'),
            'status_breakdown': self._count_field(filtered_events, 'status'),
            'events_by_month': self._group_by_month(filtered_events)
        }
        
        return patterns
    
    def _count_field(self, events: List[Dict], field: str) -> Dict[str, int]:
        """Count occurrences of field values"""
        counts = {}
        
        for event in events:
            value = event.get(field)
            if value:
                if isinstance(value, list):
                    for item in value:
                        counts[item] = counts.get(item, 0) + 1
                else:
                    counts[value] = counts.get(value, 0) + 1
        
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def _group_by_month(self, events: List[Dict]) -> Dict[str, int]:
        """Group events by month"""
        months = {}
        
        for event in events:
            date = str(event.get('date', ''))
            if date and len(date) >= 7:
                month = date[:7]  # YYYY-MM
                months[month] = months.get(month, 0) + 1
        
        return dict(sorted(months.items()))


def main():
    """Example usage"""
    
    # Initialize RAG system
    print("Initializing Timeline RAG System...")
    rag = TimelineRAG(
        timeline_dir="../timeline_data/events",
        use_local_embeddings=True  # Use local model, no API key needed
    )
    
    # Example queries
    queries = [
        "What events involve cryptocurrency and Trump?",
        "What happened with Epstein files in 2025?",
        "Show me events about regulatory capture",
        "What executive orders were signed in January 2025?"
    ]
    
    print("\n" + "="*60)
    print("EXAMPLE QUERIES")
    print("="*60)
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        # Get answer
        result = rag.answer_question(query, max_events=3, use_llm=False)
        
        print(f"Answer: {result['answer']}")
        print(f"Relevant Events: {', '.join(result['events'][:3])}")
        print(f"Sources: {len(result['sources'])} sources found")
    
    # Pattern analysis example
    print("\n" + "="*60)
    print("PATTERN ANALYSIS: Cryptocurrency Events")
    print("="*60)
    
    patterns = rag.find_patterns(tag='cryptocurrency')
    print(f"Total crypto events: {patterns['total_events']}")
    print(f"Date range: {patterns['date_range']['earliest']} to {patterns['date_range']['latest']}")
    print(f"Top actors: {list(patterns['top_actors'].keys())[:5]}")
    
    # Interactive mode
    print("\n" + "="*60)
    print("INTERACTIVE MODE (type 'quit' to exit)")
    print("="*60)
    
    while True:
        query = input("\nYour question: ").strip()
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not query:
            continue
        
        result = rag.answer_question(query, max_events=5, use_llm=False)
        print(f"\nAnswer: {result['answer']}")
        
        if result['events']:
            print(f"\nRelevant events:")
            for event_id in result['events'][:3]:
                print(f"  - {event_id}")
        
        if result['sources']:
            print(f"\nSources:")
            for source in result['sources'][:3]:
                print(f"  - {source}")


if __name__ == "__main__":
    main()