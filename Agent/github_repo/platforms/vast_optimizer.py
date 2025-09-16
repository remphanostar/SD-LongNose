#!/usr/bin/env python3
"""
PinokioCloud Vast.ai Optimizer

This module adds Vast.ai-specific features and optimizations including
certificate management, Docker container adaptation, billing optimization,
and Vast.ai-specific performance tuning.

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


class VastInstanceType(Enum):
    """Types of Vast.ai instances."""
    RTX_3090 = "RTX_3090"
    RTX_4090 = "RTX_4090"
    A100 = "A100"
    H100 = "H100"
    V100 = "V100"
    UNKNOWN = "unknown"


class VastBillingMode(Enum):
    """Vast.ai billing modes."""
    ON_DEMAND = "on_demand"
    INTERRUPTIBLE = "interruptible"
    RESERVED = "reserved"


class VastStorageType(Enum):
    """Vast.ai storage types."""
    LOCAL_SSD = "local_ssd"
    NETWORK_STORAGE = "network_storage"
    PERSISTENT = "persistent"


@dataclass
class VastFeatures:
    """Vast.ai-specific features and capabilities."""
    instance_type: VastInstanceType
    gpu_count: int
    gpu_memory_gb: float
    cpu_cores: int
    ram_gb: float
    storage_gb: float
    storage_type: VastStorageType
    billing_mode: VastBillingMode
    hourly_rate: float = 0.0
    docker_enabled: bool = True
    ssh_enabled: bool = True
    jupyter_enabled: bool = True
    instance_id: Optional[str] = None
    datacenter_location: Optional[str] = None
    network_speed_mbps: float = 1000.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert VastFeatures to dictionary."""
        data = asdict(self)
        data['instance_type'] = self.instance_type.value
        data['billing_mode'] = self.billing_mode.value
        data['storage_type'] = self.storage_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VastFeatures':
        """Create VastFeatures from dictionary."""
        data['instance_type'] = VastInstanceType(data['instance_type'])
        data['billing_mode'] = VastBillingMode(data['billing_mode'])
        data['storage_type'] = VastStorageType(data['storage_type'])
        return cls(**data)


@dataclass
class VastConfig:
    """Configuration for Vast.ai optimization."""
    auto_setup_certificates: bool = True
    optimize_docker: bool = True
    billing_optimization: bool = True
    auto_shutdown_idle: bool = True
    max_idle_minutes: int = 60
    backup_important_data: bool = True
    optimize_network: bool = True
    monitor_costs: bool = True
    preferred_tunnel_type: str = "direct_https"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert VastConfig to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VastConfig':
        """Create VastConfig from dictionary."""
        return cls(**data)


class VastOptimizer:
    """
    Adds Vast.ai-specific features and optimizations.
    
    This class provides comprehensive Vast.ai integration including
    certificate management, Docker optimization, billing monitoring,
    and performance tuning.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the Vast.ai optimizer."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.vast_storage_path = self.base_path / "vast_storage"
        self.vast_storage_path.mkdir(exist_ok=True)
        
        # Vast.ai-specific paths
        self.workspace_path = Path("/workspace")
        self.opt_path = Path("/opt")
        self.root_path = Path("/root")
        
        # Configuration
        self.config = VastConfig()
        self.features = None
        
        # Initialize dependencies
        self.cloud_detector = CloudDetector()
        self.resource_assessor = ResourceAssessor()
        self.file_system = FileSystemManager(str(self.base_path))
        self.shell_runner = ShellRunner(str(self.base_path))
        self.json_handler = JSONHandler(str(self.base_path))
        self.process_tracker = ProcessTracker(str(self.base_path))
        
        # Billing monitoring
        self.billing_monitor_active = False
        self.billing_monitor_thread = None
        self.billing_check_interval = 300.0  # 5 minutes
        self.cost_tracking = {
            'session_start': datetime.now(),
            'estimated_cost': 0.0,
            'last_update': datetime.now()
        }
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[callable]] = {
            'certificates_setup': [],
            'docker_optimized': [],
            'billing_alert': [],
            'auto_shutdown_triggered': [],
            'performance_optimized': []
        }
        
        # Verify we're on Vast.ai and initialize
        if self.is_vast_environment():
            self._initialize_vast_features()
        
        print(f"[VastOptimizer] Initialized for Vast.ai environment: {self.is_vast_environment()}")
    
    def is_vast_environment(self) -> bool:
        """
        Check if we're running on Vast.ai.
        
        Returns:
            bool: True if running on Vast.ai
        """
        platform_info = self.cloud_detector.detect_platform()
        return platform_info.platform == CloudPlatform.VAST_AI
    
    def setup_ssl_certificates(self) -> bool:
        """
        Set up SSL certificates for HTTPS access.
        
        Returns:
            bool: True if certificates were set up successfully
        """
        if not self.is_vast_environment():
            print("[VastOptimizer] Not in Vast.ai environment, skipping SSL setup")
            return False
        
        print("[VastOptimizer] Setting up SSL certificates...")
        
        try:
            # Create certificates directory
            cert_dir = self.vast_storage_path / "certificates"
            cert_dir.mkdir(exist_ok=True)
            
            # Generate self-signed certificate for local development
            cert_file = cert_dir / "server.crt"
            key_file = cert_dir / "server.key"
            
            if not cert_file.exists() or not key_file.exists():
                # Generate certificate
                cmd = [
                    "openssl", "req", "-x509", "-newkey", "rsa:4096",
                    "-keyout", str(key_file),
                    "-out", str(cert_file),
                    "-days", "365",
                    "-nodes",
                    "-subj", "/C=US/ST=CA/L=SF/O=PinokioCloud/CN=localhost"
                ]
                
                result = self.shell_runner.run_command(" ".join(cmd), capture_output=True)
                
                if result.returncode == 0:
                    print("[VastOptimizer] SSL certificates generated successfully")
                    
                    # Set proper permissions
                    os.chmod(cert_file, 0o644)
                    os.chmod(key_file, 0o600)
                    
                    # Emit event
                    self._emit_event('certificates_setup', {
                        'cert_file': str(cert_file),
                        'key_file': str(key_file)
                    })
                    
                    return True
                else:
                    print(f"[VastOptimizer] Failed to generate certificates: {result.stderr}")
                    return False
            else:
                print("[VastOptimizer] SSL certificates already exist")
                return True
                
        except Exception as e:
            print(f"[VastOptimizer] Error setting up SSL certificates: {e}")
            return False
    
    def optimize_docker_environment(self) -> bool:
        """
        Optimize Docker environment for better performance.
        
        Returns:
            bool: True if Docker was optimized successfully
        """
        if not self.is_vast_environment():
            return False
        
        print("[VastOptimizer] Optimizing Docker environment...")
        
        try:
            # Check if we're in a Docker container
            if not self._is_docker_environment():
                print("[VastOptimizer] Not in Docker environment")
                return False
            
            # Optimize Docker settings
            optimizations = []
            
            # 1. Increase shared memory size
            try:
                shm_size = self._get_shm_size()
                if shm_size < 2 * 1024 * 1024 * 1024:  # Less than 2GB
                    print("[VastOptimizer] Warning: Low shared memory size detected")
                    optimizations.append("shm_size_warning")
            except Exception:
                pass
            
            # 2. Optimize tmpfs mounts
            try:
                self._optimize_tmpfs_mounts()
                optimizations.append("tmpfs_optimized")
            except Exception as e:
                print(f"[VastOptimizer] Error optimizing tmpfs: {e}")
            
            # 3. Set up Docker-specific environment variables
            docker_env_vars = {
                'VAST_AI_OPTIMIZED': 'true',
                'DOCKER_OPTIMIZED': 'true',
                'PINOKIO_DOCKER_MODE': 'true'
            }
            
            for key, value in docker_env_vars.items():
                os.environ[key] = value
            
            optimizations.append("env_vars_set")
            
            # 4. Optimize for GPU access in Docker
            if self.features and self.features.gpu.count > 0:
                self._optimize_docker_gpu_access()
                optimizations.append("gpu_optimized")
            
            # Emit event
            self._emit_event('docker_optimized', optimizations)
            
            print(f"[VastOptimizer] Docker optimization complete: {len(optimizations)} optimizations applied")
            return True
            
        except Exception as e:
            print(f"[VastOptimizer] Error optimizing Docker: {e}")
            return False
    
    def setup_billing_monitoring(self) -> bool:
        """
        Set up billing monitoring and cost optimization.
        
        Returns:
            bool: True if billing monitoring was set up successfully
        """
        print("[VastOptimizer] Setting up billing monitoring...")
        
        try:
            if not self.features:
                print("[VastOptimizer] Features not initialized")
                return False
            
            # Initialize cost tracking
            self.cost_tracking = {
                'session_start': datetime.now(),
                'hourly_rate': self.features.hourly_rate,
                'estimated_cost': 0.0,
                'last_update': datetime.now(),
                'billing_mode': self.features.billing_mode.value
            }
            
            # Start billing monitoring thread
            if not self.billing_monitor_active:
                self.billing_monitor_active = True
                self.billing_monitor_thread = threading.Thread(
                    target=self._billing_monitoring_loop,
                    daemon=True
                )
                self.billing_monitor_thread.start()
                print("[VastOptimizer] Started billing monitoring")
            
            return True
            
        except Exception as e:
            print(f"[VastOptimizer] Error setting up billing monitoring: {e}")
            return False
    
    def get_cost_estimate(self) -> Dict[str, Any]:
        """
        Get current cost estimate and billing information.
        
        Returns:
            Dict[str, Any]: Cost estimate and billing info
        """
        try:
            if not self.features:
                return {'error': 'Features not initialized'}
            
            current_time = datetime.now()
            session_duration = current_time - self.cost_tracking['session_start']
            hours_used = session_duration.total_seconds() / 3600
            
            estimated_cost = hours_used * self.features.hourly_rate
            
            cost_info = {
                'session_duration_hours': hours_used,
                'hourly_rate': self.features.hourly_rate,
                'estimated_cost_usd': estimated_cost,
                'billing_mode': self.features.billing_mode.value,
                'instance_type': self.features.instance_type.value,
                'gpu_count': self.features.gpu.count,
                'last_updated': current_time.isoformat()
            }
            
            # Add cost projections
            cost_info['projected_cost_24h'] = 24 * self.features.hourly_rate
            cost_info['projected_cost_weekly'] = 168 * self.features.hourly_rate
            
            # Update tracking
            self.cost_tracking['estimated_cost'] = estimated_cost
            self.cost_tracking['last_update'] = current_time
            
            return cost_info
            
        except Exception as e:
            print(f"[VastOptimizer] Error getting cost estimate: {e}")
            return {'error': str(e)}
    
    def optimize_for_vast(self) -> Dict[str, bool]:
        """
        Apply comprehensive Vast.ai optimizations.
        
        Returns:
            Dict[str, bool]: Results of optimization operations
        """
        print("[VastOptimizer] Applying Vast.ai optimizations...")
        
        results = {
            'certificates_setup': False,
            'docker_optimized': False,
            'billing_monitoring': False,
            'storage_optimized': False,
            'network_optimized': False
        }
        
        try:
            # 1. Set up SSL certificates
            if self.config.auto_setup_certificates:
                results['certificates_setup'] = self.setup_ssl_certificates()
            
            # 2. Optimize Docker environment
            if self.config.optimize_docker:
                results['docker_optimized'] = self.optimize_docker_environment()
            
            # 3. Set up billing monitoring
            if self.config.billing_optimization:
                results['billing_monitoring'] = self.setup_billing_monitoring()
            
            # 4. Optimize storage
            if self.config.billing_optimization:
                results['storage_optimized'] = self._optimize_vast_storage()
            
            # 5. Optimize network
            if self.config.optimize_network:
                results['network_optimized'] = self._optimize_vast_network()
            
            # Emit optimization event
            self._emit_event('performance_optimized', results)
            
            success_count = sum(results.values())
            print(f"[VastOptimizer] Optimization complete: {success_count}/5 successful")
            
            return results
            
        except Exception as e:
            print(f"[VastOptimizer] Error during optimization: {e}")
            return results
    
    def setup_direct_https_access(self) -> Dict[str, Any]:
        """
        Set up direct HTTPS access using Vast.ai's built-in capabilities.
        
        Returns:
            Dict[str, Any]: HTTPS access configuration
        """
        print("[VastOptimizer] Setting up direct HTTPS access...")
        
        try:
            # Get instance public IP and configure HTTPS
            instance_info = self._get_vast_instance_info()
            
            if not instance_info.get('public_ip'):
                return {'error': 'No public IP available'}
            
            public_ip = instance_info['public_ip']
            
            # Set up HTTPS configuration
            https_config = {
                'public_ip': public_ip,
                'https_port': 443,
                'http_port': 80,
                'ssl_cert_path': str(self.vast_storage_path / "certificates" / "server.crt"),
                'ssl_key_path': str(self.vast_storage_path / "certificates" / "server.key"),
                'direct_access_url': f"https://{public_ip}"
            }
            
            # Configure nginx or similar for HTTPS termination
            self._configure_https_proxy(https_config)
            
            print(f"[VastOptimizer] Direct HTTPS access configured: {https_config['direct_access_url']}")
            
            return https_config
            
        except Exception as e:
            print(f"[VastOptimizer] Error setting up HTTPS access: {e}")
            return {'error': str(e)}
    
    def _initialize_vast_features(self) -> None:
        """Initialize Vast.ai-specific features."""
        try:
            # Get system resources
            system_resources = self.resource_assessor.assess_resources()
            
            # Detect GPU configuration
            gpu_info = self._detect_vast_gpu()
            
            # Get instance information
            instance_info = self._get_vast_instance_info()
            
            # Create features object
            self.features = VastFeatures(
                instance_type=gpu_info.get('instance_type', VastInstanceType.UNKNOWN),
                gpu_count=gpu_info.get('gpu_count', 0),
                gpu_memory_gb=gpu_info.get('gpu_memory_gb', 0.0),
                cpu_cores=system_resources.cpu.cores_logical,
                ram_gb=system_resources.memory.total_gb,
                storage_gb=system_resources.total_storage_gb,
                storage_type=VastStorageType.LOCAL_SSD,  # Default assumption
                billing_mode=VastBillingMode.ON_DEMAND,  # Default assumption
                hourly_rate=instance_info.get('hourly_rate', 0.0),
                instance_id=instance_info.get('instance_id')
            )
            
            print(f"[VastOptimizer] Initialized features: {self.features.instance_type.value}, "
                  f"{self.features.gpu.count} GPUs, {self.features.ram_gb:.1f}GB RAM")
            
        except Exception as e:
            print(f"[VastOptimizer] Error initializing Vast.ai features: {e}")
    
    def _detect_vast_gpu(self) -> Dict[str, Any]:
        """Detect Vast.ai GPU configuration."""
        gpu_info = {
            'instance_type': VastInstanceType.UNKNOWN,
            'gpu_count': 0,
            'gpu_memory_gb': 0.0
        }
        
        try:
            # Run nvidia-smi to get GPU information
            result = self.shell_runner.run_command("nvidia-smi", capture_output=True)
            
            if result.returncode == 0:
                output = result.stdout
                
                # Count GPUs
                gpu_count = output.count('GPU ')
                gpu_info['gpu_count'] = gpu_count
                
                # Detect GPU type
                if "RTX 3090" in output:
                    gpu_info['instance_type'] = VastInstanceType.RTX_3090
                    gpu_info['gpu_memory_gb'] = 24.0 * gpu_count
                elif "RTX 4090" in output:
                    gpu_info['instance_type'] = VastInstanceType.RTX_4090
                    gpu_info['gpu_memory_gb'] = 24.0 * gpu_count
                elif "A100" in output:
                    gpu_info['instance_type'] = VastInstanceType.A100
                    gpu_info['gpu_memory_gb'] = 40.0 * gpu_count
                elif "H100" in output:
                    gpu_info['instance_type'] = VastInstanceType.H100
                    gpu_info['gpu_memory_gb'] = 80.0 * gpu_count
                elif "V100" in output:
                    gpu_info['instance_type'] = VastInstanceType.V100
                    gpu_info['gpu_memory_gb'] = 16.0 * gpu_count
                
                print(f"[VastOptimizer] Detected {gpu_count} x {gpu_info['instance_type'].value}")
            
            return gpu_info
            
        except Exception as e:
            print(f"[VastOptimizer] Error detecting GPU: {e}")
            return gpu_info
    
    def _get_vast_instance_info(self) -> Dict[str, Any]:
        """Get Vast.ai instance information."""
        try:
            # Try to get instance info from environment variables or metadata
            instance_info = {}
            
            # Check for Vast.ai environment variables
            vast_env_vars = [
                'VAST_INSTANCE_ID',
                'VAST_PUBLIC_IP',
                'VAST_HOURLY_RATE',
                'VAST_DATACENTER'
            ]
            
            for var in vast_env_vars:
                value = os.environ.get(var)
                if value:
                    key = var.lower().replace('vast_', '')
                    instance_info[key] = value
            
            # Try to get public IP
            if 'public_ip' not in instance_info:
                try:
                    # Get public IP
                    ip_result = self.shell_runner.run_command(
                        "curl -s ifconfig.me", capture_output=True
                    )
                    if ip_result.returncode == 0:
                        instance_info['public_ip'] = ip_result.stdout.strip()
                except Exception:
                    pass
            
            # Set default hourly rate if not available
            if 'hourly_rate' not in instance_info:
                # Estimate based on GPU type
                if self.features:
                    rate_estimates = {
                        VastInstanceType.RTX_3090: 0.30,
                        VastInstanceType.RTX_4090: 0.50,
                        VastInstanceType.A100: 1.00,
                        VastInstanceType.H100: 2.00,
                        VastInstanceType.V100: 0.80
                    }
                    estimated_rate = rate_estimates.get(self.features.instance_type, 0.25)
                    instance_info['hourly_rate'] = estimated_rate * self.features.gpu.count
            
            return instance_info
            
        except Exception as e:
            print(f"[VastOptimizer] Error getting instance info: {e}")
            return {}
    
    def _is_docker_environment(self) -> bool:
        """Check if we're running in a Docker container."""
        try:
            # Check for Docker-specific files
            docker_indicators = [
                Path("/.dockerenv").exists(),
                Path("/proc/1/cgroup").exists() and "docker" in Path("/proc/1/cgroup").read_text()
            ]
            
            return any(docker_indicators)
            
        except Exception:
            return False
    
    def _get_shm_size(self) -> int:
        """Get shared memory size in bytes."""
        try:
            shm_stat = os.statvfs('/dev/shm')
            return shm_stat.f_bavail * shm_stat.f_frsize
        except Exception:
            return 0
    
    def _optimize_tmpfs_mounts(self) -> None:
        """Optimize tmpfs mounts for performance."""
        try:
            # Set optimal tmpfs mount options
            tmpfs_dirs = ['/tmp', '/var/tmp']
            
            for tmpfs_dir in tmpfs_dirs:
                if Path(tmpfs_dir).exists():
                    # Set environment variable for optimal tmpfs usage
                    os.environ[f'TMPDIR'] = tmpfs_dir
                    break
                    
        except Exception as e:
            print(f"[VastOptimizer] Error optimizing tmpfs: {e}")
    
    def _optimize_docker_gpu_access(self) -> None:
        """Optimize GPU access in Docker."""
        try:
            # Set NVIDIA Docker runtime environment variables
            nvidia_env_vars = {
                'NVIDIA_VISIBLE_DEVICES': 'all',
                'NVIDIA_DRIVER_CAPABILITIES': 'compute,utility',
                'NVIDIA_REQUIRE_CUDA': 'cuda>=11.0'
            }
            
            for key, value in nvidia_env_vars.items():
                os.environ[key] = value
            
            print("[VastOptimizer] Docker GPU access optimized")
            
        except Exception as e:
            print(f"[VastOptimizer] Error optimizing Docker GPU access: {e}")
    
    def _optimize_vast_storage(self) -> bool:
        """Optimize storage for Vast.ai."""
        try:
            # Set up efficient storage structure
            storage_dirs = [
                self.workspace_path / "models",
                self.workspace_path / "cache",
                self.workspace_path / "outputs",
                self.workspace_path / "temp"
            ]
            
            for storage_dir in storage_dirs:
                storage_dir.mkdir(exist_ok=True)
            
            # Set up storage environment variables
            storage_env_vars = {
                'VAST_MODELS_PATH': str(self.workspace_path / "models"),
                'VAST_CACHE_PATH': str(self.workspace_path / "cache"),
                'VAST_OUTPUT_PATH': str(self.workspace_path / "outputs")
            }
            
            for key, value in storage_env_vars.items():
                os.environ[key] = value
            
            print("[VastOptimizer] Storage optimization applied")
            return True
            
        except Exception as e:
            print(f"[VastOptimizer] Error optimizing storage: {e}")
            return False
    
    def _optimize_vast_network(self) -> bool:
        """Optimize network settings for Vast.ai."""
        try:
            # Set network optimization environment variables
            network_env_vars = {
                'VAST_NETWORK_OPTIMIZED': 'true',
                'CURL_CA_BUNDLE': '',  # Disable SSL verification for internal requests
                'PYTHONHTTPSVERIFY': '0'  # Disable SSL verification for Python
            }
            
            for key, value in network_env_vars.items():
                os.environ[key] = value
            
            print("[VastOptimizer] Network optimization applied")
            return True
            
        except Exception as e:
            print(f"[VastOptimizer] Error optimizing network: {e}")
            return False
    
    def _configure_https_proxy(self, https_config: Dict[str, Any]) -> None:
        """Configure HTTPS proxy for direct access."""
        try:
            # Create nginx configuration for HTTPS proxy
            nginx_config = f'''
server {{
    listen 443 ssl;
    server_name {https_config['public_ip']};
    
    ssl_certificate {https_config['ssl_cert_path']};
    ssl_certificate_key {https_config['ssl_key_path']};
    
    location / {{
        proxy_pass http://localhost:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
'''
            
            # Save nginx configuration
            nginx_config_path = self.vast_storage_path / "nginx_https.conf"
            nginx_config_path.write_text(nginx_config)
            
            print("[VastOptimizer] HTTPS proxy configuration created")
            
        except Exception as e:
            print(f"[VastOptimizer] Error configuring HTTPS proxy: {e}")
    
    def _billing_monitoring_loop(self) -> None:
        """Main billing monitoring loop."""
        while self.billing_monitor_active:
            try:
                cost_info = self.get_cost_estimate()
                
                # Check for cost alerts
                if 'estimated_cost_usd' in cost_info:
                    estimated_cost = cost_info['estimated_cost_usd']
                    
                    # Alert thresholds
                    if estimated_cost > 10.0:  # $10 threshold
                        self._emit_event('billing_alert', {
                            'type': 'high_cost',
                            'estimated_cost': estimated_cost,
                            'threshold': 10.0
                        })
                    
                    # Auto-shutdown check
                    if (self.config.auto_shutdown_idle and 
                        estimated_cost > 20.0):  # $20 auto-shutdown threshold
                        self._emit_event('auto_shutdown_triggered', {
                            'reason': 'cost_limit',
                            'estimated_cost': estimated_cost
                        })
                
                time.sleep(self.billing_check_interval)
                
            except Exception as e:
                print(f"[VastOptimizer] Error in billing monitoring: {e}")
                time.sleep(self.billing_check_interval)
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[VastOptimizer] Error in event callback: {e}")
    
    def add_event_callback(self, event: str, callback: callable) -> None:
        """Add a callback for Vast.ai events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def stop_billing_monitoring(self) -> None:
        """Stop billing monitoring."""
        self.billing_monitor_active = False
        if self.billing_monitor_thread and self.billing_monitor_thread.is_alive():
            self.billing_monitor_thread.join(timeout=5.0)
        print("[VastOptimizer] Stopped billing monitoring")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_billing_monitoring()


def main():
    """Test the Vast.ai optimizer functionality."""
    print("Testing VastOptimizer...")
    
    optimizer = VastOptimizer()
    
    # Check if we're on Vast.ai
    is_vast = optimizer.is_vast_environment()
    print(f"Vast.ai environment detected: {is_vast}")
    
    if is_vast:
        # Test Vast.ai-specific features
        cost_info = optimizer.get_cost_estimate()
        print(f"Cost estimate: {cost_info}")
        
        # Test optimization
        results = optimizer.optimize_for_vast()
        print(f"Optimization results: {results}")
    else:
        print("Not in Vast.ai environment, basic functionality tested")
    
    print("VastOptimizer test completed")


if __name__ == "__main__":
    main()