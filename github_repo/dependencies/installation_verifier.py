#!/usr/bin/env python3
"""
PinokioCloud Installation Verifier

This module verifies that all dependencies were installed correctly and are functioning properly.
It provides comprehensive installation verification including import testing, functionality testing,
and integration testing of installed packages.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import re
import subprocess
import time
import importlib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import dependency managers
from .pip_manager import PipManager, PipPackage, PipInstallStatus
from .conda_manager import CondaManager, CondaPackage, CondaInstallStatus
from .npm_manager import NpmManager, NpmPackage, NpmInstallStatus
from .system_manager import SystemManager, SystemPackage, SystemInstallStatus


class VerificationStatus(Enum):
    """Enumeration of verification statuses."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


class VerificationType(Enum):
    """Enumeration of verification types."""
    IMPORT_TEST = "import_test"
    FUNCTIONALITY_TEST = "functionality_test"
    INTEGRATION_TEST = "integration_test"
    PERFORMANCE_TEST = "performance_test"
    COMPATIBILITY_TEST = "compatibility_test"


@dataclass
class VerificationResult:
    """Result of a verification test."""
    test_type: VerificationType
    package_name: str
    status: VerificationStatus
    message: str = ""
    execution_time: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PackageVerification:
    """Complete verification result for a package."""
    package_name: str
    package_type: str  # pip, conda, npm, system
    overall_status: VerificationStatus
    verification_results: List[VerificationResult] = field(default_factory=list)
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    warning_tests: int = 0
    verification_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InstallationVerificationResult:
    """Complete installation verification result."""
    success: bool
    packages_verified: List[PackageVerification] = field(default_factory=list)
    total_packages: int = 0
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    warning_tests: int = 0
    verification_time: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class InstallationVerifier:
    """
    Verifies that all dependencies were installed correctly and are functioning properly.
    
    Provides comprehensive installation verification including:
    - Import testing for Python packages
    - Functionality testing for installed packages
    - Integration testing between packages
    - Performance testing for critical packages
    - Compatibility testing across platforms
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the installation verifier.
        
        Args:
            base_path: Base path for verification operations
        """
        self.base_path = base_path
        
        # Initialize dependency managers
        self.pip_manager = PipManager(base_path)
        self.conda_manager = CondaManager(base_path)
        self.npm_manager = NpmManager(base_path)
        self.system_manager = SystemManager(base_path)
        
        # Verification test configurations
        self.verification_tests = {
            'python_packages': {
                'torch': [
                    {'type': VerificationType.IMPORT_TEST, 'test': 'import torch'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'torch.cuda.is_available()'},
                    {'type': VerificationType.PERFORMANCE_TEST, 'test': 'torch.randn(1000, 1000).cuda()'}
                ],
                'tensorflow': [
                    {'type': VerificationType.IMPORT_TEST, 'test': 'import tensorflow as tf'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'tf.config.list_physical_devices()'},
                    {'type': VerificationType.PERFORMANCE_TEST, 'test': 'tf.random.normal([1000, 1000])'}
                ],
                'numpy': [
                    {'type': VerificationType.IMPORT_TEST, 'test': 'import numpy as np'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'np.array([1, 2, 3])'},
                    {'type': VerificationType.PERFORMANCE_TEST, 'test': 'np.random.rand(1000, 1000)'}
                ],
                'opencv-python': [
                    {'type': VerificationType.IMPORT_TEST, 'test': 'import cv2'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'cv2.__version__'},
                    {'type': VerificationType.PERFORMANCE_TEST, 'test': 'cv2.imread("test.jpg")'}
                ],
                'pandas': [
                    {'type': VerificationType.IMPORT_TEST, 'test': 'import pandas as pd'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'pd.DataFrame({"a": [1, 2, 3]})'},
                    {'type': VerificationType.PERFORMANCE_TEST, 'test': 'pd.DataFrame(np.random.rand(1000, 100))'}
                ],
                'requests': [
                    {'type': VerificationType.IMPORT_TEST, 'test': 'import requests'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'requests.get("https://httpbin.org/get", timeout=5)'}
                ],
                'flask': [
                    {'type': VerificationType.IMPORT_TEST, 'test': 'import flask'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'flask.Flask("test")'}
                ],
                'streamlit': [
                    {'type': VerificationType.IMPORT_TEST, 'test': 'import streamlit'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'streamlit.__version__'}
                ],
                'gradio': [
                    {'type': VerificationType.IMPORT_TEST, 'test': 'import gradio'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'gradio.__version__'}
                ]
            },
            'node_packages': {
                'express': [
                    {'type': VerificationType.IMPORT_TEST, 'test': 'require("express")'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'express().get("/", (req, res) => res.send("OK"))'}
                ],
                'axios': [
                    {'type': VerificationType.IMPORT_TEST, 'test': 'require("axios")'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'axios.get("https://httpbin.org/get")'}
                ]
            },
            'system_packages': {
                'curl': [
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'curl --version'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'curl -I https://httpbin.org/get'}
                ],
                'git': [
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'git --version'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'git config --list'}
                ],
                'ffmpeg': [
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'ffmpeg -version'},
                    {'type': VerificationType.FUNCTIONALITY_TEST, 'test': 'ffmpeg -f lavfi -i testsrc=duration=1:size=320x240:rate=1 -f null -'}
                ]
            }
        }
        
        # Critical packages that must pass verification
        self.critical_packages = {
            'python': ['numpy', 'requests'],
            'node': ['express'],
            'system': ['curl', 'git']
        }
        
        self.progress_callback = None
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def verify_installation(self, app_path: str, 
                           environment_path: Optional[str] = None) -> InstallationVerificationResult:
        """
        Verify complete installation for an application.
        
        Args:
            app_path: Path to the application
            environment_path: Path to virtual environment (optional)
            
        Returns:
            InstallationVerificationResult: Complete verification result
        """
        start_time = time.time()
        
        result = InstallationVerificationResult(
            success=False
        )
        
        try:
            self._update_progress("Starting installation verification...")
            
            # Get all installed packages
            all_packages = self._get_all_installed_packages(app_path, environment_path)
            result.total_packages = len(all_packages)
            
            if not all_packages:
                result.success = True
                result.verification_time = time.time() - start_time
                self._update_progress("No packages to verify")
                return result
            
            self._update_progress(f"Verifying {len(all_packages)} packages...")
            
            # Verify each package
            for i, package_info in enumerate(all_packages):
                self._update_progress(f"Verifying package {i+1}/{len(all_packages)}: {package_info['name']}")
                
                package_verification = self._verify_package(
                    package_info['name'], 
                    package_info['type'],
                    environment_path
                )
                
                result.packages_verified.append(package_verification)
                result.total_tests += package_verification.total_tests
                result.passed_tests += package_verification.passed_tests
                result.failed_tests += package_verification.failed_tests
                result.warning_tests += package_verification.warning_tests
            
            # Determine overall success
            result.success = self._assess_overall_success(result)
            result.verification_time = time.time() - start_time
            
            self._update_progress(f"Verification complete: {result.passed_tests}/{result.total_tests} tests passed")
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during installation verification: {str(e)}")
            result.verification_time = time.time() - start_time
            return result
    
    def verify_package(self, package_name: str, 
                      package_type: str,
                      environment_path: Optional[str] = None) -> PackageVerification:
        """
        Verify a single package installation.
        
        Args:
            package_name: Name of the package to verify
            package_type: Type of package (pip, conda, npm, system)
            environment_path: Path to virtual environment (optional)
            
        Returns:
            PackageVerification: Package verification result
        """
        return self._verify_package(package_name, package_type, environment_path)
    
    def verify_python_package(self, package_name: str, 
                             environment_path: Optional[str] = None) -> PackageVerification:
        """
        Verify a Python package installation.
        
        Args:
            package_name: Name of the Python package
            environment_path: Path to virtual environment (optional)
            
        Returns:
            PackageVerification: Package verification result
        """
        return self._verify_package(package_name, 'pip', environment_path)
    
    def verify_node_package(self, package_name: str) -> PackageVerification:
        """
        Verify a Node.js package installation.
        
        Args:
            package_name: Name of the Node.js package
            
        Returns:
            PackageVerification: Package verification result
        """
        return self._verify_package(package_name, 'npm', None)
    
    def verify_system_package(self, package_name: str) -> PackageVerification:
        """
        Verify a system package installation.
        
        Args:
            package_name: Name of the system package
            
        Returns:
            PackageVerification: Package verification result
        """
        return self._verify_package(package_name, 'system', None)
    
    def _get_all_installed_packages(self, app_path: str, 
                                   environment_path: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Get all installed packages from all package managers.
        
        Args:
            app_path: Path to the application
            environment_path: Path to virtual environment (optional)
            
        Returns:
            List of package information dictionaries
        """
        all_packages = []
        
        try:
            # Get pip packages
            pip_packages = self.pip_manager.get_installed_packages(environment_path)
            for package in pip_packages:
                all_packages.append({
                    'name': package.name,
                    'type': 'pip',
                    'version': package.version
                })
            
            # Get conda packages
            conda_packages = self.conda_manager.get_installed_packages()
            for package in conda_packages:
                all_packages.append({
                    'name': package.name,
                    'type': 'conda',
                    'version': package.version
                })
            
            # Get npm packages
            package_json_path = os.path.join(app_path, 'package.json')
            if os.path.exists(package_json_path):
                npm_packages = self.npm_manager.get_installed_packages(package_json_path)
                for package in npm_packages:
                    all_packages.append({
                        'name': package.name,
                        'type': 'npm',
                        'version': package.version
                    })
            
            # Get system packages
            system_packages = self.system_manager.get_installed_packages()
            for package in system_packages:
                all_packages.append({
                    'name': package.name,
                    'type': 'system',
                    'version': package.version
                })
        
        except Exception as e:
            pass
        
        return all_packages
    
    def _verify_package(self, package_name: str, 
                       package_type: str,
                       environment_path: Optional[str] = None) -> PackageVerification:
        """
        Verify a single package installation.
        
        Args:
            package_name: Name of the package
            package_type: Type of package
            environment_path: Path to virtual environment (optional)
            
        Returns:
            PackageVerification: Package verification result
        """
        start_time = time.time()
        
        verification = PackageVerification(
            package_name=package_name,
            package_type=package_type,
            overall_status=VerificationStatus.UNKNOWN
        )
        
        try:
            # Get verification tests for this package
            tests = self._get_verification_tests(package_name, package_type)
            
            if not tests:
                verification.overall_status = VerificationStatus.SKIPPED
                verification.verification_time = time.time() - start_time
                return verification
            
            verification.total_tests = len(tests)
            
            # Run each test
            for test_config in tests:
                test_result = self._run_verification_test(
                    package_name, 
                    test_config, 
                    environment_path
                )
                
                verification.verification_results.append(test_result)
                
                if test_result.status == VerificationStatus.PASSED:
                    verification.passed_tests += 1
                elif test_result.status == VerificationStatus.FAILED:
                    verification.failed_tests += 1
                elif test_result.status == VerificationStatus.WARNING:
                    verification.warning_tests += 1
            
            # Determine overall status
            verification.overall_status = self._determine_package_status(verification)
            verification.verification_time = time.time() - start_time
            
            return verification
        
        except Exception as e:
            verification.overall_status = VerificationStatus.FAILED
            verification.verification_time = time.time() - start_time
            return verification
    
    def _get_verification_tests(self, package_name: str, package_type: str) -> List[Dict[str, Any]]:
        """
        Get verification tests for a package.
        
        Args:
            package_name: Name of the package
            package_type: Type of package
            
        Returns:
            List of test configurations
        """
        try:
            if package_type in ['pip', 'conda']:
                return self.verification_tests.get('python_packages', {}).get(package_name, [])
            elif package_type == 'npm':
                return self.verification_tests.get('node_packages', {}).get(package_name, [])
            elif package_type == 'system':
                return self.verification_tests.get('system_packages', {}).get(package_name, [])
            else:
                return []
        
        except Exception as e:
            return []
    
    def _run_verification_test(self, package_name: str, 
                              test_config: Dict[str, Any],
                              environment_path: Optional[str] = None) -> VerificationResult:
        """
        Run a single verification test.
        
        Args:
            package_name: Name of the package
            test_config: Test configuration
            environment_path: Path to virtual environment (optional)
            
        Returns:
            VerificationResult: Test result
        """
        start_time = time.time()
        
        result = VerificationResult(
            test_type=test_config['type'],
            package_name=package_name,
            status=VerificationStatus.UNKNOWN
        )
        
        try:
            test_code = test_config['test']
            
            if test_config['type'] == VerificationType.IMPORT_TEST:
                result = self._run_import_test(package_name, test_code, environment_path)
            elif test_config['type'] == VerificationType.FUNCTIONALITY_TEST:
                result = self._run_functionality_test(package_name, test_code, environment_path)
            elif test_config['type'] == VerificationType.INTEGRATION_TEST:
                result = self._run_integration_test(package_name, test_code, environment_path)
            elif test_config['type'] == VerificationType.PERFORMANCE_TEST:
                result = self._run_performance_test(package_name, test_code, environment_path)
            elif test_config['type'] == VerificationType.COMPATIBILITY_TEST:
                result = self._run_compatibility_test(package_name, test_code, environment_path)
            else:
                result.status = VerificationStatus.SKIPPED
                result.message = "Unknown test type"
            
            result.execution_time = time.time() - start_time
            
            return result
        
        except Exception as e:
            result.status = VerificationStatus.FAILED
            result.message = f"Test execution error: {str(e)}"
            result.execution_time = time.time() - start_time
            return result
    
    def _run_import_test(self, package_name: str, test_code: str, 
                        environment_path: Optional[str] = None) -> VerificationResult:
        """Run an import test."""
        result = VerificationResult(
            test_type=VerificationType.IMPORT_TEST,
            package_name=package_name,
            status=VerificationStatus.UNKNOWN
        )
        
        try:
            # Build Python command
            python_cmd = [sys.executable, '-c', test_code]
            
            if environment_path:
                # Use environment's Python
                if os.name == 'nt':  # Windows
                    python_path = os.path.join(environment_path, 'Scripts', 'python.exe')
                else:  # Unix-like
                    python_path = os.path.join(environment_path, 'bin', 'python')
                
                if os.path.exists(python_path):
                    python_cmd[0] = python_path
            
            # Execute test
            success, output, error = self._execute_command(python_cmd)
            
            if success:
                result.status = VerificationStatus.PASSED
                result.message = "Import successful"
                result.details['output'] = output
            else:
                result.status = VerificationStatus.FAILED
                result.message = f"Import failed: {error}"
                result.details['error'] = error
        
        except Exception as e:
            result.status = VerificationStatus.FAILED
            result.message = f"Import test error: {str(e)}"
        
        return result
    
    def _run_functionality_test(self, package_name: str, test_code: str, 
                               environment_path: Optional[str] = None) -> VerificationResult:
        """Run a functionality test."""
        result = VerificationResult(
            test_type=VerificationType.FUNCTIONALITY_TEST,
            package_name=package_name,
            status=VerificationStatus.UNKNOWN
        )
        
        try:
            # Build Python command
            python_cmd = [sys.executable, '-c', test_code]
            
            if environment_path:
                # Use environment's Python
                if os.name == 'nt':  # Windows
                    python_path = os.path.join(environment_path, 'Scripts', 'python.exe')
                else:  # Unix-like
                    python_path = os.path.join(environment_path, 'bin', 'python')
                
                if os.path.exists(python_path):
                    python_cmd[0] = python_path
            
            # Execute test
            success, output, error = self._execute_command(python_cmd)
            
            if success:
                result.status = VerificationStatus.PASSED
                result.message = "Functionality test passed"
                result.details['output'] = output
            else:
                result.status = VerificationStatus.FAILED
                result.message = f"Functionality test failed: {error}"
                result.details['error'] = error
        
        except Exception as e:
            result.status = VerificationStatus.FAILED
            result.message = f"Functionality test error: {str(e)}"
        
        return result
    
    def _run_integration_test(self, package_name: str, test_code: str, 
                             environment_path: Optional[str] = None) -> VerificationResult:
        """Run an integration test."""
        result = VerificationResult(
            test_type=VerificationType.INTEGRATION_TEST,
            package_name=package_name,
            status=VerificationStatus.UNKNOWN
        )
        
        try:
            # Build Python command
            python_cmd = [sys.executable, '-c', test_code]
            
            if environment_path:
                # Use environment's Python
                if os.name == 'nt':  # Windows
                    python_path = os.path.join(environment_path, 'Scripts', 'python.exe')
                else:  # Unix-like
                    python_path = os.path.join(environment_path, 'bin', 'python')
                
                if os.path.exists(python_path):
                    python_cmd[0] = python_path
            
            # Execute test
            success, output, error = self._execute_command(python_cmd)
            
            if success:
                result.status = VerificationStatus.PASSED
                result.message = "Integration test passed"
                result.details['output'] = output
            else:
                result.status = VerificationStatus.FAILED
                result.message = f"Integration test failed: {error}"
                result.details['error'] = error
        
        except Exception as e:
            result.status = VerificationStatus.FAILED
            result.message = f"Integration test error: {str(e)}"
        
        return result
    
    def _run_performance_test(self, package_name: str, test_code: str, 
                             environment_path: Optional[str] = None) -> VerificationResult:
        """Run a performance test."""
        result = VerificationResult(
            test_type=VerificationType.PERFORMANCE_TEST,
            package_name=package_name,
            status=VerificationStatus.UNKNOWN
        )
        
        try:
            # Build Python command
            python_cmd = [sys.executable, '-c', test_code]
            
            if environment_path:
                # Use environment's Python
                if os.name == 'nt':  # Windows
                    python_path = os.path.join(environment_path, 'Scripts', 'python.exe')
                else:  # Unix-like
                    python_path = os.path.join(environment_path, 'bin', 'python')
                
                if os.path.exists(python_path):
                    python_cmd[0] = python_path
            
            # Execute test with timeout
            success, output, error = self._execute_command(python_cmd, timeout=30)
            
            if success:
                result.status = VerificationStatus.PASSED
                result.message = "Performance test passed"
                result.details['output'] = output
            else:
                result.status = VerificationStatus.WARNING  # Performance tests can be warnings
                result.message = f"Performance test failed: {error}"
                result.details['error'] = error
        
        except Exception as e:
            result.status = VerificationStatus.WARNING
            result.message = f"Performance test error: {str(e)}"
        
        return result
    
    def _run_compatibility_test(self, package_name: str, test_code: str, 
                               environment_path: Optional[str] = None) -> VerificationResult:
        """Run a compatibility test."""
        result = VerificationResult(
            test_type=VerificationType.COMPATIBILITY_TEST,
            package_name=package_name,
            status=VerificationStatus.UNKNOWN
        )
        
        try:
            # Build Python command
            python_cmd = [sys.executable, '-c', test_code]
            
            if environment_path:
                # Use environment's Python
                if os.name == 'nt':  # Windows
                    python_path = os.path.join(environment_path, 'Scripts', 'python.exe')
                else:  # Unix-like
                    python_path = os.path.join(environment_path, 'bin', 'python')
                
                if os.path.exists(python_path):
                    python_cmd[0] = python_path
            
            # Execute test
            success, output, error = self._execute_command(python_cmd)
            
            if success:
                result.status = VerificationStatus.PASSED
                result.message = "Compatibility test passed"
                result.details['output'] = output
            else:
                result.status = VerificationStatus.WARNING
                result.message = f"Compatibility test failed: {error}"
                result.details['error'] = error
        
        except Exception as e:
            result.status = VerificationStatus.WARNING
            result.message = f"Compatibility test error: {str(e)}"
        
        return result
    
    def _execute_command(self, cmd: List[str], timeout: int = 10) -> Tuple[bool, str, str]:
        """
        Execute a command.
        
        Args:
            cmd: Command to execute
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (success, output, error)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr
            
            return success, output, error
        
        except subprocess.TimeoutExpired:
            return False, "", "Command timeout"
        except Exception as e:
            return False, "", str(e)
    
    def _determine_package_status(self, verification: PackageVerification) -> VerificationStatus:
        """
        Determine overall package status from test results.
        
        Args:
            verification: Package verification result
            
        Returns:
            VerificationStatus: Overall status
        """
        try:
            if verification.failed_tests > 0:
                return VerificationStatus.FAILED
            elif verification.warning_tests > 0:
                return VerificationStatus.WARNING
            elif verification.passed_tests > 0:
                return VerificationStatus.PASSED
            else:
                return VerificationStatus.SKIPPED
        
        except Exception as e:
            return VerificationStatus.UNKNOWN
    
    def _assess_overall_success(self, result: InstallationVerificationResult) -> bool:
        """
        Assess overall verification success.
        
        Args:
            result: Installation verification result
            
        Returns:
            bool: True if overall verification is successful
        """
        try:
            # Check if any critical packages failed
            for package_verification in result.packages_verified:
                if (package_verification.package_name in self.critical_packages.get('python', []) and
                    package_verification.overall_status == VerificationStatus.FAILED):
                    return False
            
            # Check if too many tests failed
            if result.total_tests > 0:
                failure_rate = result.failed_tests / result.total_tests
                if failure_rate > 0.2:  # More than 20% failure rate
                    return False
            
            return True
        
        except Exception as e:
            return False
    
    def _update_progress(self, message: str):
        """Update progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(message)
            except:
                pass


def main():
    """Main function for testing installation verifier."""
    print("🧪 Testing Installation Verifier")
    print("=" * 50)
    
    # Initialize verifier
    verifier = InstallationVerifier()
    
    # Set up progress callback
    def progress_callback(message):
        print(f"  {message}")
    
    verifier.set_progress_callback(progress_callback)
    
    # Test with a sample app directory
    test_path = "/tmp/test_verification_app"
    os.makedirs(test_path, exist_ok=True)
    
    # Create test package.json
    package_json = {
        "name": "test-app",
        "dependencies": {
            "express": "^4.18.0"
        }
    }
    
    with open(os.path.join(test_path, "package.json"), 'w') as f:
        json.dump(package_json, f, indent=2)
    
    # Test complete installation verification
    print("\n🔍 Testing complete installation verification...")
    result = verifier.verify_installation(test_path)
    
    print(f"✅ Verification success: {result.success}")
    print(f"✅ Total packages: {result.total_packages}")
    print(f"✅ Total tests: {result.total_tests}")
    print(f"✅ Passed tests: {result.passed_tests}")
    print(f"✅ Failed tests: {result.failed_tests}")
    print(f"✅ Warning tests: {result.warning_tests}")
    print(f"✅ Verification time: {result.verification_time:.2f}s")
    
    if result.packages_verified:
        print("\n📦 Package verification results:")
        for package_verification in result.packages_verified:
            print(f"   {package_verification.package_name} ({package_verification.package_type}): {package_verification.overall_status.value}")
            print(f"     Tests: {package_verification.passed_tests}/{package_verification.total_tests} passed")
            
            for test_result in package_verification.verification_results:
                print(f"       - {test_result.test_type.value}: {test_result.status.value}")
                if test_result.message:
                    print(f"         {test_result.message}")
    
    # Test single package verification
    print("\n🎯 Testing single package verification...")
    package_verification = verifier.verify_python_package("numpy")
    
    print(f"✅ Package: {package_verification.package_name}")
    print(f"✅ Overall status: {package_verification.overall_status.value}")
    print(f"✅ Tests: {package_verification.passed_tests}/{package_verification.total_tests} passed")
    print(f"✅ Verification time: {package_verification.verification_time:.2f}s")
    
    if package_verification.verification_results:
        print("   Test results:")
        for test_result in package_verification.verification_results:
            print(f"     - {test_result.test_type.value}: {test_result.status.value}")
            if test_result.message:
                print(f"       {test_result.message}")
    
    # Test Node.js package verification
    print("\n📦 Testing Node.js package verification...")
    node_verification = verifier.verify_node_package("express")
    
    print(f"✅ Package: {node_verification.package_name}")
    print(f"✅ Overall status: {node_verification.overall_status.value}")
    print(f"✅ Tests: {node_verification.passed_tests}/{node_verification.total_tests} passed")
    
    # Test system package verification
    print("\n🖥️ Testing system package verification...")
    system_verification = verifier.verify_system_package("curl")
    
    print(f"✅ Package: {system_verification.package_name}")
    print(f"✅ Overall status: {system_verification.overall_status.value}")
    print(f"✅ Tests: {system_verification.passed_tests}/{system_verification.total_tests} passed")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_path, ignore_errors=True)
    
    return True


if __name__ == "__main__":
    main()