#!/usr/bin/env python3
"""
Comprehensive Logging System for Kleptocracy Timeline Research
Handles event logging, task timing, and performance metrics
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import hashlib
import traceback
from contextlib import contextmanager
import jsonschema
from dataclasses import dataclass, asdict
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class EventAction(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VALIDATE = "VALIDATE"
    LOAD = "LOAD"

@dataclass
class TaskTiming:
    task_id: str
    task_type: str
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    status: str = "running"
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def complete(self, status: str = "completed", error: Optional[str] = None):
        """Mark task as completed and calculate duration"""
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time
        self.status = status
        self.error = error

@dataclass 
class EventLog:
    timestamp: str
    action: str
    entity_type: str  # "timeline_event" or "research_priority"
    entity_id: str
    file_path: str
    status: str  # "success" or "error"
    details: Dict[str, Any]
    error: Optional[str] = None
    validation_errors: List[str] = None

class LoggingSystem:
    def __init__(self, base_dir: str = "logs"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.events_dir = self.base_dir / "events" 
        self.tasks_dir = self.base_dir / "tasks"
        self.performance_dir = self.base_dir / "performance"
        
        for dir_path in [self.events_dir, self.tasks_dir, self.performance_dir]:
            dir_path.mkdir(exist_ok=True)
            
        # Load schemas
        self.schemas = self._load_schemas()
        
        # Active task timings
        self.active_tasks: Dict[str, TaskTiming] = {}
        
        # Setup loggers
        self._setup_loggers()
        
    def _load_schemas(self) -> Dict[str, Dict]:
        """Load JSON schemas for validation"""
        schemas = {}
        schema_dir = Path("schemas")
        
        if schema_dir.exists():
            for schema_file in schema_dir.glob("*.json"):
                try:
                    with open(schema_file) as f:
                        schema_name = schema_file.stem
                        schemas[schema_name] = json.load(f)
                        logging.info(f"Loaded schema: {schema_name}")
                except Exception as e:
                    logging.error(f"Failed to load schema {schema_file}: {e}")
                    
        return schemas
        
    def _setup_loggers(self):
        """Setup structured loggers"""
        # Event logger
        self.event_logger = logging.getLogger("events")
        event_handler = logging.FileHandler(self.events_dir / f"events_{datetime.now():%Y%m%d}.log")
        event_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.event_logger.addHandler(event_handler)
        self.event_logger.setLevel(logging.INFO)
        
        # Task logger
        self.task_logger = logging.getLogger("tasks")
        task_handler = logging.FileHandler(self.tasks_dir / f"tasks_{datetime.now():%Y%m%d}.log")
        task_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.task_logger.addHandler(task_handler)
        self.task_logger.setLevel(logging.INFO)
        
        # Performance logger
        self.perf_logger = logging.getLogger("performance")
        perf_handler = logging.FileHandler(self.performance_dir / f"performance_{datetime.now():%Y%m%d}.log")
        perf_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.perf_logger.addHandler(perf_handler)
        self.perf_logger.setLevel(logging.INFO)
        
    def validate_json(self, data: Dict, schema_name: str) -> tuple[bool, List[str]]:
        """Validate JSON data against schema"""
        if schema_name not in self.schemas:
            return False, [f"Schema '{schema_name}' not found"]
            
        try:
            jsonschema.validate(data, self.schemas[schema_name])
            return True, []
        except jsonschema.ValidationError as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
            
    def log_event_operation(self, action: EventAction, entity_type: str, 
                          entity_id: str, file_path: str, 
                          data: Optional[Dict] = None, error: Optional[str] = None,
                          validation_errors: Optional[List[str]] = None):
        """Log event creation, update, or deletion"""
        
        # Validate data if provided
        schema_name = None
        if entity_type == "timeline_event":
            schema_name = "timeline_event_schema"
        elif entity_type == "research_priority":
            schema_name = "research_priority_schema"
            
        if data and schema_name:
            is_valid, val_errors = self.validate_json(data, schema_name)
            if not is_valid:
                validation_errors = val_errors
                
        event_log = EventLog(
            timestamp=datetime.now().isoformat(),
            action=action.value,
            entity_type=entity_type,
            entity_id=entity_id,
            file_path=file_path,
            status="success" if not error and not validation_errors else "error",
            details={
                "data_hash": hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest() if data else None,
                "data_size": len(json.dumps(data)) if data else 0,
                "has_validation_errors": bool(validation_errors)
            },
            error=error,
            validation_errors=validation_errors or []
        )
        
        # Log to structured file
        log_entry = asdict(event_log)
        self.event_logger.info(json.dumps(log_entry))
        
        # Also log to daily event log file
        daily_log_file = self.events_dir / f"events_{datetime.now():%Y%m%d}.jsonl"
        with open(daily_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\\n')
            
        # Print validation errors if any
        if validation_errors:
            logging.error(f"Validation errors for {entity_id}: {validation_errors}")
            
    def start_task(self, task_id: str, task_type: str, metadata: Optional[Dict] = None) -> str:
        """Start timing a task"""
        timing = TaskTiming(
            task_id=task_id,
            task_type=task_type,
            start_time=time.time(),
            metadata=metadata or {}
        )
        
        self.active_tasks[task_id] = timing
        
        self.task_logger.info(f"STARTED - {task_type} - {task_id} - {json.dumps(metadata or {})}")
        return task_id
        
    def complete_task(self, task_id: str, status: str = "completed", 
                     error: Optional[str] = None, metadata: Optional[Dict] = None):
        """Complete a task and log timing"""
        if task_id not in self.active_tasks:
            logging.warning(f"Task {task_id} not found in active tasks")
            return
            
        timing = self.active_tasks[task_id]
        timing.complete(status, error)
        
        if metadata:
            timing.metadata.update(metadata)
            
        # Log completion
        log_data = asdict(timing)
        self.task_logger.info(f"COMPLETED - {json.dumps(log_data)}")
        
        # Log to daily task file
        daily_task_file = self.tasks_dir / f"tasks_{datetime.now():%Y%m%d}.jsonl"
        with open(daily_task_file, 'a') as f:
            f.write(json.dumps(log_data) + '\\n')
            
        # Remove from active tasks
        del self.active_tasks[task_id]
        
        return timing
        
    @contextmanager
    def timed_task(self, task_id: str, task_type: str, metadata: Optional[Dict] = None):
        """Context manager for timing tasks"""
        self.start_task(task_id, task_type, metadata)
        
        try:
            yield task_id
            self.complete_task(task_id, "completed")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.complete_task(task_id, "error", error_msg)
            raise
            
    def log_performance_metrics(self, round_number: int, metrics: Dict[str, Any]):
        """Log round performance metrics"""
        perf_data = {
            "timestamp": datetime.now().isoformat(),
            "round_number": round_number,
            "metrics": metrics
        }
        
        self.perf_logger.info(json.dumps(perf_data))
        
        # Daily performance file
        daily_perf_file = self.performance_dir / f"performance_{datetime.now():%Y%m%d}.jsonl"
        with open(daily_perf_file, 'a') as f:
            f.write(json.dumps(perf_data) + '\\n')
            
    def get_task_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get task performance statistics"""
        # Read task logs from the last N hours
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        tasks = []
        daily_task_file = self.tasks_dir / f"tasks_{datetime.now():%Y%m%d}.jsonl"
        
        if daily_task_file.exists():
            with open(daily_task_file, 'r') as f:
                for line in f:
                    try:
                        task_data = json.loads(line.strip())
                        if task_data.get('start_time', 0) >= cutoff_time:
                            tasks.append(task_data)
                    except json.JSONDecodeError:
                        continue
                        
        if not tasks:
            return {"total_tasks": 0, "avg_duration": 0, "success_rate": 100}
            
        completed_tasks = [t for t in tasks if t['status'] == 'completed']
        error_tasks = [t for t in tasks if t['status'] == 'error']
        
        avg_duration = sum(t.get('duration_seconds', 0) for t in completed_tasks) / len(completed_tasks) if completed_tasks else 0
        success_rate = (len(completed_tasks) / len(tasks)) * 100 if tasks else 100
        
        by_type = {}
        for task in tasks:
            task_type = task['task_type']
            if task_type not in by_type:
                by_type[task_type] = {'count': 0, 'avg_duration': 0, 'errors': 0}
            by_type[task_type]['count'] += 1
            if task['status'] == 'error':
                by_type[task_type]['errors'] += 1
            if task.get('duration_seconds'):
                current_avg = by_type[task_type]['avg_duration']
                count = by_type[task_type]['count']
                by_type[task_type]['avg_duration'] = (current_avg * (count - 1) + task['duration_seconds']) / count
                
        return {
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "error_tasks": len(error_tasks),
            "success_rate": success_rate,
            "avg_duration_seconds": avg_duration,
            "by_type": by_type,
            "active_tasks": len(self.active_tasks)
        }
        
    def get_validation_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get validation error statistics"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        events = []
        daily_event_file = self.events_dir / f"events_{datetime.now():%Y%m%d}.jsonl"
        
        if daily_event_file.exists():
            with open(daily_event_file, 'r') as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        timestamp = datetime.fromisoformat(event_data['timestamp']).timestamp()
                        if timestamp >= cutoff_time:
                            events.append(event_data)
                    except (json.JSONDecodeError, ValueError):
                        continue
                        
        if not events:
            return {"total_events": 0, "validation_errors": 0, "error_rate": 0}
            
        validation_errors = [e for e in events if e.get('validation_errors')]
        error_rate = (len(validation_errors) / len(events)) * 100 if events else 0
        
        by_entity_type = {}
        for event in events:
            entity_type = event['entity_type']
            if entity_type not in by_entity_type:
                by_entity_type[entity_type] = {'total': 0, 'errors': 0}
            by_entity_type[entity_type]['total'] += 1
            if event.get('validation_errors'):
                by_entity_type[entity_type]['errors'] += 1
                
        return {
            "total_events": len(events),
            "validation_errors": len(validation_errors),
            "error_rate": error_rate,
            "by_entity_type": by_entity_type
        }

# Global logging instance
logger_system = LoggingSystem()

def log_event_operation(action: EventAction, entity_type: str, entity_id: str, 
                       file_path: str, data: Optional[Dict] = None, 
                       error: Optional[str] = None) -> None:
    """Convenience function for logging events"""
    logger_system.log_event_operation(action, entity_type, entity_id, file_path, data, error)

def timed_task(task_id: str, task_type: str, metadata: Optional[Dict] = None):
    """Convenience function for timing tasks"""
    return logger_system.timed_task(task_id, task_type, metadata)

def validate_timeline_event(data: Dict) -> tuple[bool, List[str]]:
    """Convenience function for validating timeline events"""
    return logger_system.validate_json(data, "timeline_event_schema")

def validate_research_priority(data: Dict) -> tuple[bool, List[str]]:
    """Convenience function for validating research priorities"""
    return logger_system.validate_json(data, "research_priority_schema")