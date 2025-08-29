"""
Semantic Retrieval Component

Enhanced semantic similarity search with domain-specific optimizations
for kleptocracy/democracy research.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class SemanticRetriever:
    """
    Semantic similarity retrieval using sentence transformers.
    
    Optimized for research queries with:
    - Domain-specific embedding model selection
    - Query preprocessing for better similarity
    - Score normalization and thresholding
    """
    
    def __init__(self, collection, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize semantic retriever.
        
        Args:
            collection: ChromaDB collection
            model_name: Sentence transformer model name
        """
        self.collection = collection
        self.model_name = model_name
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            logger.warning(f"Failed to load {model_name}, using default: {e}")
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        self.retrieval_count = 0
    
    def retrieve(self, query: str, n_results: int = 20) -> List[Dict]:
        """
        Retrieve semantically similar events.
        
        Args:
            query: Search query
            n_results: Maximum number of results
            
        Returns:
            List of result dictionaries with semantic scores
        """
        self.retrieval_count += 1
        
        try:
            # Preprocess query for better semantic matching
            processed_query = self._preprocess_query(query)
            
            # Query the collection
            results = self.collection.query(
                query_texts=[processed_query],
                n_results=n_results,
                include=['metadatas', 'distances', 'documents']
            )
            
            # Process and enhance results
            enhanced_results = self._enhance_results(results, query)
            
            logger.debug(f"Semantic retrieval: {len(enhanced_results)} results for query: {query[:50]}...")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Semantic retrieval failed: {e}")
            return []
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess query for better semantic matching.
        
        Args:
            query: Raw query string
            
        Returns:
            Preprocessed query string
        """
        # Basic preprocessing
        processed = query.strip()
        
        # Expand domain-specific abbreviations
        abbreviation_expansions = {
            'DJT': 'Donald J Trump',
            'POTUS': 'President of the United States',
            'SCOTUS': 'Supreme Court of the United States',
            'DOJ': 'Department of Justice',
            'FBI': 'Federal Bureau of Investigation',
            'SEC': 'Securities and Exchange Commission',
            'FTC': 'Federal Trade Commission',
            'BTC': 'Bitcoin',
            'crypto': 'cryptocurrency'
        }
        
        for abbrev, expansion in abbreviation_expansions.items():
            if abbrev in processed:
                processed = processed.replace(abbrev, expansion)
        
        # Add context for better semantic understanding
        research_context_terms = [
            'kleptocracy', 'corruption', 'democracy', 'government', 'political'
        ]
        
        # If query is very short, add relevant context
        if len(processed.split()) <= 3:
            for term in research_context_terms:
                if term.lower() in processed.lower():
                    processed = f"{processed} political research"
                    break
        
        return processed
    
    def _enhance_results(self, results: Dict, original_query: str) -> List[Dict]:
        """
        Enhance ChromaDB results with additional processing.
        
        Args:
            results: Raw ChromaDB results
            original_query: Original query for context
            
        Returns:
            List of enhanced result dictionaries
        """
        if not results['ids'] or not results['ids'][0]:
            return []
        
        enhanced_results = []
        
        for i in range(len(results['ids'][0])):
            # Extract result data
            event_id = results['ids'][0][i]
            distance = results['distances'][0][i]
            metadata = results['metadatas'][0][i]
            document = results['documents'][0][i]
            
            # Convert distance to similarity score (0-1, higher is better)
            # ChromaDB uses cosine distance, so similarity = 1 - distance
            semantic_score = max(0.0, 1.0 - distance)
            
            # Apply domain-specific score adjustments
            adjusted_score = self._apply_domain_adjustments(
                semantic_score, metadata, document, original_query
            )
            
            result = {
                'id': event_id,
                'metadata': metadata,
                'document': document,
                'semantic_score': adjusted_score,
                'raw_distance': distance
            }
            
            enhanced_results.append(result)
        
        # Sort by adjusted semantic score
        enhanced_results.sort(key=lambda x: x['semantic_score'], reverse=True)
        
        return enhanced_results
    
    def _apply_domain_adjustments(self, 
                                 score: float, 
                                 metadata: Dict, 
                                 document: str, 
                                 query: str) -> float:
        """
        Apply domain-specific score adjustments.
        
        Args:
            score: Base semantic similarity score
            metadata: Event metadata
            document: Event text content
            query: Original query
            
        Returns:
            Adjusted semantic score
        """
        adjusted_score = score
        
        # Research domain boosting
        research_keywords = {
            'kleptocracy': 1.15,
            'corruption': 1.1,
            'regulatory capture': 1.2,
            'oligarch': 1.1,
            'democracy': 1.05,
            'authoritarian': 1.1,
            'transparency': 1.05
        }
        
        query_lower = query.lower()
        document_lower = document.lower()
        
        # Boost if query contains research keywords and document matches
        for keyword, boost in research_keywords.items():
            if keyword in query_lower and keyword in document_lower:
                adjusted_score *= boost
        
        # Importance-based boosting
        importance = metadata.get('importance', '').lower()
        importance_boosts = {
            'critical': 1.2,
            'major': 1.15,
            'high': 1.1,
            'moderate': 1.0,
            'low': 0.95
        }
        
        for level, boost in importance_boosts.items():
            if level in importance:
                adjusted_score *= boost
                break
        
        # Actor relevance boosting
        actors = metadata.get('actors', [])
        if isinstance(actors, str):
            actors = [actors]
        
        # Boost if query mentions specific actors found in result
        query_words = set(query_lower.split())
        for actor in actors:
            if isinstance(actor, str):
                actor_words = set(actor.lower().split())
                if actor_words.intersection(query_words):
                    adjusted_score *= 1.1
                    break
        
        # Tag relevance boosting  
        tags = metadata.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        
        for tag in tags:
            if isinstance(tag, str) and tag.lower() in query_lower:
                adjusted_score *= 1.05
                break
        
        # Temporal relevance (simple year matching)
        date_str = metadata.get('date', '')
        if date_str:
            # Extract years from query
            import re
            query_years = re.findall(r'\b(19|20)\d{2}\b', query)
            if query_years:
                for year in query_years:
                    if year in date_str:
                        adjusted_score *= 1.1
                        break
        
        # Cap the maximum boost to prevent over-inflation
        adjusted_score = min(adjusted_score, score * 1.5)
        
        return adjusted_score
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding vector for text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        try:
            return self.embedding_model.encode([text])[0]
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Return zero vector as fallback
            return np.zeros(384)  # Default dimension for MiniLM
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        return {
            'model_name': self.model_name,
            'retrieval_count': self.retrieval_count
        }