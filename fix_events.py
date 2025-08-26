#!/usr/bin/env python3
import os
import yaml
from pathlib import Path

# List of events that need fixing
events_to_fix = [
    "2009-04-13--peter-thiel-anti-democracy-essay.yaml",
    "2011-01-01--thiel-meets-vance-yale.yaml",
    "2016-01-01--vance-joins-mithril-capital.yaml",
    "2016-05-01--roger-stone-russian-national-meeting-clinton-dirt.yaml",
    "2019-01-01--thiel-funds-narya-capital.yaml",
    "2022-04-01--thiel-funds-vance-senate.yaml",
    "2022-07-01--roger-stone-drake-ventures-tax-fraud-settlement.yaml",
    "2024-07-15--vance-vp-nomination.yaml",
    "2025-01-20--howard-lutnick-600-million-tether-conflict.yaml",
    "2025-01-20--rfk-jr-11-million-anti-vaccine-profits.yaml",
    "2025-01-20--susie-wiles-42-corporate-clients-chief-of-staff.yaml",
    "2025-01-21--pam-bondi-shuts-down-kleptocapture-unit.yaml",
    "2025-01-22--kelly-loeffler-insider-trading-sba.yaml",
    "2025-01-23--doug-burgum-oil-leases-interior-secretary.yaml",
    "2025-01-24--michael-waltz-92-million-war-profits.yaml",
    "2025-01-25--tulsi-gabbard-assad-meeting-dni.yaml",
    "2025-01-26--kristi-noem-80k-dark-money-homeland.yaml",
    "2025-02-01--doug-collins-cuts-72000-va-jobs.yaml",
    "2025-02-10--lee-zeldin-cuts-epa-65-percent.yaml",
    "2025-02-15--federal-employees-154000-administrative-leave.yaml",
    "2025-03-15--snap-benefits-40-million-americans-cut.yaml",
    "2025-05-29--trump-federal-employee-loyalty-tests.yaml",
    "2025-08-06--brazil-50-percent-tariff-bolsonaro.yaml",
    "2025-08-13--trump-revokes-competition-order.yaml",
    "2025-08-18--gsa-ai-procurement-privatization.yaml",
    "2025-08-19--nexstar-tegna-media-merger.yaml",
    "2025-08-20--us-sanctions-icc-judges.yaml",
    "2025-08-25--trump-fires-fed-governor-cook.yaml",
    "2025-08-25--trump-national-guard-specialized-units.yaml",
    "2025-08-27--india-50-percent-tariff-russian-oil.yaml",
    "2025-03-01--federal-workforce-mass-firings-62000.yaml",
    "2025-11-04--california-special-election-redistricting-response.yaml"
]

events_dir = Path("/Users/markr/kleptocracy-timeline/timeline_data/events")

for event_file in events_to_fix:
    file_path = events_dir / event_file
    if not file_path.exists():
        print(f"File not found: {event_file}")
        continue
    
    try:
        # Read the event file
        with open(file_path, 'r') as f:
            content = f.read()
            data = yaml.safe_load(content)
        
        # Extract event ID from filename
        event_id = event_file.replace('.yaml', '')
        
        # Add missing fields
        if 'id' not in data:
            data['id'] = event_id
        
        if 'summary' not in data and 'description' in data:
            # Create a summary from the first 150 chars of description
            desc = data['description']
            if len(desc) > 150:
                summary = desc[:147] + "..."
            else:
                summary = desc
            data['summary'] = summary
        
        # Ensure proper field ordering
        ordered_data = {}
        field_order = ['id', 'date', 'title', 'summary', 'description', 'importance', 
                      'tags', 'actors', 'capture_lane', 'status', 'sources', 
                      'connections', 'patterns', 'notes', 'location']
        
        for field in field_order:
            if field in data:
                ordered_data[field] = data[field]
        
        # Add any remaining fields
        for field in data:
            if field not in ordered_data:
                ordered_data[field] = data[field]
        
        # Write back to file
        with open(file_path, 'w') as f:
            yaml.dump(ordered_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"✓ Fixed: {event_file}")
        
    except Exception as e:
        print(f"✗ Error fixing {event_file}: {e}")

print("\nDone!")