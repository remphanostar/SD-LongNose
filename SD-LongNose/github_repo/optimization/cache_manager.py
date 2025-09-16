#!/usr/bin/env python3
"""
PinokioCloud Cache Manager

This module implements a multi-layer caching system with intelligent prefetching
for models, applications, and data. It provides comprehensive caching strategies
to optimize performance across all PinokioCloud operations.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import hashlib
import threading
import sqlite3
import pickle
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import shutil

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from environment_management.file_system import FileSystemManager
from environment_management.json_handler import JSONHandler
from cloud_detection.cloud_detector import CloudDetector
from running.process_tracker import ProcessTracker
from app_analysis.app_analyzer import AppAnalyzer


class CacheLayer(Enum):
    """Enumeration of cache layers."""
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    PERSISTENT = "persistent"


class CacheStrategy(Enum):
    """Enumeration of cache strategies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In, First Out
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptive based on usage patterns


class CacheType(Enum):
    """Types of cached data."""
    APP_METADATA = "app_metadata"
    MODEL_FILES = "model_files"
    DEPENDENCY_INFO = "dependency_info"
    INSTALLATION_STATE = "installation_state"
    PROCESS_INFO = "process_info"
    TUNNEL_CONFIG = "tunnel_config"
    PLATFORM_CONFIG = "platform_config"
    USER_PREFERENCES = "user_preferences"


@dataclass
class CacheEntry:
    """Information about a cache entry."""
    key: str
    cache_type: CacheType
    data_size: int
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.ttl_seconds is None:
            return False
        
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert CacheEntry to dictionary."""
        data = asdict(self)
        data['cache_type'] = self.cache_type.value
        data['created_at'] = self.created_at.isoformat()
        data['last_accessed'] = self.last_accessed.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create CacheEntry from dictionary."""
        data['cache_type'] = CacheType(data['cache_type'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_accessed'] = datetime.fromisoformat(data['last_accessed'])
        return cls(**data)


class CacheManager:
    """
    Multi-layer caching system with intelligent prefetching.
    
    This class provides comprehensive caching for models, applications, and data
    with intelligent prefetching, cache invalidation, and performance optimization.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the cache manager."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.cache_storage_path = self.base_path / "cache_storage"
        self.cache_storage_path.mkdir(exist_ok=True)
        
        # Cache layers
        self.memory_cache: Dict[str, Any] = {}
        self.disk_cache_path = self.cache_storage_path / "disk_cache"
        self.disk_cache_path.mkdir(exist_ok=True)
        
        # Cache database
        self.cache_db_path = self.cache_storage_path / "cache.db"
        self.cache_entries: Dict[str, CacheEntry] = {}
        
        # Cache configuration
        self.max_memory_cache_mb = 512  # 512MB memory cache
        self.max_disk_cache_gb = 10.0   # 10GB disk cache
        self.default_ttl_hours = 24     # 24 hour default TTL
        self.cleanup_interval = 3600    # 1 hour cleanup interval
        
        # Cache strategies by type
        self.cache_strategies = {
            CacheType.APP_METADATA: CacheStrategy.LRU,
            CacheType.MODEL_FILES: CacheStrategy.LFU,
            CacheType.DEPENDENCY_INFO: CacheStrategy.TTL,
            CacheType.INSTALLATION_STATE: CacheStrategy.ADAPTIVE,
            CacheType.PROCESS_INFO: CacheStrategy.TTL,
            CacheType.TUNNEL_CONFIG: CacheStrategy.LRU,
            CacheType.PLATFORM_CONFIG: CacheStrategy.PERSISTENT,
            CacheType.USER_PREFERENCES: CacheStrategy.PERSISTENT
        }
        
        # Cache locks
        self.memory_lock = threading.RLock()
        self.disk_lock = threading.RLock()
        self.db_lock = threading.RLock()
        
        # Initialize dependencies
        self.file_system = FileSystemManager(str(self.base_path))
        self.json_handler = JSONHandler(str(self.base_path))
        self.cloud_detector = CloudDetector()
        self.process_tracker = ProcessTracker(str(self.base_path))
        self.app_analyzer = AppAnalyzer(str(self.base_path))
        
        # Platform-specific cache limits
        self.platform_info = self.cloud_detector.detect_platform()
        self._adjust_cache_limits_for_platform()
        
        # Cleanup thread
        self.cleanup_active = False
        self.cleanup_thread = None
        
        # Statistics
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'prefetch_hits': 0,
            'total_size_bytes': 0
        }
        
        # Initialize cache system
        self._initialize_cache_database()
        self._load_existing_cache_entries()
        self._start_cleanup_thread()
        
        print(f"[CacheManager] Initialized with memory limit: {self.max_memory_cache_mb}MB, "
              f"disk limit: {self.max_disk_cache_gb}GB")
        print(f"[CacheManager] Platform: {self.platform_info.platform}, "
              f"loaded {len(self.cache_entries)} existing entries")
    
    def get(self, key: str, cache_type: CacheType = CacheType.APP_METADATA) -> Optional[Any]:
        """
        Get data from cache.
        
        Args:
            key: Cache key
            cache_type: Type of cached data
        
        Returns:
            Optional[Any]: Cached data if found and valid
        """
        try:
            # Check memory cache first
            with self.memory_lock:
                if key in self.memory_cache:
                    self.cache_stats['hits'] += 1
                    
                    # Update access info
                    if key in self.cache_entries:
                        entry = self.cache_entries[key]
                        entry.last_accessed = datetime.now()
                        entry.access_count += 1
                        self._update_cache_entry_in_db(entry)
                    
                    print(f"[CacheManager] Memory cache hit: {key}")
                    return self.memory_cache[key]
            
            # Check disk cache
            disk_file = self._get_disk_cache_path(key, cache_type)
            if disk_file.exists():
                with self.disk_lock:
                    try:
                        # Load from disk
                        if cache_type in [CacheType.APP_METADATA, CacheType.DEPENDENCY_INFO]:
                            # JSON data
                            data = self.json_handler.read_json_file(str(disk_file))
                        else:
                            # Binary data
                            with open(disk_file, 'rb') as f:
                                data = pickle.load(f)
                        
                        # Check if entry is expired
                        if key in self.cache_entries:
                            entry = self.cache_entries[key]
                            if entry.is_expired():
                                self._evict_entry(key)
                                self.cache_stats['misses'] += 1
                                return None
                            
                            # Update access info
                            entry.last_accessed = datetime.now()
                            entry.access_count += 1
                            self._update_cache_entry_in_db(entry)
                        
                        # Promote to memory cache if small enough
                        data_size = self._estimate_data_size(data)
                        if data_size < self.max_memory_cache_mb * 1024 * 1024 * 0.1:  # 10% of memory limit
                            with self.memory_lock:
                                self.memory_cache[key] = data
                        
                        self.cache_stats['hits'] += 1
                        print(f"[CacheManager] Disk cache hit: {key}")
                        return data
                        
                    except Exception as e:
                        print(f"[CacheManager] Error loading from disk cache: {e}")
                        # Remove corrupted cache file
                        disk_file.unlink(missing_ok=True)
            
            # Cache miss
            self.cache_stats['misses'] += 1
            return None
            
        except Exception as e:
            print(f"[CacheManager] Error getting cache entry {key}: {e}")
            self.cache_stats['misses'] += 1
            return None
    
    def put(self, key: str, data: Any, cache_type: CacheType = CacheType.APP_METADATA,
            ttl_seconds: Optional[int] = None, priority: int = 1) -> bool:
        """
        Store data in cache.
        
        Args:
            key: Cache key
            data: Data to cache
            cache_type: Type of cached data
            ttl_seconds: Time to live in seconds
            priority: Cache priority (higher = more important)
        
        Returns:
            bool: True if successfully cached
        """
        try:
            data_size = self._estimate_data_size(data)
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                cache_type=cache_type,
                data_size=data_size,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl_seconds=ttl_seconds or (self.default_ttl_hours * 3600),
                priority=priority
            )
            
            # Determine cache layer based on size and strategy
            strategy = self.cache_strategies.get(cache_type, CacheStrategy.LRU)
            
            # Store in memory cache if small enough
            memory_limit_bytes = self.max_memory_cache_mb * 1024 * 1024
            if data_size < memory_limit_bytes * 0.2:  # 20% of memory limit per item
                with self.memory_lock:
                    # Check if we need to evict items
                    current_memory_usage = sum(self._estimate_data_size(v) for v in self.memory_cache.values())
                    
                    while current_memory_usage + data_size > memory_limit_bytes:
                        # Evict least important item
                        evicted_key = self._evict_from_memory(strategy)
                        if not evicted_key:
                            break
                        current_memory_usage = sum(self._estimate_data_size(v) for v in self.memory_cache.values())
                    
                    self.memory_cache[key] = data
                    print(f"[CacheManager] Stored in memory cache: {key} ({data_size} bytes)")
            
            # Store in disk cache
            with self.disk_lock:
                disk_file = self._get_disk_cache_path(key, cache_type)
                disk_file.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    if cache_type in [CacheType.APP_METADATA, CacheType.DEPENDENCY_INFO]:
                        # JSON data
                        self.json_handler.write_json_file(str(disk_file), data)
                    else:
                        # Binary data
                        with open(disk_file, 'wb') as f:
                            pickle.dump(data, f)
                    
                    print(f"[CacheManager] Stored in disk cache: {key}")
                    
                except Exception as e:
                    print(f"[CacheManager] Error storing to disk: {e}")
                    return False
            
            # Register cache entry
            with self.db_lock:
                self.cache_entries[key] = entry
                self._save_cache_entry_to_db(entry)
            
            # Update statistics
            self.cache_stats['total_size_bytes'] += data_size
            
            # Check if we need to cleanup disk cache
            self._check_disk_cache_limits()
            
            return True
            
        except Exception as e:
            print(f"[CacheManager] Error caching data: {e}")
            return False
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
        
        Returns:
            bool: True if successfully invalidated
        """
        try:
            invalidated = False
            
            # Remove from memory cache
            with self.memory_lock:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    invalidated = True
            
            # Remove from disk cache
            if key in self.cache_entries:
                entry = self.cache_entries[key]
                disk_file = self._get_disk_cache_path(key, entry.cache_type)
                
                with self.disk_lock:
                    if disk_file.exists():
                        disk_file.unlink()
                        invalidated = True
                
                # Update statistics
                self.cache_stats['total_size_bytes'] -= entry.data_size
                
                # Remove from entries
                with self.db_lock:
                    del self.cache_entries[key]
                    self._remove_cache_entry_from_db(key)
            
            if invalidated:
                print(f"[CacheManager] Invalidated cache entry: {key}")
            
            return invalidated
            
        except Exception as e:
            print(f"[CacheManager] Error invalidating cache entry {key}: {e}")
            return False
    
    def prefetch_app_data(self, app_name: str) -> bool:
        """
        Prefetch data for an application.
        
        Args:
            app_name: Name of the application to prefetch
        
        Returns:
            bool: True if prefetch was successful
        """
        print(f"[CacheManager] Prefetching data for app: {app_name}")
        
        try:
            prefetch_tasks = []
            
            # 1. Prefetch app metadata
            app_profile = self.app_analyzer.get_app_profile(app_name)
            if app_profile:
                cache_key = f"app_profile_{app_name}"
                self.put(cache_key, app_profile, CacheType.APP_METADATA, priority=3)
                prefetch_tasks.append("app_profile")
            
            # 2. Prefetch dependency information
            try:
                # This would integrate with dependency managers
                dep_info = {"dependencies": [], "prefetched_at": datetime.now().isoformat()}
                cache_key = f"dependencies_{app_name}"
                self.put(cache_key, dep_info, CacheType.DEPENDENCY_INFO, priority=2)
                prefetch_tasks.append("dependencies")
            except Exception:
                pass
            
            # 3. Prefetch common model files (if they exist)
            app_path = self.base_path / "apps" / app_name
            if app_path.exists():
                model_patterns = ["*.safetensors", "*.ckpt", "*.pt", "*.pth", "*.bin"]
                for pattern in model_patterns:
                    for model_file in app_path.rglob(pattern):
                        if model_file.stat().st_size < 100 * 1024 * 1024:  # Less than 100MB
                            cache_key = f"model_{app_name}_{model_file.name}"
                            try:
                                model_data = model_file.read_bytes()
                                self.put(cache_key, model_data, CacheType.MODEL_FILES, priority=1)
                                prefetch_tasks.append(f"model_{model_file.name}")
                            except Exception:
                                continue
            
            # Update statistics
            if prefetch_tasks:
                self.cache_stats['prefetch_hits'] += len(prefetch_tasks)
            
            print(f"[CacheManager] Prefetch completed for {app_name}: {len(prefetch_tasks)} items")
            return True
            
        except Exception as e:
            print(f"[CacheManager] Error prefetching app data: {e}")
            return False
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        try:
            # Calculate current usage
            memory_usage_bytes = sum(self._estimate_data_size(v) for v in self.memory_cache.values())
            disk_usage_bytes = sum(entry.data_size for entry in self.cache_entries.values())
            
            # Calculate hit rate
            total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
            hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            # Count by type
            entries_by_type = {}
            for entry in self.cache_entries.values():
                cache_type = entry.cache_type.value
                if cache_type not in entries_by_type:
                    entries_by_type[cache_type] = 0
                entries_by_type[cache_type] += 1
            
            stats = {
                'timestamp': datetime.now().isoformat(),
                'memory_cache': {
                    'entries': len(self.memory_cache),
                    'usage_bytes': memory_usage_bytes,
                    'usage_mb': memory_usage_bytes / (1024 * 1024),
                    'limit_mb': self.max_memory_cache_mb,
                    'utilization_percent': (memory_usage_bytes / (self.max_memory_cache_mb * 1024 * 1024)) * 100
                },
                'disk_cache': {
                    'entries': len(self.cache_entries),
                    'usage_bytes': disk_usage_bytes,
                    'usage_gb': disk_usage_bytes / (1024 * 1024 * 1024),
                    'limit_gb': self.max_disk_cache_gb,
                    'utilization_percent': (disk_usage_bytes / (self.max_disk_cache_gb * 1024 * 1024 * 1024)) * 100
                },
                'performance': {
                    'hit_rate_percent': hit_rate,
                    'total_hits': self.cache_stats['hits'],
                    'total_misses': self.cache_stats['misses'],
                    'total_evictions': self.cache_stats['evictions'],
                    'prefetch_hits': self.cache_stats['prefetch_hits']
                },
                'entries_by_type': entries_by_type,
                'platform': self.platform_info.platform.value
            }
            
            return stats
            
        except Exception as e:
            print(f"[CacheManager] Error getting statistics: {e}")
            return {}
    
    def cleanup_expired_entries(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            int: Number of entries cleaned up
        """
        print("[CacheManager] Cleaning up expired cache entries...")
        
        cleaned_count = 0
        
        try:
            expired_keys = []
            
            # Find expired entries
            for key, entry in self.cache_entries.items():
                if entry.is_expired():
                    expired_keys.append(key)
            
            # Remove expired entries
            for key in expired_keys:
                if self.invalidate(key):
                    cleaned_count += 1
            
            # Update statistics
            self.cache_stats['evictions'] += cleaned_count
            
            if cleaned_count > 0:
                print(f"[CacheManager] Cleaned up {cleaned_count} expired entries")
            
            return cleaned_count
            
        except Exception as e:
            print(f"[CacheManager] Error cleaning up expired entries: {e}")
            return 0
    
    def optimize_cache_performance(self) -> Dict[str, Any]:
        """
        Optimize cache performance based on usage patterns.
        
        Returns:
            Dict[str, Any]: Optimization results
        """
        print("[CacheManager] Optimizing cache performance...")
        
        optimization_results = {
            'memory_optimized': False,
            'disk_optimized': False,
            'strategies_adjusted': False,
            'prefetch_optimized': False
        }
        
        try:
            # 1. Optimize memory cache
            optimization_results['memory_optimized'] = self._optimize_memory_cache()
            
            # 2. Optimize disk cache
            optimization_results['disk_optimized'] = self._optimize_disk_cache()
            
            # 3. Adjust cache strategies based on usage patterns
            optimization_results['strategies_adjusted'] = self._adjust_cache_strategies()
            
            # 4. Optimize prefetching
            optimization_results['prefetch_optimized'] = self._optimize_prefetching()
            
            print(f"[CacheManager] Cache optimization complete: "
                  f"{sum(optimization_results.values())}/4 optimizations applied")
            
            return optimization_results
            
        except Exception as e:
            print(f"[CacheManager] Error optimizing cache: {e}")
            return optimization_results
    
    def _adjust_cache_limits_for_platform(self) -> None:
        """Adjust cache limits based on cloud platform."""
        try:
            platform = self.platform_info.platform.value
            
            if platform == "google_colab":
                # Colab has limited storage
                self.max_memory_cache_mb = 256
                self.max_disk_cache_gb = 5.0
            elif platform == "vast_ai":
                # Vast.ai typically has more resources
                self.max_memory_cache_mb = 1024
                self.max_disk_cache_gb = 20.0
            elif platform == "lightning_ai":
                # Lightning.ai has shared storage
                self.max_memory_cache_mb = 512
                self.max_disk_cache_gb = 15.0
            else:
                # Default limits
                self.max_memory_cache_mb = 512
                self.max_disk_cache_gb = 10.0
            
            print(f"[CacheManager] Adjusted limits for {platform}: "
                  f"{self.max_memory_cache_mb}MB memory, {self.max_disk_cache_gb}GB disk")
            
        except Exception as e:
            print(f"[CacheManager] Error adjusting cache limits: {e}")
    
    def _get_disk_cache_path(self, key: str, cache_type: CacheType) -> Path:
        """Get disk cache file path for a key."""
        # Create subdirectory by cache type
        cache_dir = self.disk_cache_path / cache_type.value
        cache_dir.mkdir(exist_ok=True)
        
        # Hash the key to create filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        
        # Determine file extension
        if cache_type in [CacheType.APP_METADATA, CacheType.DEPENDENCY_INFO]:
            extension = ".json"
        else:
            extension = ".pkl"
        
        return cache_dir / f"{key_hash}{extension}"
    
    def _estimate_data_size(self, data: Any) -> int:
        """Estimate the size of data in bytes."""
        try:
            if isinstance(data, (str, bytes)):
                return len(data)
            elif isinstance(data, (dict, list)):
                return len(json.dumps(data).encode())
            else:
                return len(pickle.dumps(data))
        except:
            return 1024  # Default estimate
    
    def _evict_from_memory(self, strategy: CacheStrategy) -> Optional[str]:
        """Evict an item from memory cache based on strategy."""
        if not self.memory_cache:
            return None
        
        try:
            if strategy == CacheStrategy.LRU:
                # Evict least recently used
                lru_key = min(self.cache_entries.keys(), 
                             key=lambda k: self.cache_entries[k].last_accessed 
                             if k in self.cache_entries else datetime.min)
                if lru_key in self.memory_cache:
                    del self.memory_cache[lru_key]
                    self.cache_stats['evictions'] += 1
                    return lru_key
            
            elif strategy == CacheStrategy.LFU:
                # Evict least frequently used
                lfu_key = min(self.cache_entries.keys(),
                             key=lambda k: self.cache_entries[k].access_count
                             if k in self.cache_entries else 0)
                if lfu_key in self.memory_cache:
                    del self.memory_cache[lfu_key]
                    self.cache_stats['evictions'] += 1
                    return lfu_key
            
            else:
                # Default: evict first item
                first_key = next(iter(self.memory_cache))
                del self.memory_cache[first_key]
                self.cache_stats['evictions'] += 1
                return first_key
            
            return None
            
        except Exception as e:
            print(f"[CacheManager] Error evicting from memory: {e}")
            return None
    
    def _evict_entry(self, key: str) -> bool:
        """Completely evict an entry from all cache layers."""
        return self.invalidate(key)
    
    def _check_disk_cache_limits(self) -> None:
        """Check and enforce disk cache limits."""
        try:
            total_size = sum(entry.data_size for entry in self.cache_entries.values())
            limit_bytes = self.max_disk_cache_gb * 1024 * 1024 * 1024
            
            if total_size > limit_bytes:
                # Need to evict entries
                excess_bytes = total_size - limit_bytes
                
                # Sort entries by priority and last access
                sorted_entries = sorted(
                    self.cache_entries.items(),
                    key=lambda x: (x[1].priority, x[1].last_accessed)
                )
                
                # Evict entries until under limit
                for key, entry in sorted_entries:
                    if excess_bytes <= 0:
                        break
                    
                    if self.invalidate(key):
                        excess_bytes -= entry.data_size
                        print(f"[CacheManager] Evicted for disk limit: {key}")
                        
        except Exception as e:
            print(f"[CacheManager] Error checking disk cache limits: {e}")
    
    def _optimize_memory_cache(self) -> bool:
        """Optimize memory cache performance."""
        try:
            # Remove least accessed items that are also on disk
            optimized = False
            
            with self.memory_lock:
                keys_to_remove = []
                
                for key in self.memory_cache.keys():
                    if key in self.cache_entries:
                        entry = self.cache_entries[key]
                        
                        # Remove from memory if rarely accessed and available on disk
                        if (entry.access_count < 3 and 
                            self._get_disk_cache_path(key, entry.cache_type).exists()):
                            keys_to_remove.append(key)
                
                for key in keys_to_remove[:len(keys_to_remove)//2]:  # Remove half
                    del self.memory_cache[key]
                    optimized = True
            
            return optimized
            
        except Exception as e:
            print(f"[CacheManager] Error optimizing memory cache: {e}")
            return False
    
    def _optimize_disk_cache(self) -> bool:
        """Optimize disk cache performance."""
        try:
            # Defragment cache directories and remove empty directories
            for cache_type in CacheType:
                cache_dir = self.disk_cache_path / cache_type.value
                if cache_dir.exists() and not any(cache_dir.iterdir()):
                    cache_dir.rmdir()
            
            return True
            
        except Exception as e:
            print(f"[CacheManager] Error optimizing disk cache: {e}")
            return False
    
    def _adjust_cache_strategies(self) -> bool:
        """Adjust cache strategies based on usage patterns."""
        try:
            # Analyze usage patterns and adjust strategies
            for cache_type in CacheType:
                entries_of_type = [e for e in self.cache_entries.values() if e.cache_type == cache_type]
                
                if len(entries_of_type) > 10:  # Enough data to analyze
                    avg_access_count = sum(e.access_count for e in entries_of_type) / len(entries_of_type)
                    
                    # Adjust strategy based on access patterns
                    if avg_access_count > 10:
                        # High access - use LFU
                        self.cache_strategies[cache_type] = CacheStrategy.LFU
                    elif avg_access_count < 2:
                        # Low access - use TTL
                        self.cache_strategies[cache_type] = CacheStrategy.TTL
                    else:
                        # Medium access - use LRU
                        self.cache_strategies[cache_type] = CacheStrategy.LRU
            
            return True
            
        except Exception as e:
            print(f"[CacheManager] Error adjusting cache strategies: {e}")
            return False
    
    def _optimize_prefetching(self) -> bool:
        """Optimize prefetching based on usage patterns."""
        try:
            # Identify frequently accessed apps for prefetching
            app_access_counts = {}
            
            for entry in self.cache_entries.values():
                if entry.cache_type == CacheType.APP_METADATA:
                    app_name = entry.key.replace("app_profile_", "")
                    if app_name not in app_access_counts:
                        app_access_counts[app_name] = 0
                    app_access_counts[app_name] += entry.access_count
            
            # Prefetch data for top accessed apps
            top_apps = sorted(app_access_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for app_name, access_count in top_apps:
                if access_count > 5:  # Threshold for prefetching
                    self.prefetch_app_data(app_name)
            
            return True
            
        except Exception as e:
            print(f"[CacheManager] Error optimizing prefetching: {e}")
            return False
    
    def _initialize_cache_database(self) -> None:
        """Initialize the cache database."""
        try:
            conn = sqlite3.connect(str(self.cache_db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    cache_type TEXT NOT NULL,
                    data_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    ttl_seconds INTEGER,
                    priority INTEGER DEFAULT 1,
                    metadata TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"[CacheManager] Error initializing cache database: {e}")
    
    def _save_cache_entry_to_db(self, entry: CacheEntry) -> None:
        """Save cache entry to database."""
        try:
            conn = sqlite3.connect(str(self.cache_db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO cache_entries 
                (key, cache_type, data_size, created_at, last_accessed, access_count, ttl_seconds, priority, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.key,
                entry.cache_type.value,
                entry.data_size,
                entry.created_at.isoformat(),
                entry.last_accessed.isoformat(),
                entry.access_count,
                entry.ttl_seconds,
                entry.priority,
                json.dumps(entry.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"[CacheManager] Error saving cache entry to database: {e}")
    
    def _load_existing_cache_entries(self) -> None:
        """Load existing cache entries from database."""
        try:
            if not self.cache_db_path.exists():
                return
            
            conn = sqlite3.connect(str(self.cache_db_path))
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM cache_entries')
            rows = cursor.fetchall()
            
            for row in rows:
                try:
                    entry = CacheEntry(
                        key=row[0],
                        cache_type=CacheType(row[1]),
                        data_size=row[2],
                        created_at=datetime.fromisoformat(row[3]),
                        last_accessed=datetime.fromisoformat(row[4]),
                        access_count=row[5],
                        ttl_seconds=row[6],
                        priority=row[7],
                        metadata=json.loads(row[8]) if row[8] else {}
                    )
                    
                    # Only load if not expired and disk file exists
                    if not entry.is_expired():
                        disk_file = self._get_disk_cache_path(entry.key, entry.cache_type)
                        if disk_file.exists():
                            self.cache_entries[entry.key] = entry
                        else:
                            # Remove stale database entry
                            self._remove_cache_entry_from_db(entry.key)
                    else:
                        # Remove expired entry
                        self._remove_cache_entry_from_db(entry.key)
                        
                except Exception as e:
                    print(f"[CacheManager] Error loading cache entry: {e}")
            
            conn.close()
            
        except Exception as e:
            print(f"[CacheManager] Error loading cache entries: {e}")
    
    def _update_cache_entry_in_db(self, entry: CacheEntry) -> None:
        """Update cache entry in database."""
        try:
            conn = sqlite3.connect(str(self.cache_db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE cache_entries 
                SET last_accessed = ?, access_count = ?
                WHERE key = ?
            ''', (
                entry.last_accessed.isoformat(),
                entry.access_count,
                entry.key
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"[CacheManager] Error updating cache entry: {e}")
    
    def _remove_cache_entry_from_db(self, key: str) -> None:
        """Remove cache entry from database."""
        try:
            conn = sqlite3.connect(str(self.cache_db_path))
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"[CacheManager] Error removing cache entry from database: {e}")
    
    def _start_cleanup_thread(self) -> None:
        """Start the cleanup thread."""
        if self.cleanup_thread is None or not self.cleanup_thread.is_alive():
            self.cleanup_active = True
            self.cleanup_thread = threading.Thread(
                target=self._cleanup_loop,
                daemon=True
            )
            self.cleanup_thread.start()
            print("[CacheManager] Started cache cleanup thread")
    
    def _cleanup_loop(self) -> None:
        """Main cleanup loop."""
        while self.cleanup_active:
            try:
                self.cleanup_expired_entries()
                self._check_disk_cache_limits()
                time.sleep(self.cleanup_interval)
                
            except Exception as e:
                print(f"[CacheManager] Error in cleanup loop: {e}")
                time.sleep(self.cleanup_interval)
    
    def stop_cleanup_thread(self) -> None:
        """Stop the cleanup thread."""
        self.cleanup_active = False
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5.0)
        print("[CacheManager] Stopped cache cleanup thread")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            if hasattr(self, 'cleanup_thread'):
                self.stop_cleanup_thread()
        except Exception:
            pass  # Ignore errors during cleanup


def main():
    """Test the cache manager functionality."""
    print("Testing CacheManager...")
    
    cache_manager = CacheManager()
    
    # Test basic caching
    test_data = {"test": "data", "number": 42}
    cache_manager.put("test_key", test_data, CacheType.APP_METADATA)
    
    # Test retrieval
    retrieved_data = cache_manager.get("test_key", CacheType.APP_METADATA)
    print(f"Cache test: {retrieved_data == test_data}")
    
    # Test statistics
    stats = cache_manager.get_cache_statistics()
    print(f"Cache stats: {stats['performance']['hit_rate_percent']:.1f}% hit rate")
    
    # Test cleanup
    cleaned = cache_manager.cleanup_expired_entries()
    print(f"Cleaned up {cleaned} expired entries")
    
    # Test optimization
    optimization_results = cache_manager.optimize_cache_performance()
    print(f"Optimization results: {optimization_results}")
    
    print("CacheManager test completed")


if __name__ == "__main__":
    main()