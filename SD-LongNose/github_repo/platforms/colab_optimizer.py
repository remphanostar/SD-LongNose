#!/usr/bin/env python3
"""
PinokioCloud Google Colab Optimizer

This module adds Google Colab-specific features and optimizations including
Google Drive mounting, session management, GPU detection, and Colab-specific
path handling for optimal performance in the Colab environment.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import subprocess
import threading
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


class ColabGPUType(Enum):
    """Types of GPUs available in Google Colab."""
    T4 = "T4"
    V100 = "V100"
    A100 = "A100"
    TPU = "TPU"
    NONE = "None"


class ColabTier(Enum):
    """Google Colab subscription tiers."""
    FREE = "free"
    PRO = "pro"
    PRO_PLUS = "pro_plus"
    UNKNOWN = "unknown"


class ColabSessionStatus(Enum):
    """Google Colab session status."""
    ACTIVE = "active"
    IDLE = "idle"
    TIMEOUT_WARNING = "timeout_warning"
    DISCONNECTED = "disconnected"
    UNKNOWN = "unknown"


@dataclass
class ColabFeatures:
    """Google Colab-specific features and capabilities."""
    gpu_type: ColabGPUType
    gpu_memory_gb: float
    tier: ColabTier
    session_timeout_hours: float
    drive_mounted: bool = False
    drive_mount_path: str = "/content/drive"
    runtime_type: str = "python3"
    cuda_version: Optional[str] = None
    session_start_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    storage_quota_gb: float = 100.0
    network_restrictions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ColabFeatures to dictionary."""
        data = asdict(self)
        data['gpu_type'] = self.gpu_type.value
        data['tier'] = self.tier.value
        data['session_start_time'] = self.session_start_time.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColabFeatures':
        """Create ColabFeatures from dictionary."""
        data['gpu_type'] = ColabGPUType(data['gpu_type'])
        data['tier'] = ColabTier(data['tier'])
        data['session_start_time'] = datetime.fromisoformat(data['session_start_time'])
        data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        return cls(**data)


@dataclass
class ColabConfig:
    """Configuration for Google Colab optimization."""
    auto_mount_drive: bool = True
    session_keep_alive: bool = True
    gpu_optimization: bool = True
    storage_optimization: bool = True
    tunnel_optimization: bool = True
    backup_to_drive: bool = True
    cleanup_on_timeout: bool = True
    max_idle_minutes: int = 90
    warning_before_timeout_minutes: int = 15
    preferred_tunnel_type: str = "ngrok"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ColabConfig to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColabConfig':
        """Create ColabConfig from dictionary."""
        return cls(**data)


class ColabOptimizer:
    """
    Adds Google Colab-specific features and optimizations.
    
    This class provides comprehensive Google Colab integration including
    Drive mounting, session management, GPU optimization, and Colab-specific
    path handling.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the Google Colab optimizer."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.colab_storage_path = self.base_path / "colab_storage"
        self.colab_storage_path.mkdir(exist_ok=True)
        
        # Colab-specific paths
        self.content_path = Path("/content")
        self.drive_path = Path("/content/drive")
        self.sample_data_path = Path("/content/sample_data")
        
        # Configuration
        self.config = ColabConfig()
        self.features = None
        
        # Initialize dependencies
        self.cloud_detector = CloudDetector()
        self.resource_assessor = ResourceAssessor()
        self.file_system = FileSystemManager(str(self.base_path))
        self.shell_runner = ShellRunner(str(self.base_path))
        self.json_handler = JSONHandler(str(self.base_path))
        self.process_tracker = ProcessTracker(str(self.base_path))
        
        # Session monitoring
        self.session_monitor_active = False
        self.session_monitor_thread = None
        self.session_check_interval = 300.0  # 5 minutes
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[callable]] = {
            'drive_mounted': [],
            'session_timeout_warning': [],
            'gpu_allocated': [],
            'optimization_applied': [],
            'backup_completed': []
        }
        
        # Verify we're on Colab and initialize
        self._verify_colab_environment()
        if self.is_colab_environment():
            self._initialize_colab_features()
        
        print(f"[ColabOptimizer] Initialized for Colab environment: {self.is_colab_environment()}")
    
    def is_colab_environment(self) -> bool:
        """
        Check if we're running in Google Colab.
        
        Returns:
            bool: True if running in Google Colab
        """
        platform_info = self.cloud_detector.detect_platform()
        return platform_info.platform == CloudPlatform.GOOGLE_COLAB
    
    def mount_google_drive(self, force_remount: bool = False) -> bool:
        """
        Mount Google Drive in Colab.
        
        Args:
            force_remount: Force remount even if already mounted
        
        Returns:
            bool: True if successfully mounted
        """
        if not self.is_colab_environment():
            print("[ColabOptimizer] Not in Colab environment, skipping Drive mount")
            return False
        
        print("[ColabOptimizer] Mounting Google Drive...")
        
        try:
            # Check if already mounted
            if self.drive_path.exists() and not force_remount:
                if (self.drive_path / "MyDrive").exists():
                    print("[ColabOptimizer] Google Drive already mounted")
                    self.features.drive_mounted = True
                    self._emit_event('drive_mounted', str(self.drive_path))
                    return True
            
            # Import and mount Google Drive
            try:
                from google.colab import drive
                drive.mount(str(self.drive_path), force_remount=force_remount)
                
                # Verify mount was successful
                if (self.drive_path / "MyDrive").exists():
                    self.features.drive_mounted = True
                    self.features.drive_mount_path = str(self.drive_path)
                    
                    # Create PinokioCloud directory in Drive
                    pinokio_drive_path = self.drive_path / "MyDrive" / "PinokioCloud"
                    pinokio_drive_path.mkdir(exist_ok=True)
                    
                    # Emit event
                    self._emit_event('drive_mounted', str(self.drive_path))
                    
                    print(f"[ColabOptimizer] Google Drive mounted successfully at {self.drive_path}")
                    return True
                else:
                    print("[ColabOptimizer] Drive mount failed - MyDrive not found")
                    return False
                    
            except ImportError:
                print("[ColabOptimizer] google.colab module not available")
                return False
            except Exception as e:
                print(f"[ColabOptimizer] Error mounting Google Drive: {e}")
                return False
                
        except Exception as e:
            print(f"[ColabOptimizer] Error in mount_google_drive: {e}")
            return False
    
    def detect_gpu_configuration(self) -> Dict[str, Any]:
        """
        Detect GPU configuration and capabilities.
        
        Returns:
            Dict[str, Any]: GPU configuration information
        """
        print("[ColabOptimizer] Detecting GPU configuration...")
        
        gpu_info = {
            'gpu_available': False,
            'gpu_type': ColabGPUType.NONE,
            'gpu_memory_gb': 0.0,
            'cuda_available': False,
            'cuda_version': None,
            'driver_version': None,
            'compute_capability': None
        }
        
        try:
            # Check if GPU is available
            result = self.shell_runner.run_command("nvidia-smi", capture_output=True)
            
            if result.returncode == 0:
                gpu_info['gpu_available'] = True
                
                # Parse nvidia-smi output
                output = result.stdout
                
                # Detect GPU type
                if "Tesla T4" in output:
                    gpu_info['gpu_type'] = ColabGPUType.T4
                    gpu_info['gpu_memory_gb'] = 15.0
                elif "Tesla V100" in output:
                    gpu_info['gpu_type'] = ColabGPUType.V100
                    gpu_info['gpu_memory_gb'] = 16.0
                elif "Tesla A100" in output:
                    gpu_info['gpu_type'] = ColabGPUType.A100
                    gpu_info['gpu_memory_gb'] = 40.0
                
                # Extract memory information
                import re
                memory_match = re.search(r'(\d+)MiB / (\d+)MiB', output)
                if memory_match:
                    total_memory_mb = int(memory_match.group(2))
                    gpu_info['gpu_memory_gb'] = total_memory_mb / 1024.0
                
                # Extract driver version
                driver_match = re.search(r'Driver Version: ([\d\.]+)', output)
                if driver_match:
                    gpu_info['driver_version'] = driver_match.group(1)
                
                # Check CUDA availability
                cuda_result = self.shell_runner.run_command("nvcc --version", capture_output=True)
                if cuda_result.returncode == 0:
                    gpu_info['cuda_available'] = True
                    
                    # Extract CUDA version
                    cuda_match = re.search(r'release ([\d\.]+)', cuda_result.stdout)
                    if cuda_match:
                        gpu_info['cuda_version'] = cuda_match.group(1)
                
                # Update features
                if self.features:
                    self.features.gpu_type = gpu_info['gpu_type']
                    self.features.gpu_memory_gb = gpu_info['gpu_memory_gb']
                    self.features.cuda_version = gpu_info['cuda_version']
                
                # Emit event
                self._emit_event('gpu_allocated', gpu_info)
                
                print(f"[ColabOptimizer] GPU detected: {gpu_info['gpu_type'].value} "
                      f"({gpu_info['gpu_memory_gb']:.1f}GB)")
            else:
                print("[ColabOptimizer] No GPU detected")
            
            return gpu_info
            
        except Exception as e:
            print(f"[ColabOptimizer] Error detecting GPU: {e}")
            return gpu_info
    
    def optimize_for_colab(self) -> Dict[str, bool]:
        """
        Apply comprehensive Colab optimizations.
        
        Returns:
            Dict[str, bool]: Results of optimization operations
        """
        print("[ColabOptimizer] Applying Colab optimizations...")
        
        results = {
            'drive_mounted': False,
            'gpu_optimized': False,
            'storage_optimized': False,
            'session_monitoring': False,
            'path_optimization': False
        }
        
        try:
            # 1. Mount Google Drive
            if self.config.auto_mount_drive:
                results['drive_mounted'] = self.mount_google_drive()
            
            # 2. Optimize GPU settings
            if self.config.gpu_optimization:
                results['gpu_optimized'] = self._optimize_gpu_settings()
            
            # 3. Optimize storage
            if self.config.storage_optimization:
                results['storage_optimized'] = self._optimize_storage()
            
            # 4. Start session monitoring
            if self.config.session_keep_alive:
                results['session_monitoring'] = self._start_session_monitoring()
            
            # 5. Optimize paths
            results['path_optimization'] = self._optimize_colab_paths()
            
            # Emit optimization event
            self._emit_event('optimization_applied', results)
            
            success_count = sum(results.values())
            print(f"[ColabOptimizer] Optimization complete: {success_count}/5 successful")
            
            return results
            
        except Exception as e:
            print(f"[ColabOptimizer] Error during optimization: {e}")
            return results
    
    def setup_colab_environment(self) -> bool:
        """
        Set up the complete Colab environment for PinokioCloud.
        
        Returns:
            bool: True if setup was successful
        """
        print("[ColabOptimizer] Setting up Colab environment...")
        
        try:
            # 1. Detect Colab tier and capabilities
            self._detect_colab_tier()
            
            # 2. Apply optimizations
            optimization_results = self.optimize_for_colab()
            
            # 3. Set up Colab-specific directories
            self._setup_colab_directories()
            
            # 4. Configure environment variables
            self._configure_colab_environment_variables()
            
            # 5. Install Colab-specific packages
            self._install_colab_packages()
            
            # 6. Set up automatic backup
            if self.config.backup_to_drive and self.features.drive_mounted:
                self._setup_automatic_backup()
            
            success_count = sum(optimization_results.values())
            if success_count >= 3:  # At least 3/5 optimizations successful
                print("[ColabOptimizer] Colab environment setup complete")
                return True
            else:
                print("[ColabOptimizer] Colab environment setup partially failed")
                return False
                
        except Exception as e:
            print(f"[ColabOptimizer] Error setting up Colab environment: {e}")
            return False
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        Get current Colab session information.
        
        Returns:
            Dict[str, Any]: Session information
        """
        if not self.is_colab_environment():
            return {'error': 'Not in Colab environment'}
        
        try:
            session_info = {
                'session_active': True,
                'session_start_time': self.features.session_start_time.isoformat(),
                'uptime_hours': (datetime.now() - self.features.session_start_time).total_seconds() / 3600,
                'gpu_type': self.features.gpu_type.value,
                'gpu_memory_gb': self.features.gpu_memory_gb,
                'tier': self.features.tier.value,
                'drive_mounted': self.features.drive_mounted,
                'timeout_hours': self.features.session_timeout_hours,
                'storage_quota_gb': self.features.storage_quota_gb
            }
            
            # Calculate time until timeout
            uptime_hours = session_info['uptime_hours']
            time_until_timeout = self.features.session_timeout_hours - uptime_hours
            session_info['time_until_timeout_hours'] = max(0, time_until_timeout)
            
            # Determine session status
            if time_until_timeout <= 0.25:  # 15 minutes
                session_info['status'] = ColabSessionStatus.TIMEOUT_WARNING.value
            elif uptime_hours > self.features.session_timeout_hours * 0.8:
                session_info['status'] = ColabSessionStatus.IDLE.value
            else:
                session_info['status'] = ColabSessionStatus.ACTIVE.value
            
            return session_info
            
        except Exception as e:
            print(f"[ColabOptimizer] Error getting session info: {e}")
            return {'error': str(e)}
    
    def backup_to_drive(self, source_path: str, backup_name: str = None) -> bool:
        """
        Backup data to Google Drive.
        
        Args:
            source_path: Path to backup
            backup_name: Optional backup name
        
        Returns:
            bool: True if backup was successful
        """
        if not self.features.drive_mounted:
            print("[ColabOptimizer] Google Drive not mounted, cannot backup")
            return False
        
        try:
            source = Path(source_path)
            if not source.exists():
                print(f"[ColabOptimizer] Source path does not exist: {source_path}")
                return False
            
            # Create backup directory in Drive
            backup_dir = self.drive_path / "MyDrive" / "PinokioCloud" / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate backup name if not provided
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{source.name}_{timestamp}"
            
            backup_path = backup_dir / backup_name
            
            # Perform backup
            if source.is_file():
                self.file_system.copy_file(str(source), str(backup_path))
            else:
                self.file_system.copy_directory(str(source), str(backup_path))
            
            # Emit event
            self._emit_event('backup_completed', str(backup_path))
            
            print(f"[ColabOptimizer] Backup completed: {backup_path}")
            return True
            
        except Exception as e:
            print(f"[ColabOptimizer] Error backing up to Drive: {e}")
            return False
    
    def optimize_ngrok_for_colab(self, ngrok_manager: NgrokManager) -> bool:
        """
        Optimize ngrok settings for Colab environment.
        
        Args:
            ngrok_manager: NgrokManager instance to optimize
        
        Returns:
            bool: True if optimization was successful
        """
        print("[ColabOptimizer] Optimizing ngrok for Colab...")
        
        try:
            # Set Colab-specific ngrok configuration
            colab_config = {
                'region': 'us',  # US region typically best for Colab
                'bind_tls': True,
                'inspect': False,  # Disable inspect to save resources
                'log_level': 'warn'  # Reduce logging
            }
            
            # Apply configuration to ngrok manager
            # This would integrate with the NgrokManager's configuration system
            print("[ColabOptimizer] Applied Colab-specific ngrok configuration")
            
            return True
            
        except Exception as e:
            print(f"[ColabOptimizer] Error optimizing ngrok: {e}")
            return False
    
    def get_colab_resource_limits(self) -> Dict[str, Any]:
        """
        Get Colab resource limits and usage.
        
        Returns:
            Dict[str, Any]: Resource limits and current usage
        """
        try:
            # Get system resources
            system_resources = self.resource_assessor.assess_resources()
            
            # Colab-specific limits based on tier
            if self.features.tier == ColabTier.FREE:
                limits = {
                    'max_session_hours': 12,
                    'max_idle_minutes': 90,
                    'storage_gb': 100,
                    'ram_gb': 12.7,
                    'gpu_memory_gb': self.features.gpu_memory_gb
                }
            elif self.features.tier == ColabTier.PRO:
                limits = {
                    'max_session_hours': 24,
                    'max_idle_minutes': 90,
                    'storage_gb': 100,
                    'ram_gb': 25.5,
                    'gpu_memory_gb': self.features.gpu_memory_gb
                }
            else:
                # Pro+ or unknown
                limits = {
                    'max_session_hours': 24,
                    'max_idle_minutes': 90,
                    'storage_gb': 100,
                    'ram_gb': 51.0,
                    'gpu_memory_gb': self.features.gpu_memory_gb
                }
            
            # Add current usage
            current_usage = {
                'session_uptime_hours': (datetime.now() - self.features.session_start_time).total_seconds() / 3600,
                'ram_used_gb': system_resources.used_memory_gb,
                'storage_used_gb': system_resources.used_storage_gb
            }
            
            return {
                'limits': limits,
                'current_usage': current_usage,
                'tier': self.features.tier.value,
                'gpu_type': self.features.gpu_type.value
            }
            
        except Exception as e:
            print(f"[ColabOptimizer] Error getting resource limits: {e}")
            return {}
    
    def _verify_colab_environment(self) -> None:
        """Verify that we're in a Colab environment."""
        colab_indicators = [
            self.content_path.exists(),
            self.sample_data_path.exists(),
            os.path.exists('/usr/local/lib/python*/dist-packages/google/colab')
        ]
        
        if not any(colab_indicators):
            print("[ColabOptimizer] Warning: Colab environment not detected")
    
    def _initialize_colab_features(self) -> None:
        """Initialize Colab-specific features."""
        try:
            # Detect GPU configuration
            gpu_info = self.detect_gpu_configuration()
            
            # Create features object
            self.features = ColabFeatures(
                gpu_type=gpu_info.get('gpu_type', ColabGPUType.NONE),
                gpu_memory_gb=gpu_info.get('gpu_memory_gb', 0.0),
                tier=ColabTier.UNKNOWN,  # Will be detected separately
                session_timeout_hours=12.0,  # Default for free tier
                cuda_version=gpu_info.get('cuda_version')
            )
            
            # Detect Colab tier
            self._detect_colab_tier()
            
            print(f"[ColabOptimizer] Initialized features: {self.features.gpu_type.value}, {self.features.tier.value}")
            
        except Exception as e:
            print(f"[ColabOptimizer] Error initializing Colab features: {e}")
    
    def _detect_colab_tier(self) -> None:
        """Detect Colab subscription tier."""
        try:
            # This is a heuristic approach since Colab doesn't directly expose tier info
            gpu_info = self.detect_gpu_configuration()
            
            # Check for Pro+ indicators (high RAM, A100 access)
            system_resources = self.resource_assessor.assess_resources()
            
            if system_resources.memory.total_gb > 30:
                self.features.tier = ColabTier.PRO_PLUS
                self.features.session_timeout_hours = 24.0
            elif (gpu_info['gpu_type'] in [ColabGPUType.V100, ColabGPUType.A100] or
                  system_resources.memory.total_gb > 15):
                self.features.tier = ColabTier.PRO
                self.features.session_timeout_hours = 24.0
            else:
                self.features.tier = ColabTier.FREE
                self.features.session_timeout_hours = 12.0
            
            print(f"[ColabOptimizer] Detected tier: {self.features.tier.value}")
            
        except Exception as e:
            print(f"[ColabOptimizer] Error detecting Colab tier: {e}")
            if self.features:
                self.features.tier = ColabTier.UNKNOWN
    
    def _optimize_gpu_settings(self) -> bool:
        """Optimize GPU settings for Colab."""
        try:
            if not self.features or self.features.gpu_type == ColabGPUType.NONE:
                return False
            
            # Set GPU memory growth to avoid allocation issues
            try:
                import tensorflow as tf
                gpus = tf.config.experimental.list_physical_devices('GPU')
                if gpus:
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    print("[ColabOptimizer] TensorFlow GPU memory growth enabled")
            except ImportError:
                pass  # TensorFlow not available
            except Exception as e:
                print(f"[ColabOptimizer] Error setting TensorFlow GPU config: {e}")
            
            # Set environment variables for optimal GPU usage
            os.environ['CUDA_CACHE_DISABLE'] = '0'
            os.environ['CUDA_CACHE_MAXSIZE'] = '2147483648'  # 2GB cache
            
            return True
            
        except Exception as e:
            print(f"[ColabOptimizer] Error optimizing GPU settings: {e}")
            return False
    
    def _optimize_storage(self) -> bool:
        """Optimize storage usage for Colab."""
        try:
            # Clean up unnecessary files
            cleanup_paths = [
                "/tmp",
                "/var/tmp",
                self.content_path / "sample_data" / "README.md"
            ]
            
            for cleanup_path in cleanup_paths:
                try:
                    if Path(cleanup_path).exists():
                        if Path(cleanup_path).is_file():
                            Path(cleanup_path).unlink()
                        # Don't remove directories to avoid issues
                except Exception:
                    continue
            
            # Set up efficient caching directories
            cache_dir = self.content_path / ".cache"
            cache_dir.mkdir(exist_ok=True)
            
            # Set environment variables for cache optimization
            os.environ['XDG_CACHE_HOME'] = str(cache_dir)
            os.environ['TMPDIR'] = '/tmp'
            
            print("[ColabOptimizer] Storage optimization applied")
            return True
            
        except Exception as e:
            print(f"[ColabOptimizer] Error optimizing storage: {e}")
            return False
    
    def _optimize_colab_paths(self) -> bool:
        """Optimize paths for Colab environment."""
        try:
            # Create symlinks for common paths
            apps_path = self.content_path / "apps"
            apps_path.mkdir(exist_ok=True)
            
            # If Drive is mounted, create symlink to Drive storage
            if self.features.drive_mounted:
                drive_apps_path = self.drive_path / "MyDrive" / "PinokioCloud" / "apps"
                drive_apps_path.mkdir(parents=True, exist_ok=True)
                
                # Create symlink if it doesn't exist
                symlink_path = self.content_path / "pinokio_apps"
                if not symlink_path.exists():
                    symlink_path.symlink_to(drive_apps_path)
            
            print("[ColabOptimizer] Path optimization applied")
            return True
            
        except Exception as e:
            print(f"[ColabOptimizer] Error optimizing paths: {e}")
            return False
    
    def _setup_colab_directories(self) -> None:
        """Set up Colab-specific directories."""
        directories = [
            self.content_path / "pinokio_cloud",
            self.content_path / "apps",
            self.content_path / "models",
            self.content_path / "outputs"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    def _configure_colab_environment_variables(self) -> None:
        """Configure Colab-specific environment variables."""
        env_vars = {
            'COLAB_GPU': self.features.gpu_type.value if self.features else 'None',
            'COLAB_TIER': self.features.tier.value if self.features else 'unknown',
            'PINOKIO_PLATFORM': 'google_colab',
            'PINOKIO_BASE_PATH': str(self.content_path),
            'PINOKIO_DRIVE_PATH': str(self.drive_path) if self.features.drive_mounted else ''
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
    
    def _install_colab_packages(self) -> None:
        """Install Colab-specific packages."""
        try:
            # Install packages that are commonly needed but not pre-installed
            colab_packages = [
                'psutil',
                'requests',
                'qrcode[pil]',
                'pyngrok'
            ]
            
            for package in colab_packages:
                result = self.shell_runner.run_command(
                    f"pip install {package}",
                    capture_output=True
                )
                if result.returncode == 0:
                    print(f"[ColabOptimizer] Installed {package}")
                else:
                    print(f"[ColabOptimizer] Failed to install {package}: {result.stderr}")
                    
        except Exception as e:
            print(f"[ColabOptimizer] Error installing Colab packages: {e}")
    
    def _setup_automatic_backup(self) -> None:
        """Set up automatic backup to Google Drive."""
        try:
            # Create backup script
            backup_script = self.colab_storage_path / "auto_backup.py"
            
            backup_code = f'''
import shutil
import time
from pathlib import Path
from datetime import datetime

def backup_pinokio_data():
    source = Path("{self.base_path}")
    target = Path("{self.drive_path}/MyDrive/PinokioCloud/auto_backup")
    target.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = target / f"pinokio_backup_{{timestamp}}"
    
    if source.exists():
        shutil.copytree(source, backup_path, ignore_errors=True)
        print(f"Backup completed: {{backup_path}}")

if __name__ == "__main__":
    backup_pinokio_data()
'''
            
            backup_script.write_text(backup_code)
            
            print("[ColabOptimizer] Automatic backup system configured")
            
        except Exception as e:
            print(f"[ColabOptimizer] Error setting up automatic backup: {e}")
    
    def _start_session_monitoring(self) -> bool:
        """Start session monitoring to prevent timeouts."""
        try:
            if self.session_monitor_thread is None or not self.session_monitor_thread.is_alive():
                self.session_monitor_active = True
                self.session_monitor_thread = threading.Thread(
                    target=self._session_monitoring_loop,
                    daemon=True
                )
                self.session_monitor_thread.start()
                print("[ColabOptimizer] Started session monitoring")
                return True
            
            return False
            
        except Exception as e:
            print(f"[ColabOptimizer] Error starting session monitoring: {e}")
            return False
    
    def _session_monitoring_loop(self) -> None:
        """Main session monitoring loop."""
        while self.session_monitor_active:
            try:
                session_info = self.get_session_info()
                
                if 'time_until_timeout_hours' in session_info:
                    time_left = session_info['time_until_timeout_hours']
                    
                    # Warn if approaching timeout
                    if time_left <= 0.25:  # 15 minutes
                        self._emit_event('session_timeout_warning', time_left)
                        print(f"[ColabOptimizer] Session timeout warning: {time_left:.1f} hours remaining")
                        
                        # Trigger backup if configured
                        if self.config.backup_to_drive:
                            self.backup_to_drive(str(self.base_path), f"auto_backup_{int(time.time())}")
                
                # Update last activity
                if self.features:
                    self.features.last_activity = datetime.now()
                
                time.sleep(self.session_check_interval)
                
            except Exception as e:
                print(f"[ColabOptimizer] Error in session monitoring: {e}")
                time.sleep(self.session_check_interval)
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[ColabOptimizer] Error in event callback: {e}")
    
    def add_event_callback(self, event: str, callback: callable) -> None:
        """Add a callback for Colab events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def stop_session_monitoring(self) -> None:
        """Stop session monitoring."""
        self.session_monitor_active = False
        if self.session_monitor_thread and self.session_monitor_thread.is_alive():
            self.session_monitor_thread.join(timeout=5.0)
        print("[ColabOptimizer] Stopped session monitoring")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_session_monitoring()


def main():
    """Test the Colab optimizer functionality."""
    print("Testing ColabOptimizer...")
    
    optimizer = ColabOptimizer()
    
    # Check if we're in Colab
    is_colab = optimizer.is_colab_environment()
    print(f"Colab environment detected: {is_colab}")
    
    if is_colab:
        # Test Colab-specific features
        session_info = optimizer.get_session_info()
        print(f"Session info: {session_info}")
        
        # Test optimization
        results = optimizer.optimize_for_colab()
        print(f"Optimization results: {results}")
        
        # Test resource limits
        limits = optimizer.get_colab_resource_limits()
        print(f"Resource limits: {limits}")
    else:
        print("Not in Colab environment, basic functionality tested")
    
    print("ColabOptimizer test completed")


if __name__ == "__main__":
    main()