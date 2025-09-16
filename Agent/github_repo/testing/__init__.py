#!/usr/bin/env python3
"""
PinokioCloud Testing Module - Phase 10: Comprehensive Testing and Validation

This module provides comprehensive testing and validation for the entire PinokioCloud
system, including real-world application testing, multi-cloud testing, performance
benchmarking, and error condition testing.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "PinokioCloud Development Team"

# Import all testing components
from .app_test_suite import AppTestSuite
from .cloud_test_matrix import CloudTestMatrix  
from .performance_benchmark import PerformanceBenchmark
from .error_condition_test import ErrorConditionTest

__all__ = [
    'AppTestSuite',
    'CloudTestMatrix', 
    'PerformanceBenchmark',
    'ErrorConditionTest'
]