#!/usr/bin/env python3

from research_api import ResearchAPI
import json

def main():
    api = ResearchAPI(base_url='http://localhost:5560', api_key='test')
    
    # Create comprehensive timeline events for cyber mercenary industry with correct source format
    events = [
        {
            'id': '2014-01-01--candiru-spyware-company-founding-eran-shorer-yaakov-weizman',
            'date': '2014-01-01',
            'title': 'Candiru Spyware Company Founded by Israeli Veterans',
            'summary': 'Candiru, Israel\'s second-largest cyber-espionage firm after NSO Group, is founded by Eran Shorer and Yaakov Weizman. The company would undergo multiple name changes from 2014-2020 before operating under Saito Tech Ltd. Isaac Zack, an early NSO Group investor, serves as Candiru\'s chairman, establishing deep connections between the two spyware giants. Candiru receives investment from "Founders Group," an angel investment syndicate operated by NSO Group co-founders Omri Lavie and Shalev Hulio, demonstrating systematic coordination in Israel\'s mercenary surveillance industry.',
            'tags': ['candiru', 'spyware', 'israel', 'nso_group', 'surveillance_industry', 'cyber_mercenaries'],
            'actors': ['Eran Shorer', 'Yaakov Weizman', 'Isaac Zack', 'Omri Lavie', 'Shalev Hulio', 'Candiru', 'NSO Group', 'Saito Tech Ltd'],
            'sources': [
                {
                    'title': 'Hooking Candiru: Another Mercenary Spyware Vendor Comes into Focus',
                    'url': 'https://citizenlab.ca/2021/07/hooking-candiru-another-mercenary-spyware-vendor-comes-into-focus/',
                    'outlet': 'The Citizen Lab',
                    'date': '2021-07-15'
                },
                {
                    'title': 'Candiru (spyware company) - Wikipedia',
                    'url': 'https://en.wikipedia.org/wiki/Candiru_(spyware_company)',
                    'outlet': 'Wikipedia',
                    'date': '2024-01-01'
                }
            ],
            'importance': 8
        },
        {
            'id': '2017-01-01--cytrox-establishment-north-macedonia-spyware-development',
            'date': '2017-01-01', 
            'title': 'Cytrox Established in North Macedonia as NSO Competitor',
            'summary': 'Cytrox is established as a startup in North Macedonia with initial funding from Israel Aerospace Industries, creating a new front for Israeli intelligence-linked spyware development. CEO Ivo Malinkovski, a 30-year-old from Skopje, leads operations while the company begins developing Predator spyware to compete with NSO Group\'s Pegasus. On October 6, 2017, Cytrox and Cyshark formally request authorization from North Macedonia\'s Ministry of Interior for manufacturing, sale, resale, and export of surveillance software, despite government claims of being unaware of the operations.',
            'tags': ['cytrox', 'north_macedonia', 'spyware', 'predator', 'israel_aerospace_industries', 'surveillance_industry'],
            'actors': ['Ivo Malinkovski', 'Cytrox', 'Israel Aerospace Industries', 'North Macedonia Ministry of Interior', 'Cyshark'],
            'sources': [
                {
                    'title': 'Cytrox - Wikipedia',
                    'url': 'https://en.wikipedia.org/wiki/Cytrox',
                    'outlet': 'Wikipedia',
                    'date': '2024-01-01'
                },
                {
                    'title': 'Pegasus vs. Predator: Dissident Doubly-Infected iPhone Reveals Cytrox Mercenary Spyware',
                    'url': 'https://citizenlab.ca/2021/12/pegasus-vs-predator-dissidents-doubly-infected-iphone-reveals-cytrox-mercenary-spyware/',
                    'outlet': 'The Citizen Lab',
                    'date': '2021-12-16'
                }
            ],
            'importance': 8
        },
        {
            'id': '2019-01-01--intellexa-alliance-formation-nso-competitor-consortium',
            'date': '2019-01-01',
            'title': 'Intellexa Alliance Forms as "Star Alliance of Spyware" to Compete with NSO',
            'summary': 'The Intellexa Alliance is formed as a marketing consortium of mercenary surveillance vendors to compete against NSO Group and Verint. The alliance includes Nexa Technologies (formerly Amesys), WiSpear/Passitora Ltd., Cytrox, and Senpai Technologies. Former Israeli Defense Forces commander Tal Dilian acquires Cytrox for under $5 million, rescuing the company and integrating it into the broader Intellexa ecosystem. This systematic coordination creates a European-based alternative to Israeli spyware dominance, with operations spanning North Macedonia, Greece, Hungary, and Ireland.',
            'tags': ['intellexa', 'tal_dilian', 'cytrox', 'spyware_consortium', 'nexa_technologies', 'surveillance_industry'],
            'actors': ['Tal Dilian', 'Intellexa', 'Nexa Technologies', 'WiSpear', 'Passitora Ltd', 'Cytrox', 'Senpai Technologies', 'NSO Group', 'Verint'],
            'sources': [
                {
                    'title': 'Intellexa and Cytrox: From fixer-upper to Intel Agency-grade spyware',
                    'url': 'https://blog.talosintelligence.com/intellexa-and-cytrox-intel-agency-grade-spyware/',
                    'outlet': 'Cisco Talos Intelligence',
                    'date': '2022-08-18'
                },
                {
                    'title': 'Treasury Sanctions Members of the Intellexa Commercial Spyware Consortium',
                    'url': 'https://home.treasury.gov/news/press-releases/jy2155',
                    'outlet': 'US Treasury Department',
                    'date': '2024-03-05'
                }
            ],
            'importance': 9
        },
        {
            'id': '2021-11-03--candiru-nso-group-us-entity-list-commerce-department',
            'date': '2021-11-03',
            'title': 'US Commerce Department Adds Candiru and NSO Group to Entity List',
            'summary': 'The US Commerce Department\'s Bureau of Industry and Security adds Israeli spyware companies NSO Group and Candiru to the Entity List for developing surveillance software used to spy on journalists, activists, and government officials. This action restricts US companies from selling technology to these firms without licenses. The designation represents the first major US government action against the systematic use of commercial spyware for authoritarian surveillance, targeting companies whose tools have been used against American citizens and allies worldwide.',
            'tags': ['candiru', 'nso_group', 'us_sanctions', 'entity_list', 'commerce_department', 'spyware_regulation'],
            'actors': ['US Commerce Department', 'Bureau of Industry and Security', 'Candiru', 'NSO Group'],
            'sources': [
                {
                    'title': 'Malicious activities: US blacklists Israel NSO Group and Candiru spyware firms',
                    'url': 'https://www.timesofisrael.com/us-blacklists-israels-nso-group-and-candiru-spyware-firms/',
                    'outlet': 'The Times of Israel',
                    'date': '2021-11-03'
                },
                {
                    'title': 'Two more foreign spyware firms blacklisted by US',
                    'url': 'https://therecord.media/two-more-foreign-spyware-firms-blacklisted-by-us',
                    'outlet': 'The Record',
                    'date': '2021-11-03'
                }
            ],
            'importance': 9
        },
        {
            'id': '2023-07-01--cytrox-intellexa-us-entity-list-trafficking-cyber-exploits',
            'date': '2023-07-01',
            'title': 'US Adds Intellexa and Cytrox to Entity List for Cyber Exploit Trafficking',
            'summary': 'The US Commerce Department adds surveillance technology vendors Intellexa and Cytrox to the Entity List for "trafficking in cyber exploits used to gain access to information systems, threatening the privacy and security of individuals and organizations worldwide." Specific entities sanctioned include Intellexa S.A. (Greece), Cytrox Holdings Crt (Hungary), Intellexa Limited (Ireland), and Cytrox AD (North Macedonia). This action expands US efforts to combat the global spyware industry beyond Israeli companies to European-based consortiums.',
            'tags': ['intellexa', 'cytrox', 'us_sanctions', 'entity_list', 'cyber_exploits', 'commerce_department'],
            'actors': ['US Commerce Department', 'Bureau of Industry and Security', 'Intellexa S.A.', 'Cytrox Holdings Crt', 'Intellexa Limited', 'Cytrox AD'],
            'sources': [
                {
                    'title': 'US Gov adds surveillance firms Cytrox and Intellexa to Entity List',
                    'url': 'https://securityaffairs.com/148603/laws-and-regulations/us-gov-cytrox-intellexa-entity-list.html',
                    'outlet': 'Security Affairs',
                    'date': '2023-07-14'
                },
                {
                    'title': 'Two more foreign spyware firms blacklisted by US',
                    'url': 'https://therecord.media/spyware-companies-commerce-department-entity-list-intellexa-cytrox',
                    'outlet': 'The Record',
                    'date': '2023-07-14'
                }
            ],
            'importance': 8
        },
        {
            'id': '2024-03-05--treasury-sanctions-intellexa-consortium-tal-dilian',
            'date': '2024-03-05',
            'title': 'Treasury Department Sanctions Intellexa Consortium and Tal Dilian',
            'summary': 'The US Treasury Department\'s Office of Foreign Assets Control (OFAC) designates two individuals and five entities associated with the Intellexa Consortium for developing commercial spyware used to target Americans, including US government officials, journalists, and policy experts. Key sanctioned individuals include Israeli founder Tal Jonathan Dilian and corporate specialist Sara Aleksandra Fayssal Hamou. Five corporate entities operating under Intellexa, Cytrox, and Thalestris Limited across Greece, Hungary, Ireland, and North Macedonia are sanctioned. This marks the first Treasury sanctions against spyware industry actors, representing escalated US efforts to combat systematic surveillance targeting Americans.',
            'tags': ['treasury_department', 'ofac', 'intellexa', 'tal_dilian', 'spyware_sanctions', 'financial_sanctions'],
            'actors': ['US Treasury Department', 'Office of Foreign Assets Control', 'Tal Jonathan Dilian', 'Sara Aleksandra Fayssal Hamou', 'Intellexa Consortium', 'Thalestris Limited'],
            'sources': [
                {
                    'title': 'Treasury Sanctions Members of the Intellexa Commercial Spyware Consortium',
                    'url': 'https://home.treasury.gov/news/press-releases/jy2155',
                    'outlet': 'US Treasury Department',
                    'date': '2024-03-05'
                },
                {
                    'title': 'U.S. sanctions maker of Predator spyware',
                    'url': 'https://cyberscoop.com/predator-intellexa-cytrox-sanctions/',
                    'outlet': 'CyberScoop',
                    'date': '2024-03-05'
                }
            ],
            'importance': 9
        }
    ]
    
    print('Created', len(events), 'events with properly formatted sources')
    
    # Submit events batch
    result = api.submit_events_batch(events, 'RT-EXP-6AAA129F-cyber-mercenary-industry-nso-competitors')
    print(f'\nSubmission result: {result}')
    
    return result

if __name__ == '__main__':
    main()