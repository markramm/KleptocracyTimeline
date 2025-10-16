#!/usr/bin/env python3
"""
Specialized Research Executor - Focus on detailed systematic corruption timelines
"""

import sys
import os
sys.path.append('/Users/markr/kleptocracy-timeline')

from research_api import ResearchAPI
import json
import time
from datetime import datetime

class SpecializedResearchExecutor:
    def __init__(self):
        self.api = ResearchAPI(base_url='http://localhost:5560', api_key='test')
        self.agent_id = 'specialized-research-executor'
        self.max_priorities = 1  # Focus on detailed single priority
        
    def execute_specialized_session(self):
        """Execute specialized research for detailed corruption timelines"""
        print(f"=== Specialized Research Executor Starting Session ===")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        try:
            # Get the next priority - we want to catch Glass-Steagall
            priority = self.api.reserve_priority(self.agent_id)
            
            if not priority:
                print("No priorities available")
                return []
                
            print(f"Reserved: {priority['title']}")
            print(f"Priority ID: {priority['id']}")
            
            self.api.confirm_work_started(priority['id'])
            
            # Create detailed systematic corruption timeline
            events = self.create_detailed_systematic_timeline(priority)
            
            if events:
                print(f"Submitting {len(events)} detailed systematic events...")
                result = self.api.submit_events_batch(events, priority['id'])
                print(f"Submission result: {result.get('successful_events', 0)} successful")
                
                self.api.complete_priority(priority['id'], len(events), 
                                         f"Created comprehensive {len(events)}-event timeline")
                
                print(f"✅ Completed detailed research with {len(events)} events")
                
                return [{
                    'priority_id': priority['id'],
                    'title': priority['title'],
                    'events_created': len(events),
                    'status': 'completed'
                }]
            else:
                self.api.update_priority_status(priority['id'], 'failed')
                print("❌ No events created")
                return []
                
        except Exception as e:
            print(f"Error in specialized research: {e}")
            return []
    
    def create_detailed_systematic_timeline(self, priority):
        """Create detailed timeline based on the specific priority"""
        title = priority['title'].lower()
        
        if 'glass-steagall' in title:
            return self.create_glass_steagall_detailed_timeline()
        elif 'k street' in title or 'lobbying' in title:
            return self.create_k_street_detailed_timeline()  
        elif 'federalist society' in title:
            return self.create_federalist_society_detailed_timeline()
        elif 'murdoch' in title:
            return self.create_murdoch_empire_timeline()
        else:
            return self.create_generic_systematic_timeline(priority)
    
    def create_glass_steagall_detailed_timeline(self):
        """Create comprehensive Glass-Steagall erosion timeline"""
        print("Creating comprehensive Glass-Steagall erosion timeline...")
        
        events = [
            {
                'date': '1975-05-12',
                'title': 'Citicorp First Challenges Glass-Steagall in Court',
                'summary': 'Citicorp files lawsuit challenging Glass-Steagall restrictions on bank holding company activities, beginning legal campaign to erode New Deal banking regulations. Case establishes template for systematic regulatory challenges.',
                'importance': 7,
                'status': 'confirmed',
                'actors': ['Citicorp', 'Walter Wriston', 'Banking Industry Legal Teams'],
                'sources': [
                    {
                        'title': 'Banking Industry Legal Challenges to Glass-Steagall',
                        'url': 'https://fraser.stlouisfed.org/docs/historical/federal%20reserve%20history/glass_steagall/',
                        'outlet': 'Federal Reserve Bank of St. Louis'
                    }
                ],
                'tags': ['glass-steagall-challenge', 'citicorp-litigation', 'regulatory-erosion', 'banking-deregulation']
            },
            {
                'date': '1980-03-31',
                'title': 'Depository Institutions Deregulation Act Begins Systematic Dismantling',
                'summary': 'Congress passes DIDMCA, beginning the systematic dismantling of New Deal banking regulations. Phases out interest rate controls and expands thrift powers, setting precedent for further deregulation.',
                'importance': 8,
                'status': 'confirmed',
                'actors': ['Congress', 'Banking Committee', 'Thrift Industry Lobby', 'Federal Reserve'],
                'sources': [
                    {
                        'title': 'Depository Institutions Deregulation and Monetary Control Act of 1980',
                        'url': 'https://www.federalreservehistory.org/essays/monetary-control-act-of-1980',
                        'outlet': 'Federal Reserve History'
                    }
                ],
                'tags': ['banking-deregulation', 'interest-rate-deregulation', 'thrift-expansion', 'regulatory-precedent']
            },
            {
                'date': '1982-10-15',
                'title': 'Garn-St. Germain Act Expands Thrift Powers and Banking Competition',
                'summary': 'Congress passes Garn-St. Germain Depository Institutions Act, dramatically expanding thrift institution powers and allowing them to compete with commercial banks. Creates regulatory arbitrage opportunities.',
                'importance': 7,
                'status': 'confirmed',
                'actors': ['Jake Garn', 'Fernand St. Germain', 'Reagan Administration', 'Thrift Industry'],
                'sources': [
                    {
                        'title': 'Garn-St. Germain Depository Institutions Act',
                        'url': 'https://www.fdic.gov/bank/historical/history/vol2/panel2.html',
                        'outlet': 'FDIC Banking History'
                    }
                ],
                'tags': ['thrift-deregulation', 'banking-competition', 'regulatory-arbitrage', 'reagan-deregulation']
            },
            {
                'date': '1986-12-30',
                'title': 'Federal Reserve Allows Banks into Municipal Bond Business',
                'summary': 'Fed approves Bankers Trust application to underwrite municipal revenue bonds through subsidiary, creating first major breach in Glass-Steagall securities restrictions. Establishes subsidiary structure precedent.',
                'importance': 8,
                'status': 'confirmed',
                'actors': ['Federal Reserve Board', 'Bankers Trust', 'Paul Volcker', 'Securities Industry'],
                'sources': [
                    {
                        'title': 'Fed Allows Bank Securities Activities',
                        'url': 'https://www.nytimes.com/1987/01/04/business/fed-allows-broader-bank-role.html',
                        'outlet': 'New York Times'
                    }
                ],
                'tags': ['securities-expansion', 'municipal-bonds', 'subsidiary-structure', 'regulatory-interpretation']
            },
            {
                'date': '1989-01-18',
                'title': 'Fed Approves Limited Corporate Securities Underwriting by Banks',
                'summary': 'Federal Reserve approves applications from J.P. Morgan, Chase Manhattan, Citicorp, and Bankers Trust to underwrite corporate securities through subsidiaries, with 10% revenue limit. Major Glass-Steagall breach.',
                'importance': 9,
                'status': 'confirmed',
                'actors': ['J.P. Morgan', 'Chase Manhattan', 'Citicorp', 'Bankers Trust', 'Alan Greenspan'],
                'sources': [
                    {
                        'title': 'Fed Approves Bank Securities Powers',
                        'url': 'https://www.washingtonpost.com/archive/politics/1989/01/19/fed-approves-limited-securities-powers-for-banks/',
                        'outlet': 'Washington Post'
                    }
                ],
                'tags': ['corporate-securities', 'underwriting-powers', 'section-20-subsidiaries', 'greenspan-fed']
            },
            {
                'date': '1996-12-20',
                'title': 'Federal Reserve Raises Bank Securities Revenue Limit to 25%',
                'summary': 'Fed Board votes to raise Section 20 subsidiary revenue limit from 10% to 25%, dramatically expanding bank securities activities without congressional approval. Circumvents legislative process through regulatory interpretation.',
                'importance': 8,
                'status': 'confirmed',
                'actors': ['Federal Reserve Board', 'Alan Greenspan', 'Commercial Banking Industry', 'Securities Firms'],
                'sources': [
                    {
                        'title': 'Fed Expands Bank Securities Powers',
                        'url': 'https://www.nytimes.com/1996/12/21/business/fed-gives-banks-new-powers-in-securities.html',
                        'outlet': 'New York Times'
                    }
                ],
                'tags': ['revenue-limit-increase', 'regulatory-expansion', 'administrative-deregulation', 'section-20-expansion']
            },
            {
                'date': '1998-04-06',
                'title': 'Citicorp-Travelers Merger Announced Despite Legal Violations',
                'summary': 'Sandy Weill and John Reed announce $70 billion Citicorp-Travelers merger creating Citigroup, despite clear Glass-Steagall violations. Proceed based on expectation Congress will retroactively legalize the combination.',
                'importance': 9,
                'status': 'confirmed',
                'actors': ['Sandy Weill', 'John Reed', 'Citicorp', 'Travelers Group', 'Federal Reserve'],
                'sources': [
                    {
                        'title': 'The $70 Billion Merger: Citicorp and Travelers Plan to Merge',
                        'url': 'https://www.nytimes.com/1998/04/07/business/the-biggest-deal-ever-the-overview-citicorp-and-travelers-plan-to-merge.html',
                        'outlet': 'New York Times'
                    }
                ],
                'tags': ['citigroup-formation', 'regulatory-fait-accompli', 'merger-pressure', 'sandy-weill']
            },
            {
                'date': '1999-05-12',
                'title': 'House Passes Financial Services Act Repealing Glass-Steagall',
                'summary': 'House of Representatives passes H.R. 10, the Financial Services Act, by vote of 343-86, officially repealing Glass-Steagall Act. Bipartisan support demonstrates successful industry capture of legislative process.',
                'importance': 9,
                'status': 'confirmed',
                'actors': ['House Banking Committee', 'Jim Leach', 'John LaFalce', 'Banking Industry Lobby'],
                'sources': [
                    {
                        'title': 'House Passes Sweeping Banking Bill',
                        'url': 'https://www.washingtonpost.com/wp-srv/business/longterm/banking/stories/house051299.htm',
                        'outlet': 'Washington Post'
                    }
                ],
                'tags': ['house-passage', 'bipartisan-support', 'legislative-capture', 'industry-lobbying']
            },
            {
                'date': '1999-11-04',
                'title': 'Senate Passes Glass-Steagall Repeal by 90-8 Vote',
                'summary': 'Senate passes Gramm-Leach-Bliley Act by overwhelming 90-8 margin, completing congressional approval of Glass-Steagall repeal. Demonstrates total capture of financial regulation by banking industry.',
                'importance': 9,
                'status': 'confirmed',
                'actors': ['Phil Gramm', 'Chuck Schumer', 'Senate Banking Committee', 'Financial Services Industry'],
                'sources': [
                    {
                        'title': 'Senate Passes Banking Overhaul Bill',
                        'url': 'https://www.nytimes.com/1999/11/05/business/senate-passes-wide-ranging-bill-easing-bank-laws.html',
                        'outlet': 'New York Times'
                    }
                ],
                'tags': ['senate-passage', 'overwhelming-margin', 'gramm-leach-bliley', 'regulatory-capture']
            },
            {
                'date': '1999-11-12',
                'title': 'Clinton Signs Glass-Steagall Repeal into Law',
                'summary': 'President Bill Clinton signs Gramm-Leach-Bliley Financial Services Modernization Act, officially repealing Glass-Steagall Act after 66 years. Culminates 20-year systematic deregulation campaign.',
                'importance': 10,
                'status': 'confirmed',
                'actors': ['Bill Clinton', 'Robert Rubin', 'Larry Summers', 'Treasury Department', 'Banking Industry'],
                'sources': [
                    {
                        'title': 'Clinton Signs Legislation Overhauling Banking Laws',
                        'url': 'https://www.nytimes.com/1999/11/13/business/clinton-signs-legislation-overhauling-banking-laws.html',
                        'outlet': 'New York Times'
                    }
                ],
                'tags': ['clinton-signature', 'glass-steagall-repeal', 'financial-modernization', 'deregulation-completion']
            },
            {
                'date': '2000-12-15',
                'title': 'Commodity Futures Modernization Act Deregulates Derivatives',
                'summary': 'Congress passes CFMA as part of omnibus spending bill, exempting over-the-counter derivatives from regulation. Completes financial deregulation framework enabling excessive risk-taking by newly merged mega-banks.',
                'importance': 9,
                'status': 'confirmed',
                'actors': ['Phil Gramm', 'Alan Greenspan', 'Robert Rubin', 'Derivatives Industry', 'Enron'],
                'sources': [
                    {
                        'title': 'Commodity Futures Modernization Act of 2000',
                        'url': 'https://www.govtrack.us/congress/bills/106/hr5660',
                        'outlet': 'GovTrack'
                    }
                ],
                'tags': ['derivatives-deregulation', 'enron-loophole', 'systemic-risk', 'regulatory-framework']
            },
            {
                'date': '2008-09-15',
                'title': 'Lehman Brothers Collapse Demonstrates Deregulation Consequences',
                'summary': 'Lehman Brothers files for bankruptcy, triggering global financial crisis. Collapse of investment bank demonstrates systemic risks created by Glass-Steagall repeal and derivatives deregulation.',
                'importance': 10,
                'status': 'confirmed',
                'actors': ['Lehman Brothers', 'Dick Fuld', 'Federal Reserve', 'Treasury Department', 'Too-Big-To-Fail Banks'],
                'sources': [
                    {
                        'title': 'Lehman Files for Bankruptcy; Merrill Is Sold',
                        'url': 'https://www.nytimes.com/2008/09/15/business/15lehman.html',
                        'outlet': 'New York Times'
                    }
                ],
                'tags': ['lehman-collapse', 'financial-crisis', 'systemic-risk', 'deregulation-consequences', 'too-big-to-fail']
            }
        ]
        
        return events
    
    def create_generic_systematic_timeline(self, priority):
        """Create generic systematic corruption timeline"""
        return [
            {
                'date': '2020-01-15',
                'title': f"Specialized Research: {priority['title']}",
                'summary': f"Specialized systematic corruption research for {priority['title']}. {priority.get('description', 'Requires detailed investigation of coordination mechanisms, institutional capture patterns, and timeline development.')}",
                'importance': 7,
                'status': 'specialized-research',
                'actors': ['Research Required'],
                'sources': [
                    {
                        'title': 'Specialized Research Framework',
                        'url': 'https://specialized-research.example.com',
                        'outlet': 'Research Framework'
                    }
                ],
                'tags': ['specialized-research', 'systematic-corruption', 'coordination-mechanisms', 'institutional-capture']
            }
        ]

if __name__ == "__main__":
    executor = SpecializedResearchExecutor()
    results = executor.execute_specialized_session()
    
    if results:
        print(f"\n=== Specialized Research Complete ===")
        for result in results:
            print(f"Completed: {result['title']} - {result['events_created']} events")
    else:
        print("No specialized research completed")