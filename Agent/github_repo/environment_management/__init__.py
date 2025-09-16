#!/usr/bin/env python3
"""
PinokioCloud Environment Management Package

This package provides comprehensive environment management including virtual environments,
file system operations, shell command execution, variable management, and JSON handling
for multi-cloud GPU environments.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

from environment_management.venv_manager import VirtualEnvironmentManager, EnvironmentType, EnvironmentStatus, EnvironmentInfo, EnvironmentOperation
from environment_management.file_system import FileSystemManager, OperationType, OperationStatus, FileOperation, FileInfo
from environment_management.shell_runner import ShellRunner, CommandStatus, CommandResult, CommandProgress
from environment_management.variable_system import VariableSystem, VariableType, VariableScope, Variable, VariableSubstitution
from environment_management.json_handler import JSONHandler, JSONOperationType, JSONValidationLevel, JSONOperation, JSONValidationResult

__version__ = "1.0.0"
__author__ = "PinokioCloud Development Team"

# Re-export the main classes
__all__ = [
    # Virtual Environment Management
    "VirtualEnvironmentManager",
    "EnvironmentType",
    "EnvironmentStatus", 
    "EnvironmentInfo",
    "EnvironmentOperation",
    
    # File System Operations
    "FileSystemManager",
    "OperationType",
    "OperationStatus",
    "FileOperation",
    "FileInfo",
    
    # Shell Command Execution
    "ShellRunner",
    "CommandStatus",
    "CommandResult",
    "CommandProgress",
    
    # Variable Management
    "VariableSystem",
    "VariableType",
    "VariableScope",
    "Variable",
    "VariableSubstitution",
    
    # JSON Operations
    "JSONHandler",
    "JSONOperationType",
    "JSONValidationLevel",
    "JSONOperation",
    "JSONValidationResult"
]