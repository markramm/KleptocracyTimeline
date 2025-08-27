#!/usr/bin/env python3
"""
Standardize actor names across all timeline events to fix duplicates and inconsistencies.
"""
import yaml
from pathlib import Path
import sys

# Define standardization mappings
ACTOR_MAPPINGS = {
    # Trump-related
    'donald-trump': 'Donald Trump',
    'Trump administration': 'Trump Administration',
    'trump-administration': 'Trump Administration',
    'trump administration': 'Trump Administration',
    'Donald Trump, Jr.': 'Donald Trump Jr.',
    'Donald Trump, Jr': 'Donald Trump Jr.',
    'donald trump jr': 'Donald Trump Jr.',
    'donald trump jr.': 'Donald Trump Jr.',
    'JD vance': 'JD Vance',
    'J.D. Vance': 'JD Vance',
    'j.d. vance': 'JD Vance',
    
    # Organizations
    'trump Organization': 'Trump Organization',
    'trump organization': 'Trump Organization',
    'Trump Campaign': 'Trump Campaign',
    'trump campaign': 'Trump Campaign',
    'Trump Media & technology Group': 'Trump Media & Technology Group',
    'Trump media & Technology Group': 'Trump Media & Technology Group',
    
    # Government entities
    'Us Government': 'US Government',
    'us government': 'US Government',
    'U.S. Government': 'US Government',
    'Us Department Of Justice': 'US Department of Justice',
    'us department of justice': 'US Department of Justice',
    'U.S. Department of Justice': 'US Department of Justice',
    'Us Department Of State': 'US Department of State',
    'us department of state': 'US Department of State',
    'U.S. Department of State': 'US Department of State',
    'Department of justice': 'US Department of Justice',
    'Department Of Justice': 'US Department of Justice',
    'department of justice': 'US Department of Justice',
    'Supreme court': 'US Supreme Court',
    'supreme court': 'US Supreme Court',
    'U.S. Supreme Court': 'US Supreme Court',
    
    # Other common duplicates
    'Steve bannon': 'Steve Bannon',
    'steve bannon': 'Steve Bannon',
    'Roger stone': 'Roger Stone',
    'roger stone': 'Roger Stone',
    'Paul manafort': 'Paul Manafort',
    'paul manafort': 'Paul Manafort',
    'Michael flynn': 'Michael Flynn',
    'michael flynn': 'Michael Flynn',
    'Rudy giuliani': 'Rudy Giuliani',
    'rudy giuliani': 'Rudy Giuliani',
    'Bill barr': 'Bill Barr',
    'bill barr': 'Bill Barr',
    'William Barr': 'Bill Barr',
    'william barr': 'Bill Barr',
    'Mike pence': 'Mike Pence',
    'mike pence': 'Mike Pence',
    'Jared kushner': 'Jared Kushner',
    'jared kushner': 'Jared Kushner',
    'Ivanka trump': 'Ivanka Trump',
    'ivanka trump': 'Ivanka Trump',
    'Eric trump': 'Eric Trump',
    'eric trump': 'Eric Trump',
    'Melania trump': 'Melania Trump',
    'melania trump': 'Melania Trump',
    
    # Additional entities
    'Russian Government': 'Russian Government',
    'russian government': 'Russian Government',
    'Russian government': 'Russian Government',
    'Saudi government': 'Saudi Government',
    'saudi government': 'Saudi Government',
    'Saudi Arabia': 'Saudi Arabia',
    'saudi arabia': 'Saudi Arabia',
    
    # Fix hyphenated versions
    'cantor-fitzgerald': 'Cantor Fitzgerald',
    'cfpb': 'CFPB',
    'commerce-department': 'Commerce Department',
    'Commerce department': 'Commerce Department',
    'dark-money-groups': 'Dark money groups',
    'department-of-homeland-security': 'Department of Homeland Security',
    'department-of-justice': 'Department of Justice',
    'department-of-labor': 'Department of Labor',
    'elizabeth-warren': 'Elizabeth Warren',
    'environmental-protection-agency': 'Environmental Protection Agency',
    'epa': 'EPA',
    'fbi': 'FBI',
    'Federal Agencies': 'Federal agencies',
    'federal-employees': 'Federal employees',
    'Federal Law Enforcement': 'Federal law enforcement',
    'general-services-administration': 'General Services Administration',
    'trump-organization': 'Trump Organization',
    'trump-media': 'Trump Media & Technology Group',
    'Donald Trump Jr': 'Donald Trump Jr.',
    'Trump campaign': 'Trump Campaign',
}

def standardize_actors(actors_list):
    """Standardize a list of actors using the mapping."""
    if not actors_list or not isinstance(actors_list, list):
        return actors_list
    
    standardized = []
    for actor in actors_list:
        if not actor or not isinstance(actor, str):
            standardized.append(actor)
            continue
            
        # Check for exact match in mapping
        if actor in ACTOR_MAPPINGS:
            standardized.append(ACTOR_MAPPINGS[actor])
        else:
            standardized.append(actor)
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for actor in standardized:
        if actor not in seen:
            seen.add(actor)
            unique.append(actor)
    
    return unique

def process_file(yaml_file):
    """Process a single YAML file to standardize actors."""
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            event = yaml.safe_load(content)
        
        if not event or not isinstance(event, dict):
            return False
        
        # Check if file has actors field
        if 'actors' not in event:
            return False
        
        original_actors = event['actors']
        standardized = standardize_actors(original_actors)
        
        # Check if anything changed
        if original_actors == standardized:
            return False
        
        # Update the actors
        event['actors'] = standardized
        
        # Write back to file
        with open(yaml_file, 'w', encoding='utf-8') as f:
            yaml.dump(event, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        return True
        
    except Exception as e:
        print(f"Error processing {yaml_file}: {e}")
        return False

def main():
    events_dir = Path('events')
    
    if not events_dir.exists():
        print("Error: events directory not found. Run from timeline_data directory.")
        sys.exit(1)
    
    files_modified = 0
    files_processed = 0
    
    for yaml_file in sorted(events_dir.glob('*.yaml')):
        files_processed += 1
        if process_file(yaml_file):
            files_modified += 1
            print(f"Updated: {yaml_file.name}")
    
    print(f"\n{'=' * 60}")
    print(f"Processed {files_processed} files")
    print(f"Modified {files_modified} files")
    print(f"{'=' * 60}")
    
    if files_modified > 0:
        print("\n✅ Actor names standardized successfully!")
        print("Run 'python3 validate_yaml.py' to verify all files are still valid.")
    else:
        print("\n✅ No changes needed - all actors already standardized.")

if __name__ == '__main__':
    main()