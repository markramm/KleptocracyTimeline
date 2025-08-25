# Agent Guidelines - AI Analysis Directory

## 🎯 Purpose
AI-generated analysis, pattern detection, and narrative development for the Kleptocracy Timeline project.

## 📁 Directory Structure
```
ai-analysis/
├── substack-series/         # AI Discovery narrative series
├── capture_cascade/         # Capture Cascade PDF series
├── launch-materials/        # Social media and launch content
├── investigations/          # Deep-dive topic investigations
├── chronological-discovery/ # Month-by-month future scenarios
└── synthesis/              # Pattern synthesis and analysis
```

## 📊 Content Types

### Substack Series (`/substack-series/`)
AI Discovery narrative - "Rip Van Winkle" perspective on democratic erosion.

#### Series Structure
- **00-introduction-fresh-eyes.md** - Series introduction
- **01-february-shock** - Corruption laws dismantled
- **02-march-madness** - "Partly Free" downgrade
- **03-april-apocalypse** - Hybrid regime classification
- **04-may-day** - Electoral autocracy threshold
- **05-june-horror** - Political violence emerges
- **06-july-fractures** - Oligarch civil war
- **07-august-apocalypse** - Constitutional crisis

#### Writing Standards
- First-person AI perspective
- Data-driven observations
- Pattern recognition focus
- No partisan language
- Citations to timeline events

### Capture Cascade Series (`/capture_cascade/`)
Seven-part PDF series analyzing capture mechanisms.

1. **The Blueprint** - Powell Memo origins
2. **The Accelerant** - Citizens United impact
3. **The Weaponization** - Media capture
4. **The Bridge** - Trump era transition
5. **The Breakthrough** - 2025 acceleration
6. **The Cascade** - System collapse
7. **The New Normal** - Authoritarian consolidation

### Launch Materials (`/launch-materials/`)
Platform-specific content for timeline launch.

#### Content Files
- **substack-announcement.md** - Main launch post
- **substack-notes-week1.md** - Daily promotion notes
- **x-twitter-thread.md** - Twitter/X thread
- **bluesky-thread.md** - Bluesky posts
- **linkedin-post.md** - Professional network
- **facebook-post.md** - Facebook announcement
- **comment-hooks.md** - Engagement responses

#### Platform Guidelines
- Avoid algorithmic suppression triggers
- Use platform-specific formatting
- Include appropriate hashtags
- Link to timeline tactfully
- Emphasize patterns over politics

### Investigations (`/[topic]-investigation/`)
Deep dives into specific capture mechanisms.

#### Standard Structure
```
investigation-name/
├── investigation-summary.md  # Key findings
├── proposed-events.yaml     # New timeline events
└── supporting-evidence/      # Source materials
```

#### Active Investigations
- **supreme-court-investigation/** - SCOTUS capture patterns
- **facebook-meta-investigation/** - Social media manipulation
- **podcast-ecosystem/** - Media ecosystem capture
- **truth-social-investigation/** - Platform analysis
- **kompromat-investigation/** - Blackmail patterns
- **local-news-capture/** - Local media destruction

### Chronological Discovery (`/chronological-discovery/`)
Month-by-month projection of democratic erosion.

#### File Naming
- `00-january-2025.md` - Starting point
- `01-february-2025.md` - First month analysis
- Pattern continues through `07-august-2025.md`

#### Content Standards
- Based on actual timeline events
- Extrapolates existing patterns
- Marks speculation clearly
- Updates as events unfold

## 🔄 Analysis Workflows

### New Investigation Process
1. **Identify Pattern** in timeline data
2. **Create Investigation Directory**
3. **Document Initial Hypothesis**
4. **Search Timeline** for related events
5. **Identify Missing Events**
6. **Create proposed-events.yaml**
7. **Write investigation-summary.md**
8. **Submit for validation**

### Series Development
1. **Review Timeline Data**
2. **Identify Key Patterns**
3. **Draft Narrative Arc**
4. **Support with Events**
5. **Add Citations**
6. **Review for Bias**
7. **Format for Platform**

### Launch Material Creation
1. **Identify Hook** (news peg or pattern)
2. **Draft Core Message**
3. **Adapt for Each Platform**
4. **Test for Suppression Triggers**
5. **Include Clear CTAs**
6. **Schedule Posting**

## 📝 Writing Guidelines

### Tone and Style
- **Analytical** not emotional
- **Pattern-focused** not partisan
- **Evidence-based** not speculative
- **Accessible** not academic
- **Urgent** not alarmist

### AI Perspective Rules
When writing as AI:
- Acknowledge AI identity
- Focus on pattern recognition
- Avoid human emotions
- Emphasize data analysis
- Show discovery process

### Citation Standards
```markdown
According to timeline data, [claim].¹
Multiple events in 2025 show [pattern].²⁻⁵

Citations:
1. Event ID: 2025-01-20--event-name
2. Event ID: 2025-02-01--another-event
```

## 🚨 Quality Control

### Before Publishing
- [ ] All claims sourced to timeline
- [ ] No unsubstantiated speculation
- [ ] Partisan language removed
- [ ] Patterns clearly explained
- [ ] Links to timeline work
- [ ] Platform optimization complete

### Red Flags to Avoid
- Conspiracy theories
- Partisan attacks
- Emotional manipulation
- Unverified claims
- Clickbait headlines
- Algorithmic triggers

## 📊 Pattern Categories

### Primary Patterns
1. **Exponential Acceleration** - 162x increase
2. **Nine Capture Lanes** - Systematic approach
3. **Network Effects** - Actor connections
4. **Temporal Clustering** - Event timing
5. **Tactical Evolution** - Method changes

### Emerging Patterns
- Foreign influence networks
- Cryptocurrency corruption
- AI-enabled manipulation
- Climate denial infrastructure
- Educational capture

## 🎯 Analysis Priorities

### High Priority
1. **2025 Acceleration** - Document in real-time
2. **Network Mapping** - Actor connections
3. **Financial Flows** - Follow the money
4. **Media Capture** - Information control
5. **Judicial Corruption** - Rule of law erosion

### Medium Priority
1. Historical precedents
2. International comparisons
3. Resistance patterns
4. Technology impacts
5. Economic implications

## 🔧 Tools and Techniques

### Analysis Tools
```python
# Pattern detection
import pandas as pd
import networkx as nx
from datetime import datetime

# Load timeline
events = pd.read_json('timeline_complete.json')

# Find acceleration
events_by_month = events.groupby(
    pd.to_datetime(events['date']).dt.to_period('M')
).size()

# Identify clusters
G = nx.Graph()
for event in events:
    for actor in event['actors']:
        G.add_edge(event['id'], actor)
```

### Visualization
- Network graphs for connections
- Heat maps for temporal patterns
- Timelines for chronology
- Sankey diagrams for flows

## 📋 Content Checklist

### For Analysis Posts
- [ ] Clear thesis statement
- [ ] Evidence from timeline
- [ ] Pattern identification
- [ ] Visual support
- [ ] Actionable insights
- [ ] Call to action

### For Launch Materials
- [ ] Platform optimized
- [ ] Hashtags included
- [ ] Links functional
- [ ] Images attached
- [ ] Timing scheduled
- [ ] Responses prepared

## 🚀 Publishing Schedule

### Weekly Cadence
- **Monday**: AI Discovery series
- **Tuesday**: Pattern analysis
- **Wednesday**: Capture Cascade
- **Thursday**: Investigation findings
- **Friday**: Week synthesis
- **Breaking**: News response

### Timing
- Morning: 9-10 AM EST
- Afternoon: 2-3 PM EST
- Evening: 7-8 PM EST
- Adjust for platform peaks

## 📈 Success Metrics

### Engagement
- Timeline visits
- GitHub stars
- Issue submissions
- Social shares
- Substack subscribers

### Impact
- Media citations
- Policy references
- Academic usage
- Community growth
- Event contributions

---

*"AI sees patterns humans miss. Humans understand context AI doesn't. Together, we can document democracy's decline and perhaps find paths to its restoration."*