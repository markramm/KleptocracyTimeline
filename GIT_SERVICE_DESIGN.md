# Git Service Layer - Multi-Tenant Architecture Design

**Purpose**: Replace filesystem sync complexity with clean Git operations that support multiple timeline repositories.

**Status**: Design Document (Phase 2 Implementation)

---

## Design Principles

1. **Repository Agnostic**: Work with any timeline repo (fork, staging, production)
2. **PR-Based Workflow**: Git operations only at defined boundaries
3. **Database Authoritative**: Server database is source of truth for work-in-progress
4. **Clean Separation**: Prepare for future extraction into separate repository
5. **Multi-Tenant Ready**: Support multiple researchers with different repos/forks

---

## Current Problems to Solve

### 1. Filesystem Sync Complexity (~500 lines)
```python
# Current: app_v2.py lines 200-700
- Filesystem polling every 30 seconds
- Complex state synchronization
- WAL file management
- Commit threshold tracking
- Manual orchestration required
```

### 2. Tight Coupling
- Timeline data hardcoded to local filesystem
- Can't work with forks or alternative repos
- Server deployment requires git repo mount
- Can't run multiple servers on same timeline

### 3. Git Operations Scattered
- Manual git commands in documentation
- No programmatic PR creation
- No conflict resolution strategy
- No sync status tracking

---

## Proposed Architecture

### Service Layer Structure

```
research_monitor/
├── services/
│   ├── git_service.py           # Core Git operations
│   ├── timeline_sync.py         # Import/export coordination
│   ├── pr_builder.py            # GitHub PR creation
│   └── conflict_resolver.py     # Merge conflict handling
├── core/
│   ├── config.py                # Multi-tenant configuration
│   └── git_config.py            # Git-specific settings
└── models/
    └── sync_status.py           # Track sync state in DB
```

### Configuration Design

```python
# research_monitor/core/config.py
class Config:
    """Application configuration with multi-tenant support"""

    # Timeline Repository Configuration
    TIMELINE_REPO_URL = os.getenv('TIMELINE_REPO_URL',
                                   'https://github.com/user/kleptocracy-timeline')
    TIMELINE_BRANCH = os.getenv('TIMELINE_BRANCH', 'main')
    TIMELINE_WORKSPACE = Path(os.getenv('TIMELINE_WORKSPACE',
                                        '/tmp/timeline-workspace'))

    # GitHub Integration
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # For PR creation
    GITHUB_API_URL = 'https://api.github.com'

    # Sync Settings
    AUTO_PULL_ON_START = os.getenv('AUTO_PULL_ON_START', 'true').lower() == 'true'
    PR_AUTO_BRANCH_PREFIX = os.getenv('PR_BRANCH_PREFIX', 'research-batch')

    # Multi-tenant support
    WORKSPACE_ISOLATION = True  # Each repo gets own workspace
```

---

## Core Services

### 1. GitService - Core Git Operations

```python
# research_monitor/services/git_service.py

class GitService:
    """
    Core Git operations for timeline repository management.
    Repository-agnostic, supports any timeline repo.
    """

    def __init__(self, config: Config):
        self.repo_url = config.TIMELINE_REPO_URL
        self.branch = config.TIMELINE_BRANCH
        self.workspace = self._get_workspace(config)
        self.github_token = config.GITHUB_TOKEN

    # === Core Operations ===

    def clone_or_update(self) -> bool:
        """
        Clone repository if not present, otherwise pull latest.
        Returns: True if successful, False otherwise
        """
        pass

    def pull_latest(self) -> Dict[str, Any]:
        """
        Pull latest changes from configured branch.
        Returns: {
            'success': bool,
            'new_commits': int,
            'files_changed': List[str],
            'conflicts': List[str]
        }
        """
        pass

    def create_branch(self, branch_name: str) -> bool:
        """Create new branch from current HEAD."""
        pass

    def commit_changes(self, message: str, files: List[Path]) -> str:
        """
        Commit specified files.
        Returns: commit hash
        """
        pass

    def push_branch(self, branch_name: str) -> bool:
        """Push branch to remote."""
        pass

    # === Repository Information ===

    def get_status(self) -> Dict[str, Any]:
        """
        Get current repository status.
        Returns: {
            'repo_url': str,
            'current_branch': str,
            'last_sync': datetime,
            'commits_behind': int,
            'local_changes': int
        }
        """
        pass

    def get_changed_files(self, since_commit: str = None) -> List[str]:
        """Get list of changed files since commit."""
        pass

    # === Helpers ===

    def _get_workspace(self, config: Config) -> Path:
        """Get workspace path, isolated per repo if multi-tenant."""
        if config.WORKSPACE_ISOLATION:
            # Create unique workspace per repo URL
            repo_hash = hashlib.md5(self.repo_url.encode()).hexdigest()[:8]
            return config.TIMELINE_WORKSPACE / repo_hash
        return config.TIMELINE_WORKSPACE
```

### 2. TimelineSyncService - Coordination

```python
# research_monitor/services/timeline_sync.py

class TimelineSyncService:
    """
    Coordinates import/export between database and git repository.
    Replaces filesystem sync complexity with explicit operations.
    """

    def __init__(self, git_service: GitService, db_session):
        self.git = git_service
        self.db = db_session

    # === Import from Git ===

    def import_from_repo(self, force: bool = False) -> Dict[str, Any]:
        """
        Import events from git repository to database.
        Replaces: Filesystem sync polling

        Returns: {
            'imported': int,
            'updated': int,
            'conflicts': List[str],
            'errors': List[str]
        }
        """
        # 1. Pull latest from repo
        pull_result = self.git.pull_latest()
        if not pull_result['success']:
            return {'error': 'Pull failed'}

        # 2. Get changed event files
        changed_files = [f for f in pull_result['files_changed']
                        if f.startswith('timeline_data/events/')]

        # 3. Import each changed event
        imported = 0
        updated = 0
        for filepath in changed_files:
            event_data = self._load_event_file(filepath)
            if self._event_exists(event_data['id']):
                self._update_event(event_data)
                updated += 1
            else:
                self._import_event(event_data)
                imported += 1

        # 4. Record sync status
        self._record_sync(pull_result)

        return {
            'imported': imported,
            'updated': updated,
            'conflicts': pull_result['conflicts'],
            'last_sync': datetime.now(timezone.utc)
        }

    # === Export to Git ===

    def export_pending_events(self) -> List[Dict[str, Any]]:
        """
        Get events ready for export (validated, not yet in repo).

        Returns: List of event dictionaries ready for PR
        """
        pass

    def prepare_export_files(self, events: List[Dict]) -> List[Path]:
        """
        Write events to workspace for commit.
        Returns: List of file paths written
        """
        pass

    # === Status ===

    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current sync status.

        Returns: {
            'last_import': datetime,
            'events_in_db': int,
            'events_in_repo': int,
            'pending_export': int,
            'repo_status': Dict
        }
        """
        pass
```

### 3. PRBuilderService - GitHub Integration

```python
# research_monitor/services/pr_builder.py

class PRBuilderService:
    """
    Creates GitHub Pull Requests for validated events.
    Replaces: Manual git commands and orchestration
    """

    def __init__(self, git_service: GitService, sync_service: TimelineSyncService):
        self.git = git_service
        self.sync = sync_service

    def create_pr(self,
                  events: List[Dict] = None,
                  title: str = None,
                  description: str = None) -> Dict[str, Any]:
        """
        Create Pull Request with validated events.

        Args:
            events: Events to include (None = all pending)
            title: PR title (auto-generated if None)
            description: PR description (auto-generated if None)

        Returns: {
            'success': bool,
            'pr_url': str,
            'pr_number': int,
            'branch': str,
            'events_count': int
        }
        """
        # 1. Get events to export
        if events is None:
            events = self.sync.export_pending_events()

        if not events:
            return {'error': 'No events to export'}

        # 2. Create branch
        branch_name = self._generate_branch_name(len(events))
        self.git.create_branch(branch_name)

        # 3. Write events to files
        files = self.sync.prepare_export_files(events)

        # 4. Commit changes
        commit_msg = self._generate_commit_message(events)
        commit_hash = self.git.commit_changes(commit_msg, files)

        # 5. Push branch
        self.git.push_branch(branch_name)

        # 6. Create PR via GitHub API
        pr_data = self._create_github_pr(
            branch=branch_name,
            title=title or self._generate_pr_title(events),
            description=description or self._generate_pr_description(events)
        )

        # 7. Mark events as exported
        self._mark_events_exported(events, pr_data['pr_number'])

        return {
            'success': True,
            'pr_url': pr_data['html_url'],
            'pr_number': pr_data['number'],
            'branch': branch_name,
            'events_count': len(events),
            'commit_hash': commit_hash
        }

    def _create_github_pr(self, branch: str, title: str, description: str) -> Dict:
        """Create PR using GitHub API."""
        url = f"{self.git.config.GITHUB_API_URL}/repos/{self._get_repo_path()}/pulls"
        headers = {
            'Authorization': f'token {self.git.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        data = {
            'title': title,
            'body': description,
            'head': branch,
            'base': self.git.branch
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def _generate_pr_title(self, events: List[Dict]) -> str:
        """Auto-generate PR title from events."""
        count = len(events)
        date_range = self._get_date_range(events)
        return f"Add {count} researched events ({date_range})"

    def _generate_pr_description(self, events: List[Dict]) -> str:
        """Auto-generate PR description with event summary."""
        lines = [
            "## Research Batch Summary",
            f"",
            f"**Events**: {len(events)}",
            f"**Date Range**: {self._get_date_range(events)}",
            f"",
            "### Events Added:",
            ""
        ]
        for event in sorted(events, key=lambda e: e['date']):
            lines.append(f"- `{event['date']}` - {event['title']}")

        lines.extend([
            "",
            "### Quality Assurance",
            f"- All events validated by QA system",
            f"- Average quality score: {self._avg_quality_score(events):.2f}/10",
            f"- Total sources: {sum(len(e.get('sources', [])) for e in events)}",
            "",
            "🤖 Generated by Timeline Research Tools"
        ])

        return "\n".join(lines)
```

---

## Database Models for Sync Tracking

```python
# research_monitor/models/sync_status.py

class SyncStatus(Base):
    """Track sync operations between database and git repo."""
    __tablename__ = 'sync_status'

    id = Column(Integer, primary_key=True)
    repo_url = Column(String, nullable=False)
    sync_type = Column(String)  # 'import' or 'export'
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime)
    success = Column(Boolean)

    # Import stats
    events_imported = Column(Integer, default=0)
    events_updated = Column(Integer, default=0)

    # Export stats
    events_exported = Column(Integer, default=0)
    pr_number = Column(Integer)
    pr_url = Column(String)
    branch_name = Column(String)

    # Metadata
    commits_processed = Column(Integer)
    files_changed = Column(Integer)
    conflicts = Column(JSON)
    errors = Column(JSON)


class EventExportStatus(Base):
    """Track which events have been exported to git."""
    __tablename__ = 'event_export_status'

    id = Column(Integer, primary_key=True)
    event_id = Column(String, ForeignKey('timeline_events.id'), unique=True)

    exported = Column(Boolean, default=False)
    export_date = Column(DateTime)
    pr_number = Column(Integer)
    merged = Column(Boolean, default=False)
    merge_date = Column(DateTime)

    event = relationship('TimelineEvent', backref='export_status')
```

---

## CLI Commands

### New Research CLI Commands

```bash
# === Import from Git ===

# Pull latest changes from timeline repo
python3 research_cli.py git-pull
# Returns: {'imported': 5, 'updated': 3, 'conflicts': []}

# Check sync status
python3 research_cli.py git-status
# Returns: {'last_sync': '2025-10-16T12:00:00Z', 'commits_behind': 2}

# === Export to Git ===

# Create PR with all pending validated events
python3 research_cli.py create-pr
# Returns: {'pr_url': 'https://github.com/...', 'pr_number': 42}

# Create PR with specific events
python3 research_cli.py create-pr --events "2025-01-15--event-1,2025-01-16--event-2"

# Create PR with custom title/description
python3 research_cli.py create-pr --title "Crypto corruption batch" --description "Focus on Trump crypto conflicts"

# === Configuration ===

# Configure timeline repo (switch to fork)
python3 research_cli.py git-config --repo https://github.com/alice/timeline-fork --branch main

# Get current git configuration
python3 research_cli.py git-config --show

# === Multi-tenant Usage ===

# Work with different repos via environment variables
TIMELINE_REPO_URL=https://github.com/alice/fork research_cli.py git-pull
TIMELINE_REPO_URL=https://github.com/bob/fork research_cli.py create-pr
```

---

## Workflow Comparison

### Current Workflow (Complex)

```
┌─────────────────────────────────────────┐
│ 1. Research events                      │
│ 2. Server creates JSON files            │
│ 3. Wait for filesystem sync (30s poll) │
│ 4. Manual: Check commit threshold       │
│ 5. Manual: git add/commit/push          │
│ 6. Manual: Create PR on GitHub          │
│ 7. Pray sync state is consistent        │
└─────────────────────────────────────────┘
```

### New Workflow (Simple)

```
┌─────────────────────────────────────────┐
│ 1. Research events                      │
│ 2. Events in database (validated)       │
│ 3. Run: create-pr                       │
│ 4. ✅ Done - PR created automatically   │
└─────────────────────────────────────────┘

Sync from upstream:
┌─────────────────────────────────────────┐
│ 1. Run: git-pull                        │
│ 2. ✅ Database updated automatically    │
└─────────────────────────────────────────┘
```

---

## Migration Strategy

### Phase 2A: Build Git Service Layer (Week 2-3)
1. Create `git_service.py` with core operations
2. Create `timeline_sync.py` for import/export
3. Add database models for sync tracking
4. Implement CLI commands
5. **Keep filesystem sync running** (parallel operation)

### Phase 2B: PR Builder (Week 3)
1. Implement `pr_builder.py`
2. GitHub API integration
3. Auto-generate PR descriptions
4. Test PR creation with fork

### Phase 2C: Deprecate Filesystem Sync (Week 4)
1. Switch to git operations for all sync
2. Remove filesystem polling code (~500 lines)
3. Remove commit threshold system
4. Update documentation

### Testing Strategy
- **Unit tests**: Mock git operations
- **Integration tests**: Use test repo on GitHub
- **Manual testing**: Create fork, test full workflow

---

## Multi-Tenant Configuration Examples

### Example 1: Multiple Researchers

```bash
# Alice working on main timeline
cat > .env.alice
TIMELINE_REPO_URL=https://github.com/org/kleptocracy-timeline
TIMELINE_BRANCH=main
GITHUB_TOKEN=alice_token_here
DB_PATH=/data/alice.db

# Bob working on specialized fork
cat > .env.bob
TIMELINE_REPO_URL=https://github.com/bob/healthcare-corruption
TIMELINE_BRANCH=main
GITHUB_TOKEN=bob_token_here
DB_PATH=/data/bob.db
```

### Example 2: Staging/Production

```bash
# Development server (working fork)
TIMELINE_REPO_URL=https://github.com/org/timeline-staging
TIMELINE_BRANCH=develop
AUTO_PULL_ON_START=true

# Production server (main timeline)
TIMELINE_REPO_URL=https://github.com/org/kleptocracy-timeline
TIMELINE_BRANCH=main
AUTO_PULL_ON_START=true
```

### Example 3: International Instances

```yaml
# Docker Compose: Multiple timeline instances
services:
  timeline-us:
    image: timeline-research-tools
    environment:
      - TIMELINE_REPO_URL=https://github.com/org/timeline-us
      - INSTANCE_NAME=US Corruption

  timeline-brazil:
    image: timeline-research-tools
    environment:
      - TIMELINE_REPO_URL=https://github.com/org/timeline-brazil
      - INSTANCE_NAME=Brazil Corruption
```

---

## Benefits Summary

### Immediate Benefits
- ✅ Remove ~500 lines of filesystem sync code
- ✅ Eliminate 30-second polling
- ✅ Programmatic PR creation
- ✅ Clear git workflow (pull → work → PR)
- ✅ Database is source of truth (no sync conflicts)

### Multi-Tenant Benefits
- ✅ Support forks and alternative timelines
- ✅ Multiple researchers, independent databases
- ✅ Specialized timelines (topic-specific corruption)
- ✅ Staging/production workflows
- ✅ International instances

### Future Extraction Benefits
- ✅ Clean service boundaries
- ✅ Repository-agnostic design
- ✅ Easy to extract into separate app
- ✅ Timeline repo becomes pure data repository
- ✅ Research tools become standalone platform

---

## Success Criteria

### Phase 2 Complete When:
- ✅ GitService operational (clone, pull, commit, push)
- ✅ TimelineSyncService replaces filesystem sync
- ✅ PRBuilderService can create GitHub PRs
- ✅ CLI commands work (`git-pull`, `create-pr`)
- ✅ All tests pass (no regression)
- ✅ Filesystem sync code removed
- ✅ Multi-tenant configuration works

### Validation Tests:
- Create PR from main timeline → verify on GitHub
- Pull changes from timeline → verify DB updated
- Switch to fork → verify working independently
- Run two servers on different repos → both work

---

**Next Steps**:
1. Complete Phase 1 (test fixes)
2. Begin Phase 2A implementation
3. Build git service with multi-tenant from day 1
4. Prepare for clean extraction in Phase 5

**Last Updated**: 2025-10-16
