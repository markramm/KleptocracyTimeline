#!/usr/bin/env python3
"""
Save researched timeline events to JSON files
"""
import json
import os
from pathlib import Path

# Base directory for events
EVENTS_DIR = Path("timeline_data/events")

# Financial crisis events
financial_crisis_events = [
    {
        "id": "2009-02-23--holder-testifies-banks-too-big-to-jail",
        "date": "2009-02-23",
        "importance": 10,
        "title": "Holder Testifies Some Banks Are Too Big to Jail",
        "summary": "Attorney General Eric Holder testifies before Congress that some financial institutions are so large that prosecuting them could threaten the economy, institutionalizing 'too big to jail' doctrine.",
        "actors": ["Eric Holder", "Department of Justice", "JPMorgan Chase", "Bank of America", "Citigroup"],
        "tags": ["institutional-capture", "regulatory-capture", "corruption", "financial-crisis"],
        "sources": [
            {"title": "Holder: Some banks 'too big to jail'", "url": "https://www.politico.com/story/2013/03/eric-holder-banks-too-big-to-jail-088518", "outlet": "Politico", "date": "2013-03-06"}
        ]
    },
    {
        "id": "2010-04-14--robo-signing-scandal-exposed",
        "date": "2010-04-14", 
        "importance": 8,
        "title": "Robo-Signing Scandal Exposed Systematic Foreclosure Document Fraud",
        "summary": "Investigation reveals major banks systematically falsified foreclosure documents through 'robo-signing', affecting 3.8 million homes.",
        "actors": ["Bank of America", "JPMorgan Chase", "Wells Fargo", "Citigroup", "GMAC"],
        "tags": ["financial-crisis", "fraud", "foreclosure-abuse", "perjury"],
        "sources": [
            {"title": "Robo-Signing, Explained", "url": "https://www.cbsnews.com/news/robo-signing-explained/", "outlet": "CBS News", "date": "2010-10-06"}
        ]
    },
    {
        "id": "2012-02-09--mortgage-settlement-provides-immunity",
        "date": "2012-02-09",
        "importance": 8,
        "title": "25 Billion Mortgage Settlement Provides Banks Immunity for Minimal Payments",
        "summary": "$25 billion settlement with five major banks over foreclosure abuses provides broad legal immunity for only $5 billion in actual cash payments.",
        "actors": ["Eric Holder", "Bank of America", "JPMorgan Chase", "Wells Fargo", "Citigroup", "Ally Financial"],
        "tags": ["prosecutorial-capture", "settlement-abuse", "foreclosure-fraud", "immunity-deal"],
        "sources": [
            {"title": "U.S., States Reach $25 Billion Mortgage Settlement", "url": "https://www.reuters.com/article/us-usa-housing-settlement-idUSTRE8180W220120209", "outlet": "Reuters", "date": "2012-02-09"}
        ]
    },
    {
        "id": "2011-12-01--gao-reveals-fed-secret-16-trillion-crisis-loans",
        "date": "2011-12-01",
        "importance": 9,
        "title": "GAO Audit Reveals Fed Secretly Provided 16 Trillion in Crisis Loans",
        "summary": "GAO audit reveals Federal Reserve secretly provided $16.1 trillion in emergency loans to major banks and corporations, far exceeding the $700 billion TARP program.",
        "actors": ["Federal Reserve", "Ben Bernanke", "Citigroup", "Morgan Stanley", "Goldman Sachs", "Bank of America"],
        "tags": ["financial-crisis", "secret-bailout", "monetary-capture", "federal-reserve"],
        "sources": [
            {"title": "Federal Reserve Emergency Lending", "url": "https://www.gao.gov/products/gao-11-696", "outlet": "GAO", "date": "2011-07-21"}
        ]
    }
]

# Regulatory capture events
regulatory_capture_events = [
    {
        "id": "2004-04-28--sec-reduces-leverage-limits-investment-banks",
        "date": "2004-04-28",
        "importance": 9,
        "title": "SEC Reduces Leverage Limits for Major Investment Banks",
        "summary": "SEC voted to allow five major investment banks to use alternative net capital rules, enabling leverage ratios to increase from 12:1 to over 40:1, contributing to 2008 crisis.",
        "actors": ["Securities and Exchange Commission", "Goldman Sachs", "Morgan Stanley", "Merrill Lynch", "Lehman Brothers", "Bear Stearns"],
        "tags": ["regulatory-capture", "financial-crisis", "sec", "leverage"],
        "sources": [
            {"title": "SEC Concedes Oversight Flaws Fueled Collapse", "url": "https://www.nytimes.com/2008/09/27/business/27sec.html", "outlet": "New York Times", "date": "2008-09-27"}
        ]
    },
    {
        "id": "2017-12-14--fcc-repeals-net-neutrality-regulations",
        "date": "2017-12-14",
        "importance": 8,
        "title": "FCC Repeals Net Neutrality Regulations Under Industry Pressure",
        "summary": "FCC Chairman Ajit Pai, former Verizon lawyer, leads repeal of net neutrality despite overwhelming public opposition, prioritizing ISP profits over consumer protection.",
        "actors": ["Ajit Pai", "Federal Communications Commission", "Verizon", "Comcast", "AT&T"],
        "tags": ["regulatory-capture", "net-neutrality", "fcc", "telecom"],
        "sources": [
            {"title": "F.C.C. Repeals Net Neutrality Rules", "url": "https://www.nytimes.com/2017/12/14/technology/net-neutrality-repeal-vote.html", "outlet": "New York Times", "date": "2017-12-14"}
        ]
    }
]

# Dark money events
dark_money_events = [
    {
        "id": "2010-01-21--citizens-united-unleashes-unlimited-corporate-spending",
        "date": "2010-01-21",
        "importance": 10,
        "title": "Supreme Court Citizens United Decision Unleashes Unlimited Corporate Spending",
        "summary": "Supreme Court ruled 5-4 that corporations can spend unlimited amounts on elections through independent expenditures, enabling creation of Super PACs and dark money networks.",
        "actors": ["Supreme Court", "Citizens United", "Federal Election Commission", "Justice Anthony Kennedy"],
        "tags": ["dark-money", "campaign-finance", "supreme-court", "corporate-power"],
        "sources": [
            {"title": "Citizens United v. Federal Election Commission", "url": "https://www.supremecourt.gov/opinions/09pdf/08-205.pdf", "outlet": "Supreme Court", "date": "2010-01-21"}
        ]
    },
    {
        "id": "2012-01-01--koch-network-spends-400-million-targeting-obama",
        "date": "2012-01-01",
        "importance": 8,
        "title": "Koch Network Spends $400 Million Targeting Obama Reelection",
        "summary": "Koch brothers coordinate network of wealthy donors and front groups spending approximately $400 million in 2012 election cycle, primarily targeting President Obama's reelection.",
        "actors": ["Charles Koch", "David Koch", "Americans for Prosperity", "Freedom Partners Chamber of Commerce"],
        "tags": ["dark-money", "koch-network", "election-influence", "campaign-finance"],
        "sources": [
            {"title": "The Koch Brothers' Political Network Spent $400 Million in 2012", "url": "https://www.motherjones.com/politics/2013/02/koch-brothers-400-million-2012-election/", "outlet": "Mother Jones", "date": "2013-02-05"}
        ]
    }
]

def save_event(event_data, events_dir=EVENTS_DIR):
    """Save a single event to JSON file"""
    filename = f"{event_data['date']}--{event_data['id'].split('--')[1]}.json"
    filepath = events_dir / filename
    
    # Check if file already exists
    if filepath.exists():
        print(f"⚠️  File already exists: {filename}")
        return False
    
    # Save to JSON
    with open(filepath, 'w') as f:
        json.dump(event_data, f, indent=2)
    
    print(f"✅ Saved: {filename}")
    return True

def main():
    """Save all researched events"""
    all_events = financial_crisis_events + regulatory_capture_events + dark_money_events
    
    saved_count = 0
    skipped_count = 0
    
    for event in all_events:
        if save_event(event):
            saved_count += 1
        else:
            skipped_count += 1
    
    print(f"\n📊 Summary:")
    print(f"   Saved: {saved_count} new events")
    print(f"   Skipped: {skipped_count} existing events")
    print(f"   Total: {len(all_events)} events processed")

if __name__ == "__main__":
    main()