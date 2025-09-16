#!/usr/bin/env python3
"""
PinokioCloud Lightning.ai Optimizer

This module adds Lightning.ai-specific features and optimizations including
team workspaces, collaboration features, resource sharing, and Lightning.ai
Studio integration for optimal performance in the Lightning.ai environment.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import subprocess
import threading
import requests
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import json

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from cloud_detection.cloud_detector import CloudDetector, CloudPlatform
from cloud_detection.resource_assessor import ResourceAssessor
from environment_management.file_system import FileSystemManager
from environment_management.shell_runner import ShellRunner
from environment_management.json_handler import JSONHandler
from running.process_tracker import ProcessTracker
from tunneling.ngrok_manager import NgrokManager


class LightningWorkspaceType(Enum):
    """Types of Lightning.ai workspaces."""
    STUDIO = "studio"
    APP = "app"
    FLOW = "flow"
    RESEARCH = "research"
    TEAM = "team"


class LightningGPUType(Enum):
    """Types of GPUs available in Lightning.ai."""
    T4 = "T4"
    V100 = "V100"
    A100 = "A100"
    H100 = "H100"
    NONE = "None"


class LightningTier(Enum):
    """Lightning.ai subscription tiers."""
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"
    UNKNOWN = "unknown"


@dataclass
class LightningFeatures:
    """Lightning.ai-specific features and capabilities."""
    workspace_type: LightningWorkspaceType
    gpu_type: LightningGPUType
    gpu_memory_gb: float
    tier: LightningTier
    team_enabled: bool = False
    collaboration_enabled: bool = False
    shared_storage_gb: float = 0.0
    workspace_id: Optional[str] = None
    team_id: Optional[str] = None
    user_id: Optional[str] = None
    project_name: Optional[str] = None
    studio_version: Optional[str] = None
    python_version: str = "3.9"
    lightning_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert LightningFeatures to dictionary."""
        data = asdict(self)
        data['workspace_type'] = self.workspace_type.value
        data['gpu_type'] = self.gpu_type.value
        data['tier'] = self.tier.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LightningFeatures':
        """Create LightningFeatures from dictionary."""
        data['workspace_type'] = LightningWorkspaceType(data['workspace_type'])
        data['gpu_type'] = LightningGPUType(data['gpu_type'])
        data['tier'] = LightningTier(data['tier'])
        return cls(**data)


@dataclass
class LightningConfig:
    """Configuration for Lightning.ai optimization."""
    enable_team_features: bool = True
    auto_setup_collaboration: bool = True
    optimize_shared_storage: bool = True
    sync_with_team: bool = True
    backup_to_shared: bool = True
    monitor_team_resources: bool = True
    auto_share_outputs: bool = True
    preferred_tunnel_type: str = "lightning_share"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert LightningConfig to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LightningConfig':
        """Create LightningConfig from dictionary."""
        return cls(**data)


class LightningOptimizer:
    """
    Adds Lightning.ai-specific features and optimizations.
    
    This class provides comprehensive Lightning.ai integration including
    team workspaces, collaboration features, resource sharing, and
    Lightning.ai Studio optimization.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the Lightning.ai optimizer."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.lightning_storage_path = self.base_path / "lightning_storage"
        self.lightning_storage_path.mkdir(exist_ok=True)
        
        # Lightning.ai-specific paths
        self.teamspace_path = Path("/teamspace")
        self.studio_path = Path("/studio")
        self.shared_path = Path("/shared")
        
        # Configuration
        self.config = LightningConfig()
        self.features = None
        
        # Initialize dependencies
        self.cloud_detector = CloudDetector()
        self.resource_assessor = ResourceAssessor()
        self.file_system = FileSystemManager(str(self.base_path))
        self.shell_runner = ShellRunner(str(self.base_path))
        self.json_handler = JSONHandler(str(self.base_path))
        self.process_tracker = ProcessTracker(str(self.base_path))
        
        # Team synchronization
        self.sync_monitor_active = False
        self.sync_monitor_thread = None
        self.sync_check_interval = 180.0  # 3 minutes
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[callable]] = {
            'team_workspace_setup': [],
            'collaboration_enabled': [],
            'shared_storage_mounted': [],
            'team_sync_completed': [],
            'resource_shared': []
        }
        
        # Verify we're on Lightning.ai and initialize
        if self.is_lightning_environment():
            self._initialize_lightning_features()
        
        print(f"[LightningOptimizer] Initialized for Lightning.ai environment: {self.is_lightning_environment()}")
    
    def is_lightning_environment(self) -> bool:
        """
        Check if we're running on Lightning.ai.
        
        Returns:
            bool: True if running on Lightning.ai
        """
        platform_info = self.cloud_detector.detect_platform()
        return platform_info.platform == CloudPlatform.LIGHTNING_AI
    
    def setup_team_workspace(self) -> bool:
        """
        Set up team workspace and collaboration features.
        
        Returns:
            bool: True if team workspace was set up successfully
        """
        if not self.is_lightning_environment():
            print("[LightningOptimizer] Not in Lightning.ai environment, skipping team setup")
            return False
        
        print("[LightningOptimizer] Setting up team workspace...")
        
        try:
            # Check if teamspace is available
            if self.teamspace_path.exists():
                print(f"[LightningOptimizer] Teamspace found at {self.teamspace_path}")
                
                # Create PinokioCloud team directory
                team_pinokio_path = self.teamspace_path / "PinokioCloud"
                team_pinokio_path.mkdir(exist_ok=True)
                
                # Set up shared directories
                shared_dirs = [
                    team_pinokio_path / "shared_models",
                    team_pinokio_path / "shared_datasets",
                    team_pinokio_path / "shared_outputs",
                    team_pinokio_path / "team_configs"
                ]
                
                for shared_dir in shared_dirs:
                    shared_dir.mkdir(exist_ok=True)
                
                # Create symlinks to shared resources
                local_shared_path = self.base_path / "team_shared"
                if not local_shared_path.exists():
                    local_shared_path.symlink_to(team_pinokio_path)
                
                # Update features
                if self.features:
                    self.features.team_enabled = True
                    self.features.collaboration_enabled = True
                    self.features.shared_storage_gb = self._get_teamspace_size()
                
                # Emit event
                self._emit_event('team_workspace_setup', {
                    'teamspace_path': str(team_pinokio_path),
                    'shared_dirs': [str(d) for d in shared_dirs]
                })
                
                print("[LightningOptimizer] Team workspace setup complete")
                return True
            else:
                print("[LightningOptimizer] Teamspace not available")
                return False
                
        except Exception as e:
            print(f"[LightningOptimizer] Error setting up team workspace: {e}")
            return False
    
    def enable_collaboration_features(self) -> bool:
        """
        Enable Lightning.ai collaboration features.
        
        Returns:
            bool: True if collaboration features were enabled successfully
        """
        print("[LightningOptimizer] Enabling collaboration features...")
        
        try:
            if not self.features or not self.features.team_enabled:
                print("[LightningOptimizer] Team workspace not available")
                return False
            
            # Set up collaboration configuration
            collab_config = {
                'real_time_sync': True,
                'shared_notebooks': True,
                'shared_experiments': True,
                'team_notifications': True,
                'resource_sharing': True
            }
            
            # Create collaboration config file
            collab_config_path = self.lightning_storage_path / "collaboration.json"
            self.json_handler.write_json_file(str(collab_config_path), collab_config)
            
            # Set up environment variables for collaboration
            collab_env_vars = {
                'LIGHTNING_TEAM_MODE': 'true',
                'LIGHTNING_COLLABORATION': 'enabled',
                'LIGHTNING_SHARED_STORAGE': str(self.teamspace_path / "PinokioCloud"),
                'PINOKIO_TEAM_MODE': 'true'
            }
            
            for key, value in collab_env_vars.items():
                os.environ[key] = value
            
            # Start team synchronization
            if self.config.sync_with_team:
                self._start_team_sync()
            
            # Emit event
            self._emit_event('collaboration_enabled', collab_config)
            
            print("[LightningOptimizer] Collaboration features enabled")
            return True
            
        except Exception as e:
            print(f"[LightningOptimizer] Error enabling collaboration: {e}")
            return False
    
    def optimize_shared_storage(self) -> bool:
        """
        Optimize shared storage for team collaboration.
        
        Returns:
            bool: True if storage was optimized successfully
        """
        print("[LightningOptimizer] Optimizing shared storage...")
        
        try:
            if not self.teamspace_path.exists():
                print("[LightningOptimizer] Shared storage not available")
                return False
            
            # Create optimized storage structure
            storage_structure = {
                'models': self.teamspace_path / "PinokioCloud" / "shared_models",
                'datasets': self.teamspace_path / "PinokioCloud" / "shared_datasets",
                'outputs': self.teamspace_path / "PinokioCloud" / "shared_outputs",
                'cache': self.teamspace_path / "PinokioCloud" / "shared_cache",
                'configs': self.teamspace_path / "PinokioCloud" / "team_configs"
            }
            
            # Create directories and set up symlinks
            for storage_type, storage_path in storage_structure.items():
                storage_path.mkdir(parents=True, exist_ok=True)
                
                # Create local symlink
                local_link = self.base_path / f"shared_{storage_type}"
                if not local_link.exists():
                    local_link.symlink_to(storage_path)
            
            # Set up storage optimization
            self._setup_storage_deduplication()
            
            # Configure storage environment variables
            storage_env_vars = {
                'LIGHTNING_SHARED_MODELS': str(storage_structure['models']),
                'LIGHTNING_SHARED_DATASETS': str(storage_structure['datasets']),
                'LIGHTNING_SHARED_OUTPUTS': str(storage_structure['outputs']),
                'PINOKIO_SHARED_STORAGE': str(self.teamspace_path / "PinokioCloud")
            }
            
            for key, value in storage_env_vars.items():
                os.environ[key] = value
            
            # Emit event
            self._emit_event('shared_storage_mounted', storage_structure)
            
            print("[LightningOptimizer] Shared storage optimization complete")
            return True
            
        except Exception as e:
            print(f"[LightningOptimizer] Error optimizing shared storage: {e}")
            return False
    
    def setup_lightning_studio_integration(self) -> Dict[str, Any]:
        """
        Set up Lightning.ai Studio integration.
        
        Returns:
            Dict[str, Any]: Studio integration configuration
        """
        print("[LightningOptimizer] Setting up Lightning.ai Studio integration...")
        
        try:
            studio_config = {
                'studio_available': False,
                'studio_version': None,
                'jupyter_enabled': False,
                'vscode_enabled': False,
                'tensorboard_enabled': False
            }
            
            # Check if Lightning Studio is available
            if self.studio_path.exists():
                studio_config['studio_available'] = True
                
                # Detect Studio version
                try:
                    result = self.shell_runner.run_command(
                        "lightning --version", capture_output=True
                    )
                    if result.returncode == 0:
                        studio_config['studio_version'] = result.stdout.strip()
                        if self.features:
                            self.features.studio_version = result.stdout.strip()
                except Exception:
                    pass
                
                # Check for Jupyter
                if (self.studio_path / "jupyter").exists() or os.path.exists("/usr/local/bin/jupyter"):
                    studio_config['jupyter_enabled'] = True
                
                # Check for VSCode
                if (self.studio_path / "code").exists() or os.path.exists("/usr/local/bin/code"):
                    studio_config['vscode_enabled'] = True
                
                # Check for TensorBoard
                try:
                    result = self.shell_runner.run_command(
                        "tensorboard --version", capture_output=True
                    )
                    if result.returncode == 0:
                        studio_config['tensorboard_enabled'] = True
                except Exception:
                    pass
            
            # Set up Studio-specific optimizations
            if studio_config['studio_available']:
                self._optimize_studio_environment()
            
            return studio_config
            
        except Exception as e:
            print(f"[LightningOptimizer] Error setting up Studio integration: {e}")
            return {'error': str(e)}
    
    def optimize_for_lightning(self) -> Dict[str, bool]:
        """
        Apply comprehensive Lightning.ai optimizations.
        
        Returns:
            Dict[str, bool]: Results of optimization operations
        """
        print("[LightningOptimizer] Applying Lightning.ai optimizations...")
        
        results = {
            'team_workspace': False,
            'collaboration': False,
            'shared_storage': False,
            'studio_integration': False,
            'resource_optimization': False
        }
        
        try:
            # 1. Set up team workspace
            if self.config.enable_team_features:
                results['team_workspace'] = self.setup_team_workspace()
            
            # 2. Enable collaboration features
            if self.config.auto_setup_collaboration:
                results['collaboration'] = self.enable_collaboration_features()
            
            # 3. Optimize shared storage
            if self.config.optimize_shared_storage:
                results['shared_storage'] = self.optimize_shared_storage()
            
            # 4. Set up Studio integration
            studio_config = self.setup_lightning_studio_integration()
            results['studio_integration'] = studio_config.get('studio_available', False)
            
            # 5. Optimize resources
            results['resource_optimization'] = self._optimize_lightning_resources()
            
            success_count = sum(results.values())
            print(f"[LightningOptimizer] Optimization complete: {success_count}/5 successful")
            
            return results
            
        except Exception as e:
            print(f"[LightningOptimizer] Error during optimization: {e}")
            return results
    
    def share_with_team(self, resource_path: str, resource_type: str = "output") -> bool:
        """
        Share a resource with the team.
        
        Args:
            resource_path: Path to the resource to share
            resource_type: Type of resource (model, dataset, output, config)
        
        Returns:
            bool: True if successfully shared
        """
        if not self.features or not self.features.team_enabled:
            print("[LightningOptimizer] Team features not available")
            return False
        
        print(f"[LightningOptimizer] Sharing {resource_type} with team: {resource_path}")
        
        try:
            source_path = Path(resource_path)
            if not source_path.exists():
                print(f"[LightningOptimizer] Resource path does not exist: {resource_path}")
                return False
            
            # Determine target directory based on resource type
            team_base = self.teamspace_path / "PinokioCloud"
            target_mapping = {
                'model': team_base / "shared_models",
                'dataset': team_base / "shared_datasets", 
                'output': team_base / "shared_outputs",
                'config': team_base / "team_configs"
            }
            
            target_dir = target_mapping.get(resource_type, team_base / "shared_outputs")
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            target_path = target_dir / target_name
            
            # Copy resource to shared location
            if source_path.is_file():
                self.file_system.copy_file(str(source_path), str(target_path))
            else:
                self.file_system.copy_directory(str(source_path), str(target_path))
            
            # Create metadata file
            metadata = {
                'shared_by': os.environ.get('USER', 'unknown'),
                'shared_at': datetime.now().isoformat(),
                'resource_type': resource_type,
                'original_path': str(source_path),
                'shared_path': str(target_path),
                'size_bytes': self._get_path_size(target_path)
            }
            
            metadata_file = target_path.parent / f"{target_path.name}.metadata.json"
            self.json_handler.write_json_file(str(metadata_file), metadata)
            
            # Emit event
            self._emit_event('resource_shared', metadata)
            
            print(f"[LightningOptimizer] Resource shared: {target_path}")
            return True
            
        except Exception as e:
            print(f"[LightningOptimizer] Error sharing resource: {e}")
            return False
    
    def get_team_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get list of shared team resources.
        
        Returns:
            Dict[str, List[Dict[str, Any]]]: Categorized team resources
        """
        if not self.features or not self.features.team_enabled:
            return {}
        
        try:
            team_base = self.teamspace_path / "PinokioCloud"
            
            resources = {
                'models': [],
                'datasets': [],
                'outputs': [],
                'configs': []
            }
            
            resource_dirs = {
                'models': team_base / "shared_models",
                'datasets': team_base / "shared_datasets",
                'outputs': team_base / "shared_outputs",
                'configs': team_base / "team_configs"
            }
            
            for resource_type, resource_dir in resource_dirs.items():
                if resource_dir.exists():
                    for item in resource_dir.iterdir():
                        if item.is_file() and not item.name.endswith('.metadata.json'):
                            # Get metadata if available
                            metadata_file = item.parent / f"{item.name}.metadata.json"
                            metadata = {}
                            
                            if metadata_file.exists():
                                try:
                                    metadata = self.json_handler.read_json_file(str(metadata_file))
                                except Exception:
                                    pass
                            
                            resource_info = {
                                'name': item.name,
                                'path': str(item),
                                'size_bytes': item.stat().st_size,
                                'modified_at': datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                                'metadata': metadata
                            }
                            
                            resources[resource_type].append(resource_info)
            
            return resources
            
        except Exception as e:
            print(f"[LightningOptimizer] Error getting team resources: {e}")
            return {}
    
    def get_lightning_workspace_info(self) -> Dict[str, Any]:
        """
        Get Lightning.ai workspace information.
        
        Returns:
            Dict[str, Any]: Workspace information
        """
        if not self.is_lightning_environment():
            return {'error': 'Not in Lightning.ai environment'}
        
        try:
            workspace_info = {
                'workspace_type': self.features.workspace_type.value if self.features else 'unknown',
                'gpu_type': self.features.gpu_type.value if self.features else 'none',
                'gpu_memory_gb': self.features.gpu_memory_gb if self.features else 0.0,
                'tier': self.features.tier.value if self.features else 'unknown',
                'team_enabled': self.features.team_enabled if self.features else False,
                'collaboration_enabled': self.features.collaboration_enabled if self.features else False,
                'shared_storage_gb': self.features.shared_storage_gb if self.features else 0.0
            }
            
            # Add workspace paths
            workspace_info['paths'] = {
                'teamspace': str(self.teamspace_path) if self.teamspace_path.exists() else None,
                'studio': str(self.studio_path) if self.studio_path.exists() else None,
                'shared': str(self.shared_path) if self.shared_path.exists() else None
            }
            
            # Add resource usage
            system_resources = self.resource_assessor.assess_resources()
            workspace_info['resources'] = {
                'cpu_cores': system_resources.cpu.cores_logical,
                'ram_gb': system_resources.memory.total_gb,
                'storage_gb': system_resources.total_storage_gb,
                'gpu_available': system_resources.gpu_available
            }
            
            return workspace_info
            
        except Exception as e:
            print(f"[LightningOptimizer] Error getting workspace info: {e}")
            return {'error': str(e)}
    
    def _initialize_lightning_features(self) -> None:
        """Initialize Lightning.ai-specific features."""
        try:
            # Get system resources
            system_resources = self.resource_assessor.assess_resources()
            
            # Detect GPU configuration
            gpu_info = self._detect_lightning_gpu()
            
            # Detect workspace type
            workspace_type = self._detect_workspace_type()
            
            # Detect Lightning.ai tier
            tier = self._detect_lightning_tier()
            
            # Create features object
            self.features = LightningFeatures(
                workspace_type=workspace_type,
                gpu_type=gpu_info.get('gpu_type', LightningGPUType.NONE),
                gpu_memory_gb=gpu_info.get('gpu_memory_gb', 0.0),
                tier=tier,
                team_enabled=self.teamspace_path.exists(),
                collaboration_enabled=False,  # Will be set up later
                workspace_id=os.environ.get('LIGHTNING_WORKSPACE_ID'),
                team_id=os.environ.get('LIGHTNING_TEAM_ID'),
                user_id=os.environ.get('LIGHTNING_USER_ID'),
                project_name=os.environ.get('LIGHTNING_PROJECT_NAME')
            )
            
            print(f"[LightningOptimizer] Initialized features: {self.features.workspace_type.value}, "
                  f"{self.features.gpu_type.value}, {self.features.tier.value}")
            
        except Exception as e:
            print(f"[LightningOptimizer] Error initializing Lightning.ai features: {e}")
    
    def _detect_lightning_gpu(self) -> Dict[str, Any]:
        """Detect Lightning.ai GPU configuration."""
        gpu_info = {
            'gpu_type': LightningGPUType.NONE,
            'gpu_memory_gb': 0.0
        }
        
        try:
            result = self.shell_runner.run_command("nvidia-smi", capture_output=True)
            
            if result.returncode == 0:
                output = result.stdout
                
                # Detect GPU type
                if "Tesla T4" in output:
                    gpu_info['gpu_type'] = LightningGPUType.T4
                    gpu_info['gpu_memory_gb'] = 15.0
                elif "Tesla V100" in output:
                    gpu_info['gpu_type'] = LightningGPUType.V100
                    gpu_info['gpu_memory_gb'] = 16.0
                elif "A100" in output:
                    gpu_info['gpu_type'] = LightningGPUType.A100
                    gpu_info['gpu_memory_gb'] = 40.0
                elif "H100" in output:
                    gpu_info['gpu_type'] = LightningGPUType.H100
                    gpu_info['gpu_memory_gb'] = 80.0
                
                print(f"[LightningOptimizer] GPU detected: {gpu_info['gpu_type'].value}")
            
            return gpu_info
            
        except Exception as e:
            print(f"[LightningOptimizer] Error detecting GPU: {e}")
            return gpu_info
    
    def _detect_workspace_type(self) -> LightningWorkspaceType:
        """Detect Lightning.ai workspace type."""
        try:
            # Check environment variables and paths
            if os.environ.get('LIGHTNING_STUDIO_MODE'):
                return LightningWorkspaceType.STUDIO
            elif self.teamspace_path.exists():
                return LightningWorkspaceType.TEAM
            elif os.environ.get('LIGHTNING_APP_MODE'):
                return LightningWorkspaceType.APP
            elif os.environ.get('LIGHTNING_FLOW_MODE'):
                return LightningWorkspaceType.FLOW
            else:
                return LightningWorkspaceType.RESEARCH
                
        except Exception:
            return LightningWorkspaceType.RESEARCH
    
    def _detect_lightning_tier(self) -> LightningTier:
        """Detect Lightning.ai subscription tier."""
        try:
            # This is heuristic-based since Lightning.ai doesn't directly expose tier info
            if self.teamspace_path.exists():
                return LightningTier.TEAM
            elif os.environ.get('LIGHTNING_PRO_MODE'):
                return LightningTier.PRO
            else:
                return LightningTier.FREE
                
        except Exception:
            return LightningTier.UNKNOWN
    
    def _get_teamspace_size(self) -> float:
        """Get teamspace storage size in GB."""
        try:
            if self.teamspace_path.exists():
                stat = os.statvfs(str(self.teamspace_path))
                total_bytes = stat.f_blocks * stat.f_frsize
                return total_bytes / (1024 ** 3)  # Convert to GB
            return 0.0
        except Exception:
            return 0.0
    
    def _setup_storage_deduplication(self) -> None:
        """Set up storage deduplication for team resources."""
        try:
            # Create deduplication index
            dedup_index_path = self.lightning_storage_path / "dedup_index.json"
            
            if not dedup_index_path.exists():
                dedup_index = {
                    'files': {},
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
                self.json_handler.write_json_file(str(dedup_index_path), dedup_index)
            
            print("[LightningOptimizer] Storage deduplication configured")
            
        except Exception as e:
            print(f"[LightningOptimizer] Error setting up deduplication: {e}")
    
    def _optimize_studio_environment(self) -> None:
        """Optimize Lightning.ai Studio environment."""
        try:
            # Set Studio-specific environment variables
            studio_env_vars = {
                'LIGHTNING_STUDIO_OPTIMIZED': 'true',
                'JUPYTER_ENABLE_LAB': 'yes',
                'LIGHTNING_PINOKIO_MODE': 'true'
            }
            
            for key, value in studio_env_vars.items():
                os.environ[key] = value
            
            print("[LightningOptimizer] Studio environment optimized")
            
        except Exception as e:
            print(f"[LightningOptimizer] Error optimizing Studio: {e}")
    
    def _optimize_lightning_resources(self) -> bool:
        """Optimize Lightning.ai resource usage."""
        try:
            # Set resource optimization environment variables
            resource_env_vars = {
                'LIGHTNING_RESOURCE_OPTIMIZED': 'true',
                'OMP_NUM_THREADS': str(os.cpu.cores_logical()),
                'LIGHTNING_GPU_OPTIMIZED': 'true' if self.features and self.features.gpu_type != LightningGPUType.NONE else 'false'
            }
            
            for key, value in resource_env_vars.items():
                os.environ[key] = value
            
            print("[LightningOptimizer] Resource optimization applied")
            return True
            
        except Exception as e:
            print(f"[LightningOptimizer] Error optimizing resources: {e}")
            return False
    
    def _get_path_size(self, path: Path) -> int:
        """Get total size of a path in bytes."""
        try:
            if path.is_file():
                return path.stat().st_size
            elif path.is_dir():
                total_size = 0
                for file_path in path.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                return total_size
            return 0
        except Exception:
            return 0
    
    def _start_team_sync(self) -> None:
        """Start team synchronization monitoring."""
        try:
            if self.sync_monitor_thread is None or not self.sync_monitor_thread.is_alive():
                self.sync_monitor_active = True
                self.sync_monitor_thread = threading.Thread(
                    target=self._team_sync_loop,
                    daemon=True
                )
                self.sync_monitor_thread.start()
                print("[LightningOptimizer] Started team synchronization")
        except Exception as e:
            print(f"[LightningOptimizer] Error starting team sync: {e}")
    
    def _team_sync_loop(self) -> None:
        """Main team synchronization loop."""
        while self.sync_monitor_active:
            try:
                # Check for new team resources
                team_resources = self.get_team_resources()
                
                # Emit sync event
                self._emit_event('team_sync_completed', {
                    'timestamp': datetime.now().isoformat(),
                    'resources_count': sum(len(resources) for resources in team_resources.values())
                })
                
                time.sleep(self.sync_check_interval)
                
            except Exception as e:
                print(f"[LightningOptimizer] Error in team sync loop: {e}")
                time.sleep(self.sync_check_interval)
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[LightningOptimizer] Error in event callback: {e}")
    
    def add_event_callback(self, event: str, callback: callable) -> None:
        """Add a callback for Lightning.ai events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def stop_team_sync(self) -> None:
        """Stop team synchronization."""
        self.sync_monitor_active = False
        if self.sync_monitor_thread and self.sync_monitor_thread.is_alive():
            self.sync_monitor_thread.join(timeout=5.0)
        print("[LightningOptimizer] Stopped team synchronization")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_team_sync()


def main():
    """Test the Lightning.ai optimizer functionality."""
    print("Testing LightningOptimizer...")
    
    optimizer = LightningOptimizer()
    
    # Check if we're on Lightning.ai
    is_lightning = optimizer.is_lightning_environment()
    print(f"Lightning.ai environment detected: {is_lightning}")
    
    if is_lightning:
        # Test Lightning.ai-specific features
        workspace_info = optimizer.get_lightning_workspace_info()
        print(f"Workspace info: {workspace_info}")
        
        # Test optimization
        results = optimizer.optimize_for_lightning()
        print(f"Optimization results: {results}")
        
        # Test team resources
        team_resources = optimizer.get_team_resources()
        print(f"Team resources: {sum(len(r) for r in team_resources.values())} items")
    else:
        print("Not in Lightning.ai environment, basic functionality tested")
    
    print("LightningOptimizer test completed")


if __name__ == "__main__":
    main()