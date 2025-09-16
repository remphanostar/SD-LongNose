#!/usr/bin/env python3
"""
PinokioCloud Path Mapping System

This module provides intelligent path mapping between different cloud platforms,
ensuring consistent file system access across Google Colab, Vast.ai, Lightning.ai,
Paperspace, and RunPod environments.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import shutil
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class CloudPlatform(Enum):
    """Enumeration of supported cloud platforms."""
    GOOGLE_COLAB = "google-colab"
    VAST_AI = "vast-ai"
    LIGHTNING_AI = "lightning-ai"
    PAPERSPACE = "paperspace"
    RUNPOD = "runpod"
    UNKNOWN = "unknown"


@dataclass
class PathMapping:
    """Path mapping configuration for a cloud platform."""
    platform: CloudPlatform
    base_path: str
    apps_path: str
    data_path: str
    temp_path: str
    logs_path: str
    cache_path: str
    models_path: str
    config_path: str
    workspace_path: str
    drive_mount_path: Optional[str] = None
    shared_storage_path: Optional[str] = None
    custom_mappings: Dict[str, str] = field(default_factory=dict)


@dataclass
class PathMappingResult:
    """Result of path mapping operation."""
    source_path: str
    target_path: str
    platform: CloudPlatform
    mapping_type: str
    success: bool
    error_message: Optional[str] = None
    created_directories: List[str] = field(default_factory=list)


class PathMapper:
    """
    Intelligent path mapping system for multi-cloud environments.
    
    Provides consistent file system access across different cloud platforms
    by mapping platform-specific paths to standardized locations.
    """
    
    def __init__(self, current_platform: CloudPlatform):
        """
        Initialize the path mapper.
        
        Args:
            current_platform: The current cloud platform
        """
        self.current_platform = current_platform
        self.path_mappings = self._initialize_path_mappings()
        self.standard_paths = self._initialize_standard_paths()
    
    def _initialize_path_mappings(self) -> Dict[CloudPlatform, PathMapping]:
        """Initialize path mappings for all platforms."""
        mappings = {}
        
        # Google Colab mappings
        mappings[CloudPlatform.GOOGLE_COLAB] = PathMapping(
            platform=CloudPlatform.GOOGLE_COLAB,
            base_path="/content",
            apps_path="/content/apps",
            data_path="/content/data",
            temp_path="/tmp",
            logs_path="/content/logs",
            cache_path="/content/cache",
            models_path="/content/models",
            config_path="/content/config",
            workspace_path="/content/workspace",
            drive_mount_path="/mnt/MyDrive",
            shared_storage_path="/content/shared",
            custom_mappings={
                "jupyter": "/content",
                "notebooks": "/content/notebooks",
                "uploads": "/content/uploads",
                "downloads": "/content/downloads"
            }
        )
        
        # Vast.ai mappings
        mappings[CloudPlatform.VAST_AI] = PathMapping(
            platform=CloudPlatform.VAST_AI,
            base_path="/workspace",
            apps_path="/workspace/apps",
            data_path="/workspace/data",
            temp_path="/tmp",
            logs_path="/workspace/logs",
            cache_path="/workspace/cache",
            models_path="/workspace/models",
            config_path="/workspace/config",
            workspace_path="/workspace",
            drive_mount_path=None,
            shared_storage_path="/workspace/shared",
            custom_mappings={
                "jupyter": "/workspace",
                "notebooks": "/workspace/notebooks",
                "uploads": "/workspace/uploads",
                "downloads": "/workspace/downloads"
            }
        )
        
        # Lightning.ai mappings
        mappings[CloudPlatform.LIGHTNING_AI] = PathMapping(
            platform=CloudPlatform.LIGHTNING_AI,
            base_path="/teamspace",
            apps_path="/teamspace/apps",
            data_path="/teamspace/data",
            temp_path="/tmp",
            logs_path="/teamspace/logs",
            cache_path="/teamspace/cache",
            models_path="/teamspace/models",
            config_path="/teamspace/config",
            workspace_path="/teamspace/workspace",
            drive_mount_path=None,
            shared_storage_path="/teamspace/shared",
            custom_mappings={
                "jupyter": "/teamspace",
                "notebooks": "/teamspace/notebooks",
                "uploads": "/teamspace/uploads",
                "downloads": "/teamspace/downloads"
            }
        )
        
        # Paperspace mappings
        mappings[CloudPlatform.PAPERSPACE] = PathMapping(
            platform=CloudPlatform.PAPERSPACE,
            base_path="/paperspace",
            apps_path="/paperspace/apps",
            data_path="/paperspace/data",
            temp_path="/tmp",
            logs_path="/paperspace/logs",
            cache_path="/paperspace/cache",
            models_path="/paperspace/models",
            config_path="/paperspace/config",
            workspace_path="/paperspace/workspace",
            drive_mount_path=None,
            shared_storage_path="/paperspace/shared",
            custom_mappings={
                "jupyter": "/paperspace",
                "notebooks": "/paperspace/notebooks",
                "uploads": "/paperspace/uploads",
                "downloads": "/paperspace/downloads"
            }
        )
        
        # RunPod mappings
        mappings[CloudPlatform.RUNPOD] = PathMapping(
            platform=CloudPlatform.RUNPOD,
            base_path="/runpod",
            apps_path="/runpod/apps",
            data_path="/runpod/data",
            temp_path="/tmp",
            logs_path="/runpod/logs",
            cache_path="/runpod/cache",
            models_path="/runpod/models",
            config_path="/runpod/config",
            workspace_path="/runpod/workspace",
            drive_mount_path=None,
            shared_storage_path="/runpod/shared",
            custom_mappings={
                "jupyter": "/runpod",
                "notebooks": "/runpod/notebooks",
                "uploads": "/runpod/uploads",
                "downloads": "/runpod/downloads"
            }
        )
        
        return mappings
    
    def _initialize_standard_paths(self) -> Dict[str, str]:
        """Initialize standard path definitions."""
        return {
            "base": "base_path",
            "apps": "apps_path",
            "data": "data_path",
            "temp": "temp_path",
            "logs": "logs_path",
            "cache": "cache_path",
            "models": "models_path",
            "config": "config_path",
            "workspace": "workspace_path",
            "drive": "drive_mount_path",
            "shared": "shared_storage_path"
        }
    
    def map_path(self, source_path: str, target_platform: Optional[CloudPlatform] = None,
                 path_type: Optional[str] = None) -> PathMappingResult:
        """
        Map a path from source to target platform.
        
        Args:
            source_path: Source path to map
            target_platform: Target platform (defaults to current platform)
            path_type: Type of path (base, apps, data, etc.)
            
        Returns:
            PathMappingResult: Result of the mapping operation
        """
        if target_platform is None:
            target_platform = self.current_platform
        
        try:
            # Determine the mapping type
            if path_type:
                mapping_type = f"standard_{path_type}"
                target_path = self._map_standard_path(source_path, target_platform, path_type)
            else:
                mapping_type = "custom"
                target_path = self._map_custom_path(source_path, target_platform)
            
            # Create directories if they don't exist
            created_dirs = self._ensure_directories_exist(target_path)
            
            return PathMappingResult(
                source_path=source_path,
                target_path=target_path,
                platform=target_platform,
                mapping_type=mapping_type,
                success=True,
                created_directories=created_dirs
            )
        
        except Exception as e:
            return PathMappingResult(
                source_path=source_path,
                target_path="",
                platform=target_platform,
                mapping_type="error",
                success=False,
                error_message=str(e)
            )
    
    def _map_standard_path(self, source_path: str, target_platform: CloudPlatform, 
                          path_type: str) -> str:
        """Map a standard path type to target platform."""
        if target_platform not in self.path_mappings:
            raise ValueError(f"Unsupported platform: {target_platform}")
        
        mapping = self.path_mappings[target_platform]
        
        # Get the base path for the path type
        if path_type in self.standard_paths:
            base_path_attr = self.standard_paths[path_type]
            base_path = getattr(mapping, base_path_attr)
        else:
            raise ValueError(f"Unknown path type: {path_type}")
        
        if base_path is None:
            raise ValueError(f"Path type {path_type} not supported on {target_platform.value}")
        
        # Extract relative path from source
        relative_path = self._extract_relative_path(source_path)
        
        # Combine base path with relative path
        target_path = os.path.join(base_path, relative_path)
        
        return target_path
    
    def _map_custom_path(self, source_path: str, target_platform: CloudPlatform) -> str:
        """Map a custom path to target platform."""
        if target_platform not in self.path_mappings:
            raise ValueError(f"Unsupported platform: {target_platform}")
        
        mapping = self.path_mappings[target_platform]
        
        # Check if source path matches any custom mappings
        for custom_key, custom_path in mapping.custom_mappings.items():
            if custom_key in source_path.lower():
                relative_path = self._extract_relative_path(source_path)
                return os.path.join(custom_path, relative_path)
        
        # Default to base path
        relative_path = self._extract_relative_path(source_path)
        return os.path.join(mapping.base_path, relative_path)
    
    def _extract_relative_path(self, source_path: str) -> str:
        """Extract relative path from source path."""
        # Normalize the path
        normalized_path = os.path.normpath(source_path)
        
        # Find the longest matching base path
        best_match = ""
        best_length = 0
        
        for platform, mapping in self.path_mappings.items():
            # Check against all possible base paths
            base_paths = [
                mapping.base_path,
                mapping.apps_path,
                mapping.data_path,
                mapping.temp_path,
                mapping.logs_path,
                mapping.cache_path,
                mapping.models_path,
                mapping.config_path,
                mapping.workspace_path
            ]
            
            for base_path in base_paths:
                if base_path and normalized_path.startswith(base_path):
                    if len(base_path) > best_length:
                        best_match = base_path
                        best_length = len(base_path)
        
        # Extract relative path
        if best_match:
            relative_path = normalized_path[len(best_match):].lstrip('/')
        else:
            # If no match found, use the entire path
            relative_path = normalized_path.lstrip('/')
        
        return relative_path
    
    def _ensure_directories_exist(self, target_path: str) -> List[str]:
        """Ensure that all directories in the target path exist."""
        created_dirs = []
        
        try:
            # Create the directory and all parent directories
            os.makedirs(target_path, exist_ok=True)
            
            # Check if we actually created any new directories
            path_parts = Path(target_path).parts
            current_path = ""
            
            for part in path_parts:
                current_path = os.path.join(current_path, part) if current_path else part
                if not os.path.exists(current_path):
                    created_dirs.append(current_path)
        
        except Exception as e:
            # If we can't create directories, that's okay - they might already exist
            pass
        
        return created_dirs
    
    def get_platform_paths(self, platform: CloudPlatform) -> Dict[str, str]:
        """
        Get all paths for a specific platform.
        
        Args:
            platform: CloudPlatform enum value
            
        Returns:
            Dictionary of path types to paths
        """
        if platform not in self.path_mappings:
            return {}
        
        mapping = self.path_mappings[platform]
        
        paths = {
            "base": mapping.base_path,
            "apps": mapping.apps_path,
            "data": mapping.data_path,
            "temp": mapping.temp_path,
            "logs": mapping.logs_path,
            "cache": mapping.cache_path,
            "models": mapping.models_path,
            "config": mapping.config_path,
            "workspace": mapping.workspace_path,
            "drive": mapping.drive_mount_path,
            "shared": mapping.shared_storage_path
        }
        
        # Add custom mappings
        paths.update(mapping.custom_mappings)
        
        return paths
    
    def get_current_platform_paths(self) -> Dict[str, str]:
        """Get all paths for the current platform."""
        return self.get_platform_paths(self.current_platform)
    
    def copy_file(self, source_path: str, target_path: str, 
                  create_dirs: bool = True) -> bool:
        """
        Copy a file from source to target path.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            create_dirs: Whether to create target directories
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if create_dirs:
                target_dir = os.path.dirname(target_path)
                os.makedirs(target_dir, exist_ok=True)
            
            shutil.copy2(source_path, target_path)
            return True
        
        except Exception as e:
            return False
    
    def copy_directory(self, source_path: str, target_path: str,
                      create_dirs: bool = True) -> bool:
        """
        Copy a directory from source to target path.
        
        Args:
            source_path: Source directory path
            target_path: Target directory path
            create_dirs: Whether to create target directories
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if create_dirs:
                os.makedirs(target_path, exist_ok=True)
            
            shutil.copytree(source_path, target_path, dirs_exist_ok=True)
            return True
        
        except Exception as e:
            return False
    
    def move_file(self, source_path: str, target_path: str,
                 create_dirs: bool = True) -> bool:
        """
        Move a file from source to target path.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            create_dirs: Whether to create target directories
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if create_dirs:
                target_dir = os.path.dirname(target_path)
                os.makedirs(target_dir, exist_ok=True)
            
            shutil.move(source_path, target_path)
            return True
        
        except Exception as e:
            return False
    
    def create_symlink(self, source_path: str, target_path: str,
                      create_dirs: bool = True) -> bool:
        """
        Create a symbolic link from source to target path.
        
        Args:
            source_path: Source path
            target_path: Target path
            create_dirs: Whether to create target directories
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if create_dirs:
                target_dir = os.path.dirname(target_path)
                os.makedirs(target_dir, exist_ok=True)
            
            # Remove existing link if it exists
            if os.path.exists(target_path) or os.path.islink(target_path):
                os.remove(target_path)
            
            os.symlink(source_path, target_path)
            return True
        
        except Exception as e:
            return False
    
    def get_path_info(self, path: str) -> Dict[str, Any]:
        """
        Get information about a path.
        
        Args:
            path: Path to analyze
            
        Returns:
            Dictionary with path information
        """
        info = {
            "path": path,
            "exists": os.path.exists(path),
            "is_file": os.path.isfile(path),
            "is_directory": os.path.isdir(path),
            "is_symlink": os.path.islink(path),
            "size_bytes": 0,
            "permissions": "",
            "modified_time": 0,
            "access_time": 0
        }
        
        try:
            if info["exists"]:
                stat_info = os.stat(path)
                info["size_bytes"] = stat_info.st_size
                info["permissions"] = oct(stat_info.st_mode)[-3:]
                info["modified_time"] = stat_info.st_mtime
                info["access_time"] = stat_info.st_atime
        except:
            pass
        
        return info
    
    def validate_path_mapping(self, source_path: str, target_path: str) -> bool:
        """
        Validate that a path mapping is correct.
        
        Args:
            source_path: Source path
            target_path: Target path
            
        Returns:
            bool: True if mapping is valid, False otherwise
        """
        try:
            # Check if source path exists
            if not os.path.exists(source_path):
                return False
            
            # Check if target path is accessible
            target_dir = os.path.dirname(target_path)
            if not os.path.exists(target_dir):
                # Try to create the directory
                try:
                    os.makedirs(target_dir, exist_ok=True)
                except:
                    return False
            
            # Check if we can write to target location
            test_file = os.path.join(target_dir, ".path_mapping_test")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                return True
            except:
                return False
        
        except:
            return False
    
    def get_mapping_summary(self) -> str:
        """Get a summary of current path mappings."""
        summary = f"Path Mapping Summary for {self.current_platform.value}:\n"
        
        current_paths = self.get_current_platform_paths()
        for path_type, path in current_paths.items():
            if path:
                summary += f"  {path_type}: {path}\n"
        
        return summary


def main():
    """Main function for testing path mapping."""
    # Test with different platforms
    test_platforms = [
        CloudPlatform.GOOGLE_COLAB,
        CloudPlatform.VAST_AI,
        CloudPlatform.LIGHTNING_AI
    ]
    
    for platform in test_platforms:
        print(f"\nTesting {platform.value}:")
        mapper = PathMapper(platform)
        
        # Test standard path mapping
        result = mapper.map_path("/content/apps/myapp", path_type="apps")
        print(f"  Standard mapping: {result.source_path} -> {result.target_path}")
        
        # Test custom path mapping
        result = mapper.map_path("/content/notebooks/test.ipynb")
        print(f"  Custom mapping: {result.source_path} -> {result.target_path}")
        
        # Show platform paths
        print(f"  Platform paths: {mapper.get_current_platform_paths()}")
    
    return True


if __name__ == "__main__":
    main()