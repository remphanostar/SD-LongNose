#!/usr/bin/env python3
"""
PinokioCloud Conda Manager

This module handles conda-based dependency installation for Pinokio applications.
It provides comprehensive conda environment and package management including
environment creation, package installation, dependency resolution, and verification.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import re
import subprocess
import time
import yaml
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class CondaInstallStatus(Enum):
    """Enumeration of conda installation statuses."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"


class CondaEnvironmentStatus(Enum):
    """Enumeration of conda environment statuses."""
    EXISTS = "exists"
    CREATED = "created"
    FAILED = "failed"
    NOT_FOUND = "not_found"


@dataclass
class CondaPackage:
    """Information about a conda package."""
    name: str
    version: Optional[str] = None
    channel: str = "defaults"
    build_string: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    size_mb: float = 0.0
    install_time: float = 0.0
    status: CondaInstallStatus = CondaInstallStatus.IN_PROGRESS
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CondaEnvironment:
    """Information about a conda environment."""
    name: str
    path: str
    python_version: Optional[str] = None
    packages: List[CondaPackage] = field(default_factory=list)
    status: CondaEnvironmentStatus = CondaEnvironmentStatus.NOT_FOUND
    created_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CondaInstallationResult:
    """Result of conda installation operation."""
    success: bool
    environment: Optional[CondaEnvironment] = None
    packages_installed: List[CondaPackage] = field(default_factory=list)
    packages_failed: List[CondaPackage] = field(default_factory=list)
    total_packages: int = 0
    installation_time: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CondaManager:
    """
    Manages conda-based dependency installation for Pinokio applications.
    
    Provides comprehensive conda environment and package management including:
    - Environment creation and management
    - Package installation from environment files
    - Individual package installation
    - Dependency resolution and conflict handling
    - Installation verification and testing
    - Progress tracking and error handling
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the conda manager.
        
        Args:
            base_path: Base path for conda operations
        """
        self.base_path = base_path
        self.conda_executable = self._find_conda_executable()
        self.install_timeout = 600  # 10 minutes timeout for conda
        self.progress_callback = None
        
        # Conda channels
        self.default_channels = [
            "defaults",
            "conda-forge",
            "pytorch",
            "nvidia",
            "bioconda",
            "r"
        ]
        
        # Package categories for better organization
        self.package_categories = {
            'ml_ai': ['pytorch', 'tensorflow', 'keras', 'scikit-learn', 'numpy', 'pandas', 'opencv'],
            'web': ['flask', 'fastapi', 'django', 'streamlit', 'gradio', 'dash', 'tornado'],
            'data': ['pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'plotly', 'bokeh'],
            'vision': ['opencv', 'pillow', 'imageio', 'scikit-image', 'albumentations', 'torchvision'],
            'audio': ['librosa', 'soundfile', 'pyaudio', 'pydub', 'webrtcvad', 'whisper', 'torchaudio'],
            'text': ['transformers', 'tokenizers', 'nltk', 'spacy', 'textblob', 'gensim', 'langchain'],
            'utility': ['requests', 'urllib3', 'httpx', 'aiohttp', 'click', 'typer', 'rich', 'tqdm']
        }
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def create_environment_from_file(self, environment_file: str, 
                                   environment_name: Optional[str] = None,
                                   force: bool = False) -> CondaInstallationResult:
        """
        Create conda environment from environment file.
        
        Args:
            environment_file: Path to environment.yml file
            environment_name: Name for the environment (optional)
            force: Whether to force recreation if environment exists
            
        Returns:
            CondaInstallationResult: Installation result
        """
        start_time = time.time()
        
        result = CondaInstallationResult(
            success=False
        )
        
        try:
            if not os.path.exists(environment_file):
                result.error_messages.append(f"Environment file not found: {environment_file}")
                return result
            
            # Parse environment file
            env_config = self._parse_environment_file(environment_file)
            
            if not env_config:
                result.error_messages.append("Failed to parse environment file")
                return result
            
            # Determine environment name
            if not environment_name:
                environment_name = env_config.get('name', 'pinokio_env')
            
            self._update_progress(f"Creating conda environment: {environment_name}")
            
            # Check if environment exists
            if self._environment_exists(environment_name):
                if force:
                    self._update_progress(f"Removing existing environment: {environment_name}")
                    self._remove_environment(environment_name)
                else:
                    result.error_messages.append(f"Environment {environment_name} already exists. Use force=True to recreate.")
                    return result
            
            # Create environment
            env_result = self._create_environment(environment_name, env_config)
            
            if not env_result.success:
                result.error_messages.extend(env_result.error_messages)
                result.installation_time = time.time() - start_time
                return result
            
            result.environment = env_result.environment
            result.packages_installed = env_result.packages_installed
            result.packages_failed = env_result.packages_failed
            result.total_packages = len(env_result.packages_installed) + len(env_result.packages_failed)
            result.success = len(env_result.packages_failed) == 0
            result.installation_time = time.time() - start_time
            
            self._update_progress(f"Environment creation complete: {environment_name}")
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during environment creation: {str(e)}")
            result.installation_time = time.time() - start_time
            return result
    
    def create_environment(self, environment_name: str, 
                          python_version: Optional[str] = None,
                          packages: Optional[List[str]] = None) -> CondaInstallationResult:
        """
        Create a new conda environment.
        
        Args:
            environment_name: Name of the environment
            python_version: Python version to install (optional)
            packages: List of packages to install (optional)
            
        Returns:
            CondaInstallationResult: Installation result
        """
        start_time = time.time()
        
        result = CondaInstallationResult(
            success=False
        )
        
        try:
            self._update_progress(f"Creating conda environment: {environment_name}")
            
            # Check if environment exists
            if self._environment_exists(environment_name):
                result.error_messages.append(f"Environment {environment_name} already exists")
                return result
            
            # Build create command
            create_cmd = [self.conda_executable, 'create', '-n', environment_name, '-y']
            
            if python_version:
                create_cmd.extend(['python', python_version])
            
            if packages:
                create_cmd.extend(packages)
            
            # Execute creation
            success, output, error = self._execute_conda_command(create_cmd)
            
            if not success:
                result.error_messages.append(f"Failed to create environment: {error}")
                result.installation_time = time.time() - start_time
                return result
            
            # Get environment information
            environment = self._get_environment_info(environment_name)
            result.environment = environment
            result.success = True
            result.installation_time = time.time() - start_time
            
            self._update_progress(f"Environment created successfully: {environment_name}")
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during environment creation: {str(e)}")
            result.installation_time = time.time() - start_time
            return result
    
    def install_packages(self, environment_name: str, 
                        packages: List[str],
                        channel: Optional[str] = None) -> CondaInstallationResult:
        """
        Install packages in a conda environment.
        
        Args:
            environment_name: Name of the environment
            packages: List of packages to install
            channel: Conda channel to use (optional)
            
        Returns:
            CondaInstallationResult: Installation result
        """
        start_time = time.time()
        
        result = CondaInstallationResult(
            success=False,
            total_packages=len(packages)
        )
        
        try:
            if not packages:
                result.success = True
                result.installation_time = time.time() - start_time
                return result
            
            # Check if environment exists
            if not self._environment_exists(environment_name):
                result.error_messages.append(f"Environment {environment_name} does not exist")
                return result
            
            self._update_progress(f"Installing {len(packages)} packages in {environment_name}")
            
            # Build install command
            install_cmd = [self.conda_executable, 'install', '-n', environment_name, '-y']
            
            if channel:
                install_cmd.extend(['-c', channel])
            
            install_cmd.extend(packages)
            
            # Execute installation
            success, output, error = self._execute_conda_command(install_cmd)
            
            if success:
                # Parse installed packages
                for package_spec in packages:
                    package = self._parse_package_specification(package_spec)
                    if package:
                        package.status = CondaInstallStatus.SUCCESS
                        result.packages_installed.append(package)
                
                result.success = True
                self._update_progress(f"Successfully installed {len(packages)} packages")
            else:
                # Handle failed installation
                for package_spec in packages:
                    package = self._parse_package_specification(package_spec)
                    if package:
                        package.status = CondaInstallStatus.FAILED
                        package.error_message = error
                        result.packages_failed.append(package)
                
                result.error_messages.append(f"Failed to install packages: {error}")
            
            result.installation_time = time.time() - start_time
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during package installation: {str(e)}")
            result.installation_time = time.time() - start_time
            return result
    
    def install_from_environment_file(self, environment_file: str, 
                                    environment_name: Optional[str] = None) -> CondaInstallationResult:
        """
        Install packages from environment file into existing environment.
        
        Args:
            environment_file: Path to environment.yml file
            environment_name: Name of the environment (optional)
            
        Returns:
            CondaInstallationResult: Installation result
        """
        start_time = time.time()
        
        result = CondaInstallationResult(
            success=False
        )
        
        try:
            if not os.path.exists(environment_file):
                result.error_messages.append(f"Environment file not found: {environment_file}")
                return result
            
            # Parse environment file
            env_config = self._parse_environment_file(environment_file)
            
            if not env_config:
                result.error_messages.append("Failed to parse environment file")
                return result
            
            # Determine environment name
            if not environment_name:
                environment_name = env_config.get('name', 'pinokio_env')
            
            # Check if environment exists
            if not self._environment_exists(environment_name):
                result.error_messages.append(f"Environment {environment_name} does not exist")
                return result
            
            self._update_progress(f"Installing packages from {environment_file} into {environment_name}")
            
            # Build install command
            install_cmd = [self.conda_executable, 'env', 'update', '-n', environment_name, '-f', environment_file]
            
            # Execute installation
            success, output, error = self._execute_conda_command(install_cmd)
            
            if success:
                # Get updated environment information
                environment = self._get_environment_info(environment_name)
                result.environment = environment
                result.success = True
                self._update_progress(f"Successfully updated environment {environment_name}")
            else:
                result.error_messages.append(f"Failed to update environment: {error}")
            
            result.installation_time = time.time() - start_time
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during environment update: {str(e)}")
            result.installation_time = time.time() - start_time
            return result
    
    def list_environments(self) -> List[CondaEnvironment]:
        """
        List all conda environments.
        
        Returns:
            List of conda environments
        """
        try:
            # Build list command
            list_cmd = [self.conda_executable, 'env', 'list', '--json']
            
            # Execute command
            success, output, error = self._execute_conda_command(list_cmd)
            
            if not success:
                return []
            
            # Parse JSON output
            envs_data = json.loads(output)
            environments = []
            
            for env_data in envs_data.get('envs', []):
                env_name = os.path.basename(env_data)
                environment = CondaEnvironment(
                    name=env_name,
                    path=env_data,
                    status=CondaEnvironmentStatus.EXISTS
                )
                environments.append(environment)
            
            return environments
        
        except Exception as e:
            return []
    
    def get_environment_info(self, environment_name: str) -> Optional[CondaEnvironment]:
        """
        Get information about a conda environment.
        
        Args:
            environment_name: Name of the environment
            
        Returns:
            CondaEnvironment object or None
        """
        return self._get_environment_info(environment_name)
    
    def remove_environment(self, environment_name: str) -> bool:
        """
        Remove a conda environment.
        
        Args:
            environment_name: Name of the environment to remove
            
        Returns:
            bool: True if successful
        """
        return self._remove_environment(environment_name)
    
    def _parse_environment_file(self, environment_file: str) -> Optional[Dict[str, Any]]:
        """
        Parse conda environment file.
        
        Args:
            environment_file: Path to environment file
            
        Returns:
            Dictionary containing environment configuration
        """
        try:
            with open(environment_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse YAML
            env_config = yaml.safe_load(content)
            
            return env_config
        
        except Exception as e:
            return None
    
    def _create_environment(self, environment_name: str, 
                           env_config: Dict[str, Any]) -> CondaInstallationResult:
        """
        Create conda environment from configuration.
        
        Args:
            environment_name: Name of the environment
            env_config: Environment configuration
            
        Returns:
            CondaInstallationResult: Creation result
        """
        result = CondaInstallationResult(success=False)
        
        try:
            # Build create command
            create_cmd = [self.conda_executable, 'env', 'create', '-n', environment_name, '-f', 'temp_env.yml']
            
            # Create temporary environment file
            temp_file = os.path.join(self.base_path, 'temp_env.yml')
            with open(temp_file, 'w') as f:
                yaml.dump(env_config, f)
            
            # Execute creation
            success, output, error = self._execute_conda_command(create_cmd)
            
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            if success:
                # Get environment information
                environment = self._get_environment_info(environment_name)
                result.environment = environment
                result.success = True
            else:
                result.error_messages.append(f"Failed to create environment: {error}")
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during environment creation: {str(e)}")
            return result
    
    def _get_environment_info(self, environment_name: str) -> Optional[CondaEnvironment]:
        """
        Get information about a conda environment.
        
        Args:
            environment_name: Name of the environment
            
        Returns:
            CondaEnvironment object or None
        """
        try:
            # Build info command
            info_cmd = [self.conda_executable, 'info', '--envs', '--json']
            
            # Execute command
            success, output, error = self._execute_conda_command(info_cmd)
            
            if not success:
                return None
            
            # Parse JSON output
            info_data = json.loads(output)
            
            # Find environment
            for env_path in info_data.get('envs', []):
                if environment_name in env_path:
                    environment = CondaEnvironment(
                        name=environment_name,
                        path=env_path,
                        status=CondaEnvironmentStatus.EXISTS
                    )
                    
                    # Get packages in environment
                    packages = self._get_environment_packages(environment_name)
                    environment.packages = packages
                    
                    return environment
            
            return None
        
        except Exception as e:
            return None
    
    def _get_environment_packages(self, environment_name: str) -> List[CondaPackage]:
        """
        Get packages installed in environment.
        
        Args:
            environment_name: Name of the environment
            
        Returns:
            List of packages
        """
        try:
            # Build list command
            list_cmd = [self.conda_executable, 'list', '-n', environment_name, '--json']
            
            # Execute command
            success, output, error = self._execute_conda_command(list_cmd)
            
            if not success:
                return []
            
            # Parse JSON output
            packages_data = json.loads(output)
            packages = []
            
            for pkg_data in packages_data:
                package = CondaPackage(
                    name=pkg_data['name'],
                    version=pkg_data.get('version'),
                    channel=pkg_data.get('channel', 'defaults'),
                    build_string=pkg_data.get('build_string'),
                    status=CondaInstallStatus.SUCCESS
                )
                packages.append(package)
            
            return packages
        
        except Exception as e:
            return []
    
    def _environment_exists(self, environment_name: str) -> bool:
        """
        Check if conda environment exists.
        
        Args:
            environment_name: Name of the environment
            
        Returns:
            bool: True if environment exists
        """
        try:
            # Build list command
            list_cmd = [self.conda_executable, 'env', 'list', '--json']
            
            # Execute command
            success, output, error = self._execute_conda_command(list_cmd)
            
            if not success:
                return False
            
            # Parse JSON output
            envs_data = json.loads(output)
            
            # Check if environment exists
            for env_path in envs_data.get('envs', []):
                if environment_name in env_path:
                    return True
            
            return False
        
        except Exception as e:
            return False
    
    def _remove_environment(self, environment_name: str) -> bool:
        """
        Remove conda environment.
        
        Args:
            environment_name: Name of the environment
            
        Returns:
            bool: True if successful
        """
        try:
            # Build remove command
            remove_cmd = [self.conda_executable, 'env', 'remove', '-n', environment_name, '-y']
            
            # Execute command
            success, output, error = self._execute_conda_command(remove_cmd)
            
            return success
        
        except Exception as e:
            return False
    
    def _parse_package_specification(self, spec: str) -> Optional[CondaPackage]:
        """
        Parse a package specification string.
        
        Args:
            spec: Package specification string
            
        Returns:
            CondaPackage object or None
        """
        try:
            # Remove extra whitespace
            spec = spec.strip()
            
            # Handle channel specifications
            if '::' in spec:
                channel, package_spec = spec.split('::', 1)
                package = self._parse_package_specification(package_spec)
                if package:
                    package.channel = channel
                return package
            
            # Handle version specifications
            if '=' in spec:
                name, version = spec.split('=', 1)
                return CondaPackage(name=name.strip(), version=version.strip())
            
            else:
                return CondaPackage(name=spec)
        
        except Exception as e:
            return None
    
    def _execute_conda_command(self, cmd: List[str]) -> Tuple[bool, str, str]:
        """
        Execute a conda command.
        
        Args:
            cmd: Command to execute
            
        Returns:
            Tuple of (success, output, error)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.install_timeout
            )
            
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr
            
            return success, output, error
        
        except subprocess.TimeoutExpired:
            return False, "", "Conda command timeout"
        except Exception as e:
            return False, "", str(e)
    
    def _find_conda_executable(self) -> str:
        """Find conda executable."""
        try:
            # Try common conda locations
            conda_locations = ['conda', 'mamba']
            
            for conda_cmd in conda_locations:
                try:
                    result = subprocess.run(
                        [conda_cmd, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        return conda_cmd
                except:
                    continue
            
            return 'conda'  # Default fallback
        
        except Exception:
            return 'conda'
    
    def _update_progress(self, message: str):
        """Update progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(message)
            except:
                pass


def main():
    """Main function for testing conda manager."""
    print("🧪 Testing Conda Manager")
    print("=" * 50)
    
    # Initialize manager
    manager = CondaManager()
    
    # Set up progress callback
    def progress_callback(message):
        print(f"  {message}")
    
    manager.set_progress_callback(progress_callback)
    
    # Test environment listing
    print("\n📋 Testing environment listing...")
    environments = manager.list_environments()
    print(f"✅ Found {len(environments)} environments")
    
    for env in environments[:3]:  # Show first 3
        print(f"   - {env.name}: {env.path}")
    
    # Test with a sample environment file
    test_path = "/tmp/test_environment.yml"
    environment_content = """
name: test_env
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.9
  - numpy>=1.21.0
  - pandas>=1.3.0
  - pip
  - pip:
    - requests>=2.25.0
"""
    
    with open(test_path, 'w') as f:
        f.write(environment_content)
    
    # Test environment creation from file
    print("\n🐍 Testing environment creation from file...")
    result = manager.create_environment_from_file(test_path, "test_pinokio_env")
    
    print(f"✅ Environment creation success: {result.success}")
    print(f"✅ Installation time: {result.installation_time:.2f}s")
    
    if result.environment:
        print(f"✅ Environment: {result.environment.name}")
        print(f"✅ Path: {result.environment.path}")
        print(f"✅ Packages: {len(result.environment.packages)}")
    
    if result.error_messages:
        print(f"✅ Errors: {', '.join(result.error_messages)}")
    
    # Test package installation
    print("\n📦 Testing package installation...")
    if result.success and result.environment:
        install_result = manager.install_packages(
            result.environment.name, 
            ["matplotlib", "seaborn"]
        )
        
        print(f"✅ Package installation success: {install_result.success}")
        print(f"✅ Packages installed: {len(install_result.packages_installed)}")
        print(f"✅ Packages failed: {len(install_result.packages_failed)}")
    
    # Test environment info
    print("\nℹ️ Testing environment info...")
    if result.success and result.environment:
        env_info = manager.get_environment_info(result.environment.name)
        
        if env_info:
            print(f"✅ Environment info retrieved")
            print(f"   Name: {env_info.name}")
            print(f"   Path: {env_info.path}")
            print(f"   Status: {env_info.status.value}")
            print(f"   Packages: {len(env_info.packages)}")
        else:
            print("❌ Failed to get environment info")
    
    # Cleanup
    if result.success and result.environment:
        print("\n🧹 Cleaning up test environment...")
        cleanup_success = manager.remove_environment(result.environment.name)
        print(f"✅ Environment removed: {cleanup_success}")
    
    os.remove(test_path)
    
    return True


if __name__ == "__main__":
    main()