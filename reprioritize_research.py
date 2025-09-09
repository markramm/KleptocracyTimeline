#!/usr/bin/env python3
"""
Reprioritize research priorities based on timeline coverage gaps analysis
"""

import json
from pathlib import Path

def analyze_and_reprioritize():
    """Analyze timeline coverage and reprioritize research priorities"""
    
    print("🔍 REPRIORITIZING RESEARCH PRIORITIES BASED ON TIMELINE COVERAGE")
    print("=" * 70)
    
    # High-value targets based on analysis:
    # - Timeline has good 1970s-early 2000s coverage (124 events)
    # - Missing detailed 1980s-1990s foundational periods  
    # - Need better corporate-financial network documentation
    # - Missing systematic intelligence privatization details
    
    high_value_priorities = [
        # Historical foundation periods with gaps
        ("RT-051-reagan-era-regulatory-capture-foundation.json", 10),
        ("RT-050-clinton-era-financial-deregulation-capture.json", 10), 
        ("RT-052-bush-sr-intelligence-privatization-acceleration.json", 10),
        ("RT-012-post-watergate-intelligence-privatization.json", 9),
        ("RT-013-powell-memorandum-institutional-capture-blueprint.json", 9),
        
        # Corporate-financial networks (underrepresented)
        ("RT-003-telecom-nsa-financial.json", 9),
        ("RT-004-enron-cheney-connection.json", 9),
        ("RT-014-oligarch-information-warfare-networks.json", 9),
        
        # Systematic infrastructure (unique mechanisms)
        ("RT-016-corporate-state-fusion-infrastructure.json", 8),
        ("RT-017-congressional-institutional-capture-mechanisms.json", 8),
        ("RT-015-systematic-intelligence-community-corruption.json", 8),
        
        # Bush Sr era (major gap period)
        ("RT-053-bush-sr-regulatory-capture-consolidation.json", 8),
        ("RT-054-bush-sr-executive-power-expansion.json", 8),
        ("RT-055-bush-sr-military-industrial-consolidation.json", 8),
        ("RT-056-bush-sr-systematic-corruption-networks.json", 8),
    ]
    
    updated_count = 0
    
    for filename, new_priority in high_value_priorities:
        priority_file = Path("research_priorities") / filename
        
        if priority_file.exists():
            try:
                with open(priority_file, 'r') as f:
                    priority_data = json.load(f)
                
                old_priority = priority_data.get('priority', 5)
                priority_data['priority'] = new_priority
                priority_data['updated_date'] = '2025-09-06'
                priority_data['reprioritization_reason'] = 'Timeline coverage gap analysis - high value for unique content'
                
                with open(priority_file, 'w') as f:
                    json.dump(priority_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ {filename}: {old_priority} → {new_priority}")
                updated_count += 1
                
            except Exception as e:
                print(f"❌ Error updating {filename}: {str(e)}")
    
    print(f"\n📊 REPRIORITIZATION COMPLETE")
    print(f"Updated {updated_count} research priorities")
    print(f"Focus areas: Historical foundations, Corporate networks, Systematic infrastructure")
    
    return updated_count

if __name__ == "__main__":
    analyze_and_reprioritize()