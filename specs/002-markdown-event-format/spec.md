# Specification: Markdown Event Format Support

**Spec ID**: 002-markdown-event-format
**Created**: 2025-10-17
**Status**: Draft
**Author**: Claude Code

## Problem Statement

### Current State
- Timeline events stored as JSON files (1,580 events)
- High barrier to entry for casual contributors
- GitHub web editor challenging for JSON editing
- JSON syntax errors common (missing commas, quotes, brackets)
- Adding a source link requires understanding JSON structure
- Diffs are hard to read (especially for arrays)

### User Pain Points
1. **Academic contributors**: Want to add events but intimidated by JSON
2. **Casual editors**: Want to fix typos or add sources, blocked by syntax
3. **GitHub web editing**: JSON editor doesn't validate in real-time
4. **Pull request reviews**: JSON diffs are noisy and hard to review
5. **Book readers**: Want to contribute after reading, need low friction

### Impact
- Lower community engagement
- Fewer contributions despite interest
- Higher maintenance burden (fixing JSON syntax errors)
- Missed opportunities for crowdsourced validation

## Desired State

### Progressive Enhancement Approach
- **Support both .json and .md files** in `timeline/data/events/`
- **No breaking changes** - existing 1,580 JSON events continue working
- **Gradual migration** - convert events to markdown as they're updated
- **User choice** - advanced users can still use JSON for precision

### Markdown Event Format
```markdown
---
id: 2025-01-15--event-slug
date: 2025-01-15
title: Event Title
importance: 8
tags:
  - corruption
  - conflicts-of-interest
actors:
  - Donald Trump
sources:
  - url: https://example.com/article
    title: Source Title
    publisher: New York Times
    date: 2025-01-15
    tier: 1
  - url: https://propublica.org/story
    title: Investigation Details
    publisher: ProPublica
    tier: 1
---

Event summary with **markdown formatting**.

Multiple paragraphs supported.

- Bullet points work
- Easy to read and edit
```

### Benefits
1. **Lower barrier**: Markdown is familiar to most developers
2. **GitHub web editor**: Click "Edit", make changes, done
3. **Better diffs**: See actual content changes, not JSON syntax
4. **Hugo support**: Can generate static site with clean pages
5. **SEO**: Each event becomes discoverable page
6. **Human readable**: Reviewers understand changes immediately

## Success Criteria

### Must Have
- [ ] Research server parses both `.json` and `.md` files
- [ ] All 1,580 existing JSON events continue working
- [ ] Markdown events pass same validation as JSON
- [ ] CLI tools work with both formats
- [ ] Documentation updated with markdown format guide
- [ ] At least 10 example events converted to markdown

### Should Have
- [ ] GitHub issue template for markdown events
- [ ] `CONTRIBUTING.md` updated with markdown format
- [ ] Validation error messages helpful for markdown
- [ ] CLI command to convert JSON → Markdown
- [ ] Pre-commit hooks validate markdown events

### Nice to Have
- [ ] Hugo static site generation (timeline + viewer)
- [ ] Markdown events have syntax highlighting in GitHub
- [ ] Visual diff tool for event changes
- [ ] Automatic schema validation in VS Code

## Non-Goals

### Explicitly Out of Scope
- **Remove JSON support** - Both formats coexist indefinitely
- **Migrate all events** - Only convert as events are updated
- **Change API responses** - Internal format, API stays same
- **Hugo as primary viewer** - React viewer remains primary
- **Breaking changes** - Backward compatibility required

### Future Considerations
- WYSIWYG editor for events (future spec)
- Collaborative editing (future spec)
- Event templates (future spec)
- Multi-language support (future spec)

## Constraints

### Technical Constraints
1. **Schema compliance**: Markdown events must validate against `timeline_event_schema.json`
2. **Filesystem authoritative**: Events remain filesystem-based, not database
3. **Research server compatibility**: Must work with existing sync system
4. **Performance**: No significant slowdown in event loading
5. **Git integration**: Must work with existing git workflows

### Project Constraints
1. **Constitution compliance**: Must meet all quality standards
2. **Testing requirements**: 80%+ coverage for new code
3. **Type safety**: 100% MyPy compliance
4. **Documentation**: Clear guide for contributors
5. **Book launch timeline**: Should be ready within 1 month

### Security Constraints
1. **No code injection**: Markdown must be safely parsed
2. **URL validation**: Source URLs must be validated
3. **File permissions**: Markdown files same as JSON (644)
4. **No executable content**: No script execution from markdown

## Assumptions

### User Assumptions
- Contributors familiar with markdown (GitHub READMEs, etc.)
- Users understand YAML frontmatter (common format)
- GitHub web editor is primary editing interface
- Pull requests remain primary contribution method

### Technical Assumptions
- Python 3.11+ with `python-frontmatter` library available
- YAML is safe to parse (using safe_load)
- Markdown body is plain text (no rendering in research server)
- File extensions determine format (.json vs .md)

### Project Assumptions
- Current JSON schema remains authoritative
- No competing event format proposals
- Book launch creates influx of contributors
- Community wants to contribute more easily

## Research & References

### Similar Projects
1. **Hugo** - Static site generator using markdown + YAML frontmatter
2. **Jekyll** - GitHub Pages default, same format
3. **Obsidian** - Note-taking with YAML frontmatter
4. **Foam** - Knowledge base using markdown

### Standards
- **YAML 1.2**: Frontmatter format
- **CommonMark**: Markdown spec (GitHub flavor)
- **JSON Schema**: Validation remains JSON-based

### Prior Art in This Project
- Already using YAML in GitHub workflows
- Research priorities use JSON (could also support markdown)
- Documentation already in markdown

## Risks & Mitigations

### Technical Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Parsing inconsistencies | Medium | High | Extensive testing, schema validation |
| Performance degradation | Low | Medium | Benchmark before/after |
| YAML security issues | Low | Critical | Use yaml.safe_load only |
| Markdown injection | Low | High | Sanitize, no execution |

### User Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Format confusion | Medium | Low | Clear documentation |
| Invalid YAML syntax | High | Low | Helpful error messages |
| Inconsistent formatting | Medium | Low | Linter/formatter |
| Migration mistakes | Low | Medium | Backup before conversion |

### Project Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Delayed book launch | Low | Critical | Timeboxed implementation |
| Maintenance burden | Medium | Medium | Good documentation |
| Format fragmentation | Low | Medium | Prefer one format over time |

## Implementation Phases

### Phase 1: Core Parsing (Week 1)
- Create markdown event parser
- Integrate with filesystem sync
- Validate against schema
- Update CLI tools

### Phase 2: Documentation & Examples (Week 1-2)
- Convert 10 high-visibility events
- Update CONTRIBUTING.md
- Create GitHub issue templates
- Document markdown format

### Phase 3: Tooling & Validation (Week 2-3)
- Pre-commit hooks for markdown
- CLI conversion tool (JSON → Markdown)
- Validation error improvements
- Testing and QA

### Phase 4: Hugo Integration (Week 3-4)
- Configure Hugo for static site
- Deploy alongside React viewer
- SEO optimization
- Documentation

### Phase 5: Community Launch (Week 4+)
- Announce markdown format
- Onboard early contributors
- Monitor for issues
- Iterate based on feedback

## Acceptance Criteria

### Functional Requirements
1. ✅ Research server loads `.md` events without errors
2. ✅ Markdown events appear in search results
3. ✅ CLI commands work with markdown files
4. ✅ Validation catches errors in markdown events
5. ✅ Both formats coexist in same directory

### Quality Requirements
1. ✅ 80%+ test coverage for new parser code
2. ✅ 100% MyPy compliance
3. ✅ All existing tests continue passing
4. ✅ No performance regression (<5% slower)
5. ✅ Documentation complete and clear

### User Experience
1. ✅ Contributor can add markdown event via GitHub web editor
2. ✅ Reviewer can understand changes from diff
3. ✅ Error messages help fix YAML syntax issues
4. ✅ Format documented in CONTRIBUTING.md
5. ✅ Examples available for reference

## Metrics

### Success Metrics
- **Contribution increase**: 50%+ more PRs within 3 months
- **Error reduction**: 80%+ fewer JSON syntax errors
- **Conversion rate**: 10+ events converted to markdown by month 2
- **Contributor satisfaction**: Positive feedback in issues/PRs

### Performance Metrics
- **Parse time**: <5% increase vs JSON
- **Server startup**: No measurable impact
- **Search performance**: No regression
- **File size**: Markdown ~10-20% larger (acceptable)

## Open Questions

1. **Default format**: Should new events default to markdown or JSON?
   - **Recommendation**: Markdown for new contributors, either for maintainers

2. **Conversion timeline**: How fast should we convert existing events?
   - **Recommendation**: Only convert when updating, no bulk conversion

3. **Hugo deployment**: Where to host Hugo static site?
   - **Recommendation**: GitHub Pages, separate from React viewer

4. **Linting**: Should we enforce markdown/YAML style?
   - **Recommendation**: Yes, but warnings not errors initially

5. **Binary choice**: Should we eventually pick one format?
   - **Recommendation**: Revisit after 6 months, prefer markdown if successful

## Dependencies

### Technical Dependencies
- `python-frontmatter` - YAML frontmatter parsing
- `pyyaml` - YAML validation
- `markdown` - Markdown rendering (optional, for Hugo)
- Existing: `jsonschema`, `Flask`, `SQLAlchemy`

### Project Dependencies
- Completed repository restructuring (✅ Done)
- Research server working with new paths (✅ Done)
- Timeline viewer tested (⏸️ Pending)
- Book publication timeline (📅 ~1 month)

## Stakeholders

### Primary Stakeholders
- **Project maintainer (Mark)**: Needs easy contributions for book launch
- **Academic contributors**: Want to add events without JSON friction
- **Casual editors**: Want to fix typos and add sources
- **Future maintainers**: Need sustainable codebase

### Secondary Stakeholders
- **Research server users**: Need reliable parsing
- **Timeline viewers**: Want accurate data
- **AI agents**: Using CLI tools for QA work
- **Future timeline forks**: May adopt this pattern

## Sign-off

- [ ] Specification reviewed by project maintainer
- [ ] Constitution compliance verified
- [ ] Dependencies confirmed available
- [ ] Risks understood and accepted
- [ ] Timeline feasible for book launch

---

**Next Steps**: Create technical implementation plan (`plan.md`)
