#!/usr/bin/env python3
"""
PinokioCloud Virtual Environment Management System

This module provides comprehensive virtual environment management including
Python venv, conda environments, dependency installation, and environment
isolation for multi-cloud GPU environments.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import subprocess
import shutil
import time
import json
import tempfile
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class EnvironmentType(Enum):
    """Enumeration of environment types."""
    PYTHON_VENV = "python_venv"
    CONDA = "conda"
    SYSTEM = "system"
    DOCKER = "docker"


class EnvironmentStatus(Enum):
    """Enumeration of environment statuses."""
    NOT_CREATED = "not_created"
    CREATING = "creating"
    CREATED = "created"
    ACTIVATING = "activating"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    DEACTIVATED = "deactivated"
    ERROR = "error"
    DESTROYED = "destroyed"


@dataclass
class EnvironmentInfo:
    """Information about a virtual environment."""
    name: str
    env_type: EnvironmentType
    status: EnvironmentStatus
    path: str
    python_version: str
    created_time: float
    last_activated: float
    dependencies: List[str] = field(default_factory=list)
    size_bytes: int = 0
    error_message: Optional[str] = None


@dataclass
class EnvironmentOperation:
    """Information about an environment operation."""
    operation_id: str
    operation_type: str
    environment_name: str
    status: str
    start_time: float
    end_time: Optional[float] = None
    progress_percent: float = 0.0
    current_step: str = ""
    error_message: Optional[str] = None
    output: List[str] = field(default_factory=list)


class VirtualEnvironmentManager:
    """
    Comprehensive virtual environment management system.
    
    Manages Python venv, conda environments, dependency installation,
    and environment isolation for multi-cloud GPU environments.
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the virtual environment manager.
        
        Args:
            base_path: Base path for environment storage
        """
        self.base_path = base_path
        self.environments_path = os.path.join(base_path, "environments")
        self.active_environments = {}
        self.environment_info = {}
        self.operations = {}
        self.progress_callback = None
        
        # Ensure environments directory exists
        os.makedirs(self.environments_path, exist_ok=True)
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def create_environment(self, name: str, env_type: EnvironmentType = EnvironmentType.PYTHON_VENV,
                          python_version: str = "python3", force_recreate: bool = False) -> EnvironmentOperation:
        """
        Create a new virtual environment.
        
        Args:
            name: Environment name
            env_type: Type of environment to create
            python_version: Python version to use
            force_recreate: Force recreation if environment exists
            
        Returns:
            EnvironmentOperation: Operation tracking object
        """
        operation_id = f"create_{name}_{int(time.time())}"
        operation = EnvironmentOperation(
            operation_id=operation_id,
            operation_type="create",
            environment_name=name,
            status="starting",
            start_time=time.time(),
            current_step="Initializing environment creation"
        )
        
        self.operations[operation_id] = operation
        self._update_progress(operation)
        
        try:
            # Check if environment already exists
            env_path = os.path.join(self.environments_path, name)
            if os.path.exists(env_path) and not force_recreate:
                operation.status = "completed"
                operation.end_time = time.time()
                operation.progress_percent = 100.0
                operation.current_step = "Environment already exists"
                self._update_progress(operation)
                return operation
            
            # Remove existing environment if force recreate
            if force_recreate and os.path.exists(env_path):
                operation.current_step = "Removing existing environment"
                operation.progress_percent = 10.0
                self._update_progress(operation)
                shutil.rmtree(env_path)
                time.sleep(2)  # Ensure cleanup is complete
            
            # Create environment based on type
            if env_type == EnvironmentType.PYTHON_VENV:
                success = self._create_python_venv(name, python_version, operation)
            elif env_type == EnvironmentType.CONDA:
                success = self._create_conda_env(name, python_version, operation)
            else:
                raise ValueError(f"Unsupported environment type: {env_type}")
            
            if success:
                operation.status = "completed"
                operation.end_time = time.time()
                operation.progress_percent = 100.0
                operation.current_step = "Environment created successfully"
                
                # Update environment info
                self._update_environment_info(name, env_type, env_path)
            else:
                operation.status = "failed"
                operation.end_time = time.time()
                operation.current_step = "Environment creation failed"
                operation.error_message = "Failed to create environment"
            
            self._update_progress(operation)
            return operation
        
        except Exception as e:
            operation.status = "failed"
            operation.end_time = time.time()
            operation.error_message = str(e)
            operation.current_step = f"Error: {str(e)}"
            self._update_progress(operation)
            return operation
    
    def _create_python_venv(self, name: str, python_version: str, operation: EnvironmentOperation) -> bool:
        """Create a Python virtual environment."""
        try:
            env_path = os.path.join(self.environments_path, name)
            
            operation.current_step = f"Creating Python venv with {python_version}"
            operation.progress_percent = 20.0
            self._update_progress(operation)
            
            # Create virtual environment
            cmd = [python_version, "-m", "venv", env_path]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                operation.error_message = f"Failed to create venv: {result.stderr}"
                return False
            
            operation.current_step = "Installing pip and setuptools"
            operation.progress_percent = 40.0
            self._update_progress(operation)
            
            # Upgrade pip and install setuptools
            pip_path = os.path.join(env_path, "bin", "pip")
            if not os.path.exists(pip_path):
                pip_path = os.path.join(env_path, "Scripts", "pip.exe")
            
            if os.path.exists(pip_path):
                upgrade_cmd = [pip_path, "install", "--upgrade", "pip", "setuptools", "wheel"]
                result = subprocess.run(
                    upgrade_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    operation.error_message = f"Failed to upgrade pip: {result.stderr}"
                    return False
            
            operation.current_step = "Verifying environment"
            operation.progress_percent = 80.0
            self._update_progress(operation)
            
            # Verify environment
            python_path = os.path.join(env_path, "bin", "python")
            if not os.path.exists(python_path):
                python_path = os.path.join(env_path, "Scripts", "python.exe")
            
            if os.path.exists(python_path):
                verify_cmd = [python_path, "--version"]
                result = subprocess.run(
                    verify_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    operation.output.append(f"Python version: {result.stdout.strip()}")
                else:
                    operation.error_message = f"Failed to verify Python: {result.stderr}"
                    return False
            
            operation.current_step = "Environment creation complete"
            operation.progress_percent = 100.0
            self._update_progress(operation)
            
            return True
        
        except subprocess.TimeoutExpired:
            operation.error_message = "Environment creation timed out"
            return False
        except Exception as e:
            operation.error_message = f"Environment creation error: {str(e)}"
            return False
    
    def _create_conda_env(self, name: str, python_version: str, operation: EnvironmentOperation) -> bool:
        """Create a conda environment."""
        try:
            operation.current_step = f"Creating conda environment with Python {python_version}"
            operation.progress_percent = 20.0
            self._update_progress(operation)
            
            # Check if conda is available
            conda_cmd = ["conda", "--version"]
            result = subprocess.run(conda_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                operation.error_message = "Conda is not available on this system"
                return False
            
            operation.current_step = "Creating conda environment"
            operation.progress_percent = 40.0
            self._update_progress(operation)
            
            # Create conda environment
            env_path = os.path.join(self.environments_path, name)
            create_cmd = [
                "conda", "create",
                "--prefix", env_path,
                f"python={python_version}",
                "--yes"
            ]
            
            result = subprocess.run(
                create_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                operation.error_message = f"Failed to create conda environment: {result.stderr}"
                return False
            
            operation.current_step = "Installing conda packages"
            operation.progress_percent = 70.0
            self._update_progress(operation)
            
            # Install essential packages
            install_cmd = [
                "conda", "install",
                "--prefix", env_path,
                "pip", "setuptools", "wheel",
                "--yes"
            ]
            
            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode != 0:
                operation.error_message = f"Failed to install conda packages: {result.stderr}"
                return False
            
            operation.current_step = "Conda environment creation complete"
            operation.progress_percent = 100.0
            self._update_progress(operation)
            
            return True
        
        except subprocess.TimeoutExpired:
            operation.error_message = "Conda environment creation timed out"
            return False
        except Exception as e:
            operation.error_message = f"Conda environment creation error: {str(e)}"
            return False
    
    def activate_environment(self, name: str) -> bool:
        """
        Activate a virtual environment.
        
        Args:
            name: Environment name to activate
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            env_path = os.path.join(self.environments_path, name)
            
            if not os.path.exists(env_path):
                return False
            
            # Update environment info
            if name in self.environment_info:
                self.environment_info[name].status = EnvironmentStatus.ACTIVE
                self.environment_info[name].last_activated = time.time()
            
            # Store activation info
            self.active_environments[name] = {
                "path": env_path,
                "activated_time": time.time(),
                "python_path": self._get_python_path(env_path),
                "pip_path": self._get_pip_path(env_path)
            }
            
            return True
        
        except Exception as e:
            return False
    
    def deactivate_environment(self, name: str) -> bool:
        """
        Deactivate a virtual environment.
        
        Args:
            name: Environment name to deactivate
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if name in self.active_environments:
                del self.active_environments[name]
            
            # Update environment info
            if name in self.environment_info:
                self.environment_info[name].status = EnvironmentStatus.DEACTIVATED
            
            return True
        
        except Exception as e:
            return False
    
    def install_dependencies(self, name: str, dependencies: List[str], 
                           requirements_file: Optional[str] = None) -> EnvironmentOperation:
        """
        Install dependencies in an environment.
        
        Args:
            name: Environment name
            dependencies: List of dependencies to install
            requirements_file: Optional requirements file path
            
        Returns:
            EnvironmentOperation: Operation tracking object
        """
        operation_id = f"install_{name}_{int(time.time())}"
        operation = EnvironmentOperation(
            operation_id=operation_id,
            operation_type="install",
            environment_name=name,
            status="starting",
            start_time=time.time(),
            current_step="Preparing dependency installation"
        )
        
        self.operations[operation_id] = operation
        self._update_progress(operation)
        
        try:
            if name not in self.active_environments:
                operation.error_message = f"Environment {name} is not active"
                operation.status = "failed"
                operation.end_time = time.time()
                return operation
            
            env_info = self.active_environments[name]
            pip_path = env_info["pip_path"]
            
            if not os.path.exists(pip_path):
                operation.error_message = f"Pip not found in environment {name}"
                operation.status = "failed"
                operation.end_time = time.time()
                return operation
            
            # Install from requirements file if provided
            if requirements_file and os.path.exists(requirements_file):
                operation.current_step = f"Installing from requirements file: {requirements_file}"
                operation.progress_percent = 20.0
                self._update_progress(operation)
                
                cmd = [pip_path, "install", "-r", requirements_file]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result.returncode != 0:
                    operation.error_message = f"Failed to install from requirements: {result.stderr}"
                    operation.status = "failed"
                    operation.end_time = time.time()
                    return operation
                
                operation.output.extend(result.stdout.split('\n'))
            
            # Install individual dependencies
            if dependencies:
                operation.current_step = f"Installing {len(dependencies)} dependencies"
                operation.progress_percent = 50.0
                self._update_progress(operation)
                
                for i, dep in enumerate(dependencies):
                    operation.current_step = f"Installing {dep} ({i+1}/{len(dependencies)})"
                    operation.progress_percent = 50.0 + (i / len(dependencies)) * 40.0
                    self._update_progress(operation)
                    
                    cmd = [pip_path, "install", dep]
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode != 0:
                        operation.error_message = f"Failed to install {dep}: {result.stderr}"
                        operation.status = "failed"
                        operation.end_time = time.time()
                        return operation
                    
                    operation.output.append(f"Installed {dep}")
            
            operation.status = "completed"
            operation.end_time = time.time()
            operation.progress_percent = 100.0
            operation.current_step = "Dependency installation complete"
            self._update_progress(operation)
            
            return operation
        
        except subprocess.TimeoutExpired:
            operation.error_message = "Dependency installation timed out"
            operation.status = "failed"
            operation.end_time = time.time()
            self._update_progress(operation)
            return operation
        except Exception as e:
            operation.error_message = f"Dependency installation error: {str(e)}"
            operation.status = "failed"
            operation.end_time = time.time()
            self._update_progress(operation)
            return operation
    
    def destroy_environment(self, name: str) -> bool:
        """
        Destroy a virtual environment.
        
        Args:
            name: Environment name to destroy
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            env_path = os.path.join(self.environments_path, name)
            
            if not os.path.exists(env_path):
                return True  # Already doesn't exist
            
            # Deactivate if active
            if name in self.active_environments:
                self.deactivate_environment(name)
            
            # Remove environment directory
            shutil.rmtree(env_path)
            
            # Update environment info
            if name in self.environment_info:
                self.environment_info[name].status = EnvironmentStatus.DESTROYED
            
            return True
        
        except Exception as e:
            return False
    
    def list_environments(self) -> List[EnvironmentInfo]:
        """
        List all available environments.
        
        Returns:
            List of EnvironmentInfo objects
        """
        environments = []
        
        try:
            if not os.path.exists(self.environments_path):
                return environments
            
            for item in os.listdir(self.environments_path):
                env_path = os.path.join(self.environments_path, item)
                
                if os.path.isdir(env_path):
                    env_info = self._get_environment_info(item, env_path)
                    if env_info:
                        environments.append(env_info)
        
        except Exception as e:
            pass
        
        return environments
    
    def get_environment_info(self, name: str) -> Optional[EnvironmentInfo]:
        """
        Get information about a specific environment.
        
        Args:
            name: Environment name
            
        Returns:
            EnvironmentInfo or None if not found
        """
        env_path = os.path.join(self.environments_path, name)
        
        if not os.path.exists(env_path):
            return None
        
        return self._get_environment_info(name, env_path)
    
    def _get_environment_info(self, name: str, env_path: str) -> Optional[EnvironmentInfo]:
        """Get environment information from path."""
        try:
            # Determine environment type
            env_type = EnvironmentType.PYTHON_VENV
            if os.path.exists(os.path.join(env_path, "conda-meta")):
                env_type = EnvironmentType.CONDA
            
            # Get Python version
            python_path = self._get_python_path(env_path)
            python_version = "unknown"
            
            if python_path and os.path.exists(python_path):
                result = subprocess.run(
                    [python_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    python_version = result.stdout.strip()
            
            # Get dependencies
            dependencies = []
            pip_path = self._get_pip_path(env_path)
            
            if pip_path and os.path.exists(pip_path):
                result = subprocess.run(
                    [pip_path, "list", "--format=json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    try:
                        packages = json.loads(result.stdout)
                        dependencies = [pkg["name"] for pkg in packages]
                    except:
                        pass
            
            # Get directory size
            size_bytes = self._get_directory_size(env_path)
            
            # Get status
            status = EnvironmentStatus.CREATED
            if name in self.active_environments:
                status = EnvironmentStatus.ACTIVE
            
            return EnvironmentInfo(
                name=name,
                env_type=env_type,
                status=status,
                path=env_path,
                python_version=python_version,
                created_time=os.path.getctime(env_path),
                last_activated=0.0,
                dependencies=dependencies,
                size_bytes=size_bytes
            )
        
        except Exception as e:
            return None
    
    def _get_python_path(self, env_path: str) -> Optional[str]:
        """Get Python executable path for environment."""
        python_paths = [
            os.path.join(env_path, "bin", "python"),
            os.path.join(env_path, "bin", "python3"),
            os.path.join(env_path, "Scripts", "python.exe"),
            os.path.join(env_path, "Scripts", "python3.exe")
        ]
        
        for path in python_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _get_pip_path(self, env_path: str) -> Optional[str]:
        """Get pip executable path for environment."""
        pip_paths = [
            os.path.join(env_path, "bin", "pip"),
            os.path.join(env_path, "bin", "pip3"),
            os.path.join(env_path, "Scripts", "pip.exe"),
            os.path.join(env_path, "Scripts", "pip3.exe")
        ]
        
        for path in pip_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _get_directory_size(self, directory: str) -> int:
        """Get total size of directory in bytes."""
        total_size = 0
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        pass
        except:
            pass
        
        return total_size
    
    def _update_environment_info(self, name: str, env_type: EnvironmentType, env_path: str):
        """Update environment information."""
        env_info = self._get_environment_info(name, env_path)
        if env_info:
            self.environment_info[name] = env_info
    
    def _update_progress(self, operation: EnvironmentOperation):
        """Update operation progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(operation)
            except:
                pass
    
    def get_operation_status(self, operation_id: str) -> Optional[EnvironmentOperation]:
        """Get status of an operation."""
        return self.operations.get(operation_id)
    
    def get_active_environments(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active environments."""
        return self.active_environments.copy()
    
    def cleanup_old_operations(self, max_age_hours: int = 24):
        """Clean up old operation records."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        operations_to_remove = []
        for op_id, operation in self.operations.items():
            if current_time - operation.start_time > max_age_seconds:
                operations_to_remove.append(op_id)
        
        for op_id in operations_to_remove:
            del self.operations[op_id]


def main():
    """Main function for testing virtual environment management."""
    print("🧪 Testing Virtual Environment Manager")
    print("=" * 50)
    
    # Initialize manager
    manager = VirtualEnvironmentManager()
    
    # Set up progress callback
    def progress_callback(operation):
        print(f"  {operation.current_step}: {operation.progress_percent:.1f}%")
    
    manager.set_progress_callback(progress_callback)
    
    # Test environment creation
    print("\n📦 Creating test environment...")
    operation = manager.create_environment("test_env", force_recreate=True)
    
    if operation.status == "completed":
        print(f"✅ Environment created successfully")
        
        # Test activation
        print("\n🔄 Activating environment...")
        if manager.activate_environment("test_env"):
            print("✅ Environment activated")
            
            # Test dependency installation
            print("\n📥 Installing test dependencies...")
            install_op = manager.install_dependencies("test_env", ["requests", "numpy"])
            
            if install_op.status == "completed":
                print("✅ Dependencies installed")
            else:
                print(f"❌ Dependency installation failed: {install_op.error_message}")
            
            # Test deactivation
            print("\n🔄 Deactivating environment...")
            if manager.deactivate_environment("test_env"):
                print("✅ Environment deactivated")
        
        # Test environment listing
        print("\n📋 Listing environments...")
        environments = manager.list_environments()
        for env in environments:
            print(f"  - {env.name}: {env.env_type.value} ({env.status.value})")
        
        # Test cleanup
        print("\n🗑️  Cleaning up test environment...")
        if manager.destroy_environment("test_env"):
            print("✅ Environment destroyed")
    
    else:
        print(f"❌ Environment creation failed: {operation.error_message}")
    
    return True


if __name__ == "__main__":
    main()