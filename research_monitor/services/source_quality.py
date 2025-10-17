#!/usr/bin/env python3
"""
Source Quality Classification Service

Classifies timeline event sources into quality tiers based on outlet credibility,
editorial standards, and journalistic reputation. Helps ensure research credibility
by requiring mix of high-quality sources.

Tier Classification:
- Tier 1: Major news organizations, government sources, academic institutions
- Tier 2: Established smaller outlets, investigative journalism, trade publications
- Tier 3: Blogs, opinion sites, less established sources, unknown outlets

Quality Standards:
- Prefer 2+ tier-1 sources per event
- Acceptable: Mix of tier-1 and tier-2 sources
- Flag: Events with only tier-3 sources
- Flag: Events with < 2 total sources
"""

from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict


class SourceQualityClassifier:
    """Classifies source outlets by quality tier"""

    # Tier 1: Major credible news organizations, government, academic
    TIER_1_OUTLETS = {
        # Major US News Organizations
        'Associated Press', 'Reuters', 'NPR', 'PBS', 'PBS News', 'PBS NewsHour',
        'Wall Street Journal', 'New York Times', 'The New York Times',
        'Washington Post', 'The Washington Post', 'Bloomberg', 'Bloomberg News',
        'CNN', 'CNN Politics', 'CNN Business', 'ABC News', 'NBC News', 'CBS News',
        'CNBC', 'BBC', 'BBC News',

        # Major International News
        'Al Jazeera', 'The Guardian', 'Financial Times', 'The Economist',

        # Government Sources (Primary)
        'U.S. Department of Justice', 'Department of Justice', 'DOJ',
        'Federal Bureau of Investigation', 'FBI',
        'Securities and Exchange Commission', 'SEC',
        'Federal Trade Commission', 'FTC',
        'White House', 'U.S. Senate', 'U.S. House of Representatives',
        'Congressional Record', 'Federal Register', 'Supreme Court',
        'U.S. Courts', 'Government Accountability Office', 'GAO',
        'Office of Government Ethics', 'OGE',
        'Federal Communications Commission', 'FCC',
        'Environmental Protection Agency', 'EPA',
        'Treasury Department', 'U.S. Treasury',
        'State Department', 'U.S. State Department',
        'Congress.gov', 'GovInfo', 'USA.gov',

        # Academic & Research Institutions
        'Harvard Law Review', 'Stanford Law Review', 'Yale Law Journal',
        'Brookings Institution', 'RAND Corporation', 'Pew Research Center',
        'American Economic Review', 'Journal of Economic Perspectives',

        # International Organizations
        'United Nations', 'World Bank', 'International Monetary Fund', 'IMF',
        'OECD', 'Transparency International',

        # Investigative Journalism (Top Tier)
        'ProPublica', 'The Intercept', 'Center for Public Integrity',
        'International Consortium of Investigative Journalists', 'ICIJ',

        # Legal/Judicial Analysis
        'SCOTUSblog', 'Lawfare', 'Just Security',
    }

    # Tier 2: Established outlets, trade publications, smaller news orgs
    TIER_2_OUTLETS = {
        # Established News Outlets
        'Politico', 'The Hill', 'Axios', 'Newsweek', 'Time', 'Vox',
        'The Atlantic', 'The New Yorker', 'Vanity Fair',
        'Rolling Stone', 'Mother Jones', 'The Nation',
        'Fortune', 'Forbes', 'Business Insider',
        'The Daily Beast', 'Salon', 'Slate',
        'Yahoo News', 'Yahoo Finance', 'MarketWatch',

        # Trade & Industry Publications
        'TechCrunch', 'Ars Technica', 'Wired', 'The Verge',
        'CoinDesk', 'Coinbase', 'Decrypt', 'Fortune Crypto',
        'Federal News Network', 'Government Executive',
        'Roll Call', 'The National Law Journal', 'Law360',
        'Healthcare Dive', 'Defense News',

        # Regional News
        'Los Angeles Times', 'Chicago Tribune', 'Boston Globe',
        'San Francisco Chronicle', 'Miami Herald',

        # International Established
        'Deutsche Welle', 'France 24', 'South China Morning Post',
        'The Times of India', 'The Globe and Mail',

        # Think Tanks & Policy Organizations
        'Brennan Center for Justice', 'American Civil Liberties Union', 'ACLU',
        'Electronic Frontier Foundation', 'EFF',
        'Center for American Progress', 'Cato Institute',
        'Heritage Foundation', 'American Enterprise Institute',
        'Hoover Institution', 'Council on Foreign Relations',

        # Watchdog Organizations
        'OpenSecrets', 'SourceWatch', 'FollowTheMoney',
        'Project on Government Oversight', 'POGO',
        'Citizens for Responsibility and Ethics', 'CREW',
        'Common Cause', 'Public Citizen',

        # Legal Research
        'Bloomberg Law', 'Cornell Law School', 'Justia',

        # Financial Data
        'S&P Global', 'Moody\'s', 'Fitch Ratings',

        # News Aggregators (Quality)
        'RealClearPolitics', 'Memeorandum',

        # Specialized News
        'Inside Higher Ed', 'Chronicle of Higher Education',
        'The Hollywood Reporter', 'Variety',
        'Science', 'Nature', 'Scientific American',

        # Regional/Local Investigative
        'Texas Observer', 'Voice of San Diego', 'The Seattle Times',
    }

    # Tier 3: Less established, blogs, opinion, unknown
    TIER_3_OUTLETS = {
        # General catch-all
        'Unknown', 'Blog', 'Personal Blog', 'Medium', 'Substack',

        # Questionable/Partisan
        'Breitbart', 'InfoWars', 'The Daily Caller', 'The Daily Wire',
        'The Federalist', 'Red State', 'The Blaze',
        'Occupy Democrats', 'Palmer Report', 'Raw Story',

        # Social Media
        'Twitter', 'Facebook', 'Reddit', 'YouTube',

        # Press Releases (Not Independent)
        'PR Newswire', 'Business Wire', 'Globe Newswire',

        # Reference (Not Primary Sources)
        'Wikipedia', 'Britannica', 'Dictionary.com',
    }

    # Domain patterns for auto-classification
    TIER_1_DOMAINS = {
        'npr.org', 'pbs.org', 'apnews.com', 'reuters.com',
        'wsj.com', 'nytimes.com', 'washingtonpost.com', 'bloomberg.com',
        'bbc.com', 'bbc.co.uk', 'theguardian.com', 'ft.com',
        'cnn.com', 'abcnews.go.com', 'nbcnews.com', 'cbsnews.com',
        'justice.gov', 'fbi.gov', 'sec.gov', 'ftc.gov', 'whitehouse.gov',
        'senate.gov', 'house.gov', 'congress.gov', 'supremecourt.gov',
        'gao.gov', 'federalregister.gov', 'govinfo.gov',
        'propublica.org', 'icij.org',
    }

    TIER_2_DOMAINS = {
        'politico.com', 'thehill.com', 'axios.com', 'newsweek.com',
        'vox.com', 'theatlantic.com', 'newyorker.com',
        'fortune.com', 'forbes.com', 'businessinsider.com',
        'techcrunch.com', 'arstechnica.com', 'theverge.com',
        'opensecrets.org', 'sourcewatch.org', 'brennancenter.org',
        'aclu.org', 'eff.org',
    }

    @classmethod
    def classify_outlet(cls, outlet: str, url: Optional[str] = None) -> int:
        """
        Classify source outlet into tier (1, 2, or 3)

        Args:
            outlet: Name of the source outlet
            url: Optional URL for domain-based classification

        Returns:
            Tier number: 1 (best), 2 (good), or 3 (questionable/unknown)
        """
        if not outlet:
            return 3

        # Check explicit tier lists
        if outlet in cls.TIER_1_OUTLETS:
            return 1
        if outlet in cls.TIER_2_OUTLETS:
            return 2
        if outlet in cls.TIER_3_OUTLETS:
            return 3

        # Check domain if URL provided
        if url:
            url_lower = url.lower()
            for domain in cls.TIER_1_DOMAINS:
                if domain in url_lower:
                    return 1
            for domain in cls.TIER_2_DOMAINS:
                if domain in url_lower:
                    return 2

        # Check for government domains (.gov)
        if url and '.gov' in url.lower():
            return 1

        # Check for academic domains (.edu)
        if url and '.edu' in url.lower():
            return 1

        # Default to tier 3 for unknown
        return 3

    @classmethod
    def classify_event_sources(cls, event: Dict) -> Dict:
        """
        Classify all sources for an event

        Args:
            event: Event dictionary with 'sources' field

        Returns:
            Dict with classification results:
            {
                'total_sources': int,
                'tier_1_count': int,
                'tier_2_count': int,
                'tier_3_count': int,
                'tier_1_percent': float,
                'tier_2_percent': float,
                'tier_3_percent': float,
                'quality_score': float (0-10),
                'quality_level': str (excellent/good/fair/poor),
                'issues': List[str],
                'sources_by_tier': Dict[int, List[Dict]]
            }
        """
        sources = event.get('sources', [])
        if not isinstance(sources, list):
            sources = []

        result = {
            'total_sources': len(sources),
            'tier_1_count': 0,
            'tier_2_count': 0,
            'tier_3_count': 0,
            'tier_1_percent': 0.0,
            'tier_2_percent': 0.0,
            'tier_3_percent': 0.0,
            'quality_score': 0.0,
            'quality_level': 'unknown',
            'issues': [],
            'sources_by_tier': {1: [], 2: [], 3: []}
        }

        if len(sources) == 0:
            result['issues'].append('No sources provided')
            result['quality_level'] = 'poor'
            return result

        # Classify each source
        for source in sources:
            if not isinstance(source, dict):
                continue

            outlet = source.get('outlet', 'Unknown')
            url = source.get('url', '')
            tier = cls.classify_outlet(outlet, url)

            source_info = {
                'outlet': outlet,
                'url': url,
                'tier': tier,
                'title': source.get('title', ''),
            }

            result['sources_by_tier'][tier].append(source_info)

            if tier == 1:
                result['tier_1_count'] += 1
            elif tier == 2:
                result['tier_2_count'] += 1
            else:
                result['tier_3_count'] += 1

        # Calculate percentages
        total = result['total_sources']
        if total > 0:
            result['tier_1_percent'] = (result['tier_1_count'] / total) * 100
            result['tier_2_percent'] = (result['tier_2_count'] / total) * 100
            result['tier_3_percent'] = (result['tier_3_count'] / total) * 100

        # Calculate quality score (0-10)
        # Formula: (tier1 * 1.0 + tier2 * 0.6 + tier3 * 0.2) / total * 10
        if total > 0:
            weighted_sum = (
                result['tier_1_count'] * 1.0 +
                result['tier_2_count'] * 0.6 +
                result['tier_3_count'] * 0.2
            )
            result['quality_score'] = (weighted_sum / total) * 10

        # Determine quality level
        score = result['quality_score']
        if score >= 8.0:
            result['quality_level'] = 'excellent'
        elif score >= 6.0:
            result['quality_level'] = 'good'
        elif score >= 4.0:
            result['quality_level'] = 'fair'
        else:
            result['quality_level'] = 'poor'

        # Check for issues
        if total < 2:
            result['issues'].append(f'Only {total} source(s) - minimum 2 recommended')

        if result['tier_1_count'] == 0 and result['tier_2_count'] == 0:
            result['issues'].append('No tier-1 or tier-2 sources - all sources are tier-3')

        if result['tier_1_count'] == 0 and total >= 2:
            result['issues'].append('No tier-1 sources - recommend adding major news source')

        if result['tier_3_count'] > result['tier_1_count'] + result['tier_2_count']:
            result['issues'].append('More tier-3 sources than tier-1/tier-2 combined')

        return result

    @classmethod
    def get_statistics(cls) -> Dict:
        """Get classifier statistics"""
        return {
            'tier_1_outlets': len(cls.TIER_1_OUTLETS),
            'tier_2_outlets': len(cls.TIER_2_OUTLETS),
            'tier_3_outlets': len(cls.TIER_3_OUTLETS),
            'tier_1_domains': len(cls.TIER_1_DOMAINS),
            'tier_2_domains': len(cls.TIER_2_DOMAINS),
            'total_classified': len(cls.TIER_1_OUTLETS) + len(cls.TIER_2_OUTLETS) + len(cls.TIER_3_OUTLETS)
        }

    @classmethod
    def suggest_outlets_for_topic(cls, topic: str) -> List[Tuple[str, int]]:
        """
        Suggest appropriate outlets for a given topic

        Args:
            topic: Topic area (e.g., 'crypto', 'legal', 'government')

        Returns:
            List of (outlet, tier) tuples
        """
        topic_lower = topic.lower()
        suggestions = []

        # Topic-specific suggestions
        if 'crypto' in topic_lower or 'blockchain' in topic_lower:
            suggestions.extend([
                ('CoinDesk', 2), ('Bloomberg', 1), ('Fortune Crypto', 2),
                ('Reuters', 1), ('Wall Street Journal', 1)
            ])
        elif 'legal' in topic_lower or 'court' in topic_lower:
            suggestions.extend([
                ('SCOTUSblog', 1), ('Lawfare', 1), ('Reuters', 1),
                ('Bloomberg Law', 2), ('New York Times', 1)
            ])
        elif 'government' in topic_lower or 'federal' in topic_lower:
            suggestions.extend([
                ('NPR', 1), ('Washington Post', 1), ('Politico', 2),
                ('Government Executive', 2), ('The Hill', 2)
            ])
        elif 'tech' in topic_lower:
            suggestions.extend([
                ('TechCrunch', 2), ('Ars Technica', 2), ('The Verge', 2),
                ('Bloomberg', 1), ('Reuters', 1)
            ])
        else:
            # General recommendations
            suggestions.extend([
                ('Reuters', 1), ('Associated Press', 1), ('NPR', 1),
                ('Washington Post', 1), ('Bloomberg', 1), ('ProPublica', 1)
            ])

        return suggestions
