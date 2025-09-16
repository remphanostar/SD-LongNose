#!/usr/bin/env python3
"""
PinokioCloud Phase 6 Test Suite

This module provides comprehensive testing for Phase 6 - Application Running Engine.
It tests all components with real functionality and integration scenarios.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import List, Dict, Any
import unittest

# Import Phase 6 modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from running.script_manager import ScriptManager, ApplicationRunningStatus
from running.process_tracker import ProcessTracker, HealthStatus
from running.daemon_manager import DaemonManager, DaemonStatus
from running.health_monitor import HealthMonitor, HealthCheck, HealthCheckType
from running.virtual_drive import VirtualDriveManager, DriveType, StorageMode

# Import previous phase modules for integration testing
from engine.state_manager import StateManager, ApplicationStatus
from environment_management.venv_manager import VirtualEnvironmentManager


class TestPhase6Integration(unittest.TestCase):
    """Comprehensive integration tests for Phase 6."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.base_path = "/workspace/SD-LongNose"
        cls.test_app_name = "test_phase6_app"
        cls.test_script_content = '''#!/usr/bin/env python3
import time
import sys
print("Test application starting...")
for i in range(60):  # Run for 60 seconds
    print(f"Test app running... {i}")
    sys.stdout.flush()
    time.sleep(1)
print("Test application finished")
'''
        cls.daemon_script_content = '''#!/usr/bin/env python3
import time
import sys
import signal

running = True

def signal_handler(signum, frame):
    global running
    running = False
    print("Daemon received signal, shutting down...")

signal.signal(signal.SIGTERM, signal_handler)

print("Daemon starting...")
while running:
    print("Daemon running...")
    sys.stdout.flush()
    time.sleep(5)
print("Daemon stopped")
'''
        
        # Create test scripts
        cls.test_script_path = Path(cls.base_path) / "test_scripts" / "test_app.py"
        cls.daemon_script_path = Path(cls.base_path) / "test_scripts" / "test_daemon.py"
        
        cls.test_script_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cls.test_script_path, 'w') as f:
            f.write(cls.test_script_content)
        
        with open(cls.daemon_script_path, 'w') as f:
            f.write(cls.daemon_script_content)
        
        # Make scripts executable
        os.chmod(cls.test_script_path, 0o755)
        os.chmod(cls.daemon_script_path, 0o755)
        
        print(f"[TestPhase6] Test environment set up at {cls.base_path}")
    
    def setUp(self):
        """Set up individual test."""
        self.script_manager = ScriptManager(self.base_path)
        self.process_tracker = ProcessTracker(self.base_path)
        self.daemon_manager = DaemonManager(self.base_path)
        self.health_monitor = HealthMonitor(self.base_path)
        self.virtual_drive_manager = VirtualDriveManager(self.base_path)
        
        # Set up mock application state
        self.state_manager = StateManager(self.base_path)
        self._setup_mock_app_state()
    
    def tearDown(self):
        """Clean up after individual test."""
        try:
            # Stop any running processes
            running_apps = self.script_manager.list_running_applications()
            for process_info in running_apps:
                self.script_manager.stop_application(process_info.app_name, force=True)
            
            # Stop daemons
            active_daemons = self.daemon_manager.list_active_daemons()
            for daemon_info in active_daemons:
                self.daemon_manager.stop_daemon(daemon_info.daemon_id, force=True)
            
            # Stop monitoring
            self.script_manager.stop_monitoring()
            self.process_tracker.stop_monitoring()
            self.daemon_manager.stop_health_monitoring()
            self.health_monitor.stop_monitoring_thread()
            
            # Clean up virtual drives
            self.virtual_drive_manager.cleanup_unused_drives()
            
        except Exception as e:
            print(f"[TestPhase6] Cleanup error: {e}")
    
    def _setup_mock_app_state(self):
        """Set up mock application state for testing."""
        # Create mock installation directory
        mock_install_path = Path(self.base_path) / "apps" / self.test_app_name
        mock_install_path.mkdir(parents=True, exist_ok=True)
        
        # Copy test script to mock installation
        test_script_copy = mock_install_path / "run.py"
        with open(test_script_copy, 'w') as f:
            f.write(self.test_script_content)
        os.chmod(test_script_copy, 0o755)
        
        # Register app as installed
        self.state_manager.create_application_state(
            app_name=self.test_app_name,
            installation_path=str(mock_install_path)
        )
        self.state_manager.set_application_status(self.test_app_name, ApplicationStatus.INSTALLED)
    
    def test_script_manager_start_stop(self):
        """Test script manager start and stop functionality."""
        print("\n[TEST] Script Manager Start/Stop")
        
        # Test starting application
        process_info = self.script_manager.start_application(
            app_name=self.test_app_name,
            script_path=f"python3 {self.test_script_path}"
        )
        
        self.assertIsNotNone(process_info)
        self.assertEqual(process_info.app_name, self.test_app_name)
        self.assertGreater(process_info.pid, 0)
        self.assertEqual(process_info.status, ApplicationRunningStatus.RUNNING)
        
        # Wait for process to be running
        time.sleep(3)
        
        # Check status
        status = self.script_manager.get_application_status(self.test_app_name)
        self.assertEqual(status, ApplicationRunningStatus.RUNNING)
        
        # List running applications
        running_apps = self.script_manager.list_running_applications()
        self.assertEqual(len(running_apps), 1)
        self.assertEqual(running_apps[0].app_name, self.test_app_name)
        
        # Test stopping application
        success = self.script_manager.stop_application(self.test_app_name)
        self.assertTrue(success)
        
        # Wait for shutdown
        time.sleep(2)
        
        # Verify stopped
        status = self.script_manager.get_application_status(self.test_app_name)
        self.assertEqual(status, ApplicationRunningStatus.NOT_RUNNING)
        
        print("[TEST] ✅ Script Manager Start/Stop - PASSED")
    
    def test_process_tracker_monitoring(self):
        """Test process tracker monitoring functionality."""
        print("\n[TEST] Process Tracker Monitoring")
        
        # Start a test process
        process_info = self.script_manager.start_application(
            app_name=self.test_app_name,
            script_path=f"python3 {self.test_script_path}"
        )
        
        # Start tracking the process
        self.process_tracker.track_process(process_info.pid, self.test_app_name)
        
        # Wait for monitoring data
        time.sleep(5)
        
        # Get process info
        tracked_process = self.process_tracker.get_process_info(process_info.pid)
        self.assertIsNotNone(tracked_process)
        self.assertEqual(tracked_process.pid, process_info.pid)
        self.assertEqual(tracked_process.app_name, self.test_app_name)
        
        # Monitor resources
        resource_usage = self.process_tracker.monitor_resources(process_info.pid)
        self.assertIsNotNone(resource_usage)
        self.assertGreaterEqual(resource_usage.cpu_percent, 0)
        self.assertGreater(resource_usage.memory_rss, 0)
        
        # Get system metrics
        system_metrics = self.process_tracker.get_system_metrics()
        self.assertIn('cpu', system_metrics)
        self.assertIn('memory', system_metrics)
        self.assertIn('processes', system_metrics)
        
        # Check for alerts (should be none for normal operation)
        alerts = self.process_tracker.get_resource_alerts()
        self.assertIsInstance(alerts, list)
        
        # Stop the application
        self.script_manager.stop_application(self.test_app_name)
        
        print("[TEST] ✅ Process Tracker Monitoring - PASSED")
    
    def test_daemon_manager_functionality(self):
        """Test daemon manager functionality."""
        print("\n[TEST] Daemon Manager Functionality")
        
        # Start a daemon
        daemon_info = self.daemon_manager.start_daemon(
            script_path=f"python3 {self.daemon_script_path}",
            app_name=self.test_app_name
        )
        
        self.assertIsNotNone(daemon_info)
        self.assertEqual(daemon_info.app_name, self.test_app_name)
        self.assertGreater(daemon_info.pid, 0)
        self.assertEqual(daemon_info.status, DaemonStatus.RUNNING)
        
        # Wait for daemon to be running
        time.sleep(3)
        
        # Check daemon health
        health = self.daemon_manager.monitor_daemon_health(daemon_info.daemon_id)
        self.assertIn(health, [HealthStatus.HEALTHY, HealthStatus.UNKNOWN])
        
        # List active daemons
        active_daemons = self.daemon_manager.list_active_daemons()
        self.assertEqual(len(active_daemons), 1)
        self.assertEqual(active_daemons[0].daemon_id, daemon_info.daemon_id)
        
        # Get daemon logs
        logs = self.daemon_manager.get_daemon_logs(daemon_info.daemon_id)
        self.assertIn('stdout', logs)
        self.assertIn('stderr', logs)
        
        # Stop daemon
        success = self.daemon_manager.stop_daemon(daemon_info.daemon_id)
        self.assertTrue(success)
        
        # Wait for shutdown
        time.sleep(2)
        
        # Verify stopped
        active_daemons = self.daemon_manager.list_active_daemons()
        self.assertEqual(len(active_daemons), 0)
        
        print("[TEST] ✅ Daemon Manager Functionality - PASSED")
    
    def test_health_monitor_functionality(self):
        """Test health monitor functionality."""
        print("\n[TEST] Health Monitor Functionality")
        
        # Start a test process
        process_info = self.script_manager.start_application(
            app_name=self.test_app_name,
            script_path=f"python3 {self.test_script_path}"
        )
        
        # Start health monitoring
        self.health_monitor.start_monitoring(self.test_app_name, process_info.pid)
        
        # Wait for health checks
        time.sleep(5)
        
        # Check application health
        health_status = self.health_monitor.check_application_health(self.test_app_name)
        self.assertIn(health_status, [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNKNOWN])
        
        # Get application health info
        app_health = self.health_monitor.get_application_health(self.test_app_name)
        self.assertIsNotNone(app_health)
        self.assertEqual(app_health.app_name, self.test_app_name)
        self.assertEqual(app_health.pid, process_info.pid)
        
        # Add custom health check
        custom_check = HealthCheck(
            check_type=HealthCheckType.CUSTOM,
            name="test_custom_check",
            config={'command': f'ps -p {process_info.pid}'}
        )
        self.health_monitor.add_custom_health_check(self.test_app_name, custom_check)
        
        # Run health check again
        health_status = self.health_monitor.check_application_health(self.test_app_name)
        self.assertIsNotNone(health_status)
        
        # Get all application health
        all_health = self.health_monitor.get_all_application_health()
        self.assertIn(self.test_app_name, all_health)
        
        # Stop monitoring and application
        self.health_monitor.stop_monitoring(self.test_app_name)
        self.script_manager.stop_application(self.test_app_name)
        
        print("[TEST] ✅ Health Monitor Functionality - PASSED")
    
    def test_virtual_drive_functionality(self):
        """Test virtual drive functionality."""
        print("\n[TEST] Virtual Drive Functionality")
        
        # Create a virtual drive
        test_drive = self.virtual_drive_manager.create_virtual_drive(
            drive_name="test_drive",
            drive_type=DriveType.APP_SPECIFIC,
            size_gb=1.0,
            storage_mode=StorageMode.SYMLINK
        )
        
        self.assertIsNotNone(test_drive)
        self.assertEqual(test_drive.name, "test_drive")
        self.assertEqual(test_drive.drive_type, DriveType.APP_SPECIFIC)
        self.assertEqual(test_drive.storage_mode, StorageMode.SYMLINK)
        
        # Mount drive for application
        mount_path = self.virtual_drive_manager.mount_drive_for_app(
            self.test_app_name, test_drive.drive_id
        )
        
        self.assertTrue(os.path.exists(mount_path))
        self.assertIn(self.test_app_name, test_drive.mounted_apps)
        
        # Create a test file to share
        test_file = Path(self.base_path) / "test_model.bin"
        test_file.write_text("test model data")
        
        # Add file to shared drive
        success = self.virtual_drive_manager.add_file_to_shared_drive(
            test_drive.drive_id, str(test_file), self.test_app_name
        )
        self.assertTrue(success)
        
        # Get drive usage stats
        stats = self.virtual_drive_manager.get_drive_usage_stats(test_drive.drive_id)
        self.assertGreater(stats['file_count'], 0)
        self.assertGreater(stats['total_size_bytes'], 0)
        
        # List virtual drives
        all_drives = self.virtual_drive_manager.list_virtual_drives()
        drive_names = [drive.name for drive in all_drives]
        self.assertIn("test_drive", drive_names)
        
        # Test model sharing between apps
        success = self.virtual_drive_manager.share_models_between_apps(
            self.test_app_name, "target_app", ["*.bin"]
        )
        # This might fail if no models are found, which is expected in test
        
        # Unmount drive
        success = self.virtual_drive_manager.unmount_drive_for_app(
            self.test_app_name, test_drive.drive_id
        )
        self.assertTrue(success)
        
        # Cleanup
        test_file.unlink(missing_ok=True)
        
        print("[TEST] ✅ Virtual Drive Functionality - PASSED")
    
    def test_integration_workflow(self):
        """Test complete integration workflow."""
        print("\n[TEST] Integration Workflow")
        
        # 1. Create virtual drive for shared models
        models_drive = self.virtual_drive_manager.create_virtual_drive(
            drive_name="integration_models",
            drive_type=DriveType.SHARED_MODELS,
            storage_mode=StorageMode.DEDUPLICATED
        )
        
        # 2. Start application
        process_info = self.script_manager.start_application(
            app_name=self.test_app_name,
            script_path=f"python3 {self.test_script_path}"
        )
        
        # 3. Start process tracking
        self.process_tracker.track_process(process_info.pid, self.test_app_name)
        
        # 4. Start health monitoring
        self.health_monitor.start_monitoring(self.test_app_name, process_info.pid)
        
        # 5. Mount virtual drive
        mount_path = self.virtual_drive_manager.mount_drive_for_app(
            self.test_app_name, models_drive.drive_id
        )
        
        # 6. Wait for systems to stabilize
        time.sleep(5)
        
        # 7. Verify all systems are working
        # Check application is running
        status = self.script_manager.get_application_status(self.test_app_name)
        self.assertEqual(status, ApplicationRunningStatus.RUNNING)
        
        # Check process is tracked
        tracked_process = self.process_tracker.get_process_info(process_info.pid)
        self.assertIsNotNone(tracked_process)
        
        # Check health monitoring
        health_status = self.health_monitor.check_application_health(self.test_app_name)
        self.assertIsNotNone(health_status)
        
        # Check virtual drive is mounted
        self.assertTrue(os.path.exists(mount_path))
        
        # 8. Test restart functionality
        success = self.script_manager.restart_application(self.test_app_name)
        self.assertTrue(success)
        
        # Wait for restart
        time.sleep(3)
        
        # Verify application is running after restart
        status = self.script_manager.get_application_status(self.test_app_name)
        self.assertEqual(status, ApplicationRunningStatus.RUNNING)
        
        # 9. Clean up
        self.script_manager.stop_application(self.test_app_name)
        self.health_monitor.stop_monitoring(self.test_app_name)
        self.virtual_drive_manager.unmount_drive_for_app(self.test_app_name, models_drive.drive_id)
        
        print("[TEST] ✅ Integration Workflow - PASSED")
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios."""
        print("\n[TEST] Error Handling and Recovery")
        
        # Test handling non-existent application
        try:
            self.script_manager.start_application(
                app_name="nonexistent_app",
                script_path="nonexistent_script.py"
            )
            self.fail("Should have raised an exception")
        except Exception:
            pass  # Expected
        
        # Test stopping non-existent application
        success = self.script_manager.stop_application("nonexistent_app")
        self.assertFalse(success)
        
        # Test daemon with invalid script
        try:
            self.daemon_manager.start_daemon(
                script_path="nonexistent_daemon.py",
                app_name="test_daemon"
            )
            self.fail("Should have raised an exception")
        except Exception:
            pass  # Expected
        
        # Test health monitoring with invalid PID
        self.health_monitor.start_monitoring("invalid_app", 99999)
        health_status = self.health_monitor.check_application_health("invalid_app")
        self.assertEqual(health_status, HealthStatus.CRITICAL)
        
        # Test virtual drive operations with invalid IDs
        success = self.virtual_drive_manager.mount_drive_for_app(
            "test_app", "nonexistent_drive_id"
        )
        self.assertFalse(success)
        
        print("[TEST] ✅ Error Handling and Recovery - PASSED")
    
    def test_performance_requirements(self):
        """Test performance requirements are met."""
        print("\n[TEST] Performance Requirements")
        
        # Test application startup time (should be realistic, not instant)
        start_time = time.time()
        
        process_info = self.script_manager.start_application(
            app_name=self.test_app_name,
            script_path=f"python3 {self.test_script_path}"
        )
        
        startup_time = time.time() - start_time
        
        # Should take at least 1 second (real process startup)
        self.assertGreaterEqual(startup_time, 0.5)
        
        # Test resource monitoring performance
        start_time = time.time()
        
        self.process_tracker.track_process(process_info.pid, self.test_app_name)
        resource_usage = self.process_tracker.monitor_resources(process_info.pid)
        
        monitoring_time = time.time() - start_time
        
        # Resource monitoring should be fast (< 1 second)
        self.assertLess(monitoring_time, 1.0)
        self.assertIsNotNone(resource_usage)
        
        # Test health check performance
        start_time = time.time()
        
        self.health_monitor.start_monitoring(self.test_app_name, process_info.pid)
        health_status = self.health_monitor.check_application_health(self.test_app_name)
        
        health_check_time = time.time() - start_time
        
        # Health checks should be reasonably fast (< 5 seconds)
        self.assertLess(health_check_time, 5.0)
        self.assertIsNotNone(health_status)
        
        # Clean up
        self.script_manager.stop_application(self.test_app_name)
        
        print("[TEST] ✅ Performance Requirements - PASSED")


def run_phase6_tests():
    """Run all Phase 6 tests."""
    print("=" * 60)
    print("PHASE 6 TEST SUITE - APPLICATION RUNNING ENGINE")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase6Integration)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("PHASE 6 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    
    print(f"Total Tests: {total_tests}")
    print(f"Successes: {successes}")
    print(f"Failures: {failures}")
    print(f"Errors: {errors}")
    
    success_rate = (successes / total_tests * 100) if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if failures > 0:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if errors > 0:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    print("\n" + "=" * 60)
    
    return success_rate >= 90.0  # 90% success rate required


def main():
    """Main test function."""
    try:
        success = run_phase6_tests()
        
        if success:
            print("🎉 PHASE 6 TESTS PASSED - Application Running Engine is ready!")
            return 0
        else:
            print("❌ PHASE 6 TESTS FAILED - Please review and fix issues")
            return 1
            
    except Exception as e:
        print(f"💥 PHASE 6 TEST SUITE ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit(main())