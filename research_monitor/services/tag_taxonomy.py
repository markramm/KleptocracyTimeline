#!/usr/bin/env python3
"""
Tag Taxonomy and Normalization Service

Provides controlled vocabulary for timeline event tags with consistent naming,
normalization, and validation. Addresses data quality issues with 3,654 unique
tags and 295 concepts with multiple variations.

Design Principles:
- Use lowercase with hyphens as separators
- Prefer singular forms unless plural is more natural
- Group related tags into categories
- Provide migration path from legacy tags
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class TagTaxonomy:
    """Tag taxonomy with normalization and validation"""

    # Standard format: lowercase, hyphens, singular preferred
    CANONICAL_TAGS = {
        # === CAPTURE MECHANISMS (Primary Theme) ===
        'regulatory-capture': 'Capture of regulatory agencies by industry',
        'institutional-capture': 'Capture of government institutions',
        'judicial-capture': 'Capture of courts and judicial system',
        'legislative-capture': 'Capture of Congress/legislature',
        'financial-capture': 'Capture of financial regulators',
        'corporate-capture': 'General corporate capture of government',
        'media-capture': 'Capture of news media outlets',

        # === CORRUPTION & KLEPTOCRACY ===
        'corruption': 'General corruption',
        'kleptocracy': 'Systematic theft by those in power',
        'bribery': 'Bribery and payoffs',
        'embezzlement': 'Embezzlement of public funds',
        'fraud': 'Fraudulent activities',
        'money-laundering': 'Money laundering schemes',
        'systematic-corruption': 'Systemic patterns of corruption',
        'political-corruption': 'Corruption in political systems',
        'financial-corruption': 'Corruption in financial systems',

        # === INFLUENCE MECHANISMS ===
        'revolving-door': 'Movement between government and private sector',
        'lobbying': 'Lobbying activities',
        'campaign-finance': 'Campaign finance violations',
        'dark-money': 'Untraceable political spending',
        'foreign-influence': 'Foreign government influence',
        'corporate-influence': 'Corporate influence on policy',

        # === LEGAL & JUSTICE ===
        'constitutional-crisis': 'Constitutional violations or crises',
        'rule-of-law': 'Rule of law violations',
        'obstruction-of-justice': 'Justice obstruction',
        'justice-weaponization': 'Weaponization of justice system',
        'ethics-violation': 'Ethics violations',
        'conflict-of-interest': 'Conflicts of interest',
        'emoluments': 'Emoluments clause violations',
        'pardon': 'Presidential pardons',
        'constitutional-violation': 'Constitutional violations',
        'separation-of-powers': 'Separation of powers violations',

        # === COURTS & JUDICIARY ===
        'supreme-court': 'Supreme Court related',
        'judicial-ethics': 'Judicial ethics issues',
        'court-capture': 'Judicial capture',

        # === EXECUTIVE BRANCH ===
        'executive-power': 'Executive power abuse',
        'executive-overreach': 'Executive branch overreach',
        'executive-order': 'Executive orders',
        'presidential-authority': 'Presidential authority issues',

        # === FINANCIAL CRIMES ===
        'insider-trading': 'Insider trading',
        'securities-fraud': 'Securities fraud',
        'financial-crime': 'Financial crimes',
        'tax-evasion': 'Tax evasion',
        'wire-fraud': 'Wire fraud',

        # === GOVERNMENT CONTRACTS ===
        'government-contract': 'Government contracts',
        'no-bid-contract': 'No-bid contracts',
        'contract-fraud': 'Contract fraud',
        'procurement-abuse': 'Procurement abuse',

        # === MEDIA & INFORMATION ===
        'media-control': 'Media control',
        'media-manipulation': 'Media manipulation',
        'propaganda': 'Propaganda',
        'disinformation': 'Disinformation campaigns',
        'misinformation': 'Misinformation',
        'media-consolidation': 'Media consolidation',
        'press-freedom': 'Press freedom issues',

        # === SURVEILLANCE & SECURITY ===
        'surveillance': 'Surveillance programs',
        'warrantless-surveillance': 'Warrantless surveillance',
        'national-security': 'National security issues',
        'intelligence-abuse': 'Intelligence agency abuse',
        'privacy-violation': 'Privacy violations',

        # === TECHNOLOGY ===
        'crypto': 'Cryptocurrency related',
        'cryptocurrency': 'Cryptocurrency (use crypto)',
        'blockchain': 'Blockchain technology',
        'ai-safety': 'AI safety issues',
        'tech-regulation': 'Technology regulation',
        'cybersecurity': 'Cybersecurity issues',
        'data-privacy': 'Data privacy issues',

        # === ELECTION & POLITICAL ===
        'election-interference': 'Election interference',
        'election-fraud': 'Election fraud',
        'voter-suppression': 'Voter suppression',
        'gerrymandering': 'Gerrymandering',
        'campaign-violation': 'Campaign violations',

        # === FOREIGN RELATIONS ===
        'foreign-interference': 'Foreign interference',
        'sanctions': 'Sanctions',
        'foreign-policy': 'Foreign policy',
        'international-corruption': 'International corruption',

        # === SPECIFIC COUNTRIES ===
        'russia': 'Russia related',
        'china': 'China related',
        'saudi-arabia': 'Saudi Arabia related',
        'ukraine': 'Ukraine related',

        # === AGENCIES & INSTITUTIONS ===
        'doj': 'Department of Justice',
        'fbi': 'FBI',
        'cia': 'CIA',
        'nsa': 'NSA',
        'sec': 'Securities and Exchange Commission',
        'fcc': 'Federal Communications Commission',
        'epa': 'Environmental Protection Agency',

        # === ADMINISTRATIONS ===
        'trump-administration': 'Trump administration',
        'biden-administration': 'Biden administration',
        'obama-administration': 'Obama administration',
        'bush-administration': 'Bush administration',

        # === SPECIFIC EVENTS/PROGRAMS ===
        'whig': 'White House Iraq Group',
        'iraq-war': 'Iraq War',
        'project-2025': 'Project 2025',
        'january-6': 'January 6 attack',

        # === PEOPLE ===
        'trump': 'Donald Trump',
        'biden': 'Joe Biden',
        'kushner': 'Jared Kushner',
        'musk': 'Elon Musk',
        'thiel': 'Peter Thiel',
        'cheney': 'Dick Cheney',
        'barr': 'William Barr',

        # === NETWORKS ===
        'epstein-network': 'Jeffrey Epstein network',
        'koch-network': 'Koch network',
        'federalist-society': 'Federalist Society',
        'heritage-foundation': 'Heritage Foundation',

        # === WORKFORCE & LABOR ===
        'workforce-reduction': 'Government workforce reduction',
        'federal-workforce': 'Federal workforce',
        'immigration-enforcement': 'Immigration enforcement',

        # === FINANCIAL INSTITUTIONS ===
        'wall-street': 'Wall Street',
        'banking-regulation': 'Banking regulation',
        'financial-regulation': 'Financial regulation',
        'deregulation': 'Deregulation',

        # === ECONOMIC ===
        'structural-adjustment': 'Structural adjustment programs',
        'asian-financial-crisis': 'Asian financial crisis',
        'financial-crisis': 'Financial crisis',
        'economic-policy': 'Economic policy',
    }

    # Map variations to canonical tags
    TAG_MIGRATIONS = {
        # === Capture variations ===
        'regulatory capture': 'regulatory-capture',
        'regulatory_capture': 'regulatory-capture',
        'Regulatory Capture': 'regulatory-capture',

        'institutional capture': 'institutional-capture',
        'institutional_capture': 'institutional-capture',
        'Institutional Capture': 'institutional-capture',

        'judicial capture': 'judicial-capture',

        'corporate_capture': 'corporate-capture',
        'corporate capture': 'corporate-capture',

        'financial_capture': 'financial-capture',

        # === Conflict variations ===
        'conflict of interest': 'conflict-of-interest',
        'conflict_of_interest': 'conflict-of-interest',
        'conflicts-of-interest': 'conflict-of-interest',  # Prefer singular
        'conflicts_of_interest': 'conflict-of-interest',

        # === Ethics variations ===
        'ethics-violations': 'ethics-violation',  # Prefer singular
        'ethics_violations': 'ethics-violation',
        'ethics_violation': 'ethics-violation',

        # === Constitutional variations ===
        'constitutional_crisis': 'constitutional-crisis',
        'constitutional-violations': 'constitutional-violation',  # Prefer singular
        'constitutional_violations': 'constitutional-violation',
        'constitutional violations': 'constitutional-violation',

        # === Court variations ===
        'supreme_court': 'supreme-court',
        'Supreme Court': 'supreme-court',

        # === Administration variations ===
        'trump_administration': 'trump-administration',
        'Trump administration': 'trump-administration',

        # === Contract variations ===
        'government_contracts': 'government-contract',  # Prefer singular
        'government contracts': 'government-contract',

        # === Campaign variations ===
        'campaign_finance': 'campaign-finance',
        'campaign finance': 'campaign-finance',

        # === Media variations ===
        'media_control': 'media-control',
        'media_manipulation': 'media-manipulation',
        'Media Manipulation': 'media-manipulation',

        # === Security variations ===
        'national security': 'national-security',
        'national_security': 'national-security',
        'National Security': 'national-security',

        # === Executive variations ===
        'executive_power': 'executive-power',
        'executive-powers': 'executive-power',  # Prefer singular

        # === Election variations ===
        'election interference': 'election-interference',
        'election_interference': 'election-interference',

        # === Money variations ===
        'money laundering': 'money-laundering',
        'money_laundering': 'money-laundering',

        # === Justice variations ===
        'obstruction_of_justice': 'obstruction-of-justice',

        # === Revolving door variations ===
        'revolving door': 'revolving-door',
        'revolving_door': 'revolving-door',

        # === Iraq War variations ===
        'iraq_war': 'iraq-war',
        'Iraq War': 'iraq-war',

        # === Project 2025 variations ===
        'project_2025': 'project-2025',

        # === Foreign influence variations ===
        'foreign_influence': 'foreign-influence',

        # === Corporate influence variations ===
        'corporate_influence': 'corporate-influence',

        # === Separation of powers variations ===
        'separation_of_powers': 'separation-of-powers',

        # === AI safety variations ===
        'AI safety': 'ai-safety',
        'ai_safety': 'ai-safety',

        # === Insider trading variations ===
        'insider_trading': 'insider-trading',

        # === Federal workforce variations ===
        'federal_workforce': 'federal-workforce',

        # === WHIG variations ===
        'WHIG': 'whig',

        # === Financial crisis variations ===
        'asian_financial_crisis': 'asian-financial-crisis',

        # === Cryptocurrency synonym ===
        'cryptocurrency': 'crypto',  # Standardize on shorter form

        # === Pardons singular ===
        'pardons': 'pardon',
    }

    # Category groupings
    CATEGORIES = {
        'capture': [
            'regulatory-capture', 'institutional-capture', 'judicial-capture',
            'legislative-capture', 'financial-capture', 'corporate-capture',
            'media-capture'
        ],
        'corruption': [
            'corruption', 'kleptocracy', 'bribery', 'embezzlement', 'fraud',
            'money-laundering', 'systematic-corruption', 'political-corruption',
            'financial-corruption'
        ],
        'influence': [
            'revolving-door', 'lobbying', 'campaign-finance', 'dark-money',
            'foreign-influence', 'corporate-influence'
        ],
        'legal-justice': [
            'constitutional-crisis', 'rule-of-law', 'obstruction-of-justice',
            'justice-weaponization', 'ethics-violation', 'conflict-of-interest',
            'emoluments', 'pardon', 'constitutional-violation', 'separation-of-powers'
        ],
        'courts': [
            'supreme-court', 'judicial-ethics', 'court-capture'
        ],
        'executive': [
            'executive-power', 'executive-overreach', 'executive-order',
            'presidential-authority'
        ],
        'financial-crime': [
            'insider-trading', 'securities-fraud', 'financial-crime',
            'tax-evasion', 'wire-fraud'
        ],
        'contracts': [
            'government-contract', 'no-bid-contract', 'contract-fraud',
            'procurement-abuse'
        ],
        'media-information': [
            'media-control', 'media-manipulation', 'propaganda',
            'disinformation', 'misinformation', 'media-consolidation',
            'press-freedom'
        ],
        'surveillance-security': [
            'surveillance', 'warrantless-surveillance', 'national-security',
            'intelligence-abuse', 'privacy-violation'
        ],
        'technology': [
            'crypto', 'blockchain', 'ai-safety', 'tech-regulation',
            'cybersecurity', 'data-privacy'
        ],
        'election-political': [
            'election-interference', 'election-fraud', 'voter-suppression',
            'gerrymandering', 'campaign-violation'
        ],
        'foreign-relations': [
            'foreign-interference', 'sanctions', 'foreign-policy',
            'international-corruption', 'russia', 'china', 'saudi-arabia', 'ukraine'
        ],
        'agencies': [
            'doj', 'fbi', 'cia', 'nsa', 'sec', 'fcc', 'epa'
        ],
        'people': [
            'trump', 'biden', 'kushner', 'musk', 'thiel', 'cheney', 'barr'
        ],
        'networks': [
            'epstein-network', 'koch-network', 'federalist-society',
            'heritage-foundation'
        ],
    }

    @classmethod
    def normalize_tag(cls, tag: str) -> str:
        """
        Normalize a tag to canonical form

        Args:
            tag: Raw tag string

        Returns:
            Normalized canonical tag, or original if no mapping exists
        """
        if not tag:
            return tag

        # Check direct migration mapping first
        if tag in cls.TAG_MIGRATIONS:
            return cls.TAG_MIGRATIONS[tag]

        # Check if already canonical
        if tag in cls.CANONICAL_TAGS:
            return tag

        # Auto-normalize: lowercase + hyphens
        normalized = tag.lower().strip()
        normalized = re.sub(r'[_\s]+', '-', normalized)

        # Check if normalized form exists
        if normalized in cls.CANONICAL_TAGS:
            return normalized

        # Return normalized form even if not in vocabulary
        # (allows for new tags while enforcing format)
        return normalized

    @classmethod
    def normalize_tags(cls, tags: List[str]) -> List[str]:
        """
        Normalize a list of tags and remove duplicates

        Args:
            tags: List of raw tag strings

        Returns:
            List of normalized unique tags, preserving order
        """
        if not tags:
            return []

        seen = set()
        result = []

        for tag in tags:
            normalized = cls.normalize_tag(tag)
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)

        return result

    @classmethod
    def validate_tag(cls, tag: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a tag against taxonomy

        Args:
            tag: Tag to validate

        Returns:
            (is_valid, suggested_tag)
        """
        if not tag:
            return (False, None)

        normalized = cls.normalize_tag(tag)

        # Check if normalized form is canonical
        if normalized in cls.CANONICAL_TAGS:
            return (True, normalized if normalized != tag else None)

        # Check if it's a known variation
        if tag in cls.TAG_MIGRATIONS:
            return (False, cls.TAG_MIGRATIONS[tag])

        # Unknown tag - suggest normalized form
        return (False, normalized)

    @classmethod
    def get_category(cls, tag: str) -> Optional[str]:
        """Get category for a tag"""
        normalized = cls.normalize_tag(tag)

        for category, tags in cls.CATEGORIES.items():
            if normalized in tags:
                return category

        return None

    @classmethod
    def get_related_tags(cls, tag: str) -> List[str]:
        """Get related tags in the same category"""
        category = cls.get_category(tag)
        if not category:
            return []

        normalized = cls.normalize_tag(tag)
        return [t for t in cls.CATEGORIES[category] if t != normalized]

    @classmethod
    def get_statistics(cls) -> Dict[str, int]:
        """Get taxonomy statistics"""
        return {
            'canonical_tags': len(cls.CANONICAL_TAGS),
            'migration_rules': len(cls.TAG_MIGRATIONS),
            'categories': len(cls.CATEGORIES),
            'total_category_tags': sum(len(tags) for tags in cls.CATEGORIES.values())
        }
