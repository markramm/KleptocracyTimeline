#!/usr/bin/env python3
"""
Add capture_lanes field to existing timeline events based on their tags
"""

import os
import yaml
from typing import List, Dict, Set

# Tag to Capture Lane mapping
TAG_TO_LANE_MAPPING = {
    # Executive Power & Emergency Authority
    'executive-order': 'Executive Power & Emergency Authority',
    'emergency-powers': 'Executive Power & Emergency Authority', 
    'constitutional-crisis': 'Executive Power & Emergency Authority',
    'presidential-authority': 'Executive Power & Emergency Authority',
    'national-emergency': 'Executive Power & Emergency Authority',
    'military-deployment': 'Executive Power & Emergency Authority',
    'martial-law': 'Executive Power & Emergency Authority',
    'emergency-declarations': 'Executive Power & Emergency Authority',
    'domestic-troops': 'Executive Power & Emergency Authority',
    
    # Judicial Capture & Corruption
    'judicial-capture': 'Judicial Capture & Corruption',
    'supreme-court': 'Judicial Capture & Corruption',
    'court-defiance': 'Judicial Capture & Corruption',
    'judicial-independence': 'Judicial Capture & Corruption',
    'judicial-threats': 'Judicial Capture & Corruption',
    'federal-judges': 'Judicial Capture & Corruption',
    'scotus': 'Judicial Capture & Corruption',
    'courts': 'Judicial Capture & Corruption',
    
    # Financial Corruption & Kleptocracy
    'kleptocracy': 'Financial Corruption & Kleptocracy',
    'conflicts-of-interest': 'Financial Corruption & Kleptocracy',
    'money-laundering': 'Financial Corruption & Kleptocracy',
    'corruption': 'Financial Corruption & Kleptocracy',
    'ethics-violations': 'Financial Corruption & Kleptocracy',
    'foreign-payments': 'Financial Corruption & Kleptocracy',
    'tariff-exemptions': 'Financial Corruption & Kleptocracy',
    'cryptocurrency': 'Financial Corruption & Kleptocracy',
    'memecoin': 'Financial Corruption & Kleptocracy',
    'crypto-regulation': 'Financial Corruption & Kleptocracy',
    'digital-assets': 'Financial Corruption & Kleptocracy',
    'blockchain': 'Financial Corruption & Kleptocracy',
    
    # Foreign Influence Operations
    'foreign-influence': 'Foreign Influence Operations',
    'russian-interference': 'Foreign Influence Operations',
    'chinese-investment': 'Foreign Influence Operations',
    'mossad-operations': 'Foreign Influence Operations',
    'sanctions-evasion': 'Foreign Influence Operations',
    'russian-oligarchs': 'Foreign Influence Operations',
    'foreign-governments': 'Foreign Influence Operations',
    
    # Federal Workforce Capture
    'federal-workforce': 'Federal Workforce Capture',
    'workforce-reduction': 'Federal Workforce Capture',
    'schedule-f': 'Federal Workforce Capture',
    'loyalty-tests': 'Federal Workforce Capture',
    'inspector-general': 'Federal Workforce Capture',
    'mass-firings': 'Federal Workforce Capture',
    'doge': 'Federal Workforce Capture',
    
    # Corporate Capture & Regulatory Breakdown
    'regulatory-capture': 'Corporate Capture & Regulatory Breakdown',
    'deregulation': 'Corporate Capture & Regulatory Breakdown',
    'epa-rollback': 'Corporate Capture & Regulatory Breakdown',
    'enforcement-pause': 'Corporate Capture & Regulatory Breakdown',
    'agency-capture': 'Corporate Capture & Regulatory Breakdown',
    'fcpa-pause': 'Corporate Capture & Regulatory Breakdown',
    'corporate-capture': 'Corporate Capture & Regulatory Breakdown',
    'lobbying': 'Corporate Capture & Regulatory Breakdown',
    'dark-money': 'Corporate Capture & Regulatory Breakdown',
    'industry-influence': 'Corporate Capture & Regulatory Breakdown',
    'corporate-welfare': 'Corporate Capture & Regulatory Breakdown',
    'monopoly-power': 'Corporate Capture & Regulatory Breakdown',
    
    # Law Enforcement Weaponization
    'fbi-weaponization': 'Law Enforcement Weaponization',
    'doj-politicization': 'Law Enforcement Weaponization',
    'police-state': 'Law Enforcement Weaponization',
    'political-retaliation': 'Law Enforcement Weaponization',
    'surveillance': 'Law Enforcement Weaponization',
    'investigations': 'Law Enforcement Weaponization',
    'democratic-surveillance': 'Law Enforcement Weaponization',
    'political-prisoner': 'Law Enforcement Weaponization',
    
    # Election System Attack
    'elections': 'Election System Attack',
    'voting-rights': 'Election System Attack',
    'redistricting': 'Election System Attack',
    'gerrymandering': 'Election System Attack',
    'election-interference': 'Election System Attack',
    'voter-suppression': 'Election System Attack',
    'quorum-break': 'Election System Attack',
    'trump-interference': 'Election System Attack',
    
    # Information & Media Control
    'media-capture': 'Information & Media Control',
    'press-freedom': 'Information & Media Control',
    'fact-checking': 'Information & Media Control',
    'social-media': 'Information & Media Control',
    'platform-policy': 'Information & Media Control',
    'journalist-harassment': 'Information & Media Control',
    'meta-policy': 'Information & Media Control',
    'x-twitter': 'Information & Media Control',
    'platform-manipulation': 'Information & Media Control',
    'content-moderation': 'Information & Media Control',
    'algorithmic-bias': 'Information & Media Control',
    'tech-capture': 'Information & Media Control',
    
    # Constitutional & Democratic Breakdown
    'democratic-norms': 'Constitutional & Democratic Breakdown',
    'institutional-capture': 'Constitutional & Democratic Breakdown',
    'oversight-elimination': 'Constitutional & Democratic Breakdown',
    'checks-and-balances': 'Constitutional & Democratic Breakdown',
    'separation-of-powers': 'Constitutional & Democratic Breakdown',
    'civil-rights': 'Constitutional & Democratic Breakdown',
    'free-speech': 'Constitutional & Democratic Breakdown',
    'assembly-rights': 'Constitutional & Democratic Breakdown',
    'due-process': 'Constitutional & Democratic Breakdown',
    'constitutional-rights': 'Constitutional & Democratic Breakdown',
    'democracy-erosion': 'Constitutional & Democratic Breakdown',
    'democracy-breakdown': 'Constitutional & Democratic Breakdown',
    'authoritarian-tactics': 'Constitutional & Democratic Breakdown',
    'authoritarian-governance': 'Constitutional & Democratic Breakdown',
    
    # Epstein Network & Kompromat
    'epstein-network': 'Epstein Network & Kompromat',
    'epstein-files': 'Epstein Network & Kompromat',
    'kompromat': 'Epstein Network & Kompromat',
    'maxwell-testimony': 'Epstein Network & Kompromat',
    'client-list': 'Epstein Network & Kompromat',
    'blackmail-operations': 'Epstein Network & Kompromat',
    'kompromat-allegations': 'Epstein Network & Kompromat',
    'cover-up-accusations': 'Epstein Network & Kompromat',
    'doj-cover-up': 'Epstein Network & Kompromat',
    'victim-silencing': 'Epstein Network & Kompromat',
    'evidence-contradiction': 'Epstein Network & Kompromat',
    'justice-obstruction': 'Epstein Network & Kompromat',
    'doj-reversal': 'Epstein Network & Kompromat',
    'bondi-contradiction': 'Epstein Network & Kompromat',
    'client-list-denial': 'Epstein Network & Kompromat',
    'trump-exoneration': 'Epstein Network & Kompromat',
    'blanche-interview': 'Epstein Network & Kompromat',
    'limited-immunity': 'Epstein Network & Kompromat',
    'credibility-concerns': 'Epstein Network & Kompromat',
    
    # Immigration & Border Militarization
    'border-emergency': 'Immigration & Border Militarization',
    'immigration': 'Immigration & Border Militarization',
    'ice-operations': 'Immigration & Border Militarization',
    'detention': 'Immigration & Border Militarization',
    'militarization': 'Immigration & Border Militarization',
    'family-separation': 'Immigration & Border Militarization',
    
    # International Democracy Impact  
    'democracy-ratings': 'International Democracy Impact',
    'international-relations': 'International Democracy Impact',
    'authoritarian-alignment': 'International Democracy Impact',
    'democracy-export': 'International Democracy Impact',
    'global-influence': 'International Democracy Impact',
    
    # Additional common tags that map to multiple lanes
    'project-2025': 'Executive Power & Emergency Authority',  # Primary mapping
    'trump-loyalist': 'Federal Workforce Capture',
    'authoritarian-blueprint': 'Constitutional & Democratic Breakdown',
    'legislative-bypass': 'Executive Power & Emergency Authority',
    'heritage-foundation': 'Corporate Capture & Regulatory Breakdown',
    'rule-of-law': 'Constitutional & Democratic Breakdown',
    'judicial-authority': 'Judicial Capture & Corruption',
    'federal-takeover': 'Executive Power & Emergency Authority',
    'loyalist-appointment': 'Federal Workforce Capture',
    'judicial-intervention': 'Judicial Capture & Corruption',
    'dc-autonomy': 'Constitutional & Democratic Breakdown',
    'emergency-powers': 'Executive Power & Emergency Authority',
    'musk-trump-feud': 'Financial Corruption & Kleptocracy',
    'oligarch-conflict': 'Financial Corruption & Kleptocracy',
}


def get_capture_lanes_for_tags(tags: List[str]) -> List[str]:
    """Map tags to capture lanes"""
    capture_lanes = set()
    
    for tag in tags:
        if tag in TAG_TO_LANE_MAPPING:
            capture_lanes.add(TAG_TO_LANE_MAPPING[tag])
            
    return sorted(list(capture_lanes))


def add_capture_lanes_to_file(filepath: str) -> bool:
    """Add capture_lanes field to a single YAML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse YAML while preserving order and comments
        data = yaml.safe_load(content)
        
        if not data or 'tags' not in data or not data['tags']:
            print(f"Skipping {filepath}: No tags found")
            return False
            
        # Skip if capture_lanes already exists
        if 'capture_lanes' in data:
            print(f"Skipping {filepath}: capture_lanes already exists")
            return False
            
        # Get capture lanes for this event's tags
        capture_lanes = get_capture_lanes_for_tags(data['tags'])
        
        if not capture_lanes:
            print(f"Warning: No capture lanes mapped for {filepath}")
            return False
            
        # Insert capture_lanes after tags in the content
        lines = content.split('\n')
        new_lines = []
        tags_section_found = False
        in_tags_section = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if we're at the tags section
            if line.strip().startswith('tags:'):
                tags_section_found = True
                in_tags_section = True
                new_lines.append(line)
                
                # Add all tag lines
                i += 1
                while i < len(lines) and (lines[i].startswith('- ') or lines[i].strip() == ''):
                    new_lines.append(lines[i])
                    i += 1
                    
                # Add capture_lanes section
                new_lines.append('capture_lanes:')
                for lane in capture_lanes:
                    new_lines.append(f'- {lane}')
                    
                # Continue with the next line (don't increment i, we're already there)
                continue
            else:
                new_lines.append(line)
                i += 1
                
        if not tags_section_found:
            print(f"Warning: No tags section found in {filepath}")
            return False
            
        # Write back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
            
        print(f"✅ Added {len(capture_lanes)} capture lanes to {os.path.basename(filepath)}: {', '.join(capture_lanes)}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return False


def main():
    """Add capture_lanes to all timeline events"""
    events_dir = 'events'
    
    if not os.path.exists(events_dir):
        print(f"Events directory not found: {events_dir}")
        return
        
    files = sorted([f for f in os.listdir(events_dir) if f.endswith('.yaml')])
    
    print(f"Processing {len(files)} YAML files...")
    print("=" * 60)
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for filename in files:
        filepath = os.path.join(events_dir, filename)
        result = add_capture_lanes_to_file(filepath)
        
        if result:
            success_count += 1
        elif "already exists" in str(result):
            skip_count += 1
        else:
            error_count += 1
            
    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"  ✅ Successfully updated: {success_count}")
    print(f"  ⏭️  Skipped (already had capture_lanes): {skip_count}")
    print(f"  ❌ Errors: {error_count}")


if __name__ == "__main__":
    main()