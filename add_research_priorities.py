#!/usr/bin/env python3
"""
Add research priorities to the research monitor system
Based on the comprehensive research priorities document
"""

import json
import os
from datetime import datetime
import hashlib

# Base path for research priorities
PRIORITIES_PATH = "research_priorities"

def create_priority(title, description, priority_level, tags, capture_lane=None, decade=None):
    """Create a research priority JSON object"""
    priority_id = f"RT-{hashlib.md5(title.encode()).hexdigest()[:8].upper()}"
    
    return {
        "id": priority_id,
        "title": title,
        "description": description,
        "priority": priority_level,
        "tags": tags,
        "capture_lane": capture_lane,
        "decade": decade,
        "created": datetime.now().isoformat(),
        "status": "pending",
        "category": "capture_research"
    }

def save_priority(priority):
    """Save priority to file system"""
    os.makedirs(PRIORITIES_PATH, exist_ok=True)
    filename = f"{priority['id']}-{priority['title'].lower().replace(' ', '-')[:50]}.json"
    filepath = os.path.join(PRIORITIES_PATH, filename)
    
    with open(filepath, 'w') as f:
        json.dump(priority, f, indent=2)
    
    print(f"Created: {filepath}")
    return filepath

# Research priorities organized by decade and capture lane
priorities_data = [
    # 1970s Priorities
    {
        "title": "SEC Revolving Door 1970s",
        "description": "Document revolving door between Wall Street and SEC leadership in 1970s, tracking personnel movements and regulatory decisions",
        "priority_level": "high",
        "tags": ["regulatory_capture", "sec", "wall_street", "revolving_door"],
        "capture_lane": "regulatory",
        "decade": "1970s"
    },
    {
        "title": "Powell Memo Judicial Implementation",
        "description": "Track judicial appointments and law school funding following 1971 Powell Memo blueprint for corporate capture",
        "priority_level": "critical",
        "tags": ["powell_memo", "judicial_capture", "corporate_power"],
        "capture_lane": "judicial",
        "decade": "1970s"
    },
    {
        "title": "ALEC Formation 1973",
        "description": "Document American Legislative Exchange Council formation and early model legislation pipeline establishment",
        "priority_level": "high",
        "tags": ["alec", "legislative_capture", "model_legislation"],
        "capture_lane": "legislative",
        "decade": "1970s"
    },
    {
        "title": "Heritage Foundation Launch 1973",
        "description": "Investigate Heritage Foundation founding and early think tank proliferation strategy for narrative control",
        "priority_level": "high",
        "tags": ["heritage_foundation", "think_tanks", "media_capture"],
        "capture_lane": "media",
        "decade": "1970s"
    },
    {
        "title": "Church Committee CIA Operations",
        "description": "Document Church Committee findings on illegal CIA domestic operations and intelligence community abuse",
        "priority_level": "critical",
        "tags": ["church_committee", "cia", "intelligence_capture"],
        "capture_lane": "intelligence",
        "decade": "1970s"
    },
    
    # 1980s Priorities
    {
        "title": "S&L Deregulation Crisis",
        "description": "Document Garn-St. Germain Act (1982) and subsequent Savings & Loan crisis as regulatory capture case study",
        "priority_level": "high",
        "tags": ["s&l_crisis", "deregulation", "financial_capture"],
        "capture_lane": "regulatory",
        "decade": "1980s"
    },
    {
        "title": "Federalist Society Pipeline",
        "description": "Map Federalist Society expansion and conservative judge pipeline establishment in 1980s",
        "priority_level": "critical",
        "tags": ["federalist_society", "judicial_capture", "conservative_judiciary"],
        "capture_lane": "judicial",
        "decade": "1980s"
    },
    {
        "title": "K Street Lobbying Boom",
        "description": "Document exponential growth of K Street lobbying industry and corporate influence infrastructure",
        "priority_level": "high",
        "tags": ["k_street", "lobbying", "corporate_influence"],
        "capture_lane": "legislative",
        "decade": "1980s"
    },
    {
        "title": "Murdoch Media Empire Expansion",
        "description": "Track Rupert Murdoch's Fox acquisition, citizenship change, and media consolidation strategy",
        "priority_level": "high",
        "tags": ["murdoch", "fox", "media_consolidation"],
        "capture_lane": "media",
        "decade": "1980s"
    },
    {
        "title": "Corporate PAC Explosion Post-Buckley",
        "description": "Document corporate PAC proliferation following Buckley v. Valeo implementation",
        "priority_level": "high",
        "tags": ["citizens_united_precursor", "campaign_finance", "corporate_pacs"],
        "capture_lane": "electoral",
        "decade": "1980s"
    },
    
    # 1990s Priorities
    {
        "title": "Glass-Steagall Erosion Campaign",
        "description": "Track banking lobby pressure campaign to erode and eventually repeal Glass-Steagall Act",
        "priority_level": "critical",
        "tags": ["glass_steagall", "banking_deregulation", "financial_crisis_setup"],
        "capture_lane": "regulatory",
        "decade": "1990s"
    },
    {
        "title": "Gingrich K Street Project",
        "description": "Document Gingrich Revolution (1994) and K Street Project for systematic legislative capture",
        "priority_level": "high",
        "tags": ["gingrich", "k_street_project", "republican_revolution"],
        "capture_lane": "legislative",
        "decade": "1990s"
    },
    {
        "title": "Fox News Partisan Media Model",
        "description": "Analyze Fox News 1996 launch and establishment of partisan cable news model",
        "priority_level": "critical",
        "tags": ["fox_news", "roger_ailes", "partisan_media"],
        "capture_lane": "media",
        "decade": "1990s"
    },
    {
        "title": "Blackwater PMC Founding",
        "description": "Document Blackwater founding (1997) and private military contractor emergence",
        "priority_level": "high",
        "tags": ["blackwater", "pmc", "military_privatization"],
        "capture_lane": "intelligence",
        "decade": "1990s"
    },
    {
        "title": "Derivatives Deregulation Enron Loophole",
        "description": "Track commodity futures deregulation and creation of 'Enron loophole' for unregulated derivatives",
        "priority_level": "critical",
        "tags": ["derivatives", "enron", "financial_deregulation"],
        "capture_lane": "financial",
        "decade": "1990s"
    },
    
    # 2000s Priorities
    {
        "title": "Bush v Gore Judicial Coup",
        "description": "Analyze Bush v. Gore (2000) as judicial coup precedent for electoral manipulation",
        "priority_level": "critical",
        "tags": ["bush_v_gore", "supreme_court", "electoral_manipulation"],
        "capture_lane": "judicial",
        "decade": "2000s"
    },
    {
        "title": "Cheney Energy Task Force",
        "description": "Investigate Cheney's secret energy industry meetings and regulatory capture blueprint",
        "priority_level": "high",
        "tags": ["cheney", "energy_task_force", "oil_industry"],
        "capture_lane": "regulatory",
        "decade": "2000s"
    },
    {
        "title": "Iraq War Media Complicity",
        "description": "Document media complicity in Iraq War WMD propaganda and manufactured consent",
        "priority_level": "critical",
        "tags": ["iraq_war", "wmd_lies", "media_manipulation"],
        "capture_lane": "media",
        "decade": "2000s"
    },
    {
        "title": "NSA Silicon Valley Partnerships",
        "description": "Map NSA partnerships with Silicon Valley for mass surveillance infrastructure",
        "priority_level": "critical",
        "tags": ["nsa", "prism", "tech_surveillance"],
        "capture_lane": "intelligence",
        "decade": "2000s"
    },
    {
        "title": "Subprime Regulatory Capture",
        "description": "Document regulatory capture enabling subprime mortgage crisis and 2008 financial collapse",
        "priority_level": "critical",
        "tags": ["subprime_crisis", "2008_crash", "regulatory_failure"],
        "capture_lane": "financial",
        "decade": "2000s"
    },
    
    # 2010s Priorities
    {
        "title": "Citizens United Corporate Spending",
        "description": "Track Citizens United (2010) implementation and unlimited corporate political spending explosion",
        "priority_level": "critical",
        "tags": ["citizens_united", "dark_money", "corporate_speech"],
        "capture_lane": "judicial",
        "decade": "2010s"
    },
    {
        "title": "Tea Party Koch Astroturf",
        "description": "Document Koch network activation and Tea Party astroturfing operation",
        "priority_level": "high",
        "tags": ["koch_network", "tea_party", "astroturfing"],
        "capture_lane": "legislative",
        "decade": "2010s"
    },
    {
        "title": "Cambridge Analytica Facebook",
        "description": "Investigate Cambridge Analytica scandal and Facebook electoral manipulation infrastructure",
        "priority_level": "critical",
        "tags": ["cambridge_analytica", "facebook", "data_manipulation"],
        "capture_lane": "electoral",
        "decade": "2010s"
    },
    {
        "title": "Snowden Mass Surveillance Revelations",
        "description": "Document Snowden revelations on mass surveillance and intelligence community overreach",
        "priority_level": "critical",
        "tags": ["snowden", "mass_surveillance", "nsa"],
        "capture_lane": "intelligence",
        "decade": "2010s"
    },
    {
        "title": "Private Equity Media Destruction",
        "description": "Track private equity acquisition and gutting of local newspapers and media outlets",
        "priority_level": "high",
        "tags": ["private_equity", "local_news", "media_consolidation"],
        "capture_lane": "media",
        "decade": "2010s"
    },
    
    # 2020s Current Priorities
    {
        "title": "Supreme Court Ethics Scandals",
        "description": "Document Thomas-Crow revelations and systematic Supreme Court ethics violations",
        "priority_level": "critical",
        "tags": ["clarence_thomas", "harlan_crow", "scotus_corruption"],
        "capture_lane": "judicial",
        "decade": "2020s"
    },
    {
        "title": "Crypto Regulatory Self-Writing",
        "description": "Track cryptocurrency industry writing own regulations and regulatory capture",
        "priority_level": "high",
        "tags": ["crypto", "self_regulation", "financial_capture"],
        "capture_lane": "regulatory",
        "decade": "2020s"
    },
    {
        "title": "Congressional Insider Trading",
        "description": "Document systematic congressional insider trading and stock manipulation",
        "priority_level": "high",
        "tags": ["congress", "insider_trading", "corruption"],
        "capture_lane": "legislative",
        "decade": "2020s"
    },
    {
        "title": "Twitter X Political Weaponization",
        "description": "Analyze Twitter/X transformation into political weapon under Musk ownership",
        "priority_level": "high",
        "tags": ["twitter", "elon_musk", "platform_manipulation"],
        "capture_lane": "media",
        "decade": "2020s"
    },
    {
        "title": "Election Denial Infrastructure",
        "description": "Map Big Lie infrastructure and election denial institutionalization efforts",
        "priority_level": "critical",
        "tags": ["big_lie", "election_denial", "democracy_threat"],
        "capture_lane": "electoral",
        "decade": "2020s"
    },
    {
        "title": "Pegasus Journalist Surveillance",
        "description": "Document Pegasus spyware proliferation for journalist and dissident surveillance",
        "priority_level": "critical",
        "tags": ["pegasus", "nso_group", "journalist_surveillance"],
        "capture_lane": "intelligence",
        "decade": "2020s"
    },
    {
        "title": "Fed Regional Bank Corruption",
        "description": "Investigate Federal Reserve regional bank corruption and capture patterns",
        "priority_level": "high",
        "tags": ["federal_reserve", "banking_corruption", "monetary_capture"],
        "capture_lane": "financial",
        "decade": "2020s"
    }
]

def main():
    """Add all research priorities to the system"""
    print(f"Adding {len(priorities_data)} research priorities to the system...")
    print("=" * 60)
    
    created_files = []
    for priority_data in priorities_data:
        priority = create_priority(**priority_data)
        filepath = save_priority(priority)
        created_files.append(filepath)
    
    print("=" * 60)
    print(f"Successfully created {len(created_files)} research priority files")
    print(f"Location: {PRIORITIES_PATH}/")
    
    # Create summary file
    summary = {
        "generated": datetime.now().isoformat(),
        "total_priorities": len(created_files),
        "by_decade": {},
        "by_capture_lane": {},
        "files": created_files
    }
    
    for p in priorities_data:
        decade = p.get("decade", "unspecified")
        lane = p.get("capture_lane", "unspecified")
        
        if decade not in summary["by_decade"]:
            summary["by_decade"][decade] = 0
        summary["by_decade"][decade] += 1
        
        if lane not in summary["by_capture_lane"]:
            summary["by_capture_lane"][lane] = 0
        summary["by_capture_lane"][lane] += 1
    
    with open(os.path.join(PRIORITIES_PATH, "PRIORITIES_SUMMARY.json"), 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\nSummary by decade:")
    for decade, count in sorted(summary["by_decade"].items()):
        print(f"  {decade}: {count} priorities")
    
    print("\nSummary by capture lane:")
    for lane, count in sorted(summary["by_capture_lane"].items()):
        print(f"  {lane}: {count} priorities")

if __name__ == "__main__":
    main()