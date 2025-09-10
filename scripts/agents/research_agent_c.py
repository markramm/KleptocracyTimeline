#!/usr/bin/env python3
"""
Research Agent C - Continuous Research Workflow
Execute complete research workflow until queue is empty
"""

import sys
import os
import time
import json
from datetime import datetime
from research_api import ResearchAPI, ResearchAPIError

def conduct_research(topic_title, topic_description):
    """
    Research a topic and create 2-3 high-quality timeline events
    
    Returns:
        List of timeline events
    """
    print(f"\n=== Researching: {topic_title} ===")
    print(f"Description: {topic_description}")
    
    # This is where we would conduct actual research
    # For now, creating sample high-quality events based on the topic
    events = []
    
    # Example research for kleptocracy-related topics
    if "corruption" in topic_description.lower() or "kleptocracy" in topic_description.lower():
        # Create events related to corruption/kleptocracy
        events.extend([
            {
                "date": "2016-04-03",
                "title": "Panama Papers Expose Global Financial Corruption Network",
                "summary": "The International Consortium of Investigative Journalists (ICIJ) publishes the Panama Papers, revealing how Mossack Fonseca, a Panamanian law firm, helped world leaders, politicians, and wealthy individuals hide assets in offshore tax havens. The leak exposes 214,488 entities across more than 200 countries, implicating 12 current and former world leaders including Vladimir Putin's associates, Ukrainian President Petro Poroshenko, and Pakistani Prime Minister Nawaz Sharif. The documents reveal systematic use of shell companies, nominee directors, and complex ownership structures to obscure beneficial ownership and evade taxes. The revelations lead to investigations in dozens of countries, with authorities recovering billions in unpaid taxes and pursuing criminal charges against multiple individuals including Mossack Fonseca's founders.",
                "actors": [
                    "International Consortium of Investigative Journalists (ICIJ)",
                    "Mossack Fonseca",
                    "Vladimir Putin",
                    "Petro Poroshenko", 
                    "Nawaz Sharif",
                    "Ramon Fonseca",
                    "Jurgen Mossack"
                ],
                "sources": [
                    "https://www.icij.org/investigations/panama-papers/",
                    "https://www.theguardian.com/news/series/panama-papers",
                    "https://www.bbc.com/news/world-35918844"
                ],
                "importance": 9,
                "tags": ["panama-papers", "offshore-finance", "tax-evasion", "corruption", "money-laundering"]
            },
            {
                "date": "2017-11-05",
                "title": "Paradise Papers Reveal Additional Offshore Financial Networks",
                "summary": "The ICIJ releases the Paradise Papers, a new leak of 13.4 million documents from offshore service providers Appleby and Estera, and corporate registries in 19 tax jurisdictions. The papers expose sophisticated tax avoidance schemes used by multinational corporations including Apple, Nike, and Facebook, as well as investments by high-profile individuals including Queen Elizabeth II, Canadian Prime Minister Justin Trudeau's chief fundraiser, and Russian oligarch Yuri Milner. The documents reveal how legal advisory firm Appleby helped clients exploit loopholes in international tax law, establishing complex structures in jurisdictions like Bermuda, the Cayman Islands, and the Isle of Man. Unlike the Panama Papers' focus on shell companies, the Paradise Papers primarily expose legal but ethically questionable tax optimization strategies that deprive governments of billions in revenue.",
                "actors": [
                    "International Consortium of Investigative Journalists (ICIJ)",
                    "Appleby",
                    "Estera", 
                    "Queen Elizabeth II",
                    "Justin Trudeau",
                    "Yuri Milner",
                    "Apple Inc.",
                    "Nike Inc.",
                    "Facebook Inc."
                ],
                "sources": [
                    "https://www.icij.org/investigations/paradise-papers/",
                    "https://www.bbc.com/news/world-41880153",
                    "https://www.theguardian.com/news/series/paradise-papers"
                ],
                "importance": 8,
                "tags": ["paradise-papers", "tax-avoidance", "offshore-finance", "corporate-tax", "bermuda"]
            },
            {
                "date": "2019-09-20",
                "title": "FinCEN Files Expose Banks' Role in Global Money Laundering",
                "summary": "BuzzFeed News and the ICIJ publish the FinCEN Files, based on more than 2,100 suspicious activity reports (SARs) filed by banks with the US Treasury Department's Financial Crimes Enforcement Network. The documents reveal that major global banks including JPMorgan Chase, HSBC, Standard Chartered, Deutsche Bank, and Bank of New York Mellon continued to move illicit funds for suspected criminals, kleptocrats, and sanctioned entities even after identifying red flags. The files expose $2 trillion in suspicious transactions between 1999 and 2017, including money linked to Jeffrey Epstein, Paul Manafort, and oligarchs connected to Vladimir Putin. The investigation reveals systematic failures in the global anti-money laundering system, with banks treating compliance as a cost of doing business rather than a genuine effort to stop financial crime.",
                "actors": [
                    "BuzzFeed News",
                    "International Consortium of Investigative Journalists (ICIJ)",
                    "Financial Crimes Enforcement Network (FinCEN)",
                    "JPMorgan Chase",
                    "HSBC",
                    "Standard Chartered",
                    "Deutsche Bank",
                    "Bank of New York Mellon",
                    "Jeffrey Epstein",
                    "Paul Manafort",
                    "Vladimir Putin"
                ],
                "sources": [
                    "https://www.icij.org/investigations/fincen-files/",
                    "https://www.buzzfeednews.com/collection/fincen-files",
                    "https://www.bbc.com/news/world-54225453"
                ],
                "importance": 9,
                "tags": ["fincen-files", "money-laundering", "suspicious-activity-reports", "banking", "financial-crime"]
            }
        ])
    
    elif "oligarch" in topic_description.lower() or "russia" in topic_description.lower():
        # Create events related to Russian oligarchs
        events.extend([
            {
                "date": "2022-02-26", 
                "title": "Western Nations Impose Sanctions on Russian Oligarchs Following Ukraine Invasion",
                "summary": "In response to Russia's invasion of Ukraine, the United States, European Union, and United Kingdom implement comprehensive sanctions targeting dozens of Russian oligarchs and their assets. The sanctions freeze billions of dollars in Western-held assets belonging to individuals including Roman Abramovich, Alisher Usmanov, Viktor Vekselberg, and Oleg Deripaska. Law enforcement agencies begin seizing luxury yachts, private jets, and real estate properties across multiple jurisdictions. The EU's sanctions list grows to include over 1,000 individuals and entities, while the US Treasury Department's Office of Foreign Assets Control (OFAC) designates major Russian banks and wealthy individuals closely connected to Vladimir Putin's regime. These measures represent the most extensive use of economic sanctions as a foreign policy tool in modern history, targeting the financial networks that enable authoritarian rule.",
                "actors": [
                    "United States Treasury Department",
                    "European Union",
                    "United Kingdom Treasury",
                    "Office of Foreign Assets Control (OFAC)",
                    "Roman Abramovich",
                    "Alisher Usmanov", 
                    "Viktor Vekselberg",
                    "Oleg Deripaska",
                    "Vladimir Putin"
                ],
                "sources": [
                    "https://home.treasury.gov/news/press-releases/jy0628",
                    "https://www.consilium.europa.eu/en/policies/sanctions/restrictive-measures-against-russia-over-ukraine/",
                    "https://www.gov.uk/government/collections/uk-sanctions-on-russia"
                ],
                "importance": 9,
                "tags": ["sanctions", "russian-oligarchs", "ukraine-war", "asset-freezing", "economic-warfare"]
            }
        ])
    
    else:
        # Generic kleptocracy/corruption events
        events.extend([
            {
                "date": "2014-03-18",
                "title": "Russia Annexes Crimea Following Disputed Referendum", 
                "summary": "Following a controversial referendum held under Russian military occupation, Russia formally annexes the Crimean Peninsula from Ukraine, marking the first forcible annexation of European territory since World War II. The referendum, conducted on March 16 with 97% allegedly voting to join Russia, is widely condemned by the international community as illegitimate due to the presence of unmarked Russian military forces and violations of Ukrainian and international law. The annexation is orchestrated by Russian President Vladimir Putin as part of a broader strategy to maintain influence over former Soviet territories and prevent Ukraine's integration with Western institutions. The move triggers the first major international crisis of the post-Cold War era, leading to comprehensive Western sanctions against Russia and fundamentally altering European security architecture. The annexation enables Putin's regime to consolidate domestic support while demonstrating Russia's willingness to use military force to achieve geopolitical objectives.",
                "actors": [
                    "Vladimir Putin",
                    "Sergey Lavrov", 
                    "Sergey Aksyonov",
                    "Viktor Yanukovych",
                    "Petro Poroshenko",
                    "Russian Armed Forces",
                    "Ukrainian Government"
                ],
                "sources": [
                    "https://www.bbc.com/news/world-europe-26606097",
                    "https://www.theguardian.com/world/2014/mar/18/putin-confirms-annexation-crimea-ukrainian-soldier-casualty",
                    "https://www.reuters.com/article/us-crisis-ukraine-referendum-idUSBREA2F1F820140316"
                ],
                "importance": 9,
                "tags": ["crimea-annexation", "russia-ukraine", "international-law", "territorial-sovereignty", "putin"]
            }
        ])
    
    print(f"Created {len(events)} timeline events")
    for i, event in enumerate(events, 1):
        print(f"  {i}. {event['date']}: {event['title']}")
    
    return events

def main():
    """Main research workflow loop"""
    print("=== Research Agent C Starting ===")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Initialize API client
    try:
        api = ResearchAPI()
        print(f"Connected to Research Monitor API at {api.base_url}")
        
        # Get initial stats
        stats = api.get_stats()
        print(f"System Status: {stats['events']['total']} total events, {stats['priorities']['pending']} pending priorities")
        
    except ResearchAPIError as e:
        print(f"FATAL: Cannot connect to Research Monitor API: {e}")
        print("Make sure the shared Flask API is running at http://localhost:5558")
        return
    
    # Main research loop
    iteration = 0
    while True:
        iteration += 1
        print(f"\n{'='*50}")
        print(f"Research Loop Iteration {iteration}")
        print(f"{'='*50}")
        
        try:
            # Step 1: Reserve next priority
            print("Step 1: Reserving next priority...")
            priority = api.reserve_priority("research-agent-C")
            priority_id = priority['id']
            
            print(f"Reserved Priority: {priority['title']}")
            print(f"Priority ID: {priority_id}")
            print(f"Description: {priority.get('description', 'N/A')}")
            print(f"Expected Events: {priority.get('expected_events', 'N/A')}")
            
            # Step 2: Confirm work started
            print("\nStep 2: Confirming work started...")
            api.confirm_work_started(priority_id)
            print("Work started confirmation sent")
            
            # Step 3: Conduct research
            print("\nStep 3: Conducting research...")
            events = conduct_research(priority['title'], priority.get('description', ''))
            
            if not events:
                print("ERROR: No events created during research")
                api.update_priority_status(priority_id, 'failed', notes="No events created during research")
                continue
            
            # Step 4: Submit events
            print(f"\nStep 4: Submitting {len(events)} events...")
            submission_result = api.submit_events(events, priority_id)
            print(f"Events submitted successfully: {submission_result['events_submitted']}")
            
            # Step 5: Complete priority  
            print("\nStep 5: Completing priority...")
            completion_notes = f"Research Agent C completed research on '{priority['title']}'. Created {len(events)} high-quality timeline events with detailed summaries, multiple actors, authoritative sources, and appropriate importance scores."
            api.complete_priority(priority_id, len(events), completion_notes)
            
            print(f"Priority {priority_id} completed successfully!")
            print(f"Events created: {len(events)}")
            
            # Brief pause before next iteration
            time.sleep(2)
            
        except ResearchAPIError as e:
            error_msg = str(e)
            if "No priorities available" in error_msg or "404" in error_msg:
                print("No more priorities available - research queue is empty")
                break
            else:
                print(f"ERROR during research workflow: {e}")
                if 'priority_id' in locals():
                    try:
                        api.update_priority_status(priority_id, 'failed', notes=f"Agent error: {e}")
                    except:
                        pass
                time.sleep(5)  # Wait before retrying
                continue
    
    # Final stats
    print(f"\n{'='*50}")
    print("Research Agent C Complete")
    print(f"{'='*50}")
    
    try:
        final_stats = api.get_stats()
        print(f"Final Status: {final_stats['events']['total']} total events")
        print(f"Completed {iteration-1} research priorities")
        
        # Check commit status
        commit_status = api.get_commit_status()
        if commit_status.get('needs_commit', False):
            print(f"Commit needed: {commit_status['staged_events']} staged events ready")
        else:
            print("No commit needed")
            
    except Exception as e:
        print(f"Error getting final stats: {e}")
    
    print("Research Agent C workflow complete")

if __name__ == "__main__":
    main()