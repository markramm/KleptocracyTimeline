#!/bin/bash

# Test the static site locally
# This builds and serves the site exactly as it would appear on GitHub Pages

set -e

echo "🧪 Testing static site locally..."

# 1. Build the static site
./build_static_site.sh

# 2. Serve it locally
echo ""
echo "🌐 Starting local static server..."
echo "🔗 Open http://localhost:8000 in your browser"
echo "🛍️ Press Ctrl+C to stop"
echo ""

cd docs
python3 -m http.server 8000
