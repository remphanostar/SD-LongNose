#!/usr/bin/env python3
"""
PinokioCloud System Manager

This module handles system-level dependency installation for Pinokio applications.
It provides comprehensive system package management including installation via
apt, yum, dnf, brew, pacman, and other system package managers.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import re
import subprocess
import time
import platform
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class SystemPackageManager(Enum):
    """Enumeration of system package managers."""
    APT = "apt"
    YUM = "yum"
    DNF = "dnf"
    BREW = "brew"
    PACMAN = "pacman"
    ZYPPER = "zypper"
    EMERGE = "emerge"
    PKG = "pkg"
    UNKNOWN = "unknown"


class SystemInstallStatus(Enum):
    """Enumeration of system installation statuses."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"


class SystemPackageType(Enum):
    """Enumeration of system package types."""
    LIBRARY = "library"
    DEVELOPMENT = "development"
    RUNTIME = "runtime"
    UTILITY = "utility"
    MULTIMEDIA = "multimedia"
    NETWORK = "network"
    SECURITY = "security"
    UNKNOWN = "unknown"


@dataclass
class SystemPackage:
    """Information about a system package."""
    name: str
    version: Optional[str] = None
    package_type: SystemPackageType = SystemPackageType.UNKNOWN
    package_manager: SystemPackageManager = SystemPackageManager.UNKNOWN
    dependencies: List[str] = field(default_factory=list)
    size_mb: float = 0.0
    install_time: float = 0.0
    status: SystemInstallStatus = SystemInstallStatus.IN_PROGRESS
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemInstallationResult:
    """Result of system installation operation."""
    success: bool
    packages_installed: List[SystemPackage] = field(default_factory=list)
    packages_failed: List[SystemPackage] = field(default_factory=list)
    total_packages: int = 0
    installation_time: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    package_manager: SystemPackageManager = SystemPackageManager.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)


class SystemManager:
    """
    Manages system-level dependency installation for Pinokio applications.
    
    Provides comprehensive system package management including:
    - Package manager detection and selection
    - Package installation via various package managers
    - Dependency resolution and conflict handling
    - Installation verification and testing
    - Progress tracking and error handling
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the system manager.
        
        Args:
            base_path: Base path for system operations
        """
        self.base_path = base_path
        self.package_manager = self._detect_package_manager()
        self.install_timeout = 600  # 10 minutes timeout for system packages
        self.progress_callback = None
        self.sudo_required = self._check_sudo_required()
        
        # Package manager configurations
        self.package_manager_configs = {
            SystemPackageManager.APT: {
                'update_cmd': ['apt', 'update'],
                'install_cmd': ['apt', 'install', '-y'],
                'remove_cmd': ['apt', 'remove', '-y'],
                'list_cmd': ['dpkg', '-l'],
                'search_cmd': ['apt', 'search'],
                'info_cmd': ['apt', 'show']
            },
            SystemPackageManager.YUM: {
                'update_cmd': ['yum', 'update', '-y'],
                'install_cmd': ['yum', 'install', '-y'],
                'remove_cmd': ['yum', 'remove', '-y'],
                'list_cmd': ['yum', 'list', 'installed'],
                'search_cmd': ['yum', 'search'],
                'info_cmd': ['yum', 'info']
            },
            SystemPackageManager.DNF: {
                'update_cmd': ['dnf', 'update', '-y'],
                'install_cmd': ['dnf', 'install', '-y'],
                'remove_cmd': ['dnf', 'remove', '-y'],
                'list_cmd': ['dnf', 'list', 'installed'],
                'search_cmd': ['dnf', 'search'],
                'info_cmd': ['dnf', 'info']
            },
            SystemPackageManager.BREW: {
                'update_cmd': ['brew', 'update'],
                'install_cmd': ['brew', 'install'],
                'remove_cmd': ['brew', 'uninstall'],
                'list_cmd': ['brew', 'list'],
                'search_cmd': ['brew', 'search'],
                'info_cmd': ['brew', 'info']
            },
            SystemPackageManager.PACMAN: {
                'update_cmd': ['pacman', '-Sy'],
                'install_cmd': ['pacman', '-S', '--noconfirm'],
                'remove_cmd': ['pacman', '-R', '--noconfirm'],
                'list_cmd': ['pacman', '-Q'],
                'search_cmd': ['pacman', '-Ss'],
                'info_cmd': ['pacman', '-Si']
            },
            SystemPackageManager.ZYPPER: {
                'update_cmd': ['zypper', 'refresh'],
                'install_cmd': ['zypper', 'install', '-y'],
                'remove_cmd': ['zypper', 'remove', '-y'],
                'list_cmd': ['zypper', 'packages', '--installed'],
                'search_cmd': ['zypper', 'search'],
                'info_cmd': ['zypper', 'info']
            }
        }
        
        # Package categories for better organization
        self.package_categories = {
            'development': ['build-essential', 'gcc', 'g++', 'make', 'cmake', 'git', 'curl', 'wget'],
            'multimedia': ['ffmpeg', 'imagemagick', 'gstreamer', 'vlc', 'mplayer'],
            'network': ['openssh-server', 'nginx', 'apache2', 'postgresql', 'mysql-server'],
            'security': ['openssl', 'libssl-dev', 'ca-certificates', 'gnupg'],
            'utilities': ['htop', 'tree', 'unzip', 'zip', 'tar', 'rsync', 'vim', 'nano'],
            'libraries': ['libc6-dev', 'libffi-dev', 'libssl-dev', 'libxml2-dev', 'libxslt1-dev']
        }
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def install_packages(self, packages: List[str], 
                        update_first: bool = True) -> SystemInstallationResult:
        """
        Install system packages.
        
        Args:
            packages: List of package names to install
            update_first: Whether to update package lists first
            
        Returns:
            SystemInstallationResult: Installation result
        """
        start_time = time.time()
        
        result = SystemInstallationResult(
            success=False,
            total_packages=len(packages),
            package_manager=self.package_manager
        )
        
        try:
            if not packages:
                result.success = True
                result.installation_time = time.time() - start_time
                return result
            
            if self.package_manager == SystemPackageManager.UNKNOWN:
                result.error_messages.append("No supported package manager found")
                return result
            
            self._update_progress(f"Installing {len(packages)} system packages using {self.package_manager.value}")
            
            # Update package lists if requested
            if update_first:
                self._update_progress("Updating package lists...")
                update_success = self._update_package_lists()
                if not update_success:
                    result.warnings.append("Failed to update package lists")
            
            # Install packages
            install_result = self._install_packages_batch(packages)
            
            result.packages_installed = install_result.packages_installed
            result.packages_failed = install_result.packages_failed
            result.success = len(install_result.packages_failed) == 0
            result.error_messages = install_result.error_messages
            result.warnings.extend(install_result.warnings)
            result.installation_time = time.time() - start_time
            
            self._update_progress(f"System installation complete: {len(result.packages_installed)}/{result.total_packages} packages installed")
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during system package installation: {str(e)}")
            result.installation_time = time.time() - start_time
            return result
    
    def install_package(self, package_name: str) -> SystemPackage:
        """
        Install a single system package.
        
        Args:
            package_name: Name of the package to install
            
        Returns:
            SystemPackage: Installation result
        """
        start_time = time.time()
        
        package = SystemPackage(
            name=package_name,
            package_type=self._categorize_package(package_name),
            package_manager=self.package_manager
        )
        
        try:
            self._update_progress(f"Installing system package: {package_name}")
            
            # Build install command
            install_cmd = self._build_install_command([package_name])
            
            # Execute installation
            success, output, error = self._execute_system_command(install_cmd)
            
            package.install_time = time.time() - start_time
            
            if success:
                package.status = SystemInstallStatus.SUCCESS
                self._update_progress(f"Successfully installed {package_name}")
            else:
                package.status = SystemInstallStatus.FAILED
                package.error_message = error
                self._update_progress(f"Failed to install {package_name}: {error}")
            
            return package
        
        except Exception as e:
            package.status = SystemInstallStatus.FAILED
            package.error_message = str(e)
            package.install_time = time.time() - start_time
            return package
    
    def install_development_tools(self) -> SystemInstallationResult:
        """
        Install common development tools.
        
        Returns:
            SystemInstallationResult: Installation result
        """
        dev_packages = self.package_categories.get('development', [])
        return self.install_packages(dev_packages)
    
    def install_multimedia_tools(self) -> SystemInstallationResult:
        """
        Install multimedia tools and libraries.
        
        Returns:
            SystemInstallationResult: Installation result
        """
        multimedia_packages = self.package_categories.get('multimedia', [])
        return self.install_packages(multimedia_packages)
    
    def install_network_tools(self) -> SystemInstallationResult:
        """
        Install network tools and services.
        
        Returns:
            SystemInstallationResult: Installation result
        """
        network_packages = self.package_categories.get('network', [])
        return self.install_packages(network_packages)
    
    def verify_installation(self, package_name: str) -> bool:
        """
        Verify that a system package is properly installed.
        
        Args:
            package_name: Name of the package to verify
            
        Returns:
            bool: True if package is properly installed
        """
        try:
            # Build verification command
            verify_cmd = self._build_verify_command(package_name)
            
            # Execute verification
            success, output, error = self._execute_system_command(verify_cmd)
            
            return success
        
        except Exception as e:
            return False
    
    def get_installed_packages(self) -> List[SystemPackage]:
        """
        Get list of installed system packages.
        
        Returns:
            List of installed packages
        """
        try:
            # Build list command
            list_cmd = self._build_list_command()
            
            # Execute command
            success, output, error = self._execute_system_command(list_cmd)
            
            if not success:
                return []
            
            # Parse output
            packages = self._parse_package_list(output)
            
            return packages
        
        except Exception as e:
            return []
    
    def search_packages(self, search_term: str) -> List[str]:
        """
        Search for available packages.
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of matching package names
        """
        try:
            # Build search command
            search_cmd = self._build_search_command(search_term)
            
            # Execute command
            success, output, error = self._execute_system_command(search_cmd)
            
            if not success:
                return []
            
            # Parse output
            packages = self._parse_search_results(output)
            
            return packages
        
        except Exception as e:
            return []
    
    def _detect_package_manager(self) -> SystemPackageManager:
        """
        Detect the system package manager.
        
        Returns:
            SystemPackageManager: Detected package manager
        """
        try:
            # Check for different package managers
            package_managers = [
                (SystemPackageManager.APT, ['apt', 'apt-get']),
                (SystemPackageManager.YUM, ['yum']),
                (SystemPackageManager.DNF, ['dnf']),
                (SystemPackageManager.BREW, ['brew']),
                (SystemPackageManager.PACMAN, ['pacman']),
                (SystemPackageManager.ZYPPER, ['zypper']),
                (SystemPackageManager.EMERGE, ['emerge']),
                (SystemPackageManager.PKG, ['pkg'])
            ]
            
            for pm_type, commands in package_managers:
                for cmd in commands:
                    try:
                        result = subprocess.run(
                            [cmd, '--version'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        if result.returncode == 0:
                            return pm_type
                    except:
                        continue
            
            return SystemPackageManager.UNKNOWN
        
        except Exception:
            return SystemPackageManager.UNKNOWN
    
    def _check_sudo_required(self) -> bool:
        """
        Check if sudo is required for package installation.
        
        Returns:
            bool: True if sudo is required
        """
        try:
            # Check if we're running as root
            if os.geteuid() == 0:
                return False
            
            # Check if sudo is available
            result = subprocess.run(
                ['sudo', '-n', 'true'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return result.returncode == 0
        
        except Exception:
            return False
    
    def _update_package_lists(self) -> bool:
        """
        Update package lists.
        
        Returns:
            bool: True if successful
        """
        try:
            config = self.package_manager_configs.get(self.package_manager, {})
            update_cmd = config.get('update_cmd', [])
            
            if not update_cmd:
                return False
            
            # Add sudo if required
            if self.sudo_required:
                update_cmd = ['sudo'] + update_cmd
            
            success, output, error = self._execute_system_command(update_cmd)
            
            return success
        
        except Exception as e:
            return False
    
    def _install_packages_batch(self, packages: List[str]) -> SystemInstallationResult:
        """
        Install packages in batch.
        
        Args:
            packages: List of packages to install
            
        Returns:
            SystemInstallationResult: Installation result
        """
        result = SystemInstallationResult(
            success=False,
            total_packages=len(packages),
            package_manager=self.package_manager
        )
        
        try:
            # Build install command
            install_cmd = self._build_install_command(packages)
            
            # Execute installation
            success, output, error = self._execute_system_command(install_cmd)
            
            if success:
                # Parse installed packages
                for package_name in packages:
                    package = SystemPackage(
                        name=package_name,
                        package_type=self._categorize_package(package_name),
                        package_manager=self.package_manager,
                        status=SystemInstallStatus.SUCCESS
                    )
                    result.packages_installed.append(package)
                
                result.success = True
            else:
                # Handle failed installation
                for package_name in packages:
                    package = SystemPackage(
                        name=package_name,
                        package_type=self._categorize_package(package_name),
                        package_manager=self.package_manager,
                        status=SystemInstallStatus.FAILED,
                        error_message=error
                    )
                    result.packages_failed.append(package)
                
                result.error_messages.append(f"Failed to install packages: {error}")
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during batch installation: {str(e)}")
            return result
    
    def _build_install_command(self, packages: List[str]) -> List[str]:
        """
        Build package installation command.
        
        Args:
            packages: List of packages to install
            
        Returns:
            List of command arguments
        """
        config = self.package_manager_configs.get(self.package_manager, {})
        install_cmd = config.get('install_cmd', [])
        
        if not install_cmd:
            return []
        
        # Add sudo if required
        if self.sudo_required:
            install_cmd = ['sudo'] + install_cmd
        
        # Add packages
        install_cmd.extend(packages)
        
        return install_cmd
    
    def _build_verify_command(self, package_name: str) -> List[str]:
        """
        Build package verification command.
        
        Args:
            package_name: Name of the package to verify
            
        Returns:
            List of command arguments
        """
        config = self.package_manager_configs.get(self.package_manager, {})
        
        if self.package_manager == SystemPackageManager.APT:
            return ['dpkg', '-l', package_name]
        elif self.package_manager in [SystemPackageManager.YUM, SystemPackageManager.DNF]:
            return ['rpm', '-q', package_name]
        elif self.package_manager == SystemPackageManager.BREW:
            return ['brew', 'list', package_name]
        elif self.package_manager == SystemPackageManager.PACMAN:
            return ['pacman', '-Q', package_name]
        elif self.package_manager == SystemPackageManager.ZYPPER:
            return ['zypper', 'search', '-i', package_name]
        else:
            return []
    
    def _build_list_command(self) -> List[str]:
        """
        Build package list command.
        
        Returns:
            List of command arguments
        """
        config = self.package_manager_configs.get(self.package_manager, {})
        list_cmd = config.get('list_cmd', [])
        
        if not list_cmd:
            return []
        
        # Add sudo if required
        if self.sudo_required:
            list_cmd = ['sudo'] + list_cmd
        
        return list_cmd
    
    def _build_search_command(self, search_term: str) -> List[str]:
        """
        Build package search command.
        
        Args:
            search_term: Term to search for
            
        Returns:
            List of command arguments
        """
        config = self.package_manager_configs.get(self.package_manager, {})
        search_cmd = config.get('search_cmd', [])
        
        if not search_cmd:
            return []
        
        # Add search term
        search_cmd.append(search_term)
        
        return search_cmd
    
    def _parse_package_list(self, output: str) -> List[SystemPackage]:
        """
        Parse package list output.
        
        Args:
            output: Command output to parse
            
        Returns:
            List of packages
        """
        packages = []
        
        try:
            lines = output.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if not line or line.startswith('Desired') or line.startswith('ii'):
                    continue
                
                # Parse based on package manager
                if self.package_manager == SystemPackageManager.APT:
                    # dpkg -l format: ii package_name version description
                    parts = line.split()
                    if len(parts) >= 3:
                        package_name = parts[1]
                        version = parts[2]
                        
                        package = SystemPackage(
                            name=package_name,
                            version=version,
                            package_type=self._categorize_package(package_name),
                            package_manager=self.package_manager,
                            status=SystemInstallStatus.SUCCESS
                        )
                        packages.append(package)
                
                elif self.package_manager in [SystemPackageManager.YUM, SystemPackageManager.DNF]:
                    # yum/dnf list format: package_name.version arch
                    parts = line.split()
                    if len(parts) >= 2:
                        package_name = parts[0].split('.')[0]
                        version = parts[1]
                        
                        package = SystemPackage(
                            name=package_name,
                            version=version,
                            package_type=self._categorize_package(package_name),
                            package_manager=self.package_manager,
                            status=SystemInstallStatus.SUCCESS
                        )
                        packages.append(package)
                
                elif self.package_manager == SystemPackageManager.BREW:
                    # brew list format: package_name
                    if line and not line.startswith('==>'):
                        package = SystemPackage(
                            name=line,
                            package_type=self._categorize_package(line),
                            package_manager=self.package_manager,
                            status=SystemInstallStatus.SUCCESS
                        )
                        packages.append(package)
                
                elif self.package_manager == SystemPackageManager.PACMAN:
                    # pacman -Q format: package_name version
                    parts = line.split()
                    if len(parts) >= 2:
                        package_name = parts[0]
                        version = parts[1]
                        
                        package = SystemPackage(
                            name=package_name,
                            version=version,
                            package_type=self._categorize_package(package_name),
                            package_manager=self.package_manager,
                            status=SystemInstallStatus.SUCCESS
                        )
                        packages.append(package)
        
        except Exception as e:
            pass
        
        return packages
    
    def _parse_search_results(self, output: str) -> List[str]:
        """
        Parse search results output.
        
        Args:
            output: Command output to parse
            
        Returns:
            List of package names
        """
        packages = []
        
        try:
            lines = output.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if not line or line.startswith('==>') or line.startswith('Loading'):
                    continue
                
                # Extract package name (first part before space)
                package_name = line.split()[0]
                if package_name:
                    packages.append(package_name)
        
        except Exception as e:
            pass
        
        return packages
    
    def _execute_system_command(self, cmd: List[str]) -> Tuple[bool, str, str]:
        """
        Execute a system command.
        
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
            return False, "", "System command timeout"
        except Exception as e:
            return False, "", str(e)
    
    def _categorize_package(self, package_name: str) -> SystemPackageType:
        """
        Categorize a package by its name.
        
        Args:
            package_name: Name of the package
            
        Returns:
            SystemPackageType: Category of the package
        """
        package_lower = package_name.lower()
        
        # Check against categories
        for category, packages in self.package_categories.items():
            for pkg in packages:
                if pkg.lower() in package_lower or package_lower in pkg.lower():
                    if category == 'development':
                        return SystemPackageType.DEVELOPMENT
                    elif category == 'multimedia':
                        return SystemPackageType.MULTIMEDIA
                    elif category == 'network':
                        return SystemPackageType.NETWORK
                    elif category == 'security':
                        return SystemPackageType.SECURITY
                    elif category == 'utilities':
                        return SystemPackageType.UTILITY
                    elif category == 'libraries':
                        return SystemPackageType.LIBRARY
        
        # Check for common patterns
        if any(dev_indicator in package_lower for dev_indicator in ['dev', 'devel', 'build']):
            return SystemPackageType.DEVELOPMENT
        
        if any(lib_indicator in package_lower for lib_indicator in ['lib', 'library']):
            return SystemPackageType.LIBRARY
        
        if any(util_indicator in package_lower for util_indicator in ['util', 'tool', 'bin']):
            return SystemPackageType.UTILITY
        
        return SystemPackageType.RUNTIME
    
    def _update_progress(self, message: str):
        """Update progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(message)
            except:
                pass


def main():
    """Main function for testing system manager."""
    print("🧪 Testing System Manager")
    print("=" * 50)
    
    # Initialize manager
    manager = SystemManager()
    
    # Set up progress callback
    def progress_callback(message):
        print(f"  {message}")
    
    manager.set_progress_callback(progress_callback)
    
    # Test package manager detection
    print(f"\n🔍 Detected package manager: {manager.package_manager.value}")
    print(f"🔍 Sudo required: {manager.sudo_required}")
    
    # Test development tools installation
    print("\n🛠️ Testing development tools installation...")
    dev_result = manager.install_development_tools()
    
    print(f"✅ Development tools installation success: {dev_result.success}")
    print(f"✅ Total packages: {dev_result.total_packages}")
    print(f"✅ Packages installed: {len(dev_result.packages_installed)}")
    print(f"✅ Packages failed: {len(dev_result.packages_failed)}")
    print(f"✅ Installation time: {dev_result.installation_time:.2f}s")
    
    if dev_result.packages_installed:
        print("   Installed packages:")
        for pkg in dev_result.packages_installed:
            print(f"     - {pkg.name} ({pkg.version or 'unknown'}) [{pkg.package_type.value}]")
    
    if dev_result.packages_failed:
        print("   Failed packages:")
        for pkg in dev_result.packages_failed:
            print(f"     - {pkg.name}: {pkg.error_message}")
    
    # Test single package installation
    print("\n📦 Testing single package installation...")
    package = manager.install_package("curl")
    
    print(f"✅ Package: {package.name}")
    print(f"✅ Status: {package.status.value}")
    print(f"✅ Install time: {package.install_time:.2f}s")
    
    if package.error_message:
        print(f"✅ Error: {package.error_message}")
    
    # Test package verification
    print("\n✅ Testing package verification...")
    is_installed = manager.verify_installation("curl")
    print(f"✅ Curl installed: {is_installed}")
    
    # Test package search
    print("\n🔍 Testing package search...")
    search_results = manager.search_packages("python")
    print(f"✅ Found {len(search_results)} packages matching 'python'")
    
    if search_results:
        print("   Sample packages:")
        for pkg in search_results[:5]:
            print(f"     - {pkg}")
    
    # Test installed packages list
    print("\n📋 Testing installed packages list...")
    installed_packages = manager.get_installed_packages()
    print(f"✅ Total installed packages: {len(installed_packages)}")
    
    if installed_packages:
        print("   Sample packages:")
        for pkg in installed_packages[:5]:
            print(f"     - {pkg.name} ({pkg.version or 'unknown'}) [{pkg.package_type.value}]")
    
    return True


if __name__ == "__main__":
    main()