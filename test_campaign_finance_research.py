#!/usr/bin/env python3
"""
Test script to demonstrate the campaign finance research capabilities
"""

from research_api import ResearchAPI
from research_executor import ResearchExecutor

def test_campaign_finance_research():
    """Test the specialized campaign finance research"""
    
    # Create executor
    executor = ResearchExecutor(base_url='http://localhost:5560', api_key='test')
    
    # Create a mock campaign finance priority
    mock_priority = {
        'id': 'RT-TEST-corporate-pac-explosion-post-buckley',
        'title': 'Corporate PAC Explosion Post-Buckley',
        'description': 'Document corporate PAC proliferation following Buckley v. Valeo implementation',
        'tags': ['campaign_finance', 'corporate_pacs', 'buckley_valeo', 'systematic_corruption'],
        'status': 'pending',
        'priority': 'high'
    }
    
    print("=== Testing Campaign Finance Research ===")
    print(f"Priority: {mock_priority['title']}")
    print(f"Tags: {mock_priority['tags']}")
    print()
    
    # Test the research method directly
    print("Testing campaign finance topic detection...")
    is_finance = executor.is_campaign_finance_topic(mock_priority)
    print(f"Is campaign finance topic: {is_finance}")
    print()
    
    if is_finance:
        print("Running specialized campaign finance research...")
        events = executor.research_campaign_finance(mock_priority)
        
        print(f"Generated {len(events)} timeline events:")
        for i, event in enumerate(events, 1):
            print(f"\n--- Event {i} ---")
            print(f"Date: {event['date']}")
            print(f"Title: {event['title']}")
            print(f"Importance: {event['importance']}")
            print(f"Tags: {event['tags']}")
            print(f"Summary (first 150 chars): {event['summary'][:150]}...")
            print(f"Actors: {event['actors']}")
            print(f"Sources: {len(event['sources'])} sources")
        
        # Test submitting the events
        if events:
            print(f"\nSubmitting {len(events)} events to server...")
            try:
                result = executor.api.submit_events_batch(events, mock_priority['id'])
                print(f"Results: {result['successful_events']} successful, {result['failed_events']} failed")
                
                if result['failed_events'] > 0:
                    print("Failed events details:")
                    for res in result.get('results', []):
                        if res['status'] == 'failed':
                            print(f"  Event {res['index']}: {res['errors']}")
                
                return result['successful_events']
            except Exception as e:
                print(f"Error submitting events: {e}")
                return 0
    else:
        print("Priority not detected as campaign finance topic")
        return 0

if __name__ == "__main__":
    try:
        events_created = test_campaign_finance_research()
        print(f"\nFinal result: {events_created} events successfully created")
    except Exception as e:
        print(f"Test failed: {e}")