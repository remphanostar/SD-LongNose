#!/usr/bin/env python3
"""
PinokioCloud JSON Handler

This module provides comprehensive JSON operations including parsing, validation,
merging, transformation, and error handling for multi-cloud GPU environments.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
import copy


class JSONOperationType(Enum):
    """Enumeration of JSON operation types."""
    PARSE = "parse"
    VALIDATE = "validate"
    MERGE = "merge"
    TRANSFORM = "transform"
    EXTRACT = "extract"
    SET = "set"
    GET = "get"
    DELETE = "delete"
    SAVE = "save"
    LOAD = "load"


class JSONValidationLevel(Enum):
    """Enumeration of JSON validation levels."""
    BASIC = "basic"
    STRICT = "strict"
    SCHEMA = "schema"


@dataclass
class JSONOperation:
    """Information about a JSON operation."""
    operation_id: str
    operation_type: JSONOperationType
    status: str
    start_time: float
    end_time: Optional[float] = None
    input_data: Any = None
    output_data: Any = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JSONValidationResult:
    """Result of JSON validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    schema_errors: List[str] = field(default_factory=list)
    validation_level: JSONValidationLevel = JSONValidationLevel.BASIC


class JSONHandler:
    """
    Comprehensive JSON operations handler.
    
    Provides parsing, validation, merging, transformation, and error handling
    for multi-cloud GPU environments.
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the JSON handler.
        
        Args:
            base_path: Base path for JSON file operations
        """
        self.base_path = base_path
        self.operations = {}
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.progress_callback = None
        self.operation_lock = threading.Lock()
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def parse_json(self, json_string: str, strict: bool = True) -> Tuple[bool, Any, Optional[str]]:
        """
        Parse JSON string into Python object.
        
        Args:
            json_string: JSON string to parse
            strict: Use strict JSON parsing
            
        Returns:
            Tuple of (success, parsed_data, error_message)
        """
        operation_id = f"parse_{int(time.time())}_{hash(json_string) % 10000}"
        
        with self.operation_lock:
            operation = JSONOperation(
                operation_id=operation_id,
                operation_type=JSONOperationType.PARSE,
                status="starting",
                start_time=time.time(),
                input_data=json_string
            )
            self.operations[operation_id] = operation
        
        try:
            # Check cache first
            cache_key = f"parse_{hashlib.md5(json_string.encode()).hexdigest()}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if time.time() - cached_data["timestamp"] < self.cache_ttl:
                    operation.status = "completed"
                    operation.end_time = time.time()
                    operation.output_data = cached_data["data"]
                    return True, cached_data["data"], None
            
            # Parse JSON
            if strict:
                parsed_data = json.loads(json_string)
            else:
                # Try to parse with more lenient settings
                parsed_data = json.loads(json_string, strict=False)
            
            # Cache result
            self.cache[cache_key] = {
                "data": parsed_data,
                "timestamp": time.time()
            }
            
            operation.status = "completed"
            operation.end_time = time.time()
            operation.output_data = parsed_data
            
            return True, parsed_data, None
        
        except json.JSONDecodeError as e:
            error_msg = f"JSON decode error: {str(e)}"
            operation.status = "failed"
            operation.end_time = time.time()
            operation.error_message = error_msg
            return False, None, error_msg
        
        except Exception as e:
            error_msg = f"JSON parse error: {str(e)}"
            operation.status = "failed"
            operation.end_time = time.time()
            operation.error_message = error_msg
            return False, None, error_msg
    
    def validate_json(self, data: Any, validation_level: JSONValidationLevel = JSONValidationLevel.BASIC,
                     schema: Optional[Dict[str, Any]] = None) -> JSONValidationResult:
        """
        Validate JSON data structure and content.
        
        Args:
            data: Data to validate
            validation_level: Level of validation to perform
            schema: Optional JSON schema for validation
            
        Returns:
            JSONValidationResult: Validation result
        """
        operation_id = f"validate_{int(time.time())}_{hash(str(data)) % 10000}"
        
        with self.operation_lock:
            operation = JSONOperation(
                operation_id=operation_id,
                operation_type=JSONOperationType.VALIDATE,
                status="starting",
                start_time=time.time(),
                input_data=data
            )
            self.operations[operation_id] = operation
        
        try:
            result = JSONValidationResult(
                is_valid=True,
                validation_level=validation_level
            )
            
            # Basic validation
            if validation_level in [JSONValidationLevel.BASIC, JSONValidationLevel.STRICT, JSONValidationLevel.SCHEMA]:
                if not self._is_valid_json_type(data):
                    result.is_valid = False
                    result.errors.append("Invalid JSON data type")
            
            # Strict validation
            if validation_level in [JSONValidationLevel.STRICT, JSONValidationLevel.SCHEMA]:
                strict_errors = self._validate_strict_json(data)
                result.errors.extend(strict_errors)
                if strict_errors:
                    result.is_valid = False
            
            # Schema validation
            if validation_level == JSONValidationLevel.SCHEMA and schema:
                schema_errors = self._validate_json_schema(data, schema)
                result.schema_errors.extend(schema_errors)
                if schema_errors:
                    result.is_valid = False
            
            operation.status = "completed"
            operation.end_time = time.time()
            operation.output_data = result
            
            return result
        
        except Exception as e:
            error_msg = f"JSON validation error: {str(e)}"
            operation.status = "failed"
            operation.end_time = time.time()
            operation.error_message = error_msg
            
            return JSONValidationResult(
                is_valid=False,
                errors=[error_msg],
                validation_level=validation_level
            )
    
    def merge_json(self, base_data: Dict[str, Any], merge_data: Dict[str, Any],
                  deep_merge: bool = True, overwrite: bool = True) -> Dict[str, Any]:
        """
        Merge two JSON objects.
        
        Args:
            base_data: Base JSON object
            merge_data: JSON object to merge
            deep_merge: Perform deep merging
            overwrite: Overwrite existing keys
            
        Returns:
            Dict: Merged JSON object
        """
        operation_id = f"merge_{int(time.time())}_{hash(str(base_data)) % 10000}"
        
        with self.operation_lock:
            operation = JSONOperation(
                operation_id=operation_id,
                operation_type=JSONOperationType.MERGE,
                status="starting",
                start_time=time.time(),
                input_data={"base": base_data, "merge": merge_data}
            )
            self.operations[operation_id] = operation
        
        try:
            if deep_merge:
                merged_data = self._deep_merge(base_data, merge_data, overwrite)
            else:
                merged_data = base_data.copy()
                for key, value in merge_data.items():
                    if overwrite or key not in merged_data:
                        merged_data[key] = value
            
            operation.status = "completed"
            operation.end_time = time.time()
            operation.output_data = merged_data
            
            return merged_data
        
        except Exception as e:
            error_msg = f"JSON merge error: {str(e)}"
            operation.status = "failed"
            operation.end_time = time.time()
            operation.error_message = error_msg
            return base_data
    
    def get_json_value(self, data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """
        Get value from JSON object using dot notation key path.
        
        Args:
            data: JSON object
            key_path: Dot notation path (e.g., "user.profile.name")
            default: Default value if key not found
            
        Returns:
            Value at key path or default
        """
        try:
            keys = key_path.split('.')
            current_data = data
            
            for key in keys:
                if isinstance(current_data, dict) and key in current_data:
                    current_data = current_data[key]
                else:
                    return default
            
            return current_data
        
        except Exception as e:
            return default
    
    def set_json_value(self, data: Dict[str, Any], key_path: str, value: Any) -> bool:
        """
        Set value in JSON object using dot notation key path.
        
        Args:
            data: JSON object
            key_path: Dot notation path (e.g., "user.profile.name")
            value: Value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            keys = key_path.split('.')
            current_data = data
            
            # Navigate to parent of target key
            for key in keys[:-1]:
                if key not in current_data:
                    current_data[key] = {}
                current_data = current_data[key]
            
            # Set the value
            current_data[keys[-1]] = value
            return True
        
        except Exception as e:
            return False
    
    def delete_json_value(self, data: Dict[str, Any], key_path: str) -> bool:
        """
        Delete value from JSON object using dot notation key path.
        
        Args:
            data: JSON object
            key_path: Dot notation path (e.g., "user.profile.name")
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            keys = key_path.split('.')
            current_data = data
            
            # Navigate to parent of target key
            for key in keys[:-1]:
                if isinstance(current_data, dict) and key in current_data:
                    current_data = current_data[key]
                else:
                    return False
            
            # Delete the key
            if isinstance(current_data, dict) and keys[-1] in current_data:
                del current_data[keys[-1]]
                return True
            
            return False
        
        except Exception as e:
            return False
    
    def transform_json(self, data: Any, transformation_rules: Dict[str, Any]) -> Any:
        """
        Transform JSON data using transformation rules.
        
        Args:
            data: Data to transform
            transformation_rules: Rules for transformation
            
        Returns:
            Transformed data
        """
        operation_id = f"transform_{int(time.time())}_{hash(str(data)) % 10000}"
        
        with self.operation_lock:
            operation = JSONOperation(
                operation_id=operation_id,
                operation_type=JSONOperationType.TRANSFORM,
                status="starting",
                start_time=time.time(),
                input_data=data
            )
            self.operations[operation_id] = operation
        
        try:
            transformed_data = self._apply_transformations(data, transformation_rules)
            
            operation.status = "completed"
            operation.end_time = time.time()
            operation.output_data = transformed_data
            
            return transformed_data
        
        except Exception as e:
            error_msg = f"JSON transformation error: {str(e)}"
            operation.status = "failed"
            operation.end_time = time.time()
            operation.error_message = error_msg
            return data
    
    def save_json(self, data: Any, file_path: str, indent: int = 2, 
                 ensure_ascii: bool = False) -> bool:
        """
        Save JSON data to file.
        
        Args:
            data: Data to save
            file_path: File path to save to
            indent: JSON indentation
            ensure_ascii: Ensure ASCII encoding
            
        Returns:
            bool: True if successful, False otherwise
        """
        operation_id = f"save_{int(time.time())}_{hash(str(data)) % 10000}"
        
        with self.operation_lock:
            operation = JSONOperation(
                operation_id=operation_id,
                operation_type=JSONOperationType.SAVE,
                status="starting",
                start_time=time.time(),
                input_data=data
            )
            self.operations[operation_id] = operation
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save JSON to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            
            operation.status = "completed"
            operation.end_time = time.time()
            operation.output_data = file_path
            
            return True
        
        except Exception as e:
            error_msg = f"JSON save error: {str(e)}"
            operation.status = "failed"
            operation.end_time = time.time()
            operation.error_message = error_msg
            return False
    
    def load_json(self, file_path: str) -> Tuple[bool, Any, Optional[str]]:
        """
        Load JSON data from file.
        
        Args:
            file_path: File path to load from
            
        Returns:
            Tuple of (success, loaded_data, error_message)
        """
        operation_id = f"load_{int(time.time())}_{hash(file_path) % 10000}"
        
        with self.operation_lock:
            operation = JSONOperation(
                operation_id=operation_id,
                operation_type=JSONOperationType.LOAD,
                status="starting",
                start_time=time.time(),
                input_data=file_path
            )
            self.operations[operation_id] = operation
        
        try:
            # Check cache first
            cache_key = f"load_{file_path}"
            if cache_key in self.cache:
                cached_data = self.cache[cache_key]
                if time.time() - cached_data["timestamp"] < self.cache_ttl:
                    operation.status = "completed"
                    operation.end_time = time.time()
                    operation.output_data = cached_data["data"]
                    return True, cached_data["data"], None
            
            # Load JSON from file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cache result
            self.cache[cache_key] = {
                "data": data,
                "timestamp": time.time()
            }
            
            operation.status = "completed"
            operation.end_time = time.time()
            operation.output_data = data
            
            return True, data, None
        
        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            operation.status = "failed"
            operation.end_time = time.time()
            operation.error_message = error_msg
            return False, None, error_msg
        
        except json.JSONDecodeError as e:
            error_msg = f"JSON decode error in file {file_path}: {str(e)}"
            operation.status = "failed"
            operation.end_time = time.time()
            operation.error_message = error_msg
            return False, None, error_msg
        
        except Exception as e:
            error_msg = f"JSON load error: {str(e)}"
            operation.status = "failed"
            operation.end_time = time.time()
            operation.error_message = error_msg
            return False, None, error_msg
    
    def _is_valid_json_type(self, data: Any) -> bool:
        """Check if data is a valid JSON type."""
        return isinstance(data, (dict, list, str, int, float, bool, type(None)))
    
    def _validate_strict_json(self, data: Any) -> List[str]:
        """Perform strict JSON validation."""
        errors = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                if not isinstance(key, str):
                    errors.append(f"Dictionary key must be string: {key}")
                if not self._is_valid_json_type(value):
                    errors.append(f"Invalid value type for key '{key}': {type(value)}")
                else:
                    errors.extend(self._validate_strict_json(value))
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if not self._is_valid_json_type(item):
                    errors.append(f"Invalid item type at index {i}: {type(item)}")
                else:
                    errors.extend(self._validate_strict_json(item))
        
        return errors
    
    def _validate_json_schema(self, data: Any, schema: Dict[str, Any]) -> List[str]:
        """Validate JSON data against schema."""
        errors = []
        
        # Basic schema validation (simplified)
        if "type" in schema:
            expected_type = schema["type"]
            if expected_type == "object" and not isinstance(data, dict):
                errors.append(f"Expected object, got {type(data)}")
            elif expected_type == "array" and not isinstance(data, list):
                errors.append(f"Expected array, got {type(data)}")
            elif expected_type == "string" and not isinstance(data, str):
                errors.append(f"Expected string, got {type(data)}")
            elif expected_type == "number" and not isinstance(data, (int, float)):
                errors.append(f"Expected number, got {type(data)}")
            elif expected_type == "boolean" and not isinstance(data, bool):
                errors.append(f"Expected boolean, got {type(data)}")
        
        # Properties validation for objects
        if isinstance(data, dict) and "properties" in schema:
            properties = schema["properties"]
            for key, value in data.items():
                if key in properties:
                    prop_schema = properties[key]
                    prop_errors = self._validate_json_schema(value, prop_schema)
                    errors.extend([f"Property '{key}': {error}" for error in prop_errors])
        
        return errors
    
    def _deep_merge(self, base: Dict[str, Any], merge: Dict[str, Any], overwrite: bool = True) -> Dict[str, Any]:
        """Perform deep merge of two dictionaries."""
        result = copy.deepcopy(base)
        
        for key, value in merge.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value, overwrite)
            elif overwrite or key not in result:
                result[key] = copy.deepcopy(value)
        
        return result
    
    def _apply_transformations(self, data: Any, rules: Dict[str, Any]) -> Any:
        """Apply transformation rules to data."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Apply key transformation
                new_key = key
                if "key_transform" in rules:
                    new_key = rules["key_transform"](key)
                
                # Apply value transformation
                new_value = value
                if "value_transform" in rules:
                    new_value = rules["value_transform"](value)
                elif isinstance(value, (dict, list)):
                    new_value = self._apply_transformations(value, rules)
                
                result[new_key] = new_value
            
            return result
        
        elif isinstance(data, list):
            result = []
            for item in data:
                if "item_transform" in rules:
                    new_item = rules["item_transform"](item)
                else:
                    new_item = self._apply_transformations(item, rules)
                result.append(new_item)
            
            return result
        
        else:
            # Apply value transformation to primitive types
            if "value_transform" in rules:
                return rules["value_transform"](data)
            return data
    
    def get_operation_status(self, operation_id: str) -> Optional[JSONOperation]:
        """Get status of a JSON operation."""
        return self.operations.get(operation_id)
    
    def cleanup_old_operations(self, max_age_hours: int = 24):
        """Clean up old operation records."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        operations_to_remove = []
        for op_id, operation in self.operations.items():
            if current_time - operation.start_time > max_age_seconds:
                operations_to_remove.append(op_id)
        
        for op_id in operations_to_remove:
            del self.operations[op_id]
    
    def clear_cache(self):
        """Clear the JSON cache."""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache),
            "cache_ttl": self.cache_ttl,
            "operations_count": len(self.operations)
        }


def main():
    """Main function for testing JSON handler."""
    print("🧪 Testing JSON Handler")
    print("=" * 50)
    
    # Initialize JSON handler
    json_handler = JSONHandler()
    
    # Test JSON parsing
    print("\n📝 Testing JSON parsing...")
    test_json = '{"name": "test", "value": 42, "nested": {"key": "value"}}'
    success, parsed_data, error = json_handler.parse_json(test_json)
    
    if success:
        print(f"✅ JSON parsed successfully: {parsed_data}")
    else:
        print(f"❌ JSON parsing failed: {error}")
    
    # Test JSON validation
    print("\n✅ Testing JSON validation...")
    validation_result = json_handler.validate_json(parsed_data, JSONValidationLevel.STRICT)
    
    if validation_result.is_valid:
        print("✅ JSON validation passed")
    else:
        print(f"❌ JSON validation failed: {validation_result.errors}")
    
    # Test JSON merging
    print("\n🔄 Testing JSON merging...")
    base_data = {"a": 1, "b": {"c": 2}}
    merge_data = {"b": {"d": 3}, "e": 4}
    merged_data = json_handler.merge_json(base_data, merge_data)
    
    print(f"✅ JSON merged: {merged_data}")
    
    # Test JSON value operations
    print("\n🔍 Testing JSON value operations...")
    test_data = {"user": {"profile": {"name": "John", "age": 30}}}
    
    # Get value
    name = json_handler.get_json_value(test_data, "user.profile.name")
    print(f"✅ Retrieved value: {name}")
    
    # Set value
    json_handler.set_json_value(test_data, "user.profile.email", "john@example.com")
    print(f"✅ Set value: {test_data}")
    
    # Test JSON file operations
    print("\n💾 Testing JSON file operations...")
    test_file = "/tmp/test.json"
    
    # Save JSON
    if json_handler.save_json(test_data, test_file):
        print("✅ JSON saved to file")
        
        # Load JSON
        success, loaded_data, error = json_handler.load_json(test_file)
        if success:
            print(f"✅ JSON loaded from file: {loaded_data}")
        else:
            print(f"❌ JSON loading failed: {error}")
    
    # Test cache stats
    print("\n📊 Testing cache statistics...")
    cache_stats = json_handler.get_cache_stats()
    print(f"✅ Cache stats: {cache_stats}")
    
    # Test cleanup
    print("\n🗑️  Testing cleanup...")
    json_handler.cleanup_old_operations()
    json_handler.clear_cache()
    print("✅ Cleanup complete")
    
    # Clean up test file
    if os.path.exists(test_file):
        os.remove(test_file)
    
    return True


if __name__ == "__main__":
    main()