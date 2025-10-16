#!/usr/bin/env python3
"""
Trump Tyranny Tracker Substack Crawler
Systematically downloads and tracks articles from trumptyrannytracker.substack.com
"""

import requests
import json
import os
import time
import hashlib
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional

class TrumpTyrannyTrackerCrawler:
    def __init__(self, base_dir: str = "ai-analysis/trump-tyranny-tracker"):
        self.base_url = "https://trumptyrannytracker.substack.com"
        self.base_dir = base_dir
        self.articles_dir = os.path.join(base_dir, "articles")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.metadata_dir = os.path.join(base_dir, "metadata")
        
        # Create directories
        os.makedirs(self.articles_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Load existing metadata
        self.metadata_file = os.path.join(self.metadata_dir, "crawl_metadata.json")
        self.metadata = self.load_metadata()
    
    def load_metadata(self) -> Dict:
        """Load existing crawl metadata"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            "articles": {},
            "crawl_sessions": [],
            "last_crawl": None,
            "total_articles": 0
        }
    
    def save_metadata(self):
        """Save crawl metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_article_links_api(self) -> List[Dict]:
        """Get all article links using Substack's JSON API (preferred method)"""
        articles = []
        
        try:
            print("Fetching articles via Substack JSON API...")
            
            # Try different API endpoints
            api_urls = [
                f"{self.base_url}/api/v1/archive",
                f"{self.base_url}/api/v1/posts",
                f"{self.base_url}/api/v1/publications/posts"
            ]
            
            for api_url in api_urls:
                try:
                    print(f"Trying API endpoint: {api_url}")
                    response = self.session.get(api_url)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Handle different JSON structures
                    posts = []
                    if isinstance(data, list):
                        posts = data
                    elif isinstance(data, dict):
                        # Common Substack API structures
                        posts = data.get('posts', data.get('data', data.get('items', [])))
                    
                    print(f"Found {len(posts)} posts in API response")
                    
                    for post in posts:
                        if isinstance(post, dict):
                            # Extract article information from JSON
                            post_id = post.get('id')
                            slug = post.get('slug', '')
                            title = post.get('title', 'Untitled')
                            date = post.get('post_date', post.get('created_at', ''))
                            
                            if slug and title:
                                url = f"{self.base_url}/p/{slug}"
                                
                                articles.append({
                                    'url': url,
                                    'title': title,
                                    'date': date,
                                    'post_id': post_id,
                                    'discovered': datetime.now().isoformat(),
                                    'source': 'api'
                                })
                    
                    if articles:
                        # Found articles with this API endpoint
                        print(f"Successfully retrieved {len(articles)} articles from API")
                        return articles
                        
                except Exception as e:
                    print(f"API endpoint {api_url} failed: {e}")
                    continue
            
            print("All API endpoints failed, falling back to HTML scraping...")
            return self.get_article_links_html(max_pages=50)
            
        except Exception as e:
            print(f"API method failed: {e}")
            print("Falling back to HTML scraping...")
            return self.get_article_links_html(max_pages=50)
    
    def get_article_links_html(self, max_pages: int = 50) -> List[Dict]:
        """Get all article links from the Substack archive with improved discovery"""
        articles = []
        articles_per_page = 12  # Substack default
        page = 0
        consecutive_empty_pages = 0
        
        print(f"Starting comprehensive article discovery (max {max_pages} pages)...")
        
        while page < max_pages and consecutive_empty_pages < 3:
            try:
                # Multiple URL patterns to try
                urls_to_try = []
                
                if page == 0:
                    # First page patterns
                    urls_to_try = [
                        f"{self.base_url}/archive",
                        f"{self.base_url}/archive?sort=new",
                        f"{self.base_url}/archive?sort=top"
                    ]
                else:
                    # Pagination patterns
                    offset = page * articles_per_page
                    urls_to_try = [
                        f"{self.base_url}/archive?sort=new&search=&offset={offset}",
                        f"{self.base_url}/archive?offset={offset}",
                        f"{self.base_url}/archive?sort=top&offset={offset}",
                        f"{self.base_url}/archive?page={page}",
                        f"{self.base_url}/archive?p={page}"
                    ]
                
                page_articles = []
                
                for url in urls_to_try:
                    try:
                        print(f"Trying URL: {url}")
                        response = self.session.get(url)
                        response.raise_for_status()
                        
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Multiple selectors for article links
                        selectors = [
                            'a[href*="/p/"]',  # Direct href pattern
                            'h2 a[href*="/p/"]',  # Title links
                            'h3 a[href*="/p/"]',  # Subtitle links
                            '.post-preview a[href*="/p/"]',  # Post preview links
                            '.pencraft a[href*="/p/"]',  # Substack's CSS class
                            'article a[href*="/p/"]'  # Article container links
                        ]
                        
                        found_links = []
                        for selector in selectors:
                            found_links.extend(soup.select(selector))
                        
                        print(f"Found {len(found_links)} potential article links")
                        
                        for link in found_links:
                            href = link.get('href')
                            if href and '/p/' in href and not href.endswith('/comments'):
                                # Get full URL
                                full_url = urljoin(self.base_url, href)
                                
                                # Extract title from multiple sources
                                title = None
                                
                                # Try link text
                                title = link.get_text().strip()
                                
                                # Try nearby title elements
                                if not title or len(title) < 5:
                                    parent = link.find_parent()
                                    if parent:
                                        title_elem = (parent.find('h1') or parent.find('h2') or 
                                                     parent.find('h3') or parent.find('.post-title') or
                                                     parent.find('[class*="title"]'))
                                        if title_elem:
                                            title = title_elem.get_text().strip()
                                
                                # Try data attributes
                                if not title or len(title) < 5:
                                    title = link.get('title') or link.get('aria-label', '')
                                
                                # Clean up title
                                if title:
                                    title = re.sub(r'\s+', ' ', title).strip()
                                    title = title.replace('\n', ' ').replace('\t', ' ')
                                
                                # Only add if we have a reasonable title and haven't seen this URL
                                if title and len(title) > 3 and full_url not in [a['url'] for a in articles]:
                                    page_articles.append({
                                        'url': full_url,
                                        'title': title,
                                        'discovered': datetime.now().isoformat(),
                                        'page': page,
                                        'selector_used': url
                                    })
                        
                        if page_articles:
                            # Found articles with this URL pattern, use it
                            break
                            
                    except Exception as e:
                        print(f"Error with URL {url}: {e}")
                        continue
                
                if page_articles:
                    articles.extend(page_articles)
                    consecutive_empty_pages = 0
                    print(f"Page {page + 1}: Found {len(page_articles)} new articles (total: {len(articles)})")
                else:
                    consecutive_empty_pages += 1
                    print(f"Page {page + 1}: No articles found (empty page {consecutive_empty_pages}/3)")
                
                page += 1
                time.sleep(2)  # Be more respectful with multiple requests
                
            except Exception as e:
                print(f"Error fetching archive page {page}: {e}")
                consecutive_empty_pages += 1
                page += 1
                time.sleep(1)
        
        # Remove duplicates based on URL
        unique_articles = []
        seen_urls = set()
        for article in articles:
            if article['url'] not in seen_urls:
                unique_articles.append(article)
                seen_urls.add(article['url'])
        
        print(f"Discovered {len(unique_articles)} unique articles across {page} pages")
        return unique_articles
    
    def extract_article_content(self, url: str) -> Optional[Dict]:
        """Extract content from a single article"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article content (Substack-specific selectors)
            title_elem = soup.find('h1', class_='post-title') or soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else "Unknown Title"
            
            # Extract date
            date_elem = soup.find('time') or soup.find('span', class_='pencraft')
            date = date_elem.get('datetime') or date_elem.get_text() if date_elem else None
            
            # Extract content
            content_elem = soup.find('div', class_='available-content') or soup.find('div', class_='body')
            if not content_elem:
                # Try alternative selectors
                content_elem = soup.find('article') or soup.find('main')
            
            content = content_elem.get_text().strip() if content_elem else ""
            
            # Extract any structured data
            tags = []
            tag_elems = soup.find_all('a', href=re.compile(r'/tag/'))
            for tag in tag_elems:
                tags.append(tag.get_text().strip())
            
            return {
                'url': url,
                'title': title,
                'date': date,
                'content': content,
                'tags': tags,
                'html': str(soup),
                'extracted_at': datetime.now().isoformat(),
                'content_length': len(content),
                'word_count': len(content.split()) if content else 0
            }
            
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return None
    
    def generate_article_id(self, url: str, title: str) -> str:
        """Generate unique ID for article"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        title_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        title_slug = re.sub(r'\s+', '-', title_slug)[:50]
        return f"ttt-{url_hash}-{title_slug}"
    
    def save_article(self, article_data: Dict) -> str:
        """Save article to file and return filename"""
        article_id = self.generate_article_id(article_data['url'], article_data['title'])
        filename = f"{article_id}.json"
        filepath = os.path.join(self.articles_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(article_data, f, indent=2)
        
        return filename
    
    def mark_processed(self, article_id: str, research_priority: str = None):
        """Mark article as processed for research priorities"""
        processed_file = os.path.join(self.processed_dir, f"{article_id}_processed.json")
        processed_data = {
            'article_id': article_id,
            'processed_at': datetime.now().isoformat(),
            'research_priority': research_priority,
            'status': 'processed'
        }
        
        with open(processed_file, 'w') as f:
            json.dump(processed_data, f, indent=2)
    
    def is_processed(self, article_id: str) -> bool:
        """Check if article has been processed"""
        processed_file = os.path.join(self.processed_dir, f"{article_id}_processed.json")
        return os.path.exists(processed_file)
    
    def crawl_all(self, max_pages: int = 15) -> Dict:
        """Main crawl function"""
        print("Starting Trump Tyranny Tracker crawl...")
        
        # Start new crawl session
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_data = {
            'session_id': session_id,
            'started_at': datetime.now().isoformat(),
            'articles_discovered': 0,
            'articles_downloaded': 0,
            'errors': []
        }
        
        try:
            # Get all article links (try API first, fall back to HTML scraping)
            articles = self.get_article_links_api()
            session_data['articles_discovered'] = len(articles)
            
            # Download each article
            for i, article in enumerate(articles):
                print(f"Processing article {i+1}/{len(articles)}: {article['title'][:60]}...")
                
                # Generate article ID
                article_id = self.generate_article_id(article['url'], article['title'])
                
                # Skip if already downloaded
                article_file = os.path.join(self.articles_dir, f"{article_id}.json")
                if os.path.exists(article_file):
                    print(f"  Already downloaded: {article_id}")
                    continue
                
                # Extract content
                content = self.extract_article_content(article['url'])
                if content:
                    # Save article
                    filename = self.save_article(content)
                    session_data['articles_downloaded'] += 1
                    
                    # Update metadata
                    self.metadata['articles'][article_id] = {
                        'title': content['title'],
                        'url': content['url'],
                        'date': content['date'],
                        'filename': filename,
                        'downloaded_at': datetime.now().isoformat(),
                        'session_id': session_id
                    }
                    
                    print(f"  Downloaded: {filename}")
                else:
                    error_msg = f"Failed to extract content from {article['url']}"
                    session_data['errors'].append(error_msg)
                    print(f"  Error: {error_msg}")
                
                time.sleep(2)  # Be respectful
            
            # Update metadata
            session_data['completed_at'] = datetime.now().isoformat()
            self.metadata['crawl_sessions'].append(session_data)
            self.metadata['last_crawl'] = datetime.now().isoformat()
            self.metadata['total_articles'] = len(self.metadata['articles'])
            
            self.save_metadata()
            
            print(f"\nCrawl completed!")
            print(f"Articles discovered: {session_data['articles_discovered']}")
            print(f"Articles downloaded: {session_data['articles_downloaded']}")
            print(f"Total articles in collection: {self.metadata['total_articles']}")
            print(f"Errors: {len(session_data['errors'])}")
            
            return session_data
            
        except Exception as e:
            session_data['error'] = str(e)
            session_data['completed_at'] = datetime.now().isoformat()
            self.metadata['crawl_sessions'].append(session_data)
            self.save_metadata()
            raise
    
    def get_unprocessed_articles(self) -> List[Dict]:
        """Get list of articles that haven't been processed for research priorities"""
        unprocessed = []
        
        for article_id, article_data in self.metadata['articles'].items():
            if not self.is_processed(article_id):
                unprocessed.append({
                    'id': article_id,
                    'title': article_data['title'],
                    'url': article_data['url'],
                    'date': article_data['date'],
                    'filename': article_data['filename']
                })
        
        return unprocessed
    
    def get_stats(self) -> Dict:
        """Get crawler statistics"""
        unprocessed = self.get_unprocessed_articles()
        
        return {
            'total_articles': len(self.metadata['articles']),
            'unprocessed_articles': len(unprocessed),
            'processed_articles': len(self.metadata['articles']) - len(unprocessed),
            'crawl_sessions': len(self.metadata['crawl_sessions']),
            'last_crawl': self.metadata['last_crawl']
        }

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crawl Trump Tyranny Tracker Substack')
    parser.add_argument('--max-pages', type=int, default=15, help='Maximum pages to crawl')
    parser.add_argument('--stats', action='store_true', help='Show crawler statistics')
    parser.add_argument('--unprocessed', action='store_true', help='List unprocessed articles')
    
    args = parser.parse_args()
    
    crawler = TrumpTyrannyTrackerCrawler()
    
    if args.stats:
        stats = crawler.get_stats()
        print("Trump Tyranny Tracker Crawler Statistics:")
        print(f"  Total articles: {stats['total_articles']}")
        print(f"  Processed articles: {stats['processed_articles']}")
        print(f"  Unprocessed articles: {stats['unprocessed_articles']}")
        print(f"  Crawl sessions: {stats['crawl_sessions']}")
        print(f"  Last crawl: {stats['last_crawl']}")
    
    elif args.unprocessed:
        unprocessed = crawler.get_unprocessed_articles()
        print(f"Unprocessed articles ({len(unprocessed)}):")
        for article in unprocessed:
            print(f"  {article['id']}: {article['title']}")
    
    else:
        crawler.crawl_all(max_pages=args.max_pages)

if __name__ == "__main__":
    main()