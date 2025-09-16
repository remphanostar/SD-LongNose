"""
PinokioCloud Platform Optimization Engine - Phase 8

This package contains cloud platform-specific optimizations and features.
It provides specialized functionality for Google Colab, Vast.ai, Lightning.ai,
Paperspace, and RunPod platforms with intelligent adaptation and optimization.

Author: PinokioCloud Development Team
Version: 1.0.0
Phase: 8 - Cloud Platform Specialization
"""

from platforms.colab_optimizer import ColabOptimizer, ColabFeatures, ColabConfig
from platforms.vast_optimizer import VastOptimizer, VastFeatures, VastConfig
from platforms.lightning_optimizer import LightningOptimizer, LightningFeatures, LightningConfig

__all__ = [
    'ColabOptimizer',
    'ColabFeatures',
    'ColabConfig',
    'VastOptimizer',
    'VastFeatures',
    'VastConfig',
    'LightningOptimizer',
    'LightningFeatures',
    'LightningConfig'
]

__version__ = "1.0.0"
__phase__ = "8"
__description__ = "Cloud Platform Specialization for PinokioCloud"