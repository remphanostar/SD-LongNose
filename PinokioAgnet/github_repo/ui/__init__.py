#!/usr/bin/env python3
"""
PinokioCloud Streamlit UI Package

This package provides the complete Streamlit web interface for PinokioCloud,
including the main application, terminal widget, app gallery, resource monitoring,
and tunnel dashboard components.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

from ui.streamlit_app import PinokioCloudApp
from ui.terminal_widget import TerminalWidget
from ui.app_gallery import AppGallery
from ui.resource_monitor import ResourceMonitor
from ui.tunnel_dashboard import TunnelDashboard

__version__ = "1.0.0"
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