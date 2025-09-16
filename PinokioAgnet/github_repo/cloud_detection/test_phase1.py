#!/usr/bin/env python3
"""
PinokioCloud Phase 1 Test Script

Standalone test script for Phase 1 components without relative imports.
"""

import os
import sys
import time
import json

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Phase 1 modules
from cloud_detector import CloudDetector, CloudPlatform, CloudDetectionResult
from platform_configs import PlatformConfigurationManager, PlatformConfigurationuration
from resource_assessor import ResourceAssessor, ResourceAssessment
from path_mapper import PathMapper, PathMappingResult
from repo_cloner import RepositoryCloner, CloneResult


def test_cloud_detection():
    """Test cloud platform detection."""
    print("🧪 Testing Cloud Detection...")
    
    detector = CloudDetector()
    result = detector.detect_platform()
    
    print(f"✅ Detected Platform: {result.platform.value}")
    print(f"   Confidence: {result.confidence:.2f}")
    print(f"   Methods: {', '.join(result.detection_methods)}")
    
    if result.environment_vars:
        print(f"   Environment Variables: {list(result.environment_vars.keys())}")
    
    if result.file_system_indicators:
        print(f"   File System Indicators: {result.file_system_indicators}")
    
    return result


def test_platform_configs():
    """Test platform configuration loading."""
    print("\n🧪 Testing Platform Configurations...")
    
    manager = PlatformConfigurationManager()
    platforms = manager.get_supported_platforms()
    
    print(f"✅ Supported Platforms: {len(platforms)}")
    for platform in platforms:
        if platform != CloudPlatform.UNKNOWN:
            config = manager.get_config(platform)
            if config:
                print(f"   {platform.value}: {config.display_name}")
                print(f"     Base Path: {config.paths.base_path}")
                print(f"     Max Memory: {config.limits.max_memory_gb} GB")
                print(f"     Max GPU: {config.limits.max_gpu_count}")
    
    return manager


def test_resource_assessment():
    """Test resource assessment."""
    print("\n🧪 Testing Resource Assessment...")
    
    assessor = ResourceAssessor()
    assessment = assessor.assess_resources(force_refresh=True)
    
    print(f"✅ Resource Assessment Complete")
    print(f"   Overall Score: {assessment.overall_score:.1f}/100")
    print(f"   CPU: {assessment.cpu.cores_logical} cores, {assessment.cpu.usage_percent:.1f}% usage")
    print(f"   GPU: {assessment.gpu.count} device(s), {assessment.gpu.total_memory_mb}MB total")
    print(f"   Memory: {assessment.memory.total_gb:.1f}GB total, {assessment.memory.usage_percent:.1f}% used")
    
    if assessment.storage:
        main_storage = assessment.storage[0]
        print(f"   Storage: {main_storage.total_gb:.1f}GB total, {main_storage.usage_percent:.1f}% used")
    
    if assessment.recommendations:
        print(f"   Recommendations: {len(assessment.recommendations)}")
        for rec in assessment.recommendations[:3]:
            print(f"     - {rec}")
    
    return assessment


def test_path_mapping():
    """Test path mapping."""
    print("\n🧪 Testing Path Mapping...")
    
    # Test with detected platform
    detector = CloudDetector()
    detection_result = detector.detect_platform()
    
    mapper = PathMapper(detection_result.platform)
    
    # Test standard path mapping
    path_mappings = {}
    standard_paths = ["base", "apps", "data", "temp", "logs", "cache", "models", "config", "workspace"]
    
    for path_type in standard_paths:
        result = mapper.map_path(f"/{path_type}/test", path_type=path_type)
        path_mappings[path_type] = result
        
        if result.success:
            print(f"   ✅ {path_type}: {result.target_path}")
        else:
            print(f"   ❌ {path_type}: {result.error_message}")
    
    print(f"✅ Path Mapping Complete: {len(path_mappings)} mappings")
    
    return path_mappings


def test_repository_cloning():
    """Test repository cloning."""
    print("\n🧪 Testing Repository Cloning...")
    
    # Test with detected platform
    detector = CloudDetector()
    detection_result = detector.detect_platform()
    
    manager = PlatformConfigurationManager()
    config = manager.get_config(detection_result.platform)
    
    if not config:
        print(f"   ❌ No config available for {detection_result.platform.value}")
        return None
    
    # Use a test directory
    test_base = "/tmp/test_clone"
    os.makedirs(test_base, exist_ok=True)
    
    cloner = RepositoryCloner(detection_result.platform.value, test_base)
    
    # Set up progress callback
    def progress_callback(progress):
        if progress.progress_percent % 25 == 0:  # Log every 25%
            print(f"     Progress: {progress.progress_percent:.0f}% - {progress.current_operation}")
    
    cloner.set_progress_callback(progress_callback)
    
    # Perform clone
    result = cloner.clone_repository(force_clone=True, shallow_clone=True)
    
    if result.success:
        print(f"   ✅ Clone successful: {result.repository_path}")
        print(f"   📁 Files: {len(result.cloned_files)}")
        print(f"   📊 Size: {result.total_size_bytes / (1024*1024):.2f} MB")
        print(f"   ⏱️  Duration: {result.clone_duration:.2f} seconds")
    else:
        print(f"   ❌ Clone failed: {result.error_message}")
    
    # Cleanup
    cloner.cleanup_repository()
    import shutil
    shutil.rmtree(test_base, ignore_errors=True)
    
    return result


def main():
    """Main test function."""
    print("🚀 PinokioCloud Phase 1 Component Testing")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Test all components
        detection_result = test_cloud_detection()
        config_manager = test_platform_configs()
        resource_assessment = test_resource_assessment()
        path_mappings = test_path_mapping()
        clone_result = test_repository_cloning()
        
        execution_time = time.time() - start_time
        
        print(f"\n🎉 All Tests Complete! Execution Time: {execution_time:.2f} seconds")
        print("=" * 60)
        
        # Summary
        print(f"✅ Cloud Detection: {detection_result.platform.value} (confidence: {detection_result.confidence:.2f})")
        print(f"✅ Platform Configs: {len(config_manager.get_supported_platforms())} platforms")
        print(f"✅ Resource Assessment: {resource_assessment.overall_score:.1f}/100 score")
        print(f"✅ Path Mapping: {len(path_mappings)} mappings")
        print(f"✅ Repository Cloning: {'Success' if clone_result and clone_result.success else 'Failed'}")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)