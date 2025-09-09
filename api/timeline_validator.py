#!/usr/bin/env python3
"""
Timeline Entry Validator - Spot checks timeline entries for quality
"""
import json
import random
from pathlib import Path
from datetime import datetime
import sys

class TimelineValidator:
    def __init__(self):
        self.events_dir = Path("timeline_data/events")
        self.errors = []
        self.warnings = []
        
    def validate_entry(self, filepath):
        """Validate a single timeline entry"""
        try:
            with open(filepath, 'r') as f:
                event = json.load(f)
            
            # Required fields
            required = ['id', 'date', 'title', 'summary', 'importance', 'actors', 'tags', 'sources']
            for field in required:
                if field not in event:
                    self.errors.append(f"{filepath.name}: Missing required field '{field}'")
            
            # Date format validation
            if 'date' in event:
                try:
                    datetime.strptime(event['date'], '%Y-%m-%d')
                except ValueError:
                    self.errors.append(f"{filepath.name}: Invalid date format '{event['date']}' (expected YYYY-MM-DD)")
            
            # Importance range
            if 'importance' in event:
                if not (1 <= event['importance'] <= 10):
                    self.errors.append(f"{filepath.name}: Importance {event['importance']} out of range (1-10)")
            
            # Summary length check
            if 'summary' in event:
                if len(event['summary']) < 50:
                    self.warnings.append(f"{filepath.name}: Summary very short ({len(event['summary'])} chars)")
                elif len(event['summary']) > 1000:
                    self.warnings.append(f"{filepath.name}: Summary very long ({len(event['summary'])} chars)")
            
            # Source validation
            if 'sources' in event:
                if len(event['sources']) == 0:
                    self.errors.append(f"{filepath.name}: No sources provided")
                for i, source in enumerate(event['sources']):
                    if 'title' not in source:
                        self.errors.append(f"{filepath.name}: Source {i+1} missing title")
                    if 'url' not in source and 'outlet' not in source:
                        self.warnings.append(f"{filepath.name}: Source {i+1} has no URL or outlet")
            
            # Actors validation
            if 'actors' in event:
                if len(event['actors']) == 0:
                    self.warnings.append(f"{filepath.name}: No actors listed")
            
            # Tags validation
            if 'tags' in event:
                if len(event['tags']) == 0:
                    self.warnings.append(f"{filepath.name}: No tags provided")
            
            # ID-filename consistency
            if 'id' in event and 'date' in event:
                expected_filename = f"{event['date']}--{event['id'].split('--')[1]}.json"
                if filepath.name != expected_filename:
                    self.warnings.append(f"{filepath.name}: Filename doesn't match ID pattern")
            
            return True
            
        except json.JSONDecodeError as e:
            self.errors.append(f"{filepath.name}: Invalid JSON - {e}")
            return False
        except Exception as e:
            self.errors.append(f"{filepath.name}: Unexpected error - {e}")
            return False
    
    def spot_check(self, sample_size=10):
        """Randomly sample and validate entries"""
        all_events = list(self.events_dir.glob("*.json"))
        
        if len(all_events) == 0:
            print("❌ No events found in timeline_data/events/")
            return
        
        sample_size = min(sample_size, len(all_events))
        sample = random.sample(all_events, sample_size)
        
        print(f"🔍 Validating {sample_size} random timeline entries...")
        print(f"   Total entries: {len(all_events)}")
        print()
        
        valid_count = 0
        for filepath in sample:
            if self.validate_entry(filepath):
                valid_count += 1
                print(f"✅ {filepath.name}")
            else:
                print(f"❌ {filepath.name}")
        
        print(f"\n📊 Validation Summary:")
        print(f"   Valid: {valid_count}/{sample_size}")
        
        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors[:10]:  # Show first 10 errors
                print(f"   - {error}")
            if len(self.errors) > 10:
                print(f"   ... and {len(self.errors) - 10} more")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Show first 10 warnings
                print(f"   - {warning}")
            if len(self.warnings) > 10:
                print(f"   ... and {len(self.warnings) - 10} more")
        
        return valid_count == sample_size

def main():
    validator = TimelineValidator()
    
    # Check command line args for sample size
    sample_size = 10
    if len(sys.argv) > 1:
        try:
            sample_size = int(sys.argv[1])
        except ValueError:
            print(f"Invalid sample size: {sys.argv[1]}, using default: 10")
    
    success = validator.spot_check(sample_size)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()