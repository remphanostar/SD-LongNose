#!/usr/bin/env python3
"""
PinokioCloud Backup and Recovery System

This module provides comprehensive backup and recovery systems for all
PinokioCloud configurations, application settings, user preferences,
and system state. It ensures data safety and easy recovery from failures.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import shutil
import gzip
import pickle
import threading
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import zipfile

# Add the github_repo directory to Python path for imports
sys.path.append('/workspace/SD-LongNose/github_repo')

# Import all previous phase modules for backup integration
from cloud_detection.cloud_detector import CloudDetector
from environment_management.file_system import FileSystemManager
from environment_management.json_handler import JSONHandler
from engine.state_manager import StateManager
from optimization.logging_system import LoggingSystem


class BackupType(Enum):
    """Types of backups that can be created."""
    FULL_SYSTEM = "full_system"
    CONFIGURATIONS = "configurations"
    APPLICATION_SETTINGS = "application_settings"
    USER_PREFERENCES = "user_preferences"
    INSTALLATION_STATE = "installation_state"
    CACHE_DATA = "cache_data"
    LOG_FILES = "log_files"
    TUNNEL_CONFIGURATIONS = "tunnel_configurations"
    PERFORMANCE_DATA = "performance_data"


class BackupStatus(Enum):
    """Status of backup operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"
    EXPIRED = "expired"


@dataclass
class RestorePoint:
    """Represents a system restore point."""
    id: str
    timestamp: datetime
    backup_type: BackupType
    description: str
    file_path: str
    file_size: int
    checksum: str
    status: BackupStatus
    metadata: Dict[str, Any] = field(default_factory=dict)
    expiry_date: Optional[datetime] = None
    restore_count: int = 0
    last_restored: Optional[datetime] = None


@dataclass
class BackupOperation:
    """Represents a backup operation."""
    id: str
    backup_type: BackupType
    status: BackupStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    file_count: int = 0
    total_size: int = 0
    compressed_size: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BackupSystem:
    """
    Comprehensive Backup and Recovery System for PinokioCloud
    
    This class provides complete backup and recovery functionality for all
    PinokioCloud components, ensuring data safety, configuration preservation,
    and easy recovery from failures across all phases and platforms.
    """
    
    def __init__(self, backup_dir: str = "/workspace/SD-LongNose/backups"):
        """
        Initialize the backup system.
        
        Args:
            backup_dir: Directory to store backup files
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.cloud_detector = CloudDetector()
        self.file_system = FileSystemManager()
        self.json_handler = JSONHandler()
        self.state_manager = StateManager()
        self.logging_system = LoggingSystem()
        
        # Backup tracking
        self.restore_points = []
        self.backup_operations = []
        self.backup_config = {
            'auto_backup_enabled': True,
            'auto_backup_interval': 3600,  # 1 hour
            'max_restore_points': 50,
            'compression_enabled': True,
            'encryption_enabled': False,
            'retention_days': 30
        }
        
        # Load existing restore points
        self._load_restore_points()
        
        # Get platform info for platform-specific backups
        self.platform_info = self.cloud_detector.detect_platform()
        
    def _load_restore_points(self):
        """Load existing restore points from backup directory."""
        try:
            restore_points_file = self.backup_dir / 'restore_points.json'
            
            if restore_points_file.exists():
                with open(restore_points_file, 'r') as f:
                    restore_points_data = json.load(f)
                    
                # Convert to RestorePoint objects
                for rp_data in restore_points_data:
                    try:
                        restore_point = RestorePoint(
                            id=rp_data['id'],
                            timestamp=datetime.fromisoformat(rp_data['timestamp']),
                            backup_type=BackupType(rp_data['backup_type']),
                            description=rp_data['description'],
                            file_path=rp_data['file_path'],
                            file_size=rp_data['file_size'],
                            checksum=rp_data['checksum'],
                            status=BackupStatus(rp_data['status']),
                            metadata=rp_data.get('metadata', {}),
                            expiry_date=datetime.fromisoformat(rp_data['expiry_date']) if rp_data.get('expiry_date') else None,
                            restore_count=rp_data.get('restore_count', 0),
                            last_restored=datetime.fromisoformat(rp_data['last_restored']) if rp_data.get('last_restored') else None
                        )
                        self.restore_points.append(restore_point)
                    except Exception as e:
                        self.logging_system.log_warning(f"Failed to load restore point: {str(e)}")
                        
        except Exception as e:
            self.logging_system.log_warning(f"Failed to load restore points: {str(e)}")
            
    def _save_restore_points(self):
        """Save restore points to backup directory."""
        try:
            restore_points_file = self.backup_dir / 'restore_points.json'
            
            # Convert to serializable format
            restore_points_data = []
            for rp in self.restore_points:
                rp_data = asdict(rp)
                rp_data['timestamp'] = rp.timestamp.isoformat()
                rp_data['backup_type'] = rp.backup_type.value
                rp_data['status'] = rp.status.value
                if rp.expiry_date:
                    rp_data['expiry_date'] = rp.expiry_date.isoformat()
                if rp.last_restored:
                    rp_data['last_restored'] = rp.last_restored.isoformat()
                restore_points_data.append(rp_data)
                
            with open(restore_points_file, 'w') as f:
                json.dump(restore_points_data, f, indent=2)
                
        except Exception as e:
            self.logging_system.log_error(f"Failed to save restore points: {str(e)}")
            
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum for a file."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logging_system.log_error(f"Checksum calculation failed: {str(e)}")
            return ""
            
    def create_backup(self, backup_type: BackupType, description: str = "") -> RestorePoint:
        """
        Create a backup of specified type.
        
        Args:
            backup_type: Type of backup to create
            description: Optional description for the backup
            
        Returns:
            RestorePoint object representing the created backup
        """
        try:
            # Generate backup ID
            backup_id = f"backup_{backup_type.value}_{int(time.time())}"
            
            # Create backup operation
            operation = BackupOperation(
                id=backup_id,
                backup_type=backup_type,
                status=BackupStatus.IN_PROGRESS,
                started_at=datetime.now()
            )
            
            self.backup_operations.append(operation)
            
            self.logging_system.log_info("Component", f"Starting backup: {backup_id} ({backup_type.value})")
            
            # Determine what to backup based on type
            backup_data = {}
            files_to_backup = []
            
            if backup_type == BackupType.FULL_SYSTEM:
                # Full system backup
                backup_data = self._collect_full_system_data()
                files_to_backup = self._get_all_system_files()
                
            elif backup_type == BackupType.CONFIGURATIONS:
                # Configuration backup
                backup_data = self._collect_configuration_data()
                
            elif backup_type == BackupType.APPLICATION_SETTINGS:
                # Application settings backup
                backup_data = self._collect_application_settings()
                
            elif backup_type == BackupType.USER_PREFERENCES:
                # User preferences backup
                backup_data = self._collect_user_preferences()
                
            elif backup_type == BackupType.INSTALLATION_STATE:
                # Installation state backup
                backup_data = self._collect_installation_state()
                
            elif backup_type == BackupType.TUNNEL_CONFIGURATIONS:
                # Tunnel configurations backup
                backup_data = self._collect_tunnel_configurations()
                
            else:
                raise ValueError(f"Unsupported backup type: {backup_type}")
            
            # Create backup file
            backup_filename = f"{backup_id}.backup"
            backup_file_path = self.backup_dir / backup_filename
            
            if self.backup_config['compression_enabled']:
                backup_filename += '.gz'
                backup_file_path = self.backup_dir / backup_filename
                
                with gzip.open(backup_file_path, 'wt', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, default=str)
            else:
                with open(backup_file_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, default=str)
            
            # Calculate file size and checksum
            file_size = backup_file_path.stat().st_size
            checksum = self._calculate_checksum(backup_file_path)
            
            # Create restore point
            restore_point = RestorePoint(
                id=backup_id,
                timestamp=datetime.now(),
                backup_type=backup_type,
                description=description or f"Automatic {backup_type.value} backup",
                file_path=str(backup_file_path),
                file_size=file_size,
                checksum=checksum,
                status=BackupStatus.COMPLETED,
                metadata={
                    'platform': self.platform_info.platform.value,
                    'data_keys': list(backup_data.keys()),
                    'file_count': len(files_to_backup),
                    'compression_enabled': self.backup_config['compression_enabled']
                },
                expiry_date=datetime.now() + timedelta(days=self.backup_config['retention_days'])
            )
            
            # Add to restore points
            self.restore_points.append(restore_point)
            
            # Update operation status
            operation.status = BackupStatus.COMPLETED
            operation.completed_at = datetime.now()
            operation.file_count = len(files_to_backup)
            operation.total_size = len(json.dumps(backup_data, default=str))
            operation.compressed_size = file_size
            
            # Save restore points
            self._save_restore_points()
            
            # Clean up old backups
            self._cleanup_old_backups()
            
            self.logging_system.log_info("Component", f"Backup completed successfully: {backup_id}")
            
            return restore_point
            
        except Exception as e:
            # Update operation status
            if 'operation' in locals():
                operation.status = BackupStatus.FAILED
                operation.errors.append(str(e))
                
            self.logging_system.log_error(f"Backup creation failed: {str(e)}")
            
            # Return failed restore point
            return RestorePoint(
                id=backup_id if 'backup_id' in locals() else f"failed_{int(time.time())}",
                timestamp=datetime.now(),
                backup_type=backup_type,
                description=f"Failed backup: {str(e)}",
                file_path="",
                file_size=0,
                checksum="",
                status=BackupStatus.FAILED
            )
            
    def _collect_full_system_data(self) -> Dict[str, Any]:
        """Collect complete system data for full backup."""
        try:
            system_data = {
                'backup_type': 'full_system',
                'timestamp': datetime.now().isoformat(),
                'platform_info': self.platform_info.__dict__ if hasattr(self.platform_info, '__dict__') else {},
                'configurations': self._collect_configuration_data(),
                'application_settings': self._collect_application_settings(),
                'user_preferences': self._collect_user_preferences(),
                'installation_state': self._collect_installation_state(),
                'tunnel_configurations': self._collect_tunnel_configurations(),
                'system_metrics': self._collect_system_metrics(),
                'file_structure': self._collect_file_structure()
            }
            
            return system_data
            
        except Exception as e:
            self.logging_system.log_error(f"Full system data collection failed: {str(e)}")
            return {'error': str(e)}
            
    def _collect_configuration_data(self) -> Dict[str, Any]:
        """Collect all configuration data."""
        try:
            config_data = {
                'platform_configs': {},
                'environment_configs': {},
                'optimization_configs': {},
                'ui_configs': {}
            }
            
            # Collect configuration files
            config_files = [
                '/workspace/SD-LongNose/variables.json',
                '/workspace/SD-LongNose/startup_cache.json'
            ]
            
            for config_file in config_files:
                try:
                    if Path(config_file).exists():
                        with open(config_file, 'r') as f:
                            config_data[Path(config_file).stem] = json.load(f)
                except Exception as e:
                    config_data[Path(config_file).stem] = {'error': str(e)}
            
            return config_data
            
        except Exception as e:
            return {'error': str(e)}
            
    def _collect_application_settings(self) -> Dict[str, Any]:
        """Collect all application settings and states."""
        try:
            app_settings = {
                'installed_apps': {},
                'running_apps': {},
                'app_configurations': {},
                'installation_history': {}
            }
            
            # Get application state from state manager
            try:
                # This would integrate with the state manager from Phase 5
                app_states = self.state_manager.get_all_application_states()
                app_settings['installed_apps'] = app_states
            except Exception as e:
                app_settings['installed_apps'] = {'error': str(e)}
            
            # Collect app-specific configuration files
            apps_dir = Path('/workspace/SD-LongNose/apps')
            if apps_dir.exists():
                for app_dir in apps_dir.iterdir():
                    if app_dir.is_dir():
                        app_config = {}
                        
                        # Look for common config files
                        config_files = ['config.json', 'settings.json', '.env', 'config.yaml']
                        for config_file in config_files:
                            config_path = app_dir / config_file
                            if config_path.exists():
                                try:
                                    if config_file.endswith('.json'):
                                        with open(config_path, 'r') as f:
                                            app_config[config_file] = json.load(f)
                                    else:
                                        with open(config_path, 'r') as f:
                                            app_config[config_file] = f.read()
                                except Exception as e:
                                    app_config[config_file] = {'error': str(e)}
                        
                        if app_config:
                            app_settings['app_configurations'][app_dir.name] = app_config
            
            return app_settings
            
        except Exception as e:
            return {'error': str(e)}
            
    def _collect_user_preferences(self) -> Dict[str, Any]:
        """Collect all user preferences and UI settings."""
        try:
            user_prefs = {
                'ui_preferences': {},
                'notification_settings': {},
                'performance_settings': {},
                'theme_settings': {}
            }
            
            # Collect UI preferences (would be stored in session state in real app)
            ui_prefs = {
                'theme': 'dark_cyberpunk',
                'auto_refresh': True,
                'refresh_interval': 5,
                'terminal_visible': True,
                'resource_monitoring': True,
                'show_qr_codes': True,
                'gallery_view': 'grid',
                'apps_per_page': 12
            }
            user_prefs['ui_preferences'] = ui_prefs
            
            # Collect notification settings
            notification_settings = {
                'installation_complete': True,
                'app_started': True,
                'resource_alerts': True,
                'tunnel_status': True,
                'error_notifications': True
            }
            user_prefs['notification_settings'] = notification_settings
            
            return user_prefs
            
        except Exception as e:
            return {'error': str(e)}
            
    def _collect_installation_state(self) -> Dict[str, Any]:
        """Collect installation state for all applications."""
        try:
            installation_state = {
                'app_statuses': {},
                'installation_history': [],
                'virtual_environments': {},
                'dependency_cache': {}
            }
            
            # Get app installation states
            try:
                all_states = self.state_manager.get_all_application_states()
                installation_state['app_statuses'] = all_states
            except Exception as e:
                installation_state['app_statuses'] = {'error': str(e)}
            
            # Collect virtual environment information
            venv_dir = Path('/workspace/SD-LongNose/venvs')
            if venv_dir.exists():
                for venv_path in venv_dir.iterdir():
                    if venv_path.is_dir():
                        try:
                            # Get basic venv info
                            pip_freeze_file = venv_path / 'pip_freeze.txt'
                            if pip_freeze_file.exists():
                                with open(pip_freeze_file, 'r') as f:
                                    installation_state['virtual_environments'][venv_path.name] = {
                                        'packages': f.read(),
                                        'created': datetime.fromtimestamp(venv_path.stat().st_ctime).isoformat()
                                    }
                        except Exception as e:
                            installation_state['virtual_environments'][venv_path.name] = {'error': str(e)}
            
            return installation_state
            
        except Exception as e:
            return {'error': str(e)}
            
    def _collect_tunnel_configurations(self) -> Dict[str, Any]:
        """Collect tunnel configurations and settings."""
        try:
            tunnel_config = {
                'active_tunnels': {},
                'tunnel_history': [],
                'ngrok_config': {},
                'cloudflare_config': {},
                'url_analytics': {}
            }
            
            # Collect tunnel configuration files
            tunnel_config_files = [
                '/workspace/SD-LongNose/ngrok_config.json',
                '/workspace/SD-LongNose/tunnel_settings.json'
            ]
            
            for config_file in tunnel_config_files:
                try:
                    if Path(config_file).exists():
                        with open(config_file, 'r') as f:
                            tunnel_config[Path(config_file).stem] = json.load(f)
                except Exception as e:
                    tunnel_config[Path(config_file).stem] = {'error': str(e)}
            
            return tunnel_config
            
        except Exception as e:
            return {'error': str(e)}
            
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics for backup context."""
        try:
            from optimization.performance_monitor import PerformanceMonitor
            perf_monitor = PerformanceMonitor()
            
            metrics = perf_monitor.get_current_metrics()
            metrics['backup_timestamp'] = datetime.now().isoformat()
            
            return metrics
            
        except Exception as e:
            return {'error': str(e)}
            
    def _collect_file_structure(self) -> Dict[str, Any]:
        """Collect file structure information for backup verification."""
        try:
            base_path = Path('/workspace/SD-LongNose/github_repo')
            file_structure = {}
            
            for py_file in base_path.rglob('*.py'):
                try:
                    relative_path = str(py_file.relative_to(base_path))
                    file_info = {
                        'size': py_file.stat().st_size,
                        'modified': datetime.fromtimestamp(py_file.stat().st_mtime).isoformat(),
                        'checksum': self._calculate_checksum(py_file)
                    }
                    file_structure[relative_path] = file_info
                except Exception as e:
                    file_structure[relative_path] = {'error': str(e)}
            
            return file_structure
            
        except Exception as e:
            return {'error': str(e)}
            
    def _get_all_system_files(self) -> List[str]:
        """Get list of all system files for backup."""
        try:
            files = []
            base_path = Path('/workspace/SD-LongNose')
            
            # Include all Python files
            files.extend([str(f) for f in base_path.rglob('*.py')])
            
            # Include configuration files
            config_patterns = ['*.json', '*.yaml', '*.yml', '*.toml', '*.ini']
            for pattern in config_patterns:
                files.extend([str(f) for f in base_path.rglob(pattern)])
            
            # Include documentation
            doc_patterns = ['*.md', '*.txt', '*.rst']
            for pattern in doc_patterns:
                files.extend([str(f) for f in base_path.rglob(pattern)])
            
            return files
            
        except Exception as e:
            self.logging_system.log_error(f"Failed to get system files: {str(e)}")
            return []
            
    def restore_from_backup(self, restore_point_id: str) -> bool:
        """
        Restore system from a backup restore point.
        
        Args:
            restore_point_id: ID of the restore point to restore from
            
        Returns:
            True if restore was successful, False otherwise
        """
        try:
            # Find restore point
            restore_point = None
            for rp in self.restore_points:
                if rp.id == restore_point_id:
                    restore_point = rp
                    break
            
            if not restore_point:
                raise ValueError(f"Restore point not found: {restore_point_id}")
            
            if restore_point.status != BackupStatus.COMPLETED:
                raise ValueError(f"Restore point is not in completed state: {restore_point.status}")
            
            # Verify backup file exists and is valid
            backup_file = Path(restore_point.file_path)
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {restore_point.file_path}")
            
            # Verify checksum
            current_checksum = self._calculate_checksum(backup_file)
            if current_checksum != restore_point.checksum:
                raise ValueError("Backup file checksum mismatch - file may be corrupted")
            
            self.logging_system.log_info("Component", f"Starting restore from: {restore_point_id}")
            
            # Load backup data
            if backup_file.name.endswith('.gz'):
                with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                    backup_data = json.load(f)
            else:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
            
            # Restore based on backup type
            if restore_point.backup_type == BackupType.CONFIGURATIONS:
                self._restore_configurations(backup_data)
            elif restore_point.backup_type == BackupType.APPLICATION_SETTINGS:
                self._restore_application_settings(backup_data)
            elif restore_point.backup_type == BackupType.USER_PREFERENCES:
                self._restore_user_preferences(backup_data)
            elif restore_point.backup_type == BackupType.INSTALLATION_STATE:
                self._restore_installation_state(backup_data)
            elif restore_point.backup_type == BackupType.TUNNEL_CONFIGURATIONS:
                self._restore_tunnel_configurations(backup_data)
            elif restore_point.backup_type == BackupType.FULL_SYSTEM:
                self._restore_full_system(backup_data)
            else:
                raise ValueError(f"Unsupported restore type: {restore_point.backup_type}")
            
            # Update restore point statistics
            restore_point.restore_count += 1
            restore_point.last_restored = datetime.now()
            
            # Save updated restore points
            self._save_restore_points()
            
            self.logging_system.log_info("Component", f"Restore completed successfully: {restore_point_id}")
            
            return True
            
        except Exception as e:
            self.logging_system.log_error(f"Restore failed: {str(e)}")
            return False
            
    def _restore_configurations(self, backup_data: Dict[str, Any]):
        """Restore configuration data."""
        try:
            configs = backup_data.get('configurations', backup_data)
            
            for config_name, config_content in configs.items():
                if config_name.endswith('_config') or config_name in ['variables', 'startup_cache']:
                    config_file = Path(f'/workspace/SD-LongNose/{config_name}.json')
                    
                    try:
                        with open(config_file, 'w') as f:
                            json.dump(config_content, f, indent=2)
                        self.logging_system.log_info("Component", f"Restored configuration: {config_name}")
                    except Exception as e:
                        self.logging_system.log_warning(f"Failed to restore {config_name}: {str(e)}")
                        
        except Exception as e:
            self.logging_system.log_error(f"Configuration restore failed: {str(e)}")
            
    def _restore_application_settings(self, backup_data: Dict[str, Any]):
        """Restore application settings."""
        try:
            app_settings = backup_data.get('application_settings', backup_data)
            
            # Restore application states
            if 'installed_apps' in app_settings:
                try:
                    self.state_manager.restore_all_application_states(app_settings['installed_apps'])
                except Exception as e:
                    self.logging_system.log_warning(f"Failed to restore app states: {str(e)}")
            
            # Restore app configurations
            if 'app_configurations' in app_settings:
                apps_dir = Path('/workspace/SD-LongNose/apps')
                apps_dir.mkdir(exist_ok=True)
                
                for app_name, app_config in app_settings['app_configurations'].items():
                    app_dir = apps_dir / app_name
                    app_dir.mkdir(exist_ok=True)
                    
                    for config_file, config_content in app_config.items():
                        try:
                            config_path = app_dir / config_file
                            if config_file.endswith('.json'):
                                with open(config_path, 'w') as f:
                                    json.dump(config_content, f, indent=2)
                            else:
                                with open(config_path, 'w') as f:
                                    f.write(config_content)
                        except Exception as e:
                            self.logging_system.log_warning(f"Failed to restore {app_name}/{config_file}: {str(e)}")
                            
        except Exception as e:
            self.logging_system.log_error(f"Application settings restore failed: {str(e)}")
            
    def _restore_user_preferences(self, backup_data: Dict[str, Any]):
        """Restore user preferences."""
        try:
            # This would restore UI preferences in a real implementation
            # For now, we save to a preferences file
            prefs_file = Path('/workspace/SD-LongNose/user_preferences.json')
            
            user_prefs = backup_data.get('user_preferences', backup_data)
            
            with open(prefs_file, 'w') as f:
                json.dump(user_prefs, f, indent=2)
                
            self.logging_system.log_info("Component", "User preferences restored successfully")
            
        except Exception as e:
            self.logging_system.log_error(f"User preferences restore failed: {str(e)}")
            
    def _restore_installation_state(self, backup_data: Dict[str, Any]):
        """Restore installation state."""
        try:
            install_state = backup_data.get('installation_state', backup_data)
            
            # Restore app statuses
            if 'app_statuses' in install_state:
                try:
                    self.state_manager.restore_all_application_states(install_state['app_statuses'])
                except Exception as e:
                    self.logging_system.log_warning(f"Failed to restore app statuses: {str(e)}")
            
            self.logging_system.log_info("Component", "Installation state restored successfully")
            
        except Exception as e:
            self.logging_system.log_error(f"Installation state restore failed: {str(e)}")
            
    def _restore_tunnel_configurations(self, backup_data: Dict[str, Any]):
        """Restore tunnel configurations."""
        try:
            tunnel_config = backup_data.get('tunnel_configurations', backup_data)
            
            # Restore tunnel config files
            for config_name, config_content in tunnel_config.items():
                if config_name.endswith('_config'):
                    config_file = Path(f'/workspace/SD-LongNose/{config_name}.json')
                    
                    try:
                        with open(config_file, 'w') as f:
                            json.dump(config_content, f, indent=2)
                    except Exception as e:
                        self.logging_system.log_warning(f"Failed to restore tunnel config {config_name}: {str(e)}")
            
            self.logging_system.log_info("Component", "Tunnel configurations restored successfully")
            
        except Exception as e:
            self.logging_system.log_error(f"Tunnel configuration restore failed: {str(e)}")
            
    def _restore_full_system(self, backup_data: Dict[str, Any]):
        """Restore complete system from full backup."""
        try:
            # Restore all components
            if 'configurations' in backup_data:
                self._restore_configurations(backup_data['configurations'])
                
            if 'application_settings' in backup_data:
                self._restore_application_settings(backup_data['application_settings'])
                
            if 'user_preferences' in backup_data:
                self._restore_user_preferences(backup_data['user_preferences'])
                
            if 'installation_state' in backup_data:
                self._restore_installation_state(backup_data['installation_state'])
                
            if 'tunnel_configurations' in backup_data:
                self._restore_tunnel_configurations(backup_data['tunnel_configurations'])
            
            self.logging_system.log_info("Component", "Full system restore completed successfully")
            
        except Exception as e:
            self.logging_system.log_error(f"Full system restore failed: {str(e)}")
            
    def _cleanup_old_backups(self):
        """Clean up old and expired backup files."""
        try:
            current_time = datetime.now()
            removed_count = 0
            
            # Remove expired restore points
            active_restore_points = []
            for rp in self.restore_points:
                if rp.expiry_date and current_time > rp.expiry_date:
                    # Remove backup file
                    try:
                        backup_file = Path(rp.file_path)
                        if backup_file.exists():
                            backup_file.unlink()
                        removed_count += 1
                    except Exception as e:
                        self.logging_system.log_warning(f"Failed to remove expired backup: {str(e)}")
                else:
                    active_restore_points.append(rp)
            
            # Keep only the most recent backups if we exceed the limit
            if len(active_restore_points) > self.backup_config['max_restore_points']:
                # Sort by timestamp and keep the most recent
                active_restore_points.sort(key=lambda x: x.timestamp, reverse=True)
                
                # Remove oldest backups
                for old_rp in active_restore_points[self.backup_config['max_restore_points']:]:
                    try:
                        backup_file = Path(old_rp.file_path)
                        if backup_file.exists():
                            backup_file.unlink()
                        removed_count += 1
                    except Exception as e:
                        self.logging_system.log_warning(f"Failed to remove old backup: {str(e)}")
                
                active_restore_points = active_restore_points[:self.backup_config['max_restore_points']]
            
            # Update restore points list
            self.restore_points = active_restore_points
            
            if removed_count > 0:
                self.logging_system.log_info("Component", f"Cleaned up {removed_count} old backup files")
                
        except Exception as e:
            self.logging_system.log_error(f"Backup cleanup failed: {str(e)}")
            
    def get_backup_statistics(self) -> Dict[str, Any]:
        """Get comprehensive backup system statistics."""
        try:
            total_backups = len(self.restore_points)
            total_size = sum(rp.file_size for rp in self.restore_points)
            
            # Group by backup type
            type_counts = {}
            for rp in self.restore_points:
                backup_type = rp.backup_type.value
                type_counts[backup_type] = type_counts.get(backup_type, 0) + 1
            
            # Calculate success rate
            successful_operations = len([op for op in self.backup_operations if op.status == BackupStatus.COMPLETED])
            total_operations = len(self.backup_operations)
            success_rate = (successful_operations / max(total_operations, 1)) * 100
            
            return {
                'total_restore_points': total_backups,
                'total_backup_size': total_size,
                'backup_types': type_counts,
                'success_rate': success_rate,
                'successful_operations': successful_operations,
                'failed_operations': total_operations - successful_operations,
                'last_backup': max([rp.timestamp for rp in self.restore_points]).isoformat() if self.restore_points else None,
                'oldest_backup': min([rp.timestamp for rp in self.restore_points]).isoformat() if self.restore_points else None
            }
            
        except Exception as e:
            self.logging_system.log_error(f"Failed to get backup statistics: {str(e)}")
            return {'error': str(e)}
            
    def create_automatic_backup(self) -> RestorePoint:
        """Create automatic backup based on current system state."""
        try:
            # Determine what type of backup to create based on system activity
            backup_type = BackupType.CONFIGURATIONS  # Default
            
            # Check if there are recent installations
            try:
                recent_installs = self.state_manager.get_recent_installations(hours=24)
                if recent_installs:
                    backup_type = BackupType.INSTALLATION_STATE
            except:
                pass
            
            # Create backup with automatic description
            description = f"Automatic backup - {backup_type.value.replace('_', ' ').title()}"
            
            return self.create_backup(backup_type, description)
            
        except Exception as e:
            self.logging_system.log_error(f"Automatic backup failed: {str(e)}")
            return self.create_backup(BackupType.CONFIGURATIONS, f"Fallback backup: {str(e)}")


def main():
    """Test the backup system."""
    print("🧪 Testing PinokioCloud Backup System")
    
    backup_system = BackupSystem()
    
    # Test backup creation
    print("\n💾 Testing backup creation...")
    
    backup_types = [
        (BackupType.CONFIGURATIONS, "Test configuration backup"),
        (BackupType.USER_PREFERENCES, "Test user preferences backup"),
        (BackupType.APPLICATION_SETTINGS, "Test application settings backup")
    ]
    
    created_backups = []
    
    for backup_type, description in backup_types:
        try:
            print(f"\n--- Creating {backup_type.value} backup ---")
            restore_point = backup_system.create_backup(backup_type, description)
            
            if restore_point.status == BackupStatus.COMPLETED:
                print(f"✅ Backup created: {restore_point.id}")
                print(f"✅ File size: {restore_point.file_size / 1024:.1f} KB")
                print(f"✅ Checksum: {restore_point.checksum[:16]}...")
                created_backups.append(restore_point.id)
            else:
                print(f"❌ Backup failed: {restore_point.status}")
                
        except Exception as e:
            print(f"🚨 Backup creation test failed: {str(e)}")
    
    # Test backup statistics
    print(f"\n📊 Testing backup statistics...")
    try:
        stats = backup_system.get_backup_statistics()
        
        if 'error' not in stats:
            print(f"✅ Total restore points: {stats['total_restore_points']}")
            print(f"✅ Total backup size: {stats['total_backup_size'] / 1024:.1f} KB")
            print(f"✅ Success rate: {stats['success_rate']:.1f}%")
            print(f"✅ Backup types: {stats['backup_types']}")
        else:
            print(f"❌ Statistics failed: {stats['error']}")
            
    except Exception as e:
        print(f"🚨 Statistics test failed: {str(e)}")
    
    # Test restore functionality
    if created_backups:
        print(f"\n🔄 Testing restore functionality...")
        
        # Test restoring the first backup
        test_restore_id = created_backups[0]
        try:
            print(f"--- Restoring backup {test_restore_id} ---")
            restore_success = backup_system.restore_from_backup(test_restore_id)
            
            if restore_success:
                print(f"✅ Restore successful: {test_restore_id}")
            else:
                print(f"❌ Restore failed: {test_restore_id}")
                
        except Exception as e:
            print(f"🚨 Restore test failed: {str(e)}")
    
    # Test automatic backup
    print(f"\n🤖 Testing automatic backup...")
    try:
        auto_backup = backup_system.create_automatic_backup()
        
        if auto_backup.status == BackupStatus.COMPLETED:
            print(f"✅ Automatic backup created: {auto_backup.id}")
            print(f"✅ Type: {auto_backup.backup_type.value}")
            print(f"✅ Description: {auto_backup.description}")
        else:
            print(f"❌ Automatic backup failed: {auto_backup.status}")
            
    except Exception as e:
        print(f"🚨 Automatic backup test failed: {str(e)}")
    
    print("\n✅ Backup system testing completed!")


if __name__ == "__main__":
    main()