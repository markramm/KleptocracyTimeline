#!/usr/bin/env python3
"""
Add importance field to all timeline events.

The importance field is a 1-10 scale that helps prioritize events for display:
- 10: Constitutional crisis, existential threat to democracy
- 9: Major scandal with lasting impact, criminal convictions
- 8: Significant policy changes, major investigations
- 7: Important legal actions, regulatory changes
- 6: Notable political events, significant appointments
- 5: Standard political developments
- 4: Minor policy changes, routine appointments
- 3: Procedural actions, minor controversies
- 2: Background events, context-setting
- 1: Minor, peripheral events
"""

import yaml
import os
from pathlib import Path
from datetime import datetime
import json

# Path to timeline events
TIMELINE_DIR = Path("timeline_data/events")

def calculate_initial_importance(event):
    """
    Calculate an initial importance score based on event characteristics.
    This is a starting point that should be manually reviewed.
    """
    score = 5  # Start with a baseline
    
    # Tags that indicate higher importance
    if event.get('tags'):
        tags = event['tags']
        
        # Critical tags
        if 'constitutional-crisis' in tags:
            score = max(score, 9)
        if 'democracy-threat' in tags:
            score = max(score, 8)
        if 'insurrection' in tags or 'coup-attempt' in tags:
            score = max(score, 10)
        
        # Major scandal/criminal tags
        if 'criminal-investigation' in tags:
            score = max(score, 7)
        if 'indictment' in tags or 'conviction' in tags:
            score = max(score, 8)
        if 'major-scandal' in tags:
            score = max(score, 8)
        
        # Significant policy/legal
        if 'supreme-court' in tags:
            score = max(score, 7)
        if 'executive-order' in tags:
            score = max(score, 6)
        if 'regulatory-capture' in tags:
            score = max(score, 7)
        
        # Financial crimes
        if 'money-laundering' in tags or 'fraud' in tags:
            score = max(score, 7)
        if 'corruption' in tags:
            score = max(score, 7)
        
        # Foreign influence
        if 'foreign-influence' in tags or 'espionage' in tags:
            score = max(score, 8)
        if 'russia' in tags or 'china' in tags:
            score = min(score + 1, 10)
    
    # Monitoring status indicates current importance
    if event.get('monitoring_status') == 'active':
        score = max(score, 7)
    
    # Recent events might be more important
    if event.get('date'):
        try:
            event_date = datetime.strptime(event['date'], '%Y-%m-%d')
            days_ago = (datetime.now() - event_date).days
            if days_ago < 30:
                score = min(score + 1, 10)
            elif days_ago < 90:
                score = min(score + 0.5, 10)
        except:
            pass
    
    # More sources often indicates more significant event
    if event.get('sources'):
        if len(event['sources']) > 5:
            score = min(score + 1, 10)
        elif len(event['sources']) > 3:
            score = min(score + 0.5, 10)
    
    # Key actors indicate importance
    if event.get('actors'):
        actors = event['actors']
        key_figures = ['Donald Trump', 'Joe Biden', 'Elon Musk', 'Vladimir Putin', 
                       'Xi Jinping', 'Jeffrey Epstein', 'Supreme Court']
        for actor in actors:
            if any(key in actor for key in key_figures):
                score = min(score + 0.5, 10)
                break
    
    # Round to nearest integer
    return int(round(score))

def add_importance_field():
    """Add importance field to all events that don't have it."""
    
    if not TIMELINE_DIR.exists():
        print(f"Timeline directory not found: {TIMELINE_DIR}")
        return
    
    updated_count = 0
    already_has_count = 0
    total_count = 0
    importance_distribution = {}
    
    # Process each YAML file
    for yaml_file in sorted(TIMELINE_DIR.glob("*.yaml")):
        total_count += 1
        
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            event = yaml.safe_load(content)
        
        # Check if importance field already exists
        if 'importance' in event:
            already_has_count += 1
            importance = event['importance']
        else:
            # Calculate initial importance
            importance = calculate_initial_importance(event)
            
            # Add importance field after date (for consistent ordering)
            lines = content.split('\n')
            new_lines = []
            date_found = False
            
            for line in lines:
                new_lines.append(line)
                if line.startswith('date:') and not date_found:
                    new_lines.append(f'importance: {importance}')
                    date_found = True
            
            # If no date field found, add at the beginning after id
            if not date_found:
                new_lines = []
                for line in lines:
                    new_lines.append(line)
                    if line.startswith('id:'):
                        new_lines.append(f'importance: {importance}')
                        date_found = True
                        break
            
            # Write updated content
            with open(yaml_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
            updated_count += 1
            print(f"Added importance: {importance} to {yaml_file.name}")
        
        # Track distribution
        importance_distribution[importance] = importance_distribution.get(importance, 0) + 1
    
    # Print summary
    print(f"\n=== Summary ===")
    print(f"Total events: {total_count}")
    print(f"Updated: {updated_count}")
    print(f"Already had importance: {already_has_count}")
    
    print(f"\n=== Importance Distribution ===")
    for score in sorted(importance_distribution.keys(), reverse=True):
        count = importance_distribution[score]
        bar = '█' * (count // 5) + '▌' * ((count % 5) // 3)
        print(f"  {score:2d}: {count:3d} {bar}")
    
    # Save distribution to file for review
    with open('importance_distribution.json', 'w') as f:
        json.dump({
            'summary': {
                'total': total_count,
                'updated': updated_count,
                'already_has': already_has_count
            },
            'distribution': importance_distribution,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\nDistribution saved to importance_distribution.json")
    
    # Suggest manual review for extreme scores
    print(f"\n=== Manual Review Suggested ===")
    print(f"Events with importance >= 8 should be manually reviewed for accuracy.")
    print(f"Events with importance <= 3 might be candidates for removal or merging.")

def main():
    """Main entry point."""
    print("Adding importance field to timeline events...")
    print("=" * 50)
    
    add_importance_field()
    
    print("\n✅ Complete! Please review the importance scores and adjust as needed.")
    print("\nImportance Scale:")
    print("  10: Constitutional crisis, existential threat")
    print("   9: Major scandal with lasting impact")
    print("   8: Significant policy changes, major investigations")
    print("   7: Important legal actions, regulatory changes")
    print("   6: Notable political events")
    print("   5: Standard political developments")
    print("   4: Minor policy changes")
    print("   3: Procedural actions")
    print("   2: Background events")
    print("   1: Minor, peripheral events")

if __name__ == "__main__":
    main()