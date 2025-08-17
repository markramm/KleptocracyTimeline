# Launch Checklist - Kleptocracy Timeline

## Phase 1: Data Quality (Week 1)
**Goal**: 100% verified, accurate timeline data

### Day 1-2: Automated QA Setup
- [ ] Create bulk verification script
- [ ] Set up parallel source checking
- [ ] Build summary quality analyzer
- [ ] Create automated archive.org integration

### Day 3-5: Manual Verification Sprint  
- [ ] Verify 50 events per day
- [ ] Fix dates, summaries, sources
- [ ] Create archive links
- [ ] Document verification status

### Day 6-7: Quality Review
- [ ] Review all changes
- [ ] Run validation scripts
- [ ] Generate QA report
- [ ] Fix remaining issues

## Phase 2: Technical Infrastructure (Week 2)
**Goal**: Fully functional, tested application

### GitHub Actions Setup
```yaml
- [ ] .github/workflows/test.yml
- [ ] .github/workflows/validate-timeline.yml  
- [ ] .github/workflows/check-links.yml
- [ ] .github/workflows/deploy.yml
```

### API Server Fixes
- [ ] Update all paths to timeline_data/events/
- [ ] Add proper error handling
- [ ] Implement caching
- [ ] Add CORS configuration
- [ ] Create health check endpoint

### Viewer Application Updates
- [ ] Fix data loading paths
- [ ] Update API endpoints
- [ ] Test all filters
- [ ] Add loading states
- [ ] Improve error messages

### Testing Implementation
```bash
# Python tests
- [ ] tests/test_timeline_validation.py
- [ ] tests/test_source_verification.py
- [ ] tests/test_api_endpoints.py

# JavaScript tests  
- [ ] viewer/src/App.test.js
- [ ] viewer/src/components/*.test.js

# Integration tests
- [ ] tests/test_end_to_end.py
```

## Phase 3: Documentation & Community (Week 3)
**Goal**: Repository ready for contributors

### Essential Documentation
- [ ] INSTALL.md - Setup instructions
- [ ] API.md - Endpoint documentation
- [ ] SCHEMA.md - Data structure docs
- [ ] WORKFLOW.md - Contribution workflow

### GitHub Configuration
- [ ] Issue templates (.github/ISSUE_TEMPLATE/)
  - [ ] bug_report.md
  - [ ] event_addition.md
  - [ ] event_correction.md
- [ ] Pull request template
- [ ] Code of conduct
- [ ] Security policy

### Community Setup
- [ ] Enable Discussions
- [ ] Create welcome message
- [ ] Set up project board
- [ ] Configure branch protection
- [ ] Add CODEOWNERS file

## Phase 4: Deployment (Week 4)
**Goal**: Live, accessible application

### Pre-Deployment Checklist
- [ ] All tests passing
- [ ] No console errors
- [ ] Links validated
- [ ] Performance acceptable
- [ ] Mobile responsive

### Deployment Steps
```bash
# 1. Build viewer app
cd viewer
npm install
npm run build
npm test

# 2. Deploy to GitHub Pages
git checkout -b gh-pages
git add -f viewer/build
git commit -m "Deploy to GitHub Pages"
git push origin gh-pages

# 3. Configure repository settings
# Settings > Pages > Source: gh-pages branch

# 4. Deploy API (choose one)
# Option A: Vercel
vercel deploy api/

# Option B: Netlify Functions
netlify deploy --dir=api/

# Option C: Heroku
heroku create kleptocracy-timeline-api
git push heroku main
```

### Post-Deployment Verification
- [ ] Timeline loads correctly
- [ ] Search works
- [ ] Filters work
- [ ] API responds
- [ ] HTTPS enabled
- [ ] Custom domain (optional)

## Critical Path Items 🚨

These MUST be completed before launch:

1. **Data Integrity**
   - [ ] No future events marked "confirmed"
   - [ ] All events have sources
   - [ ] Dates are correct
   - [ ] Summaries are complete

2. **Legal Compliance**
   - [ ] Licenses properly applied
   - [ ] Attribution requirements clear
   - [ ] Fair use disclaimer present
   - [ ] No copyrighted content

3. **Security**
   - [ ] No exposed secrets
   - [ ] Input validation working
   - [ ] Rate limiting enabled
   - [ ] CORS properly configured

4. **Functionality**
   - [ ] Timeline displays
   - [ ] Search works
   - [ ] Filters work
   - [ ] Links work
   - [ ] Mobile works

## Launch Day Checklist

### Morning of Launch
- [ ] Final test run
- [ ] Backup everything
- [ ] Clear cache
- [ ] Check monitoring

### Launch Steps
1. [ ] Create release tag (v1.0.0)
2. [ ] Push to main branch
3. [ ] Deploy to production
4. [ ] Verify deployment
5. [ ] Post announcement

### Post-Launch Monitoring
- [ ] Check error logs
- [ ] Monitor performance
- [ ] Watch for 404s
- [ ] Track usage
- [ ] Respond to issues

## Success Metrics

### Technical Metrics
- [ ] Page load time < 3s
- [ ] API response time < 500ms
- [ ] 0 broken links
- [ ] 0 console errors
- [ ] 100% test coverage

### Data Quality Metrics
- [ ] 100% events verified
- [ ] 100% sources accessible
- [ ] 0 date errors
- [ ] All summaries > 50 chars
- [ ] Archive link coverage > 90%

### Community Metrics
- [ ] Clear contribution path
- [ ] Response time < 24h
- [ ] Documentation complete
- [ ] Issue templates used
- [ ] PR template used

## Risk Mitigation

### Identified Risks
1. **Sources disappearing** → Create archives immediately
2. **API overload** → Implement caching and rate limiting
3. **Data corruption** → Regular backups, version control
4. **Security issues** → Security audit, dependency scanning
5. **Performance issues** → Optimize queries, add pagination

### Contingency Plans
- **If sources are deleted**: Use archive.org versions
- **If API fails**: Serve static JSON files
- **If viewer breaks**: Provide raw data download
- **If contributions flood in**: Set up review team
- **If disputed events arise**: Clear dispute process

## Contact for Launch

### Team Roles
- **Data Verification**: [Assigned]
- **Technical Lead**: [Assigned]
- **Documentation**: [Assigned]
- **Community Manager**: [Assigned]
- **Security Review**: [Assigned]

### External Resources
- GitHub Support: support.github.com
- Archive.org API: archive.org/help/api
- Vercel Support: vercel.com/support
- Security Issues: security@domain.com

---

**LAUNCH STATUS: 🔴 NOT READY**
- Data Verification: 2% (6/303)
- Technical Setup: 40%
- Documentation: 60%
- Testing: 0%
- Deployment: 0%

**Estimated Ready Date**: 3-4 weeks

*This checklist should be reviewed daily during launch preparation*