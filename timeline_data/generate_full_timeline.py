#!/usr/bin/env python3
"""
Generate a complete timeline in a single markdown file with all event content.
Includes all metadata, sources, and formatting for easy reading and sharing.
"""

import os
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

def load_event(filepath: Path) -> Dict[str, Any]:
    """Load and parse a YAML event file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def format_importance(importance: int) -> str:
    """Format importance with visual indicators."""
    if importance >= 9:
        return f"🔴 **Critical ({importance}/10)**"
    elif importance >= 7:
        return f"🟠 **High ({importance}/10)**"
    elif importance >= 5:
        return f"🟡 **Medium ({importance}/10)**"
    else:
        return f"⚪ **Low ({importance}/10)**"

def format_tags(tags: List[str]) -> str:
    """Format tags as inline badges."""
    if not tags:
        return ""
    return " ".join([f"`{tag}`" for tag in tags[:8]])  # Limit to 8 for readability

def format_sources(sources: List[Dict]) -> str:
    """Format sources with links and metadata."""
    if not sources:
        return "*No sources listed*"
    
    formatted = []
    for i, source in enumerate(sources, 1):
        title = source.get('title', 'Untitled')
        url = source.get('url', '')
        outlet = source.get('outlet', 'Unknown')
        date = source.get('date', '')
        archive_url = source.get('archive_url', '')
        
        # Main source link
        source_str = f"{i}. [{title}]({url})"
        
        # Add metadata
        meta_parts = []
        if outlet:
            meta_parts.append(f"*{outlet}*")
        if date:
            meta_parts.append(date)
        
        if meta_parts:
            source_str += f" - {', '.join(meta_parts)}"
        
        # Add archive link if available
        if archive_url:
            source_str += f" ([archived]({archive_url}))"
        
        formatted.append(source_str)
    
    return "\n".join(formatted)

def format_actors(actors: List[str]) -> str:
    """Format actors as a readable list."""
    if not actors:
        return ""
    
    if len(actors) <= 3:
        return ", ".join(actors)
    else:
        # Show first 3 and count of others
        shown = ", ".join(actors[:3])
        others = len(actors) - 3
        return f"{shown}, and {others} others"

def format_capture_lanes(lanes: List[str]) -> str:
    """Format capture lanes with icons."""
    if not lanes:
        return ""
    
    lane_icons = {
        "Judicial Capture & Corruption": "⚖️",
        "Financial Corruption & Kleptocracy": "💰",
        "Constitutional & Democratic Breakdown": "📜",
        "Foreign Influence Operations": "🌍",
        "Information & Media Control": "📡",
        "Executive Power & Emergency Authority": "🏛️",
        "Federal Workforce Capture": "👥",
        "Corporate Capture & Regulatory Breakdown": "🏢",
        "Election System Attack": "🗳️"
    }
    
    formatted = []
    for lane in lanes:
        icon = lane_icons.get(lane, "▪️")
        formatted.append(f"{icon} {lane}")
    
    return " | ".join(formatted)

def generate_timeline_markdown(events_dir: Path, output_file: Path):
    """Generate the complete timeline markdown file."""
    
    # Load all events
    events = []
    for filepath in events_dir.glob("*.yaml"):
        try:
            event_data = load_event(filepath)
            if event_data:
                events.append(event_data)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    
    # Sort by date (handle both string and date objects)
    events.sort(key=get_sort_date)
    
    # Group by year for better organization
    events_by_year = {}
    for event in events:
        date = event.get('date', '')
        # Handle both string dates and date objects
        if isinstance(date, str):
            year = date[:4] if date else 'Unknown'
        elif hasattr(date, 'year'):
            year = str(date.year)
        else:
            year = 'Unknown'
        if year not in events_by_year:
            events_by_year[year] = []
        events_by_year[year].append(event)
    
    # Start building the markdown
    md_lines = []
    
    # Header
    md_lines.append("# 🏛️ The Kleptocracy Timeline: Complete Archive")
    md_lines.append("")
    md_lines.append(f"*Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
    md_lines.append("")
    
    # Executive Summary
    md_lines.append("## 📊 Executive Summary")
    md_lines.append("")
    md_lines.append(f"- **Total Events**: {len(events)}")
    # Get date range
    first_date = events[0].get('date', 'Unknown') if events else 'Unknown'
    last_date = events[-1].get('date', 'Unknown') if events else 'Unknown'
    # Convert to strings if needed
    if hasattr(first_date, 'isoformat'):
        first_date = first_date.isoformat()
    if hasattr(last_date, 'isoformat'):
        last_date = last_date.isoformat()
    md_lines.append(f"- **Date Range**: {first_date} to {last_date}")
    
    # Count importance levels
    critical = sum(1 for e in events if e.get('importance', 0) >= 9)
    high = sum(1 for e in events if 7 <= e.get('importance', 0) < 9)
    md_lines.append(f"- **Critical Events**: {critical}")
    md_lines.append(f"- **High Importance Events**: {high}")
    
    # Count capture lanes
    all_lanes = set()
    for event in events:
        lanes = event.get('capture_lanes', [])
        if lanes:
            all_lanes.update(lanes)
    md_lines.append(f"- **Capture Lanes Documented**: {len(all_lanes)}")
    md_lines.append("")
    
    # Table of Contents
    md_lines.append("## 📑 Table of Contents")
    md_lines.append("")
    md_lines.append("Jump to year: ", )
    year_links = []
    for year in sorted(events_by_year.keys()):
        if year != 'Unknown':
            count = len(events_by_year[year])
            year_links.append(f"[{year} ({count})](#year-{year})")
    md_lines.append(" | ".join(year_links))
    md_lines.append("")
    
    # Pattern Analysis Link
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## 🔍 Pattern Analysis")
    md_lines.append("")
    md_lines.append("For comprehensive analysis of patterns and trends, see [PATTERN_ANALYSIS.md](PATTERN_ANALYSIS.md)")
    md_lines.append("")
    
    # Events by Year
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## 📅 Complete Timeline")
    md_lines.append("")
    
    for year in sorted(events_by_year.keys()):
        if year == 'Unknown':
            continue
            
        year_events = events_by_year[year]
        
        # Year header
        md_lines.append(f"### Year: {year}")
        md_lines.append("")
        md_lines.append(f"*{len(year_events)} events*")
        md_lines.append("")
        
        # Events in this year
        for event in year_events:
            # Event header with date and title
            date_val = event.get('date', 'Unknown')
            # Convert date objects to string
            if hasattr(date_val, 'isoformat'):
                date = date_val.isoformat()
            else:
                date = str(date_val)
            title = event.get('title', 'Untitled')
            importance = event.get('importance', 5)
            event_id = event.get('id', '')
            
            md_lines.append(f"#### 📌 {date}: {title}")
            md_lines.append("")
            
            # Importance and Status
            md_lines.append(f"**Importance**: {format_importance(importance)}")
            status = event.get('status', 'confirmed')
            status_emoji = "✅" if status == 'confirmed' else "⏳" if status == 'pending' else "❓"
            md_lines.append(f"**Status**: {status_emoji} {status.title()}")
            
            # Location
            location = event.get('location', '')
            if location:
                md_lines.append(f"**Location**: 📍 {location}")
            
            md_lines.append("")
            
            # Summary
            summary = event.get('summary', '')
            if summary:
                md_lines.append("**Summary**:")
                md_lines.append(f"> {summary}")
                md_lines.append("")
            
            # Key Actors
            actors = event.get('actors', [])
            if actors:
                md_lines.append(f"**Key Actors**: {format_actors(actors)}")
                md_lines.append("")
            
            # Capture Lanes
            lanes = event.get('capture_lanes', [])
            if lanes:
                md_lines.append(f"**Capture Lanes**: {format_capture_lanes(lanes)}")
                md_lines.append("")
            
            # Tags
            tags = event.get('tags', [])
            if tags:
                md_lines.append(f"**Tags**: {format_tags(tags)}")
                md_lines.append("")
            
            # Sources
            sources = event.get('sources', [])
            if sources:
                md_lines.append("**Sources**:")
                md_lines.append(format_sources(sources))
                md_lines.append("")
            
            # Notes
            notes = event.get('notes', '')
            if notes:
                md_lines.append("**Additional Notes**:")
                md_lines.append(f"> {notes}")
                md_lines.append("")
            
            # Event ID for reference
            if event_id:
                md_lines.append(f"*Event ID: `{event_id}`*")
                md_lines.append("")
            
            # Separator
            md_lines.append("---")
            md_lines.append("")
    
    # Footer
    md_lines.append("## 📚 Additional Resources")
    md_lines.append("")
    md_lines.append("- **Repository**: [GitHub - Kleptocracy Timeline](https://github.com/yourusername/kleptocracy-timeline)")
    md_lines.append("- **Validation Tool**: Run `python3 validation_app_enhanced.py` to verify sources")
    md_lines.append("- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) to add or validate events")
    md_lines.append("- **Pattern Analysis**: See [PATTERN_ANALYSIS.md](PATTERN_ANALYSIS.md) for trends")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("*This timeline documents the systematic capture of democratic institutions through "
                    "verified sources and evidence. Every event has been documented with multiple sources "
                    "where possible. Help us validate and expand this historical record.*")
    md_lines.append("")
    md_lines.append("**License**: Data (CC-BY-SA-4.0) | Code (MIT)")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    print(f"✅ Timeline generated successfully!")
    print(f"📄 Output: {output_file}")
    print(f"📊 Total events: {len(events)}")
    print(f"📅 Years covered: {len(events_by_year) - (1 if 'Unknown' in events_by_year else 0)}")

def generate_summary_stats(events: List[Dict]) -> Dict:
    """Generate summary statistics for the timeline."""
    stats = {
        'total_events': len(events),
        'date_range': '',
        'importance_breakdown': {},
        'top_actors': {},
        'top_tags': {},
        'capture_lanes': {},
        'sources_count': 0
    }
    
    # Calculate various statistics
    all_actors = []
    all_tags = []
    all_lanes = []
    total_sources = 0
    
    for event in events:
        # Actors
        actors = event.get('actors', [])
        all_actors.extend(actors)
        
        # Tags
        tags = event.get('tags', [])
        all_tags.extend(tags)
        
        # Capture lanes
        lanes = event.get('capture_lanes', [])
        all_lanes.extend(lanes)
        
        # Sources
        sources = event.get('sources', [])
        total_sources += len(sources)
    
    # Count frequencies
    from collections import Counter
    stats['top_actors'] = dict(Counter(all_actors).most_common(10))
    stats['top_tags'] = dict(Counter(all_tags).most_common(10))
    stats['capture_lanes'] = dict(Counter(all_lanes).most_common())
    stats['sources_count'] = total_sources
    
    return stats

def get_sort_date(event):
    """Get sortable date from event, handling different date types."""
    date = event.get('date', '')
    if isinstance(date, str):
        return date
    elif hasattr(date, 'isoformat'):
        return date.isoformat()
    else:
        return str(date)

if __name__ == "__main__":
    # Set up paths
    events_dir = Path("events")
    output_file = Path("COMPLETE_TIMELINE.md")
    
    # Check if events directory exists
    if not events_dir.exists():
        print(f"❌ Error: Events directory '{events_dir}' not found!")
        exit(1)
    
    # Generate the timeline
    try:
        generate_timeline_markdown(events_dir, output_file)
        
        # Also generate a JSON version for programmatic use
        events = []
        for filepath in events_dir.glob("*.yaml"):
            try:
                event_data = load_event(filepath)
                if event_data:
                    events.append(event_data)
            except Exception as e:
                print(f"Warning: Could not load {filepath}: {e}")
        
        # Sort and save as JSON
        events.sort(key=get_sort_date)
        with open('timeline_complete.json', 'w') as f:
            json.dump(events, f, indent=2, default=str)
        print(f"📊 JSON version saved to: timeline_complete.json")
        
    except Exception as e:
        print(f"❌ Error generating timeline: {e}")
        exit(1)