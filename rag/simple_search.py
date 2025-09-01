#!/usr/bin/env python3
"""Simple search functionality for timeline events."""

import json
from typing import List, Dict, Any
from pathlib import Path

class SimpleSearch:
    """Simple keyword-based search for timeline events."""
    
    def __init__(self, data_file: str = 'timeline_events.json'):
        """Load timeline events."""
        self.events = []
        data_path = Path(data_file)
        
        if data_path.exists():
            with open(data_path, 'r') as f:
                self.events = json.load(f)
            print(f"Loaded {len(self.events)} events")
        else:
            print(f"Error: {data_file} not found")
    
    def search(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search events by keyword.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of matching events
        """
        query_lower = query.lower()
        matches = []
        
        for event in self.events:
            # Calculate relevance score
            score = 0
            
            # Check title (highest weight)
            if query_lower in event.get('title', '').lower():
                score += 10
            
            # Check summary (medium weight)
            if query_lower in event.get('summary', '').lower():
                score += 5
            
            # Check actors (medium weight)
            for actor in event.get('actors', []):
                if query_lower in actor.lower():
                    score += 5
                    break
            
            # Check tags (low weight)
            for tag in event.get('tags', []):
                if query_lower in tag.lower():
                    score += 2
                    break
            
            # Check date
            if query_lower in event.get('date', ''):
                score += 3
            
            if score > 0:
                matches.append((score, event))
        
        # Sort by score (descending) then by date (descending)
        matches.sort(key=lambda x: (-x[0], x[1].get('date', '')), reverse=True)
        
        # Return just the events (without scores)
        return [event for _, event in matches[:max_results]]
    
    def search_multiple(self, terms: List[str], require_all: bool = False, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search with multiple terms.
        
        Args:
            terms: List of search terms
            require_all: If True, all terms must match. If False, any term can match.
            max_results: Maximum results to return
            
        Returns:
            List of matching events
        """
        matches = []
        
        for event in self.events:
            event_text = f"{event.get('title', '')} {event.get('summary', '')} {' '.join(event.get('actors', []))} {' '.join(event.get('tags', []))}".lower()
            
            if require_all:
                # All terms must be present
                if all(term.lower() in event_text for term in terms):
                    matches.append(event)
            else:
                # Any term can match
                if any(term.lower() in event_text for term in terms):
                    matches.append(event)
        
        # Sort by date descending
        matches.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return matches[:max_results]
    
    def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        Get events within a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of events in date range
        """
        matches = []
        
        for event in self.events:
            event_date = event.get('date', '')
            if start_date <= event_date <= end_date:
                matches.append(event)
        
        matches.sort(key=lambda x: x.get('date', ''), reverse=True)
        return matches
    
    def get_by_actor(self, actor_name: str) -> List[Dict[str, Any]]:
        """Get all events involving a specific actor."""
        actor_lower = actor_name.lower()
        matches = []
        
        for event in self.events:
            actors = [a.lower() for a in event.get('actors', [])]
            if any(actor_lower in a for a in actors):
                matches.append(event)
        
        matches.sort(key=lambda x: x.get('date', ''), reverse=True)
        return matches
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the timeline."""
        if not self.events:
            return {"error": "No events loaded"}
        
        # Date range
        dates = [e.get('date', '') for e in self.events if e.get('date')]
        dates.sort()
        
        # Actor frequency
        actor_count = {}
        for event in self.events:
            for actor in event.get('actors', []):
                actor_count[actor] = actor_count.get(actor, 0) + 1
        
        # Tag frequency
        tag_count = {}
        for event in self.events:
            for tag in event.get('tags', []):
                tag_count[tag] = tag_count.get(tag, 0) + 1
        
        # Sort by frequency
        top_actors = sorted(actor_count.items(), key=lambda x: x[1], reverse=True)[:10]
        top_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_events": len(self.events),
            "date_range": f"{dates[0]} to {dates[-1]}" if dates else "No dates",
            "top_actors": top_actors,
            "top_tags": top_tags
        }


def main():
    """Test the search functionality."""
    search = SimpleSearch()
    
    # Test single term search
    print("\n" + "="*60)
    print("Searching for 'Epstein':")
    results = search.search("Epstein", max_results=5)
    for i, event in enumerate(results, 1):
        print(f"{i}. {event.get('date')}: {event.get('title', '')[:60]}...")
    
    # Test multi-term search
    print("\n" + "="*60)
    print("Searching for 'money laundering' (all terms):")
    results = search.search_multiple(["money", "laundering"], require_all=True, max_results=5)
    for i, event in enumerate(results, 1):
        print(f"{i}. {event.get('date')}: {event.get('title', '')[:60]}...")
    
    # Get stats
    print("\n" + "="*60)
    print("Timeline Statistics:")
    stats = search.get_stats()
    print(f"Total events: {stats['total_events']}")
    print(f"Date range: {stats['date_range']}")
    print(f"Top 5 actors: {stats['top_actors'][:5]}")
    print(f"Top 5 tags: {stats['top_tags'][:5]}")


if __name__ == "__main__":
    main()