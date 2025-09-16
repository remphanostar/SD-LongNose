#!/usr/bin/env python3
"""
PinokioCloud Finalization Package

This package provides the final polish and production readiness components
for PinokioCloud, including comprehensive error handling, performance optimization,
documentation generation, and backup systems.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

from finalization.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from finalization.performance_optimizer import PerformanceOptimizer, OptimizationType
from finalization.documentation_generator import DocumentationGenerator, DocumentationType
from finalization.backup_system import BackupSystem, BackupType, RestorePoint

__version__ = "1.0.0"
__author__ = "PinokioCloud Development Team"

# Re-export the main classes
__all__ = [
    # Error Handling
    "ErrorHandler",
    "ErrorCategory",
    "ErrorSeverity",
    
    # Performance Optimization
    "PerformanceOptimizer",
    "OptimizationType",
    
    # Documentation Generation
    "DocumentationGenerator",
    "DocumentationType",
    
    # Backup and Recovery
    "BackupSystem",
    "BackupType",
    "RestorePoint"
]