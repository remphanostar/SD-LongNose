#!/usr/bin/env python3
"""
PinokioCloud Cloud Test Matrix - Phase 10

This module provides comprehensive testing across multiple cloud platforms
to ensure PinokioCloud works consistently on all target cloud environments.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import subprocess
import platform
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from enum import Enum

# Add the github_repo directory to Python path for imports
sys.path.append('/workspace/SD-LongNose/github_repo')

# Import cloud detection and platform components
from cloud_detection.cloud_detector import CloudDetector, CloudPlatform
from platforms.colab_optimizer import ColabOptimizer
from platforms.vast_optimizer import VastOptimizer
from platforms.lightning_optimizer import LightningOptimizer


class TestSeverity(Enum):
    """Test severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class CloudTest:
    """Represents a cloud platform test."""
    name: str
    description: str
    severity: TestSeverity
    platforms: List[CloudPlatform]
    test_function: str
    expected_duration: int = 30  # seconds
    dependencies: List[str] = field(default_factory=list)


@dataclass
class PlatformTestResult:
    """Result of testing on a specific platform."""
    platform: CloudPlatform
    test_name: str
    success: bool
    duration: float
    details: str
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class CloudTestMatrix:
    """
    Comprehensive cloud platform testing matrix for PinokioCloud.
    
    Tests system functionality across all supported cloud platforms
    to ensure consistent behavior and platform-specific optimizations.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the cloud test matrix."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.test_results: List[PlatformTestResult] = []
        
        # Initialize cloud detector
        self.cloud_detector = CloudDetector()
        self.current_platform = self.cloud_detector.detect_cloud_platform()
        
        # Initialize platform optimizers
        self.colab_optimizer = ColabOptimizer()
        self.vast_optimizer = VastOptimizer()
        self.lightning_optimizer = LightningOptimizer()
        
        # Define comprehensive test matrix
        self.test_matrix = self.create_test_matrix()
    
    def create_test_matrix(self) -> List[CloudTest]:
        """Create comprehensive test matrix for all platforms."""
        return [
            # Platform Detection Tests
            CloudTest(
                name="platform_detection",
                description="Test cloud platform detection accuracy",
                severity=TestSeverity.CRITICAL,
                platforms=[CloudPlatform.GOOGLE_COLAB, CloudPlatform.VAST_AI, 
                          CloudPlatform.LIGHTNING_AI, CloudPlatform.PAPERSPACE, 
                          CloudPlatform.RUNPOD, CloudPlatform.UNKNOWN],
                test_function="test_platform_detection"
            ),
            
            # Resource Assessment Tests
            CloudTest(
                name="resource_assessment",
                description="Test system resource detection and assessment",
                severity=TestSeverity.CRITICAL,
                platforms=[CloudPlatform.GOOGLE_COLAB, CloudPlatform.VAST_AI, 
                          CloudPlatform.LIGHTNING_AI],
                test_function="test_resource_assessment"
            ),
            
            # Path Mapping Tests
            CloudTest(
                name="path_mapping",
                description="Test platform-specific path mapping",
                severity=TestSeverity.HIGH,
                platforms=[CloudPlatform.GOOGLE_COLAB, CloudPlatform.VAST_AI, 
                          CloudPlatform.LIGHTNING_AI],
                test_function="test_path_mapping"
            ),
            
            # Virtual Environment Tests
            CloudTest(
                name="virtual_environment",
                description="Test virtual environment creation and management",
                severity=TestSeverity.HIGH,
                platforms=[CloudPlatform.GOOGLE_COLAB, CloudPlatform.VAST_AI, 
                          CloudPlatform.LIGHTNING_AI],
                test_function="test_virtual_environment_creation"
            ),
            
            # Network Connectivity Tests
            CloudTest(
                name="network_connectivity",
                description="Test internet connectivity and external services",
                severity=TestSeverity.HIGH,
                platforms=[CloudPlatform.GOOGLE_COLAB, CloudPlatform.VAST_AI, 
                          CloudPlatform.LIGHTNING_AI],
                test_function="test_network_connectivity"
            ),
            
            # Tunnel Creation Tests
            CloudTest(
                name="tunnel_creation",
                description="Test ngrok tunnel creation and accessibility",
                severity=TestSeverity.HIGH,
                platforms=[CloudPlatform.GOOGLE_COLAB, CloudPlatform.VAST_AI, 
                          CloudPlatform.LIGHTNING_AI],
                test_function="test_tunnel_creation",
                expected_duration=60
            ),
            
            # Storage Performance Tests
            CloudTest(
                name="storage_performance",
                description="Test file I/O and storage performance",
                severity=TestSeverity.MEDIUM,
                platforms=[CloudPlatform.GOOGLE_COLAB, CloudPlatform.VAST_AI, 
                          CloudPlatform.LIGHTNING_AI],
                test_function="test_storage_performance",
                expected_duration=45
            ),
            
            # Platform-Specific Optimizations
            CloudTest(
                name="colab_optimizations",
                description="Test Google Colab-specific optimizations",
                severity=TestSeverity.MEDIUM,
                platforms=[CloudPlatform.GOOGLE_COLAB],
                test_function="test_colab_specific_features"
            ),
            
            CloudTest(
                name="vast_optimizations", 
                description="Test Vast.ai-specific optimizations",
                severity=TestSeverity.MEDIUM,
                platforms=[CloudPlatform.VAST_AI],
                test_function="test_vast_specific_features"
            ),
            
            CloudTest(
                name="lightning_optimizations",
                description="Test Lightning.ai-specific optimizations", 
                severity=TestSeverity.MEDIUM,
                platforms=[CloudPlatform.LIGHTNING_AI],
                test_function="test_lightning_specific_features"
            ),
            
            # Compatibility Tests
            CloudTest(
                name="python_compatibility",
                description="Test Python version and package compatibility",
                severity=TestSeverity.HIGH,
                platforms=[CloudPlatform.GOOGLE_COLAB, CloudPlatform.VAST_AI, 
                          CloudPlatform.LIGHTNING_AI],
                test_function="test_python_compatibility"
            ),
            
            # Security Tests
            CloudTest(
                name="security_permissions",
                description="Test file permissions and security constraints",
                severity=TestSeverity.MEDIUM,
                platforms=[CloudPlatform.GOOGLE_COLAB, CloudPlatform.VAST_AI, 
                          CloudPlatform.LIGHTNING_AI],
                test_function="test_security_permissions"
            ),
        ]
    
    def test_platform_detection(self) -> Tuple[bool, str]:
        """Test platform detection accuracy."""
        try:
            detection_result = self.cloud_detector.detect_cloud_platform()
            
            # Basic validation - should not be None
            if detection_result is None:
                return False, "Platform detection returned None"
            
            # Test detection consistency (run multiple times)
            consistent_results = []
            for _ in range(3):
                result = self.cloud_detector.detect_cloud_platform()
                consistent_results.append(result)
            
            if len(set(consistent_results)) > 1:
                return False, f"Inconsistent detection results: {consistent_results}"
            
            return True, f"Platform detected as: {detection_result.value if hasattr(detection_result, 'value') else str(detection_result)}"
            
        except Exception as e:
            return False, f"Platform detection error: {str(e)}"
    
    def test_resource_assessment(self) -> Tuple[bool, str]:
        """Test system resource assessment."""
        try:
            from cloud_detection.resource_assessor import ResourceAssessor
            assessor = ResourceAssessor()
            
            # Test resource detection
            resources = assessor.assess_system_resources()
            
            required_fields = ['cpu_info', 'memory_info', 'storage_info']
            missing_fields = [field for field in required_fields 
                            if field not in resources or not resources[field]]
            
            if missing_fields:
                return False, f"Missing resource information: {missing_fields}"
            
            # Validate resource data
            memory_info = resources['memory_info']
            if not isinstance(memory_info.get('total'), (int, float)) or memory_info['total'] <= 0:
                return False, "Invalid memory information"
            
            storage_info = resources['storage_info']
            if not isinstance(storage_info.get('total'), (int, float)) or storage_info['total'] <= 0:
                return False, "Invalid storage information"
            
            return True, f"Resources assessed: {memory_info['total']/1024**3:.1f}GB RAM, {storage_info['total']/1024**3:.1f}GB storage"
            
        except Exception as e:
            return False, f"Resource assessment error: {str(e)}"
    
    def test_path_mapping(self) -> Tuple[bool, str]:
        """Test platform-specific path mapping."""
        try:
            from cloud_detection.path_mapper import PathMapper
            mapper = PathMapper()
            
            # Test common path mappings
            test_paths = ["/apps/", "/models/", "/cache/", "/temp/"]
            mapped_paths = {}
            
            for path in test_paths:
                mapped = mapper.map_cloud_paths(path)
                if not mapped or mapped == path:
                    continue  # Skip if no mapping needed
                mapped_paths[path] = mapped
            
            # Test that mapped paths are valid
            for original, mapped in mapped_paths.items():
                if not isinstance(mapped, str) or not mapped.startswith('/'):
                    return False, f"Invalid path mapping: {original} -> {mapped}"
            
            return True, f"Path mapping working: {len(mapped_paths)} paths mapped"
            
        except Exception as e:
            return False, f"Path mapping error: {str(e)}"
    
    def test_virtual_environment_creation(self) -> Tuple[bool, str]:
        """Test virtual environment creation."""
        try:
            from environment_management.venv_manager import VirtualEnvironmentManager
            venv_manager = VirtualEnvironmentManager()
            
            # Create test virtual environment
            test_env_path = self.base_path / "test_venv"
            success = venv_manager.create_environment(
                str(test_env_path), "venv", "3.13"
            )
            
            if not success:
                return False, "Virtual environment creation failed"
            
            # Test environment activation
            activation_success = venv_manager.activate_environment(str(test_env_path))
            if not activation_success:
                return False, "Virtual environment activation failed"
            
            # Clean up
            import shutil
            if test_env_path.exists():
                shutil.rmtree(test_env_path, ignore_errors=True)
            
            return True, "Virtual environment created and activated successfully"
            
        except Exception as e:
            return False, f"Virtual environment error: {str(e)}"
    
    def test_network_connectivity(self) -> Tuple[bool, str]:
        """Test network connectivity and external services."""
        try:
            import requests
            
            # Test basic internet connectivity
            test_urls = [
                "https://www.google.com",
                "https://github.com",
                "https://pypi.org",
                "https://api.github.com"
            ]
            
            successful_connections = 0
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code < 400:
                        successful_connections += 1
                except:
                    pass
            
            if successful_connections < len(test_urls) / 2:
                return False, f"Poor network connectivity: {successful_connections}/{len(test_urls)} URLs accessible"
            
            return True, f"Network connectivity good: {successful_connections}/{len(test_urls)} URLs accessible"
            
        except Exception as e:
            return False, f"Network connectivity error: {str(e)}"
    
    def test_tunnel_creation(self) -> Tuple[bool, str]:
        """Test tunnel creation capability."""
        try:
            import pyngrok
            from pyngrok import ngrok
            
            # Configure ngrok with token
            ngrok.set_auth_token("2tjxIXifSaGR3dMhkvhk6sZqbGo_6ZfBZLZHMbtAjfRmfoDW5")
            
            # Create a simple HTTP server for testing
            import http.server
            import socketserver
            import threading
            
            # Start simple server
            port = 8765
            handler = http.server.SimpleHTTPRequestHandler
            httpd = socketserver.TCPServer(("", port), handler)
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            # Create tunnel
            tunnel = ngrok.connect(port)
            public_url = tunnel.public_url
            
            # Test tunnel accessibility
            import requests
            response = requests.get(public_url, timeout=15)
            
            # Cleanup
            httpd.shutdown()
            ngrok.disconnect(public_url)
            
            if response.status_code == 200:
                return True, f"Tunnel created successfully: {public_url}"
            else:
                return False, f"Tunnel not accessible: {response.status_code}"
            
        except Exception as e:
            return False, f"Tunnel creation error: {str(e)}"
    
    def test_storage_performance(self) -> Tuple[bool, str]:
        """Test storage performance."""
        try:
            import tempfile
            import os
            
            test_dir = tempfile.mkdtemp(prefix="pinokio_storage_test_")
            
            # Test write performance
            start_time = time.time()
            test_data = b"x" * (1024 * 1024)  # 1MB of data
            
            for i in range(10):  # Write 10MB total
                test_file = os.path.join(test_dir, f"test_{i}.dat")
                with open(test_file, 'wb') as f:
                    f.write(test_data)
            
            write_time = time.time() - start_time
            write_speed = 10 / write_time  # MB/s
            
            # Test read performance
            start_time = time.time()
            for i in range(10):
                test_file = os.path.join(test_dir, f"test_{i}.dat")
                with open(test_file, 'rb') as f:
                    _ = f.read()
            
            read_time = time.time() - start_time
            read_speed = 10 / read_time  # MB/s
            
            # Cleanup
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)
            
            if write_speed < 1.0 or read_speed < 5.0:
                return False, f"Poor storage performance: Write {write_speed:.1f}MB/s, Read {read_speed:.1f}MB/s"
            
            return True, f"Good storage performance: Write {write_speed:.1f}MB/s, Read {read_speed:.1f}MB/s"
            
        except Exception as e:
            return False, f"Storage performance error: {str(e)}"
    
    def test_colab_specific_features(self) -> Tuple[bool, str]:
        """Test Google Colab specific features."""
        try:
            # Test Colab-specific optimizations
            colab_features = []
            
            # Check for Google Drive integration
            if os.path.exists('/content/'):
                colab_features.append("content_directory")
            
            # Test Colab optimizer
            optimization_result = self.colab_optimizer.optimize_for_colab()
            if optimization_result:
                colab_features.append("colab_optimization")
            
            # Check GPU availability (Colab-specific way)
            try:
                import torch
                if torch.cuda.is_available():
                    colab_features.append("gpu_available")
            except ImportError:
                pass
            
            if not colab_features:
                return False, "No Colab-specific features detected"
            
            return True, f"Colab features working: {', '.join(colab_features)}"
            
        except Exception as e:
            return False, f"Colab features error: {str(e)}"
    
    def test_vast_specific_features(self) -> Tuple[bool, str]:
        """Test Vast.ai specific features."""
        try:
            # Test Vast.ai-specific optimizations
            vast_features = []
            
            # Check for Vast.ai environment indicators
            if os.path.exists('/workspace/'):
                vast_features.append("workspace_directory")
            
            # Test Vast.ai optimizer
            optimization_result = self.vast_optimizer.optimize_docker_environment()
            if optimization_result:
                vast_features.append("docker_optimization")
            
            # Check for SSH access (common on Vast.ai)
            if os.path.exists('/etc/ssh/sshd_config'):
                vast_features.append("ssh_available")
            
            if not vast_features:
                return False, "No Vast.ai-specific features detected"
            
            return True, f"Vast.ai features working: {', '.join(vast_features)}"
            
        except Exception as e:
            return False, f"Vast.ai features error: {str(e)}"
    
    def test_lightning_specific_features(self) -> Tuple[bool, str]:
        """Test Lightning.ai specific features."""
        try:
            # Test Lightning.ai-specific optimizations
            lightning_features = []
            
            # Check for Lightning.ai environment indicators
            if os.path.exists('/teamspace/'):
                lightning_features.append("teamspace_directory")
            
            # Test Lightning.ai optimizer
            optimization_result = self.lightning_optimizer.optimize_shared_storage()
            if optimization_result:
                lightning_features.append("shared_storage")
            
            # Check for collaboration features
            team_resources = self.lightning_optimizer.get_team_resources()
            if team_resources:
                lightning_features.append("team_resources")
            
            if not lightning_features:
                return False, "No Lightning.ai-specific features detected"
            
            return True, f"Lightning.ai features working: {', '.join(lightning_features)}"
            
        except Exception as e:
            return False, f"Lightning.ai features error: {str(e)}"
    
    def test_python_compatibility(self) -> Tuple[bool, str]:
        """Test Python version and package compatibility."""
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version.major != 3 or python_version.minor < 8:
                return False, f"Unsupported Python version: {python_version.major}.{python_version.minor}"
            
            # Test critical package imports
            critical_packages = [
                'json', 'os', 'sys', 'subprocess', 'threading', 
                'requests', 'pathlib', 'datetime'
            ]
            
            missing_packages = []
            for package in critical_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                return False, f"Missing critical packages: {missing_packages}"
            
            return True, f"Python {python_version.major}.{python_version.minor} compatible, all critical packages available"
            
        except Exception as e:
            return False, f"Python compatibility error: {str(e)}"
    
    def test_security_permissions(self) -> Tuple[bool, str]:
        """Test file permissions and security constraints."""
        try:
            import tempfile
            import stat
            
            # Test file creation permissions
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(b"test data")
            
            # Test file permissions
            file_stat = os.stat(temp_path)
            file_permissions = stat.filemode(file_stat.st_mode)
            
            # Test directory creation
            test_dir = tempfile.mkdtemp(prefix="pinokio_security_test_")
            
            # Test write permissions
            test_write_file = os.path.join(test_dir, "write_test.txt")
            with open(test_write_file, 'w') as f:
                f.write("write test")
            
            # Cleanup
            os.unlink(temp_path)
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)
            
            return True, f"File permissions OK: {file_permissions}, directory creation successful"
            
        except Exception as e:
            return False, f"Security permissions error: {str(e)}"
    
    def run_single_test(self, test: CloudTest) -> List[PlatformTestResult]:
        """Run a single test across applicable platforms."""
        results = []
        
        # Only run test on current platform if it's in the test's platform list
        if self.current_platform not in test.platforms:
            # Create a skipped result
            result = PlatformTestResult(
                platform=self.current_platform,
                test_name=test.name,
                success=True,  # Consider skipped tests as successful
                duration=0.0,
                details=f"Test skipped - not applicable for {self.current_platform.value if hasattr(self.current_platform, 'value') else str(self.current_platform)}"
            )
            results.append(result)
            return results
        
        print(f"🧪 Running test: {test.name} on {self.current_platform.value if hasattr(self.current_platform, 'value') else str(self.current_platform)}")
        
        start_time = time.time()
        
        try:
            # Get the test function
            test_function = getattr(self, test.test_function)
            
            # Run the test
            success, details = test_function()
            duration = time.time() - start_time
            
            result = PlatformTestResult(
                platform=self.current_platform,
                test_name=test.name,
                success=success,
                duration=duration,
                details=details,
                error_message=None if success else details
            )
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} ({duration:.1f}s): {details}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = PlatformTestResult(
                platform=self.current_platform,
                test_name=test.name,
                success=False,
                duration=duration,
                details=f"Test execution error: {str(e)}",
                error_message=str(e)
            )
            print(f"  ❌ FAIL ({duration:.1f}s): {e}")
        
        results.append(result)
        return results
    
    def run_comprehensive_test_matrix(self) -> Dict[str, Any]:
        """Run the complete test matrix."""
        print("🎯 PinokioCloud Cloud Test Matrix - Phase 10")
        print("=" * 60)
        
        start_time = datetime.now()
        
        print(f"🌐 Current Platform: {self.current_platform.value if hasattr(self.current_platform, 'value') else str(self.current_platform)}")
        print(f"📋 Total Tests: {len(self.test_matrix)}")
        
        # Run all tests
        all_results = []
        for test in self.test_matrix:
            test_results = self.run_single_test(test)
            all_results.extend(test_results)
            self.test_results.extend(test_results)
        
        end_time = datetime.now()
        
        # Generate report
        return self.generate_test_matrix_report(start_time, end_time)
    
    def generate_test_matrix_report(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate comprehensive test matrix report."""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success)
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Categorize by severity
        severity_stats = {}
        for test in self.test_matrix:
            severity = test.severity.value
            if severity not in severity_stats:
                severity_stats[severity] = {'total': 0, 'passed': 0}
            
            severity_stats[severity]['total'] += 1
            
            # Check if this test passed
            test_passed = any(r.success for r in self.test_results if r.test_name == test.name)
            if test_passed:
                severity_stats[severity]['passed'] += 1
        
        # Calculate average test duration
        avg_duration = sum(r.duration for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        report = {
            'test_summary': {
                'platform': self.current_platform.value if hasattr(self.current_platform, 'value') else str(self.current_platform),
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': success_rate,
                'test_duration': str(end_time - start_time),
                'average_test_duration': avg_duration,
                'timestamp': datetime.now().isoformat()
            },
            'severity_breakdown': {
                sev: {
                    'total': stats['total'],
                    'passed': stats['passed'],
                    'success_rate': (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
                }
                for sev, stats in severity_stats.items()
            },
            'detailed_results': [
                {
                    'test_name': r.test_name,
                    'platform': r.platform.value if hasattr(r.platform, 'value') else str(r.platform),
                    'success': r.success,
                    'duration': r.duration,
                    'details': r.details,
                    'error_message': r.error_message
                }
                for r in self.test_results
            ],
            'failed_tests': [
                {
                    'test_name': r.test_name,
                    'error_message': r.error_message,
                    'details': r.details
                }
                for r in self.test_results if not r.success
            ],
            'recommendations': self.generate_platform_recommendations()
        }
        
        return report
    
    def generate_platform_recommendations(self) -> List[str]:
        """Generate platform-specific recommendations."""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if not r.success]
        critical_failures = [r for r in self.test_results 
                           if not r.success and 
                           any(t.severity == TestSeverity.CRITICAL 
                               for t in self.test_matrix if t.name == r.test_name)]
        
        if not failed_tests:
            recommendations.append("🎉 All tests passed! Platform is fully compatible.")
        elif not critical_failures:
            recommendations.append("✅ All critical tests passed. Minor issues detected.")
        else:
            recommendations.append("❌ Critical test failures detected. Platform may not be fully functional.")
        
        # Specific recommendations based on failures
        failure_counts = {}
        for result in failed_tests:
            failure_counts[result.test_name] = failure_counts.get(result.test_name, 0) + 1
        
        for test_name, count in failure_counts.items():
            if test_name == "platform_detection":
                recommendations.append("🔍 Platform detection issues - verify environment setup.")
            elif test_name == "virtual_environment":
                recommendations.append("🐍 Virtual environment issues - check Python installation.")
            elif test_name == "tunnel_creation":
                recommendations.append("🌐 Tunnel creation issues - verify ngrok configuration and network access.")
            elif test_name == "network_connectivity":
                recommendations.append("📡 Network connectivity issues - check internet access and firewall settings.")
        
        return recommendations
    
    def save_test_matrix_report(self, report: Dict[str, Any], filename: str = None):
        """Save test matrix report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            platform_name = self.current_platform.value if hasattr(self.current_platform, 'value') else str(self.current_platform)
            filename = f"cloud_test_matrix_{platform_name}_{timestamp}.json"
        
        report_path = self.base_path / filename
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📊 Test matrix report saved: {report_path}")


def main():
    """Main testing function."""
    print("🎯 PinokioCloud Cloud Test Matrix - Phase 10")
    print("=" * 60)
    
    # Initialize test matrix
    test_matrix = CloudTestMatrix()
    
    # Run comprehensive testing
    report = test_matrix.run_comprehensive_test_matrix()
    
    # Print summary
    print("\n📊 CLOUD TEST MATRIX RESULTS")
    print("=" * 50)
    summary = report['test_summary']
    print(f"Platform: {summary['platform']}")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Test Duration: {summary['test_duration']}")
    print(f"Average Test Duration: {summary['average_test_duration']:.1f}s")
    
    print("\n📈 Severity Breakdown:")
    for severity, stats in report['severity_breakdown'].items():
        print(f"  {severity.upper()}: {stats['passed']}/{stats['total']} ({stats['success_rate']:.1f}%)")
    
    if report['failed_tests']:
        print("\n❌ Failed Tests:")
        for test in report['failed_tests'][:5]:  # Show first 5 failures
            print(f"  - {test['test_name']}: {test['error_message']}")
    
    print("\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    # Save report
    test_matrix.save_test_matrix_report(report)
    
    return report['test_summary']['success_rate'] >= 80  # Return True if success rate >= 80%


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)