#!/usr/bin/env python3
"""
PinokioCloud Gradio Integration

This module automatically enables Gradio's built-in sharing capabilities.
It provides intelligent Gradio detection, automatic share parameter injection,
and integration with the PinokioCloud tunneling system.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import re
import ast
import time
import threading
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime
import shutil

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from environment_management.file_system import FileSystemManager
from environment_management.json_handler import JSONHandler
from app_analysis.webui_detector import WebUIDetector, WebUIType


class GradioShareMode(Enum):
    """Enumeration of Gradio sharing modes."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    AUTO = "auto"
    FORCED = "forced"


class GradioIntegrationStatus(Enum):
    """Status of Gradio integration."""
    NOT_GRADIO = "not_gradio"
    DETECTED = "detected"
    MODIFIED = "modified"
    ENABLED = "enabled"
    ERROR = "error"


@dataclass
class GradioConfig:
    """Configuration for Gradio integration."""
    app_name: str
    app_path: Path
    share_mode: GradioShareMode = GradioShareMode.AUTO
    share_url: Optional[str] = None
    modified_files: List[str] = field(default_factory=list)
    backup_files: List[str] = field(default_factory=list)
    status: GradioIntegrationStatus = GradioIntegrationStatus.NOT_GRADIO
    detected_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)
    gradio_version: Optional[str] = None
    interface_files: List[str] = field(default_factory=list)
    launch_parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert GradioConfig to dictionary."""
        data = asdict(self)
        data['app_path'] = str(self.app_path)
        data['share_mode'] = self.share_mode.value
        data['status'] = self.status.value
        data['detected_at'] = self.detected_at.isoformat()
        data['last_modified'] = self.last_modified.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GradioConfig':
        """Create GradioConfig from dictionary."""
        data['app_path'] = Path(data['app_path'])
        data['share_mode'] = GradioShareMode(data['share_mode'])
        data['status'] = GradioIntegrationStatus(data['status'])
        data['detected_at'] = datetime.fromisoformat(data['detected_at'])
        data['last_modified'] = datetime.fromisoformat(data['last_modified'])
        return cls(**data)


class GradioIntegration:
    """
    Automatically enables Gradio's built-in sharing capabilities.
    
    This class provides intelligent Gradio detection and automatic share parameter
    injection for seamless public URL generation.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the Gradio integration system."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.gradio_storage_path = self.base_path / "gradio_storage"
        self.gradio_storage_path.mkdir(exist_ok=True)
        
        # Gradio app tracking
        self.gradio_apps: Dict[str, GradioConfig] = {}
        self.integration_lock = threading.RLock()
        
        # Detection patterns
        self.gradio_patterns = self._setup_gradio_patterns()
        self.launch_patterns = self._setup_launch_patterns()
        
        # Initialize dependencies
        self.file_system = FileSystemManager(str(self.base_path))
        self.json_handler = JSONHandler(str(self.base_path))
        self.webui_detector = WebUIDetector(str(self.base_path))
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[callable]] = {
            'gradio_detected': [],
            'share_enabled': [],
            'share_disabled': [],
            'modification_error': []
        }
        
        print("[GradioIntegration] Initialized Gradio integration system")
    
    def detect_gradio_apps(self, app_path: str, app_name: str) -> GradioConfig:
        """
        Detect if an application uses Gradio and analyze its configuration.
        
        Args:
            app_path: Path to the application directory
            app_name: Name of the application
        
        Returns:
            GradioConfig: Gradio configuration information
        """
        print(f"[GradioIntegration] Detecting Gradio in app: {app_name}")
        
        app_path_obj = Path(app_path)
        
        # Create Gradio config
        config = GradioConfig(
            app_name=app_name,
            app_path=app_path_obj
        )
        
        try:
            # Use WebUIDetector to check if it's a Gradio app
            webui_info = self.webui_detector.detect_webui_type(app_path)
            
            if webui_info.ui_type != WebUIType.GRADIO:
                config.status = GradioIntegrationStatus.NOT_GRADIO
                return config
            
            config.status = GradioIntegrationStatus.DETECTED
            config.gradio_version = webui_info.version
            
            # Find Gradio interface files
            interface_files = self._find_gradio_files(app_path_obj)
            config.interface_files = [str(f) for f in interface_files]
            
            # Analyze existing launch parameters
            launch_params = self._analyze_launch_parameters(interface_files)
            config.launch_parameters = launch_params
            
            # Register the app
            with self.integration_lock:
                self.gradio_apps[app_name] = config
            
            # Save configuration
            self._save_gradio_config(config)
            
            # Emit event
            self._emit_event('gradio_detected', config)
            
            print(f"[GradioIntegration] Gradio detected in {app_name}: {len(interface_files)} files")
            return config
            
        except Exception as e:
            print(f"[GradioIntegration] Error detecting Gradio in {app_name}: {e}")
            config.status = GradioIntegrationStatus.ERROR
            return config
    
    def enable_gradio_share(self, app_name: str, force: bool = False) -> bool:
        """
        Enable Gradio share for an application.
        
        Args:
            app_name: Name of the application
            force: Force enable even if already enabled
        
        Returns:
            bool: True if successfully enabled
        """
        print(f"[GradioIntegration] Enabling Gradio share for: {app_name}")
        
        if app_name not in self.gradio_apps:
            print(f"[GradioIntegration] App {app_name} not found in Gradio apps")
            return False
        
        config = self.gradio_apps[app_name]
        
        if config.status != GradioIntegrationStatus.DETECTED and not force:
            print(f"[GradioIntegration] App {app_name} is not a valid Gradio app")
            return False
        
        try:
            # Create backups of all interface files
            self._create_backups(config)
            
            # Modify each interface file to enable sharing
            modified_files = []
            
            for file_path in config.interface_files:
                if self._modify_gradio_file(file_path):
                    modified_files.append(file_path)
            
            if modified_files:
                config.modified_files = modified_files
                config.status = GradioIntegrationStatus.MODIFIED
                config.share_mode = GradioShareMode.ENABLED
                config.last_modified = datetime.now()
                
                # Save updated configuration
                self._save_gradio_config(config)
                
                # Emit event
                self._emit_event('share_enabled', config)
                
                print(f"[GradioIntegration] Share enabled for {app_name}: {len(modified_files)} files modified")
                return True
            else:
                print(f"[GradioIntegration] No files were modified for {app_name}")
                return False
                
        except Exception as e:
            print(f"[GradioIntegration] Error enabling share for {app_name}: {e}")
            config.status = GradioIntegrationStatus.ERROR
            self._emit_event('modification_error', config, str(e))
            return False
    
    def disable_gradio_share(self, app_name: str) -> bool:
        """
        Disable Gradio share for an application by restoring backups.
        
        Args:
            app_name: Name of the application
        
        Returns:
            bool: True if successfully disabled
        """
        print(f"[GradioIntegration] Disabling Gradio share for: {app_name}")
        
        if app_name not in self.gradio_apps:
            return False
        
        config = self.gradio_apps[app_name]
        
        try:
            # Restore backup files
            restored_files = self._restore_backups(config)
            
            if restored_files:
                config.share_mode = GradioShareMode.DISABLED
                config.status = GradioIntegrationStatus.DETECTED
                config.last_modified = datetime.now()
                
                # Save updated configuration
                self._save_gradio_config(config)
                
                # Emit event
                self._emit_event('share_disabled', config)
                
                print(f"[GradioIntegration] Share disabled for {app_name}: {len(restored_files)} files restored")
                return True
            else:
                print(f"[GradioIntegration] No backup files found for {app_name}")
                return False
                
        except Exception as e:
            print(f"[GradioIntegration] Error disabling share for {app_name}: {e}")
            return False
    
    def get_gradio_share_url(self, app_name: str) -> Optional[str]:
        """
        Get the Gradio share URL for an application.
        
        Args:
            app_name: Name of the application
        
        Returns:
            Optional[str]: Share URL if available
        """
        if app_name in self.gradio_apps:
            return self.gradio_apps[app_name].share_url
        return None
    
    def list_gradio_apps(self) -> List[GradioConfig]:
        """
        Get list of all detected Gradio applications.
        
        Returns:
            List[GradioConfig]: List of Gradio configurations
        """
        with self.integration_lock:
            return list(self.gradio_apps.values())
    
    def add_event_callback(self, event: str, callback: callable) -> None:
        """Add a callback for Gradio events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def _find_gradio_files(self, app_path: Path) -> List[Path]:
        """Find all Python files that contain Gradio interfaces."""
        gradio_files = []
        
        try:
            # Search for Python files with Gradio patterns
            for py_file in app_path.rglob("*.py"):
                if self._contains_gradio_interface(py_file):
                    gradio_files.append(py_file)
            
            return gradio_files
            
        except Exception as e:
            print(f"[GradioIntegration] Error finding Gradio files: {e}")
            return []
    
    def _contains_gradio_interface(self, file_path: Path) -> bool:
        """Check if a Python file contains Gradio interface code."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Check for Gradio import and interface patterns
            gradio_indicators = [
                'import gradio',
                'from gradio',
                'gr.Interface',
                'gr.Blocks',
                'gr.ChatInterface',
                'gradio.Interface',
                'gradio.Blocks',
                '.launch(',
                '.queue().launch('
            ]
            
            return any(indicator in content for indicator in gradio_indicators)
            
        except Exception:
            return False
    
    def _analyze_launch_parameters(self, interface_files: List[Path]) -> Dict[str, Any]:
        """Analyze existing launch parameters in Gradio files."""
        launch_params = {}
        
        try:
            for file_path in interface_files:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                # Find launch() calls
                launch_matches = re.finditer(r'\.launch\s*\([^)]*\)', content)
                
                for match in launch_matches:
                    launch_call = match.group(0)
                    
                    # Extract parameters
                    params = self._extract_launch_params(launch_call)
                    launch_params.update(params)
            
            return launch_params
            
        except Exception as e:
            print(f"[GradioIntegration] Error analyzing launch parameters: {e}")
            return {}
    
    def _extract_launch_params(self, launch_call: str) -> Dict[str, Any]:
        """Extract parameters from a launch() call."""
        params = {}
        
        try:
            # Simple parameter extraction using regex
            param_patterns = [
                (r'share\s*=\s*(True|False)', 'share'),
                (r'server_port\s*=\s*(\d+)', 'server_port'),
                (r'server_name\s*=\s*["\']([^"\']+)["\']', 'server_name'),
                (r'auth\s*=\s*\([^)]+\)', 'auth'),
                (r'debug\s*=\s*(True|False)', 'debug'),
                (r'enable_queue\s*=\s*(True|False)', 'enable_queue')
            ]
            
            for pattern, param_name in param_patterns:
                match = re.search(pattern, launch_call)
                if match:
                    value = match.group(1)
                    if value in ['True', 'False']:
                        params[param_name] = value == 'True'
                    elif value.isdigit():
                        params[param_name] = int(value)
                    else:
                        params[param_name] = value
            
            return params
            
        except Exception as e:
            print(f"[GradioIntegration] Error extracting launch params: {e}")
            return {}
    
    def _modify_gradio_file(self, file_path: str) -> bool:
        """Modify a Gradio file to enable sharing."""
        try:
            file_path_obj = Path(file_path)
            content = file_path_obj.read_text(encoding='utf-8', errors='ignore')
            original_content = content
            
            # Find and modify launch() calls
            modified = False
            
            # Pattern 1: .launch() without parameters
            pattern1 = r'\.launch\s*\(\s*\)'
            if re.search(pattern1, content):
                content = re.sub(pattern1, '.launch(share=True)', content)
                modified = True
            
            # Pattern 2: .launch(...) with parameters but no share
            pattern2 = r'\.launch\s*\(([^)]*)\)'
            
            def replace_launch(match):
                params = match.group(1).strip()
                
                # Check if share parameter already exists
                if 'share' in params:
                    # Update existing share parameter
                    params = re.sub(r'share\s*=\s*(True|False)', 'share=True', params)
                else:
                    # Add share parameter
                    if params:
                        params += ', share=True'
                    else:
                        params = 'share=True'
                
                return f'.launch({params})'
            
            new_content = re.sub(pattern2, replace_launch, content)
            if new_content != content:
                content = new_content
                modified = True
            
            # Pattern 3: Handle queue().launch() calls
            pattern3 = r'\.queue\(\)\.launch\s*\(([^)]*)\)'
            
            def replace_queue_launch(match):
                params = match.group(1).strip()
                
                if 'share' not in params:
                    if params:
                        params += ', share=True'
                    else:
                        params = 'share=True'
                else:
                    params = re.sub(r'share\s*=\s*(True|False)', 'share=True', params)
                
                return f'.queue().launch({params})'
            
            new_content = re.sub(pattern3, replace_queue_launch, content)
            if new_content != content:
                content = new_content
                modified = True
            
            # Write modified content if changes were made
            if modified and content != original_content:
                file_path_obj.write_text(content, encoding='utf-8')
                print(f"[GradioIntegration] Modified {file_path_obj.name} to enable sharing")
                return True
            
            return False
            
        except Exception as e:
            print(f"[GradioIntegration] Error modifying file {file_path}: {e}")
            return False
    
    def _create_backups(self, config: GradioConfig) -> None:
        """Create backup copies of files before modification."""
        backup_dir = self.gradio_storage_path / config.app_name / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_files = []
        
        for file_path in config.interface_files:
            try:
                source_file = Path(file_path)
                backup_file = backup_dir / f"{source_file.name}.backup"
                
                shutil.copy2(source_file, backup_file)
                backup_files.append(str(backup_file))
                
                print(f"[GradioIntegration] Created backup: {backup_file}")
                
            except Exception as e:
                print(f"[GradioIntegration] Error creating backup for {file_path}: {e}")
        
        config.backup_files = backup_files
    
    def _restore_backups(self, config: GradioConfig) -> List[str]:
        """Restore backup files."""
        restored_files = []
        
        try:
            backup_dir = self.gradio_storage_path / config.app_name / "backups"
            
            if not backup_dir.exists():
                print(f"[GradioIntegration] No backup directory found for {config.app_name}")
                return []
            
            for backup_file_path in config.backup_files:
                backup_file = Path(backup_file_path)
                
                if backup_file.exists():
                    # Determine original file path
                    original_name = backup_file.name.replace('.backup', '')
                    original_file = None
                    
                    # Find the original file
                    for interface_file in config.interface_files:
                        if Path(interface_file).name == original_name:
                            original_file = Path(interface_file)
                            break
                    
                    if original_file:
                        shutil.copy2(backup_file, original_file)
                        restored_files.append(str(original_file))
                        print(f"[GradioIntegration] Restored {original_file}")
            
            return restored_files
            
        except Exception as e:
            print(f"[GradioIntegration] Error restoring backups: {e}")
            return []
    
    def _setup_gradio_patterns(self) -> List[str]:
        """Set up patterns for detecting Gradio interfaces."""
        return [
            r'import\s+gradio',
            r'from\s+gradio',
            r'gr\.Interface',
            r'gr\.Blocks',
            r'gr\.ChatInterface',
            r'gradio\.Interface',
            r'gradio\.Blocks',
            r'gradio\.ChatInterface'
        ]
    
    def _setup_launch_patterns(self) -> List[str]:
        """Set up patterns for detecting launch() calls."""
        return [
            r'\.launch\s*\(',
            r'\.queue\(\)\.launch\s*\(',
            r'interface\.launch\s*\(',
            r'app\.launch\s*\(',
            r'demo\.launch\s*\('
        ]
    
    def _save_gradio_config(self, config: GradioConfig) -> None:
        """Save Gradio configuration to disk."""
        config_file = self.gradio_storage_path / f"{config.app_name}.json"
        try:
            self.json_handler.write_json_file(str(config_file), config.to_dict())
        except Exception as e:
            print(f"[GradioIntegration] Error saving Gradio config: {e}")
    
    def _load_gradio_configs(self) -> None:
        """Load existing Gradio configurations."""
        try:
            for config_file in self.gradio_storage_path.glob("*.json"):
                try:
                    config_data = self.json_handler.read_json_file(str(config_file))
                    config = GradioConfig.from_dict(config_data)
                    
                    # Only load if app directory still exists
                    if config.app_path.exists():
                        self.gradio_apps[config.app_name] = config
                        print(f"[GradioIntegration] Loaded Gradio config for: {config.app_name}")
                    else:
                        # Remove stale config
                        config_file.unlink()
                        
                except Exception as e:
                    print(f"[GradioIntegration] Error loading config {config_file}: {e}")
                    
        except Exception as e:
            print(f"[GradioIntegration] Error loading Gradio configs: {e}")
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[GradioIntegration] Error in event callback: {e}")


def main():
    """Test the Gradio integration functionality."""
    print("Testing GradioIntegration...")
    
    integration = GradioIntegration()
    
    # Test detecting Gradio apps (would need actual Gradio app)
    try:
        # This would detect Gradio in an actual app directory
        # config = integration.detect_gradio_apps("/path/to/gradio/app", "test_app")
        # print(f"Gradio detection result: {config.status}")
        
        # List Gradio apps
        gradio_apps = integration.list_gradio_apps()
        print(f"Gradio apps: {len(gradio_apps)}")
        
        print("GradioIntegration test completed")
        
    except Exception as e:
        print(f"GradioIntegration test error: {e}")


if __name__ == "__main__":
    main()