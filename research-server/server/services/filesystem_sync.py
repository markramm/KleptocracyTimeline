#!/usr/bin/env python3
"""
Filesystem Syncer Service - Single-threaded filesystem to database syncer

Handles:
- Syncing timeline events from filesystem to database (one-way, filesystem authoritative)
- Seeding research priorities from filesystem (database authoritative after initial seed)
- Releasing expired priority reservations
- Releasing expired QA reservations
"""

import hashlib
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session
from models import TimelineEvent, ResearchPriority, ActivityLog
from parsers.factory import EventParserFactory
from qa_queue_system import QAQueueManager

logger = logging.getLogger(__name__)


class FilesystemSyncer:
    """Single-threaded filesystem to database syncer"""

    def __init__(self, app, session_factory, sync_lock):
        """
        Initialize the filesystem syncer

        Args:
            app: Flask app instance (for config access)
            session_factory: SQLAlchemy session factory
            sync_lock: Threading lock for sync operations
        """
        self.app = app
        self.Session = session_factory
        self.sync_lock = sync_lock
        self.running = False
        self.thread = None

    def start(self):
        """Start the sync thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.thread.start()
            logger.info("Filesystem sync thread started")

    def stop(self):
        """Stop the sync thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            logger.info("Filesystem sync thread stopped")

    def _sync_loop(self):
        """Main sync loop - runs every 30 seconds"""
        while self.running:
            try:
                with self.sync_lock:
                    self.sync_events()
                    self.seed_priorities()
                    self.release_expired_reservations()

                    # Release expired QA reservations
                    try:
                        db = self.Session()
                        qa_manager = QAQueueManager(db)
                        released_count = qa_manager.release_expired_qa_reservations()
                        if released_count > 0:
                            logger.info(f"Released {released_count} expired QA reservations")
                        db.close()
                    except Exception as e:
                        logger.error(f"Error releasing expired QA reservations: {e}")
                        if db:
                            db.close()
            except Exception as e:
                logger.error(f"Sync error: {e}")

            time.sleep(30)

    def release_expired_reservations(self):
        """Release priority reservations that have expired (1 hour timeout)"""
        db = self.Session()
        try:
            cutoff = datetime.now() - timedelta(hours=1)

            expired = db.query(ResearchPriority)\
                .filter_by(status='reserved')\
                .filter(ResearchPriority.reserved_at < cutoff)\
                .all()

            if expired:
                for priority in expired:
                    priority.status = 'pending'
                    priority.assigned_agent = None
                    priority.reserved_at = None

                    # Log timeout
                    activity = ActivityLog(
                        action='priority_timeout',
                        priority_id=priority.id,
                        agent=priority.assigned_agent,
                        details={'reason': 'reservation_expired'}
                    )
                    db.add(activity)

                db.commit()
                logger.info(f"Released {len(expired)} expired priority reservations")

        except Exception as e:
            logger.error(f"Error releasing expired reservations: {e}")
            db.rollback()
        finally:
            db.close()

    def sync_events(self):
        """Sync timeline events from filesystem to database (one-way)"""
        db = self.Session()
        try:
            synced = 0
            events_path = self.app.config.get('EVENTS_PATH')
            parser_factory = EventParserFactory()

            # Sync both .json and .md files (but skip README and other non-event markdown files)
            md_files = [f for f in events_path.glob('*.md') if f.name.upper() != 'README.MD']
            for event_file in list(events_path.glob('*.json')) + md_files:
                try:
                    # Calculate file hash
                    with open(event_file, 'rb') as f:
                        file_content = f.read()
                        file_hash = hashlib.md5(file_content).hexdigest()

                    # Extract event ID from filename (without extension)
                    event_id = event_file.stem
                    existing = db.query(TimelineEvent).filter_by(id=event_id).first()

                    if not existing or existing.file_hash != file_hash:
                        # Parse event using appropriate parser
                        try:
                            data = parser_factory.parse_event(event_file)
                        except ValueError as parse_error:
                            logger.error(f"Parse error for {event_file}: {parse_error}")
                            continue

                        # Create or update event (filesystem is authoritative)
                        if not existing:
                            event = TimelineEvent(id=event_id)
                        else:
                            event = existing

                        event.json_content = data
                        event.date = data.get('date', '')
                        event.title = data.get('title', '')
                        event.summary = data.get('summary', '')
                        event.importance = data.get('importance', 5)
                        event.status = data.get('status', 'confirmed')
                        event.file_path = str(event_file)
                        event.file_hash = file_hash
                        event.last_synced = datetime.now()

                        if not existing:
                            db.add(event)

                        synced += 1

                        # Log which format was parsed
                        format_type = event_file.suffix[1:]  # Remove leading dot
                        logger.debug(f"Synced {event_id} from {format_type} format")

                except Exception as e:
                    logger.error(f"Error syncing {event_file}: {e}")

            db.commit()
            if synced > 0:
                logger.info(f"Synced {synced} events from filesystem")

                # Log activity for monitoring
                activity = ActivityLog(
                    action='filesystem_sync',
                    agent='system',
                    details={'new_events': synced}
                )
                db.add(activity)
                db.commit()

        except Exception as e:
            logger.error(f"Events sync error: {e}")
            db.rollback()
        finally:
            db.close()

    def seed_priorities(self):
        """Seed initial priorities from filesystem (only if not exists)"""
        db = self.Session()
        try:
            seeded = 0
            priorities_path = self.app.config.get('PRIORITIES_PATH')
            for json_file in priorities_path.glob('*.json'):
                try:
                    priority_id = json_file.stem

                    # Only seed if doesn't exist (database is authoritative)
                    existing = db.query(ResearchPriority).filter_by(id=priority_id).first()
                    if not existing:
                        with open(json_file, 'r') as f:
                            data = json.load(f)

                        priority = ResearchPriority(
                            id=priority_id,
                            title=data.get('title', ''),
                            description=data.get('description', ''),
                            priority=data.get('priority', 5),
                            status=data.get('status', 'pending'),
                            estimated_events=data.get('estimated_events', 1),
                            actual_events=data.get('actual_events', 0),
                            category=data.get('category', ''),
                            tags=data.get('tags', []),
                            source_file=str(json_file),
                            is_generated=False
                        )
                        db.add(priority)
                        seeded += 1

                except Exception as e:
                    logger.error(f"Error seeding priority {json_file}: {e}")

            if seeded > 0:
                db.commit()
                logger.info(f"Seeded {seeded} new priorities from filesystem")

        except Exception as e:
            logger.error(f"Priority seed error: {e}")
            db.rollback()
        finally:
            db.close()
