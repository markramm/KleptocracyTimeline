# Kleptocracy Timeline - Launch Preparation Todo List

## 🚨 Critical Pre-Launch Tasks

### Priority 1: Complete QA Process ✅
- [ ] **Finish verification of all 303 timeline events**
  - [x] Verify first 6 events
  - [ ] Verify remaining 297 events
  - [ ] Fix all incorrect dates
  - [ ] Update all summaries to include WHO/WHAT/WHEN/WHERE/WHY/IMPACT
  - [ ] Verify all sources actually support claims
  - [ ] Create archive.org links for all sources
  - [ ] Save key excerpts in timeline_data/archive/
  - [ ] Cross-reference related events
  - [ ] Add impact statements to all events

### Source Documentation
- [ ] **Archive all sources**
  - [ ] Create archive.org links for all 1000+ source URLs
  - [ ] Download and save article excerpts locally
  - [ ] Document which facts each source verifies
  - [ ] Replace broken/outdated links
  - [ ] Add multiple sources for controversial events

### Repository Structure
- [x] Create proper directory structure
- [x] Set up .gitignore
- [x] Remove node_modules from tracking
- [ ] **Fix all tool paths** to use timeline_data/events/
- [ ] **Ensure all tests pass**
- [ ] Add data validation tests

### Documentation Enhancement
- [x] Create comprehensive README.md
- [x] Create CONTRIBUTING.md with guidelines
- [x] Create agent.md with verification protocol
- [ ] **Add INSTALL.md** with setup instructions
- [ ] **Create API documentation** for server endpoints
- [ ] **Add timeline schema documentation**
- [ ] **Create data dictionary** for all fields
- [ ] **Add citation style guide**

- [ ] **Research documentation** 📚
  - [ ] **RESEARCH_PRIORITIES.md** - What we're looking for
    - [ ] Key time periods needing coverage
    - [ ] Specific actors/organizations to track
    - [ ] Patterns we're investigating
    - [ ] Types of sources most valuable
  
  - [ ] **VERIFICATION_GUIDE.md** - How to verify events
    - [ ] Source credibility criteria
    - [ ] Fact-checking methodology
    - [ ] Archive creation process
    - [ ] Cross-reference requirements
  
  - [ ] **PATTERNS.md** - Documented patterns
    - [ ] Regulatory capture patterns
    - [ ] Money laundering methods
    - [ ] Influence operation tactics
    - [ ] Network analysis guides

### Technical Infrastructure
- [ ] **Set up GitHub Actions**
  - [ ] Automated testing on PR
  - [ ] Timeline validation checks
  - [ ] Link checking
  - [ ] Whitespace/formatting checks
  - [ ] Deploy previews for PRs

- [ ] **Configure deployment**
  - [ ] Set up GitHub Pages for viewer app
  - [ ] Configure custom domain (if desired)
  - [ ] Set up CDN for assets
  - [ ] Enable HTTPS

- [ ] **RAG System (AI-Powered Search)** 🤖
  - [ ] **Phase 1: Basic Implementation**
    - [ ] Generate embeddings for all events
    - [ ] Set up vector database (Chroma/Pinecone)
    - [ ] Create search API endpoint
    - [ ] Simple question-answering interface
  
  - [ ] **Phase 2: Advanced Features**
    - [ ] Temporal reasoning (before/after queries)
    - [ ] Actor network analysis
    - [ ] Pattern detection algorithms
    - [ ] Multi-index search (semantic + temporal)
  
  - [ ] **Phase 3: Integration**
    - [ ] REST API for RAG queries
    - [ ] Python SDK for researchers
    - [ ] JavaScript client for web app
    - [ ] CLI tool for command line queries
  
  - [ ] **Phase 4: Writing Assistant**
    - [ ] Fact-checking interface
    - [ ] Citation generator
    - [ ] Timeline narrative builder
    - [ ] Pattern analysis reports

- [ ] **API Server**
  - [ ] Deploy API server (Vercel/Netlify/Heroku)
  - [ ] Set up CORS properly
  - [ ] Add rate limiting
  - [ ] Add caching layer
  - [ ] Create API keys system (optional)

- [ ] **Stable URL System** 🔗
  - [ ] **Permanent event URLs**
    - [ ] `/event/[event-id]` - Direct link to event
    - [ ] `/event/[date]/[slug]` - Human-readable alternative
    - [ ] Redirects for renamed events
    - [ ] 301 redirects for moved content
  
  - [ ] **Citation-friendly links**
    - [ ] `/cite/[event-id]` - Returns citation format
    - [ ] `/cite/[event-id].bib` - BibTeX format
    - [ ] `/cite/[event-id].ris` - RIS format
    - [ ] `/cite/[event-id].json` - JSON-LD structured data
  
  - [ ] **Permalink features**
    - [ ] Version permalinks `/event/[id]?v=[commit-hash]`
    - [ ] Date range permalinks `/timeline/2025-01-01/2025-01-31`
    - [ ] Filter permalinks `/timeline?tags=crypto&status=confirmed`
    - [ ] Search permalinks `/search?q=epstein&from=2025`
  
  - [ ] **Embed URLs**
    - [ ] `/embed/[event-id]` - Embeddable widget
    - [ ] `/embed/timeline?filter=...` - Filtered timeline embed
    - [ ] CORS headers for embedding
    - [ ] oEmbed endpoint for auto-embedding

### Viewer Application - Collaboration Features
- [ ] **Fix core functionality**
  - [ ] Update to use timeline_data/events/ path
  - [ ] Test all filtering functions
  - [ ] Improve mobile responsiveness
  - [ ] Add search functionality
  - [ ] Add export features (JSON, CSV)
  - [ ] Add timeline visualization

- [ ] **Add collaboration features** 🤝
  - [ ] **"Report Issue" button on each event**
    - [ ] Links to GitHub issue with pre-filled template
    - [ ] Auto-populates event ID, title, and current data
    - [ ] Categories: Wrong date, Missing source, Inaccurate summary, Broken link
  
  - [ ] **"Suggest Source" button**
    - [ ] Opens form to submit additional sources
    - [ ] Validates URL format
    - [ ] Explains verification requirements
    - [ ] Creates GitHub issue with source suggestion
  
  - [ ] **"Suggest New Event" feature**
    - [ ] Guided form with required fields
    - [ ] Date picker with validation
    - [ ] Source URL input with validation
    - [ ] Preview before submission
    - [ ] Creates GitHub issue with event template
  
  - [ ] **"Request Research" section**
    - [ ] List of topics needing investigation
    - [ ] Voting system for priority
    - [ ] Links to contribute research
    - [ ] Shows bounties/recognition for contributions
  
  - [ ] **Collaboration dashboard**
    - [ ] Recent contributions
    - [ ] Top contributors
    - [ ] Events needing verification
    - [ ] Sources needing archives
    - [ ] Open research questions

- [ ] **Social features**
  - [ ] Share buttons for events (Twitter, Reddit, etc.)
  - [ ] Embed widget for blogs
  - [ ] RSS feed of new events
  - [ ] Email subscription for updates

- [ ] **Build and deploy**
  - [ ] Run npm install and build
  - [ ] Test production build
  - [ ] Deploy to GitHub Pages
  - [ ] Test live deployment

### Legal & Licensing
- [x] Add dual license (CC-BY-SA for data, MIT for code)
- [ ] **Add attribution requirements**
- [ ] **Add fair use disclaimer**
- [ ] **Add content moderation policy**
- [ ] **Add security policy** (SECURITY.md)

### Community Preparation
- [ ] **Create issue templates**
  - [ ] Bug report template
  - [ ] Event addition template
  - [ ] Event correction template
  - [ ] Feature request template

- [ ] **Set up discussions**
  - [ ] Enable GitHub Discussions
  - [ ] Create categories (General, Events, Sources, Development)
  - [ ] Write welcome post

- [ ] **Prepare for contributions**
  - [ ] Create good first issue labels
  - [ ] Document review process
  - [ ] Set up code owners file
  - [ ] Create pull request template

### Data Validation
- [ ] **Fix critical errors**
  - [x] Fix Bondi event date (Feb 1 → Feb 21)
  - [ ] Fix all future events marked as "confirmed"
  - [ ] Fix all archive URLs pointing to homepages
  - [ ] Fix source dates (using event date instead of publication date)

- [ ] **Enhance data quality**
  - [ ] Add missing locations
  - [ ] Add missing actors
  - [ ] Expand short summaries
  - [ ] Add impact statements
  - [ ] Cross-reference related events

### Testing & Quality Assurance
- [ ] **Create test suite**
  - [ ] Timeline data validation tests
  - [ ] API endpoint tests
  - [ ] Viewer app component tests
  - [ ] End-to-end tests
  - [ ] Link checker tests

- [ ] **Run comprehensive tests**
  - [ ] All Python scripts work
  - [ ] All Node.js tools work
  - [ ] API serves correct data
  - [ ] Viewer displays timeline correctly
  - [ ] Search and filters work

### Performance Optimization
- [ ] **Optimize data loading**
  - [ ] Create indexed JSON for faster searches
  - [ ] Implement pagination for large results
  - [ ] Add caching strategies
  - [ ] Minimize JSON size

- [ ] **Optimize viewer app**
  - [ ] Lazy load images
  - [ ] Code splitting
  - [ ] Minimize bundle size
  - [ ] Add service worker for offline access

### Security Review
- [ ] **Security audit**
  - [ ] No exposed API keys
  - [ ] No hardcoded credentials
  - [ ] Sanitize user inputs
  - [ ] Validate all data inputs
  - [ ] Review dependencies for vulnerabilities

### Launch Checklist
- [ ] **Pre-launch**
  - [ ] All tests passing
  - [ ] Documentation complete
  - [ ] Demo data verified
  - [ ] Backup created
  - [ ] Team review completed

- [ ] **Launch day**
  - [ ] Create GitHub release
  - [ ] Tag version 1.0.0
  - [ ] Publish to GitHub Pages
  - [ ] Deploy API server
  - [ ] Monitor for issues

- [ ] **Post-launch**
  - [ ] Monitor error reports
  - [ ] Respond to initial feedback
  - [ ] Fix critical bugs
  - [ ] Plan v1.1 improvements

## 📊 Progress Tracking

### Current Status
- **Events Verified**: 6/303 (2%)
- **Sources Archived**: 0/1000+ (0%)
- **Tests Passing**: Unknown
- **Documentation**: 65% complete
- **Collaboration Features**: 0% complete
- **Deployment Ready**: No

### Priority Order (Updated)
1. 🔴 **CRITICAL**: Complete QA of all 303 events
2. 🔴 **CRITICAL**: Archive all sources before they disappear
3. 🔴 **CRITICAL**: Add collaboration features to encourage contributions
4. 🟡 **HIGH**: Implement stable URL system for citations
5. 🟡 **HIGH**: Enhance documentation with research priorities
6. 🟡 **HIGH**: Fix viewer app and add contribution buttons
7. 🟡 **HIGH**: Set up GitHub Actions and testing
8. 🟢 **MEDIUM**: Deploy to GitHub Pages
9. 🟢 **MEDIUM**: Create research dashboard
10. 🔵 **LOW**: Performance optimizations

### Estimated Timeline
- **Week 1**: Complete QA of all events, fix critical errors
- **Week 2**: Archive sources, update documentation
- **Week 3**: Fix technical issues, set up CI/CD
- **Week 4**: Testing, deployment, and launch

### Resources Needed
- [ ] GitHub Actions minutes
- [ ] Archive.org API access
- [ ] Hosting for API (free tier sufficient)
- [ ] Custom domain (optional)
- [ ] CDN service (optional)

## 📝 Notes

### Known Issues
1. Many archive URLs point to homepages not articles
2. Source dates often use event date not publication date
3. Some summaries too brief
4. Viewer app needs path updates
5. Tests need to be updated for new structure

### Questions to Resolve
1. Should we require 2+ sources for "confirmed" status?
2. How to handle disputed/controversial events?
3. Should we add a "reliability score" to sources?
4. How to handle events with no available sources?
5. Should we version the timeline data?

### Success Criteria
- [ ] All events have verified sources
- [ ] No broken links in repository
- [ ] Tests achieve >90% coverage
- [ ] Documentation is comprehensive
- [ ] Community can easily contribute
- [ ] Timeline is searchable and filterable
- [ ] Data can be exported and reused

---

*Last Updated: 2025-08-17*
*Total Events: 303*
*Ready for Launch: ❌ NO*