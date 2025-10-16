#!/usr/bin/env python3
"""
QA Queue System for Timeline Events
====================================

Simplified QA system that processes all events by importance.
Since we plan to process all events, complex scoring is unnecessary.
Events are prioritized simply by:
1. Event importance (high importance events first)
2. Date (newer events first as tiebreaker)

Validation statuses:
- pending: Not yet processed
- in_progress: Currently being processed 
- validated: Processing complete
- rejected: Event rejected
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
from models import EventMetadata, ActivityLog, ValidationLog

logger = logging.getLogger(__name__)

class QAQueueManager:
    """Manages the quality assurance queue for timeline events"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
        
    def get_simple_priority(self, event_data: Dict) -> int:
        """
        Get simple priority based only on importance score
        Since we'll process all events, complex scoring is unnecessary
        
        Returns:
            int: Event importance (1-10)
        """
        return event_data.get('importance', 1) or 1
    
    def reserve_qa_batch(self, batch_size: int = 5, agent_id: str = None, 
                        min_importance: int = 1) -> List[Dict]:
        """
        Reserve a batch of events for QA processing to prevent duplicate work
        
        Args:
            batch_size: Number of events to reserve
            agent_id: Agent identifier for the reservation
            min_importance: Minimum importance score to include
            
        Returns:
            List of reserved events with QA priority scores
        """
        
        if not agent_id:
            agent_id = f"qa-agent-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Get events that are not reserved or being processed
        query = text("""
            SELECT 
                e.id,
                e.date,
                e.title,
                e.summary,
                e.importance,
                e.json_content,
                m.validation_status,
                m.quality_score,
                m.validation_date,
                m.reserved_at,
                m.reserved_by
            FROM timeline_events e
            LEFT JOIN event_metadata m ON e.id = m.event_id
            WHERE e.importance >= :min_importance
            AND (m.validation_status IS NULL OR m.validation_status = 'pending')
            AND (m.reserved_at IS NULL OR m.reserved_at < :expiry_cutoff)
            ORDER BY e.importance DESC, e.date DESC
            LIMIT :batch_size
        """)
        
        # Set expiry cutoff to 1 hour ago
        expiry_cutoff = datetime.utcnow() - timedelta(hours=1)
        
        params = {
            'min_importance': min_importance,
            'batch_size': batch_size * 2,  # Get more events to filter and prioritize
            'expiry_cutoff': expiry_cutoff
        }
        
        result = self.session.execute(query, params)
        events = result.fetchall()
        
        qa_queue = []
        reserved_events = []
        
        for event_row in events:
            # Parse the JSON content
            try:
                event_data = json.loads(event_row.json_content) if event_row.json_content else {}
            except (json.JSONDecodeError, TypeError):
                event_data = {
                    'id': event_row.id,
                    'date': event_row.date,
                    'title': event_row.title,
                    'summary': event_row.summary,
                    'importance': event_row.importance,
                    'sources': [],
                    'actors': [],
                    'tags': []
                }
            
            # Metadata
            metadata = {
                'validation_status': event_row.validation_status,
                'quality_score': event_row.quality_score,
                'validation_date': event_row.validation_date
            } if event_row.validation_status else None
            
            # Skip validated, rejected, or in_progress events
            if metadata and metadata['validation_status'] in ['validated', 'rejected', 'in_progress']:
                continue
            
            try:
                # Get simple priority (just importance)
                importance = self.get_simple_priority(event_data)
                
                # Add to queue
                qa_item = {
                    'id': event_row.id,
                    'date': event_row.date,
                    'title': event_row.title,
                    'summary': event_row.summary or '',
                    'importance': importance,
                    'sources': event_data.get('sources', []),
                    'actors': event_data.get('actors', []),
                    'tags': event_data.get('tags', []),
                    'capture_lanes': event_data.get('capture_lanes', []),
                    'source_count': len(event_data.get('sources', [])),
                    'validation_status': metadata.get('validation_status', 'pending') if metadata else 'pending',
                    'needs_attention': self._identify_qa_issues(event_data, metadata)
                }
                
                qa_queue.append(qa_item)
                
            except Exception as e:
                logger.error(f"Error processing event {event_row.id} for QA queue: {e}", exc_info=True)
                continue
        
        # Sort by importance (highest first) then date (newest first)
        qa_queue.sort(key=lambda x: (x.get('importance', 1), x.get('date', '')), reverse=True)
        selected_events = qa_queue[:batch_size]
        
        # Reserve the selected events
        reservation_time = datetime.utcnow()
        for event in selected_events:
            try:
                # Check if metadata record exists
                existing_query = text("SELECT event_id FROM event_metadata WHERE event_id = :event_id")
                existing = self.session.execute(existing_query, {'event_id': event['id']}).fetchone()
                
                if existing:
                    # Update existing record with reservation
                    update_query = text("""
                        UPDATE event_metadata 
                        SET reserved_at = :reserved_at,
                            reserved_by = :reserved_by
                        WHERE event_id = :event_id
                    """)
                    
                    self.session.execute(update_query, {
                        'event_id': event['id'],
                        'reserved_at': reservation_time,
                        'reserved_by': agent_id
                    })
                else:
                    # Create new metadata record with reservation
                    insert_query = text("""
                        INSERT INTO event_metadata (
                            event_id, validation_status, reserved_at, reserved_by, created_at
                        ) VALUES (
                            :event_id, 'pending', :reserved_at, :reserved_by, :created_at
                        )
                    """)
                    
                    self.session.execute(insert_query, {
                        'event_id': event['id'],
                        'reserved_at': reservation_time,
                        'reserved_by': agent_id,
                        'created_at': reservation_time
                    })
                
                # Add reservation info to event
                event['reserved_at'] = reservation_time.isoformat()
                event['reserved_by'] = agent_id
                event['reserved_until'] = (reservation_time + timedelta(hours=1)).isoformat()
                
                reserved_events.append(event)
                
            except Exception as e:
                logger.error(f"Error reserving event {event['id']}: {e}", exc_info=True)
                continue
        
        self.session.commit()
        logger.info(f"Reserved {len(reserved_events)} events for QA processing by {agent_id}")
        
        return reserved_events
    
    def release_expired_qa_reservations(self):
        """Release QA event reservations that have expired (1 hour timeout)"""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=1)
            logger.debug(f"Releasing QA reservations older than {cutoff}")
            
            # Find expired reservations
            expired_query = text("""
                SELECT event_id, reserved_by, reserved_at, validation_status FROM event_metadata
                WHERE reserved_at IS NOT NULL 
                AND reserved_at < :cutoff
                AND (validation_status IS NULL OR validation_status NOT IN ('validated', 'rejected'))
            """)
            
            try:
                expired_reservations = self.session.execute(expired_query, {'cutoff': cutoff}).fetchall()
                logger.debug(f"Found {len(expired_reservations)} expired reservations")
            except Exception as e:
                logger.error(f"Error finding expired reservations: {e}", exc_info=True)
                return 0
            
            if expired_reservations:
                # Log what we're about to release
                for reservation in expired_reservations:
                    logger.debug(f"Releasing: event_id={reservation.event_id}, reserved_by={reservation.reserved_by}, reserved_at={reservation.reserved_at}, validation_status={reservation.validation_status}")
                
                # Release expired reservations
                release_query = text("""
                    UPDATE event_metadata 
                    SET reserved_at = NULL, reserved_by = NULL
                    WHERE reserved_at IS NOT NULL 
                    AND reserved_at < :cutoff
                    AND (validation_status IS NULL OR validation_status NOT IN ('validated', 'rejected'))
                """)
                
                try:
                    result = self.session.execute(release_query, {'cutoff': cutoff})
                    self.session.commit()
                    
                    logger.info(f"Released {result.rowcount} expired QA reservations")
                    return result.rowcount
                except Exception as e:
                    logger.error(f"Error executing release query: {e}", exc_info=True)
                    self.session.rollback()
                    return 0
            else:
                logger.debug("No expired reservations to release")
                return 0
            
        except Exception as e:
            logger.error(f"Error releasing expired QA reservations: {e}", exc_info=True)
            self.session.rollback()
            return 0
    
    def get_qa_queue(self, limit: int = 50, offset: int = 0, 
                     min_importance: int = 1, include_validated: bool = False) -> List[Dict]:
        """
        Get prioritized queue of events needing QA
        
        Args:
            limit: Maximum number of events to return
            offset: Offset for pagination
            min_importance: Minimum importance score to include
            include_validated: Whether to include already validated events
            
        Returns:
            List of events with QA priority scores
        """
        
        # Build the query
        query = text("""
            SELECT 
                e.id,
                e.date,
                e.title,
                e.summary,
                e.importance,
                e.json_content,
                m.validation_status,
                m.quality_score,
                m.validation_date,
                m.created_at as metadata_created_at
            FROM timeline_events e
            LEFT JOIN event_metadata m ON e.id = m.event_id
            WHERE e.importance >= :min_importance
            ORDER BY e.importance DESC, e.date DESC
            LIMIT :limit OFFSET :offset
        """)
        
        params = {
            'min_importance': min_importance,
            'limit': limit,
            'offset': offset
        }
        
        result = self.session.execute(query, params)
        events = result.fetchall()
        
        qa_queue = []
        
        for event_row in events:
            # Parse the JSON content
            try:
                event_data = json.loads(event_row.json_content) if event_row.json_content else {}
            except (json.JSONDecodeError, TypeError):
                event_data = {
                    'id': event_row.id,
                    'date': event_row.date,
                    'title': event_row.title,
                    'summary': event_row.summary,
                    'importance': event_row.importance,
                    'sources': [],
                    'actors': [],
                    'tags': []
                }
            
            # Metadata
            metadata = {
                'validation_status': event_row.validation_status,
                'quality_score': event_row.quality_score,
                'validation_date': event_row.validation_date,
                'metadata_created_at': event_row.metadata_created_at
            } if event_row.validation_status else None
            
            # Skip validated events if requested
            if not include_validated and metadata and metadata['validation_status'] == 'validated':
                continue
                
            # Always skip rejected and in_progress events from the main QA queue
            if metadata and metadata['validation_status'] in ['rejected', 'in_progress']:
                continue
            
            try:
                # Get simple priority (just importance)
                importance = self.get_simple_priority(event_data)
                
                # Add to queue
                qa_item = {
                    'id': event_row.id,
                    'date': event_row.date,
                    'title': event_row.title,
                    'summary': event_row.summary or '',
                    'importance': importance,
                    'sources': event_data.get('sources', []),
                    'actors': event_data.get('actors', []),
                    'tags': event_data.get('tags', []),
                    'capture_lanes': event_data.get('capture_lanes', []),
                    'validation_status': metadata['validation_status'] if metadata else 'pending',
                    'quality_score': metadata['quality_score'] if metadata else None,
                    'needs_attention': self._identify_qa_issues(event_data, metadata)
                }
                
                qa_queue.append(qa_item)
                
            except Exception as e:
                logger.error(f"Error processing event {event_row.id} for QA queue: {e}", exc_info=True)
                continue
        
        # Sort by importance (highest first) then date (newest first)
        qa_queue.sort(key=lambda x: (x.get('importance', 1), x.get('date', '')), reverse=True)
        
        return qa_queue
    
    def _identify_qa_issues(self, event_data: Dict, metadata: Optional[Dict]) -> List[str]:
        """Identify specific QA issues for an event"""
        issues = []
        
        # Check sources
        sources = event_data.get('sources', [])
        source_count = len(sources) if isinstance(sources, list) else 1 if sources else 0
        
        if source_count == 0:
            issues.append('No sources')
        elif source_count < 2:
            issues.append('Insufficient sources (<2)')
        elif source_count < 3:
            issues.append('Below recommended sources (<3)')
        
        # Check for placeholder sources
        for source in sources:
            if isinstance(source, dict):
                if ('example.com' in source.get('url', '') or 
                    'TBD' in source.get('outlet', '') or
                    'needs' in source.get('title', '').lower()):
                    issues.append('Placeholder sources')
                    break
        
        # Check metadata completeness
        if not event_data.get('actors'):
            issues.append('Missing actors')
        elif any('needs identification' in str(actor).lower() for actor in event_data.get('actors', [])):
            issues.append('Placeholder actors')
            
        if not event_data.get('tags'):
            issues.append('Missing tags')
        elif any('needs' in str(tag).lower() for tag in event_data.get('tags', [])):
            issues.append('Placeholder tags')
            
        if not event_data.get('capture_lanes'):
            issues.append('Missing capture lanes')
        
        # Check summary quality
        summary = event_data.get('summary', '')
        if not summary:
            issues.append('Missing summary')
        elif len(summary) < 50:
            issues.append('Very brief summary')
        elif 'needs completion' in summary.lower():
            issues.append('Incomplete summary')
        
        # Check validation status
        if not metadata:
            issues.append('No validation record')
        elif metadata.get('validation_status') == 'pending':
            issues.append('Pending validation')
        elif metadata.get('validation_status') == 'rejected':
            issues.append('Previously rejected')
        
        return issues
    
    def get_qa_stats(self) -> Dict[str, Any]:
        """Get statistics about the QA queue using validation logs as source of truth"""
        
        # Total events
        total_query = text("SELECT COUNT(*) as count FROM timeline_events")
        total_events = self.session.execute(total_query).fetchone().count
        
        # Validation status breakdown based on validation logs (source of truth)
        validation_logs_query = text("""
            SELECT 
                CASE 
                    WHEN vl.latest_status IS NULL THEN 'no_record'
                    WHEN vl.latest_status = 'validated' THEN 'validated'
                    WHEN vl.latest_status = 'rejected' THEN 'rejected'
                    WHEN vl.latest_status = 'needs_work' THEN 'needs_work'
                    WHEN vl.latest_status = 'flagged' THEN 'flagged'
                    ELSE 'pending'
                END as validation_status,
                COUNT(DISTINCT e.id) as count
            FROM timeline_events e
            LEFT JOIN (
                SELECT DISTINCT event_id, 
                       FIRST_VALUE(status) OVER (
                           PARTITION BY event_id 
                           ORDER BY validation_date DESC
                       ) as latest_status
                FROM validation_logs
            ) vl ON e.id = vl.event_id
            GROUP BY validation_status
        """)
        
        validation_stats = {}
        for row in self.session.execute(validation_logs_query):
            validation_stats[row.validation_status] = row.count
        
        # Source quality stats
        source_query = text("""
            SELECT 
                CASE 
                    WHEN json_extract(json_content, '$.sources') IS NULL THEN 'no_sources'
                    WHEN json_array_length(json_extract(json_content, '$.sources')) = 0 THEN 'no_sources'
                    WHEN json_array_length(json_extract(json_content, '$.sources')) = 1 THEN 'one_source'
                    WHEN json_array_length(json_extract(json_content, '$.sources')) = 2 THEN 'two_sources'
                    WHEN json_array_length(json_extract(json_content, '$.sources')) >= 3 THEN 'adequate_sources'
                    ELSE 'unknown'
                END as source_category,
                COUNT(*) as count
            FROM timeline_events
            WHERE json_content IS NOT NULL
            GROUP BY source_category
        """)
        
        source_stats = {}
        for row in self.session.execute(source_query):
            source_stats[row.source_category] = row.count
        
        # High priority events needing QA (using validation logs)
        high_priority_query = text("""
            SELECT COUNT(*) as count
            FROM timeline_events e
            LEFT JOIN (
                SELECT DISTINCT event_id, 
                       FIRST_VALUE(status) OVER (
                           PARTITION BY event_id 
                           ORDER BY validation_date DESC
                       ) as latest_status
                FROM validation_logs
            ) vl ON e.id = vl.event_id
            WHERE e.importance >= 7 
            AND (vl.latest_status IS NULL OR vl.latest_status IN ('pending', 'needs_work', 'flagged'))
        """)
        
        high_priority_count = self.session.execute(high_priority_query).fetchone().count
        
        # Total validation logs count for reference
        logs_count_query = text("SELECT COUNT(*) as count FROM validation_logs")
        total_validation_logs = self.session.execute(logs_count_query).fetchone().count
        
        return {
            'total_events': total_events,
            'validation_status': validation_stats,
            'source_quality': source_stats,
            'high_priority_needs_qa': high_priority_count,
            'estimated_qa_backlog': validation_stats.get('no_record', 0) + validation_stats.get('needs_work', 0) + validation_stats.get('flagged', 0),
            'total_validation_logs': total_validation_logs,
            'data_source': 'validation_logs'
        }
    
    def mark_event_validated(self, event_id: str, quality_score: float, 
                           validation_notes: str = "", created_by: str = "qa-agent") -> bool:
        """Mark an event as validated with quality score"""
        
        try:
            # Check if metadata record exists
            existing_query = text("SELECT event_id FROM event_metadata WHERE event_id = :event_id")
            existing = self.session.execute(existing_query, {'event_id': event_id}).fetchone()
            
            if existing:
                # Update existing record
                update_query = text("""
                    UPDATE event_metadata 
                    SET validation_status = 'validated',
                        validation_date = :validation_date,
                        validation_notes = :validation_notes,
                        quality_score = :quality_score
                    WHERE event_id = :event_id
                """)
                
                self.session.execute(update_query, {
                    'event_id': event_id,
                    'validation_date': datetime.utcnow(),
                    'validation_notes': validation_notes,
                    'quality_score': quality_score
                })
            else:
                # Create new metadata record
                insert_query = text("""
                    INSERT INTO event_metadata (
                        event_id, validation_status, validation_date, 
                        validation_notes, quality_score, created_by, created_at
                    ) VALUES (
                        :event_id, 'validated', :validation_date,
                        :validation_notes, :quality_score, :created_by, :created_at
                    )
                """)
                
                self.session.execute(insert_query, {
                    'event_id': event_id,
                    'validation_date': datetime.utcnow(),
                    'validation_notes': validation_notes,
                    'quality_score': quality_score,
                    'created_by': created_by,
                    'created_at': datetime.utcnow()
                })
            
            # Create ValidationLog entry for audit trail
            validation_log = ValidationLog(
                event_id=event_id,
                validator_type='agent',
                validator_id=created_by,
                validation_date=datetime.utcnow(),
                status='validated',
                confidence=quality_score / 10.0,  # Convert 0-10 score to 0-1.0 confidence
                notes=validation_notes,
                sources_verified=None,  # Could be enhanced later
                issues_found=None,
                corrections_made=None,
                validation_criteria=None,
                time_spent_minutes=None
            )
            
            self.session.add(validation_log)
            self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error marking event {event_id} as validated: {e}", exc_info=True)
            self.session.rollback()
            return False
    
    def mark_event_in_progress(self, event_id: str, created_by: str = "qa-agent", 
                              agent_id: str = None) -> bool:
        """
        Mark an event as in_progress to prevent duplicate processing
        
        Args:
            event_id: Event ID to mark as in_progress
            created_by: Who is starting the processing
            agent_id: Agent identifier for tracking
            
        Returns:
            bool: Success status (False if already in_progress)
        """
        try:
            # Check if metadata record exists and current status
            existing = self.session.query(EventMetadata).filter_by(event_id=event_id).first()
            
            if existing:
                # Don't allow marking as in_progress if already validated, rejected, or in_progress
                if existing.validation_status in ['validated', 'rejected', 'in_progress']:
                    return False
                    
                # Update existing record
                existing.validation_status = 'in_progress'
                existing.validation_date = datetime.utcnow()
                existing.validation_notes = f"Started by {agent_id or created_by}"
                existing.created_by = created_by
            else:
                # Create new metadata record
                new_metadata = EventMetadata(
                    event_id=event_id,
                    validation_status='in_progress',
                    validation_date=datetime.utcnow(),
                    validation_notes=f"Started by {agent_id or created_by}",
                    created_by=created_by,
                    created_at=datetime.utcnow()
                )
                self.session.add(new_metadata)
            
            self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error marking event {event_id} as in_progress: {e}", exc_info=True)
            self.session.rollback()
            return False
    
    def mark_event_rejected(self, event_id: str, rejection_reason: str, 
                           created_by: str = "qa-agent") -> bool:
        """
        Mark an event as rejected with detailed reasoning
        
        Args:
            event_id: Event ID to reject
            rejection_reason: Detailed reason for rejection
            created_by: Who performed the rejection
            
        Returns:
            bool: Success status
        """
        try:
            # Check if metadata record exists
            existing = self.session.query(EventMetadata).filter_by(event_id=event_id).first()
            
            if existing:
                # Update existing record
                existing.validation_status = 'rejected'
                existing.validation_date = datetime.utcnow()
                existing.validation_notes = rejection_reason
                existing.quality_score = 0.0  # Rejected events get 0 quality score
                existing.created_by = created_by
            else:
                # Create new metadata record
                insert_query = text("""
                    INSERT INTO event_metadata (
                        event_id, validation_status, validation_date, 
                        validation_notes, quality_score, created_by, created_at
                    ) VALUES (
                        :event_id, 'rejected', :validation_date,
                        :validation_notes, :quality_score, :created_by, :created_at
                    )
                """)
                
                self.session.execute(insert_query, {
                    'event_id': event_id,
                    'validation_date': datetime.utcnow(),
                    'validation_notes': rejection_reason,
                    'quality_score': 0.0,
                    'created_by': created_by,
                    'created_at': datetime.utcnow()
                })
            
            self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error marking event {event_id} as rejected: {e}", exc_info=True)
            self.session.rollback()
            return False
    
    def get_next_qa_event(self, min_importance: int = 1) -> Optional[Dict]:
        """Get the next highest priority event for QA"""
        
        queue = self.get_qa_queue(limit=1, min_importance=min_importance)
        return queue[0] if queue else None
    
    def get_qa_candidates_by_issue(self, issue_type: str, limit: int = 20) -> List[Dict]:
        """Get events with specific QA issues"""
        
        # Get a larger sample to filter
        queue = self.get_qa_queue(limit=limit * 3)
        
        # Filter by issue type
        candidates = []
        for event in queue:
            if issue_type in event.get('needs_attention', []):
                candidates.append(event)
                if len(candidates) >= limit:
                    break
        
        return candidates
    
    def get_rejected_events(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Get rejected events for audit purposes
        
        Args:
            limit: Maximum number of events to return
            offset: Offset for pagination
            
        Returns:
            List of rejected events with rejection details
        """
        
        query = text("""
            SELECT 
                e.id,
                e.date,
                e.title,
                e.summary,
                e.importance,
                e.json_content,
                m.validation_status,
                m.validation_date,
                m.validation_notes,
                m.created_by
            FROM timeline_events e
            JOIN event_metadata m ON e.id = m.event_id
            WHERE m.validation_status = 'rejected'
            ORDER BY m.validation_date DESC, e.importance DESC
            LIMIT :limit OFFSET :offset
        """)
        
        params = {
            'limit': limit,
            'offset': offset
        }
        
        result = self.session.execute(query, params)
        events = result.fetchall()
        
        rejected_events = []
        
        for event_row in events:
            # Parse the JSON content
            try:
                event_data = json.loads(event_row.json_content) if event_row.json_content else {}
            except (json.JSONDecodeError, TypeError):
                event_data = {}
            
            rejected_item = {
                'id': event_row.id,
                'date': event_row.date,
                'title': event_row.title,
                'summary': event_row.summary or '',
                'importance': event_row.importance,
                'validation_status': event_row.validation_status,
                'validation_date': event_row.validation_date,
                'rejection_reason': event_row.validation_notes,
                'rejected_by': event_row.created_by,
                'sources': event_data.get('sources', []),
                'actors': event_data.get('actors', []),
                'tags': event_data.get('tags', [])
            }
            
            rejected_events.append(rejected_item)
        
        return rejected_events
    
    def initialize_validation_audit_trail(self, created_by: str = "system-init", dry_run: bool = False) -> Dict:
        """Initialize metadata records for all events to create complete validation audit trail"""
        
        try:
            # Find all events without metadata records
            missing_metadata_query = text("""
                SELECT e.id, e.importance, e.date
                FROM timeline_events e
                LEFT JOIN event_metadata m ON e.id = m.event_id
                WHERE m.event_id IS NULL
                ORDER BY e.importance DESC, e.date DESC
            """)
            
            missing_events = self.session.execute(missing_metadata_query).fetchall()
            
            if dry_run:
                return {
                    'action': 'dry_run',
                    'events_to_initialize': len(missing_events),
                    'sample_events': [
                        {'id': row.id, 'importance': row.importance, 'date': row.date}
                        for row in missing_events[:10]
                    ]
                }
            
            # Initialize metadata records for missing events
            initialized_count = 0
            failed_count = 0
            
            for event_row in missing_events:
                try:
                    insert_query = text("""
                        INSERT INTO event_metadata (
                            event_id, validation_status, created_by, created_at
                        ) VALUES (
                            :event_id, 'pending', :created_by, :created_at
                        )
                    """)
                    
                    self.session.execute(insert_query, {
                        'event_id': event_row.id,
                        'created_by': created_by,
                        'created_at': datetime.now()
                    })
                    
                    initialized_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to initialize metadata for {event_row.id}: {e}", exc_info=True)
                    failed_count += 1
                    continue
            
            # Commit all changes
            self.session.commit()
            
            logger.info(f"Validation audit trail initialized: {initialized_count} events, {failed_count} failures")
            
            return {
                'action': 'initialize',
                'initialized_count': initialized_count,
                'failed_count': failed_count,
                'total_events_processed': len(missing_events),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error initializing validation audit trail: {e}", exc_info=True)
            self.session.rollback()
            return {
                'action': 'initialize',
                'error': str(e),
                'success': False
            }
    
    def reset_validation_audit_trail(self, created_by: str = "system-reset", dry_run: bool = False) -> Dict:
        """Reset all validation records to pending status for complete re-validation"""
        
        try:
            if dry_run:
                # Count existing records
                count_query = text("SELECT COUNT(*) as count FROM event_metadata")
                count_result = self.session.execute(count_query).fetchone()
                
                return {
                    'action': 'dry_run',
                    'existing_metadata_records': count_result.count,
                    'action_would_be': 'reset_all_to_pending'
                }
            
            # Reset all existing records to pending
            reset_query = text("""
                UPDATE event_metadata 
                SET validation_status = 'pending',
                    validation_date = NULL,
                    validation_notes = NULL,
                    quality_score = NULL,
                    created_by = :created_by,
                    created_at = :created_at
            """)
            
            result = self.session.execute(reset_query, {
                'created_by': created_by,
                'created_at': datetime.now()
            })
            
            # Initialize records for events without metadata
            init_result = self.initialize_validation_audit_trail(created_by, dry_run=False)
            
            self.session.commit()
            
            logger.info(f"Validation audit trail reset: {result.rowcount} existing records, {init_result.get('initialized_count', 0)} new records")
            
            return {
                'action': 'reset',
                'reset_existing_count': result.rowcount,
                'initialized_new_count': init_result.get('initialized_count', 0),
                'failed_count': init_result.get('failed_count', 0),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error resetting validation audit trail: {e}", exc_info=True)
            self.session.rollback()
            return {
                'action': 'reset',
                'error': str(e),
                'success': False
            }