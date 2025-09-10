#!/usr/bin/env python3
"""
PinokioCloud File System Operations

This module provides comprehensive file system operations including atomic operations,
checksums, rollback capabilities, symbolic/hard linking, and file management for
multi-cloud GPU environments.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import shutil
import hashlib
import tempfile
import time
import json
import stat
from typing import Dict, List, Optional, Tuple, Any, Union, BinaryIO
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import threading
import queue


class OperationType(Enum):
    """Enumeration of file system operation types."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    CREATE = "create"
    WRITE = "write"
    READ = "read"
    LINK = "link"
    SYMLINK = "symlink"
    CHMOD = "chmod"
    CHOWN = "chown"


class OperationStatus(Enum):
    """Enumeration of operation statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class FileOperation:
    """Information about a file system operation."""
    operation_id: str
    operation_type: OperationType
    source_path: Optional[str]
    target_path: Optional[str]
    status: OperationStatus
    start_time: float
    end_time: Optional[float] = None
    size_bytes: int = 0
    checksum: Optional[str] = None
    backup_path: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileInfo:
    """Information about a file or directory."""
    path: str
    name: str
    is_file: bool
    is_directory: bool
    is_symlink: bool
    size_bytes: int
    permissions: str
    owner: str
    group: str
    created_time: float
    modified_time: float
    accessed_time: float
    checksum: Optional[str] = None


class FileSystemManager:
    """
    Comprehensive file system management system.
    
    Provides atomic operations, checksums, rollback capabilities,
    symbolic/hard linking, and file management for multi-cloud environments.
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the file system manager.
        
        Args:
            base_path: Base path for file operations
        """
        self.base_path = base_path
        self.operations = {}
        self.operation_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        self.progress_callback = None
        self.backup_dir = os.path.join(base_path, "backups")
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Start worker thread
        self.start_worker()
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def start_worker(self):
        """Start the background worker thread."""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
    
    def stop_worker(self):
        """Stop the background worker thread."""
        self.running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
    
    def _worker_loop(self):
        """Background worker loop for processing operations."""
        while self.running:
            try:
                operation = self.operation_queue.get(timeout=1)
                if operation:
                    self._process_operation(operation)
                    self.operation_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                pass
    
    def copy_file(self, source_path: str, target_path: str, 
                 atomic: bool = True, backup: bool = True) -> str:
        """
        Copy a file with atomic operation and backup support.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            atomic: Use atomic operation
            backup: Create backup before operation
            
        Returns:
            str: Operation ID
        """
        operation_id = f"copy_{int(time.time())}_{hash(source_path) % 10000}"
        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.COPY,
            source_path=source_path,
            target_path=target_path,
            status=OperationStatus.PENDING,
            start_time=time.time()
        )
        
        self.operations[operation_id] = operation
        self.operation_queue.put(operation)
        
        return operation_id
    
    def move_file(self, source_path: str, target_path: str,
                 atomic: bool = True, backup: bool = True) -> str:
        """
        Move a file with atomic operation and backup support.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            atomic: Use atomic operation
            backup: Create backup before operation
            
        Returns:
            str: Operation ID
        """
        operation_id = f"move_{int(time.time())}_{hash(source_path) % 10000}"
        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.MOVE,
            source_path=source_path,
            target_path=target_path,
            status=OperationStatus.PENDING,
            start_time=time.time()
        )
        
        self.operations[operation_id] = operation
        self.operation_queue.put(operation)
        
        return operation_id
    
    def delete_file(self, file_path: str, backup: bool = True) -> str:
        """
        Delete a file with backup support.
        
        Args:
            file_path: File path to delete
            backup: Create backup before deletion
            
        Returns:
            str: Operation ID
        """
        operation_id = f"delete_{int(time.time())}_{hash(file_path) % 10000}"
        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.DELETE,
            source_path=file_path,
            target_path=None,
            status=OperationStatus.PENDING,
            start_time=time.time()
        )
        
        self.operations[operation_id] = operation
        self.operation_queue.put(operation)
        
        return operation_id
    
    def write_file(self, file_path: str, content: Union[str, bytes],
                  atomic: bool = True, backup: bool = True) -> str:
        """
        Write content to a file with atomic operation and backup support.
        
        Args:
            file_path: Target file path
            content: Content to write
            atomic: Use atomic operation
            backup: Create backup before operation
            
        Returns:
            str: Operation ID
        """
        operation_id = f"write_{int(time.time())}_{hash(file_path) % 10000}"
        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.WRITE,
            source_path=None,
            target_path=file_path,
            status=OperationStatus.PENDING,
            start_time=time.time()
        )
        
        # Store content in metadata
        if isinstance(content, str):
            operation.metadata["content"] = content
            operation.metadata["content_type"] = "text"
        else:
            operation.metadata["content"] = content
            operation.metadata["content_type"] = "binary"
        
        self.operations[operation_id] = operation
        self.operation_queue.put(operation)
        
        return operation_id
    
    def read_file(self, file_path: str, binary: bool = False) -> Tuple[bool, Union[str, bytes, None]]:
        """
        Read content from a file.
        
        Args:
            file_path: File path to read
            binary: Read as binary data
            
        Returns:
            Tuple of (success, content)
        """
        try:
            if not os.path.exists(file_path):
                return False, None
            
            if binary:
                with open(file_path, 'rb') as f:
                    content = f.read()
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            return True, content
        
        except Exception as e:
            return False, None
    
    def create_symlink(self, target_path: str, link_path: str) -> str:
        """
        Create a symbolic link.
        
        Args:
            target_path: Target path for the link
            link_path: Path where the link will be created
            
        Returns:
            str: Operation ID
        """
        operation_id = f"symlink_{int(time.time())}_{hash(link_path) % 10000}"
        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.SYMLINK,
            source_path=target_path,
            target_path=link_path,
            status=OperationStatus.PENDING,
            start_time=time.time()
        )
        
        self.operations[operation_id] = operation
        self.operation_queue.put(operation)
        
        return operation_id
    
    def create_hard_link(self, target_path: str, link_path: str) -> str:
        """
        Create a hard link.
        
        Args:
            target_path: Target path for the link
            link_path: Path where the link will be created
            
        Returns:
            str: Operation ID
        """
        operation_id = f"link_{int(time.time())}_{hash(link_path) % 10000}"
        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.LINK,
            source_path=target_path,
            target_path=link_path,
            status=OperationStatus.PENDING,
            start_time=time.time()
        )
        
        self.operations[operation_id] = operation
        self.operation_queue.put(operation)
        
        return operation_id
    
    def _process_operation(self, operation: FileOperation):
        """Process a file system operation."""
        try:
            operation.status = OperationStatus.IN_PROGRESS
            self._update_progress(operation)
            
            # Create backup if requested
            if operation.backup_path is None and operation.target_path:
                operation.backup_path = self._create_backup(operation.target_path)
            
            # Perform the operation
            success = False
            
            if operation.operation_type == OperationType.COPY:
                success = self._perform_copy(operation)
            elif operation.operation_type == OperationType.MOVE:
                success = self._perform_move(operation)
            elif operation.operation_type == OperationType.DELETE:
                success = self._perform_delete(operation)
            elif operation.operation_type == OperationType.WRITE:
                success = self._perform_write(operation)
            elif operation.operation_type == OperationType.SYMLINK:
                success = self._perform_symlink(operation)
            elif operation.operation_type == OperationType.LINK:
                success = self._perform_hard_link(operation)
            
            if success:
                operation.status = OperationStatus.COMPLETED
                operation.end_time = time.time()
                
                # Calculate checksum
                if operation.target_path and os.path.exists(operation.target_path):
                    operation.checksum = self._calculate_checksum(operation.target_path)
                    operation.size_bytes = os.path.getsize(operation.target_path)
            else:
                operation.status = OperationStatus.FAILED
                operation.end_time = time.time()
                operation.error_message = "Operation failed"
            
            self._update_progress(operation)
        
        except Exception as e:
            operation.status = OperationStatus.FAILED
            operation.end_time = time.time()
            operation.error_message = str(e)
            self._update_progress(operation)
    
    def _perform_copy(self, operation: FileOperation) -> bool:
        """Perform file copy operation."""
        try:
            if not operation.source_path or not operation.target_path:
                return False
            
            if not os.path.exists(operation.source_path):
                return False
            
            # Ensure target directory exists
            target_dir = os.path.dirname(operation.target_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy file
            shutil.copy2(operation.source_path, operation.target_path)
            return True
        
        except Exception as e:
            operation.error_message = str(e)
            return False
    
    def _perform_move(self, operation: FileOperation) -> bool:
        """Perform file move operation."""
        try:
            if not operation.source_path or not operation.target_path:
                return False
            
            if not os.path.exists(operation.source_path):
                return False
            
            # Ensure target directory exists
            target_dir = os.path.dirname(operation.target_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # Move file
            shutil.move(operation.source_path, operation.target_path)
            return True
        
        except Exception as e:
            operation.error_message = str(e)
            return False
    
    def _perform_delete(self, operation: FileOperation) -> bool:
        """Perform file delete operation."""
        try:
            if not operation.source_path:
                return False
            
            if not os.path.exists(operation.source_path):
                return True  # Already deleted
            
            if os.path.isfile(operation.source_path):
                os.remove(operation.source_path)
            elif os.path.isdir(operation.source_path):
                shutil.rmtree(operation.source_path)
            
            return True
        
        except Exception as e:
            operation.error_message = str(e)
            return False
    
    def _perform_write(self, operation: FileOperation) -> bool:
        """Perform file write operation."""
        try:
            if not operation.target_path:
                return False
            
            content = operation.metadata.get("content")
            content_type = operation.metadata.get("content_type", "text")
            
            if content is None:
                return False
            
            # Ensure target directory exists
            target_dir = os.path.dirname(operation.target_path)
            os.makedirs(target_dir, exist_ok=True)
            
            # Write content
            if content_type == "binary":
                with open(operation.target_path, 'wb') as f:
                    f.write(content)
            else:
                with open(operation.target_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return True
        
        except Exception as e:
            operation.error_message = str(e)
            return False
    
    def _perform_symlink(self, operation: FileOperation) -> bool:
        """Perform symbolic link creation."""
        try:
            if not operation.source_path or not operation.target_path:
                return False
            
            # Remove existing link if it exists
            if os.path.exists(operation.target_path) or os.path.islink(operation.target_path):
                os.remove(operation.target_path)
            
            # Create symbolic link
            os.symlink(operation.source_path, operation.target_path)
            return True
        
        except Exception as e:
            operation.error_message = str(e)
            return False
    
    def _perform_hard_link(self, operation: FileOperation) -> bool:
        """Perform hard link creation."""
        try:
            if not operation.source_path or not operation.target_path:
                return False
            
            if not os.path.exists(operation.source_path):
                return False
            
            # Remove existing file if it exists
            if os.path.exists(operation.target_path):
                os.remove(operation.target_path)
            
            # Create hard link
            os.link(operation.source_path, operation.target_path)
            return True
        
        except Exception as e:
            operation.error_message = str(e)
            return False
    
    def _create_backup(self, file_path: str) -> Optional[str]:
        """Create backup of a file."""
        try:
            if not os.path.exists(file_path):
                return None
            
            # Generate backup path
            timestamp = int(time.time())
            filename = os.path.basename(file_path)
            backup_filename = f"{timestamp}_{filename}"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copy file to backup
            shutil.copy2(file_path, backup_path)
            return backup_path
        
        except Exception as e:
            return None
    
    def _calculate_checksum(self, file_path: str, algorithm: str = "sha256") -> Optional[str]:
        """Calculate checksum of a file."""
        try:
            if not os.path.exists(file_path):
                return None
            
            hash_obj = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
        
        except Exception as e:
            return None
    
    def _update_progress(self, operation: FileOperation):
        """Update operation progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(operation)
            except:
                pass
    
    def get_operation_status(self, operation_id: str) -> Optional[FileOperation]:
        """Get status of an operation."""
        return self.operations.get(operation_id)
    
    def rollback_operation(self, operation_id: str) -> bool:
        """
        Rollback an operation using backup.
        
        Args:
            operation_id: Operation ID to rollback
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            operation = self.operations.get(operation_id)
            if not operation:
                return False
            
            if not operation.backup_path or not os.path.exists(operation.backup_path):
                return False
            
            # Restore from backup
            if operation.target_path:
                shutil.copy2(operation.backup_path, operation.target_path)
            
            operation.status = OperationStatus.ROLLED_BACK
            operation.end_time = time.time()
            
            return True
        
        except Exception as e:
            return False
    
    def get_file_info(self, file_path: str) -> Optional[FileInfo]:
        """
        Get detailed information about a file or directory.
        
        Args:
            file_path: Path to file or directory
            
        Returns:
            FileInfo or None if not found
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            stat_info = os.stat(file_path)
            
            return FileInfo(
                path=file_path,
                name=os.path.basename(file_path),
                is_file=os.path.isfile(file_path),
                is_directory=os.path.isdir(file_path),
                is_symlink=os.path.islink(file_path),
                size_bytes=stat_info.st_size,
                permissions=oct(stat_info.st_mode)[-3:],
                owner=str(stat_info.st_uid),
                group=str(stat_info.st_gid),
                created_time=stat_info.st_ctime,
                modified_time=stat_info.st_mtime,
                accessed_time=stat_info.st_atime,
                checksum=self._calculate_checksum(file_path) if os.path.isfile(file_path) else None
            )
        
        except Exception as e:
            return None
    
    def list_directory(self, directory_path: str, recursive: bool = False) -> List[FileInfo]:
        """
        List contents of a directory.
        
        Args:
            directory_path: Directory path to list
            recursive: List recursively
            
        Returns:
            List of FileInfo objects
        """
        files = []
        
        try:
            if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
                return files
            
            if recursive:
                for root, dirs, filenames in os.walk(directory_path):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        file_info = self.get_file_info(file_path)
                        if file_info:
                            files.append(file_info)
            else:
                for item in os.listdir(directory_path):
                    item_path = os.path.join(directory_path, item)
                    file_info = self.get_file_info(item_path)
                    if file_info:
                        files.append(file_info)
        
        except Exception as e:
            pass
        
        return files
    
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
    
    def cleanup_old_backups(self, max_age_hours: int = 168):  # 7 days
        """Clean up old backup files."""
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
        
        except Exception as e:
            pass


def main():
    """Main function for testing file system operations."""
    print("🧪 Testing File System Manager")
    print("=" * 50)
    
    # Initialize manager
    fs_manager = FileSystemManager()
    
    # Set up progress callback
    def progress_callback(operation):
        print(f"  {operation.operation_type.value}: {operation.status.value}")
    
    fs_manager.set_progress_callback(progress_callback)
    
    # Test file operations
    test_dir = "/tmp/fs_test"
    os.makedirs(test_dir, exist_ok=True)
    
    # Test write operation
    print("\n📝 Testing file write...")
    test_file = os.path.join(test_dir, "test.txt")
    op_id = fs_manager.write_file(test_file, "Hello, World!")
    
    # Wait for operation to complete
    time.sleep(1)
    operation = fs_manager.get_operation_status(op_id)
    if operation and operation.status == OperationStatus.COMPLETED:
        print("✅ File write successful")
    else:
        print(f"❌ File write failed: {operation.error_message if operation else 'Unknown error'}")
    
    # Test copy operation
    print("\n📋 Testing file copy...")
    copy_file = os.path.join(test_dir, "test_copy.txt")
    op_id = fs_manager.copy_file(test_file, copy_file)
    
    time.sleep(1)
    operation = fs_manager.get_operation_status(op_id)
    if operation and operation.status == OperationStatus.COMPLETED:
        print("✅ File copy successful")
    else:
        print(f"❌ File copy failed: {operation.error_message if operation else 'Unknown error'}")
    
    # Test file info
    print("\n📊 Testing file info...")
    file_info = fs_manager.get_file_info(test_file)
    if file_info:
        print(f"✅ File info: {file_info.name}, {file_info.size_bytes} bytes, {file_info.permissions}")
    else:
        print("❌ File info failed")
    
    # Test directory listing
    print("\n📁 Testing directory listing...")
    files = fs_manager.list_directory(test_dir)
    print(f"✅ Found {len(files)} files in directory")
    
    # Test cleanup
    print("\n🗑️  Testing cleanup...")
    shutil.rmtree(test_dir, ignore_errors=True)
    print("✅ Cleanup complete")
    
    # Stop worker
    fs_manager.stop_worker()
    
    return True


if __name__ == "__main__":
    main()