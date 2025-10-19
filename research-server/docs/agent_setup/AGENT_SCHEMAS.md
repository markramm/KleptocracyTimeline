# Agent System Schemas and API Specifications

This document defines standardized input/output schemas for all subagents and API endpoints to ensure consistency and proper coordination.

## Core Data Types

### Timeline Event Schema
```json
{
  "id": "2001-10-25--stellar-wind-authorization",
  "date": "2001-10-25",
  "title": "NSA Stellar Wind Program Authorization",
  "summary": "President Bush authorizes NSA's warrantless surveillance program...",
  "actors": ["George W. Bush", "NSA", "John Yoo"],
  "financial_impact": "$100 million",
  "sources": ["https://example.com/source1", "https://example.com/source2"],
  "importance": 8,
  "tags": ["surveillance", "constitutional-crisis"],
  "status": "confirmed"
}
```

### Research Priority Schema
```json
{
  "id": "RT-001-surveillance-state-origins",
  "title": "Surveillance State Origins 2001-2003",
  "description": "Research systematic expansion of surveillance...",
  "priority": 9,
  "status": "pending|in_progress|completed",
  "category": "surveillance|financial|constitutional-crisis",
  "tags": ["high-priority", "systematic-capture"],
  "estimated_events": 5,
  "actual_events": 0,
  "created_date": "2025-09-09",
  "time_period": "2001-2003",
  "research_notes": "Additional context or findings"
}
```

### Investigation Schema (PDF Breakdown Output)
```json
{
  "id": "INV-001-patriot-act-expansion",
  "title": "Patriot Act Surveillance Expansion 2001-2003",
  "description": "Research specific surveillance programs...",
  "priority": 9,
  "estimated_events": 3,
  "research_queries": [
    "Patriot Act Section 215 bulk metadata collection start date",
    "FISA court approval October 2001 specific programs"
  ],
  "duplicate_check_keywords": [
    "patriot act surveillance",
    "section 215"
  ],
  "date_range": {
    "start": "2001-10-01",
    "end": "2003-12-31"
  },
  "key_actors": ["George W. Bush", "John Ashcroft"],
  "dependencies": [],
  "can_parallel": true,
  "chunk_size": "small|medium|large"
}
```

## API Endpoints and Schemas

### GET /api/priorities/next
**Response:**
```json
{
  "id": "RT-001-surveillance-origins",
  "title": "Surveillance State Origins",
  "description": "Research description...",
  "priority": 9,
  "estimated_events": 5,
  "tags": ["surveillance", "constitutional-crisis"],
  "status": "pending"
}
```

**Error Response:**
```json
{
  "message": "No pending priorities",
  "error": "queue_empty"
}
```

### POST /api/events/staged
**Request:**
```json
{
  "events": [
    {
      "id": "2001-10-25--stellar-wind-authorization",
      "date": "2001-10-25",
      "title": "NSA Stellar Wind Authorization",
      "summary": "Detailed summary...",
      "actors": ["George W. Bush", "NSA"],
      "financial_impact": "$100 million",
      "sources": ["url1", "url2"],
      "importance": 8,
      "tags": ["surveillance"]
    }
  ],
  "priority_id": "RT-001-surveillance-origins"
}
```

**Response:**
```json
{
  "status": "staged",
  "events_processed": 1,
  "events_since_commit": 5
}
```

### PUT /api/priorities/{priority_id}/status
**Request:**
```json
{
  "status": "completed",
  "actual_events": 3,
  "notes": "Research completed successfully"
}
```

## Subagent Input/Output Schemas

### Timeline Researcher Agent

**Input Schema:**
```json
{
  "priority": {
    "id": "RT-001-example",
    "title": "Research Topic",
    "description": "Detailed research description",
    "estimated_events": 3
  },
  "research_queries": [
    "specific query 1",
    "specific query 2"
  ],
  "date_range": "2001-2003",
  "actors": ["Person 1", "Organization 2"]
}
```

**Output Schema (Research Results):**
```json
{
  "type": "research_results",
  "priority_id": "RT-001-example",
  "events_created": 3,
  "events": [
    {
      "id": "2001-10-25--stellar-wind",
      "date": "2001-10-25",
      "title": "Event Title",
      "summary": "Event summary...",
      "actors": ["Actor 1", "Actor 2"],
      "financial_impact": "$100 million",
      "sources": ["url1", "url2"],
      "importance": 8,
      "tags": ["tag1", "tag2"]
    }
  ],
  "research_quality": "high|medium|low",
  "completion_status": "completed"
}
```

**Output Schema (Chunking Recommendation):**
```json
{
  "type": "chunking_recommendation",
  "priority_id": "RT-001-example",
  "scope_assessment": "too_broad",
  "issue": "Date range 1991-1996 covers 5 years of complex transitions",
  "estimated_events": 12,
  "recommended_chunks": [
    {
      "chunk_id": "oligarch-emergence-1991-1993",
      "title": "Early Privatization 1991-1993",
      "date_range": "1991-08-01 to 1993-12-31",
      "estimated_events": 4,
      "key_queries": ["query1", "query2"]
    }
  ],
  "rationale": "Original scope would require 8,000+ tokens and 20+ minutes"
}
```

### PDF Investigation Planner

**Input Schema:**
```json
{
  "pdf_title": "The Capture Cascade - Part 3",
  "pdf_summary": "High-level summary from PDF analyzer",
  "key_topics": ["topic1", "topic2", "topic3"],
  "date_range": "2001-2009",
  "actors_mentioned": ["Actor1", "Actor2"],
  "existing_timeline_context": ["related events already in timeline"]
}
```

**Output Schema:**
```json
{
  "pdf_id": "capture-cascade-part-3",
  "total_investigations": 5,
  "investigations": [
    {
      "id": "INV-001-patriot-act-surveillance",
      "title": "Patriot Act Surveillance Expansion 2001-2003",
      "description": "Research specific surveillance programs...",
      "priority": 9,
      "estimated_events": 3,
      "research_queries": ["query1", "query2"],
      "duplicate_check_keywords": ["keyword1", "keyword2"],
      "date_range": {
        "start": "2001-10-01",
        "end": "2003-12-31"
      },
      "key_actors": ["George W. Bush", "John Ashcroft"],
      "dependencies": [],
      "can_parallel": true,
      "chunk_size": "small"
    }
  ],
  "duplicate_risk_assessment": {
    "high_risk": [],
    "medium_risk": ["INV-002"],
    "low_risk": ["INV-001", "INV-003"]
  }
}
```

### Topic Coverage Checker

**Input Schema:**
```json
{
  "topic": "NSA surveillance programs",
  "date_range": "2001-2007",
  "key_actors": ["NSA", "George W. Bush"],
  "search_keywords": ["surveillance", "patriot act", "fisa"]
}
```

**Output Schema:**
```json
{
  "coverage_assessment": "full|partial|minimal|none",
  "existing_events_count": 5,
  "coverage_percentage": 75,
  "gaps_identified": [
    {
      "gap_type": "missing_timeframe",
      "description": "2004-2005 period lacks coverage",
      "severity": "high"
    }
  ],
  "related_events": [
    "2001-10-25--stellar-wind-authorization",
    "2008-07-10--fisa-amendments-act"
  ],
  "recommendation": "proceed|modify_scope|skip_duplicate"
}
```

### Source Validator Agent

**Input Schema:**
```json
{
  "sources": [
    {
      "url": "https://example.com/article",
      "title": "Article Title",
      "outlet": "Publication Name",
      "date": "2025-01-01"
    }
  ],
  "event_claims": [
    "George W. Bush signed executive order on 2001-10-25",
    "NSA surveillance program cost $100 million"
  ]
}
```

**Output Schema:**
```json
{
  "validation_results": [
    {
      "source_url": "https://example.com/article",
      "credibility_score": 8,
      "credibility_tier": "high|medium|low",
      "issues": [],
      "verified_claims": ["claim1", "claim2"],
      "disputed_claims": [],
      "status": "verified|questionable|unreliable"
    }
  ],
  "overall_credibility": "high",
  "recommended_action": "approve|review|reject"
}
```

### Duplicate Checker Agent

**Input Schema:**
```json
{
  "event_candidate": {
    "date": "2001-10-25",
    "title": "NSA Stellar Wind Authorization",
    "actors": ["George W. Bush", "NSA"],
    "keywords": ["surveillance", "patriot act"]
  },
  "search_scope": {
    "date_tolerance_days": 30,
    "actor_overlap_threshold": 0.5
  }
}
```

**Output Schema:**
```json
{
  "duplicate_found": true,
  "confidence_level": "high|medium|low",
  "matching_events": [
    {
      "event_id": "2001-10-04--nsa-surveillance-program",
      "similarity_score": 0.85,
      "match_reasons": ["same_date", "actor_overlap", "keyword_similarity"]
    }
  ],
  "recommendation": "skip|merge|proceed_as_distinct",
  "suggested_modifications": [
    "Adjust focus to specific authorization aspect",
    "Clarify distinction from existing event"
  ]
}
```

## Queue Behavior Specifications

### Priority Assignment (Race Condition Fix)

**Current Issue:** Multiple agents calling `/api/priorities/next` get the same priority.

**Solution: Implement atomic queue operations**

```python
@app.route('/api/priorities/next', methods=['POST'])
@require_api_key
def reserve_next_priority():
    """Atomically reserve the next priority for an agent"""
    db = get_db()
    try:
        agent_id = request.json.get('agent_id', f'agent-{int(time.time())}')
        
        # Start transaction
        with db.begin():
            priority = db.query(ResearchPriority)\
                .filter_by(status='pending')\
                .order_by(ResearchPriority.priority.desc())\
                .with_for_update()\
                .first()
            
            if not priority:
                return jsonify({'message': 'No pending priorities'}), 404
            
            # Atomically reserve priority
            priority.status = 'reserved'
            priority.assigned_agent = agent_id
            priority.reserved_at = datetime.now()
            
            db.commit()
            
            return jsonify({
                'id': priority.id,
                'title': priority.title,
                'description': priority.description,
                'priority': priority.priority,
                'estimated_events': priority.estimated_events,
                'tags': priority.tags,
                'agent_id': agent_id,
                'reserved_until': (datetime.now() + timedelta(hours=1)).isoformat()
            })
            
    finally:
        db.close()
```

### Priority States
- `pending` - Available for assignment
- `reserved` - Temporarily assigned to agent (1 hour timeout)
- `in_progress` - Agent confirmed work started
- `completed` - Research finished
- `failed` - Research failed/abandoned

### Timeout Mechanism
- Reserved priorities auto-release after 1 hour
- Agents must call `/api/priorities/{id}/start` within timeout to confirm

## Error Handling Schemas

### Validation Errors
```json
{
  "valid": false,
  "errors": [
    "Missing required field: date",
    "Date must be YYYY-MM-DD format"
  ],
  "warnings": [
    "Financial impact should be numeric"
  ]
}
```

### API Errors
```json
{
  "error": "priority_not_found",
  "message": "Priority RT-001 does not exist",
  "code": 404
}
```

## Agent Coordination Patterns

### Parallel Research Workflow (Race Condition Safe)
1. Agent calls `POST /api/priorities/next` with `{"agent_id": "unique-id"}`
2. API atomically reserves highest priority for 1 hour (status: `reserved`)
3. Agent calls `PUT /api/priorities/{id}/start` to confirm work (status: `in_progress`)
4. Agent performs research (events OR chunking recommendation)
5. Agent submits results via `POST /api/events/staged` with `priority_id`
6. Agent marks complete via `PUT /api/priorities/{id}/status` with `status: "completed"`

### Priority States Flow
- `pending` → `reserved` (1 hour timeout) → `in_progress` → `completed`
- `reserved` → `pending` (automatic after 1 hour timeout)
- `pending` → `failed` (if research cannot be completed)

### API Call Examples

**Reserve Priority:**
```bash
curl -X POST http://localhost:5558/api/priorities/next \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"agent_id": "agent-researcher-1"}'
```

**Confirm Work Started:**
```bash
curl -X PUT http://localhost:5558/api/priorities/RT-001/start \
  -H "X-API-Key: your-key"
```

**Submit Events:**
```bash
curl -X POST http://localhost:5558/api/events/staged \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "events": [...],
    "priority_id": "RT-001"
  }'
```

### Chunking Workflow
1. If agent determines scope too broad, return chunking recommendation
2. System creates new priorities from chunks
3. Original priority marked as `chunked`
4. New priorities available for assignment

This schema system ensures consistent data flow and prevents race conditions while enabling true parallel processing.