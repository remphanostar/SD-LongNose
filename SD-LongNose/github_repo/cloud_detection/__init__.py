#!/usr/bin/env python3
"""
PinokioCloud Multi-Cloud Detection Package

This package provides comprehensive cloud platform detection, configuration,
resource assessment, path mapping, and repository cloning capabilities for
multi-cloud GPU environments.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

from .cloud_detector import CloudDetector, CloudPlatform, CloudDetectionResult
from .platform_configs import PlatformConfigurationManager, PlatformConfigurationuration, CloudPlatform as ConfigCloudPlatform
from .resource_assessor import ResourceAssessor, ResourceAssessment, ResourceType
from .path_mapper import PathMapper, PathMapping, PathMappingResult, CloudPlatform as PathCloudPlatform
from .repo_cloner import RepositoryCloner, CloneResult, CloneStatus, CloneProgress

__version__ = "1.0.0"
__author__ = "PinokioCloud Development Team"

# Re-export the main classes
__all__ = [
    # Cloud Detection
    "CloudDetector",
    "CloudPlatform", 
    "CloudDetectionResult",
    
    # Platform Configuration
    "PlatformConfigurationManager",
    "PlatformConfigurationuration",
    
    # Resource Assessment
    "ResourceAssessor",
    "ResourceAssessment",
    "ResourceType",
    
    # Path Mapping
    "PathMapper",
    "PathMapping",
    "PathMappingResult",
    
    # Repository Cloning
    "RepositoryCloner",
    "CloneResult",
    "CloneStatus",
    "CloneProgress"
]