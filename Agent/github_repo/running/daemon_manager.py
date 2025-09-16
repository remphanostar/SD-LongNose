#!/usr/bin/env python3
"""
PinokioCloud Daemon Manager

This module handles background processes when daemon: true flag is used in Pinokio scripts.
It provides comprehensive daemon process management including lifecycle control, health monitoring,
and automatic recovery capabilities.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import signal
import psutil
import threading
import subprocess
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from environment_management.shell_runner import ShellRunner
from environment_management.variable_system import VariableSystem
from environment_management.file_system import FileSystemManager
from environment_management.json_handler import JSONHandler


class DaemonStatus(Enum):
    """Enumeration of daemon statuses."""
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    CRASHED = "crashed"
    RESTARTING = "restarting"
    FAILED = "failed"
    UNKNOWN = "unknown"


class DaemonHealth(Enum):
    """Enumeration of daemon health states."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class DaemonInfo:
    """Information about a daemon process."""
    daemon_id: str
    app_name: str
    pid: int
    command: str
    working_directory: str
    environment_path: Optional[str]
    started_at: datetime
    status: DaemonStatus
    health: DaemonHealth
    restart_count: int = 0
    max_restarts: int = 5
    last_health_check: Optional[datetime] = None
    health_check_interval: float = 30.0  # seconds
    auto_restart: bool = True
    stdout_log: Optional[str] = None
    stderr_log: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DaemonInfo to dictionary."""
        data = asdict(self)
        data['started_at'] = self.started_at.isoformat()
        data['last_health_check'] = self.last_health_check.isoformat() if self.last_health_check else None
        data['status'] = self.status.value
        data['health'] = self.health.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DaemonInfo':
        """Create DaemonInfo from dictionary."""
        data['started_at'] = datetime.fromisoformat(data['started_at'])
        data['last_health_check'] = datetime.fromisoformat(data['last_health_check']) if data['last_health_check'] else None
        data['status'] = DaemonStatus(data['status'])
        data['health'] = DaemonHealth(data['health'])
        return cls(**data)


class DaemonManager:
    """
    Handles background processes when daemon: true flag is used.
    
    This class provides comprehensive daemon process management including
    process lifecycle control, health monitoring, and automatic recovery.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the daemon manager."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.daemon_storage_path = self.base_path / "daemon_storage"
        self.daemon_storage_path.mkdir(exist_ok=True)
        
        # Daemon tracking
        self.active_daemons: Dict[str, DaemonInfo] = {}
        self.daemon_lock = threading.RLock()
        
        # Health monitoring
        self.health_monitor_active = False
        self.health_monitor_thread = None
        self.health_check_interval = 10.0  # seconds
        
        # Initialize dependencies
        self.shell_runner = ShellRunner(str(self.base_path))
        self.variable_system = VariableSystem(str(self.base_path))
        self.file_system = FileSystemManager(str(self.base_path))
        self.json_handler = JSONHandler(str(self.base_path))
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            'daemon_started': [],
            'daemon_stopped': [],
            'daemon_crashed': [],
            'daemon_restarted': [],
            'daemon_health_changed': []
        }
        
        # Load existing daemon configurations
        self._load_daemon_configs()
        
        # Start health monitoring
        self._start_health_monitoring()
        
        print(f"[DaemonManager] Initialized with storage at: {self.daemon_storage_path}")
    
    def start_daemon(self, script_path: str, app_name: str, 
                    config: Optional[Dict[str, Any]] = None) -> DaemonInfo:
        """
        Start a daemon process.
        
        Args:
            script_path: Path to the script to run as daemon
            app_name: Name of the application
            config: Optional configuration for the daemon
        
        Returns:
            DaemonInfo: Information about the started daemon
        """
        print(f"[DaemonManager] Starting daemon for app: {app_name}")
        
        # Generate unique daemon ID
        daemon_id = f"{app_name}_{uuid.uuid4().hex[:8]}"
        
        # Prepare configuration
        daemon_config = config or {}
        daemon_config.setdefault('max_restarts', 5)
        daemon_config.setdefault('health_check_interval', 30.0)
        daemon_config.setdefault('auto_restart', True)
        
        # Prepare environment and command
        working_dir = self._get_working_directory(script_path)
        command = self._prepare_daemon_command(script_path, app_name, daemon_config)
        env_path = daemon_config.get('environment_path')
        
        # Create log files
        log_dir = self.daemon_storage_path / daemon_id
        log_dir.mkdir(exist_ok=True)
        stdout_log = str(log_dir / "stdout.log")
        stderr_log = str(log_dir / "stderr.log")
        
        # Start the daemon process
        start_time = datetime.now()
        
        try:
            pid = self._start_daemon_process(
                command, working_dir, env_path, stdout_log, stderr_log
            )
            
            # Create daemon info
            daemon_info = DaemonInfo(
                daemon_id=daemon_id,
                app_name=app_name,
                pid=pid,
                command=command,
                working_directory=working_dir,
                environment_path=env_path,
                started_at=start_time,
                status=DaemonStatus.STARTING,
                health=DaemonHealth.UNKNOWN,
                max_restarts=daemon_config['max_restarts'],
                health_check_interval=daemon_config['health_check_interval'],
                auto_restart=daemon_config['auto_restart'],
                stdout_log=stdout_log,
                stderr_log=stderr_log,
                config=daemon_config
            )
            
            # Register daemon
            with self.daemon_lock:
                self.active_daemons[daemon_id] = daemon_info
            
            # Save daemon configuration
            self._save_daemon_config(daemon_info)
            
            # Wait for startup verification
            time.sleep(3.0)
            
            # Check if daemon started successfully
            if self._is_daemon_alive(pid):
                daemon_info.status = DaemonStatus.RUNNING
                daemon_info.health = DaemonHealth.HEALTHY
                daemon_info.last_health_check = datetime.now()
                
                # Emit event
                self._emit_event('daemon_started', daemon_info)
                
                print(f"[DaemonManager] Started daemon {daemon_id} with PID: {pid}")
                return daemon_info
            else:
                # Daemon failed to start
                daemon_info.status = DaemonStatus.FAILED
                daemon_info.health = DaemonHealth.CRITICAL
                
                # Clean up
                with self.daemon_lock:
                    del self.active_daemons[daemon_id]
                
                raise RuntimeError(f"Daemon {daemon_id} failed to start")
                
        except Exception as e:
            print(f"[DaemonManager] Error starting daemon {daemon_id}: {e}")
            raise
    
    def stop_daemon(self, daemon_id: str, force: bool = False) -> bool:
        """
        Stop a daemon process.
        
        Args:
            daemon_id: ID of the daemon to stop
            force: Whether to force stop (SIGKILL vs SIGTERM)
        
        Returns:
            bool: True if successfully stopped
        """
        print(f"[DaemonManager] Stopping daemon: {daemon_id}")
        
        with self.daemon_lock:
            if daemon_id not in self.active_daemons:
                print(f"[DaemonManager] Daemon {daemon_id} not found")
                return False
            
            daemon_info = self.active_daemons[daemon_id]
            daemon_info.status = DaemonStatus.STOPPING
            
            try:
                # Stop the daemon process
                success = self._stop_daemon_process(daemon_info.pid, force)
                
                if success:
                    daemon_info.status = DaemonStatus.STOPPED
                    daemon_info.health = DaemonHealth.UNKNOWN
                    
                    # Remove from active daemons
                    del self.active_daemons[daemon_id]
                    
                    # Remove daemon configuration
                    self._remove_daemon_config(daemon_id)
                    
                    # Emit event
                    self._emit_event('daemon_stopped', daemon_info)
                    
                    print(f"[DaemonManager] Successfully stopped daemon {daemon_id}")
                    return True
                else:
                    daemon_info.status = DaemonStatus.FAILED
                    daemon_info.health = DaemonHealth.CRITICAL
                    print(f"[DaemonManager] Failed to stop daemon {daemon_id}")
                    return False
                    
            except Exception as e:
                print(f"[DaemonManager] Error stopping daemon {daemon_id}: {e}")
                daemon_info.status = DaemonStatus.FAILED
                daemon_info.health = DaemonHealth.CRITICAL
                return False
    
    def restart_daemon(self, daemon_id: str) -> bool:
        """
        Restart a daemon process.
        
        Args:
            daemon_id: ID of the daemon to restart
        
        Returns:
            bool: True if successfully restarted
        """
        print(f"[DaemonManager] Restarting daemon: {daemon_id}")
        
        with self.daemon_lock:
            if daemon_id not in self.active_daemons:
                print(f"[DaemonManager] Daemon {daemon_id} not found")
                return False
            
            daemon_info = self.active_daemons[daemon_id]
            
            # Check restart limits
            if daemon_info.restart_count >= daemon_info.max_restarts:
                print(f"[DaemonManager] Daemon {daemon_id} has exceeded max restarts")
                daemon_info.status = DaemonStatus.FAILED
                daemon_info.health = DaemonHealth.CRITICAL
                return False
            
            daemon_info.status = DaemonStatus.RESTARTING
            daemon_info.restart_count += 1
            
            try:
                # Stop the current process
                self._stop_daemon_process(daemon_info.pid, force=True)
                
                # Wait a moment for cleanup
                time.sleep(2.0)
                
                # Start new process
                new_pid = self._start_daemon_process(
                    daemon_info.command,
                    daemon_info.working_directory,
                    daemon_info.environment_path,
                    daemon_info.stdout_log,
                    daemon_info.stderr_log
                )
                
                # Update daemon info
                daemon_info.pid = new_pid
                daemon_info.started_at = datetime.now()
                daemon_info.status = DaemonStatus.RUNNING
                daemon_info.health = DaemonHealth.HEALTHY
                daemon_info.last_health_check = datetime.now()
                
                # Save updated configuration
                self._save_daemon_config(daemon_info)
                
                # Emit event
                self._emit_event('daemon_restarted', daemon_info)
                
                print(f"[DaemonManager] Successfully restarted daemon {daemon_id} with new PID: {new_pid}")
                return True
                
            except Exception as e:
                print(f"[DaemonManager] Error restarting daemon {daemon_id}: {e}")
                daemon_info.status = DaemonStatus.FAILED
                daemon_info.health = DaemonHealth.CRITICAL
                return False
    
    def list_active_daemons(self) -> List[DaemonInfo]:
        """
        Get list of all active daemons.
        
        Returns:
            List[DaemonInfo]: List of active daemon information
        """
        with self.daemon_lock:
            return list(self.active_daemons.values())
    
    def get_daemon_info(self, daemon_id: str) -> Optional[DaemonInfo]:
        """
        Get information about a specific daemon.
        
        Args:
            daemon_id: ID of the daemon
        
        Returns:
            Optional[DaemonInfo]: Daemon information if exists
        """
        return self.active_daemons.get(daemon_id)
    
    def monitor_daemon_health(self, daemon_id: str) -> DaemonHealth:
        """
        Check the health of a specific daemon.
        
        Args:
            daemon_id: ID of the daemon to check
        
        Returns:
            DaemonHealth: Current health status
        """
        if daemon_id not in self.active_daemons:
            return DaemonHealth.UNKNOWN
        
        daemon_info = self.active_daemons[daemon_id]
        
        # Check if process is alive
        if not self._is_daemon_alive(daemon_info.pid):
            old_health = daemon_info.health
            daemon_info.health = DaemonHealth.CRITICAL
            daemon_info.status = DaemonStatus.CRASHED
            
            if old_health != DaemonHealth.CRITICAL:
                self._emit_event('daemon_health_changed', daemon_info, old_health)
                self._emit_event('daemon_crashed', daemon_info)
            
            return DaemonHealth.CRITICAL
        
        # Perform health checks based on daemon configuration
        health_status = self._perform_health_check(daemon_info)
        
        # Update health if changed
        if health_status != daemon_info.health:
            old_health = daemon_info.health
            daemon_info.health = health_status
            daemon_info.last_health_check = datetime.now()
            self._emit_event('daemon_health_changed', daemon_info, old_health)
        
        return health_status
    
    def get_daemon_logs(self, daemon_id: str, lines: int = 100) -> Dict[str, List[str]]:
        """
        Get recent log lines for a daemon.
        
        Args:
            daemon_id: ID of the daemon
            lines: Number of lines to retrieve
        
        Returns:
            Dict[str, List[str]]: Dictionary with stdout and stderr logs
        """
        if daemon_id not in self.active_daemons:
            return {'stdout': [], 'stderr': []}
        
        daemon_info = self.active_daemons[daemon_id]
        logs = {'stdout': [], 'stderr': []}
        
        # Read stdout log
        if daemon_info.stdout_log and os.path.exists(daemon_info.stdout_log):
            try:
                with open(daemon_info.stdout_log, 'r') as f:
                    logs['stdout'] = f.readlines()[-lines:]
            except Exception as e:
                print(f"[DaemonManager] Error reading stdout log: {e}")
        
        # Read stderr log
        if daemon_info.stderr_log and os.path.exists(daemon_info.stderr_log):
            try:
                with open(daemon_info.stderr_log, 'r') as f:
                    logs['stderr'] = f.readlines()[-lines:]
            except Exception as e:
                print(f"[DaemonManager] Error reading stderr log: {e}")
        
        return logs
    
    def add_event_callback(self, event: str, callback: Callable) -> None:
        """Add a callback for daemon events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def _start_daemon_process(self, command: str, working_dir: str,
                            env_path: Optional[str], stdout_log: str,
                            stderr_log: str) -> int:
        """Start the actual daemon process."""
        # Prepare environment
        env = os.environ.copy()
        if env_path:
            if env_path.endswith('venv'):
                # Virtual environment
                env['PATH'] = f"{env_path}/bin:{env['PATH']}"
                env['VIRTUAL_ENV'] = env_path
            else:
                # Conda environment
                env['CONDA_DEFAULT_ENV'] = env_path
        
        # Open log files
        stdout_file = open(stdout_log, 'a')
        stderr_file = open(stderr_log, 'a')
        
        try:
            # Start daemon process with double fork for proper daemonization
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=working_dir,
                env=env,
                stdout=stdout_file,
                stderr=stderr_file,
                stdin=subprocess.DEVNULL,
                preexec_fn=os.setsid,  # Create new session
                start_new_session=True
            )
            
            return process.pid
            
        except Exception as e:
            stdout_file.close()
            stderr_file.close()
            raise RuntimeError(f"Failed to start daemon process: {e}")
    
    def _stop_daemon_process(self, pid: int, force: bool = False) -> bool:
        """Stop a daemon process."""
        try:
            if force:
                # Force kill the process group
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            else:
                # Graceful termination
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                
                # Wait for graceful shutdown
                for _ in range(15):  # Wait up to 15 seconds for daemons
                    if not self._is_daemon_alive(pid):
                        return True
                    time.sleep(1.0)
                
                # Force kill if still alive
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            
            # Final check
            time.sleep(2.0)
            return not self._is_daemon_alive(pid)
            
        except (OSError, ProcessLookupError):
            # Process already dead
            return True
        except Exception as e:
            print(f"[DaemonManager] Error stopping daemon process {pid}: {e}")
            return False
    
    def _is_daemon_alive(self, pid: int) -> bool:
        """Check if a daemon process is alive."""
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _perform_health_check(self, daemon_info: DaemonInfo) -> DaemonHealth:
        """Perform health check on a daemon."""
        try:
            process = psutil.Process(daemon_info.pid)
            
            # Basic health checks
            if not process.is_running():
                return DaemonHealth.CRITICAL
            
            if process.status() == psutil.STATUS_ZOMBIE:
                return DaemonHealth.CRITICAL
            
            # Resource-based health checks
            cpu_percent = process.cpu_percent()
            memory_percent = process.memory_percent()
            
            # Check for resource exhaustion
            if memory_percent > 95.0:
                return DaemonHealth.CRITICAL
            elif memory_percent > 80.0:
                return DaemonHealth.DEGRADED
            
            # Check for high CPU usage (might indicate problems)
            if cpu_percent > 95.0:
                return DaemonHealth.DEGRADED
            
            # Check log files for errors
            health_from_logs = self._check_log_health(daemon_info)
            if health_from_logs != DaemonHealth.HEALTHY:
                return health_from_logs
            
            return DaemonHealth.HEALTHY
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return DaemonHealth.CRITICAL
        except Exception:
            return DaemonHealth.UNKNOWN
    
    def _check_log_health(self, daemon_info: DaemonInfo) -> DaemonHealth:
        """Check daemon health based on log files."""
        try:
            # Check stderr log for recent errors
            if daemon_info.stderr_log and os.path.exists(daemon_info.stderr_log):
                with open(daemon_info.stderr_log, 'r') as f:
                    # Read last 50 lines
                    lines = f.readlines()[-50:]
                    recent_lines = [line for line in lines 
                                  if self._is_recent_log_line(line)]
                    
                    # Count error indicators
                    error_count = sum(1 for line in recent_lines 
                                    if any(keyword in line.lower() 
                                          for keyword in ['error', 'exception', 'failed', 'crash']))
                    
                    if error_count > 10:
                        return DaemonHealth.CRITICAL
                    elif error_count > 5:
                        return DaemonHealth.DEGRADED
                    elif error_count > 0:
                        return DaemonHealth.UNHEALTHY
            
            return DaemonHealth.HEALTHY
            
        except Exception:
            return DaemonHealth.UNKNOWN
    
    def _is_recent_log_line(self, line: str) -> bool:
        """Check if a log line is recent (within last 5 minutes)."""
        # This is a simplified check - in practice, you'd parse timestamps
        return True  # For now, consider all lines recent
    
    def _prepare_daemon_command(self, script_path: str, app_name: str,
                               config: Dict[str, Any]) -> str:
        """Prepare the command for daemon execution."""
        # Apply variable substitution
        variables = {
            'app_name': app_name,
            'script_path': script_path,
            **config.get('variables', {})
        }
        
        command = self.variable_system.substitute_variables(script_path, variables)
        return command
    
    def _get_working_directory(self, script_path: str) -> str:
        """Get the working directory for a script."""
        script_dir = os.path.dirname(os.path.abspath(script_path))
        return script_dir
    
    def _save_daemon_config(self, daemon_info: DaemonInfo) -> None:
        """Save daemon configuration to disk."""
        config_file = self.daemon_storage_path / f"{daemon_info.daemon_id}.json"
        try:
            self.json_handler.write_json_file(str(config_file), daemon_info.to_dict())
        except Exception as e:
            print(f"[DaemonManager] Error saving daemon config: {e}")
    
    def _load_daemon_configs(self) -> None:
        """Load existing daemon configurations."""
        try:
            for config_file in self.daemon_storage_path.glob("*.json"):
                try:
                    config_data = self.json_handler.read_json_file(str(config_file))
                    daemon_info = DaemonInfo.from_dict(config_data)
                    
                    # Check if daemon is still alive
                    if self._is_daemon_alive(daemon_info.pid):
                        self.active_daemons[daemon_info.daemon_id] = daemon_info
                        print(f"[DaemonManager] Restored daemon: {daemon_info.daemon_id}")
                    else:
                        # Remove stale config
                        config_file.unlink()
                        
                except Exception as e:
                    print(f"[DaemonManager] Error loading daemon config {config_file}: {e}")
                    
        except Exception as e:
            print(f"[DaemonManager] Error loading daemon configs: {e}")
    
    def _remove_daemon_config(self, daemon_id: str) -> None:
        """Remove daemon configuration from disk."""
        config_file = self.daemon_storage_path / f"{daemon_id}.json"
        try:
            if config_file.exists():
                config_file.unlink()
        except Exception as e:
            print(f"[DaemonManager] Error removing daemon config: {e}")
    
    def _start_health_monitoring(self) -> None:
        """Start the health monitoring thread."""
        if self.health_monitor_thread is None or not self.health_monitor_thread.is_alive():
            self.health_monitor_active = True
            self.health_monitor_thread = threading.Thread(
                target=self._health_monitoring_loop,
                daemon=True
            )
            self.health_monitor_thread.start()
            print("[DaemonManager] Started health monitoring")
    
    def _health_monitoring_loop(self) -> None:
        """Main health monitoring loop."""
        while self.health_monitor_active:
            try:
                with self.daemon_lock:
                    for daemon_id in list(self.active_daemons.keys()):
                        daemon_info = self.active_daemons[daemon_id]
                        
                        # Check if it's time for health check
                        now = datetime.now()
                        if (daemon_info.last_health_check is None or 
                            (now - daemon_info.last_health_check).total_seconds() >= 
                            daemon_info.health_check_interval):
                            
                            # Perform health check
                            health = self.monitor_daemon_health(daemon_id)
                            
                            # Handle critical health
                            if health == DaemonHealth.CRITICAL and daemon_info.auto_restart:
                                if daemon_info.restart_count < daemon_info.max_restarts:
                                    print(f"[DaemonManager] Auto-restarting unhealthy daemon: {daemon_id}")
                                    self.restart_daemon(daemon_id)
                                else:
                                    print(f"[DaemonManager] Daemon {daemon_id} exceeded max restarts, marking as failed")
                                    daemon_info.status = DaemonStatus.FAILED
                
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                print(f"[DaemonManager] Error in health monitoring loop: {e}")
                time.sleep(self.health_check_interval)
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[DaemonManager] Error in event callback: {e}")
    
    def stop_health_monitoring(self) -> None:
        """Stop the health monitoring thread."""
        self.health_monitor_active = False
        if self.health_monitor_thread and self.health_monitor_thread.is_alive():
            self.health_monitor_thread.join(timeout=5.0)
        print("[DaemonManager] Stopped health monitoring")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_health_monitoring()


def main():
    """Test the daemon manager functionality."""
    print("Testing DaemonManager...")
    
    daemon_manager = DaemonManager()
    
    # Test basic functionality
    print("DaemonManager initialized successfully")
    
    # List active daemons (should be empty initially)
    active_daemons = daemon_manager.list_active_daemons()
    print(f"Active daemons: {len(active_daemons)}")
    
    # Test would require actual daemon scripts to run
    print("DaemonManager test completed")


if __name__ == "__main__":
    main()