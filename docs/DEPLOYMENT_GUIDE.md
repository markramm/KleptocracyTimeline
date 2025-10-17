# Deployment Guide

**Last Updated**: 2025-10-17

This guide covers deploying the Kleptocracy Timeline in production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Timeline Viewer Deployment (GitHub Pages)](#timeline-viewer-deployment)
3. [Research Server Deployment](#research-server-deployment)
4. [Database Management](#database-management)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)
6. [Security Considerations](#security-considerations)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### For Timeline Viewer
- GitHub account with Pages enabled
- Node.js 16+ and npm
- Git

### For Research Server
- Linux server or VPS
- Python 3.9+
- SQLite3
- 2GB+ RAM recommended
- systemd (for service management)
- nginx or Apache (optional, for reverse proxy)

---

## Timeline Viewer Deployment

The timeline viewer is a static React application suitable for GitHub Pages deployment.

### Step 1: Build the Static Site

```bash
cd timeline/viewer

# Install dependencies
npm install

# Build with PUBLIC_URL set for GitHub Pages
PUBLIC_URL=/kleptocracy-timeline npm run build

# Build output will be in timeline/viewer/build/
```

### Step 2: Deploy to GitHub Pages

**Option A: GitHub Actions (Recommended)**

Create `.github/workflows/deploy-timeline.yml`:

```yaml
name: Deploy Timeline Viewer

on:
  push:
    branches: [ main ]
    paths:
      - 'timeline/viewer/**'
      - 'timeline/data/events/**'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install and Build
        run: |
          cd timeline/viewer
          npm ci
          PUBLIC_URL=/kleptocracy-timeline npm run build

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./timeline/viewer/build
```

**Option B: Manual Deployment**

```bash
# Build the site
cd timeline/viewer
PUBLIC_URL=/kleptocracy-timeline npm run build

# Deploy using gh-pages
npm install -g gh-pages
gh-pages -d build
```

### Step 3: Configure GitHub Pages

1. Go to repository Settings → Pages
2. Set Source to `gh-pages` branch
3. Custom domain (optional): Add CNAME file to `timeline/viewer/public/`

### Step 4: Verify Deployment

Visit: `https://[username].github.io/kleptocracy-timeline/`

---

## Research Server Deployment

The research server is a Flask application with SQLite database.

### Step 1: Prepare the Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.9 python3-pip python3-venv sqlite3 git

# Create application user
sudo useradd -r -s /bin/bash -d /opt/kleptocracy timeline
sudo mkdir -p /opt/kleptocracy
sudo chown timeline:timeline /opt/kleptocracy
```

### Step 2: Clone and Setup

```bash
# Switch to application user
sudo su - timeline

# Clone repository
git clone https://github.com/[username]/kleptocracy-timeline.git
cd kleptocracy-timeline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r research-server/requirements.txt

# Verify installation
python3 research_cli.py --help
```

### Step 3: Configure the Service

Create `/etc/systemd/system/kleptocracy-research-server.service`:

```ini
[Unit]
Description=Kleptocracy Timeline Research Server
After=network.target

[Service]
Type=simple
User=timeline
WorkingDirectory=/opt/kleptocracy/kleptocracy-timeline
Environment="PATH=/opt/kleptocracy/kleptocracy-timeline/venv/bin"
Environment="RESEARCH_MONITOR_PORT=5558"
Environment="FLASK_ENV=production"
ExecStart=/opt/kleptocracy/kleptocracy-timeline/venv/bin/python3 research_monitor/app_v2.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 4: Start the Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable kleptocracy-research-server

# Start service
sudo systemctl start kleptocracy-research-server

# Check status
sudo systemctl status kleptocracy-research-server

# View logs
sudo journalctl -u kleptocracy-research-server -f
```

### Step 5: Configure Reverse Proxy (Optional)

**nginx configuration** (`/etc/nginx/sites-available/kleptocracy-research`):

```nginx
server {
    listen 80;
    server_name research.your-domain.com;

    location / {
        proxy_pass http://localhost:5558;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running operations
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

Enable and restart nginx:

```bash
sudo ln -s /etc/nginx/sites-available/kleptocracy-research /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: SSL Certificate (Recommended)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d research.your-domain.com

# Auto-renewal is configured by default
sudo certbot renew --dry-run
```

---

## Database Management

### Backup Strategy

**Automated Daily Backups**:

Create `/opt/kleptocracy/backup-database.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/kleptocracy/backups"
DB_PATH="/opt/kleptocracy/kleptocracy-timeline/unified_research.db"
DATE=$(date +%Y-%m-%d-%H%M%S)

mkdir -p $BACKUP_DIR

# Create backup with timestamp
sqlite3 $DB_PATH ".backup $BACKUP_DIR/unified_research-$DATE.db"

# Keep only last 30 days
find $BACKUP_DIR -name "unified_research-*.db" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/unified_research-$DATE.db"
```

**Add to crontab**:

```bash
# Run daily at 2 AM
0 2 * * * /opt/kleptocracy/backup-database.sh >> /var/log/kleptocracy-backup.log 2>&1
```

### Database Migrations

```bash
cd /opt/kleptocracy/kleptocracy-timeline
source venv/bin/activate

# Check current version
cd research-server
alembic current

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Database Maintenance

```bash
# Vacuum database (reduces file size)
sqlite3 unified_research.db "VACUUM;"

# Analyze for query optimization
sqlite3 unified_research.db "ANALYZE;"

# Check integrity
sqlite3 unified_research.db "PRAGMA integrity_check;"
```

---

## Monitoring and Maintenance

### Log Management

```bash
# View research server logs
sudo journalctl -u kleptocracy-research-server -f

# Last 100 lines
sudo journalctl -u kleptocracy-research-server -n 100

# Logs from specific date
sudo journalctl -u kleptocracy-research-server --since "2025-01-15"
```

### Health Checks

**Manual Health Check**:

```bash
# Using CLI
python3 research_cli.py server-status

# Using curl
curl http://localhost:5558/api/server/health
```

**Automated Monitoring** (optional):

Create `/opt/kleptocracy/health-check.sh`:

```bash
#!/bin/bash
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5558/api/server/health)

if [ "$STATUS" != "200" ]; then
    echo "Research server unhealthy! Status: $STATUS"
    # Send alert (email, Slack, etc.)
    systemctl restart kleptocracy-research-server
fi
```

Add to crontab:
```bash
*/5 * * * * /opt/kleptocracy/health-check.sh
```

### System Statistics

```bash
# Check system resource usage
python3 research_cli.py get-stats

# Database size
du -h unified_research.db

# Disk space
df -h /opt/kleptocracy
```

### Updates

```bash
# Pull latest changes
cd /opt/kleptocracy/kleptocracy-timeline
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart kleptocracy-research-server
```

---

## Security Considerations

### 1. Database Security

```bash
# Set proper permissions
chmod 600 unified_research.db
chown timeline:timeline unified_research.db

# Backup encryption (optional)
gpg --encrypt --recipient your-email@example.com backup.db
```

### 2. API Authentication (Recommended for Production)

Add API key authentication to research server:

In `research_monitor/app_v2.py`, add:

```python
from functools import wraps
import os

API_KEY = os.environ.get('RESEARCH_API_KEY')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if not key or key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Apply to routes:
@app.route('/api/events', methods=['POST'])
@require_api_key
def create_event():
    # ...
```

Set API key in systemd service:

```ini
Environment="RESEARCH_API_KEY=your-secure-random-key"
```

### 3. Firewall Configuration

```bash
# Allow SSH and HTTP/HTTPS
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443

# Block direct access to Flask port (use nginx instead)
sudo ufw deny 5558

# Enable firewall
sudo ufw enable
```

### 4. Rate Limiting

Configure nginx rate limiting:

```nginx
http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://localhost:5558;
        }
    }
}
```

---

## Troubleshooting

### Research Server Won't Start

**Check logs:**
```bash
sudo journalctl -u kleptocracy-research-server -n 50
```

**Common issues:**

1. **Port already in use:**
   ```bash
   lsof -i :5558
   kill [PID]
   ```

2. **Database locked:**
   ```bash
   # Stop all processes accessing database
   sudo systemctl stop kleptocracy-research-server
   # Remove lock files
   rm -f unified_research.db-wal unified_research.db-shm
   # Restart
   sudo systemctl start kleptocracy-research-server
   ```

3. **Permission errors:**
   ```bash
   sudo chown -R timeline:timeline /opt/kleptocracy/kleptocracy-timeline
   chmod 755 /opt/kleptocracy/kleptocracy-timeline
   chmod 600 unified_research.db
   ```

### Timeline Viewer Not Loading

1. **Check build artifacts:**
   ```bash
   ls -la timeline/viewer/build/
   ```

2. **Verify PUBLIC_URL:**
   ```bash
   # Should match GitHub Pages URL
   grep PUBLIC_URL timeline/viewer/build/index.html
   ```

3. **Check GitHub Pages settings:**
   - Repository Settings → Pages
   - Verify source branch is correct

### Database Corruption

```bash
# Check integrity
sqlite3 unified_research.db "PRAGMA integrity_check;"

# Restore from backup
cd /opt/kleptocracy/backups
ls -lt unified_research-*.db | head -1  # Find latest backup
cp unified_research-2025-01-15-020000.db ../kleptocracy-timeline/unified_research.db
sudo systemctl restart kleptocracy-research-server
```

---

## Performance Tuning

### SQLite Optimization

Add to `research_monitor/app_v2.py`:

```python
# Configure SQLite for better performance
db.session.execute(text("PRAGMA journal_mode=WAL"))
db.session.execute(text("PRAGMA synchronous=NORMAL"))
db.session.execute(text("PRAGMA cache_size=10000"))
db.session.execute(text("PRAGMA temp_store=MEMORY"))
```

### Flask Configuration

```python
# Production settings
app.config.update(
    ENV='production',
    DEBUG=False,
    TESTING=False,
    PROPAGATE_EXCEPTIONS=False
)
```

---

## Additional Resources

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Repository layout
- [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) - Development environment
- [SECURITY.md](../SECURITY.md) - Security policy
- Flask Documentation: https://flask.palletsprojects.com/
- nginx Documentation: https://nginx.org/en/docs/
- SQLite Documentation: https://www.sqlite.org/docs.html

---

**Status**: Production Ready
**Last Updated**: 2025-10-17
**Tested Platforms**: Ubuntu 20.04 LTS, Ubuntu 22.04 LTS
