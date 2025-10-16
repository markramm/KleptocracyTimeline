#!/usr/bin/env python3
"""
Research Monitor Configuration
Centralized configuration for consistent server management
"""

import os

# Default port for Research Monitor server
DEFAULT_RESEARCH_MONITOR_PORT = 5558

def get_research_monitor_port():
    """Get the Research Monitor port from environment or default"""
    return int(os.environ.get('RESEARCH_MONITOR_PORT', DEFAULT_RESEARCH_MONITOR_PORT))

def get_research_monitor_url():
    """Get the full URL for the Research Monitor server"""
    port = get_research_monitor_port()
    return f"http://localhost:{port}"

# Server process management
SERVER_PID_FILE = "/tmp/research_monitor.pid"
SERVER_LOG_FILE = "/tmp/research_monitor.log"

# Database configuration
DATABASE_PATH = "../unified_research.db"
EVENTS_PATH = "../timeline_data/events"
PRIORITIES_PATH = "../research_priorities"

# Commit orchestration
COMMIT_THRESHOLD = 10