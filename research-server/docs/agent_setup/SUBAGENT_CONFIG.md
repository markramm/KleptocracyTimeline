# Subagent Configuration System v2

## Architecture Overview

This system uses a tiered approach with Claude Haiku for simple tasks and Opus/Sonnet for complex analysis, optimizing for both quality and cost.

## Agent Tiers and Model Assignment

### Tier 1: Simple Tasks (Claude Haiku)
Fast, cost-effective tasks that don't require deep reasoning:

#### Duplicate Checker Agent
```yaml
name: duplicate_checker
model: claude-3-haiku
max_tokens: 1000
tasks:
  - Check for exact date matches
  - Search for actor name matches
  - Compare event titles
  - Return similarity scores
api_endpoints:
  - GET /api/events/search
  - POST /api/events/check-duplicate
```

#### Date Extractor Agent
```yaml
name: date_extractor
model: claude-3-haiku
max_tokens: 500
tasks:
  - Extract dates from text
  - Normalize date formats
  - Identify date ranges
  - Return structured date data
```

#### Tag Generator Agent
```yaml
name: tag_generator
model: claude-3-haiku
max_tokens: 500
tasks:
  - Generate tags from event content
  - Standardize tag formats
  - Identify category tags
  - Return tag array
```

### Tier 2: Moderate Tasks (Claude Sonnet)
Tasks requiring reasoning but not deep analysis:

#### Event Validator Agent
```yaml
name: event_validator
model: claude-3-5-sonnet
max_tokens: 2000
tasks:
  - Validate event facts
  - Check source credibility
  - Score importance (1-10)
  - Identify missing information
api_endpoints:
  - GET /api/events/search
  - GET /api/priorities/export
```

#### Pattern Detector Agent
```yaml
name: pattern_detector
model: claude-3-5-sonnet
max_tokens: 3000
tasks:
  - Identify patterns across events
  - Find recurring actors
  - Detect systematic behaviors
  - Generate pattern reports
```

### Tier 3: Complex Tasks (Claude Opus/Sonnet)
Tasks requiring deep analysis and creative thinking:

#### Research Planner Agent
```yaml
name: research_planner
model: claude-3-opus
max_tokens: 4000
tasks:
  - Analyze research priorities
  - Generate research strategies
  - Identify knowledge gaps
  - Create detailed research plans
api_endpoints:
  - GET /api/priorities/next
  - PUT /api/priorities/{id}/status
  - GET /api/events/search
```

#### PDF Analyzer Agent
```yaml
name: pdf_analyzer
model: claude-3-opus
max_tokens: 8000
multimodal: true
tasks:
  - Process PDF documents
  - Extract timeline events
  - Identify key information
  - Generate research priorities
api_endpoints:
  - POST /api/events/staged
  - GET /api/events/search
```

## Orchestration Pattern

```python
class SubagentOrchestrator:
    def __init__(self):
        self.haiku_agents = ['duplicate_checker', 'date_extractor', 'tag_generator']
        self.sonnet_agents = ['event_validator', 'pattern_detector']
        self.opus_agents = ['research_planner', 'pdf_analyzer']
        
    async def process_research_task(self, task):
        # Step 1: Quick duplicate check (Haiku)
        duplicates = await self.run_agent('duplicate_checker', {
            'query': task.keywords,
            'date_range': task.date_range
        })
        
        if duplicates['has_exact_match']:
            return {'status': 'duplicate', 'existing': duplicates['matches']}
        
        # Step 2: Extract dates and tags (Haiku - parallel)
        dates_task = self.run_agent('date_extractor', {'text': task.content})
        tags_task = self.run_agent('tag_generator', {'text': task.content})
        dates, tags = await asyncio.gather(dates_task, tags_task)
        
        # Step 3: Validate importance (Sonnet)
        validation = await self.run_agent('event_validator', {
            'event': task.event_data,
            'dates': dates,
            'tags': tags
        })
        
        if validation['importance'] < 3:
            return {'status': 'low_priority', 'reason': validation['reason']}
        
        # Step 4: Deep research only if important (Opus)
        if validation['importance'] >= 7:
            research_plan = await self.run_agent('research_planner', {
                'event': task.event_data,
                'context': validation['context'],
                'gaps': validation['missing_info']
            })
            return {'status': 'research_needed', 'plan': research_plan}
        
        return {'status': 'ready_to_add', 'event': validation['enhanced_event']}
```

## Cost Optimization Strategies

### 1. Cascade Pattern
Start with cheapest model, escalate only when needed:
```python
async def cascade_analysis(content):
    # Try Haiku first
    haiku_result = await analyze_with_haiku(content)
    if haiku_result['confidence'] > 0.9:
        return haiku_result
    
    # Escalate to Sonnet if uncertain
    sonnet_result = await analyze_with_sonnet(content, haiku_result)
    if sonnet_result['confidence'] > 0.9:
        return sonnet_result
    
    # Use Opus only for complex cases
    return await analyze_with_opus(content, sonnet_result)
```

### 2. Batch Processing
Group similar tasks for efficiency:
```python
async def batch_duplicate_check(events):
    # Send all events to Haiku in one batch
    return await haiku_batch_api.check_duplicates(events)
```

### 3. Caching
Cache common queries:
```python
@cache(ttl=3600)
async def search_cached(query):
    return await api.search(query)
```

## API Integration Points

### Research Monitor v2 Integration
```yaml
base_url: http://localhost:5558
endpoints:
  search: /api/events/search
  priorities: /api/priorities/next
  stage_event: /api/events/staged
  commit_status: /api/commit/status
  stats: /api/stats
```

### Agent Communication Protocol
```python
class AgentMessage:
    def __init__(self, agent_id, task_type, payload):
        self.id = generate_id()
        self.agent_id = agent_id
        self.task_type = task_type
        self.payload = payload
        self.timestamp = datetime.now()
        self.model_tier = self.get_tier(agent_id)
    
    def get_tier(self, agent_id):
        if agent_id in haiku_agents:
            return 'haiku'
        elif agent_id in sonnet_agents:
            return 'sonnet'
        else:
            return 'opus'
```

## Prompt Templates

### Haiku Duplicate Check
```
Check if this event is a duplicate:
Date: {date}
Title: {title}
Actors: {actors}

Search the timeline for:
1. Events on the same date
2. Events with same actors
3. Similar titles

Return JSON:
{
  "is_duplicate": boolean,
  "confidence": 0.0-1.0,
  "similar_events": []
}
```

### Sonnet Pattern Detection
```
Analyze these events for patterns:
{events_json}

Identify:
1. Recurring actors and their roles
2. Systematic behaviors
3. Financial patterns
4. Timeline correlations

Return structured analysis with:
- Pattern name and description
- Events involved
- Actors network
- Significance score (1-10)
```

### Opus Research Planning
```
Context: {research_context}
Priority: {priority_details}
Existing Events: {related_events}

Create a comprehensive research plan:
1. Identify knowledge gaps
2. Suggest specific sources
3. Estimate number of events to discover
4. Provide search strategies
5. List key questions to answer

Focus on constitutional violations, systemic corruption, and network connections.
```

## Quality Control

### Validation Pipeline
```python
class QualityController:
    def validate_event(self, event):
        checks = [
            self.check_date_format(event),
            self.check_duplicate(event),
            self.check_importance_justified(event),
            self.check_summary_quality(event),
            self.check_source_credibility(event)
        ]
        
        return all(checks)
    
    async def check_duplicate(self, event):
        # Use Haiku for quick check
        result = await haiku_agent.check_duplicate(event)
        if result['confidence'] < 0.8:
            # Escalate to Sonnet for verification
            result = await sonnet_agent.verify_duplicate(event, result)
        return not result['is_duplicate']
```

## Monitoring and Metrics

### Cost Tracking
```python
class CostTracker:
    rates = {
        'haiku': 0.0025,  # per 1K tokens
        'sonnet': 0.015,   # per 1K tokens
        'opus': 0.075      # per 1K tokens
    }
    
    def track_usage(self, agent_id, tokens):
        tier = self.get_tier(agent_id)
        cost = (tokens / 1000) * self.rates[tier]
        self.log_usage(agent_id, tokens, cost)
        return cost
```

### Performance Metrics
```yaml
metrics:
  duplicate_detection:
    accuracy: 95%
    false_positives: < 2%
    false_negatives: < 5%
  
  cost_per_event:
    target: < $0.10
    current: $0.07
  
  processing_time:
    haiku_task: < 2s
    sonnet_task: < 5s
    opus_task: < 10s
```

## Deployment Configuration

### Environment Variables
```bash
# API Configuration
RESEARCH_MONITOR_URL=http://localhost:5558
API_KEY=your-api-key

# Model Configuration
HAIKU_MAX_CONCURRENT=10
SONNET_MAX_CONCURRENT=5
OPUS_MAX_CONCURRENT=2

# Cost Limits
DAILY_COST_LIMIT=50.00
HOURLY_COST_LIMIT=5.00

# Caching
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
```

### Docker Compose
```yaml
version: '3.8'
services:
  orchestrator:
    image: kleptocracy/orchestrator
    environment:
      - MODEL_TIER=mixed
    depends_on:
      - research_monitor
      - redis
  
  research_monitor:
    image: kleptocracy/research-monitor
    ports:
      - "5558:5558"
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

## Usage Examples

### Simple Duplicate Check (Haiku)
```python
# Fast, cheap duplicate detection
checker = DuplicateChecker(model='haiku')
result = await checker.check({
    'date': '2024-01-15',
    'title': 'Trump announces new policy',
    'actors': ['Trump']
})
# Cost: ~$0.002
```

### Complex Research (Orchestrated)
```python
# Full pipeline with model escalation
orchestrator = SubagentOrchestrator()
result = await orchestrator.process_research_task({
    'type': 'pdf_analysis',
    'file': 'senate_report.pdf'
})
# Cost: ~$0.05-0.15 depending on complexity
```

### Batch Processing (Haiku)
```python
# Process multiple simple tasks efficiently
batch = BatchProcessor(model='haiku')
results = await batch.process([
    {'task': 'extract_date', 'text': text1},
    {'task': 'extract_date', 'text': text2},
    {'task': 'generate_tags', 'text': text3}
])
# Cost: ~$0.01 for all
```

## Best Practices

1. **Always start with Haiku** for simple extraction and matching
2. **Use Sonnet** for validation and pattern detection
3. **Reserve Opus** for creative research and complex analysis
4. **Batch similar tasks** to reduce API calls
5. **Cache frequently accessed data** to avoid repeated searches
6. **Monitor costs continuously** and adjust thresholds
7. **Validate outputs** at each tier before escalation

## Error Handling

```python
class AgentErrorHandler:
    async def handle_error(self, error, agent_id, task):
        if isinstance(error, RateLimitError):
            await self.wait_and_retry(agent_id, task)
        elif isinstance(error, ModelOverloadError):
            await self.escalate_to_higher_tier(agent_id, task)
        elif isinstance(error, InvalidResponseError):
            await self.retry_with_refined_prompt(agent_id, task)
        else:
            await self.log_and_alert(error, agent_id, task)
```

This configuration provides a cost-effective, high-quality agentic system that leverages Claude Haiku for simple tasks while maintaining the ability to escalate to more powerful models when needed.