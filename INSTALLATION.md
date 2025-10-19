# Installation Guide

## Prerequisites

### System Requirements
- **Python**: 3.9 or higher
- **Node.js**: 16.x or higher (for timeline viewer)
- **Git**: For cloning the repository
- **Operating System**: macOS, Linux, or Windows (WSL recommended)

### Recommended
- **SQLite3**: For database management (usually pre-installed)
- **curl**: For API testing
- **jq**: For JSON formatting

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/kleptocracy-timeline.git
cd kleptocracy-timeline
```

### 2. Set Up Research Server

#### Install Python Dependencies

```bash
cd research-server
pip3 install -r requirements.txt
```

#### Configure Environment (Optional)

Create a `.env` file in the `research-server/` directory:

```bash
# Optional - defaults work for development
RESEARCH_MONITOR_PORT=5558
RESEARCH_MONITOR_API_KEY=your-api-key-here
COMMIT_THRESHOLD=10
```

#### Start the Server

```bash
# Using the CLI wrapper (recommended)
cd /path/to/kleptocracy-timeline
./research server-start

# Or manually
cd research-server/server
python3 app_v2.py
```

The server will start on `http://localhost:5558`

#### Verify Server is Running

```bash
# Using CLI wrapper
./research server-status

# Or directly
curl http://localhost:5558/api/server/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "healthy",
  "timestamp": "2025-10-19T..."
}
```

### 3. Set Up Timeline Viewer (Optional)

```bash
cd timeline/viewer
npm install
npm start
```

The viewer will open at `http://localhost:3000`

## Detailed Setup

### Research Server Components

The research server includes:
- **REST API**: Flask application for event and priority management
- **CLI Tools**: Command-line interface for research workflows
- **MCP Server**: AI agent integration (optional)
- **Database**: SQLite database for event metadata

#### Database Initialization

The database is automatically created on first run. To reset:

```bash
cd research-server
rm unified_research.db*
python3 server/app_v2.py
```

The server will:
1. Create fresh database schema
2. Sync all events from `timeline/data/events/`
3. Initialize validation tracking

### CLI Wrapper Setup

The CLI wrapper simplifies command execution:

```bash
# Make executable (if not already)
chmod +x research
chmod +x research-server/research

# Test the wrapper
./research get-stats
./research help
```

### Environment Variables

Complete list of environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `RESEARCH_MONITOR_PORT` | `5558` | Server port |
| `RESEARCH_MONITOR_API_KEY` | None | API authentication key |
| `RESEARCH_DB_PATH` | `../unified_research.db` | Database file path |
| `TIMELINE_EVENTS_PATH` | `../../timeline/data/events` | Events directory |
| `COMMIT_THRESHOLD` | `10` | Events before commit signal |
| `CACHE_TYPE` | `simple` | Flask cache type |
| `CACHE_DEFAULT_TIMEOUT` | `300` | Cache timeout (seconds) |

### Configuration Files

#### .env File Example

```bash
# Server Configuration
RESEARCH_MONITOR_PORT=5558
RESEARCH_MONITOR_API_KEY=my-secure-key-123

# Paths (usually don't need to change)
RESEARCH_DB_PATH=../unified_research.db
TIMELINE_EVENTS_PATH=../../timeline/data/events

# Performance
COMMIT_THRESHOLD=10
CACHE_DEFAULT_TIMEOUT=300
```

## Verification

### Test Core Functionality

```bash
# Get system statistics
./research get-stats

# Search events
./research search-events --query "Trump"

# List available tags
./research list-tags

# Create a test validation run
./research validation-runs-create --run-type random_sample --target-count 5
```

### Run Tests

```bash
cd research-server
python3 -m pytest tests/
```

## Common Issues

### Port Already in Use

```bash
# Check what's using port 5558
lsof -i :5558

# Stop existing server
./research server-stop

# Or kill manually
kill $(lsof -t -i:5558)
```

### Database Locked

```bash
# Stop the server first
./research server-stop

# Wait a few seconds
sleep 3

# Restart
./research server-start
```

### Module Not Found Errors

```bash
# Ensure you're using the CLI wrapper
./research <command>

# Or set PYTHONPATH manually
cd research-server
PYTHONPATH=client:server python3 cli/research_cli.py <command>
```

### Permission Denied

```bash
# Make scripts executable
chmod +x research
chmod +x research-server/research
```

## Development Setup

### Additional Tools

```bash
# Install development dependencies
pip3 install pytest pytest-cov pylint black mypy

# Run linter
cd research-server
pylint server/ client/ cli/

# Format code
black server/ client/ cli/

# Type checking
mypy server/ client/ cli/
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip3 install pre-commit

# Set up hooks
pre-commit install
```

## Production Deployment

### Server Deployment

For production use:

1. **Use environment variables** for configuration
2. **Set strong API key**: `RESEARCH_MONITOR_API_KEY`
3. **Use process manager**: systemd, supervisord, or pm2
4. **Set up reverse proxy**: nginx or Apache
5. **Enable HTTPS**: Use Let's Encrypt
6. **Configure log rotation**
7. **Set up monitoring**

### Example systemd Service

```ini
[Unit]
Description=Research Monitor Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/kleptocracy-timeline/research-server/server
Environment="RESEARCH_MONITOR_PORT=5558"
Environment="RESEARCH_MONITOR_API_KEY=your-secure-key"
ExecStart=/usr/bin/python3 app_v2.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:5558;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Backup and Maintenance

### Database Backup

```bash
# Stop server first
./research server-stop

# Backup database
cp research-server/unified_research.db research-server/unified_research.db.backup

# Restart server
./research server-start
```

### Log Management

```bash
# View server logs
./research server-logs

# Or manually
tail -f /tmp/research_server_restart.log
```

### Database Maintenance

```bash
# Vacuum database (optimize size)
sqlite3 research-server/unified_research.db "VACUUM;"

# Check integrity
sqlite3 research-server/unified_research.db "PRAGMA integrity_check;"
```

## Troubleshooting

### Check Server Logs

```bash
# View recent logs
tail -50 /tmp/research_server_restart.log

# Follow logs in real-time
tail -f /tmp/research_server_restart.log
```

### Database Issues

```bash
# Check database size
du -sh research-server/unified_research.db*

# Check table counts
sqlite3 research-server/unified_research.db "SELECT COUNT(*) FROM timeline_events;"
```

### Reset Everything

```bash
# Stop server
./research server-stop

# Remove database
rm research-server/unified_research.db*

# Start server (will rebuild)
./research server-start
```

## Next Steps

- Read [API_DOCUMENTATION.md](research-server/server/API_DOCUMENTATION.md) for API details
- See [CLAUDE.md](CLAUDE.md) for CLI command reference
- Check [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for maintenance tasks
- Review [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines

## Support

For issues or questions:
- Check existing documentation
- Review GitHub issues
- Submit new issue with detailed description
