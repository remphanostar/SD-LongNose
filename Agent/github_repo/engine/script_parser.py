#!/usr/bin/env python3
"""
PinokioCloud Script Parser

This module parses and executes Pinokio install scripts (.js and .json).
It handles the execution of installation steps, command parsing, and script validation.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import subprocess
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import previous phase modules
sys.path.append('/workspace/github_repo')
from environment_management.shell_runner import ShellRunner
from environment_management.variable_system import VariableSystem
from environment_management.json_handler import JSONHandler
from environment_management.file_system import FileSystemManager


class ScriptType(Enum):
    """Enumeration of script types."""
    JAVASCRIPT = "javascript"
    JSON = "json"
    SHELL = "shell"
    PYTHON = "python"
    UNKNOWN = "unknown"


class ExecutionStatus(Enum):
    """Enumeration of execution statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepType(Enum):
    """Enumeration of step types."""
    SHELL_COMMAND = "shell_command"
    FILE_OPERATION = "file_operation"
    DOWNLOAD = "download"
    EXTRACT = "extract"
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    CREATE_DIRECTORY = "create_directory"
    SET_PERMISSIONS = "set_permissions"
    ENVIRONMENT_VARIABLE = "environment_variable"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    FUNCTION_CALL = "function_call"


@dataclass
class ScriptStep:
    """Individual script step."""
    step_id: str
    step_type: StepType
    command: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None
    timeout: int = 300
    retry_count: int = 0
    retry_delay: int = 5
    continue_on_error: bool = False
    working_directory: Optional[str] = None
    environment_variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of script execution."""
    success: bool
    step_id: str
    execution_time: float
    output: str = ""
    error: str = ""
    return_code: int = 0
    status: ExecutionStatus = ExecutionStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScriptExecutionResult:
    """Complete script execution result."""
    success: bool
    script_path: str
    script_type: ScriptType
    total_steps: int
    completed_steps: int
    failed_steps: int
    skipped_steps: int
    execution_time: float
    step_results: List[ExecutionResult] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=list)


class ScriptParser:
    """
    Parses and executes Pinokio install scripts (.js and .json).
    
    Provides comprehensive script parsing and execution including:
    - JavaScript script parsing and execution
    - JSON configuration parsing and execution
    - Shell command execution with timeout and retry
    - File operations and system commands
    - Variable substitution and environment handling
    - Progress tracking and error handling
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the script parser.
        
        Args:
            base_path: Base path for script operations
        """
        self.base_path = base_path
        
        # Initialize components
        self.shell_runner = ShellRunner(base_path)
        self.variable_system = VariableSystem(base_path)
        self.json_handler = JSONHandler(base_path)
        self.file_system = FileSystemManager(base_path)
        
        # Script execution tracking
        self.active_executions: Dict[str, ScriptExecutionResult] = {}
        self.execution_history: List[ScriptExecutionResult] = []
        
        # Progress callback
        self.progress_callback = None
        
        # Supported script patterns
        self.script_patterns = {
            'install.js': ScriptType.JAVASCRIPT,
            'install.json': ScriptType.JSON,
            'setup.sh': ScriptType.SHELL,
            'setup.py': ScriptType.PYTHON,
            'install.sh': ScriptType.SHELL
        }
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def parse_script(self, script_path: str) -> List[ScriptStep]:
        """
        Parse a script file and extract execution steps.
        
        Args:
            script_path: Path to the script file
            
        Returns:
            List of script steps
        """
        try:
            script_type = self._detect_script_type(script_path)
            
            if script_type == ScriptType.JAVASCRIPT:
                return self._parse_javascript_script(script_path)
            elif script_type == ScriptType.JSON:
                return self._parse_json_script(script_path)
            elif script_type == ScriptType.SHELL:
                return self._parse_shell_script(script_path)
            elif script_type == ScriptType.PYTHON:
                return self._parse_python_script(script_path)
            else:
                return []
        
        except Exception as e:
            return []
    
    def execute_script(self, script_path: str, 
                      working_directory: Optional[str] = None,
                      environment_variables: Optional[Dict[str, str]] = None,
                      variables: Optional[Dict[str, Any]] = None) -> ScriptExecutionResult:
        """
        Execute a script file.
        
        Args:
            script_path: Path to the script file
            working_directory: Working directory for execution
            environment_variables: Environment variables to set
            variables: Variables for substitution
            
        Returns:
            ScriptExecutionResult: Complete execution result
        """
        start_time = time.time()
        
        result = ScriptExecutionResult(
            success=False,
            script_path=script_path,
            script_type=ScriptType.UNKNOWN,
            total_steps=0,
            completed_steps=0,
            failed_steps=0,
            skipped_steps=0,
            execution_time=0.0
        )
        
        try:
            self._update_progress(f"Starting script execution: {script_path}")
            
            # Set working directory
            if working_directory:
                original_cwd = os.getcwd()
                os.chdir(working_directory)
            
            # Set environment variables
            if environment_variables:
                for key, value in environment_variables.items():
                    os.environ[key] = value
            
            # Set variables for substitution
            if variables:
                for key, value in variables.items():
                    self.variable_system.set_variable(key, value)
            
            # Parse script
            steps = self.parse_script(script_path)
            result.total_steps = len(steps)
            result.script_type = self._detect_script_type(script_path)
            
            if not steps:
                result.error_messages.append("No steps found in script")
                result.execution_time = time.time() - start_time
                return result
            
            self._update_progress(f"Found {len(steps)} steps to execute")
            
            # Execute steps
            for i, step in enumerate(steps):
                self._update_progress(f"Executing step {i+1}/{len(steps)}: {step.step_id}")
                
                step_result = self._execute_step(step, working_directory)
                result.step_results.append(step_result)
                
                if step_result.status == ExecutionStatus.COMPLETED:
                    result.completed_steps += 1
                elif step_result.status == ExecutionStatus.FAILED:
                    result.failed_steps += 1
                    if not step.continue_on_error:
                        result.error_messages.append(f"Step {step.step_id} failed: {step_result.error}")
                        break
                elif step_result.status == ExecutionStatus.SKIPPED:
                    result.skipped_steps += 1
            
            # Determine overall success
            result.success = result.failed_steps == 0
            result.execution_time = time.time() - start_time
            
            # Restore working directory
            if working_directory:
                os.chdir(original_cwd)
            
            self._update_progress(f"Script execution complete: {result.completed_steps}/{result.total_steps} steps successful")
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Script execution error: {str(e)}")
            result.execution_time = time.time() - start_time
            return result
    
    def execute_script_step(self, step: ScriptStep, 
                           working_directory: Optional[str] = None) -> ExecutionResult:
        """
        Execute a single script step.
        
        Args:
            step: Script step to execute
            working_directory: Working directory for execution
            
        Returns:
            ExecutionResult: Step execution result
        """
        return self._execute_step(step, working_directory)
    
    def validate_script(self, script_path: str) -> Tuple[bool, List[str]]:
        """
        Validate a script file.
        
        Args:
            script_path: Path to the script file
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            if not os.path.exists(script_path):
                return False, ["Script file does not exist"]
            
            script_type = self._detect_script_type(script_path)
            
            if script_type == ScriptType.JAVASCRIPT:
                return self._validate_javascript_script(script_path)
            elif script_type == ScriptType.JSON:
                return self._validate_json_script(script_path)
            elif script_type == ScriptType.SHELL:
                return self._validate_shell_script(script_path)
            elif script_type == ScriptType.PYTHON:
                return self._validate_python_script(script_path)
            else:
                return False, ["Unknown script type"]
        
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
    
    def _detect_script_type(self, script_path: str) -> ScriptType:
        """Detect script type from file path and content."""
        try:
            filename = os.path.basename(script_path).lower()
            
            # Check by filename pattern
            for pattern, script_type in self.script_patterns.items():
                if pattern in filename:
                    return script_type
            
            # Check by file extension
            if script_path.endswith('.js'):
                return ScriptType.JAVASCRIPT
            elif script_path.endswith('.json'):
                return ScriptType.JSON
            elif script_path.endswith('.sh'):
                return ScriptType.SHELL
            elif script_path.endswith('.py'):
                return ScriptType.PYTHON
            else:
                return ScriptType.UNKNOWN
        
        except Exception as e:
            return ScriptType.UNKNOWN
    
    def _parse_javascript_script(self, script_path: str) -> List[ScriptStep]:
        """Parse JavaScript script file."""
        try:
            steps = []
            
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Extract function calls and commands
            # Look for common patterns like shell.run, fs.download, etc.
            patterns = [
                r'shell\.run\(["\']([^"\']+)["\']\)',
                r'fs\.download\(["\']([^"\']+)["\']\)',
                r'fs\.copy\(["\']([^"\']+)["\']\)',
                r'fs\.move\(["\']([^"\']+)["\']\)',
                r'fs\.write\(["\']([^"\']+)["\']\)',
                r'fs\.read\(["\']([^"\']+)["\']\)',
                r'fs\.exists\(["\']([^"\']+)["\']\)',
                r'fs\.rm\(["\']([^"\']+)["\']\)'
            ]
            
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, content)
                for j, match in enumerate(matches):
                    step = ScriptStep(
                        step_id=f"js_step_{i}_{j}",
                        step_type=StepType.SHELL_COMMAND,
                        command=match,
                        timeout=300,
                        retry_count=3,
                        retry_delay=5
                    )
                    steps.append(step)
            
            return steps
        
        except Exception as e:
            return []
    
    def _parse_json_script(self, script_path: str) -> List[ScriptStep]:
        """Parse JSON script file."""
        try:
            steps = []
            
            with open(script_path, 'r') as f:
                config = json.load(f)
            
            # Parse steps from JSON configuration
            script_steps = config.get('steps', [])
            
            for i, step_config in enumerate(script_steps):
                step_type_str = step_config.get('type', 'shell_command')
                step_type = self._parse_step_type(step_type_str)
                
                step = ScriptStep(
                    step_id=step_config.get('id', f"json_step_{i}"),
                    step_type=step_type,
                    command=step_config.get('command', ''),
                    parameters=step_config.get('parameters', {}),
                    condition=step_config.get('condition'),
                    timeout=step_config.get('timeout', 300),
                    retry_count=step_config.get('retry_count', 0),
                    retry_delay=step_config.get('retry_delay', 5),
                    continue_on_error=step_config.get('continue_on_error', False),
                    working_directory=step_config.get('working_directory'),
                    environment_variables=step_config.get('environment_variables', {})
                )
                steps.append(step)
            
            return steps
        
        except Exception as e:
            return []
    
    def _parse_shell_script(self, script_path: str) -> List[ScriptStep]:
        """Parse shell script file."""
        try:
            steps = []
            
            with open(script_path, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line and not line.startswith('#'):
                    step = ScriptStep(
                        step_id=f"shell_step_{i}",
                        step_type=StepType.SHELL_COMMAND,
                        command=line,
                        timeout=300,
                        retry_count=0,
                        retry_delay=5
                    )
                    steps.append(step)
            
            return steps
        
        except Exception as e:
            return []
    
    def _parse_python_script(self, script_path: str) -> List[ScriptStep]:
        """Parse Python script file."""
        try:
            steps = []
            
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Extract subprocess calls and system commands
            patterns = [
                r'subprocess\.run\(["\']([^"\']+)["\']\)',
                r'os\.system\(["\']([^"\']+)["\']\)',
                r'os\.popen\(["\']([^"\']+)["\']\)'
            ]
            
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, content)
                for j, match in enumerate(matches):
                    step = ScriptStep(
                        step_id=f"python_step_{i}_{j}",
                        step_type=StepType.SHELL_COMMAND,
                        command=match,
                        timeout=300,
                        retry_count=0,
                        retry_delay=5
                    )
                    steps.append(step)
            
            return steps
        
        except Exception as e:
            return []
    
    def _parse_step_type(self, step_type_str: str) -> StepType:
        """Parse step type from string."""
        try:
            step_type_map = {
                'shell_command': StepType.SHELL_COMMAND,
                'file_operation': StepType.FILE_OPERATION,
                'download': StepType.DOWNLOAD,
                'extract': StepType.EXTRACT,
                'copy': StepType.COPY,
                'move': StepType.MOVE,
                'delete': StepType.DELETE,
                'create_directory': StepType.CREATE_DIRECTORY,
                'set_permissions': StepType.SET_PERMISSIONS,
                'environment_variable': StepType.ENVIRONMENT_VARIABLE,
                'conditional': StepType.CONDITIONAL,
                'loop': StepType.LOOP,
                'function_call': StepType.FUNCTION_CALL
            }
            
            return step_type_map.get(step_type_str, StepType.SHELL_COMMAND)
        
        except Exception as e:
            return StepType.SHELL_COMMAND
    
    def _execute_step(self, step: ScriptStep, working_directory: Optional[str] = None) -> ExecutionResult:
        """Execute a single script step."""
        start_time = time.time()
        
        result = ExecutionResult(
            success=False,
            step_id=step.step_id,
            execution_time=0.0,
            status=ExecutionStatus.PENDING
        )
        
        try:
            # Check condition if present
            if step.condition:
                if not self._evaluate_condition(step.condition):
                    result.status = ExecutionStatus.SKIPPED
                    result.execution_time = time.time() - start_time
                    return result
            
            # Set working directory
            if step.working_directory:
                original_cwd = os.getcwd()
                os.chdir(step.working_directory)
            elif working_directory:
                original_cwd = os.getcwd()
                os.chdir(working_directory)
            
            # Set environment variables
            for key, value in step.environment_variables.items():
                os.environ[key] = value
            
            # Execute step based on type
            if step.step_type == StepType.SHELL_COMMAND:
                result = self._execute_shell_command(step)
            elif step.step_type == StepType.FILE_OPERATION:
                result = self._execute_file_operation(step)
            elif step.step_type == StepType.DOWNLOAD:
                result = self._execute_download(step)
            elif step.step_type == StepType.EXTRACT:
                result = self._execute_extract(step)
            elif step.step_type == StepType.COPY:
                result = self._execute_copy(step)
            elif step.step_type == StepType.MOVE:
                result = self._execute_move(step)
            elif step.step_type == StepType.DELETE:
                result = self._execute_delete(step)
            elif step.step_type == StepType.CREATE_DIRECTORY:
                result = self._execute_create_directory(step)
            elif step.step_type == StepType.SET_PERMISSIONS:
                result = self._execute_set_permissions(step)
            elif step.step_type == StepType.ENVIRONMENT_VARIABLE:
                result = self._execute_environment_variable(step)
            else:
                result.error = f"Unknown step type: {step.step_type}"
                result.status = ExecutionStatus.FAILED
            
            # Restore working directory
            if step.working_directory or working_directory:
                os.chdir(original_cwd)
            
            result.execution_time = time.time() - start_time
            
            return result
        
        except Exception as e:
            result.error = str(e)
            result.status = ExecutionStatus.FAILED
            result.execution_time = time.time() - start_time
            return result
    
    def _execute_shell_command(self, step: ScriptStep) -> ExecutionResult:
        """Execute shell command step."""
        result = ExecutionResult(
            success=False,
            step_id=step.step_id,
            execution_time=0.0,
            status=ExecutionStatus.PENDING
        )
        
        try:
            # Substitute variables in command
            command = self.variable_system.substitute_variables(step.command)
            
            # Execute command with retry logic
            for attempt in range(step.retry_count + 1):
                try:
                    process_result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=step.timeout
                    )
                    
                    result.return_code = process_result.returncode
                    result.output = process_result.stdout
                    result.error = process_result.stderr
                    
                    if process_result.returncode == 0:
                        result.success = True
                        result.status = ExecutionStatus.COMPLETED
                        break
                    else:
                        if attempt < step.retry_count:
                            time.sleep(step.retry_delay)
                            continue
                        else:
                            result.status = ExecutionStatus.FAILED
                    
                except subprocess.TimeoutExpired:
                    result.error = f"Command timeout after {step.timeout} seconds"
                    if attempt < step.retry_count:
                        time.sleep(step.retry_delay)
                        continue
                    else:
                        result.status = ExecutionStatus.FAILED
                
                except Exception as e:
                    result.error = str(e)
                    if attempt < step.retry_count:
                        time.sleep(step.retry_delay)
                        continue
                    else:
                        result.status = ExecutionStatus.FAILED
            
            return result
        
        except Exception as e:
            result.error = str(e)
            result.status = ExecutionStatus.FAILED
            return result
    
    def _execute_file_operation(self, step: ScriptStep) -> ExecutionResult:
        """Execute file operation step."""
        result = ExecutionResult(
            success=False,
            step_id=step.step_id,
            execution_time=0.0,
            status=ExecutionStatus.PENDING
        )
        
        try:
            operation = step.parameters.get('operation', '')
            source = step.parameters.get('source', '')
            target = step.parameters.get('target', '')
            
            if operation == 'copy':
                self.file_system.copy_file(source, target)
            elif operation == 'move':
                self.file_system.move_file(source, target)
            elif operation == 'delete':
                self.file_system.delete_file(source)
            elif operation == 'create_directory':
                os.makedirs(source, exist_ok=True)
            else:
                result.error = f"Unknown file operation: {operation}"
                result.status = ExecutionStatus.FAILED
                return result
            
            result.success = True
            result.status = ExecutionStatus.COMPLETED
            
            return result
        
        except Exception as e:
            result.error = str(e)
            result.status = ExecutionStatus.FAILED
            return result
    
    def _execute_download(self, step: ScriptStep) -> ExecutionResult:
        """Execute download step."""
        result = ExecutionResult(
            success=False,
            step_id=step.step_id,
            execution_time=0.0,
            status=ExecutionStatus.PENDING
        )
        
        try:
            url = step.parameters.get('url', '')
            target = step.parameters.get('target', '')
            
            if not url or not target:
                result.error = "URL and target required for download"
                result.status = ExecutionStatus.FAILED
                return result
            
            # Use wget or curl to download
            command = f"wget -O {target} {url}"
            download_result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=step.timeout
            )
            
            if download_result.returncode == 0:
                result.success = True
                result.status = ExecutionStatus.COMPLETED
                result.output = f"Downloaded {url} to {target}"
            else:
                result.error = download_result.stderr
                result.status = ExecutionStatus.FAILED
            
            return result
        
        except Exception as e:
            result.error = str(e)
            result.status = ExecutionStatus.FAILED
            return result
    
    def _execute_extract(self, step: ScriptStep) -> ExecutionResult:
        """Execute extract step."""
        result = ExecutionResult(
            success=False,
            step_id=step.step_id,
            execution_time=0.0,
            status=ExecutionStatus.PENDING
        )
        
        try:
            archive = step.parameters.get('archive', '')
            target = step.parameters.get('target', '')
            
            if not archive or not target:
                result.error = "Archive and target required for extract"
                result.status = ExecutionStatus.FAILED
                return result
            
            # Determine extraction command based on file type
            if archive.endswith('.tar.gz') or archive.endswith('.tgz'):
                command = f"tar -xzf {archive} -C {target}"
            elif archive.endswith('.zip'):
                command = f"unzip {archive} -d {target}"
            elif archive.endswith('.tar'):
                command = f"tar -xf {archive} -C {target}"
            else:
                result.error = f"Unsupported archive format: {archive}"
                result.status = ExecutionStatus.FAILED
                return result
            
            extract_result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=step.timeout
            )
            
            if extract_result.returncode == 0:
                result.success = True
                result.status = ExecutionStatus.COMPLETED
                result.output = f"Extracted {archive} to {target}"
            else:
                result.error = extract_result.stderr
                result.status = ExecutionStatus.FAILED
            
            return result
        
        except Exception as e:
            result.error = str(e)
            result.status = ExecutionStatus.FAILED
            return result
    
    def _execute_copy(self, step: ScriptStep) -> ExecutionResult:
        """Execute copy step."""
        return self._execute_file_operation(step)
    
    def _execute_move(self, step: ScriptStep) -> ExecutionResult:
        """Execute move step."""
        return self._execute_file_operation(step)
    
    def _execute_delete(self, step: ScriptStep) -> ExecutionResult:
        """Execute delete step."""
        return self._execute_file_operation(step)
    
    def _execute_create_directory(self, step: ScriptStep) -> ExecutionResult:
        """Execute create directory step."""
        return self._execute_file_operation(step)
    
    def _execute_set_permissions(self, step: ScriptStep) -> ExecutionResult:
        """Execute set permissions step."""
        result = ExecutionResult(
            success=False,
            step_id=step.step_id,
            execution_time=0.0,
            status=ExecutionStatus.PENDING
        )
        
        try:
            path = step.parameters.get('path', '')
            permissions = step.parameters.get('permissions', '755')
            
            if not path:
                result.error = "Path required for set permissions"
                result.status = ExecutionStatus.FAILED
                return result
            
            command = f"chmod {permissions} {path}"
            chmod_result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=step.timeout
            )
            
            if chmod_result.returncode == 0:
                result.success = True
                result.status = ExecutionStatus.COMPLETED
                result.output = f"Set permissions {permissions} on {path}"
            else:
                result.error = chmod_result.stderr
                result.status = ExecutionStatus.FAILED
            
            return result
        
        except Exception as e:
            result.error = str(e)
            result.status = ExecutionStatus.FAILED
            return result
    
    def _execute_environment_variable(self, step: ScriptStep) -> ExecutionResult:
        """Execute environment variable step."""
        result = ExecutionResult(
            success=False,
            step_id=step.step_id,
            execution_time=0.0,
            status=ExecutionStatus.PENDING
        )
        
        try:
            name = step.parameters.get('name', '')
            value = step.parameters.get('value', '')
            
            if not name:
                result.error = "Name required for environment variable"
                result.status = ExecutionStatus.FAILED
                return result
            
            os.environ[name] = value
            result.success = True
            result.status = ExecutionStatus.COMPLETED
            result.output = f"Set environment variable {name}={value}"
            
            return result
        
        except Exception as e:
            result.error = str(e)
            result.status = ExecutionStatus.FAILED
            return result
    
    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate condition string."""
        try:
            # Simple condition evaluation
            # This can be enhanced for more complex conditions
            if '==' in condition:
                left, right = condition.split('==', 1)
                return left.strip() == right.strip()
            elif '!=' in condition:
                left, right = condition.split('!=', 1)
                return left.strip() != right.strip()
            elif 'exists' in condition:
                path = condition.replace('exists', '').strip()
                return os.path.exists(path)
            else:
                return True
        
        except Exception as e:
            return False
    
    def _validate_javascript_script(self, script_path: str) -> Tuple[bool, List[str]]:
        """Validate JavaScript script."""
        try:
            with open(script_path, 'r') as f:
                content = f.read()
            
            errors = []
            
            # Basic syntax validation
            if not content.strip():
                errors.append("Script is empty")
            
            # Check for common patterns
            if 'shell.run' not in content and 'fs.' not in content:
                errors.append("No recognizable Pinokio API calls found")
            
            return len(errors) == 0, errors
        
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
    
    def _validate_json_script(self, script_path: str) -> Tuple[bool, List[str]]:
        """Validate JSON script."""
        try:
            with open(script_path, 'r') as f:
                config = json.load(f)
            
            errors = []
            
            # Check required fields
            if 'steps' not in config:
                errors.append("Missing 'steps' field")
            
            # Validate steps
            steps = config.get('steps', [])
            for i, step in enumerate(steps):
                if 'type' not in step:
                    errors.append(f"Step {i} missing 'type' field")
                if 'command' not in step and 'parameters' not in step:
                    errors.append(f"Step {i} missing 'command' or 'parameters' field")
            
            return len(errors) == 0, errors
        
        except json.JSONDecodeError as e:
            return False, [f"JSON syntax error: {str(e)}"]
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
    
    def _validate_shell_script(self, script_path: str) -> Tuple[bool, List[str]]:
        """Validate shell script."""
        try:
            with open(script_path, 'r') as f:
                content = f.read()
            
            errors = []
            
            # Basic validation
            if not content.strip():
                errors.append("Script is empty")
            
            # Check for shebang
            if not content.startswith('#!/'):
                errors.append("Missing shebang line")
            
            return len(errors) == 0, errors
        
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
    
    def _validate_python_script(self, script_path: str) -> Tuple[bool, List[str]]:
        """Validate Python script."""
        try:
            with open(script_path, 'r') as f:
                content = f.read()
            
            errors = []
            
            # Basic validation
            if not content.strip():
                errors.append("Script is empty")
            
            # Try to compile the script
            try:
                compile(content, script_path, 'exec')
            except SyntaxError as e:
                errors.append(f"Python syntax error: {str(e)}")
            
            return len(errors) == 0, errors
        
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
    
    def _update_progress(self, message: str):
        """Update progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(message)
            except:
                pass


def main():
    """Main function for testing script parser."""
    print("🧪 Testing Script Parser")
    print("=" * 50)
    
    # Initialize parser
    parser = ScriptParser()
    
    # Set up progress callback
    def progress_callback(message):
        print(f"  {message}")
    
    parser.set_progress_callback(progress_callback)
    
    # Test script validation
    print("\n🔍 Testing script validation...")
    
    # Create test scripts
    test_dir = "/tmp/test_scripts"
    os.makedirs(test_dir, exist_ok=True)
    
    # Test JavaScript script
    js_script = """
shell.run("pip install torch")
fs.download("https://example.com/model.bin", "model.bin")
shell.run("python train.py")
"""
    
    js_path = os.path.join(test_dir, "install.js")
    with open(js_path, 'w') as f:
        f.write(js_script)
    
    is_valid, errors = parser.validate_script(js_path)
    print(f"✅ JavaScript script validation: {is_valid}")
    if errors:
        for error in errors:
            print(f"   - {error}")
    
    # Test JSON script
    json_script = {
        "steps": [
            {
                "id": "install_deps",
                "type": "shell_command",
                "command": "pip install torch",
                "timeout": 300
            },
            {
                "id": "download_model",
                "type": "download",
                "parameters": {
                    "url": "https://example.com/model.bin",
                    "target": "model.bin"
                }
            }
        ]
    }
    
    json_path = os.path.join(test_dir, "install.json")
    with open(json_path, 'w') as f:
        json.dump(json_script, f, indent=2)
    
    is_valid, errors = parser.validate_script(json_path)
    print(f"✅ JSON script validation: {is_valid}")
    if errors:
        for error in errors:
            print(f"   - {error}")
    
    # Test script parsing
    print("\n📝 Testing script parsing...")
    
    js_steps = parser.parse_script(js_path)
    print(f"✅ JavaScript script steps: {len(js_steps)}")
    for step in js_steps:
        print(f"   - {step.step_id}: {step.command}")
    
    json_steps = parser.parse_script(json_path)
    print(f"✅ JSON script steps: {len(json_steps)}")
    for step in json_steps:
        print(f"   - {step.step_id}: {step.step_type.value}")
    
    # Test script execution
    print("\n🚀 Testing script execution...")
    
    # Create a simple test script
    test_script = {
        "steps": [
            {
                "id": "test_command",
                "type": "shell_command",
                "command": "echo 'Hello from script parser'",
                "timeout": 30
            }
        ]
    }
    
    test_script_path = os.path.join(test_dir, "test.json")
    with open(test_script_path, 'w') as f:
        json.dump(test_script, f, indent=2)
    
    result = parser.execute_script(test_script_path)
    
    print(f"✅ Script execution success: {result.success}")
    print(f"✅ Total steps: {result.total_steps}")
    print(f"✅ Completed steps: {result.completed_steps}")
    print(f"✅ Failed steps: {result.failed_steps}")
    print(f"✅ Execution time: {result.execution_time:.2f}s")
    
    if result.step_results:
        for step_result in result.step_results:
            print(f"   - {step_result.step_id}: {step_result.status.value}")
            if step_result.output:
                print(f"     Output: {step_result.output.strip()}")
    
    # Cleanup
    shutil.rmtree(test_dir, ignore_errors=True)
    
    return True


if __name__ == "__main__":
    main()