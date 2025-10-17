# Contributing to Kleptocracy Timeline

Thank you for helping document threats to democracy! This guide will help you contribute effectively.

## 🎯 What We're Looking For

### Events That Belong Here

✅ **Include events that:**
- Demonstrate institutional capture or corruption
- Show patterns of democratic erosion
- Involve abuse of power for private gain
- Reveal systemic rather than isolated problems
- Can be verified through multiple sources
- Have specific dates and concrete outcomes

❌ **Exclude events that:**
- Are purely partisan disagreements
- Lack credible sources
- Are speculation or predictions (unless marked as such)
- Focus on personal scandals without systemic impact
- Cannot be independently verified

## 📝 Adding New Events

### Step 1: Check for Duplicates

Search existing events first:
```bash
grep -r "your search term" timeline_data/events/
```

### Step 2: Choose Your Format

We support **two formats** for timeline events:

**JSON Format** (`.json`) - Best for:
- Programmatic creation
- Strict structure requirements
- Automated workflows

**Markdown Format** (`.md`) - Best for:
- Manual editing in text editors
- Editing directly on GitHub
- Community contributions
- Longer, formatted summaries

Both formats are fully equivalent. Use whichever you're more comfortable with!

### Step 3: Create Your Event File

#### Option A: JSON Format

Create a new file in `timeline_data/events/` named:
```
YYYY-MM-DD--brief-description.json
```

**JSON Template:**

```json
{
  "id": "YYYY-MM-DD--brief-description",
  "date": "YYYY-MM-DD",
  "title": "Factual, neutral title without editorializing",
  "summary": "Objective description of what happened. Include: What specifically occurred, which institutions/people were involved, what the immediate impact was, and why this represents a systemic issue. Keep it factual. No speculation or editorial language.",
  "importance": 7,
  "status": "confirmed",
  "location": "City, State",
  "actors": [
    "Person Name (Role)",
    "Organization Name"
  ],
  "tags": [
    "democratic-erosion",
    "regulatory-capture"
  ],
  "sources": [
    {
      "title": "Exact Article Headline",
      "url": "https://original-source.com/article",
      "publisher": "Publication Name",
      "date": "2024-01-15",
      "tier": 1,
      "archive_url": "https://web.archive.org/..."
    }
  ]
}
```

#### Option B: Markdown Format

Create a new file in `timeline_data/events/` named:
```
YYYY-MM-DD--brief-description.md
```

**Markdown Template:**

```markdown
---
id: YYYY-MM-DD--brief-description
date: YYYY-MM-DD
title: Factual, neutral title without editorializing
importance: 7
status: confirmed
location: City, State
actors:
  - Person Name (Role)
  - Organization Name
tags:
  - democratic-erosion
  - regulatory-capture
sources:
  - title: Exact Article Headline
    url: https://original-source.com/article
    publisher: Publication Name
    date: 2024-01-15
    tier: 1
    archive_url: https://web.archive.org/...
---

Objective description of what happened. Include:
- What specifically occurred
- Which institutions/people were involved
- What the immediate impact was
- Why this represents a systemic issue

Keep it factual. No speculation or editorial language.

## Background

You can use standard Markdown formatting:
- **Bold** for emphasis
- *Italics* for titles
- [Links](https://example.com) for references
- Lists for clarity

## Significance

Explain why this event matters in the broader context...
```

**Benefits of Markdown Format:**
- ✅ Easier to edit directly on GitHub
- ✅ Better for longer summaries with formatting
- ✅ More readable in text editors
- ✅ Supports headers, lists, bold, italics
- ✅ Lower barrier to entry for contributors

For complete format documentation, see [timeline/docs/EVENT_FORMAT.md](timeline/docs/EVENT_FORMAT.md)

### Step 4: Validate Your Event

Before submitting, run:
```bash
python3 tools/validation/validate_timeline_dates.py
```

### Step 5: Submit Pull Request

1. Fork this repository
2. Create a branch: `add-event-YYYY-MM-DD-description`
3. Add your event file
4. Commit with message: `Add: YYYY-MM-DD event description`
5. Open a Pull Request

## ✅ Verification Process

### For `pending` → `confirmed` status:

1. **Multiple Sources**: At least 2 credible sources required
2. **Source Review**: Reviewers will check each source
3. **Archive Creation**: We'll archive all sources
4. **Fact Check**: Cross-reference with other reporting
5. **Community Review**: Two approvals needed

### Source Quality Tiers

**Tier 1** (Highest credibility):
- Court documents
- Government reports
- Academic research
- Official statements

**Tier 2** (Standard credibility):
- Major newspapers
- Investigative journalism
- Wire services (AP, Reuters)
- Established NGO reports

**Tier 3** (Needs corroboration):
- Opinion pieces with facts
- Partisan sources
- Social media posts
- Single-source claims

## 🏷️ Tagging Guidelines

### System Pattern Tags
- `democratic-erosion` - Weakening of democratic norms
- `kleptocratic-capture` - Using power for private enrichment
- `regulatory-capture` - Agencies serving those they regulate
- `judicial-capture` - Court system compromise
- `electoral-manipulation` - Voting/election interference
- `disinformation` - Coordinated false information campaigns
- `institutional-decay` - Breakdown of governing norms
- `authoritarian-tactics` - Anti-democratic methods

### Actor Tags
- `executive-branch`
- `legislative-branch`
- `judicial-branch`
- `state-government`
- `federal-government`
- `tech-platforms`
- `media-manipulation`

## 🔧 For Developers

### Running Tests

```bash
# Validate all timeline data
python3 tools/validation/validate_timeline_dates.py

# Check for broken links
python3 tools/archiving/link_check.py timeline_data/events/

# Build searchable index
python3 tools/generation/build_timeline_index.py
```

### Setting Up Development Environment

```bash
# Clone the repo
git clone https://github.com/[USERNAME]/kleptocracy-timeline
cd kleptocracy-timeline

# Install Python dependencies
pip install -r requirements.txt

# Install viewer dependencies
cd viewer && npm install
```

## 📚 Writing Style Guide

### Titles
- State facts, not conclusions
- ❌ "Trump's Corrupt Deal with..."
- ✅ "Administration Awards Contract to Major Donor"

### Summaries
- Use past tense for completed events
- Include specific dates and numbers
- Name all key actors
- Explain systemic significance
- Avoid loaded language

### Language Guidelines for Corruption Timeline

#### ✅ Appropriate Language
- **"Corruption"** - When factually documented and sourced
- **"Financial corruption"** - For monetary conflicts of interest
- **"Systematic corruption"** - For institutional capture patterns
- **"Violated norm of..."** - For norm-breaking behavior
- **"Previously unprecedented..."** - For historical firsts
- **"Departed from tradition..."** - For institutional changes
- **"Documents show..."** - For evidence-based claims

#### ⚠️ Use With Caution (Require Strong Sources)
- **"Corrupt"** as adjective - Should be backed by legal findings or clear evidence
- **"Fraudulent"** - Requires documentation or legal determinations
- **"Criminal"** - Only when charges filed or convictions obtained

#### ❌ Language to Avoid
- **"Dictatorial"** - Use "authoritarian methods" or "executive overreach"
- **"Fascist"** - Use specific descriptions of actions
- **"Treasonous"** - Use "violated oath" or "constitutional violations"
- **Partisan labels** without factual basis
- **Emotional rhetoric** not supported by evidence

#### 📝 Context Matters
Since this is a **kleptocracy and corruption timeline**, terms like "corruption," "kleptocracy," and "capture" are appropriate and necessary when:
1. **Factually accurate** and well-documented
2. **Supported by credible sources**
3. **Used descriptively** rather than as political attacks
4. **Part of institutional analysis** rather than personal insults

## 🛡️ Archiving Sources

We archive everything to prevent memory-holing:

1. **Automatic**: GitHub Actions will archive to Wayback Machine
2. **Manual**: You can add archived URLs yourself:
   - Go to https://web.archive.org/save
   - Enter your source URL
   - Copy the archived URL

## ⚖️ Code of Conduct

1. **Stick to facts** - No speculation or editorializing
2. **Assume good faith** - Be patient with new contributors
3. **Remain neutral** - This isn't about parties, it's about patterns
4. **Document everything** - Better to over-source than under-source
5. **Protect sources** - Don't expose whistleblowers or sensitive sources

## 🆘 Getting Help

- **Questions**: Open an issue with `[Question]` tag
- **Discussion**: Use GitHub Discussions
- **Validation errors**: Include full error message in issue
- **Source help**: We can help find and archive sources

## 📈 After Your Contribution

Once merged, your event will:
- Appear in the timeline viewer
- Be included in the searchable index
- Be available for researchers worldwide
- Be preserved for historical record
- Help reveal systemic patterns

Thank you for helping preserve democracy's historical record! 🙏