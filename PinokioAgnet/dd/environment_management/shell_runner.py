#!/usr/bin/env python3
"""
PinokioCloud Shell Command Runner

This module provides comprehensive shell command execution with real-time output,
progress tracking, environment variable support, and multi-platform compatibility
for cloud GPU environments.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import subprocess
import threading
import time
import queue
import signal
import shlex
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class CommandStatus(Enum):
    """Enumeration of command execution statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class CommandResult:
    """Result of a shell command execution."""
    command_id: str
    command: str
    status: CommandStatus
    return_code: int
    stdout: str
    stderr: str
    start_time: float
    end_time: float
    duration: float
    pid: Optional[int] = None
    working_directory: str = ""
    environment_vars: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class CommandProgress:
    """Progress information for a running command."""
    command_id: str
    status: CommandStatus
    progress_percent: float
    current_output: str
    total_output_lines: int
    elapsed_time: float
    estimated_remaining: float


class ShellRunner:
    """
    Comprehensive shell command execution system.
    
    Provides real-time output, progress tracking, environment variable support,
    and multi-platform compatibility for cloud GPU environments.
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the shell runner.
        
        Args:
            base_path: Base path for command execution
        """
        self.base_path = base_path
        self.running_commands = {}
        self.command_results = {}
        self.output_queues = {}
        self.progress_callback = None
        self.default_timeout = 300  # 5 minutes
        self.max_concurrent_commands = 10
    
    def set_progress_callback(self, callback: Callable[[CommandProgress], None]):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def run_command(self, command: str, working_directory: Optional[str] = None,
                   environment_vars: Optional[Dict[str, str]] = None,
                   timeout: Optional[float] = None, realtime_output: bool = True,
                   shell: bool = True) -> str:
        """
        Run a shell command with real-time output and progress tracking.
        
        Args:
            command: Command to execute
            working_directory: Working directory for command
            environment_vars: Environment variables to set
            timeout: Command timeout in seconds
            realtime_output: Enable real-time output streaming
            shell: Use shell for command execution
            
        Returns:
            str: Command ID for tracking
        """
        command_id = f"cmd_{int(time.time())}_{hash(command) % 10000}"
        
        # Set defaults
        if working_directory is None:
            working_directory = self.base_path
        
        if timeout is None:
            timeout = self.default_timeout
        
        if environment_vars is None:
            environment_vars = {}
        
        # Create command result object
        result = CommandResult(
            command_id=command_id,
            command=command,
            status=CommandStatus.PENDING,
            return_code=0,
            stdout="",
            stderr="",
            start_time=time.time(),
            end_time=0.0,
            duration=0.0,
            working_directory=working_directory,
            environment_vars=environment_vars.copy(),
            timeout_seconds=timeout
        )
        
        self.command_results[command_id] = result
        
        # Start command execution in background thread
        thread = threading.Thread(
            target=self._execute_command,
            args=(command_id, command, working_directory, environment_vars, timeout, realtime_output, shell),
            daemon=True
        )
        thread.start()
        
        return command_id
    
    def _execute_command(self, command_id: str, command: str, working_directory: str,
                        environment_vars: Dict[str, str], timeout: float,
                        realtime_output: bool, shell: bool):
        """Execute a command in a background thread."""
        try:
            result = self.command_results[command_id]
            result.status = CommandStatus.RUNNING
            
            # Prepare environment
            env = os.environ.copy()
            env.update(environment_vars)
            
            # Prepare command
            if shell:
                cmd = command
            else:
                cmd = shlex.split(command)
            
            # Create output queue for real-time streaming
            if realtime_output:
                output_queue = queue.Queue()
                self.output_queues[command_id] = output_queue
            
            # Start command process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                cwd=working_directory,
                env=env,
                shell=shell,
                universal_newlines=True,
                bufsize=1
            )
            
            result.pid = process.pid
            self.running_commands[command_id] = process
            
            # Stream output in real-time
            if realtime_output:
                self._stream_output(command_id, process)
            else:
                # Wait for completion
                stdout, stderr = process.communicate(timeout=timeout)
                result.stdout = stdout
                result.stderr = stderr
                result.return_code = process.returncode
            
            # Handle completion
            if process.returncode == 0:
                result.status = CommandStatus.COMPLETED
            else:
                result.status = CommandStatus.FAILED
                result.error_message = f"Command failed with return code {process.returncode}"
            
            result.end_time = time.time()
            result.duration = result.end_time - result.start_time
            
            # Cleanup
            if command_id in self.running_commands:
                del self.running_commands[command_id]
            
            if command_id in self.output_queues:
                del self.output_queues[command_id]
        
        except subprocess.TimeoutExpired:
            result = self.command_results[command_id]
            result.status = CommandStatus.TIMEOUT
            result.end_time = time.time()
            result.duration = result.end_time - result.start_time
            result.error_message = f"Command timed out after {timeout} seconds"
            
            # Kill the process
            if command_id in self.running_commands:
                process = self.running_commands[command_id]
                try:
                    process.kill()
                except:
                    pass
                del self.running_commands[command_id]
        
        except Exception as e:
            result = self.command_results[command_id]
            result.status = CommandStatus.FAILED
            result.end_time = time.time()
            result.duration = result.end_time - result.start_time
            result.error_message = str(e)
            
            if command_id in self.running_commands:
                del self.running_commands[command_id]
        
        finally:
            # Cleanup output queue
            if command_id in self.output_queues:
                del self.output_queues[command_id]
    
    def _stream_output(self, command_id: str, process: subprocess.Popen):
        """Stream command output in real-time."""
        try:
            stdout_lines = []
            stderr_lines = []
            
            # Read output line by line
            while True:
                # Read stdout
                stdout_line = process.stdout.readline()
                if stdout_line:
                    stdout_lines.append(stdout_line.rstrip())
                    self._send_output(command_id, stdout_line.rstrip(), "stdout")
                
                # Read stderr
                stderr_line = process.stderr.readline()
                if stderr_line:
                    stderr_lines.append(stderr_line.rstrip())
                    self._send_output(command_id, stderr_line.rstrip(), "stderr")
                
                # Check if process is done
                if process.poll() is not None:
                    break
            
            # Read any remaining output
            remaining_stdout, remaining_stderr = process.communicate()
            if remaining_stdout:
                stdout_lines.extend(remaining_stdout.splitlines())
                for line in remaining_stdout.splitlines():
                    self._send_output(command_id, line, "stdout")
            
            if remaining_stderr:
                stderr_lines.extend(remaining_stderr.splitlines())
                for line in remaining_stderr.splitlines():
                    self._send_output(command_id, line, "stderr")
            
            # Update result
            result = self.command_results[command_id]
            result.stdout = "\n".join(stdout_lines)
            result.stderr = "\n".join(stderr_lines)
            result.return_code = process.returncode
        
        except Exception as e:
            result = self.command_results[command_id]
            result.error_message = f"Output streaming error: {str(e)}"
    
    def _send_output(self, command_id: str, line: str, output_type: str):
        """Send output line to queue and progress callback."""
        try:
            # Send to output queue
            if command_id in self.output_queues:
                self.output_queues[command_id].put((output_type, line))
            
            # Send to progress callback
            if self.progress_callback:
                result = self.command_results.get(command_id)
                if result:
                    progress = CommandProgress(
                        command_id=command_id,
                        status=result.status,
                        progress_percent=0.0,  # Can't determine progress for shell commands
                        current_output=line,
                        total_output_lines=0,  # Can't determine total lines
                        elapsed_time=time.time() - result.start_time,
                        estimated_remaining=0.0
                    )
                    self.progress_callback(progress)
        
        except Exception as e:
            pass
    
    def get_command_result(self, command_id: str) -> Optional[CommandResult]:
        """Get the result of a command execution."""
        return self.command_results.get(command_id)
    
    def get_command_status(self, command_id: str) -> Optional[CommandStatus]:
        """Get the status of a command execution."""
        result = self.command_results.get(command_id)
        return result.status if result else None
    
    def cancel_command(self, command_id: str) -> bool:
        """
        Cancel a running command.
        
        Args:
            command_id: Command ID to cancel
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if command_id not in self.running_commands:
                return False
            
            process = self.running_commands[command_id]
            
            # Try graceful termination first
            process.terminate()
            
            # Wait a bit for graceful termination
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if graceful termination fails
                process.kill()
                process.wait()
            
            # Update result
            result = self.command_results[command_id]
            result.status = CommandStatus.CANCELLED
            result.end_time = time.time()
            result.duration = result.end_time - result.start_time
            result.error_message = "Command was cancelled"
            
            # Cleanup
            del self.running_commands[command_id]
            if command_id in self.output_queues:
                del self.output_queues[command_id]
            
            return True
        
        except Exception as e:
            return False
    
    def get_realtime_output(self, command_id: str, timeout: float = 1.0) -> List[Tuple[str, str]]:
        """
        Get real-time output from a running command.
        
        Args:
            command_id: Command ID
            timeout: Timeout for getting output
            
        Returns:
            List of (output_type, line) tuples
        """
        output_lines = []
        
        try:
            if command_id not in self.output_queues:
                return output_lines
            
            output_queue = self.output_queues[command_id]
            
            # Get all available output
            while True:
                try:
                    output_type, line = output_queue.get(timeout=timeout)
                    output_lines.append((output_type, line))
                except queue.Empty:
                    break
        
        except Exception as e:
            pass
        
        return output_lines
    
    def wait_for_command(self, command_id: str, timeout: Optional[float] = None) -> Optional[CommandResult]:
        """
        Wait for a command to complete.
        
        Args:
            command_id: Command ID to wait for
            timeout: Maximum time to wait
            
        Returns:
            CommandResult or None if timeout
        """
        start_time = time.time()
        
        while True:
            result = self.command_results.get(command_id)
            if not result:
                return None
            
            if result.status in [CommandStatus.COMPLETED, CommandStatus.FAILED, 
                               CommandStatus.TIMEOUT, CommandStatus.CANCELLED]:
                return result
            
            if timeout and (time.time() - start_time) > timeout:
                return None
            
            time.sleep(0.1)
    
    def run_command_sync(self, command: str, working_directory: Optional[str] = None,
                        environment_vars: Optional[Dict[str, str]] = None,
                        timeout: Optional[float] = None, shell: bool = True) -> CommandResult:
        """
        Run a command synchronously and return the result.
        
        Args:
            command: Command to execute
            working_directory: Working directory for command
            environment_vars: Environment variables to set
            timeout: Command timeout in seconds
            shell: Use shell for command execution
            
        Returns:
            CommandResult: Result of command execution
        """
        command_id = self.run_command(
            command=command,
            working_directory=working_directory,
            environment_vars=environment_vars,
            timeout=timeout,
            realtime_output=False,
            shell=shell
        )
        
        result = self.wait_for_command(command_id, timeout)
        return result if result else CommandResult(
            command_id=command_id,
            command=command,
            status=CommandStatus.FAILED,
            return_code=-1,
            stdout="",
            stderr="",
            start_time=time.time(),
            end_time=time.time(),
            duration=0.0,
            error_message="Command execution failed"
        )
    
    def get_running_commands(self) -> List[str]:
        """Get list of currently running command IDs."""
        return list(self.running_commands.keys())
    
    def cleanup_old_results(self, max_age_hours: int = 24):
        """Clean up old command results."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        results_to_remove = []
        for cmd_id, result in self.command_results.items():
            if current_time - result.start_time > max_age_seconds:
                results_to_remove.append(cmd_id)
        
        for cmd_id in results_to_remove:
            del self.command_results[cmd_id]
    
    def get_command_summary(self, command_id: str) -> str:
        """Get a human-readable summary of command execution."""
        result = self.command_results.get(command_id)
        if not result:
            return f"Command {command_id} not found"
        
        summary = f"Command: {result.command}\n"
        summary += f"Status: {result.status.value}\n"
        summary += f"Return Code: {result.return_code}\n"
        summary += f"Duration: {result.duration:.2f} seconds\n"
        summary += f"Working Directory: {result.working_directory}\n"
        
        if result.pid:
            summary += f"PID: {result.pid}\n"
        
        if result.error_message:
            summary += f"Error: {result.error_message}\n"
        
        if result.stdout:
            summary += f"Stdout ({len(result.stdout.splitlines())} lines):\n"
            summary += result.stdout[:500] + ("..." if len(result.stdout) > 500 else "")
        
        if result.stderr:
            summary += f"\nStderr ({len(result.stderr.splitlines())} lines):\n"
            summary += result.stderr[:500] + ("..." if len(result.stderr) > 500 else "")
        
        return summary


def main():
    """Main function for testing shell command runner."""
    print("🧪 Testing Shell Command Runner")
    print("=" * 50)
    
    # Initialize runner
    runner = ShellRunner()
    
    # Set up progress callback
    def progress_callback(progress):
        print(f"  {progress.command_id}: {progress.current_output}")
    
    runner.set_progress_callback(progress_callback)
    
    # Test synchronous command
    print("\n🔄 Testing synchronous command...")
    result = runner.run_command_sync("echo 'Hello, World!'", timeout=10)
    
    if result.status == CommandStatus.COMPLETED:
        print(f"✅ Command completed: {result.stdout.strip()}")
    else:
        print(f"❌ Command failed: {result.error_message}")
    
    # Test asynchronous command
    print("\n🔄 Testing asynchronous command...")
    command_id = runner.run_command("sleep 2 && echo 'Async command completed'", realtime_output=True)
    
    # Wait for completion
    result = runner.wait_for_command(command_id, timeout=10)
    if result and result.status == CommandStatus.COMPLETED:
        print(f"✅ Async command completed: {result.stdout.strip()}")
    else:
        print(f"❌ Async command failed: {result.error_message if result else 'Timeout'}")
    
    # Test command with environment variables
    print("\n🔄 Testing command with environment variables...")
    env_vars = {"TEST_VAR": "test_value"}
    result = runner.run_command_sync("echo $TEST_VAR", environment_vars=env_vars, timeout=10)
    
    if result.status == CommandStatus.COMPLETED:
        print(f"✅ Environment variable test: {result.stdout.strip()}")
    else:
        print(f"❌ Environment variable test failed: {result.error_message}")
    
    # Test command cancellation
    print("\n🔄 Testing command cancellation...")
    command_id = runner.run_command("sleep 10", realtime_output=True)
    
    # Cancel after 1 second
    time.sleep(1)
    if runner.cancel_command(command_id):
        print("✅ Command cancelled successfully")
    else:
        print("❌ Command cancellation failed")
    
    # Test cleanup
    print("\n🗑️  Testing cleanup...")
    runner.cleanup_old_results()
    print("✅ Cleanup complete")
    
    return True


if __name__ == "__main__":
    main()