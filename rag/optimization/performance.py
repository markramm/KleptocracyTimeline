"""
Performance Optimization System

Advanced performance optimization techniques including batching,
connection pooling, and intelligent resource management.
"""

import logging
import time
import threading
import asyncio
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, deque
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Configuration for performance optimization."""
    # Batch processing
    batch_size: int = 32
    max_batch_wait_time: float = 0.1  # seconds
    enable_batching: bool = True
    
    # Threading
    max_workers: int = 4
    enable_threading: bool = True
    
    # Connection pooling
    max_connections: int = 10
    connection_timeout: float = 30.0
    enable_connection_pooling: bool = True
    
    # Memory management
    memory_limit_mb: int = 1024
    enable_memory_monitoring: bool = True
    
    # Performance monitoring
    enable_profiling: bool = True
    profile_sample_rate: float = 0.1
    
    # Research optimizations
    prefetch_related_documents: bool = True
    cache_frequent_patterns: bool = True
    optimize_for_latency: bool = True


class BatchProcessor:
    """
    Intelligent batch processor for RAG operations.
    
    Batches similar operations together for improved throughput
    while maintaining reasonable latency.
    """
    
    def __init__(self, config: OptimizationConfig):
        """Initialize batch processor."""
        self.config = config
        
        # Batch queues for different operation types
        self.embedding_queue = queue.Queue()
        self.similarity_queue = queue.Queue()
        self.retrieval_queue = queue.Queue()
        
        # Batch processing threads
        self.batch_threads = {}
        self.running = False
        
        # Performance tracking
        self.batch_stats = defaultdict(int)
    
    def start(self):
        """Start batch processing threads."""
        if not self.config.enable_batching or self.running:
            return
        
        self.running = True
        
        # Start batch processing threads
        batch_types = ['embedding', 'similarity', 'retrieval']
        for batch_type in batch_types:
            thread = threading.Thread(
                target=self._batch_processor_worker,
                args=(batch_type,),
                daemon=True
            )
            thread.start()
            self.batch_threads[batch_type] = thread
        
        logger.info("Started batch processing threads")
    
    def stop(self):
        """Stop batch processing."""
        self.running = False
        for thread in self.batch_threads.values():
            thread.join(timeout=1.0)
        self.batch_threads.clear()
        
        logger.info("Stopped batch processing")
    
    def process_embeddings_batch(self, texts: List[str], callback: Callable) -> str:
        """Submit texts for batch embedding processing."""
        if not self.config.enable_batching:
            # Process immediately
            callback(texts)
            return "immediate"
        
        # Add to batch queue
        batch_id = f"emb_{int(time.time() * 1000000)}"
        self.embedding_queue.put({
            'id': batch_id,
            'texts': texts,
            'callback': callback,
            'timestamp': time.time()
        })
        
        return batch_id
    
    def process_similarity_batch(self, query_embeddings: List[np.ndarray], 
                                doc_embeddings: List[np.ndarray], 
                                callback: Callable) -> str:
        """Submit embeddings for batch similarity computation."""
        if not self.config.enable_batching:
            callback(query_embeddings, doc_embeddings)
            return "immediate"
        
        batch_id = f"sim_{int(time.time() * 1000000)}"
        self.similarity_queue.put({
            'id': batch_id,
            'query_embeddings': query_embeddings,
            'doc_embeddings': doc_embeddings,
            'callback': callback,
            'timestamp': time.time()
        })
        
        return batch_id
    
    def _batch_processor_worker(self, batch_type: str):
        """Worker thread for batch processing."""
        queue_map = {
            'embedding': self.embedding_queue,
            'similarity': self.similarity_queue,
            'retrieval': self.retrieval_queue
        }
        
        process_map = {
            'embedding': self._process_embedding_batch,
            'similarity': self._process_similarity_batch,
            'retrieval': self._process_retrieval_batch
        }
        
        work_queue = queue_map[batch_type]
        processor = process_map[batch_type]
        
        batch_items = []
        
        while self.running:
            try:
                # Collect items for batch
                timeout = self.config.max_batch_wait_time
                
                try:
                    item = work_queue.get(timeout=timeout)
                    batch_items.append(item)
                except queue.Empty:
                    if batch_items:
                        # Process accumulated items
                        processor(batch_items)
                        batch_items = []
                    continue
                
                # Collect more items until batch size or timeout
                start_time = time.time()
                while (len(batch_items) < self.config.batch_size and
                       time.time() - start_time < timeout):
                    try:
                        item = work_queue.get(timeout=0.01)
                        batch_items.append(item)
                    except queue.Empty:
                        break
                
                # Process batch
                if batch_items:
                    processor(batch_items)
                    batch_items = []
                
            except Exception as e:
                logger.error(f"Batch processor error for {batch_type}: {e}")
                batch_items = []
    
    def _process_embedding_batch(self, batch_items: List[Dict]):
        """Process a batch of embedding requests."""
        try:
            # Combine all texts
            all_texts = []
            item_indices = []
            
            for item in batch_items:
                start_idx = len(all_texts)
                all_texts.extend(item['texts'])
                end_idx = len(all_texts)
                item_indices.append((start_idx, end_idx, item))
            
            # Process all embeddings at once (would use actual embedding model)
            # embeddings = embedding_model.encode(all_texts)
            
            # Distribute results back to callbacks
            for start_idx, end_idx, item in item_indices:
                # item_embeddings = embeddings[start_idx:end_idx]
                # item['callback'](item_embeddings)
                pass
            
            self.batch_stats['embedding_batches'] += 1
            self.batch_stats['embedding_items'] += len(batch_items)
            
        except Exception as e:
            logger.error(f"Embedding batch processing failed: {e}")
    
    def _process_similarity_batch(self, batch_items: List[Dict]):
        """Process a batch of similarity computation requests."""
        try:
            # Batch similarity computations
            for item in batch_items:
                # Compute similarities (vectorized operations)
                query_embs = np.array(item['query_embeddings'])
                doc_embs = np.array(item['doc_embeddings'])
                
                # similarities = np.dot(query_embs, doc_embs.T)
                # item['callback'](similarities)
            
            self.batch_stats['similarity_batches'] += 1
            self.batch_stats['similarity_items'] += len(batch_items)
            
        except Exception as e:
            logger.error(f"Similarity batch processing failed: {e}")
    
    def _process_retrieval_batch(self, batch_items: List[Dict]):
        """Process a batch of retrieval requests."""
        # Placeholder for retrieval batching
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        return dict(self.batch_stats)


class ConnectionPoolManager:
    """
    Connection pool manager for database and external service connections.
    
    Manages connections to ChromaDB and other services to optimize
    resource utilization and reduce connection overhead.
    """
    
    def __init__(self, config: OptimizationConfig):
        """Initialize connection pool manager."""
        self.config = config
        
        # Connection pools
        self.chromadb_pool = deque()
        self.embedding_service_pool = deque()
        
        # Pool management
        self.pool_lock = threading.RLock()
        self.active_connections = defaultdict(int)
        self.connection_stats = defaultdict(int)
        
        # Initialize pools
        self._initialize_pools()
    
    def _initialize_pools(self):
        """Initialize connection pools."""
        if not self.config.enable_connection_pooling:
            return
        
        # Pre-create some connections
        initial_connections = min(2, self.config.max_connections // 2)
        
        for _ in range(initial_connections):
            # Would create actual connections here
            # conn = create_chromadb_connection()
            # self.chromadb_pool.append(conn)
            pass
        
        logger.info(f"Initialized connection pools with {initial_connections} connections")
    
    def get_chromadb_connection(self):
        """Get a ChromaDB connection from pool."""
        with self.pool_lock:
            if self.chromadb_pool:
                conn = self.chromadb_pool.popleft()
                self.active_connections['chromadb'] += 1
                self.connection_stats['chromadb_reused'] += 1
                return conn
            elif self.active_connections['chromadb'] < self.config.max_connections:
                # Create new connection
                # conn = create_chromadb_connection()
                conn = None  # Placeholder
                self.active_connections['chromadb'] += 1
                self.connection_stats['chromadb_created'] += 1
                return conn
            else:
                # Pool exhausted
                self.connection_stats['chromadb_pool_exhausted'] += 1
                return None
    
    def return_chromadb_connection(self, conn):
        """Return a ChromaDB connection to pool."""
        with self.pool_lock:
            if conn and len(self.chromadb_pool) < self.config.max_connections:
                self.chromadb_pool.append(conn)
            
            self.active_connections['chromadb'] = max(0, self.active_connections['chromadb'] - 1)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        with self.pool_lock:
            stats = dict(self.connection_stats)
            stats['active_connections'] = dict(self.active_connections)
            stats['pool_sizes'] = {
                'chromadb': len(self.chromadb_pool),
                'embedding_service': len(self.embedding_service_pool)
            }
            return stats
    
    def cleanup(self):
        """Clean up connection pools."""
        with self.pool_lock:
            # Close all pooled connections
            while self.chromadb_pool:
                conn = self.chromadb_pool.popleft()
                # conn.close()
            
            while self.embedding_service_pool:
                conn = self.embedding_service_pool.popleft()
                # conn.close()
            
            self.active_connections.clear()


class PerformanceOptimizer:
    """
    Master performance optimizer that coordinates all optimization techniques.
    
    Integrates caching, batching, connection pooling, and intelligent
    resource management for optimal RAG performance.
    """
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        """Initialize performance optimizer."""
        self.config = config or OptimizationConfig()
        
        # Initialize optimization components
        self.batch_processor = BatchProcessor(self.config)
        self.connection_manager = ConnectionPoolManager(self.config)
        
        # Performance monitoring
        self.performance_metrics = defaultdict(list)
        self.optimization_stats = defaultdict(int)
        
        # Resource monitoring
        self.memory_usage = deque(maxlen=100)  # Keep last 100 measurements
        self.latency_history = deque(maxlen=1000)
        
        # Optimization state
        self.auto_tuning_enabled = True
        self.last_optimization_time = datetime.now()
        
        logger.info("Initialized PerformanceOptimizer")
    
    def start(self):
        """Start performance optimization systems."""
        self.batch_processor.start()
        
        # Start monitoring thread
        if self.config.enable_profiling:
            monitor_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
            monitor_thread.start()
        
        logger.info("Started performance optimization systems")
    
    def stop(self):
        """Stop performance optimization systems."""
        self.batch_processor.stop()
        self.connection_manager.cleanup()
        
        logger.info("Stopped performance optimization systems")
    
    def optimize_query_processing(self, query_processor_func: Callable) -> Callable:
        """Optimize query processing function."""
        def optimized_processor(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Apply optimizations
                if self.config.cache_frequent_patterns:
                    # Check if this is a frequent pattern
                    pass
                
                # Execute with performance monitoring
                result = query_processor_func(*args, **kwargs)
                
                # Record performance
                latency = time.time() - start_time
                self.latency_history.append(latency)
                self.optimization_stats['queries_optimized'] += 1
                
                return result
                
            except Exception as e:
                self.optimization_stats['optimization_errors'] += 1
                raise e
        
        return optimized_processor
    
    def optimize_retrieval_batch(self, retrieval_requests: List[Dict]) -> List[Dict]:
        """Optimize a batch of retrieval requests."""
        if not retrieval_requests:
            return []
        
        start_time = time.time()
        
        # Group similar requests
        grouped_requests = self._group_similar_requests(retrieval_requests)
        
        # Process groups efficiently
        results = []
        for group in grouped_requests:
            group_results = self._process_request_group(group)
            results.extend(group_results)
        
        # Record optimization impact
        optimization_time = time.time() - start_time
        self.performance_metrics['batch_optimization_time'].append(optimization_time)
        self.optimization_stats['batches_optimized'] += 1
        
        return results
    
    def _group_similar_requests(self, requests: List[Dict]) -> List[List[Dict]]:
        """Group similar requests for batch processing."""
        # Simple grouping by request type
        groups = defaultdict(list)
        
        for request in requests:
            request_type = request.get('type', 'unknown')
            groups[request_type].append(request)
        
        return list(groups.values())
    
    def _process_request_group(self, group: List[Dict]) -> List[Dict]:
        """Process a group of similar requests efficiently."""
        # Placeholder for optimized group processing
        return group
    
    def optimize_memory_usage(self):
        """Optimize memory usage across RAG components."""
        try:
            import psutil
            
            # Get current memory usage
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            self.memory_usage.append(memory_mb)
            
            # Check if memory usage is too high
            if memory_mb > self.config.memory_limit_mb:
                logger.warning(f"High memory usage: {memory_mb:.1f}MB")
                
                # Trigger memory optimization
                self._trigger_memory_cleanup()
            
        except ImportError:
            # psutil not available
            pass
    
    def _trigger_memory_cleanup(self):
        """Trigger memory cleanup operations."""
        # This would trigger cache cleanup, garbage collection, etc.
        self.optimization_stats['memory_cleanups'] += 1
        logger.info("Triggered memory cleanup")
    
    def auto_tune_parameters(self):
        """Automatically tune optimization parameters based on performance."""
        if not self.auto_tuning_enabled:
            return
        
        # Analyze recent performance
        if len(self.latency_history) < 50:
            return  # Not enough data
        
        recent_latencies = list(self.latency_history)[-50:]
        avg_latency = np.mean(recent_latencies)
        latency_std = np.std(recent_latencies)
        
        # Tune batch size based on latency
        if self.config.optimize_for_latency:
            if avg_latency > 0.5 and self.config.batch_size > 16:
                # High latency - reduce batch size
                self.config.batch_size = max(16, self.config.batch_size - 4)
                self.optimization_stats['batch_size_reductions'] += 1
            elif avg_latency < 0.1 and latency_std < 0.05:
                # Low, stable latency - can increase batch size
                self.config.batch_size = min(64, self.config.batch_size + 4)
                self.optimization_stats['batch_size_increases'] += 1
        
        # Tune other parameters
        self._tune_connection_pool_size()
        self._tune_cache_sizes()
        
        self.last_optimization_time = datetime.now()
        self.optimization_stats['auto_tuning_runs'] += 1
    
    def _tune_connection_pool_size(self):
        """Tune connection pool size based on usage patterns."""
        conn_stats = self.connection_manager.get_connection_stats()
        
        exhausted_count = conn_stats.get('chromadb_pool_exhausted', 0)
        if exhausted_count > 10:  # Frequent exhaustion
            self.config.max_connections = min(20, self.config.max_connections + 2)
            self.optimization_stats['connection_pool_increases'] += 1
    
    def _tune_cache_sizes(self):
        """Tune cache sizes based on hit rates."""
        # This would analyze cache performance and adjust sizes
        pass
    
    def _monitoring_worker(self):
        """Background worker for performance monitoring."""
        while True:
            try:
                # Monitor memory usage
                if self.config.enable_memory_monitoring:
                    self.optimize_memory_usage()
                
                # Auto-tune parameters periodically
                if (datetime.now() - self.last_optimization_time).seconds > 300:  # 5 minutes
                    self.auto_tune_parameters()
                
                # Sleep before next monitoring cycle
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                time.sleep(30)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        summary = {
            'optimization_stats': dict(self.optimization_stats),
            'batch_processor_stats': self.batch_processor.get_stats(),
            'connection_stats': self.connection_manager.get_connection_stats(),
            'config': {
                'batch_size': self.config.batch_size,
                'max_connections': self.config.max_connections,
                'memory_limit_mb': self.config.memory_limit_mb
            }
        }
        
        # Add performance metrics
        if self.latency_history:
            recent_latencies = list(self.latency_history)[-100:]
            summary['latency_metrics'] = {
                'avg_latency': np.mean(recent_latencies),
                'p95_latency': np.percentile(recent_latencies, 95),
                'p99_latency': np.percentile(recent_latencies, 99)
            }
        
        if self.memory_usage:
            recent_memory = list(self.memory_usage)[-10:]
            summary['memory_metrics'] = {
                'avg_memory_mb': np.mean(recent_memory),
                'max_memory_mb': np.max(recent_memory)
            }
        
        return summary
    
    def reset_stats(self):
        """Reset all performance statistics."""
        self.optimization_stats.clear()
        self.performance_metrics.clear()
        self.latency_history.clear()
        self.memory_usage.clear()