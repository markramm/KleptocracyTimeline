# Repository Restructuring Analysis
## Kleptocracy Timeline Project - Repository Split Plan

**Date**: 2025-10-17
**Status**: Analysis and Planning Phase
**Goal**: Enable forking for domain-specific timelines and shared research infrastructure

---

## Executive Summary

The Kleptocracy Timeline project currently combines core timeline data/viewers with research infrastructure in a single repository. This analysis proposes splitting into two repositories to enable:

1. **Easy forking** for domain-specific timelines (gun lobby, Supreme Court, global patterns, etc.)
2. **Shared research infrastructure** that can work with any forked timeline
3. **Sustainable funding model** - Patreon for MCP server, n8n for AI analysis
4. **Community-driven expansion** - Lower barriers to contribution

---

## Current Architecture Assessment

### Repository Contents (1,581 events, ~500 research priorities)

```
kleptocracy-timeline/
├── timeline_data/              # 1,581 JSON events (CORE)
│   └── events/
├── viewer/                     # React timeline viewer (CORE)
│   ├── src/
│   ├── public/api/            # Static JSON API (CORE)
│   └── package.json
├── research_monitor/           # Flask research server (RESEARCH)
│   ├── app_v2.py              # 4,695 lines - main server
│   ├── models.py              # Database schemas
│   ├── qa_queue_system.py     # QA validation
│   └── ARCHITECTURE.md
├── research_cli.py            # 1,127 lines - CLI tool (RESEARCH)
├── research_client.py         # 1,143 lines - Client library (RESEARCH)
├── research_priorities/        # 400+ JSON priorities (RESEARCH)
├── mcp_timeline_server_v2.py  # MCP server (RESEARCH)
├── scripts/                   # Mixed - validation, generation
├── docs/                      # Documentation (both)
└── tests/                     # Tests (both)
```

### Key Components

**Core Timeline (should be forkable):**
- Event JSON files (1,581 files @ ~2KB each = 3MB)
- React viewer (static site generation)
- Static API generation (`generate_static_api.py`)
- Event validation logic
- Viewer deployment to GitHub Pages

**Research Infrastructure (shared service):**
- Research Monitor Flask server (REST API)
- SQLite database (events, priorities, validation logs)
- QA validation system
- Research CLI tool
- MCP server for Claude integration
- Research priorities management
- Source quality classification

---

## Proposed Repository Structure

### Repository 1: `kleptocracy-timeline-core`
**Purpose**: The timeline data and viewer - designed to be forked

```
kleptocracy-timeline-core/
├── timeline_data/
│   └── events/                 # All event JSON files
├── viewer/                     # React viewer
│   ├── src/
│   ├── public/
│   └── package.json
├── schemas/
│   ├── event_schema.json      # JSON schema for events
│   └── validation.py          # Shared validation logic
├── scripts/
│   ├── generate_static_api.py # API generation
│   └── validate_events.py     # Event validation
├── docs/
│   ├── FORKING_GUIDE.md       # How to fork for your domain
│   ├── EVENT_CREATION.md      # Creating events
│   └── DEPLOYMENT.md          # Deploy your fork
├── .github/
│   └── workflows/
│       ├── validate.yml       # Event validation
│       └── deploy.yml         # GitHub Pages deployment
├── tests/                     # Core validation tests
├── config.example.json        # Configuration template
├── README.md                  # Forking-focused README
└── LICENSE
```

**Key Design Decisions:**
- **Zero Python dependencies for viewing** - Just HTML/CSS/JS viewer
- **Optional Python for development** - Event creation, validation
- **GitHub Pages ready** - One-click deployment
- **Fork-friendly** - Clear separation of concerns
- **Configuration file** - Points to research server (optional)

### Repository 2: `kleptocracy-timeline-research-server`
**Purpose**: Shared research infrastructure (MCP server + tools)

```
kleptocracy-timeline-research-server/
├── server/
│   ├── app.py                 # Flask REST API
│   ├── models.py              # Database schemas
│   ├── qa_system.py           # QA validation
│   ├── source_classifier.py   # Source quality
│   └── file_sync.py           # Git repo sync
├── mcp/
│   ├── mcp_server.py          # MCP server implementation
│   └── tools/                 # MCP tool definitions
├── cli/
│   ├── research_cli.py        # CLI tool
│   └── client.py              # Python client library
├── n8n/
│   ├── workflows/             # n8n workflow templates
│   └── README.md              # n8n integration guide
├── config/
│   ├── config.example.yaml    # Configuration template
│   └── docker-compose.yml     # Docker deployment
├── docs/
│   ├── API.md                 # REST API documentation
│   ├── MCP.md                 # MCP server guide
│   ├── DEPLOYMENT.md          # Self-hosting guide
│   ├── N8N_INTEGRATION.md     # n8n setup
│   └── FUNDING.md             # Patreon/sustainability
├── tests/                     # Server tests
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker image
├── README.md                  # Server-focused README
└── LICENSE
```

**Key Design Decisions:**
- **Repository-agnostic** - Works with any forked timeline
- **Multi-tenancy ready** - Can serve multiple timeline repos
- **Docker-first deployment** - Easy self-hosting
- **MCP standard** - Works with Claude Desktop, other MCP clients
- **n8n integration** - Pre-built workflows for AI analysis
- **Funding model** - Designed for Patreon-supported shared instance

---

## Interface Design: How They Work Together

### Configuration in Core Repository

**config.json** (in forked timeline):
```json
{
  "repository": {
    "name": "Supreme Court Capture Timeline",
    "url": "https://github.com/username/scotus-capture-timeline",
    "owner": "username"
  },
  "research_server": {
    "enabled": true,
    "url": "https://research.kleptocracy-timeline.org",
    "api_key": "your-api-key-here"
  },
  "viewer": {
    "title": "Supreme Court Capture Timeline",
    "description": "Documenting judicial capture",
    "github_pages_url": "https://username.github.io/scotus-capture-timeline"
  },
  "validation": {
    "require_sources": 2,
    "min_importance": 1,
    "max_importance": 10
  }
}
```

### Research Server API - Timeline Registration

**POST /api/timelines/register**
```json
{
  "name": "Supreme Court Capture Timeline",
  "git_url": "https://github.com/username/scotus-capture-timeline",
  "branch": "main",
  "events_path": "timeline_data/events",
  "priorities_path": "research_priorities",
  "webhook_secret": "generated-secret-for-push-notifications"
}
```

**Response:**
```json
{
  "timeline_id": "scotus-capture-timeline-abc123",
  "api_key": "your-api-key-here",
  "mcp_config": {
    "server_url": "https://research.kleptocracy-timeline.org/mcp",
    "timeline_id": "scotus-capture-timeline-abc123"
  },
  "webhook_url": "https://research.kleptocracy-timeline.org/webhooks/github/scotus-capture-timeline-abc123"
}
```

### Research Server Features for Forked Timelines

1. **Event Management**
   - `GET /api/timelines/{id}/events` - Search events
   - `POST /api/timelines/{id}/events` - Create event
   - `PUT /api/timelines/{id}/events/{event_id}` - Update event
   - `GET /api/timelines/{id}/events/validate` - Validate before save

2. **Research Priorities**
   - `GET /api/timelines/{id}/priorities` - List priorities
   - `GET /api/timelines/{id}/priorities/next` - Get next task
   - `POST /api/timelines/{id}/priorities` - Create priority
   - `PUT /api/timelines/{id}/priorities/{id}` - Update status

3. **QA System**
   - `GET /api/timelines/{id}/qa/queue` - Get validation queue
   - `POST /api/timelines/{id}/qa/validate` - Mark validated
   - `GET /api/timelines/{id}/qa/stats` - QA statistics

4. **Git Integration**
   - Automatic sync via GitHub webhooks
   - Creates PRs for validated events
   - Maintains local git clone for each timeline

### MCP Server Integration

**~/.config/claude/claude_code_mcp_config.json**:
```json
{
  "mcpServers": {
    "timeline-research": {
      "command": "npx",
      "args": [
        "@kleptocracy-timeline/mcp-server",
        "--url", "https://research.kleptocracy-timeline.org/mcp",
        "--timeline-id", "scotus-capture-timeline-abc123",
        "--api-key", "your-api-key-here"
      ]
    }
  }
}
```

**Available MCP Tools:**
- `timeline_search_events` - Search your timeline
- `timeline_create_event` - Create validated event
- `timeline_get_priority` - Get next research task
- `timeline_update_priority` - Update task status
- `timeline_qa_validate` - Mark event as validated
- `timeline_get_stats` - Get timeline statistics

### n8n Integration

**Pre-built Workflows:**

1. **Event Enhancement Workflow**
   - Trigger: New event pushed to timeline
   - Actions:
     - Fetch event from GitHub
     - Search for additional sources (GPT-4, web search)
     - Classify source quality
     - Create PR with enhancements
     - Notify timeline owner

2. **Research Priority Workflow**
   - Trigger: New research priority created
   - Actions:
     - Analyze priority with AI
     - Search for relevant events
     - Generate initial event drafts
     - Submit for human review

3. **QA Validation Workflow**
   - Trigger: Scheduled (daily)
   - Actions:
     - Get validation queue
     - For each event:
       - Verify sources still accessible
       - Check for duplicate content
       - Validate claims with AI
     - Flag issues for review

**n8n Shared Credentials:**
```json
{
  "name": "Kleptocracy Timeline Research Server",
  "type": "httpRequest",
  "data": {
    "url": "https://research.kleptocracy-timeline.org",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth",
    "httpHeaderAuth": {
      "name": "X-API-Key",
      "value": "={{$env.TIMELINE_API_KEY}}"
    }
  }
}
```

---

## Forking Guide - User Perspective

### Scenario: Creating "Gun Lobby Capture Timeline"

**Step 1: Fork the Core Repository**
```bash
# Click "Fork" on github.com/markramm/kleptocracy-timeline-core
# Or use GitHub CLI
gh repo fork markramm/kleptocracy-timeline-core --clone --fork-name gun-lobby-timeline
cd gun-lobby-timeline
```

**Step 2: Configure Your Timeline**
```bash
cp config.example.json config.json
# Edit config.json with your timeline details
```

**Step 3: Customize the Viewer**
```bash
cd viewer
npm install
npm start  # Preview locally
```

Edit `viewer/public/index.html` to customize title, description, etc.

**Step 4: Start Adding Events**
```bash
# Option A: Manual creation
python3 scripts/create_event.py

# Option B: Use research server (optional)
# Register your timeline with shared research server
curl -X POST https://research.kleptocracy-timeline.org/api/timelines/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gun Lobby Capture Timeline",
    "git_url": "https://github.com/yourusername/gun-lobby-timeline",
    "branch": "main"
  }'
```

**Step 5: Deploy to GitHub Pages**
```bash
# Enabled in repository Settings > Pages > GitHub Actions
git add .
git commit -m "Initial gun lobby timeline"
git push

# GitHub Actions will automatically:
# 1. Validate all events
# 2. Generate static API
# 3. Build viewer
# 4. Deploy to GitHub Pages
```

Your timeline is now live at: `https://yourusername.github.io/gun-lobby-timeline`

**Step 6 (Optional): Connect to n8n for AI Analysis**
```bash
# Import n8n workflows from research server repository
# Configure with your timeline API key
# AI will help enhance events, find sources, validate
```

---

## Migration Strategy

### Phase 1: Core Repository Extraction (Week 1)
1. Create `kleptocracy-timeline-core` repository
2. Copy timeline_data/, viewer/, essential scripts
3. Create configuration system
4. Update documentation for forking
5. Test GitHub Pages deployment

### Phase 2: Research Server Extraction (Week 2)
1. Create `kleptocracy-timeline-research-server` repository
2. Extract research_monitor/, research_cli.py, MCP server
3. Implement multi-timeline support
4. Create Docker deployment
5. Document API for forked timelines

### Phase 3: Timeline Registration System (Week 3)
1. Implement timeline registration endpoint
2. Build Git sync for multiple timelines
3. Create webhook handlers
4. Test with 2-3 forked timelines

### Phase 4: n8n Integration (Week 4)
1. Create n8n workflow templates
2. Document shared credentials setup
3. Build example workflows
4. Test end-to-end with research server

### Phase 5: Documentation & Launch (Week 5)
1. Comprehensive forking guide
2. Research server self-hosting guide
3. n8n integration tutorials
4. Funding model documentation
5. Community guidelines

---

## Funding Model: Book Launch + Public Infrastructure

### Vision: Free Research Infrastructure for Democratic Accountability

The timeline serves as the empirical foundation for **a book analyzing 50 years of institutional capture patterns**. The research server becomes public infrastructure - free for everyone - funded by the book's launch campaign.

### GoFundMe Campaign (Book Launch)

**Target: $15,000-25,000** (2-3 years of operations)

**Cost Breakdown:**
- **Server hosting**: $50/month × 36 months = $1,800
- **Domain + SSL**: $100/year × 3 = $300
- **Database backup/storage**: $20/month × 36 = $720
- **CDN/bandwidth**: $30/month × 36 = $1,080
- **Monitoring/security**: $25/month × 36 = $900
- **Development time** (maintenance): $500/month × 6 = $3,000
- **Documentation/support**: $2,000 one-time
- **Buffer (20%)**: $2,000
- **Total 3-year runway**: ~$12,000

**Stretch goals:**
- $15K: 3 years operations + better infrastructure
- $20K: 5 years operations + paid maintenance
- $25K: 5 years + AI analysis features + community grants

### Book as Revenue Model

**The Book:**
- **Title**: *[Working title about capture patterns]*
- **Content**: Uses timeline as empirical evidence for systematic analysis
- **Audience**: Academics, journalists, activists, policymakers
- **Platform**: The timeline is the book's "living appendix"

**Mutual Reinforcement:**
- **Book → Timeline**: Drives traffic, validates methodology, attracts contributors
- **Timeline → Book**: Provides credibility, ongoing updates, community engagement
- **Both**: Demonstrate the power of open-source research infrastructure

### Free Tier for Everyone

**No Paywalls, No Tiers, Just Rate Limits:**
- **Basic users**: 100 API calls/hour (enough for research)
- **Registered users**: 500 API calls/hour (sign up with email)
- **Timeline owners**: 2,000 API calls/hour (registered timeline)
- **Fair use policy**: No commercial scraping, cite the project

**Why Free Works:**
1. **Lower costs**: No billing system, no tier management, no payment processing
2. **Public good**: Research infrastructure shouldn't be paywalled
3. **Network effects**: More users = more contributions = better data
4. **Book marketing**: Timeline is best advertisement for the book
5. **Academic integrity**: Open access aligns with research values

### n8n Integration (User-Paid or Self-Hosted)

**Options for AI Analysis:**
1. **n8n Cloud**: Users pay for their own instance ($20-50/month)
2. **Self-hosted n8n**: Free, open source, users run locally
3. **Shared workflows**: Free templates connecting to research server

**Research server provides:**
- Free API access for n8n workflows
- Pre-built workflow templates
- Documentation for self-hosting
- No cost for basic automation

**AI costs stay with users:**
- OpenAI API keys (users provide their own)
- Claude API keys (users provide their own)
- Self-hosted models (users run locally)

### Sustainability Model

**Years 1-3: GoFundMe funded**
- Research server runs on campaign funds
- Free for all users
- Focus on stability and community growth

**Year 3+: Community supported**
- **Book sales**: Ongoing revenue from book
- **Institutional grants**: Academic/foundation support
- **Corporate sponsors**: "Supported by" credits (no influence)
- **Community donations**: Optional tip jar
- **Consulting**: Help organizations set up private instances

**Emergency backup: Self-hosting**
- If funding runs out, pivot to community self-hosted model
- All code open source (MIT license)
- Docker setup for easy deployment
- Community can run their own instances

### Book Launch Strategy

**Pre-Launch (3 months before):**
- Announce book + timeline infrastructure
- Start GoFundMe campaign
- Early access for contributors
- Build anticipation with preview chapters

**Launch Day:**
- Book release
- Research server goes live
- Press coverage emphasizes free public resource
- "Living appendix" becomes talking point

**Post-Launch:**
- Timeline updates referenced in book marketing
- Community contributions highlighted
- Case studies of forked timelines
- Academic partnerships

### Value Proposition for Donors

**"Support free research infrastructure for democratic accountability"**

**What $100 buys:**
- 2 months of server hosting for everyone
- Infrastructure used by dozens of researchers
- Empirical foundation for book analysis
- Precedent for open-source accountability tools

**What you get:**
- **All donors**: Acknowledgment in book
- **$100+**: Early access to book chapters
- **$500+**: Signed copy + research server credits
- **$1000+**: Listed as major supporter, consultation call
- **Institutions**: Partnership opportunities, co-branding

---

## Technical Debt & Quality Improvements Needed

### Before Split

1. **Validation Logic Standardization**
   - Extract into shared `schemas/` package
   - Ensure both repos use same validation
   - Create comprehensive test suite

2. **API Versioning**
   - Implement `/api/v1/` versioning
   - Plan for breaking changes
   - Backwards compatibility strategy

3. **Configuration Management**
   - Standardize config format (YAML or JSON)
   - Environment variable support
   - Secrets management (API keys, webhooks)

4. **Documentation**
   - API documentation (OpenAPI/Swagger)
   - MCP tool documentation
   - Deployment guides for all options

5. **Testing**
   - Integration tests for API
   - End-to-end tests for forking workflow
   - CI/CD for both repositories

### During Split

1. **Dependency Management**
   - Audit all imports
   - Create clean dependency boundaries
   - Document all cross-repo dependencies

2. **Database Migration**
   - Research server needs timeline_id in all tables
   - Migrate existing data
   - Create migration scripts

3. **GitHub Actions**
   - Core: validation, deployment
   - Research: tests, Docker build
   - Both: security scanning

---

## Success Metrics

### Pre-Launch (Book Release - 3 months)
- [ ] GoFundMe campaign launched
- [ ] $15K minimum funding secured
- [ ] Beta research server deployed
- [ ] 3-5 test timelines running
- [ ] Book manuscript finalized

### Launch Day (Book Release)
- [ ] Book published and available
- [ ] Research server publicly launched (free for all)
- [ ] Press coverage emphasizing open infrastructure
- [ ] 10+ forked timelines ready to showcase
- [ ] n8n workflow templates published

### After 3 Months
- [ ] 20+ forked timelines created
- [ ] 500+ registered API users
- [ ] Book reviews citing timeline as resource
- [ ] 200+ events added across all forks
- [ ] Academic partnerships forming

### After 6 Months
- [ ] 50+ forked timelines (various domains)
- [ ] Research server serving 10+ active domains
- [ ] Citations in academic papers
- [ ] Community maintenance contributors
- [ ] Self-hosted instances by 3+ organizations

### After 1 Year
- [ ] 100+ timelines across domains
- [ ] Book established as key reference
- [ ] Institutional grant applications
- [ ] Model replicated for other countries
- [ ] Sustainable through book sales + grants

---

## Open Questions

1. **Book Details**: Title, publisher, release date timeline?
2. **GoFundMe Target**: $15K minimum, $25K stretch - does this align with launch scale?
3. **Authentication**: Simple API keys (free registration) vs OAuth?
4. **Data Privacy**: Should timelines be able to be private? (Book argues for transparency)
5. **Collaboration**: Multiple users per timeline - needed initially?
6. **Backup Strategy**: Who owns data? (Users own their git repos, server is just cache)
7. **Cross-Timeline Analysis**: Network graphs showing patterns across domains?
8. **Academic Partnerships**: IRB approval needed? University affiliation?
9. **Press Strategy**: Embargo dates, exclusive access for journalists?
10. **International**: Non-US timelines supported from day one?

---

## Next Steps

### Immediate (This Week)
1. **Get feedback** on this analysis document
2. **Create branch** to test extraction of core repo
3. **Prototype config.json** structure
4. **Test GitHub Pages** deployment with minimal core

### Short Term (Next 2 Weeks)
1. **Build prototype** research server with timeline registration
2. **Create 1-2 test forks** (gun lobby, Supreme Court)
3. **Document API** with OpenAPI spec
4. **Containerize** research server with Docker

### Medium Term (Next Month)
1. **Launch beta** with 3-5 test timelines
2. **Set up Patreon** for research server funding
3. **Create n8n workflows** and documentation
4. **Gather feedback** from early adopters

---

## Conclusion

This restructuring will:
- **Lower barriers** to creating domain-specific timelines
- **Enable sustainability** through book launch + free public infrastructure
- **Improve code quality** through clear separation of concerns
- **Foster community** by making forking and contribution easier
- **Scale effectively** with shared research infrastructure
- **Support the book** as empirical foundation and living appendix
- **Serve public good** through free access to research tools

### The Bigger Picture

**The book argues**: Institutional capture follows predictable patterns across 50 years and multiple domains.

**The timeline proves it**: 1,581+ events, meticulously sourced and validated.

**The infrastructure enables**: Anyone can fork this methodology for their domain.

**The model scales**: From one person's research to a global movement.

### Why This Works

1. **Credibility**: Book provides academic rigor and visibility
2. **Funding**: One-time campaign, not ongoing extraction
3. **Access**: Free for everyone, maximum impact
4. **Network**: Each forked timeline strengthens the whole
5. **Sustainability**: Multiple revenue streams (book, grants, consulting)
6. **Resilience**: Open source, community-owned, self-hostable

### The Vision

**Year 1**: Launch with book, 50+ domain timelines, free research server
**Year 3**: Academic standard for analyzing institutional capture
**Year 5**: Replicated in multiple countries, hundreds of timelines
**Year 10**: The methodology for documenting kleptocracy globally

**Recommendation**:
1. **Immediate**: Finalize book manuscript, start repository restructuring
2. **Pre-launch (-3 months)**: Beta test research server, prepare GoFundMe
3. **Launch day**: Book + free infrastructure + press campaign
4. **Post-launch**: Community growth, academic partnerships, sustainability planning
