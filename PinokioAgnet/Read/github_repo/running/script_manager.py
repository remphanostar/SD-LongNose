#!/usr/bin/env python3
"""
PinokioCloud Script Manager

This module manages running applications and processes. It provides the core functionality
for starting, stopping, and managing Pinokio applications with full process control,
daemon support, and integration with the state management system.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import signal
import psutil
import subprocess
import threading
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from environment_management.venv_manager import VirtualEnvironmentManager
from environment_management.shell_runner import ShellRunner
from environment_management.variable_system import VariableSystem
from environment_management.file_system import FileSystemManager
from engine.state_manager import StateManager, ApplicationStatus
from app_analysis.app_analyzer import AppAnalyzer


class ApplicationRunningStatus(Enum):
    """Enumeration of application running statuses."""
    NOT_RUNNING = "not_running"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    CRASHED = "crashed"
    DAEMON = "daemon"
    ERROR = "error"


class ProcessType(Enum):
    """Enumeration of process types."""
    MAIN = "main"
    DAEMON = "daemon"
    CHILD = "child"
    HELPER = "helper"


@dataclass
class ProcessInfo:
    """Information about a running process."""
    pid: int
    app_name: str
    process_type: ProcessType
    command: str
    started_at: datetime
    status: ApplicationRunningStatus
    working_directory: str
    environment_path: Optional[str] = None
    daemon: bool = False
    parent_pid: Optional[int] = None
    children_pids: List[int] = field(default_factory=list)
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    last_health_check: Optional[datetime] = None
    restart_count: int = 0
    max_restarts: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ProcessInfo to dictionary."""
        data = asdict(self)
        data['started_at'] = self.started_at.isoformat()
        data['last_health_check'] = self.last_health_check.isoformat() if self.last_health_check else None
        data['status'] = self.status.value
        data['process_type'] = self.process_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessInfo':
        """Create ProcessInfo from dictionary."""
        data['started_at'] = datetime.fromisoformat(data['started_at'])
        data['last_health_check'] = datetime.fromisoformat(data['last_health_check']) if data['last_health_check'] else None
        data['status'] = ApplicationRunningStatus(data['status'])
        data['process_type'] = ProcessType(data['process_type'])
        return cls(**data)


class ScriptManager:
    """
    Manages running applications and processes.
    
    This class provides comprehensive process management for Pinokio applications,
    including starting, stopping, monitoring, and daemon handling.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the script manager."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.running_processes: Dict[str, ProcessInfo] = {}
        self.process_lock = threading.RLock()
        
        # Initialize dependencies
        self.state_manager = StateManager(base_path)
        self.venv_manager = VirtualEnvironmentManager(base_path)
        self.shell_runner = ShellRunner(base_path)
        self.variable_system = VariableSystem(base_path)
        self.file_system = FileSystemManager(base_path)
        self.app_analyzer = AppAnalyzer(base_path)
        
        # Process monitoring
        self.monitoring_thread = None
        self.monitoring_active = False
        self.monitoring_interval = 5.0  # seconds
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            'process_started': [],
            'process_stopped': [],
            'process_crashed': [],
            'daemon_started': [],
            'daemon_stopped': []
        }
        
        # Initialize monitoring
        self._start_monitoring()
        
        print(f"[ScriptManager] Initialized with base path: {self.base_path}")
    
    def add_event_handler(self, event: str, handler: Callable) -> None:
        """Add an event handler."""
        if event in self.event_handlers:
            self.event_handlers[event].append(handler)
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all handlers."""
        for handler in self.event_handlers.get(event, []):
            try:
                handler(*args, **kwargs)
            except Exception as e:
                print(f"[ScriptManager] Error in event handler: {e}")
    
    def start_application(self, app_name: str, script_path: str, 
                         daemon: bool = False, **kwargs) -> ProcessInfo:
        """
        Start a Pinokio application.
        
        Args:
            app_name: Name of the application
            script_path: Path to the script to run
            daemon: Whether to run as daemon process
            **kwargs: Additional arguments for the application
        
        Returns:
            ProcessInfo: Information about the started process
        """
        print(f"[ScriptManager] Starting application: {app_name}")
        
        with self.process_lock:
            # Check if already running
            if app_name in self.running_processes:
                existing_process = self.running_processes[app_name]
                if self._is_process_alive(existing_process.pid):
                    print(f"[ScriptManager] Application {app_name} is already running (PID: {existing_process.pid})")
                    return existing_process
                else:
                    # Clean up dead process
                    print(f"[ScriptManager] Cleaning up dead process for {app_name}")
                    self._cleanup_process(app_name)
            
            # Get application info from state manager
            app_state = self.state_manager.get_application_state(app_name)
            if not app_state or app_state.status != ApplicationStatus.INSTALLED:
                raise RuntimeError(f"Application {app_name} is not installed or ready to run")
            
            # Get application profile for running requirements
            app_profile = self.app_analyzer.analyze_application(app_state.installation_path)
            
            # Prepare environment
            env_path = self._prepare_environment(app_name, app_state.installation_path)
            
            # Prepare command with variable substitution
            command = self._prepare_command(script_path, app_name, **kwargs)
            
            # Set working directory
            working_dir = str(app_state.installation_path)
            
            # Start the process
            start_time = datetime.now()
            
            if daemon:
                # Start as daemon process
                process_info = self._start_daemon_process(
                    app_name, command, working_dir, env_path, start_time
                )
            else:
                # Start as regular process
                process_info = self._start_regular_process(
                    app_name, command, working_dir, env_path, start_time
                )
            
            # Register process
            self.running_processes[app_name] = process_info
            
            # Update state manager
            self.state_manager.set_application_status(app_name, ApplicationStatus.RUNNING)
            
            # Emit event
            event_name = 'daemon_started' if daemon else 'process_started'
            self._emit_event(event_name, process_info)
            
            print(f"[ScriptManager] Started {app_name} with PID: {process_info.pid}")
            return process_info
    
    def stop_application(self, app_name: str, force: bool = False) -> bool:
        """
        Stop a running application.
        
        Args:
            app_name: Name of the application to stop
            force: Whether to force stop (SIGKILL vs SIGTERM)
        
        Returns:
            bool: True if successfully stopped
        """
        print(f"[ScriptManager] Stopping application: {app_name}")
        
        with self.process_lock:
            if app_name not in self.running_processes:
                print(f"[ScriptManager] Application {app_name} is not running")
                return False
            
            process_info = self.running_processes[app_name]
            
            # Update status to stopping
            process_info.status = ApplicationRunningStatus.STOPPING
            
            try:
                # Stop the process
                success = self._stop_process(process_info.pid, force)
                
                if success:
                    # Clean up process info
                    process_info.status = ApplicationRunningStatus.STOPPED
                    
                    # Update state manager
                    self.state_manager.set_application_status(app_name, ApplicationStatus.STOPPED)
                    
                    # Remove from running processes
                    del self.running_processes[app_name]
                    
                    # Emit event
                    event_name = 'daemon_stopped' if process_info.daemon else 'process_stopped'
                    self._emit_event(event_name, process_info)
                    
                    print(f"[ScriptManager] Successfully stopped {app_name}")
                    return True
                else:
                    process_info.status = ApplicationRunningStatus.ERROR
                    print(f"[ScriptManager] Failed to stop {app_name}")
                    return False
                    
            except Exception as e:
                print(f"[ScriptManager] Error stopping {app_name}: {e}")
                process_info.status = ApplicationRunningStatus.ERROR
                return False
    
    def restart_application(self, app_name: str, **kwargs) -> bool:
        """
        Restart a running application.
        
        Args:
            app_name: Name of the application to restart
            **kwargs: Additional arguments for restart
        
        Returns:
            bool: True if successfully restarted
        """
        print(f"[ScriptManager] Restarting application: {app_name}")
        
        # Get current process info if exists
        original_command = None
        original_daemon = False
        
        if app_name in self.running_processes:
            process_info = self.running_processes[app_name]
            original_command = process_info.command
            original_daemon = process_info.daemon
            
            # Stop the application
            if not self.stop_application(app_name):
                print(f"[ScriptManager] Failed to stop {app_name} for restart")
                return False
        
        # Wait a moment for cleanup
        time.sleep(2.0)
        
        try:
            # Get application state for script path
            app_state = self.state_manager.get_application_state(app_name)
            if not app_state:
                print(f"[ScriptManager] No application state found for {app_name}")
                return False
            
            # Find the run script
            run_script = self._find_run_script(app_state.installation_path)
            if not run_script:
                print(f"[ScriptManager] No run script found for {app_name}")
                return False
            
            # Restart the application
            process_info = self.start_application(
                app_name, run_script, daemon=original_daemon, **kwargs
            )
            
            # Increment restart count
            process_info.restart_count += 1
            
            print(f"[ScriptManager] Successfully restarted {app_name}")
            return True
            
        except Exception as e:
            print(f"[ScriptManager] Error restarting {app_name}: {e}")
            return False
    
    def get_application_status(self, app_name: str) -> ApplicationRunningStatus:
        """
        Get the running status of an application.
        
        Args:
            app_name: Name of the application
        
        Returns:
            ApplicationRunningStatus: Current running status
        """
        if app_name not in self.running_processes:
            return ApplicationRunningStatus.NOT_RUNNING
        
        process_info = self.running_processes[app_name]
        
        # Check if process is still alive
        if not self._is_process_alive(process_info.pid):
            # Process is dead, update status
            process_info.status = ApplicationRunningStatus.CRASHED
            self._emit_event('process_crashed', process_info)
        
        return process_info.status
    
    def list_running_applications(self) -> List[ProcessInfo]:
        """
        Get list of all running applications.
        
        Returns:
            List[ProcessInfo]: List of running process information
        """
        with self.process_lock:
            # Clean up dead processes first
            self._cleanup_dead_processes()
            return list(self.running_processes.values())
    
    def get_process_info(self, app_name: str) -> Optional[ProcessInfo]:
        """
        Get detailed process information for an application.
        
        Args:
            app_name: Name of the application
        
        Returns:
            Optional[ProcessInfo]: Process information if running
        """
        return self.running_processes.get(app_name)
    
    def _prepare_environment(self, app_name: str, installation_path: Path) -> Optional[str]:
        """Prepare the environment for running the application."""
        # Check if app has virtual environment
        venv_path = installation_path / "venv"
        if venv_path.exists():
            return str(venv_path)
        
        # Check for conda environment
        conda_env = f"{app_name}_env"
        if self.venv_manager.conda_env_exists(conda_env):
            return conda_env
        
        return None
    
    def _prepare_command(self, script_path: str, app_name: str, **kwargs) -> str:
        """Prepare the command with variable substitution."""
        # Create variable context
        variables = {
            'app_name': app_name,
            'script_path': script_path,
            **kwargs
        }
        
        # Apply variable substitution
        command = self.variable_system.substitute_variables(script_path, variables)
        
        return command
    
    def _start_regular_process(self, app_name: str, command: str, 
                             working_dir: str, env_path: Optional[str],
                             start_time: datetime) -> ProcessInfo:
        """Start a regular (non-daemon) process."""
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
        
        # Start process
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=working_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Create process info
        process_info = ProcessInfo(
            pid=process.pid,
            app_name=app_name,
            process_type=ProcessType.MAIN,
            command=command,
            started_at=start_time,
            status=ApplicationRunningStatus.STARTING,
            working_directory=working_dir,
            environment_path=env_path,
            daemon=False
        )
        
        # Wait a moment to ensure process started successfully
        time.sleep(2.0)
        
        if process.poll() is None:
            # Process is running
            process_info.status = ApplicationRunningStatus.RUNNING
        else:
            # Process failed to start
            stdout, stderr = process.communicate()
            print(f"[ScriptManager] Process failed to start: {stderr.decode()}")
            raise RuntimeError(f"Failed to start {app_name}: {stderr.decode()}")
        
        return process_info
    
    def _start_daemon_process(self, app_name: str, command: str,
                            working_dir: str, env_path: Optional[str],
                            start_time: datetime) -> ProcessInfo:
        """Start a daemon process."""
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
        
        # Start daemon process
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=working_dir,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            preexec_fn=os.setsid  # Create new process group
        )
        
        # Create process info
        process_info = ProcessInfo(
            pid=process.pid,
            app_name=app_name,
            process_type=ProcessType.DAEMON,
            command=command,
            started_at=start_time,
            status=ApplicationRunningStatus.DAEMON,
            working_directory=working_dir,
            environment_path=env_path,
            daemon=True
        )
        
        # Wait a moment to ensure daemon started successfully
        time.sleep(3.0)
        
        if not self._is_process_alive(process.pid):
            raise RuntimeError(f"Failed to start daemon {app_name}")
        
        return process_info
    
    def _stop_process(self, pid: int, force: bool = False) -> bool:
        """Stop a process by PID."""
        try:
            if force:
                # Force kill
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            else:
                # Graceful termination
                os.killpg(os.getpgid(pid), signal.SIGTERM)
                
                # Wait for graceful shutdown
                for _ in range(10):  # Wait up to 10 seconds
                    if not self._is_process_alive(pid):
                        return True
                    time.sleep(1.0)
                
                # Force kill if still alive
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            
            # Final check
            time.sleep(1.0)
            return not self._is_process_alive(pid)
            
        except (OSError, ProcessLookupError):
            # Process already dead
            return True
        except Exception as e:
            print(f"[ScriptManager] Error stopping process {pid}: {e}")
            return False
    
    def _is_process_alive(self, pid: int) -> bool:
        """Check if a process is alive."""
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _cleanup_process(self, app_name: str) -> None:
        """Clean up a dead process."""
        if app_name in self.running_processes:
            process_info = self.running_processes[app_name]
            process_info.status = ApplicationRunningStatus.CRASHED
            
            # Update state manager
            self.state_manager.set_application_status(app_name, ApplicationStatus.STOPPED)
            
            # Remove from running processes
            del self.running_processes[app_name]
            
            # Emit event
            self._emit_event('process_crashed', process_info)
    
    def _cleanup_dead_processes(self) -> None:
        """Clean up all dead processes."""
        dead_processes = []
        
        for app_name, process_info in self.running_processes.items():
            if not self._is_process_alive(process_info.pid):
                dead_processes.append(app_name)
        
        for app_name in dead_processes:
            self._cleanup_process(app_name)
    
    def _find_run_script(self, installation_path: Path) -> Optional[str]:
        """Find the run script for an application."""
        possible_scripts = [
            "run.js",
            "run.json", 
            "start.js",
            "start.json",
            "app.js",
            "main.py",
            "run.py"
        ]
        
        for script in possible_scripts:
            script_path = installation_path / script
            if script_path.exists():
                return str(script_path)
        
        return None
    
    def _start_monitoring(self) -> None:
        """Start the process monitoring thread."""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            print("[ScriptManager] Started process monitoring")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                with self.process_lock:
                    self._cleanup_dead_processes()
                    self._update_resource_usage()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"[ScriptManager] Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _update_resource_usage(self) -> None:
        """Update resource usage for all running processes."""
        for app_name, process_info in self.running_processes.items():
            try:
                process = psutil.Process(process_info.pid)
                
                # Get resource usage
                cpu_percent = process.cpu_percent()
                memory_info = process.memory_info()
                
                # Update process info
                process_info.resource_usage = {
                    'cpu_percent': cpu_percent,
                    'memory_rss': memory_info.rss,
                    'memory_vms': memory_info.vms,
                    'num_threads': process.num_threads(),
                    'status': process.status(),
                    'updated_at': datetime.now().isoformat()
                }
                
                process_info.last_health_check = datetime.now()
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process is dead or inaccessible
                continue
            except Exception as e:
                print(f"[ScriptManager] Error updating resource usage for {app_name}: {e}")
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring thread."""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        print("[ScriptManager] Stopped process monitoring")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_monitoring()


def main():
    """Test the script manager functionality."""
    print("Testing ScriptManager...")
    
    script_manager = ScriptManager()
    
    # Test basic functionality
    print("ScriptManager initialized successfully")
    
    # List running applications (should be empty initially)
    running_apps = script_manager.list_running_applications()
    print(f"Running applications: {len(running_apps)}")
    
    # Test would require actual Pinokio applications to be installed
    print("ScriptManager test completed")


if __name__ == "__main__":
    main()