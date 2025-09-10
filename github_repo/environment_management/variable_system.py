#!/usr/bin/env python3
"""
PinokioCloud Variable System

This module provides comprehensive variable management including memory variables,
environment variables, dynamic variable substitution, and variable persistence
for multi-cloud GPU environments.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import random
import string
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
import re


class VariableType(Enum):
    """Enumeration of variable types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    FUNCTION = "function"


class VariableScope(Enum):
    """Enumeration of variable scopes."""
    GLOBAL = "global"
    LOCAL = "local"
    ENVIRONMENT = "environment"
    TEMPORARY = "temporary"


@dataclass
class Variable:
    """Information about a variable."""
    name: str
    value: Any
    var_type: VariableType
    scope: VariableScope
    created_time: float
    modified_time: float
    description: str = ""
    is_readonly: bool = False
    is_encrypted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VariableSubstitution:
    """Information about variable substitution."""
    original_text: str
    substituted_text: str
    variables_found: List[str]
    substitution_count: int
    success: bool
    error_message: Optional[str] = None


class VariableSystem:
    """
    Comprehensive variable management system.
    
    Manages memory variables, environment variables, dynamic variable substitution,
    and variable persistence for multi-cloud GPU environments.
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the variable system.
        
        Args:
            base_path: Base path for variable storage
        """
        self.base_path = base_path
        self.variables = {}
        self.variable_locks = {}
        self.substitution_patterns = {
            "memory": r'\{\{([^}]+)\}\}',
            "env": r'\$\{([^}]+)\}',
            "simple": r'\$([a-zA-Z_][a-zA-Z0-9_]*)'
        }
        self.persistent_file = os.path.join(base_path, "variables.json")
        self.auto_save = True
        self.save_interval = 300  # 5 minutes
        self.last_save_time = time.time()
        
        # Initialize built-in variables
        self._initialize_builtin_variables()
        
        # Load persistent variables
        self._load_persistent_variables()
        
        # Start auto-save thread
        self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self.auto_save_thread.start()
    
    def _initialize_builtin_variables(self):
        """Initialize built-in system variables."""
        # Platform variables
        self.set_variable("platform", os.name, VariableType.STRING, VariableScope.GLOBAL, "Operating system platform")
        self.set_variable("python_version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", 
                         VariableType.STRING, VariableScope.GLOBAL, "Python version")
        
        # Path variables
        self.set_variable("base_path", self.base_path, VariableType.STRING, VariableScope.GLOBAL, "Base working directory")
        self.set_variable("cwd", os.getcwd(), VariableType.STRING, VariableScope.GLOBAL, "Current working directory")
        
        # Time variables
        self.set_variable("timestamp", int(time.time()), VariableType.INTEGER, VariableScope.GLOBAL, "Current timestamp")
        self.set_variable("random", random.randint(1000, 9999), VariableType.INTEGER, VariableScope.GLOBAL, "Random number")
        
        # Cloud-specific variables (will be updated by cloud detection)
        self.set_variable("cloud.base_path", self.base_path, VariableType.STRING, VariableScope.GLOBAL, "Cloud platform base path")
        self.set_variable("cloud.platform", "unknown", VariableType.STRING, VariableScope.GLOBAL, "Cloud platform name")
        
        # GPU variables
        self.set_variable("gpu", "unknown", VariableType.STRING, VariableScope.GLOBAL, "GPU information")
        
        # Port variables
        self.set_variable("port", 8000, VariableType.INTEGER, VariableScope.GLOBAL, "Default port number")
    
    def set_variable(self, name: str, value: Any, var_type: VariableType = VariableType.STRING,
                    scope: VariableScope = VariableScope.LOCAL, description: str = "",
                    is_readonly: bool = False, is_encrypted: bool = False) -> bool:
        """
        Set a variable value.
        
        Args:
            name: Variable name
            value: Variable value
            var_type: Variable type
            scope: Variable scope
            description: Variable description
            is_readonly: Whether variable is read-only
            is_encrypted: Whether variable is encrypted
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate variable name
            if not self._is_valid_variable_name(name):
                return False
            
            # Check if variable is read-only
            if name in self.variables and self.variables[name].is_readonly:
                return False
            
            # Convert value to appropriate type
            converted_value = self._convert_value(value, var_type)
            
            # Create or update variable
            current_time = time.time()
            
            if name in self.variables:
                # Update existing variable
                self.variables[name].value = converted_value
                self.variables[name].var_type = var_type
                self.variables[name].scope = scope
                self.variables[name].modified_time = current_time
                if description:
                    self.variables[name].description = description
                if is_readonly:
                    self.variables[name].is_readonly = is_readonly
                if is_encrypted:
                    self.variables[name].is_encrypted = is_encrypted
            else:
                # Create new variable
                self.variables[name] = Variable(
                    name=name,
                    value=converted_value,
                    var_type=var_type,
                    scope=scope,
                    created_time=current_time,
                    modified_time=current_time,
                    description=description,
                    is_readonly=is_readonly,
                    is_encrypted=is_encrypted
                )
            
            # Trigger auto-save if enabled
            if self.auto_save:
                self._check_auto_save()
            
            return True
        
        except Exception as e:
            return False
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Get a variable value.
        
        Args:
            name: Variable name
            default: Default value if variable not found
            
        Returns:
            Variable value or default
        """
        try:
            # Check memory variables first
            if name in self.variables:
                return self.variables[name].value
            
            # Check environment variables
            if name in os.environ:
                return os.environ[name]
            
            # Check nested variables (e.g., "cloud.platform")
            if "." in name:
                parts = name.split(".")
                if len(parts) == 2:
                    parent_name = parts[0]
                    child_name = parts[1]
                    
                    if parent_name in self.variables:
                        parent_value = self.variables[parent_name].value
                        if isinstance(parent_value, dict) and child_name in parent_value:
                            return parent_value[child_name]
            
            return default
        
        except Exception as e:
            return default
    
    def delete_variable(self, name: str) -> bool:
        """
        Delete a variable.
        
        Args:
            name: Variable name to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if name in self.variables:
                # Check if variable is read-only
                if self.variables[name].is_readonly:
                    return False
                
                del self.variables[name]
                
                # Trigger auto-save if enabled
                if self.auto_save:
                    self._check_auto_save()
                
                return True
            
            return False
        
        except Exception as e:
            return False
    
    def list_variables(self, scope: Optional[VariableScope] = None) -> List[Variable]:
        """
        List all variables, optionally filtered by scope.
        
        Args:
            scope: Optional scope filter
            
        Returns:
            List of Variable objects
        """
        variables = []
        
        try:
            for var in self.variables.values():
                if scope is None or var.scope == scope:
                    variables.append(var)
            
            # Sort by name
            variables.sort(key=lambda x: x.name)
            
        except Exception as e:
            pass
        
        return variables
    
    def substitute_variables(self, text: str, recursive: bool = True, 
                           max_iterations: int = 10) -> VariableSubstitution:
        """
        Substitute variables in text using {{variable}} syntax.
        
        Args:
            text: Text containing variable references
            recursive: Whether to perform recursive substitution
            max_iterations: Maximum number of substitution iterations
            
        Returns:
            VariableSubstitution: Result of substitution
        """
        try:
            original_text = text
            substituted_text = text
            variables_found = []
            substitution_count = 0
            iterations = 0
            
            while iterations < max_iterations:
                # Find all variable references
                pattern = self.substitution_patterns["memory"]
                matches = re.findall(pattern, substituted_text)
                
                if not matches:
                    break
                
                # Substitute each variable
                for var_name in matches:
                    var_name = var_name.strip()
                    var_value = self.get_variable(var_name)
                    
                    if var_value is not None:
                        # Convert value to string
                        if isinstance(var_value, (list, dict)):
                            var_value = json.dumps(var_value)
                        else:
                            var_value = str(var_value)
                        
                        # Replace variable reference
                        old_text = substituted_text
                        substituted_text = substituted_text.replace(f"{{{{{var_name}}}}}", var_value)
                        
                        if old_text != substituted_text:
                            substitution_count += 1
                            if var_name not in variables_found:
                                variables_found.append(var_name)
                    else:
                        # Variable not found - leave as is or replace with empty string
                        substituted_text = substituted_text.replace(f"{{{{{var_name}}}}}", "")
                
                iterations += 1
                
                # If not recursive, break after first iteration
                if not recursive:
                    break
            
            return VariableSubstitution(
                original_text=original_text,
                substituted_text=substituted_text,
                variables_found=variables_found,
                substitution_count=substitution_count,
                success=True
            )
        
        except Exception as e:
            return VariableSubstitution(
                original_text=text,
                substituted_text=text,
                variables_found=[],
                substitution_count=0,
                success=False,
                error_message=str(e)
            )
    
    def substitute_environment_variables(self, text: str) -> VariableSubstitution:
        """
        Substitute environment variables in text using ${VAR} syntax.
        
        Args:
            text: Text containing environment variable references
            
        Returns:
            VariableSubstitution: Result of substitution
        """
        try:
            original_text = text
            substituted_text = text
            variables_found = []
            substitution_count = 0
            
            # Find all environment variable references
            pattern = self.substitution_patterns["env"]
            matches = re.findall(pattern, substituted_text)
            
            # Substitute each environment variable
            for var_name in matches:
                var_name = var_name.strip()
                var_value = os.environ.get(var_name, "")
                
                # Replace variable reference
                old_text = substituted_text
                substituted_text = substituted_text.replace(f"${{{var_name}}}", var_value)
                
                if old_text != substituted_text:
                    substitution_count += 1
                    if var_name not in variables_found:
                        variables_found.append(var_name)
            
            return VariableSubstitution(
                original_text=original_text,
                substituted_text=substituted_text,
                variables_found=variables_found,
                substitution_count=substitution_count,
                success=True
            )
        
        except Exception as e:
            return VariableSubstitution(
                original_text=text,
                substituted_text=text,
                variables_found=[],
                substitution_count=0,
                success=False,
                error_message=str(e)
            )
    
    def substitute_all_variables(self, text: str) -> VariableSubstitution:
        """
        Substitute all types of variables in text.
        
        Args:
            text: Text containing variable references
            
        Returns:
            VariableSubstitution: Result of substitution
        """
        try:
            # First substitute environment variables
            env_result = self.substitute_environment_variables(text)
            
            # Then substitute memory variables
            memory_result = self.substitute_variables(env_result.substituted_text)
            
            # Combine results
            all_variables_found = env_result.variables_found + memory_result.variables_found
            total_substitutions = env_result.substitution_count + memory_result.substitution_count
            
            return VariableSubstitution(
                original_text=text,
                substituted_text=memory_result.substituted_text,
                variables_found=all_variables_found,
                substitution_count=total_substitutions,
                success=env_result.success and memory_result.success,
                error_message=env_result.error_message or memory_result.error_message
            )
        
        except Exception as e:
            return VariableSubstitution(
                original_text=text,
                substituted_text=text,
                variables_found=[],
                substitution_count=0,
                success=False,
                error_message=str(e)
            )
    
    def _is_valid_variable_name(self, name: str) -> bool:
        """Check if variable name is valid."""
        if not name or not isinstance(name, str):
            return False
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', name):
            return False
        
        return True
    
    def _convert_value(self, value: Any, var_type: VariableType) -> Any:
        """Convert value to specified type."""
        try:
            if var_type == VariableType.STRING:
                return str(value)
            elif var_type == VariableType.INTEGER:
                return int(value)
            elif var_type == VariableType.FLOAT:
                return float(value)
            elif var_type == VariableType.BOOLEAN:
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes', 'on']
                else:
                    return bool(value)
            elif var_type == VariableType.LIST:
                if isinstance(value, list):
                    return value
                elif isinstance(value, str):
                    try:
                        return json.loads(value)
                    except:
                        return [value]
                else:
                    return [value]
            elif var_type == VariableType.DICT:
                if isinstance(value, dict):
                    return value
                elif isinstance(value, str):
                    try:
                        return json.loads(value)
                    except:
                        return {"value": value}
                else:
                    return {"value": value}
            else:
                return value
        
        except Exception as e:
            return value
    
    def _load_persistent_variables(self):
        """Load variables from persistent storage."""
        try:
            if os.path.exists(self.persistent_file):
                with open(self.persistent_file, 'r') as f:
                    data = json.load(f)
                
                for var_data in data.get("variables", []):
                    var = Variable(
                        name=var_data["name"],
                        value=var_data["value"],
                        var_type=VariableType(var_data["var_type"]),
                        scope=VariableScope(var_data["scope"]),
                        created_time=var_data["created_time"],
                        modified_time=var_data["modified_time"],
                        description=var_data.get("description", ""),
                        is_readonly=var_data.get("is_readonly", False),
                        is_encrypted=var_data.get("is_encrypted", False),
                        metadata=var_data.get("metadata", {})
                    )
                    self.variables[var.name] = var
        
        except Exception as e:
            pass
    
    def save_persistent_variables(self) -> bool:
        """Save variables to persistent storage."""
        try:
            data = {
                "variables": [],
                "metadata": {
                    "save_time": time.time(),
                    "version": "1.0.0"
                }
            }
            
            for var in self.variables.values():
                var_data = {
                    "name": var.name,
                    "value": var.value,
                    "var_type": var.var_type.value,
                    "scope": var.scope.value,
                    "created_time": var.created_time,
                    "modified_time": var.modified_time,
                    "description": var.description,
                    "is_readonly": var.is_readonly,
                    "is_encrypted": var.is_encrypted,
                    "metadata": var.metadata
                }
                data["variables"].append(var_data)
            
            with open(self.persistent_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.last_save_time = time.time()
            return True
        
        except Exception as e:
            return False
    
    def _check_auto_save(self):
        """Check if auto-save should be triggered."""
        if time.time() - self.last_save_time > self.save_interval:
            self.save_persistent_variables()
    
    def _auto_save_loop(self):
        """Auto-save loop running in background thread."""
        while True:
            try:
                time.sleep(self.save_interval)
                if self.auto_save:
                    self.save_persistent_variables()
            except:
                break
    
    def get_variable_info(self, name: str) -> Optional[Variable]:
        """Get detailed information about a variable."""
        return self.variables.get(name)
    
    def get_variable_summary(self) -> str:
        """Get a summary of all variables."""
        summary = f"Variable System Summary:\n"
        summary += f"Total Variables: {len(self.variables)}\n"
        
        # Group by scope
        scope_counts = {}
        for var in self.variables.values():
            scope_counts[var.scope.value] = scope_counts.get(var.scope.value, 0) + 1
        
        for scope, count in scope_counts.items():
            summary += f"  {scope}: {count}\n"
        
        # Show some example variables
        summary += f"\nExample Variables:\n"
        for var in list(self.variables.values())[:5]:
            summary += f"  {var.name}: {var.value} ({var.var_type.value})\n"
        
        return summary


def main():
    """Main function for testing variable system."""
    print("🧪 Testing Variable System")
    print("=" * 50)
    
    # Initialize variable system
    var_system = VariableSystem()
    
    # Test setting variables
    print("\n📝 Testing variable setting...")
    var_system.set_variable("test_string", "Hello, World!", VariableType.STRING, VariableScope.LOCAL, "Test string variable")
    var_system.set_variable("test_number", 42, VariableType.INTEGER, VariableScope.LOCAL, "Test number variable")
    var_system.set_variable("test_boolean", True, VariableType.BOOLEAN, VariableScope.LOCAL, "Test boolean variable")
    
    print("✅ Variables set successfully")
    
    # Test getting variables
    print("\n📖 Testing variable retrieval...")
    test_string = var_system.get_variable("test_string")
    test_number = var_system.get_variable("test_number")
    test_boolean = var_system.get_variable("test_boolean")
    
    print(f"✅ Retrieved: {test_string}, {test_number}, {test_boolean}")
    
    # Test variable substitution
    print("\n🔄 Testing variable substitution...")
    test_text = "Hello {{test_string}}, the answer is {{test_number}}, and it's {{test_boolean}}!"
    result = var_system.substitute_variables(test_text)
    
    if result.success:
        print(f"✅ Substitution successful: {result.substituted_text}")
        print(f"   Variables found: {result.variables_found}")
        print(f"   Substitutions: {result.substitution_count}")
    else:
        print(f"❌ Substitution failed: {result.error_message}")
    
    # Test environment variable substitution
    print("\n🌍 Testing environment variable substitution...")
    env_text = "Current user: ${USER}, Home: ${HOME}"
    env_result = var_system.substitute_environment_variables(env_text)
    
    if env_result.success:
        print(f"✅ Environment substitution: {env_result.substituted_text}")
    else:
        print(f"❌ Environment substitution failed: {env_result.error_message}")
    
    # Test combined substitution
    print("\n🔄 Testing combined substitution...")
    combined_text = "User: ${USER}, Test: {{test_string}}, Number: {{test_number}}"
    combined_result = var_system.substitute_all_variables(combined_text)
    
    if combined_result.success:
        print(f"✅ Combined substitution: {combined_result.substituted_text}")
    else:
        print(f"❌ Combined substitution failed: {combined_result.error_message}")
    
    # Test variable listing
    print("\n📋 Testing variable listing...")
    variables = var_system.list_variables()
    print(f"✅ Found {len(variables)} variables")
    
    for var in variables[:5]:  # Show first 5
        print(f"  - {var.name}: {var.value} ({var.var_type.value})")
    
    # Test variable summary
    print("\n📊 Testing variable summary...")
    summary = var_system.get_variable_summary()
    print(summary)
    
    # Test persistent storage
    print("\n💾 Testing persistent storage...")
    if var_system.save_persistent_variables():
        print("✅ Variables saved to persistent storage")
    else:
        print("❌ Failed to save variables")
    
    return True


if __name__ == "__main__":
    main()