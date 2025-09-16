#!/usr/bin/env python3
"""
PinokioCloud App Profiler

This module creates comprehensive profiles for Pinokio applications.
It combines analysis from installer detection, web UI detection,
dependency analysis, and tunnel requirements to create complete app profiles.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import analysis modules
from .installer_detector import InstallerType, InstallerInfo
from .webui_detector import WebUIType, WebUIInfo
from .dependency_analyzer import DependencyType, DependencyInfo
from .tunnel_requirements import TunnelType, TunnelInfo


class AppCategory(Enum):
    """Enumeration of app categories."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    LLM = "llm"
    UTILITY = "utility"
    GAME = "game"
    WEB = "web"
    DATA = "data"
    DEVELOPMENT = "development"
    UNKNOWN = "unknown"


class AppComplexity(Enum):
    """Enumeration of app complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ADVANCED = "advanced"


class AppStatus(Enum):
    """Enumeration of app status."""
    READY = "ready"
    NEEDS_SETUP = "needs_setup"
    NEEDS_DEPENDENCIES = "needs_dependencies"
    NEEDS_CONFIGURATION = "needs_configuration"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class AppProfile:
    """Complete application profile."""
    app_name: str
    app_path: str
    category: AppCategory
    complexity: AppComplexity
    status: AppStatus
    
    # Analysis results
    installer_info: Optional[InstallerInfo] = None
    webui_info: Optional[WebUIInfo] = None
    dependency_info: Optional[DependencyInfo] = None
    tunnel_info: Optional[TunnelInfo] = None
    
    # Profile metadata
    profile_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    version: str = "1.0.0"
    
    # App characteristics
    has_web_ui: bool = False
    has_cli_interface: bool = False
    has_api: bool = False
    requires_gpu: bool = False
    requires_internet: bool = False
    requires_authentication: bool = False
    
    # Resource requirements
    estimated_memory_mb: int = 0
    estimated_storage_mb: int = 0
    estimated_cpu_cores: int = 1
    estimated_gpu_memory_mb: int = 0
    
    # Installation characteristics
    installation_time_estimate: int = 0  # seconds
    startup_time_estimate: int = 0  # seconds
    shutdown_time_estimate: int = 0  # seconds
    
    # Compatibility
    python_version_compatibility: List[str] = field(default_factory=list)
    operating_system_compatibility: List[str] = field(default_factory=list)
    cloud_platform_compatibility: List[str] = field(default_factory=list)
    
    # Tags and descriptions
    tags: List[str] = field(default_factory=list)
    description: str = ""
    long_description: str = ""
    author: str = ""
    license: str = ""
    repository_url: str = ""
    
    # Risk assessment
    security_risks: List[str] = field(default_factory=list)
    stability_risks: List[str] = field(default_factory=list)
    performance_risks: List[str] = field(default_factory=list)
    
    # Recommendations
    installation_recommendations: List[str] = field(default_factory=list)
    usage_recommendations: List[str] = field(default_factory=list)
    optimization_recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class AppProfiler:
    """
    Creates comprehensive profiles for Pinokio applications.
    
    Combines analysis from multiple sources to create complete app profiles including:
    - App characteristics and capabilities
    - Resource requirements and estimates
    - Installation and runtime characteristics
    - Compatibility and risk assessment
    - Recommendations and optimizations
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the app profiler.
        
        Args:
            base_path: Base path for profiling
        """
        self.base_path = base_path
        
        # Category mapping patterns
        self.category_patterns = {
            AppCategory.IMAGE: [
                "image", "vision", "computer vision", "opencv", "pillow", "pil",
                "stable diffusion", "dalle", "midjourney", "img2img", "inpainting",
                "upscaling", "super resolution", "face", "detection", "recognition"
            ],
            AppCategory.VIDEO: [
                "video", "movie", "animation", "ffmpeg", "opencv", "video processing",
                "video generation", "video editing", "video synthesis", "video upscaling"
            ],
            AppCategory.AUDIO: [
                "audio", "sound", "music", "speech", "voice", "whisper", "tts",
                "text to speech", "speech to text", "audio processing", "audio generation"
            ],
            AppCategory.TEXT: [
                "text", "nlp", "natural language", "language model", "transformer",
                "gpt", "bert", "text generation", "text processing", "text analysis"
            ],
            AppCategory.LLM: [
                "llm", "large language model", "gpt", "chatgpt", "claude", "llama",
                "falcon", "mistral", "text generation", "conversation", "chat"
            ],
            AppCategory.UTILITY: [
                "utility", "tool", "helper", "converter", "formatter", "parser",
                "downloader", "uploader", "backup", "sync", "monitor"
            ],
            AppCategory.GAME: [
                "game", "gaming", "play", "entertainment", "simulation", "engine"
            ],
            AppCategory.WEB: [
                "web", "website", "server", "api", "rest", "graphql", "http",
                "flask", "django", "fastapi", "streamlit", "gradio"
            ],
            AppCategory.DATA: [
                "data", "database", "analytics", "visualization", "plot", "chart",
                "pandas", "numpy", "matplotlib", "seaborn", "plotly"
            ],
            AppCategory.DEVELOPMENT: [
                "development", "dev", "code", "programming", "ide", "editor",
                "debug", "test", "build", "deploy", "ci", "cd"
            ]
        }
        
        # Complexity assessment patterns
        self.complexity_indicators = {
            AppComplexity.SIMPLE: {
                "max_dependencies": 5,
                "max_files": 10,
                "max_lines": 500,
                "indicators": ["single file", "simple script", "basic functionality"]
            },
            AppComplexity.MODERATE: {
                "max_dependencies": 15,
                "max_files": 25,
                "max_lines": 2000,
                "indicators": ["multiple files", "configuration", "basic web ui"]
            },
            AppComplexity.COMPLEX: {
                "max_dependencies": 30,
                "max_files": 50,
                "max_lines": 5000,
                "indicators": ["multiple modules", "advanced features", "web ui", "api"]
            },
            AppComplexity.ADVANCED: {
                "max_dependencies": 50,
                "max_files": 100,
                "max_lines": 10000,
                "indicators": ["microservices", "distributed", "enterprise", "advanced ml"]
            }
        }
    
    def create_profile(self, app_name: str, app_path: str, 
                      installer_info: Optional[InstallerInfo],
                      webui_info: Optional[WebUIInfo],
                      dependency_info: Optional[DependencyInfo],
                      tunnel_info: Optional[TunnelInfo]) -> AppProfile:
        """
        Create a comprehensive app profile.
        
        Args:
            app_name: Name of the application
            app_path: Path to the application
            installer_info: Installer analysis information
            webui_info: Web UI analysis information
            dependency_info: Dependency analysis information
            tunnel_info: Tunnel requirements information
            
        Returns:
            AppProfile: Complete application profile
        """
        try:
            # Create base profile
            profile = AppProfile(
                app_name=app_name,
                app_path=app_path,
                category=AppCategory.UNKNOWN,
                complexity=AppComplexity.SIMPLE,
                status=AppStatus.UNKNOWN,
                profile_id=self._generate_profile_id(app_name, app_path),
                created_at=self._get_timestamp(),
                updated_at=self._get_timestamp()
            )
            
            # Store analysis results
            profile.installer_info = installer_info
            profile.webui_info = webui_info
            profile.dependency_info = dependency_info
            profile.tunnel_info = tunnel_info
            
            # Analyze app characteristics
            self._analyze_app_characteristics(profile)
            
            # Determine category
            profile.category = self._determine_category(profile)
            
            # Assess complexity
            profile.complexity = self._assess_complexity(profile)
            
            # Determine status
            profile.status = self._determine_status(profile)
            
            # Estimate resource requirements
            self._estimate_resource_requirements(profile)
            
            # Estimate timing characteristics
            self._estimate_timing_characteristics(profile)
            
            # Assess compatibility
            self._assess_compatibility(profile)
            
            # Generate tags and descriptions
            self._generate_tags_and_descriptions(profile)
            
            # Assess risks
            self._assess_risks(profile)
            
            # Generate recommendations
            self._generate_recommendations(profile)
            
            # Update metadata
            profile.metadata = {
                "analysis_timestamp": self._get_timestamp(),
                "profile_version": "1.0.0",
                "analysis_confidence": self._calculate_analysis_confidence(profile)
            }
            
            return profile
        
        except Exception as e:
            return AppProfile(
                app_name=app_name,
                app_path=app_path,
                category=AppCategory.UNKNOWN,
                complexity=AppComplexity.SIMPLE,
                status=AppStatus.ERROR,
                metadata={"error": str(e)}
            )
    
    def _generate_profile_id(self, app_name: str, app_path: str) -> str:
        """Generate unique profile ID."""
        try:
            content = f"{app_name}:{app_path}:{self._get_timestamp()}"
            return hashlib.md5(content.encode()).hexdigest()[:12]
        except:
            return f"profile_{int(time.time())}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def _analyze_app_characteristics(self, profile: AppProfile):
        """Analyze app characteristics."""
        try:
            # Check for web UI
            if profile.webui_info and profile.webui_info.webui_type != WebUIType.NONE:
                profile.has_web_ui = True
            
            # Check for CLI interface
            if profile.installer_info and profile.installer_info.installer_type in [InstallerType.PYTHON_SCRIPT, InstallerType.SHELL_SCRIPT]:
                profile.has_cli_interface = True
            
            # Check for API
            if profile.webui_info and profile.webui_info.webui_type in [WebUIType.FASTAPI, WebUIType.FLASK]:
                profile.has_api = True
            
            # Check for GPU requirements
            if profile.dependency_info:
                gpu_deps = ["torch", "tensorflow", "cuda", "cudnn", "nvidia", "gpu"]
                all_deps = (profile.dependency_info.pip_dependencies + 
                           profile.dependency_info.conda_dependencies)
                
                for dep in all_deps:
                    if any(gpu_dep in dep.lower() for gpu_dep in gpu_deps):
                        profile.requires_gpu = True
                        break
            
            # Check for internet requirements
            if profile.dependency_info:
                internet_deps = ["requests", "urllib", "httpx", "aiohttp", "download", "fetch"]
                all_deps = (profile.dependency_info.pip_dependencies + 
                           profile.dependency_info.conda_dependencies)
                
                for dep in all_deps:
                    if any(internet_dep in dep.lower() for internet_dep in internet_deps):
                        profile.requires_internet = True
                        break
            
            # Check for authentication requirements
            if profile.tunnel_info and profile.tunnel_info.authentication_required:
                profile.requires_authentication = True
        
        except Exception as e:
            pass
    
    def _determine_category(self, profile: AppProfile) -> AppCategory:
        """Determine app category."""
        try:
            # Get all text to analyze
            text_to_analyze = [
                profile.app_name,
                profile.app_path
            ]
            
            if profile.dependency_info:
                text_to_analyze.extend(profile.dependency_info.pip_dependencies)
                text_to_analyze.extend(profile.dependency_info.conda_dependencies)
            
            if profile.webui_info:
                text_to_analyze.append(profile.webui_info.webui_type.value)
            
            # Analyze against category patterns
            category_scores = {}
            for category, patterns in self.category_patterns.items():
                score = 0
                for text in text_to_analyze:
                    text_lower = text.lower()
                    for pattern in patterns:
                        if pattern in text_lower:
                            score += 1
                
                if score > 0:
                    category_scores[category] = score
            
            # Return highest scoring category
            if category_scores:
                return max(category_scores.items(), key=lambda x: x[1])[0]
            
            return AppCategory.UNKNOWN
        
        except Exception as e:
            return AppCategory.UNKNOWN
    
    def _assess_complexity(self, profile: AppProfile) -> AppComplexity:
        """Assess app complexity."""
        try:
            # Count dependencies
            total_dependencies = 0
            if profile.dependency_info:
                total_dependencies = (len(profile.dependency_info.pip_dependencies) + 
                                    len(profile.dependency_info.conda_dependencies) + 
                                    len(profile.dependency_info.npm_dependencies))
            
            # Count files (estimate)
            file_count = 0
            if os.path.exists(profile.app_path):
                try:
                    for root, dirs, files in os.walk(profile.app_path):
                        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                        file_count += len(files)
                except:
                    pass
            
            # Assess against complexity indicators
            for complexity, indicators in self.complexity_indicators.items():
                if (total_dependencies <= indicators["max_dependencies"] and 
                    file_count <= indicators["max_files"]):
                    return complexity
            
            return AppComplexity.ADVANCED
        
        except Exception as e:
            return AppComplexity.SIMPLE
    
    def _determine_status(self, profile: AppProfile) -> AppStatus:
        """Determine app status."""
        try:
            # Check if app has all required components
            if not profile.installer_info or profile.installer_info.installer_type == InstallerType.UNKNOWN:
                return AppStatus.NEEDS_SETUP
            
            if not profile.dependency_info or not profile.dependency_info.dependency_types:
                return AppStatus.NEEDS_DEPENDENCIES
            
            if profile.webui_info and profile.webui_info.webui_type != WebUIType.NONE:
                if not profile.tunnel_info or profile.tunnel_info.tunnel_type == TunnelType.UNKNOWN:
                    return AppStatus.NEEDS_CONFIGURATION
            
            return AppStatus.READY
        
        except Exception as e:
            return AppStatus.ERROR
    
    def _estimate_resource_requirements(self, profile: AppProfile):
        """Estimate resource requirements."""
        try:
            # Base estimates
            profile.estimated_memory_mb = 512
            profile.estimated_storage_mb = 100
            profile.estimated_cpu_cores = 1
            profile.estimated_gpu_memory_mb = 0
            
            # Adjust based on dependencies
            if profile.dependency_info:
                total_deps = (len(profile.dependency_info.pip_dependencies) + 
                             len(profile.dependency_info.conda_dependencies))
                
                # Memory estimation
                profile.estimated_memory_mb += total_deps * 50
                
                # Storage estimation
                profile.estimated_storage_mb += total_deps * 20
                
                # GPU memory estimation
                if profile.requires_gpu:
                    profile.estimated_gpu_memory_mb = 2048  # 2GB default
            
            # Adjust based on complexity
            complexity_multipliers = {
                AppComplexity.SIMPLE: 1.0,
                AppComplexity.MODERATE: 1.5,
                AppComplexity.COMPLEX: 2.0,
                AppComplexity.ADVANCED: 3.0
            }
            
            multiplier = complexity_multipliers.get(profile.complexity, 1.0)
            profile.estimated_memory_mb = int(profile.estimated_memory_mb * multiplier)
            profile.estimated_storage_mb = int(profile.estimated_storage_mb * multiplier)
            profile.estimated_cpu_cores = max(1, int(profile.estimated_cpu_cores * multiplier))
        
        except Exception as e:
            pass
    
    def _estimate_timing_characteristics(self, profile: AppProfile):
        """Estimate timing characteristics."""
        try:
            # Base estimates (minimum 30 seconds as per requirements)
            profile.installation_time_estimate = 30
            profile.startup_time_estimate = 30
            profile.shutdown_time_estimate = 5
            
            # Adjust based on dependencies
            if profile.dependency_info:
                total_deps = (len(profile.dependency_info.pip_dependencies) + 
                             len(profile.dependency_info.conda_dependencies))
                
                # Installation time (minimum 30 seconds)
                profile.installation_time_estimate = max(30, total_deps * 10)
                
                # Startup time (minimum 30 seconds)
                profile.startup_time_estimate = max(30, total_deps * 5)
            
            # Adjust based on complexity
            complexity_multipliers = {
                AppComplexity.SIMPLE: 1.0,
                AppComplexity.MODERATE: 1.5,
                AppComplexity.COMPLEX: 2.0,
                AppComplexity.ADVANCED: 3.0
            }
            
            multiplier = complexity_multipliers.get(profile.complexity, 1.0)
            profile.installation_time_estimate = int(profile.installation_time_estimate * multiplier)
            profile.startup_time_estimate = int(profile.startup_time_estimate * multiplier)
        
        except Exception as e:
            pass
    
    def _assess_compatibility(self, profile: AppProfile):
        """Assess compatibility."""
        try:
            # Python version compatibility
            if profile.dependency_info and profile.dependency_info.python_version_requirement:
                profile.python_version_compatibility = [profile.dependency_info.python_version_requirement]
            else:
                profile.python_version_compatibility = ["3.8", "3.9", "3.10", "3.11"]
            
            # Operating system compatibility
            profile.operating_system_compatibility = ["linux", "windows", "macos"]
            
            # Cloud platform compatibility
            profile.cloud_platform_compatibility = ["colab", "vast", "lightning", "paperspace", "runpod"]
        
        except Exception as e:
            pass
    
    def _generate_tags_and_descriptions(self, profile: AppProfile):
        """Generate tags and descriptions."""
        try:
            # Generate tags
            tags = []
            
            # Category tag
            tags.append(profile.category.value)
            
            # Complexity tag
            tags.append(profile.complexity.value)
            
            # Web UI tag
            if profile.has_web_ui:
                tags.append("web-ui")
            
            # CLI tag
            if profile.has_cli_interface:
                tags.append("cli")
            
            # API tag
            if profile.has_api:
                tags.append("api")
            
            # GPU tag
            if profile.requires_gpu:
                tags.append("gpu")
            
            # Internet tag
            if profile.requires_internet:
                tags.append("internet")
            
            # Authentication tag
            if profile.requires_authentication:
                tags.append("authentication")
            
            profile.tags = list(set(tags))
            
            # Generate description
            description_parts = []
            description_parts.append(f"{profile.complexity.value.title()} {profile.category.value} application")
            
            if profile.has_web_ui:
                description_parts.append("with web interface")
            
            if profile.requires_gpu:
                description_parts.append("requiring GPU")
            
            if profile.requires_internet:
                description_parts.append("requiring internet connection")
            
            profile.description = " ".join(description_parts)
            
            # Generate long description
            long_description_parts = [profile.description]
            
            if profile.dependency_info and profile.dependency_info.dependency_types:
                dep_types = [dt.value for dt in profile.dependency_info.dependency_types]
                long_description_parts.append(f"Uses {', '.join(dep_types)} for dependency management.")
            
            if profile.webui_info and profile.webui_info.webui_type != WebUIType.NONE:
                long_description_parts.append(f"Web interface powered by {profile.webui_info.webui_type.value}.")
            
            if profile.tunnel_info and profile.tunnel_info.tunnel_type != TunnelType.NONE:
                long_description_parts.append(f"Supports {profile.tunnel_info.tunnel_type.value} tunneling for public access.")
            
            profile.long_description = " ".join(long_description_parts)
        
        except Exception as e:
            pass
    
    def _assess_risks(self, profile: AppProfile):
        """Assess security, stability, and performance risks."""
        try:
            # Security risks
            security_risks = []
            
            if profile.requires_internet:
                security_risks.append("Requires internet connection - potential data exposure")
            
            if profile.requires_authentication:
                security_risks.append("Requires authentication - credential management needed")
            
            if profile.tunnel_info and profile.tunnel_info.tunnel_type != TunnelType.NONE:
                security_risks.append("Public tunneling enabled - potential security exposure")
            
            profile.security_risks = security_risks
            
            # Stability risks
            stability_risks = []
            
            if profile.complexity in [AppComplexity.COMPLEX, AppComplexity.ADVANCED]:
                stability_risks.append("High complexity - potential stability issues")
            
            if profile.dependency_info and len(profile.dependency_info.conflict_potential) > 0:
                stability_risks.append("Dependency conflicts detected")
            
            if profile.requires_gpu:
                stability_risks.append("GPU requirements - hardware compatibility issues")
            
            profile.stability_risks = stability_risks
            
            # Performance risks
            performance_risks = []
            
            if profile.estimated_memory_mb > 4096:
                performance_risks.append("High memory requirements - potential performance issues")
            
            if profile.estimated_gpu_memory_mb > 8192:
                performance_risks.append("High GPU memory requirements - potential performance issues")
            
            if profile.installation_time_estimate > 300:
                performance_risks.append("Long installation time - potential timeout issues")
            
            profile.performance_risks = performance_risks
        
        except Exception as e:
            pass
    
    def _generate_recommendations(self, profile: AppProfile):
        """Generate recommendations."""
        try:
            # Installation recommendations
            installation_recommendations = []
            
            if profile.requires_gpu:
                installation_recommendations.append("Ensure GPU drivers are installed and compatible")
            
            if profile.dependency_info and len(profile.dependency_info.conflict_potential) > 0:
                installation_recommendations.append("Resolve dependency conflicts before installation")
            
            if profile.estimated_memory_mb > 2048:
                installation_recommendations.append("Ensure sufficient memory is available")
            
            profile.installation_recommendations = installation_recommendations
            
            # Usage recommendations
            usage_recommendations = []
            
            if profile.has_web_ui:
                usage_recommendations.append("Access via web browser for best experience")
            
            if profile.requires_internet:
                usage_recommendations.append("Ensure stable internet connection")
            
            if profile.requires_authentication:
                usage_recommendations.append("Keep authentication credentials secure")
            
            profile.usage_recommendations = usage_recommendations
            
            # Optimization recommendations
            optimization_recommendations = []
            
            if profile.estimated_memory_mb > 2048:
                optimization_recommendations.append("Consider increasing system memory")
            
            if profile.requires_gpu:
                optimization_recommendations.append("Use GPU-optimized versions of dependencies")
            
            if profile.installation_time_estimate > 180:
                optimization_recommendations.append("Consider using pre-built containers or images")
            
            profile.optimization_recommendations = optimization_recommendations
        
        except Exception as e:
            pass
    
    def _calculate_analysis_confidence(self, profile: AppProfile) -> float:
        """Calculate analysis confidence score."""
        try:
            confidence = 0.0
            total_checks = 0
            
            # Check installer analysis
            if profile.installer_info and profile.installer_info.installer_type != InstallerType.UNKNOWN:
                confidence += 0.25
            total_checks += 1
            
            # Check web UI analysis
            if profile.webui_info and profile.webui_info.webui_type != WebUIType.UNKNOWN:
                confidence += 0.25
            total_checks += 1
            
            # Check dependency analysis
            if profile.dependency_info and profile.dependency_info.dependency_types:
                confidence += 0.25
            total_checks += 1
            
            # Check tunnel analysis
            if profile.tunnel_info and profile.tunnel_info.tunnel_type != TunnelType.UNKNOWN:
                confidence += 0.25
            total_checks += 1
            
            return confidence / total_checks if total_checks > 0 else 0.0
        
        except Exception as e:
            return 0.0
    
    def save_profile(self, profile: AppProfile, output_path: str) -> bool:
        """
        Save app profile to JSON file.
        
        Args:
            profile: App profile to save
            output_path: Path to save profile
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert profile to serializable format
            profile_dict = {
                "app_name": profile.app_name,
                "app_path": profile.app_path,
                "category": profile.category.value,
                "complexity": profile.complexity.value,
                "status": profile.status.value,
                "profile_id": profile.profile_id,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
                "version": profile.version,
                "has_web_ui": profile.has_web_ui,
                "has_cli_interface": profile.has_cli_interface,
                "has_api": profile.has_api,
                "requires_gpu": profile.requires_gpu,
                "requires_internet": profile.requires_internet,
                "requires_authentication": profile.requires_authentication,
                "estimated_memory_mb": profile.estimated_memory_mb,
                "estimated_storage_mb": profile.estimated_storage_mb,
                "estimated_cpu_cores": profile.estimated_cpu_cores,
                "estimated_gpu_memory_mb": profile.estimated_gpu_memory_mb,
                "installation_time_estimate": profile.installation_time_estimate,
                "startup_time_estimate": profile.startup_time_estimate,
                "shutdown_time_estimate": profile.shutdown_time_estimate,
                "python_version_compatibility": profile.python_version_compatibility,
                "operating_system_compatibility": profile.operating_system_compatibility,
                "cloud_platform_compatibility": profile.cloud_platform_compatibility,
                "tags": profile.tags,
                "description": profile.description,
                "long_description": profile.long_description,
                "author": profile.author,
                "license": profile.license,
                "repository_url": profile.repository_url,
                "security_risks": profile.security_risks,
                "stability_risks": profile.stability_risks,
                "performance_risks": profile.performance_risks,
                "installation_recommendations": profile.installation_recommendations,
                "usage_recommendations": profile.usage_recommendations,
                "optimization_recommendations": profile.optimization_recommendations,
                "metadata": profile.metadata
            }
            
            # Save to file
            with open(output_path, 'w') as f:
                json.dump(profile_dict, f, indent=2, default=str)
            
            return True
        
        except Exception as e:
            return False


def main():
    """Main function for testing app profiler."""
    print("🧪 Testing App Profiler")
    print("=" * 50)
    
    # Initialize profiler
    profiler = AppProfiler()
    
    # Create sample analysis results
    from .installer_detector import InstallerInfo, InstallerType
    from .webui_detector import WebUIInfo, WebUIType
    from .dependency_analyzer import DependencyInfo, DependencyType
    from .tunnel_requirements import TunnelInfo, TunnelType
    
    installer_info = InstallerInfo(
        installer_type=InstallerType.REQUIREMENTS_TXT,
        installer_path="/tmp/requirements.txt",
        installer_content="torch>=1.9.0\nnumpy>=1.21.0\nopencv-python>=4.5.0",
        dependencies=["torch", "numpy", "opencv-python"],
        has_venv_creation=True
    )
    
    webui_info = WebUIInfo(
        webui_type=WebUIType.GRADIO,
        main_file="app.py",
        port=7860,
        share_enabled=True
    )
    
    dependency_info = DependencyInfo(
        dependency_types=[DependencyType.PIP],
        pip_dependencies=["torch", "numpy", "opencv-python", "gradio"],
        python_version_requirement="3.8"
    )
    
    tunnel_info = TunnelInfo(
        tunnel_type=TunnelType.NGROK,
        required=True,
        port=7860,
        share_enabled=True
    )
    
    # Test profile creation
    print("\n📊 Testing app profile creation...")
    profile = profiler.create_profile(
        "test-app",
        "/tmp/test-app",
        installer_info,
        webui_info,
        dependency_info,
        tunnel_info
    )
    
    print(f"✅ App name: {profile.app_name}")
    print(f"✅ Category: {profile.category.value}")
    print(f"✅ Complexity: {profile.complexity.value}")
    print(f"✅ Status: {profile.status.value}")
    print(f"✅ Has web UI: {profile.has_web_ui}")
    print(f"✅ Has CLI: {profile.has_cli_interface}")
    print(f"✅ Has API: {profile.has_api}")
    print(f"✅ Requires GPU: {profile.requires_gpu}")
    print(f"✅ Requires internet: {profile.requires_internet}")
    print(f"✅ Estimated memory: {profile.estimated_memory_mb} MB")
    print(f"✅ Estimated storage: {profile.estimated_storage_mb} MB")
    print(f"✅ Installation time: {profile.installation_time_estimate} seconds")
    print(f"✅ Startup time: {profile.startup_time_estimate} seconds")
    print(f"✅ Tags: {', '.join(profile.tags)}")
    print(f"✅ Description: {profile.description}")
    print(f"✅ Security risks: {len(profile.security_risks)} found")
    print(f"✅ Stability risks: {len(profile.stability_risks)} found")
    print(f"✅ Performance risks: {len(profile.performance_risks)} found")
    print(f"✅ Installation recommendations: {len(profile.installation_recommendations)} found")
    print(f"✅ Usage recommendations: {len(profile.usage_recommendations)} found")
    print(f"✅ Optimization recommendations: {len(profile.optimization_recommendations)} found")
    print(f"✅ Analysis confidence: {profile.metadata.get('analysis_confidence', 0):.2f}")
    
    return True


if __name__ == "__main__":
    main()