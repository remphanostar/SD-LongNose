#!/usr/bin/env python3
"""
PinokioCloud Platform Configuration System

This module provides platform-specific configurations for all supported cloud platforms.
Each platform has specific paths, limitations, features, and optimizations.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class CloudPlatform(Enum):
    """Enumeration of supported cloud platforms."""
    GOOGLE_COLAB = "google-colab"
    VAST_AI = "vast-ai"
    LIGHTNING_AI = "lightning-ai"
    PAPERSPACE = "paperspace"
    RUNPOD = "runpod"
    UNKNOWN = "unknown"


@dataclass
class PathConfiguration:
    """Path configuration for a cloud platform."""
    base_path: str
    apps_path: str
    data_path: str
    temp_path: str
    logs_path: str
    cache_path: str
    models_path: str
    config_path: str
    workspace_path: str
    drive_mount_path: Optional[str] = None
    shared_storage_path: Optional[str] = None


@dataclass
class ResourceLimits:
    """Resource limits for a cloud platform."""
    max_memory_gb: float
    max_disk_gb: float
    max_cpu_cores: int
    max_gpu_count: int
    session_timeout_hours: float
    idle_timeout_minutes: float
    max_concurrent_processes: int
    max_file_size_mb: float


@dataclass
class PlatformFeatures:
    """Available features for a cloud platform."""
    supports_gpu: bool
    supports_tpu: bool
    supports_drive_mounting: bool
    supports_ssh: bool
    supports_docker: bool
    supports_conda: bool
    supports_pip: bool
    supports_npm: bool
    supports_git: bool
    supports_ngrok: bool
    supports_cloudflare_tunnel: bool
    supports_gradio_share: bool
    supports_streamlit: bool
    supports_jupyter: bool
    supports_terminal: bool
    supports_file_upload: bool
    supports_file_download: bool
    supports_network_access: bool
    supports_persistent_storage: bool
    supports_environment_variables: bool


@dataclass
class PlatformOptimizations:
    """Platform-specific optimizations."""
    enable_memory_optimization: bool
    enable_disk_optimization: bool
    enable_network_optimization: bool
    enable_gpu_optimization: bool
    enable_caching: bool
    enable_compression: bool
    enable_deduplication: bool
    enable_cleanup: bool
    cleanup_interval_minutes: int
    cache_size_mb: int
    compression_level: int


@dataclass
class PlatformConfigurationuration:
    """Complete platform configuration."""
    platform: CloudPlatform
    display_name: str
    description: str
    paths: PathConfiguration
    limits: ResourceLimits
    features: PlatformFeatures
    optimizations: PlatformOptimizations
    environment_variables: Dict[str, str] = field(default_factory=dict)
    system_requirements: List[str] = field(default_factory=list)
    installation_commands: List[str] = field(default_factory=list)
    troubleshooting_tips: List[str] = field(default_factory=list)


class PlatformConfigurationManager:
    """
    Manager for platform-specific configurations.
    
    Provides access to platform configurations and handles platform-specific
    optimizations and limitations.
    """
    
    def __init__(self):
        """Initialize the platform configuration manager."""
        self._configs = self._initialize_configurations()
    
    def _initialize_configurations(self) -> Dict[CloudPlatform, PlatformConfigurationuration]:
        """Initialize all platform configurations."""
        configs = {}
        
        # Google Colab Configuration
        configs[CloudPlatform.GOOGLE_COLAB] = PlatformConfigurationuration(
            platform=CloudPlatform.GOOGLE_COLAB,
            display_name="Google Colab",
            description="Google's cloud-based Jupyter notebook environment with GPU support",
            paths=PathConfiguration(
                base_path="/content",
                apps_path="/content/apps",
                data_path="/content/data",
                temp_path="/tmp",
                logs_path="/content/logs",
                cache_path="/content/cache",
                models_path="/content/models",
                config_path="/content/config",
                workspace_path="/content/workspace",
                drive_mount_path="/mnt/MyDrive",
                shared_storage_path="/content/shared"
            ),
            limits=ResourceLimits(
                max_memory_gb=12.0,
                max_disk_gb=100.0,
                max_cpu_cores=2,
                max_gpu_count=1,
                session_timeout_hours=12.0,
                idle_timeout_minutes=90.0,
                max_concurrent_processes=10,
                max_file_size_mb=100.0
            ),
            features=PlatformFeatures(
                supports_gpu=True,
                supports_tpu=True,
                supports_drive_mounting=True,
                supports_ssh=False,
                supports_docker=False,
                supports_conda=True,
                supports_pip=True,
                supports_npm=True,
                supports_git=True,
                supports_ngrok=True,
                supports_cloudflare_tunnel=True,
                supports_gradio_share=True,
                supports_streamlit=True,
                supports_jupyter=True,
                supports_terminal=True,
                supports_file_upload=True,
                supports_file_download=True,
                supports_network_access=True,
                supports_persistent_storage=False,
                supports_environment_variables=True
            ),
            optimizations=PlatformOptimizations(
                enable_memory_optimization=True,
                enable_disk_optimization=True,
                enable_network_optimization=True,
                enable_gpu_optimization=True,
                enable_caching=True,
                enable_compression=True,
                enable_deduplication=True,
                enable_cleanup=True,
                cleanup_interval_minutes=30,
                cache_size_mb=1000,
                compression_level=6
            ),
            environment_variables={
                'COLAB_GPU': '1',
                'COLAB_TPU': '0',
                'COLAB_CPU': '2',
                'COLAB_RUNTIME_VERSION': '3.0'
            },
            system_requirements=[
                'Python 3.8+',
                'CUDA 11.0+',
                'cuDNN 8.0+',
                'TensorFlow 2.0+',
                'PyTorch 1.0+'
            ],
            installation_commands=[
                'pip install --upgrade pip',
                'pip install torch torchvision torchaudio',
                'pip install tensorflow',
                'pip install jupyter',
                'pip install streamlit',
                'pip install gradio'
            ],
            troubleshooting_tips=[
                'Restart runtime if GPU is not detected',
                'Check GPU availability with nvidia-smi',
                'Clear cache if running out of memory',
                'Use drive mounting for persistent storage'
            ]
        )
        
        # Vast.ai Configuration
        configs[CloudPlatform.VAST_AI] = PlatformConfigurationuration(
            platform=CloudPlatform.VAST_AI,
            display_name="Vast.ai",
            description="Distributed GPU cloud computing platform with Docker support",
            paths=PathConfiguration(
                base_path="/workspace",
                apps_path="/workspace/apps",
                data_path="/workspace/data",
                temp_path="/tmp",
                logs_path="/workspace/logs",
                cache_path="/workspace/cache",
                models_path="/workspace/models",
                config_path="/workspace/config",
                workspace_path="/workspace",
                drive_mount_path=None,
                shared_storage_path="/workspace/shared"
            ),
            limits=ResourceLimits(
                max_memory_gb=32.0,
                max_disk_gb=500.0,
                max_cpu_cores=8,
                max_gpu_count=4,
                session_timeout_hours=24.0,
                idle_timeout_minutes=60.0,
                max_concurrent_processes=20,
                max_file_size_mb=1000.0
            ),
            features=PlatformFeatures(
                supports_gpu=True,
                supports_tpu=False,
                supports_drive_mounting=False,
                supports_ssh=True,
                supports_docker=True,
                supports_conda=True,
                supports_pip=True,
                supports_npm=True,
                supports_git=True,
                supports_ngrok=True,
                supports_cloudflare_tunnel=True,
                supports_gradio_share=True,
                supports_streamlit=True,
                supports_jupyter=True,
                supports_terminal=True,
                supports_file_upload=True,
                supports_file_download=True,
                supports_network_access=True,
                supports_persistent_storage=True,
                supports_environment_variables=True
            ),
            optimizations=PlatformOptimizations(
                enable_memory_optimization=True,
                enable_disk_optimization=True,
                enable_network_optimization=True,
                enable_gpu_optimization=True,
                enable_caching=True,
                enable_compression=True,
                enable_deduplication=True,
                enable_cleanup=True,
                cleanup_interval_minutes=60,
                cache_size_mb=2000,
                compression_level=9
            ),
            environment_variables={
                'VAST_CONTAINERLABEL': 'vast-ai',
                'VAST_CONTAINERNAME': 'vast-container',
                'VAST_SSH_PORT': '22'
            },
            system_requirements=[
                'Python 3.8+',
                'CUDA 11.0+',
                'cuDNN 8.0+',
                'Docker 20.0+',
                'NVIDIA Container Toolkit'
            ],
            installation_commands=[
                'apt update && apt install -y python3-pip',
                'pip install --upgrade pip',
                'pip install torch torchvision torchaudio',
                'pip install tensorflow',
                'pip install jupyter',
                'pip install streamlit',
                'pip install gradio'
            ],
            troubleshooting_tips=[
                'Check Docker container status',
                'Verify GPU availability with nvidia-smi',
                'Check SSH connectivity',
                'Monitor resource usage'
            ]
        )
        
        # Lightning.ai Configuration
        configs[CloudPlatform.LIGHTNING_AI] = PlatformConfigurationuration(
            platform=CloudPlatform.LIGHTNING_AI,
            display_name="Lightning.ai",
            description="Cloud platform for AI/ML development with team collaboration features",
            paths=PathConfiguration(
                base_path="/teamspace",
                apps_path="/teamspace/apps",
                data_path="/teamspace/data",
                temp_path="/tmp",
                logs_path="/teamspace/logs",
                cache_path="/teamspace/cache",
                models_path="/teamspace/models",
                config_path="/teamspace/config",
                workspace_path="/teamspace/workspace",
                drive_mount_path=None,
                shared_storage_path="/teamspace/shared"
            ),
            limits=ResourceLimits(
                max_memory_gb=64.0,
                max_disk_gb=1000.0,
                max_cpu_cores=16,
                max_gpu_count=8,
                session_timeout_hours=48.0,
                idle_timeout_minutes=120.0,
                max_concurrent_processes=50,
                max_file_size_mb=5000.0
            ),
            features=PlatformFeatures(
                supports_gpu=True,
                supports_tpu=False,
                supports_drive_mounting=False,
                supports_ssh=True,
                supports_docker=True,
                supports_conda=True,
                supports_pip=True,
                supports_npm=True,
                supports_git=True,
                supports_ngrok=True,
                supports_cloudflare_tunnel=True,
                supports_gradio_share=True,
                supports_streamlit=True,
                supports_jupyter=True,
                supports_terminal=True,
                supports_file_upload=True,
                supports_file_download=True,
                supports_network_access=True,
                supports_persistent_storage=True,
                supports_environment_variables=True
            ),
            optimizations=PlatformOptimizations(
                enable_memory_optimization=True,
                enable_disk_optimization=True,
                enable_network_optimization=True,
                enable_gpu_optimization=True,
                enable_caching=True,
                enable_compression=True,
                enable_deduplication=True,
                enable_cleanup=True,
                cleanup_interval_minutes=120,
                cache_size_mb=5000,
                compression_level=9
            ),
            environment_variables={
                'LIGHTNING_CLOUD_PROJECT_ID': 'lightning-project',
                'LIGHTNING_CLOUD_APP_ID': 'lightning-app',
                'LIGHTNING_CLOUD_WORK_ID': 'lightning-work'
            },
            system_requirements=[
                'Python 3.8+',
                'CUDA 11.0+',
                'cuDNN 8.0+',
                'Docker 20.0+',
                'Lightning CLI'
            ],
            installation_commands=[
                'pip install --upgrade pip',
                'pip install lightning',
                'pip install torch torchvision torchaudio',
                'pip install tensorflow',
                'pip install jupyter',
                'pip install streamlit',
                'pip install gradio'
            ],
            troubleshooting_tips=[
                'Check Lightning CLI status',
                'Verify team workspace access',
                'Check resource allocation',
                'Monitor collaboration features'
            ]
        )
        
        # Paperspace Configuration
        configs[CloudPlatform.PAPERSPACE] = PlatformConfigurationuration(
            platform=CloudPlatform.PAPERSPACE,
            display_name="Paperspace",
            description="Cloud computing platform with GPU instances and persistent storage",
            paths=PathConfiguration(
                base_path="/paperspace",
                apps_path="/paperspace/apps",
                data_path="/paperspace/data",
                temp_path="/tmp",
                logs_path="/paperspace/logs",
                cache_path="/paperspace/cache",
                models_path="/paperspace/models",
                config_path="/paperspace/config",
                workspace_path="/paperspace/workspace",
                drive_mount_path=None,
                shared_storage_path="/paperspace/shared"
            ),
            limits=ResourceLimits(
                max_memory_gb=128.0,
                max_disk_gb=2000.0,
                max_cpu_cores=32,
                max_gpu_count=8,
                session_timeout_hours=72.0,
                idle_timeout_minutes=180.0,
                max_concurrent_processes=100,
                max_file_size_mb=10000.0
            ),
            features=PlatformFeatures(
                supports_gpu=True,
                supports_tpu=False,
                supports_drive_mounting=False,
                supports_ssh=True,
                supports_docker=True,
                supports_conda=True,
                supports_pip=True,
                supports_npm=True,
                supports_git=True,
                supports_ngrok=True,
                supports_cloudflare_tunnel=True,
                supports_gradio_share=True,
                supports_streamlit=True,
                supports_jupyter=True,
                supports_terminal=True,
                supports_file_upload=True,
                supports_file_download=True,
                supports_network_access=True,
                supports_persistent_storage=True,
                supports_environment_variables=True
            ),
            optimizations=PlatformOptimizations(
                enable_memory_optimization=True,
                enable_disk_optimization=True,
                enable_network_optimization=True,
                enable_gpu_optimization=True,
                enable_caching=True,
                enable_compression=True,
                enable_deduplication=True,
                enable_cleanup=True,
                cleanup_interval_minutes=180,
                cache_size_mb=10000,
                compression_level=9
            ),
            environment_variables={
                'PAPERSPACE_API_KEY': 'paperspace-api-key',
                'PAPERSPACE_MACHINE_ID': 'paperspace-machine',
                'PAPERSPACE_WORKSPACE_ID': 'paperspace-workspace'
            },
            system_requirements=[
                'Python 3.8+',
                'CUDA 11.0+',
                'cuDNN 8.0+',
                'Docker 20.0+',
                'Paperspace CLI'
            ],
            installation_commands=[
                'pip install --upgrade pip',
                'pip install paperspace',
                'pip install torch torchvision torchaudio',
                'pip install tensorflow',
                'pip install jupyter',
                'pip install streamlit',
                'pip install gradio'
            ],
            troubleshooting_tips=[
                'Check Paperspace CLI status',
                'Verify machine instance status',
                'Check persistent storage access',
                'Monitor billing and usage'
            ]
        )
        
        # RunPod Configuration
        configs[CloudPlatform.RUNPOD] = PlatformConfigurationuration(
            platform=CloudPlatform.RUNPOD,
            display_name="RunPod",
            description="Serverless GPU cloud platform with container-based deployment",
            paths=PathConfiguration(
                base_path="/runpod",
                apps_path="/runpod/apps",
                data_path="/runpod/data",
                temp_path="/tmp",
                logs_path="/runpod/logs",
                cache_path="/runpod/cache",
                models_path="/runpod/models",
                config_path="/runpod/config",
                workspace_path="/runpod/workspace",
                drive_mount_path=None,
                shared_storage_path="/runpod/shared"
            ),
            limits=ResourceLimits(
                max_memory_gb=256.0,
                max_disk_gb=5000.0,
                max_cpu_cores=64,
                max_gpu_count=16,
                session_timeout_hours=168.0,
                idle_timeout_minutes=240.0,
                max_concurrent_processes=200,
                max_file_size_mb=50000.0
            ),
            features=PlatformFeatures(
                supports_gpu=True,
                supports_tpu=False,
                supports_drive_mounting=False,
                supports_ssh=True,
                supports_docker=True,
                supports_conda=True,
                supports_pip=True,
                supports_npm=True,
                supports_git=True,
                supports_ngrok=True,
                supports_cloudflare_tunnel=True,
                supports_gradio_share=True,
                supports_streamlit=True,
                supports_jupyter=True,
                supports_terminal=True,
                supports_file_upload=True,
                supports_file_download=True,
                supports_network_access=True,
                supports_persistent_storage=True,
                supports_environment_variables=True
            ),
            optimizations=PlatformOptimizations(
                enable_memory_optimization=True,
                enable_disk_optimization=True,
                enable_network_optimization=True,
                enable_gpu_optimization=True,
                enable_caching=True,
                enable_compression=True,
                enable_deduplication=True,
                enable_cleanup=True,
                cleanup_interval_minutes=240,
                cache_size_mb=20000,
                compression_level=9
            ),
            environment_variables={
                'RUNPOD_POD_ID': 'runpod-pod',
                'RUNPOD_API_KEY': 'runpod-api-key',
                'RUNPOD_WORKSPACE_ID': 'runpod-workspace'
            },
            system_requirements=[
                'Python 3.8+',
                'CUDA 11.0+',
                'cuDNN 8.0+',
                'Docker 20.0+',
                'RunPod CLI'
            ],
            installation_commands=[
                'pip install --upgrade pip',
                'pip install runpod',
                'pip install torch torchvision torchaudio',
                'pip install tensorflow',
                'pip install jupyter',
                'pip install streamlit',
                'pip install gradio'
            ],
            troubleshooting_tips=[
                'Check RunPod CLI status',
                'Verify pod instance status',
                'Check container deployment',
                'Monitor resource usage and billing'
            ]
        )
        
        return configs
    
    def get_config(self, platform: CloudPlatform) -> Optional[PlatformConfigurationuration]:
        """
        Get configuration for a specific platform.
        
        Args:
            platform: CloudPlatform enum value
            
        Returns:
            PlatformConfigurationuration or None if not found
        """
        return self._configs.get(platform)
    
    def get_all_configs(self) -> Dict[CloudPlatform, PlatformConfigurationuration]:
        """
        Get all platform configurations.
        
        Returns:
            Dictionary of all platform configurations
        """
        return self._configs.copy()
    
    def get_supported_platforms(self) -> List[CloudPlatform]:
        """
        Get list of all supported platforms.
        
        Returns:
            List of supported CloudPlatform enum values
        """
        return list(self._configs.keys())
    
    def validate_platform_requirements(self, platform: CloudPlatform) -> Dict[str, bool]:
        """
        Validate if current environment meets platform requirements.
        
        Args:
            platform: CloudPlatform enum value
            
        Returns:
            Dictionary of requirement validation results
        """
        config = self.get_config(platform)
        if not config:
            return {}
        
        validation_results = {}
        
        # Check Python version
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        validation_results['python_version'] = sys.version_info >= (3, 8)
        
        # Check available memory
        try:
            import psutil
            available_memory_gb = psutil.virtual_memory().total / (1024**3)
            validation_results['memory'] = available_memory_gb >= config.limits.max_memory_gb
        except ImportError:
            validation_results['memory'] = False
        
        # Check available disk space
        try:
            import shutil
            available_disk_gb = shutil.disk_usage('/').free / (1024**3)
            validation_results['disk_space'] = available_disk_gb >= config.limits.max_disk_gb
        except:
            validation_results['disk_space'] = False
        
        # Check GPU availability
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
            validation_results['gpu'] = result.returncode == 0 and config.features.supports_gpu
        except:
            validation_results['gpu'] = not config.features.supports_gpu
        
        # Check required tools
        required_tools = ['pip', 'git']
        for tool in required_tools:
            try:
                import subprocess
                result = subprocess.run([tool, '--version'], capture_output=True, text=True, timeout=5)
                validation_results[tool] = result.returncode == 0
            except:
                validation_results[tool] = False
        
        return validation_results
    
    def get_platform_summary(self, platform: CloudPlatform) -> str:
        """
        Get a human-readable summary of platform configuration.
        
        Args:
            platform: CloudPlatform enum value
            
        Returns:
            Human-readable platform summary
        """
        config = self.get_config(platform)
        if not config:
            return f"Platform {platform.value} not found"
        
        summary = f"Platform: {config.display_name}\n"
        summary += f"Description: {config.description}\n"
        summary += f"Base Path: {config.paths.base_path}\n"
        summary += f"Max Memory: {config.limits.max_memory_gb} GB\n"
        summary += f"Max Disk: {config.limits.max_disk_gb} GB\n"
        summary += f"Max GPU: {config.limits.max_gpu_count}\n"
        summary += f"Session Timeout: {config.limits.session_timeout_hours} hours\n"
        summary += f"Supports GPU: {config.features.supports_gpu}\n"
        summary += f"Supports Docker: {config.features.supports_docker}\n"
        summary += f"Supports SSH: {config.features.supports_ssh}\n"
        
        return summary


def main():
    """Main function for testing platform configurations."""
    manager = PlatformConfigurationManager()
    
    print("Supported Platforms:")
    for platform in manager.get_supported_platforms():
        if platform != CloudPlatform.UNKNOWN:
            print(f"- {platform.value}")
    
    print("\nPlatform Configurations:")
    for platform in manager.get_supported_platforms():
        if platform != CloudPlatform.UNKNOWN:
            print(f"\n{manager.get_platform_summary(platform)}")
    
    return manager.get_all_configs()


if __name__ == "__main__":
    main()