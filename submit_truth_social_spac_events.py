#!/usr/bin/env python3

from research_api import ResearchAPI
import json

def main():
    api = ResearchAPI(base_url='http://localhost:5560', api_key='test')
    
    # Create timeline events for Truth Social SPAC fraud network investigation and enforcement
    events = [
        {
            'id': '2023-03-22--patrick-orlando-fired-dwac-ceo-unprecedented-headwinds',
            'date': '2023-03-22',
            'title': 'Digital World Acquisition Corp Fires CEO Patrick Orlando Amid SEC Investigation',
            'summary': 'Digital World Acquisition Corp (DWAC) fires CEO Patrick Orlando, citing "unprecedented headwinds" that necessitated a leadership change. Orlando, a former Deutsche Bank trader and founder of Benessere Capital, had been central to the SPAC\'s plan to merge with Trump Media & Technology Group. The firing occurs amid ongoing SEC and federal prosecutor investigations into potential securities fraud related to pre-IPO merger discussions with Truth Social. Orlando\'s removal represents a significant development in the systematic financial fraud investigation surrounding the Trump media venture.',
            'tags': ['dwac', 'patrick_orlando', 'truth_social', 'spac_fraud', 'sec_investigation', 'trump_media'],
            'actors': ['Patrick Orlando', 'Digital World Acquisition Corp', 'DWAC', 'Trump Media & Technology Group', 'SEC'],
            'sources': [
                {
                    'title': 'Trump-linked Digital World Acquisition Corp fires CEO Patrick Orlando',
                    'url': 'https://www.cnbc.com/2023/03/22/trump-linked-digital-world-acquisition-corp-fires-ceo.html',
                    'outlet': 'CNBC',
                    'date': '2023-03-22'
                }
            ],
            'importance': 8
        },
        {
            'id': '2023-06-29--trust-social-insider-trading-arrests-shvartsman-garelick',
            'date': '2023-06-29',
            'title': 'FBI Arrests Three in "Trust Social" Investigation for DWAC Insider Trading',
            'summary': 'FBI and HSI agents arrest three individuals in coordinated raids as part of "Trust Social," a joint investigation targeting insider trading related to Digital World Acquisition Corp (DWAC) and Trump Media. Michael Shvartsman, his brother Gerald Shvartsman, and Bruce Garelick (investment chief of Rocket One Capital) are charged with conspiracy and securities fraud for allegedly trading DWAC shares based on nonpublic information about the Truth Social merger. The suspects had signed confidentiality agreements but purchased hundreds of thousands of dollars in DWAC shares before the public announcement, facing potential sentences of 90-130 years. Garelick had secured a seat on DWAC\'s board through their investments.',
            'tags': ['dwac', 'insider_trading', 'fbi_arrests', 'trust_social_investigation', 'truth_social', 'securities_fraud'],
            'actors': ['Michael Shvartsman', 'Gerald Shvartsman', 'Bruce Garelick', 'FBI', 'HSI', 'Rocket One Capital', 'Digital World Acquisition Corp'],
            'sources': [
                {
                    'title': 'The wild probe into investors of DWAC, Trump Media\'s proposed merger ally',
                    'url': 'https://www.washingtonpost.com/technology/2024/02/03/trump-social-dwac-investigation/',
                    'outlet': 'The Washington Post',
                    'date': '2024-02-03'
                }
            ],
            'importance': 9
        },
        {
            'id': '2023-07-18--sec-charges-dwac-material-misrepresentations-18-million-penalty',
            'date': '2023-07-18',
            'title': 'SEC Charges DWAC with Securities Fraud, Imposes $18 Million Penalty',
            'summary': 'The Securities and Exchange Commission announces settled fraud charges against Digital World Acquisition Corp for making material misrepresentations to investors about merger discussions with Trump Media & Technology Group. The SEC found that dating back to February 2021, individuals who would later become DWAC\'s leadership had extensive SPAC merger discussions with TMTG, contradicting public filings that claimed no such discussions had occurred. DWAC agrees to pay an $18 million civil penalty to settle the charges. The enforcement action demonstrates systematic deception of investors about the predetermined nature of the SPAC merger, a violation of securities laws requiring disclosure of material information.',
            'tags': ['sec_charges', 'dwac', 'securities_fraud', 'trump_media', 'spac_fraud', 'regulatory_enforcement'],
            'actors': ['Securities and Exchange Commission', 'Digital World Acquisition Corp', 'Trump Media & Technology Group', 'SEC'],
            'sources': [
                {
                    'title': 'SEC Charges Digital World SPAC for Material Misrepresentations to Investors',
                    'url': 'https://www.sec.gov/newsroom/press-releases/2023-135',
                    'outlet': 'US Securities and Exchange Commission',
                    'date': '2023-07-18'
                }
            ],
            'importance': 9
        },
        {
            'id': '2024-07-17--sec-sues-patrick-orlando-securities-fraud-allegations',
            'date': '2024-07-17',
            'title': 'SEC Files Securities Fraud Lawsuit Against Former DWAC CEO Patrick Orlando',
            'summary': 'The Securities and Exchange Commission files a federal lawsuit against Patrick Orlando, former CEO and Chairman of Digital World Acquisition Corporation, alleging securities fraud in connection with DWAC\'s initial public offering and proposed merger with Trump Media. The SEC alleges Orlando made materially false and misleading statements in SEC filings, claiming DWAC had no discussions with potential merger targets when extensive negotiations with Trump Media had occurred since February 2021. The complaint details how Orlando initially pursued the TMTG merger through another SPAC before forming a plan in Spring 2021 to use DWAC instead. This represents the culmination of a multi-year investigation into systematic deception of public investors.',
            'tags': ['sec_lawsuit', 'patrick_orlando', 'securities_fraud', 'dwac', 'trump_media', 'spac_fraud'],
            'actors': ['Securities and Exchange Commission', 'Patrick Orlando', 'Digital World Acquisition Corp', 'Trump Media & Technology Group'],
            'sources': [
                {
                    'title': 'SEC Sues Digital World Ex-CEO Patrick Orlando, Alleging Securities Fraud',
                    'url': 'https://www.bloomberg.com/news/articles/2024-07-17/sec-sues-ex-ceo-of-digital-world-alleging-securities-fraud',
                    'outlet': 'Bloomberg',
                    'date': '2024-07-17'
                },
                {
                    'title': 'Patrick Orlando SEC Complaint',
                    'url': 'https://www.sec.gov/files/litigation/complaints/2024/comp26051.pdf',
                    'outlet': 'US Securities and Exchange Commission',
                    'date': '2024-07-17'
                }
            ],
            'importance': 9
        }
    ]
    
    print('Created', len(events), 'events for Truth Social SPAC fraud network investigation')
    print('Events span from 2023-2024 covering:')
    for event in events:
        print(f'- {event["date"]}: {event["title"]}')
    
    # Submit events batch
    result = api.submit_events_batch(events, 'RT-EXP-0A6CB614-truth-social-spac-fraud-network')
    print(f'\nSubmission result: {result}')
    
    return result

if __name__ == '__main__':
    main()