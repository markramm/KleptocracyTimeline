# Tag Taxonomy and Guidelines

**Version**: 1.0
**Last Updated**: 2025-10-17
**Status**: Active

## Overview

This document defines the controlled tag vocabulary for timeline events. Tags provide consistent categorization, enabling better search, filtering, and analysis.

## Tag Format Standards

### Rules
1. **Lowercase only**: All tags use lowercase letters
2. **Hyphen separators**: Use hyphens (`-`) not underscores or spaces
3. **Singular form**: Prefer singular unless plural is more natural
4. **Concise**: Use shortest clear form (e.g., `crypto` not `cryptocurrency`)

### Examples
- ✅ `regulatory-capture`
- ✅ `conflict-of-interest`
- ✅ `supreme-court`
- ❌ `Regulatory Capture` (capitalized)
- ❌ `regulatory_capture` (underscores)
- ❌ `conflicts-of-interest` (plural)

## Tag Categories

### Capture Mechanisms (Primary Theme)
- `regulatory-capture` - Capture of regulatory agencies by industry
- `institutional-capture` - Capture of government institutions
- `judicial-capture` - Capture of courts and judicial system
- `legislative-capture` - Capture of Congress/legislature
- `financial-capture` - Capture of financial regulators
- `corporate-capture` - General corporate capture of government
- `media-capture` - Capture of news media outlets

### Corruption & Kleptocracy
- `corruption` - General corruption
- `kleptocracy` - Systematic theft by those in power
- `bribery` - Bribery and payoffs
- `embezzlement` - Embezzlement of public funds
- `fraud` - Fraudulent activities
- `money-laundering` - Money laundering schemes
- `systematic-corruption` - Systemic patterns of corruption
- `political-corruption` - Corruption in political systems

### Influence Mechanisms
- `revolving-door` - Movement between government and private sector
- `lobbying` - Lobbying activities
- `campaign-finance` - Campaign finance violations
- `dark-money` - Untraceable political spending
- `foreign-influence` - Foreign government influence
- `corporate-influence` - Corporate influence on policy

### Legal & Justice
- `constitutional-crisis` - Constitutional violations or crises
- `rule-of-law` - Rule of law violations
- `obstruction-of-justice` - Justice obstruction
- `justice-weaponization` - Weaponization of justice system
- `ethics-violation` - Ethics violations
- `conflict-of-interest` - Conflicts of interest
- `emoluments` - Emoluments clause violations
- `pardon` - Presidential pardons
- `constitutional-violation` - Constitutional violations
- `separation-of-powers` - Separation of powers violations

### Courts & Judiciary
- `supreme-court` - Supreme Court related
- `judicial-ethics` - Judicial ethics issues
- `court-capture` - Judicial capture

### Executive Branch
- `executive-power` - Executive power abuse
- `executive-overreach` - Executive branch overreach
- `executive-order` - Executive orders
- `presidential-authority` - Presidential authority issues

### Financial Crimes
- `insider-trading` - Insider trading
- `securities-fraud` - Securities fraud
- `financial-crime` - Financial crimes
- `tax-evasion` - Tax evasion
- `wire-fraud` - Wire fraud

### Government Contracts
- `government-contract` - Government contracts
- `no-bid-contract` - No-bid contracts
- `contract-fraud` - Contract fraud
- `procurement-abuse` - Procurement abuse

### Media & Information
- `media-control` - Media control
- `media-manipulation` - Media manipulation
- `propaganda` - Propaganda
- `disinformation` - Disinformation campaigns
- `misinformation` - Misinformation
- `media-consolidation` - Media consolidation
- `press-freedom` - Press freedom issues

### Surveillance & Security
- `surveillance` - Surveillance programs
- `warrantless-surveillance` - Warrantless surveillance
- `national-security` - National security issues
- `intelligence-abuse` - Intelligence agency abuse
- `privacy-violation` - Privacy violations

### Technology
- `crypto` - Cryptocurrency related
- `blockchain` - Blockchain technology
- `ai-safety` - AI safety issues
- `tech-regulation` - Technology regulation
- `cybersecurity` - Cybersecurity issues
- `data-privacy` - Data privacy issues

### Election & Political
- `election-interference` - Election interference
- `election-fraud` - Election fraud
- `voter-suppression` - Voter suppression
- `gerrymandering` - Gerrymandering
- `campaign-violation` - Campaign violations

### Foreign Relations
- `foreign-interference` - Foreign interference
- `sanctions` - Sanctions
- `foreign-policy` - Foreign policy
- `international-corruption` - International corruption

### Specific Countries
- `russia` - Russia related
- `china` - China related
- `saudi-arabia` - Saudi Arabia related
- `ukraine` - Ukraine related

### Agencies & Institutions
- `doj` - Department of Justice
- `fbi` - FBI
- `cia` - CIA
- `nsa` - NSA
- `sec` - Securities and Exchange Commission
- `fcc` - Federal Communications Commission
- `epa` - Environmental Protection Agency

### Administrations
- `trump-administration` - Trump administration
- `biden-administration` - Biden administration
- `obama-administration` - Obama administration
- `bush-administration` - Bush administration

### Specific Events/Programs
- `whig` - White House Iraq Group
- `iraq-war` - Iraq War
- `project-2025` - Project 2025
- `january-6` - January 6 attack

### People (use sparingly, prefer full names in actors field)
- `trump` - Donald Trump
- `biden` - Joe Biden
- `kushner` - Jared Kushner
- `musk` - Elon Musk
- `thiel` - Peter Thiel
- `cheney` - Dick Cheney
- `barr` - William Barr

### Networks
- `epstein-network` - Jeffrey Epstein network
- `koch-network` - Koch network
- `federalist-society` - Federalist Society
- `heritage-foundation` - Heritage Foundation

## Tag Migration

### Common Migrations
Tags are automatically normalized during import. Common transformations:

| Old Format | New Format | Reason |
|------------|------------|--------|
| `regulatory_capture` | `regulatory-capture` | Hyphen separator |
| `Regulatory Capture` | `regulatory-capture` | Lowercase |
| `conflicts-of-interest` | `conflict-of-interest` | Singular form |
| `ethics-violations` | `ethics-violation` | Singular form |
| `cryptocurrency` | `crypto` | Shorter standard form |
| `AI safety` | `ai-safety` | Hyphen separator |
| `pardons` | `pardon` | Singular form |

### Migration Script
To normalize all existing tags:

```bash
# Dry run (preview changes)
python3 scripts/migrate_tags.py

# Apply changes
python3 scripts/migrate_tags.py --apply

# Save detailed report
python3 scripts/migrate_tags.py --report migration_report.json
```

## Adding New Tags

When adding new tags:

1. **Check existing taxonomy** - Use existing tags when possible
2. **Follow naming conventions** - lowercase, hyphens, singular
3. **Consider categories** - Place in appropriate category
4. **Update taxonomy** - Add to `research_monitor/services/tag_taxonomy.py`
5. **Document** - Add to this file with description

### Example

```python
# In tag_taxonomy.py CANONICAL_TAGS:
'ransomware-attack': 'Ransomware attacks on infrastructure',

# In tag_taxonomy.py CATEGORIES:
'technology': [
    # ... existing tags ...
    'ransomware-attack',
]
```

## Usage Guidelines

### DO
- ✅ Use 3-7 tags per event
- ✅ Mix general and specific tags
- ✅ Include primary capture/corruption mechanism
- ✅ Tag with relevant institutions/agencies
- ✅ Use consistent spelling

### DON'T
- ❌ Create duplicate variations (`media capture` vs `media-capture`)
- ❌ Use extremely specific tags (`trump-july-2023-golf-meeting`)
- ❌ Tag every person mentioned (use actors field instead)
- ❌ Use capitalization (`Supreme Court` → use `supreme-court`)
- ❌ Use spaces or underscores (use hyphens)

### Good Example
```json
{
  "id": "2020-01-15--sec-musk-settlement",
  "title": "SEC settles with Musk over Twitter fraud",
  "tags": [
    "securities-fraud",
    "sec",
    "regulatory-capture",
    "social-media",
    "corporate-influence"
  ],
  "actors": ["Elon Musk", "SEC", "Tesla"]
}
```

### Bad Example
```json
{
  "id": "2020-01-15--sec-musk-settlement",
  "title": "SEC settles with Musk over Twitter fraud",
  "tags": [
    "Securities Fraud",
    "musk",
    "twitter",
    "sec_settlement",
    "regulatory capture",
    "Elon Musk Twitter Case 2020"
  ]
}
```

## Statistics

As of 2025-10-17:
- **3,654 unique tags** (before normalization)
- **117 canonical tags** in taxonomy
- **295 concepts** with multiple variations
- **58 migration rules** defined
- **16 tag categories**

After migration:
- **402 files** will be updated
- **1,618 tags** will be normalized (19%)
- **3 duplicate tags** will be removed

## Validation

Tags are validated automatically:
- During event creation via CLI
- During QA validation process
- During filesystem sync to database

Invalid tags receive suggestions:
```
Warning: Tag 'regulatory capture' should be 'regulatory-capture'
Warning: Tag 'AI safety' should be 'ai-safety'
```

## Future Improvements

- [ ] Add tag hierarchy (parent-child relationships)
- [ ] Create tag aliases for search
- [ ] Implement tag trending analysis
- [ ] Add tag co-occurrence patterns
- [ ] Create tag recommendation system

## See Also

- `research_monitor/services/tag_taxonomy.py` - Tag normalization code
- `scripts/migrate_tags.py` - Tag migration script
- `CLAUDE.md` - Research workflow guidelines
- `CONTRIBUTING.md` - Contribution guidelines
