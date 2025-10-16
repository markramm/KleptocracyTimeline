# Trump Tyranny Tracker Crawler

Systematic crawler for downloading and tracking articles from [Trump Tyranny Tracker Substack](https://trumptyrannytracker.substack.com/).

## Purpose

This crawler systematically downloads all articles from the Trump Tyranny Tracker Substack to:
1. Create a local archive of their 231+ days of corruption tracking
2. Track which articles have been processed for research priorities
3. Identify gaps in our kleptocracy timeline coverage
4. Enable systematic analysis of institutional capture patterns

## Directory Structure

```
ai-analysis/trump-tyranny-tracker/
├── articles/          # Downloaded article content (JSON files)
├── processed/         # Tracking files for processed articles
├── metadata/          # Crawl metadata and statistics
├── crawler.py         # Main crawler script
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Installation

```bash
cd ai-analysis/trump-tyranny-tracker
pip install -r requirements.txt
```

## Usage

### Full Crawl
```bash
python crawler.py --max-pages 20
```

### Check Statistics
```bash
python crawler.py --stats
```

### List Unprocessed Articles
```bash
python crawler.py --unprocessed
```

## Features

### Article Discovery
- Automatically discovers articles from Substack archive pages
- Extracts article metadata (title, date, URL, tags)
- Generates unique IDs for each article
- Tracks discovery timestamps

### Content Extraction
- Downloads full article content
- Preserves HTML structure
- Extracts structured metadata
- Counts words and content length
- Handles Substack-specific formatting

### Processing Tracking
- Tracks which articles have been converted to research priorities
- Prevents duplicate processing
- Maintains audit trail of analysis work
- Enables gap analysis

### Data Integrity
- Uses content hashes for duplicate detection
- Validates article structure
- Handles network errors gracefully
- Maintains crawl session history

## Article Processing Workflow

1. **Discovery**: Crawler finds all articles from archive pages
2. **Download**: Full content extracted and saved as JSON
3. **Analysis**: Articles reviewed for research priority creation
4. **Marking**: Processed articles marked to prevent re-analysis
5. **Tracking**: Unprocessed articles available for future work

## Integration with Research Pipeline

### Mark Article as Processed
```python
from crawler import TrumpTyrannyTrackerCrawler

crawler = TrumpTyrannyTrackerCrawler()
crawler.mark_processed("ttt-12345678-article-slug", "RT-TTT-2025-doj-weaponization")
```

### Get Unprocessed Articles
```python
unprocessed = crawler.get_unprocessed_articles()
for article in unprocessed:
    print(f"Need to analyze: {article['title']}")
```

## Output Format

### Article Files (articles/*.json)
```json
{
  "url": "https://trumptyrannytracker.substack.com/p/article-slug",
  "title": "Article Title",
  "date": "2025-01-15T10:30:00Z",
  "content": "Full article text...",
  "tags": ["corruption", "institutional-capture"],
  "html": "<html>...</html>",
  "extracted_at": "2025-09-10T15:45:00Z",
  "content_length": 5420,
  "word_count": 892
}
```

### Processed Files (processed/*.json)
```json
{
  "article_id": "ttt-12345678-article-slug",
  "processed_at": "2025-09-10T16:00:00Z",
  "research_priority": "RT-TTT-2025-doj-weaponization",
  "status": "processed"
}
```

## Metadata Tracking

The crawler maintains comprehensive metadata in `metadata/crawl_metadata.json`:

- **Articles**: Complete inventory with download timestamps
- **Crawl Sessions**: History of all crawl runs
- **Statistics**: Total articles, processed counts, etc.
- **Error Tracking**: Failed downloads and issues

## Best Practices

### Respectful Crawling
- 2-second delays between requests
- Proper User-Agent headers
- Error handling for rate limits
- Session management

### Data Quality
- Content validation
- Duplicate detection
- Error logging
- Retry mechanisms

### Analysis Integration
- Clear processing status tracking
- Research priority linkage
- Gap identification tools
- Progress monitoring

## Expected Results

Based on initial analysis, expect:
- **200-300 articles** from 231+ days of tracking
- **Systematic corruption patterns** across multiple institutions
- **Specific events with dates** ready for timeline integration
- **Institutional capture mechanisms** not covered in current timeline

## Next Steps

1. Run full crawl: `python crawler.py --max-pages 25`
2. Review unprocessed articles: `python crawler.py --unprocessed`
3. Create research priorities for high-value articles
4. Mark processed articles to track progress
5. Identify systematic patterns for timeline integration