"""
Alert Management for RAG Monitoring

Handle alerts and notifications for research quality issues.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional
from enum import Enum
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from pathlib import Path


logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertType(Enum):
    """Types of alerts."""
    LOW_RECALL = "low_recall"
    LOW_PRECISION = "low_precision"
    INCONSISTENT_RESULTS = "inconsistent_results"
    INCOMPLETE_COVERAGE = "incomplete_coverage"
    SLOW_QUERY = "slow_query"
    HIGH_ERROR_RATE = "high_error_rate"
    SYSTEM_FAILURE = "system_failure"


class Alert:
    """Individual alert instance."""
    
    def __init__(self, level: AlertLevel, type: AlertType, 
                 message: str, details: Dict[str, Any] = None):
        """
        Create alert.
        
        Args:
            level: Alert severity
            type: Alert type
            message: Alert message
            details: Additional details
        """
        self.id = datetime.now().isoformat() + "_" + type.value
        self.timestamp = datetime.now()
        self.level = level
        self.type = type
        self.message = message
        self.details = details or {}
        self.acknowledged = False
        self.resolved = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'type': self.type.value,
            'message': self.message,
            'details': self.details,
            'acknowledged': self.acknowledged,
            'resolved': self.resolved
        }


class AlertManager:
    """
    Manage alerts for RAG monitoring system.
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize alert manager.
        
        Args:
            config_file: Path to alert configuration
        """
        self.config_file = config_file
        self.config = self._load_config()
        
        # Alert storage
        self.active_alerts = {}
        self.alert_history = []
        
        # Alert handlers
        self.handlers = {
            'log': self._handle_log_alert,
            'file': self._handle_file_alert,
            'email': self._handle_email_alert,
            'callback': []
        }
        
        # Alert rules
        self.rules = self._init_rules()
        
        # Statistics
        self.stats = defaultdict(int)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load alert configuration."""
        default_config = {
            'enabled': True,
            'handlers': ['log', 'file'],
            'thresholds': {
                'low_recall': 0.95,
                'low_precision': 0.90,
                'consistency': 0.99,
                'completeness': 0.98,
                'response_time': 5.0,
                'error_rate': 0.01
            },
            'email': {
                'enabled': False,
                'smtp_server': '',
                'smtp_port': 587,
                'from_email': '',
                'to_emails': [],
                'subject_prefix': '[RAG Alert]'
            },
            'file': {
                'path': 'alerts.log',
                'max_size': 10485760  # 10MB
            }
        }
        
        if self.config_file and Path(self.config_file).exists():
            with open(self.config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _init_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize alert rules."""
        return {
            AlertType.LOW_RECALL: {
                'level': AlertLevel.CRITICAL,
                'threshold': self.config['thresholds']['low_recall'],
                'message_template': "Recall rate {value:.2%} below critical threshold {threshold:.2%}"
            },
            AlertType.LOW_PRECISION: {
                'level': AlertLevel.WARNING,
                'threshold': self.config['thresholds']['low_precision'],
                'message_template': "Precision rate {value:.2%} below target {threshold:.2%}"
            },
            AlertType.INCONSISTENT_RESULTS: {
                'level': AlertLevel.CRITICAL,
                'threshold': self.config['thresholds']['consistency'],
                'message_template': "Result consistency {value:.2%} indicates reproducibility issues"
            },
            AlertType.INCOMPLETE_COVERAGE: {
                'level': AlertLevel.WARNING,
                'threshold': self.config['thresholds']['completeness'],
                'message_template': "Coverage completeness {value:.2%} may miss relevant events"
            },
            AlertType.SLOW_QUERY: {
                'level': AlertLevel.INFO,
                'threshold': self.config['thresholds']['response_time'],
                'message_template': "Query took {value:.2f}s (threshold: {threshold:.1f}s)"
            },
            AlertType.HIGH_ERROR_RATE: {
                'level': AlertLevel.ERROR,
                'threshold': self.config['thresholds']['error_rate'],
                'message_template': "Error rate {value:.2%} exceeds acceptable limit"
            }
        }
    
    def check_metrics(self, metrics: Dict[str, Any]) -> List[Alert]:
        """
        Check metrics against alert rules.
        
        Args:
            metrics: Current metrics
            
        Returns:
            List of triggered alerts
        """
        if not self.config['enabled']:
            return []
        
        alerts = []
        
        # Check research metrics
        research_metrics = metrics.get('research_metrics', {})
        
        # Recall check
        if 'avg_recall' in research_metrics:
            value = research_metrics['avg_recall']
            rule = self.rules[AlertType.LOW_RECALL]
            if value < rule['threshold']:
                alerts.append(self._create_alert(
                    AlertType.LOW_RECALL,
                    rule['level'],
                    rule['message_template'].format(value=value, threshold=rule['threshold']),
                    {'value': value, 'threshold': rule['threshold']}
                ))
        
        # Consistency check
        if 'consistency_rate' in research_metrics:
            value = research_metrics['consistency_rate']
            rule = self.rules[AlertType.INCONSISTENT_RESULTS]
            if value < rule['threshold']:
                alerts.append(self._create_alert(
                    AlertType.INCONSISTENT_RESULTS,
                    rule['level'],
                    rule['message_template'].format(value=value, threshold=rule['threshold']),
                    {'value': value, 'threshold': rule['threshold'],
                     'violations': research_metrics.get('consistency_violations', 0)}
                ))
        
        # Performance checks
        perf_metrics = metrics.get('performance_metrics', {})
        
        if 'avg_response_time' in perf_metrics:
            value = perf_metrics['avg_response_time']
            rule = self.rules[AlertType.SLOW_QUERY]
            if value > rule['threshold']:
                alerts.append(self._create_alert(
                    AlertType.SLOW_QUERY,
                    rule['level'],
                    rule['message_template'].format(value=value, threshold=rule['threshold']),
                    {'value': value, 'threshold': rule['threshold']}
                ))
        
        return alerts
    
    def _create_alert(self, type: AlertType, level: AlertLevel,
                     message: str, details: Dict[str, Any]) -> Alert:
        """Create and process alert."""
        alert = Alert(level, type, message, details)
        
        # Check if similar alert already active
        if not self._is_duplicate(alert):
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)
            self.stats[f'{level.value}_count'] += 1
            
            # Process through handlers
            self._process_alert(alert)
        
        return alert
    
    def _is_duplicate(self, alert: Alert, window_seconds: int = 300) -> bool:
        """Check if alert is duplicate within time window."""
        cutoff = datetime.now().timestamp() - window_seconds
        
        for existing_id, existing_alert in self.active_alerts.items():
            if (existing_alert.type == alert.type and
                existing_alert.timestamp.timestamp() > cutoff and
                not existing_alert.resolved):
                return True
        
        return False
    
    def _process_alert(self, alert: Alert):
        """Process alert through configured handlers."""
        for handler_name in self.config['handlers']:
            if handler_name == 'callback':
                for callback in self.handlers['callback']:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")
            elif handler_name in self.handlers:
                try:
                    self.handlers[handler_name](alert)
                except Exception as e:
                    logger.error(f"Error in {handler_name} handler: {e}")
    
    def _handle_log_alert(self, alert: Alert):
        """Log alert to logger."""
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }.get(alert.level, logging.INFO)
        
        logger.log(log_level, f"[{alert.type.value}] {alert.message}")
    
    def _handle_file_alert(self, alert: Alert):
        """Write alert to file."""
        file_path = Path(self.config['file']['path'])
        
        # Rotate if too large
        if file_path.exists() and file_path.stat().st_size > self.config['file']['max_size']:
            file_path.rename(f"{file_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        with open(file_path, 'a') as f:
            f.write(json.dumps(alert.to_dict()) + '\n')
    
    def _handle_email_alert(self, alert: Alert):
        """Send alert via email."""
        if not self.config['email']['enabled']:
            return
        
        # Only send email for critical alerts
        if alert.level != AlertLevel.CRITICAL:
            return
        
        try:
            subject = f"{self.config['email']['subject_prefix']} {alert.type.value}"
            body = f"""
RAG System Alert

Level: {alert.level.value}
Type: {alert.type.value}
Time: {alert.timestamp.isoformat()}
Message: {alert.message}

Details:
{json.dumps(alert.details, indent=2)}

---
This is an automated alert from the RAG monitoring system.
"""
            
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.config['email']['from_email']
            msg['To'] = ', '.join(self.config['email']['to_emails'])
            
            with smtplib.SMTP(self.config['email']['smtp_server'], 
                             self.config['email']['smtp_port']) as server:
                server.starttls()
                # Add authentication if needed
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def register_callback(self, callback: Callable[[Alert], None]):
        """
        Register callback for alert handling.
        
        Args:
            callback: Function to call with alert
        """
        self.handlers['callback'].append(callback)
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Success status
        """
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """
        Mark alert as resolved.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Success status
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = datetime.now()
            return True
        return False
    
    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """
        Get active alerts.
        
        Args:
            level: Optional filter by level
            
        Returns:
            List of active alerts
        """
        alerts = [a for a in self.active_alerts.values() if not a.resolved]
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        active_by_level = defaultdict(int)
        active_by_type = defaultdict(int)
        
        for alert in self.active_alerts.values():
            if not alert.resolved:
                active_by_level[alert.level.value] += 1
                active_by_type[alert.type.value] += 1
        
        return {
            'total_active': len([a for a in self.active_alerts.values() if not a.resolved]),
            'total_historical': len(self.alert_history),
            'by_level': dict(active_by_level),
            'by_type': dict(active_by_type),
            'counts': dict(self.stats)
        }
    
    def clear_resolved_alerts(self, older_than_hours: int = 24):
        """
        Clear resolved alerts older than specified hours.
        
        Args:
            older_than_hours: Age threshold in hours
        """
        cutoff = datetime.now().timestamp() - (older_than_hours * 3600)
        
        to_remove = []
        for alert_id, alert in self.active_alerts.items():
            if alert.resolved and alert.timestamp.timestamp() < cutoff:
                to_remove.append(alert_id)
        
        for alert_id in to_remove:
            del self.active_alerts[alert_id]
        
        logger.info(f"Cleared {len(to_remove)} resolved alerts")


if __name__ == '__main__':
    # Example usage
    manager = AlertManager()
    
    # Test metrics
    test_metrics = {
        'research_metrics': {
            'avg_recall': 0.85,  # Below threshold
            'consistency_rate': 0.95  # Below threshold
        },
        'performance_metrics': {
            'avg_response_time': 6.5  # Above threshold
        }
    }
    
    # Check for alerts
    alerts = manager.check_metrics(test_metrics)
    
    print(f"Generated {len(alerts)} alerts:")
    for alert in alerts:
        print(f"  {alert.level.value}: {alert.message}")
    
    # Get statistics
    stats = manager.get_alert_statistics()
    print(f"\nAlert Statistics:")
    print(json.dumps(stats, indent=2))