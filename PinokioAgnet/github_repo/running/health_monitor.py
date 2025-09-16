#!/usr/bin/env python3
"""
PinokioCloud Health Monitor

This module monitors application health and automatically restarts crashed applications.
It provides comprehensive health monitoring with configurable checks, automatic recovery,
and detailed health reporting for all Pinokio applications.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import psutil
import threading
import requests
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import socket
import subprocess

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from environment_management.json_handler import JSONHandler
from environment_management.file_system import FileSystemManager


class HealthStatus(Enum):
    """Enumeration of health statuses."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    RECOVERING = "recovering"


class HealthCheckType(Enum):
    """Types of health checks."""
    PROCESS = "process"
    HTTP = "http"
    TCP = "tcp"
    LOG = "log"
    RESOURCE = "resource"
    CUSTOM = "custom"


@dataclass
class HealthCheck:
    """Configuration for a health check."""
    check_type: HealthCheckType
    name: str
    enabled: bool = True
    interval: float = 30.0  # seconds
    timeout: float = 10.0   # seconds
    retries: int = 3
    failure_threshold: int = 3
    success_threshold: int = 1
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert HealthCheck to dictionary."""
        data = asdict(self)
        data['check_type'] = self.check_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthCheck':
        """Create HealthCheck from dictionary."""
        data['check_type'] = HealthCheckType(data['check_type'])
        return cls(**data)


@dataclass
class HealthResult:
    """Result of a health check."""
    check_name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    response_time: float = 0.0  # seconds
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert HealthResult to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HealthResult':
        """Create HealthResult from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['status'] = HealthStatus(data['status'])
        return cls(**data)


@dataclass
class ApplicationHealth:
    """Overall health information for an application."""
    app_name: str
    overall_status: HealthStatus
    pid: Optional[int]
    last_check: datetime
    checks: Dict[str, HealthResult] = field(default_factory=dict)
    failure_count: int = 0
    success_count: int = 0
    restart_count: int = 0
    max_restarts: int = 5
    auto_restart: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ApplicationHealth to dictionary."""
        data = asdict(self)
        data['last_check'] = self.last_check.isoformat()
        data['overall_status'] = self.overall_status.value
        data['checks'] = {k: v.to_dict() for k, v in self.checks.items()}
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationHealth':
        """Create ApplicationHealth from dictionary."""
        data['last_check'] = datetime.fromisoformat(data['last_check'])
        data['overall_status'] = HealthStatus(data['overall_status'])
        data['checks'] = {k: HealthResult.from_dict(v) for k, v in data['checks'].items()}
        return cls(**data)


class HealthMonitor:
    """
    Monitors application health and automatically restarts crashed applications.
    
    This class provides comprehensive health monitoring with multiple check types,
    automatic recovery, and detailed health reporting.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the health monitor."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.health_storage_path = self.base_path / "health_storage"
        self.health_storage_path.mkdir(exist_ok=True)
        
        # Application monitoring
        self.monitored_apps: Dict[str, ApplicationHealth] = {}
        self.health_checks: Dict[str, Dict[str, HealthCheck]] = {}
        self.monitor_lock = threading.RLock()
        
        # Monitoring thread
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 10.0  # seconds
        
        # Initialize dependencies
        self.json_handler = JSONHandler(str(self.base_path))
        self.file_system = FileSystemManager(str(self.base_path))
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            'health_changed': [],
            'app_unhealthy': [],
            'app_recovered': [],
            'restart_triggered': [],
            'restart_failed': []
        }
        
        # Default health checks
        self._setup_default_health_checks()
        
        # Load existing configurations
        self._load_health_configs()
        
        print(f"[HealthMonitor] Initialized with storage at: {self.health_storage_path}")
    
    def start_monitoring(self, app_name: str, pid: int, 
                        health_checks: Optional[List[HealthCheck]] = None) -> None:
        """
        Start monitoring an application.
        
        Args:
            app_name: Name of the application to monitor
            pid: Process ID of the application
            health_checks: Optional custom health checks
        """
        print(f"[HealthMonitor] Starting monitoring for app: {app_name} (PID: {pid})")
        
        with self.monitor_lock:
            # Create application health record
            app_health = ApplicationHealth(
                app_name=app_name,
                overall_status=HealthStatus.UNKNOWN,
                pid=pid,
                last_check=datetime.now()
            )
            
            self.monitored_apps[app_name] = app_health
            
            # Set up health checks
            if health_checks:
                self.health_checks[app_name] = {check.name: check for check in health_checks}
            else:
                # Use default health checks
                self.health_checks[app_name] = self._get_default_health_checks(app_name, pid)
            
            # Save configuration
            self._save_health_config(app_name)
            
            # Start monitoring thread if not already active
            if not self.monitoring_active:
                self._start_monitoring_thread()
    
    def stop_monitoring(self, app_name: str) -> None:
        """
        Stop monitoring an application.
        
        Args:
            app_name: Name of the application to stop monitoring
        """
        print(f"[HealthMonitor] Stopping monitoring for app: {app_name}")
        
        with self.monitor_lock:
            if app_name in self.monitored_apps:
                del self.monitored_apps[app_name]
            
            if app_name in self.health_checks:
                del self.health_checks[app_name]
            
            # Remove configuration
            self._remove_health_config(app_name)
    
    def check_application_health(self, app_name: str) -> HealthStatus:
        """
        Check the health of a specific application.
        
        Args:
            app_name: Name of the application
        
        Returns:
            HealthStatus: Current health status
        """
        if app_name not in self.monitored_apps:
            return HealthStatus.UNKNOWN
        
        app_health = self.monitored_apps[app_name]
        health_checks = self.health_checks.get(app_name, {})
        
        # Perform all health checks
        check_results = {}
        overall_healthy = True
        overall_critical = False
        
        for check_name, health_check in health_checks.items():
            if not health_check.enabled:
                continue
            
            try:
                result = self._perform_health_check(health_check, app_health.pid)
                check_results[check_name] = result
                
                # Evaluate overall health
                if result.status in [HealthStatus.CRITICAL, HealthStatus.UNHEALTHY]:
                    overall_healthy = False
                    if result.status == HealthStatus.CRITICAL:
                        overall_critical = True
                elif result.status == HealthStatus.DEGRADED:
                    overall_healthy = False
                
            except Exception as e:
                # Health check failed
                result = HealthResult(
                    check_name=check_name,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {e}",
                    timestamp=datetime.now()
                )
                check_results[check_name] = result
                overall_healthy = False
                overall_critical = True
        
        # Determine overall status
        if overall_critical:
            new_status = HealthStatus.CRITICAL
        elif not overall_healthy:
            new_status = HealthStatus.UNHEALTHY
        elif any(r.status == HealthStatus.DEGRADED for r in check_results.values()):
            new_status = HealthStatus.DEGRADED
        else:
            new_status = HealthStatus.HEALTHY
        
        # Update application health
        old_status = app_health.overall_status
        app_health.overall_status = new_status
        app_health.last_check = datetime.now()
        app_health.checks = check_results
        
        # Update counters
        if new_status in [HealthStatus.CRITICAL, HealthStatus.UNHEALTHY]:
            app_health.failure_count += 1
            app_health.success_count = 0
        else:
            app_health.success_count += 1
            if app_health.failure_count > 0:
                app_health.failure_count = max(0, app_health.failure_count - 1)
        
        # Emit events if status changed
        if old_status != new_status:
            self._emit_event('health_changed', app_name, old_status, new_status)
            
            if new_status in [HealthStatus.CRITICAL, HealthStatus.UNHEALTHY]:
                self._emit_event('app_unhealthy', app_name, new_status)
            elif old_status in [HealthStatus.CRITICAL, HealthStatus.UNHEALTHY]:
                self._emit_event('app_recovered', app_name, new_status)
        
        # Save updated health state
        self._save_health_config(app_name)
        
        return new_status
    
    def auto_restart_failed_apps(self) -> List[str]:
        """
        Automatically restart failed applications.
        
        Returns:
            List[str]: List of application names that were restarted
        """
        restarted_apps = []
        
        with self.monitor_lock:
            for app_name, app_health in self.monitored_apps.items():
                # Check if app needs restart
                if (app_health.overall_status == HealthStatus.CRITICAL and
                    app_health.auto_restart and
                    app_health.restart_count < app_health.max_restarts and
                    app_health.failure_count >= 3):  # Multiple consecutive failures
                    
                    try:
                        # Attempt restart
                        success = self._restart_application(app_name, app_health)
                        
                        if success:
                            restarted_apps.append(app_name)
                            app_health.restart_count += 1
                            app_health.failure_count = 0
                            app_health.overall_status = HealthStatus.RECOVERING
                            
                            self._emit_event('restart_triggered', app_name)
                            print(f"[HealthMonitor] Successfully restarted {app_name}")
                        else:
                            self._emit_event('restart_failed', app_name)
                            print(f"[HealthMonitor] Failed to restart {app_name}")
                    
                    except Exception as e:
                        print(f"[HealthMonitor] Error restarting {app_name}: {e}")
                        self._emit_event('restart_failed', app_name)
        
        return restarted_apps
    
    def get_application_health(self, app_name: str) -> Optional[ApplicationHealth]:
        """
        Get health information for an application.
        
        Args:
            app_name: Name of the application
        
        Returns:
            Optional[ApplicationHealth]: Health information if monitored
        """
        return self.monitored_apps.get(app_name)
    
    def get_all_application_health(self) -> Dict[str, ApplicationHealth]:
        """
        Get health information for all monitored applications.
        
        Returns:
            Dict[str, ApplicationHealth]: Health information for all apps
        """
        with self.monitor_lock:
            return self.monitored_apps.copy()
    
    def set_health_check_interval(self, seconds: float) -> None:
        """
        Set the health check interval.
        
        Args:
            seconds: Interval in seconds between health checks
        """
        self.monitoring_interval = seconds
        print(f"[HealthMonitor] Set health check interval to {seconds} seconds")
    
    def add_custom_health_check(self, app_name: str, health_check: HealthCheck) -> None:
        """
        Add a custom health check for an application.
        
        Args:
            app_name: Name of the application
            health_check: Custom health check configuration
        """
        if app_name not in self.health_checks:
            self.health_checks[app_name] = {}
        
        self.health_checks[app_name][health_check.name] = health_check
        self._save_health_config(app_name)
        
        print(f"[HealthMonitor] Added custom health check '{health_check.name}' for {app_name}")
    
    def remove_health_check(self, app_name: str, check_name: str) -> bool:
        """
        Remove a health check for an application.
        
        Args:
            app_name: Name of the application
            check_name: Name of the health check to remove
        
        Returns:
            bool: True if removed successfully
        """
        if (app_name in self.health_checks and 
            check_name in self.health_checks[app_name]):
            
            del self.health_checks[app_name][check_name]
            self._save_health_config(app_name)
            
            print(f"[HealthMonitor] Removed health check '{check_name}' for {app_name}")
            return True
        
        return False
    
    def add_event_callback(self, event: str, callback: Callable) -> None:
        """Add a callback for health events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def _perform_health_check(self, health_check: HealthCheck, pid: Optional[int]) -> HealthResult:
        """Perform a specific health check."""
        start_time = time.time()
        
        try:
            if health_check.check_type == HealthCheckType.PROCESS:
                return self._check_process_health(health_check, pid)
            elif health_check.check_type == HealthCheckType.HTTP:
                return self._check_http_health(health_check)
            elif health_check.check_type == HealthCheckType.TCP:
                return self._check_tcp_health(health_check)
            elif health_check.check_type == HealthCheckType.LOG:
                return self._check_log_health(health_check)
            elif health_check.check_type == HealthCheckType.RESOURCE:
                return self._check_resource_health(health_check, pid)
            elif health_check.check_type == HealthCheckType.CUSTOM:
                return self._check_custom_health(health_check, pid)
            else:
                return HealthResult(
                    check_name=health_check.name,
                    status=HealthStatus.UNKNOWN,
                    message=f"Unknown check type: {health_check.check_type}",
                    timestamp=datetime.now(),
                    response_time=time.time() - start_time
                )
        
        except Exception as e:
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.CRITICAL,
                message=f"Health check error: {e}",
                timestamp=datetime.now(),
                response_time=time.time() - start_time
            )
    
    def _check_process_health(self, health_check: HealthCheck, pid: Optional[int]) -> HealthResult:
        """Check process-based health."""
        if pid is None:
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.CRITICAL,
                message="No PID available",
                timestamp=datetime.now()
            )
        
        try:
            process = psutil.Process(pid)
            
            if not process.is_running():
                return HealthResult(
                    check_name=health_check.name,
                    status=HealthStatus.CRITICAL,
                    message="Process not running",
                    timestamp=datetime.now()
                )
            
            if process.status() == psutil.STATUS_ZOMBIE:
                return HealthResult(
                    check_name=health_check.name,
                    status=HealthStatus.CRITICAL,
                    message="Process is zombie",
                    timestamp=datetime.now()
                )
            
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.HEALTHY,
                message="Process running normally",
                timestamp=datetime.now(),
                details={
                    'pid': pid,
                    'status': process.status(),
                    'cpu_percent': process.cpu_percent(),
                    'memory_percent': process.memory_percent()
                }
            )
        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.CRITICAL,
                message="Process not found or access denied",
                timestamp=datetime.now()
            )
    
    def _check_http_health(self, health_check: HealthCheck) -> HealthResult:
        """Check HTTP endpoint health."""
        url = health_check.config.get('url', 'http://localhost:7860')
        expected_status = health_check.config.get('expected_status', 200)
        
        try:
            response = requests.get(url, timeout=health_check.timeout)
            
            if response.status_code == expected_status:
                return HealthResult(
                    check_name=health_check.name,
                    status=HealthStatus.HEALTHY,
                    message=f"HTTP endpoint responding (status: {response.status_code})",
                    timestamp=datetime.now(),
                    details={'status_code': response.status_code, 'url': url}
                )
            else:
                return HealthResult(
                    check_name=health_check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"HTTP endpoint returned status {response.status_code}, expected {expected_status}",
                    timestamp=datetime.now(),
                    details={'status_code': response.status_code, 'url': url}
                )
        
        except requests.exceptions.RequestException as e:
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.CRITICAL,
                message=f"HTTP check failed: {e}",
                timestamp=datetime.now(),
                details={'url': url, 'error': str(e)}
            )
    
    def _check_tcp_health(self, health_check: HealthCheck) -> HealthResult:
        """Check TCP port health."""
        host = health_check.config.get('host', 'localhost')
        port = health_check.config.get('port', 7860)
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(health_check.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return HealthResult(
                    check_name=health_check.name,
                    status=HealthStatus.HEALTHY,
                    message=f"TCP port {port} is open",
                    timestamp=datetime.now(),
                    details={'host': host, 'port': port}
                )
            else:
                return HealthResult(
                    check_name=health_check.name,
                    status=HealthStatus.CRITICAL,
                    message=f"TCP port {port} is not accessible",
                    timestamp=datetime.now(),
                    details={'host': host, 'port': port}
                )
        
        except Exception as e:
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.CRITICAL,
                message=f"TCP check failed: {e}",
                timestamp=datetime.now(),
                details={'host': host, 'port': port, 'error': str(e)}
            )
    
    def _check_log_health(self, health_check: HealthCheck) -> HealthResult:
        """Check log file health."""
        log_file = health_check.config.get('log_file')
        error_patterns = health_check.config.get('error_patterns', ['error', 'exception', 'failed'])
        max_errors = health_check.config.get('max_errors', 5)
        
        if not log_file or not os.path.exists(log_file):
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.UNKNOWN,
                message="Log file not found or not specified",
                timestamp=datetime.now()
            )
        
        try:
            with open(log_file, 'r') as f:
                # Read last 100 lines
                lines = f.readlines()[-100:]
                
                # Count errors in recent lines
                error_count = 0
                for line in lines:
                    if any(pattern.lower() in line.lower() for pattern in error_patterns):
                        error_count += 1
                
                if error_count == 0:
                    status = HealthStatus.HEALTHY
                    message = "No errors found in recent logs"
                elif error_count <= max_errors:
                    status = HealthStatus.DEGRADED
                    message = f"Found {error_count} errors in recent logs"
                else:
                    status = HealthStatus.UNHEALTHY
                    message = f"Found {error_count} errors in recent logs (threshold: {max_errors})"
                
                return HealthResult(
                    check_name=health_check.name,
                    status=status,
                    message=message,
                    timestamp=datetime.now(),
                    details={'error_count': error_count, 'log_file': log_file}
                )
        
        except Exception as e:
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.UNKNOWN,
                message=f"Error reading log file: {e}",
                timestamp=datetime.now(),
                details={'log_file': log_file, 'error': str(e)}
            )
    
    def _check_resource_health(self, health_check: HealthCheck, pid: Optional[int]) -> HealthResult:
        """Check resource usage health."""
        if pid is None:
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.CRITICAL,
                message="No PID available for resource check",
                timestamp=datetime.now()
            )
        
        cpu_threshold = health_check.config.get('cpu_threshold', 90.0)
        memory_threshold = health_check.config.get('memory_threshold', 90.0)
        
        try:
            process = psutil.Process(pid)
            cpu_percent = process.cpu_percent()
            memory_percent = process.memory_percent()
            
            issues = []
            if cpu_percent > cpu_threshold:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory_percent > memory_threshold:
                issues.append(f"High memory usage: {memory_percent:.1f}%")
            
            if issues:
                return HealthResult(
                    check_name=health_check.name,
                    status=HealthStatus.DEGRADED,
                    message="; ".join(issues),
                    timestamp=datetime.now(),
                    details={
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory_percent,
                        'cpu_threshold': cpu_threshold,
                        'memory_threshold': memory_threshold
                    }
                )
            else:
                return HealthResult(
                    check_name=health_check.name,
                    status=HealthStatus.HEALTHY,
                    message="Resource usage within normal limits",
                    timestamp=datetime.now(),
                    details={
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory_percent
                    }
                )
        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.CRITICAL,
                message="Process not found for resource check",
                timestamp=datetime.now()
            )
    
    def _check_custom_health(self, health_check: HealthCheck, pid: Optional[int]) -> HealthResult:
        """Check custom health using a script or command."""
        command = health_check.config.get('command')
        if not command:
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.UNKNOWN,
                message="No command specified for custom health check",
                timestamp=datetime.now()
            )
        
        try:
            # Replace PID placeholder if present
            if pid:
                command = command.replace('{{PID}}', str(pid))
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=health_check.timeout
            )
            
            if result.returncode == 0:
                return HealthResult(
                    check_name=health_check.name,
                    status=HealthStatus.HEALTHY,
                    message="Custom health check passed",
                    timestamp=datetime.now(),
                    details={
                        'command': command,
                        'stdout': result.stdout.strip(),
                        'stderr': result.stderr.strip()
                    }
                )
            else:
                return HealthResult(
                    check_name=health_check.name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Custom health check failed (exit code: {result.returncode})",
                    timestamp=datetime.now(),
                    details={
                        'command': command,
                        'exit_code': result.returncode,
                        'stdout': result.stdout.strip(),
                        'stderr': result.stderr.strip()
                    }
                )
        
        except subprocess.TimeoutExpired:
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.CRITICAL,
                message="Custom health check timed out",
                timestamp=datetime.now(),
                details={'command': command, 'timeout': health_check.timeout}
            )
        except Exception as e:
            return HealthResult(
                check_name=health_check.name,
                status=HealthStatus.CRITICAL,
                message=f"Custom health check error: {e}",
                timestamp=datetime.now(),
                details={'command': command, 'error': str(e)}
            )
    
    def _setup_default_health_checks(self) -> None:
        """Set up default health check configurations."""
        self.default_checks = {
            'process': HealthCheck(
                check_type=HealthCheckType.PROCESS,
                name='process_check',
                interval=30.0
            ),
            'resource': HealthCheck(
                check_type=HealthCheckType.RESOURCE,
                name='resource_check',
                interval=60.0,
                config={'cpu_threshold': 90.0, 'memory_threshold': 85.0}
            )
        }
    
    def _get_default_health_checks(self, app_name: str, pid: int) -> Dict[str, HealthCheck]:
        """Get default health checks for an application."""
        checks = {}
        
        # Always include process check
        checks['process_check'] = HealthCheck(
            check_type=HealthCheckType.PROCESS,
            name='process_check',
            interval=30.0
        )
        
        # Include resource check
        checks['resource_check'] = HealthCheck(
            check_type=HealthCheckType.RESOURCE,
            name='resource_check',
            interval=60.0,
            config={'cpu_threshold': 90.0, 'memory_threshold': 85.0}
        )
        
        # Try to detect web interface and add HTTP check
        common_ports = [7860, 7861, 8000, 8080, 5000, 3000]
        for port in common_ports:
            if self._is_port_open('localhost', port):
                checks[f'http_check_{port}'] = HealthCheck(
                    check_type=HealthCheckType.HTTP,
                    name=f'http_check_{port}',
                    interval=45.0,
                    config={'url': f'http://localhost:{port}', 'expected_status': 200}
                )
                break
        
        return checks
    
    def _is_port_open(self, host: str, port: int) -> bool:
        """Check if a port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _restart_application(self, app_name: str, app_health: ApplicationHealth) -> bool:
        """Restart an application (placeholder - would integrate with ScriptManager)."""
        # This would typically call the ScriptManager to restart the application
        # For now, this is a placeholder that simulates restart logic
        
        print(f"[HealthMonitor] Attempting to restart application: {app_name}")
        
        # In a real implementation, this would:
        # 1. Call script_manager.restart_application(app_name)
        # 2. Update the PID in app_health
        # 3. Reset health status
        
        # Placeholder logic
        time.sleep(2.0)  # Simulate restart time
        
        # For now, just mark as recovering
        app_health.overall_status = HealthStatus.RECOVERING
        
        return True  # Simulate successful restart
    
    def _start_monitoring_thread(self) -> None:
        """Start the monitoring thread."""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            print("[HealthMonitor] Started health monitoring thread")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Check health of all monitored applications
                with self.monitor_lock:
                    for app_name in list(self.monitored_apps.keys()):
                        self.check_application_health(app_name)
                
                # Perform auto-restart if needed
                self.auto_restart_failed_apps()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"[HealthMonitor] Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _save_health_config(self, app_name: str) -> None:
        """Save health configuration to disk."""
        if app_name not in self.monitored_apps:
            return
        
        config_file = self.health_storage_path / f"{app_name}_health.json"
        try:
            config_data = {
                'app_health': self.monitored_apps[app_name].to_dict(),
                'health_checks': {k: v.to_dict() for k, v in self.health_checks.get(app_name, {}).items()}
            }
            self.json_handler.write_json_file(str(config_file), config_data)
        except Exception as e:
            print(f"[HealthMonitor] Error saving health config for {app_name}: {e}")
    
    def _load_health_configs(self) -> None:
        """Load existing health configurations."""
        try:
            for config_file in self.health_storage_path.glob("*_health.json"):
                try:
                    config_data = self.json_handler.read_json_file(str(config_file))
                    
                    app_health = ApplicationHealth.from_dict(config_data['app_health'])
                    health_checks = {k: HealthCheck.from_dict(v) 
                                   for k, v in config_data.get('health_checks', {}).items()}
                    
                    app_name = app_health.app_name
                    
                    # Only restore if process is still alive
                    if app_health.pid and self._is_process_alive(app_health.pid):
                        self.monitored_apps[app_name] = app_health
                        self.health_checks[app_name] = health_checks
                        print(f"[HealthMonitor] Restored health monitoring for: {app_name}")
                    else:
                        # Remove stale config
                        config_file.unlink()
                        
                except Exception as e:
                    print(f"[HealthMonitor] Error loading health config {config_file}: {e}")
                    
        except Exception as e:
            print(f"[HealthMonitor] Error loading health configs: {e}")
    
    def _remove_health_config(self, app_name: str) -> None:
        """Remove health configuration from disk."""
        config_file = self.health_storage_path / f"{app_name}_health.json"
        try:
            if config_file.exists():
                config_file.unlink()
        except Exception as e:
            print(f"[HealthMonitor] Error removing health config for {app_name}: {e}")
    
    def _is_process_alive(self, pid: int) -> bool:
        """Check if a process is alive."""
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[HealthMonitor] Error in event callback: {e}")
    
    def stop_monitoring_thread(self) -> None:
        """Stop the monitoring thread."""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        print("[HealthMonitor] Stopped health monitoring thread")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_monitoring_thread()


def main():
    """Test the health monitor functionality."""
    print("Testing HealthMonitor...")
    
    health_monitor = HealthMonitor()
    
    # Test monitoring current process
    current_pid = os.getpid()
    health_monitor.start_monitoring("test_app", current_pid)
    
    # Wait for health checks
    time.sleep(5)
    
    # Check health
    health_status = health_monitor.check_application_health("test_app")
    print(f"Test app health: {health_status}")
    
    # Get detailed health info
    app_health = health_monitor.get_application_health("test_app")
    if app_health:
        print(f"Overall status: {app_health.overall_status}")
        print(f"Last check: {app_health.last_check}")
        print(f"Checks: {len(app_health.checks)}")
    
    # Cleanup
    health_monitor.stop_monitoring("test_app")
    health_monitor.stop_monitoring_thread()
    
    print("HealthMonitor test completed")


if __name__ == "__main__":
    main()