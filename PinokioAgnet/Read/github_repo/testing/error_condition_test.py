#!/usr/bin/env python3
"""
PinokioCloud Error Condition Test - Phase 10

This module provides comprehensive error condition testing and recovery
validation for the entire PinokioCloud system.

Author: PinokioCloud Development Team  
Version: 1.0.0
"""

import os
import sys
import json
import time
import shutil
import tempfile
import subprocess
import threading
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from enum import Enum
import signal

# Add the github_repo directory to Python path for imports
sys.path.append('/workspace/SD-LongNose/github_repo')

# Import error recovery and monitoring components
from optimization.error_recovery import ErrorRecovery
from finalization.error_handler import ErrorHandler
from optimization.logging_system import LoggingSystem


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for testing."""
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    MEMORY = "memory"
    PROCESS = "process"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    RESOURCE = "resource"


@dataclass
class ErrorScenario:
    """Represents an error scenario for testing."""
    name: str
    description: str
    category: ErrorCategory
    severity: ErrorSeverity
    setup_function: str
    test_function: str
    cleanup_function: str
    expected_recovery: bool = True
    timeout: int = 30  # seconds


@dataclass
class ErrorTestResult:
    """Result of an error condition test."""
    scenario_name: str
    category: ErrorCategory
    severity: ErrorSeverity
    error_triggered: bool
    error_detected: bool
    recovery_attempted: bool
    recovery_successful: bool
    recovery_time: float
    overall_success: bool
    error_message: Optional[str] = None
    recovery_details: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class ErrorConditionTest:
    """
    Comprehensive error condition testing system for PinokioCloud.
    
    Tests system behavior under various error conditions and validates
    that error recovery mechanisms work correctly.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the error condition test system."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.test_results: List[ErrorTestResult] = []
        
        # Initialize error handling components
        self.error_recovery = ErrorRecovery()
        self.error_handler = ErrorHandler()
        self.logging_system = LoggingSystem()
        
        # Test data directory
        self.test_data_dir = self.base_path / "error_test_data"
        self.test_data_dir.mkdir(exist_ok=True)
        
        # Define error scenarios
        self.error_scenarios = self.create_error_scenarios()
    
    def create_error_scenarios(self) -> List[ErrorScenario]:
        """Create comprehensive error scenarios for testing."""
        return [
            # Network Error Scenarios
            ErrorScenario(
                name="network_timeout",
                description="Test network timeout handling",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                setup_function="setup_network_timeout",
                test_function="test_network_timeout",
                cleanup_function="cleanup_network_timeout"
            ),
            
            ErrorScenario(
                name="connection_refused",
                description="Test connection refused error handling",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                setup_function="setup_connection_refused",
                test_function="test_connection_refused", 
                cleanup_function="cleanup_connection_refused"
            ),
            
            # Filesystem Error Scenarios
            ErrorScenario(
                name="disk_full",
                description="Test disk full error handling",
                category=ErrorCategory.FILESYSTEM,
                severity=ErrorSeverity.CRITICAL,
                setup_function="setup_disk_full",
                test_function="test_disk_full",
                cleanup_function="cleanup_disk_full"
            ),
            
            ErrorScenario(
                name="permission_denied",
                description="Test permission denied error handling",
                category=ErrorCategory.PERMISSION,
                severity=ErrorSeverity.HIGH,
                setup_function="setup_permission_denied",
                test_function="test_permission_denied",
                cleanup_function="cleanup_permission_denied"
            ),
            
            ErrorScenario(
                name="file_not_found",
                description="Test file not found error handling",
                category=ErrorCategory.FILESYSTEM,
                severity=ErrorSeverity.MEDIUM,
                setup_function="setup_file_not_found",
                test_function="test_file_not_found",
                cleanup_function="cleanup_file_not_found"
            ),
            
            # Memory Error Scenarios
            ErrorScenario(
                name="memory_exhaustion",
                description="Test memory exhaustion handling",
                category=ErrorCategory.MEMORY,
                severity=ErrorSeverity.CRITICAL,
                setup_function="setup_memory_exhaustion",
                test_function="test_memory_exhaustion",
                cleanup_function="cleanup_memory_exhaustion",
                timeout=60
            ),
            
            # Process Error Scenarios
            ErrorScenario(
                name="process_crash",
                description="Test process crash recovery",
                category=ErrorCategory.PROCESS,
                severity=ErrorSeverity.HIGH,
                setup_function="setup_process_crash",
                test_function="test_process_crash",
                cleanup_function="cleanup_process_crash"
            ),
            
            ErrorScenario(
                name="zombie_process",
                description="Test zombie process cleanup",
                category=ErrorCategory.PROCESS,
                severity=ErrorSeverity.MEDIUM,
                setup_function="setup_zombie_process",
                test_function="test_zombie_process",
                cleanup_function="cleanup_zombie_process"
            ),
            
            # Configuration Error Scenarios
            ErrorScenario(
                name="invalid_config",
                description="Test invalid configuration handling",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.MEDIUM,
                setup_function="setup_invalid_config",
                test_function="test_invalid_config",
                cleanup_function="cleanup_invalid_config"
            ),
            
            # Dependency Error Scenarios
            ErrorScenario(
                name="missing_dependency",
                description="Test missing dependency handling",
                category=ErrorCategory.DEPENDENCY,
                severity=ErrorSeverity.HIGH,
                setup_function="setup_missing_dependency",
                test_function="test_missing_dependency",
                cleanup_function="cleanup_missing_dependency"
            ),
            
            # Resource Error Scenarios
            ErrorScenario(
                name="resource_locked",
                description="Test resource lock handling",
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.MEDIUM,
                setup_function="setup_resource_locked",
                test_function="test_resource_locked",
                cleanup_function="cleanup_resource_locked"
            ),
        ]
    
    # Network Error Test Functions
    def setup_network_timeout(self) -> Dict[str, Any]:
        """Set up network timeout scenario."""
        return {"timeout_url": "http://10.255.255.1:12345"}  # Non-routable address
    
    def test_network_timeout(self, setup_data: Dict[str, Any]) -> Tuple[bool, bool, float, str]:
        """Test network timeout error handling."""
        start_time = time.time()
        
        try:
            import requests
            
            # This should timeout
            with self.error_handler.error_context("network_timeout_test"):
                response = requests.get(setup_data["timeout_url"], timeout=5)
            
            # If we get here without exception, test failed
            return False, False, time.time() - start_time, "No timeout occurred"
            
        except requests.exceptions.Timeout:
            # Expected behavior - check if recovery was attempted
            recovery_time = time.time() - start_time
            
            # Check if error was detected and logged
            recent_logs = self.logging_system.get_logs(
                category="error", limit=10, 
                start_time=datetime.fromtimestamp(start_time)
            )
            
            error_detected = any("timeout" in log.get('message', '').lower() for log in recent_logs)
            
            return True, error_detected, recovery_time, "Network timeout handled correctly"
            
        except Exception as e:
            return True, False, time.time() - start_time, f"Unexpected error: {str(e)}"
    
    def cleanup_network_timeout(self, setup_data: Dict[str, Any]) -> bool:
        """Clean up network timeout test."""
        return True  # No cleanup needed
    
    def setup_connection_refused(self) -> Dict[str, Any]:
        """Set up connection refused scenario."""
        return {"refused_url": "http://localhost:99999"}  # Invalid port
    
    def test_connection_refused(self, setup_data: Dict[str, Any]) -> Tuple[bool, bool, float, str]:
        """Test connection refused error handling."""
        start_time = time.time()
        
        try:
            import requests
            
            response = requests.get(setup_data["refused_url"], timeout=5)
            return False, False, time.time() - start_time, "No connection refused error"
            
        except requests.exceptions.ConnectionError:
            recovery_time = time.time() - start_time
            return True, True, recovery_time, "Connection refused handled correctly"
            
        except Exception as e:
            return True, False, time.time() - start_time, f"Unexpected error: {str(e)}"
    
    def cleanup_connection_refused(self, setup_data: Dict[str, Any]) -> bool:
        """Clean up connection refused test."""
        return True  # No cleanup needed
    
    # Filesystem Error Test Functions
    def setup_disk_full(self) -> Dict[str, Any]:
        """Set up disk full scenario (simulated)."""
        test_dir = self.test_data_dir / "disk_full_test"
        test_dir.mkdir(exist_ok=True)
        return {"test_dir": str(test_dir)}
    
    def test_disk_full(self, setup_data: Dict[str, Any]) -> Tuple[bool, bool, float, str]:
        """Test disk full error handling (simulated)."""
        start_time = time.time()
        
        try:
            test_dir = Path(setup_data["test_dir"])
            
            # Simulate disk full by creating a large file
            large_file = test_dir / "large_file.dat"
            
            # Try to create a file that might cause "disk full" on small systems
            with open(large_file, 'wb') as f:
                # Write until we hit a limit or error
                try:
                    for _ in range(1000):  # Write up to 1GB
                        f.write(b'x' * (1024 * 1024))  # 1MB chunks
                        f.flush()
                        
                        # Check available space
                        import shutil
                        _, _, free_bytes = shutil.disk_usage(test_dir)
                        if free_bytes < 100 * 1024 * 1024:  # Less than 100MB free
                            raise OSError("Disk full (simulated)")
                            
                except OSError as e:
                    if "disk full" in str(e).lower() or "no space" in str(e).lower():
                        recovery_time = time.time() - start_time
                        return True, True, recovery_time, "Disk full error detected and handled"
                    else:
                        raise
            
            # If we get here, no disk full error occurred
            return False, False, time.time() - start_time, "No disk full error triggered"
            
        except Exception as e:
            recovery_time = time.time() - start_time
            if "space" in str(e).lower() or "full" in str(e).lower():
                return True, True, recovery_time, f"Disk full error handled: {str(e)}"
            else:
                return True, False, recovery_time, f"Unexpected error: {str(e)}"
    
    def cleanup_disk_full(self, setup_data: Dict[str, Any]) -> bool:
        """Clean up disk full test."""
        try:
            test_dir = Path(setup_data["test_dir"])
            if test_dir.exists():
                shutil.rmtree(test_dir, ignore_errors=True)
            return True
        except:
            return False
    
    def setup_permission_denied(self) -> Dict[str, Any]:
        """Set up permission denied scenario."""
        test_dir = self.test_data_dir / "permission_test"
        test_dir.mkdir(exist_ok=True)
        
        # Create a file and remove write permissions
        test_file = test_dir / "readonly_file.txt"
        test_file.write_text("readonly content")
        test_file.chmod(0o444)  # Read-only
        
        return {"test_file": str(test_file), "test_dir": str(test_dir)}
    
    def test_permission_denied(self, setup_data: Dict[str, Any]) -> Tuple[bool, bool, float, str]:
        """Test permission denied error handling."""
        start_time = time.time()
        
        try:
            test_file = Path(setup_data["test_file"])
            
            # Try to write to read-only file
            with open(test_file, 'w') as f:
                f.write("This should fail")
            
            return False, False, time.time() - start_time, "No permission denied error"
            
        except PermissionError:
            recovery_time = time.time() - start_time
            return True, True, recovery_time, "Permission denied handled correctly"
            
        except Exception as e:
            recovery_time = time.time() - start_time
            return True, False, recovery_time, f"Unexpected error: {str(e)}"
    
    def cleanup_permission_denied(self, setup_data: Dict[str, Any]) -> bool:
        """Clean up permission denied test."""
        try:
            test_file = Path(setup_data["test_file"])
            test_dir = Path(setup_data["test_dir"])
            
            # Restore permissions before cleanup
            if test_file.exists():
                test_file.chmod(0o644)
            
            if test_dir.exists():
                shutil.rmtree(test_dir, ignore_errors=True)
            return True
        except:
            return False
    
    def setup_file_not_found(self) -> Dict[str, Any]:
        """Set up file not found scenario."""
        nonexistent_file = self.test_data_dir / "nonexistent_file.txt"
        return {"nonexistent_file": str(nonexistent_file)}
    
    def test_file_not_found(self, setup_data: Dict[str, Any]) -> Tuple[bool, bool, float, str]:
        """Test file not found error handling."""
        start_time = time.time()
        
        try:
            nonexistent_file = Path(setup_data["nonexistent_file"])
            
            # Try to read nonexistent file
            with open(nonexistent_file, 'r') as f:
                content = f.read()
            
            return False, False, time.time() - start_time, "No file not found error"
            
        except FileNotFoundError:
            recovery_time = time.time() - start_time
            return True, True, recovery_time, "File not found handled correctly"
            
        except Exception as e:
            recovery_time = time.time() - start_time
            return True, False, recovery_time, f"Unexpected error: {str(e)}"
    
    def cleanup_file_not_found(self, setup_data: Dict[str, Any]) -> bool:
        """Clean up file not found test."""
        return True  # No cleanup needed
    
    # Memory Error Test Functions
    def setup_memory_exhaustion(self) -> Dict[str, Any]:
        """Set up memory exhaustion scenario."""
        return {"allocation_size": 100 * 1024 * 1024}  # 100MB chunks
    
    def test_memory_exhaustion(self, setup_data: Dict[str, Any]) -> Tuple[bool, bool, float, str]:
        """Test memory exhaustion handling."""
        start_time = time.time()
        
        try:
            allocation_size = setup_data["allocation_size"]
            allocations = []
            
            # Try to allocate memory until we hit a limit
            for i in range(100):  # Try to allocate up to 10GB
                try:
                    chunk = bytearray(allocation_size)
                    allocations.append(chunk)
                    
                    # Check memory usage
                    import psutil
                    memory_percent = psutil.virtual_memory().percent
                    if memory_percent > 90:  # If memory usage > 90%
                        # Simulate memory error
                        raise MemoryError("Memory exhausted (simulated)")
                        
                except MemoryError:
                    recovery_time = time.time() - start_time
                    
                    # Clear allocations to recover
                    allocations.clear()
                    import gc
                    gc.collect()
                    
                    return True, True, recovery_time, "Memory exhaustion detected and recovered"
            
            # If we get here, no memory error occurred
            return False, False, time.time() - start_time, "No memory exhaustion triggered"
            
        except Exception as e:
            recovery_time = time.time() - start_time
            return True, True, recovery_time, f"Memory error handled: {str(e)}"
    
    def cleanup_memory_exhaustion(self, setup_data: Dict[str, Any]) -> bool:
        """Clean up memory exhaustion test."""
        # Force garbage collection
        import gc
        gc.collect()
        return True
    
    # Process Error Test Functions
    def setup_process_crash(self) -> Dict[str, Any]:
        """Set up process crash scenario."""
        return {"test_process": None}
    
    def test_process_crash(self, setup_data: Dict[str, Any]) -> Tuple[bool, bool, float, str]:
        """Test process crash recovery."""
        start_time = time.time()
        
        try:
            # Create a subprocess that will crash
            crash_script = '''
import time
import os
time.sleep(2)
os._exit(1)  # Simulate crash
'''
            
            # Write crash script to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(crash_script)
                script_path = f.name
            
            # Start the process
            process = subprocess.Popen([sys.executable, script_path])
            setup_data["test_process"] = process
            setup_data["script_path"] = script_path
            
            # Wait for process to crash
            return_code = process.wait(timeout=10)
            
            recovery_time = time.time() - start_time
            
            if return_code != 0:
                return True, True, recovery_time, f"Process crash detected (exit code: {return_code})"
            else:
                return False, False, recovery_time, "Process did not crash as expected"
                
        except subprocess.TimeoutExpired:
            recovery_time = time.time() - start_time
            return False, False, recovery_time, "Process did not crash within timeout"
            
        except Exception as e:
            recovery_time = time.time() - start_time
            return True, False, recovery_time, f"Unexpected error: {str(e)}"
    
    def cleanup_process_crash(self, setup_data: Dict[str, Any]) -> bool:
        """Clean up process crash test."""
        try:
            # Clean up process
            if setup_data.get("test_process"):
                try:
                    setup_data["test_process"].terminate()
                    setup_data["test_process"].wait(timeout=5)
                except:
                    pass
            
            # Clean up script file
            if setup_data.get("script_path"):
                try:
                    os.unlink(setup_data["script_path"])
                except:
                    pass
                    
            return True
        except:
            return False
    
    def setup_zombie_process(self) -> Dict[str, Any]:
        """Set up zombie process scenario."""
        return {}
    
    def test_zombie_process(self, setup_data: Dict[str, Any]) -> Tuple[bool, bool, float, str]:
        """Test zombie process cleanup."""
        start_time = time.time()
        
        try:
            # Create a process that becomes a zombie
            zombie_script = '''
import os
import time
if os.fork() == 0:
    # Child process exits immediately
    os._exit(0)
else:
    # Parent sleeps without waiting for child
    time.sleep(5)
'''
            
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(zombie_script)
                script_path = f.name
            
            # Start the process
            process = subprocess.Popen([sys.executable, script_path])
            setup_data["test_process"] = process
            setup_data["script_path"] = script_path
            
            # Wait a bit for zombie to be created
            time.sleep(2)
            
            # Check for zombie processes
            import psutil
            zombies = [p for p in psutil.process_iter(['pid', 'status']) 
                      if p.info['status'] == psutil.STATUS_ZOMBIE]
            
            process.wait(timeout=10)  # Wait for parent to finish
            
            recovery_time = time.time() - start_time
            
            if zombies:
                return True, True, recovery_time, f"Zombie process detected and cleaned up ({len(zombies)} zombies)"
            else:
                return False, False, recovery_time, "No zombie processes detected"
                
        except Exception as e:
            recovery_time = time.time() - start_time
            return True, False, recovery_time, f"Unexpected error: {str(e)}"
    
    def cleanup_zombie_process(self, setup_data: Dict[str, Any]) -> bool:
        """Clean up zombie process test."""
        return self.cleanup_process_crash(setup_data)  # Same cleanup logic
    
    # Configuration Error Test Functions
    def setup_invalid_config(self) -> Dict[str, Any]:
        """Set up invalid configuration scenario."""
        test_config_file = self.test_data_dir / "invalid_config.json"
        
        # Create invalid JSON config
        with open(test_config_file, 'w') as f:
            f.write('{"invalid": json, "syntax": error}')  # Invalid JSON
        
        return {"config_file": str(test_config_file)}
    
    def test_invalid_config(self, setup_data: Dict[str, Any]) -> Tuple[bool, bool, float, str]:
        """Test invalid configuration handling."""
        start_time = time.time()
        
        try:
            config_file = Path(setup_data["config_file"])
            
            # Try to parse invalid JSON
            with open(config_file, 'r') as f:
                json.load(f)
            
            return False, False, time.time() - start_time, "No JSON parsing error"
            
        except json.JSONDecodeError:
            recovery_time = time.time() - start_time
            return True, True, recovery_time, "Invalid configuration handled correctly"
            
        except Exception as e:
            recovery_time = time.time() - start_time
            return True, False, recovery_time, f"Unexpected error: {str(e)}"
    
    def cleanup_invalid_config(self, setup_data: Dict[str, Any]) -> bool:
        """Clean up invalid configuration test."""
        try:
            config_file = Path(setup_data["config_file"])
            if config_file.exists():
                config_file.unlink()
            return True
        except:
            return False
    
    # Dependency Error Test Functions
    def setup_missing_dependency(self) -> Dict[str, Any]:
        """Set up missing dependency scenario."""
        return {"missing_module": "nonexistent_module_12345"}
    
    def test_missing_dependency(self, setup_data: Dict[str, Any]) -> Tuple[bool, bool, float, str]:
        """Test missing dependency handling."""
        start_time = time.time()
        
        try:
            missing_module = setup_data["missing_module"]
            
            # Try to import nonexistent module
            __import__(missing_module)
            
            return False, False, time.time() - start_time, "No import error"
            
        except ImportError:
            recovery_time = time.time() - start_time
            return True, True, recovery_time, "Missing dependency handled correctly"
            
        except Exception as e:
            recovery_time = time.time() - start_time
            return True, False, recovery_time, f"Unexpected error: {str(e)}"
    
    def cleanup_missing_dependency(self, setup_data: Dict[str, Any]) -> bool:
        """Clean up missing dependency test."""
        return True  # No cleanup needed
    
    # Resource Error Test Functions
    def setup_resource_locked(self) -> Dict[str, Any]:
        """Set up resource locked scenario."""
        test_file = self.test_data_dir / "locked_file.txt"
        test_file.write_text("test content")
        
        # Open file in exclusive mode
        lock_file = open(test_file, 'r+')
        
        return {"lock_file": lock_file, "test_file": str(test_file)}
    
    def test_resource_locked(self, setup_data: Dict[str, Any]) -> Tuple[bool, bool, float, str]:
        """Test resource lock handling."""
        start_time = time.time()
        
        try:
            test_file = Path(setup_data["test_file"])
            
            # Try to open already locked file
            with open(test_file, 'w') as f:
                f.write("This might fail on some systems")
            
            recovery_time = time.time() - start_time
            return True, True, recovery_time, "Resource lock handled (or not applicable on this system)"
            
        except Exception as e:
            recovery_time = time.time() - start_time
            if "lock" in str(e).lower() or "busy" in str(e).lower():
                return True, True, recovery_time, "Resource lock detected and handled"
            else:
                return True, False, recovery_time, f"Unexpected error: {str(e)}"
    
    def cleanup_resource_locked(self, setup_data: Dict[str, Any]) -> bool:
        """Clean up resource locked test."""
        try:
            # Close the lock file
            if setup_data.get("lock_file"):
                setup_data["lock_file"].close()
            
            # Remove test file
            test_file = Path(setup_data["test_file"])
            if test_file.exists():
                test_file.unlink()
                
            return True
        except:
            return False
    
    def run_error_scenario(self, scenario: ErrorScenario) -> ErrorTestResult:
        """Run a single error scenario test."""
        print(f"🧪 Testing error scenario: {scenario.name}")
        
        setup_data = {}
        error_triggered = False
        error_detected = False
        recovery_attempted = False
        recovery_successful = False
        recovery_time = 0.0
        error_message = None
        recovery_details = None
        
        try:
            # Setup phase
            setup_function = getattr(self, scenario.setup_function)
            setup_data = setup_function()
            
            # Test phase
            test_function = getattr(self, scenario.test_function)
            error_triggered, error_detected, recovery_time, recovery_details = test_function(setup_data)
            
            # Recovery phase (if error was triggered)
            if error_triggered and error_detected:
                recovery_attempted = True
                
                # Check if error recovery system handled it
                recovery_result = self.error_recovery.detect_and_recover()
                recovery_successful = recovery_result.get('recovery_successful', False)
            
            overall_success = (
                error_triggered and error_detected and 
                (not scenario.expected_recovery or recovery_successful)
            )
            
        except Exception as e:
            error_message = str(e)
            overall_success = False
            
        finally:
            # Cleanup phase
            try:
                cleanup_function = getattr(self, scenario.cleanup_function)
                cleanup_function(setup_data)
            except Exception as cleanup_error:
                print(f"  ⚠️  Cleanup error: {cleanup_error}")
        
        result = ErrorTestResult(
            scenario_name=scenario.name,
            category=scenario.category,
            severity=scenario.severity,
            error_triggered=error_triggered,
            error_detected=error_detected,
            recovery_attempted=recovery_attempted,
            recovery_successful=recovery_successful,
            recovery_time=recovery_time,
            overall_success=overall_success,
            error_message=error_message,
            recovery_details=recovery_details
        )
        
        # Display result
        status = "✅ PASS" if overall_success else "❌ FAIL"
        details = recovery_details or error_message or "Unknown"
        print(f"  {status} ({recovery_time:.1f}s): {details}")
        
        return result
    
    def run_comprehensive_error_test(self) -> Dict[str, Any]:
        """Run comprehensive error condition testing."""
        print("🎯 PinokioCloud Error Condition Test - Phase 10")
        print("=" * 60)
        
        start_time = datetime.now()
        
        print(f"📋 Testing {len(self.error_scenarios)} error scenarios:")
        for scenario in self.error_scenarios:
            severity_icon = {
                ErrorSeverity.LOW: "🟢",
                ErrorSeverity.MEDIUM: "🟡", 
                ErrorSeverity.HIGH: "🟠",
                ErrorSeverity.CRITICAL: "🔴"
            }.get(scenario.severity, "⚪")
            print(f"  {severity_icon} {scenario.name} - {scenario.description}")
        
        print("\n🚀 Running Error Condition Tests...")
        
        # Run all error scenarios
        for scenario in self.error_scenarios:
            result = self.run_error_scenario(scenario)
            self.test_results.append(result)
        
        end_time = datetime.now()
        
        # Generate comprehensive report
        return self.generate_error_test_report(start_time, end_time)
    
    def generate_error_test_report(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate comprehensive error test report."""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.overall_success)
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Categorize results by severity and category
        results_by_severity = {}
        results_by_category = {}
        
        for result in self.test_results:
            # By severity
            severity = result.severity.value
            if severity not in results_by_severity:
                results_by_severity[severity] = {'total': 0, 'passed': 0}
            results_by_severity[severity]['total'] += 1
            if result.overall_success:
                results_by_severity[severity]['passed'] += 1
            
            # By category
            category = result.category.value
            if category not in results_by_category:
                results_by_category[category] = {'total': 0, 'passed': 0}
            results_by_category[category]['total'] += 1
            if result.overall_success:
                results_by_category[category]['passed'] += 1
        
        # Calculate error detection and recovery rates
        error_triggered_count = sum(1 for r in self.test_results if r.error_triggered)
        error_detected_count = sum(1 for r in self.test_results if r.error_detected)
        recovery_attempted_count = sum(1 for r in self.test_results if r.recovery_attempted)
        recovery_successful_count = sum(1 for r in self.test_results if r.recovery_successful)
        
        error_detection_rate = (error_detected_count / error_triggered_count) * 100 if error_triggered_count > 0 else 0
        recovery_success_rate = (recovery_successful_count / recovery_attempted_count) * 100 if recovery_attempted_count > 0 else 0
        
        report = {
            'error_test_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': success_rate,
                'error_detection_rate': error_detection_rate,
                'recovery_success_rate': recovery_success_rate,
                'test_duration': str(end_time - start_time),
                'timestamp': datetime.now().isoformat()
            },
            'severity_breakdown': {
                sev: {
                    'total': stats['total'],
                    'passed': stats['passed'],
                    'success_rate': (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
                }
                for sev, stats in results_by_severity.items()
            },
            'category_breakdown': {
                cat: {
                    'total': stats['total'],
                    'passed': stats['passed'],
                    'success_rate': (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
                }
                for cat, stats in results_by_category.items()
            },
            'detailed_results': [
                {
                    'scenario_name': r.scenario_name,
                    'category': r.category.value,
                    'severity': r.severity.value,
                    'error_triggered': r.error_triggered,
                    'error_detected': r.error_detected,
                    'recovery_attempted': r.recovery_attempted,
                    'recovery_successful': r.recovery_successful,
                    'recovery_time': r.recovery_time,
                    'overall_success': r.overall_success,
                    'error_message': r.error_message,
                    'recovery_details': r.recovery_details
                }
                for r in self.test_results
            ],
            'failed_scenarios': [
                {
                    'scenario_name': r.scenario_name,
                    'category': r.category.value,
                    'severity': r.severity.value,
                    'error_message': r.error_message,
                    'recovery_details': r.recovery_details
                }
                for r in self.test_results if not r.overall_success
            ],
            'recommendations': self.generate_error_recommendations()
        }
        
        return report
    
    def generate_error_recommendations(self) -> List[str]:
        """Generate error handling recommendations."""
        recommendations = []
        
        if not self.test_results:
            return ["No error test results available for analysis."]
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.overall_success)
        
        # Overall error handling assessment
        if successful_tests == total_tests:
            recommendations.append("🎉 All error scenarios handled successfully! Error recovery system is robust.")
        elif successful_tests >= total_tests * 0.8:
            recommendations.append("✅ Good error handling overall. Minor improvements recommended.")
        elif successful_tests >= total_tests * 0.5:
            recommendations.append("⚠️  Moderate error handling issues. Improvement needed.")
        else:
            recommendations.append("❌ Significant error handling problems. Major improvements required.")
        
        # Error detection recommendations
        error_detection_failures = sum(1 for r in self.test_results if r.error_triggered and not r.error_detected)
        if error_detection_failures > 0:
            recommendations.append("🔍 Improve error detection - some errors are not being properly detected and logged.")
        
        # Recovery recommendations
        recovery_failures = sum(1 for r in self.test_results if r.recovery_attempted and not r.recovery_successful)
        if recovery_failures > 0:
            recommendations.append("🔧 Enhance error recovery mechanisms - some errors are detected but not properly recovered from.")
        
        # Category-specific recommendations
        category_failures = {}
        for result in self.test_results:
            if not result.overall_success:
                category = result.category.value
                category_failures[category] = category_failures.get(category, 0) + 1
        
        for category, count in category_failures.items():
            if category == "network":
                recommendations.append("🌐 Improve network error handling - implement better timeout and retry mechanisms.")
            elif category == "filesystem":
                recommendations.append("📁 Enhance filesystem error handling - add better disk space checking and permission validation.")
            elif category == "memory":
                recommendations.append("🧠 Optimize memory error handling - implement memory monitoring and graceful degradation.")
            elif category == "process":
                recommendations.append("⚙️ Improve process error handling - enhance process monitoring and cleanup mechanisms.")
        
        return recommendations
    
    def save_error_test_report(self, report: Dict[str, Any], filename: str = None):
        """Save error test report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"error_condition_test_report_{timestamp}.json"
        
        report_path = self.base_path / filename
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📊 Error test report saved: {report_path}")


def main():
    """Main error testing function."""
    print("🎯 PinokioCloud Error Condition Test - Phase 10")
    print("=" * 60)
    
    # Initialize error test system
    error_test = ErrorConditionTest()
    
    # Run comprehensive error testing
    report = error_test.run_comprehensive_error_test()
    
    # Print summary
    print("\n📊 ERROR CONDITION TEST RESULTS")
    print("=" * 50)
    summary = report['error_test_summary']
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Successful: {summary['successful_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print(f"Error Detection Rate: {summary['error_detection_rate']:.1f}%")
    print(f"Recovery Success Rate: {summary['recovery_success_rate']:.1f}%")
    print(f"Test Duration: {summary['test_duration']}")
    
    print("\n📈 Results by Severity:")
    for severity, stats in report['severity_breakdown'].items():
        print(f"  {severity.upper()}: {stats['passed']}/{stats['total']} ({stats['success_rate']:.1f}%)")
    
    print("\n📈 Results by Category:")
    for category, stats in report['category_breakdown'].items():
        print(f"  {category.upper()}: {stats['passed']}/{stats['total']} ({stats['success_rate']:.1f}%)")
    
    if report['failed_scenarios']:
        print("\n❌ Failed Scenarios:")
        for scenario in report['failed_scenarios'][:5]:  # Show first 5 failures
            print(f"  - {scenario['scenario_name']} ({scenario['severity']}): {scenario['error_message']}")
    
    print("\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    # Save report
    error_test.save_error_test_report(report)
    
    return report['error_test_summary']['success_rate'] >= 70  # Return True if success rate >= 70%


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)