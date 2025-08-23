#!/usr/bin/env python3
"""
Simple Web UI for Event Validation
Run with: python3 validation_app.py
Then open http://localhost:8080 in your browser
"""

import json
import yaml
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Timeline Event Validator</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stat-label {{
            font-size: 12px;
            color: #7f8c8d;
            text-transform: uppercase;
        }}
        .event-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .event-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }}
        .importance {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
        }}
        .importance-10 {{ background: #e74c3c; }}
        .importance-9 {{ background: #e67e22; }}
        .importance-8 {{ background: #f39c12; }}
        .importance-7 {{ background: #3498db; }}
        .importance-6, .importance-5 {{ background: #95a5a6; }}
        .event-title {{
            font-size: 18px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .event-date {{
            color: #7f8c8d;
            margin-bottom: 10px;
        }}
        .event-summary {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
            line-height: 1.6;
        }}
        .sources {{
            margin: 15px 0;
        }}
        .source {{
            background: #fff;
            border: 1px solid #ddd;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
        }}
        .source-title {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .source-url {{
            color: #3498db;
            text-decoration: none;
            word-break: break-all;
            font-size: 12px;
        }}
        .source-url:hover {{
            text-decoration: underline;
        }}
        .archive-link {{
            color: #27ae60;
            margin-left: 10px;
        }}
        .broken-link {{
            color: #e74c3c;
        }}
        .actions {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }}
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .btn-validate {{
            background: #27ae60;
            color: white;
        }}
        .btn-validate:hover {{
            background: #229954;
        }}
        .btn-problem {{
            background: #e74c3c;
            color: white;
        }}
        .btn-problem:hover {{
            background: #c0392b;
        }}
        .btn-skip {{
            background: #95a5a6;
            color: white;
        }}
        .btn-skip:hover {{
            background: #7f8c8d;
        }}
        .problem-form {{
            display: none;
            background: #fff3cd;
            padding: 15px;
            border-radius: 4px;
            margin-top: 15px;
        }}
        .problem-form.show {{
            display: block;
        }}
        .checkbox-group {{
            margin: 10px 0;
        }}
        .checkbox-group label {{
            display: block;
            margin: 5px 0;
        }}
        .notes {{
            width: 100%;
            min-height: 60px;
            margin-top: 10px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .nav {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }}
        .progress {{
            background: #ecf0f1;
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        .progress-bar {{
            background: #27ae60;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 0.3s;
        }}
        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin: 10px 0;
        }}
        .tag {{
            background: #3498db;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Timeline Event Validator</h1>
        <p>Review and validate timeline events in order of importance</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{validated_count}</div>
            <div class="stat-label">Validated</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{needs_review_count}</div>
            <div class="stat-label">Needs Review</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{problematic_count}</div>
            <div class="stat-label">Problematic</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{percent_complete}%</div>
            <div class="stat-label">Complete</div>
        </div>
    </div>
    
    <div class="progress">
        <div class="progress-bar" style="width: {percent_complete}%">
            {validated_count} / {total_events} Events Validated
        </div>
    </div>
    
    <div class="nav">
        <h2>Current Event ({current_index} of {queue_size} in queue)</h2>
        <div>
            <form method="GET" style="display: inline;">
                <input type="hidden" name="skip" value="true">
                <button type="submit" class="btn btn-skip">Skip to Next</button>
            </form>
        </div>
    </div>
    
    <div class="event-card">
        <div class="event-header">
            <div>
                <span class="importance importance-{importance}">Importance: {importance}</span>
                <div class="event-title">{title}</div>
                <div class="event-date">Date: {date}</div>
                <div class="tags">
                    {tags_html}
                </div>
            </div>
            <div>
                <strong>Status:</strong> {status}<br>
                <strong>ID:</strong> {event_id}
            </div>
        </div>
        
        <div class="event-summary">
            <strong>Summary:</strong><br>
            {summary}
        </div>
        
        <div class="sources">
            <h3>Sources ({sources_count})</h3>
            {sources_html}
        </div>
        
        {notes_section}
        
        <div class="problem-form" id="problemForm">
            <h3>Report Issues</h3>
            <div class="checkbox-group">
                <label><input type="checkbox" name="issue" value="broken_links"> Broken source links</label>
                <label><input type="checkbox" name="issue" value="incorrect_date"> Incorrect date</label>
                <label><input type="checkbox" name="issue" value="unsupported_claims"> Sources don't support claims</label>
                <label><input type="checkbox" name="issue" value="missing_sources"> Missing important sources</label>
                <label><input type="checkbox" name="issue" value="inaccurate_summary"> Inaccurate summary</label>
                <label><input type="checkbox" name="issue" value="wrong_importance"> Wrong importance level</label>
                <label><input type="checkbox" name="issue" value="duplicate"> Duplicate event</label>
            </div>
            <textarea class="notes" id="problemNotes" placeholder="Additional notes about the issues..."></textarea>
        </div>
        
        <div class="actions">
            <form method="POST" style="display: inline;">
                <input type="hidden" name="action" value="validate">
                <input type="hidden" name="event_id" value="{event_id}">
                <button type="submit" class="btn btn-validate">✓ Validate Event</button>
            </form>
            
            <button class="btn btn-problem" onclick="toggleProblemForm()">⚠ Report Problem</button>
            
            <form method="POST" id="problemSubmit" style="display: none;">
                <input type="hidden" name="action" value="problem">
                <input type="hidden" name="event_id" value="{event_id}">
                <input type="hidden" name="issues" id="issuesField">
                <input type="hidden" name="notes" id="notesField">
            </form>
        </div>
    </div>
    
    <script>
        function toggleProblemForm() {{
            const form = document.getElementById('problemForm');
            form.classList.toggle('show');
        }}
        
        function submitProblem() {{
            const checkboxes = document.querySelectorAll('input[name="issue"]:checked');
            const issues = Array.from(checkboxes).map(cb => cb.value);
            const notes = document.getElementById('problemNotes').value;
            
            if (issues.length === 0) {{
                alert('Please select at least one issue');
                return;
            }}
            
            document.getElementById('issuesField').value = issues.join(',');
            document.getElementById('notesField').value = notes;
            document.getElementById('problemSubmit').submit();
        }}
        
        // Add submit button to problem form
        document.getElementById('problemForm').innerHTML += 
            '<button type="button" class="btn btn-problem" onclick="submitProblem()">Submit Issues</button>';
    </script>
</body>
</html>
"""

class ValidationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        from validation_tracker import ValidationTracker
        
        tracker = ValidationTracker()
        
        # Parse query parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        # Get next event in queue
        queue = tracker.get_validation_queue(limit=50)
        
        if not queue:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>All events validated!</h1>")
            return
        
        # Skip to next if requested
        index = 0
        if 'skip' in params:
            index = min(1, len(queue) - 1)
        
        event = queue[index]
        
        # Load full event data
        with open(event['file'], 'r') as f:
            event_data = yaml.safe_load(f)
        
        # Get stats
        stats = tracker.get_stats()
        
        # Format sources HTML
        sources_html = ""
        for source in event_data.get('sources', []):
            url = source.get('url', '')
            is_archive = 'archive.org' in url
            sources_html += f"""
            <div class="source">
                <div class="source-title">{source.get('title', 'Untitled')}</div>
                <div>Outlet: {source.get('outlet', 'Unknown')} | Date: {source.get('date', 'Unknown')}</div>
                <a href="{url}" target="_blank" class="source-url {'archive-link' if is_archive else ''}">
                    {url}
                </a>
            </div>
            """
        
        # Format tags HTML
        tags_html = "".join([f'<span class="tag">{tag}</span>' 
                            for tag in event_data.get('tags', [])])
        
        # Format notes section
        notes_section = ""
        if event_data.get('notes'):
            notes_section = f"""
            <div class="event-summary" style="background: #fff9e6;">
                <strong>Notes:</strong><br>
                {event_data['notes']}
            </div>
            """
        
        # Format HTML with event data
        html = HTML_TEMPLATE.format(
            validated_count=stats['validation_status'].get('validated', 0),
            needs_review_count=stats['validation_status'].get('needs_review', 0),
            problematic_count=stats['validation_status'].get('problematic', 0),
            percent_complete=stats['percent_complete'],
            total_events=stats['total_events'],
            current_index=index + 1,
            queue_size=len(queue),
            event_id=event['id'],
            title=event_data.get('title', 'Untitled'),
            date=event_data.get('date', 'Unknown'),
            importance=event_data.get('importance', 5),
            status=event_data.get('status', 'unknown'),
            summary=event_data.get('summary', 'No summary available'),
            sources_count=len(event_data.get('sources', [])),
            sources_html=sources_html,
            tags_html=tags_html,
            notes_section=notes_section
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def do_POST(self):
        """Handle POST requests"""
        from validation_tracker import ValidationTracker
        
        # Read form data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = urllib.parse.parse_qs(post_data)
        
        tracker = ValidationTracker()
        
        action = params.get('action', [''])[0]
        event_id = params.get('event_id', [''])[0]
        
        if action == 'validate':
            tracker.mark_validated(event_id, validator="web_ui")
            message = f"Event {event_id} marked as validated"
            
        elif action == 'problem':
            issues = params.get('issues', [''])[0].split(',')
            notes = params.get('notes', [''])[0]
            all_issues = issues
            if notes:
                all_issues.append(f"Notes: {notes}")
            tracker.mark_problematic(event_id, all_issues, validator="web_ui")
            message = f"Event {event_id} marked as problematic"
        
        # Redirect back to GET
        self.send_response(303)
        self.send_header('Location', '/')
        self.end_headers()


def run_server(port=8080):
    """Run the validation web server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ValidationHandler)
    print(f"Validation server running at http://localhost:{port}")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)