"""
PinokioCloud Running Engine - Phase 6

This package contains the application running engine that manages running Pinokio applications.
It provides process management, health monitoring, daemon handling, and virtual storage capabilities.

Author: PinokioCloud Development Team
Version: 1.0.0
Phase: 6 - Application Running Engine
"""

from running.script_manager import ScriptManager, ProcessInfo, ApplicationRunningStatus
from running.process_tracker import ProcessTracker, ResourceUsage
from running.daemon_manager import DaemonManager, DaemonInfo, DaemonHealth
from running.health_monitor import HealthMonitor, HealthStatus
from running.virtual_drive import VirtualDrive, VirtualDriveManager

__all__ = [
    'ScriptManager',
    'ProcessInfo', 
    'ApplicationRunningStatus',
    'ProcessTracker',
    'ResourceUsage',
    'DaemonManager',
    'DaemonInfo',
    'DaemonHealth',
    'HealthMonitor',
    'HealthStatus',
    'VirtualDrive',
    'VirtualDriveManager'
]

__version__ = "1.0.0"
__phase__ = "6"
__description__ = "Application Running Engine for PinokioCloud"