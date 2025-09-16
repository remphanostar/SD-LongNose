#!/usr/bin/env python3
"""
PinokioCloud Phase 1 Launcher

This module serves as the main entry point for Phase 1: Multi-Cloud Detection & Repository Cloning.
It orchestrates the complete Phase 1 workflow including cloud detection, resource assessment,
path mapping, and repository cloning.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Import Phase 1 modules
from .cloud_detector import CloudDetector, CloudPlatform, CloudDetectionResult
from .platform_configs import PlatformConfigurationManager, PlatformConfigurationuration
from .resource_assessor import ResourceAssessor, ResourceAssessment
from .path_mapper import PathMapper, PathMappingResult
from .repo_cloner import RepositoryCloner, CloneResult


@dataclass
class Phase1Result:
    """Complete result of Phase 1 execution."""
    success: bool
    detected_platform: CloudPlatform
    platform_config: PlatformConfigurationuration
    resource_assessment: ResourceAssessment
    path_mappings: Dict[str, PathMappingResult]
    clone_result: CloneResult
    execution_time: float
    errors: List[str] = None
    warnings: List[str] = None


class Phase1Launcher:
    """
    Phase 1 launcher for multi-cloud detection and repository cloning.
    
    Orchestrates the complete Phase 1 workflow:
    1. Cloud platform detection
    2. Platform configuration loading
    3. Resource assessment
    4. Path mapping setup
    5. Repository cloning
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize Phase 1 launcher.
        
        Args:
            base_path: Base path for operations
        """
        self.base_path = base_path
        self.start_time = 0.0
        self.results = {}
        
        # Initialize components
        self.cloud_detector = CloudDetector()
        self.platform_config_manager = PlatformConfigurationManager()
        self.resource_assessor = ResourceAssessor()
        self.path_mapper = None
        self.repo_cloner = None
    
    def execute_phase1(self, force_clone: bool = False) -> Phase1Result:
        """
        Execute complete Phase 1 workflow.
        
        Args:
            force_clone: Force repository clone even if exists
            
        Returns:
            Phase1Result: Complete Phase 1 execution result
        """
        self.start_time = time.time()
        errors = []
        warnings = []
        
        try:
            print("🚀 Starting Phase 1: Multi-Cloud Detection & Repository Cloning")
            print("=" * 70)
            
            # Step 1: Cloud Platform Detection
            print("\n📡 Step 1: Detecting Cloud Platform...")
            detection_result = self._detect_cloud_platform()
            if not detection_result:
                errors.append("Failed to detect cloud platform")
                return self._create_failed_result(errors, warnings)
            
            print(f"✅ Detected Platform: {detection_result.platform.value}")
            print(f"   Confidence: {detection_result.confidence:.2f}")
            print(f"   Methods: {', '.join(detection_result.detection_methods)}")
            
            # Step 2: Load Platform Configuration
            print("\n⚙️  Step 2: Loading Platform Configuration...")
            platform_config = self._load_platform_config(detection_result.platform)
            if not platform_config:
                errors.append(f"Failed to load configuration for {detection_result.platform.value}")
                return self._create_failed_result(errors, warnings)
            
            print(f"✅ Platform Configuration Loaded")
            print(f"   Display Name: {platform_config.display_name}")
            print(f"   Base Path: {platform_config.paths.base_path}")
            print(f"   Max Memory: {platform_config.limits.max_memory_gb} GB")
            print(f"   Max GPU: {platform_config.limits.max_gpu_count}")
            
            # Step 3: Resource Assessment
            print("\n🔍 Step 3: Assessing System Resources...")
            resource_assessment = self._assess_resources()
            if not resource_assessment:
                errors.append("Failed to assess system resources")
                return self._create_failed_result(errors, warnings)
            
            print(f"✅ Resource Assessment Complete")
            print(f"   Overall Score: {resource_assessment.overall_score:.1f}/100")
            print(f"   CPU: {resource_assessment.cpu.cores_logical} cores")
            print(f"   GPU: {resource_assessment.gpu.count} device(s)")
            print(f"   Memory: {resource_assessment.memory.total_gb:.1f} GB")
            
            # Step 4: Setup Path Mapping
            print("\n🗺️  Step 4: Setting Up Path Mapping...")
            path_mappings = self._setup_path_mapping(detection_result.platform)
            if not path_mappings:
                errors.append("Failed to setup path mapping")
                return self._create_failed_result(errors, warnings)
            
            print(f"✅ Path Mapping Setup Complete")
            print(f"   Mapped {len(path_mappings)} path types")
            
            # Step 5: Clone Repository
            print("\n📥 Step 5: Cloning PinokioCloud Repository...")
            clone_result = self._clone_repository(detection_result.platform, force_clone)
            if not clone_result:
                errors.append("Failed to clone repository")
                return self._create_failed_result(errors, warnings)
            
            print(f"✅ Repository Clone Complete")
            print(f"   Repository Path: {clone_result.repository_path}")
            print(f"   Files Cloned: {len(clone_result.cloned_files)}")
            print(f"   Total Size: {clone_result.total_size_bytes / (1024*1024):.2f} MB")
            
            # Calculate execution time
            execution_time = time.time() - self.start_time
            
            print(f"\n🎉 Phase 1 Complete! Execution Time: {execution_time:.2f} seconds")
            print("=" * 70)
            
            return Phase1Result(
                success=True,
                detected_platform=detection_result.platform,
                platform_config=platform_config,
                resource_assessment=resource_assessment,
                path_mappings=path_mappings,
                clone_result=clone_result,
                execution_time=execution_time,
                errors=errors,
                warnings=warnings
            )
        
        except Exception as e:
            errors.append(f"Phase 1 execution failed: {str(e)}")
            execution_time = time.time() - self.start_time
            return self._create_failed_result(errors, warnings, execution_time)
    
    def _detect_cloud_platform(self) -> Optional[CloudDetectionResult]:
        """Detect the current cloud platform."""
        try:
            result = self.cloud_detector.detect_platform()
            
            # Log detection details
            print(f"   Detection Methods: {', '.join(result.detection_methods)}")
            if result.environment_vars:
                print(f"   Environment Variables: {list(result.environment_vars.keys())}")
            if result.file_system_indicators:
                print(f"   File System Indicators: {result.file_system_indicators}")
            
            return result
        
        except Exception as e:
            print(f"   ❌ Cloud detection failed: {str(e)}")
            return None
    
    def _load_platform_config(self, platform: CloudPlatform) -> Optional[PlatformConfigurationuration]:
        """Load platform configuration."""
        try:
            config = self.platform_config_manager.get_config(platform)
            
            if config:
                # Validate platform requirements
                validation_results = self.platform_config_manager.validate_platform_requirements(platform)
                print(f"   Platform Requirements Validation:")
                for requirement, valid in validation_results.items():
                    status = "✅" if valid else "❌"
                    print(f"     {status} {requirement}")
                
                return config
            else:
                print(f"   ❌ No configuration found for platform: {platform.value}")
                return None
        
        except Exception as e:
            print(f"   ❌ Failed to load platform config: {str(e)}")
            return None
    
    def _assess_resources(self) -> Optional[ResourceAssessment]:
        """Assess system resources."""
        try:
            assessment = self.resource_assessor.assess_resources(force_refresh=True)
            
            # Log resource details
            print(f"   CPU: {assessment.cpu.cores_logical} cores, {assessment.cpu.usage_percent:.1f}% usage")
            print(f"   GPU: {assessment.gpu.count} device(s), {assessment.gpu.total_memory_mb}MB total")
            print(f"   Memory: {assessment.memory.total_gb:.1f}GB total, {assessment.memory.usage_percent:.1f}% used")
            
            if assessment.storage:
                main_storage = assessment.storage[0]
                print(f"   Storage: {main_storage.total_gb:.1f}GB total, {main_storage.usage_percent:.1f}% used")
            
            if assessment.recommendations:
                print(f"   Recommendations: {len(assessment.recommendations)}")
                for rec in assessment.recommendations[:3]:  # Show first 3
                    print(f"     - {rec}")
            
            return assessment
        
        except Exception as e:
            print(f"   ❌ Resource assessment failed: {str(e)}")
            return None
    
    def _setup_path_mapping(self, platform: CloudPlatform) -> Optional[Dict[str, PathMappingResult]]:
        """Setup path mapping for the platform."""
        try:
            self.path_mapper = PathMapper(platform)
            
            # Map standard paths
            path_mappings = {}
            standard_paths = ["base", "apps", "data", "temp", "logs", "cache", "models", "config", "workspace"]
            
            for path_type in standard_paths:
                result = self.path_mapper.map_path(f"/{path_type}/test", path_type=path_type)
                path_mappings[path_type] = result
                
                if result.success:
                    print(f"     ✅ {path_type}: {result.target_path}")
                else:
                    print(f"     ❌ {path_type}: {result.error_message}")
            
            return path_mappings
        
        except Exception as e:
            print(f"   ❌ Path mapping setup failed: {str(e)}")
            return None
    
    def _clone_repository(self, platform: CloudPlatform, force_clone: bool) -> Optional[CloneResult]:
        """Clone the PinokioCloud repository."""
        try:
            # Get platform configuration for base path
            config = self.platform_config_manager.get_config(platform)
            if not config:
                print(f"   ❌ No platform config available for cloning")
                return None
            
            # Initialize repository cloner
            self.repo_cloner = RepositoryCloner(platform.value, config.paths.base_path)
            
            # Set up progress callback
            def progress_callback(progress):
                if progress.progress_percent % 20 == 0:  # Log every 20%
                    print(f"     Progress: {progress.progress_percent:.0f}% - {progress.current_operation}")
            
            self.repo_cloner.set_progress_callback(progress_callback)
            
            # Perform clone
            result = self.repo_cloner.clone_repository(force_clone=force_clone, shallow_clone=True)
            
            if result.success:
                print(f"     ✅ Clone successful: {result.repository_path}")
                print(f"     📁 Files: {len(result.cloned_files)}")
                print(f"     📊 Size: {result.total_size_bytes / (1024*1024):.2f} MB")
                print(f"     ⏱️  Duration: {result.clone_duration:.2f} seconds")
            else:
                print(f"     ❌ Clone failed: {result.error_message}")
            
            return result
        
        except Exception as e:
            print(f"   ❌ Repository cloning failed: {str(e)}")
            return None
    
    def _create_failed_result(self, errors: List[str], warnings: List[str], 
                            execution_time: float = 0.0) -> Phase1Result:
        """Create a failed Phase 1 result."""
        if execution_time == 0.0:
            execution_time = time.time() - self.start_time
        
        return Phase1Result(
            success=False,
            detected_platform=CloudPlatform.UNKNOWN,
            platform_config=None,
            resource_assessment=None,
            path_mappings={},
            clone_result=None,
            execution_time=execution_time,
            errors=errors,
            warnings=warnings
        )
    
    def get_phase1_summary(self, result: Phase1Result) -> str:
        """Get a human-readable summary of Phase 1 results."""
        summary = f"Phase 1 Execution Summary:\n"
        summary += f"Success: {result.success}\n"
        summary += f"Execution Time: {result.execution_time:.2f} seconds\n"
        
        if result.success:
            summary += f"Detected Platform: {result.detected_platform.value}\n"
            summary += f"Platform Display Name: {result.platform_config.display_name}\n"
            summary += f"Resource Score: {result.resource_assessment.overall_score:.1f}/100\n"
            summary += f"Repository Path: {result.clone_result.repository_path}\n"
            summary += f"Files Cloned: {len(result.clone_result.cloned_files)}\n"
        else:
            summary += f"Errors: {len(result.errors)}\n"
            for error in result.errors:
                summary += f"  - {error}\n"
        
        if result.warnings:
            summary += f"Warnings: {len(result.warnings)}\n"
            for warning in result.warnings:
                summary += f"  - {warning}\n"
        
        return summary
    
    def save_results(self, result: Phase1Result, output_path: str = None) -> str:
        """Save Phase 1 results to JSON file."""
        if output_path is None:
            output_path = os.path.join(self.base_path, "phase1_results.json")
        
        try:
            # Convert result to dictionary
            result_dict = asdict(result)
            
            # Convert non-serializable objects
            result_dict['detected_platform'] = result.detected_platform.value
            result_dict['platform_config'] = asdict(result.platform_config) if result.platform_config else None
            result_dict['resource_assessment'] = asdict(result.resource_assessment) if result.resource_assessment else None
            result_dict['clone_result'] = asdict(result.clone_result) if result.clone_result else None
            
            # Save to file
            with open(output_path, 'w') as f:
                json.dump(result_dict, f, indent=2, default=str)
            
            return output_path
        
        except Exception as e:
            print(f"Failed to save results: {str(e)}")
            return ""


def main():
    """Main function for testing Phase 1 launcher."""
    print("🧪 Testing Phase 1 Launcher")
    print("=" * 50)
    
    # Initialize launcher
    launcher = Phase1Launcher()
    
    # Execute Phase 1
    result = launcher.execute_phase1(force_clone=True)
    
    # Print summary
    print("\n" + launcher.get_phase1_summary(result))
    
    # Save results
    if result.success:
        output_file = launcher.save_results(result)
        if output_file:
            print(f"\n💾 Results saved to: {output_file}")
    
    return result


if __name__ == "__main__":
    main()