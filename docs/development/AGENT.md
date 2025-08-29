# Agent Guidelines - Root Directory

## 🤖 For AI Agents

You are working on the Kleptocracy Timeline - a critical documentation project tracking democratic capture from 1970-2025. This is Open Source Intelligence for democratic defense.

### Context
- **395+ events** documenting systematic corruption
- **1,900+ sources** all must be verifiable
- **9 capture lanes** categorizing types of democratic erosion
- **162x acceleration** from 1970s to 2025
- **Community-driven** validation and contribution

### Your Role
- Maintain rigorous sourcing standards
- Preserve factual accuracy over sensationalism
- Help identify patterns and connections
- Assist with validation and verification
- Generate clear, accessible analysis

### Key Directories & Their AGENT.md Files
- `/timeline_data/AGENT.md` - Event data, validation, QA procedures
- `/viewer/AGENT.md` - React timeline application
- `/analysis/AGENT.md` - Pattern analysis and findings
- `/ai-analysis/AGENT.md` - AI-generated series and launch materials
- `/.github/AGENT.md` - GitHub integration and workflows
- `/tools/AGENT.md` - Utility scripts and automation

### 🔗 AI Integration
- **Multiple AI tools supported** - See `/AI_INTEGRATION.md`
- **Claude Code** - Deep analysis and bulk operations
- **ChatGPT** - Data analysis and visualization
- **Cursor** - IDE integration and refactoring
- **GitHub Copilot** - In-line code suggestions

### Standards to Maintain
1. Every claim must have 2+ verified sources
2. No speculation without marking it as such
3. ID format: `YYYY-MM-DD--event-name-with-hyphens` (NO underscores!)
4. Preserve link integrity with archive.org backups
5. Follow AGENT.md guidelines in each directory

### YAML Management Tools
The project now includes unified YAML management tools (`yaml_tools.py`) that provide:
- **Unified search** - Search events by any field, date range, importance, status, tags, or actors
- **Smart editing** - Field-level edits with automatic validation and backup
- **Bulk operations** - Apply changes to multiple events matching criteria
- **Source management** - Add, validate, check URLs, detect duplicates
- **Validation** - Schema validation with improvement suggestions
- **Built-in safety** - Automatic backups, dry-run mode, validation before save

Use these tools instead of multiple grep/read/edit operations for better efficiency and safety:
```python
from yaml_tools import YamlEventManager
manager = YamlEventManager()
results = manager.yaml_search(query="Trump", date_range=("2024-01-01", "2024-12-31"))
```

## 👤 For Human Contributors

### Quick Navigation
- Add new event: `/timeline_data/events/` + PR
- Report broken link: Use issue templates
- Validate events: Run `/timeline_data/validation_app_enhanced.py`
- View timeline: `/viewer/` or https://markramm.github.io/KleptocracyTimeline

### Commit Standards
- Clear, descriptive commit messages
- Reference issue numbers when applicable
- One logical change per commit
- Test before committing

### Communication
- Use GitHub Issues for bugs/features
- Discussions for broader topics
- PRs for all changes
- Cite sources in all contributions

## 🔧 Repository Maintenance

### Daily Tasks
- Check for broken links
- Review new event submissions
- Validate recent additions
- Monitor source availability

### Weekly Tasks
- Run full validation suite
- Update statistics
- Archive new sources
- Pattern analysis review

### Monthly Tasks
- Deep pattern analysis
- Update capture lane definitions
- Performance optimization
- Documentation updates

## 📊 Quality Standards

### For Events
- Minimum 2 sources
- Clear, factual title
- Concise summary
- Accurate date
- Appropriate importance rating (1-10)
- Correct capture lane assignment

### For Code
- Comment complex logic
- Maintain consistent style
- Test all changes
- Update documentation
- No console.logs in production

### For Analysis
- Data-driven conclusions
- Clear methodology
- Transparent limitations
- Reproducible results

## 🚀 Getting Started

### For New AI Agents
```markdown
1. Read this AGENT.md
2. Review AI_INTEGRATION.md for tool-specific setup
3. Read timeline_data/AGENT.md for data standards
4. Check viewer/AGENT.md for app details
5. Understand the 9 capture lanes in analysis/PATTERN_ANALYSIS.md
6. Begin with: "I'm working on the Kleptocracy Timeline..."
```

### For New Human Contributors
1. Star and fork the repository
2. Read CONTRIBUTING.md
3. Choose: Validate, Add Event, or Fix Issues
4. Follow the guides in relevant AGENT.md files
5. Submit PR with clear description

### For AI-Human Collaboration
- See `AI_INTEGRATION.md` for using multiple AI tools
- Use ChatGPT for quick analysis and visualization
- Use Claude Code for deep context and bulk operations
- Combine tools for best results

## ⚠️ Critical Rules

1. **No Fabrication**: Every event must be real and sourced
2. **No Editorializing**: Facts only in event descriptions
3. **No Partisan Language**: Focus on actions, not parties
4. **No Speculation**: Mark analysis as such
5. **No Link Rot**: Report and replace broken links immediately

## 📈 Success Metrics

- Event accuracy: 100% sourced
- Link integrity: >95% working
- Validation rate: >10% of events
- Response time: <24h for critical issues
- Build status: Always passing

---

*"Those who would destroy democracy depend on our ignorance. This timeline is our defense. Maintain it well."*