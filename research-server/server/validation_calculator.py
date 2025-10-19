#!/usr/bin/env python3
"""
ValidationRunCalculator - Calculate validation runs using different sampling strategies
Replaces static validation queue with dynamic validation run generation
"""

import random
import json
import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, text
from models import TimelineEvent, ValidationRun, ValidationRunEvent, ValidationLog


class ValidationRunCalculator:
    """
    Calculate validation runs using different sampling and prioritization strategies
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_random_sample_run(self, 
                                target_count: int = 50, 
                                min_importance: int = 5,
                                exclude_recent_validations: bool = True) -> ValidationRun:
        """
        Create a random sample validation run for timeline health assessment
        
        Args:
            target_count: Number of events to sample
            min_importance: Minimum importance score to include
            exclude_recent_validations: Skip events validated in last 30 days
        """
        
        # Base query for eligible events
        query = self.session.query(TimelineEvent).filter(
            TimelineEvent.importance >= min_importance
        )
        
        # Exclude recently validated events if requested
        if exclude_recent_validations:
            cutoff_date = datetime.now() - timedelta(days=30)
            recently_validated = self.session.query(ValidationLog.event_id).filter(
                ValidationLog.validation_date >= cutoff_date
            ).subquery()
            
            query = query.filter(
                ~TimelineEvent.id.in_(recently_validated)
            )
        
        # Get total eligible events
        total_events = query.count()
        if total_events == 0:
            raise ValueError("No events found matching criteria")
        
        # Sample events randomly
        if total_events <= target_count:
            selected_events = query.all()
        else:
            # Use random sampling
            all_events = query.all()
            selected_events = random.sample(all_events, target_count)
        
        # Create validation run
        run = ValidationRun(
            run_name=f"Random Sample - {datetime.now().strftime('%Y%m%d_%H%M')}",
            run_type='random_sample',
            target_count=target_count,
            actual_count=len(selected_events),
            selection_criteria={
                'min_importance': min_importance,
                'exclude_recent_validations': exclude_recent_validations,
                'total_eligible': total_events,
                'selection_date': datetime.now().isoformat()
            },
            created_by='system',
            events_remaining=len(selected_events)
        )
        
        self.session.add(run)
        self.session.flush()  # Get the run ID
        
        # Add events to run
        for i, event in enumerate(selected_events):
            run_event = ValidationRunEvent(
                validation_run_id=run.id,
                event_id=event.id,
                selection_reason=f"Random sample selection (importance: {event.importance})",
                selection_priority=random.random(),  # Random priority within run
                high_priority=(event.importance >= 8)
            )
            self.session.add(run_event)
        
        self.session.commit()
        return run
    
    def create_importance_focused_run(self, 
                                    target_count: int = 30,
                                    min_importance: int = 7,
                                    focus_unvalidated: bool = True) -> ValidationRun:
        """
        Create validation run focused on high-importance events
        
        Args:
            target_count: Number of events to include
            min_importance: Minimum importance score
            focus_unvalidated: Prioritize events with no recent validations
        """
        
        # Base query for high-importance events
        query = self.session.query(TimelineEvent).filter(
            TimelineEvent.importance >= min_importance
        )
        
        # Get validation status for each event
        if focus_unvalidated:
            # Subquery for events with recent validations
            recent_validations = self.session.query(ValidationLog.event_id).filter(
                ValidationLog.validation_date >= datetime.now() - timedelta(days=60)
            ).subquery()
            
            # Prioritize unvalidated events, but include validated ones if needed
            unvalidated = query.filter(~TimelineEvent.id.in_(recent_validations))
            validated = query.filter(TimelineEvent.id.in_(recent_validations))
            
            # Take unvalidated first, then fill with validated
            unvalidated_events = unvalidated.order_by(desc(TimelineEvent.importance)).all()
            
            if len(unvalidated_events) >= target_count:
                selected_events = unvalidated_events[:target_count]
            else:
                validated_events = validated.order_by(desc(TimelineEvent.importance)).limit(
                    target_count - len(unvalidated_events)
                ).all()
                selected_events = unvalidated_events + validated_events
        else:
            # Just take highest importance events
            selected_events = query.order_by(desc(TimelineEvent.importance)).limit(target_count).all()
        
        # Create validation run
        run = ValidationRun(
            run_name=f"High Importance Focus - {datetime.now().strftime('%Y%m%d_%H%M')}",
            run_type='importance_focused',
            target_count=target_count,
            actual_count=len(selected_events),
            selection_criteria={
                'min_importance': min_importance,
                'focus_unvalidated': focus_unvalidated,
                'selection_strategy': 'importance_descending',
                'selection_date': datetime.now().isoformat()
            },
            created_by='system',
            events_remaining=len(selected_events)
        )
        
        self.session.add(run)
        self.session.flush()
        
        # Add events to run with importance-based priority
        for i, event in enumerate(selected_events):
            # Higher importance = higher priority (lower number)
            priority = (10 - event.importance) + (i * 0.01)  # Break ties with selection order
            
            run_event = ValidationRunEvent(
                validation_run_id=run.id,
                event_id=event.id,
                selection_reason=f"High importance event (score: {event.importance})",
                selection_priority=priority,
                high_priority=(event.importance >= 8),
                needs_attention=(event.importance >= 9)
            )
            self.session.add(run_event)
        
        self.session.commit()
        return run
    
    def create_date_range_run(self, 
                             start_date: str,
                             end_date: str,
                             target_count: Optional[int] = None,
                             min_importance: int = 5) -> ValidationRun:
        """
        Create validation run for specific date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            target_count: Max events to include (None = all matching)
            min_importance: Minimum importance score
        """
        
        query = self.session.query(TimelineEvent).filter(
            and_(
                TimelineEvent.date >= start_date,
                TimelineEvent.date <= end_date,
                TimelineEvent.importance >= min_importance
            )
        ).order_by(desc(TimelineEvent.importance), asc(TimelineEvent.date))
        
        if target_count:
            selected_events = query.limit(target_count).all()
        else:
            selected_events = query.all()
        
        if not selected_events:
            raise ValueError(f"No events found in date range {start_date} to {end_date}")
        
        # Create validation run
        run = ValidationRun(
            run_name=f"Date Range {start_date} to {end_date} - {datetime.now().strftime('%Y%m%d_%H%M')}",
            run_type='date_range',
            target_count=target_count or len(selected_events),
            actual_count=len(selected_events),
            selection_criteria={
                'start_date': start_date,
                'end_date': end_date,
                'min_importance': min_importance,
                'selection_date': datetime.now().isoformat()
            },
            created_by='system',
            events_remaining=len(selected_events)
        )
        
        self.session.add(run)
        self.session.flush()
        
        # Add events to run
        for i, event in enumerate(selected_events):
            run_event = ValidationRunEvent(
                validation_run_id=run.id,
                event_id=event.id,
                selection_reason=f"Date range selection ({event.date})",
                selection_priority=i,  # Chronological priority
                high_priority=(event.importance >= 8)
            )
            self.session.add(run_event)
        
        self.session.commit()
        return run
    
    def create_pattern_detection_run(self, 
                                   pattern_keywords: List[str],
                                   target_count: int = 40,
                                   pattern_description: str = "") -> ValidationRun:
        """
        Create validation run to detect potential contamination or quality issues
        
        Args:
            pattern_keywords: Keywords that might indicate issues
            target_count: Max events to include
            pattern_description: Description of what pattern we're looking for
        """
        
        # Search for events matching suspicious patterns
        search_conditions = []
        for keyword in pattern_keywords:
            search_conditions.extend([
                TimelineEvent.title.contains(keyword),
                TimelineEvent.summary.contains(keyword),
                text(f"json_content LIKE '%{keyword}%'")
            ])
        
        query = self.session.query(TimelineEvent).filter(
            or_(*search_conditions)
        ).order_by(desc(TimelineEvent.importance))
        
        selected_events = query.limit(target_count).all()
        
        if not selected_events:
            raise ValueError(f"No events found matching pattern keywords: {pattern_keywords}")
        
        # Create validation run
        run = ValidationRun(
            run_name=f"Pattern Detection - {pattern_description or 'Custom'} - {datetime.now().strftime('%Y%m%d_%H%M')}",
            run_type='pattern_detection',
            target_count=target_count,
            actual_count=len(selected_events),
            selection_criteria={
                'pattern_keywords': pattern_keywords,
                'pattern_description': pattern_description,
                'selection_date': datetime.now().isoformat()
            },
            created_by='system',
            events_remaining=len(selected_events)
        )
        
        self.session.add(run)
        self.session.flush()
        
        # Add events to run with contamination risk flagging
        for i, event in enumerate(selected_events):
            run_event = ValidationRunEvent(
                validation_run_id=run.id,
                event_id=event.id,
                selection_reason=f"Pattern match: {pattern_keywords}",
                selection_priority=i,
                high_priority=True,  # Pattern detection runs are high priority
                needs_attention=True  # Flag all pattern matches for attention
            )
            self.session.add(run_event)
        
        self.session.commit()
        return run
    
    def create_source_quality_run(self, 
                                 target_count: int = 30,
                                 min_importance: int = 1) -> ValidationRun:
        """
        Create validation run targeting events with source quality issues
        
        Args:
            target_count: Number of events to sample
            min_importance: Minimum importance score to include
        """
        
        # Find events with placeholder or problematic sources
        query = self.session.query(TimelineEvent).filter(
            TimelineEvent.importance >= min_importance
        )
        
        # Filter for events with source quality issues using SQLite JSON functions
        
        # Use SQLite JSON functions to search within sources
        source_quality_issues = query.filter(
            or_(
                text("json_extract(json_content, '$.sources') LIKE '%example.com%'"),
                text("json_extract(json_content, '$.sources') LIKE '%TBD%'"),
                text("json_extract(json_content, '$.sources') LIKE '%TODO%'"),
                text("json_extract(json_content, '$.sources') LIKE '%FIXME%'"),
                text("json_extract(json_content, '$.sources') LIKE '%placeholder%'")
            )
        ).order_by(desc(TimelineEvent.importance))
        
        selected_events = source_quality_issues.limit(target_count).all()
        
        if not selected_events:
            raise ValueError("No events found with placeholder or problematic sources")
        
        # Create validation run
        run = ValidationRun(
            run_name=f"Source Quality Focus - {datetime.now().strftime('%Y%m%d_%H%M')}",
            run_type='source_quality',
            target_count=target_count,
            actual_count=len(selected_events),
            selection_criteria={
                'min_importance': min_importance,
                'focus_area': 'source_quality_issues',
                'filters': ['example.com', 'TBD', 'TODO', 'FIXME', 'placeholder'],
                'selection_date': datetime.now().isoformat(),
                'total_eligible': source_quality_issues.count()
            },
            created_by='system',
            events_remaining=len(selected_events)
        )
        
        self.session.add(run)
        self.session.flush()
        
        # Add events to validation run
        for i, event in enumerate(selected_events):
            run_event = ValidationRunEvent(
                validation_run_id=run.id,
                event_id=event.id,
                selection_reason="Source quality issues detected",
                selection_priority=i,
                high_priority=event.importance >= 8,  # High importance events are high priority
                needs_attention=True,  # All source quality issues need attention
                assigned_date=datetime.now()
            )
            self.session.add(run_event)
        
        self.session.commit()
        return run
    
    def get_next_validation_event(self, validation_run_id: int, validator_id: Optional[str] = None) -> Optional[ValidationRunEvent]:
        """
        Get the next event to validate from a validation run
        
        Args:
            validation_run_id: ID of the validation run
            validator_id: Optional validator to assign the event to
        """
        
        # Find next pending event in the run, ordered by priority
        run_event = self.session.query(ValidationRunEvent).filter(
            and_(
                ValidationRunEvent.validation_run_id == validation_run_id,
                ValidationRunEvent.validation_status == 'pending'
            )
        ).order_by(
            desc(ValidationRunEvent.high_priority),
            desc(ValidationRunEvent.needs_attention), 
            asc(ValidationRunEvent.selection_priority)
        ).first()
        
        if run_event and validator_id:
            # Assign to validator
            run_event.validation_status = 'assigned'
            run_event.assigned_validator = validator_id
            run_event.assigned_date = datetime.now()
            self.session.commit()
        
        return run_event
    
    def complete_validation_run_event(self, 
                                    run_event_id: int,
                                    status: str,
                                    notes: str = "") -> ValidationRunEvent:
        """
        Mark a validation run event as completed with flexible status handling
        
        Args:
            run_event_id: ID of the ValidationRunEvent
            status: Completion status ('validated', 'needs_work', 'skipped', 'rejected')
            notes: Validation notes
        """
        
        # Valid completion statuses
        valid_statuses = ['validated', 'needs_work', 'skipped', 'rejected', 'completed']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {valid_statuses}")
        
        run_event = self.session.query(ValidationRunEvent).get(run_event_id)
        if not run_event:
            raise ValueError(f"ValidationRunEvent {run_event_id} not found")
        
        # Set status - map 'validated' to 'completed' for backward compatibility
        if status == 'validated':
            run_event.validation_status = 'completed'
        elif status == 'needs_work':
            run_event.validation_status = 'needs_work'
        elif status == 'rejected':
            run_event.validation_status = 'rejected'
            # Archive the rejected event
            try:
                archived = self.archive_rejected_event(run_event.event_id, notes)
                if archived:
                    run_event.validation_notes = f"{notes}\n[ARCHIVED: Event moved to archive/rejected_events]"
                else:
                    run_event.validation_notes = f"{notes}\n[ARCHIVE FAILED: Event file not found]"
            except Exception as e:
                run_event.validation_notes = f"{notes}\n[ARCHIVE ERROR: {str(e)}]"
        else:
            run_event.validation_status = status
            
        run_event.completed_date = datetime.now()
        if not hasattr(run_event, 'validation_notes') or run_event.validation_notes is None:
            run_event.validation_notes = notes
        
        # Update run progress
        validation_run = self.session.query(ValidationRun).get(run_event.validation_run_id)
        if validation_run:
            # Only count as validated if status is 'validated' or 'completed'
            if status in ['validated', 'completed']:
                validation_run.events_validated += 1
            
            validation_run.events_remaining = max(0, validation_run.events_remaining - 1)
            validation_run.progress_percentage = (validation_run.events_validated / validation_run.actual_count) * 100
            
            # Check if run is complete
            if validation_run.events_remaining == 0:
                validation_run.status = 'completed'
                validation_run.completed_date = datetime.now()
        
        self.session.commit()
        return run_event
    
    def requeue_needs_work_events(self, validation_run_id: int) -> int:
        """
        Requeue events marked as 'needs_work' back to 'pending' status
        
        Args:
            validation_run_id: ID of the validation run
            
        Returns:
            Number of events requeued
        """
        
        # Find events that need work
        needs_work_events = self.session.query(ValidationRunEvent).filter(
            and_(
                ValidationRunEvent.validation_run_id == validation_run_id,
                ValidationRunEvent.validation_status == 'needs_work'
            )
        ).all()
        
        # Reset them to pending status
        requeued_count = 0
        for event in needs_work_events:
            event.validation_status = 'pending'
            event.assigned_validator = None
            event.assigned_date = None
            event.completed_date = None
            # Keep validation_notes as history
            if event.validation_notes:
                event.validation_notes += f"\n[REQUEUED {datetime.now().isoformat()}]"
            requeued_count += 1
        
        # Update validation run counters
        if requeued_count > 0:
            validation_run = self.session.query(ValidationRun).get(validation_run_id)
            if validation_run:
                validation_run.events_remaining += requeued_count
                validation_run.progress_percentage = (validation_run.events_validated / validation_run.actual_count) * 100
                
                # If run was marked complete but now has pending events, reactivate it
                if validation_run.status == 'completed' and validation_run.events_remaining > 0:
                    validation_run.status = 'active'
        
        self.session.commit()
        return requeued_count
    
    def archive_rejected_event(self, event_id: str, rejection_reason: str = "") -> bool:
        """
        Archive a rejected event by moving it from timeline/data/events to archive/rejected_events
        
        Args:
            event_id: The event ID to archive
            rejection_reason: Reason for rejection (logged in archive)
            
        Returns:
            True if successfully archived, False if event not found
        """
        
        # Construct file paths
        source_path = f"../timeline/data/events/{event_id}.json"
        archive_dir = "../archive/rejected_events"
        archive_path = f"{archive_dir}/{event_id}.json"
        log_path = f"{archive_dir}/rejection_log.txt"
        
        # Check if source file exists
        if not os.path.exists(source_path):
            return False
        
        try:
            # Ensure archive directory exists
            os.makedirs(archive_dir, exist_ok=True)
            
            # Move the event file to archive
            shutil.move(source_path, archive_path)
            
            # Log the rejection
            timestamp = datetime.now().isoformat()
            log_entry = f"{timestamp} - REJECTED: {event_id} - Reason: {rejection_reason}\n"
            
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(log_entry)
            
            return True
            
        except Exception as e:
            # If something went wrong, try to restore the file
            if os.path.exists(archive_path) and not os.path.exists(source_path):
                shutil.move(archive_path, source_path)
            raise e
    
    def get_validation_run_stats(self, validation_run_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a validation run"""
        
        validation_run = self.session.query(ValidationRun).get(validation_run_id)
        if not validation_run:
            raise ValueError(f"ValidationRun {validation_run_id} not found")
        
        # Get event status counts
        status_counts = {}
        events = self.session.query(ValidationRunEvent).filter(
            ValidationRunEvent.validation_run_id == validation_run_id
        ).all()
        
        for event in events:
            status = event.validation_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Get validation logs for this run
        validation_logs = self.session.query(ValidationLog).filter(
            ValidationLog.validation_run_id == validation_run_id
        ).all()
        
        # Calculate validation statistics
        validation_stats = {}
        for log in validation_logs:
            status = log.status
            validation_stats[status] = validation_stats.get(status, 0) + 1
        
        return {
            'run_info': {
                'id': validation_run.id,
                'name': validation_run.run_name,
                'type': validation_run.run_type,
                'status': validation_run.status,
                'created_date': validation_run.created_date.isoformat() if validation_run.created_date else None,
                'progress_percentage': validation_run.progress_percentage
            },
            'event_counts': {
                'target_count': validation_run.target_count,
                'actual_count': validation_run.actual_count,
                'events_validated': validation_run.events_validated,
                'events_remaining': validation_run.events_remaining
            },
            'event_status_breakdown': status_counts,
            'validation_results': validation_stats,
            'selection_criteria': validation_run.selection_criteria
        }