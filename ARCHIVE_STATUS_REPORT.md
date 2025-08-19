# Archive Status Report
*Generated: August 19, 2025*

## Overall Archive Coverage

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Events** | 332 | 100% |
| **Events with Archived Sources** | 88 | 26.5% |
| **Total Sources** | 1,044 | 100% |
| **Sources with Archive URLs** | 132 | 12.6% |

## Archive Progress Summary

| Status | Count | Notes |
|--------|-------|-------|
| **Successfully Archived** | 5 | URLs successfully saved to Archive.org |
| **Failed Attempts** | 521 | Most failed due to rate limiting (429 errors) |
| **Not Yet Attempted** | ~518 | Sources without archive attempts |

## Failed Archive Reasons

- **Rate Limiting (429)**: Most failures - Archive.org rate limits
- **Timeouts**: Some URLs took too long to archive
- **404 Not Found**: Some sources no longer exist

## Priority Sources Needing Archive

### Critical Government Sources
- Department of Justice press releases
- White House statements
- Congressional documents
- Court filings and opinions

### News Sources at Risk
- Paywalled content (Washington Post, NYT, etc.)
- Smaller outlets that may disappear
- Tech news sites with high turnover

### Academic and Research
- Think tank reports
- University research papers
- Policy institute analyses

## Recommendations

### Immediate Actions
1. **Resume Archiving with Rate Limiting**
   ```bash
   python3 scripts/archive.py --rate 30
   ```

2. **Retry Failed URLs**
   ```bash
   python3 scripts/archive.py --retry-failed
   ```

3. **Check Archive Coverage**
   ```bash
   python3 scripts/archive.py --check-coverage
   ```

### Long-term Strategy
1. **Daily Archive Runs**: Set up automated daily archiving for new sources
2. **Priority Queue**: Archive most critical sources first
3. **Alternative Archives**: Consider using multiple archive services
4. **Local Backup**: Keep local copies of most critical sources

## Archive Status by Event Category

### High-Priority Events (Monitoring Active)
- LA National Guard Deployment: 3/4 sources archived
- DOGE Establishment: 0/3 sources archived
- Border Emergency: 0/5 sources archived
- Minnesota Assassination: 0/4 sources archived (needs update)
- CFPB Shutdown: 0/3 sources archived
- IG Mass Firings: 0/7 sources archived

### Recent Events (2025)
- Most 2025 events have minimal archive coverage
- Priority should be given to government sources that may be removed

### Historical Events (Pre-2025)
- Better archive coverage for older events
- Many sources already in Archive.org from previous captures

## Technical Notes

### Archive Infrastructure
- **Progress Tracking**: `timeline_data/archive_progress.json`
- **Error Logging**: `timeline_data/archive.log`
- **Rate Limiting**: Configured for 30-second delays between requests
- **Retry Logic**: Failed URLs marked for retry after 24 hours

### Archive URL Format
```
https://web.archive.org/web/[timestamp]/[original_url]
```

### Integration Points
- Archive URLs are stored directly in event YAML files
- `archive_url` field added to each source when archived
- Validation scripts check for archive coverage

## Next Steps

1. **Run Full Archive Pass**
   - Estimated time: ~9 hours for remaining sources (with rate limiting)
   - Best run overnight or in background

2. **Update Critical Events**
   - Focus on events with monitoring status = "active"
   - Prioritize government and legal sources

3. **Create Archive Policy**
   - Define which sources must be archived
   - Set up automatic archiving for new events
   - Regular archive health checks

---

*Note: Archive.org may have captured many of these URLs independently. Run `--check-coverage` to verify actual archive availability before creating new snapshots.*