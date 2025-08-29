#!/usr/bin/env python3
"""
Production RAG API with FastAPI

Features:
- RESTful API endpoints
- Request/response validation
- Monitoring and metrics
- Caching and performance optimization
- Error handling and logging
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import time
import hashlib
from pathlib import Path
import logging
from collections import defaultdict
import asyncio
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our RAG systems
from rag_system import AdvancedRAGSystem


# ============= Pydantic Models =============

class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    top_k: int = Field(20, ge=1, le=100, description="Number of results to return")
    system: str = Field("advanced", description="RAG system to use (advanced/optimized)")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What events involve cryptocurrency and Trump?",
                "top_k": 10,
                "system": "advanced"
            }
        }


class EventResult(BaseModel):
    """Event result model."""
    id: str
    date: str
    title: str
    summary: str
    actors: List[str]
    tags: List[str]
    importance: int
    score: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "2025-01-20--trump-memecoin-launch",
                "date": "2025-01-20",
                "title": "Trump launches official memecoin",
                "summary": "President Trump launches cryptocurrency...",
                "actors": ["Donald Trump"],
                "tags": ["cryptocurrency", "conflicts-of-interest"],
                "importance": 8,
                "score": 0.95
            }
        }


class SearchResponse(BaseModel):
    """Search response model."""
    query: str
    results: List[EventResult]
    total_results: int
    search_time: float
    system_used: str
    metadata: Optional[Dict[str, Any]] = None


class SystemStatus(BaseModel):
    """System status model."""
    status: str
    total_events: int
    systems_available: List[str]
    cache_size: int
    total_searches: int
    average_search_time: float
    uptime_seconds: float


class EvaluationRequest(BaseModel):
    """Evaluation request model."""
    query_limit: Optional[int] = Field(10, description="Number of queries to evaluate")
    system: str = Field("advanced", description="System to evaluate")


class FeedbackRequest(BaseModel):
    """Feedback request model."""
    query: str
    event_id: str
    relevant: bool
    comment: Optional[str] = None


# ============= Monitoring and Metrics =============

class MetricsCollector:
    """Collects and manages system metrics."""
    
    def __init__(self):
        self.searches = 0
        self.total_search_time = 0
        self.search_times = []
        self.query_history = []
        self.feedback_data = []
        self.errors = defaultdict(int)
        self.start_time = time.time()
    
    def record_search(self, query: str, search_time: float, results_count: int):
        """Record a search operation."""
        self.searches += 1
        self.total_search_time += search_time
        self.search_times.append(search_time)
        
        # Keep last 100 search times for rolling average
        if len(self.search_times) > 100:
            self.search_times.pop(0)
        
        self.query_history.append({
            'query': query,
            'time': search_time,
            'results': results_count,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep last 1000 queries
        if len(self.query_history) > 1000:
            self.query_history.pop(0)
    
    def record_error(self, error_type: str):
        """Record an error."""
        self.errors[error_type] += 1
    
    def record_feedback(self, feedback: FeedbackRequest):
        """Record user feedback."""
        self.feedback_data.append({
            'query': feedback.query,
            'event_id': feedback.event_id,
            'relevant': feedback.relevant,
            'comment': feedback.comment,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_metrics(self) -> Dict:
        """Get current metrics."""
        avg_time = sum(self.search_times) / len(self.search_times) if self.search_times else 0
        
        return {
            'total_searches': self.searches,
            'average_search_time': avg_time,
            'recent_search_times': self.search_times[-10:],
            'error_counts': dict(self.errors),
            'feedback_count': len(self.feedback_data),
            'uptime_seconds': time.time() - self.start_time
        }


# ============= Cache Manager =============

class CacheManager:
    """Manages search result caching."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def get_key(self, query: str, top_k: int, system: str) -> str:
        """Generate cache key."""
        return hashlib.md5(f"{query}:{top_k}:{system}".encode()).hexdigest()
    
    def get(self, query: str, top_k: int, system: str) -> Optional[List[Dict]]:
        """Get cached results."""
        key = self.get_key(query, top_k, system)
        
        if key in self.cache:
            # Check if still valid
            if time.time() - self.access_times[key] < self.ttl_seconds:
                self.access_times[key] = time.time()  # Update access time
                return self.cache[key]
            else:
                # Expired
                del self.cache[key]
                del self.access_times[key]
        
        return None
    
    def set(self, query: str, top_k: int, system: str, results: List[Dict]):
        """Cache results."""
        key = self.get_key(query, top_k, system)
        
        # Check cache size
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.access_times, key=self.access_times.get)
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = results
        self.access_times[key] = time.time()
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.access_times.clear()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.cache)


# ============= Background Tasks =============

async def log_search_analytics(query: str, results_count: int, search_time: float):
    """Log search analytics in background."""
    # This could write to a database or analytics service
    logger.info(f"Search analytics: query='{query[:50]}...', results={results_count}, time={search_time:.3f}s")


# ============= FastAPI App =============

# Global instances
rag_systems = {}
metrics = MetricsCollector()
cache = CacheManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting RAG API server...")
    
    # Initialize RAG systems
    try:
        rag_systems['advanced'] = AdvancedRAGSystem("../timeline_data/timeline_complete.json")
        logger.info("Advanced RAG system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Advanced RAG: {e}")
    
    try:
        # Only using advanced system now (best performance)
        # rag_systems['optimized'] = OptimizedRAGSystem("../timeline_data/timeline_complete.json")
        logger.info("Optimized RAG system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Optimized RAG: {e}")
    
    if not rag_systems:
        logger.error("No RAG systems available!")
        raise RuntimeError("Failed to initialize any RAG system")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RAG API server...")
    cache.clear()


# Create FastAPI app
app = FastAPI(
    title="Kleptocracy Timeline RAG API",
    description="Advanced retrieval-augmented generation system for timeline events",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= API Endpoints =============

@app.get("/", tags=["Info"])
async def root():
    """Root endpoint."""
    return {
        "name": "Kleptocracy Timeline RAG API",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs"
    }


@app.get("/status", response_model=SystemStatus, tags=["Info"])
async def get_status():
    """Get system status and metrics."""
    metrics_data = metrics.get_metrics()
    
    # Get event count from first available system
    total_events = 0
    if rag_systems:
        first_system = next(iter(rag_systems.values()))
        total_events = len(first_system.events)
    
    return SystemStatus(
        status="online",
        total_events=total_events,
        systems_available=list(rag_systems.keys()),
        cache_size=cache.size(),
        total_searches=metrics_data['total_searches'],
        average_search_time=metrics_data['average_search_time'],
        uptime_seconds=metrics_data['uptime_seconds']
    )


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    use_cache: bool = Query(True, description="Use cached results if available")
):
    """
    Perform semantic search on timeline events.
    
    Returns relevant events ranked by relevance score.
    """
    try:
        # Check if system is available
        if request.system not in rag_systems:
            raise HTTPException(
                status_code=400,
                detail=f"System '{request.system}' not available. Use one of: {list(rag_systems.keys())}"
            )
        
        # Check cache
        if use_cache:
            cached_results = cache.get(request.query, request.top_k, request.system)
            if cached_results:
                logger.info(f"Cache hit for query: {request.query[:50]}...")
                return SearchResponse(
                    query=request.query,
                    results=cached_results,
                    total_results=len(cached_results),
                    search_time=0.0,
                    system_used=request.system,
                    metadata={"cache_hit": True}
                )
        
        # Perform search
        start_time = time.time()
        rag_system = rag_systems[request.system]
        raw_results = rag_system.search(request.query, request.top_k)
        search_time = time.time() - start_time
        
        # Format results
        formatted_results = []
        for result in raw_results:
            event = result.get('event', {})
            
            # Determine score field
            score = result.get('ranking_score', 
                              result.get('final_score',
                                       result.get('relevance_score', 0)))
            
            formatted_results.append(EventResult(
                id=event.get('id', ''),
                date=event.get('date', ''),
                title=event.get('title', ''),
                summary=event.get('summary', ''),
                actors=event.get('actors', []),
                tags=event.get('tags', []),
                importance=event.get('importance', 5),
                score=score
            ))
        
        # Cache results
        if use_cache:
            cache.set(request.query, request.top_k, request.system, formatted_results)
        
        # Record metrics
        metrics.record_search(request.query, search_time, len(formatted_results))
        
        # Log analytics in background
        background_tasks.add_task(
            log_search_analytics,
            request.query,
            len(formatted_results),
            search_time
        )
        
        return SearchResponse(
            query=request.query,
            results=formatted_results,
            total_results=len(formatted_results),
            search_time=search_time,
            system_used=request.system,
            metadata={"cache_hit": False}
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        metrics.record_error("search_error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback", tags=["Feedback"])
async def submit_feedback(feedback: FeedbackRequest):
    """Submit relevance feedback for a search result."""
    try:
        metrics.record_feedback(feedback)
        
        # In a production system, this would update the ranking model
        logger.info(f"Feedback received: query='{feedback.query[:50]}...', "
                   f"event={feedback.event_id}, relevant={feedback.relevant}")
        
        return {"status": "success", "message": "Feedback recorded"}
    
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        metrics.record_error("feedback_error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Get detailed system metrics."""
    return metrics.get_metrics()


@app.post("/cache/clear", tags=["Admin"])
async def clear_cache():
    """Clear the search cache."""
    cache.clear()
    return {"status": "success", "message": "Cache cleared"}


@app.get("/events/{event_id}", tags=["Events"])
async def get_event(event_id: str):
    """Get a specific event by ID."""
    try:
        # Find event in first available system
        for system in rag_systems.values():
            if event_id in system.event_dict:
                event = system.event_dict[event_id]
                return {
                    "id": event.id,
                    "date": event.date,
                    "title": event.title,
                    "summary": event.summary,
                    "actors": event.actors,
                    "tags": event.tags,
                    "importance": event.importance,
                    "sources": event.sources
                }
        
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    
    except Exception as e:
        logger.error(f"Get event error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ============= Main =============

if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )