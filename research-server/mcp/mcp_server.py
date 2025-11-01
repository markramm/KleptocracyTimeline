#!/usr/bin/env python3
"""
Modern MCP Server for Kleptocracy Timeline Research System

Uses the TimelineResearchClient for direct API integration with comprehensive
research capabilities including event search, QA workflows, validation,
and research priority management.
"""

import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Import our research client
from research_client import TimelineResearchClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimelineResearchMCPServer:
    """Modern MCP Server for timeline research using direct API integration."""
    
    def __init__(self):
        self.server = Server("timeline-research")
        self.client = None
        
        # Register handlers
        self.setup_handlers()
        
    def setup_handlers(self):
        """Set up MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available research tools."""
            return [
                # Search & Discovery Tools
                types.Tool(
                    name="search_events",
                    description="Search timeline events with full-text search and filters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                            "actor": {"type": "string", "description": "Filter by actor"},
                            "tag": {"type": "string", "description": "Filter by tag"},
                            "min_importance": {"type": "integer", "description": "Minimum importance (1-10)"},
                            "limit": {"type": "integer", "description": "Max results", "default": 20}
                        },
                        "required": []
                    }
                ),
                
                types.Tool(
                    name="get_event",
                    description="Get a specific event by ID with full details",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "event_id": {"type": "string", "description": "Event ID to retrieve"}
                        },
                        "required": ["event_id"]
                    }
                ),
                
                types.Tool(
                    name="analyze_actor",
                    description="Comprehensive analysis of an actor's timeline and connections",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "actor_name": {"type": "string", "description": "Name of actor to analyze"}
                        },
                        "required": ["actor_name"]
                    }
                ),
                
                # Quality Assurance Tools
                types.Tool(
                    name="get_qa_queue", 
                    description="Get events prioritized for quality assurance review",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "description": "Max events to return", "default": 20},
                            "offset": {"type": "integer", "description": "Offset for pagination", "default": 0}
                        },
                        "required": []
                    }
                ),
                
                types.Tool(
                    name="validate_event",
                    description="Validate an event's schema and data quality",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "event_data": {"type": "object", "description": "Event data to validate"}
                        },
                        "required": ["event_data"]
                    }
                ),
                
                types.Tool(
                    name="mark_event_validated",
                    description="Mark an event as validated with quality score",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "event_id": {"type": "string", "description": "Event ID"},
                            "quality_score": {"type": "number", "description": "Quality score (0-10)"},
                            "notes": {"type": "string", "description": "Validation notes"},
                            "validator_id": {"type": "string", "description": "Validator identifier"}
                        },
                        "required": ["event_id", "quality_score"]
                    }
                ),
                
                # Research Discovery Tools
                types.Tool(
                    name="get_missing_sources",
                    description="Find events that need additional sources",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "min_sources": {"type": "integer", "description": "Minimum required sources", "default": 2},
                            "limit": {"type": "integer", "description": "Max results", "default": 20}
                        },
                        "required": []
                    }
                ),
                
                types.Tool(
                    name="get_research_candidates",
                    description="Get high-importance events needing research enhancement",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "min_importance": {"type": "integer", "description": "Minimum importance level", "default": 7},
                            "limit": {"type": "integer", "description": "Max results", "default": 20}
                        },
                        "required": []
                    }
                ),
                
                types.Tool(
                    name="get_validation_queue",
                    description="Get events prioritized for fact-checking and validation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "description": "Max results", "default": 20}
                        },
                        "required": []
                    }
                ),
                
                # Research Priority Management
                types.Tool(
                    name="get_next_priority",
                    description="Get the next research priority task",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                
                types.Tool(
                    name="update_priority",
                    description="Update research priority status and progress", 
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "priority_id": {"type": "string", "description": "Priority ID"},
                            "status": {"type": "string", "description": "New status"},
                            "notes": {"type": "string", "description": "Progress notes"},
                            "actual_events": {"type": "integer", "description": "Number of events created"}
                        },
                        "required": ["priority_id", "status"]
                    }
                ),
                
                # Event Creation Tools
                types.Tool(
                    name="create_event",
                    description="Create a new timeline event",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "event_data": {"type": "object", "description": "Complete event data"}
                        },
                        "required": ["event_data"]
                    }
                ),
                
                # System Information Tools
                types.Tool(
                    name="get_stats",
                    description="Get comprehensive timeline statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                
                types.Tool(
                    name="get_qa_stats", 
                    description="Get quality assurance system statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                
                types.Tool(
                    name="list_actors",
                    description="Get list of all actors in the timeline",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                
                types.Tool(
                    name="list_tags",
                    description="Get list of all tags used in the timeline", 
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, 
            arguments: Optional[Dict[str, Any]]
        ) -> list[types.TextContent]:
            """Handle tool calls using the research client."""
            
            # Initialize client if needed
            if self.client is None:
                self.client = TimelineResearchClient()
            
            try:
                # Route tool calls to appropriate client methods
                if name == "search_events":
                    result = self.client.search_events(
                        query=arguments.get("query", ""),
                        start_date=arguments.get("start_date"),
                        end_date=arguments.get("end_date"), 
                        actor=arguments.get("actor"),
                        tag=arguments.get("tag"),
                        min_importance=arguments.get("min_importance"),
                        limit=arguments.get("limit", 20)
                    )
                    return [types.TextContent(
                        type="text", 
                        text=self._format_events_list(result)
                    )]
                
                elif name == "get_event":
                    result = self.client.get_event(arguments["event_id"])
                    if result:
                        return [types.TextContent(
                            type="text",
                            text=self._format_single_event(result)
                        )]
                    else:
                        return [types.TextContent(
                            type="text", 
                            text=f"Event '{arguments['event_id']}' not found"
                        )]
                
                elif name == "analyze_actor":
                    result = self.client.analyze_actor(arguments["actor_name"])
                    return [types.TextContent(
                        type="text",
                        text=self._format_actor_analysis(result)
                    )]
                
                elif name == "get_qa_queue":
                    result = self.client.get_qa_queue(
                        limit=arguments.get("limit", 20),
                        offset=arguments.get("offset", 0)
                    )
                    return [types.TextContent(
                        type="text",
                        text=self._format_qa_queue(result)
                    )]
                
                elif name == "validate_event":
                    result = self.client.validate_event(arguments["event_data"])
                    return [types.TextContent(
                        type="text",
                        text=self._format_validation_result(result)
                    )]
                
                elif name == "mark_event_validated":
                    result = self.client.mark_event_validated(
                        event_id=arguments["event_id"],
                        quality_score=arguments["quality_score"],
                        notes=arguments.get("notes", ""),
                        validator_id=arguments.get("validator_id", "mcp-user")
                    )
                    return [types.TextContent(
                        type="text",
                        text=f"✅ Event validated successfully: {json.dumps(result, indent=2)}"
                    )]
                
                elif name == "get_missing_sources":
                    result = self.client.get_events_missing_sources(
                        min_sources=arguments.get("min_sources", 2),
                        limit=arguments.get("limit", 20)
                    )
                    return [types.TextContent(
                        type="text",
                        text=self._format_events_list(result)
                    )]
                
                elif name == "get_research_candidates":
                    result = self.client.get_research_candidates(
                        min_importance=arguments.get("min_importance", 7),
                        limit=arguments.get("limit", 20)
                    )
                    return [types.TextContent(
                        type="text",
                        text=self._format_events_list(result)
                    )]
                
                elif name == "get_validation_queue":
                    result = self.client.get_validation_queue(
                        limit=arguments.get("limit", 20)
                    )
                    return [types.TextContent(
                        type="text",
                        text=self._format_events_list(result)
                    )]
                
                elif name == "get_next_priority":
                    result = self.client.get_next_priority()
                    return [types.TextContent(
                        type="text",
                        text=self._format_priority(result)
                    )]
                
                elif name == "update_priority":
                    result = self.client.update_priority(
                        priority_id=arguments["priority_id"],
                        status=arguments["status"],
                        notes=arguments.get("notes"),
                        actual_events=arguments.get("actual_events")
                    )
                    return [types.TextContent(
                        type="text", 
                        text=f"✅ Priority updated: {json.dumps(result, indent=2)}"
                    )]
                
                elif name == "create_event":
                    result = self.client.create_event(arguments["event_data"])
                    return [types.TextContent(
                        type="text",
                        text=f"✅ Event created: {json.dumps(result, indent=2)}"
                    )]
                
                elif name == "get_stats":
                    result = self.client.get_stats()
                    return [types.TextContent(
                        type="text",
                        text=self._format_stats(result)
                    )]
                
                elif name == "get_qa_stats":
                    result = self.client.get_qa_stats()
                    return [types.TextContent(
                        type="text",
                        text=self._format_qa_stats(result)
                    )]
                
                elif name == "list_actors":
                    result = self.client.get_actors()
                    return [types.TextContent(
                        type="text",
                        text=f"**Actors ({len(result)}):**\n" + "\n".join(f"- {actor}" for actor in sorted(result)[:50])
                    )]
                
                elif name == "list_tags":
                    result = self.client.get_tags()
                    return [types.TextContent(
                        type="text",
                        text=f"**Tags ({len(result)}):**\n" + "\n".join(f"- {tag}" for tag in sorted(result)[:50])
                    )]
                
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"Tool call error: {e}")
                return [types.TextContent(
                    type="text",
                    text=f"❌ Error: {str(e)}"
                )]
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """List available resources."""
            return [
                types.Resource(
                    uri="timeline://stats",
                    name="Timeline Statistics",
                    description="Overall timeline statistics and metrics",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="timeline://qa-stats", 
                    name="QA Statistics",
                    description="Quality assurance system statistics",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="timeline://actors",
                    name="Actor List",
                    description="Complete list of actors in the timeline",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="timeline://tags",
                    name="Tag List", 
                    description="Complete list of tags used in events",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read a resource."""
            if self.client is None:
                self.client = TimelineResearchClient()
                
            if uri == "timeline://stats":
                return json.dumps(self.client.get_stats(), indent=2)
            elif uri == "timeline://qa-stats":
                return json.dumps(self.client.get_qa_stats(), indent=2)
            elif uri == "timeline://actors":
                return json.dumps(self.client.get_actors(), indent=2)
            elif uri == "timeline://tags":
                return json.dumps(self.client.get_tags(), indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    def _format_events_list(self, events: List[Dict]) -> str:
        """Format a list of events for display."""
        if not events:
            return "No events found matching the criteria."
        
        output = f"**Found {len(events)} events:**\n\n"
        
        for i, event in enumerate(events, 1):
            output += f"{i}. **{event.get('title', 'Untitled')}** ({event.get('date', 'No date')})\n"
            output += f"   ID: `{event.get('id', 'unknown')}`\n"
            output += f"   Importance: {event.get('importance', 'N/A')}/10\n"
            
            summary = event.get('summary', 'No summary')
            if len(summary) > 150:
                summary = summary[:150] + "..."
            output += f"   Summary: {summary}\n"
            
            if event.get('actors'):
                actors = event['actors'][:3]  # Show first 3 actors
                output += f"   Actors: {', '.join(actors)}\n"
            
            if event.get('tags'):
                tags = event['tags'][:5]  # Show first 5 tags
                output += f"   Tags: {', '.join(tags)}\n"
            
            output += "\n"
        
        return output
    
    def _format_single_event(self, event: Dict) -> str:
        """Format a single event with full details."""
        output = f"# {event.get('title', 'Untitled Event')}\n\n"
        output += f"**Date:** {event.get('date', 'Unknown')}\n"
        output += f"**ID:** `{event.get('id', 'unknown')}`\n"
        output += f"**Importance:** {event.get('importance', 'N/A')}/10\n"
        output += f"**Status:** {event.get('status', 'unknown')}\n\n"
        
        if event.get('location'):
            output += f"**Location:** {event['location']}\n\n"
        
        output += f"**Summary:**\n{event.get('summary', 'No summary available')}\n\n"
        
        if event.get('actors'):
            output += f"**Actors:**\n"
            for actor in event['actors']:
                output += f"- {actor}\n"
            output += "\n"
        
        if event.get('tags'):
            output += f"**Tags:** {', '.join(event['tags'])}\n\n"
        
        if event.get('sources'):
            output += f"**Sources:**\n"
            for i, source in enumerate(event['sources'], 1):
                output += f"{i}. [{source.get('title', 'Source')}]({source.get('url', '#')})\n"
                if source.get('outlet'):
                    output += f"   *{source['outlet']}*\n"
            output += "\n"
        
        return output
    
    def _format_actor_analysis(self, analysis: Dict) -> str:
        """Format actor analysis results."""
        actor = analysis.get('actor', 'Unknown')
        events = analysis.get('events', [])
        
        output = f"# Actor Analysis: {actor}\n\n"
        output += f"**Total Events:** {len(events)}\n"
        
        if events:
            # Calculate date range
            dates = [e.get('date', '') for e in events if e.get('date')]
            if dates:
                dates.sort()
                output += f"**Timeline:** {dates[0]} to {dates[-1]}\n"
            
            # Calculate average importance
            importances = [e.get('importance', 0) for e in events if e.get('importance')]
            if importances:
                avg_importance = sum(importances) / len(importances)
                output += f"**Average Importance:** {avg_importance:.1f}/10\n"
            
            output += "\n**Recent Events:**\n"
            for event in events[:10]:  # Show 10 most recent
                output += f"- {event.get('title', 'Untitled')} ({event.get('date', 'No date')})\n"
        
        return output
    
    def _format_qa_queue(self, queue_data: Dict) -> str:
        """Format QA queue results."""
        events = queue_data.get('events', [])
        if not events:
            return "No events in QA queue."
        
        output = f"**QA Queue ({len(events)} events):**\n\n"
        
        for i, event in enumerate(events, 1):
            output += f"{i}. **{event.get('title', 'Untitled')}** ({event.get('date', 'No date')})\n"
            output += f"   ID: `{event.get('id', 'unknown')}`\n"
            output += f"   Importance: {event.get('importance', 'N/A')}/10\n"
            
            # Show QA priority score if available
            if 'qa_priority_score' in event:
                output += f"   QA Priority: {event['qa_priority_score']:.1f}\n"
            
            # Show validation status
            if 'validation_status' in event:
                output += f"   Status: {event['validation_status']}\n"
            
            output += "\n"
        
        return output
    
    def _format_validation_result(self, result: Dict) -> str:
        """Format event validation results."""
        is_valid = result.get('valid', False)
        errors = result.get('errors', [])
        
        if is_valid:
            output = "✅ **Event validation passed**\n\n"
            output += "All required fields present and valid."
        else:
            output = "❌ **Event validation failed**\n\n"
            output += "**Errors found:**\n"
            for error in errors:
                output += f"- {error}\n"
        
        return output
    
    def _format_priority(self, priority: Dict) -> str:
        """Format research priority information."""
        if not priority or 'error' in priority:
            return "No research priorities available or error occurred."
        
        output = f"# Next Research Priority\n\n"
        output += f"**ID:** `{priority.get('id', 'unknown')}`\n"
        output += f"**Title:** {priority.get('title', 'Untitled')}\n"
        output += f"**Status:** {priority.get('status', 'unknown')}\n"
        output += f"**Priority:** {priority.get('priority', 'N/A')}/10\n\n"
        
        if priority.get('description'):
            output += f"**Description:**\n{priority['description']}\n\n"
        
        if priority.get('expected_events'):
            output += f"**Expected Events:** {priority['expected_events']}\n\n"
        
        return output
    
    def _format_stats(self, stats: Dict) -> str:
        """Format timeline statistics."""
        output = "# Timeline Statistics\n\n"
        
        for key, value in stats.items():
            if isinstance(value, dict):
                output += f"**{key.replace('_', ' ').title()}:**\n"
                for subkey, subvalue in value.items():
                    output += f"- {subkey.replace('_', ' ').title()}: {subvalue}\n"
                output += "\n"
            else:
                output += f"**{key.replace('_', ' ').title()}:** {value}\n"
        
        return output
    
    def _format_qa_stats(self, stats: Dict) -> str:
        """Format QA system statistics."""
        output = "# Quality Assurance Statistics\n\n"
        
        for key, value in stats.items():
            if isinstance(value, dict):
                output += f"**{key.replace('_', ' ').title()}:**\n"
                for subkey, subvalue in value.items():
                    output += f"- {subkey.replace('_', ' ').title()}: {subvalue}\n"
                output += "\n"
            else:
                output += f"**{key.replace('_', ' ').title()}:** {value}\n"
        
        return output
    
    async def run(self):
        """Run the MCP server."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="timeline-research",
                    server_version="2.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    )
                )
            )

async def main():
    """Main entry point."""
    server = TimelineResearchMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())