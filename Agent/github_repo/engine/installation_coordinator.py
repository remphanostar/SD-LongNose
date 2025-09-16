#!/usr/bin/env python3
"""
PinokioCloud Installation Coordinator

This module coordinates the entire installation process.
It combines app analysis, dependency installation, and app installation into a seamless workflow.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import threading
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
from .installer import ApplicationInstaller, InstallationResult, InstallationStatus
from .script_parser import ScriptParser, ScriptExecutionResult
from .input_handler import InputHandler, FormResult
from .state_manager import StateManager, ApplicationState, InstallationState


class CoordinationStatus(Enum):
    """Enumeration of coordination statuses."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    COLLECTING_INPUT = "collecting_input"
    SETTING_UP_ENVIRONMENT = "setting_up_environment"
    INSTALLING_DEPENDENCIES = "installing_dependencies"
    INSTALLING_APPLICATION = "installing_application"
    VERIFYING_INSTALLATION = "verifying_installation"
    CONFIGURING_APPLICATION = "configuring_application"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CoordinationProgress:
    """Installation coordination progress."""
    current_phase: CoordinationStatus
    phase_progress: float  # 0.0 to 1.0
    overall_progress: float  # 0.0 to 1.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    start_time: float = 0.0
    estimated_remaining: float = 0.0


@dataclass
class CoordinationResult:
    """Complete coordination result."""
    success: bool
    installation_id: str
    app_name: str
    coordination_time: float
    status: CoordinationStatus
    app_profile: Optional[AppProfile] = None
    form_result: Optional[FormResult] = None
    installation_result: Optional[InstallationResult] = None
    progress_history: List[CoordinationProgress] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class InstallationCoordinator:
    """
    Coordinates the entire installation process.
    
    Provides comprehensive installation coordination including:
    - Application analysis and profiling
    - User input collection and validation
    - Environment setup and configuration
    - Dependency resolution and installation
    - Application installation and configuration
    - Installation verification and testing
    - Progress tracking and error handling
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the installation coordinator.
        
        Args:
            base_path: Base path for coordination operations
        """
        self.base_path = base_path
        
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
        self.installer = ApplicationInstaller(base_path)
        self.script_parser = ScriptParser(base_path)
        self.input_handler = InputHandler(base_path)
        self.state_manager = StateManager(base_path)
        
        # Coordination tracking
        self.active_coordinations: Dict[str, CoordinationResult] = {}
        self.coordination_history: List[CoordinationResult] = []
        
        # Progress callback
        self.progress_callback = None
        
        # Threading
        self.lock = threading.RLock()
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def coordinate_installation(self, app_name: str, app_source: str,
                              user_inputs: Optional[Dict[str, Any]] = None,
                              force_reinstall: bool = False) -> CoordinationResult:
        """
        Coordinate complete application installation.
        
        Args:
            app_name: Name of the application
            app_source: Source of the application
            user_inputs: User inputs for installation
            force_reinstall: Force reinstallation
            
        Returns:
            CoordinationResult: Complete coordination result
        """
        start_time = time.time()
        installation_id = f"install_{app_name}_{int(time.time())}"
        
        result = CoordinationResult(
            success=False,
            installation_id=installation_id,
            app_name=app_name,
            coordination_time=0.0,
            status=CoordinationStatus.PENDING
        )
        
        try:
            with self.lock:
                self.active_coordinations[installation_id] = result
            
            self._update_progress("Starting installation coordination...", result)
            
            # Phase 1: Application Analysis
            self._update_progress("Analyzing application...", result, CoordinationStatus.ANALYZING, 0.0)
            app_profile = self._analyze_application(app_name, app_source)
            if not app_profile:
                result.error_messages.append("Failed to analyze application")
                result.status = CoordinationStatus.FAILED
                return result
            
            result.app_profile = app_profile
            self._update_progress("Application analysis complete", result, CoordinationStatus.ANALYZING, 1.0)
            
            # Phase 2: User Input Collection
            self._update_progress("Collecting user input...", result, CoordinationStatus.COLLECTING_INPUT, 0.0)
            form_result = self._collect_user_input(app_name, app_profile, user_inputs)
            if not form_result or not form_result.success:
                result.error_messages.append("Failed to collect user input")
                result.status = CoordinationStatus.FAILED
                return result
            
            result.form_result = form_result
            self._update_progress("User input collection complete", result, CoordinationStatus.COLLECTING_INPUT, 1.0)
            
            # Phase 3: Environment Setup
            self._update_progress("Setting up environment...", result, CoordinationStatus.SETTING_UP_ENVIRONMENT, 0.0)
            environment_success = self._setup_environment(app_name, app_profile, form_result.submitted_data)
            if not environment_success:
                result.error_messages.append("Failed to setup environment")
                result.status = CoordinationStatus.FAILED
                return result
            
            self._update_progress("Environment setup complete", result, CoordinationStatus.SETTING_UP_ENVIRONMENT, 1.0)
            
            # Phase 4: Dependency Installation
            self._update_progress("Installing dependencies...", result, CoordinationStatus.INSTALLING_DEPENDENCIES, 0.0)
            dependency_success = self._install_dependencies(app_name, app_profile, form_result.submitted_data)
            if not dependency_success:
                result.error_messages.append("Failed to install dependencies")
                result.status = CoordinationStatus.FAILED
                return result
            
            self._update_progress("Dependency installation complete", result, CoordinationStatus.INSTALLING_DEPENDENCIES, 1.0)
            
            # Phase 5: Application Installation
            self._update_progress("Installing application...", result, CoordinationStatus.INSTALLING_APPLICATION, 0.0)
            installation_result = self._install_application(app_name, app_source, app_profile, form_result.submitted_data)
            if not installation_result or not installation_result.success:
                result.error_messages.append("Failed to install application")
                result.status = CoordinationStatus.FAILED
                return result
            
            result.installation_result = installation_result
            self._update_progress("Application installation complete", result, CoordinationStatus.INSTALLING_APPLICATION, 1.0)
            
            # Phase 6: Installation Verification
            self._update_progress("Verifying installation...", result, CoordinationStatus.VERIFYING_INSTALLATION, 0.0)
            verification_success = self._verify_installation(app_name, installation_result.app_path)
            if not verification_success:
                result.warnings.append("Installation verification failed")
            
            self._update_progress("Installation verification complete", result, CoordinationStatus.VERIFYING_INSTALLATION, 1.0)
            
            # Phase 7: Application Configuration
            self._update_progress("Configuring application...", result, CoordinationStatus.CONFIGURING_APPLICATION, 0.0)
            configuration_success = self._configure_application(app_name, installation_result.app_path, app_profile, form_result.submitted_data)
            if not configuration_success:
                result.warnings.append("Application configuration failed")
            
            self._update_progress("Application configuration complete", result, CoordinationStatus.CONFIGURING_APPLICATION, 1.0)
            
            # Finalize coordination
            result.success = True
            result.status = CoordinationStatus.COMPLETED
            result.coordination_time = time.time() - start_time
            
            # Register application in state manager
            self.state_manager.register_application(
                app_name=app_name,
                app_path=installation_result.app_path,
                configuration=installation_result.configuration
            )
            
            # Register installation in state manager
            self.state_manager.register_installation(installation_id, app_name)
            self.state_manager.update_installation_status(
                installation_id=installation_id,
                status=result.status,
                progress=1.0,
                current_step="Installation complete"
            )
            
            self._update_progress("Installation coordination complete!", result)
            
            # Move to history
            self.coordination_history.append(result)
            if installation_id in self.active_coordinations:
                del self.active_coordinations[installation_id]
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Coordination error: {str(e)}")
            result.status = CoordinationStatus.FAILED
            result.coordination_time = time.time() - start_time
            
            # Update state manager
            if installation_id in self.active_coordinations:
                self.state_manager.update_installation_status(
                    installation_id=installation_id,
                    status=result.status,
                    error_messages=result.error_messages
                )
            
            return result
    
    def coordinate_batch_installation(self, app_requests: List[Dict[str, Any]]) -> List[CoordinationResult]:
        """
        Coordinate batch installation of multiple applications.
        
        Args:
            app_requests: List of app installation requests
            
        Returns:
            List of coordination results
        """
        results = []
        
        for i, request in enumerate(app_requests):
            app_name = request.get('name', f'app_{i}')
            app_source = request.get('source', '')
            user_inputs = request.get('inputs', {})
            force_reinstall = request.get('force_reinstall', False)
            
            self._update_progress(f"Coordinating installation {i+1}/{len(app_requests)}: {app_name}")
            
            result = self.coordinate_installation(
                app_name=app_name,
                app_source=app_source,
                user_inputs=user_inputs,
                force_reinstall=force_reinstall
            )
            
            results.append(result)
        
        return results
    
    def get_coordination_status(self, installation_id: str) -> Optional[CoordinationResult]:
        """
        Get coordination status.
        
        Args:
            installation_id: Installation ID
            
        Returns:
            CoordinationResult or None if not found
        """
        with self.lock:
            return self.active_coordinations.get(installation_id)
    
    def cancel_coordination(self, installation_id: str) -> bool:
        """
        Cancel coordination.
        
        Args:
            installation_id: Installation ID
            
        Returns:
            bool: True if cancellation successful
        """
        try:
            with self.lock:
                if installation_id in self.active_coordinations:
                    result = self.active_coordinations[installation_id]
                    result.status = CoordinationStatus.CANCELLED
                    result.coordination_time = time.time() - result.progress_history[0].start_time if result.progress_history else 0.0
                    
                    # Update state manager
                    self.state_manager.update_installation_status(
                        installation_id=installation_id,
                        status=result.status
                    )
                    
                    # Move to history
                    self.coordination_history.append(result)
                    del self.active_coordinations[installation_id]
                    
                    self._update_progress(f"Cancelled coordination: {installation_id}")
                    return True
            
            return False
        
        except Exception as e:
            return False
    
    def get_coordination_history(self, limit: int = 100) -> List[CoordinationResult]:
        """
        Get coordination history.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of coordination results
        """
        with self.lock:
            history = list(self.coordination_history)
            history.sort(key=lambda x: x.coordination_time, reverse=True)
            return history[:limit]
    
    def _analyze_application(self, app_name: str, app_source: str) -> Optional[AppProfile]:
        """Analyze application to determine requirements."""
        try:
            # Create temporary directory for analysis
            temp_path = os.path.join(self.base_path, "temp", app_name)
            os.makedirs(temp_path, exist_ok=True)
            
            # Download or copy application source
            if app_source.startswith('http'):
                self._download_application(app_source, temp_path)
            else:
                if os.path.exists(app_source):
                    import shutil
                    shutil.copytree(app_source, temp_path, dirs_exist_ok=True)
            
            # Analyze the application
            profile = self.app_analyzer.analyze_app(app_name, temp_path)
            
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_path, ignore_errors=True)
            
            return profile
        
        except Exception as e:
            return None
    
    def _collect_user_input(self, app_name: str, app_profile: AppProfile, 
                           user_inputs: Optional[Dict[str, Any]]) -> Optional[FormResult]:
        """Collect user input for installation."""
        try:
            # Create installation form
            form_id = self.input_handler.create_installation_form(app_name, app_profile.__dict__)
            
            if not form_id:
                return None
            
            # Use provided inputs or create default inputs
            if user_inputs:
                inputs = user_inputs
            else:
                # Create default inputs based on app profile
                inputs = self._create_default_inputs(app_profile)
            
            # Collect input
            form_result = self.input_handler.collect_input(form_id, inputs)
            
            return form_result
        
        except Exception as e:
            return None
    
    def _setup_environment(self, app_name: str, app_profile: AppProfile, 
                          user_inputs: Dict[str, Any]) -> bool:
        """Setup environment for installation."""
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
                return result.success
            else:
                # Use Python venv
                result = self.venv_manager.create_environment(
                    name=app_name,
                    env_type="venv",
                    python_version=app_profile.python_version or "3.9"
                )
                return result.success
        
        except Exception as e:
            return False
    
    def _install_dependencies(self, app_name: str, app_profile: AppProfile, 
                            user_inputs: Dict[str, Any]) -> bool:
        """Install application dependencies."""
        try:
            # Find dependencies
            app_path = os.path.join(self.base_path, "apps", app_name)
            dependencies = self.dependency_finder.find_dependencies(
                app_path=app_path,
                app_type=app_profile.category
            )
            
            if not dependencies:
                return True  # No dependencies to install
            
            # Resolve conflicts
            resolution_result = self.dependency_resolver.resolve_conflicts(app_path=app_path)
            if not resolution_result.success:
                return False
            
            # Install dependencies by type
            for dep_type, packages in dependencies.items():
                if dep_type == 'pip':
                    for package in packages:
                        result = self.pip_manager.install_package(
                            package_name=package['name'],
                            version=package.get('version')
                        )
                        if result.status != 'success':
                            return False
                
                elif dep_type == 'conda':
                    for package in packages:
                        result = self.conda_manager.install_packages(
                            environment=f"{app_name}_env",
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
    
    def _install_application(self, app_name: str, app_source: str, app_profile: AppProfile, 
                           user_inputs: Dict[str, Any]) -> Optional[InstallationResult]:
        """Install the application."""
        try:
            # Use the application installer
            result = self.installer.install_application(
                app_name=app_name,
                app_source=app_source,
                user_inputs=user_inputs,
                force_reinstall=True
            )
            
            return result
        
        except Exception as e:
            return None
    
    def _verify_installation(self, app_name: str, app_path: str) -> bool:
        """Verify application installation."""
        try:
            # Run installation verification
            result = self.installation_verifier.verify_installation(
                app_path=app_path
            )
            
            return result.success
        
        except Exception as e:
            return False
    
    def _configure_application(self, app_name: str, app_path: str, app_profile: AppProfile, 
                             user_inputs: Dict[str, Any]) -> bool:
        """Configure application after installation."""
        try:
            # Create configuration file
            config = {
                'app_name': app_name,
                'app_path': app_path,
                'installer_type': app_profile.installer_type.value if app_profile.installer_type else 'unknown',
                'webui_type': app_profile.webui_type.value if app_profile.webui_type else 'none',
                'dependency_systems': app_profile.dependency_systems or [],
                'installed_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'version': app_profile.version or 'unknown',
                'user_inputs': user_inputs
            }
            
            # Save configuration
            config_path = os.path.join(app_path, "config.json")
            self.json_handler.write_json(config_path, config)
            
            return True
        
        except Exception as e:
            return False
    
    def _create_default_inputs(self, app_profile: AppProfile) -> Dict[str, Any]:
        """Create default inputs based on app profile."""
        try:
            inputs = {}
            
            # Add default inputs based on app category
            if app_profile.category in ['LLM', 'TEXT']:
                inputs['model_name'] = 'gpt-3.5-turbo'
                inputs['max_tokens'] = 1000
            
            if app_profile.category in ['IMAGE', 'VIDEO']:
                inputs['gpu_type'] = 'T4'
                inputs['image_size'] = '512x512'
            
            if app_profile.category in ['AUDIO']:
                inputs['audio_quality'] = 'high'
            
            # Add web UI defaults
            if app_profile.webui_type:
                inputs['port'] = 7860
                inputs['share'] = False
                inputs['tunnel_type'] = 'ngrok'
            
            # Add advanced defaults
            inputs['auto_start'] = True
            
            return inputs
        
        except Exception as e:
            return {}
    
    def _download_application(self, url: str, target_path: str):
        """Download application from URL."""
        try:
            # Use git clone if it's a git repository
            if 'github.com' in url or 'gitlab.com' in url:
                import subprocess
                subprocess.run(['git', 'clone', url, target_path], check=True)
            else:
                # Use wget or curl for other URLs
                import subprocess
                subprocess.run(['wget', '-O', target_path, url], check=True)
        
        except Exception as e:
            raise Exception(f"Failed to download application: {str(e)}")
    
    def _update_progress(self, message: str, result: Optional[CoordinationResult] = None,
                        phase: Optional[CoordinationStatus] = None, phase_progress: float = 0.0):
        """Update progress and call callback if set."""
        if result:
            progress = CoordinationProgress(
                current_phase=phase or result.status,
                phase_progress=phase_progress,
                overall_progress=phase_progress,  # Simplified for now
                message=message,
                start_time=time.time()
            )
            result.progress_history.append(progress)
        
        if self.progress_callback:
            try:
                self.progress_callback(message, result, phase, phase_progress)
            except:
                pass


def main():
    """Main function for testing installation coordinator."""
    print("🧪 Testing Installation Coordinator")
    print("=" * 50)
    
    # Initialize coordinator
    coordinator = InstallationCoordinator()
    
    # Set up progress callback
    def progress_callback(message, result=None, phase=None, phase_progress=0.0):
        print(f"  {message}")
        if phase:
            print(f"    Phase: {phase.value} ({phase_progress*100:.1f}%)")
    
    coordinator.set_progress_callback(progress_callback)
    
    # Test single application coordination
    print("\n🔧 Testing single application coordination...")
    
    result = coordinator.coordinate_installation(
        app_name="test_app",
        app_source="https://github.com/example/test-app",
        user_inputs={
            'model_name': 'gpt-3.5-turbo',
            'gpu_type': 'T4',
            'port': 7860,
            'auto_start': True
        },
        force_reinstall=True
    )
    
    print(f"✅ Coordination success: {result.success}")
    print(f"✅ Installation ID: {result.installation_id}")
    print(f"✅ App name: {result.app_name}")
    print(f"✅ Coordination time: {result.coordination_time:.2f}s")
    print(f"✅ Status: {result.status.value}")
    
    if result.app_profile:
        print(f"✅ App profile: {result.app_profile.category}")
    
    if result.form_result:
        print(f"✅ Form result: {result.form_result.success}")
    
    if result.installation_result:
        print(f"✅ Installation result: {result.installation_result.success}")
        print(f"   App path: {result.installation_result.app_path}")
    
    if result.error_messages:
        print("❌ Errors:")
        for error in result.error_messages:
            print(f"   - {error}")
    
    if result.warnings:
        print("⚠️ Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")
    
    # Test batch coordination
    print("\n📦 Testing batch coordination...")
    
    batch_requests = [
        {'name': 'app1', 'source': 'https://github.com/example/app1'},
        {'name': 'app2', 'source': 'https://github.com/example/app2'},
        {'name': 'app3', 'source': 'https://github.com/example/app3'}
    ]
    
    batch_results = coordinator.coordinate_batch_installation(batch_requests)
    
    print(f"✅ Batch coordination: {len(batch_results)} apps processed")
    successful = sum(1 for r in batch_results if r.success)
    print(f"✅ Successful coordinations: {successful}/{len(batch_results)}")
    
    # Test coordination status
    print("\n📊 Testing coordination status...")
    
    status = coordinator.get_coordination_status(result.installation_id)
    print(f"✅ Status retrieval: {status is not None}")
    
    # Test coordination history
    print("\n📋 Testing coordination history...")
    
    history = coordinator.get_coordination_history(limit=10)
    print(f"✅ History retrieval: {len(history)} entries")
    
    return True


if __name__ == "__main__":
    main()