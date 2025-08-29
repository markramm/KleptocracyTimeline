"""
Fact-Checking and Source Verification System

Advanced fact-checking capabilities for verifying claims and sources
in the kleptocracy/democracy research domain.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import re
from collections import defaultdict
import numpy as np
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class FactCheckResult:
    """Result of fact-checking a claim."""
    claim: str
    verdict: str  # verified, partially_verified, disputed, unverified
    confidence: float
    
    # Supporting evidence
    supporting_sources: List[Dict] = field(default_factory=list)
    contradicting_sources: List[Dict] = field(default_factory=list)
    
    # Analysis details
    claim_type: str = ''  # statistical, temporal, attribution, etc.
    verification_method: str = ''
    notes: str = ''


@dataclass
class SourceVerificationResult:
    """Result of source verification."""
    source_url: str
    credibility_score: float
    
    # Source attributes
    domain_reputation: float = 0.0
    content_consistency: float = 0.0
    citation_quality: float = 0.0
    temporal_validity: float = 0.0
    
    # Issues found
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class FactChecker:
    """
    Advanced fact-checking system for research validation.
    
    Features:
    - Claim extraction and classification
    - Multi-source verification
    - Statistical claim validation
    - Temporal claim verification
    - Attribution verification
    """
    
    def __init__(self, knowledge_base: List[Dict[str, Any]]):
        """
        Initialize fact checker.
        
        Args:
            knowledge_base: Corpus of verified events for fact-checking
        """
        self.knowledge_base = knowledge_base
        
        # Build fact indices
        self._build_fact_indices()
        
        # Fact-checking statistics
        self.check_stats = defaultdict(int)
        
        logger.info(f"Initialized FactChecker with {len(knowledge_base)} knowledge base events")
    
    def _build_fact_indices(self):
        """Build indices for efficient fact lookup."""
        # Statistical facts index
        self.statistical_facts = defaultdict(list)
        
        # Temporal facts index
        self.temporal_facts = defaultdict(list)
        
        # Attribution index
        self.attribution_facts = defaultdict(list)
        
        for event in self.knowledge_base:
            # Extract and index facts from event
            facts = self._extract_facts_from_event(event)
            
            for fact in facts:
                if fact['type'] == 'statistical':
                    self.statistical_facts[fact['category']].append(fact)
                elif fact['type'] == 'temporal':
                    self.temporal_facts[fact['date']].append(fact)
                elif fact['type'] == 'attribution':
                    self.attribution_facts[fact['subject']].append(fact)
    
    def _extract_facts_from_event(self, event: Dict) -> List[Dict]:
        """Extract verifiable facts from an event."""
        facts = []
        
        # Extract statistical facts (numbers, percentages)
        summary = event.get('summary', '')
        
        # Find percentages
        percentage_pattern = r'(\d+(?:\.\d+)?)\s*(?:percent|%)'
        for match in re.finditer(percentage_pattern, summary, re.IGNORECASE):
            facts.append({
                'type': 'statistical',
                'category': 'percentage',
                'value': float(match.group(1)),
                'context': summary[max(0, match.start()-50):min(len(summary), match.end()+50)],
                'source_event': event.get('id'),
                'confidence': event.get('status') == 'confirmed' and 1.0 or 0.7
            })
        
        # Find monetary amounts
        money_pattern = r'\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion|trillion)?'
        for match in re.finditer(money_pattern, summary, re.IGNORECASE):
            amount = float(match.group(1).replace(',', ''))
            multiplier = {'million': 1e6, 'billion': 1e9, 'trillion': 1e12}.get(
                (match.group(2) or '').lower(), 1
            )
            facts.append({
                'type': 'statistical',
                'category': 'monetary',
                'value': amount * multiplier,
                'context': summary[max(0, match.start()-50):min(len(summary), match.end()+50)],
                'source_event': event.get('id'),
                'confidence': event.get('status') == 'confirmed' and 1.0 or 0.7
            })
        
        # Extract temporal facts
        if event.get('date'):
            facts.append({
                'type': 'temporal',
                'date': event['date'],
                'event_title': event.get('title', ''),
                'actors': event.get('actors', []),
                'source_event': event.get('id'),
                'confidence': 1.0 if event.get('sources') else 0.5
            })
        
        # Extract attribution facts
        actors = event.get('actors', [])
        if isinstance(actors, str):
            actors = [actors]
        
        for actor in actors:
            if actor:
                facts.append({
                    'type': 'attribution',
                    'subject': actor.lower(),
                    'action': event.get('title', ''),
                    'date': event.get('date', ''),
                    'source_event': event.get('id'),
                    'confidence': event.get('status') == 'confirmed' and 1.0 or 0.6
                })
        
        return facts
    
    def check_claim(self, claim: str, context: Optional[Dict] = None) -> FactCheckResult:
        """
        Fact-check a specific claim.
        
        Args:
            claim: The claim to check
            context: Optional context (e.g., date, actors involved)
            
        Returns:
            FactCheckResult with verdict and evidence
        """
        self.check_stats['total_checks'] += 1
        
        # Classify claim type
        claim_type = self._classify_claim(claim)
        
        # Route to appropriate verification method
        if claim_type == 'statistical':
            result = self._check_statistical_claim(claim, context)
        elif claim_type == 'temporal':
            result = self._check_temporal_claim(claim, context)
        elif claim_type == 'attribution':
            result = self._check_attribution_claim(claim, context)
        else:
            result = self._check_general_claim(claim, context)
        
        # Update statistics
        self.check_stats[f'{result.verdict}_count'] += 1
        
        return result
    
    def _classify_claim(self, claim: str) -> str:
        """Classify the type of claim."""
        claim_lower = claim.lower()
        
        # Check for statistical indicators
        if any(pattern in claim_lower for pattern in ['%', 'percent', 'number', 'amount', '$']):
            return 'statistical'
        
        # Check for temporal indicators
        if any(word in claim_lower for word in ['when', 'date', 'year', 'month', 'before', 'after']):
            return 'temporal'
        
        # Check for attribution indicators
        if any(word in claim_lower for word in ['said', 'stated', 'claimed', 'announced', 'declared']):
            return 'attribution'
        
        return 'general'
    
    def _check_statistical_claim(self, claim: str, context: Optional[Dict]) -> FactCheckResult:
        """Check a statistical claim."""
        # Extract numbers from claim
        numbers = re.findall(r'\d+(?:\.\d+)?', claim)
        
        if not numbers:
            return FactCheckResult(
                claim=claim,
                verdict='unverified',
                confidence=0.0,
                claim_type='statistical',
                verification_method='no_numbers_found'
            )
        
        # Find relevant statistical facts
        relevant_facts = []
        for category_facts in self.statistical_facts.values():
            for fact in category_facts:
                # Check if fact is contextually relevant
                if context:
                    if context.get('date') and fact.get('date'):
                        if not self._dates_compatible(context['date'], fact['date']):
                            continue
                
                # Check if numbers match
                for num_str in numbers:
                    num = float(num_str)
                    if abs(fact['value'] - num) / max(fact['value'], num) < 0.1:  # Within 10%
                        relevant_facts.append(fact)
        
        # Determine verdict based on findings
        if relevant_facts:
            avg_confidence = np.mean([f['confidence'] for f in relevant_facts])
            
            if avg_confidence >= 0.8:
                verdict = 'verified'
            elif avg_confidence >= 0.6:
                verdict = 'partially_verified'
            else:
                verdict = 'unverified'
            
            return FactCheckResult(
                claim=claim,
                verdict=verdict,
                confidence=avg_confidence,
                supporting_sources=[{'event_id': f['source_event'], 'confidence': f['confidence']} 
                                  for f in relevant_facts],
                claim_type='statistical',
                verification_method='numerical_matching'
            )
        
        return FactCheckResult(
            claim=claim,
            verdict='unverified',
            confidence=0.3,
            claim_type='statistical',
            verification_method='no_matching_facts',
            notes='No matching statistical facts found in knowledge base'
        )
    
    def _check_temporal_claim(self, claim: str, context: Optional[Dict]) -> FactCheckResult:
        """Check a temporal claim."""
        # Extract dates from claim
        date_patterns = [
            r'\b(\d{4})\b',  # Year
            r'\b(\d{4}-\d{2}-\d{2})\b',  # Full date
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, claim, re.IGNORECASE)
            dates_found.extend(matches)
        
        if not dates_found:
            return FactCheckResult(
                claim=claim,
                verdict='unverified',
                confidence=0.0,
                claim_type='temporal',
                verification_method='no_dates_found'
            )
        
        # Check temporal facts
        supporting = []
        contradicting = []
        
        for date_str in dates_found:
            # Find events on or near this date
            matching_facts = self.temporal_facts.get(date_str, [])
            
            for fact in matching_facts:
                # Check if claim content matches
                if self._claim_matches_fact(claim, fact):
                    supporting.append(fact)
                elif self._claim_contradicts_fact(claim, fact):
                    contradicting.append(fact)
        
        # Determine verdict
        if contradicting:
            return FactCheckResult(
                claim=claim,
                verdict='disputed',
                confidence=0.3,
                contradicting_sources=[{'event_id': f['source_event']} for f in contradicting],
                claim_type='temporal',
                verification_method='temporal_contradiction_found'
            )
        elif supporting:
            avg_confidence = np.mean([f.get('confidence', 0.5) for f in supporting])
            return FactCheckResult(
                claim=claim,
                verdict='verified' if avg_confidence >= 0.8 else 'partially_verified',
                confidence=avg_confidence,
                supporting_sources=[{'event_id': f['source_event']} for f in supporting],
                claim_type='temporal',
                verification_method='temporal_match_found'
            )
        
        return FactCheckResult(
            claim=claim,
            verdict='unverified',
            confidence=0.4,
            claim_type='temporal',
            verification_method='no_temporal_matches'
        )
    
    def _check_attribution_claim(self, claim: str, context: Optional[Dict]) -> FactCheckResult:
        """Check an attribution claim (who said/did what)."""
        # Extract subject from claim
        subjects = []
        
        # Look for person names (capitalized words)
        name_pattern = r'\b([A-Z][a-z]+ (?:[A-Z][a-z]+ )?[A-Z][a-z]+)\b'
        subjects.extend(re.findall(name_pattern, claim))
        
        if not subjects and context and context.get('actors'):
            subjects = context['actors']
        
        if not subjects:
            return FactCheckResult(
                claim=claim,
                verdict='unverified',
                confidence=0.0,
                claim_type='attribution',
                verification_method='no_subject_identified'
            )
        
        # Check attribution facts
        supporting = []
        
        for subject in subjects:
            subject_facts = self.attribution_facts.get(subject.lower(), [])
            
            for fact in subject_facts:
                if self._claim_matches_fact(claim, fact):
                    supporting.append(fact)
        
        if supporting:
            avg_confidence = np.mean([f.get('confidence', 0.5) for f in supporting])
            return FactCheckResult(
                claim=claim,
                verdict='verified' if avg_confidence >= 0.8 else 'partially_verified',
                confidence=avg_confidence,
                supporting_sources=[{'event_id': f['source_event']} for f in supporting],
                claim_type='attribution',
                verification_method='attribution_verified'
            )
        
        return FactCheckResult(
            claim=claim,
            verdict='unverified',
            confidence=0.3,
            claim_type='attribution',
            verification_method='no_attribution_found'
        )
    
    def _check_general_claim(self, claim: str, context: Optional[Dict]) -> FactCheckResult:
        """Check a general claim using keyword matching."""
        # Simple keyword-based verification
        claim_words = set(claim.lower().split())
        
        best_match_score = 0.0
        best_match_event = None
        
        for event in self.knowledge_base:
            event_text = f"{event.get('title', '')} {event.get('summary', '')}".lower()
            event_words = set(event_text.split())
            
            # Calculate overlap
            overlap = len(claim_words.intersection(event_words))
            score = overlap / len(claim_words) if claim_words else 0
            
            if score > best_match_score:
                best_match_score = score
                best_match_event = event
        
        if best_match_score >= 0.5:
            confidence = min(1.0, best_match_score)
            return FactCheckResult(
                claim=claim,
                verdict='partially_verified' if confidence >= 0.6 else 'unverified',
                confidence=confidence,
                supporting_sources=[{'event_id': best_match_event.get('id')}] if best_match_event else [],
                claim_type='general',
                verification_method='keyword_matching'
            )
        
        return FactCheckResult(
            claim=claim,
            verdict='unverified',
            confidence=0.2,
            claim_type='general',
            verification_method='no_matches'
        )
    
    def _dates_compatible(self, date1: str, date2: str) -> bool:
        """Check if two dates are compatible (close enough)."""
        # Simplified date compatibility check
        if date1[:4] == date2[:4]:  # Same year
            return True
        return False
    
    def _claim_matches_fact(self, claim: str, fact: Dict) -> bool:
        """Check if claim matches a fact."""
        # Simplified matching - would use NLP in production
        claim_lower = claim.lower()
        
        # Check for key terms from fact in claim
        if fact.get('event_title'):
            title_words = set(fact['event_title'].lower().split())
            claim_words = set(claim_lower.split())
            if len(title_words.intersection(claim_words)) >= 2:
                return True
        
        return False
    
    def _claim_contradicts_fact(self, claim: str, fact: Dict) -> bool:
        """Check if claim contradicts a fact."""
        # Simplified contradiction detection
        negation_words = ['not', 'no', 'never', 'false', 'incorrect', 'denied']
        
        claim_lower = claim.lower()
        has_negation = any(word in claim_lower for word in negation_words)
        
        if has_negation and self._claim_matches_fact(claim.replace('not', '').replace('no', ''), fact):
            return True
        
        return False


class SourceVerifier:
    """
    Source verification and credibility assessment.
    
    Features:
    - Domain reputation analysis
    - Content consistency checking
    - Citation quality assessment
    - Temporal validity verification
    """
    
    def __init__(self):
        """Initialize source verifier."""
        # Domain reputation database
        self.domain_reputations = {
            # Government domains
            '.gov': 0.95,
            '.mil': 0.95,
            
            # Educational domains
            '.edu': 0.90,
            '.ac.uk': 0.90,
            
            # Reputable news organizations
            'reuters.com': 0.90,
            'apnews.com': 0.90,
            'bbc.com': 0.85,
            'npr.org': 0.85,
            'pbs.org': 0.85,
            'nytimes.com': 0.80,
            'washingtonpost.com': 0.80,
            'wsj.com': 0.80,
            'bloomberg.com': 0.80,
            'ft.com': 0.80,
            
            # Research organizations
            'brookings.edu': 0.85,
            'rand.org': 0.85,
            'pewresearch.org': 0.85,
            
            # International organizations
            '.un.org': 0.90,
            '.who.int': 0.90,
            '.worldbank.org': 0.85,
            
            # Generic
            '.org': 0.60,
            '.com': 0.50,
            '.net': 0.50,
            
            # Social media (lower credibility)
            'twitter.com': 0.30,
            'facebook.com': 0.30,
            'instagram.com': 0.25,
            'tiktok.com': 0.20,
            'reddit.com': 0.35,
            
            # Known problematic sources
            'infowars.com': 0.10,
            'breitbart.com': 0.25,
        }
        
        self.verification_stats = defaultdict(int)
    
    def verify_source(self, source_url: str, 
                     content: Optional[str] = None,
                     metadata: Optional[Dict] = None) -> SourceVerificationResult:
        """
        Verify a source's credibility.
        
        Args:
            source_url: URL of the source
            content: Optional content from the source
            metadata: Optional metadata about the source
            
        Returns:
            SourceVerificationResult with credibility assessment
        """
        self.verification_stats['total_verifications'] += 1
        
        result = SourceVerificationResult(source_url=source_url, credibility_score=0.5)
        
        # Assess domain reputation
        result.domain_reputation = self._assess_domain_reputation(source_url)
        
        # Check content consistency if provided
        if content:
            result.content_consistency = self._assess_content_consistency(content)
        
        # Assess citation quality if metadata provided
        if metadata:
            result.citation_quality = self._assess_citation_quality(metadata)
            result.temporal_validity = self._assess_temporal_validity(metadata)
        
        # Calculate overall credibility score
        scores = [result.domain_reputation]
        if result.content_consistency > 0:
            scores.append(result.content_consistency)
        if result.citation_quality > 0:
            scores.append(result.citation_quality)
        if result.temporal_validity > 0:
            scores.append(result.temporal_validity)
        
        result.credibility_score = np.mean(scores)
        
        # Identify issues
        if result.domain_reputation < 0.5:
            result.issues.append("Low domain reputation")
        if result.content_consistency > 0 and result.content_consistency < 0.5:
            result.issues.append("Content consistency concerns")
        if result.temporal_validity > 0 and result.temporal_validity < 0.5:
            result.warnings.append("Content may be outdated")
        
        # Update statistics
        if result.credibility_score >= 0.8:
            self.verification_stats['high_credibility'] += 1
        elif result.credibility_score >= 0.5:
            self.verification_stats['medium_credibility'] += 1
        else:
            self.verification_stats['low_credibility'] += 1
        
        return result
    
    def _assess_domain_reputation(self, url: str) -> float:
        """Assess reputation of the domain."""
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc
            
            # Check exact domain match
            if domain in self.domain_reputations:
                return self.domain_reputations[domain]
            
            # Check domain suffix
            for suffix, reputation in self.domain_reputations.items():
                if domain.endswith(suffix):
                    return reputation
            
            # Unknown domain - neutral score
            return 0.5
            
        except Exception as e:
            logger.warning(f"Error parsing URL {url}: {e}")
            return 0.3
    
    def _assess_content_consistency(self, content: str) -> float:
        """Assess consistency of content."""
        if not content:
            return 0.5
        
        # Check for consistency indicators
        consistency_score = 0.5
        
        # Check for citations
        if 'according to' in content.lower() or 'source:' in content.lower():
            consistency_score += 0.1
        
        # Check for dates
        if re.search(r'\b\d{4}\b', content):
            consistency_score += 0.1
        
        # Check for specific details
        if re.search(r'\b\d+\b', content):  # Numbers
            consistency_score += 0.1
        
        # Check for balanced language
        extreme_words = ['always', 'never', 'definitely', 'absolutely', 'conspiracy', 'hoax']
        if not any(word in content.lower() for word in extreme_words):
            consistency_score += 0.1
        
        return min(1.0, consistency_score)
    
    def _assess_citation_quality(self, metadata: Dict) -> float:
        """Assess quality of citations."""
        # Check for author
        if metadata.get('author'):
            return 0.7
        
        # Check for publication date
        if metadata.get('date') or metadata.get('published'):
            return 0.6
        
        return 0.4
    
    def _assess_temporal_validity(self, metadata: Dict) -> float:
        """Assess temporal validity of source."""
        # Check if source has a date
        date_str = metadata.get('date') or metadata.get('published')
        
        if not date_str:
            return 0.5  # Unknown date
        
        # Check age of source (simplified)
        current_year = datetime.now().year
        
        # Extract year from date string
        year_match = re.search(r'\b(20\d{2})\b', str(date_str))
        if year_match:
            source_year = int(year_match.group(1))
            years_old = current_year - source_year
            
            if years_old <= 1:
                return 1.0  # Very recent
            elif years_old <= 3:
                return 0.8  # Recent
            elif years_old <= 5:
                return 0.6  # Somewhat dated
            else:
                return 0.4  # Old
        
        return 0.5  # Could not determine