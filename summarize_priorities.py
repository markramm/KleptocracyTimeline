#!/usr/bin/env python3
import os
import json
from collections import Counter, defaultdict

def analyze_priorities():
    priorities_dir = "research_priorities"
    
    # Categories
    by_status = Counter()
    by_priority = Counter()
    by_decade = Counter()
    by_category = Counter()
    by_capture_lane = Counter()
    
    titles = []
    
    for filename in os.listdir(priorities_dir):
        if filename.endswith(".json") and filename != "PRIORITIES_SUMMARY.json":
            filepath = os.path.join(priorities_dir, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    
                    status = data.get('status', 'pending')
                    by_status[status] += 1
                    
                    priority = data.get('priority', 'unknown')
                    by_priority[priority] += 1
                    
                    decade = data.get('decade', 'unspecified')
                    by_decade[decade] += 1
                    
                    category = data.get('category', 'general')
                    by_category[category] += 1
                    
                    capture_lane = data.get('capture_lane', 'none')
                    by_capture_lane[capture_lane] += 1
                    
                    title = data.get('title', filename)
                    titles.append(title)
                    
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    print("=== REMAINING RESEARCH PRIORITIES ANALYSIS ===")
    print(f"\nTotal remaining priorities: {sum(by_status.values())}")
    
    print(f"\nBy Status:")
    for status, count in by_status.most_common():
        print(f"  {status}: {count}")
    
    print(f"\nBy Priority Level:")
    for level, count in by_priority.most_common():
        print(f"  {level}: {count}")
    
    print(f"\nBy Decade:")
    for decade, count in sorted(by_decade.items()):
        print(f"  {decade}: {count}")
    
    print(f"\nBy Category:")
    for cat, count in by_category.most_common():
        print(f"  {cat}: {count}")
    
    print(f"\nBy Capture Lane:")
    for lane, count in by_capture_lane.most_common():
        if lane != 'none':
            print(f"  {lane}: {count}")
    
    print(f"\nSample Priority Titles:")
    for title in titles[:10]:
        print(f"  • {title}")
    
    if len(titles) > 10:
        print(f"  ... and {len(titles) - 10} more")

if __name__ == "__main__":
    analyze_priorities()