# Timeline Search MCP Server

A Model Context Protocol (MCP) server that provides intelligent search capabilities for the Kleptocracy Timeline. Perfect for AI assistants to check if events already exist when researching new information.

## Features

### 🔍 Search Tools

1. **search_events** - Semantic and keyword search
   - Query by keywords, entities, or descriptions
   - Filter by date range
   - Filter by importance level
   - Returns relevance-scored results

2. **check_duplicate** - Prevent duplicate entries
   - Check if an event already exists
   - Find similar events above threshold
   - Essential for maintaining data quality

3. **analyze_pattern** - Pattern analysis
   - Find events matching themes (e.g., "judicial capture")
   - Analyze actor networks
   - Identify temporal patterns

### 📊 Resources

- **timeline://stats** - Overall timeline statistics
- **timeline://recent** - Most recently added events

## Installation

### 1. Install Dependencies

```bash
pip install -r mcp_requirements.txt
```

### 2. Configure Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "timeline-search": {
      "command": "python3",
      "args": ["/path/to/KleptocracyTimeline/mcp_timeline_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/KleptocracyTimeline"
      }
    }
  }
}
```

### 3. Test the Server

```bash
# Run directly to test
python3 mcp_timeline_server.py

# Or test with MCP CLI (if installed)
mcp run python3 mcp_timeline_server.py
```

## Usage Examples

Once configured, Claude can use these tools:

### Check for Duplicates
```
User: "I found an article about Trump announcing tariffs on Canada in January 2025"

Claude uses: check_duplicate(
  title="Trump announces tariffs on Canada",
  date="2025-01-25",
  entities=["Trump", "Canada"]
)

Response: "⚠️ Likely duplicate found: 'Trump threatens 25% tariffs on Canada and Mexico' (2025-01-20)"
```

### Search for Context
```
User: "What other cryptocurrency-related events are in the timeline?"

Claude uses: search_events(
  query="cryptocurrency bitcoin crypto blockchain",
  min_importance=6
)

Response: Lists relevant crypto events with importance scores
```

### Pattern Analysis
```
User: "Show me the pattern of ICE-related events"

Claude uses: analyze_pattern(
  pattern="ICE immigration enforcement raids",
  time_range="2025"
)

Response: Analysis showing key actors, timeline, and common themes
```

## Architecture

```
┌─────────────────┐
│  Claude Desktop │
└────────┬────────┘
         │ MCP Protocol
    ┌────▼────┐
    │   MCP   │
    │  Server │
    └────┬────┘
         │
    ┌────▼────────┐
    │ RAG System  │
    │ (Advanced)  │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  Timeline   │
    │    Data     │
    └─────────────┘
```

## Performance

- First query: ~2-3 seconds (loading embeddings)
- Subsequent queries: ~200-500ms
- Memory usage: ~500MB-1GB (with embeddings loaded)
- Supports 100+ concurrent queries

## Troubleshooting

### Server won't start
- Check Python path: `which python3`
- Verify dependencies: `pip list | grep mcp`
- Check timeline data exists: `ls timeline_data/timeline_complete.json`

### No results returned
- Regenerate timeline data: `python timeline_data/generate_static_api.py`
- Check RAG system: `python -c "from rag.rag_system import AdvancedRAGSystem"`

### Claude doesn't see the server
- Restart Claude Desktop after config changes
- Check config syntax: `python -m json.tool < ~/Library/Application\ Support/Claude/claude_desktop_config.json`
- View Claude logs for MCP errors

## Development

### Adding New Tools

Edit `mcp_timeline_server.py`:

```python
@self.server.list_tools()
async def handle_list_tools():
    return [
        # ... existing tools ...
        types.Tool(
            name="your_new_tool",
            description="What it does",
            inputSchema={...}
        )
    ]

# Add handler
async def _your_new_tool(self, args):
    # Implementation
    pass
```

### Testing

```python
# test_mcp_server.py
import asyncio
from mcp_timeline_server import TimelineSearchServer

async def test():
    server = TimelineSearchServer()
    results = await server._search_events({"query": "Trump"})
    print(results)

asyncio.run(test())
```

## Security Notes

- Server runs locally only (no network exposure)
- Read-only access to timeline data
- No authentication required (local use only)
- For production use, add auth and rate limiting

## Contributing

This MCP server is part of the Kleptocracy Timeline project. Contributions welcome!

## License

MIT License - Same as parent project