# Kleptocracy Timeline - Project Constitution

## Project Mission

The Kleptocracy Timeline is a research-driven, evidence-based chronological database documenting systematic corruption, regulatory capture, and democratic backsliding in the United States and globally. Our mission is to:

1. **Document systematic patterns** of institutional capture, corruption, and kleptocracy
2. **Maintain research integrity** through rigorous sourcing and validation
3. **Enable analysis** of corruption networks and patterns across time
4. **Preserve evidence** for accountability and historical record
5. **Support democratic resistance** through transparency and documentation

## Core Principles

### 1. Research Integrity

**Evidence-First Approach**
- All timeline events must be supported by credible sources
- Minimum 2 sources required per event (3+ preferred)
- Sources must be verifiable and archived when possible
- Primary sources (government records, court documents) preferred over secondary

**Source Quality Hierarchy**
1. **Tier 1 (Highest)**: Government records, court filings, official documents
2. **Tier 2**: Investigative journalism (ICIJ, ProPublica, Reuters, AP)
3. **Tier 3**: Mainstream media with editorial standards (NYT, WaPo, Bloomberg)
4. **Tier 4**: Specialized reporting with domain expertise
5. **Not Acceptable**: Social media posts, unverified claims, partisan blogs

**Transparency Requirements**
- Document uncertainty explicitly ("allegedly", "reportedly")
- Note conflicting information when present
- Acknowledge gaps in evidence
- Tag events by confirmation status (confirmed, developing, alleged)

### 2. Code Quality Standards

**Testing Requirements**
- **Minimum 80% test coverage** for core modules
- All new features must include tests
- Integration tests for critical workflows
- Data validation tests for all timeline events

**Type Safety**
- **100% MyPy compliance** required for all Python code
- Use type hints for all function signatures
- Explicit Optional[] for nullable values
- Document complex type structures

**Code Review Standards**
- Peer review for all production code
- AI-assisted code must be reviewed and understood
- No hardcoded credentials (use environment variables)
- Security-first approach (see SECURITY.md)

### 3. Data Quality

**Event Validation**
- Required fields: id, date, title, summary
- Sources in structured format: {title, url}
- At least one of title OR url must be non-empty
- Importance scores (1-10) must be justified
- Dates in YYYY-MM-DD format
- No future events marked as "confirmed"

**Source Standards**
- URLs must be accessible (or archived)
- Titles must be descriptive
- Publication dates when available
- Outlet/publisher identified when possible

**Continuous Validation**
- Pre-commit hooks validate all events
- Automated tests run on every commit
- QA validation queue for systematic review
- Regular audits of source availability

### 4. Architecture Principles

**Separation of Concerns**
- Timeline data (JSON) is filesystem-authoritative
- Research priorities are database-authoritative
- API layer provides unified access
- Git service layer handles version control

**Dependency Injection**
- Services should receive dependencies, not create them
- Configuration via environment variables
- Testability through mocking and interfaces

**Modular Design**
- Routes in separate modules (not monolithic app.py)
- Reusable services and utilities
- Clear boundaries between components
- Single Responsibility Principle

**API Design**
- RESTful conventions
- Structured JSON responses
- Consistent error handling
- Authentication via API keys

### 5. Security Requirements

**Credentials Management**
- **NEVER** commit credentials to version control
- Use .env files (in .gitignore)
- Minimum 32-character random keys for production
- Regular key rotation (90-day recommended)

**Access Control**
- API key authentication required
- GitHub token with minimal scopes (repo only)
- Database files with restrictive permissions (600)
- HTTPS required in production

**Security Reviews**
- Monthly security audits
- Dependency vulnerability scanning
- Review hardcoded values regularly
- Incident response plan documented

### 6. Version Control Standards

**Commit Message Format**
```
Brief summary (50 chars or less)

**Category**: Description of what changed and why

**Changes**:
- Specific change 1
- Specific change 2

**Impact**: How this affects the project

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Branch Strategy**
- `main`: Production-ready code
- `json-migration`: Current major migration work
- Feature branches for specific work
- Meaningful branch names

**Pre-commit Requirements**
- All tests must pass
- JSON validation for timeline events
- API generation succeeds
- No merge conflicts

### 7. Documentation Standards

**Required Documentation**
- README.md: Project overview and getting started
- CLAUDE.md: AI assistant instructions and workflows
- CONTRIBUTING.md: Contribution guidelines
- SECURITY.md: Security policies and procedures
- API documentation in code comments

**Code Documentation**
- Docstrings for all public functions
- Type hints for maintainability
- Inline comments for complex logic
- Architecture decisions documented

### 8. Research Workflow

**Priority Management**
- Research priorities tracked in database
- Status tracking (pending, in_progress, completed)
- Estimated vs actual event counts
- Notes and context preserved

**QA Validation**
- Systematic validation of event quality
- Source verification and enhancement
- Importance scoring validation
- Pattern detection and connection tracking

**Batch Processing**
- Validation runs for parallel agent processing
- Unique validator IDs prevent duplicate work
- Progress tracking and resumability
- Requeue mechanism for incomplete work

### 9. Deferred Refactoring Principles

When technical debt is identified but deferred:

1. **Document the debt** in METRICS.md or dedicated docs
2. **Create specifications** using spec-kit before implementing
3. **Plan systematically** - don't hack incrementally
4. **Test first** - ensure existing behavior preserved
5. **Review thoroughly** - major refactors need extra scrutiny

**Current Deferred Items**:
- Extract routes from app_v2.py into routes/ modules
- Remove legacy filesystem sync code (~500 lines)
- Complete dependency injection throughout app_v2.py
- Migrate 7 pytest tests to unittest
- Add URLs to 21 events with missing source links

### 10. AI Collaboration Standards

**When Using AI Assistants**
- AI suggestions must be reviewed and understood
- Test AI-generated code thoroughly
- Document AI-assisted contributions
- Use Co-Authored-By for attribution

**Prompt Engineering**
- Provide clear context and requirements
- Specify testing and quality standards
- Request explanations for complex solutions
- Iterate based on feedback

**Quality Assurance**
- AI code is not automatically correct
- Run tests before accepting changes
- Review security implications
- Check for subtle bugs or edge cases

## Technology Stack

### Core Technologies
- **Python 3.11+**: Primary language
- **Flask**: API framework
- **SQLite**: Database for metadata
- **Git**: Version control
- **JSON**: Event data format

### Development Tools
- **MyPy**: Static type checking
- **coverage.py**: Test coverage measurement
- **unittest**: Testing framework
- **uv**: Package management
- **spec-kit**: Specification-driven development

### AI Coding Assistants
- **Claude Code**: Primary development assistant
- Support for other AI tools via spec-kit

## Quality Metrics

### Test Coverage Targets
- **Core modules**: 80%+ coverage
- **API layer**: 85%+ coverage
- **Critical paths**: 90%+ coverage
- **Overall project**: 70%+ coverage

### Code Quality
- **MyPy**: 100% compliance (0 errors)
- **Test pass rate**: 99%+ required
- **Pre-commit hooks**: All passing

### Data Quality
- **Event validation**: 100% passing
- **Source quality**: 95%+ with URLs
- **Schema compliance**: 100%

## Decision-Making Framework

### When to Add a New Feature
1. Does it support the research mission?
2. Is it well-specified (use spec-kit)?
3. Can we maintain it long-term?
4. Does it compromise security or integrity?

### When to Refactor
1. Code becomes difficult to understand or maintain
2. Test coverage falls below targets
3. Technical debt blocks new features
4. Security vulnerabilities identified

### When to Accept Contributions
1. Aligns with project mission
2. Meets code quality standards
3. Includes tests and documentation
4. Passes all validation checks

## Maintenance Commitments

### Regular Tasks
- **Daily**: Monitor QA validation queue
- **Weekly**: Review research priorities
- **Monthly**: Security audit, dependency updates
- **Quarterly**: Architecture review, technical debt assessment

### Long-term Sustainability
- Documentation for future maintainers
- Avoid single points of failure
- Knowledge sharing and training
- Community building (when ready)

## Evolution of This Constitution

This constitution is a living document and should evolve with the project. Changes should:

1. Be proposed via specifications (spec-kit)
2. Be discussed with stakeholders
3. Be documented in commit messages
4. Maintain consistency with core mission

**Last Updated**: 2025-10-16
**Next Review**: 2025-11-16

---

**This constitution guides all development decisions. When in doubt, refer to these principles.**
