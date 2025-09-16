#!/usr/bin/env python3
"""
PinokioCloud Repository Cloning System

This module handles cloning the PinokioCloud repository into the detected cloud
GPU service's file system. Provides intelligent cloning with progress tracking,
error handling, and platform-specific optimizations.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import subprocess
import shutil
import time
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class CloneStatus(Enum):
    """Enumeration of clone operation statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CloneProgress:
    """Clone operation progress information."""
    status: CloneStatus
    progress_percent: float
    current_operation: str
    bytes_received: int
    bytes_total: int
    objects_received: int
    objects_total: int
    start_time: float
    elapsed_time: float
    estimated_remaining: float
    error_message: Optional[str] = None


@dataclass
class CloneResult:
    """Result of repository cloning operation."""
    success: bool
    status: CloneStatus
    repository_path: str
    progress: CloneProgress
    cloned_files: List[str] = field(default_factory=list)
    cloned_directories: List[str] = field(default_factory=list)
    total_size_bytes: int = 0
    clone_duration: float = 0.0
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class RepositoryCloner:
    """
    Repository cloning system for multi-cloud environments.
    
    Handles cloning the PinokioCloud repository into the detected cloud
    GPU service's file system with intelligent progress tracking and
    platform-specific optimizations.
    """
    
    def __init__(self, target_platform: str, base_path: str):
        """
        Initialize the repository cloner.
        
        Args:
            target_platform: Target cloud platform
            base_path: Base path for cloning
        """
        self.target_platform = target_platform
        self.base_path = base_path
        self.repository_url = "https://github.com/pinokio-cloud/pinokio-cloud.git"
        self.repository_name = "pinokio-cloud"
        self.target_path = os.path.join(base_path, self.repository_name)
        self.progress_callback = None
        self.cancel_requested = False
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def clone_repository(self, force_clone: bool = False, 
                        shallow_clone: bool = True) -> CloneResult:
        """
        Clone the PinokioCloud repository.
        
        Args:
            force_clone: Force clone even if repository exists
            shallow_clone: Perform shallow clone (faster)
            
        Returns:
            CloneResult: Result of the cloning operation
        """
        start_time = time.time()
        
        # Initialize progress
        progress = CloneProgress(
            status=CloneStatus.PENDING,
            progress_percent=0.0,
            current_operation="Initializing clone operation",
            bytes_received=0,
            bytes_total=0,
            objects_received=0,
            objects_total=0,
            start_time=start_time,
            elapsed_time=0.0,
            estimated_remaining=0.0
        )
        
        try:
            # Check if repository already exists
            if os.path.exists(self.target_path) and not force_clone:
                progress.status = CloneStatus.COMPLETED
                progress.progress_percent = 100.0
                progress.current_operation = "Repository already exists"
                progress.elapsed_time = time.time() - start_time
                
                return CloneResult(
                    success=True,
                    status=CloneStatus.COMPLETED,
                    repository_path=self.target_path,
                    progress=progress,
                    cloned_files=self._get_existing_files(),
                    cloned_directories=self._get_existing_directories(),
                    total_size_bytes=self._calculate_directory_size(self.target_path),
                    clone_duration=progress.elapsed_time
                )
            
            # Remove existing repository if force clone
            if force_clone and os.path.exists(self.target_path):
                progress.current_operation = "Removing existing repository"
                self._update_progress(progress)
                shutil.rmtree(self.target_path)
            
            # Create target directory
            progress.current_operation = "Creating target directory"
            progress.progress_percent = 5.0
            self._update_progress(progress)
            
            os.makedirs(os.path.dirname(self.target_path), exist_ok=True)
            
            # Perform git clone
            progress.status = CloneStatus.IN_PROGRESS
            progress.current_operation = "Cloning repository"
            progress.progress_percent = 10.0
            self._update_progress(progress)
            
            clone_success = self._perform_git_clone(shallow_clone, progress)
            
            if not clone_success:
                progress.status = CloneStatus.FAILED
                progress.current_operation = "Clone failed"
                progress.elapsed_time = time.time() - start_time
                
                return CloneResult(
                    success=False,
                    status=CloneStatus.FAILED,
                    repository_path=self.target_path,
                    progress=progress,
                    clone_duration=progress.elapsed_time,
                    error_message=progress.error_message
                )
            
            # Verify clone
            progress.current_operation = "Verifying clone"
            progress.progress_percent = 90.0
            self._update_progress(progress)
            
            verification_success = self._verify_clone()
            
            if not verification_success:
                progress.status = CloneStatus.FAILED
                progress.current_operation = "Clone verification failed"
                progress.elapsed_time = time.time() - start_time
                
                return CloneResult(
                    success=False,
                    status=CloneStatus.FAILED,
                    repository_path=self.target_path,
                    progress=progress,
                    clone_duration=progress.elapsed_time,
                    error_message="Clone verification failed"
                )
            
            # Finalize
            progress.status = CloneStatus.COMPLETED
            progress.progress_percent = 100.0
            progress.current_operation = "Clone completed successfully"
            progress.elapsed_time = time.time() - start_time
            self._update_progress(progress)
            
            # Get clone statistics
            cloned_files = self._get_existing_files()
            cloned_directories = self._get_existing_directories()
            total_size = self._calculate_directory_size(self.target_path)
            
            return CloneResult(
                success=True,
                status=CloneStatus.COMPLETED,
                repository_path=self.target_path,
                progress=progress,
                cloned_files=cloned_files,
                cloned_directories=cloned_directories,
                total_size_bytes=total_size,
                clone_duration=progress.elapsed_time
            )
        
        except Exception as e:
            progress.status = CloneStatus.FAILED
            progress.current_operation = f"Clone failed: {str(e)}"
            progress.elapsed_time = time.time() - start_time
            progress.error_message = str(e)
            
            return CloneResult(
                success=False,
                status=CloneStatus.FAILED,
                repository_path=self.target_path,
                progress=progress,
                clone_duration=progress.elapsed_time,
                error_message=str(e)
            )
    
    def _perform_git_clone(self, shallow_clone: bool, progress: CloneProgress) -> bool:
        """Perform the actual git clone operation."""
        try:
            # Build git clone command
            cmd = ["git", "clone"]
            
            if shallow_clone:
                cmd.extend(["--depth", "1"])
            
            # Add platform-specific optimizations
            if self.target_platform == "google-colab":
                # Colab-specific optimizations
                cmd.extend(["--single-branch", "--branch", "main"])
            elif self.target_platform == "vast-ai":
                # Vast.ai-specific optimizations
                cmd.extend(["--single-branch", "--branch", "main"])
            elif self.target_platform == "lightning-ai":
                # Lightning.ai-specific optimizations
                cmd.extend(["--single-branch", "--branch", "main"])
            elif self.target_platform == "paperspace":
                # Paperspace-specific optimizations
                cmd.extend(["--single-branch", "--branch", "main"])
            elif self.target_platform == "runpod":
                # RunPod-specific optimizations
                cmd.extend(["--single-branch", "--branch", "main"])
            
            cmd.extend([self.repository_url, self.target_path])
            
            # Execute git clone with progress tracking
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Track progress
            progress.progress_percent = 20.0
            self._update_progress(progress)
            
            # Read output line by line
            for line in process.stdout:
                if self.cancel_requested:
                    process.terminate()
                    return False
                
                # Parse git output for progress information
                self._parse_git_output(line, progress)
                self._update_progress(progress)
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code != 0:
                progress.error_message = f"Git clone failed with return code {return_code}"
                return False
            
            progress.progress_percent = 80.0
            return True
        
        except Exception as e:
            progress.error_message = f"Git clone error: {str(e)}"
            return False
    
    def _parse_git_output(self, line: str, progress: CloneProgress):
        """Parse git output for progress information."""
        line = line.strip()
        
        # Parse different types of git output
        if "Receiving objects:" in line:
            # Parse object progress
            try:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "Receiving" and i + 1 < len(parts):
                        objects_info = parts[i + 1]
                        if "/" in objects_info:
                            received, total = objects_info.split("/")
                            progress.objects_received = int(received)
                            progress.objects_total = int(total)
                            
                            if progress.objects_total > 0:
                                progress.progress_percent = 20.0 + (progress.objects_received / progress.objects_total) * 60.0
            except:
                pass
        
        elif "Resolving deltas:" in line:
            # Parse delta progress
            try:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "Resolving" and i + 1 < len(parts):
                        delta_info = parts[i + 1]
                        if "/" in delta_info:
                            received, total = delta_info.split("/")
                            progress.progress_percent = 80.0 + (int(received) / int(total)) * 10.0
            except:
                pass
        
        elif "remote:" in line:
            # Parse remote information
            progress.current_operation = f"Remote: {line[7:]}"
        
        elif "Cloning into" in line:
            # Parse clone target
            progress.current_operation = f"Cloning into {line.split()[-1]}"
    
    def _verify_clone(self) -> bool:
        """Verify that the clone was successful."""
        try:
            # Check if target directory exists
            if not os.path.exists(self.target_path):
                return False
            
            # Check if it's a git repository
            git_dir = os.path.join(self.target_path, ".git")
            if not os.path.exists(git_dir):
                return False
            
            # Check for essential files
            essential_files = [
                "README.md",
                "requirements.txt",
                "setup.py",
                "pinokio_cloud"
            ]
            
            for file in essential_files:
                file_path = os.path.join(self.target_path, file)
                if not os.path.exists(file_path):
                    return False
            
            # Check git status
            try:
                result = subprocess.run(
                    ["git", "status"],
                    cwd=self.target_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.returncode == 0
            except:
                return False
        
        except:
            return False
    
    def _get_existing_files(self) -> List[str]:
        """Get list of existing files in the repository."""
        files = []
        
        try:
            for root, dirs, filenames in os.walk(self.target_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, self.target_path)
                    files.append(relative_path)
        except:
            pass
        
        return files
    
    def _get_existing_directories(self) -> List[str]:
        """Get list of existing directories in the repository."""
        directories = []
        
        try:
            for root, dirs, filenames in os.walk(self.target_path):
                for dirname in dirs:
                    dir_path = os.path.join(root, dirname)
                    relative_path = os.path.relpath(dir_path, self.target_path)
                    directories.append(relative_path)
        except:
            pass
        
        return directories
    
    def _calculate_directory_size(self, directory_path: str) -> int:
        """Calculate total size of directory in bytes."""
        total_size = 0
        
        try:
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        pass
        except:
            pass
        
        return total_size
    
    def _update_progress(self, progress: CloneProgress):
        """Update progress and call callback if set."""
        progress.elapsed_time = time.time() - progress.start_time
        
        # Estimate remaining time
        if progress.progress_percent > 0:
            estimated_total = progress.elapsed_time / (progress.progress_percent / 100.0)
            progress.estimated_remaining = max(0, estimated_total - progress.elapsed_time)
        
        # Call progress callback if set
        if self.progress_callback:
            try:
                self.progress_callback(progress)
            except:
                pass
    
    def cancel_clone(self):
        """Cancel the clone operation."""
        self.cancel_requested = True
    
    def get_repository_info(self) -> Dict[str, Any]:
        """Get information about the cloned repository."""
        info = {
            "repository_path": self.target_path,
            "exists": os.path.exists(self.target_path),
            "is_git_repo": False,
            "branch": "",
            "commit": "",
            "remote_url": "",
            "file_count": 0,
            "directory_count": 0,
            "total_size_bytes": 0
        }
        
        if not info["exists"]:
            return info
        
        try:
            # Check if it's a git repository
            git_dir = os.path.join(self.target_path, ".git")
            info["is_git_repo"] = os.path.exists(git_dir)
            
            if info["is_git_repo"]:
                # Get git information
                try:
                    result = subprocess.run(
                        ["git", "branch", "--show-current"],
                        cwd=self.target_path,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        info["branch"] = result.stdout.strip()
                except:
                    pass
                
                try:
                    result = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        cwd=self.target_path,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        info["commit"] = result.stdout.strip()
                except:
                    pass
                
                try:
                    result = subprocess.run(
                        ["git", "remote", "get-url", "origin"],
                        cwd=self.target_path,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        info["remote_url"] = result.stdout.strip()
                except:
                    pass
            
            # Get file and directory counts
            files = self._get_existing_files()
            directories = self._get_existing_directories()
            
            info["file_count"] = len(files)
            info["directory_count"] = len(directories)
            info["total_size_bytes"] = self._calculate_directory_size(self.target_path)
        
        except:
            pass
        
        return info
    
    def cleanup_repository(self) -> bool:
        """Clean up the cloned repository."""
        try:
            if os.path.exists(self.target_path):
                shutil.rmtree(self.target_path)
                return True
            return True
        except:
            return False
    
    def get_clone_summary(self, result: CloneResult) -> str:
        """Get a human-readable summary of the clone operation."""
        summary = f"Repository Clone Summary:\n"
        summary += f"Status: {result.status.value}\n"
        summary += f"Success: {result.success}\n"
        summary += f"Repository Path: {result.repository_path}\n"
        summary += f"Duration: {result.clone_duration:.2f} seconds\n"
        
        if result.success:
            summary += f"Files Cloned: {len(result.cloned_files)}\n"
            summary += f"Directories Cloned: {len(result.cloned_directories)}\n"
            summary += f"Total Size: {result.total_size_bytes / (1024*1024):.2f} MB\n"
        else:
            summary += f"Error: {result.error_message}\n"
        
        if result.warnings:
            summary += f"Warnings: {len(result.warnings)}\n"
            for warning in result.warnings:
                summary += f"  - {warning}\n"
        
        return summary


def main():
    """Main function for testing repository cloning."""
    # Test with different platforms
    test_platforms = ["google-colab", "vast-ai", "lightning-ai"]
    
    for platform in test_platforms:
        print(f"\nTesting {platform}:")
        
        # Create test base path
        test_base = f"/tmp/test_{platform}"
        os.makedirs(test_base, exist_ok=True)
        
        # Initialize cloner
        cloner = RepositoryCloner(platform, test_base)
        
        # Set up progress callback
        def progress_callback(progress):
            print(f"  Progress: {progress.progress_percent:.1f}% - {progress.current_operation}")
        
        cloner.set_progress_callback(progress_callback)
        
        # Perform clone
        result = cloner.clone_repository(force_clone=True, shallow_clone=True)
        
        # Print summary
        print(cloner.get_clone_summary(result))
        
        # Get repository info
        info = cloner.get_repository_info()
        print(f"  Repository Info: {info}")
        
        # Cleanup
        cloner.cleanup_repository()
        shutil.rmtree(test_base, ignore_errors=True)
    
    return True


if __name__ == "__main__":
    main()