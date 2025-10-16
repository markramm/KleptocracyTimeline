#!/usr/bin/env python3
"""
Research API CLI - Agentic Interface
====================================

A command-line interface designed for AI agents to interact with the Research Monitor v2 API.
All input/output is JSON for easy parsing and automation.

Usage:
    python3 research_cli.py <command> [options]

Commands:
    search-events       Search timeline events
    get-next-priority   Get next research priority
    update-priority     Update priority status
    create-event        Create new timeline event
    get-stats          Get system statistics
    list-tags          List all available tags
    list-actors        List all actors
    validate-event     Validate event data
    help               Get comprehensive help documentation

Git Service Layer:
    git-pull           Pull latest from timeline repository
    git-status         Check repository sync status
    create-pr          Create GitHub Pull Request
    git-config         Show git configuration

All commands return JSON output for easy parsing.
"""

import sys
import json
import argparse
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

# Import the comprehensive research client
sys.path.insert(0, str(Path(__file__).parent))
from research_client import TimelineResearchClient

# Add server management capability
sys.path.append(str(Path(__file__).parent / "research_monitor"))
try:
    from server_manager import ServerManager
except ImportError:
    ServerManager = None

# Add git service layer imports
try:
    from research_monitor.core.config import GitConfig
    from research_monitor.services.git_service import GitService
    from research_monitor.services.timeline_sync import TimelineSyncService
    from research_monitor.services.pr_builder import PRBuilderService
    GIT_SERVICES_AVAILABLE = True
except ImportError:
    GIT_SERVICES_AVAILABLE = False

# Configuration
API_BASE_URL = "http://localhost:5558"
API_KEY = "test-key"  # For authenticated endpoints

class ResearchCLIWrapper:
    """CLI wrapper around TimelineResearchClient with structured JSON responses."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.client = TimelineResearchClient(base_url)
        self.api_key = API_KEY
    
    def _make_request(self, func, *args, **kwargs) -> Dict[str, Any]:
        """Execute client method and return structured CLI response."""
        try:
            data = func(*args, **kwargs)
            return {
                "success": True,
                "status_code": 200,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "data": data
            }
        except Exception as e:
            # Parse error details
            error_msg = str(e)
            status_code = 500
            
            if "API Error" in error_msg and ":" in error_msg:
                try:
                    status_code = int(error_msg.split("API Error ")[1].split(":")[0])
                except:
                    pass
            elif "HTTP Error" in error_msg:
                try:
                    status_code = int(error_msg.split("HTTP Error ")[1].split(":")[0])
                except:
                    pass
                    
            return {
                "success": False,
                "status_code": status_code,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "error": {
                    "message": error_msg,
                    "details": "Check server status and API endpoint availability"
                }
            }
    
    # Core API Methods
    
    def search_events(self, query: str, limit: int = 50) -> Dict[str, Any]:
        """Search timeline events."""
        return self._make_request(self.client.search, query, limit=limit)
    
    def get_next_priority(self) -> Dict[str, Any]:
        """Get next research priority."""
        return self._make_request(self.client.get_next_priority)
    
    def update_priority(self, priority_id: str, status: str, notes: Optional[str] = None, 
                       actual_events: Optional[int] = None) -> Dict[str, Any]:
        """Update priority status."""
        return self._make_request(self.client.update_priority, priority_id, status, notes, actual_events)
    
    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new timeline event."""
        return self._make_request(self.client.create_event, event_data)
    
    def validate_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate event data without creating it."""
        return self._make_request(self.client.validate_event, event_data)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        return self._make_request(self.client.get_stats)
    
    def list_tags(self) -> Dict[str, Any]:
        """List all available tags."""
        return self._make_request(self.client.get_tags)
    
    def list_actors(self) -> Dict[str, Any]:
        """List all actors."""
        return self._make_request(self.client.get_actors)
    
    def get_events(self, page: int = 1, per_page: int = 50, 
                   start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get timeline events with pagination."""
        filters = {"page": page, "per_page": per_page}
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        return self._make_request(self.client.get_events, **filters)
    
    def get_event_by_id(self, event_id: str) -> Dict[str, Any]:
        """Get specific event by ID."""
        return self._make_request(self.client.get_event, event_id)
    
    def check_commit_status(self) -> Dict[str, Any]:
        """Check if commit is needed."""
        return self._make_request(self.client.get_commit_status)
    
    def reset_commit_counter(self) -> Dict[str, Any]:
        """Reset commit counter."""
        return self._make_request(self.client.reset_commit_counter)
    
    # Research Enhancement Methods
    
    def get_events_missing_sources(self, min_sources: int = 2, limit: int = 50) -> Dict[str, Any]:
        """Find events with insufficient sources."""
        return self._make_request(self.client.get_events_missing_sources, min_sources, limit)
    
    def get_validation_queue(self, limit: int = 50) -> Dict[str, Any]:
        """Get events prioritized for validation."""
        return self._make_request(self.client.get_validation_queue, limit)
    
    def get_broken_links(self, limit: int = 50) -> Dict[str, Any]:
        """Find events with potentially broken source links."""
        return self._make_request(self.client.get_broken_links, limit)
    
    def get_research_candidates(self, min_importance: int = 7, limit: int = 50) -> Dict[str, Any]:
        """Get high-importance events with insufficient sources."""
        return self._make_request(self.client.get_research_candidates, min_importance, limit)
    
    def get_actor_timeline(self, actor: str, start_year: Optional[int] = None, 
                          end_year: Optional[int] = None) -> Dict[str, Any]:
        """Get comprehensive timeline for specific actor."""
        return self._make_request(self.client.get_actor_timeline, actor, start_year, end_year)
    
    # QA Queue Methods
    
    def get_qa_queue(self, limit: int = 50, offset: int = 0, 
                     min_importance: int = 1, include_validated: bool = False) -> Dict[str, Any]:
        """Get prioritized queue of events needing QA."""
        return self._make_request(self.client.get_qa_queue, limit, offset, min_importance, include_validated)
    
    def get_next_qa_event(self, min_importance: int = 7) -> Dict[str, Any]:
        """Get the next highest priority event for QA."""
        return self._make_request(self.client.get_next_qa_event, min_importance)
    
    def get_qa_stats(self) -> Dict[str, Any]:
        """Get comprehensive QA statistics."""
        return self._make_request(self.client.get_qa_stats)
    
    def mark_event_validated(self, event_id: str, quality_score: float, 
                           validation_notes: str = "", created_by: str = "qa-agent") -> Dict[str, Any]:
        """Mark an event as validated with quality score."""
        return self._make_request(self.client.mark_event_validated, event_id, quality_score, validation_notes, created_by)
    
    def enhance_event_with_qa(self, event_id: str, enhanced_event_file: str, quality_score: float, 
                             validation_notes: str = "", created_by: str = "qa-agent") -> Dict[str, Any]:
        """Enhance an event with improved content and record QA metadata."""
        return self._make_request(self.client.enhance_event_with_qa, event_id, enhanced_event_file, quality_score, validation_notes, created_by)
    
    def mark_event_in_progress(self, event_id: str, created_by: str = "qa-agent", 
                              agent_id: str = None) -> Dict[str, Any]:
        """Mark an event as in_progress to prevent duplicate processing."""
        return self._make_request(self.client.mark_event_in_progress, event_id, created_by, agent_id)
    
    def mark_event_rejected(self, event_id: str, rejection_reason: str, created_by: str = "qa-agent") -> Dict[str, Any]:
        """Mark an event as rejected with detailed reasoning."""
        return self._make_request(self.client.mark_event_rejected, event_id, rejection_reason, created_by)
    
    def get_qa_candidates_by_issue(self, issue_type: str, limit: int = 20) -> Dict[str, Any]:
        """Get events with specific QA issues."""
        return self._make_request(self.client.get_qa_candidates_by_issue, issue_type, limit)
    
    def calculate_qa_score(self, event_data: Dict, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Calculate QA priority score for event data."""
        return self._make_request(self.client.calculate_qa_score, event_data, metadata)
    
    def initialize_validation_audit_trail(self, created_by: str = "cli-init", dry_run: bool = False) -> Dict[str, Any]:
        """Initialize metadata records for all events to create complete validation audit trail."""
        return self._make_request(self.client.initialize_validation_audit_trail, created_by, dry_run)
    
    def reset_validation_audit_trail(self, created_by: str = "cli-reset", dry_run: bool = False) -> Dict[str, Any]:
        """Reset all validation records to pending status for complete re-validation."""
        return self._make_request(self.client.reset_validation_audit_trail, created_by, dry_run)
    
    def get_help(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive help documentation."""
        try:
            help_text = self.client.help(topic)
            return {
                "success": True,
                "status_code": 200,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "data": {"help": help_text}
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 400,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "error": {
                    "message": str(e),
                    "details": "Invalid help topic requested"
                }
            }

    # ============ Validation Runs System Methods ============
    
    def list_validation_runs(self, status: Optional[str] = None, run_type: Optional[str] = None, 
                           limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """List validation runs with optional filtering."""
        return self._make_request(self.client.list_validation_runs, status, run_type, limit, offset)
    
    def create_validation_run(self, run_type: str, **kwargs) -> Dict[str, Any]:
        """Create a new validation run."""
        return self._make_request(self.client.create_validation_run, run_type, **kwargs)
    
    def get_validation_run(self, run_id: int) -> Dict[str, Any]:
        """Get detailed information about a validation run."""
        return self._make_request(self.client.get_validation_run, run_id)
    
    def get_next_validation_event(self, run_id: int, validator_id: Optional[str] = None) -> Dict[str, Any]:
        """Get next event to validate from a validation run."""
        return self._make_request(self.client.get_next_validation_event, run_id, validator_id)
    
    def complete_validation_run_event(self, run_id: int, run_event_id: int, 
                                    status: str = 'completed', notes: str = '') -> Dict[str, Any]:
        """Complete a validation run event."""
        return self._make_request(self.client.complete_validation_run_event, run_id, run_event_id, status, notes)
    
    def requeue_needs_work_events(self, run_id: int) -> Dict[str, Any]:
        """Requeue events marked as 'needs_work' back to pending status."""
        return self._make_request(self.client.requeue_needs_work_events, run_id)
    
    def create_validation_log(self, event_id: str, validator_type: str, status: str, notes: str, **kwargs) -> Dict[str, Any]:
        """Create a validation log entry."""
        # Parse JSON string fields before passing to client
        for field in ['issues_found', 'sources_verified', 'corrections_made', 'validation_criteria']:
            if field in kwargs and kwargs[field]:
                try:
                    kwargs[field] = json.loads(kwargs[field])
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "status_code": 400,
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                        "error": {
                            "message": f"Invalid JSON for {field}",
                            "details": f"Failed to parse JSON string for {field}"
                        }
                    }
        
        return self._make_request(self.client.create_validation_log, event_id, validator_type, status, notes, **kwargs)
    
    def list_validation_logs(self, event_id: Optional[str] = None, validation_run_id: Optional[int] = None,
                           validator_type: Optional[str] = None, status: Optional[str] = None,
                           limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List validation logs with optional filtering."""
        return self._make_request(self.client.list_validation_logs, event_id, validation_run_id, validator_type, status, limit, offset)
    
    def list_event_update_failures(self, event_id: Optional[str] = None, failure_type: Optional[str] = None,
                                  validator_id: Optional[str] = None, resolved: Optional[str] = None,
                                  limit: int = 25, offset: int = 0) -> Dict[str, Any]:
        """List event update failures with optional filtering."""
        return self._make_request(self.client.list_event_update_failures, event_id, failure_type, validator_id, resolved, limit, offset)
    
    def get_event_update_failure_stats(self) -> Dict[str, Any]:
        """Get statistics about event update failures."""
        return self._make_request(self.client.get_event_update_failure_stats)

    # ============ Git Service Layer Methods ============

    def _get_git_services(self, repo_url: Optional[str] = None,
                          branch: Optional[str] = None) -> Dict[str, Any]:
        """Initialize git services with optional configuration override."""
        if not GIT_SERVICES_AVAILABLE:
            return {
                "success": False,
                "status_code": 500,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "error": {
                    "message": "Git services not available",
                    "details": "Missing git service dependencies"
                }
            }

        try:
            # Create config with overrides if provided
            config = GitConfig()
            if repo_url:
                config.TIMELINE_REPO_URL = repo_url
            if branch:
                config.TIMELINE_BRANCH = branch

            git_service = GitService(config)
            sync_service = TimelineSyncService(git_service)
            pr_service = PRBuilderService(git_service, sync_service)

            return {
                "success": True,
                "git": git_service,
                "sync": sync_service,
                "pr": pr_service
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 500,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "error": {
                    "message": str(e),
                    "details": "Failed to initialize git services"
                }
            }

    def git_pull(self, repo_url: Optional[str] = None, branch: Optional[str] = None) -> Dict[str, Any]:
        """Pull latest changes from timeline repository."""
        services = self._get_git_services(repo_url, branch)
        if not services["success"]:
            return services

        try:
            # Clone or update repository
            result = services["git"].clone_or_update()

            # Get sync status
            sync_result = services["sync"].import_from_repo()

            return {
                "success": True,
                "status_code": 200,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "data": {
                    "git_result": result,
                    "sync_result": sync_result,
                    "workspace": str(services["git"].workspace)
                }
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 500,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "error": {
                    "message": str(e),
                    "details": "Failed to pull from repository"
                }
            }

    def git_status(self, repo_url: Optional[str] = None, branch: Optional[str] = None) -> Dict[str, Any]:
        """Get current git repository status."""
        services = self._get_git_services(repo_url, branch)
        if not services["success"]:
            return services

        try:
            git_status = services["git"].get_status()
            sync_status = services["sync"].get_sync_status()

            return {
                "success": True,
                "status_code": 200,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "data": {
                    "git_status": git_status,
                    "sync_status": sync_status
                }
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 500,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "error": {
                    "message": str(e),
                    "details": "Failed to get repository status"
                }
            }

    def create_pr(self, event_ids: Optional[str] = None,
                  title: Optional[str] = None,
                  description: Optional[str] = None,
                  repo_url: Optional[str] = None,
                  branch: Optional[str] = None) -> Dict[str, Any]:
        """Create GitHub Pull Request with validated events."""
        services = self._get_git_services(repo_url, branch)
        if not services["success"]:
            return services

        try:
            # Get events to include in PR
            if event_ids:
                # Get specific events by ID
                event_id_list = [eid.strip() for eid in event_ids.split(',')]
                events = []
                for event_id in event_id_list:
                    event = services["sync"].get_workspace_event(event_id)
                    if event:
                        events.append(event)
                    else:
                        return {
                            "success": False,
                            "status_code": 404,
                            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                            "error": {
                                "message": f"Event not found: {event_id}",
                                "details": "Check event ID and try again"
                            }
                        }
            else:
                # Get all workspace events
                event_ids_all = services["sync"].list_workspace_events()
                events = [services["sync"].get_workspace_event(eid) for eid in event_ids_all]
                events = [e for e in events if e is not None]

            if not events:
                return {
                    "success": False,
                    "status_code": 400,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                    "error": {
                        "message": "No events available for PR",
                        "details": "Workspace has no events to export"
                    }
                }

            # Create PR
            pr_result = services["pr"].create_pr(events, title, description)

            if pr_result["success"]:
                return {
                    "success": True,
                    "status_code": 201,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                    "data": pr_result
                }
            else:
                return {
                    "success": False,
                    "status_code": 500,
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                    "error": {
                        "message": pr_result.get("error", "PR creation failed"),
                        "details": "Check GitHub token and repository configuration"
                    }
                }
        except Exception as e:
            return {
                "success": False,
                "status_code": 500,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "error": {
                    "message": str(e),
                    "details": "Failed to create pull request"
                }
            }

    def git_config_show(self) -> Dict[str, Any]:
        """Show current git configuration."""
        if not GIT_SERVICES_AVAILABLE:
            return {
                "success": False,
                "status_code": 500,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "error": {
                    "message": "Git services not available",
                    "details": "Missing git service dependencies"
                }
            }

        try:
            config = GitConfig()
            validation = PRBuilderService(
                GitService(config),
                TimelineSyncService(GitService(config))
            ).validate_github_config()

            return {
                "success": True,
                "status_code": 200,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "data": {
                    "repo_url": config.TIMELINE_REPO_URL,
                    "branch": config.TIMELINE_BRANCH,
                    "workspace": str(config.TIMELINE_WORKSPACE),
                    "workspace_isolation": config.WORKSPACE_ISOLATION,
                    "has_github_token": bool(config.GITHUB_TOKEN),
                    "validation": validation
                }
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 500,
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
                "error": {
                    "message": str(e),
                    "details": "Failed to get git configuration"
                }
            }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Research API CLI - Agentic Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Search for events about Trump
    python3 research_cli.py search-events --query "Trump"
    
    # Get next research priority
    python3 research_cli.py get-next-priority
    
    # Update priority status
    python3 research_cli.py update-priority --id "RP-123" --status "completed" --notes "Research finished"
    
    # Create new event from JSON file
    python3 research_cli.py create-event --file event.json
    
    # Get system statistics
    python3 research_cli.py get-stats
    
    # Research enhancement commands
    python3 research_cli.py missing-sources --min-sources 2 --limit 5
    python3 research_cli.py research-candidates --min-importance 8
    python3 research_cli.py actor-timeline --actor "Trump"

    # Git service layer commands
    python3 research_cli.py git-pull
    python3 research_cli.py git-status
    python3 research_cli.py create-pr
    python3 research_cli.py create-pr --events "2025-01-15--event-1,2025-01-16--event-2"
    python3 research_cli.py git-config
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Search events
    search_parser = subparsers.add_parser('search-events', help='Search timeline events')
    search_parser.add_argument('--query', '-q', required=True, help='Search query')
    search_parser.add_argument('--limit', '-l', type=int, default=50, help='Max results (default: 50)')
    
    # Get next priority
    subparsers.add_parser('get-next-priority', help='Get next research priority')
    
    # Update priority
    update_parser = subparsers.add_parser('update-priority', help='Update priority status')
    update_parser.add_argument('--id', required=True, help='Priority ID')
    update_parser.add_argument('--status', required=True, choices=['pending', 'in_progress', 'completed'], help='New status')
    update_parser.add_argument('--notes', help='Optional notes')
    update_parser.add_argument('--actual-events', type=int, help='Number of events actually created')
    
    # Create event
    create_parser = subparsers.add_parser('create-event', help='Create new timeline event')
    create_group = create_parser.add_mutually_exclusive_group(required=True)
    create_group.add_argument('--file', help='JSON file containing event data')
    create_group.add_argument('--json', help='JSON string containing event data')
    
    # Validate event
    validate_parser = subparsers.add_parser('validate-event', help='Validate event data')
    validate_group = validate_parser.add_mutually_exclusive_group(required=True)
    validate_group.add_argument('--file', help='JSON file containing event data')
    validate_group.add_argument('--json', help='JSON string containing event data')
    
    # Get stats
    subparsers.add_parser('get-stats', help='Get system statistics')
    
    # List tags
    subparsers.add_parser('list-tags', help='List all available tags')
    
    # List actors
    subparsers.add_parser('list-actors', help='List all actors')
    
    # Help command
    help_parser = subparsers.add_parser('help', help='Get comprehensive help documentation')
    help_parser.add_argument('--topic', help='Specific help topic (search, validation, timeline, events, research, examples, endpoints)')
    
    # Get events
    events_parser = subparsers.add_parser('get-events', help='Get timeline events')
    events_parser.add_argument('--page', type=int, default=1, help='Page number (default: 1)')
    events_parser.add_argument('--per-page', type=int, default=50, help='Results per page (default: 50)')
    events_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    events_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    
    # Get event by ID
    get_event_parser = subparsers.add_parser('get-event', help='Get event by ID')
    get_event_parser.add_argument('--id', required=True, help='Event ID')
    
    # Commit status
    subparsers.add_parser('commit-status', help='Check commit status')
    subparsers.add_parser('reset-commit', help='Reset commit counter')
    
    # Research Enhancement Endpoints
    missing_sources_parser = subparsers.add_parser('missing-sources', help='Find events with insufficient sources')
    missing_sources_parser.add_argument('--min-sources', type=int, default=2, help='Minimum sources required (default: 2)')
    missing_sources_parser.add_argument('--limit', type=int, default=50, help='Max results (default: 50)')
    
    validation_queue_parser = subparsers.add_parser('validation-queue', help='Get events needing validation')
    validation_queue_parser.add_argument('--limit', type=int, default=50, help='Max results (default: 50)')
    
    broken_links_parser = subparsers.add_parser('broken-links', help='Find events with potentially broken source links')
    broken_links_parser.add_argument('--limit', type=int, default=50, help='Max results (default: 50)')
    
    research_candidates_parser = subparsers.add_parser('research-candidates', help='Get high-importance events with insufficient sources')
    research_candidates_parser.add_argument('--min-importance', type=int, default=7, help='Minimum importance score (default: 7)')
    research_candidates_parser.add_argument('--limit', type=int, default=50, help='Max results (default: 50)')
    
    actor_timeline_parser = subparsers.add_parser('actor-timeline', help='Get comprehensive timeline for specific actor')
    actor_timeline_parser.add_argument('--actor', required=True, help='Actor name')
    actor_timeline_parser.add_argument('--start-year', type=int, help='Start year filter')
    actor_timeline_parser.add_argument('--end-year', type=int, help='End year filter')
    
    # QA Queue Commands
    qa_queue_parser = subparsers.add_parser('qa-queue', help='Get prioritized queue of events needing QA')
    qa_queue_parser.add_argument('--limit', type=int, default=50, help='Max results (default: 50)')
    qa_queue_parser.add_argument('--offset', type=int, default=0, help='Offset for pagination (default: 0)')
    qa_queue_parser.add_argument('--min-importance', type=int, default=1, help='Minimum importance score (default: 1)')
    qa_queue_parser.add_argument('--include-validated', action='store_true', help='Include already validated events')
    
    qa_next_parser = subparsers.add_parser('qa-next', help='Get next highest priority event for QA')
    qa_next_parser.add_argument('--min-importance', type=int, default=7, help='Minimum importance score (default: 7)')
    
    subparsers.add_parser('qa-stats', help='Get comprehensive QA statistics')
    
    qa_validate_parser = subparsers.add_parser('qa-validate', help='Mark an event as validated with quality score')
    qa_validate_parser.add_argument('--event-id', required=True, help='Event ID to validate')
    qa_validate_parser.add_argument('--quality-score', type=float, required=True, help='Quality score (0-10)')
    qa_validate_parser.add_argument('--validation-notes', default='', help='Optional validation notes')
    qa_validate_parser.add_argument('--created-by', default='qa-agent', help='Who performed the validation')
    
    qa_enhance_parser = subparsers.add_parser('qa-enhance', help='Enhance an event with improved content and QA validation')
    qa_enhance_parser.add_argument('--event-id', required=True, help='Event ID to enhance')
    qa_enhance_parser.add_argument('--enhanced-event-file', required=True, help='Path to JSON file with enhanced event content')
    qa_enhance_parser.add_argument('--quality-score', type=float, required=True, help='Quality score (0-10) for the enhanced event')
    qa_enhance_parser.add_argument('--validation-notes', default='', help='Notes about the enhancements made')
    qa_enhance_parser.add_argument('--created-by', default='qa-agent', help='Who performed the enhancement')
    
    # QA start processing command
    qa_start_parser = subparsers.add_parser('qa-start', help='Mark event as in_progress to prevent duplicate processing')
    qa_start_parser.add_argument('--event-id', required=True, help='Event ID to mark as in_progress')
    qa_start_parser.add_argument('--created-by', default='qa-agent', help='Who is starting the processing')
    qa_start_parser.add_argument('--agent-id', help='Agent identifier for tracking')
    
    qa_reject_parser = subparsers.add_parser('qa-reject', help='Mark an event as rejected with detailed reasoning')
    qa_reject_parser.add_argument('--event-id', required=True, help='Event ID to reject')
    qa_reject_parser.add_argument('--rejection-reason', required=True, help='Detailed reason for rejection')
    qa_reject_parser.add_argument('--created-by', default='qa-agent', help='Who performed the rejection')
    
    # Validation Audit Trail Commands
    validation_init_parser = subparsers.add_parser('validation-init', help='Initialize validation audit trail for all events')
    validation_init_parser.add_argument('--created-by', default='cli-init', help='Who initiated the validation audit trail')
    validation_init_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    validation_reset_parser = subparsers.add_parser('validation-reset', help='Reset all validation records to pending status')
    validation_reset_parser.add_argument('--created-by', default='cli-reset', help='Who reset the validation audit trail')
    validation_reset_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    
    qa_issues_parser = subparsers.add_parser('qa-issues', help='Get events with specific QA issues')
    qa_issues_parser.add_argument('--issue-type', required=True, help='Type of QA issue (e.g., "No sources", "Missing actors")')
    qa_issues_parser.add_argument('--limit', type=int, default=20, help='Max results (default: 20)')
    
    qa_score_parser = subparsers.add_parser('qa-score', help='Calculate QA priority score for event data')
    qa_score_group = qa_score_parser.add_mutually_exclusive_group(required=True)
    qa_score_group.add_argument('--file', help='JSON file containing event data')
    qa_score_group.add_argument('--json', help='JSON string containing event data')
    
    # Server management commands
    server_status_parser = subparsers.add_parser('server-status', help='Get research monitor server status')
    
    server_start_parser = subparsers.add_parser('server-start', help='Start research monitor server')
    server_start_parser.add_argument('--foreground', action='store_true', help='Start server in foreground')
    
    server_stop_parser = subparsers.add_parser('server-stop', help='Stop research monitor server')
    server_stop_parser.add_argument('--force', action='store_true', help='Force stop server')
    
    server_restart_parser = subparsers.add_parser('server-restart', help='Restart research monitor server')
    
    server_logs_parser = subparsers.add_parser('server-logs', help='Get research monitor server logs')
    server_logs_parser.add_argument('--lines', type=int, default=50, help='Number of log lines to show')

    # Git Service Layer Commands
    git_pull_parser = subparsers.add_parser('git-pull', help='Pull latest changes from timeline repository')
    git_pull_parser.add_argument('--repo-url', help='Repository URL (overrides environment variable)')
    git_pull_parser.add_argument('--branch', help='Branch name (overrides environment variable)')

    git_status_parser = subparsers.add_parser('git-status', help='Get git repository status')
    git_status_parser.add_argument('--repo-url', help='Repository URL (overrides environment variable)')
    git_status_parser.add_argument('--branch', help='Branch name (overrides environment variable)')

    create_pr_parser = subparsers.add_parser('create-pr', help='Create GitHub Pull Request with events')
    create_pr_parser.add_argument('--events', help='Comma-separated event IDs (default: all workspace events)')
    create_pr_parser.add_argument('--title', help='PR title (auto-generated if not provided)')
    create_pr_parser.add_argument('--description', help='PR description (auto-generated if not provided)')
    create_pr_parser.add_argument('--repo-url', help='Repository URL (overrides environment variable)')
    create_pr_parser.add_argument('--branch', help='Base branch (overrides environment variable)')

    git_config_parser = subparsers.add_parser('git-config', help='Show git configuration')

    # Validation Runs System Commands
    validation_runs_list_parser = subparsers.add_parser('validation-runs-list', help='List validation runs')
    validation_runs_list_parser.add_argument('--status', help='Filter by status (active, completed, paused, cancelled)')
    validation_runs_list_parser.add_argument('--type', help='Filter by run type (random_sample, importance_focused, date_range, pattern_detection)')
    validation_runs_list_parser.add_argument('--limit', type=int, default=20, help='Max results (default: 20)')
    validation_runs_list_parser.add_argument('--offset', type=int, default=0, help='Offset for pagination (default: 0)')
    
    validation_runs_create_parser = subparsers.add_parser('validation-runs-create', help='Create new validation run')
    validation_runs_create_parser.add_argument('--run-type', required=True, 
                                             choices=['random_sample', 'importance_focused', 'date_range', 'pattern_detection', 'source_quality'],
                                             help='Type of validation run to create')
    validation_runs_create_parser.add_argument('--target-count', type=int, help='Target number of events for the run')
    validation_runs_create_parser.add_argument('--min-importance', type=int, help='Minimum importance score')
    validation_runs_create_parser.add_argument('--start-date', help='Start date for date_range runs (YYYY-MM-DD)')
    validation_runs_create_parser.add_argument('--end-date', help='End date for date_range runs (YYYY-MM-DD)')
    validation_runs_create_parser.add_argument('--pattern-keywords', nargs='+', help='Keywords for pattern_detection runs')
    validation_runs_create_parser.add_argument('--pattern-description', help='Description for pattern_detection runs')
    validation_runs_create_parser.add_argument('--exclude-recent-validations', action='store_true', help='Skip recently validated events')
    validation_runs_create_parser.add_argument('--focus-unvalidated', action='store_true', help='Focus on unvalidated events')
    validation_runs_create_parser.add_argument('--created-by', default='cli', help='Creator identifier')
    
    validation_runs_get_parser = subparsers.add_parser('validation-runs-get', help='Get validation run details')
    validation_runs_get_parser.add_argument('--run-id', type=int, required=True, help='Validation run ID')
    
    validation_runs_next_parser = subparsers.add_parser('validation-runs-next', help='Get next event from validation run')
    validation_runs_next_parser.add_argument('--run-id', type=int, required=True, help='Validation run ID')
    validation_runs_next_parser.add_argument('--validator-id', help='Validator identifier')
    
    validation_runs_complete_parser = subparsers.add_parser('validation-runs-complete', help='Complete validation run event')
    validation_runs_complete_parser.add_argument('--run-id', type=int, required=True, help='Validation run ID')
    validation_runs_complete_parser.add_argument('--run-event-id', type=int, required=True, help='Run event ID')
    validation_runs_complete_parser.add_argument('--status', default='validated', 
                                               choices=['validated', 'needs_work', 'skipped', 'rejected'],
                                               help='Completion status')
    validation_runs_complete_parser.add_argument('--notes', default='', help='Completion notes')
    
    validation_runs_requeue_parser = subparsers.add_parser('validation-runs-requeue', help='Requeue events that need more work')
    validation_runs_requeue_parser.add_argument('--run-id', type=int, required=True, help='Validation run ID')
    
    validation_logs_create_parser = subparsers.add_parser('validation-logs-create', help='Create validation log entry')
    validation_logs_create_parser.add_argument('--event-id', required=True, help='Event ID')
    validation_logs_create_parser.add_argument('--validator-type', required=True, 
                                             choices=['human', 'agent', 'automated'],
                                             help='Type of validator')
    validation_logs_create_parser.add_argument('--status', required=True,
                                             choices=['validated', 'rejected', 'needs_work', 'flagged'],
                                             help='Validation status')
    validation_logs_create_parser.add_argument('--notes', required=True, help='Validation notes')
    validation_logs_create_parser.add_argument('--validator-id', help='Validator identifier')
    validation_logs_create_parser.add_argument('--validation-run-id', type=int, help='Associated validation run ID')
    validation_logs_create_parser.add_argument('--confidence', type=float, help='Confidence score (0-1)')
    validation_logs_create_parser.add_argument('--issues-found', help='JSON string of issues found')
    validation_logs_create_parser.add_argument('--sources-verified', help='JSON string of sources verified')
    validation_logs_create_parser.add_argument('--corrections-made', help='JSON string of corrections made')
    validation_logs_create_parser.add_argument('--time-spent-minutes', type=float, help='Time spent validating')
    validation_logs_create_parser.add_argument('--validation-criteria', help='JSON string of validation criteria used')
    
    validation_logs_list_parser = subparsers.add_parser('validation-logs-list', help='List validation logs')
    validation_logs_list_parser.add_argument('--event-id', help='Filter by event ID')
    validation_logs_list_parser.add_argument('--validation-run-id', type=int, help='Filter by validation run ID')
    validation_logs_list_parser.add_argument('--validator-type', help='Filter by validator type')
    validation_logs_list_parser.add_argument('--status', help='Filter by validation status')
    validation_logs_list_parser.add_argument('--limit', type=int, default=50, help='Max results (default: 50)')
    validation_logs_list_parser.add_argument('--offset', type=int, default=0, help='Offset for pagination (default: 0)')

    # Event Update Failures Management
    update_failures_list_parser = subparsers.add_parser('update-failures-list', help='List event update failures')
    update_failures_list_parser.add_argument('--event-id', help='Filter by event ID')
    update_failures_list_parser.add_argument('--failure-type', help='Filter by failure type (file_not_found, permission_error, etc.)')
    update_failures_list_parser.add_argument('--validator-id', help='Filter by validator ID')
    update_failures_list_parser.add_argument('--resolved', help='Filter by resolved status (true/false)')
    update_failures_list_parser.add_argument('--limit', type=int, default=25, help='Max results (default: 25)')
    update_failures_list_parser.add_argument('--offset', type=int, default=0, help='Offset for pagination (default: 0)')
    
    update_failures_stats_parser = subparsers.add_parser('update-failures-stats', help='Get event update failure statistics')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize client
    client = ResearchCLIWrapper()
    
    # Execute command
    try:
        if args.command == 'search-events':
            result = client.search_events(args.query, args.limit)
        
        elif args.command == 'get-next-priority':
            result = client.get_next_priority()
        
        elif args.command == 'update-priority':
            result = client.update_priority(args.id, args.status, args.notes, args.actual_events)
        
        elif args.command == 'create-event':
            # Load event data
            if args.file:
                with open(args.file, 'r') as f:
                    event_data = json.load(f)
            else:
                event_data = json.loads(args.json)
            result = client.create_event(event_data)
        
        elif args.command == 'validate-event':
            # Load event data
            if args.file:
                with open(args.file, 'r') as f:
                    event_data = json.load(f)
            else:
                event_data = json.loads(args.json)
            result = client.validate_event(event_data)
        
        elif args.command == 'get-stats':
            result = client.get_stats()
        
        elif args.command == 'list-tags':
            result = client.list_tags()
        
        elif args.command == 'list-actors':
            result = client.list_actors()
        
        elif args.command == 'get-events':
            result = client.get_events(args.page, args.per_page, args.start_date, args.end_date)
        
        elif args.command == 'get-event':
            result = client.get_event_by_id(args.id)
        
        elif args.command == 'commit-status':
            result = client.check_commit_status()
        
        elif args.command == 'reset-commit':
            result = client.reset_commit_counter()
        
        elif args.command == 'missing-sources':
            result = client.get_events_missing_sources(args.min_sources, args.limit)
        
        elif args.command == 'validation-queue':
            result = client.get_validation_queue(args.limit)
        
        elif args.command == 'broken-links':
            result = client.get_broken_links(args.limit)
        
        elif args.command == 'research-candidates':
            result = client.get_research_candidates(args.min_importance, args.limit)
        
        elif args.command == 'actor-timeline':
            result = client.get_actor_timeline(args.actor, args.start_year, args.end_year)
        
        elif args.command == 'qa-queue':
            result = client.get_qa_queue(args.limit, args.offset, args.min_importance, args.include_validated)
        
        elif args.command == 'qa-next':
            result = client.get_next_qa_event(args.min_importance)
        
        elif args.command == 'qa-stats':
            result = client.get_qa_stats()
        
        elif args.command == 'qa-validate':
            result = client.mark_event_validated(args.event_id, args.quality_score, args.validation_notes, args.created_by)
        
        elif args.command == 'qa-enhance':
            result = client.enhance_event_with_qa(args.event_id, args.enhanced_event_file, args.quality_score, args.validation_notes, args.created_by)
        
        elif args.command == 'qa-start':
            result = client.mark_event_in_progress(args.event_id, args.created_by, args.agent_id)
        
        elif args.command == 'qa-reject':
            result = client.mark_event_rejected(args.event_id, args.rejection_reason, args.created_by)
        
        elif args.command == 'validation-init':
            result = client.initialize_validation_audit_trail(args.created_by, args.dry_run)
        
        elif args.command == 'validation-reset':
            result = client.reset_validation_audit_trail(args.created_by, args.dry_run)
        
        elif args.command == 'qa-issues':
            result = client.get_qa_candidates_by_issue(args.issue_type, args.limit)
        
        elif args.command == 'qa-score':
            # Load event data
            if args.file:
                with open(args.file, 'r') as f:
                    event_data = json.load(f)
            else:
                event_data = json.loads(args.json)
            result = client.calculate_qa_score(event_data)
        
        # Server management commands
        elif args.command.startswith('server-'):
            if ServerManager is None:
                result = {"success": False, "error": {"message": "Server management not available. Missing dependencies."}}
            else:
                manager = ServerManager()
                
                if args.command == 'server-status':
                    result = manager.get_server_status()
                    result["success"] = True
                
                elif args.command == 'server-start':
                    result = manager.start_server(background=not args.foreground)
                
                elif args.command == 'server-stop':
                    result = manager.stop_server(force=args.force)
                
                elif args.command == 'server-restart':
                    result = manager.restart_server()
                
                elif args.command == 'server-logs':
                    logs = manager.get_server_logs(lines=args.lines)
                    result = {"success": True, "logs": logs, "lines": args.lines}
                
                else:
                    result = {"success": False, "error": {"message": f"Unknown server command: {args.command}"}}

        # Git Service Layer Commands
        elif args.command == 'git-pull':
            result = client.git_pull(
                repo_url=getattr(args, 'repo_url', None),
                branch=getattr(args, 'branch', None)
            )

        elif args.command == 'git-status':
            result = client.git_status(
                repo_url=getattr(args, 'repo_url', None),
                branch=getattr(args, 'branch', None)
            )

        elif args.command == 'create-pr':
            result = client.create_pr(
                event_ids=getattr(args, 'events', None),
                title=getattr(args, 'title', None),
                description=getattr(args, 'description', None),
                repo_url=getattr(args, 'repo_url', None),
                branch=getattr(args, 'branch', None)
            )

        elif args.command == 'git-config':
            result = client.git_config_show()

        # Validation Runs System Commands
        elif args.command == 'validation-runs-list':
            result = client.list_validation_runs(
                status=getattr(args, 'status', None),
                run_type=getattr(args, 'type', None),
                limit=args.limit,
                offset=args.offset
            )
        
        elif args.command == 'validation-runs-create':
            kwargs = {
                'created_by': args.created_by
            }
            
            if hasattr(args, 'target_count') and args.target_count:
                kwargs['target_count'] = args.target_count
            if hasattr(args, 'min_importance') and args.min_importance:
                kwargs['min_importance'] = args.min_importance
            if hasattr(args, 'start_date') and args.start_date:
                kwargs['start_date'] = args.start_date
            if hasattr(args, 'end_date') and args.end_date:
                kwargs['end_date'] = args.end_date
            if hasattr(args, 'pattern_keywords') and args.pattern_keywords:
                kwargs['pattern_keywords'] = args.pattern_keywords
            if hasattr(args, 'pattern_description') and args.pattern_description:
                kwargs['pattern_description'] = args.pattern_description
            if hasattr(args, 'exclude_recent_validations') and args.exclude_recent_validations:
                kwargs['exclude_recent_validations'] = True
            if hasattr(args, 'focus_unvalidated') and args.focus_unvalidated:
                kwargs['focus_unvalidated'] = True
            
            result = client.create_validation_run(args.run_type, **kwargs)
        
        elif args.command == 'validation-runs-get':
            result = client.get_validation_run(args.run_id)
        
        elif args.command == 'validation-runs-next':
            result = client.get_next_validation_event(
                args.run_id,
                getattr(args, 'validator_id', None)
            )
        
        elif args.command == 'validation-runs-complete':
            result = client.complete_validation_run_event(
                args.run_id,
                args.run_event_id,
                args.status,
                args.notes
            )
        
        elif args.command == 'validation-runs-requeue':
            result = client.requeue_needs_work_events(args.run_id)
        
        elif args.command == 'validation-logs-create':
            kwargs = {}
            
            # Add optional fields
            if hasattr(args, 'validator_id') and args.validator_id:
                kwargs['validator_id'] = args.validator_id
            if hasattr(args, 'validation_run_id') and args.validation_run_id:
                kwargs['validation_run_id'] = args.validation_run_id
            if hasattr(args, 'confidence') and args.confidence is not None:
                kwargs['confidence'] = args.confidence
            if hasattr(args, 'time_spent_minutes') and args.time_spent_minutes is not None:
                kwargs['time_spent_minutes'] = args.time_spent_minutes
            
            # Add JSON string fields
            for field in ['issues_found', 'sources_verified', 'corrections_made', 'validation_criteria']:
                if hasattr(args, field) and getattr(args, field):
                    kwargs[field] = getattr(args, field)
            
            result = client.create_validation_log(
                args.event_id,
                args.validator_type,
                args.status,
                args.notes,
                **kwargs
            )
        
        elif args.command == 'validation-logs-list':
            result = client.list_validation_logs(
                event_id=getattr(args, 'event_id', None),
                validation_run_id=getattr(args, 'validation_run_id', None),
                validator_type=getattr(args, 'validator_type', None),
                status=getattr(args, 'status', None),
                limit=args.limit,
                offset=args.offset
            )
        
        elif args.command == 'update-failures-list':
            result = client.list_event_update_failures(
                event_id=getattr(args, 'event_id', None),
                failure_type=getattr(args, 'failure_type', None),
                validator_id=getattr(args, 'validator_id', None),
                resolved=getattr(args, 'resolved', None),
                limit=args.limit,
                offset=args.offset
            )
        
        elif args.command == 'update-failures-stats':
            result = client.get_event_update_failure_stats()
        
        elif args.command == 'help':
            result = client.get_help(getattr(args, 'topic', None))
        
        else:
            result = {"success": False, "error": {"message": f"Unknown command: {args.command}"}}
        
        # Output JSON result
        print(json.dumps(result, indent=2))
        
        # Exit with appropriate code
        sys.exit(0 if result.get("success", False) else 1)
        
    except KeyboardInterrupt:
        result = {"success": False, "error": {"message": "Interrupted by user"}}
        print(json.dumps(result, indent=2))
        sys.exit(1)
    
    except Exception as e:
        result = {
            "success": False,
            "error": {
                "message": "Unexpected error",
                "details": str(e)
            },
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()