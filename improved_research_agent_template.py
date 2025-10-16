#!/usr/bin/env python3
"""
Improved Research Agent Template with Enhanced Validation
Demonstrates proper event creation with validation and fixing
"""

from research_api import ResearchAPI
from enhanced_event_validator import TimelineEventValidator
import json

def create_properly_formatted_event(title: str, date: str, summary: str, importance: int, 
                                   actors: list, sources: list, tags: list, 
                                   location: str = None) -> dict:
    """
    Create a properly formatted timeline event that meets all schema requirements
    
    Args:
        title: Event title 
        date: Date in YYYY-MM-DD format
        summary: Detailed summary of the event
        importance: Importance score 1-10
        actors: List of actors involved
        sources: List of source objects with title, url, outlet
        tags: List of tags for categorization
        location: Optional location
        
    Returns:
        Properly formatted timeline event dict
    """
    # Create slug from title for ID
    import re
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
    slug = re.sub(r'\s+', '-', slug)[:60].strip('-')
    
    event = {
        'id': f"{date}--{slug}",
        'date': date,
        'title': title,
        'summary': summary,
        'importance': importance,
        'actors': actors,
        'sources': sources,
        'tags': tags,
        'status': 'confirmed'
    }
    
    if location:
        event['location'] = location
    
    # Infer capture lanes from content
    validator = TimelineEventValidator()
    event['capture_lanes'] = validator._infer_capture_lanes(event)
    
    return event

def create_source_object(title: str, url: str, outlet: str, date: str = None) -> dict:
    """
    Create a properly formatted source object
    
    Args:
        title: Title of the source article/document
        url: URL to the source
        outlet: Publishing outlet (e.g., "New York Times", "SEC", "DOJ")
        date: Publication date (optional)
        
    Returns:
        Properly formatted source object
    """
    source = {
        'title': title,
        'url': url, 
        'outlet': outlet
    }
    
    if date:
        source['date'] = date
        
    return source

def example_research_workflow():
    """
    Example of proper research workflow with validation
    """
    # Initialize API client
    api = ResearchAPI(base_url='http://localhost:5560', api_key='test')
    
    # Reserve a priority
    try:
        priority = api.reserve_priority('improved-research-agent')
        print(f"Reserved priority: {priority['id']}")
        
        # Confirm work started
        api.confirm_work_started(priority['id'])
        
        # Example: Create a properly formatted event
        event = create_properly_formatted_event(
            title="Example Trump DOJ Weaponization Event",
            date="2025-02-15",
            summary="Attorney General directs systematic targeting of prosecutors who investigated Trump cases, firing 15 federal prosecutors in coordinated purge. This represents escalation of DOJ weaponization for political retaliation, undermining prosecutorial independence and rule of law.",
            importance=9,
            actors=[
                "Attorney General",
                "Department of Justice", 
                "Federal Prosecutors",
                "Trump Administration"
            ],
            sources=[
                create_source_object(
                    title="DOJ Fires 15 Prosecutors in Trump Investigation Purge",
                    url="https://example.com/doj-purge-2025",
                    outlet="Washington Post",
                    date="2025-02-15"
                )
            ],
            tags=[
                "DOJ weaponization",
                "prosecutorial independence", 
                "Trump administration",
                "retaliation",
                "rule of law"
            ],
            location="Washington, D.C."
        )
        
        # Validate the event before submission
        print("\nValidating event before submission...")
        validation_result = api.validate_event(event, auto_fix=True)
        
        if validation_result['is_valid']:
            print("✅ Event passed validation")
        else:
            print(f"⚠️  Event has {len(validation_result['errors'])} errors")
            print("Using auto-fixed version...")
            event = validation_result['fixed_event']
        
        # Submit the event
        events = [event]
        result = api.submit_events_batch(events, priority['id'])
        
        print(f"\nSubmission result: {result}")
        
        if result.get('successful_events', 0) > 0:
            print("✅ Event successfully submitted!")
            
            # Complete the priority
            api.complete_priority(priority['id'], events_created=1, 
                                notes="Successfully created systematic corruption event with validation")
        else:
            print("❌ Event submission failed")
            
    except Exception as e:
        print(f"Error in research workflow: {e}")

# Agent prompt template with improved validation guidance
IMPROVED_RESEARCH_AGENT_PROMPT = """
ENHANCED RESEARCH EXECUTION TASK

You are a research agent with enhanced validation capabilities. Use the improved workflow for creating timeline events.

SERVER ENDPOINT: {server_endpoint}
API KEY: {api_key}

ENHANCED WORKFLOW:
```python
from research_api import ResearchAPI
from enhanced_event_validator import TimelineEventValidator

# Initialize with validation
api = ResearchAPI(base_url='{server_endpoint}', api_key='{api_key}')

# Reserve and confirm priority
priority = api.reserve_priority('research-agent-{agent_id}')
api.confirm_work_started(priority['id'])

# Create properly formatted events
events = []
for research_finding in your_research:
    event = {{
        'id': f"{{research_finding['date']}}--{{slug_from_title}}",
        'date': research_finding['date'],  # MUST be YYYY-MM-DD format
        'title': research_finding['title'],
        'summary': research_finding['detailed_summary'],  # REQUIRED field
        'importance': research_finding['importance'],  # Integer 1-10
        'actors': research_finding['actors'],  # List of strings
        'sources': [  # List of source objects
            {{
                'title': 'Source title',
                'url': 'https://credible-source.com',
                'outlet': 'Credible Outlet Name'  # REQUIRED
            }}
        ],
        'tags': research_finding['tags'],  # List of strings
        'status': 'confirmed'  # Optional but recommended
    }}
    
    # Validate BEFORE adding to list
    validation = api.validate_event(event, auto_fix=True)
    if validation['is_valid'] or validation['fixes_applied'] > 0:
        events.append(validation['fixed_event'])
    else:
        print(f"Skipping invalid event: {{validation['errors']}}")

# Submit with auto-validation
result = api.submit_events_batch(events, priority['id'], auto_fix=True)
print(f"Submitted {{result.get('successful_events', 0)}} events successfully")

# Complete priority
api.complete_priority(priority['id'], len(events))
```

CRITICAL REQUIREMENTS:
1. **summary field is REQUIRED** - provide detailed context
2. **sources must have outlet field** - specify publishing organization
3. **ID format**: YYYY-MM-DD--descriptive-slug (auto-fixed if wrong)
4. **date format**: YYYY-MM-DD (auto-fixed if wrong)
5. **Use validation** - call api.validate_event() before submission

VALIDATION FEATURES:
- Auto-fixes common format issues
- Adds missing required fields with placeholders
- Provides detailed error feedback
- Infers capture_lanes automatically

CREATE SYSTEMATIC CORRUPTION EVENTS:
Focus on coordinated institutional capture patterns with specific:
- Dates and actors involved
- Mechanisms of coordination
- Sources with credible outlets
- Clear connection to broader corruption patterns

The enhanced validation will help you create high-quality events that integrate successfully into the timeline.
"""

if __name__ == "__main__":
    # Run example workflow
    print("Running improved research agent example...")
    example_research_workflow()