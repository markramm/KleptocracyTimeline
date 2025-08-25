#!/usr/bin/env python3
"""
Enhanced validation app with integrated source scraping and archiving.
Provides real-time status checking and on-demand scraping/archiving.
"""

import os
import json
import yaml
import time
import hashlib
import requests
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from datetime import datetime
from urllib.parse import urlparse, quote

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration
EVENTS_DIR = Path("events")
SOURCES_DIR = EVENTS_DIR / ".sources"
SOURCES_DIR.mkdir(exist_ok=True)
VALIDATION_FILE = Path("validation_status.json")

# Cache for source statuses
source_status_cache = {}
last_cache_update = 0
CACHE_DURATION = 300  # 5 minutes

# Load validation status
def load_validation_status():
    """Load validation status from file."""
    if VALIDATION_FILE.exists():
        with open(VALIDATION_FILE, 'r') as f:
            data = json.load(f)
            # Handle both old and new format
            if 'validated' in data and isinstance(data['validated'], dict):
                return data
            # Convert simple format to structured format
            return {'validated': data, 'in_review': {}, 'needs_review': {}, 'problematic': {}}
    return {'validated': {}, 'in_review': {}, 'needs_review': {}, 'problematic': {}}

def save_validation_status(status):
    """Save validation status to file."""
    # Update stats
    validated_count = len(status.get('validated', {}))
    total_events = len(list(get_event_files()))
    
    status['stats'] = {
        'total_events': total_events,
        'validated_count': validated_count,
        'last_updated': datetime.now().isoformat()
    }
    
    with open(VALIDATION_FILE, 'w') as f:
        json.dump(status, f, indent=2)

validation_status = load_validation_status()

def get_event_files():
    """Get all YAML event files sorted by date."""
    files = sorted(EVENTS_DIR.glob("*.yaml"))
    return files

def load_event(filepath):
    """Load and parse a YAML event file."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def check_scraped_file(event_id, source_num):
    """Check if source has been scraped locally."""
    filename = f"{event_id}_source{source_num}.html"
    filepath = SOURCES_DIR / filename
    if filepath.exists():
        return {
            'scraped': True,
            'size': filepath.stat().st_size,
            'modified': filepath.stat().st_mtime
        }
    return {'scraped': False}

def check_archive_status(url):
    """Check if URL is in archive.org."""
    try:
        # Use Wayback Machine API
        api_url = f"https://archive.org/wayback/available?url={quote(url)}"
        response = requests.get(api_url, timeout=5)
        data = response.json()
        
        if data.get('archived_snapshots', {}).get('closest'):
            snapshot = data['archived_snapshots']['closest']
            return {
                'archived': True,
                'url': snapshot['url'],
                'timestamp': snapshot['timestamp'],
                'status': snapshot['status']
            }
    except:
        pass
    return {'archived': False}

def check_url_status(url):
    """Check if URL is accessible."""
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return {
            'accessible': True,
            'status_code': response.status_code,
            'content_type': response.headers.get('Content-Type', '')
        }
    except requests.exceptions.Timeout:
        return {'accessible': False, 'error': 'timeout'}
    except requests.exceptions.RequestException as e:
        return {'accessible': False, 'error': str(e)[:100]}

@app.route('/')
def index():
    """Main validation interface."""
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Timeline Event Validator - Enhanced</title>
    <link rel="stylesheet" href="/static/validation.css">
</head>
<body>
    <div class="header">
        <h1>Timeline Event Validator - Enhanced</h1>
        <p>Validate events, check sources, and archive content</p>
        <div class="validation-progress" id="validation-progress"></div>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <h3>Total Events</h3>
            <div class="stat-value" id="total-events">-</div>
            <div class="stat-subtitle" id="validated-count">-</div>
        </div>
        <div class="stat-card">
            <h3>Sources Checked</h3>
            <div class="stat-value" id="sources-checked">-</div>
        </div>
        <div class="stat-card">
            <h3>Cached Locally</h3>
            <div class="stat-value" id="sources-cached">-</div>
        </div>
        <div class="stat-card">
            <h3>Archived</h3>
            <div class="stat-value" id="sources-archived">-</div>
        </div>
    </div>

    <div class="filter-bar">
        <label>Filter by Status:</label>
        <select id="status-filter" onchange="renderEvents()">
            <option value="">All Events</option>
            <option value="validated">Validated</option>
            <option value="unvalidated">Not Validated</option>
            <option value="unchecked">Unchecked Sources</option>
            <option value="errors">With Errors</option>
            <option value="unarchived">Not Archived</option>
        </select>
        <label>Importance:</label>
        <select id="importance-filter" onchange="renderEvents()">
            <option value="">All</option>
            <option value="10">10</option>
            <option value="9">9</option>
            <option value="8">8</option>
            <option value="7">≤7</option>
        </select>
        <button class="btn btn-check" onclick="checkAllSources()">Check All Sources</button>
    </div>

    <div class="event-grid" id="events-container">
        <div style="text-align: center; padding: 40px;">
            <div class="loading"></div>
            <p>Loading events...</p>
        </div>
    </div>

    <script src="/static/validation.js"></script>
</body>
</html>
    '''

@app.route('/api/events')
def api_events():
    """Get all events with their sources and validation status."""
    events = []
    validation_status = load_validation_status()  # Reload to get latest
    
    for filepath in get_event_files():
        try:
            event_data = load_event(filepath)
            event_id = filepath.stem
            
            # Get validation info for this event
            validation_info = validation_status.get('validated', {}).get(event_id, {})
            
            events.append({
                'id': event_id,
                'date': event_data.get('date', ''),
                'title': event_data.get('title', ''),
                'summary': event_data.get('summary', ''),
                'importance': event_data.get('importance', 5),
                'sources': event_data.get('sources', []),
                'validated': event_id in validation_status.get('validated', {}),
                'validated_date': validation_info.get('timestamp', None),
                'validated_by': validation_info.get('validator', None),
                'validation_notes': validation_info.get('notes', '')
            })
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    return jsonify(events)

@app.route('/api/check_source', methods=['POST'])
def api_check_source():
    """Check the status of a source - accessibility, cache, archive."""
    data = request.json
    source_id = data.get('source_id')
    url = data.get('url')
    
    # Parse source_id to get event_id and source_num
    parts = source_id.split('_source')
    event_id = parts[0]
    source_num = parts[1] if len(parts) > 1 else '1'
    
    # Check if scraped locally
    scraped_info = check_scraped_file(event_id, source_num)
    
    # Check if URL is accessible
    url_status = check_url_status(url)
    
    # Check archive.org status
    archive_status = check_archive_status(url)
    
    result = {
        'source_id': source_id,
        'url': url,
        'accessible': url_status.get('accessible', False),
        'status_code': url_status.get('status_code'),
        'error': url_status.get('error'),
        'scraped': scraped_info['scraped'],
        'scraped_size': scraped_info.get('size'),
        'scraped_modified': scraped_info.get('modified'),
        'archived': archive_status['archived'],
        'archive_url': archive_status.get('url'),
        'archive_timestamp': archive_status.get('timestamp')
    }
    
    # Cache the result
    source_status_cache[source_id] = result
    
    return jsonify(result)

@app.route('/api/scrape_source', methods=['POST'])
def api_scrape_source():
    """Scrape a source and save to .sources folder."""
    data = request.json
    source_id = data.get('source_id')
    url = data.get('url')
    
    # Parse source_id
    parts = source_id.split('_source')
    event_id = parts[0]
    source_num = parts[1] if len(parts) > 1 else '1'
    
    try:
        # Fetch the content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save to file
        filename = f"{event_id}_source{source_num}.html"
        filepath = SOURCES_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'size': len(response.text),
            'path': str(filepath)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/archive_source', methods=['POST'])
def api_archive_source():
    """Submit a source to archive.org."""
    data = request.json
    url = data.get('url')
    
    try:
        # Submit to Wayback Machine
        save_url = f"https://web.archive.org/save/{url}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(save_url, headers=headers, timeout=30)
        
        # Check if it was saved
        if response.status_code == 200:
            # Get the archive URL from the response
            archive_url = response.url if response.url.startswith('https://web.archive.org/') else None
            
            return jsonify({
                'success': True,
                'archive_url': archive_url,
                'message': 'Successfully submitted to archive.org'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Archive.org returned status {response.status_code}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/validate', methods=['POST'])
def api_validate():
    """Mark an event as validated."""
    data = request.json
    event_id = data.get('event_id')
    notes = data.get('notes', '')
    validated = data.get('validated', True)
    
    # Load current status
    validation_status = load_validation_status()
    
    # Update validation status
    if validated:
        validation_status['validated'][event_id] = {
            'validator': data.get('validated_by', 'web_ui'),
            'timestamp': datetime.now().isoformat(),
            'notes': notes
        }
    else:
        # Remove validation if unchecking
        if event_id in validation_status.get('validated', {}):
            del validation_status['validated'][event_id]
    
    # Save updated status
    save_validation_status(validation_status)
    
    return jsonify({
        'success': True,
        'event_id': event_id,
        'validated': validated,
        'message': f'Event {"validated" if validated else "unvalidated"}'
    })

@app.route('/api/validation_summary')
def api_validation_summary():
    """Get validation summary statistics."""
    validation_status = load_validation_status()
    total_events = len(list(get_event_files()))
    validated_events = len(validation_status.get('validated', {}))
    
    # Get validation timeline
    timeline = []
    for event_id, info in validation_status.items():
        timeline.append({
            'event_id': event_id,
            'date': info.get('validated_date'),
            'by': info.get('validated_by')
        })
    timeline.sort(key=lambda x: x['date'] or '', reverse=True)
    
    return jsonify({
        'total_events': total_events,
        'validated_events': validated_events,
        'percentage': round((validated_events / total_events * 100) if total_events > 0 else 0, 1),
        'recent_validations': timeline[:10]
    })

@app.route('/api/scraped/<path:filename>')
def serve_scraped(filename):
    """Serve scraped HTML files."""
    return send_from_directory(SOURCES_DIR, filename)

if __name__ == '__main__':
    print("Starting Enhanced Validation Server...")
    print("Open http://localhost:8082 in your browser")
    app.run(debug=True, port=8082)