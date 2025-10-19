#!/usr/bin/env python3
"""
Complete Trump Tyranny Tracker Crawler - GET ALL 269 ARTICLES!
Uses the correct substack-api library to get complete coverage
"""

import json
import os
import time
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional

# Import the working substack-api functions
from substack_api.newsletter import get_newsletter_post_metadata, get_post_contents
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class CompleteTrumpTyrannyTrackerCrawler:
    def __init__(self, base_dir: str = "ai-analysis/trump-tyranny-tracker"):
        self.base_url = "https://trumptyrannytracker.substack.com"
        self.newsletter_name = "trumptyrannytracker"
        self.base_dir = base_dir
        self.articles_dir = os.path.join(base_dir, "articles")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.metadata_dir = os.path.join(base_dir, "metadata")
        
        # Create directories
        os.makedirs(self.articles_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # Session for fallback content extraction
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Load existing metadata
        self.metadata_file = os.path.join(self.metadata_dir, "complete_crawl_metadata.json")
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
            "api_method": "substack-api-library"
        }
    
    def save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def generate_article_id(self, url: str, title: str) -> str:
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        title_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
        title_slug = re.sub(r'\s+', '-', title_slug)[:50]
        return f"ttt-{url_hash}-{title_slug}"
    
    def get_all_posts_metadata(self) -> List[Dict]:
        """Get all post metadata using the working substack-api"""
        print("Fetching all posts using substack-api library...")
        
        try:
            posts = get_newsletter_post_metadata(self.newsletter_name)
            print(f"✅ Retrieved {len(posts)} posts from substack-api!")
            
            # Process and clean up the metadata
            processed_posts = []
            for post in posts:
                if isinstance(post, dict):
                    # Extract key information
                    title = post.get('title', 'Untitled')
                    slug = post.get('slug', '')
                    post_id = post.get('id', '')
                    date = post.get('date', post.get('post_date', ''))
                    
                    if slug and title:
                        processed_posts.append({
                            'url': f"{self.base_url}/p/{slug}",
                            'title': title,
                            'slug': slug,
                            'post_id': post_id,
                            'date': date,
                            'raw_metadata': post,
                            'discovered_at': datetime.now().isoformat(),
                            'source': 'substack-api-metadata'
                        })
            
            print(f"✅ Processed {len(processed_posts)} valid posts")
            return processed_posts
            
        except Exception as e:
            print(f"❌ Error getting posts metadata: {e}")
            return []
    
    def extract_article_content(self, post_info: Dict) -> Optional[Dict]:
        """Extract full content from a post using multiple methods"""
        url = post_info['url']
        slug = post_info['slug']
        
        try:
            print(f"  Extracting content from: {slug}")
            
            # Method 1: Try substack-api get_post_contents
            try:
                content_data = get_post_contents(url)
                if content_data and content_data.get('content'):
                    return {
                        'url': url,
                        'title': content_data.get('title', post_info['title']),
                        'date': content_data.get('date', post_info['date']),
                        'content': content_data['content'],
                        'subtitle': content_data.get('subtitle', ''),
                        'author': content_data.get('author', ''),
                        'extraction_method': 'substack-api-content',
                        'extracted_at': datetime.now().isoformat(),
                        'word_count': len(content_data['content'].split()) if content_data['content'] else 0
                    }
            except Exception as e:
                print(f"    substack-api content extraction failed: {e}")
            
            # Method 2: Fall back to direct HTTP scraping
            print(f"    Falling back to HTTP scraping...")
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content
            title_elem = soup.find('h1', class_='post-title') or soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else post_info['title']
            
            date_elem = soup.find('time')
            date = date_elem.get('datetime') if date_elem else post_info['date']
            
            # Try multiple content selectors
            content_selectors = [
                'div.available-content',
                'div.body',
                'div.post-content',
                'article',
                'main'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text().strip()
                    break
            
            if not content:
                # Last resort - get all paragraph text
                paragraphs = soup.find_all('p')
                content = "\\n\\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            return {
                'url': url,
                'title': title,
                'date': date,
                'content': content,
                'html': str(soup),
                'extraction_method': 'http-scraping',
                'extracted_at': datetime.now().isoformat(),
                'content_length': len(content),
                'word_count': len(content.split()) if content else 0
            }
            
        except Exception as e:
            print(f"    ❌ Error extracting content from {url}: {e}")
            return None
    
    def save_article(self, article_data: Dict, post_info: Dict) -> str:
        """Save article with both content and metadata"""
        # Merge content with original post info
        complete_data = {**post_info, **article_data}
        
        article_id = self.generate_article_id(article_data['url'], article_data['title'])
        filename = f"{article_id}.json"
        filepath = os.path.join(self.articles_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(complete_data, f, indent=2)
        
        return filename
    
    def analyze_coverage(self) -> Dict:
        """Analyze day coverage in downloaded articles"""
        day_numbers = []
        day_ranges = []
        
        for article_id, article_data in self.metadata['articles'].items():
            title = article_data['title']
            
            # Extract day numbers
            day_match = re.search(r'Day (\\d+)', title)
            if day_match:
                day_numbers.append(int(day_match.group(1)))
            
            # Extract day ranges
            range_match = re.search(r'Day (\\d+)-(\\d+)', title)
            if range_match:
                start_day = int(range_match.group(1))
                end_day = int(range_match.group(2))
                day_ranges.append((start_day, end_day))
        
        if day_numbers:
            day_numbers.sort()
            unique_days = set(day_numbers)
            
            # Add days from ranges
            for start_day, end_day in day_ranges:
                unique_days.update(range(start_day, end_day + 1))
            
            return {
                'total_day_articles': len(day_numbers),
                'unique_days_covered': len(unique_days),
                'day_range': f"{min(day_numbers)}-{max(day_numbers)}",
                'coverage_percentage': len(unique_days) / 231 * 100,
                'missing_days': 231 - len(unique_days),
                'days_covered': sorted(unique_days)
            }
        
        return {'total_day_articles': 0, 'unique_days_covered': 0}
    
    def complete_crawl(self) -> Dict:
        """Execute complete crawl to get all 269+ articles"""
        print("=== COMPLETE TRUMP TYRANNY TRACKER CRAWL ===")
        print("Target: ALL articles using working substack-api\\n")
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_data = {
            'session_id': session_id,
            'started_at': datetime.now().isoformat(),
            'method': 'substack-api-complete',
            'articles_discovered': 0,
            'articles_downloaded': 0,
            'articles_skipped': 0,
            'errors': []
        }
        
        try:
            # Get all posts metadata
            posts = self.get_all_posts_metadata()
            session_data['articles_discovered'] = len(posts)
            
            if not posts:
                session_data['error'] = 'No posts discovered'
                return session_data
            
            print(f"\\n=== DOWNLOADING {len(posts)} ARTICLES ===\\n")
            
            # Download each article
            for i, post_info in enumerate(posts):
                print(f"[{i+1}/{len(posts)}] {post_info['title'][:70]}...")
                
                article_id = self.generate_article_id(post_info['url'], post_info['title'])
                article_file = os.path.join(self.articles_dir, f"{article_id}.json")
                
                # Skip if already downloaded
                if os.path.exists(article_file):
                    print(f"  ⏭️  Already exists: {article_id}")
                    session_data['articles_skipped'] += 1
                    continue
                
                # Extract content
                content = self.extract_article_content(post_info)
                if content:
                    # Save article with complete data
                    filename = self.save_article(content, post_info)
                    session_data['articles_downloaded'] += 1
                    
                    # Update metadata
                    self.metadata['articles'][article_id] = {
                        'title': content['title'],
                        'url': content['url'],
                        'date': content['date'],
                        'filename': filename,
                        'downloaded_at': datetime.now().isoformat(),
                        'session_id': session_id,
                        'extraction_method': content['extraction_method'],
                        'word_count': content.get('word_count', 0)
                    }
                    
                    print(f"  ✅ Downloaded: {filename} ({content.get('word_count', 0)} words)")
                else:
                    error_msg = f"Failed to extract content from {post_info['url']}"
                    session_data['errors'].append(error_msg)
                    print(f"  ❌ Failed: {error_msg}")
                
                # Be respectful to the server
                time.sleep(1.5)
                
                # Progress updates every 10 articles
                if (i + 1) % 10 == 0:
                    print(f"\\n--- Progress: {i+1}/{len(posts)} articles processed ---")
                    print(f"Downloaded: {session_data['articles_downloaded']}, Skipped: {session_data['articles_skipped']}, Errors: {len(session_data['errors'])}\\n")
            
            # Final metadata update
            session_data['completed_at'] = datetime.now().isoformat()
            self.metadata['crawl_sessions'].append(session_data)
            self.metadata['last_crawl'] = datetime.now().isoformat()
            self.metadata['total_articles'] = len(self.metadata['articles'])
            self.metadata['api_method'] = 'substack-api-complete'
            
            self.save_metadata()
            
            # Analyze coverage
            coverage = self.analyze_coverage()
            
            print(f"\\n=== COMPLETE CRAWL FINISHED ===")
            print(f"📊 RESULTS:")
            print(f"  Articles discovered: {session_data['articles_discovered']}")
            print(f"  Articles downloaded: {session_data['articles_downloaded']}")
            print(f"  Articles skipped (already had): {session_data['articles_skipped']}")
            print(f"  Total in collection: {self.metadata['total_articles']}")
            print(f"  Errors: {len(session_data['errors'])}")
            
            print(f"\\n📈 COVERAGE ANALYSIS:")
            if coverage['total_day_articles'] > 0:
                print(f"  Days with articles: {coverage['unique_days_covered']} out of 231 target days")
                print(f"  Coverage percentage: {coverage['coverage_percentage']:.1f}%")
                print(f"  Day range: {coverage['day_range']}")
                print(f"  Missing days: {coverage['missing_days']}")
            else:
                print(f"  Coverage analysis not available (no day-numbered articles found)")
            
            print(f"\\n🎯 SUCCESS METRICS:")
            original_articles = 45  # What we had before
            improvement = session_data['articles_discovered'] - original_articles
            print(f"  Before: {original_articles} articles")
            print(f"  After: {session_data['articles_discovered']} articles")
            print(f"  Improvement: +{improvement} articles ({improvement/original_articles*100:.0f}% increase)")
            
            if session_data['errors']:
                print(f"\\n⚠️  ERRORS ENCOUNTERED:")
                for error in session_data['errors'][:10]:  # Show first 10 errors
                    print(f"  - {error}")
                if len(session_data['errors']) > 10:
                    print(f"  ... and {len(session_data['errors']) - 10} more errors")
            
            return session_data
            
        except Exception as e:
            session_data['error'] = str(e)
            session_data['completed_at'] = datetime.now().isoformat()
            self.metadata['crawl_sessions'].append(session_data)
            self.save_metadata()
            print(f"\\n❌ CRAWL FAILED: {e}")
            return session_data
    
    def get_stats(self) -> Dict:
        """Get comprehensive statistics"""
        coverage = self.analyze_coverage()
        return {
            'total_articles': len(self.metadata['articles']),
            'crawl_sessions': len(self.metadata['crawl_sessions']),
            'last_crawl': self.metadata['last_crawl'],
            'api_method': self.metadata.get('api_method', 'unknown'),
            'coverage_analysis': coverage
        }

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Complete Trump Tyranny Tracker Crawler')
    parser.add_argument('--stats', action='store_true', help='Show crawler statistics')
    
    args = parser.parse_args()
    
    crawler = CompleteTrumpTyrannyTrackerCrawler()
    
    if args.stats:
        stats = crawler.get_stats()
        print("Complete Trump Tyranny Tracker Crawler Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        crawler.complete_crawl()

if __name__ == "__main__":
    main()