#!/usr/bin/env python3
"""
PinokioCloud Engine Package

This package contains the core engine components for application installation,
script parsing, input handling, state management, and installation coordination.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

from .installer import ApplicationInstaller, InstallationResult, InstallationStatus
from .script_parser import ScriptParser, ScriptExecutionResult, ScriptType
from .input_handler import InputHandler, FormResult, FormDefinition, InputType
from .state_manager import StateManager, ApplicationState, InstallationState, ApplicationStatus
from .installation_coordinator import InstallationCoordinator, CoordinationResult, CoordinationStatus

__all__ = [
    # Installer
    'ApplicationInstaller',
    'InstallationResult',
    'InstallationStatus',
    
    # Script Parser
    'ScriptParser',
    'ScriptExecutionResult',
    'ScriptType',
    
    # Input Handler
    'InputHandler',
    'FormResult',
    'FormDefinition',
    'InputType',
    
    # State Manager
    'StateManager',
    'ApplicationState',
    'InstallationState',
    'ApplicationStatus',
    
    # Installation Coordinator
    'InstallationCoordinator',
    'CoordinationResult',
    'CoordinationStatus'
]

__version__ = "1.0.0"
__author__ = "PinokioCloud Development Team"