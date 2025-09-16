#!/usr/bin/env python3
"""
PinokioCloud Application Installer

This module installs Pinokio applications using their detected installation method.
It coordinates the entire installation process including dependency resolution,
environment setup, and application installation.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import subprocess
import shutil
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import previous phase modules
sys.path.append('/workspace/github_repo')
from app_analysis.app_analyzer import AppAnalyzer, AppProfile
from app_analysis.installer_detector import InstallerDetector, InstallerType
from app_analysis.webui_detector import WebUIDetector, WebUIType
from app_analysis.dependency_analyzer import DependencyAnalyzer, DependencyType
from dependencies.dependency_finder import DependencyFinder
from dependencies.pip_manager import PipManager
from dependencies.conda_manager import CondaManager
from dependencies.npm_manager import NpmManager
from dependencies.system_manager import SystemManager
from dependencies.dependency_resolver import DependencyResolver
from dependencies.installation_verifier import InstallationVerifier
from environment_management.venv_manager import VirtualEnvironmentManager
from environment_management.file_system import FileSystemManager
from environment_management.shell_runner import ShellRunner
from environment_management.variable_system import VariableSystem
from environment_management.json_handler import JSONHandler


class InstallationStatus(Enum):
    """Enumeration of installation statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InstallationStep(Enum):
    """Enumeration of installation steps."""
    ANALYSIS = "analysis"
    ENVIRONMENT_SETUP = "environment_setup"
    DEPENDENCY_INSTALLATION = "dependency_installation"
    APPLICATION_INSTALLATION = "application_installation"
    VERIFICATION = "verification"
    CONFIGURATION = "configuration"


@dataclass
class InstallationProgress:
    """Installation progress tracking."""
    current_step: InstallationStep
    step_progress: float  # 0.0 to 1.0
    overall_progress: float  # 0.0 to 1.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    start_time: float = 0.0
    estimated_remaining: float = 0.0


@dataclass
class InstallationResult:
    """Result of application installation."""
    success: bool
    app_name: str
    app_path: str
    installation_time: float
    status: InstallationStatus
    progress_history: List[InstallationProgress] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    installed_files: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ApplicationInstaller:
    """
    Installs Pinokio applications using their detected installation method.
    
    Provides comprehensive application installation including:
    - App analysis and profile generation
    - Environment setup and configuration
    - Dependency resolution and installation
    - Application installation and configuration
    - Installation verification and testing
    - Progress tracking and error handling
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the application installer.
        
        Args:
            base_path: Base path for installation operations
        """
        self.base_path = base_path
        self.apps_path = os.path.join(base_path, "apps")
        
        # Initialize components
        self.app_analyzer = AppAnalyzer(base_path)
        self.installer_detector = InstallerDetector(base_path)
        self.webui_detector = WebUIDetector(base_path)
        self.dependency_analyzer = DependencyAnalyzer(base_path)
        self.dependency_finder = DependencyFinder(base_path)
        self.pip_manager = PipManager(base_path)
        self.conda_manager = CondaManager(base_path)
        self.npm_manager = NpmManager(base_path)
        self.system_manager = SystemManager(base_path)
        self.dependency_resolver = DependencyResolver(base_path)
        self.installation_verifier = InstallationVerifier(base_path)
        self.venv_manager = VirtualEnvironmentManager(base_path)
        self.file_system = FileSystemManager(base_path)
        self.shell_runner = ShellRunner(base_path)
        self.variable_system = VariableSystem(base_path)
        self.json_handler = JSONHandler(base_path)
        
        # Installation tracking
        self.active_installations: Dict[str, InstallationResult] = {}
        self.installation_history: List[InstallationResult] = []
        
        # Progress callback
        self.progress_callback = None
        
        # Ensure apps directory exists
        os.makedirs(self.apps_path, exist_ok=True)
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def install_application(self, app_name: str, 
                           app_source: str,
                           user_inputs: Optional[Dict[str, Any]] = None,
                           force_reinstall: bool = False) -> InstallationResult:
        """
        Install a Pinokio application.
        
        Args:
            app_name: Name of the application to install
            app_source: Source of the application (URL, path, or identifier)
            user_inputs: User inputs for installation configuration
            force_reinstall: Force reinstallation even if already installed
            
        Returns:
            InstallationResult: Complete installation result
        """
        start_time = time.time()
        
        result = InstallationResult(
            success=False,
            app_name=app_name,
            app_path="",
            installation_time=0.0,
            status=InstallationStatus.PENDING
        )
        
        try:
            self._update_progress("Starting application installation...", result)
            
            # Check if already installed
            if not force_reinstall and self._is_app_installed(app_name):
                result.success = True
                result.app_path = os.path.join(self.apps_path, app_name)
                result.status = InstallationStatus.COMPLETED
                result.installation_time = time.time() - start_time
                self._update_progress("Application already installed", result)
                return result
            
            # Step 1: App Analysis
            self._update_progress("Analyzing application...", result, InstallationStep.ANALYSIS, 0.0)
            app_profile = self._analyze_application(app_name, app_source)
            if not app_profile:
                result.error_messages.append("Failed to analyze application")
                result.status = InstallationStatus.FAILED
                return result
            
            self._update_progress("Application analysis complete", result, InstallationStep.ANALYSIS, 1.0)
            
            # Step 2: Environment Setup
            self._update_progress("Setting up environment...", result, InstallationStep.ENVIRONMENT_SETUP, 0.0)
            environment_path = self._setup_environment(app_name, app_profile)
            if not environment_path:
                result.error_messages.append("Failed to setup environment")
                result.status = InstallationStatus.FAILED
                return result
            
            self._update_progress("Environment setup complete", result, InstallationStep.ENVIRONMENT_SETUP, 1.0)
            
            # Step 3: Dependency Installation
            self._update_progress("Installing dependencies...", result, InstallationStep.DEPENDENCY_INSTALLATION, 0.0)
            dependency_success = self._install_dependencies(app_name, app_profile, environment_path)
            if not dependency_success:
                result.error_messages.append("Failed to install dependencies")
                result.status = InstallationStatus.FAILED
                return result
            
            self._update_progress("Dependency installation complete", result, InstallationStep.DEPENDENCY_INSTALLATION, 1.0)
            
            # Step 4: Application Installation
            self._update_progress("Installing application...", result, InstallationStep.APPLICATION_INSTALLATION, 0.0)
            app_path = self._install_application_files(app_name, app_source, app_profile, environment_path)
            if not app_path:
                result.error_messages.append("Failed to install application files")
                result.status = InstallationStatus.FAILED
                return result
            
            result.app_path = app_path
            self._update_progress("Application installation complete", result, InstallationStep.APPLICATION_INSTALLATION, 1.0)
            
            # Step 5: Verification
            self._update_progress("Verifying installation...", result, InstallationStep.VERIFICATION, 0.0)
            verification_success = self._verify_installation(app_name, app_path, environment_path)
            if not verification_success:
                result.warnings.append("Installation verification failed")
            
            self._update_progress("Installation verification complete", result, InstallationStep.VERIFICATION, 1.0)
            
            # Step 6: Configuration
            self._update_progress("Configuring application...", result, InstallationStep.CONFIGURATION, 0.0)
            configuration = self._configure_application(app_name, app_path, app_profile, user_inputs)
            result.configuration = configuration
            
            self._update_progress("Application configuration complete", result, InstallationStep.CONFIGURATION, 1.0)
            
            # Finalize installation
            result.success = True
            result.status = InstallationStatus.COMPLETED
            result.installation_time = time.time() - start_time
            
            # Save installation record
            self._save_installation_record(result)
            
            self._update_progress("Application installation complete!", result)
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Installation error: {str(e)}")
            result.status = InstallationStatus.FAILED
            result.installation_time = time.time() - start_time
            return result
    
    def install_applications_batch(self, app_requests: List[Dict[str, Any]]) -> List[InstallationResult]:
        """
        Install multiple applications in batch.
        
        Args:
            app_requests: List of app installation requests
            
        Returns:
            List of installation results
        """
        results = []
        
        for i, request in enumerate(app_requests):
            app_name = request.get('name', f'app_{i}')
            app_source = request.get('source', '')
            user_inputs = request.get('inputs', {})
            force_reinstall = request.get('force_reinstall', False)
            
            self._update_progress(f"Installing {app_name} ({i+1}/{len(app_requests)})...")
            
            result = self.install_application(
                app_name=app_name,
                app_source=app_source,
                user_inputs=user_inputs,
                force_reinstall=force_reinstall
            )
            
            results.append(result)
        
        return results
    
    def uninstall_application(self, app_name: str) -> bool:
        """
        Uninstall an application.
        
        Args:
            app_name: Name of the application to uninstall
            
        Returns:
            bool: True if uninstalled successfully
        """
        try:
            app_path = os.path.join(self.apps_path, app_name)
            
            if not os.path.exists(app_path):
                return False
            
            # Remove application files
            shutil.rmtree(app_path, ignore_errors=True)
            
            # Remove installation record
            self._remove_installation_record(app_name)
            
            return True
        
        except Exception as e:
            return False
    
    def get_installed_applications(self) -> List[Dict[str, Any]]:
        """
        Get list of installed applications.
        
        Returns:
            List of installed application information
        """
        installed_apps = []
        
        try:
            for item in os.listdir(self.apps_path):
                app_path = os.path.join(self.apps_path, item)
                if os.path.isdir(app_path):
                    # Load installation record
                    record = self._load_installation_record(item)
                    if record:
                        installed_apps.append({
                            'name': item,
                            'path': app_path,
                            'installed_date': record.get('installed_date', ''),
                            'version': record.get('version', ''),
                            'status': record.get('status', 'unknown')
                        })
        
        except Exception as e:
            pass
        
        return installed_apps
    
    def get_installation_status(self, app_name: str) -> Optional[InstallationResult]:
        """
        Get installation status for an application.
        
        Args:
            app_name: Name of the application
            
        Returns:
            InstallationResult or None if not found
        """
        return self.active_installations.get(app_name)
    
    def _analyze_application(self, app_name: str, app_source: str) -> Optional[AppProfile]:
        """
        Analyze application to determine installation requirements.
        
        Args:
            app_name: Name of the application
            app_source: Source of the application
            
        Returns:
            AppProfile or None if analysis failed
        """
        try:
            # Create temporary directory for analysis
            temp_path = os.path.join(self.base_path, "temp", app_name)
            os.makedirs(temp_path, exist_ok=True)
            
            # Download or copy application source
            if app_source.startswith('http'):
                # Download from URL
                self._download_application(app_source, temp_path)
            else:
                # Copy from local path
                if os.path.exists(app_source):
                    shutil.copytree(app_source, temp_path, dirs_exist_ok=True)
            
            # Analyze the application
            profile = self.app_analyzer.analyze_app(app_name, temp_path)
            
            # Cleanup temp directory
            shutil.rmtree(temp_path, ignore_errors=True)
            
            return profile
        
        except Exception as e:
            return None
    
    def _setup_environment(self, app_name: str, app_profile: AppProfile) -> Optional[str]:
        """
        Setup environment for application installation.
        
        Args:
            app_name: Name of the application
            app_profile: Application profile
            
        Returns:
            Environment path or None if setup failed
        """
        try:
            # Determine environment type
            if app_profile.dependency_systems and 'conda' in app_profile.dependency_systems:
                # Use conda environment
                env_name = f"{app_name}_env"
                result = self.conda_manager.create_environment(
                    name=env_name,
                    python_version=app_profile.python_version or "3.9",
                    packages=[]
                )
                if result.success:
                    return result.environment_path
            else:
                # Use Python venv
                env_path = os.path.join(self.apps_path, app_name, "venv")
                result = self.venv_manager.create_environment(
                    name=app_name,
                    env_type="venv",
                    python_version=app_profile.python_version or "3.9"
                )
                if result.success:
                    return result.environment_path
            
            return None
        
        except Exception as e:
            return None
    
    def _install_dependencies(self, app_name: str, app_profile: AppProfile, 
                            environment_path: str) -> bool:
        """
        Install application dependencies.
        
        Args:
            app_name: Name of the application
            app_profile: Application profile
            environment_path: Path to environment
            
        Returns:
            bool: True if dependencies installed successfully
        """
        try:
            # Find dependencies
            dependencies = self.dependency_finder.find_dependencies(
                app_path=os.path.join(self.apps_path, app_name),
                app_type=app_profile.category
            )
            
            if not dependencies:
                return True  # No dependencies to install
            
            # Resolve conflicts
            resolution_result = self.dependency_resolver.resolve_conflicts(
                app_path=os.path.join(self.apps_path, app_name)
            )
            
            if not resolution_result.success:
                return False
            
            # Install dependencies by type
            for dep_type, packages in dependencies.items():
                if dep_type == 'pip':
                    for package in packages:
                        result = self.pip_manager.install_package(
                            package_name=package['name'],
                            version=package.get('version'),
                            environment_path=environment_path
                        )
                        if result.status != 'success':
                            return False
                
                elif dep_type == 'conda':
                    for package in packages:
                        result = self.conda_manager.install_packages(
                            environment=environment_path,
                            packages=[package['name']]
                        )
                        if not result.success:
                            return False
                
                elif dep_type == 'npm':
                    for package in packages:
                        result = self.npm_manager.install_package(
                            package_name=package['name'],
                            version=package.get('version')
                        )
                        if result.status != 'success':
                            return False
                
                elif dep_type == 'system':
                    for package in packages:
                        result = self.system_manager.install_package(
                            package_name=package['name']
                        )
                        if result.status != 'success':
                            return False
            
            return True
        
        except Exception as e:
            return False
    
    def _install_application_files(self, app_name: str, app_source: str, 
                                 app_profile: AppProfile, environment_path: str) -> Optional[str]:
        """
        Install application files.
        
        Args:
            app_name: Name of the application
            app_source: Source of the application
            app_profile: Application profile
            environment_path: Path to environment
            
        Returns:
            Application path or None if installation failed
        """
        try:
            app_path = os.path.join(self.apps_path, app_name)
            os.makedirs(app_path, exist_ok=True)
            
            # Download or copy application files
            if app_source.startswith('http'):
                # Download from URL
                self._download_application(app_source, app_path)
            else:
                # Copy from local path
                if os.path.exists(app_source):
                    shutil.copytree(app_source, app_path, dirs_exist_ok=True)
            
            # Execute installation scripts if present
            if app_profile.installer_type == InstallerType.JS:
                # Execute install.js
                install_js_path = os.path.join(app_path, "install.js")
                if os.path.exists(install_js_path):
                    self._execute_install_script(install_js_path, app_path, environment_path)
            
            elif app_profile.installer_type == InstallerType.JSON:
                # Execute install.json
                install_json_path = os.path.join(app_path, "install.json")
                if os.path.exists(install_json_path):
                    self._execute_install_json(install_json_path, app_path, environment_path)
            
            return app_path
        
        except Exception as e:
            return None
    
    def _verify_installation(self, app_name: str, app_path: str, 
                           environment_path: str) -> bool:
        """
        Verify application installation.
        
        Args:
            app_name: Name of the application
            app_path: Path to application
            environment_path: Path to environment
            
        Returns:
            bool: True if verification successful
        """
        try:
            # Run installation verification
            result = self.installation_verifier.verify_installation(
                app_path=app_path,
                environment_path=environment_path
            )
            
            return result.success
        
        except Exception as e:
            return False
    
    def _configure_application(self, app_name: str, app_path: str, 
                             app_profile: AppProfile, user_inputs: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Configure application after installation.
        
        Args:
            app_name: Name of the application
            app_path: Path to application
            app_profile: Application profile
            user_inputs: User inputs for configuration
            
        Returns:
            Configuration dictionary
        """
        try:
            configuration = {
                'app_name': app_name,
                'app_path': app_path,
                'installer_type': app_profile.installer_type.value if app_profile.installer_type else 'unknown',
                'webui_type': app_profile.webui_type.value if app_profile.webui_type else 'none',
                'dependency_systems': app_profile.dependency_systems or [],
                'installed_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'version': app_profile.version or 'unknown'
            }
            
            # Add user inputs
            if user_inputs:
                configuration.update(user_inputs)
            
            # Save configuration
            config_path = os.path.join(app_path, "config.json")
            self.json_handler.write_json(config_path, configuration)
            
            return configuration
        
        except Exception as e:
            return {}
    
    def _download_application(self, url: str, target_path: str):
        """Download application from URL."""
        try:
            # Use git clone if it's a git repository
            if 'github.com' in url or 'gitlab.com' in url:
                subprocess.run(['git', 'clone', url, target_path], check=True)
            else:
                # Use wget or curl for other URLs
                subprocess.run(['wget', '-O', target_path, url], check=True)
        
        except Exception as e:
            raise Exception(f"Failed to download application: {str(e)}")
    
    def _execute_install_script(self, script_path: str, app_path: str, environment_path: str):
        """Execute install.js script."""
        try:
            # Change to app directory
            original_cwd = os.getcwd()
            os.chdir(app_path)
            
            # Execute script with Node.js
            result = subprocess.run(['node', script_path], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                raise Exception(f"Install script failed: {result.stderr}")
            
            # Restore original directory
            os.chdir(original_cwd)
        
        except Exception as e:
            raise Exception(f"Failed to execute install script: {str(e)}")
    
    def _execute_install_json(self, json_path: str, app_path: str, environment_path: str):
        """Execute install.json configuration."""
        try:
            # Load install.json
            with open(json_path, 'r') as f:
                install_config = json.load(f)
            
            # Execute installation steps
            for step in install_config.get('steps', []):
                step_type = step.get('type')
                step_command = step.get('command')
                
                if step_type == 'shell' and step_command:
                    # Execute shell command
                    result = subprocess.run(step_command, shell=True, 
                                          capture_output=True, text=True, timeout=60)
                    
                    if result.returncode != 0:
                        raise Exception(f"Install step failed: {result.stderr}")
        
        except Exception as e:
            raise Exception(f"Failed to execute install.json: {str(e)}")
    
    def _is_app_installed(self, app_name: str) -> bool:
        """Check if application is already installed."""
        app_path = os.path.join(self.apps_path, app_name)
        return os.path.exists(app_path) and os.path.isdir(app_path)
    
    def _save_installation_record(self, result: InstallationResult):
        """Save installation record."""
        try:
            record = {
                'app_name': result.app_name,
                'app_path': result.app_path,
                'installed_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'installation_time': result.installation_time,
                'status': result.status.value,
                'configuration': result.configuration
            }
            
            record_path = os.path.join(self.base_path, "installation_records", f"{result.app_name}.json")
            os.makedirs(os.path.dirname(record_path), exist_ok=True)
            
            self.json_handler.write_json(record_path, record)
        
        except Exception as e:
            pass
    
    def _load_installation_record(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Load installation record."""
        try:
            record_path = os.path.join(self.base_path, "installation_records", f"{app_name}.json")
            if os.path.exists(record_path):
                return self.json_handler.read_json(record_path)
        except Exception as e:
            pass
        return None
    
    def _remove_installation_record(self, app_name: str):
        """Remove installation record."""
        try:
            record_path = os.path.join(self.base_path, "installation_records", f"{app_name}.json")
            if os.path.exists(record_path):
                os.remove(record_path)
        except Exception as e:
            pass
    
    def _update_progress(self, message: str, result: Optional[InstallationResult] = None,
                        step: Optional[InstallationStep] = None, step_progress: float = 0.0):
        """Update progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(message, result, step, step_progress)
            except:
                pass


def main():
    """Main function for testing application installer."""
    print("🧪 Testing Application Installer")
    print("=" * 50)
    
    # Initialize installer
    installer = ApplicationInstaller()
    
    # Set up progress callback
    def progress_callback(message, result=None, step=None, step_progress=0.0):
        print(f"  {message}")
        if step:
            print(f"    Step: {step.value} ({step_progress*100:.1f}%)")
    
    installer.set_progress_callback(progress_callback)
    
    # Test application installation
    print("\n🔧 Testing application installation...")
    
    # Test with a sample app
    test_app_name = "test_app"
    test_app_source = "https://github.com/example/test-app"
    
    result = installer.install_application(
        app_name=test_app_name,
        app_source=test_app_source,
        user_inputs={'gpu': 'T4', 'model': 'base'},
        force_reinstall=True
    )
    
    print(f"✅ Installation success: {result.success}")
    print(f"✅ App name: {result.app_name}")
    print(f"✅ App path: {result.app_path}")
    print(f"✅ Installation time: {result.installation_time:.2f}s")
    print(f"✅ Status: {result.status.value}")
    
    if result.error_messages:
        print("❌ Errors:")
        for error in result.error_messages:
            print(f"   - {error}")
    
    if result.warnings:
        print("⚠️ Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")
    
    # Test batch installation
    print("\n📦 Testing batch installation...")
    batch_requests = [
        {'name': 'app1', 'source': 'https://github.com/example/app1'},
        {'name': 'app2', 'source': 'https://github.com/example/app2'},
        {'name': 'app3', 'source': 'https://github.com/example/app3'}
    ]
    
    batch_results = installer.install_applications_batch(batch_requests)
    
    print(f"✅ Batch installation: {len(batch_results)} apps processed")
    successful = sum(1 for r in batch_results if r.success)
    print(f"✅ Successful installations: {successful}/{len(batch_results)}")
    
    # Test installed applications list
    print("\n📋 Testing installed applications list...")
    installed_apps = installer.get_installed_applications()
    
    print(f"✅ Installed applications: {len(installed_apps)}")
    for app in installed_apps:
        print(f"   - {app['name']}: {app['status']}")
    
    # Test uninstallation
    print("\n🗑️ Testing application uninstallation...")
    uninstall_success = installer.uninstall_application(test_app_name)
    print(f"✅ Uninstallation success: {uninstall_success}")
    
    return True


if __name__ == "__main__":
    main()