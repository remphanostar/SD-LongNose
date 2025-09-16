#!/usr/bin/env python3
"""
PinokioCloud Enhanced UI Package

This package provides the enhanced Streamlit web interface for PinokioCloud,
utilizing every cutting-edge Streamlit feature available including fragments,
dialogs, popovers, pills, segmented controls, feedback widgets, and more.

Author: PinokioCloud Development Team
Version: 2.0.0 (Enhanced)
"""

from ui_enhanced.streamlit_app import PinokioCloudEnhancedApp
from ui_enhanced.terminal_widget import EnhancedTerminalWidget
from ui_enhanced.app_gallery import EnhancedAppGallery
from ui_enhanced.resource_monitor import EnhancedResourceMonitor
from ui_enhanced.tunnel_dashboard import EnhancedTunnelDashboard

__version__ = "2.0.0-enhanced"
__author__ = "PinokioCloud Development Team"

# Re-export the main classes
__all__ = [
    # Main Application
    "PinokioCloudEnhancedApp",
    
    # Enhanced UI Components
    "EnhancedTerminalWidget",
    "EnhancedAppGallery", 
    "EnhancedResourceMonitor",
    "EnhancedTunnelDashboard"
]