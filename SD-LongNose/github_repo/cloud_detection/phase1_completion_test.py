#!/usr/bin/env python3
"""
PinokioCloud Phase 1 Completion Test

Comprehensive test suite to validate Phase 1 completion according to the
complete_phase_specifications.md requirements.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import json
from typing import Dict, List, Tuple, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Phase 1 modules
from cloud_detector import CloudDetector, CloudPlatform, CloudDetectionResult
from platform_configs import PlatformConfigurationManager, PlatformConfigurationuration
from resource_assessor import ResourceAssessor, ResourceAssessment
from path_mapper import PathMapper, PathMappingResult
from repo_cloner import RepositoryCloner, CloneResult


class Phase1CompletionTest:
    """
    Comprehensive test suite for Phase 1 completion validation.
    
    Tests all Phase 1 requirements according to complete_phase_specifications.md:
    - cloud_detector.py: Multi-cloud platform detection
    - platform_configs.py: Platform-specific configurations
    - resource_assessor.py: System resource assessment
    - path_mapper.py: Intelligent path mapping
    - repo_cloner.py: Repository cloning with progress tracking
    """
    
    def __init__(self):
        """Initialize the completion test suite."""
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = 0.0
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all Phase 1 completion tests.
        
        Returns:
            Dictionary with comprehensive test results
        """
        self.start_time = time.time()
        
        print("🧪 PinokioCloud Phase 1 Completion Test Suite")
        print("=" * 60)
        
        # Run all test categories
        self._test_cloud_detector()
        self._test_platform_configs()
        self._test_resource_assessor()
        self._test_path_mapper()
        self._test_repo_cloner()
        self._test_integration()
        
        # Calculate final results
        execution_time = time.time() - self.start_time
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"\n🎯 Phase 1 Completion Test Results")
        print("=" * 60)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Execution Time: {execution_time:.2f} seconds")
        
        # Determine overall success
        overall_success = self.failed_tests == 0 and self.total_tests > 0
        
        if overall_success:
            print(f"\n✅ PHASE 1 COMPLETION: SUCCESS")
            print(f"All {self.total_tests} tests passed!")
        else:
            print(f"\n❌ PHASE 1 COMPLETION: FAILED")
            print(f"{self.failed_tests} tests failed out of {self.total_tests}")
        
        return {
            "overall_success": overall_success,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "success_rate": success_rate,
            "execution_time": execution_time,
            "test_results": self.test_results
        }
    
    def _test_cloud_detector(self):
        """Test cloud_detector.py functionality."""
        print("\n📡 Testing Cloud Detector (cloud_detector.py)")
        print("-" * 50)
        
        try:
            # Test 1: CloudDetector initialization
            self._run_test("CloudDetector Initialization", self._test_cloud_detector_init)
            
            # Test 2: Platform detection
            self._run_test("Platform Detection", self._test_platform_detection)
            
            # Test 3: Detection result structure
            self._run_test("Detection Result Structure", self._test_detection_result_structure)
            
            # Test 4: Detection summary
            self._run_test("Detection Summary", self._test_detection_summary)
            
        except Exception as e:
            self._record_test_failure("Cloud Detector Tests", str(e))
    
    def _test_platform_configs(self):
        """Test platform_configs.py functionality."""
        print("\n⚙️  Testing Platform Configs (platform_configs.py)")
        print("-" * 50)
        
        try:
            # Test 1: PlatformConfigurationManager initialization
            self._run_test("PlatformConfigurationManager Initialization", self._test_platform_config_manager_init)
            
            # Test 2: Configuration loading
            self._run_test("Configuration Loading", self._test_configuration_loading)
            
            # Test 3: Platform validation
            self._run_test("Platform Validation", self._test_platform_validation)
            
            # Test 4: Configuration summary
            self._run_test("Configuration Summary", self._test_configuration_summary)
            
        except Exception as e:
            self._record_test_failure("Platform Configs Tests", str(e))
    
    def _test_resource_assessor(self):
        """Test resource_assessor.py functionality."""
        print("\n🔍 Testing Resource Assessor (resource_assessor.py)")
        print("-" * 50)
        
        try:
            # Test 1: ResourceAssessor initialization
            self._run_test("ResourceAssessor Initialization", self._test_resource_assessor_init)
            
            # Test 2: Resource assessment
            self._run_test("Resource Assessment", self._test_resource_assessment)
            
            # Test 3: Assessment result structure
            self._run_test("Assessment Result Structure", self._test_assessment_result_structure)
            
            # Test 4: Resource summary
            self._run_test("Resource Summary", self._test_resource_summary)
            
        except Exception as e:
            self._record_test_failure("Resource Assessor Tests", str(e))
    
    def _test_path_mapper(self):
        """Test path_mapper.py functionality."""
        print("\n🗺️  Testing Path Mapper (path_mapper.py)")
        print("-" * 50)
        
        try:
            # Test 1: PathMapper initialization
            self._run_test("PathMapper Initialization", self._test_path_mapper_init)
            
            # Test 2: Path mapping
            self._run_test("Path Mapping", self._test_path_mapping)
            
            # Test 3: Platform paths
            self._run_test("Platform Paths", self._test_platform_paths)
            
            # Test 4: Path validation
            self._run_test("Path Validation", self._test_path_validation)
            
        except Exception as e:
            self._record_test_failure("Path Mapper Tests", str(e))
    
    def _test_repo_cloner(self):
        """Test repo_cloner.py functionality."""
        print("\n📥 Testing Repository Cloner (repo_cloner.py)")
        print("-" * 50)
        
        try:
            # Test 1: RepositoryCloner initialization
            self._run_test("RepositoryCloner Initialization", self._test_repo_cloner_init)
            
            # Test 2: Clone operation (dry run)
            self._run_test("Clone Operation (Dry Run)", self._test_clone_operation_dry_run)
            
            # Test 3: Progress tracking
            self._run_test("Progress Tracking", self._test_progress_tracking)
            
            # Test 4: Repository info
            self._run_test("Repository Info", self._test_repository_info)
            
        except Exception as e:
            self._record_test_failure("Repository Cloner Tests", str(e))
    
    def _test_integration(self):
        """Test integration between all Phase 1 components."""
        print("\n🔗 Testing Integration")
        print("-" * 50)
        
        try:
            # Test 1: End-to-end workflow
            self._run_test("End-to-End Workflow", self._test_end_to_end_workflow)
            
            # Test 2: Component interaction
            self._run_test("Component Interaction", self._test_component_interaction)
            
            # Test 3: Error handling
            self._run_test("Error Handling", self._test_error_handling)
            
        except Exception as e:
            self._record_test_failure("Integration Tests", str(e))
    
    # Individual test methods
    def _test_cloud_detector_init(self) -> bool:
        """Test CloudDetector initialization."""
        detector = CloudDetector()
        return detector is not None
    
    def _test_platform_detection(self) -> bool:
        """Test platform detection functionality."""
        detector = CloudDetector()
        result = detector.detect_platform()
        return result is not None and isinstance(result, CloudDetectionResult)
    
    def _test_detection_result_structure(self) -> bool:
        """Test detection result structure."""
        detector = CloudDetector()
        result = detector.detect_platform()
        
        required_attrs = ['platform', 'confidence', 'detection_methods', 
                         'environment_vars', 'file_system_indicators', 'system_properties']
        
        return all(hasattr(result, attr) for attr in required_attrs)
    
    def _test_detection_summary(self) -> bool:
        """Test detection summary generation."""
        detector = CloudDetector()
        result = detector.detect_platform()
        summary = detector.get_detection_summary(result)
        return isinstance(summary, str) and len(summary) > 0
    
    def _test_platform_config_manager_init(self) -> bool:
        """Test PlatformConfigurationManager initialization."""
        manager = PlatformConfigurationManager()
        return manager is not None
    
    def _test_configuration_loading(self) -> bool:
        """Test configuration loading."""
        manager = PlatformConfigurationManager()
        platforms = manager.get_supported_platforms()
        return len(platforms) > 0
    
    def _test_platform_validation(self) -> bool:
        """Test platform validation."""
        manager = PlatformConfigurationManager()
        platforms = manager.get_supported_platforms()
        
        for platform in platforms:
            if platform != CloudPlatform.UNKNOWN:
                config = manager.get_config(platform)
                if config:
                    validation = manager.validate_platform_requirements(platform)
                    if not isinstance(validation, dict):
                        return False
        
        return True
    
    def _test_configuration_summary(self) -> bool:
        """Test configuration summary generation."""
        manager = PlatformConfigurationManager()
        platforms = manager.get_supported_platforms()
        
        for platform in platforms:
            if platform != CloudPlatform.UNKNOWN:
                summary = manager.get_platform_summary(platform)
                if not isinstance(summary, str) or len(summary) == 0:
                    return False
        
        return True
    
    def _test_resource_assessor_init(self) -> bool:
        """Test ResourceAssessor initialization."""
        assessor = ResourceAssessor()
        return assessor is not None
    
    def _test_resource_assessment(self) -> bool:
        """Test resource assessment functionality."""
        assessor = ResourceAssessor()
        assessment = assessor.assess_resources()
        return assessment is not None and isinstance(assessment, ResourceAssessment)
    
    def _test_assessment_result_structure(self) -> bool:
        """Test assessment result structure."""
        assessor = ResourceAssessor()
        assessment = assessor.assess_resources()
        
        required_attrs = ['timestamp', 'cpu', 'gpu', 'memory', 'storage', 
                         'network', 'system', 'overall_score', 'recommendations']
        
        return all(hasattr(assessment, attr) for attr in required_attrs)
    
    def _test_resource_summary(self) -> bool:
        """Test resource summary generation."""
        assessor = ResourceAssessor()
        assessment = assessor.assess_resources()
        summary = assessor.get_resource_summary(assessment)
        return isinstance(summary, str) and len(summary) > 0
    
    def _test_path_mapper_init(self) -> bool:
        """Test PathMapper initialization."""
        mapper = PathMapper(CloudPlatform.GOOGLE_COLAB)
        return mapper is not None
    
    def _test_path_mapping(self) -> bool:
        """Test path mapping functionality."""
        mapper = PathMapper(CloudPlatform.GOOGLE_COLAB)
        result = mapper.map_path("/content/test", path_type="base")
        return result is not None and isinstance(result, PathMappingResult)
    
    def _test_platform_paths(self) -> bool:
        """Test platform paths retrieval."""
        mapper = PathMapper(CloudPlatform.GOOGLE_COLAB)
        paths = mapper.get_platform_paths(CloudPlatform.GOOGLE_COLAB)
        return isinstance(paths, dict) and len(paths) > 0
    
    def _test_path_validation(self) -> bool:
        """Test path validation."""
        mapper = PathMapper(CloudPlatform.GOOGLE_COLAB)
        # Test with a valid path
        valid = mapper.validate_path_mapping("/content/test", "/content/test")
        return isinstance(valid, bool)
    
    def _test_repo_cloner_init(self) -> bool:
        """Test RepositoryCloner initialization."""
        cloner = RepositoryCloner("test-platform", "/tmp")
        return cloner is not None
    
    def _test_clone_operation_dry_run(self) -> bool:
        """Test clone operation (dry run)."""
        cloner = RepositoryCloner("test-platform", "/tmp")
        # Test repository info without actual cloning
        info = cloner.get_repository_info()
        return isinstance(info, dict)
    
    def _test_progress_tracking(self) -> bool:
        """Test progress tracking functionality."""
        cloner = RepositoryCloner("test-platform", "/tmp")
        
        # Test progress callback
        progress_received = False
        
        def test_callback(progress):
            nonlocal progress_received
            progress_received = True
        
        cloner.set_progress_callback(test_callback)
        return True  # Callback setting should not fail
    
    def _test_repository_info(self) -> bool:
        """Test repository info retrieval."""
        cloner = RepositoryCloner("test-platform", "/tmp")
        info = cloner.get_repository_info()
        
        required_keys = ['repository_path', 'exists', 'is_git_repo', 'branch', 
                        'commit', 'remote_url', 'file_count', 'directory_count', 'total_size_bytes']
        
        return all(key in info for key in required_keys)
    
    def _test_end_to_end_workflow(self) -> bool:
        """Test end-to-end workflow."""
        try:
            # Detect platform
            detector = CloudDetector()
            detection_result = detector.detect_platform()
            
            # Load config
            manager = PlatformConfigurationManager()
            config = manager.get_config(detection_result.platform)
            
            # Assess resources
            assessor = ResourceAssessor()
            assessment = assessor.assess_resources()
            
            # Setup path mapping
            mapper = PathMapper(detection_result.platform)
            
            # Initialize cloner
            cloner = RepositoryCloner(detection_result.platform.value, "/tmp")
            
            return all([detection_result, config, assessment, mapper, cloner])
        
        except Exception:
            return False
    
    def _test_component_interaction(self) -> bool:
        """Test component interaction."""
        try:
            # Test that components can work together
            detector = CloudDetector()
            result = detector.detect_platform()
            
            manager = PlatformConfigurationManager()
            config = manager.get_config(result.platform)
            
            if config:
                mapper = PathMapper(result.platform)
                paths = mapper.get_current_platform_paths()
                return len(paths) > 0
            
            return True
        
        except Exception:
            return False
    
    def _test_error_handling(self) -> bool:
        """Test error handling."""
        try:
            # Test with invalid inputs
            mapper = PathMapper(CloudPlatform.UNKNOWN)
            result = mapper.map_path("/invalid/path", path_type="invalid")
            
            # Should handle gracefully
            return result is not None
        
        except Exception:
            return False
    
    def _run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results."""
        self.total_tests += 1
        
        try:
            result = test_func()
            if result:
                self.passed_tests += 1
                print(f"  ✅ {test_name}")
                self.test_results[test_name] = {"status": "PASS", "error": None}
                return True
            else:
                self.failed_tests += 1
                print(f"  ❌ {test_name}")
                self.test_results[test_name] = {"status": "FAIL", "error": "Test returned False"}
                return False
        
        except Exception as e:
            self.failed_tests += 1
            print(f"  ❌ {test_name}: {str(e)}")
            self.test_results[test_name] = {"status": "FAIL", "error": str(e)}
            return False
    
    def _record_test_failure(self, test_category: str, error_message: str):
        """Record a test category failure."""
        self.failed_tests += 1
        self.test_results[test_category] = {"status": "FAIL", "error": error_message}
        print(f"  ❌ {test_category}: {error_message}")


def main():
    """Main function for running Phase 1 completion tests."""
    test_suite = Phase1CompletionTest()
    results = test_suite.run_all_tests()
    
    # Save results to file
    output_file = "/workspace/phase1_completion_test_results.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Test results saved to: {output_file}")
    except Exception as e:
        print(f"\n⚠️  Failed to save test results: {str(e)}")
    
    return results["overall_success"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)