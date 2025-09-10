#!/usr/bin/env python3
"""
PinokioCloud Pip Manager

This module handles pip-based dependency installation for Pinokio applications.
It provides comprehensive pip package management including installation, upgrading,
dependency resolution, and verification of pip packages.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import re
import subprocess
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class PipInstallStatus(Enum):
    """Enumeration of pip installation statuses."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"


class PipPackageType(Enum):
    """Enumeration of pip package types."""
    REGULAR = "regular"
    DEV = "dev"
    OPTIONAL = "optional"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class PipPackage:
    """Information about a pip package."""
    name: str
    version: Optional[str] = None
    package_type: PipPackageType = PipPackageType.REGULAR
    source: str = "pypi"
    dependencies: List[str] = field(default_factory=list)
    size_mb: float = 0.0
    install_time: float = 0.0
    status: PipInstallStatus = PipInstallStatus.IN_PROGRESS
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipInstallationResult:
    """Result of pip installation operation."""
    success: bool
    packages_installed: List[PipPackage] = field(default_factory=list)
    packages_failed: List[PipPackage] = field(default_factory=list)
    total_packages: int = 0
    installation_time: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PipManager:
    """
    Manages pip-based dependency installation for Pinokio applications.
    
    Provides comprehensive pip package management including:
    - Package installation from requirements files
    - Individual package installation
    - Dependency resolution and conflict handling
    - Installation verification and testing
    - Progress tracking and error handling
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the pip manager.
        
        Args:
            base_path: Base path for pip operations
        """
        self.base_path = base_path
        self.pip_executable = self._find_pip_executable()
        self.python_executable = self._find_python_executable()
        self.install_timeout = 300  # 5 minutes timeout
        self.progress_callback = None
        
        # Package categories for better organization
        self.package_categories = {
            'ml_ai': ['torch', 'tensorflow', 'keras', 'scikit-learn', 'numpy', 'pandas', 'opencv-python'],
            'web': ['flask', 'fastapi', 'django', 'streamlit', 'gradio', 'dash', 'tornado'],
            'data': ['pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'plotly', 'bokeh'],
            'vision': ['opencv-python', 'pillow', 'imageio', 'scikit-image', 'albumentations', 'torchvision'],
            'audio': ['librosa', 'soundfile', 'pyaudio', 'pydub', 'webrtcvad', 'whisper', 'torchaudio'],
            'text': ['transformers', 'tokenizers', 'nltk', 'spacy', 'textblob', 'gensim', 'langchain'],
            'utility': ['requests', 'urllib3', 'httpx', 'aiohttp', 'click', 'typer', 'rich', 'tqdm']
        }
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def install_from_requirements(self, requirements_path: str, 
                                 environment_path: Optional[str] = None,
                                 upgrade: bool = False,
                                 force_reinstall: bool = False) -> PipInstallationResult:
        """
        Install packages from a requirements file.
        
        Args:
            requirements_path: Path to requirements file
            environment_path: Path to virtual environment (optional)
            upgrade: Whether to upgrade existing packages
            force_reinstall: Whether to force reinstall packages
            
        Returns:
            PipInstallationResult: Installation result
        """
        start_time = time.time()
        
        result = PipInstallationResult(
            success=False,
            total_packages=0
        )
        
        try:
            if not os.path.exists(requirements_path):
                result.error_messages.append(f"Requirements file not found: {requirements_path}")
                return result
            
            # Parse requirements file
            packages = self._parse_requirements_file(requirements_path)
            result.total_packages = len(packages)
            
            if not packages:
                result.success = True
                result.installation_time = time.time() - start_time
                return result
            
            self._update_progress(f"Installing {len(packages)} packages from {requirements_path}")
            
            # Install packages
            for i, package in enumerate(packages):
                self._update_progress(f"Installing package {i+1}/{len(packages)}: {package.name}")
                
                install_result = self._install_single_package(
                    package, environment_path, upgrade, force_reinstall
                )
                
                if install_result.status == PipInstallStatus.SUCCESS:
                    result.packages_installed.append(install_result)
                else:
                    result.packages_failed.append(install_result)
            
            # Determine overall success
            result.success = len(result.packages_failed) == 0
            result.installation_time = time.time() - start_time
            
            self._update_progress(f"Installation complete: {len(result.packages_installed)}/{result.total_packages} packages installed")
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during requirements installation: {str(e)}")
            result.installation_time = time.time() - start_time
            return result
    
    def install_package(self, package_name: str, 
                       version: Optional[str] = None,
                       environment_path: Optional[str] = None,
                       upgrade: bool = False) -> PipPackage:
        """
        Install a single package.
        
        Args:
            package_name: Name of the package to install
            version: Specific version to install (optional)
            environment_path: Path to virtual environment (optional)
            upgrade: Whether to upgrade if already installed
            
        Returns:
            PipPackage: Installation result
        """
        start_time = time.time()
        
        package = PipPackage(
            name=package_name,
            version=version,
            package_type=self._categorize_package(package_name)
        )
        
        try:
            self._update_progress(f"Installing package: {package_name}")
            
            # Build install command
            install_cmd = self._build_install_command(package, environment_path, upgrade)
            
            # Execute installation
            success, output, error = self._execute_pip_command(install_cmd)
            
            package.install_time = time.time() - start_time
            
            if success:
                package.status = PipInstallStatus.SUCCESS
                self._update_progress(f"Successfully installed {package_name}")
            else:
                package.status = PipInstallStatus.FAILED
                package.error_message = error
                self._update_progress(f"Failed to install {package_name}: {error}")
            
            return package
        
        except Exception as e:
            package.status = PipInstallStatus.FAILED
            package.error_message = str(e)
            package.install_time = time.time() - start_time
            return package
    
    def install_packages_batch(self, packages: List[str], 
                              environment_path: Optional[str] = None,
                              upgrade: bool = False) -> PipInstallationResult:
        """
        Install multiple packages in batch.
        
        Args:
            packages: List of package names to install
            environment_path: Path to virtual environment (optional)
            upgrade: Whether to upgrade existing packages
            
        Returns:
            PipInstallationResult: Installation result
        """
        start_time = time.time()
        
        result = PipInstallationResult(
            success=False,
            total_packages=len(packages)
        )
        
        try:
            if not packages:
                result.success = True
                result.installation_time = time.time() - start_time
                return result
            
            self._update_progress(f"Installing {len(packages)} packages in batch")
            
            # Install packages one by one
            for i, package_name in enumerate(packages):
                self._update_progress(f"Installing package {i+1}/{len(packages)}: {package_name}")
                
                package = self.install_package(package_name, environment_path=environment_path, upgrade=upgrade)
                
                if package.status == PipInstallStatus.SUCCESS:
                    result.packages_installed.append(package)
                else:
                    result.packages_failed.append(package)
            
            # Determine overall success
            result.success = len(result.packages_failed) == 0
            result.installation_time = time.time() - start_time
            
            self._update_progress(f"Batch installation complete: {len(result.packages_installed)}/{result.total_packages} packages installed")
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during batch installation: {str(e)}")
            result.installation_time = time.time() - start_time
            return result
    
    def verify_installation(self, package_name: str, 
                           environment_path: Optional[str] = None) -> bool:
        """
        Verify that a package is properly installed.
        
        Args:
            package_name: Name of the package to verify
            environment_path: Path to virtual environment (optional)
            
        Returns:
            bool: True if package is properly installed
        """
        try:
            # Try to import the package
            import_cmd = [self.python_executable, '-c', f'import {package_name}; print("OK")']
            
            if environment_path:
                # Activate virtual environment
                if os.name == 'nt':  # Windows
                    python_path = os.path.join(environment_path, 'Scripts', 'python.exe')
                else:  # Unix-like
                    python_path = os.path.join(environment_path, 'bin', 'python')
                
                if os.path.exists(python_path):
                    import_cmd[0] = python_path
            
            success, output, error = self._execute_command(import_cmd)
            
            if success and "OK" in output:
                return True
            
            # Try alternative import methods
            alt_import_cmd = [self.python_executable, '-c', f'import pkg_resources; pkg_resources.get_distribution("{package_name}"); print("OK")']
            
            if environment_path and os.path.exists(python_path):
                alt_import_cmd[0] = python_path
            
            success, output, error = self._execute_command(alt_import_cmd)
            
            return success and "OK" in output
        
        except Exception as e:
            return False
    
    def get_installed_packages(self, environment_path: Optional[str] = None) -> List[PipPackage]:
        """
        Get list of installed packages.
        
        Args:
            environment_path: Path to virtual environment (optional)
            
        Returns:
            List of installed packages
        """
        try:
            # Build pip list command
            list_cmd = [self.pip_executable, 'list', '--format=json']
            
            if environment_path:
                # Use environment's pip
                if os.name == 'nt':  # Windows
                    pip_path = os.path.join(environment_path, 'Scripts', 'pip.exe')
                else:  # Unix-like
                    pip_path = os.path.join(environment_path, 'bin', 'pip')
                
                if os.path.exists(pip_path):
                    list_cmd[0] = pip_path
            
            success, output, error = self._execute_command(list_cmd)
            
            if not success:
                return []
            
            # Parse JSON output
            packages_data = json.loads(output)
            packages = []
            
            for pkg_data in packages_data:
                package = PipPackage(
                    name=pkg_data['name'],
                    version=pkg_data.get('version'),
                    package_type=self._categorize_package(pkg_data['name']),
                    status=PipInstallStatus.SUCCESS
                )
                packages.append(package)
            
            return packages
        
        except Exception as e:
            return []
    
    def _parse_requirements_file(self, requirements_path: str) -> List[PipPackage]:
        """
        Parse a requirements file and extract packages.
        
        Args:
            requirements_path: Path to requirements file
            
        Returns:
            List of packages to install
        """
        packages = []
        
        try:
            with open(requirements_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for line in content.split('\n'):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Skip -r, -e, and other pip options for now
                if line.startswith('-'):
                    continue
                
                # Parse package specification
                package = self._parse_package_specification(line)
                if package:
                    packages.append(package)
        
        except Exception as e:
            pass
        
        return packages
    
    def _parse_package_specification(self, spec: str) -> Optional[PipPackage]:
        """
        Parse a package specification string.
        
        Args:
            spec: Package specification string
            
        Returns:
            PipPackage object or None
        """
        try:
            # Remove extra whitespace
            spec = spec.strip()
            
            # Handle different specification formats
            if '==' in spec:
                name, version = spec.split('==', 1)
                return PipPackage(name=name.strip(), version=version.strip())
            
            elif '>=' in spec:
                name, version = spec.split('>=', 1)
                return PipPackage(name=name.strip(), version=f">={version.strip()}")
            
            elif '<=' in spec:
                name, version = spec.split('<=', 1)
                return PipPackage(name=name.strip(), version=f"<={version.strip()}")
            
            elif '>' in spec:
                name, version = spec.split('>', 1)
                return PipPackage(name=name.strip(), version=f">{version.strip()}")
            
            elif '<' in spec:
                name, version = spec.split('<', 1)
                return PipPackage(name=name.strip(), version=f"<{version.strip()}")
            
            elif '~=' in spec:
                name, version = spec.split('~=', 1)
                return PipPackage(name=name.strip(), version=f"~={version.strip()}")
            
            elif '!=' in spec:
                name, version = spec.split('!=', 1)
                return PipPackage(name=name.strip(), version=f"!={version.strip()}")
            
            else:
                # No version specification
                return PipPackage(name=spec)
        
        except Exception as e:
            return None
    
    def _build_install_command(self, package: PipPackage, 
                              environment_path: Optional[str] = None,
                              upgrade: bool = False) -> List[str]:
        """
        Build pip install command.
        
        Args:
            package: Package to install
            environment_path: Path to virtual environment (optional)
            upgrade: Whether to upgrade
            
        Returns:
            List of command arguments
        """
        cmd = [self.pip_executable, 'install']
        
        # Add upgrade flag
        if upgrade:
            cmd.append('--upgrade')
        
        # Add package specification
        if package.version:
            cmd.append(f"{package.name}{package.version}")
        else:
            cmd.append(package.name)
        
        # Add timeout
        cmd.extend(['--timeout', str(self.install_timeout)])
        
        # Add no-cache-dir for faster installation
        cmd.append('--no-cache-dir')
        
        return cmd
    
    def _install_single_package(self, package: PipPackage, 
                               environment_path: Optional[str] = None,
                               upgrade: bool = False,
                               force_reinstall: bool = False) -> PipPackage:
        """
        Install a single package.
        
        Args:
            package: Package to install
            environment_path: Path to virtual environment (optional)
            upgrade: Whether to upgrade
            force_reinstall: Whether to force reinstall
            
        Returns:
            Updated package with installation result
        """
        start_time = time.time()
        
        try:
            # Build install command
            install_cmd = self._build_install_command(package, environment_path, upgrade)
            
            if force_reinstall:
                install_cmd.append('--force-reinstall')
            
            # Execute installation
            success, output, error = self._execute_pip_command(install_cmd)
            
            package.install_time = time.time() - start_time
            
            if success:
                package.status = PipInstallStatus.SUCCESS
            else:
                package.status = PipInstallStatus.FAILED
                package.error_message = error
            
            return package
        
        except Exception as e:
            package.status = PipInstallStatus.FAILED
            package.error_message = str(e)
            package.install_time = time.time() - start_time
            return package
    
    def _execute_pip_command(self, cmd: List[str]) -> Tuple[bool, str, str]:
        """
        Execute a pip command.
        
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
            return False, "", "Installation timeout"
        except Exception as e:
            return False, "", str(e)
    
    def _execute_command(self, cmd: List[str]) -> Tuple[bool, str, str]:
        """
        Execute a general command.
        
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
                timeout=30
            )
            
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr
            
            return success, output, error
        
        except subprocess.TimeoutExpired:
            return False, "", "Command timeout"
        except Exception as e:
            return False, "", str(e)
    
    def _find_pip_executable(self) -> str:
        """Find pip executable."""
        try:
            # Try common pip locations
            pip_locations = ['pip', 'pip3', 'python -m pip', 'python3 -m pip']
            
            for pip_cmd in pip_locations:
                try:
                    result = subprocess.run(
                        pip_cmd.split() + ['--version'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        return pip_cmd.split()[0]
                except:
                    continue
            
            return 'pip'  # Default fallback
        
        except Exception:
            return 'pip'
    
    def _find_python_executable(self) -> str:
        """Find python executable."""
        try:
            # Try common python locations
            python_locations = ['python', 'python3']
            
            for python_cmd in python_locations:
                try:
                    result = subprocess.run(
                        [python_cmd, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        return python_cmd
                except:
                    continue
            
            return 'python'  # Default fallback
        
        except Exception:
            return 'python'
    
    def _categorize_package(self, package_name: str) -> PipPackageType:
        """
        Categorize a package by its name.
        
        Args:
            package_name: Name of the package
            
        Returns:
            PipPackageType: Category of the package
        """
        package_lower = package_name.lower()
        
        # Check against categories
        for category, packages in self.package_categories.items():
            for pkg in packages:
                if pkg.lower() in package_lower or package_lower in pkg.lower():
                    return PipPackageType.REGULAR
        
        # Check for dev packages
        if any(dev_indicator in package_lower for dev_indicator in ['dev', 'test', 'debug']):
            return PipPackageType.DEV
        
        # Check for system packages
        if any(sys_indicator in package_lower for sys_indicator in ['system', 'os', 'platform']):
            return PipPackageType.SYSTEM
        
        return PipPackageType.REGULAR
    
    def _update_progress(self, message: str):
        """Update progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(message)
            except:
                pass


def main():
    """Main function for testing pip manager."""
    print("🧪 Testing Pip Manager")
    print("=" * 50)
    
    # Initialize manager
    manager = PipManager()
    
    # Set up progress callback
    def progress_callback(message):
        print(f"  {message}")
    
    manager.set_progress_callback(progress_callback)
    
    # Test with a sample requirements file
    test_path = "/tmp/test_requirements.txt"
    requirements_content = """
# Test requirements file
requests>=2.25.0
numpy>=1.21.0
# This is a comment
pandas>=1.3.0
"""
    
    with open(test_path, 'w') as f:
        f.write(requirements_content)
    
    # Test installation from requirements
    print("\n📦 Testing installation from requirements file...")
    result = manager.install_from_requirements(test_path)
    
    print(f"✅ Installation success: {result.success}")
    print(f"✅ Total packages: {result.total_packages}")
    print(f"✅ Packages installed: {len(result.packages_installed)}")
    print(f"✅ Packages failed: {len(result.packages_failed)}")
    print(f"✅ Installation time: {result.installation_time:.2f}s")
    
    if result.packages_installed:
        print("   Installed packages:")
        for pkg in result.packages_installed:
            print(f"     - {pkg.name} ({pkg.version or 'latest'})")
    
    if result.packages_failed:
        print("   Failed packages:")
        for pkg in result.packages_failed:
            print(f"     - {pkg.name}: {pkg.error_message}")
    
    # Test single package installation
    print("\n📦 Testing single package installation...")
    package = manager.install_package("requests")
    
    print(f"✅ Package: {package.name}")
    print(f"✅ Status: {package.status.value}")
    print(f"✅ Install time: {package.install_time:.2f}s")
    
    if package.error_message:
        print(f"✅ Error: {package.error_message}")
    
    # Test package verification
    print("\n✅ Testing package verification...")
    is_installed = manager.verify_installation("requests")
    print(f"✅ Requests installed: {is_installed}")
    
    # Test installed packages list
    print("\n📋 Testing installed packages list...")
    installed_packages = manager.get_installed_packages()
    print(f"✅ Total installed packages: {len(installed_packages)}")
    
    if installed_packages:
        print("   Sample packages:")
        for pkg in installed_packages[:5]:
            print(f"     - {pkg.name} ({pkg.version or 'unknown'})")
    
    # Cleanup
    os.remove(test_path)
    
    return True


if __name__ == "__main__":
    main()