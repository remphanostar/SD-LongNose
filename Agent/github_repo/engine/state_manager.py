#!/usr/bin/env python3
"""
PinokioCloud State Manager

This module tracks which applications are installed and their status.
It provides comprehensive state management for applications, installations, and system state.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

# Import previous phase modules
sys.path.append('/workspace/github_repo')
from environment_management.json_handler import JSONHandler
from environment_management.file_system import FileSystemManager


class ApplicationStatus(Enum):
    """Enumeration of application statuses."""
    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    INSTALLED = "installed"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UPDATING = "updating"
    UNINSTALLING = "uninstalling"


class InstallationStatus(Enum):
    """Enumeration of installation statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SystemStatus(Enum):
    """Enumeration of system statuses."""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class ApplicationState:
    """Application state information."""
    app_name: str
    app_path: str
    status: ApplicationStatus
    version: str = ""
    installed_date: str = ""
    last_run_date: str = ""
    run_count: int = 0
    total_runtime: float = 0.0
    configuration: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    webui_info: Dict[str, Any] = field(default_factory=dict)
    process_info: Dict[str, Any] = field(default_factory=dict)
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InstallationState:
    """Installation state information."""
    installation_id: str
    app_name: str
    status: InstallationStatus
    start_time: float = 0.0
    end_time: float = 0.0
    progress: float = 0.0
    current_step: str = ""
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemState:
    """System state information."""
    system_id: str
    status: SystemStatus
    last_updated: float = 0.0
    total_apps: int = 0
    running_apps: int = 0
    total_installations: int = 0
    active_installations: int = 0
    system_resources: Dict[str, Any] = field(default_factory=dict)
    health_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class StateManager:
    """
    Tracks which applications are installed and their status.
    
    Provides comprehensive state management including:
    - Application state tracking and persistence
    - Installation state monitoring
    - System state management
    - State synchronization and backup
    - State history and audit trails
    - Real-time state updates
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the state manager.
        
        Args:
            base_path: Base path for state operations
        """
        self.base_path = base_path
        self.state_path = os.path.join(base_path, "state")
        
        # Initialize components
        self.json_handler = JSONHandler(base_path)
        self.file_system = FileSystemManager(base_path)
        
        # State storage
        self.applications: Dict[str, ApplicationState] = {}
        self.installations: Dict[str, InstallationState] = {}
        self.system_state: Optional[SystemState] = None
        
        # State persistence
        self.state_file = os.path.join(self.state_path, "state.json")
        self.backup_path = os.path.join(self.state_path, "backups")
        
        # Threading
        self.lock = threading.RLock()
        self.auto_save_interval = 30  # seconds
        self.auto_save_thread = None
        self.auto_save_enabled = True
        
        # Progress callback
        self.progress_callback = None
        
        # Ensure state directory exists
        os.makedirs(self.state_path, exist_ok=True)
        os.makedirs(self.backup_path, exist_ok=True)
        
        # Load existing state
        self._load_state()
        
        # Start auto-save thread
        self._start_auto_save()
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def register_application(self, app_name: str, app_path: str, 
                           configuration: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register a new application.
        
        Args:
            app_name: Name of the application
            app_path: Path to the application
            configuration: Application configuration
            
        Returns:
            bool: True if registration successful
        """
        try:
            with self.lock:
                if app_name in self.applications:
                    return False
                
                app_state = ApplicationState(
                    app_name=app_name,
                    app_path=app_path,
                    status=ApplicationStatus.INSTALLED,
                    version=configuration.get('version', '') if configuration else '',
                    installed_date=time.strftime('%Y-%m-%d %H:%M:%S'),
                    configuration=configuration or {},
                    dependencies=configuration.get('dependencies', []) if configuration else [],
                    webui_info=configuration.get('webui_info', {}) if configuration else {}
                )
                
                self.applications[app_name] = app_state
                self._update_system_state()
                self._save_state()
                
                self._update_progress(f"Registered application: {app_name}")
                return True
        
        except Exception as e:
            return False
    
    def update_application_status(self, app_name: str, status: ApplicationStatus,
                                metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update application status.
        
        Args:
            app_name: Name of the application
            status: New status
            metadata: Additional metadata
            
        Returns:
            bool: True if update successful
        """
        try:
            with self.lock:
                if app_name not in self.applications:
                    return False
                
                app_state = self.applications[app_name]
                app_state.status = status
                
                if status == ApplicationStatus.RUNNING:
                    app_state.last_run_date = time.strftime('%Y-%m-%d %H:%M:%S')
                    app_state.run_count += 1
                
                if metadata:
                    app_state.metadata.update(metadata)
                
                self._update_system_state()
                self._save_state()
                
                self._update_progress(f"Updated {app_name} status to {status.value}")
                return True
        
        except Exception as e:
            return False
    
    def update_application_runtime(self, app_name: str, runtime: float) -> bool:
        """
        Update application runtime.
        
        Args:
            app_name: Name of the application
            runtime: Runtime in seconds
            
        Returns:
            bool: True if update successful
        """
        try:
            with self.lock:
                if app_name not in self.applications:
                    return False
                
                self.applications[app_name].total_runtime += runtime
                self._save_state()
                
                return True
        
        except Exception as e:
            return False
    
    def update_application_process_info(self, app_name: str, process_info: Dict[str, Any]) -> bool:
        """
        Update application process information.
        
        Args:
            app_name: Name of the application
            process_info: Process information
            
        Returns:
            bool: True if update successful
        """
        try:
            with self.lock:
                if app_name not in self.applications:
                    return False
                
                self.applications[app_name].process_info = process_info
                self._save_state()
                
                return True
        
        except Exception as e:
            return False
    
    def add_application_error(self, app_name: str, error_message: str, 
                            error_type: str = "error") -> bool:
        """
        Add error to application history.
        
        Args:
            app_name: Name of the application
            error_message: Error message
            error_type: Type of error
            
        Returns:
            bool: True if addition successful
        """
        try:
            with self.lock:
                if app_name not in self.applications:
                    return False
                
                error_entry = {
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'type': error_type,
                    'message': error_message
                }
                
                self.applications[app_name].error_history.append(error_entry)
                
                # Keep only last 100 errors
                if len(self.applications[app_name].error_history) > 100:
                    self.applications[app_name].error_history = self.applications[app_name].error_history[-100:]
                
                self._save_state()
                return True
        
        except Exception as e:
            return False
    
    def unregister_application(self, app_name: str) -> bool:
        """
        Unregister an application.
        
        Args:
            app_name: Name of the application
            
        Returns:
            bool: True if unregistration successful
        """
        try:
            with self.lock:
                if app_name not in self.applications:
                    return False
                
                del self.applications[app_name]
                self._update_system_state()
                self._save_state()
                
                self._update_progress(f"Unregistered application: {app_name}")
                return True
        
        except Exception as e:
            return False
    
    def get_application_state(self, app_name: str) -> Optional[ApplicationState]:
        """
        Get application state.
        
        Args:
            app_name: Name of the application
            
        Returns:
            ApplicationState or None if not found
        """
        with self.lock:
            return self.applications.get(app_name)
    
    def get_all_applications(self) -> List[ApplicationState]:
        """
        Get all application states.
        
        Returns:
            List of application states
        """
        with self.lock:
            return list(self.applications.values())
    
    def get_applications_by_status(self, status: ApplicationStatus) -> List[ApplicationState]:
        """
        Get applications by status.
        
        Args:
            status: Application status
            
        Returns:
            List of application states with specified status
        """
        with self.lock:
            return [app for app in self.applications.values() if app.status == status]
    
    def register_installation(self, installation_id: str, app_name: str) -> bool:
        """
        Register a new installation.
        
        Args:
            installation_id: Installation ID
            app_name: Name of the application
            
        Returns:
            bool: True if registration successful
        """
        try:
            with self.lock:
                if installation_id in self.installations:
                    return False
                
                installation_state = InstallationState(
                    installation_id=installation_id,
                    app_name=app_name,
                    status=InstallationStatus.PENDING,
                    start_time=time.time()
                )
                
                self.installations[installation_id] = installation_state
                self._update_system_state()
                self._save_state()
                
                self._update_progress(f"Registered installation: {installation_id}")
                return True
        
        except Exception as e:
            return False
    
    def update_installation_status(self, installation_id: str, status: InstallationStatus,
                                 progress: float = 0.0, current_step: str = "",
                                 error_messages: Optional[List[str]] = None,
                                 warnings: Optional[List[str]] = None) -> bool:
        """
        Update installation status.
        
        Args:
            installation_id: Installation ID
            status: New status
            progress: Installation progress (0.0 to 1.0)
            current_step: Current installation step
            error_messages: Error messages
            warnings: Warning messages
            
        Returns:
            bool: True if update successful
        """
        try:
            with self.lock:
                if installation_id not in self.installations:
                    return False
                
                installation_state = self.installations[installation_id]
                installation_state.status = status
                installation_state.progress = progress
                installation_state.current_step = current_step
                
                if status in [InstallationStatus.COMPLETED, InstallationStatus.FAILED, InstallationStatus.CANCELLED]:
                    installation_state.end_time = time.time()
                
                if error_messages:
                    installation_state.error_messages.extend(error_messages)
                
                if warnings:
                    installation_state.warnings.extend(warnings)
                
                self._update_system_state()
                self._save_state()
                
                self._update_progress(f"Updated installation {installation_id} status to {status.value}")
                return True
        
        except Exception as e:
            return False
    
    def get_installation_state(self, installation_id: str) -> Optional[InstallationState]:
        """
        Get installation state.
        
        Args:
            installation_id: Installation ID
            
        Returns:
            InstallationState or None if not found
        """
        with self.lock:
            return self.installations.get(installation_id)
    
    def get_active_installations(self) -> List[InstallationState]:
        """
        Get active installations.
        
        Returns:
            List of active installation states
        """
        with self.lock:
            active_statuses = [InstallationStatus.PENDING, InstallationStatus.IN_PROGRESS]
            return [inst for inst in self.installations.values() if inst.status in active_statuses]
    
    def get_installation_history(self, limit: int = 100) -> List[InstallationState]:
        """
        Get installation history.
        
        Args:
            limit: Maximum number of installations to return
            
        Returns:
            List of installation states
        """
        with self.lock:
            installations = list(self.installations.values())
            installations.sort(key=lambda x: x.start_time, reverse=True)
            return installations[:limit]
    
    def update_system_resources(self, resources: Dict[str, Any]) -> bool:
        """
        Update system resources.
        
        Args:
            resources: System resource information
            
        Returns:
            bool: True if update successful
        """
        try:
            with self.lock:
                if not self.system_state:
                    self.system_state = SystemState(
                        system_id="main",
                        status=SystemStatus.HEALTHY,
                        last_updated=time.time()
                    )
                
                self.system_state.system_resources = resources
                self.system_state.last_updated = time.time()
                self._save_state()
                
                return True
        
        except Exception as e:
            return False
    
    def update_system_health(self, health_metrics: Dict[str, Any]) -> bool:
        """
        Update system health metrics.
        
        Args:
            health_metrics: Health metrics
            
        Returns:
            bool: True if update successful
        """
        try:
            with self.lock:
                if not self.system_state:
                    self.system_state = SystemState(
                        system_id="main",
                        status=SystemStatus.HEALTHY,
                        last_updated=time.time()
                    )
                
                self.system_state.health_metrics = health_metrics
                self.system_state.last_updated = time.time()
                
                # Determine system status based on health metrics
                if health_metrics.get('error_count', 0) > 10:
                    self.system_state.status = SystemStatus.ERROR
                elif health_metrics.get('warning_count', 0) > 5:
                    self.system_state.status = SystemStatus.WARNING
                else:
                    self.system_state.status = SystemStatus.HEALTHY
                
                self._save_state()
                return True
        
        except Exception as e:
            return False
    
    def get_system_state(self) -> Optional[SystemState]:
        """
        Get system state.
        
        Returns:
            SystemState or None if not available
        """
        with self.lock:
            return self.system_state
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get complete state summary.
        
        Returns:
            State summary dictionary
        """
        with self.lock:
            return {
                'applications': {
                    'total': len(self.applications),
                    'by_status': {
                        status.value: len([app for app in self.applications.values() if app.status == status])
                        for status in ApplicationStatus
                    }
                },
                'installations': {
                    'total': len(self.installations),
                    'active': len(self.get_active_installations()),
                    'by_status': {
                        status.value: len([inst for inst in self.installations.values() if inst.status == status])
                        for status in InstallationStatus
                    }
                },
                'system': {
                    'status': self.system_state.status.value if self.system_state else 'unknown',
                    'last_updated': self.system_state.last_updated if self.system_state else 0
                }
            }
    
    def backup_state(self) -> bool:
        """
        Create state backup.
        
        Returns:
            bool: True if backup successful
        """
        try:
            with self.lock:
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                backup_file = os.path.join(self.backup_path, f"state_backup_{timestamp}.json")
                
                state_data = self._serialize_state()
                self.json_handler.write_json(backup_file, state_data)
                
                self._update_progress(f"Created state backup: {backup_file}")
                return True
        
        except Exception as e:
            return False
    
    def restore_state(self, backup_file: str) -> bool:
        """
        Restore state from backup.
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            bool: True if restore successful
        """
        try:
            with self.lock:
                if not os.path.exists(backup_file):
                    return False
                
                state_data = self.json_handler.read_json(backup_file)
                self._deserialize_state(state_data)
                self._save_state()
                
                self._update_progress(f"Restored state from backup: {backup_file}")
                return True
        
        except Exception as e:
            return False
    
    def cleanup_old_backups(self, keep_count: int = 10) -> bool:
        """
        Cleanup old backups.
        
        Args:
            keep_count: Number of backups to keep
            
        Returns:
            bool: True if cleanup successful
        """
        try:
            backup_files = []
            for filename in os.listdir(self.backup_path):
                if filename.startswith('state_backup_') and filename.endswith('.json'):
                    filepath = os.path.join(self.backup_path, filename)
                    backup_files.append((filepath, os.path.getmtime(filepath)))
            
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            for filepath, _ in backup_files[keep_count:]:
                os.remove(filepath)
            
            self._update_progress(f"Cleaned up {len(backup_files) - keep_count} old backups")
            return True
        
        except Exception as e:
            return False
    
    def _update_system_state(self):
        """Update system state based on current applications and installations."""
        try:
            if not self.system_state:
                self.system_state = SystemState(
                    system_id="main",
                    status=SystemStatus.HEALTHY,
                    last_updated=time.time()
                )
            
            # Update application counts
            self.system_state.total_apps = len(self.applications)
            self.system_state.running_apps = len([app for app in self.applications.values() 
                                                if app.status == ApplicationStatus.RUNNING])
            
            # Update installation counts
            self.system_state.total_installations = len(self.installations)
            self.system_state.active_installations = len(self.get_active_installations())
            
            self.system_state.last_updated = time.time()
        
        except Exception as e:
            pass
    
    def _save_state(self):
        """Save state to file."""
        try:
            state_data = self._serialize_state()
            self.json_handler.write_json(self.state_file, state_data)
        
        except Exception as e:
            pass
    
    def _load_state(self):
        """Load state from file."""
        try:
            if os.path.exists(self.state_file):
                state_data = self.json_handler.read_json(self.state_file)
                self._deserialize_state(state_data)
        
        except Exception as e:
            pass
    
    def _serialize_state(self) -> Dict[str, Any]:
        """Serialize state to dictionary."""
        try:
            return {
                'applications': {
                    name: asdict(app_state) for name, app_state in self.applications.items()
                },
                'installations': {
                    inst_id: asdict(inst_state) for inst_id, inst_state in self.installations.items()
                },
                'system_state': asdict(self.system_state) if self.system_state else None,
                'metadata': {
                    'version': '1.0.0',
                    'last_saved': time.time()
                }
            }
        
        except Exception as e:
            return {}
    
    def _deserialize_state(self, state_data: Dict[str, Any]):
        """Deserialize state from dictionary."""
        try:
            # Deserialize applications
            self.applications = {}
            for name, app_data in state_data.get('applications', {}).items():
                app_state = ApplicationState(
                    app_name=app_data['app_name'],
                    app_path=app_data['app_path'],
                    status=ApplicationStatus(app_data['status']),
                    version=app_data.get('version', ''),
                    installed_date=app_data.get('installed_date', ''),
                    last_run_date=app_data.get('last_run_date', ''),
                    run_count=app_data.get('run_count', 0),
                    total_runtime=app_data.get('total_runtime', 0.0),
                    configuration=app_data.get('configuration', {}),
                    dependencies=app_data.get('dependencies', []),
                    webui_info=app_data.get('webui_info', {}),
                    process_info=app_data.get('process_info', {}),
                    error_history=app_data.get('error_history', []),
                    metadata=app_data.get('metadata', {})
                )
                self.applications[name] = app_state
            
            # Deserialize installations
            self.installations = {}
            for inst_id, inst_data in state_data.get('installations', {}).items():
                inst_state = InstallationState(
                    installation_id=inst_data['installation_id'],
                    app_name=inst_data['app_name'],
                    status=InstallationStatus(inst_data['status']),
                    start_time=inst_data.get('start_time', 0.0),
                    end_time=inst_data.get('end_time', 0.0),
                    progress=inst_data.get('progress', 0.0),
                    current_step=inst_data.get('current_step', ''),
                    error_messages=inst_data.get('error_messages', []),
                    warnings=inst_data.get('warnings', []),
                    metadata=inst_data.get('metadata', {})
                )
                self.installations[inst_id] = inst_state
            
            # Deserialize system state
            system_data = state_data.get('system_state')
            if system_data:
                self.system_state = SystemState(
                    system_id=system_data['system_id'],
                    status=SystemStatus(system_data['status']),
                    last_updated=system_data.get('last_updated', 0.0),
                    total_apps=system_data.get('total_apps', 0),
                    running_apps=system_data.get('running_apps', 0),
                    total_installations=system_data.get('total_installations', 0),
                    active_installations=system_data.get('active_installations', 0),
                    system_resources=system_data.get('system_resources', {}),
                    health_metrics=system_data.get('health_metrics', {}),
                    metadata=system_data.get('metadata', {})
                )
        
        except Exception as e:
            pass
    
    def _start_auto_save(self):
        """Start auto-save thread."""
        try:
            if self.auto_save_enabled:
                self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
                self.auto_save_thread.start()
        
        except Exception as e:
            pass
    
    def _auto_save_loop(self):
        """Auto-save loop."""
        try:
            while self.auto_save_enabled:
                time.sleep(self.auto_save_interval)
                self._save_state()
        
        except Exception as e:
            pass
    
    def _update_progress(self, message: str):
        """Update progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(message)
            except:
                pass
    
    def shutdown(self):
        """Shutdown state manager."""
        try:
            self.auto_save_enabled = False
            if self.auto_save_thread:
                self.auto_save_thread.join(timeout=5)
            
            self._save_state()
        
        except Exception as e:
            pass


def main():
    """Main function for testing state manager."""
    print("🧪 Testing State Manager")
    print("=" * 50)
    
    # Initialize state manager
    state_manager = StateManager()
    
    # Set up progress callback
    def progress_callback(message):
        print(f"  {message}")
    
    state_manager.set_progress_callback(progress_callback)
    
    # Test application registration
    print("\n📱 Testing application registration...")
    
    success = state_manager.register_application(
        app_name="test_app",
        app_path="/apps/test_app",
        configuration={
            'version': '1.0.0',
            'dependencies': ['torch', 'numpy'],
            'webui_info': {'port': 7860, 'type': 'gradio'}
        }
    )
    print(f"✅ Application registration: {success}")
    
    # Test application state retrieval
    print("\n📋 Testing application state retrieval...")
    
    app_state = state_manager.get_application_state("test_app")
    print(f"✅ Application state retrieval: {app_state is not None}")
    if app_state:
        print(f"   - App name: {app_state.app_name}")
        print(f"   - Status: {app_state.status.value}")
        print(f"   - Version: {app_state.version}")
        print(f"   - Dependencies: {len(app_state.dependencies)}")
    
    # Test application status update
    print("\n🔄 Testing application status update...")
    
    success = state_manager.update_application_status("test_app", ApplicationStatus.RUNNING)
    print(f"✅ Status update: {success}")
    
    success = state_manager.update_application_runtime("test_app", 120.5)
    print(f"✅ Runtime update: {success}")
    
    success = state_manager.update_application_process_info("test_app", {
        'pid': 1234,
        'memory_usage': '512MB',
        'cpu_usage': '15%'
    })
    print(f"✅ Process info update: {success}")
    
    # Test error tracking
    print("\n❌ Testing error tracking...")
    
    success = state_manager.add_application_error("test_app", "Test error message", "warning")
    print(f"✅ Error tracking: {success}")
    
    # Test installation registration
    print("\n🔧 Testing installation registration...")
    
    success = state_manager.register_installation("install_001", "test_app")
    print(f"✅ Installation registration: {success}")
    
    # Test installation status update
    print("\n📊 Testing installation status update...")
    
    success = state_manager.update_installation_status(
        installation_id="install_001",
        status=InstallationStatus.IN_PROGRESS,
        progress=0.5,
        current_step="Installing dependencies"
    )
    print(f"✅ Installation status update: {success}")
    
    success = state_manager.update_installation_status(
        installation_id="install_001",
        status=InstallationStatus.COMPLETED,
        progress=1.0,
        current_step="Installation complete"
    )
    print(f"✅ Installation completion: {success}")
    
    # Test system state
    print("\n🖥️ Testing system state...")
    
    success = state_manager.update_system_resources({
        'cpu_usage': '45%',
        'memory_usage': '2.1GB',
        'disk_usage': '15GB',
        'gpu_usage': '30%'
    })
    print(f"✅ System resources update: {success}")
    
    success = state_manager.update_system_health({
        'error_count': 2,
        'warning_count': 5,
        'uptime': 3600
    })
    print(f"✅ System health update: {success}")
    
    # Test state summary
    print("\n📈 Testing state summary...")
    
    summary = state_manager.get_state_summary()
    print(f"✅ State summary: {summary is not None}")
    if summary:
        print(f"   - Total applications: {summary['applications']['total']}")
        print(f"   - Running applications: {summary['applications']['by_status']['running']}")
        print(f"   - Total installations: {summary['installations']['total']}")
        print(f"   - Active installations: {summary['installations']['active']}")
        print(f"   - System status: {summary['system']['status']}")
    
    # Test backup and restore
    print("\n💾 Testing backup and restore...")
    
    backup_success = state_manager.backup_state()
    print(f"✅ State backup: {backup_success}")
    
    # Test cleanup
    print("\n🧹 Testing cleanup...")
    
    cleanup_success = state_manager.cleanup_old_backups(keep_count=5)
    print(f"✅ Backup cleanup: {cleanup_success}")
    
    # Test unregistration
    print("\n🗑️ Testing application unregistration...")
    
    unregister_success = state_manager.unregister_application("test_app")
    print(f"✅ Application unregistration: {unregister_success}")
    
    # Shutdown
    state_manager.shutdown()
    
    return True


if __name__ == "__main__":
    main()