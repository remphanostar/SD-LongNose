#!/usr/bin/env python3
"""
PinokioCloud App Test Suite - Phase 10

This module provides comprehensive testing of real Pinokio applications across
all categories (video, text, image, audio) to ensure end-to-end functionality.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import subprocess
import threading
import requests
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta

# Add the github_repo directory to Python path for imports
sys.path.append('/workspace/SD-LongNose/github_repo')

# Import all phases for comprehensive testing
from cloud_detection.cloud_detector import CloudDetector
from environment_management.venv_manager import VirtualEnvironmentManager
from environment_management.file_system import FileSystemManager
from app_analysis.app_analyzer import AppAnalyzer
from dependencies.dependency_finder import DependencyFinder
from engine.installer import ApplicationInstaller
from running.script_manager import ScriptManager
from tunneling.ngrok_manager import NgrokManager
from tunneling.url_manager import URLManager


@dataclass
class TestApplication:
    """Represents a test application for comprehensive testing."""
    name: str
    category: str
    git_url: str
    expected_port: int
    install_timeout: int = 300  # 5 minutes
    startup_timeout: int = 180  # 3 minutes
    test_endpoints: List[str] = field(default_factory=list)
    expected_ui_framework: str = "unknown"


@dataclass
class TestResult:
    """Result of an application test."""
    app_name: str
    category: str
    success: bool
    steps_completed: List[str]
    steps_failed: List[str]
    install_time: float
    startup_time: float
    public_url: Optional[str]
    error_details: Optional[str]
    timestamp: datetime


class AppTestSuite:
    """
    Comprehensive application testing suite for PinokioCloud.
    
    Tests real Pinokio applications across all categories to ensure
    complete end-to-end functionality from installation to public access.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose", ngrok_token: str = None):
        """Initialize the app test suite."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.apps_database_path = self.base_path / "cleaned_pinokio_apps.json"
        self.test_results: List[TestResult] = []
        
        # Initialize components
        self.cloud_detector = CloudDetector()
        self.venv_manager = VirtualEnvironmentManager()
        self.file_manager = FileSystemManager()
        self.app_analyzer = AppAnalyzer()
        self.dependency_finder = DependencyFinder()
        self.installer = ApplicationInstaller()
        self.script_manager = ScriptManager()
        self.ngrok_manager = NgrokManager()
        self.url_manager = URLManager()
        
        # Configure ngrok if token provided
        if ngrok_token:
            self.configure_ngrok(ngrok_token)
        
        # Define test applications (representative from each category)
        self.test_applications = self.load_test_applications()
    
    def configure_ngrok(self, token: str):
        """Configure ngrok authentication token."""
        try:
            import pyngrok
            from pyngrok import ngrok
            ngrok.set_auth_token(token)
            print("✅ Ngrok token configured successfully")
        except Exception as e:
            print(f"⚠️  Failed to configure ngrok: {e}")
    
    def load_test_applications(self) -> List[TestApplication]:
        """Load representative test applications from database."""
        test_apps = [
            # TEXT GENERATION
            TestApplication(
                name="text-generation-webui",
                category="TEXT",
                git_url="https://github.com/oobabooga/text-generation-webui",
                expected_port=7860,
                test_endpoints=["/", "/api/v1/model"],
                expected_ui_framework="gradio"
            ),
            
            # IMAGE GENERATION  
            TestApplication(
                name="AUTOMATIC1111",
                category="IMAGE", 
                git_url="https://github.com/AUTOMATIC1111/stable-diffusion-webui",
                expected_port=7860,
                test_endpoints=["/", "/sdapi/v1/txt2img"],
                expected_ui_framework="gradio"
            ),
            
            # AUDIO PROCESSING
            TestApplication(
                name="RVC-WebUI",
                category="AUDIO",
                git_url="https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI",
                expected_port=7865,
                test_endpoints=["/", "/api/predict"],
                expected_ui_framework="gradio"
            ),
            
            # VIDEO GENERATION
            TestApplication(
                name="AnimateAnyone",
                category="VIDEO",
                git_url="https://github.com/HumanAIGC/AnimateAnyone",
                expected_port=7860,
                test_endpoints=["/"],
                expected_ui_framework="gradio"
            ),
        ]
        
        # Load additional apps from database if available
        try:
            if self.apps_database_path.exists():
                with open(self.apps_database_path, 'r') as f:
                    apps_data = json.load(f)
                
                # Add 1-2 apps from each category from the database
                categories_added = set()
                for app in apps_data[:20]:  # Check first 20 apps
                    if app.get('category') and app['category'] not in categories_added:
                        if len(categories_added) < 8:  # Add up to 8 categories
                            test_app = TestApplication(
                                name=app.get('name', 'unknown'),
                                category=app.get('category', 'MISC'),
                                git_url=app.get('git', ''),
                                expected_port=7860,
                                test_endpoints=["/"],
                                expected_ui_framework=app.get('ui_framework', 'unknown')
                            )
                            test_apps.append(test_app)
                            categories_added.add(app['category'])
                            
        except Exception as e:
            print(f"⚠️  Could not load additional apps from database: {e}")
        
        return test_apps
    
    def test_application_installation(self, app: TestApplication) -> Tuple[bool, float, str]:
        """Test application installation process."""
        print(f"📦 Testing installation: {app.name}")
        start_time = time.time()
        
        try:
            # Create app directory
            app_path = self.base_path / "test_apps" / app.name
            app_path.mkdir(parents=True, exist_ok=True)
            
            # Clone repository (if git_url provided)
            if app.git_url:
                clone_cmd = ["git", "clone", app.git_url, str(app_path)]
                result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    return False, time.time() - start_time, f"Git clone failed: {result.stderr}"
            
            # Analyze application
            analysis = self.app_analyzer.analyze_app(app.name, str(app_path))
            if not analysis.get('installer_info'):
                return False, time.time() - start_time, "No installer detected"
            
            # Create virtual environment
            venv_path = app_path / "venv"
            venv_created = self.venv_manager.create_environment(
                str(venv_path), "venv", "3.13"
            )
            if not venv_created:
                return False, time.time() - start_time, "Virtual environment creation failed"
            
            # Install dependencies
            dep_info = self.dependency_finder.find_dependencies(str(app_path), app.category)
            if dep_info.get('pip_requirements'):
                install_result = self.installer.install_application(
                    app.name, str(app_path), {}, force_reinstall=False
                )
                if not install_result:
                    return False, time.time() - start_time, "Dependency installation failed"
            
            install_time = time.time() - start_time
            print(f"✅ Installation completed in {install_time:.1f}s")
            return True, install_time, "Success"
            
        except subprocess.TimeoutExpired:
            return False, time.time() - start_time, "Installation timeout"
        except Exception as e:
            return False, time.time() - start_time, f"Installation error: {str(e)}"
    
    def test_application_startup(self, app: TestApplication) -> Tuple[bool, float, str]:
        """Test application startup and web UI accessibility."""
        print(f"🚀 Testing startup: {app.name}")
        start_time = time.time()
        
        try:
            app_path = self.base_path / "test_apps" / app.name
            
            # Start application
            startup_success = self.script_manager.start_application(
                app.name, str(app_path), daemon=True
            )
            if not startup_success:
                return False, time.time() - start_time, "Application startup failed"
            
            # Wait for web UI to become available
            max_wait = app.startup_timeout
            wait_time = 0
            ui_accessible = False
            
            while wait_time < max_wait:
                try:
                    response = requests.get(f"http://localhost:{app.expected_port}", timeout=5)
                    if response.status_code == 200:
                        ui_accessible = True
                        break
                except requests.exceptions.RequestException:
                    pass
                
                time.sleep(10)
                wait_time += 10
            
            startup_time = time.time() - start_time
            
            if ui_accessible:
                print(f"✅ Startup completed in {startup_time:.1f}s")
                return True, startup_time, "Success"
            else:
                return False, startup_time, "Web UI not accessible within timeout"
                
        except Exception as e:
            return False, time.time() - start_time, f"Startup error: {str(e)}"
    
    def test_public_tunnel_creation(self, app: TestApplication) -> Tuple[bool, str]:
        """Test creation of public tunnel for application."""
        print(f"🌐 Testing public tunnel: {app.name}")
        
        try:
            # Create ngrok tunnel
            tunnel_info = self.ngrok_manager.create_tunnel(
                app.expected_port, f"{app.name}-test"
            )
            
            if tunnel_info and tunnel_info.get('public_url'):
                public_url = tunnel_info['public_url']
                
                # Test public URL accessibility
                try:
                    response = requests.get(public_url, timeout=15)
                    if response.status_code == 200:
                        print(f"✅ Public tunnel created: {public_url}")
                        return True, public_url
                    else:
                        return False, f"Public URL not accessible: {response.status_code}"
                except Exception as e:
                    return False, f"Public URL test failed: {e}"
            else:
                return False, "Tunnel creation failed"
                
        except Exception as e:
            return False, f"Tunnel creation error: {str(e)}"
    
    def test_application_endpoints(self, app: TestApplication, base_url: str) -> List[str]:
        """Test specific application endpoints."""
        print(f"🧪 Testing endpoints: {app.name}")
        working_endpoints = []
        
        for endpoint in app.test_endpoints:
            try:
                url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
                response = requests.get(url, timeout=10)
                if response.status_code < 500:  # Accept any non-server-error status
                    working_endpoints.append(endpoint)
                    print(f"  ✅ {endpoint}: {response.status_code}")
                else:
                    print(f"  ❌ {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"  ❌ {endpoint}: {e}")
        
        return working_endpoints
    
    def cleanup_application(self, app: TestApplication):
        """Clean up application resources after testing."""
        try:
            # Stop application
            self.script_manager.stop_application(app.name)
            
            # Remove test directory
            app_path = self.base_path / "test_apps" / app.name
            if app_path.exists():
                import shutil
                shutil.rmtree(app_path, ignore_errors=True)
                
            print(f"🧹 Cleaned up: {app.name}")
        except Exception as e:
            print(f"⚠️  Cleanup error for {app.name}: {e}")
    
    def test_single_application(self, app: TestApplication) -> TestResult:
        """Test a single application end-to-end."""
        print(f"\n🎯 Testing Application: {app.name} ({app.category})")
        print("=" * 60)
        
        steps_completed = []
        steps_failed = []
        install_time = 0.0
        startup_time = 0.0
        public_url = None
        error_details = None
        overall_success = True
        
        try:
            # Step 1: Installation
            install_success, install_time, install_error = self.test_application_installation(app)
            if install_success:
                steps_completed.append("installation")
            else:
                steps_failed.append("installation")
                error_details = install_error
                overall_success = False
                
            # Step 2: Startup (only if installation succeeded)
            if install_success:
                startup_success, startup_time, startup_error = self.test_application_startup(app)
                if startup_success:
                    steps_completed.append("startup")
                else:
                    steps_failed.append("startup")
                    error_details = startup_error
                    overall_success = False
                
                # Step 3: Public tunnel (only if startup succeeded)
                if startup_success:
                    tunnel_success, tunnel_result = self.test_public_tunnel_creation(app)
                    if tunnel_success:
                        steps_completed.append("tunnel")
                        public_url = tunnel_result
                        
                        # Step 4: Endpoint testing
                        working_endpoints = self.test_application_endpoints(app, public_url)
                        if working_endpoints:
                            steps_completed.append("endpoints")
                        else:
                            steps_failed.append("endpoints")
                            overall_success = False
                    else:
                        steps_failed.append("tunnel")
                        error_details = tunnel_result
                        overall_success = False
            
        except Exception as e:
            error_details = f"Unexpected error: {str(e)}"
            overall_success = False
        
        finally:
            # Always cleanup
            self.cleanup_application(app)
        
        # Create test result
        result = TestResult(
            app_name=app.name,
            category=app.category,
            success=overall_success,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            install_time=install_time,
            startup_time=startup_time,
            public_url=public_url,
            error_details=error_details,
            timestamp=datetime.now()
        )
        
        self.test_results.append(result)
        return result
    
    def run_comprehensive_test(self, max_apps: int = 4) -> Dict[str, Any]:
        """Run comprehensive testing on selected applications."""
        print("🎯 PinokioCloud Comprehensive Application Testing")
        print("=" * 70)
        
        start_time = datetime.now()
        
        # Test up to max_apps applications
        apps_to_test = self.test_applications[:max_apps]
        
        print(f"📋 Testing {len(apps_to_test)} applications:")
        for i, app in enumerate(apps_to_test, 1):
            print(f"  {i}. {app.name} ({app.category})")
        
        # Run tests
        for app in apps_to_test:
            result = self.test_single_application(app)
            
            # Show result summary
            status = "✅ PASSED" if result.success else "❌ FAILED"
            steps = f"{len(result.steps_completed)}/{len(result.steps_completed) + len(result.steps_failed)}"
            print(f"{status} - {app.name}: {steps} steps completed")
            
            if result.public_url:
                print(f"  🌐 Public URL: {result.public_url}")
        
        end_time = datetime.now()
        
        # Generate comprehensive report
        return self.generate_test_report(start_time, end_time)
    
    def generate_test_report(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_apps = len(self.test_results)
        successful_apps = sum(1 for r in self.test_results if r.success)
        success_rate = (successful_apps / total_apps) * 100 if total_apps > 0 else 0
        
        # Categorize results
        results_by_category = {}
        for result in self.test_results:
            if result.category not in results_by_category:
                results_by_category[result.category] = []
            results_by_category[result.category].append(result)
        
        # Calculate step success rates
        step_stats = {}
        all_steps = ["installation", "startup", "tunnel", "endpoints"]
        for step in all_steps:
            completed = sum(1 for r in self.test_results if step in r.steps_completed)
            step_stats[step] = (completed / total_apps) * 100 if total_apps > 0 else 0
        
        report = {
            'test_summary': {
                'total_applications': total_apps,
                'successful_applications': successful_apps,
                'failed_applications': total_apps - successful_apps,
                'success_rate': success_rate,
                'test_duration': str(end_time - start_time),
                'timestamp': datetime.now().isoformat()
            },
            'step_success_rates': step_stats,
            'results_by_category': {
                cat: {
                    'total': len(results),
                    'successful': sum(1 for r in results if r.success),
                    'applications': [r.app_name for r in results]
                }
                for cat, results in results_by_category.items()
            },
            'detailed_results': [
                {
                    'app_name': r.app_name,
                    'category': r.category,
                    'success': r.success,
                    'steps_completed': r.steps_completed,
                    'steps_failed': r.steps_failed,
                    'install_time': r.install_time,
                    'startup_time': r.startup_time,
                    'public_url': r.public_url,
                    'error_details': r.error_details
                }
                for r in self.test_results
            ],
            'recommendations': self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if not self.test_results:
            return ["No test results available for analysis."]
        
        total_apps = len(self.test_results)
        successful_apps = sum(1 for r in self.test_results if r.success)
        
        # Overall performance recommendations
        if successful_apps == total_apps:
            recommendations.append("🎉 All applications tested successfully! System is ready for production.")
        elif successful_apps >= total_apps * 0.8:
            recommendations.append("✅ Most applications working well. Minor fixes needed.")
        elif successful_apps >= total_apps * 0.5:
            recommendations.append("⚠️  Moderate issues detected. Requires attention before production.")
        else:
            recommendations.append("❌ Major issues detected. Significant fixes required.")
        
        # Step-specific recommendations
        step_failures = {}
        for result in self.test_results:
            for step in result.steps_failed:
                step_failures[step] = step_failures.get(step, 0) + 1
        
        for step, failure_count in step_failures.items():
            if failure_count >= total_apps * 0.5:
                if step == "installation":
                    recommendations.append("🔧 High installation failure rate - check dependency management.")
                elif step == "startup":
                    recommendations.append("🚀 High startup failure rate - check application launching.")
                elif step == "tunnel":
                    recommendations.append("🌐 High tunnel failure rate - check ngrok configuration.")
                elif step == "endpoints":
                    recommendations.append("🧪 High endpoint failure rate - check application responses.")
        
        return recommendations
    
    def save_test_report(self, report: Dict[str, Any], filename: str = None):
        """Save test report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pinokiocloud_test_report_{timestamp}.json"
        
        report_path = self.base_path / filename
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📊 Test report saved: {report_path}")


def main():
    """Main testing function."""
    print("🎯 PinokioCloud Application Test Suite - Phase 10")
    print("=" * 60)
    
    # Initialize test suite with ngrok token
    ngrok_token = "2tjxIXifSaGR3dMhkvhk6sZqbGo_6ZfBZLZHMbtAjfRmfoDW5"
    test_suite = AppTestSuite(ngrok_token=ngrok_token)
    
    # Run comprehensive testing
    report = test_suite.run_comprehensive_test(max_apps=4)
    
    # Print summary
    print("\n📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 50)
    summary = report['test_summary']
    print(f"Total Applications: {summary['total_applications']}")
    print(f"Successful: {summary['successful_applications']}")
    print(f"Failed: {summary['failed_applications']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Test Duration: {summary['test_duration']}")
    
    print("\n📈 Step Success Rates:")
    for step, rate in report['step_success_rates'].items():
        print(f"  {step}: {rate:.1f}%")
    
    print("\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    # Save report
    test_suite.save_test_report(report)
    
    return report['test_summary']['success_rate'] >= 75  # Return True if success rate >= 75%


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)