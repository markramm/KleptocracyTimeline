# Link Archiving Workflow

## Overview
All sources in the timeline should be archived to the Wayback Machine to prevent link rot and preserve evidence.

## Tools

### 1. Bulk Archiver (`archive_links.py`)
Archives all working links in the timeline. Run in background:
```bash
python3 archive_links.py &
```

Features:
- Tracks progress in `archive_progress.json`
- Skips already archived URLs
- Retries failed URLs after 24 hours
- Updates YAML files with archive URLs automatically
- Rate-limited to respect Archive.org (5 seconds between requests)

### 2. Single Event Archiver (`archive_new_link.py`)
Use when adding new sources to an event:
```bash
# Archive all URLs in an event file
python3 archive_new_link.py 2025-01-20--cabinet-wealth-450-billion.yaml

# Archive a single URL
python3 archive_new_link.py https://example.com/article
```

## Workflow for Adding New Sources

1. **Add the source to the YAML file** with standard format:
   ```yaml
   sources:
   - title: "Article Title"
     url: https://example.com/article
     outlet: News Outlet
     date: '2025-01-20'
   ```

2. **Archive immediately** after adding:
   ```bash
   python3 archive_new_link.py <event-file>.yaml
   ```

3. **The script will automatically update** the YAML with archive URLs:
   ```yaml
   sources:
   - title: "Article Title"
     url: https://example.com/article
     outlet: News Outlet
     date: '2025-01-20'
     archive_url: https://web.archive.org/web/20250819123456/https://example.com/article
   ```

## Archive URL Format

Archive URLs should follow this pattern:
- Specific snapshot: `https://web.archive.org/web/20250819123456/https://example.com`
- All snapshots: `https://web.archive.org/web/*/https://example.com`

## Progress Tracking

Check archiving progress:
```bash
cat archive_progress.json | python3 -m json.tool | head -20
```

## Best Practices

1. **Archive immediately** when adding new sources
2. **Check archive_progress.json** periodically for failed URLs
3. **Don't overwrite** existing archive_url entries that have specific timestamps
4. **Be patient** - archiving takes time (5 seconds per URL minimum)
5. **Run bulk archiver** periodically to catch any missed URLs

## Monitoring Background Archiver

Check if archiver is running:
```bash
ps aux | grep archive_links.py
```

View archiver output:
```bash
tail -f archive_output.log
```

## Recovery

If archiving is interrupted:
- Progress is saved every 10 URLs
- Simply restart `archive_links.py` - it will resume from where it left off
- Failed URLs are retried after 24 hours