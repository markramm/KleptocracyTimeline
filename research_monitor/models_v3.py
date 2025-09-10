"""
Enhanced Database Models v3 - With validation and metadata tracking
Enforces proper event format and tracks validation/enhancement history
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, Text, JSON, Float, ForeignKey, Index, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class TimelineEvent(Base):
    """Enhanced timeline event with strict validation requirements"""
    __tablename__ = 'timeline_events'
    
    # Core fields
    id = Column(String, primary_key=True)
    date = Column(String, nullable=False)  # YYYY-MM-DD format enforced
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    
    # Required structured fields (stored as JSON but validated)
    actors = Column(JSON, nullable=False)  # Must be non-empty list
    sources = Column(JSON, nullable=False)  # Must be list of source objects
    tags = Column(JSON, nullable=False)  # Must be non-empty list
    
    # Optional fields
    timeline_tags = Column(JSON)
    connections = Column(JSON)
    location = Column(String)
    
    # Status and importance
    status = Column(String, default='confirmed')
    importance = Column(Integer, default=7)
    
    # Validation tracking
    validation_status = Column(String, default='unvalidated')  # unvalidated, partial, validated, enhanced
    validation_score = Column(Float, default=0.0)  # 0.0 to 1.0
    last_validated = Column(DateTime)
    validation_notes = Column(Text)
    
    # Source verification
    sources_verified = Column(Boolean, default=False)
    actors_verified = Column(Boolean, default=False)
    date_verified = Column(Boolean, default=False)
    
    # File tracking
    file_path = Column(String, unique=True)
    file_hash = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)  # Agent or user that created
    last_modified_by = Column(String)  # Agent or user that last modified
    
    # Priority relationship
    priority_id = Column(String, ForeignKey('research_priorities.id'))
    priority = relationship("ResearchPriority", back_populates="events")
    
    # Validation history relationship
    validation_history = relationship("ValidationHistory", back_populates="event", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('confirmed', 'alleged', 'reported', 'speculative', 'developing', 'disputed', 'predicted')", name='valid_status'),
        CheckConstraint("importance >= 1 AND importance <= 10", name='valid_importance'),
        CheckConstraint("validation_status IN ('unvalidated', 'partial', 'validated', 'enhanced')", name='valid_validation_status'),
        CheckConstraint("validation_score >= 0.0 AND validation_score <= 1.0", name='valid_validation_score'),
        Index('idx_date', 'date'),
        Index('idx_validation_status', 'validation_status'),
        Index('idx_importance', 'importance'),
    )
    
    def validate_format(self):
        """Validate event format compliance"""
        errors = []
        
        # Check date format
        if not self.date or len(self.date) != 10 or self.date[4] != '-' or self.date[7] != '-':
            errors.append("Invalid date format - must be YYYY-MM-DD")
        
        # Check required lists are non-empty
        if not self.actors or len(self.actors) == 0:
            errors.append("Actors list cannot be empty")
        
        if not self.tags or len(self.tags) == 0:
            errors.append("Tags list cannot be empty")
        
        if not self.sources or len(self.sources) == 0:
            errors.append("Sources list cannot be empty")
        
        # Validate source format
        if self.sources:
            for i, source in enumerate(self.sources):
                if not isinstance(source, dict):
                    errors.append(f"Source {i+1} must be a dictionary")
                elif not source.get('title') or not source.get('url'):
                    errors.append(f"Source {i+1} missing required title or url")
        
        return errors
    
    def calculate_validation_score(self):
        """Calculate validation score based on completeness and verification"""
        score = 0.0
        total_checks = 10
        
        # Basic requirements (4 points)
        if self.date and len(self.date) == 10:
            score += 1
        if self.title and len(self.title) > 10:
            score += 1
        if self.summary and len(self.summary) > 50:
            score += 1
        if self.status in ['confirmed', 'alleged', 'reported', 'speculative', 'developing', 'disputed', 'predicted']:
            score += 1
        
        # Required lists (3 points)
        if self.actors and len(self.actors) >= 3:
            score += 1
        if self.sources and len(self.sources) >= 2:
            score += 1
        if self.tags and len(self.tags) >= 3:
            score += 1
        
        # Verification status (3 points)
        if self.sources_verified:
            score += 1
        if self.actors_verified:
            score += 1
        if self.date_verified:
            score += 1
        
        self.validation_score = score / total_checks
        return self.validation_score


class ValidationHistory(Base):
    """Track validation and enhancement actions on events"""
    __tablename__ = 'validation_history'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String, ForeignKey('timeline_events.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Validation action details
    action_type = Column(String, nullable=False)  # validate, enhance, fix, verify
    agent_id = Column(String, nullable=False)  # Agent that performed action
    
    # Changes made
    fields_modified = Column(JSON)  # List of field names that were modified
    changes_description = Column(Text)  # Human-readable description of changes
    
    # Before and after states
    before_state = Column(JSON)  # State before changes
    after_state = Column(JSON)  # State after changes
    
    # Validation details
    errors_found = Column(JSON)  # List of validation errors found
    errors_fixed = Column(JSON)  # List of errors that were fixed
    
    # Source verification
    sources_checked = Column(Integer, default=0)
    sources_verified = Column(Integer, default=0)
    sources_added = Column(Integer, default=0)
    
    # Actor verification
    actors_checked = Column(Integer, default=0)
    actors_verified = Column(Integer, default=0)
    actors_added = Column(Integer, default=0)
    
    # Confidence metrics
    confidence_before = Column(Float)  # 0.0 to 1.0
    confidence_after = Column(Float)  # 0.0 to 1.0
    
    # Notes
    notes = Column(Text)
    
    # Relationship
    event = relationship("TimelineEvent", back_populates="validation_history")
    
    __table_args__ = (
        CheckConstraint("action_type IN ('validate', 'enhance', 'fix', 'verify', 'review')", name='valid_action_type'),
        Index('idx_event_id', 'event_id'),
        Index('idx_timestamp', 'timestamp'),
    )


class ResearchPriority(Base):
    """Research priority with enhanced tracking"""
    __tablename__ = 'research_priorities'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    priority = Column(Integer, default=5)
    status = Column(String, default='pending')
    
    # Expected quality metrics
    estimated_events = Column(Integer)
    actual_events = Column(Integer, default=0)
    validation_required = Column(Boolean, default=True)
    
    # Tracking
    category = Column(String)
    tags = Column(JSON)
    
    # File metadata
    file_path = Column(String, unique=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Agent coordination
    assigned_agent = Column(String)
    reserved_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Quality tracking
    events_validated = Column(Integer, default=0)
    average_validation_score = Column(Float)
    
    # Notes
    notes = Column(Text)
    
    # Relationships
    events = relationship("TimelineEvent", back_populates="priority")
    
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'reserved', 'in_progress', 'completed', 'failed', 'needs_validation')", name='valid_priority_status'),
        CheckConstraint("priority >= 1 AND priority <= 10", name='valid_priority_value'),
        Index('idx_status', 'status'),
        Index('idx_priority', 'priority'),
    )


class EventValidationQueue(Base):
    """Queue for events needing validation or enhancement"""
    __tablename__ = 'event_validation_queue'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(String, ForeignKey('timeline_events.id'), unique=True, nullable=False)
    
    # Queue metadata
    added_at = Column(DateTime, default=datetime.utcnow)
    priority = Column(Integer, default=5)  # 1-10, higher = more urgent
    
    # Validation requirements
    validation_type = Column(String, default='full')  # full, sources, actors, dates, enhance
    reason = Column(Text)  # Why this event needs validation
    
    # Assignment
    assigned_to = Column(String)  # Agent assigned to validate
    assigned_at = Column(DateTime)
    
    # Status
    status = Column(String, default='pending')  # pending, assigned, processing, completed, failed
    completed_at = Column(DateTime)
    
    # Results
    validation_passed = Column(Boolean)
    errors_found = Column(JSON)
    fixes_applied = Column(JSON)
    
    __table_args__ = (
        CheckConstraint("priority >= 1 AND priority <= 10", name='valid_queue_priority'),
        CheckConstraint("status IN ('pending', 'assigned', 'processing', 'completed', 'failed')", name='valid_queue_status'),
        CheckConstraint("validation_type IN ('full', 'sources', 'actors', 'dates', 'enhance')", name='valid_validation_type'),
        Index('idx_queue_status', 'status'),
        Index('idx_queue_priority', 'priority'),
    )


def create_tables(engine):
    """Create all tables with enhanced schema"""
    Base.metadata.create_all(engine)
    
def get_engine(db_path='unified_research_v3.db'):
    """Get database engine with enhanced schema"""
    return create_engine(f'sqlite:///{db_path}')