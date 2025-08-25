#!/usr/bin/env python3
"""
Scrape and archive all sources cited in timeline events.
Saves HTML content to events/.sources/ folder with naming pattern:
{event_id}_source{number}.html
"""

import os
import sys
import json
import yaml
import time
import logging
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple

# Configuration
EVENTS_DIR = Path("events")
SOURCES_DIR = EVENTS_DIR / ".sources"
PROGRESS_FILE = SOURCES_DIR / "scraping_progress.json"
ERROR_LOG = SOURCES_DIR / "scraping_errors.log"
METADATA_FILE = SOURCES_DIR / "metadata.json"

# Rate limiting
DELAY_BETWEEN_REQUESTS = 2  # seconds
MAX_RETRIES = 3
TIMEOUT = 30  # seconds

# Headers to avoid blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def setup_logging():
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(ERROR_LOG),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def load_progress() -> Dict:
    """Load progress tracking data."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"completed": [], "failed": [], "last_run": None}

def save_progress(progress: Dict):
    """Save progress tracking data."""
    progress["last_run"] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def load_metadata() -> Dict:
    """Load metadata for scraped sources."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_metadata(metadata: Dict):
    """Save metadata for scraped sources."""
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def get_event_files() -> List[Path]:
    """Get all YAML event files."""
    return sorted(EVENTS_DIR.glob("*.yaml"))

def parse_event_sources(event_file: Path) -> Tuple[str, List[Dict]]:
    """Extract event ID and sources from YAML file."""
    with open(event_file, 'r') as f:
        data = yaml.safe_load(f)
    
    event_id = data.get('id', event_file.stem)
    sources = data.get('sources', [])
    
    return event_id, sources

def scrape_url(url: str, logger: logging.Logger) -> Optional[str]:
    """Scrape HTML content from URL with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                url, 
                headers=HEADERS, 
                timeout=TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(DELAY_BETWEEN_REQUESTS * (attempt + 1))
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error on attempt {attempt + 1} for {url}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(DELAY_BETWEEN_REQUESTS * (attempt + 1))
                
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            break
    
    return None

def scrape_with_archive_fallback(source: Dict, logger: logging.Logger) -> Optional[str]:
    """Try to scrape URL, fall back to archive.org if available."""
    url = source.get('url')
    archive_url = source.get('archive_url')
    
    if not url:
        return None
    
    # Try main URL first
    logger.info(f"Attempting to scrape: {url}")
    content = scrape_url(url, logger)
    
    if content:
        return content
    
    # Try archive URL if available
    if archive_url:
        logger.info(f"Main URL failed, trying archive: {archive_url}")
        content = scrape_url(archive_url, logger)
        if content:
            return content
    
    # Try to construct archive.org URL if not provided
    if not archive_url:
        archive_url = f"https://web.archive.org/web/2/{url}"
        logger.info(f"Trying auto-generated archive URL: {archive_url}")
        content = scrape_url(archive_url, logger)
        if content:
            return content
    
    return None

def save_source_content(event_id: str, source_num: int, content: str, source: Dict, metadata: Dict):
    """Save scraped content to file and update metadata."""
    filename = f"{event_id}_source{source_num}.html"
    filepath = SOURCES_DIR / filename
    
    # Save HTML content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Update metadata
    if event_id not in metadata:
        metadata[event_id] = {}
    
    metadata[event_id][f"source{source_num}"] = {
        "filename": filename,
        "url": source.get('url'),
        "archive_url": source.get('archive_url'),
        "outlet": source.get('outlet'),
        "title": source.get('title'),
        "date": source.get('date'),
        "scraped_at": datetime.now().isoformat(),
        "file_size": len(content)
    }

def main():
    """Main scraping function."""
    # Setup
    SOURCES_DIR.mkdir(exist_ok=True)
    logger = setup_logging()
    progress = load_progress()
    metadata = load_metadata()
    
    logger.info("Starting source scraping process...")
    
    # Statistics
    total_events = 0
    total_sources = 0
    successful_scrapes = 0
    failed_scrapes = 0
    
    # Process each event file
    event_files = get_event_files()
    logger.info(f"Found {len(event_files)} event files to process")
    
    for event_file in event_files:
        try:
            event_id, sources = parse_event_sources(event_file)
            
            if not sources:
                logger.debug(f"No sources in {event_id}")
                continue
            
            total_events += 1
            
            # Process each source
            for i, source in enumerate(sources, 1):
                source_key = f"{event_id}_source{i}"
                total_sources += 1
                
                # Skip if already processed
                if source_key in progress["completed"]:
                    logger.debug(f"Skipping already completed: {source_key}")
                    continue
                
                if source_key in progress["failed"]:
                    logger.debug(f"Skipping previously failed: {source_key}")
                    continue
                
                # Scrape the source
                content = scrape_with_archive_fallback(source, logger)
                
                if content:
                    save_source_content(event_id, i, content, source, metadata)
                    progress["completed"].append(source_key)
                    successful_scrapes += 1
                    logger.info(f"✓ Saved {source_key} ({len(content)} bytes)")
                else:
                    progress["failed"].append(source_key)
                    failed_scrapes += 1
                    logger.error(f"✗ Failed to scrape {source_key}: {source.get('url')}")
                
                # Save progress periodically
                if (successful_scrapes + failed_scrapes) % 10 == 0:
                    save_progress(progress)
                    save_metadata(metadata)
                
                # Rate limiting
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
        except Exception as e:
            logger.error(f"Error processing {event_file}: {e}")
            continue
    
    # Final save
    save_progress(progress)
    save_metadata(metadata)
    
    # Summary
    logger.info("=" * 60)
    logger.info("SCRAPING COMPLETE")
    logger.info(f"Events processed: {total_events}")
    logger.info(f"Total sources: {total_sources}")
    logger.info(f"Successful scrapes: {successful_scrapes}")
    logger.info(f"Failed scrapes: {failed_scrapes}")
    logger.info(f"Success rate: {successful_scrapes/total_sources*100:.1f}%" if total_sources > 0 else "N/A")
    logger.info("=" * 60)
    
    # List some failed sources for review
    if progress["failed"]:
        logger.info("\nFailed sources (first 10):")
        for failed in progress["failed"][:10]:
            logger.info(f"  - {failed}")
        if len(progress["failed"]) > 10:
            logger.info(f"  ... and {len(progress['failed']) - 10} more")

if __name__ == "__main__":
    main()