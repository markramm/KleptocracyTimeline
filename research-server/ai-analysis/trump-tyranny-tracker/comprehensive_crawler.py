#!/usr/bin/env python3
"""
Comprehensive Trump Tyranny Tracker Crawler - Get ALL 200+ Articles
Multiple strategies to achieve complete coverage of all systematic corruption documentation
"""

import requests
import json
import os
import time
import hashlib
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import concurrent.futures
from threading import Lock

class ComprehensiveTrumpTyrannyTrackerCrawler:
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
        
        # Enhanced session with better headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        self.articles_lock = Lock()
        self.discovered_articles = {}  # Thread-safe article storage
        
        # Load existing metadata
        self.metadata_file = os.path.join(self.metadata_dir, "comprehensive_crawl_metadata.json")
        self.metadata = self.load_metadata()
    
    def load_metadata(self) -> Dict:
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            "articles": {},
            "crawl_sessions": [],
            "last_crawl": None,
            "total_articles": 0,
            "strategies_used": []
        }
    
    def save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def generate_article_id(self, url: str, title: str) -> str:
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        title_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        title_slug = re.sub(r'\s+', '-', title_slug)[:50]
        return f"ttt-{url_hash}-{title_slug}"
    
    def add_discovered_article(self, article_info: Dict):
        """Thread-safe article addition"""
        with self.articles_lock:
            url = article_info['url']
            if url not in self.discovered_articles:
                self.discovered_articles[url] = article_info
    
    def strategy_1_advanced_api_crawling(self) -> List[Dict]:
        """Strategy 1: Advanced API crawling with multiple endpoints and parameters"""
        print("Strategy 1: Advanced API crawling...")
        articles = []
        
        # Multiple API endpoint variations
        api_endpoints = [
            f"{self.base_url}/api/v1/archive",
            f"{self.base_url}/api/v1/posts",
            f"{self.base_url}/api/v1/publication/posts",
            f"{self.base_url}/api/v1/feeds/all",
            f"{self.base_url}/api/v1/posts/published"
        ]
        
        for endpoint in api_endpoints:
            try:
                print(f"  Trying endpoint: {endpoint}")
                
                # Try different pagination approaches
                for page in range(50):  # Try up to 50 pages
                    params_sets = [
                        {'limit': 100, 'offset': page * 100},
                        {'limit': 50, 'offset': page * 50},
                        {'per_page': 100, 'page': page},
                        {'take': 100, 'skip': page * 100},
                        {'count': 100, 'start': page * 100}
                    ]
                    
                    page_found = False
                    
                    for params in params_sets:
                        try:
                            response = self.session.get(endpoint, params=params)
                            if response.status_code == 200:
                                data = response.json()
                                
                                posts = []
                                if isinstance(data, list):
                                    posts = data
                                elif isinstance(data, dict):
                                    posts = (data.get('posts') or data.get('data') or 
                                           data.get('items') or data.get('results') or
                                           data.get('publications') or [])
                                
                                if posts:
                                    print(f"    Page {page}: Found {len(posts)} posts")
                                    
                                    for post in posts:
                                        if isinstance(post, dict):
                                            slug = post.get('slug', '')
                                            title = post.get('title', 'Untitled')
                                            if slug and title:
                                                self.add_discovered_article({
                                                    'url': f"{self.base_url}/p/{slug}",
                                                    'title': title,
                                                    'date': post.get('post_date', post.get('created_at', '')),
                                                    'post_id': post.get('id'),
                                                    'slug': slug,
                                                    'strategy': 'api-advanced',
                                                    'endpoint': endpoint,
                                                    'params': str(params)
                                                })
                                    
                                    page_found = True
                                    break
                        except:
                            continue
                    
                    if not page_found:
                        break
                        
                    time.sleep(1)
                
                print(f"  {endpoint}: Found {len(self.discovered_articles)} total articles so far")
                
            except Exception as e:
                print(f"  Error with {endpoint}: {e}")
                continue
        
        return list(self.discovered_articles.values())
    
    def strategy_2_date_range_crawling(self) -> List[Dict]:
        """Strategy 2: Date-based archive crawling"""
        print("Strategy 2: Date-range crawling...")
        
        # Trump's second term started January 20, 2025
        start_date = datetime(2025, 1, 20)
        end_date = datetime.now()
        
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Try different date-based archive URLs
            date_urls = [
                f"{self.base_url}/archive/{current_date.year}/{current_date.month}",
                f"{self.base_url}/archive?date={date_str}",
                f"{self.base_url}/archive?year={current_date.year}&month={current_date.month}",
                f"{self.base_url}/api/v1/archive?date={date_str}",
                f"{self.base_url}/api/v1/posts?date_gte={date_str}&date_lte={date_str}"
            ]
            
            for url in date_urls:
                try:
                    response = self.session.get(url)
                    if response.status_code == 200:
                        # Try JSON first
                        try:
                            data = response.json()
                            posts = data if isinstance(data, list) else data.get('posts', [])
                            for post in posts:
                                if isinstance(post, dict):
                                    slug = post.get('slug', '')
                                    title = post.get('title', '')
                                    if slug and title:
                                        self.add_discovered_article({
                                            'url': f"{self.base_url}/p/{slug}",
                                            'title': title,
                                            'date': post.get('post_date', date_str),
                                            'strategy': 'date-range',
                                            'source_url': url
                                        })
                        except:
                            # Try HTML parsing
                            soup = BeautifulSoup(response.text, 'html.parser')
                            links = soup.find_all('a', href=re.compile(r'/p/'))
                            for link in links:
                                href = link.get('href')
                                title = link.get_text().strip()
                                if href and '/p/' in href and title:
                                    full_url = urljoin(self.base_url, href)
                                    self.add_discovered_article({
                                        'url': full_url,
                                        'title': title,
                                        'date': date_str,
                                        'strategy': 'date-range-html',
                                        'source_url': url
                                    })
                except:
                    continue
            
            current_date += timedelta(days=1)
            if current_date.day == 1:  # Progress update monthly
                print(f"  Processed through {current_date.strftime('%Y-%m')}: {len(self.discovered_articles)} articles")
        
        return list(self.discovered_articles.values())
    
    def strategy_3_systematic_day_search(self) -> List[Dict]:
        """Strategy 3: Systematic search for specific day numbers"""
        print("Strategy 3: Systematic day number search...")
        
        # Search for each day from 1 to 231
        for day in range(1, 232):
            search_terms = [
                f"Day {day}",
                f"Day {day:03d}",  # Day 001 format
                f"Trump Tyranny Tracker: Day {day}",
                f"Trump Tyranny Tracker Day {day}"
            ]
            
            for term in search_terms:
                # Try search API endpoints
                search_urls = [
                    f"{self.base_url}/api/v1/search?q={term}",
                    f"{self.base_url}/search?q={term}",
                    f"{self.base_url}/archive?search={term}"
                ]
                
                for search_url in search_urls:
                    try:
                        response = self.session.get(search_url)
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                results = data if isinstance(data, list) else data.get('results', data.get('posts', []))
                                
                                for result in results:
                                    if isinstance(result, dict):
                                        slug = result.get('slug', '')
                                        title = result.get('title', '')
                                        if slug and title and str(day) in title:
                                            self.add_discovered_article({
                                                'url': f"{self.base_url}/p/{slug}",
                                                'title': title,
                                                'date': result.get('post_date', ''),
                                                'day_number': day,
                                                'strategy': 'day-search',
                                                'search_term': term
                                            })
                            except:
                                # HTML fallback
                                soup = BeautifulSoup(response.text, 'html.parser')
                                links = soup.find_all('a', href=re.compile(r'/p/'), string=re.compile(f'Day {day}', re.I))
                                for link in links:
                                    href = link.get('href')
                                    title = link.get_text().strip()
                                    if href and title:
                                        full_url = urljoin(self.base_url, href)
                                        self.add_discovered_article({
                                            'url': full_url,
                                            'title': title,
                                            'day_number': day,
                                            'strategy': 'day-search-html',
                                            'search_term': term
                                        })
                        
                        time.sleep(0.5)  # Be respectful
                        
                    except:
                        continue
            
            if day % 10 == 0:  # Progress update every 10 days
                print(f"  Searched through Day {day}: {len(self.discovered_articles)} articles")
        
        return list(self.discovered_articles.values())
    
    def strategy_4_sitemap_crawling(self) -> List[Dict]:
        """Strategy 4: Sitemap and RSS feed crawling"""
        print("Strategy 4: Sitemap and RSS crawling...")
        
        feed_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/feed",
            f"{self.base_url}/rss",
            f"{self.base_url}/feed.xml",
            f"{self.base_url}/atom.xml"
        ]
        
        for feed_url in feed_urls:
            try:
                response = self.session.get(feed_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'xml')
                    
                    # Parse sitemap
                    urls = soup.find_all(['url', 'loc'])
                    for url_elem in urls:
                        loc = url_elem.find('loc') if url_elem.name == 'url' else url_elem
                        if loc and '/p/' in loc.get_text():
                            url = loc.get_text().strip()
                            self.add_discovered_article({
                                'url': url,
                                'title': 'From Sitemap',  # Will be updated when content is fetched
                                'strategy': 'sitemap',
                                'source_feed': feed_url
                            })
                    
                    # Parse RSS/Atom
                    items = soup.find_all(['item', 'entry'])
                    for item in items:
                        title_elem = item.find(['title'])
                        link_elem = item.find(['link', 'guid'])
                        
                        if title_elem and link_elem:
                            title = title_elem.get_text().strip()
                            link = link_elem.get_text().strip() if link_elem.get_text() else link_elem.get('href', '')
                            
                            if '/p/' in link:
                                self.add_discovered_article({
                                    'url': link,
                                    'title': title,
                                    'strategy': 'rss-feed',
                                    'source_feed': feed_url
                                })
                    
                    print(f"  {feed_url}: Found articles, total now {len(self.discovered_articles)}")
                    
            except Exception as e:
                print(f"  Error with {feed_url}: {e}")
                continue
        
        return list(self.discovered_articles.values())
    
    def extract_article_content(self, article_info: Dict) -> Optional[Dict]:
        """Extract full content from an article"""
        url = article_info['url']
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article content
            title_elem = soup.find('h1', class_='post-title') or soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else article_info['title']
            
            date_elem = soup.find('time')
            date = date_elem.get('datetime') if date_elem else article_info.get('date', '')
            
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
                'strategy': article_info.get('strategy', 'unknown'),
                'extracted_at': datetime.now().isoformat(),
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
    
    def comprehensive_crawl(self) -> Dict:
        """Execute all strategies to get maximum coverage"""
        print("=== COMPREHENSIVE TRUMP TYRANNY TRACKER CRAWL ===")
        print("Target: 200+ articles from 231 days of systematic corruption tracking\\n")
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_data = {
            'session_id': session_id,
            'started_at': datetime.now().isoformat(),
            'articles_discovered': 0,
            'articles_downloaded': 0,
            'strategies_used': [],
            'errors': []
        }
        
        try:
            # Execute all strategies in parallel
            strategies = [
                self.strategy_1_advanced_api_crawling,
                self.strategy_2_date_range_crawling,
                self.strategy_3_systematic_day_search,
                self.strategy_4_sitemap_crawling
            ]
            
            # Run strategies concurrently for faster execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                future_to_strategy = {executor.submit(strategy): strategy.__name__ for strategy in strategies}
                
                for future in concurrent.futures.as_completed(future_to_strategy):
                    strategy_name = future_to_strategy[future]
                    try:
                        articles = future.result()
                        session_data['strategies_used'].append(strategy_name)
                        print(f"✅ {strategy_name}: Completed")
                    except Exception as e:
                        error_msg = f"{strategy_name} failed: {e}"
                        session_data['errors'].append(error_msg)
                        print(f"❌ {strategy_name}: {error_msg}")
            
            # Deduplicate and finalize article list
            unique_articles = list(self.discovered_articles.values())
            session_data['articles_discovered'] = len(unique_articles)
            
            print(f"\\n=== DISCOVERY COMPLETE ===")
            print(f"Total unique articles discovered: {len(unique_articles)}")
            print(f"Strategies used: {', '.join(session_data['strategies_used'])}")
            
            # Download all discovered articles
            print(f"\\n=== DOWNLOADING ARTICLES ===")
            for i, article_info in enumerate(unique_articles):
                print(f"Processing {i+1}/{len(unique_articles)}: {article_info['title'][:60]}...")
                
                article_id = self.generate_article_id(article_info['url'], article_info['title'])
                article_file = os.path.join(self.articles_dir, f"{article_id}.json")
                
                if os.path.exists(article_file):
                    print(f"  Already downloaded: {article_id}")
                    continue
                
                content = self.extract_article_content(article_info)
                if content:
                    content.update(article_info)  # Merge discovery info
                    filename = self.save_article(content)
                    session_data['articles_downloaded'] += 1
                    
                    self.metadata['articles'][article_id] = {
                        'title': content['title'],
                        'url': content['url'],
                        'date': content['date'],
                        'filename': filename,
                        'downloaded_at': datetime.now().isoformat(),
                        'session_id': session_id,
                        'strategy': content['strategy']
                    }
                    
                    print(f"  Downloaded: {filename}")
                else:
                    error_msg = f"Failed to extract content from {article_info['url']}"
                    session_data['errors'].append(error_msg)
                
                time.sleep(1)  # Be respectful
            
            # Update metadata
            session_data['completed_at'] = datetime.now().isoformat()
            self.metadata['crawl_sessions'].append(session_data)
            self.metadata['last_crawl'] = datetime.now().isoformat()
            self.metadata['total_articles'] = len(self.metadata['articles'])
            self.metadata['strategies_used'] = session_data['strategies_used']
            
            self.save_metadata()
            
            print(f"\\n=== COMPREHENSIVE CRAWL COMPLETED ===")
            print(f"Articles discovered: {session_data['articles_discovered']}")
            print(f"Articles downloaded: {session_data['articles_downloaded']}")
            print(f"Total articles in collection: {self.metadata['total_articles']}")
            print(f"Strategies used: {', '.join(session_data['strategies_used'])}")
            print(f"Errors: {len(session_data['errors'])}")
            
            # Coverage analysis
            day_numbers = []
            for article_id, article_data in self.metadata['articles'].items():
                title = article_data['title']
                day_match = re.search(r'Day (\\d+)', title)
                if day_match:
                    day_numbers.append(int(day_match.group(1)))
            
            if day_numbers:
                day_numbers.sort()
                print(f"\\nCoverage Analysis:")
                print(f"Days covered: {min(day_numbers)}-{max(day_numbers)}")
                print(f"Days with articles: {len(set(day_numbers))} out of 231 target days")
                print(f"Coverage percentage: {len(set(day_numbers))/231*100:.1f}%")
            
            return session_data
            
        except Exception as e:
            session_data['error'] = str(e)
            session_data['completed_at'] = datetime.now().isoformat()
            self.metadata['crawl_sessions'].append(session_data)
            self.save_metadata()
            print(f"\\nCrawl failed with error: {e}")
            return session_data

def main():
    crawler = ComprehensiveTrumpTyrannyTrackerCrawler()
    crawler.comprehensive_crawl()

if __name__ == "__main__":
    main()