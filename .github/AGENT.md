# Agent Guidelines - GitHub Integration

## 🎯 Purpose
GitHub configuration for automated workflows, issue templates, and community management.

## 📁 Directory Structure
```
.github/
├── workflows/
│   └── deploy.yml         # GitHub Pages deployment
└── ISSUE_TEMPLATE/
    ├── broken-link.yml    # Report broken sources
    ├── new-event.yml      # Submit new events
    └── event-correction.yml # Suggest corrections
```

## 🔄 GitHub Actions Workflows

### Deploy to GitHub Pages
**File**: `workflows/deploy.yml`
**Trigger**: Push to main branch
**Process**:
1. Generate static API data from YAML
2. Build React application
3. Deploy to GitHub Pages
4. Available at: https://markramm.github.io/KleptocracyTimeline/

### Workflow Maintenance
```yaml
# Key sections to monitor
- Python version: 3.11
- Node version: 18
- Build command: npm run build:gh-pages
- Deploy artifact: ./viewer/build
```

## 📝 Issue Templates

### Broken Link Report
**Template**: `ISSUE_TEMPLATE/broken-link.yml`
**Purpose**: Track and fix source link rot
**Required Fields**:
- Event ID
- Broken URL
- Error type
- Alternative URL (optional)

### New Event Submission
**Template**: `ISSUE_TEMPLATE/new-event.yml`
**Purpose**: Community event contributions
**Required Fields**:
- Date (YYYY-MM-DD)
- Title
- Summary
- Importance (1-10)
- Sources (minimum 2)
- Capture lanes

### Event Correction
**Template**: `ISSUE_TEMPLATE/event-correction.yml`
**Purpose**: Fix errors in existing events
**Required Fields**:
- Event ID
- Correction type
- Current content
- Suggested correction
- Evidence

## 🏷️ Label Management

### Priority Labels
- `critical` - Urgent issues affecting timeline integrity
- `high-priority` - Important but not urgent
- `low-priority` - Nice to have

### Type Labels
- `broken-link` - Source accessibility issues
- `new-event` - Event submissions
- `correction` - Error fixes
- `enhancement` - Feature requests
- `bug` - Technical issues

### Status Labels
- `needs-validation` - Requires fact-checking
- `needs-sources` - Additional sources needed
- `in-progress` - Being worked on
- `blocked` - Waiting on something
- `ready` - Ready to merge

## 🔧 Issue Processing Workflows

### New Event Workflow
1. **Receive** via issue template
2. **Label** with `new-event`, `needs-validation`
3. **Validate** sources and claims
4. **Create** YAML file in PR
5. **Review** in PR
6. **Merge** when validated
7. **Close** issue with reference

### Broken Link Workflow
1. **Receive** report
2. **Verify** link is broken
3. **Search** for alternatives
4. **Update** event YAML
5. **Archive** if possible
6. **Close** with resolution

### Correction Workflow
1. **Assess** correction validity
2. **Verify** with sources
3. **Update** if accurate
4. **Document** changes
5. **Close** with explanation

## 📊 GitHub Metrics

### Monitor Weekly
- Open issues by type
- PR merge rate
- Contributor activity
- Star growth
- Fork activity

### Health Indicators
- Issue response time: <24 hours
- PR review time: <48 hours
- Broken link fixes: <1 week
- New event validation: <1 week

## 🤝 Community Management

### Issue Responses

#### For Valid Submissions
```markdown
Thank you for contributing to the timeline! This event has been validated and will be added shortly. Your help in documenting these patterns is invaluable.
```

#### For Invalid Submissions
```markdown
Thank you for your submission. After review, we found [specific issue]. Please provide additional sources or clarification if available.
```

#### For Broken Links
```markdown
Thanks for reporting this broken link. We've found an alternative source / archived the original / are searching for alternatives. The event has been updated.
```

### PR Reviews

#### Approval
```markdown
LGTM! Event validated with sources confirmed. Thank you for contributing to the historical record.
```

#### Changes Requested
```markdown
Thanks for the contribution! A few items need adjustment:
- [ ] [Specific change needed]
- [ ] [Another change]
Please update and we'll merge immediately.
```

## 🔒 Security Considerations

### Protect Against
- Spam submissions
- False information injection
- Vandalism attempts
- Automated attacks

### Validation Requirements
- All events must have verifiable sources
- New contributors need extra review
- Suspicious patterns trigger manual review
- Large changes require multiple approvals

## 🚀 Automation Opportunities

### GitHub Actions to Add
```yaml
# Validate YAML syntax
- name: Validate Event Schema
  run: |
    for file in timeline_data/events/*.yaml; do
      python3 -c "import yaml; yaml.safe_load(open('$file'))"
    done

# Check link integrity
- name: Test Source Links
  run: python3 timeline_data/test_links.py

# Generate statistics
- name: Update Statistics
  run: python3 timeline_data/generate_stats.py
```

### Bot Integration Ideas
- Auto-label issues based on content
- Check links in new events
- Validate YAML schema in PRs
- Generate weekly statistics
- Archive sources automatically

## 📋 PR Checklist Template

```markdown
## Timeline Event PR Checklist

- [ ] Event date in YYYY-MM-DD format
- [ ] Title is clear and factual
- [ ] Summary is 2-3 sentences
- [ ] Minimum 2 sources provided
- [ ] Sources include title, URL, outlet, date
- [ ] Importance rating 1-10 justified
- [ ] Appropriate capture lanes selected
- [ ] Key actors identified
- [ ] No duplicate event exists
- [ ] YAML validates without errors
- [ ] Source links tested and working
- [ ] Language is neutral and factual
```

## 🎯 Repository Settings

### Recommended Settings
- **Issues**: Enabled
- **Discussions**: Enabled
- **Wiki**: Disabled (use docs instead)
- **Projects**: Enabled for roadmap
- **Pages**: Enabled from Actions

### Branch Protection
- **Main branch**: Protected
- **Require PR reviews**: 1 minimum
- **Dismiss stale reviews**: Yes
- **Require status checks**: Yes
- **Include administrators**: No

### GitHub Pages
- **Source**: GitHub Actions
- **Custom domain**: Optional
- **HTTPS**: Enforced

## 🔧 Maintenance Tasks

### Daily
- Review new issues
- Respond to questions
- Check Action failures

### Weekly
- Process event submissions
- Fix broken links
- Update statistics
- Review PR queue

### Monthly
- Archive resolved issues
- Update templates if needed
- Review automation performance
- Generate activity report

## 🚨 Emergency Procedures

### If Vandalized
1. Revert commits immediately
2. Lock repository temporarily
3. Review and strengthen validation
4. Document incident

### If Actions Fail
1. Check error logs
2. Verify configuration
3. Test locally
4. Fix and force rebuild

### If Overwhelmed
1. Prioritize by importance
2. Ask for community help
3. Use labels to organize
4. Close stale issues

---

*"GitHub is our collaboration infrastructure. Issues are our intake. PRs are our validation. Actions are our automation. Together, they're our resilience."*