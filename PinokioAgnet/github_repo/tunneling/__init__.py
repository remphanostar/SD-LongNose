"""
PinokioCloud Tunneling Engine - Phase 7

This package contains the web UI discovery and multi-tunnel management system.
It provides comprehensive web server detection, tunnel management via ngrok and Cloudflare,
and URL tracking with QR code generation for easy access.

Author: PinokioCloud Development Team
Version: 1.0.0
Phase: 7 - Web UI Discovery and Multi-Tunnel Management
"""

from tunneling.server_detector import ServerDetector, WebServerInfo, WebFrameworkType
from tunneling.ngrok_manager import NgrokManager, NgrokTunnel, NgrokStatus
from tunneling.cloudflare_manager import CloudflareManager, CloudflareTunnel, CloudflareStatus
from tunneling.gradio_integration import GradioIntegration, GradioConfig
from tunneling.url_manager import URLManager, TunnelURL, QRCodeGenerator

__all__ = [
    'ServerDetector',
    'WebServerInfo',
    'WebFrameworkType',
    'NgrokManager',
    'NgrokTunnel',
    'NgrokStatus',
    'CloudflareManager',
    'CloudflareTunnel',
    'CloudflareStatus',
    'GradioIntegration',
    'GradioConfig',
    'URLManager',
    'TunnelURL',
    'QRCodeGenerator'
]

__version__ = "1.0.0"
__phase__ = "7"
__description__ = "Web UI Discovery and Multi-Tunnel Management for PinokioCloud"