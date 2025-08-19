#!/usr/bin/env python3
"""
Simple static file server for the generated API JSON files.
Serves files with CORS headers for local development.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
from pathlib import Path

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

if __name__ == '__main__':
    # Change to static_api directory
    static_dir = Path(__file__).parent / 'static_api'
    os.chdir(static_dir)
    
    # Start server
    port = 8081
    server = HTTPServer(('', port), CORSRequestHandler)
    print(f"Serving static API files at http://localhost:{port}")
    print("Files available at:")
    print(f"  http://localhost:{port}/timeline.json")
    print(f"  http://localhost:{port}/tags.json")
    print(f"  http://localhost:{port}/actors.json")
    print(f"  http://localhost:{port}/stats.json")
    print(f"  http://localhost:{port}/monitoring.json")
    print("\nPress Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
