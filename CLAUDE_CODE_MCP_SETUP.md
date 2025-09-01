# MCP Server Setup for Claude Code

## Important: Claude Code vs Claude Desktop

This MCP server needs to be configured differently for Claude Code than for Claude Desktop.

## For Claude Code Users

### Option 1: Built-in MCP Support (If Available)

Claude Code may have built-in MCP server management. Check:
1. Settings → Extensions → MCP Servers
2. Or use command palette: "MCP: Add Server"

### Option 2: Local Development Mode

Since Claude Code runs in a browser/cloud environment, you'll need to:

1. **Run the MCP server locally** as a development server:
```bash
# Install dependencies
pip install mcp mcp-server-stdio

# Run in development mode with HTTP transport
python3 mcp_timeline_server_http.py
```

2. **Use the HTTP bridge** (creating now) that Claude Code can connect to

### Option 3: Deploy as Cloud Service

For production use with Claude Code:

1. Deploy to a cloud service (Render, Railway, Heroku)
2. Add authentication
3. Configure Claude Code to use the remote endpoint

## Creating HTTP Bridge for Claude Code

Since Claude Code can't directly spawn local processes like Claude Desktop can, we need an HTTP bridge:

```python
# mcp_timeline_server_http.py
from fastapi import FastAPI
from mcp_timeline_server import TimelineSearchServer
import uvicorn

app = FastAPI()
server = TimelineSearchServer()

@app.post("/mcp/tools/search_events")
async def search_events(query: str, limit: int = 10):
    return await server._search_events({"query": query, "limit": limit})

@app.post("/mcp/tools/check_duplicate")
async def check_duplicate(title: str, date: str = None):
    return await server._check_duplicate({"title": title, "date": date})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8888)
```

## Current Status

**For now**, since MCP support in Claude Code is still evolving:

1. **Use the Python tools directly** in Claude Code:
   ```python
   from yaml_tools import YamlEventManager
   from rag.rag_system import AdvancedRAGSystem
   ```

2. **Wait for official MCP support** in Claude Code
   - The MCP server is ready when Claude Code adds support
   - The protocol is standardized, so it will work when available

3. **Alternative: Use the Web API**
   ```bash
   # Run the RAG API server
   cd rag && python rag_production_api.py
   
   # This gives you HTTP endpoints Claude Code could potentially use
   ```

## Why This Matters

The MCP server architecture is valuable even if not immediately usable in Claude Code because:

1. **Future-proof** - Ready when Claude Code adds MCP support
2. **Other tools** - Can be used with other MCP-compatible tools
3. **API pattern** - Shows how to wrap the RAG system for any interface

## Workaround for Now

Until Claude Code has full MCP support, you can:

1. **Run the RAG API locally**:
   ```bash
   cd rag && python rag_production_api.py
   ```

2. **I can use the Python tools directly**:
   ```python
   # I can already do this in Claude Code
   from rag.rag_system import AdvancedRAGSystem
   rag = AdvancedRAGSystem("timeline_data/timeline_complete.json")
   results = rag.search("Trump tariffs 2025")
   ```

3. **Use yaml_tools.py for simpler searches**:
   ```python
   from yaml_tools import YamlEventManager
   manager = YamlEventManager()
   results = manager.yaml_search(text="ICE raids", date_from="2025-01-01")
   ```

## The Real Value

Even without immediate Claude Code support, this MCP server:
- Documents the search interface clearly
- Can be used by other MCP-compatible tools
- Provides a template for future integration
- Shows how to properly wrap the RAG system

The infrastructure is ready - we're just waiting for the platform support!