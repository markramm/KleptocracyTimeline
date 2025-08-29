"""
Advanced Caching System for RAG

Multi-level caching with intelligent cache management, TTL support,
and research-specific optimizations.
"""

import logging
import pickle
import hashlib
import json
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
from collections import OrderedDict, defaultdict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for caching system."""
    # Cache sizes (number of entries)
    query_cache_size: int = 1000
    embedding_cache_size: int = 5000
    result_cache_size: int = 2000
    
    # TTL settings (in seconds)
    query_cache_ttl: int = 3600      # 1 hour
    embedding_cache_ttl: int = 86400  # 24 hours
    result_cache_ttl: int = 1800     # 30 minutes
    
    # Performance settings
    enable_compression: bool = True
    enable_persistence: bool = True
    cache_directory: str = "/tmp/rag_cache"
    
    # Research optimizations
    enable_semantic_similarity: bool = True
    similarity_threshold: float = 0.9
    cache_hit_boost: float = 1.2    # Boost for cache hits in scoring


class CacheEntry:
    """Individual cache entry with metadata."""
    
    def __init__(self, key: str, value: Any, ttl_seconds: int = 0):
        """
        Initialize cache entry.
        
        Args:
            key: Cache key
            value: Cached value
            ttl_seconds: Time to live in seconds (0 = no expiration)
        """
        self.key = key
        self.value = value
        self.created_at = datetime.now()
        self.accessed_at = self.created_at
        self.access_count = 1
        self.ttl_seconds = ttl_seconds
        
        # Calculate expiration time
        if ttl_seconds > 0:
            self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
        else:
            self.expires_at = None
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def touch(self):
        """Update access timestamp."""
        self.accessed_at = datetime.now()
        self.access_count += 1
    
    def size_bytes(self) -> int:
        """Estimate memory size of cached value."""
        try:
            return len(pickle.dumps(self.value))
        except:
            return len(str(self.value).encode('utf-8'))


class QueryCache:
    """
    Cache for processed queries and expansions.
    
    Caches:
    - Query processing results
    - Query expansions
    - Filter extractions
    - Intent classifications
    """
    
    def __init__(self, config: CacheConfig):
        """Initialize query cache."""
        self.config = config
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = defaultdict(int)
    
    def get(self, query: str) -> Optional[Any]:
        """Get cached query processing result."""
        with self.lock:
            key = self._hash_query(query)
            
            if key in self.cache:
                entry = self.cache[key]
                
                # Check expiration
                if entry.is_expired():
                    del self.cache[key]
                    self.stats['expired_entries'] += 1
                    return None
                
                # Move to end (LRU)
                self.cache.move_to_end(key)
                entry.touch()
                self.stats['cache_hits'] += 1
                
                return entry.value
            
            self.stats['cache_misses'] += 1
            return None
    
    def put(self, query: str, processed_result: Any):
        """Cache processed query result."""
        with self.lock:
            key = self._hash_query(query)
            
            # Create cache entry
            entry = CacheEntry(key, processed_result, self.config.query_cache_ttl)
            
            # Add to cache
            self.cache[key] = entry
            
            # Evict if over capacity
            while len(self.cache) > self.config.query_cache_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats['evicted_entries'] += 1
            
            self.stats['cache_puts'] += 1
    
    def find_similar_queries(self, query: str, threshold: float = 0.9) -> List[Tuple[str, float, Any]]:
        """Find similar cached queries using string similarity."""
        if not self.config.enable_semantic_similarity:
            return []
        
        similar_queries = []
        query_words = set(query.lower().split())
        
        with self.lock:
            for cached_key, entry in self.cache.items():
                if entry.is_expired():
                    continue
                
                # Simple word-based similarity
                original_query = self._unhash_query(cached_key)  # Would need reverse mapping
                if original_query:
                    cached_words = set(original_query.lower().split())
                    
                    if query_words and cached_words:
                        similarity = len(query_words.intersection(cached_words)) / len(query_words.union(cached_words))
                        
                        if similarity >= threshold:
                            similar_queries.append((original_query, similarity, entry.value))
        
        return sorted(similar_queries, key=lambda x: x[1], reverse=True)
    
    def _hash_query(self, query: str) -> str:
        """Create hash for query."""
        return hashlib.sha256(query.encode('utf-8')).hexdigest()[:16]
    
    def _unhash_query(self, hashed: str) -> Optional[str]:
        """Reverse hash to original query (placeholder - would need mapping)."""
        # In a real implementation, we'd maintain a reverse mapping
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            stats = dict(self.stats)
            stats['cache_size'] = len(self.cache)
            stats['hit_rate'] = (
                self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses'])
                if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0 else 0.0
            )
            return stats


class EmbeddingCache:
    """
    Cache for embeddings and semantic similarity computations.
    
    Caches:
    - Text embeddings
    - Similarity matrices
    - Semantic clustering results
    """
    
    def __init__(self, config: CacheConfig):
        """Initialize embedding cache."""
        self.config = config
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = defaultdict(int)
    
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get cached embedding for text."""
        with self.lock:
            key = self._hash_text(text)
            
            if key in self.cache:
                entry = self.cache[key]
                
                if entry.is_expired():
                    del self.cache[key]
                    self.stats['expired_entries'] += 1
                    return None
                
                self.cache.move_to_end(key)
                entry.touch()
                self.stats['embedding_hits'] += 1
                
                return entry.value
            
            self.stats['embedding_misses'] += 1
            return None
    
    def put_embedding(self, text: str, embedding: np.ndarray):
        """Cache embedding for text."""
        with self.lock:
            key = self._hash_text(text)
            
            # Compress embedding if enabled
            if self.config.enable_compression:
                # Simple compression: reduce precision
                compressed_embedding = embedding.astype(np.float16)
            else:
                compressed_embedding = embedding
            
            entry = CacheEntry(key, compressed_embedding, self.config.embedding_cache_ttl)
            self.cache[key] = entry
            
            # Evict if over capacity
            while len(self.cache) > self.config.embedding_cache_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats['evicted_entries'] += 1
            
            self.stats['embedding_puts'] += 1
    
    def get_similarity_matrix(self, texts: List[str]) -> Optional[np.ndarray]:
        """Get cached similarity matrix for set of texts."""
        with self.lock:
            key = self._hash_text_list(texts)
            
            if key in self.cache:
                entry = self.cache[key]
                
                if entry.is_expired():
                    del self.cache[key]
                    return None
                
                entry.touch()
                self.stats['matrix_hits'] += 1
                return entry.value
            
            self.stats['matrix_misses'] += 1
            return None
    
    def put_similarity_matrix(self, texts: List[str], matrix: np.ndarray):
        """Cache similarity matrix for set of texts."""
        with self.lock:
            key = self._hash_text_list(texts)
            
            if self.config.enable_compression:
                compressed_matrix = matrix.astype(np.float16)
            else:
                compressed_matrix = matrix
            
            entry = CacheEntry(key, compressed_matrix, self.config.embedding_cache_ttl)
            self.cache[key] = entry
            
            # Matrix caching is more expensive, so smaller cache
            max_matrices = self.config.embedding_cache_size // 10
            while len([k for k in self.cache.keys() if 'matrix' in k]) > max_matrices:
                # Remove oldest matrix
                for k in self.cache.keys():
                    if 'matrix' in k:
                        del self.cache[k]
                        break
            
            self.stats['matrix_puts'] += 1
    
    def _hash_text(self, text: str) -> str:
        """Create hash for text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]
    
    def _hash_text_list(self, texts: List[str]) -> str:
        """Create hash for list of texts."""
        combined = '|'.join(sorted(texts))
        return 'matrix_' + hashlib.sha256(combined.encode('utf-8')).hexdigest()[:12]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get embedding cache statistics."""
        with self.lock:
            stats = dict(self.stats)
            stats['cache_size'] = len(self.cache)
            stats['total_size_mb'] = sum(entry.size_bytes() for entry in self.cache.values()) / (1024*1024)
            return stats


class ResultCache:
    """
    Cache for retrieval results and rankings.
    
    Caches:
    - Query results
    - Reranking results  
    - Aggregated search results
    """
    
    def __init__(self, config: CacheConfig):
        """Initialize result cache."""
        self.config = config
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = defaultdict(int)
    
    def get_results(self, query: str, filters: Dict = None) -> Optional[List]:
        """Get cached results for query."""
        with self.lock:
            key = self._make_result_key(query, filters)
            
            if key in self.cache:
                entry = self.cache[key]
                
                if entry.is_expired():
                    del self.cache[key]
                    self.stats['expired_entries'] += 1
                    return None
                
                self.cache.move_to_end(key)
                entry.touch()
                self.stats['result_hits'] += 1
                
                return entry.value
            
            self.stats['result_misses'] += 1
            return None
    
    def put_results(self, query: str, results: List, filters: Dict = None):
        """Cache results for query."""
        with self.lock:
            key = self._make_result_key(query, filters)
            
            # Only cache if results are substantial
            if len(results) < 3:
                return
            
            entry = CacheEntry(key, results, self.config.result_cache_ttl)
            self.cache[key] = entry
            
            # Evict if over capacity
            while len(self.cache) > self.config.result_cache_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                self.stats['evicted_entries'] += 1
            
            self.stats['result_puts'] += 1
    
    def _make_result_key(self, query: str, filters: Dict = None) -> str:
        """Create key for query + filters combination."""
        components = [query]
        if filters:
            # Sort filters for consistent hashing
            filter_str = json.dumps(filters, sort_keys=True)
            components.append(filter_str)
        
        combined = '|'.join(components)
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get result cache statistics."""
        with self.lock:
            stats = dict(self.stats)
            stats['cache_size'] = len(self.cache)
            return stats


class RAGCache:
    """
    Master cache coordinator for RAG system.
    
    Coordinates multiple cache types and provides unified interface
    for caching operations across the RAG pipeline.
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize RAG cache system."""
        self.config = config or CacheConfig()
        
        # Initialize component caches
        self.query_cache = QueryCache(self.config)
        self.embedding_cache = EmbeddingCache(self.config)
        self.result_cache = ResultCache(self.config)
        
        # Global stats
        self.global_stats = defaultdict(int)
        
        logger.info("Initialized RAGCache with multi-level caching")
    
    # Query caching interface
    def get_processed_query(self, query: str) -> Optional[Any]:
        """Get cached processed query."""
        return self.query_cache.get(query)
    
    def cache_processed_query(self, query: str, processed_result: Any):
        """Cache processed query result."""
        self.query_cache.put(query, processed_result)
    
    # Embedding caching interface
    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get cached embedding."""
        return self.embedding_cache.get_embedding(text)
    
    def cache_embedding(self, text: str, embedding: np.ndarray):
        """Cache text embedding."""
        self.embedding_cache.put_embedding(text, embedding)
    
    def get_similarity_matrix(self, texts: List[str]) -> Optional[np.ndarray]:
        """Get cached similarity matrix."""
        return self.embedding_cache.get_similarity_matrix(texts)
    
    def cache_similarity_matrix(self, texts: List[str], matrix: np.ndarray):
        """Cache similarity matrix."""
        self.embedding_cache.put_similarity_matrix(texts, matrix)
    
    # Result caching interface
    def get_results(self, query: str, filters: Dict = None) -> Optional[List]:
        """Get cached results."""
        return self.result_cache.get_results(query, filters)
    
    def cache_results(self, query: str, results: List, filters: Dict = None):
        """Cache query results."""
        self.result_cache.put_results(query, results, filters)
    
    # Smart caching features
    def find_similar_cached_queries(self, query: str) -> List[Tuple[str, float, Any]]:
        """Find similar queries in cache."""
        return self.query_cache.find_similar_queries(query, self.config.similarity_threshold)
    
    def warm_cache_with_common_queries(self, common_queries: List[str]):
        """Pre-warm cache with common queries."""
        # This would trigger processing of common queries to populate cache
        pass
    
    def optimize_cache_performance(self):
        """Optimize cache performance by analyzing usage patterns."""
        # Analyze access patterns and optimize cache configurations
        stats = self.get_comprehensive_stats()
        
        # Adjust cache sizes based on hit rates
        for cache_name, cache_stats in stats.items():
            if 'hit_rate' in cache_stats:
                hit_rate = cache_stats['hit_rate']
                if hit_rate < 0.3:  # Low hit rate
                    logger.warning(f"Low hit rate for {cache_name}: {hit_rate:.2f}")
                elif hit_rate > 0.8:  # High hit rate - could increase size
                    logger.info(f"High hit rate for {cache_name}: {hit_rate:.2f}")
    
    def clear_expired_entries(self):
        """Clear all expired cache entries."""
        # This would be called periodically
        pass
    
    def get_comprehensive_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all cache components."""
        return {
            'query_cache': self.query_cache.get_stats(),
            'embedding_cache': self.embedding_cache.get_stats(),
            'result_cache': self.result_cache.get_stats(),
            'global_stats': dict(self.global_stats)
        }
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get memory usage statistics in MB."""
        return {
            'query_cache_mb': sum(
                entry.size_bytes() for entry in self.query_cache.cache.values()
            ) / (1024*1024),
            'embedding_cache_mb': sum(
                entry.size_bytes() for entry in self.embedding_cache.cache.values()
            ) / (1024*1024),
            'result_cache_mb': sum(
                entry.size_bytes() for entry in self.result_cache.cache.values()
            ) / (1024*1024)
        }
    
    def clear_all_caches(self):
        """Clear all caches."""
        with self.query_cache.lock:
            self.query_cache.cache.clear()
        with self.embedding_cache.lock:
            self.embedding_cache.cache.clear()
        with self.result_cache.lock:
            self.result_cache.cache.clear()
        
        logger.info("Cleared all caches")