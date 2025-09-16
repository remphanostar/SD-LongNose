#!/usr/bin/env python3
"""
PinokioCloud Phase 2 Launcher

This module serves as the main entry point for Phase 2: Environment Management Engine.
It orchestrates the complete Phase 2 workflow including virtual environment management,
file system operations, shell command execution, variable management, and JSON handling.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Import Phase 2 modules
from .venv_manager import VirtualEnvironmentManager, EnvironmentType, EnvironmentStatus
from .file_system import FileSystemManager, OperationType, OperationStatus
from .shell_runner import ShellRunner, CommandStatus, CommandResult
from .variable_system import VariableSystem, VariableType, VariableScope
from .json_handler import JSONHandler, JSONOperationType, JSONValidationLevel


@dataclass
class Phase2Result:
    """Complete result of Phase 2 execution."""
    success: bool
    venv_manager: VirtualEnvironmentManager
    file_system_manager: FileSystemManager
    shell_runner: ShellRunner
    variable_system: VariableSystem
    json_handler: JSONHandler
    execution_time: float
    errors: List[str] = None
    warnings: List[str] = None


class Phase2Launcher:
    """
    Phase 2 launcher for environment management engine.
    
    Orchestrates the complete Phase 2 workflow:
    1. Virtual environment management setup
    2. File system operations setup
    3. Shell command execution setup
    4. Variable system setup
    5. JSON handler setup
    6. Integration testing
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize Phase 2 launcher.
        
        Args:
            base_path: Base path for operations
        """
        self.base_path = base_path
        self.start_time = 0.0
        self.results = {}
        
        # Initialize components
        self.venv_manager = None
        self.file_system_manager = None
        self.shell_runner = None
        self.variable_system = None
        self.json_handler = None
    
    def execute_phase2(self) -> Phase2Result:
        """
        Execute complete Phase 2 workflow.
        
        Returns:
            Phase2Result: Complete Phase 2 execution result
        """
        self.start_time = time.time()
        errors = []
        warnings = []
        
        try:
            print("🚀 Starting Phase 2: Environment Management Engine")
            print("=" * 70)
            
            # Step 1: Virtual Environment Management Setup
            print("\n🐍 Step 1: Setting Up Virtual Environment Management...")
            venv_success = self._setup_venv_manager()
            if not venv_success:
                errors.append("Failed to setup virtual environment manager")
                return self._create_failed_result(errors, warnings)
            
            print("✅ Virtual Environment Manager initialized")
            print(f"   Environments path: {self.venv_manager.environments_path}")
            print(f"   Active environments: {len(self.venv_manager.active_environments)}")
            
            # Step 2: File System Operations Setup
            print("\n📁 Step 2: Setting Up File System Operations...")
            fs_success = self._setup_file_system_manager()
            if not fs_success:
                errors.append("Failed to setup file system manager")
                return self._create_failed_result(errors, warnings)
            
            print("✅ File System Manager initialized")
            print(f"   Base path: {self.file_system_manager.base_path}")
            print(f"   Backup directory: {self.file_system_manager.backup_dir}")
            
            # Step 3: Shell Command Execution Setup
            print("\n💻 Step 3: Setting Up Shell Command Execution...")
            shell_success = self._setup_shell_runner()
            if not shell_success:
                errors.append("Failed to setup shell runner")
                return self._create_failed_result(errors, warnings)
            
            print("✅ Shell Runner initialized")
            print(f"   Base path: {self.shell_runner.base_path}")
            print(f"   Default timeout: {self.shell_runner.default_timeout} seconds")
            
            # Step 4: Variable System Setup
            print("\n🔧 Step 4: Setting Up Variable System...")
            var_success = self._setup_variable_system()
            if not var_success:
                errors.append("Failed to setup variable system")
                return self._create_failed_result(errors, warnings)
            
            print("✅ Variable System initialized")
            print(f"   Base path: {self.variable_system.base_path}")
            print(f"   Persistent file: {self.variable_system.persistent_file}")
            print(f"   Total variables: {len(self.variable_system.variables)}")
            
            # Step 5: JSON Handler Setup
            print("\n📄 Step 5: Setting Up JSON Handler...")
            json_success = self._setup_json_handler()
            if not json_success:
                errors.append("Failed to setup JSON handler")
                return self._create_failed_result(errors, warnings)
            
            print("✅ JSON Handler initialized")
            print(f"   Base path: {self.json_handler.base_path}")
            print(f"   Cache TTL: {self.json_handler.cache_ttl} seconds")
            
            # Step 6: Integration Testing
            print("\n🔗 Step 6: Running Integration Tests...")
            integration_success = self._run_integration_tests()
            if not integration_success:
                warnings.append("Some integration tests failed")
            
            # Calculate execution time
            execution_time = time.time() - self.start_time
            
            print(f"\n🎉 Phase 2 Complete! Execution Time: {execution_time:.2f} seconds")
            print("=" * 70)
            
            return Phase2Result(
                success=True,
                venv_manager=self.venv_manager,
                file_system_manager=self.file_system_manager,
                shell_runner=self.shell_runner,
                variable_system=self.variable_system,
                json_handler=self.json_handler,
                execution_time=execution_time,
                errors=errors,
                warnings=warnings
            )
        
        except Exception as e:
            errors.append(f"Phase 2 execution failed: {str(e)}")
            execution_time = time.time() - self.start_time
            return self._create_failed_result(errors, warnings, execution_time)
    
    def _setup_venv_manager(self) -> bool:
        """Setup virtual environment manager."""
        try:
            self.venv_manager = VirtualEnvironmentManager(self.base_path)
            
            # Set up progress callback
            def venv_progress_callback(operation):
                if operation.progress_percent % 25 == 0:  # Log every 25%
                    print(f"     {operation.current_step}: {operation.progress_percent:.0f}%")
            
            self.venv_manager.set_progress_callback(venv_progress_callback)
            
            # Test environment creation
            print("     Testing environment creation...")
            test_env_name = "phase2_test_env"
            operation = self.venv_manager.create_environment(
                test_env_name, 
                EnvironmentType.PYTHON_VENV, 
                force_recreate=True
            )
            
            if operation.status == "completed":
                print(f"     ✅ Test environment created: {test_env_name}")
                
                # Test activation
                if self.venv_manager.activate_environment(test_env_name):
                    print("     ✅ Test environment activated")
                    
                    # Test dependency installation
                    install_op = self.venv_manager.install_dependencies(
                        test_env_name, 
                        ["requests"]
                    )
                    
                    if install_op.status == "completed":
                        print("     ✅ Test dependency installed")
                    else:
                        print(f"     ⚠️  Dependency installation failed: {install_op.error_message}")
                    
                    # Test deactivation
                    self.venv_manager.deactivate_environment(test_env_name)
                    print("     ✅ Test environment deactivated")
                
                # Cleanup test environment
                self.venv_manager.destroy_environment(test_env_name)
                print("     ✅ Test environment cleaned up")
            
            else:
                print(f"     ❌ Test environment creation failed: {operation.error_message}")
                return False
            
            return True
        
        except Exception as e:
            print(f"     ❌ Virtual environment manager setup failed: {str(e)}")
            return False
    
    def _setup_file_system_manager(self) -> bool:
        """Setup file system manager."""
        try:
            self.file_system_manager = FileSystemManager(self.base_path)
            
            # Set up progress callback
            def fs_progress_callback(operation):
                print(f"     {operation.operation_type.value}: {operation.status}")
            
            self.file_system_manager.set_progress_callback(fs_progress_callback)
            
            # Test file operations
            print("     Testing file operations...")
            test_dir = os.path.join(self.base_path, "phase2_test")
            os.makedirs(test_dir, exist_ok=True)
            
            test_file = os.path.join(test_dir, "test.txt")
            test_content = "Phase 2 test content"
            
            # Test file write
            op_id = self.file_system_manager.write_file(test_file, test_content)
            time.sleep(1)  # Wait for operation to complete
            
            operation = self.file_system_manager.get_operation_status(op_id)
            if operation and operation.status == OperationStatus.COMPLETED:
                print("     ✅ File write operation successful")
                
                # Test file read
                success, content = self.file_system_manager.read_file(test_file)
                if success and content == test_content:
                    print("     ✅ File read operation successful")
                else:
                    print("     ❌ File read operation failed")
                    return False
                
                # Test file copy
                copy_file = os.path.join(test_dir, "test_copy.txt")
                op_id = self.file_system_manager.copy_file(test_file, copy_file)
                time.sleep(1)
                
                operation = self.file_system_manager.get_operation_status(op_id)
                if operation and operation.status == OperationStatus.COMPLETED:
                    print("     ✅ File copy operation successful")
                else:
                    print("     ❌ File copy operation failed")
                    return False
                
                # Test file info
                file_info = self.file_system_manager.get_file_info(test_file)
                if file_info:
                    print(f"     ✅ File info retrieved: {file_info.size_bytes} bytes")
                else:
                    print("     ❌ File info retrieval failed")
                    return False
            
            else:
                print(f"     ❌ File write operation failed: {operation.error_message if operation else 'Unknown error'}")
                return False
            
            # Cleanup test files
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)
            print("     ✅ Test files cleaned up")
            
            return True
        
        except Exception as e:
            print(f"     ❌ File system manager setup failed: {str(e)}")
            return False
    
    def _setup_shell_runner(self) -> bool:
        """Setup shell runner."""
        try:
            self.shell_runner = ShellRunner(self.base_path)
            
            # Set up progress callback
            def shell_progress_callback(progress):
                if progress.current_output:
                    print(f"     {progress.current_output}")
            
            self.shell_runner.set_progress_callback(shell_progress_callback)
            
            # Test shell commands
            print("     Testing shell commands...")
            
            # Test synchronous command
            result = self.shell_runner.run_command_sync("echo 'Phase 2 test'", timeout=10)
            if result.status == CommandStatus.COMPLETED and "Phase 2 test" in result.stdout:
                print("     ✅ Synchronous command execution successful")
            else:
                print(f"     ❌ Synchronous command execution failed: {result.error_message}")
                return False
            
            # Test asynchronous command
            command_id = self.shell_runner.run_command("sleep 1 && echo 'Async test'", realtime_output=True)
            result = self.shell_runner.wait_for_command(command_id, timeout=10)
            
            if result and result.status == CommandStatus.COMPLETED and "Async test" in result.stdout:
                print("     ✅ Asynchronous command execution successful")
            else:
                print(f"     ❌ Asynchronous command execution failed: {result.error_message if result else 'Timeout'}")
                return False
            
            # Test command with environment variables
            env_vars = {"TEST_VAR": "test_value"}
            result = self.shell_runner.run_command_sync("echo $TEST_VAR", environment_vars=env_vars, timeout=10)
            
            if result.status == CommandStatus.COMPLETED and "test_value" in result.stdout:
                print("     ✅ Environment variable command execution successful")
            else:
                print(f"     ❌ Environment variable command execution failed: {result.error_message}")
                return False
            
            return True
        
        except Exception as e:
            print(f"     ❌ Shell runner setup failed: {str(e)}")
            return False
    
    def _setup_variable_system(self) -> bool:
        """Setup variable system."""
        try:
            self.variable_system = VariableSystem(self.base_path)
            
            # Test variable operations
            print("     Testing variable operations...")
            
            # Test setting variables
            self.variable_system.set_variable("test_string", "Hello, Phase 2!", VariableType.STRING, VariableScope.LOCAL)
            self.variable_system.set_variable("test_number", 42, VariableType.INTEGER, VariableScope.LOCAL)
            self.variable_system.set_variable("test_boolean", True, VariableType.BOOLEAN, VariableScope.LOCAL)
            
            # Test getting variables
            test_string = self.variable_system.get_variable("test_string")
            test_number = self.variable_system.get_variable("test_number")
            test_boolean = self.variable_system.get_variable("test_boolean")
            
            if test_string == "Hello, Phase 2!" and test_number == 42 and test_boolean == True:
                print("     ✅ Variable setting and retrieval successful")
            else:
                print("     ❌ Variable setting and retrieval failed")
                return False
            
            # Test variable substitution
            test_text = "Message: {{test_string}}, Number: {{test_number}}, Boolean: {{test_boolean}}"
            result = self.variable_system.substitute_variables(test_text)
            
            if result.success and "Hello, Phase 2!" in result.substituted_text:
                print("     ✅ Variable substitution successful")
            else:
                print(f"     ❌ Variable substitution failed: {result.error_message}")
                return False
            
            # Test environment variable substitution
            env_text = "User: ${USER}"
            env_result = self.variable_system.substitute_environment_variables(env_text)
            
            if env_result.success:
                print("     ✅ Environment variable substitution successful")
            else:
                print(f"     ❌ Environment variable substitution failed: {env_result.error_message}")
                return False
            
            # Test persistent storage
            if self.variable_system.save_persistent_variables():
                print("     ✅ Variable persistent storage successful")
            else:
                print("     ❌ Variable persistent storage failed")
                return False
            
            return True
        
        except Exception as e:
            print(f"     ❌ Variable system setup failed: {str(e)}")
            return False
    
    def _setup_json_handler(self) -> bool:
        """Setup JSON handler."""
        try:
            self.json_handler = JSONHandler(self.base_path)
            
            # Test JSON operations
            print("     Testing JSON operations...")
            
            # Test JSON parsing
            test_json = '{"name": "Phase 2", "value": 42, "nested": {"key": "value"}}'
            success, parsed_data, error = self.json_handler.parse_json(test_json)
            
            if success and parsed_data["name"] == "Phase 2":
                print("     ✅ JSON parsing successful")
            else:
                print(f"     ❌ JSON parsing failed: {error}")
                return False
            
            # Test JSON validation
            validation_result = self.json_handler.validate_json(parsed_data, JSONValidationLevel.STRICT)
            
            if validation_result.is_valid:
                print("     ✅ JSON validation successful")
            else:
                print(f"     ❌ JSON validation failed: {validation_result.errors}")
                return False
            
            # Test JSON merging
            base_data = {"a": 1, "b": {"c": 2}}
            merge_data = {"b": {"d": 3}, "e": 4}
            merged_data = self.json_handler.merge_json(base_data, merge_data)
            
            if merged_data["a"] == 1 and merged_data["b"]["d"] == 3 and merged_data["e"] == 4:
                print("     ✅ JSON merging successful")
            else:
                print("     ❌ JSON merging failed")
                return False
            
            # Test JSON value operations
            test_data = {"user": {"profile": {"name": "John", "age": 30}}}
            
            # Get value
            name = self.json_handler.get_json_value(test_data, "user.profile.name")
            if name == "John":
                print("     ✅ JSON value retrieval successful")
            else:
                print("     ❌ JSON value retrieval failed")
                return False
            
            # Set value
            if self.json_handler.set_json_value(test_data, "user.profile.email", "john@example.com"):
                if test_data["user"]["profile"]["email"] == "john@example.com":
                    print("     ✅ JSON value setting successful")
                else:
                    print("     ❌ JSON value setting failed")
                    return False
            else:
                print("     ❌ JSON value setting failed")
                return False
            
            # Test JSON file operations
            test_file = os.path.join(self.base_path, "phase2_test.json")
            
            # Save JSON
            if self.json_handler.save_json(test_data, test_file):
                print("     ✅ JSON file saving successful")
                
                # Load JSON
                success, loaded_data, error = self.json_handler.load_json(test_file)
                if success and loaded_data["user"]["profile"]["name"] == "John":
                    print("     ✅ JSON file loading successful")
                else:
                    print(f"     ❌ JSON file loading failed: {error}")
                    return False
            else:
                print("     ❌ JSON file saving failed")
                return False
            
            # Cleanup test file
            if os.path.exists(test_file):
                os.remove(test_file)
            
            return True
        
        except Exception as e:
            print(f"     ❌ JSON handler setup failed: {str(e)}")
            return False
    
    def _run_integration_tests(self) -> bool:
        """Run integration tests between all components."""
        try:
            print("     Testing component integration...")
            
            # Test 1: Variable system + JSON handler integration
            test_data = {
                "message": "{{test_string}}",
                "number": "{{test_number}}",
                "boolean": "{{test_boolean}}"
            }
            
            # Substitute variables in JSON data
            substituted_data = {}
            for key, value in test_data.items():
                result = self.variable_system.substitute_variables(value)
                substituted_data[key] = result.substituted_text
            
            # Save substituted data as JSON
            test_file = os.path.join(self.base_path, "integration_test.json")
            if self.json_handler.save_json(substituted_data, test_file):
                print("     ✅ Variable-JSON integration successful")
            else:
                print("     ❌ Variable-JSON integration failed")
                return False
            
            # Test 2: File system + JSON handler integration
            success, loaded_data, error = self.json_handler.load_json(test_file)
            if success and loaded_data["message"] == "Hello, Phase 2!":
                print("     ✅ File-JSON integration successful")
            else:
                print(f"     ❌ File-JSON integration failed: {error}")
                return False
            
            # Test 3: Shell runner + Variable system integration
            env_vars = {"PHASE2_VAR": "integration_test"}
            result = self.shell_runner.run_command_sync("echo $PHASE2_VAR", environment_vars=env_vars, timeout=10)
            
            if result.status == CommandStatus.COMPLETED and "integration_test" in result.stdout:
                print("     ✅ Shell-Variable integration successful")
            else:
                print(f"     ❌ Shell-Variable integration failed: {result.error_message}")
                return False
            
            # Cleanup test file
            if os.path.exists(test_file):
                os.remove(test_file)
            
            return True
        
        except Exception as e:
            print(f"     ❌ Integration tests failed: {str(e)}")
            return False
    
    def _create_failed_result(self, errors: List[str], warnings: List[str], 
                            execution_time: float = 0.0) -> Phase2Result:
        """Create a failed Phase 2 result."""
        if execution_time == 0.0:
            execution_time = time.time() - self.start_time
        
        return Phase2Result(
            success=False,
            venv_manager=self.venv_manager,
            file_system_manager=self.file_system_manager,
            shell_runner=self.shell_runner,
            variable_system=self.variable_system,
            json_handler=self.json_handler,
            execution_time=execution_time,
            errors=errors,
            warnings=warnings
        )
    
    def get_phase2_summary(self, result: Phase2Result) -> str:
        """Get a human-readable summary of Phase 2 results."""
        summary = f"Phase 2 Execution Summary:\n"
        summary += f"Success: {result.success}\n"
        summary += f"Execution Time: {result.execution_time:.2f} seconds\n"
        
        if result.success:
            summary += f"Virtual Environment Manager: ✅ Initialized\n"
            summary += f"File System Manager: ✅ Initialized\n"
            summary += f"Shell Runner: ✅ Initialized\n"
            summary += f"Variable System: ✅ Initialized\n"
            summary += f"JSON Handler: ✅ Initialized\n"
        else:
            summary += f"Errors: {len(result.errors)}\n"
            for error in result.errors:
                summary += f"  - {error}\n"
        
        if result.warnings:
            summary += f"Warnings: {len(result.warnings)}\n"
            for warning in result.warnings:
                summary += f"  - {warning}\n"
        
        return summary
    
    def save_results(self, result: Phase2Result, output_path: str = None) -> str:
        """Save Phase 2 results to JSON file."""
        if output_path is None:
            output_path = os.path.join(self.base_path, "phase2_results.json")
        
        try:
            # Convert result to dictionary
            result_dict = asdict(result)
            
            # Remove non-serializable objects
            result_dict['venv_manager'] = "VirtualEnvironmentManager instance"
            result_dict['file_system_manager'] = "FileSystemManager instance"
            result_dict['shell_runner'] = "ShellRunner instance"
            result_dict['variable_system'] = "VariableSystem instance"
            result_dict['json_handler'] = "JSONHandler instance"
            
            # Save to file
            with open(output_path, 'w') as f:
                json.dump(result_dict, f, indent=2, default=str)
            
            return output_path
        
        except Exception as e:
            print(f"Failed to save results: {str(e)}")
            return ""


def main():
    """Main function for testing Phase 2 launcher."""
    print("🧪 Testing Phase 2 Launcher")
    print("=" * 50)
    
    # Initialize launcher
    launcher = Phase2Launcher()
    
    # Execute Phase 2
    result = launcher.execute_phase2()
    
    # Print summary
    print("\n" + launcher.get_phase2_summary(result))
    
    # Save results
    if result.success:
        output_file = launcher.save_results(result)
        if output_file:
            print(f"\n💾 Results saved to: {output_file}")
    
    return result


if __name__ == "__main__":
    main()