#!/usr/bin/env python3
"""
PinokioCloud Multi-Cloud Detection System

This module detects which cloud platform the system is running on by analyzing
environment variables, file system characteristics, and system properties.
Supports Google Colab, Vast.ai, Lightning.ai, Paperspace, and RunPod.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import subprocess
import platform
import json
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum


class CloudPlatform(Enum):
    """Enumeration of supported cloud platforms."""
    GOOGLE_COLAB = "google-colab"
    VAST_AI = "vast-ai"
    LIGHTNING_AI = "lightning-ai"
    PAPERSPACE = "paperspace"
    RUNPOD = "runpod"
    UNKNOWN = "unknown"


@dataclass
class CloudDetectionResult:
    """Result of cloud platform detection."""
    platform: CloudPlatform
    confidence: float
    detection_methods: List[str]
    environment_vars: Dict[str, str]
    file_system_indicators: List[str]
    system_properties: Dict[str, str]
    base_path: str


class CloudDetector:
    """
    Multi-cloud platform detection system.
    
    Detects cloud platforms through multiple methods:
    1. Environment variable analysis
    2. File system characteristic detection
    3. System property analysis
    4. Network configuration analysis
    5. Process and service detection
    """
    
    def __init__(self):
        """Initialize the cloud detector."""
        self.detection_methods = []
        self.environment_vars = {}
        self.file_system_indicators = []
        self.system_properties = {}
        
    def detect_platform(self) -> CloudDetectionResult:
        """
        Detect the current cloud platform.
        
        Returns:
            CloudDetectionResult: Complete detection result with confidence score
        """
        self._reset_detection_state()
        
        # Run all detection methods
        colab_score = self._detect_google_colab()
        vast_score = self._detect_vast_ai()
        lightning_score = self._detect_lightning_ai()
        paperspace_score = self._detect_paperspace()
        runpod_score = self._detect_runpod()
        
        # Determine the platform with highest confidence
        scores = {
            CloudPlatform.GOOGLE_COLAB: colab_score,
            CloudPlatform.VAST_AI: vast_score,
            CloudPlatform.LIGHTNING_AI: lightning_score,
            CloudPlatform.PAPERSPACE: paperspace_score,
            CloudPlatform.RUNPOD: runpod_score
        }
        
        best_platform = max(scores, key=scores.get)
        best_score = scores[best_platform]
        
        # If confidence is too low, mark as unknown
        if best_score < 0.3:
            best_platform = CloudPlatform.UNKNOWN
            best_score = 0.0
        
        # Determine base path based on platform
        platform_base_paths = {
            CloudPlatform.GOOGLE_COLAB: "/content",
            CloudPlatform.VAST_AI: "/workspace", 
            CloudPlatform.LIGHTNING_AI: "/teamspace",
            CloudPlatform.PAPERSPACE: "/notebooks",
            CloudPlatform.RUNPOD: "/workspace",
            CloudPlatform.UNKNOWN: "/workspace"
        }
        
        base_path = platform_base_paths.get(best_platform, "/workspace")
        
        return CloudDetectionResult(
            platform=best_platform,
            confidence=best_score,
            detection_methods=self.detection_methods.copy(),
            environment_vars=self.environment_vars.copy(),
            file_system_indicators=self.file_system_indicators.copy(),
            system_properties=self.system_properties.copy(),
            base_path=base_path
        )
    
    def _reset_detection_state(self):
        """Reset detection state for new detection run."""
        self.detection_methods = []
        self.environment_vars = {}
        self.file_system_indicators = []
        self.system_properties = {}
    
    def _detect_google_colab(self) -> float:
        """
        Detect Google Colab environment.
        
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        score = 0.0
        methods = []
        
        # Check for Colab-specific environment variables
        colab_vars = [
            'COLAB_GPU', 'COLAB_TPU', 'COLAB_CPU', 'COLAB_RUNTIME_VERSION',
            'COLAB_USER_DATA_DIR', 'COLAB_DRIVE_MOUNTED'
        ]
        
        for var in colab_vars:
            if var in os.environ:
                self.environment_vars[var] = os.environ[var]
                score += 0.2
                methods.append(f"env_var_{var}")
        
        # Check for Colab-specific file system paths
        colab_paths = ['/content', '/mnt/MyDrive', '/root/.local/share/jupyter']
        for path in colab_paths:
            if os.path.exists(path):
                self.file_system_indicators.append(path)
                score += 0.15
                methods.append(f"path_{path}")
        
        # Check for Colab-specific Python modules
        try:
            import google.colab
            score += 0.3
            methods.append("google_colab_module")
        except ImportError:
            pass
        
        # Check for Colab-specific processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            if 'jupyter' in result.stdout and 'colab' in result.stdout:
                score += 0.2
                methods.append("colab_process")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for Colab-specific network configuration
        try:
            result = subprocess.run(['hostname'], capture_output=True, text=True, timeout=3)
            if 'colab' in result.stdout.lower():
                score += 0.15
                methods.append("hostname_colab")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        if methods:
            self.detection_methods.extend(methods)
        
        return min(score, 1.0)
    
    def _detect_vast_ai(self) -> float:
        """
        Detect Vast.ai environment.
        
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        score = 0.0
        methods = []
        
        # Check for Vast.ai-specific environment variables
        vast_vars = ['VAST_CONTAINERLABEL', 'VAST_CONTAINERNAME', 'VAST_SSH_PORT']
        for var in vast_vars:
            if var in os.environ:
                self.environment_vars[var] = os.environ[var]
                score += 0.25
                methods.append(f"env_var_{var}")
        
        # Check for Vast.ai-specific file system paths
        vast_paths = ['/workspace', '/vast', '/mnt/vast']
        for path in vast_paths:
            if os.path.exists(path):
                self.file_system_indicators.append(path)
                score += 0.2
                methods.append(f"path_{path}")
        
        # Check for Vast.ai-specific processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            if 'vast' in result.stdout.lower():
                score += 0.2
                methods.append("vast_process")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for Vast.ai-specific network configuration
        try:
            result = subprocess.run(['hostname'], capture_output=True, text=True, timeout=3)
            if 'vast' in result.stdout.lower():
                score += 0.15
                methods.append("hostname_vast")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for Vast.ai-specific system properties
        try:
            result = subprocess.run(['uname', '-a'], capture_output=True, text=True, timeout=3)
            if 'vast' in result.stdout.lower():
                score += 0.2
                methods.append("uname_vast")
                self.system_properties['uname'] = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        if methods:
            self.detection_methods.extend(methods)
        
        return min(score, 1.0)
    
    def _detect_lightning_ai(self) -> float:
        """
        Detect Lightning.ai environment.
        
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        score = 0.0
        methods = []
        
        # Check for Lightning.ai-specific environment variables
        lightning_vars = ['LIGHTNING_CLOUD_PROJECT_ID', 'LIGHTNING_CLOUD_APP_ID', 'LIGHTNING_CLOUD_WORK_ID']
        for var in lightning_vars:
            if var in os.environ:
                self.environment_vars[var] = os.environ[var]
                score += 0.3
                methods.append(f"env_var_{var}")
        
        # Check for Lightning.ai-specific file system paths
        lightning_paths = ['/teamspace', '/lightning', '/mnt/lightning']
        for path in lightning_paths:
            if os.path.exists(path):
                self.file_system_indicators.append(path)
                score += 0.25
                methods.append(f"path_{path}")
        
        # Check for Lightning.ai-specific processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            if 'lightning' in result.stdout.lower():
                score += 0.2
                methods.append("lightning_process")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for Lightning.ai-specific network configuration
        try:
            result = subprocess.run(['hostname'], capture_output=True, text=True, timeout=3)
            if 'lightning' in result.stdout.lower():
                score += 0.15
                methods.append("hostname_lightning")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for Lightning.ai-specific system properties
        try:
            result = subprocess.run(['uname', '-a'], capture_output=True, text=True, timeout=3)
            if 'lightning' in result.stdout.lower():
                score += 0.1
                methods.append("uname_lightning")
                self.system_properties['uname'] = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        if methods:
            self.detection_methods.extend(methods)
        
        return min(score, 1.0)
    
    def _detect_paperspace(self) -> float:
        """
        Detect Paperspace environment.
        
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        score = 0.0
        methods = []
        
        # Check for Paperspace-specific environment variables
        paperspace_vars = ['PAPERSPACE_API_KEY', 'PAPERSPACE_MACHINE_ID', 'PAPERSPACE_WORKSPACE_ID']
        for var in paperspace_vars:
            if var in os.environ:
                self.environment_vars[var] = os.environ[var]
                score += 0.3
                methods.append(f"env_var_{var}")
        
        # Check for Paperspace-specific file system paths
        paperspace_paths = ['/paperspace', '/mnt/paperspace', '/opt/paperspace']
        for path in paperspace_paths:
            if os.path.exists(path):
                self.file_system_indicators.append(path)
                score += 0.25
                methods.append(f"path_{path}")
        
        # Check for Paperspace-specific processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            if 'paperspace' in result.stdout.lower():
                score += 0.2
                methods.append("paperspace_process")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for Paperspace-specific network configuration
        try:
            result = subprocess.run(['hostname'], capture_output=True, text=True, timeout=3)
            if 'paperspace' in result.stdout.lower():
                score += 0.15
                methods.append("hostname_paperspace")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for Paperspace-specific system properties
        try:
            result = subprocess.run(['uname', '-a'], capture_output=True, text=True, timeout=3)
            if 'paperspace' in result.stdout.lower():
                score += 0.1
                methods.append("uname_paperspace")
                self.system_properties['uname'] = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        if methods:
            self.detection_methods.extend(methods)
        
        return min(score, 1.0)
    
    def _detect_runpod(self) -> float:
        """
        Detect RunPod environment.
        
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        score = 0.0
        methods = []
        
        # Check for RunPod-specific environment variables
        runpod_vars = ['RUNPOD_POD_ID', 'RUNPOD_API_KEY', 'RUNPOD_WORKSPACE_ID']
        for var in runpod_vars:
            if var in os.environ:
                self.environment_vars[var] = os.environ[var]
                score += 0.3
                methods.append(f"env_var_{var}")
        
        # Check for RunPod-specific file system paths
        runpod_paths = ['/runpod', '/mnt/runpod', '/opt/runpod']
        for path in runpod_paths:
            if os.path.exists(path):
                self.file_system_indicators.append(path)
                score += 0.25
                methods.append(f"path_{path}")
        
        # Check for RunPod-specific processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
            if 'runpod' in result.stdout.lower():
                score += 0.2
                methods.append("runpod_process")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for RunPod-specific network configuration
        try:
            result = subprocess.run(['hostname'], capture_output=True, text=True, timeout=3)
            if 'runpod' in result.stdout.lower():
                score += 0.15
                methods.append("hostname_runpod")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for RunPod-specific system properties
        try:
            result = subprocess.run(['uname', '-a'], capture_output=True, text=True, timeout=3)
            if 'runpod' in result.stdout.lower():
                score += 0.1
                methods.append("uname_runpod")
                self.system_properties['uname'] = result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        if methods:
            self.detection_methods.extend(methods)
        
        return min(score, 1.0)
    
    def get_detection_summary(self, result: CloudDetectionResult) -> str:
        """
        Get a human-readable summary of the detection result.
        
        Args:
            result: CloudDetectionResult from detect_platform()
            
        Returns:
            str: Human-readable detection summary
        """
        summary = f"Cloud Platform Detection Results:\n"
        summary += f"Platform: {result.platform.value}\n"
        summary += f"Confidence: {result.confidence:.2f}\n"
        summary += f"Detection Methods: {', '.join(result.detection_methods)}\n"
        
        if result.environment_vars:
            summary += f"Environment Variables: {list(result.environment_vars.keys())}\n"
        
        if result.file_system_indicators:
            summary += f"File System Indicators: {result.file_system_indicators}\n"
        
        if result.system_properties:
            summary += f"System Properties: {list(result.system_properties.keys())}\n"
        
        return summary


def main():
    """Main function for testing cloud detection."""
    detector = CloudDetector()
    result = detector.detect_platform()
    
    print(detector.get_detection_summary(result))
    
    # Return result as JSON for programmatic use
    return {
        'platform': result.platform.value,
        'confidence': result.confidence,
        'detection_methods': result.detection_methods,
        'environment_vars': result.environment_vars,
        'file_system_indicators': result.file_system_indicators,
        'system_properties': result.system_properties
    }


if __name__ == "__main__":
    main()