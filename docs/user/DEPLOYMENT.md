# Static Site Deployment Guide

The timeline viewer is a **100% static site** that can be deployed to GitHub Pages or any static hosting service.

## Architecture

- **Data**: YAML files in `timeline_data/events/`
- **API**: Static JSON files generated from YAML data
- **Frontend**: React single-page application
- **No server required**: Everything runs in the browser

## Quick Deploy to GitHub Pages

### Automatic (via GitHub Actions)

1. Push to `main` branch
2. GitHub Actions will automatically:
   - Generate static API files
   - Build React app
   - Deploy to GitHub Pages

### Manual Build

```bash
# Build complete static site
./build_static_site.sh

# Commit and push
git add docs/
git commit -m "Update static site"
git push
```

### Enable GitHub Pages

1. Go to Settings → Pages
2. Source: Deploy from a branch
3. Branch: main
4. Folder: /docs
5. Save

Your site will be available at:
`https://[username].github.io/kleptocracy-timeline/`

## Local Development

### Test Static Build

```bash
# Build and serve locally (exactly as it will appear on GitHub Pages)
./test_static_site.sh
# Open http://localhost:8000
```

### Development Mode

```bash
# Terminal 1: Generate and serve API files
cd api
python3 generate_static_api.py
python3 serve_static.py

# Terminal 2: Run React dev server
cd viewer
npm start
# Open http://localhost:3000
```

## File Structure

```
kleptocracy-timeline/
├── timeline_data/         # Source data (YAML)
│   └── events/           
├── api/                   # API generation
│   ├── generate_static_api.py
│   └── static_api/       # Generated JSON (gitignored)
├── viewer/                # React app
│   ├── src/
│   ├── public/
│   └── build/            # Production build (gitignored)
└── docs/                  # GitHub Pages site (committed)
    ├── index.html
    ├── static/           # React assets
    └── api/              # JSON data files
```

## How It Works

1. **Data Generation**: `generate_static_api.py` reads YAML files and creates JSON
2. **Build Process**: React app is built with production optimizations
3. **Static Serving**: All files are served as static assets
4. **Client-Side Routing**: React Router handles navigation
5. **Data Fetching**: App fetches JSON files via relative URLs

## Adding New Data

1. Add/edit YAML files in `timeline_data/events/`
2. Run `./build_static_site.sh`
3. Commit both source (YAML) and built files (docs/)
4. Push to GitHub

## Other Deployment Options

### Netlify

```bash
# Build
./build_static_site.sh

# Deploy
npx netlify-cli deploy --dir=docs --prod
```

### Vercel

```bash
# Build
./build_static_site.sh

# Deploy
npx vercel --prod docs/
```

### AWS S3 + CloudFront

```bash
# Build
./build_static_site.sh

# Upload to S3
aws s3 sync docs/ s3://your-bucket/ --delete

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Self-Hosted

Copy the `docs/` folder to any web server (Apache, Nginx, etc.).
No server-side processing required.

## Performance

- **Initial Load**: ~150KB gzipped (includes all timeline data)
- **No API calls**: Everything loads from static files
- **CDN-friendly**: All assets are cacheable
- **Offline-capable**: Can add service worker for offline support

## Updating Data via GitHub Actions

The workflow automatically rebuilds when:
- Timeline events are added/modified
- React app code changes
- Manual trigger via GitHub Actions UI

## Troubleshooting

### 404 Errors on GitHub Pages

- Ensure `.nojekyll` file exists in docs/
- Check GitHub Pages is enabled in settings
- Wait 10 minutes for initial deployment

### Data Not Updating

1. Regenerate API files: `cd api && python3 generate_static_api.py`
2. Rebuild site: `./build_static_site.sh`
3. Clear browser cache

### Local Testing Issues

- Ensure Python 3 is installed
- Ensure Node.js 18+ is installed
- Run `npm ci` in viewer/ directory

## Security

- No server = no server vulnerabilities
- All data is public (no authentication)
- CORS not required (same-origin)
- Content Security Policy can be strict
