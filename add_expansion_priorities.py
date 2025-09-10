#!/usr/bin/env python3
"""
Add expansion research priorities based on existing timeline gaps
These priorities are designed to expand outward from current coverage
"""

import json
import os
from datetime import datetime
import hashlib

PRIORITIES_PATH = "research_priorities"

def create_priority(title, description, priority_level, tags, connections=None, decade=None):
    """Create a research priority JSON object"""
    priority_id = f"RT-EXP-{hashlib.md5(title.encode()).hexdigest()[:8].upper()}"
    
    priority = {
        "id": priority_id,
        "title": title,
        "description": description,
        "priority": priority_level,
        "tags": tags,
        "decade": decade,
        "created": datetime.now().isoformat(),
        "status": "pending",
        "category": "expansion_research"
    }
    
    if connections:
        priority["connections"] = connections
    
    return priority

def save_priority(priority):
    """Save priority to file system"""
    os.makedirs(PRIORITIES_PATH, exist_ok=True)
    filename = f"{priority['id']}-{priority['title'].lower().replace(' ', '-')[:50]}.json"
    filepath = os.path.join(PRIORITIES_PATH, filename)
    
    with open(filepath, 'w') as f:
        json.dump(priority, f, indent=2)
    
    print(f"Created: {filepath}")
    return filepath

# Expansion priorities based on timeline analysis
expansion_priorities = [
    # 1970s - Expand from Powell/Nixon/Church Committee
    {
        "title": "Business Roundtable Formation 1972",
        "description": "Investigate Business Roundtable founding as CEO lobbying organization parallel to Powell Memo implementation. Connect to current members' capture activities.",
        "priority_level": "high",
        "tags": ["business_roundtable", "ceo_lobbying", "powell_memo_parallel"],
        "connections": ["Lewis Powell", "Nixon Administration"],
        "decade": "1970s"
    },
    {
        "title": "Trilateral Commission 1973 Banking Networks",
        "description": "Map Trilateral Commission founding by David Rockefeller, connecting to international banking coordination and petrodollar system establishment.",
        "priority_level": "high",
        "tags": ["trilateral_commission", "rockefeller", "international_banking"],
        "connections": ["Jules Kroll", "CIA networks"],
        "decade": "1970s"
    },
    {
        "title": "BCCI Early Operations 1972-1979",
        "description": "Document Bank of Credit and Commerce International's 1970s foundation as criminal banking network, connecting to later CIA/drug money laundering.",
        "priority_level": "critical",
        "tags": ["bcci", "money_laundering", "cia_banking"],
        "connections": ["Kroll Associates", "intelligence networks"],
        "decade": "1970s"
    },
    
    # 1980s - Expand from Manafort/Epstein/Maxwell
    {
        "title": "Adnan Khashoggi Arms Network",
        "description": "Map Khashoggi's 1980s arms dealing network connecting to Iran-Contra, BCCI, and Trump yacht/property deals. Links to Epstein financial origins.",
        "priority_level": "critical",
        "tags": ["khashoggi", "iran_contra", "arms_dealing", "trump_connections"],
        "connections": ["Donald Trump", "Epstein network", "BCCI"],
        "decade": "1980s"
    },
    {
        "title": "Robert Maxwell Media Empire KGB Links",
        "description": "Document Robert Maxwell's media empire, Pergamon Press scientific intelligence gathering, and KGB/Mossad connections. Foundation for Ghislaine's networks.",
        "priority_level": "critical",
        "tags": ["robert_maxwell", "media_empire", "kgb", "mossad"],
        "connections": ["Ghislaine Maxwell", "intelligence networks"],
        "decade": "1980s"
    },
    {
        "title": "Carl Icahn Corporate Raiding Network",
        "description": "Track Carl Icahn and corporate raider network in 1980s, hostile takeovers, and connections to Trump casinos and current administration.",
        "priority_level": "high",
        "tags": ["carl_icahn", "corporate_raiders", "hostile_takeovers"],
        "connections": ["Trump Organization", "casino financing"],
        "decade": "1980s"
    },
    {
        "title": "Roy Cohn Blackmail Operations",
        "description": "Document Roy Cohn's 1980s blackmail networks, Studio 54 operations, and mentorship of Trump and Roger Stone. Blueprint for Epstein model.",
        "priority_level": "critical",
        "tags": ["roy_cohn", "blackmail", "studio_54", "sexual_kompromat"],
        "connections": ["Donald Trump", "Roger Stone", "Epstein model"],
        "decade": "1980s"
    },
    
    # 1990s - Expand from Trump/Epstein/Wexner/Fox News
    {
        "title": "Wexner L Brands Intelligence Operations",
        "description": "Investigate Leslie Wexner's L Brands/Victoria's Secret as potential intelligence front, model recruiting pipeline, and Epstein funding source.",
        "priority_level": "critical",
        "tags": ["leslie_wexner", "l_brands", "model_trafficking"],
        "connections": ["Jeffrey Epstein", "Ghislaine Maxwell"],
        "decade": "1990s"
    },
    {
        "title": "Russian Oligarch NYC Property Boom",
        "description": "Map 1990s Russian oligarch money laundering through NYC real estate, connecting Mogilevich network to Trump properties and Felix Sater.",
        "priority_level": "critical",
        "tags": ["russian_oligarchs", "money_laundering", "nyc_real_estate"],
        "connections": ["Trump Organization", "Bayrock Group"],
        "decade": "1990s"
    },
    {
        "title": "Clear Channel Media Consolidation",
        "description": "Document Clear Channel (now iHeartMedia) buying 1200+ radio stations post-Telecommunications Act, creating right-wing talk radio monopoly.",
        "priority_level": "high",
        "tags": ["clear_channel", "radio_consolidation", "rush_limbaugh"],
        "connections": ["Fox News", "conservative media"],
        "decade": "1990s"
    },
    {
        "title": "DynCorp Human Trafficking Bosnia",
        "description": "Investigate DynCorp contractors' human trafficking in Bosnia, UN peacekeeping corruption, and connections to private military expansion.",
        "priority_level": "high",
        "tags": ["dyncorp", "human_trafficking", "bosnia", "pmc"],
        "connections": ["private military contractors"],
        "decade": "1990s"
    },
    
    # 2000s - Expand from limited coverage
    {
        "title": "Dubai Ports World Attempted Takeover",
        "description": "Document 2006 Dubai Ports World attempt to control US ports, UAE intelligence connections, and Trump's Dubai business dealings.",
        "priority_level": "high",
        "tags": ["dubai_ports", "uae", "port_security"],
        "connections": ["Trump Organization", "Gulf states"],
        "decade": "2000s"
    },
    {
        "title": "Jack Abramoff Indian Casino Network",
        "description": "Map Abramoff's Indian casino lobbying scandal connecting to Ralph Reed, Grover Norquist, and Tom DeLay's K Street Project.",
        "priority_level": "high",
        "tags": ["abramoff", "indian_casinos", "k_street"],
        "connections": ["GOP corruption", "lobbying scandal"],
        "decade": "2000s"
    },
    {
        "title": "Blackwater Nisour Square Massacre",
        "description": "Document Blackwater's 2007 Baghdad massacre, Erik Prince's CIA connections, and evolution into Xi/Academi/Constellis.",
        "priority_level": "critical",
        "tags": ["blackwater", "erik_prince", "war_crimes"],
        "connections": ["private military", "Trump administration"],
        "decade": "2000s"
    },
    {
        "title": "AIG Greenberg Spitzer Investigation",
        "description": "Investigate Maurice 'Hank' Greenberg's AIG fraud, Eliot Spitzer investigation derailment, and connections to 2008 crisis.",
        "priority_level": "high",
        "tags": ["aig", "greenberg", "spitzer", "insurance_fraud"],
        "connections": ["2008 financial crisis", "Wall Street"],
        "decade": "2000s"
    },
    
    # 2010s - Expand from Thiel/Vance and limited coverage
    {
        "title": "Palantir ICE Contracts Expansion",
        "description": "Track Palantir's ICE/CBP contracts growth, predictive policing algorithms, and Thiel's government surveillance infrastructure.",
        "priority_level": "critical",
        "tags": ["palantir", "ice", "thiel", "surveillance"],
        "connections": ["Peter Thiel", "immigration enforcement"],
        "decade": "2010s"
    },
    {
        "title": "Sinclair Broadcasting Must-Run Segments",
        "description": "Document Sinclair's acquisition of 200+ local stations, Boris Epshteyn must-run segments, and 'This is dangerous to our democracy' script.",
        "priority_level": "high",
        "tags": ["sinclair", "local_news", "boris_epshteyn"],
        "connections": ["media consolidation", "Trump propaganda"],
        "decade": "2010s"
    },
    {
        "title": "WeWork SoftBank Saudi Money Laundering",
        "description": "Investigate WeWork/Adam Neumann's Saudi funding via SoftBank Vision Fund, Kushner connections, and spectacular fraud collapse.",
        "priority_level": "high",
        "tags": ["wework", "softbank", "saudi_money", "neumann"],
        "connections": ["Jared Kushner", "Saudi Arabia"],
        "decade": "2010s"
    },
    {
        "title": "Mercers Cambridge Analytica Funding",
        "description": "Map Robert and Rebekah Mercer's funding network: Cambridge Analytica, Breitbart, Parler, and GAI connections to Bannon.",
        "priority_level": "critical",
        "tags": ["mercers", "cambridge_analytica", "breitbart"],
        "connections": ["Steve Bannon", "data manipulation"],
        "decade": "2010s"
    },
    
    # 2020s - Expand from current heavy coverage
    {
        "title": "Truth Social SPAC Fraud Network",
        "description": "Investigate Digital World Acquisition Corp SPAC fraud, Patrick Orlando, ARC Capital, and Chinese investor connections to Truth Social.",
        "priority_level": "critical",
        "tags": ["truth_social", "dwac", "spac_fraud"],
        "connections": ["Trump Media", "Chinese investors"],
        "decade": "2020s"
    },
    {
        "title": "Gettr Jason Miller Chinese Funding",
        "description": "Document Jason Miller's Gettr platform, Miles Guo/Guo Wengui funding, and CCP exile billionaire influence operations.",
        "priority_level": "high",
        "tags": ["gettr", "jason_miller", "guo_wengui"],
        "connections": ["Trump allies", "Chinese influence"],
        "decade": "2020s"
    },
    {
        "title": "NFT Pump and Dump Networks",
        "description": "Map celebrity NFT pump-and-dumps: Trump NFTs, Melania NFTs, connecting to crypto money laundering and campaign finance.",
        "priority_level": "high",
        "tags": ["nft", "crypto_fraud", "money_laundering"],
        "connections": ["Trump family", "crypto networks"],
        "decade": "2020s"
    },
    {
        "title": "Private Prison Expansion GEO Group",
        "description": "Track GEO Group and CoreCivic's expansion under immigration crackdowns, facility conditions, and political contribution networks.",
        "priority_level": "critical",
        "tags": ["geo_group", "corecivic", "private_prisons"],
        "connections": ["ICE detention", "mass deportation"],
        "decade": "2020s"
    },
    {
        "title": "Rumble Alternative Tech Ecosystem",
        "description": "Investigate Rumble's funding, Peter Thiel connections, and creation of parallel tech infrastructure for right-wing content.",
        "priority_level": "high",
        "tags": ["rumble", "alt_tech", "thiel_network"],
        "connections": ["Truth Social", "conservative tech"],
        "decade": "2020s"
    },
    
    # Cross-cutting network expansions
    {
        "title": "Opus Dei Political Networks",
        "description": "Map Opus Dei influence in Supreme Court (ACB, Scalia legacy), Federalist Society, and Catholic integralist movement.",
        "priority_level": "high",
        "tags": ["opus_dei", "catholic_integralism", "federalist_society"],
        "connections": ["Supreme Court", "Leonard Leo"],
        "decade": "cross-decade"
    },
    {
        "title": "Council for National Policy Coordination",
        "description": "Document CNP secret membership, coordination of conservative movement, and dark money distribution networks.",
        "priority_level": "critical",
        "tags": ["cnp", "conservative_coordination", "dark_money"],
        "connections": ["Heritage Foundation", "religious right"],
        "decade": "cross-decade"
    },
    {
        "title": "Sovereign Wealth Fund Influence Operations",
        "description": "Track Saudi PIF, UAE Mubadala, Qatar Investment Authority stakes in US tech, media, and real estate for influence.",
        "priority_level": "critical",
        "tags": ["sovereign_wealth", "saudi_pif", "gulf_influence"],
        "connections": ["Kushner Affinity", "Trump properties"],
        "decade": "cross-decade"
    },
    {
        "title": "Cyber Mercenary Industry NSO Competitors",
        "description": "Map NSO Group competitors: Candiru, Cytrox, RCS Lab creating global surveillance-for-hire industry.",
        "priority_level": "critical",
        "tags": ["cyber_mercenaries", "surveillance_tech", "spyware"],
        "connections": ["Pegasus", "journalist targeting"],
        "decade": "cross-decade"
    }
]

def main():
    """Add all expansion research priorities"""
    print(f"Adding {len(expansion_priorities)} expansion research priorities...")
    print("=" * 60)
    
    created_files = []
    for priority_data in expansion_priorities:
        priority = create_priority(**priority_data)
        filepath = save_priority(priority)
        created_files.append(filepath)
    
    print("=" * 60)
    print(f"Successfully created {len(created_files)} expansion priority files")
    
    # Create summary
    summary = {
        "generated": datetime.now().isoformat(),
        "total_priorities": len(created_files),
        "by_decade": {},
        "high_value_targets": [],
        "files": created_files
    }
    
    for p in expansion_priorities:
        decade = p.get("decade", "unspecified")
        if decade not in summary["by_decade"]:
            summary["by_decade"][decade] = 0
        summary["by_decade"][decade] += 1
        
        if p["priority_level"] == "critical":
            summary["high_value_targets"].append(p["title"])
    
    with open(os.path.join(PRIORITIES_PATH, "EXPANSION_PRIORITIES_SUMMARY.json"), 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\nSummary by decade:")
    for decade, count in sorted(summary["by_decade"].items()):
        print(f"  {decade}: {count} priorities")
    
    print(f"\nCritical priorities: {len(summary['high_value_targets'])}")
    for target in summary["high_value_targets"][:5]:
        print(f"  • {target}")

if __name__ == "__main__":
    main()