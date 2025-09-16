#!/usr/bin/env python3
"""
PinokioCloud App Analysis Package

This package provides comprehensive analysis capabilities for Pinokio applications.
It includes modules for detecting installation methods, web UI frameworks,
dependency systems, tunnel requirements, and creating complete app profiles.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

from app_analysis.app_analyzer import AppAnalyzer, AppAnalysisResult, AnalysisStatus
from app_analysis.installer_detector import InstallerDetector, InstallerType, InstallerInfo
from app_analysis.webui_detector import WebUIDetector, WebUIType, WebUIInfo
from app_analysis.dependency_analyzer import DependencyAnalyzer, DependencyType, DependencyInfo
from app_analysis.tunnel_requirements import TunnelRequirements, TunnelType, TunnelInfo
from app_analysis.app_profiler import AppProfiler, AppProfile, AppCategory, AppComplexity, AppStatus

__version__ = "1.0.0"
__author__ = "PinokioCloud Development Team"

__all__ = [
    # Main analyzer
    "AppAnalyzer",
    "AppAnalysisResult", 
    "AnalysisStatus",
    
    # Installer detection
    "InstallerDetector",
    "InstallerType",
    "InstallerInfo",
    
    # Web UI detection
    "WebUIDetector",
    "WebUIType", 
    "WebUIInfo",
    
    # Dependency analysis
    "DependencyAnalyzer",
    "DependencyType",
    "DependencyInfo",
    
    # Tunnel requirements
    "TunnelRequirements",
    "TunnelType",
    "TunnelInfo",
    
    # App profiling
    "AppProfiler",
    "AppProfile",
    "AppCategory",
    "AppComplexity",
    "AppStatus"
]