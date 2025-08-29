"""
Smart Filter Extraction from Queries

Automatically extract metadata filters from natural language queries.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def extract_date_filters(query: str) -> Dict[str, Any]:
    """
    Extract date ranges, years, time periods from query.
    
    Args:
        query: Natural language query
        
    Returns:
        Dictionary with date filters
    """
    filters = {}
    
    # Year patterns
    year_patterns = [
        r'\b(in|during|from)\s+(\d{4})\b',
        r'\b(\d{4})\s+(events?|issues?|incidents?)\b',
        r'\b(\d{4})\b(?!\d)',  # Standalone 4-digit year
    ]
    
    years = []
    for pattern in year_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                year = match[1] if match[1].isdigit() else match[0]
            else:
                year = match
            if year.isdigit() and 1900 <= int(year) <= 2030:
                years.append(int(year))
    
    if years:
        # Convert years to date ranges
        unique_years = sorted(set(years))
        if len(unique_years) == 1:
            year = unique_years[0]
            filters['start_date'] = f'{year}-01-01'
            filters['end_date'] = f'{year}-12-31'
        else:
            filters['start_date'] = f'{min(unique_years)}-01-01'
            filters['end_date'] = f'{max(unique_years)}-12-31'
    
    # Month-year patterns
    month_year_pattern = r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})\b'
    month_matches = re.findall(month_year_pattern, query, re.IGNORECASE)
    
    if month_matches:
        month_map = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        
        for month, year in month_matches:
            if year.isdigit() and 1900 <= int(year) <= 2030:
                month_num = month_map[month.lower()]
                filters['start_date'] = f'{year}-{month_num}-01'
                
                # Calculate last day of month
                if month_num in ['01', '03', '05', '07', '08', '10', '12']:
                    last_day = '31'
                elif month_num in ['04', '06', '09', '11']:
                    last_day = '30'
                else:  # February
                    is_leap = int(year) % 4 == 0 and (int(year) % 100 != 0 or int(year) % 400 == 0)
                    last_day = '29' if is_leap else '28'
                
                filters['end_date'] = f'{year}-{month_num}-{last_day}'
                break  # Use first match
    
    # Relative time patterns
    relative_patterns = [
        (r'\b(recent|recently|lately)\b', 'recent'),
        (r'\b(current|now|today|present)\b', 'current'),
        (r'\b(last|past)\s+(year|month|week|day)s?\b', 'past_period'),
        (r'\b(since|after)\s+(\d{4})\b', 'since_year'),
        (r'\b(before|until)\s+(\d{4})\b', 'until_year')
    ]
    
    current_date = datetime.now()
    
    for pattern, time_type in relative_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            if time_type == 'recent':
                # Last 6 months
                start_date = current_date - timedelta(days=180)
                filters['start_date'] = start_date.strftime('%Y-%m-%d')
            elif time_type == 'current':
                # Current year
                filters['start_date'] = f'{current_date.year}-01-01'
                filters['end_date'] = f'{current_date.year}-12-31'
            elif time_type == 'past_period':
                # Extract period
                period_match = re.search(r'(last|past)\s+(year|month|week|day)s?', query, re.IGNORECASE)
                if period_match:
                    period = period_match.group(2).lower()
                    if period == 'year':
                        start_date = current_date - timedelta(days=365)
                    elif period == 'month':
                        start_date = current_date - timedelta(days=30)
                    elif period == 'week':
                        start_date = current_date - timedelta(days=7)
                    else:  # day
                        start_date = current_date - timedelta(days=1)
                    
                    filters['start_date'] = start_date.strftime('%Y-%m-%d')
            elif time_type == 'since_year':
                year = matches[0][1] if isinstance(matches[0], tuple) else matches[0]
                if year.isdigit():
                    filters['start_date'] = f'{year}-01-01'
            elif time_type == 'until_year':
                year = matches[0][1] if isinstance(matches[0], tuple) else matches[0]
                if year.isdigit():
                    filters['end_date'] = f'{year}-12-31'
    
    # Specific date patterns (YYYY-MM-DD, MM/DD/YYYY, etc.)
    specific_date_patterns = [
        r'\b(\d{4}-\d{2}-\d{2})\b',  # YYYY-MM-DD
        r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',  # MM/DD/YYYY or M/D/YYYY
        r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b'   # MM-DD-YYYY or M-D-YYYY
    ]
    
    for pattern in specific_date_patterns:
        matches = re.findall(pattern, query)
        if matches:
            for match in matches:
                if isinstance(match, tuple) and len(match) == 3:
                    # MM/DD/YYYY format
                    month, day, year = match
                    try:
                        date_str = f'{year}-{month.zfill(2)}-{day.zfill(2)}'
                        # Validate date
                        datetime.strptime(date_str, '%Y-%m-%d')
                        filters['specific_date'] = date_str
                        break
                    except ValueError:
                        continue
                else:
                    # YYYY-MM-DD format
                    try:
                        datetime.strptime(match, '%Y-%m-%d')
                        filters['specific_date'] = match
                        break
                    except ValueError:
                        continue
    
    return filters


def extract_actor_filters(query: str, known_actors: List[str] = None) -> List[str]:
    """
    Extract actor names from query.
    
    Args:
        query: Natural language query
        known_actors: List of known actor names
        
    Returns:
        List of detected actor names
    """
    actors = []
    known_actors = known_actors or []
    
    # Check for known actors in query
    for actor in known_actors:
        if actor.lower() in query.lower():
            actors.append(actor)
    
    # Common political figures (case-insensitive patterns)
    political_figures = [
        r'\b(donald\s+trump|trump)\b',
        r'\b(joe\s+biden|biden)\b',
        r'\b(barack\s+obama|obama)\b',
        r'\b(hillary\s+clinton|clinton)\b',
        r'\b(nancy\s+pelosi|pelosi)\b',
        r'\b(mitch\s+mcconnell|mcconnell)\b',
        r'\b(chuck\s+schumer|schumer)\b',
        r'\b(elon\s+musk|musk)\b',
        r'\b(mark\s+zuckerberg|zuckerberg)\b',
        r'\b(jeff\s+bezos|bezos)\b',
        r'\b(vladimir\s+putin|putin)\b',
        r'\b(xi\s+jinping|xi)\b'
    ]
    
    for pattern in political_figures:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            # Normalize the name
            match = matches[0].lower()
            if 'trump' in match:
                actors.append('Donald Trump')
            elif 'biden' in match:
                actors.append('Joe Biden')
            elif 'obama' in match:
                actors.append('Barack Obama')
            elif 'clinton' in match:
                actors.append('Hillary Clinton')
            elif 'pelosi' in match:
                actors.append('Nancy Pelosi')
            elif 'mcconnell' in match:
                actors.append('Mitch McConnell')
            elif 'schumer' in match:
                actors.append('Chuck Schumer')
            elif 'musk' in match:
                actors.append('Elon Musk')
            elif 'zuckerberg' in match:
                actors.append('Mark Zuckerberg')
            elif 'bezos' in match:
                actors.append('Jeff Bezos')
            elif 'putin' in match:
                actors.append('Vladimir Putin')
            elif 'xi' in match:
                actors.append('Xi Jinping')
    
    # Organizations and companies
    organizations = [
        r'\b(meta|facebook)\b',
        r'\b(google|alphabet)\b',
        r'\b(amazon)\b',
        r'\b(microsoft)\b',
        r'\b(tesla)\b',
        r'\b(twitter|x\.com)\b',
        r'\b(fbi|federal\s+bureau\s+of\s+investigation)\b',
        r'\b(cia|central\s+intelligence\s+agency)\b',
        r'\b(nsa|national\s+security\s+agency)\b',
        r'\b(doj|department\s+of\s+justice)\b',
        r'\b(sec|securities\s+and\s+exchange\s+commission)\b',
        r'\b(epa|environmental\s+protection\s+agency)\b',
        r'\b(supreme\s+court)\b',
        r'\b(congress|senate|house\s+of\s+representatives)\b'
    ]
    
    for pattern in organizations:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            match = matches[0].lower()
            if 'meta' in match or 'facebook' in match:
                actors.append('Meta')
            elif 'google' in match or 'alphabet' in match:
                actors.append('Google')
            elif 'amazon' in match:
                actors.append('Amazon')
            elif 'microsoft' in match:
                actors.append('Microsoft')
            elif 'tesla' in match:
                actors.append('Tesla')
            elif 'twitter' in match or 'x.com' in match:
                actors.append('X (Twitter)')
            elif 'fbi' in match or 'federal bureau' in match:
                actors.append('FBI')
            elif 'cia' in match or 'central intelligence' in match:
                actors.append('CIA')
            elif 'nsa' in match or 'national security' in match:
                actors.append('NSA')
            elif 'doj' in match or 'department of justice' in match:
                actors.append('DOJ')
            elif 'sec' in match or 'securities and exchange' in match:
                actors.append('SEC')
            elif 'epa' in match or 'environmental protection' in match:
                actors.append('EPA')
            elif 'supreme court' in match:
                actors.append('Supreme Court')
            elif any(word in match for word in ['congress', 'senate', 'house']):
                actors.append('Congress')
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(actors))


def extract_importance_filters(query: str) -> Dict[str, Any]:
    """
    Extract importance filters (critical, major, etc.).
    
    Args:
        query: Natural language query
        
    Returns:
        Dictionary with importance filters
    """
    filters = {}
    
    # Importance level patterns
    importance_patterns = [
        (r'\b(critical|crucial|vital|essential)\b', 8),  # High importance
        (r'\b(major|significant|important|key)\b', 6),   # Medium-high importance  
        (r'\b(notable|substantial|considerable)\b', 5),   # Medium importance
        (r'\b(minor|small|slight|limited)\b', 3),        # Low importance
        (r'\b(breaking|urgent|emergency)\b', 9),         # Urgent/breaking
        (r'\b(historic|landmark|unprecedented)\b', 9),    # Historic significance
        (r'\b(scandal|controversy|illegal)\b', 7)         # Scandal importance
    ]
    
    for pattern, importance_score in importance_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            if 'min_importance' not in filters or importance_score > filters['min_importance']:
                filters['min_importance'] = importance_score
    
    # Priority modifiers
    priority_patterns = [
        r'\b(highest|maximum|top)\s+(priority|importance)\b',
        r'\b(high|top)\s+(priority|importance)\b',
        r'\b(priority|important)\s+(events?|issues?)\b'
    ]
    
    for pattern in priority_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            if 'min_importance' not in filters:
                filters['min_importance'] = 7
    
    return filters


def extract_metadata_filters(query: str) -> Dict[str, Any]:
    """
    Extract additional metadata filters from query.
    
    Args:
        query: Natural language query
        
    Returns:
        Dictionary with metadata filters
    """
    filters = {}
    
    # Status filters
    status_patterns = [
        (r'\b(confirmed|verified|validated)\b', 'confirmed'),
        (r'\b(reported|alleged|claimed)\b', 'reported'),
        (r'\b(disputed|controversial|contested)\b', 'disputed'),
        (r'\b(developing|ongoing|unfolding)\b', 'developing')
    ]
    
    statuses = []
    for pattern, status in status_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            statuses.append(status)
    
    if statuses:
        filters['status'] = statuses
    
    # Source quality filters
    source_patterns = [
        r'\b(well\s+sourced|multiple\s+sources|credible\s+sources)\b',
        r'\b(primary\s+sources?|first\s+hand|direct\s+evidence)\b',
        r'\b(reliable|trustworthy|authoritative)\s+(sources?|reports?)\b'
    ]
    
    for pattern in source_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            filters['min_sources'] = 2  # Require at least 2 sources
            break
    
    # Location filters
    location_patterns = [
        (r'\b(washington\s+d\.?c\.?|dc)\b', 'Washington, DC'),
        (r'\b(united\s+states|usa?|america)\b', 'United States'),
        (r'\b(russia|russian|moscow)\b', 'Russia'),
        (r'\b(china|chinese|beijing)\b', 'China'),
        (r'\b(saudi\s+arabia|saudi|riyadh)\b', 'Saudi Arabia'),
        (r'\b(ukraine|ukrainian|kyiv|kiev)\b', 'Ukraine'),
        (r'\b(international|global|worldwide)\b', 'International')
    ]
    
    locations = []
    for pattern, location in location_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            locations.append(location)
    
    if locations:
        filters['locations'] = locations
    
    # Tag filters (explicit tag mentions)
    tag_patterns = [
        r'\b(cryptocurrency|crypto|bitcoin)\b',
        r'\b(regulatory\s+capture|agency\s+capture)\b',
        r'\b(judicial\s+capture|court\s+packing)\b',
        r'\b(media\s+capture|propaganda)\b',
        r'\b(election\s+integrity|voter\s+fraud)\b',
        r'\b(schedule\s+f|federal\s+workforce)\b',
        r'\b(executive\s+orders?)\b',
        r'\b(national\s+security)\b',
        r'\b(foreign\s+influence|foreign\s+interference)\b',
        r'\b(corruption|bribery|kickbacks)\b'
    ]
    
    tags = []
    for pattern in tag_patterns:
        matches = re.findall(pattern, query, re.IGNORECASE)
        if matches:
            match = matches[0].lower()
            if 'crypto' in match or 'bitcoin' in match:
                tags.append('cryptocurrency')
            elif 'regulatory capture' in match or 'agency capture' in match:
                tags.append('regulatory-capture')
            elif 'judicial capture' in match or 'court packing' in match:
                tags.append('judicial-capture')
            elif 'media capture' in match or 'propaganda' in match:
                tags.append('media-manipulation')
            elif 'election' in match:
                tags.append('election-integrity')
            elif 'schedule f' in match or 'federal workforce' in match:
                tags.append('federal-workforce')
            elif 'executive order' in match:
                tags.append('executive-orders')
            elif 'national security' in match:
                tags.append('national-security')
            elif 'foreign' in match:
                tags.append('foreign-influence')
            elif any(word in match for word in ['corruption', 'bribery', 'kickbacks']):
                tags.append('corruption')
    
    if tags:
        filters['tags'] = list(set(tags))  # Remove duplicates
    
    return filters


def combine_filters(filters_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Combine multiple filter dictionaries intelligently.
    
    Args:
        filters_list: List of filter dictionaries
        
    Returns:
        Combined filter dictionary
    """
    combined = {}
    
    for filters in filters_list:
        for key, value in filters.items():
            if key not in combined:
                combined[key] = value
            elif isinstance(value, list) and isinstance(combined[key], list):
                # Combine lists, remove duplicates
                combined[key] = list(set(combined[key] + value))
            elif key == 'min_importance':
                # Take the highest importance requirement
                combined[key] = max(combined[key], value)
            elif key == 'min_sources':
                # Take the highest source requirement
                combined[key] = max(combined[key], value)
            elif key in ['start_date', 'end_date']:
                # Keep existing date unless new one is more specific
                if not combined[key] or len(str(value)) > len(str(combined[key])):
                    combined[key] = value
    
    return combined


if __name__ == '__main__':
    # Test filter extraction
    test_queries = [
        "What events involve cryptocurrency and Trump in 2025?",
        "Show me critical regulatory capture events since 2024",
        "Recent confirmed events about Schedule F with multiple sources",
        "Major scandal involving Elon Musk and regulatory agencies",
        "Breaking news about judicial capture in Washington DC"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        date_filters = extract_date_filters(query)
        print(f"Date filters: {date_filters}")
        
        actor_filters = extract_actor_filters(query)
        print(f"Actor filters: {actor_filters}")
        
        importance_filters = extract_importance_filters(query)
        print(f"Importance filters: {importance_filters}")
        
        metadata_filters = extract_metadata_filters(query)
        print(f"Metadata filters: {metadata_filters}")
        
        # Combine all filters
        all_filters = combine_filters([date_filters, importance_filters, metadata_filters])
        if actor_filters:
            all_filters['actors'] = actor_filters
        
        print(f"Combined: {all_filters}")