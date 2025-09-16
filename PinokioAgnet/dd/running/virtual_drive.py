#!/usr/bin/env python3
"""
PinokioCloud Virtual Drive Manager

This module creates virtual storage that applications can share. It provides
intelligent file sharing, deduplication, symbolic linking, and storage optimization
for Pinokio applications in cloud environments.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import shutil
import hashlib
import threading
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime
import sqlite3
import json

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from environment_management.file_system import FileSystemManager
from environment_management.json_handler import JSONHandler
from cloud_detection.cloud_detector import CloudDetector
from cloud_detection.platform_configs import PlatformConfigurationuration


class DriveType(Enum):
    """Types of virtual drives."""
    SHARED_MODELS = "shared_models"
    SHARED_CACHE = "shared_cache"
    SHARED_DATASETS = "shared_datasets"
    SHARED_OUTPUTS = "shared_outputs"
    APP_SPECIFIC = "app_specific"
    TEMPORARY = "temporary"


class StorageMode(Enum):
    """Storage modes for virtual drives."""
    COPY = "copy"           # Full copy of files
    SYMLINK = "symlink"     # Symbolic links
    HARDLINK = "hardlink"   # Hard links
    DEDUPLICATED = "deduplicated"  # Deduplicated storage


@dataclass
class VirtualDrive:
    """Information about a virtual drive."""
    drive_id: str
    name: str
    drive_type: DriveType
    storage_mode: StorageMode
    base_path: Path
    size_limit_gb: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    total_size_bytes: int = 0
    file_count: int = 0
    mounted_apps: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert VirtualDrive to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_accessed'] = self.last_accessed.isoformat()
        data['drive_type'] = self.drive_type.value
        data['storage_mode'] = self.storage_mode.value
        data['base_path'] = str(self.base_path)
        data['mounted_apps'] = list(self.mounted_apps)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VirtualDrive':
        """Create VirtualDrive from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        data['drive_type'] = DriveType(data['drive_type'])
        data['storage_mode'] = StorageMode(data['storage_mode'])
        data['base_path'] = Path(data['base_path'])
        data['mounted_apps'] = set(data['mounted_apps'])
        return cls(**data)


@dataclass
class FileEntry:
    """Information about a file in the virtual drive system."""
    file_hash: str
    original_path: str
    storage_path: str
    size_bytes: int
    created_at: datetime
    last_accessed: datetime
    reference_count: int = 1
    apps_using: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert FileEntry to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_accessed'] = self.last_accessed.isoformat()
        data['apps_using'] = list(self.apps_using)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileEntry':
        """Create FileEntry from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        data['apps_using'] = set(data['apps_using'])
        return cls(**data)


class VirtualDriveManager:
    """
    Creates virtual storage that applications can share.
    
    This class provides comprehensive virtual drive management with file sharing,
    deduplication, symbolic linking, and intelligent storage optimization.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the virtual drive manager."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.virtual_drives_path = self.base_path / "virtual_drives"
        self.virtual_drives_path.mkdir(exist_ok=True)
        
        # Storage for deduplicated files
        self.dedup_storage_path = self.virtual_drives_path / "dedup_storage"
        self.dedup_storage_path.mkdir(exist_ok=True)
        
        # Database for file tracking
        self.db_path = self.virtual_drives_path / "virtual_drives.db"
        
        # Drive management
        self.active_drives: Dict[str, VirtualDrive] = {}
        self.drive_lock = threading.RLock()
        
        # Initialize dependencies
        self.file_system = FileSystemManager(str(self.base_path))
        self.json_handler = JSONHandler(str(self.base_path))
        self.cloud_detector = CloudDetector()
        
        # Cloud platform information
        self.platform_info = self.cloud_detector.detect_platform()
        self.platform_config = PlatformConfiguration.get_config(self.platform_info.platform)
        
        # Initialize database
        self._init_database()
        
        # Load existing drives
        self._load_existing_drives()
        
        # Create default shared drives
        self._create_default_drives()
        
        print(f"[VirtualDriveManager] Initialized with storage at: {self.virtual_drives_path}")
        print(f"[VirtualDriveManager] Platform: {self.platform_info.platform}")
        print(f"[VirtualDriveManager] Active drives: {len(self.active_drives)}")
    
    def create_virtual_drive(self, drive_name: str, drive_type: DriveType,
                           size_gb: Optional[float] = None,
                           storage_mode: StorageMode = StorageMode.SYMLINK) -> VirtualDrive:
        """
        Create a new virtual drive.
        
        Args:
            drive_name: Name of the drive
            drive_type: Type of the drive
            size_gb: Optional size limit in GB
            storage_mode: Storage mode for the drive
        
        Returns:
            VirtualDrive: Created virtual drive information
        """
        print(f"[VirtualDriveManager] Creating virtual drive: {drive_name}")
        
        with self.drive_lock:
            # Generate unique drive ID
            drive_id = f"{drive_type.value}_{drive_name}_{int(datetime.now().timestamp())}"
            
            # Create drive directory
            drive_path = self.virtual_drives_path / drive_id
            drive_path.mkdir(exist_ok=True)
            
            # Create virtual drive object
            virtual_drive = VirtualDrive(
                drive_id=drive_id,
                name=drive_name,
                drive_type=drive_type,
                storage_mode=storage_mode,
                base_path=drive_path,
                size_limit_gb=size_gb
            )
            
            # Register drive
            self.active_drives[drive_id] = virtual_drive
            
            # Save drive configuration
            self._save_drive_config(virtual_drive)
            
            # Initialize drive in database
            self._init_drive_in_db(virtual_drive)
            
            print(f"[VirtualDriveManager] Created virtual drive {drive_id} at {drive_path}")
            return virtual_drive
    
    def mount_drive_for_app(self, app_name: str, drive_id: str, 
                          mount_path: Optional[str] = None) -> str:
        """
        Mount a virtual drive for an application.
        
        Args:
            app_name: Name of the application
            drive_id: ID of the drive to mount
            mount_path: Optional custom mount path
        
        Returns:
            str: Path where the drive is mounted for the app
        """
        print(f"[VirtualDriveManager] Mounting drive {drive_id} for app {app_name}")
        
        with self.drive_lock:
            if drive_id not in self.active_drives:
                raise ValueError(f"Virtual drive {drive_id} not found")
            
            virtual_drive = self.active_drives[drive_id]
            
            # Determine mount path
            if mount_path:
                app_mount_path = Path(mount_path)
            else:
                # Default mount path within app directory
                app_mount_path = self.base_path / "apps" / app_name / "virtual_drives" / virtual_drive.name
            
            app_mount_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create mount based on storage mode
            if virtual_drive.storage_mode == StorageMode.SYMLINK:
                # Create symbolic link
                if app_mount_path.exists():
                    app_mount_path.unlink()
                app_mount_path.symlink_to(virtual_drive.base_path)
            
            elif virtual_drive.storage_mode == StorageMode.COPY:
                # Copy entire drive contents
                if app_mount_path.exists():
                    shutil.rmtree(app_mount_path)
                shutil.copytree(virtual_drive.base_path, app_mount_path)
            
            elif virtual_drive.storage_mode == StorageMode.HARDLINK:
                # Create hard links for all files
                self._create_hardlink_mount(virtual_drive.base_path, app_mount_path)
            
            elif virtual_drive.storage_mode == StorageMode.DEDUPLICATED:
                # Create deduplicated mount
                self._create_dedup_mount(virtual_drive, app_mount_path, app_name)
            
            # Update drive information
            virtual_drive.mounted_apps.add(app_name)
            virtual_drive.last_accessed = datetime.now()
            
            # Save updated configuration
            self._save_drive_config(virtual_drive)
            
            print(f"[VirtualDriveManager] Mounted drive {drive_id} for {app_name} at {app_mount_path}")
            return str(app_mount_path)
    
    def unmount_drive_for_app(self, app_name: str, drive_id: str) -> bool:
        """
        Unmount a virtual drive for an application.
        
        Args:
            app_name: Name of the application
            drive_id: ID of the drive to unmount
        
        Returns:
            bool: True if successfully unmounted
        """
        print(f"[VirtualDriveManager] Unmounting drive {drive_id} for app {app_name}")
        
        with self.drive_lock:
            if drive_id not in self.active_drives:
                return False
            
            virtual_drive = self.active_drives[drive_id]
            
            # Find and remove mount point
            app_mount_path = self.base_path / "apps" / app_name / "virtual_drives" / virtual_drive.name
            
            try:
                if app_mount_path.exists():
                    if app_mount_path.is_symlink():
                        app_mount_path.unlink()
                    elif app_mount_path.is_dir():
                        shutil.rmtree(app_mount_path)
                    else:
                        app_mount_path.unlink()
                
                # Update drive information
                virtual_drive.mounted_apps.discard(app_name)
                
                # Save updated configuration
                self._save_drive_config(virtual_drive)
                
                print(f"[VirtualDriveManager] Unmounted drive {drive_id} for {app_name}")
                return True
                
            except Exception as e:
                print(f"[VirtualDriveManager] Error unmounting drive {drive_id} for {app_name}: {e}")
                return False
    
    def share_models_between_apps(self, source_app: str, target_app: str,
                                model_patterns: Optional[List[str]] = None) -> bool:
        """
        Share models between applications using virtual drives.
        
        Args:
            source_app: Source application name
            target_app: Target application name
            model_patterns: Optional patterns for model files to share
        
        Returns:
            bool: True if successfully shared
        """
        print(f"[VirtualDriveManager] Sharing models from {source_app} to {target_app}")
        
        try:
            # Find or create shared models drive
            models_drive = self._get_or_create_shared_models_drive()
            
            # Default model patterns
            if model_patterns is None:
                model_patterns = [
                    "*.safetensors", "*.ckpt", "*.pt", "*.pth", "*.bin",
                    "*.onnx", "*.trt", "*.engine", "*.pkl", "*.h5"
                ]
            
            # Find model files in source app
            source_app_path = self.base_path / "apps" / source_app
            model_files = []
            
            for pattern in model_patterns:
                model_files.extend(source_app_path.rglob(pattern))
            
            if not model_files:
                print(f"[VirtualDriveManager] No model files found in {source_app}")
                return False
            
            # Add model files to shared drive
            for model_file in model_files:
                self._add_file_to_drive(models_drive, model_file, source_app)
            
            # Mount shared drive for target app
            self.mount_drive_for_app(target_app, models_drive.drive_id)
            
            print(f"[VirtualDriveManager] Shared {len(model_files)} model files from {source_app} to {target_app}")
            return True
            
        except Exception as e:
            print(f"[VirtualDriveManager] Error sharing models: {e}")
            return False
    
    def add_file_to_shared_drive(self, drive_id: str, file_path: str, 
                               app_name: str) -> bool:
        """
        Add a file to a shared virtual drive.
        
        Args:
            drive_id: ID of the virtual drive
            file_path: Path to the file to add
            app_name: Name of the app adding the file
        
        Returns:
            bool: True if successfully added
        """
        if drive_id not in self.active_drives:
            return False
        
        virtual_drive = self.active_drives[drive_id]
        source_path = Path(file_path)
        
        if not source_path.exists():
            return False
        
        return self._add_file_to_drive(virtual_drive, source_path, app_name)
    
    def cleanup_unused_drives(self) -> List[str]:
        """
        Clean up unused virtual drives.
        
        Returns:
            List[str]: List of drive IDs that were cleaned up
        """
        print("[VirtualDriveManager] Cleaning up unused drives")
        
        cleaned_drives = []
        
        with self.drive_lock:
            for drive_id, virtual_drive in list(self.active_drives.items()):
                # Check if drive has any mounted apps
                if not virtual_drive.mounted_apps:
                    # Check last access time
                    time_since_access = datetime.now() - virtual_drive.last_accessed
                    
                    # Clean up drives not accessed for 24 hours
                    if time_since_access.total_seconds() > 86400:  # 24 hours
                        try:
                            # Remove drive directory
                            if virtual_drive.base_path.exists():
                                shutil.rmtree(virtual_drive.base_path)
                            
                            # Remove from active drives
                            del self.active_drives[drive_id]
                            
                            # Remove from database
                            self._remove_drive_from_db(drive_id)
                            
                            # Remove configuration
                            self._remove_drive_config(drive_id)
                            
                            cleaned_drives.append(drive_id)
                            print(f"[VirtualDriveManager] Cleaned up unused drive: {drive_id}")
                            
                        except Exception as e:
                            print(f"[VirtualDriveManager] Error cleaning up drive {drive_id}: {e}")
        
        return cleaned_drives
    
    def get_drive_info(self, drive_id: str) -> Optional[VirtualDrive]:
        """
        Get information about a virtual drive.
        
        Args:
            drive_id: ID of the virtual drive
        
        Returns:
            Optional[VirtualDrive]: Drive information if exists
        """
        return self.active_drives.get(drive_id)
    
    def list_virtual_drives(self) -> List[VirtualDrive]:
        """
        Get list of all virtual drives.
        
        Returns:
            List[VirtualDrive]: List of all virtual drives
        """
        with self.drive_lock:
            return list(self.active_drives.values())
    
    def get_drive_usage_stats(self, drive_id: str) -> Dict[str, Any]:
        """
        Get usage statistics for a virtual drive.
        
        Args:
            drive_id: ID of the virtual drive
        
        Returns:
            Dict[str, Any]: Usage statistics
        """
        if drive_id not in self.active_drives:
            return {}
        
        virtual_drive = self.active_drives[drive_id]
        
        # Calculate actual disk usage
        total_size = 0
        file_count = 0
        
        if virtual_drive.base_path.exists():
            for file_path in virtual_drive.base_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
        
        # Update drive information
        virtual_drive.total_size_bytes = total_size
        virtual_drive.file_count = file_count
        
        stats = {
            'drive_id': drive_id,
            'name': virtual_drive.name,
            'type': virtual_drive.drive_type.value,
            'storage_mode': virtual_drive.storage_mode.value,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'total_size_gb': total_size / (1024 * 1024 * 1024),
            'file_count': file_count,
            'mounted_apps': list(virtual_drive.mounted_apps),
            'created_at': virtual_drive.created_at.isoformat(),
            'last_accessed': virtual_drive.last_accessed.isoformat(),
            'size_limit_gb': virtual_drive.size_limit_gb
        }
        
        # Add utilization if size limit is set
        if virtual_drive.size_limit_gb:
            utilization = (total_size / (1024 * 1024 * 1024)) / virtual_drive.size_limit_gb
            stats['utilization_percent'] = min(utilization * 100, 100.0)
        
        return stats
    
    def _create_default_drives(self) -> None:
        """Create default shared drives."""
        default_drives = [
            ("shared_models", DriveType.SHARED_MODELS, StorageMode.DEDUPLICATED),
            ("shared_cache", DriveType.SHARED_CACHE, StorageMode.SYMLINK),
            ("shared_datasets", DriveType.SHARED_DATASETS, StorageMode.SYMLINK),
            ("shared_outputs", DriveType.SHARED_OUTPUTS, StorageMode.COPY)
        ]
        
        for drive_name, drive_type, storage_mode in default_drives:
            # Check if drive already exists
            existing_drive = None
            for drive in self.active_drives.values():
                if drive.name == drive_name and drive.drive_type == drive_type:
                    existing_drive = drive
                    break
            
            if not existing_drive:
                # Determine size limits based on cloud platform
                size_limit = self._get_default_size_limit(drive_type)
                
                self.create_virtual_drive(
                    drive_name=drive_name,
                    drive_type=drive_type,
                    size_gb=size_limit,
                    storage_mode=storage_mode
                )
    
    def _get_default_size_limit(self, drive_type: DriveType) -> Optional[float]:
        """Get default size limit for drive type based on cloud platform."""
        # Adjust based on cloud platform storage limits
        if self.platform_info.platform == "google_colab":
            limits = {
                DriveType.SHARED_MODELS: 15.0,  # GB
                DriveType.SHARED_CACHE: 5.0,
                DriveType.SHARED_DATASETS: 10.0,
                DriveType.SHARED_OUTPUTS: 5.0
            }
        elif self.platform_info.platform in ["vast_ai", "runpod"]:
            limits = {
                DriveType.SHARED_MODELS: 50.0,
                DriveType.SHARED_CACHE: 20.0,
                DriveType.SHARED_DATASETS: 30.0,
                DriveType.SHARED_OUTPUTS: 20.0
            }
        else:
            # Default limits
            limits = {
                DriveType.SHARED_MODELS: 25.0,
                DriveType.SHARED_CACHE: 10.0,
                DriveType.SHARED_DATASETS: 20.0,
                DriveType.SHARED_OUTPUTS: 10.0
            }
        
        return limits.get(drive_type)
    
    def _get_or_create_shared_models_drive(self) -> VirtualDrive:
        """Get or create the shared models drive."""
        # Look for existing shared models drive
        for drive in self.active_drives.values():
            if (drive.drive_type == DriveType.SHARED_MODELS and 
                drive.name == "shared_models"):
                return drive
        
        # Create new shared models drive
        return self.create_virtual_drive(
            drive_name="shared_models",
            drive_type=DriveType.SHARED_MODELS,
            size_gb=self._get_default_size_limit(DriveType.SHARED_MODELS),
            storage_mode=StorageMode.DEDUPLICATED
        )
    
    def _add_file_to_drive(self, virtual_drive: VirtualDrive, 
                          source_path: Path, app_name: str) -> bool:
        """Add a file to a virtual drive."""
        try:
            if virtual_drive.storage_mode == StorageMode.DEDUPLICATED:
                return self._add_file_deduplicated(virtual_drive, source_path, app_name)
            else:
                # Simple copy to drive
                relative_path = source_path.name
                target_path = virtual_drive.base_path / relative_path
                
                # Avoid overwriting existing files
                counter = 1
                while target_path.exists():
                    stem = source_path.stem
                    suffix = source_path.suffix
                    target_path = virtual_drive.base_path / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                shutil.copy2(source_path, target_path)
                
                # Update drive stats
                virtual_drive.total_size_bytes += source_path.stat().st_size
                virtual_drive.file_count += 1
                virtual_drive.last_accessed = datetime.now()
                
                return True
                
        except Exception as e:
            print(f"[VirtualDriveManager] Error adding file to drive: {e}")
            return False
    
    def _add_file_deduplicated(self, virtual_drive: VirtualDrive,
                             source_path: Path, app_name: str) -> bool:
        """Add a file to a deduplicated drive."""
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(source_path)
            
            # Check if file already exists in dedup storage
            dedup_file_path = self.dedup_storage_path / file_hash[:2] / file_hash
            
            if not dedup_file_path.exists():
                # Store file in dedup storage
                dedup_file_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dedup_file_path)
            
            # Create link in virtual drive
            drive_file_path = virtual_drive.base_path / source_path.name
            
            # Create hard link if possible, otherwise symlink
            try:
                if drive_file_path.exists():
                    drive_file_path.unlink()
                drive_file_path.hardlink_to(dedup_file_path)
            except OSError:
                # Fall back to symlink
                drive_file_path.symlink_to(dedup_file_path)
            
            # Update database
            self._update_file_entry_in_db(
                file_hash, str(source_path), str(dedup_file_path),
                source_path.stat().st_size, app_name
            )
            
            # Update drive stats
            virtual_drive.last_accessed = datetime.now()
            
            return True
            
        except Exception as e:
            print(f"[VirtualDriveManager] Error adding deduplicated file: {e}")
            return False
    
    def _create_hardlink_mount(self, source_path: Path, target_path: Path) -> None:
        """Create hard link mount."""
        if target_path.exists():
            shutil.rmtree(target_path)
        
        target_path.mkdir(parents=True)
        
        # Create hard links for all files
        for source_file in source_path.rglob('*'):
            if source_file.is_file():
                relative_path = source_file.relative_to(source_path)
                target_file = target_path / relative_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    target_file.hardlink_to(source_file)
                except OSError:
                    # Fall back to copy if hard link fails
                    shutil.copy2(source_file, target_file)
    
    def _create_dedup_mount(self, virtual_drive: VirtualDrive,
                          target_path: Path, app_name: str) -> None:
        """Create deduplicated mount."""
        if target_path.exists():
            shutil.rmtree(target_path)
        
        target_path.mkdir(parents=True)
        
        # Create links to deduplicated files
        for drive_file in virtual_drive.base_path.rglob('*'):
            if drive_file.is_file():
                relative_path = drive_file.relative_to(virtual_drive.base_path)
                target_file = target_path / relative_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    target_file.hardlink_to(drive_file)
                except OSError:
                    # Fall back to symlink
                    target_file.symlink_to(drive_file)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Create drives table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS drives (
                    drive_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    drive_type TEXT NOT NULL,
                    storage_mode TEXT NOT NULL,
                    base_path TEXT NOT NULL,
                    size_limit_gb REAL,
                    created_at TEXT NOT NULL,
                    metadata TEXT
                )
            ''')
            
            # Create files table for deduplication
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    file_hash TEXT PRIMARY KEY,
                    original_path TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    reference_count INTEGER DEFAULT 1,
                    apps_using TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"[VirtualDriveManager] Error initializing database: {e}")
    
    def _init_drive_in_db(self, virtual_drive: VirtualDrive) -> None:
        """Initialize a drive in the database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO drives 
                (drive_id, name, drive_type, storage_mode, base_path, size_limit_gb, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                virtual_drive.drive_id,
                virtual_drive.name,
                virtual_drive.drive_type.value,
                virtual_drive.storage_mode.value,
                str(virtual_drive.base_path),
                virtual_drive.size_limit_gb,
                virtual_drive.created_at.isoformat(),
                json.dumps(virtual_drive.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"[VirtualDriveManager] Error initializing drive in database: {e}")
    
    def _update_file_entry_in_db(self, file_hash: str, original_path: str,
                               storage_path: str, size_bytes: int, app_name: str) -> None:
        """Update file entry in database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Check if file exists
            cursor.execute('SELECT apps_using, reference_count FROM files WHERE file_hash = ?', (file_hash,))
            result = cursor.fetchone()
            
            if result:
                # Update existing entry
                apps_using = set(json.loads(result[0]))
                apps_using.add(app_name)
                reference_count = result[1] + 1
                
                cursor.execute('''
                    UPDATE files 
                    SET reference_count = ?, apps_using = ?, last_accessed = ?
                    WHERE file_hash = ?
                ''', (reference_count, json.dumps(list(apps_using)), datetime.now().isoformat(), file_hash))
            else:
                # Insert new entry
                cursor.execute('''
                    INSERT INTO files 
                    (file_hash, original_path, storage_path, size_bytes, created_at, last_accessed, reference_count, apps_using)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    file_hash, original_path, storage_path, size_bytes,
                    datetime.now().isoformat(), datetime.now().isoformat(),
                    1, json.dumps([app_name])
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"[VirtualDriveManager] Error updating file entry in database: {e}")
    
    def _remove_drive_from_db(self, drive_id: str) -> None:
        """Remove a drive from the database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM drives WHERE drive_id = ?', (drive_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"[VirtualDriveManager] Error removing drive from database: {e}")
    
    def _save_drive_config(self, virtual_drive: VirtualDrive) -> None:
        """Save drive configuration to disk."""
        config_file = self.virtual_drives_path / f"{virtual_drive.drive_id}.json"
        try:
            self.json_handler.write_json_file(str(config_file), virtual_drive.to_dict())
        except Exception as e:
            print(f"[VirtualDriveManager] Error saving drive config: {e}")
    
    def _load_existing_drives(self) -> None:
        """Load existing drive configurations."""
        try:
            for config_file in self.virtual_drives_path.glob("*.json"):
                try:
                    config_data = self.json_handler.read_json_file(str(config_file))
                    virtual_drive = VirtualDrive.from_dict(config_data)
                    
                    # Only load if drive directory exists
                    if virtual_drive.base_path.exists():
                        self.active_drives[virtual_drive.drive_id] = virtual_drive
                        print(f"[VirtualDriveManager] Loaded existing drive: {virtual_drive.drive_id}")
                    else:
                        # Remove stale config
                        config_file.unlink()
                        
                except Exception as e:
                    print(f"[VirtualDriveManager] Error loading drive config {config_file}: {e}")
                    
        except Exception as e:
            print(f"[VirtualDriveManager] Error loading drive configurations: {e}")
    
    def _remove_drive_config(self, drive_id: str) -> None:
        """Remove drive configuration from disk."""
        config_file = self.virtual_drives_path / f"{drive_id}.json"
        try:
            if config_file.exists():
                config_file.unlink()
        except Exception as e:
            print(f"[VirtualDriveManager] Error removing drive config: {e}")


def main():
    """Test the virtual drive manager functionality."""
    print("Testing VirtualDriveManager...")
    
    manager = VirtualDriveManager()
    
    # Create a test virtual drive
    test_drive = manager.create_virtual_drive(
        drive_name="test_drive",
        drive_type=DriveType.APP_SPECIFIC,
        size_gb=1.0,
        storage_mode=StorageMode.SYMLINK
    )
    
    print(f"Created test drive: {test_drive.drive_id}")
    
    # Test mounting
    mount_path = manager.mount_drive_for_app("test_app", test_drive.drive_id)
    print(f"Mounted drive at: {mount_path}")
    
    # Get drive stats
    stats = manager.get_drive_usage_stats(test_drive.drive_id)
    print(f"Drive stats: {stats}")
    
    # List all drives
    all_drives = manager.list_virtual_drives()
    print(f"Total drives: {len(all_drives)}")
    
    # Cleanup
    manager.unmount_drive_for_app("test_app", test_drive.drive_id)
    cleaned = manager.cleanup_unused_drives()
    print(f"Cleaned up drives: {cleaned}")
    
    print("VirtualDriveManager test completed")


if __name__ == "__main__":
    main()