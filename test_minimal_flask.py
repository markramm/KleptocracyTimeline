#!/usr/bin/env python3
"""
Minimal Flask app to isolate segfault causes
"""

from flask import Flask, jsonify
import sqlite3
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Simple SQLite without any threading
def get_db():
    conn = sqlite3.connect('test.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return "Test server running"

@app.route('/api/test')
def test_api():
    return jsonify({"status": "ok"})

@app.route('/api/db-test')
def test_db():
    """Test database access"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        conn.close()
        return jsonify({"db_test": "passed", "result": result[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("Starting minimal Flask test...")
    print("Testing components:")
    print("1. Basic Flask routes")
    print("2. SQLite connection") 
    print("3. No SocketIO")
    print("4. No file monitoring")
    print("5. No threading")
    
    app.run(host='127.0.0.1', port=5556, debug=False)