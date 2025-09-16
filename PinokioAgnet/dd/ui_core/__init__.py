#!/usr/bin/env python3
"""
PinokioCloud Core UI Package

This package provides the core Streamlit web interface for PinokioCloud,
meeting all Phase 11 objectives with essential modern Streamlit features.

Author: PinokioCloud Development Team
Version: 1.0.0 (Core)
"""

from ui_core.streamlit_app import PinokioCloudApp
from ui_core.terminal_widget import TerminalWidget
from ui_core.app_gallery import AppGallery
from ui_core.resource_monitor import ResourceMonitor
from ui_core.tunnel_dashboard import TunnelDashboard

__version__ = "1.0.0-core"
__author__ = "PinokioCloud Development Team"

# Re-export the main classes
__all__ = [
    # Main Application
    "PinokioCloudApp",
    
    # UI Components
    "TerminalWidget",
    "AppGallery", 
    "ResourceMonitor",
    "TunnelDashboard"
]