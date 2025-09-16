#!/usr/bin/env python3
"""
PinokioCloud NPM Manager

This module handles npm-based dependency installation for Pinokio applications.
It provides comprehensive Node.js package management including package installation,
dependency resolution, script execution, and verification of npm packages.

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


class NpmInstallStatus(Enum):
    """Enumeration of npm installation statuses."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"


class NpmPackageType(Enum):
    """Enumeration of npm package types."""
    REGULAR = "regular"
    DEV = "dev"
    PEER = "peer"
    OPTIONAL = "optional"
    BUNDLED = "bundled"
    UNKNOWN = "unknown"


@dataclass
class NpmPackage:
    """Information about an npm package."""
    name: str
    version: Optional[str] = None
    package_type: NpmPackageType = NpmPackageType.REGULAR
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)
    peer_dependencies: List[str] = field(default_factory=list)
    size_mb: float = 0.0
    install_time: float = 0.0
    status: NpmInstallStatus = NpmInstallStatus.IN_PROGRESS
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NpmInstallationResult:
    """Result of npm installation operation."""
    success: bool
    packages_installed: List[NpmPackage] = field(default_factory=list)
    packages_failed: List[NpmPackage] = field(default_factory=list)
    total_packages: int = 0
    installation_time: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    scripts: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class NpmManager:
    """
    Manages npm-based dependency installation for Pinokio applications.
    
    Provides comprehensive npm package management including:
    - Package installation from package.json
    - Individual package installation
    - Dependency resolution and conflict handling
    - Script execution and management
    - Installation verification and testing
    - Progress tracking and error handling
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the npm manager.
        
        Args:
            base_path: Base path for npm operations
        """
        self.base_path = base_path
        self.npm_executable = self._find_npm_executable()
        self.node_executable = self._find_node_executable()
        self.install_timeout = 300  # 5 minutes timeout
        self.progress_callback = None
        
        # Package categories for better organization
        self.package_categories = {
            'web_frameworks': ['express', 'koa', 'fastify', 'hapi', 'sails', 'meteor'],
            'build_tools': ['webpack', 'rollup', 'vite', 'parcel', 'esbuild', 'babel'],
            'testing': ['jest', 'mocha', 'chai', 'cypress', 'playwright', 'vitest'],
            'utilities': ['lodash', 'moment', 'axios', 'request', 'cheerio', 'fs-extra'],
            'ui_frameworks': ['react', 'vue', 'angular', 'svelte', 'preact', 'lit'],
            'backend': ['mongoose', 'sequelize', 'prisma', 'typeorm', 'knex', 'bookshelf'],
            'dev_tools': ['nodemon', 'concurrently', 'cross-env', 'dotenv', 'eslint', 'prettier']
        }
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def install_from_package_json(self, package_json_path: str, 
                                 install_dev: bool = True,
                                 install_peer: bool = True) -> NpmInstallationResult:
        """
        Install packages from package.json file.
        
        Args:
            package_json_path: Path to package.json file
            install_dev: Whether to install dev dependencies
            install_peer: Whether to install peer dependencies
            
        Returns:
            NpmInstallationResult: Installation result
        """
        start_time = time.time()
        
        result = NpmInstallationResult(
            success=False
        )
        
        try:
            if not os.path.exists(package_json_path):
                result.error_messages.append(f"package.json not found: {package_json_path}")
                return result
            
            # Parse package.json
            package_config = self._parse_package_json(package_json_path)
            
            if not package_config:
                result.error_messages.append("Failed to parse package.json")
                return result
            
            # Extract package information
            dependencies = package_config.get('dependencies', {})
            dev_dependencies = package_config.get('devDependencies', {})
            peer_dependencies = package_config.get('peerDependencies', {})
            scripts = package_config.get('scripts', {})
            
            result.scripts = scripts
            result.total_packages = len(dependencies) + (len(dev_dependencies) if install_dev else 0)
            
            if not result.total_packages:
                result.success = True
                result.installation_time = time.time() - start_time
                return result
            
            self._update_progress(f"Installing {result.total_packages} packages from package.json")
            
            # Change to package directory
            package_dir = os.path.dirname(package_json_path)
            original_cwd = os.getcwd()
            os.chdir(package_dir)
            
            try:
                # Install dependencies
                install_result = self._install_packages_from_config(
                    dependencies, dev_dependencies, peer_dependencies,
                    install_dev, install_peer
                )
                
                result.packages_installed = install_result.packages_installed
                result.packages_failed = install_result.packages_failed
                result.success = len(install_result.packages_failed) == 0
                result.warnings = install_result.warnings
                
            finally:
                # Restore original directory
                os.chdir(original_cwd)
            
            result.installation_time = time.time() - start_time
            
            self._update_progress(f"Installation complete: {len(result.packages_installed)}/{result.total_packages} packages installed")
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during package.json installation: {str(e)}")
            result.installation_time = time.time() - start_time
            return result
    
    def install_package(self, package_name: str, 
                       version: Optional[str] = None,
                       package_type: NpmPackageType = NpmPackageType.REGULAR,
                       global_install: bool = False) -> NpmPackage:
        """
        Install a single npm package.
        
        Args:
            package_name: Name of the package to install
            version: Specific version to install (optional)
            package_type: Type of package (regular, dev, peer)
            global_install: Whether to install globally
            
        Returns:
            NpmPackage: Installation result
        """
        start_time = time.time()
        
        package = NpmPackage(
            name=package_name,
            version=version,
            package_type=package_type
        )
        
        try:
            self._update_progress(f"Installing package: {package_name}")
            
            # Build install command
            install_cmd = self._build_install_command(package, global_install)
            
            # Execute installation
            success, output, error = self._execute_npm_command(install_cmd)
            
            package.install_time = time.time() - start_time
            
            if success:
                package.status = NpmInstallStatus.SUCCESS
                self._update_progress(f"Successfully installed {package_name}")
            else:
                package.status = NpmInstallStatus.FAILED
                package.error_message = error
                self._update_progress(f"Failed to install {package_name}: {error}")
            
            return package
        
        except Exception as e:
            package.status = NpmInstallStatus.FAILED
            package.error_message = str(e)
            package.install_time = time.time() - start_time
            return package
    
    def install_packages_batch(self, packages: List[str], 
                              package_type: NpmPackageType = NpmPackageType.REGULAR,
                              global_install: bool = False) -> NpmInstallationResult:
        """
        Install multiple packages in batch.
        
        Args:
            packages: List of package names to install
            package_type: Type of packages (regular, dev, peer)
            global_install: Whether to install globally
            
        Returns:
            NpmInstallationResult: Installation result
        """
        start_time = time.time()
        
        result = NpmInstallationResult(
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
                
                package = self.install_package(package_name, package_type=package_type, global_install=global_install)
                
                if package.status == NpmInstallStatus.SUCCESS:
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
    
    def run_script(self, script_name: str, 
                   package_json_path: str,
                   args: Optional[List[str]] = None) -> Tuple[bool, str, str]:
        """
        Run an npm script.
        
        Args:
            script_name: Name of the script to run
            package_json_path: Path to package.json file
            args: Additional arguments for the script
            
        Returns:
            Tuple of (success, output, error)
        """
        try:
            # Parse package.json to get scripts
            package_config = self._parse_package_json(package_json_path)
            
            if not package_config:
                return False, "", "Failed to parse package.json"
            
            scripts = package_config.get('scripts', {})
            
            if script_name not in scripts:
                return False, "", f"Script '{script_name}' not found in package.json"
            
            # Change to package directory
            package_dir = os.path.dirname(package_json_path)
            original_cwd = os.getcwd()
            os.chdir(package_dir)
            
            try:
                # Build run command
                run_cmd = [self.npm_executable, 'run', script_name]
                
                if args:
                    run_cmd.extend(args)
                
                # Execute script
                success, output, error = self._execute_npm_command(run_cmd)
                
                return success, output, error
            
            finally:
                # Restore original directory
                os.chdir(original_cwd)
        
        except Exception as e:
            return False, "", str(e)
    
    def verify_installation(self, package_name: str, 
                           package_json_path: Optional[str] = None) -> bool:
        """
        Verify that a package is properly installed.
        
        Args:
            package_name: Name of the package to verify
            package_json_path: Path to package.json file (optional)
            
        Returns:
            bool: True if package is properly installed
        """
        try:
            # Try to require the package
            require_cmd = [self.node_executable, '-e', f'require("{package_name}"); console.log("OK")']
            
            success, output, error = self._execute_command(require_cmd)
            
            if success and "OK" in output:
                return True
            
            # Try alternative verification methods
            if package_json_path:
                # Check if package is in node_modules
                package_dir = os.path.dirname(package_json_path)
                node_modules_path = os.path.join(package_dir, 'node_modules', package_name)
                
                if os.path.exists(node_modules_path):
                    return True
            
            return False
        
        except Exception as e:
            return False
    
    def get_installed_packages(self, package_json_path: Optional[str] = None) -> List[NpmPackage]:
        """
        Get list of installed packages.
        
        Args:
            package_json_path: Path to package.json file (optional)
            
        Returns:
            List of installed packages
        """
        try:
            if package_json_path:
                # Get packages from package.json and node_modules
                return self._get_packages_from_project(package_json_path)
            else:
                # Get globally installed packages
                return self._get_global_packages()
        
        except Exception as e:
            return []
    
    def _parse_package_json(self, package_json_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse package.json file.
        
        Args:
            package_json_path: Path to package.json file
            
        Returns:
            Dictionary containing package configuration
        """
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse JSON
            package_config = json.loads(content)
            
            return package_config
        
        except Exception as e:
            return None
    
    def _install_packages_from_config(self, dependencies: Dict[str, str],
                                    dev_dependencies: Dict[str, str],
                                    peer_dependencies: Dict[str, str],
                                    install_dev: bool,
                                    install_peer: bool) -> NpmInstallationResult:
        """
        Install packages from configuration dictionaries.
        
        Args:
            dependencies: Regular dependencies
            dev_dependencies: Development dependencies
            peer_dependencies: Peer dependencies
            install_dev: Whether to install dev dependencies
            install_peer: Whether to install peer dependencies
            
        Returns:
            NpmInstallationResult: Installation result
        """
        result = NpmInstallationResult(success=False)
        
        try:
            # Install regular dependencies
            if dependencies:
                self._update_progress("Installing regular dependencies...")
                install_cmd = [self.npm_executable, 'install']
                success, output, error = self._execute_npm_command(install_cmd)
                
                if success:
                    # Parse installed packages
                    for package_name, version in dependencies.items():
                        package = NpmPackage(
                            name=package_name,
                            version=version,
                            package_type=NpmPackageType.REGULAR,
                            status=NpmInstallStatus.SUCCESS
                        )
                        result.packages_installed.append(package)
                else:
                    result.error_messages.append(f"Failed to install regular dependencies: {error}")
            
            # Install dev dependencies
            if install_dev and dev_dependencies:
                self._update_progress("Installing dev dependencies...")
                install_cmd = [self.npm_executable, 'install', '--save-dev']
                install_cmd.extend([f"{name}@{version}" for name, version in dev_dependencies.items()])
                
                success, output, error = self._execute_npm_command(install_cmd)
                
                if success:
                    # Parse installed packages
                    for package_name, version in dev_dependencies.items():
                        package = NpmPackage(
                            name=package_name,
                            version=version,
                            package_type=NpmPackageType.DEV,
                            status=NpmInstallStatus.SUCCESS
                        )
                        result.packages_installed.append(package)
                else:
                    result.error_messages.append(f"Failed to install dev dependencies: {error}")
            
            # Install peer dependencies
            if install_peer and peer_dependencies:
                self._update_progress("Installing peer dependencies...")
                install_cmd = [self.npm_executable, 'install', '--save-peer']
                install_cmd.extend([f"{name}@{version}" for name, version in peer_dependencies.items()])
                
                success, output, error = self._execute_npm_command(install_cmd)
                
                if success:
                    # Parse installed packages
                    for package_name, version in peer_dependencies.items():
                        package = NpmPackage(
                            name=package_name,
                            version=version,
                            package_type=NpmPackageType.PEER,
                            status=NpmInstallStatus.SUCCESS
                        )
                        result.packages_installed.append(package)
                else:
                    result.error_messages.append(f"Failed to install peer dependencies: {error}")
            
            result.success = len(result.error_messages) == 0
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during package installation: {str(e)}")
            return result
    
    def _build_install_command(self, package: NpmPackage, global_install: bool = False) -> List[str]:
        """
        Build npm install command.
        
        Args:
            package: Package to install
            global_install: Whether to install globally
            
        Returns:
            List of command arguments
        """
        cmd = [self.npm_executable, 'install']
        
        # Add global flag
        if global_install:
            cmd.append('-g')
        
        # Add package type flags
        if package.package_type == NpmPackageType.DEV:
            cmd.append('--save-dev')
        elif package.package_type == NpmPackageType.PEER:
            cmd.append('--save-peer')
        else:
            cmd.append('--save')
        
        # Add package specification
        if package.version:
            cmd.append(f"{package.name}@{package.version}")
        else:
            cmd.append(package.name)
        
        return cmd
    
    def _get_packages_from_project(self, package_json_path: str) -> List[NpmPackage]:
        """
        Get packages from project directory.
        
        Args:
            package_json_path: Path to package.json file
            
        Returns:
            List of packages
        """
        try:
            # Parse package.json
            package_config = self._parse_package_json(package_json_path)
            
            if not package_config:
                return []
            
            packages = []
            
            # Get regular dependencies
            dependencies = package_config.get('dependencies', {})
            for name, version in dependencies.items():
                package = NpmPackage(
                    name=name,
                    version=version,
                    package_type=NpmPackageType.REGULAR,
                    status=NpmInstallStatus.SUCCESS
                )
                packages.append(package)
            
            # Get dev dependencies
            dev_dependencies = package_config.get('devDependencies', {})
            for name, version in dev_dependencies.items():
                package = NpmPackage(
                    name=name,
                    version=version,
                    package_type=NpmPackageType.DEV,
                    status=NpmInstallStatus.SUCCESS
                )
                packages.append(package)
            
            # Get peer dependencies
            peer_dependencies = package_config.get('peerDependencies', {})
            for name, version in peer_dependencies.items():
                package = NpmPackage(
                    name=name,
                    version=version,
                    package_type=NpmPackageType.PEER,
                    status=NpmInstallStatus.SUCCESS
                )
                packages.append(package)
            
            return packages
        
        except Exception as e:
            return []
    
    def _get_global_packages(self) -> List[NpmPackage]:
        """
        Get globally installed packages.
        
        Returns:
            List of global packages
        """
        try:
            # Build list command
            list_cmd = [self.npm_executable, 'list', '-g', '--depth=0', '--json']
            
            # Execute command
            success, output, error = self._execute_npm_command(list_cmd)
            
            if not success:
                return []
            
            # Parse JSON output
            packages_data = json.loads(output)
            packages = []
            
            dependencies = packages_data.get('dependencies', {})
            for name, pkg_data in dependencies.items():
                package = NpmPackage(
                    name=name,
                    version=pkg_data.get('version'),
                    package_type=NpmPackageType.REGULAR,
                    status=NpmInstallStatus.SUCCESS
                )
                packages.append(package)
            
            return packages
        
        except Exception as e:
            return []
    
    def _execute_npm_command(self, cmd: List[str]) -> Tuple[bool, str, str]:
        """
        Execute an npm command.
        
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
            return False, "", "NPM command timeout"
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
    
    def _find_npm_executable(self) -> str:
        """Find npm executable."""
        try:
            # Try common npm locations
            npm_locations = ['npm', 'npm3', 'yarn', 'pnpm']
            
            for npm_cmd in npm_locations:
                try:
                    result = subprocess.run(
                        [npm_cmd, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        return npm_cmd
                except:
                    continue
            
            return 'npm'  # Default fallback
        
        except Exception:
            return 'npm'
    
    def _find_node_executable(self) -> str:
        """Find node executable."""
        try:
            # Try common node locations
            node_locations = ['node', 'nodejs']
            
            for node_cmd in node_locations:
                try:
                    result = subprocess.run(
                        [node_cmd, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        return node_cmd
                except:
                    continue
            
            return 'node'  # Default fallback
        
        except Exception:
            return 'node'
    
    def _categorize_package(self, package_name: str) -> NpmPackageType:
        """
        Categorize a package by its name.
        
        Args:
            package_name: Name of the package
            
        Returns:
            NpmPackageType: Category of the package
        """
        package_lower = package_name.lower()
        
        # Check against categories
        for category, packages in self.package_categories.items():
            for pkg in packages:
                if pkg.lower() in package_lower or package_lower in pkg.lower():
                    return NpmPackageType.REGULAR
        
        # Check for dev packages
        if any(dev_indicator in package_lower for dev_indicator in ['dev', 'test', 'debug', 'build']):
            return NpmPackageType.DEV
        
        return NpmPackageType.REGULAR
    
    def _update_progress(self, message: str):
        """Update progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(message)
            except:
                pass


def main():
    """Main function for testing npm manager."""
    print("🧪 Testing NPM Manager")
    print("=" * 50)
    
    # Initialize manager
    manager = NpmManager()
    
    # Set up progress callback
    def progress_callback(message):
        print(f"  {message}")
    
    manager.set_progress_callback(progress_callback)
    
    # Test with a sample package.json
    test_path = "/tmp/test_package.json"
    package_json_content = {
        "name": "test-app",
        "version": "1.0.0",
        "description": "Test application",
        "main": "index.js",
        "scripts": {
            "start": "node index.js",
            "test": "jest",
            "build": "webpack"
        },
        "dependencies": {
            "express": "^4.18.0",
            "axios": "^1.0.0"
        },
        "devDependencies": {
            "nodemon": "^2.0.0",
            "jest": "^29.0.0"
        },
        "peerDependencies": {
            "react": "^18.0.0"
        }
    }
    
    with open(test_path, 'w') as f:
        json.dump(package_json_content, f, indent=2)
    
    # Test installation from package.json
    print("\n📦 Testing installation from package.json...")
    result = manager.install_from_package_json(test_path)
    
    print(f"✅ Installation success: {result.success}")
    print(f"✅ Total packages: {result.total_packages}")
    print(f"✅ Packages installed: {len(result.packages_installed)}")
    print(f"✅ Packages failed: {len(result.packages_failed)}")
    print(f"✅ Installation time: {result.installation_time:.2f}s")
    print(f"✅ Scripts found: {len(result.scripts)}")
    
    if result.scripts:
        print("   Scripts:")
        for script_name, script_command in result.scripts.items():
            print(f"     - {script_name}: {script_command}")
    
    if result.packages_installed:
        print("   Installed packages:")
        for pkg in result.packages_installed:
            print(f"     - {pkg.name} ({pkg.version or 'latest'}) [{pkg.package_type.value}]")
    
    if result.packages_failed:
        print("   Failed packages:")
        for pkg in result.packages_failed:
            print(f"     - {pkg.name}: {pkg.error_message}")
    
    # Test single package installation
    print("\n📦 Testing single package installation...")
    package = manager.install_package("lodash", package_type=NpmPackageType.REGULAR)
    
    print(f"✅ Package: {package.name}")
    print(f"✅ Status: {package.status.value}")
    print(f"✅ Install time: {package.install_time:.2f}s")
    
    if package.error_message:
        print(f"✅ Error: {package.error_message}")
    
    # Test script execution
    print("\n🚀 Testing script execution...")
    if result.scripts:
        script_name = list(result.scripts.keys())[0]
        success, output, error = manager.run_script(script_name, test_path)
        print(f"✅ Script '{script_name}' execution: {success}")
        if not success:
            print(f"   Error: {error}")
    
    # Test package verification
    print("\n✅ Testing package verification...")
    is_installed = manager.verify_installation("express", test_path)
    print(f"✅ Express installed: {is_installed}")
    
    # Test installed packages list
    print("\n📋 Testing installed packages list...")
    installed_packages = manager.get_installed_packages(test_path)
    print(f"✅ Total installed packages: {len(installed_packages)}")
    
    if installed_packages:
        print("   Sample packages:")
        for pkg in installed_packages[:5]:
            print(f"     - {pkg.name} ({pkg.version or 'unknown'}) [{pkg.package_type.value}]")
    
    # Cleanup
    os.remove(test_path)
    
    return True


if __name__ == "__main__":
    main()