#!/usr/bin/env python3
"""
PinokioCloud Advanced Logging System

This module creates comprehensive logs of everything that happens in PinokioCloud.
It provides advanced logging capabilities with analytics, log analysis, and
integration with all PinokioCloud systems for complete operational visibility.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import logging
import threading
import gzip
from typing import Dict, List, Optional, Any, Tuple, TextIO
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import json
import re
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from environment_management.json_handler import JSONHandler
from cloud_detection.cloud_detector import CloudDetector


class LogLevel(Enum):
    """Log levels for the logging system."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Categories of log entries."""
    SYSTEM = "system"
    APPLICATION = "application"
    INSTALLATION = "installation"
    PROCESS = "process"
    TUNNEL = "tunnel"
    PERFORMANCE = "performance"
    ERROR = "error"
    USER_ACTION = "user_action"


class LogFormat(Enum):
    """Log output formats."""
    STANDARD = "standard"
    JSON = "json"
    STRUCTURED = "structured"
    MINIMAL = "minimal"


@dataclass
class LogEntry:
    """Individual log entry."""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    component: str
    message: str
    app_name: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert LogEntry to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.value
        data['category'] = self.category.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create LogEntry from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['level'] = LogLevel(data['level'])
        data['category'] = LogCategory(data['category'])
        return cls(**data)


@dataclass
class LogAnalysis:
    """Log analysis results."""
    analysis_id: str
    analyzed_at: datetime
    log_count: int
    error_count: int
    warning_count: int
    time_range: Tuple[datetime, datetime]
    top_errors: List[Dict[str, Any]]
    performance_issues: List[Dict[str, Any]]
    recommendations: List[str]
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert LogAnalysis to dictionary."""
        data = asdict(self)
        data['analyzed_at'] = self.analyzed_at.isoformat()
        data['time_range'] = [self.time_range[0].isoformat(), self.time_range[1].isoformat()]
        return data


class LogAnalyzer:
    """
    Analyzes logs for patterns, issues, and insights.
    
    This class provides comprehensive log analysis with pattern recognition,
    performance insights, and operational recommendations.
    """
    
    def __init__(self, logging_system: 'LoggingSystem'):
        """Initialize the log analyzer."""
        self.logging_system = logging_system
        self.analysis_patterns = self._setup_analysis_patterns()
        
    def analyze_logs(self, hours: int = 24) -> LogAnalysis:
        """
        Analyze logs for the specified time period.
        
        Args:
            hours: Number of hours to analyze
        
        Returns:
            LogAnalysis: Analysis results
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Get logs in time range
            logs = self.logging_system.get_logs(start_time, end_time)
            
            # Analyze logs
            analysis_id = f"analysis_{int(end_time.timestamp())}"
            
            # Count by level
            error_count = len([log for log in logs if log.level == LogLevel.ERROR])
            warning_count = len([log for log in logs if log.level == LogLevel.WARNING])
            
            # Find top errors
            top_errors = self._find_top_errors(logs)
            
            # Find performance issues
            performance_issues = self._find_performance_issues(logs)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(logs, error_count, warning_count)
            
            # Create summary
            summary = self._create_summary(logs, error_count, warning_count)
            
            analysis = LogAnalysis(
                analysis_id=analysis_id,
                analyzed_at=end_time,
                log_count=len(logs),
                error_count=error_count,
                warning_count=warning_count,
                time_range=(start_time, end_time),
                top_errors=top_errors,
                performance_issues=performance_issues,
                recommendations=recommendations,
                summary=summary
            )
            
            return analysis
            
        except Exception as e:
            print(f"[LogAnalyzer] Error analyzing logs: {e}")
            return LogAnalysis(
                analysis_id="error",
                analyzed_at=datetime.now(),
                log_count=0,
                error_count=0,
                warning_count=0,
                time_range=(datetime.now(), datetime.now()),
                top_errors=[],
                performance_issues=[],
                recommendations=[],
                summary="Analysis failed"
            )
    
    def _setup_analysis_patterns(self) -> Dict[str, List[str]]:
        """Set up patterns for log analysis."""
        return {
            'performance_issues': [
                r'high cpu usage',
                r'memory.*full',
                r'slow.*response',
                r'timeout.*occurred'
            ],
            'critical_errors': [
                r'out of memory',
                r'segmentation fault',
                r'permission denied',
                r'disk.*full'
            ],
            'network_issues': [
                r'connection.*failed',
                r'network.*timeout',
                r'tunnel.*disconnected'
            ]
        }
    
    def _find_top_errors(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Find most common errors."""
        try:
            error_logs = [log for log in logs if log.level == LogLevel.ERROR]
            error_messages = {}
            
            for log in error_logs:
                # Normalize error message
                normalized = re.sub(r'\d+', 'N', log.message)  # Replace numbers
                normalized = re.sub(r'[\'"][^\'\"]*[\'"]', 'STR', normalized)  # Replace strings
                
                if normalized not in error_messages:
                    error_messages[normalized] = {'count': 0, 'example': log.message, 'component': log.component}
                error_messages[normalized]['count'] += 1
            
            # Sort by frequency
            top_errors = sorted(error_messages.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
            
            return [{'pattern': pattern, **info} for pattern, info in top_errors]
            
        except Exception as e:
            print(f"[LogAnalyzer] Error finding top errors: {e}")
            return []
    
    def _find_performance_issues(self, logs: List[LogEntry]) -> List[Dict[str, Any]]:
        """Find performance-related issues."""
        try:
            performance_logs = [log for log in logs if log.category == LogCategory.PERFORMANCE]
            issues = []
            
            for log in performance_logs:
                if any(keyword in log.message.lower() for keyword in ['slow', 'timeout', 'high', 'exceeded']):
                    issues.append({
                        'timestamp': log.timestamp.isoformat(),
                        'component': log.component,
                        'message': log.message,
                        'app_name': log.app_name
                    })
            
            return issues[:20]  # Return top 20 issues
            
        except Exception as e:
            print(f"[LogAnalyzer] Error finding performance issues: {e}")
            return []
    
    def _generate_recommendations(self, logs: List[LogEntry], error_count: int, warning_count: int) -> List[str]:
        """Generate recommendations based on log analysis."""
        recommendations = []
        
        try:
            total_logs = len(logs)
            
            # Error rate recommendations
            if total_logs > 0:
                error_rate = (error_count / total_logs) * 100
                
                if error_rate > 10:
                    recommendations.append("High error rate detected - investigate error patterns")
                elif error_rate > 5:
                    recommendations.append("Moderate error rate - monitor for trends")
            
            # Category-specific recommendations
            category_counts = {}
            for log in logs:
                category = log.category.value
                if category not in category_counts:
                    category_counts[category] = 0
                category_counts[category] += 1
            
            if category_counts.get('error', 0) > 50:
                recommendations.append("Consider implementing additional error handling")
            
            if category_counts.get('performance', 0) > 100:
                recommendations.append("Performance monitoring shows high activity - consider optimization")
            
            return recommendations
            
        except Exception as e:
            print(f"[LogAnalyzer] Error generating recommendations: {e}")
            return []
    
    def _create_summary(self, logs: List[LogEntry], error_count: int, warning_count: int) -> str:
        """Create a summary of the log analysis."""
        try:
            total_logs = len(logs)
            
            if total_logs == 0:
                return "No logs found in the specified time period"
            
            error_rate = (error_count / total_logs) * 100
            warning_rate = (warning_count / total_logs) * 100
            
            summary = f"Analyzed {total_logs} log entries. "
            summary += f"Error rate: {error_rate:.1f}%, Warning rate: {warning_rate:.1f}%. "
            
            if error_rate > 10:
                summary += "High error rate requires attention."
            elif error_rate > 5:
                summary += "Moderate error rate, monitor trends."
            else:
                summary += "Error rate is within normal range."
            
            return summary
            
        except Exception:
            return "Unable to generate summary"


class LoggingSystem:
    """
    Advanced logging system for comprehensive operational visibility.
    
    This class provides structured logging, log analysis, and integration
    with all PinokioCloud systems for complete operational monitoring.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the logging system."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.logs_storage_path = self.base_path / "logs"
        self.logs_storage_path.mkdir(exist_ok=True)
        
        # Logging configuration
        self.log_format = LogFormat.STRUCTURED
        self.max_log_size_mb = 100
        self.max_log_files = 10
        self.log_retention_days = 30
        
        # Log storage
        self.log_entries: List[LogEntry] = []
        self.log_lock = threading.RLock()
        
        # Log files by category
        self.log_files: Dict[LogCategory, Path] = {}
        self.loggers: Dict[LogCategory, logging.Logger] = {}
        
        # Initialize dependencies
        self.json_handler = JSONHandler(str(self.base_path))
        self.cloud_detector = CloudDetector()
        
        # Platform info
        self.platform_info = self.cloud_detector.detect_platform()
        self.session_id = f"session_{int(datetime.now().timestamp())}"
        
        # Log analyzer
        self.log_analyzer = LogAnalyzer(self)
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[callable]] = {
            'log_entry_added': [],
            'error_logged': [],
            'critical_logged': [],
            'log_rotated': []
        }
        
        # Initialize logging system
        self._setup_logging_infrastructure()
        
        # Log system startup
        self.log_info("LoggingSystem", "Logging system initialized", 
                     metadata={'platform': self.platform_info.platform.value})
        
        print(f"[LoggingSystem] Initialized for platform: {self.platform_info.platform}")
        print(f"[LoggingSystem] Log storage: {self.logs_storage_path}")
    
    def log_debug(self, component: str, message: str, app_name: str = None,
                 category: LogCategory = LogCategory.SYSTEM, **metadata) -> None:
        """Log a debug message."""
        self._log(LogLevel.DEBUG, category, component, message, app_name, metadata)
    
    def log_info(self, component: str, message: str, app_name: str = None,
                category: LogCategory = LogCategory.SYSTEM, **metadata) -> None:
        """Log an info message."""
        self._log(LogLevel.INFO, category, component, message, app_name, metadata)
    
    def log_warning(self, component: str, message: str, app_name: str = None,
                   category: LogCategory = LogCategory.SYSTEM, **metadata) -> None:
        """Log a warning message."""
        self._log(LogLevel.WARNING, category, component, message, app_name, metadata)
    
    def log_error(self, component: str, message: str, app_name: str = None,
                 category: LogCategory = LogCategory.ERROR, stack_trace: str = None, **metadata) -> None:
        """Log an error message."""
        self._log(LogLevel.ERROR, category, component, message, app_name, metadata, stack_trace)
    
    def log_critical(self, component: str, message: str, app_name: str = None,
                    category: LogCategory = LogCategory.ERROR, stack_trace: str = None, **metadata) -> None:
        """Log a critical message."""
        self._log(LogLevel.CRITICAL, category, component, message, app_name, metadata, stack_trace)
    
    def get_logs(self, start_time: datetime = None, end_time: datetime = None,
                level: LogLevel = None, category: LogCategory = None,
                component: str = None, app_name: str = None) -> List[LogEntry]:
        """
        Get logs with optional filtering.
        
        Args:
            start_time: Start time for log retrieval
            end_time: End time for log retrieval
            level: Filter by log level
            category: Filter by log category
            component: Filter by component
            app_name: Filter by application name
        
        Returns:
            List[LogEntry]: Filtered log entries
        """
        try:
            with self.log_lock:
                filtered_logs = self.log_entries.copy()
            
            # Apply filters
            if start_time:
                filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]
            
            if end_time:
                filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]
            
            if level:
                filtered_logs = [log for log in filtered_logs if log.level == level]
            
            if category:
                filtered_logs = [log for log in filtered_logs if log.category == category]
            
            if component:
                filtered_logs = [log for log in filtered_logs if log.component == component]
            
            if app_name:
                filtered_logs = [log for log in filtered_logs if log.app_name == app_name]
            
            return filtered_logs
            
        except Exception as e:
            print(f"[LoggingSystem] Error getting logs: {e}")
            return []
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive logging statistics.
        
        Returns:
            Dict[str, Any]: Logging statistics
        """
        try:
            with self.log_lock:
                total_logs = len(self.log_entries)
                
                if total_logs == 0:
                    return {'total_logs': 0}
                
                # Count by level
                level_counts = {}
                for level in LogLevel:
                    level_counts[level.value] = len([log for log in self.log_entries if log.level == level])
                
                # Count by category
                category_counts = {}
                for category in LogCategory:
                    category_counts[category.value] = len([log for log in self.log_entries if log.category == category])
                
                # Count by component
                component_counts = {}
                for log in self.log_entries:
                    component = log.component
                    if component not in component_counts:
                        component_counts[component] = 0
                    component_counts[component] += 1
                
                # Recent activity (last hour)
                recent_cutoff = datetime.now() - timedelta(hours=1)
                recent_logs = [log for log in self.log_entries if log.timestamp >= recent_cutoff]
                
                # Calculate log rate
                if self.log_entries:
                    time_span = (self.log_entries[-1].timestamp - self.log_entries[0].timestamp).total_seconds()
                    log_rate = total_logs / (time_span / 60) if time_span > 0 else 0  # logs per minute
                else:
                    log_rate = 0
                
                stats = {
                    'timestamp': datetime.now().isoformat(),
                    'total_logs': total_logs,
                    'level_counts': level_counts,
                    'category_counts': category_counts,
                    'component_counts': component_counts,
                    'recent_activity': {
                        'last_hour_logs': len(recent_logs),
                        'log_rate_per_minute': log_rate
                    },
                    'storage': {
                        'log_files': len(self.log_files),
                        'storage_path': str(self.logs_storage_path),
                        'retention_days': self.log_retention_days
                    },
                    'platform': self.platform_info.platform.value,
                    'session_id': self.session_id
                }
                
                return stats
                
        except Exception as e:
            print(f"[LoggingSystem] Error getting statistics: {e}")
            return {}
    
    def export_logs(self, output_path: str, format: LogFormat = LogFormat.JSON,
                   start_time: datetime = None, end_time: datetime = None) -> bool:
        """
        Export logs to a file.
        
        Args:
            output_path: Path to export logs to
            format: Export format
            start_time: Start time for export
            end_time: End time for export
        
        Returns:
            bool: True if export was successful
        """
        try:
            logs = self.get_logs(start_time, end_time)
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if format == LogFormat.JSON:
                # Export as JSON
                export_data = {
                    'exported_at': datetime.now().isoformat(),
                    'log_count': len(logs),
                    'logs': [log.to_dict() for log in logs]
                }
                
                self.json_handler.write_json_file(str(output_file), export_data)
                
            elif format == LogFormat.STRUCTURED:
                # Export as structured text
                with open(output_file, 'w') as f:
                    f.write(f"# PinokioCloud Log Export\n")
                    f.write(f"# Exported at: {datetime.now().isoformat()}\n")
                    f.write(f"# Total logs: {len(logs)}\n\n")
                    
                    for log in logs:
                        f.write(f"[{log.timestamp.isoformat()}] {log.level.value} "
                               f"{log.category.value} {log.component}: {log.message}\n")
                        if log.app_name:
                            f.write(f"  App: {log.app_name}\n")
                        if log.metadata:
                            f.write(f"  Metadata: {json.dumps(log.metadata)}\n")
                        f.write("\n")
            
            else:
                # Export as minimal format
                with open(output_file, 'w') as f:
                    for log in logs:
                        f.write(f"{log.timestamp.isoformat()} {log.level.value} {log.message}\n")
            
            print(f"[LoggingSystem] Exported {len(logs)} logs to {output_path}")
            return True
            
        except Exception as e:
            print(f"[LoggingSystem] Error exporting logs: {e}")
            return False
    
    def cleanup_old_logs(self) -> int:
        """
        Clean up old log files based on retention policy.
        
        Returns:
            int: Number of files cleaned up
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.log_retention_days)
            cleaned_count = 0
            
            # Clean up log files
            for log_file in self.logs_storage_path.rglob("*.log*"):
                try:
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        log_file.unlink()
                        cleaned_count += 1
                except Exception:
                    continue
            
            # Clean up old log entries from memory
            with self.log_lock:
                original_count = len(self.log_entries)
                self.log_entries = [log for log in self.log_entries if log.timestamp >= cutoff_date]
                memory_cleaned = original_count - len(self.log_entries)
            
            if cleaned_count > 0 or memory_cleaned > 0:
                print(f"[LoggingSystem] Cleaned up {cleaned_count} files, {memory_cleaned} memory entries")
                self._emit_event('log_rotated', cleaned_count, memory_cleaned)
            
            return cleaned_count
            
        except Exception as e:
            print(f"[LoggingSystem] Error cleaning up logs: {e}")
            return 0
    
    def _log(self, level: LogLevel, category: LogCategory, component: str, 
            message: str, app_name: Optional[str] = None, 
            metadata: Dict[str, Any] = None, stack_trace: Optional[str] = None) -> None:
        """Internal logging method."""
        try:
            # Create log entry
            log_entry = LogEntry(
                timestamp=datetime.now(),
                level=level,
                category=category,
                component=component,
                message=message,
                app_name=app_name,
                session_id=self.session_id,
                metadata=metadata or {},
                stack_trace=stack_trace
            )
            
            # Add to memory storage
            with self.log_lock:
                self.log_entries.append(log_entry)
                
                # Keep memory storage reasonable
                if len(self.log_entries) > 10000:
                    self.log_entries = self.log_entries[-5000:]  # Keep last 5000
            
            # Write to appropriate log file
            self._write_to_log_file(log_entry)
            
            # Emit events
            self._emit_event('log_entry_added', log_entry)
            
            if level == LogLevel.ERROR:
                self._emit_event('error_logged', log_entry)
            elif level == LogLevel.CRITICAL:
                self._emit_event('critical_logged', log_entry)
            
        except Exception as e:
            print(f"[LoggingSystem] Error in logging: {e}")
    
    def _setup_logging_infrastructure(self) -> None:
        """Set up logging infrastructure."""
        try:
            # Create log files for each category
            for category in LogCategory:
                log_file_path = self.logs_storage_path / f"{category.value}.log"
                self.log_files[category] = log_file_path
                
                # Set up rotating file handler
                logger = logging.getLogger(f"pinokio_{category.value}")
                logger.setLevel(logging.DEBUG)
                
                # Remove existing handlers
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)
                
                # Add rotating file handler
                handler = RotatingFileHandler(
                    str(log_file_path),
                    maxBytes=self.max_log_size_mb * 1024 * 1024,
                    backupCount=self.max_log_files
                )
                
                # Set format based on configuration
                if self.log_format == LogFormat.JSON:
                    formatter = logging.Formatter('{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s"}')
                else:
                    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                
                self.loggers[category] = logger
            
            print("[LoggingSystem] Logging infrastructure set up")
            
        except Exception as e:
            print(f"[LoggingSystem] Error setting up logging infrastructure: {e}")
    
    def _write_to_log_file(self, log_entry: LogEntry) -> None:
        """Write log entry to appropriate log file."""
        try:
            logger = self.loggers.get(log_entry.category)
            if logger:
                # Format message with metadata
                if log_entry.metadata or log_entry.app_name:
                    extra_info = []
                    if log_entry.app_name:
                        extra_info.append(f"app={log_entry.app_name}")
                    if log_entry.metadata:
                        extra_info.append(f"metadata={json.dumps(log_entry.metadata)}")
                    
                    formatted_message = f"{log_entry.component}: {log_entry.message} [{', '.join(extra_info)}]"
                else:
                    formatted_message = f"{log_entry.component}: {log_entry.message}"
                
                # Log at appropriate level
                if log_entry.level == LogLevel.DEBUG:
                    logger.debug(formatted_message)
                elif log_entry.level == LogLevel.INFO:
                    logger.info(formatted_message)
                elif log_entry.level == LogLevel.WARNING:
                    logger.warning(formatted_message)
                elif log_entry.level == LogLevel.ERROR:
                    logger.error(formatted_message)
                elif log_entry.level == LogLevel.CRITICAL:
                    logger.critical(formatted_message)
                    
        except Exception as e:
            print(f"[LoggingSystem] Error writing to log file: {e}")
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[LoggingSystem] Error in event callback: {e}")
    
    def add_event_callback(self, event: str, callback: callable) -> None:
        """Add a callback for logging events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)


def main():
    """Test the logging system functionality."""
    print("Testing LoggingSystem...")
    
    logging_system = LoggingSystem()
    
    # Test different log levels
    logging_system.log_debug("TestComponent", "Debug message for testing")
    logging_system.log_info("TestComponent", "Info message for testing")
    logging_system.log_warning("TestComponent", "Warning message for testing")
    logging_system.log_error("TestComponent", "Error message for testing")
    
    # Test with metadata
    logging_system.log_info("TestComponent", "Test with metadata", 
                           app_name="test_app", 
                           metadata={"test_key": "test_value"})
    
    # Get logs
    all_logs = logging_system.get_logs()
    print(f"Total logs: {len(all_logs)}")
    
    # Get statistics
    stats = logging_system.get_log_statistics()
    print(f"Log statistics: {stats['total_logs']} total logs")
    
    # Test log analysis
    analysis = logging_system.log_analyzer.analyze_logs(hours=1)
    print(f"Log analysis: {analysis.summary}")
    
    # Test export
    export_path = "/tmp/test_logs.json"
    success = logging_system.export_logs(export_path, LogFormat.JSON)
    print(f"Log export successful: {success}")
    
    # Cleanup
    cleaned = logging_system.cleanup_old_logs()
    print(f"Cleaned up {cleaned} old log files")
    
    print("LoggingSystem test completed")


if __name__ == "__main__":
    main()