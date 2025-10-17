# Spec-Kit Integration

This directory contains specification-driven development artifacts for the Kleptocracy Timeline project using [GitHub's Spec-Kit](https://github.com/github/spec-kit).

## What is Spec-Kit?

Spec-Kit is a toolkit that enables spec-driven development: defining **what** and **why** before implementing **how**. It helps create better software through:

- Structured specification documents
- AI-powered implementation planning
- Systematic task breakdown
- Technology-independent design

## Directory Structure

```
.specify/
├── memory/
│   └── constitution.md   # Project principles and standards
└── README.md            # This file

specs/
├── [feature-001]/
│   ├── spec.md          # Detailed specification
│   ├── plan.md          # Technical implementation plan
│   └── tasks.md         # Actionable task breakdown
└── [feature-002]/
    └── ...
```

## Workflow Commands

Spec-Kit provides slash commands for use with AI coding assistants:

### 1. Review Constitution
```
/speckit.constitution
```
Review project principles before starting any work.

### 2. Create Specification
```
/speckit.specify
```
Define requirements and success criteria for a feature.

### 3. Create Technical Plan
```
/speckit.plan
```
Outline implementation approach, tech stack, and architecture.

### 4. Break Down Tasks
```
/speckit.tasks
```
Generate actionable checklist from the plan.

### 5. Implement Feature
```
/speckit.implement
```
Execute tasks systematically with AI assistance.

## When to Use Spec-Kit

### Ideal Use Cases
- **Major refactoring** (e.g., extracting routes from app_v2.py)
- **New features** (e.g., timeline analytics dashboard)
- **Architecture changes** (e.g., adding caching layer)
- **Complex bug fixes** requiring design decisions

### Not Needed For
- Simple bug fixes
- Documentation updates
- Dependency updates
- Data quality fixes (unless systematic)

## Example: Refactoring Routes

Here's how spec-kit would be used for the deferred "extract routes" refactoring:

### Step 1: Create Specification
```bash
mkdir -p specs/001-extract-routes
```

Use `/speckit.specify` to create `specs/001-extract-routes/spec.md`:
- Current state: All routes in single app_v2.py file (1000+ lines)
- Desired state: Modular routes/ directory with blueprints
- Success criteria: All tests pass, no functionality changes
- Non-goals: Adding new features, changing API contracts

### Step 2: Technical Plan
Use `/speckit.plan` to create `specs/001-extract-routes/plan.md`:
- Module structure (routes/events.py, routes/priorities.py, etc.)
- Flask Blueprint strategy
- Import reorganization approach
- Testing strategy

### Step 3: Task Breakdown
Use `/speckit.tasks` to create `specs/001-extract-routes/tasks.md`:
- [ ] Create routes/ directory structure
- [ ] Extract event routes to routes/events.py
- [ ] Extract priority routes to routes/priorities.py
- [ ] Update imports in app_v2.py
- [ ] Run full test suite
- [ ] Verify API functionality
- [ ] Update documentation

### Step 4: Implementation
Use `/speckit.implement` with AI assistant to execute tasks systematically.

## Integration with Existing Tools

Spec-kit complements our existing workflows:

### Works With
- **Git workflow**: Specs in version control
- **Testing**: Specs define test requirements
- **Documentation**: Plans become architecture docs
- **AI assistants**: Claude Code, GitHub Copilot, etc.

### Replaces Nothing
Spec-kit doesn't replace:
- Code review processes
- Testing frameworks
- Project management tools
- Development environments

## Best Practices

### DO
- ✅ Write specs before implementing major changes
- ✅ Use constitution.md to guide decisions
- ✅ Keep specs in version control
- ✅ Update specs if implementation diverges
- ✅ Reference spec in commit messages

### DON'T
- ❌ Skip spec for "quick fixes" that turn complex
- ❌ Treat specs as rigid contracts (they can evolve)
- ❌ Create specs for trivial changes
- ❌ Forget to review constitution first

## Getting Started

### Prerequisites
- Python 3.11+
- uv package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Git
- AI coding assistant (Claude Code, etc.)

### Installation
```bash
# Install spec-kit CLI
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# Verify installation
specify check

# Add to PATH (for bash/zsh)
export PATH="$HOME/.local/bin:$PATH"
```

### Usage in This Project

Since this is an existing project, we don't use `specify init`. Instead:

1. **Review constitution** before starting work
2. **Create spec directories manually** for new features
3. **Use slash commands** in AI assistant sessions
4. **Commit specs** along with implementation

## Resources

- **Spec-Kit GitHub**: https://github.com/github/spec-kit
- **Documentation**: See spec-kit README
- **Examples**: See specs/ directory (when populated)

## Maintenance

- **Constitution reviews**: Monthly (documented in constitution.md)
- **Spec archives**: Keep completed specs for reference
- **Tool updates**: Update spec-kit quarterly with `uv tool upgrade specify-cli`

---

**Last Updated**: 2025-10-16
