#!/usr/bin/env python3

import json
from research_api import ResearchAPI

# Initialize API
api = ResearchAPI(base_url='http://localhost:5560', api_key='test')

# Create timeline events for Federal Reserve regional bank corruption
events = [
    {
        "id": "2021-09-07--kaplan-fed-trading-scandal-revealed",
        "date": "2021-09-07",
        "title": "Dallas Fed President Kaplan Trading Scandal Revealed",
        "summary": "Wall Street Journal reports Dallas Federal Reserve President Robert Kaplan made multiple stock trades worth over $1 million during 2020 while orchestrating Fed's COVID-19 pandemic response. Trades included Apple, Delta Air Lines, Occidental Petroleum, and iShares Floating Rate Bond ETFs. Kaplan was instrumental in engineering unprecedented market interventions while simultaneously profiting from individual stock positions, creating systematic conflicts of interest that undermined Federal Reserve independence and public trust in monetary policy decisions during national crisis.",
        "importance": 8,
        "tags": ["federal_reserve", "trading_scandal", "conflict_of_interest", "robert_kaplan", "dallas_fed", "financial_corruption"],
        "actors": ["Robert Kaplan", "Federal Reserve Bank of Dallas", "Wall Street Journal"],
        "sources": [
            {
                "url": "https://www.wsj.com/articles/federal-reserve-ethics-officials-pandemic-trades-11630959600",
                "title": "Fed Officials Made Trades During Pandemic",
                "date": "2021-09-07"
            }
        ]
    },
    
    {
        "id": "2021-09-08--rosengren-fed-reit-trading-scandal",
        "date": "2021-09-08", 
        "title": "Boston Fed President Rosengren REIT Trading Scandal Exposed",
        "summary": "Bloomberg reveals Boston Federal Reserve President Eric Rosengren made multiple purchases and sales in Real Estate Investment Trusts (REITs) and mortgage-backed securities during 2020 while publicly warning about commercial real estate market contagion risks. Rosengren's trades in real estate funds directly conflicted with his public warnings and his role setting Federal Reserve policy on mortgage-backed security purchases during pandemic crisis, demonstrating systematic regulatory capture where Fed officials profit from markets they regulate.",
        "importance": 8,
        "tags": ["federal_reserve", "trading_scandal", "conflict_of_interest", "eric_rosengren", "boston_fed", "real_estate", "regulatory_capture"],
        "actors": ["Eric Rosengren", "Federal Reserve Bank of Boston", "Bloomberg"],
        "sources": [
            {
                "url": "https://www.bloomberg.com/news/articles/2021-09-08/fed-s-rosengren-made-real-estate-trades-during-2020-market-turmoil",
                "title": "Fed's Rosengren Made Real Estate Trades During 2020 Market Turmoil",
                "date": "2021-09-08"
            }
        ]
    },
    
    {
        "id": "2021-09-27--fed-presidents-resign-trading-scandal",
        "date": "2021-09-27",
        "title": "Dallas and Boston Fed Presidents Resign Over Trading Scandal",
        "summary": "Robert Kaplan (Dallas Fed) and Eric Rosengren (Boston Fed) announce resignations within hours of each other following massive public backlash over their 2020 trading activities. Rosengren claims early retirement due to 'kidney condition' while Kaplan admits his financial dealings risk 'becoming a distraction.' Their simultaneous resignations demonstrate systematic corruption within Federal Reserve regional banks where senior officials routinely exploit privileged information for personal profit while setting monetary policy affecting millions of Americans during economic crisis.",
        "importance": 9,
        "tags": ["federal_reserve", "resignation", "trading_scandal", "robert_kaplan", "eric_rosengren", "institutional_corruption", "dallas_fed", "boston_fed"],
        "actors": ["Robert Kaplan", "Eric Rosengren", "Federal Reserve Bank of Dallas", "Federal Reserve Bank of Boston"],
        "sources": [
            {
                "url": "https://www.reuters.com/business/finance/dallas-fed-president-kaplan-step-down-oct-8-2021-09-27/",
                "title": "Dallas Fed President Kaplan to Step Down Oct. 8",
                "date": "2021-09-27"
            },
            {
                "url": "https://www.reuters.com/business/finance/boston-fed-president-rosengren-retire-early-due-health-reasons-2021-09-27/",
                "title": "Boston Fed President Rosengren to Retire Early Due to Health Reasons",
                "date": "2021-09-27"
            }
        ]
    },
    
    {
        "id": "2020-02-27--clarida-fed-bond-fund-trades",
        "date": "2020-02-27",
        "title": "Fed Vice Chair Clarida Trades Millions Before Rate Cuts",
        "summary": "Federal Reserve Vice Chairman Richard Clarida rotated between $1-5 million from Pimco bond funds into stock funds on February 27, 2020, just one day before Fed Chair Powell's emergency statement about coronavirus risks and weeks before the Fed began aggressive interest rate cuts. Clarida's trades demonstrate systematic pattern where Fed officials exploit advance knowledge of monetary policy decisions for personal financial gain, representing institutional capture where central bank independence is compromised by officials' personal trading activities.",
        "importance": 8,
        "tags": ["federal_reserve", "trading_scandal", "conflict_of_interest", "richard_clarida", "insider_trading", "monetary_policy", "institutional_corruption"],
        "actors": ["Richard Clarida", "Federal Reserve Board", "Jerome Powell"],
        "sources": [
            {
                "url": "https://www.wsj.com/articles/fed-officials-financial-disclosures-show-active-trading-in-2020-11632821201",
                "title": "Fed Officials' Financial Disclosures Show Active Trading in 2020",
                "date": "2021-09-28"
            }
        ]
    },
    
    {
        "id": "2017-06-15--reserve-trust-kansas-city-fed-corruption",
        "date": "2017-06-15",
        "title": "Kansas City Fed Denies Reserve Trust Master Account",
        "summary": "Federal Reserve Bank of Kansas City initially denies Reserve Trust Company's application for master account access in June 2017, one month after former Fed Governor Sarah Bloom Raskin joined the fintech's board. The initial denial would later become evidence of potential corruption when the bank reversed its decision in 2018, raising questions about whether Raskin's subsequent communications with Kansas City Fed President Esther George influenced the approval process, demonstrating systematic revolving door corruption where former Fed officials leverage their positions for private sector benefit.",
        "importance": 7,
        "tags": ["federal_reserve", "corruption", "revolving_door", "sarah_bloom_raskin", "kansas_city_fed", "reserve_trust_company", "master_account", "regulatory_capture"],
        "actors": ["Sarah Bloom Raskin", "Reserve Trust Company", "Federal Reserve Bank of Kansas City", "Esther George"],
        "sources": [
            {
                "url": "https://www.cnbc.com/2022/02/15/bank-regulator-disputes-kc-fed-claim-about-firm-linked-to-biden-nominee-raskin.html",
                "title": "State bank regulator disputes KC Fed's claim about fintech firm linked to Biden nominee Raskin",
                "date": "2022-02-15"
            }
        ]
    },
    
    {
        "id": "2018-05-15--reserve-trust-master-account-approved",
        "date": "2018-05-15",
        "title": "Kansas City Fed Approves Reserve Trust Master Account After Raskin Intervention",
        "summary": "Federal Reserve Bank of Kansas City reverses its 2017 denial and approves Reserve Trust Company's master account application, approximately nine months after former Fed Governor Sarah Bloom Raskin allegedly contacted Kansas City Fed President Esther George about the denied application. The approval raises corruption concerns about systematic revolving door influence where former Fed officials leverage relationships to benefit private sector clients, with Senator Pat Toomey later claiming he was 'stonewalled' when requesting documents about the decision process.",
        "importance": 7,
        "tags": ["federal_reserve", "corruption", "revolving_door", "sarah_bloom_raskin", "kansas_city_fed", "reserve_trust_company", "regulatory_capture", "master_account_approval"],
        "actors": ["Sarah Bloom Raskin", "Reserve Trust Company", "Federal Reserve Bank of Kansas City", "Esther George", "Pat Toomey"],
        "sources": [
            {
                "url": "https://www.cnbc.com/2022/02/15/bank-regulator-disputes-kc-fed-claim-about-firm-linked-to-biden-nominee-raskin.html",
                "title": "State bank regulator disputes KC Fed's claim about fintech firm linked to Biden nominee Raskin",
                "date": "2022-02-15"
            }
        ]
    },
    
    {
        "id": "2021-10-21--fed-announces-trading-restrictions",
        "date": "2021-10-21",
        "title": "Fed Announces 'Tough New Rules' After Trading Scandal",
        "summary": "Federal Reserve Chair Jerome Powell announces new ethics rules barring senior officials from actively trading individual securities following the Kaplan-Rosengren scandal, but critics argue the rules are inadequate and lack enforcement mechanisms. The policy gives the Fed's Designated Agency Ethics Officer 'sole discretion' to decide whether violations are material, with the Officer appointed and removable by the Fed Chair, creating systematic conflict of interest where officials can protect themselves from accountability. Senator Elizabeth Warren calls the policy 'a dismal failure' ridden with conflicts of interest.",
        "importance": 6,
        "tags": ["federal_reserve", "ethics_policy", "trading_restrictions", "jerome_powell", "regulatory_response", "elizabeth_warren", "institutional_accountability"],
        "actors": ["Jerome Powell", "Federal Reserve Board", "Elizabeth Warren"],
        "sources": [
            {
                "url": "https://www.federalreserve.gov/newsevents/pressreleases/other20211021a.htm",
                "title": "Federal Reserve Board announces new rules to bar its senior officials from investing in individual securities",
                "date": "2021-10-21"
            }
        ]
    }
]

print(f"Created {len(events)} timeline events for Federal Reserve corruption")

# Submit events using batch API
try:
    result = api.submit_events_batch(events, 'RT-90508641-fed-regional-bank-corruption')
    print("Batch submission result:", result)
    
    # Complete the priority
    completion_result = api.complete_priority('RT-90508641-fed-regional-bank-corruption', len(events))
    print("Priority completion result:", completion_result)
    
except Exception as e:
    print(f"Error submitting events: {e}")
    # Print events for manual inspection
    for event in events:
        print(f"\nEvent: {event['id']}")
        print(f"Date: {event['date']}")
        print(f"Title: {event['title']}")
        print(f"Importance: {event['importance']}")
        print(f"Tags: {', '.join(event['tags'])}")