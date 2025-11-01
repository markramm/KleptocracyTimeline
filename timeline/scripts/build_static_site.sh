#!/bin/bash

# Build complete static site for GitHub Pages deployment
# This generates all static files needed for the timeline viewer

set -e  # Exit on error

echo "🚀 Building static timeline site..."

# 1. Generate static API JSON files
echo "📊 Generating static API files..."
cd api
python3 generate_static_api.py

# 2. Copy API files to React public folder
echo "📁 Copying API files to React app..."
mkdir -p ../viewer/public/api
cp -r static_api/* ../viewer/public/api/

# 3. Build React app
echo "⚛️ Building React app..."
cd ../viewer
npm run build

# 4. Copy everything to docs folder for GitHub Pages
echo "📦 Preparing GitHub Pages deployment..."
cd ..
rm -rf docs
mkdir -p docs
cp -r viewer/build/* docs/

# 5. Copy API files to docs
cp -r api/static_api docs/api

# 6. Add .nojekyll file to prevent GitHub Pages Jekyll processing
touch docs/.nojekyll

echo "✅ Static site built successfully!"
echo "📍 Output directory: docs/"
echo "🌐 Ready for GitHub Pages deployment"
echo ""
echo "To deploy:"
echo "  1. git add docs/"
echo "  2. git commit -m 'Update static site'"
echo "  3. git push"
echo "  4. Enable GitHub Pages from docs/ folder in repo settings"
