#!/usr/bin/env python3
"""
FastAPI server for Timeline RAG System
Provides REST API for AI-powered timeline queries
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from simple_rag import TimelineRAG

# Initialize FastAPI app
app = FastAPI(
    title="Kleptocracy Timeline RAG API",
    description="AI-powered search and analysis for kleptocracy timeline events",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system
rag_system = None

@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup"""
    global rag_system
    print("Initializing RAG system...")
    rag_system = TimelineRAG(
        timeline_dir=os.getenv("TIMELINE_DIR", "../timeline_data/events"),
        use_local_embeddings=True
    )
    print("RAG system ready!")

# Request/Response models
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(10, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters")

class QuestionRequest(BaseModel):
    question: str = Field(..., description="Question to answer")
    max_events: int = Field(5, description="Maximum events to use as context")
    use_llm: bool = Field(False, description="Use LLM for answer generation")

class PatternRequest(BaseModel):
    actor: Optional[str] = Field(None, description="Specific actor to analyze")
    tag: Optional[str] = Field(None, description="Specific tag to analyze")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")

class TimelineEvent(BaseModel):
    id: str
    date: str
    title: str
    summary: Optional[str]
    actors: Optional[List[str]]
    tags: Optional[List[str]]
    status: Optional[str]
    sources: Optional[List[Any]]

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    total: int

class AnswerResponse(BaseModel):
    answer: str
    events: List[str]
    sources: List[str]
    confidence: float = Field(0.0, description="Confidence score")

class PatternResponse(BaseModel):
    patterns: Dict[str, Any]
    summary: str

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Kleptocracy Timeline RAG API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/api/search",
            "answer": "/api/answer",
            "patterns": "/api/patterns",
            "events": "/api/events/{event_id}",
            "timeline": "/api/timeline",
            "stats": "/api/stats"
        }
    }

@app.post("/api/search", response_model=SearchResponse)
async def search_events(request: SearchRequest):
    """
    Search for relevant timeline events
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        results = rag_system.search(
            query=request.query,
            n_results=request.max_results,
            filters=request.filters
        )
        
        return SearchResponse(
            results=results,
            query=request.query,
            total=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/answer", response_model=AnswerResponse)
async def answer_question(request: QuestionRequest):
    """
    Answer a question using RAG
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        result = rag_system.answer_question(
            question=request.question,
            max_events=request.max_events,
            use_llm=request.use_llm
        )
        
        # Calculate confidence based on number of sources
        confidence = min(1.0, len(result['events']) * 0.2)
        
        return AnswerResponse(
            answer=result['answer'],
            events=result['events'],
            sources=result['sources'],
            confidence=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/patterns", response_model=PatternResponse)
async def analyze_patterns(request: PatternRequest):
    """
    Analyze patterns in timeline events
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # Prepare date range
        date_range = None
        if request.start_date and request.end_date:
            date_range = (request.start_date, request.end_date)
        
        patterns = rag_system.find_patterns(
            actor=request.actor,
            tag=request.tag,
            date_range=date_range
        )
        
        # Generate summary
        summary_parts = []
        if patterns['total_events'] > 0:
            summary_parts.append(f"Found {patterns['total_events']} events")
            if request.actor:
                summary_parts.append(f"involving {request.actor}")
            if request.tag:
                summary_parts.append(f"tagged '{request.tag}'")
            if date_range:
                summary_parts.append(f"between {request.start_date} and {request.end_date}")
        else:
            summary_parts.append("No matching events found")
        
        summary = " ".join(summary_parts)
        
        return PatternResponse(
            patterns=patterns,
            summary=summary
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/{event_id}")
async def get_event(event_id: str):
    """
    Get a specific event by ID
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    # Find event
    event = next((e for e in rag_system.events if e.get('id') == event_id), None)
    
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    
    return event

@app.get("/api/timeline")
async def get_timeline(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    actor: Optional[str] = Query(None, description="Filter by actor"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum events to return")
):
    """
    Get timeline events with optional filters
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    # Filter events
    events = rag_system.events
    
    if start_date:
        events = [e for e in events if e.get('date', '') >= start_date]
    
    if end_date:
        events = [e for e in events if e.get('date', '') <= end_date]
    
    if tag:
        events = [e for e in events if tag in str(e.get('tags', []))]
    
    if actor:
        events = [e for e in events if actor in str(e.get('actors', []))]
    
    if status:
        events = [e for e in events if e.get('status') == status]
    
    # Limit results
    events = events[:limit]
    
    return {
        "events": events,
        "total": len(events),
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "tag": tag,
            "actor": actor,
            "status": status
        }
    }

@app.get("/api/stats")
async def get_statistics():
    """
    Get timeline statistics
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    events = rag_system.events
    
    # Calculate statistics
    stats = {
        "total_events": len(events),
        "date_range": {
            "earliest": min((e.get('date') for e in events), default='N/A'),
            "latest": max((e.get('date') for e in events), default='N/A')
        },
        "events_by_status": rag_system._count_field(events, 'status'),
        "top_tags": rag_system._count_field(events, 'tags'),
        "top_actors": rag_system._count_field(events, 'actors'),
        "events_by_year": {}
    }
    
    # Count by year
    for event in events:
        date = event.get('date', '')
        if date and len(date) >= 4:
            year = date[:4]
            stats['events_by_year'][year] = stats['events_by_year'].get(year, 0) + 1
    
    stats['events_by_year'] = dict(sorted(stats['events_by_year'].items()))
    
    return stats

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "rag_initialized": rag_system is not None,
        "events_loaded": len(rag_system.events) if rag_system else 0,
        "timestamp": datetime.now().isoformat()
    }

# CLI usage
if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8001))
    
    print(f"Starting RAG API server on {host}:{port}")
    print(f"Timeline directory: {os.getenv('TIMELINE_DIR', '../timeline_data/events')}")
    print("\nAPI Documentation: http://localhost:8001/docs")
    print("Health Check: http://localhost:8001/api/health")
    
    uvicorn.run(
        "rag_api:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )