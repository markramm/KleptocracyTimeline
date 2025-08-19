#!/usr/bin/env python3
"""
Extract citations and URLs from PDF research documents.
Creates a database of known good sources for timeline events.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set
import sys

# Add PyPDF2 support if available
try:
    import PyPDF2
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False
    print("Warning: PyPDF2 not installed. Install with: pip install PyPDF2")

def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text using regex patterns."""
    # Comprehensive URL pattern
    url_patterns = [
        r'https?://[^\s<>"{}|\\^`\[\]]+',
        r'www\.[^\s<>"{}|\\^`\[\]]+',
        r'(?:https?://)?(?:www\.)?[\w\-]+\.(?:com|org|net|edu|gov|mil|int|co\.uk)[^\s<>"{}|\\^`\[\]]*'
    ]
    
    urls = set()
    for pattern in url_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        urls.update(matches)
    
    # Clean up URLs
    cleaned_urls = []
    for url in urls:
        # Remove trailing punctuation
        url = re.sub(r'[.,;:!?\'\")]+$', '', url)
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')) and 'www.' in url:
            url = 'https://' + url
        cleaned_urls.append(url)
    
    return list(set(cleaned_urls))

def extract_citations_from_text(text: str) -> List[Dict[str, str]]:
    """Extract formatted citations from text."""
    citations = []
    
    # Pattern for citations like: "Title" (Source, Date)
    citation_patterns = [
        r'"([^"]+)"\s*\(([^,]+),\s*([^)]+)\)',  # "Title" (Source, Date)
        r'([^.]+)\.\s*([A-Z][^.]+)\.\s*(\d{4})',  # Title. Source. Year
        r'\[(\d+)\]\s*([^.]+)\.\s*([^.]+)',  # [1] Author. Title
    ]
    
    for pattern in citation_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if len(match) >= 2:
                citations.append({
                    'text': ' '.join(match),
                    'type': 'citation'
                })
    
    return citations

def extract_from_pdf(pdf_path: Path) -> Dict[str, any]:
    """Extract URLs and citations from a PDF file."""
    if not HAS_PYPDF:
        return {'error': 'PyPDF2 not installed', 'urls': [], 'citations': []}
    
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
            
            urls = extract_urls_from_text(text)
            citations = extract_citations_from_text(text)
            
            return {
                'file': pdf_path.name,
                'urls': urls,
                'citations': citations,
                'page_count': len(pdf_reader.pages)
            }
    except Exception as e:
        return {'error': str(e), 'file': pdf_path.name, 'urls': [], 'citations': []}

def extract_from_text_file(file_path: Path) -> Dict[str, any]:
    """Extract URLs and citations from text/markdown files."""
    try:
        text = file_path.read_text(encoding='utf-8')
        urls = extract_urls_from_text(text)
        citations = extract_citations_from_text(text)
        
        return {
            'file': file_path.name,
            'urls': urls,
            'citations': citations
        }
    except Exception as e:
        return {'error': str(e), 'file': file_path.name, 'urls': [], 'citations': []}

def categorize_urls(urls: List[str]) -> Dict[str, List[str]]:
    """Categorize URLs by domain type."""
    categories = {
        'government': [],
        'news': [],
        'academic': [],
        'legal': [],
        'social': [],
        'other': []
    }
    
    gov_domains = ['.gov', 'congress.', 'senate.', 'house.', 'whitehouse']
    news_domains = ['nytimes', 'washingtonpost', 'cnn.', 'npr.', 'bbc.', 'reuters', 
                    'apnews', 'bloomberg', 'wsj.', 'guardian', 'nbcnews', 'foxnews',
                    'politico', 'axios', 'thehill', 'newsweek', 'cbsnews', 'abcnews']
    academic_domains = ['.edu', 'scholar.', 'jstor.', 'arxiv.', 'pubmed', 'doi.org']
    legal_domains = ['justia', 'supremecourt', 'scotusblog', 'courtlistener', 'law.']
    social_domains = ['twitter.com', 'x.com', 'facebook.', 'instagram.', 'youtube.']
    
    for url in urls:
        url_lower = url.lower()
        categorized = False
        
        for domain in gov_domains:
            if domain in url_lower:
                categories['government'].append(url)
                categorized = True
                break
        
        if not categorized:
            for domain in news_domains:
                if domain in url_lower:
                    categories['news'].append(url)
                    categorized = True
                    break
        
        if not categorized:
            for domain in academic_domains:
                if domain in url_lower:
                    categories['academic'].append(url)
                    categorized = True
                    break
        
        if not categorized:
            for domain in legal_domains:
                if domain in url_lower:
                    categories['legal'].append(url)
                    categorized = True
                    break
        
        if not categorized:
            for domain in social_domains:
                if domain in url_lower:
                    categories['social'].append(url)
                    categorized = True
                    break
        
        if not categorized:
            categories['other'].append(url)
    
    return categories

def main():
    """Main function to extract citations from research documents."""
    # Look for research documents in multiple locations
    possible_paths = [
        Path.home() / "democracy" / "injest",
        Path.home() / "democracy" / "source_documents",
        Path.home() / "kleptocracy-timeline" / "research",
        Path.cwd() / "research"
    ]
    
    all_urls = set()
    all_citations = []
    processed_files = []
    
    for base_path in possible_paths:
        if not base_path.exists():
            continue
        
        print(f"\nScanning {base_path}...")
        
        # Process PDFs
        if HAS_PYPDF:
            for pdf_file in base_path.glob("**/*.pdf"):
                print(f"  Processing {pdf_file.name}...")
                result = extract_from_pdf(pdf_file)
                if 'error' not in result:
                    all_urls.update(result['urls'])
                    all_citations.extend(result['citations'])
                    processed_files.append(result)
        
        # Process text files
        for pattern in ["**/*.txt", "**/*.md"]:
            for text_file in base_path.glob(pattern):
                print(f"  Processing {text_file.name}...")
                result = extract_from_text_file(text_file)
                if 'error' not in result:
                    all_urls.update(result['urls'])
                    all_citations.extend(result['citations'])
                    processed_files.append(result)
    
    # Categorize URLs
    categorized = categorize_urls(list(all_urls))
    
    # Create output database
    output = {
        'extracted_at': Path.cwd().as_posix(),
        'total_files': len(processed_files),
        'total_urls': len(all_urls),
        'total_citations': len(all_citations),
        'categorized_urls': categorized,
        'all_urls': sorted(list(all_urls)),
        'files_processed': [f['file'] for f in processed_files]
    }
    
    # Save to JSON
    output_dir = Path.cwd() / "timeline_data" / "qa_reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "extracted_sources.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n=== Extraction Summary ===")
    print(f"Files processed: {len(processed_files)}")
    print(f"Total URLs found: {len(all_urls)}")
    print(f"  Government: {len(categorized['government'])}")
    print(f"  News: {len(categorized['news'])}")
    print(f"  Academic: {len(categorized['academic'])}")
    print(f"  Legal: {len(categorized['legal'])}")
    print(f"  Social: {len(categorized['social'])}")
    print(f"  Other: {len(categorized['other'])}")
    print(f"\nOutput saved to: {output_file}")
    
    return output

if __name__ == "__main__":
    main()