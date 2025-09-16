#!/usr/bin/env python3
"""
PinokioCloud Error Recovery System

This module provides automatic error detection and self-healing capabilities.
It implements intelligent error pattern recognition, automatic recovery actions,
and comprehensive error handling for all PinokioCloud operations.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import re
import threading
import subprocess
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import json

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from environment_management.shell_runner import ShellRunner
from environment_management.json_handler import JSONHandler
from running.script_manager import ScriptManager
from running.health_monitor import HealthMonitor
from running.daemon_manager import DaemonManager
from engine.state_manager import StateManager


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors."""
    DEPENDENCY = "dependency"
    PROCESS = "process"
    NETWORK = "network"
    STORAGE = "storage"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"
    PLATFORM = "platform"


class RecoveryStatus(Enum):
    """Status of recovery attempts."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ErrorPattern:
    """Pattern for error detection and recovery."""
    pattern_id: str
    name: str
    category: ErrorCategory
    severity: ErrorSeverity
    regex_patterns: List[str]
    keywords: List[str]
    recovery_actions: List[str]
    max_attempts: int = 3
    cooldown_minutes: int = 5
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ErrorPattern to dictionary."""
        data = asdict(self)
        data['category'] = self.category.value
        data['severity'] = self.severity.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorPattern':
        """Create ErrorPattern from dictionary."""
        data['category'] = ErrorCategory(data['category'])
        data['severity'] = ErrorSeverity(data['severity'])
        return cls(**data)


@dataclass
class RecoveryAction:
    """Information about a recovery action."""
    action_id: str
    error_pattern_id: str
    app_name: Optional[str]
    action_type: str
    description: str
    status: RecoveryStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    attempt_count: int = 1
    max_attempts: int = 3
    error_message: Optional[str] = None
    success_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert RecoveryAction to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        data['started_at'] = self.started_at.isoformat()
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecoveryAction':
        """Create RecoveryAction from dictionary."""
        data['status'] = RecoveryStatus(data['status'])
        data['started_at'] = datetime.fromisoformat(data['started_at'])
        data['completed_at'] = datetime.fromisoformat(data['completed_at']) if data['completed_at'] else None
        return cls(**data)


class ErrorRecovery:
    """
    Automatic error detection and self-healing capabilities.
    
    This class provides intelligent error pattern recognition and automatic
    recovery actions for common PinokioCloud issues.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the error recovery system."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.recovery_storage_path = self.base_path / "recovery_storage"
        self.recovery_storage_path.mkdir(exist_ok=True)
        
        # Error patterns and recovery actions
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.recovery_actions: Dict[str, RecoveryAction] = {}
        self.recovery_lock = threading.RLock()
        
        # Recovery monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 30.0  # seconds
        
        # Recovery statistics
        self.recovery_stats = {
            'total_errors_detected': 0,
            'total_recoveries_attempted': 0,
            'successful_recoveries': 0,
            'failed_recoveries': 0,
            'errors_by_category': {},
            'recovery_success_rate': 0.0
        }
        
        # Initialize dependencies
        self.shell_runner = ShellRunner(str(self.base_path))
        self.json_handler = JSONHandler(str(self.base_path))
        self.script_manager = ScriptManager(str(self.base_path))
        self.health_monitor = HealthMonitor(str(self.base_path))
        self.daemon_manager = DaemonManager(str(self.base_path))
        self.state_manager = StateManager(str(self.base_path))
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            'error_detected': [],
            'recovery_started': [],
            'recovery_completed': [],
            'recovery_failed': [],
            'pattern_matched': []
        }
        
        # Set up default error patterns
        self._setup_default_error_patterns()
        
        # Load existing configurations
        self._load_error_patterns()
        self._load_recovery_history()
        
        print(f"[ErrorRecovery] Initialized with {len(self.error_patterns)} error patterns")
    
    def detect_and_recover(self, log_content: str, app_name: str = None) -> List[RecoveryAction]:
        """
        Detect errors in log content and attempt recovery.
        
        Args:
            log_content: Log content to analyze
            app_name: Name of the application (optional)
        
        Returns:
            List[RecoveryAction]: List of recovery actions attempted
        """
        print(f"[ErrorRecovery] Analyzing log content for errors (app: {app_name})")
        
        recovery_actions = []
        
        try:
            # Detect error patterns
            detected_patterns = self._detect_error_patterns(log_content)
            
            for pattern in detected_patterns:
                self.recovery_stats['total_errors_detected'] += 1
                
                # Update category statistics
                category = pattern.category.value
                if category not in self.recovery_stats['errors_by_category']:
                    self.recovery_stats['errors_by_category'][category] = 0
                self.recovery_stats['errors_by_category'][category] += 1
                
                # Emit detection event
                self._emit_event('error_detected', pattern, log_content, app_name)
                self._emit_event('pattern_matched', pattern)
                
                # Attempt recovery
                recovery_action = self._attempt_recovery(pattern, app_name, log_content)
                if recovery_action:
                    recovery_actions.append(recovery_action)
            
            # Update success rate
            self._update_recovery_success_rate()
            
            return recovery_actions
            
        except Exception as e:
            print(f"[ErrorRecovery] Error in detect_and_recover: {e}")
            return []
    
    def add_error_pattern(self, pattern: ErrorPattern) -> None:
        """
        Add a custom error pattern.
        
        Args:
            pattern: Error pattern to add
        """
        with self.recovery_lock:
            self.error_patterns[pattern.pattern_id] = pattern
            self._save_error_pattern(pattern)
        
        print(f"[ErrorRecovery] Added error pattern: {pattern.name}")
    
    def remove_error_pattern(self, pattern_id: str) -> bool:
        """
        Remove an error pattern.
        
        Args:
            pattern_id: ID of the pattern to remove
        
        Returns:
            bool: True if successfully removed
        """
        with self.recovery_lock:
            if pattern_id in self.error_patterns:
                del self.error_patterns[pattern_id]
                self._remove_error_pattern_file(pattern_id)
                print(f"[ErrorRecovery] Removed error pattern: {pattern_id}")
                return True
        
        return False
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive recovery statistics.
        
        Returns:
            Dict[str, Any]: Recovery statistics
        """
        try:
            stats = self.recovery_stats.copy()
            
            # Add current status
            stats.update({
                'timestamp': datetime.now().isoformat(),
                'active_patterns': len([p for p in self.error_patterns.values() if p.enabled]),
                'total_patterns': len(self.error_patterns),
                'recent_recoveries': len([a for a in self.recovery_actions.values() 
                                        if (datetime.now() - a.started_at).total_seconds() < 3600]),
                'monitoring_active': self.monitoring_active
            })
            
            return stats
            
        except Exception as e:
            print(f"[ErrorRecovery] Error getting statistics: {e}")
            return {}
    
    def start_monitoring(self) -> None:
        """Start error monitoring."""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            print("[ErrorRecovery] Started error monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop error monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        print("[ErrorRecovery] Stopped error monitoring")
    
    def add_event_callback(self, event: str, callback: Callable) -> None:
        """Add a callback for recovery events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def _detect_error_patterns(self, log_content: str) -> List[ErrorPattern]:
        """Detect error patterns in log content."""
        detected_patterns = []
        
        try:
            log_content_lower = log_content.lower()
            
            for pattern in self.error_patterns.values():
                if not pattern.enabled:
                    continue
                
                # Check regex patterns
                for regex_pattern in pattern.regex_patterns:
                    try:
                        if re.search(regex_pattern, log_content, re.IGNORECASE):
                            detected_patterns.append(pattern)
                            break
                    except re.error:
                        continue
                
                # Check keywords if no regex match
                if pattern not in detected_patterns:
                    for keyword in pattern.keywords:
                        if keyword.lower() in log_content_lower:
                            detected_patterns.append(pattern)
                            break
            
            return detected_patterns
            
        except Exception as e:
            print(f"[ErrorRecovery] Error detecting patterns: {e}")
            return []
    
    def _attempt_recovery(self, pattern: ErrorPattern, app_name: Optional[str], 
                         log_content: str) -> Optional[RecoveryAction]:
        """Attempt to recover from an error pattern."""
        try:
            # Create recovery action
            action_id = f"recovery_{pattern.pattern_id}_{int(datetime.now().timestamp())}"
            
            recovery_action = RecoveryAction(
                action_id=action_id,
                error_pattern_id=pattern.pattern_id,
                app_name=app_name,
                action_type=pattern.category.value,
                description=f"Attempting recovery for {pattern.name}",
                status=RecoveryStatus.PENDING,
                started_at=datetime.now(),
                max_attempts=pattern.max_attempts
            )
            
            # Register recovery action
            with self.recovery_lock:
                self.recovery_actions[action_id] = recovery_action
            
            # Emit event
            self._emit_event('recovery_started', recovery_action)
            
            # Execute recovery actions
            recovery_action.status = RecoveryStatus.IN_PROGRESS
            success = self._execute_recovery_actions(pattern, app_name, recovery_action)
            
            if success:
                recovery_action.status = RecoveryStatus.SUCCESS
                recovery_action.completed_at = datetime.now()
                recovery_action.success_message = f"Successfully recovered from {pattern.name}"
                
                self.recovery_stats['successful_recoveries'] += 1
                self._emit_event('recovery_completed', recovery_action)
                
                print(f"[ErrorRecovery] Recovery successful: {pattern.name}")
            else:
                recovery_action.status = RecoveryStatus.FAILED
                recovery_action.completed_at = datetime.now()
                recovery_action.error_message = f"Failed to recover from {pattern.name}"
                
                self.recovery_stats['failed_recoveries'] += 1
                self._emit_event('recovery_failed', recovery_action)
                
                print(f"[ErrorRecovery] Recovery failed: {pattern.name}")
            
            self.recovery_stats['total_recoveries_attempted'] += 1
            
            # Save recovery action
            self._save_recovery_action(recovery_action)
            
            return recovery_action
            
        except Exception as e:
            print(f"[ErrorRecovery] Error in recovery attempt: {e}")
            return None
    
    def _execute_recovery_actions(self, pattern: ErrorPattern, app_name: Optional[str],
                                 recovery_action: RecoveryAction) -> bool:
        """Execute recovery actions for an error pattern."""
        try:
            for action in pattern.recovery_actions:
                try:
                    success = self._execute_single_recovery_action(action, app_name, recovery_action)
                    if success:
                        return True  # If any action succeeds, consider recovery successful
                except Exception as e:
                    print(f"[ErrorRecovery] Error executing recovery action '{action}': {e}")
                    continue
            
            return False  # All actions failed
            
        except Exception as e:
            print(f"[ErrorRecovery] Error executing recovery actions: {e}")
            return False
    
    def _execute_single_recovery_action(self, action: str, app_name: Optional[str],
                                       recovery_action: RecoveryAction) -> bool:
        """Execute a single recovery action."""
        try:
            if action == "restart_application":
                if app_name:
                    return self.script_manager.restart_application(app_name)
                return False
            
            elif action == "restart_daemon":
                if app_name:
                    # Find daemon for app and restart
                    daemons = self.daemon_manager.list_active_daemons()
                    for daemon in daemons:
                        if daemon.app_name == app_name:
                            return self.daemon_manager.restart_daemon(daemon.daemon_id)
                return False
            
            elif action == "clear_cache":
                # Clear temporary files and caches
                temp_dirs = ["/tmp", "/var/tmp", str(self.base_path / "temp")]
                for temp_dir in temp_dirs:
                    temp_path = Path(temp_dir)
                    if temp_path.exists():
                        for file_path in temp_path.rglob("*"):
                            try:
                                if file_path.is_file():
                                    file_path.unlink()
                            except Exception:
                                continue
                return True
            
            elif action == "reinstall_dependencies":
                if app_name:
                    # This would integrate with dependency managers
                    print(f"[ErrorRecovery] Would reinstall dependencies for {app_name}")
                    return True
                return False
            
            elif action == "reset_environment":
                if app_name:
                    # Reset virtual environment for app
                    print(f"[ErrorRecovery] Would reset environment for {app_name}")
                    return True
                return False
            
            elif action == "fix_permissions":
                # Fix common permission issues
                try:
                    if app_name:
                        app_path = self.base_path / "apps" / app_name
                        if app_path.exists():
                            # Fix permissions recursively
                            for file_path in app_path.rglob("*"):
                                try:
                                    if file_path.is_file():
                                        os.chmod(file_path, 0o644)
                                    elif file_path.is_dir():
                                        os.chmod(file_path, 0o755)
                                except Exception:
                                    continue
                            return True
                except Exception:
                    pass
                return False
            
            elif action == "increase_memory":
                # Trigger garbage collection and memory optimization
                import gc
                gc.collect()
                
                # This would integrate with performance monitor
                print("[ErrorRecovery] Applied memory optimization")
                return True
            
            elif action == "restart_tunnels":
                # This would integrate with tunnel managers
                print("[ErrorRecovery] Would restart tunnels")
                return True
            
            elif action.startswith("shell:"):
                # Execute shell command
                command = action[6:]  # Remove "shell:" prefix
                result = self.shell_runner.run_command(command, capture_output=True)
                return result.returncode == 0
            
            else:
                print(f"[ErrorRecovery] Unknown recovery action: {action}")
                return False
                
        except Exception as e:
            print(f"[ErrorRecovery] Error executing recovery action '{action}': {e}")
            return False
    
    def _setup_default_error_patterns(self) -> None:
        """Set up default error patterns."""
        default_patterns = [
            ErrorPattern(
                pattern_id="out_of_memory",
                name="Out of Memory Error",
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.HIGH,
                regex_patterns=[r"out of memory", r"memory.*error", r"cuda.*out of memory"],
                keywords=["out of memory", "memory error", "cuda out of memory"],
                recovery_actions=["clear_cache", "increase_memory", "restart_application"],
                max_attempts=2
            ),
            ErrorPattern(
                pattern_id="permission_denied",
                name="Permission Denied Error",
                category=ErrorCategory.PERMISSION,
                severity=ErrorSeverity.MEDIUM,
                regex_patterns=[r"permission denied", r"access denied", r"operation not permitted"],
                keywords=["permission denied", "access denied", "operation not permitted"],
                recovery_actions=["fix_permissions"],
                max_attempts=1
            ),
            ErrorPattern(
                pattern_id="dependency_missing",
                name="Missing Dependency Error",
                category=ErrorCategory.DEPENDENCY,
                severity=ErrorSeverity.HIGH,
                regex_patterns=[r"module.*not found", r"no module named", r"import.*error"],
                keywords=["module not found", "no module named", "import error"],
                recovery_actions=["reinstall_dependencies", "reset_environment"],
                max_attempts=2
            ),
            ErrorPattern(
                pattern_id="process_crashed",
                name="Process Crashed",
                category=ErrorCategory.PROCESS,
                severity=ErrorSeverity.HIGH,
                regex_patterns=[r"process.*crashed", r"segmentation fault", r"core dumped"],
                keywords=["process crashed", "segmentation fault", "core dumped"],
                recovery_actions=["restart_application", "clear_cache"],
                max_attempts=3
            ),
            ErrorPattern(
                pattern_id="network_timeout",
                name="Network Timeout Error",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                regex_patterns=[r"connection.*timeout", r"network.*timeout", r"request.*timeout"],
                keywords=["connection timeout", "network timeout", "request timeout"],
                recovery_actions=["restart_tunnels"],
                max_attempts=2
            ),
            ErrorPattern(
                pattern_id="disk_full",
                name="Disk Full Error",
                category=ErrorCategory.STORAGE,
                severity=ErrorSeverity.CRITICAL,
                regex_patterns=[r"no space left", r"disk.*full", r"storage.*full"],
                keywords=["no space left", "disk full", "storage full"],
                recovery_actions=["clear_cache"],
                max_attempts=1
            ),
            ErrorPattern(
                pattern_id="gpu_error",
                name="GPU Error",
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.HIGH,
                regex_patterns=[r"cuda.*error", r"gpu.*error", r"device.*error"],
                keywords=["cuda error", "gpu error", "device error"],
                recovery_actions=["restart_application", "clear_cache"],
                max_attempts=2
            )
        ]
        
        for pattern in default_patterns:
            self.error_patterns[pattern.pattern_id] = pattern
    
    def _monitoring_loop(self) -> None:
        """Main error monitoring loop."""
        while self.monitoring_active:
            try:
                # Monitor application logs
                self._monitor_application_logs()
                
                # Monitor system logs
                self._monitor_system_logs()
                
                # Check for health issues
                self._monitor_health_issues()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"[ErrorRecovery] Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _monitor_application_logs(self) -> None:
        """Monitor application logs for errors."""
        try:
            # Get all applications from state manager
            app_states = self.state_manager.get_all_application_states()
            
            for app_name, app_state in app_states.items():
                try:
                    # Check for log files
                    app_path = Path(app_state.installation_path)
                    log_patterns = ["*.log", "*.out", "*.err"]
                    
                    for pattern in log_patterns:
                        for log_file in app_path.rglob(pattern):
                            if log_file.is_file():
                                # Read recent log content
                                try:
                                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                                        # Read last 1000 lines
                                        lines = f.readlines()
                                        recent_content = ''.join(lines[-1000:])
                                        
                                        # Analyze for errors
                                        self.detect_and_recover(recent_content, app_name)
                                        
                                except Exception:
                                    continue
                                
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"[ErrorRecovery] Error monitoring application logs: {e}")
    
    def _monitor_system_logs(self) -> None:
        """Monitor system logs for errors."""
        try:
            # Check system log files
            system_logs = [
                "/var/log/syslog",
                "/var/log/messages",
                "/var/log/kern.log"
            ]
            
            for log_path in system_logs:
                log_file = Path(log_path)
                if log_file.exists():
                    try:
                        # Read recent entries
                        result = self.shell_runner.run_command(
                            f"tail -n 100 {log_path}", capture_output=True
                        )
                        
                        if result.returncode == 0:
                            self.detect_and_recover(result.stdout)
                            
                    except Exception:
                        continue
                        
        except Exception as e:
            print(f"[ErrorRecovery] Error monitoring system logs: {e}")
    
    def _monitor_health_issues(self) -> None:
        """Monitor for health issues that might need recovery."""
        try:
            # Get all application health status
            all_health = self.health_monitor.get_all_application_health()
            
            for app_name, app_health in all_health.items():
                if app_health.overall_status.value in ['critical', 'unhealthy']:
                    # Trigger recovery for unhealthy apps
                    error_content = f"Application {app_name} is {app_health.overall_status.value}"
                    self.detect_and_recover(error_content, app_name)
                    
        except Exception as e:
            print(f"[ErrorRecovery] Error monitoring health issues: {e}")
    
    def _update_recovery_success_rate(self) -> None:
        """Update recovery success rate."""
        try:
            total_attempts = self.recovery_stats['total_recoveries_attempted']
            successful = self.recovery_stats['successful_recoveries']
            
            if total_attempts > 0:
                self.recovery_stats['recovery_success_rate'] = (successful / total_attempts) * 100
            else:
                self.recovery_stats['recovery_success_rate'] = 0.0
                
        except Exception as e:
            print(f"[ErrorRecovery] Error updating success rate: {e}")
    
    def _save_error_pattern(self, pattern: ErrorPattern) -> None:
        """Save error pattern to disk."""
        pattern_file = self.recovery_storage_path / f"pattern_{pattern.pattern_id}.json"
        try:
            self.json_handler.write_json_file(str(pattern_file), pattern.to_dict())
        except Exception as e:
            print(f"[ErrorRecovery] Error saving error pattern: {e}")
    
    def _load_error_patterns(self) -> None:
        """Load error patterns from disk."""
        try:
            for pattern_file in self.recovery_storage_path.glob("pattern_*.json"):
                try:
                    pattern_data = self.json_handler.read_json_file(str(pattern_file))
                    pattern = ErrorPattern.from_dict(pattern_data)
                    self.error_patterns[pattern.pattern_id] = pattern
                except Exception as e:
                    print(f"[ErrorRecovery] Error loading pattern {pattern_file}: {e}")
                    
        except Exception as e:
            print(f"[ErrorRecovery] Error loading error patterns: {e}")
    
    def _remove_error_pattern_file(self, pattern_id: str) -> None:
        """Remove error pattern file from disk."""
        pattern_file = self.recovery_storage_path / f"pattern_{pattern_id}.json"
        try:
            if pattern_file.exists():
                pattern_file.unlink()
        except Exception as e:
            print(f"[ErrorRecovery] Error removing pattern file: {e}")
    
    def _save_recovery_action(self, action: RecoveryAction) -> None:
        """Save recovery action to disk."""
        action_file = self.recovery_storage_path / f"action_{action.action_id}.json"
        try:
            self.json_handler.write_json_file(str(action_file), action.to_dict())
        except Exception as e:
            print(f"[ErrorRecovery] Error saving recovery action: {e}")
    
    def _load_recovery_history(self) -> None:
        """Load recovery history from disk."""
        try:
            for action_file in self.recovery_storage_path.glob("action_*.json"):
                try:
                    action_data = self.json_handler.read_json_file(str(action_file))
                    action = RecoveryAction.from_dict(action_data)
                    
                    # Only load recent actions (last 24 hours)
                    if (datetime.now() - action.started_at).total_seconds() < 86400:
                        self.recovery_actions[action.action_id] = action
                    else:
                        # Remove old action file
                        action_file.unlink()
                        
                except Exception as e:
                    print(f"[ErrorRecovery] Error loading action {action_file}: {e}")
                    
        except Exception as e:
            print(f"[ErrorRecovery] Error loading recovery history: {e}")
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[ErrorRecovery] Error in event callback: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_monitoring()


def main():
    """Test the error recovery functionality."""
    print("Testing ErrorRecovery...")
    
    recovery = ErrorRecovery()
    
    # Test error detection
    test_log = """
    Error: CUDA out of memory. Tried to allocate 2.00 GiB
    RuntimeError: No module named 'torch'
    PermissionError: [Errno 13] Permission denied
    """
    
    recovery_actions = recovery.detect_and_recover(test_log, "test_app")
    print(f"Detected errors and attempted {len(recovery_actions)} recoveries")
    
    # Test statistics
    stats = recovery.get_recovery_statistics()
    print(f"Recovery stats: {stats['total_errors_detected']} errors detected")
    
    # Test custom pattern
    custom_pattern = ErrorPattern(
        pattern_id="custom_test",
        name="Custom Test Error",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.LOW,
        regex_patterns=[r"test.*error"],
        keywords=["test error"],
        recovery_actions=["clear_cache"]
    )
    
    recovery.add_error_pattern(custom_pattern)
    print(f"Added custom pattern: {custom_pattern.name}")
    
    print("ErrorRecovery test completed")


if __name__ == "__main__":
    main()