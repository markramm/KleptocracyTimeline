#!/usr/bin/env python3
"""
Timeline Server - Serves timeline data from YAML files via REST API
"""

import os
import yaml
import json
import webbrowser
import threading
import time
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from datetime import datetime
from pathlib import Path
import glob

app = Flask(__name__)
CORS(app)

# Configuration
TIMELINE_DIR = Path(__file__).parent / "timeline_data"
STATIC_DIR = Path(__file__).parent / "timeline-app" / "build"

def load_timeline_events():
    """Load all timeline events from YAML files"""
    events = []
    
    if TIMELINE_DIR.exists():
        for yaml_file in TIMELINE_DIR.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    event = yaml.safe_load(f)
                    if event and event.get('id'):
                        event['_file'] = yaml_file.name
                        events.append(event)
            except Exception as e:
                print(f"Error loading {yaml_file}: {e}")
    
    # Sort by date (convert to string for comparison)
    events.sort(key=lambda x: str(x.get('date', '9999-12-31')))
    return events

def extract_all_tags(events):
    """Extract all unique tags from events"""
    tags = set()
    for event in events:
        if 'tags' in event:
            tags.update(event['tags'])
    return sorted(list(tags))

def extract_all_actors(events):
    """Extract all unique actors from events"""
    actors = set()
    for event in events:
        if 'actors' in event:
            actors.update(event['actors'])
    return sorted(list(actors))

@app.route('/api/timeline')
def get_timeline():
    """Get all timeline events with optional filtering"""
    events = load_timeline_events()
    
    # Filter by tags if provided
    tags_filter = request.args.getlist('tags')
    if tags_filter:
        events = [e for e in events if any(tag in e.get('tags', []) for tag in tags_filter)]
    
    # Filter by actors if provided
    actors_filter = request.args.getlist('actors')
    if actors_filter:
        events = [e for e in events if any(actor in e.get('actors', []) for actor in actors_filter)]
    
    # Filter by date range if provided
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if start_date:
        events = [e for e in events if e.get('date', '') >= start_date]
    if end_date:
        events = [e for e in events if e.get('date', '') <= end_date]
    
    # Filter by search query if provided
    search = request.args.get('search', '').lower()
    if search:
        events = [e for e in events if 
                 search in e.get('title', '').lower() or 
                 search in e.get('summary', '').lower() or
                 search in str(e.get('notes', '')).lower()]
    
    return jsonify({
        'events': events,
        'total': len(events)
    })

@app.route('/api/tags')
def get_tags():
    """Get all unique tags"""
    events = load_timeline_events()
    tags = extract_all_tags(events)
    return jsonify({'tags': tags})

@app.route('/api/actors')
def get_actors():
    """Get all unique actors"""
    events = load_timeline_events()
    actors = extract_all_actors(events)
    return jsonify({'actors': actors})

@app.route('/api/stats')
def get_stats():
    """Get timeline statistics"""
    events = load_timeline_events()
    
    # Group events by year
    events_by_year = {}
    for event in events:
        date_str = str(event.get('date', ''))
        year = date_str.split('-')[0] if date_str else ''
        if year:
            events_by_year[year] = events_by_year.get(year, 0) + 1
    
    # Count by status
    status_counts = {}
    for event in events:
        status = event.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Count by tags
    tag_counts = {}
    for event in events:
        for tag in event.get('tags', []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    return jsonify({
        'total_events': len(events),
        'events_by_year': events_by_year,
        'status_counts': status_counts,
        'tag_counts': tag_counts,
        'date_range': {
            'start': min([str(e.get('date', '9999')) for e in events]) if events else '',
            'end': max([str(e.get('date', '0000')) for e in events]) if events else ''
        }
    })

@app.route('/api/event/<event_id>')
def get_event(event_id):
    """Get a single event by ID"""
    events = load_timeline_events()
    event = next((e for e in events if e.get('id') == event_id), None)
    if event:
        return jsonify(event)
    return jsonify({'error': 'Event not found'}), 404

# Serve React app if it exists
@app.route('/')
def serve_react_app():
    if STATIC_DIR.exists():
        return send_from_directory(STATIC_DIR, 'index.html')
    else:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Timeline API Server</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                       max-width: 800px; margin: 50px auto; padding: 20px; 
                       background: #0f172a; color: #e5e7eb; }
                .endpoint { background: #1e293b; padding: 10px; margin: 10px 0; 
                           border-radius: 5px; font-family: monospace; border: 1px solid #334155; }
                h1 { color: #3b82f6; }
                h2 { color: #94a3b8; margin-top: 30px; }
                .status { color: #10b981; margin: 20px 0; padding: 15px; 
                         background: rgba(16, 185, 129, 0.1); border-radius: 5px; 
                         border: 1px solid rgba(16, 185, 129, 0.3); }
                a { color: #60a5fa; text-decoration: none; }
                a:hover { color: #93c5fd; }
            </style>
        </head>
        <body>
            <h1>Timeline API Server</h1>
            <div class="status">✅ Server is running successfully!</div>
            
            <h2>Available Endpoints:</h2>
            <div class="endpoint">GET /api/timeline</div>
            <p>Get all timeline events (supports query params: tags[], actors[], start_date, end_date, search)</p>
            
            <div class="endpoint">GET /api/event/{id}</div>
            <p>Get a single event by ID</p>
            
            <div class="endpoint">GET /api/tags</div>
            <p>Get all unique tags</p>
            
            <div class="endpoint">GET /api/actors</div>
            <p>Get all unique actors</p>
            
            <div class="endpoint">GET /api/stats</div>
            <p>Get timeline statistics</p>
            
            <h2>React App:</h2>
            <p>To use the interactive timeline:</p>
            <ol>
                <li>Open a new terminal</li>
                <li>Navigate to: <code>cd timeline-app</code></li>
                <li>Install dependencies: <code>npm install</code></li>
                <li>Start the app: <code>npm start</code></li>
            </ol>
        </body>
        </html>
        """

@app.route('/<path:path>')
def serve_static(path):
    if STATIC_DIR.exists():
        return send_from_directory(STATIC_DIR, path)
    return jsonify({'error': 'React app not built'}), 404

def open_browser(port=5173):
    """Open browser after a short delay to let the server start"""
    time.sleep(2.0)  # Give server more time to fully start
    webbrowser.open(f'http://127.0.0.1:{port}')

if __name__ == '__main__':
    # Use port 5173 to avoid conflict with macOS AirPlay (which uses 5000)
    PORT = 5173
    
    # Load and display event information
    print(f"\n🚀 Loading timeline events from: {TIMELINE_DIR}")
    events = load_timeline_events()
    print(f"✅ Loaded {len(events)} events spanning {events[0].get('date', 'unknown')} to {events[-1].get('date', 'unknown')}")
    
    # Display server information
    print("\n" + "="*60)
    print("📊 Timeline API Server Starting...")
    print("="*60)
    print(f"🌐 API Server: http://127.0.0.1:{PORT}")
    if not os.environ.get('NO_BROWSER'):
        print(f"📱 React App:  http://localhost:3000 (run 'npm start' in timeline-app/)")
    else:
        print(f"📱 React App:  Will be started separately...")
    print("="*60)
    print(f"⚠️  Note: Using port {PORT} to avoid macOS AirPlay conflict")
    print("🛑 Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    # Open browser in a separate thread (optional - can be disabled with NO_BROWSER env var)
    if not os.environ.get('NO_BROWSER'):
        try:
            browser_thread = threading.Thread(target=lambda: open_browser(PORT))
            browser_thread.daemon = True
            browser_thread.start()
            print(f"🌐 Opening browser at http://127.0.0.1:{PORT}...")
        except Exception as e:
            print(f"⚠️  Could not auto-open browser: {e}")
            print(f"   Please manually open: http://127.0.0.1:{PORT}")
    else:
        print("ℹ️  Browser auto-open disabled")
        print(f"   Please manually open: http://127.0.0.1:{PORT}")
    
    # Start the Flask server with explicit host binding
    app.run(debug=True, host='127.0.0.1', port=PORT, use_reloader=False)