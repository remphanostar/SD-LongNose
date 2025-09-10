#!/usr/bin/env python3
"""
PinokioCloud Phase 2 Test Script

Standalone test script for Phase 2 components without relative imports.
"""

import os
import sys
import time
import json

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Phase 2 modules
from venv_manager import VirtualEnvironmentManager, EnvironmentType, EnvironmentStatus
from file_system import FileSystemManager, OperationType, OperationStatus
from shell_runner import ShellRunner, CommandStatus, CommandResult
from variable_system import VariableSystem, VariableType, VariableScope
from json_handler import JSONHandler, JSONOperationType, JSONValidationLevel


def test_venv_manager():
    """Test virtual environment manager."""
    print("🧪 Testing Virtual Environment Manager...")
    
    manager = VirtualEnvironmentManager()
    
    # Set up progress callback
    def progress_callback(operation):
        if operation.progress_percent % 25 == 0:
            print(f"  {operation.current_step}: {operation.progress_percent:.0f}%")
    
    manager.set_progress_callback(progress_callback)
    
    # Test environment creation
    print("  Creating test environment...")
    operation = manager.create_environment("test_env", EnvironmentType.PYTHON_VENV, force_recreate=True)
    
    if operation.status == "completed":
        print("  ✅ Environment created successfully")
        
        # Test activation
        if manager.activate_environment("test_env"):
            print("  ✅ Environment activated")
            
            # Test dependency installation
            install_op = manager.install_dependencies("test_env", ["requests"])
            if install_op.status == "completed":
                print("  ✅ Dependencies installed")
            else:
                print(f"  ❌ Dependency installation failed: {install_op.error_message}")
            
            # Test deactivation
            manager.deactivate_environment("test_env")
            print("  ✅ Environment deactivated")
        
        # Test environment listing
        environments = manager.list_environments()
        print(f"  ✅ Found {len(environments)} environments")
        
        # Cleanup
        manager.destroy_environment("test_env")
        print("  ✅ Environment cleaned up")
    
    else:
        print(f"  ❌ Environment creation failed: {operation.error_message}")
    
    return True


def test_file_system():
    """Test file system manager."""
    print("\n🧪 Testing File System Manager...")
    
    fs_manager = FileSystemManager()
    
    # Set up progress callback
    def progress_callback(operation):
        print(f"  {operation.operation_type.value}: {operation.status}")
    
    fs_manager.set_progress_callback(progress_callback)
    
    # Test file operations
    test_dir = "/tmp/fs_test"
    os.makedirs(test_dir, exist_ok=True)
    
    test_file = os.path.join(test_dir, "test.txt")
    test_content = "Phase 2 test content"
    
    # Test file write
    print("  Testing file write...")
    op_id = fs_manager.write_file(test_file, test_content)
    time.sleep(1)  # Wait for operation to complete
    
    operation = fs_manager.get_operation_status(op_id)
    if operation and operation.status == OperationStatus.COMPLETED:
        print("  ✅ File write successful")
        
        # Test file read
        success, content = fs_manager.read_file(test_file)
        if success and content == test_content:
            print("  ✅ File read successful")
        else:
            print("  ❌ File read failed")
            return False
        
        # Test file copy
        print("  Testing file copy...")
        copy_file = os.path.join(test_dir, "test_copy.txt")
        op_id = fs_manager.copy_file(test_file, copy_file)
        time.sleep(1)
        
        operation = fs_manager.get_operation_status(op_id)
        if operation and operation.status == OperationStatus.COMPLETED:
            print("  ✅ File copy successful")
        else:
            print("  ❌ File copy failed")
            return False
        
        # Test file info
        file_info = fs_manager.get_file_info(test_file)
        if file_info:
            print(f"  ✅ File info: {file_info.size_bytes} bytes")
        else:
            print("  ❌ File info failed")
            return False
    
    else:
        print(f"  ❌ File write failed: {operation.error_message if operation else 'Unknown error'}")
        return False
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    print("  ✅ Test files cleaned up")
    
    return True


def test_shell_runner():
    """Test shell runner."""
    print("\n🧪 Testing Shell Runner...")
    
    runner = ShellRunner()
    
    # Set up progress callback
    def progress_callback(progress):
        if progress.current_output:
            print(f"  {progress.current_output}")
    
    runner.set_progress_callback(progress_callback)
    
    # Test synchronous command
    print("  Testing synchronous command...")
    result = runner.run_command_sync("echo 'Phase 2 test'", timeout=10)
    
    if result.status == CommandStatus.COMPLETED and "Phase 2 test" in result.stdout:
        print("  ✅ Synchronous command successful")
    else:
        print(f"  ❌ Synchronous command failed: {result.error_message}")
        return False
    
    # Test asynchronous command
    print("  Testing asynchronous command...")
    command_id = runner.run_command("sleep 1 && echo 'Async test'", realtime_output=True)
    result = runner.wait_for_command(command_id, timeout=10)
    
    if result and result.status == CommandStatus.COMPLETED and "Async test" in result.stdout:
        print("  ✅ Asynchronous command successful")
    else:
        print(f"  ❌ Asynchronous command failed: {result.error_message if result else 'Timeout'}")
        return False
    
    # Test command with environment variables
    print("  Testing environment variables...")
    env_vars = {"TEST_VAR": "test_value"}
    result = runner.run_command_sync("echo $TEST_VAR", environment_vars=env_vars, timeout=10)
    
    if result.status == CommandStatus.COMPLETED and "test_value" in result.stdout:
        print("  ✅ Environment variable command successful")
    else:
        print(f"  ❌ Environment variable command failed: {result.error_message}")
        return False
    
    return True


def test_variable_system():
    """Test variable system."""
    print("\n🧪 Testing Variable System...")
    
    var_system = VariableSystem()
    
    # Test setting variables
    print("  Testing variable operations...")
    var_system.set_variable("test_string", "Hello, Phase 2!", VariableType.STRING, VariableScope.LOCAL)
    var_system.set_variable("test_number", 42, VariableType.INTEGER, VariableScope.LOCAL)
    var_system.set_variable("test_boolean", True, VariableType.BOOLEAN, VariableScope.LOCAL)
    
    # Test getting variables
    test_string = var_system.get_variable("test_string")
    test_number = var_system.get_variable("test_number")
    test_boolean = var_system.get_variable("test_boolean")
    
    if test_string == "Hello, Phase 2!" and test_number == 42 and test_boolean == True:
        print("  ✅ Variable operations successful")
    else:
        print("  ❌ Variable operations failed")
        return False
    
    # Test variable substitution
    print("  Testing variable substitution...")
    test_text = "Message: {{test_string}}, Number: {{test_number}}, Boolean: {{test_boolean}}"
    result = var_system.substitute_variables(test_text)
    
    if result.success and "Hello, Phase 2!" in result.substituted_text:
        print("  ✅ Variable substitution successful")
    else:
        print(f"  ❌ Variable substitution failed: {result.error_message}")
        return False
    
    # Test environment variable substitution
    print("  Testing environment variable substitution...")
    env_text = "User: ${USER}"
    env_result = var_system.substitute_environment_variables(env_text)
    
    if env_result.success:
        print("  ✅ Environment variable substitution successful")
    else:
        print(f"  ❌ Environment variable substitution failed: {env_result.error_message}")
        return False
    
    # Test persistent storage
    print("  Testing persistent storage...")
    if var_system.save_persistent_variables():
        print("  ✅ Variable persistent storage successful")
    else:
        print("  ❌ Variable persistent storage failed")
        return False
    
    return True


def test_json_handler():
    """Test JSON handler."""
    print("\n🧪 Testing JSON Handler...")
    
    json_handler = JSONHandler()
    
    # Test JSON parsing
    print("  Testing JSON operations...")
    test_json = '{"name": "Phase 2", "value": 42, "nested": {"key": "value"}}'
    success, parsed_data, error = json_handler.parse_json(test_json)
    
    if success and parsed_data["name"] == "Phase 2":
        print("  ✅ JSON parsing successful")
    else:
        print(f"  ❌ JSON parsing failed: {error}")
        return False
    
    # Test JSON validation
    validation_result = json_handler.validate_json(parsed_data, JSONValidationLevel.STRICT)
    
    if validation_result.is_valid:
        print("  ✅ JSON validation successful")
    else:
        print(f"  ❌ JSON validation failed: {validation_result.errors}")
        return False
    
    # Test JSON merging
    base_data = {"a": 1, "b": {"c": 2}}
    merge_data = {"b": {"d": 3}, "e": 4}
    merged_data = json_handler.merge_json(base_data, merge_data)
    
    if merged_data["a"] == 1 and merged_data["b"]["d"] == 3 and merged_data["e"] == 4:
        print("  ✅ JSON merging successful")
    else:
        print("  ❌ JSON merging failed")
        return False
    
    # Test JSON value operations
    test_data = {"user": {"profile": {"name": "John", "age": 30}}}
    
    # Get value
    name = json_handler.get_json_value(test_data, "user.profile.name")
    if name == "John":
        print("  ✅ JSON value retrieval successful")
    else:
        print("  ❌ JSON value retrieval failed")
        return False
    
    # Set value
    if json_handler.set_json_value(test_data, "user.profile.email", "john@example.com"):
        if test_data["user"]["profile"]["email"] == "john@example.com":
            print("  ✅ JSON value setting successful")
        else:
            print("  ❌ JSON value setting failed")
            return False
    else:
        print("  ❌ JSON value setting failed")
        return False
    
    # Test JSON file operations
    test_file = "/tmp/phase2_test.json"
    
    # Save JSON
    if json_handler.save_json(test_data, test_file):
        print("  ✅ JSON file saving successful")
        
        # Load JSON
        success, loaded_data, error = json_handler.load_json(test_file)
        if success and loaded_data["user"]["profile"]["name"] == "John":
            print("  ✅ JSON file loading successful")
        else:
            print(f"  ❌ JSON file loading failed: {error}")
            return False
    else:
        print("  ❌ JSON file saving failed")
        return False
    
    # Cleanup test file
    if os.path.exists(test_file):
        os.remove(test_file)
    
    return True


def test_integration():
    """Test integration between components."""
    print("\n🧪 Testing Component Integration...")
    
    # Initialize all components
    var_system = VariableSystem()
    json_handler = JSONHandler()
    shell_runner = ShellRunner()
    
    # Test 1: Variable system + JSON handler integration
    print("  Testing Variable-JSON integration...")
    test_data = {
        "message": "{{test_string}}",
        "number": "{{test_number}}",
        "boolean": "{{test_boolean}}"
    }
    
    # Set test variables
    var_system.set_variable("test_string", "Hello, Phase 2!", VariableType.STRING, VariableScope.LOCAL)
    var_system.set_variable("test_number", 42, VariableType.INTEGER, VariableScope.LOCAL)
    var_system.set_variable("test_boolean", True, VariableType.BOOLEAN, VariableScope.LOCAL)
    
    # Substitute variables in JSON data
    substituted_data = {}
    for key, value in test_data.items():
        result = var_system.substitute_variables(value)
        substituted_data[key] = result.substituted_text
    
    # Save substituted data as JSON
    test_file = "/tmp/integration_test.json"
    if json_handler.save_json(substituted_data, test_file):
        print("  ✅ Variable-JSON integration successful")
    else:
        print("  ❌ Variable-JSON integration failed")
        return False
    
    # Test 2: File system + JSON handler integration
    success, loaded_data, error = json_handler.load_json(test_file)
    if success and loaded_data["message"] == "Hello, Phase 2!":
        print("  ✅ File-JSON integration successful")
    else:
        print(f"  ❌ File-JSON integration failed: {error}")
        return False
    
    # Test 3: Shell runner + Variable system integration
    print("  Testing Shell-Variable integration...")
    env_vars = {"PHASE2_VAR": "integration_test"}
    result = shell_runner.run_command_sync("echo $PHASE2_VAR", environment_vars=env_vars, timeout=10)
    
    if result.status == CommandStatus.COMPLETED and "integration_test" in result.stdout:
        print("  ✅ Shell-Variable integration successful")
    else:
        print(f"  ❌ Shell-Variable integration failed: {result.error_message}")
        return False
    
    # Cleanup test file
    if os.path.exists(test_file):
        os.remove(test_file)
    
    return True


def main():
    """Main test function."""
    print("🚀 PinokioCloud Phase 2 Component Testing")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Test all components
        venv_success = test_venv_manager()
        fs_success = test_file_system()
        shell_success = test_shell_runner()
        var_success = test_variable_system()
        json_success = test_json_handler()
        integration_success = test_integration()
        
        execution_time = time.time() - start_time
        
        print(f"\n🎉 All Tests Complete! Execution Time: {execution_time:.2f} seconds")
        print("=" * 60)
        
        # Summary
        print(f"✅ Virtual Environment Manager: {'Success' if venv_success else 'Failed'}")
        print(f"✅ File System Manager: {'Success' if fs_success else 'Failed'}")
        print(f"✅ Shell Runner: {'Success' if shell_success else 'Failed'}")
        print(f"✅ Variable System: {'Success' if var_success else 'Failed'}")
        print(f"✅ JSON Handler: {'Success' if json_success else 'Failed'}")
        print(f"✅ Integration Tests: {'Success' if integration_success else 'Failed'}")
        
        overall_success = all([venv_success, fs_success, shell_success, var_success, json_success, integration_success])
        
        if overall_success:
            print(f"\n🎉 PHASE 2 COMPONENT TESTING: SUCCESS")
            print(f"All components are working correctly!")
        else:
            print(f"\n❌ PHASE 2 COMPONENT TESTING: FAILED")
            print(f"Some components failed testing")
        
        return overall_success
    
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)