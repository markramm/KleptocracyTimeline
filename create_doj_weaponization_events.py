#!/usr/bin/env python3

import json
from research_api import ResearchAPI

# Initialize API
api = ResearchAPI(base_url='http://localhost:5560', api_key='test')

# Create timeline events for DOJ weaponization and prosecutor targeting
events = [
    {
        "id": "2006-12-07--bush-administration-attorney-firings-scandal",
        "date": "2006-12-07",
        "title": "Bush Administration Fires Seven U.S. Attorneys in Coordinated Purge",
        "summary": "Bush administration Justice Department fires seven U.S. attorneys in coordinated operation later determined to be politically motivated retaliation. Fired prosecutors included David Iglesias (New Mexico), Carol Lam (California), Daniel Bogden (Nevada), Paul Charlton (Arizona), Margaret Chiara (Michigan), Todd Graves (Missouri), and John McKay (Washington). Investigation revealed Karl Rove was 'very agitated' over Iglesias's refusal to expedite corruption investigation against Democratic candidate before 2006 election. DOJ Inspector General's 2008 report found firings were 'arbitrary', 'fundamentally flawed', and 'raised doubts about integrity of Department prosecution decisions', establishing systematic template for DOJ weaponization against prosecutors who refuse political demands.",
        "importance": 8,
        "tags": ["doj_weaponization", "attorney_firings", "karl_rove", "political_prosecutions", "bush_administration", "prosecutor_targeting", "institutional_corruption"],
        "actors": ["Karl Rove", "David Iglesias", "Carol Lam", "Alberto Gonzales", "Bush Administration", "Department of Justice"],
        "sources": [
            {
                "url": "https://en.wikipedia.org/wiki/2006_dismissal_of_U.S._attorneys",
                "title": "2006 dismissal of U.S. attorneys",
                "outlet": "Wikipedia",
                "date": "2006-12-07"
            }
        ]
    },

    {
        "id": "2025-01-27--trump-doj-fires-jack-smith-prosecutors",
        "date": "2025-01-27",
        "title": "Trump DOJ Fires Jack Smith Special Counsel Team in Systematic Purge",
        "summary": "Trump administration Justice Department fires at least 35 DOJ employees who worked on Special Counsel Jack Smith investigations into Trump's classified documents case and January 6th election interference. Fired prosecutors included career attorneys Molly Gaston, J.P. Cooney, Anne McNamara, and Mary Dohrmann. Acting Attorney General James McHenry stated 'the Acting Attorney General does not trust these officials to assist in faithfully implementing the President's agenda', breaking traditional norm that career prosecutors remain across administrations. The unprecedented targeting of career prosecutors who investigated a president demonstrates systematic DOJ weaponization designed to intimidate future investigations and transform Justice Department into Trump's personal law firm.",
        "importance": 9,
        "tags": ["doj_weaponization", "trump_administration", "special_counsel", "prosecutor_firings", "jack_smith", "career_prosecutors", "institutional_capture"],
        "actors": ["James McHenry", "Jack Smith", "Molly Gaston", "J.P. Cooney", "Anne McNamara", "Mary Dohrmann", "Trump Administration"],
        "sources": [
            {
                "url": "https://www.npr.org/2025/01/27/nx-s1-5276334/justice-department-firings-trump-special-counsel-jack-smith",
                "title": "Justice Department moves to fire at least 12 officials who investigated Trump",
                "outlet": "NPR",
                "date": "2025-01-27"
            }
        ]
    },

    {
        "id": "2025-02-15--bondi-establishes-weaponization-working-group",
        "date": "2025-02-15",
        "title": "Attorney General Bondi Establishes 'Weaponization Working Group' to Target Prosecutors",
        "summary": "Attorney General Pam Bondi establishes 'Weaponization Working Group' as first priority after confirmation, tasked with investigating 'activities of all departments and agencies exercising civil or criminal enforcement authority over the last four years.' Bondi declares intention to 'investigate the investigators' and 'prosecute the prosecutors' who worked on Trump-related cases. The working group identifies career DOJ employees for firing based on their involvement in prosecuting Trump, creating systematic mechanism for political retaliation against prosecutors. This institutionalizes DOJ weaponization through formal bureaucratic structure designed to punish prosecutors for conducting investigations, representing unprecedented transformation of Justice Department into political enforcement arm.",
        "importance": 8,
        "tags": ["doj_weaponization", "pam_bondi", "weaponization_working_group", "prosecutor_targeting", "institutional_capture", "political_retaliation"],
        "actors": ["Pam Bondi", "Weaponization Working Group", "Department of Justice", "Trump Administration"],
        "sources": [
            {
                "url": "https://www.cbsnews.com/news/justice-department-firings-include-trump-investigators-jan-6-prosecutors/",
                "title": "Justice Department purge continues; firings include Trump classified document case investigators and Jan. 6 prosecutors",
                "outlet": "CBS News",
                "date": "2025-02-15"
            }
        ]
    },

    {
        "id": "2025-03-31--trump-doj-fires-50-prosecutors",
        "date": "2025-03-31",
        "title": "Trump Administration Fires 50 Prosecutors and Deputies in DOJ Overhaul",
        "summary": "Trump administration expands prosecutor purge by firing 50 prosecutors and deputy prosecutors in systematic DOJ overhaul designed to eliminate career officials who investigated Trump or his allies. The mass firings represent unprecedented targeting of career Justice Department personnel, breaking decades of tradition that insulates prosecutors from political interference. Critics warn the systematic removal of experienced prosecutors creates 'chilling effect' designed to deter future investigations of Trump administration, while compromising DOJ's institutional independence. The coordinated purge demonstrates systematic weaponization where Justice Department becomes instrument of political retaliation rather than impartial law enforcement agency.",
        "importance": 9,
        "tags": ["doj_weaponization", "prosecutor_purge", "mass_firings", "trump_administration", "institutional_destruction", "political_retaliation"],
        "actors": ["Trump Administration", "Department of Justice", "Career Prosecutors"],
        "sources": [
            {
                "url": "https://www.axios.com/2025/03/31/trump-doj-prosecutors-fired",
                "title": "Trump admin fires 50 prosecutors and deputies in DOJ overhaul",
                "outlet": "Axios",
                "date": "2025-03-31"
            }
        ]
    },

    {
        "id": "2025-07-12--bondi-fires-20-trump-prosecution-employees",
        "date": "2025-07-12",
        "title": "Bondi Fires 20 Justice Department Employees Tied to Trump Prosecutions",
        "summary": "Attorney General Pam Bondi fires 20 additional Justice Department employees specifically identified for their involvement in prosecuting Trump, including prosecutors who worked on January 6th cases and classified documents investigation. The targeted firings represent continuation of systematic purge designed to eliminate any DOJ personnel who participated in investigating or prosecuting Trump. The systematic targeting demonstrates institutional capture where Justice Department personnel decisions are based on loyalty to Trump rather than professional qualifications or legal expertise. Bondi's systematic elimination of prosecutors creates precedent for political control over career law enforcement officials, weaponizing DOJ hiring and firing to serve presidential political interests.",
        "importance": 8,
        "tags": ["pam_bondi", "doj_weaponization", "trump_prosecutions", "systematic_purge", "institutional_capture", "political_loyalty"],
        "actors": ["Pam Bondi", "Department of Justice", "Trump Prosecutors", "January 6 Prosecutors"],
        "sources": [
            {
                "url": "https://www.washingtonpost.com/national-security/2025/07/12/bondi-trump-justice-fbi-firings/",
                "title": "Bondi fires 20 Justice Department employees tied to Trump prosecutions",
                "outlet": "Washington Post",
                "date": "2025-07-12"
            }
        ]
    }
]

print(f"Created {len(events)} timeline events for DOJ weaponization")

# Submit events using batch API
try:
    result = api.submit_events_batch(events, 'RT-TTT-2025-BATCH2-DOJ-PROSECUTOR-TARGETING')
    print("Batch submission result:", result)
    
    # Complete the priority
    completion_result = api.complete_priority('RT-TTT-2025-BATCH2-DOJ-PROSECUTOR-TARGETING', len(events))
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