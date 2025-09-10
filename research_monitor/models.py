#!/usr/bin/env python3
"""
SQLAlchemy models for Research Monitor
Clean separation between filesystem-synced and database-authoritative data
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, JSON, Boolean, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import json

Base = declarative_base()

class TimelineEvent(Base):
    """
    Read-only mirror of timeline_data/events/*.json files
    Filesystem is authoritative - this table is only for querying
    """
    __tablename__ = 'timeline_events'
    
    # Primary key matches filename
    id = Column(String, primary_key=True)
    
    # Exact JSON from file for full-text search
    json_content = Column(JSON, nullable=False)
    
    # Extracted fields for efficient querying (denormalized from JSON)
    date = Column(String, index=True)
    title = Column(Text)
    summary = Column(Text)
    importance = Column(Integer)
    status = Column(String)
    
    # Filesystem metadata
    file_path = Column(String, nullable=False)
    file_hash = Column(String, nullable=False)
    last_synced = Column(DateTime, default=func.now())
    
    # Relationships
    event_metadata = relationship("EventMetadata", back_populates="event", uselist=False)
    research_links = relationship("EventResearchLink", back_populates="event")
    
    # Enable full-text search on this table
    __table_args__ = (
        Index('idx_event_fulltext', 'title', 'summary', mysql_prefix='FULLTEXT'),
    )

class EventMetadata(Base):
    """
    Database-authoritative metadata about events
    This enriches events without modifying source files
    """
    __tablename__ = 'event_metadata'
    
    event_id = Column(String, ForeignKey('timeline_events.id'), primary_key=True)
    
    # Validation and quality
    validation_status = Column(String, default='pending')  # pending, validated, rejected
    validation_date = Column(DateTime)
    validation_notes = Column(Text)
    quality_score = Column(Float)
    
    # Creation tracking
    created_by = Column(String)  # Which agent/process created it
    created_at = Column(DateTime, default=func.now())
    research_priority_id = Column(String, ForeignKey('research_priorities.id'))
    
    # Enrichment
    ai_summary = Column(Text)  # AI-generated summary for better search
    tags_enriched = Column(JSON)  # Additional tags beyond source
    connections_discovered = Column(JSON)  # Links found through analysis
    
    # Relationships
    event = relationship("TimelineEvent", back_populates="event_metadata")
    research_priority = relationship("ResearchPriority", back_populates="created_events")

class ResearchPriority(Base):
    """
    Database-authoritative research priorities
    Initial data from research_priorities/*.json but database is source of truth
    """
    __tablename__ = 'research_priorities'
    
    id = Column(String, primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    
    # Priority and status (mutable)
    priority = Column(Integer, default=5)
    status = Column(String, default='pending')  # pending, reserved, in_progress, completed, blocked, failed
    
    # Progress tracking (mutable)
    estimated_events = Column(Integer, default=1)
    actual_events = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    
    # Dates (mutable)
    created_date = Column(DateTime, default=func.now())
    updated_date = Column(DateTime, default=func.now(), onupdate=func.now())
    started_date = Column(DateTime)
    completion_date = Column(DateTime)
    
    # Agent coordination (for parallel processing)
    assigned_agent = Column(String)
    reserved_at = Column(DateTime)
    
    # Categorization (mostly static)
    category = Column(String)
    tags = Column(JSON)
    time_period = Column(String)
    
    # Research details (mutable)
    research_notes = Column(Text)
    blockers = Column(Text)
    next_steps = Column(Text)
    
    # Quality and value (mutable)
    estimated_importance = Column(Integer)
    actual_importance = Column(Integer)
    export_worthy = Column(Boolean, default=False)  # Should be saved back to repo
    
    # Source tracking
    source_file = Column(String)  # Original JSON file if seeded from repo
    is_generated = Column(Boolean, default=False)  # Created during session vs from file
    
    # Relationships
    created_events = relationship("EventMetadata", back_populates="research_priority")
    research_links = relationship("EventResearchLink", back_populates="priority")
    activity_logs = relationship("ActivityLog", back_populates="priority")

class EventResearchLink(Base):
    """
    Links between events and research priorities
    Tracks which research generated which events
    """
    __tablename__ = 'event_research_links'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String, ForeignKey('timeline_events.id'))
    priority_id = Column(String, ForeignKey('research_priorities.id'))
    
    link_type = Column(String)  # generated, related, validates, contradicts
    confidence = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    event = relationship("TimelineEvent", back_populates="research_links")
    priority = relationship("ResearchPriority", back_populates="research_links")

class ActivityLog(Base):
    """
    Track all research activities for metrics and debugging
    """
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now(), index=True)
    
    action = Column(String, nullable=False)  # research_started, event_created, priority_completed
    agent = Column(String)  # Which agent/tool performed action
    
    # Optional foreign keys
    event_id = Column(String, ForeignKey('timeline_events.id'))
    priority_id = Column(String, ForeignKey('research_priorities.id'))
    
    # Details
    details = Column(JSON)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    duration_seconds = Column(Float)
    
    # Relationships
    priority = relationship("ResearchPriority", back_populates="activity_logs")

class ResearchSession(Base):
    """
    Track research sessions for commit orchestration
    """
    __tablename__ = 'research_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, nullable=False)
    
    started_at = Column(DateTime, default=func.now())
    ended_at = Column(DateTime)
    
    # Tracking for commit orchestration
    events_created = Column(Integer, default=0)
    priorities_completed = Column(Integer, default=0)
    last_commit = Column(DateTime)
    commit_threshold = Column(Integer, default=10)  # Commit every N events
    
    # Session metadata
    agent_config = Column(JSON)
    notes = Column(Text)
    
class SystemMetrics(Base):
    """
    System-wide metrics for monitoring
    """
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float)
    metric_type = Column(String)  # counter, gauge, histogram
    timestamp = Column(DateTime, default=func.now())
    details = Column(JSON)

# Database setup
def init_database(db_path='unified_research.db'):
    """Initialize database with all tables"""
    engine = create_engine(f'sqlite:///{db_path}', 
                          connect_args={'check_same_thread': False})
    
    # Create all tables first
    Base.metadata.create_all(engine)
    
    # Enable SQLite optimizations and FTS after tables exist
    from sqlalchemy import text
    with engine.connect() as conn:
        conn.execute(text('PRAGMA journal_mode=WAL'))
        conn.execute(text('PRAGMA synchronous=NORMAL'))
        conn.execute(text('PRAGMA cache_size=10000'))
        conn.execute(text('PRAGMA temp_store=MEMORY'))
        conn.execute(text('PRAGMA mmap_size=268435456'))
        
        # Enable full-text search for events
        conn.execute(text('''
            CREATE VIRTUAL TABLE IF NOT EXISTS events_fts USING fts5(
                id UNINDEXED,
                title,
                summary,
                json_content,
                content=timeline_events
            )
        '''))
        
        # Triggers to keep FTS index updated
        conn.execute(text('''
            CREATE TRIGGER IF NOT EXISTS events_fts_insert 
            AFTER INSERT ON timeline_events
            BEGIN
                INSERT INTO events_fts(id, title, summary, json_content)
                VALUES (new.id, new.title, new.summary, new.json_content);
            END
        '''))
        
        conn.execute(text('''
            CREATE TRIGGER IF NOT EXISTS events_fts_update
            AFTER UPDATE ON timeline_events
            BEGIN
                UPDATE events_fts 
                SET title = new.title, summary = new.summary, json_content = new.json_content
                WHERE id = new.id;
            END
        '''))
        conn.commit()
    
    return engine

def get_session(engine):
    """Get a new database session"""
    Session = sessionmaker(bind=engine)
    return Session()