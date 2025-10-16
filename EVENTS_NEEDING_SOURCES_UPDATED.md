# Events Needing Better Sources - Updated Analysis

**Generated**: 2025-10-14 (Post Validation Run #11)

## Summary Statistics

### Overall Progress
- **Total events in timeline**: 1,554
- **Events with adequate sources (3+)**: 1,069 (68.8%)
- **Events needing better sources (<3)**: 485 (31.2%)

### Improvement from Previous Analysis
- **Previous total needing sources**: 735 events (47.4%)
- **Current total needing sources**: 485 events (31.2%)
- **Events improved**: ~250 events
- **Improvement**: 16.2 percentage point reduction

### Breakdown by Source Count
- **0 sources**: 2 events (down from 2)
- **1 source**: 139 events (down from 196)
- **2 sources**: 344 events (down from 537)

### Importance Breakdown
- **Importance 10 (critical)**: 15 events
- **Importance 9 (major)**: 117 events
- **Importance 8 (significant)**: 196 events
- **Importance 7 (notable)**: 95 events
- **Importance 6 and below**: 62 events

## Top Priority Events (Importance 10)

### Events with Only 1 Source (Highest Priority)

1. **Powell Authors Bellotti Decision** (1978-04-26)
   - Current: 1 source | Needs: 2 more
   - Importance: 10
   - ID: `1978-04-26--powell-bellotti-decision-corporate-political-speech-rights`

2. **Barre Seid Donates $1.6 Billion to Leonard Leo Dark Money Network** (2021-01-01)
   - Current: 1 source | Needs: 2 more
   - Importance: 10
   - ID: `2021-01-01--barre-seid-1-6-billion-donation-leonard-leo-network`

### Events with 2 Sources (Need 1 More)

3. **Federalist Society Established** (1982-04-25)
   - Current: 2 sources | Needs: 1 more
   - Importance: 10

4. **Clinton Signs Gramm-Leach-Bliley Act** (1999-11-12)
   - Current: 2 sources | Needs: 1 more
   - Importance: 10

5. **Meta Eliminates Fact-Checking Program** (2025-01-07)
   - Current: 2 sources | Needs: 1 more
   - Importance: 10

6. **Clinton Signs Commodity Futures Modernization Act** (2000-12-21)
   - Current: 2 sources | Needs: 1 more
   - Importance: 10

7. **Supreme Court Backs Discovery in Argentina Debt Case** (2014-06-16)
   - Current: 2 sources | Needs: 1 more
   - Importance: 10

8. **Cambridge Analytica Deploys Facebook Data** (2016-01-01)
   - Current: 2 sources | Needs: 1 more
   - Importance: 10

9. **100,000+ Emails from Ehud Barak Hacked** (2025-05-01)
   - Current: 2 sources | Needs: 1 more
   - Importance: 10

10. **Trump Tells Acting AG "Say Election Was Corrupt"** (2020-12-27)
    - Current: 2 sources | Needs: 1 more
    - Importance: 10

11. **Texas House Democrats Flee to Illinois** (2025-07-17)
    - Current: 2 sources | Needs: 1 more
    - Importance: 10

12. **Paul Manafort Shares Trump Campaign Data with Russian Agent** (2016-05-01)
    - Current: 2 sources | Needs: 1 more
    - Importance: 10

13. **Trump Fires Joint Chiefs Chairman and Navy Chief** (2025-02-22)
    - Current: 2 sources | Needs: 1 more
    - Importance: 10

14. **Trump Administration Claims Absolute Immunity** (2019-04-18)
    - Current: 2 sources | Needs: 1 more
    - Importance: 10

15. **J.D. Vance Inaugurated as Vice President** (2025-01-20)
    - Current: 2 sources | Needs: 1 more
    - Importance: 10

## Recommended Next Steps

### Priority 1: High-Importance, Single Source Events
Focus on the **139 events with only 1 source**, especially:
- 15 events with importance 10
- ~30-40 events with importance 9
These need 2 additional credible sources each.

### Priority 2: High-Importance, Two Source Events
Enhance the **344 events with 2 sources**, prioritizing:
- Importance 10 events (13 remaining)
- Importance 9 events (~70-80 remaining)
These need 1 additional credible source each.

### Priority 3: Zero Source Events
Address the **2 events with 0 sources** immediately - these should be researched comprehensively or considered for rejection.

## Creating Next Validation Run

To systematically process these remaining events:

```bash
# Create validation run for single-source high-importance events
python3 research_cli.py validation-runs-create \
  --run-type source_quality \
  --target-count 150 \
  --focus-unvalidated \
  --min-importance 8 \
  --created-by "single-source-priority-batch"
```

## Quality Metrics

**Validation Run #11 Results:**
- Events processed: 333/338 (98.5%)
- Average quality score: 8.0-8.5/10
- Sources added: 2-3 per event
- Primary sources used: Reuters, AP, Bloomberg, NPR, PBS, ProPublica, ICIJ
- Processing efficiency: ~3 minutes per event

## Notes

- After validation run #11, source quality improved significantly for 333 events
- Remaining events require continued systematic enhancement
- Focus should remain on importance 8+ events with 1-2 sources
- Total remaining work: approximately 485 events across all importance levels
