#!/usr/bin/env python3
"""
Enhanced Trump Tyranny Tracker Crawler using Substack API Library
Complete coverage of all articles using the open source substack-api package
"""

import json
import os
import time
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional

# Import the substack-api library
try:
    from substack_api import SubstackAPI
    SUBSTACK_API_AVAILABLE = True
except ImportError:
    print("substack-api library not available, falling back to manual API calls")
    SUBSTACK_API_AVAILABLE = False

# Fallback to requests for manual API calls
import requests
from urllib.parse import urljoin

class EnhancedTrumpTyrannyTrackerCrawler:
    def __init__(self, base_dir: str = "ai-analysis/trump-tyranny-tracker"):
        self.base_url = "https://trumptyrannytracker.substack.com"
        self.publication_name = "trumptyrannytracker"  # For substack-api
        self.base_dir = base_dir
        self.articles_dir = os.path.join(base_dir, "articles")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.metadata_dir = os.path.join(base_dir, "metadata")
        
        # Create directories
        os.makedirs(self.articles_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # Initialize Substack API client if available
        if SUBSTACK_API_AVAILABLE:
            self.substack_api = SubstackAPI()
        else:
            self.substack_api = None
        
        # Fallback session for manual API calls
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Research Tool; Compatible with substack-api)',
            'Accept': 'application/json'
        })
        
        # Load existing metadata
        self.metadata_file = os.path.join(self.metadata_dir, "enhanced_crawl_metadata.json")
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
            "total_articles": 0,
            "method_used": None
        }
    
    def save_metadata(self):
        """Save crawl metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_all_articles_substack_api(self) -> List[Dict]:
        """Get all articles using the substack-api library"""
        if not self.substack_api:
            return []
        
        articles = []
        
        try:
            print("Fetching articles using substack-api library...")
            
            # Get publication information and posts
            publication = self.substack_api.get_publication(self.publication_name)
            
            if publication:
                print(f"Found publication: {publication.get('name', 'Unknown')}")
                
                # Get all posts from the publication
                posts = self.substack_api.get_publication_posts(self.publication_name, limit=500)
                
                print(f"Retrieved {len(posts)} posts from substack-api")
                
                for post in posts:
                    if isinstance(post, dict):
                        # Extract article information
                        post_id = post.get('id')
                        slug = post.get('slug', '')
                        title = post.get('title', 'Untitled')
                        date = post.get('post_date', post.get('created_at', ''))
                        subtitle = post.get('subtitle', '')
                        author = post.get('author', {}).get('name', '')
                        
                        if slug and title:
                            url = f"{self.base_url}/p/{slug}"
                            
                            articles.append({
                                'url': url,
                                'title': title,
                                'subtitle': subtitle,
                                'date': date,
                                'author': author,
                                'post_id': post_id,
                                'slug': slug,
                                'discovered': datetime.now().isoformat(),
                                'source': 'substack-api-library'
                            })
                
                print(f"Successfully processed {len(articles)} articles from substack-api library")
                return articles
            
        except Exception as e:
            print(f"Substack API library failed: {e}")
            print("Falling back to manual API calls...")
            return self.get_all_articles_manual_api()
    
    def get_all_articles_manual_api(self) -> List[Dict]:
        """Get all articles using manual API calls with comprehensive pagination"""
        articles = []
        
        try:
            print("Fetching articles using manual API calls...")
            
            # Try multiple API endpoints with pagination
            api_endpoints = [
                f"{self.base_url}/api/v1/archive",
                f"{self.base_url}/api/v1/posts", 
                f"{self.base_url}/api/v1/publication/posts"
            ]
            
            for endpoint in api_endpoints:
                try:
                    print(f"Trying API endpoint: {endpoint}")
                    
                    # Try with pagination parameters
                    page = 0
                    batch_size = 50
                    total_found = 0
                    
                    while page < 20:  # Max 20 pages to prevent infinite loops
                        # Try different pagination approaches
                        paginated_urls = [
                            f"{endpoint}?limit={batch_size}&offset={page * batch_size}",
                            f"{endpoint}?page={page}&per_page={batch_size}",
                            f"{endpoint}?skip={page * batch_size}&take={batch_size}",
                            endpoint if page == 0 else None  # Base URL for first page only
                        ]
                        
                        page_articles = []
                        
                        for paginated_url in paginated_urls:
                            if not paginated_url:
                                continue
                                
                            try:
                                print(f"  Fetching: {paginated_url}")
                                response = self.session.get(paginated_url)
                                
                                if response.status_code != 200:
                                    continue
                                
                                data = response.json()
                                
                                # Handle different JSON structures
                                posts = []
                                if isinstance(data, list):
                                    posts = data
                                elif isinstance(data, dict):
                                    posts = (data.get('posts') or 
                                           data.get('data') or 
                                           data.get('items') or 
                                           data.get('results') or 
                                           [])
                                
                                if not posts:
                                    continue
                                
                                print(f"    Found {len(posts)} posts")
                                
                                for post in posts:
                                    if isinstance(post, dict):
                                        post_id = post.get('id')
                                        slug = post.get('slug', '')
                                        title = post.get('title', 'Untitled')
                                        date = post.get('post_date', post.get('created_at', ''))
                                        
                                        if slug and title:
                                            url = f"{self.base_url}/p/{slug}"
                                            
                                            # Check if we already have this article
                                            if not any(a['url'] == url for a in articles):
                                                page_articles.append({
                                                    'url': url,
                                                    'title': title,
                                                    'date': date,
                                                    'post_id': post_id,
                                                    'slug': slug,
                                                    'discovered': datetime.now().isoformat(),
                                                    'source': f'manual-api-{endpoint.split("/")[-1]}'
                                                })
                                
                                if page_articles:
                                    # Found articles with this pagination approach
                                    break
                                    
                            except Exception as e:
                                print(f"    Error with {paginated_url}: {e}")
                                continue
                        
                        if page_articles:
                            articles.extend(page_articles)
                            total_found += len(page_articles)
                            print(f"  Page {page}: Added {len(page_articles)} articles (total: {total_found})")
                            page += 1
                            time.sleep(1)  # Be respectful
                        else:
                            print(f"  Page {page}: No new articles found, ending pagination")
                            break
                    
                    if articles:
                        print(f"Successfully retrieved {len(articles)} articles from {endpoint}")
                        return articles
                        
                except Exception as e:
                    print(f"Endpoint {endpoint} failed: {e}")
                    continue
            
            print("All manual API endpoints failed")
            return articles
            
        except Exception as e:
            print(f"Manual API method failed: {e}")
            return articles
    
    def generate_article_id(self, url: str, title: str) -> str:
        """Generate unique ID for article"""
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        title_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        title_slug = re.sub(r'\s+', '-', title_slug)[:50]
        return f"ttt-{url_hash}-{title_slug}"
    
    def extract_article_content(self, article_info: Dict) -> Optional[Dict]:
        """Extract full content from an article using multiple methods"""
        url = article_info['url']
        
        try:
            # Method 1: Try substack-api library if available
            if self.substack_api and article_info.get('slug'):
                try:
                    post_data = self.substack_api.get_post(article_info['slug'])
                    if post_data:
                        return {
                            'url': url,
                            'title': post_data.get('title', article_info['title']),
                            'date': post_data.get('post_date', article_info['date']),
                            'content': post_data.get('body_html', ''),
                            'subtitle': post_data.get('subtitle', ''),
                            'author': post_data.get('author', {}).get('name', ''),
                            'tags': post_data.get('tags', []),
                            'extracted_at': datetime.now().isoformat(),
                            'extraction_method': 'substack-api-library',
                            'word_count': len(post_data.get('body_html', '').split()) if post_data.get('body_html') else 0
                        }
                except Exception as e:
                    print(f"  Substack API extraction failed: {e}")
            
            # Method 2: Fall back to direct HTTP request
            print(f"  Extracting content from {url}")
            response = self.session.get(url)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article content
            title_elem = soup.find('h1', class_='post-title') or soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else article_info['title']
            
            date_elem = soup.find('time')
            date = date_elem.get('datetime') if date_elem else article_info['date']
            
            content_elem = soup.find('div', class_='available-content') or soup.find('div', class_='body')
            if not content_elem:
                content_elem = soup.find('article') or soup.find('main')
            
            content = content_elem.get_text().strip() if content_elem else ""
            
            return {
                'url': url,
                'title': title,
                'date': date,
                'content': content,
                'html': str(soup),
                'extracted_at': datetime.now().isoformat(),
                'extraction_method': 'html-scraping',
                'content_length': len(content),
                'word_count': len(content.split()) if content else 0
            }
            
        except Exception as e:
            print(f"  Error extracting content from {url}: {e}")
            return None
    
    def save_article(self, article_data: Dict) -> str:
        """Save article to file and return filename"""
        article_id = self.generate_article_id(article_data['url'], article_data['title'])
        filename = f"{article_id}.json"
        filepath = os.path.join(self.articles_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(article_data, f, indent=2)
        
        return filename
    
    def crawl_all_comprehensive(self) -> Dict:
        """Main comprehensive crawl function using the best available method"""
        print("=== Enhanced Trump Tyranny Tracker Comprehensive Crawl ===")
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_data = {
            'session_id': session_id,
            'started_at': datetime.now().isoformat(),
            'articles_discovered': 0,
            'articles_downloaded': 0,
            'method_used': None,
            'errors': []
        }
        
        try:
            # Method 1: Try substack-api library first (most comprehensive)
            if SUBSTACK_API_AVAILABLE:
                print("Method 1: Trying substack-api library...")
                articles = self.get_all_articles_substack_api()
                session_data['method_used'] = 'substack-api-library'
            else:
                articles = []
            
            # Method 2: Fall back to manual API calls if needed
            if not articles:
                print("Method 2: Trying manual API calls...")
                articles = self.get_all_articles_manual_api()
                session_data['method_used'] = 'manual-api'
            
            # Method 3: Ultimate fallback (not implemented here, would use HTML scraping)
            if not articles:
                print("Method 3: All API methods failed")
                session_data['method_used'] = 'failed'
                session_data['error'] = 'All discovery methods failed'
                return session_data
            
            session_data['articles_discovered'] = len(articles)
            print(f"\\n=== DISCOVERED {len(articles)} ARTICLES ===")
            
            # Download each article
            for i, article_info in enumerate(articles):
                print(f"\\nProcessing article {i+1}/{len(articles)}: {article_info['title'][:60]}...")
                
                article_id = self.generate_article_id(article_info['url'], article_info['title'])
                article_file = os.path.join(self.articles_dir, f"{article_id}.json")
                
                # Skip if already downloaded
                if os.path.exists(article_file):
                    print(f"  Already downloaded: {article_id}")
                    continue
                
                # Extract content
                content = self.extract_article_content(article_info)
                if content:
                    # Merge discovery info with content
                    content.update(article_info)
                    
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
                        'session_id': session_id,
                        'method': session_data['method_used']
                    }
                    
                    print(f"  Downloaded: {filename}")
                else:
                    error_msg = f"Failed to extract content from {article_info['url']}"
                    session_data['errors'].append(error_msg)
                    print(f"  Error: {error_msg}")
                
                # Be respectful to the server
                time.sleep(1.5)
            
            # Update metadata
            session_data['completed_at'] = datetime.now().isoformat()
            self.metadata['crawl_sessions'].append(session_data)
            self.metadata['last_crawl'] = datetime.now().isoformat()
            self.metadata['total_articles'] = len(self.metadata['articles'])
            self.metadata['method_used'] = session_data['method_used']
            
            self.save_metadata()
            
            print(f"\\n=== CRAWL COMPLETED ===")
            print(f"Method used: {session_data['method_used']}")
            print(f"Articles discovered: {session_data['articles_discovered']}")
            print(f"Articles downloaded: {session_data['articles_downloaded']}")
            print(f"Total articles in collection: {self.metadata['total_articles']}")
            print(f"Errors: {len(session_data['errors'])}")
            
            if session_data['errors']:
                print("\\nErrors encountered:")
                for error in session_data['errors']:
                    print(f"  - {error}")
            
            return session_data
            
        except Exception as e:
            session_data['error'] = str(e)
            session_data['completed_at'] = datetime.now().isoformat()
            self.metadata['crawl_sessions'].append(session_data)
            self.save_metadata()
            print(f"\\nCrawl failed with error: {e}")
            return session_data
    
    def get_stats(self) -> Dict:
        """Get comprehensive crawler statistics"""
        return {
            'total_articles': len(self.metadata['articles']),
            'crawl_sessions': len(self.metadata['crawl_sessions']),
            'last_crawl': self.metadata['last_crawl'],
            'method_used': self.metadata.get('method_used', 'unknown'),
            'substack_api_available': SUBSTACK_API_AVAILABLE
        }

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Trump Tyranny Tracker Crawler')
    parser.add_argument('--stats', action='store_true', help='Show crawler statistics')
    
    args = parser.parse_args()
    
    crawler = EnhancedTrumpTyrannyTrackerCrawler()
    
    if args.stats:
        stats = crawler.get_stats()
        print("Enhanced Trump Tyranny Tracker Crawler Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        crawler.crawl_all_comprehensive()

if __name__ == "__main__":
    main()