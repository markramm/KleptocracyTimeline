#!/usr/bin/env python3
"""
MCP Server for Kleptocracy Timeline Event Lookup

A minimal Model Context Protocol server that provides intelligent search
capabilities for timeline events. Perfect for checking if events or related
events already exist when researching new information.
"""

import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "rag"))

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Import our RAG system
from rag.rag_system import AdvancedRAGSystem

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimelineSearchServer:
    """MCP Server for timeline event search and analysis."""
    
    def __init__(self):
        self.server = Server("timeline-search")
        self.rag_system = None
        self.timeline_data_path = Path(__file__).parent / "timeline_data" / "timeline_complete.json"
        
        # Register handlers
        self.setup_handlers()
        
    def setup_handlers(self):
        """Set up MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="search_events",
                    description="Search timeline for events. Supports semantic search, date ranges, entities, and patterns.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (keywords, entities, or description)"
                            },
                            "date_from": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD format, optional)"
                            },
                            "date_to": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD format, optional)"
                            },
                            "min_importance": {
                                "type": "integer",
                                "description": "Minimum importance level (1-10, optional)",
                                "minimum": 1,
                                "maximum": 10
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results to return (default 10)",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                types.Tool(
                    name="check_duplicate",
                    description="Check if an event already exists or find similar events",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Event title to check"
                            },
                            "date": {
                                "type": "string",
                                "description": "Event date (YYYY-MM-DD)"
                            },
                            "entities": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Key people/organizations involved"
                            },
                            "threshold": {
                                "type": "number",
                                "description": "Similarity threshold (0-1, default 0.7)",
                                "default": 0.7
                            }
                        },
                        "required": ["title"]
                    }
                ),
                types.Tool(
                    name="analyze_pattern",
                    description="Find events that match a specific pattern or theme",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Pattern to analyze (e.g., 'financial corruption', 'judicial capture')"
                            },
                            "entities": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific entities to focus on (optional)"
                            },
                            "time_range": {
                                "type": "string",
                                "description": "Time range (e.g., 'last year', '2024', '2020-2025')"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results (default 20)",
                                "default": 20
                            }
                        },
                        "required": ["pattern"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, 
            arguments: Optional[Dict[str, Any]]
        ) -> list[types.TextContent]:
            """Handle tool calls."""
            
            # Initialize RAG system if needed
            if self.rag_system is None:
                await self._initialize_rag()
            
            if name == "search_events":
                return await self._search_events(arguments)
            elif name == "check_duplicate":
                return await self._check_duplicate(arguments)
            elif name == "analyze_pattern":
                return await self._analyze_pattern(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
        
        @self.server.list_resources()
        async def handle_list_resources() -> list[types.Resource]:
            """List available resources."""
            return [
                types.Resource(
                    uri="timeline://stats",
                    name="Timeline Statistics",
                    description="Overall statistics about the timeline",
                    mimeType="application/json"
                ),
                types.Resource(
                    uri="timeline://recent",
                    name="Recent Events",
                    description="Most recently added events",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read a resource."""
            if uri == "timeline://stats":
                return await self._get_stats()
            elif uri == "timeline://recent":
                return await self._get_recent_events()
            else:
                raise ValueError(f"Unknown resource: {uri}")
    
    async def _initialize_rag(self):
        """Initialize the RAG system."""
        logger.info("Initializing RAG system...")
        
        # Check if timeline data exists
        if not self.timeline_data_path.exists():
            # Try to generate it
            generate_script = Path(__file__).parent / "timeline_data" / "generate_static_api.py"
            if generate_script.exists():
                import subprocess
                logger.info("Generating timeline data...")
                subprocess.run([sys.executable, str(generate_script)], check=True)
        
        # Initialize RAG system
        self.rag_system = AdvancedRAGSystem(str(self.timeline_data_path))
        logger.info("RAG system initialized")
    
    async def _search_events(self, args: Dict[str, Any]) -> list[types.TextContent]:
        """Search for events using the RAG system."""
        query = args.get("query", "")
        date_from = args.get("date_from")
        date_to = args.get("date_to")
        min_importance = args.get("min_importance")
        limit = args.get("limit", 10)
        
        # Enhance query with temporal context if provided
        if date_from or date_to:
            if date_from and date_to:
                query += f" between {date_from} and {date_to}"
            elif date_from:
                query += f" after {date_from}"
            elif date_to:
                query += f" before {date_to}"
        
        # Search using RAG
        results = self.rag_system.search(query, top_k=limit * 2)  # Get extra for filtering
        
        # Filter by importance if specified
        if min_importance:
            results = [r for r in results if r.get("importance", 0) >= min_importance]
        
        # Limit results
        results = results[:limit]
        
        # Format results
        if not results:
            return [types.TextContent(
                type="text",
                text="No matching events found."
            )]
        
        output = f"Found {len(results)} matching events:\n\n"
        
        for i, event in enumerate(results, 1):
            output += f"{i}. **{event.get('title', 'Untitled')}** ({event.get('date', 'No date')})\n"
            output += f"   Importance: {event.get('importance', 'N/A')}/10\n"
            output += f"   Summary: {event.get('summary', 'No summary')[:200]}...\n"
            
            # Add similarity score if available
            if 'score' in event:
                output += f"   Relevance: {event['score']:.2%}\n"
            
            # Add tags if present
            if event.get('tags'):
                output += f"   Tags: {', '.join(event['tags'][:5])}\n"
            
            output += "\n"
        
        return [types.TextContent(type="text", text=output)]
    
    async def _check_duplicate(self, args: Dict[str, Any]) -> list[types.TextContent]:
        """Check for duplicate or similar events."""
        title = args.get("title", "")
        date = args.get("date", "")
        entities = args.get("entities", [])
        threshold = args.get("threshold", 0.7)
        
        # Build search query
        query = title
        if entities:
            query += " " + " ".join(entities)
        if date:
            query += f" {date}"
        
        # Search for similar events
        results = self.rag_system.search(query, top_k=10)
        
        # Find high-similarity matches
        duplicates = []
        similar = []
        
        for event in results:
            score = event.get('score', 0)
            if score >= 0.9:
                duplicates.append(event)
            elif score >= threshold:
                similar.append(event)
        
        # Format response
        output = ""
        
        if duplicates:
            output += f"⚠️ **Likely Duplicates Found** ({len(duplicates)}):\n\n"
            for event in duplicates[:3]:
                output += f"- **{event['title']}** ({event['date']})\n"
                output += f"  Similarity: {event.get('score', 0):.1%}\n"
                output += f"  ID: {event.get('id', 'unknown')}\n\n"
        
        if similar:
            output += f"📋 **Similar Events** ({len(similar)}):\n\n"
            for event in similar[:5]:
                output += f"- {event['title']} ({event['date']})\n"
                output += f"  Similarity: {event.get('score', 0):.1%}\n"
                output += f"  Summary: {event['summary'][:100]}...\n\n"
        
        if not duplicates and not similar:
            output = "✅ No duplicates or highly similar events found. This appears to be a new event."
        
        return [types.TextContent(type="text", text=output)]
    
    async def _analyze_pattern(self, args: Dict[str, Any]) -> list[types.TextContent]:
        """Analyze events matching a pattern."""
        pattern = args.get("pattern", "")
        entities = args.get("entities", [])
        time_range = args.get("time_range", "")
        limit = args.get("limit", 20)
        
        # Build query
        query = pattern
        if entities:
            query += " " + " ".join(entities)
        if time_range:
            query += f" {time_range}"
        
        # Search for pattern
        results = self.rag_system.search(query, top_k=limit)
        
        if not results:
            return [types.TextContent(
                type="text",
                text=f"No events found matching pattern: {pattern}"
            )]
        
        # Analyze patterns
        dates = [r.get('date', '') for r in results if r.get('date')]
        actors = []
        tags = []
        importance_sum = 0
        
        for event in results:
            actors.extend(event.get('actors', []))
            tags.extend(event.get('tags', []))
            importance_sum += event.get('importance', 0)
        
        # Count frequencies
        from collections import Counter
        actor_counts = Counter(actors).most_common(5)
        tag_counts = Counter(tags).most_common(5)
        
        # Format analysis
        output = f"## Pattern Analysis: {pattern}\n\n"
        output += f"**Events Found**: {len(results)}\n"
        
        if dates:
            output += f"**Time Span**: {min(dates)} to {max(dates)}\n"
        
        output += f"**Average Importance**: {importance_sum/len(results):.1f}/10\n\n"
        
        if actor_counts:
            output += "**Key Actors**:\n"
            for actor, count in actor_counts:
                output += f"- {actor}: {count} events\n"
            output += "\n"
        
        if tag_counts:
            output += "**Common Themes**:\n"
            for tag, count in tag_counts:
                output += f"- {tag}: {count} events\n"
            output += "\n"
        
        output += "**Sample Events**:\n"
        for event in results[:5]:
            output += f"- {event['title']} ({event['date']})\n"
        
        return [types.TextContent(type="text", text=output)]
    
    async def _get_stats(self) -> str:
        """Get timeline statistics."""
        stats_path = Path(__file__).parent / "viewer" / "public" / "api" / "stats.json"
        
        if stats_path.exists():
            with open(stats_path, 'r') as f:
                return f.read()
        else:
            return json.dumps({"error": "Statistics not available"})
    
    async def _get_recent_events(self) -> str:
        """Get recent events."""
        if self.rag_system is None:
            await self._initialize_rag()
        
        # Search for 2025 events
        results = self.rag_system.search("2025", top_k=10)
        
        return json.dumps([{
            "id": r.get("id"),
            "date": r.get("date"),
            "title": r.get("title"),
            "importance": r.get("importance")
        } for r in results], indent=2)
    
    async def run(self):
        """Run the MCP server."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="timeline-search",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    )
                )
            )

async def main():
    """Main entry point."""
    server = TimelineSearchServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())