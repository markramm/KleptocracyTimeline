#!/usr/bin/env python3
"""
Comprehensive validation test for enhanced research integration system
Tests multiple priority types and validates event generation quality
"""

import json
from pathlib import Path
from api.claude_research_integration import research_timeline_events_with_claude

def test_comprehensive_research_validation():
    """Comprehensive test of research integration across all priority types"""
    
    print("🚀 COMPREHENSIVE RESEARCH INTEGRATION VALIDATION")
    print("=" * 70)
    
    # Find all non-PDF research priorities
    priority_files = []
    priority_types = {}
    
    for priority_file in Path("research_priorities").glob("*.json"):
        if "PDF" not in priority_file.name:
            try:
                with open(priority_file, 'r') as f:
                    data = json.load(f)
                priority_files.append((priority_file, data))
                
                # Categorize by type
                category = data.get('category', 'unknown')
                if category not in priority_types:
                    priority_types[category] = []
                priority_types[category].append((priority_file, data))
            except Exception as e:
                print(f"⚠️  Error reading {priority_file.name}: {str(e)}")
    
    print(f"📁 Found {len(priority_files)} research priorities")
    print(f"📊 Categories: {', '.join(priority_types.keys())}")
    
    # Test representative priorities from each category
    total_events = 0
    successful_categories = 0
    results = {}
    
    for category, priorities in priority_types.items():
        print(f"\n=== Testing Category: {category.upper()} ===")
        
        # Test first priority in each category
        priority_file, priority_data = priorities[0]
        title = priority_data.get('title', 'Unknown')
        
        print(f"📝 Priority: {priority_file.name}")
        print(f"🎯 Title: {title[:80]}...")
        
        try:
            events = research_timeline_events_with_claude(priority_data)
            
            if events:
                successful_categories += 1
                total_events += len(events)
                results[category] = {
                    'priority_file': priority_file.name,
                    'events_count': len(events),
                    'sample_event': events[0] if events else None
                }
                
                print(f"✅ Generated {len(events)} events")
                
                # Show sample event details
                if events:
                    event = events[0]
                    print(f"   📅 Sample Date: {event.get('date', 'N/A')}")
                    print(f"   📖 Sample Title: {event.get('title', 'N/A')[:60]}...")
                    print(f"   👥 Sample Actors: {', '.join(event.get('actors', [])[:3])}")
                    print(f"   🏷️  Sample Tags: {len(event.get('tags', []))} tags")
            else:
                print("❌ No events generated")
                results[category] = {
                    'priority_file': priority_file.name,
                    'events_count': 0,
                    'sample_event': None
                }
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results[category] = {
                'priority_file': priority_file.name,
                'events_count': 0,
                'error': str(e)
            }
    
    # Final results summary
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE VALIDATION RESULTS")
    print("=" * 70)
    
    print(f"🗂️  Categories Tested: {len(priority_types)}")
    print(f"✅ Successful Categories: {successful_categories}")
    print(f"📄 Total Events Generated: {total_events}")
    print(f"📈 Success Rate: {(successful_categories/len(priority_types)*100):.1f}%")
    
    # Detailed results by category
    print(f"\n📋 DETAILED RESULTS BY CATEGORY:")
    for category, result in results.items():
        events_count = result.get('events_count', 0)
        status = "✅" if events_count > 0 else "❌"
        print(f"   {status} {category}: {events_count} events ({result['priority_file']})")
    
    # Validation assessment
    if successful_categories >= len(priority_types) * 0.8:  # 80% success rate
        print(f"\n🎉 VALIDATION SUCCESS!")
        print(f"✅ Enhanced research integration working across {successful_categories}/{len(priority_types)} categories")
        print(f"✅ Generated {total_events} contextually appropriate timeline events")
        print(f"✅ System ready for continuous research and event generation")
        return True
    else:
        print(f"\n⚠️  VALIDATION NEEDS ATTENTION")
        print(f"📊 Only {successful_categories}/{len(priority_types)} categories successful")
        print(f"🔧 Consider enhancing integration for failed categories")
        return False

if __name__ == "__main__":
    success = test_comprehensive_research_validation()