#!/usr/bin/env python3
"""
Save generated timeline events to the timeline_data/events directory
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_timeline_event_id(event_data: Dict) -> str:
    """Create a unique ID for a timeline event"""
    date = event_data.get('date', '2025-01-01')
    title = event_data.get('title', 'unknown-event')
    
    # Clean title for filename
    clean_title = title.lower()
    clean_title = ''.join(c if c.isalnum() or c in '-_' else '-' for c in clean_title)
    clean_title = '-'.join(word for word in clean_title.split('-') if word)
    clean_title = clean_title[:60]  # Limit length
    
    return f"{date}--{clean_title}"

def save_timeline_event(event_data: Dict) -> bool:
    """Save a single timeline event to the timeline_data/events directory"""
    try:
        # Ensure timeline_data/events directory exists
        events_dir = Path("timeline_data/events")
        events_dir.mkdir(parents=True, exist_ok=True)
        
        # Create event ID and filename
        if 'id' not in event_data:
            event_data['id'] = create_timeline_event_id(event_data)
        
        event_id = event_data['id']
        filename = f"{event_id}.json"
        filepath = events_dir / filename
        
        # Check if event already exists
        if filepath.exists():
            logger.info(f"Event {event_id} already exists, skipping")
            return False
        
        # Ensure required fields are present
        required_fields = ['date', 'title', 'summary', 'importance', 'actors', 'tags']
        for field in required_fields:
            if field not in event_data:
                if field == 'importance':
                    event_data[field] = 7
                elif field == 'actors':
                    event_data[field] = []
                elif field == 'tags':
                    event_data[field] = []
                elif field == 'summary':
                    event_data[field] = event_data.get('description', 'No summary provided')
                else:
                    logger.warning(f"Missing required field {field} for event {event_id}")
                    return False
        
        # Add metadata
        event_data['category'] = event_data.get('category', 'constitutional-crisis')
        event_data['verification_status'] = event_data.get('verification_status', 'documented')
        
        # Save the event
        with open(filepath, 'w') as f:
            json.dump(event_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved timeline event: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving timeline event: {str(e)}")
        return False

def save_timeline_events_batch(events: List[Dict]) -> int:
    """Save a batch of timeline events and return count of successfully saved events"""
    saved_count = 0
    
    for event in events:
        if save_timeline_event(event):
            saved_count += 1
    
    logger.info(f"Saved {saved_count}/{len(events)} timeline events")
    return saved_count

def research_and_save_events_from_priority(priority_data: Dict) -> int:
    """Generate events from research priority and save them to timeline"""
    from api.claude_research_integration import research_timeline_events_with_claude
    
    try:
        # Generate events
        events = research_timeline_events_with_claude(priority_data)
        
        if not events:
            logger.warning(f"No events generated for priority: {priority_data.get('id', 'unknown')}")
            return 0
        
        # Save events to timeline
        saved_count = save_timeline_events_batch(events)
        
        # Update the research priority with correct completion tracking
        if saved_count > 0:
            update_research_priority_completion(priority_data, saved_count)
        
        return saved_count
        
    except Exception as e:
        logger.error(f"Error generating and saving events: {str(e)}")
        return 0

def update_research_priority_completion(priority_data: Dict, events_saved: int):
    """Update research priority with accurate completion tracking"""
    try:
        priority_id = priority_data.get('id', 'unknown')
        priority_file = Path(f"research_priorities/{priority_id}.json")
        
        if not priority_file.exists():
            logger.warning(f"Priority file not found: {priority_file}")
            return
        
        # Read current priority data
        with open(priority_file, 'r') as f:
            current_data = json.load(f)
        
        # Update with accurate completion info
        current_data['actual_events'] = events_saved
        current_data['status'] = 'completed' if events_saved > 0 else 'pending'
        current_data['completion_date'] = '2025-09-06'
        current_data['updated_date'] = '2025-09-06'
        
        # Save updated priority
        with open(priority_file, 'w') as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated priority {priority_id}: {events_saved} events saved, status: {current_data['status']}")
        
    except Exception as e:
        logger.error(f"Error updating priority completion: {str(e)}")

if __name__ == "__main__":
    # Test with a sample event
    sample_event = {
        "date": "2025-09-06",
        "title": "Test Timeline Event Creation System",
        "summary": "Testing the enhanced timeline event saving functionality to ensure events are properly persisted to the timeline_data/events directory with proper metadata and formatting.",
        "importance": 6,
        "actors": ["Timeline System", "Research Integration"],
        "tags": ["system-test", "timeline-validation", "event-persistence"],
        "category": "system-test",
        "verification_status": "confirmed"
    }
    
    logger.info("Testing timeline event saving functionality...")
    success = save_timeline_event(sample_event)
    
    if success:
        logger.info("✅ Timeline event saving working correctly!")
    else:
        logger.error("❌ Timeline event saving failed!")