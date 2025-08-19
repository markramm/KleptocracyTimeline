# Timeline Archiving Tools

This directory contains tools for archiving timeline sources to prevent link rot.

## Main Archive Script

### `archive_with_progress.py`

A respectful, rate-limited archiver that saves all timeline sources to Archive.org.

**Features:**
- Conservative rate limiting (10 requests/minute)
- Automatic progress tracking and resume capability
- Handles 429 rate limits with proper cooldown periods
- Skips recently archived URLs (within 30 days)
- Detailed logging and progress reporting
- Graceful interruption handling (Ctrl+C saves progress)

**Usage:**

```bash
# Archive all timeline sources
python3 tools/archiving/archive_with_progress.py

# Use custom events directory
python3 tools/archiving/archive_with_progress.py --events-dir path/to/events

# Retry only previously failed URLs
python3 tools/archiving/archive_with_progress.py --retry-failed
```

**Output Files:**
- `timeline_data/archive_progress.json` - Tracks archived, failed, and skipped URLs
- `timeline_data/archive.log` - Detailed log of archiving operations

**Rate Limiting:**
The script respects Archive.org's rate limits:
- Maximum 10 requests per minute (conservative, below their 15/min limit)
- 1-hour cooldown after any 429 error
- Exponential backoff for consecutive failures
- Random jitter added to avoid appearing robotic

## Other Archiving Tools

### `batch_archive.py`
Batch archiver for processing multiple URLs efficiently.

### `gen_archive_qa.py`
Quality assurance tool for verifying archived sources.

### `link_check.py`
Checks for broken links in timeline events.

## Best Practices

1. **Run During Off-Peak Hours**: Archive during times when Archive.org has lower traffic
2. **Monitor Progress**: Check the log file for any issues
3. **Handle Failures**: Re-run with `--retry-failed` to attempt failed URLs again
4. **Be Patient**: With 1000+ URLs, archiving can take several hours
5. **Check Archive Coverage**: Use `gen_archive_qa.py` to verify archive completeness

## Archive.org Guidelines

We follow Archive.org's best practices:
- Never exceed 15 requests per minute
- Respect 429 rate limit responses with 1-hour cooldown
- Use descriptive User-Agent string
- Check if URLs are already archived before re-archiving

## Troubleshooting

**Connection Refused:**
- You may have been temporarily IP blocked
- Wait 30-60 minutes before retrying
- Consider reducing request rate further

**High Failure Rate:**
- Some sites block Archive.org
- Some URLs may no longer exist
- Check failed URLs manually in `archive_progress.json`

**Script Interrupted:**
- Progress is automatically saved
- Simply re-run the script to continue where you left off

## Archive Status

Current archive coverage can be checked with:
```bash
python3 tools/archiving/gen_archive_qa.py
```

This will generate a report showing:
- Total sources requiring archival
- Successfully archived count
- Failed/pending archives
- Coverage percentage