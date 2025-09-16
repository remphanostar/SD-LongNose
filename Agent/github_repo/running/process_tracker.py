#!/usr/bin/env python3
"""
PinokioCloud Process Tracker

This module tracks all running processes and their resource usage. It provides
comprehensive monitoring of system resources, process health, and performance metrics
for all Pinokio applications.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from cloud_detection.cloud_detector import CloudDetector
from cloud_detection.resource_assessor import ResourceAssessor


class ProcessStatus(Enum):
    """Enumeration of process statuses."""
    RUNNING = "running"
    SLEEPING = "sleeping"
    DISK_SLEEP = "disk_sleep"
    STOPPED = "stopped"
    TRACING_STOP = "tracing_stop"
    ZOMBIE = "zombie"
    DEAD = "dead"
    WAKE_KILL = "wake_kill"
    WAKING = "waking"
    IDLE = "idle"
    LOCKED = "locked"
    WAITING = "waiting"
    UNKNOWN = "unknown"


@dataclass
class ResourceUsage:
    """Resource usage information for a process."""
    pid: int
    cpu_percent: float
    memory_rss: int  # Resident Set Size in bytes
    memory_vms: int  # Virtual Memory Size in bytes
    memory_percent: float
    num_threads: int
    num_fds: int  # File descriptors
    io_read_count: int
    io_write_count: int
    io_read_bytes: int
    io_write_bytes: int
    gpu_memory_used: int = 0  # GPU memory in bytes
    gpu_utilization: float = 0.0  # GPU utilization percentage
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ResourceUsage to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceUsage':
        """Create ResourceUsage from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ProcessInfo:
    """Detailed information about a tracked process."""
    pid: int
    ppid: int  # Parent process ID
    name: str
    cmdline: List[str]
    status: ProcessStatus
    username: str
    create_time: datetime
    cwd: str
    exe: str
    app_name: Optional[str] = None
    children_pids: List[int] = field(default_factory=list)
    resource_history: deque = field(default_factory=lambda: deque(maxlen=100))
    last_update: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ProcessInfo to dictionary."""
        data = asdict(self)
        data['create_time'] = self.create_time.isoformat()
        data['last_update'] = self.last_update.isoformat()
        data['status'] = self.status.value
        data['resource_history'] = [r.to_dict() for r in self.resource_history]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessInfo':
        """Create ProcessInfo from dictionary."""
        data['create_time'] = datetime.fromisoformat(data['create_time'])
        data['last_update'] = datetime.fromisoformat(data['last_update'])
        data['status'] = ProcessStatus(data['status'])
        data['resource_history'] = deque(
            [ResourceUsage.from_dict(r) for r in data['resource_history']],
            maxlen=100
        )
        return cls(**data)


class ProcessTracker:
    """
    Tracks all running processes and their resource usage.
    
    This class provides comprehensive process monitoring with resource usage tracking,
    performance metrics, and integration with cloud platform resource limits.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the process tracker."""
        self.base_path = base_path
        self.tracked_processes: Dict[int, ProcessInfo] = {}
        self.app_processes: Dict[str, Set[int]] = defaultdict(set)
        self.process_lock = threading.RLock()
        
        # Monitoring configuration
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 2.0  # seconds
        self.history_retention = timedelta(hours=24)
        
        # Resource limits and thresholds
        self.cpu_threshold = 90.0  # CPU usage threshold
        self.memory_threshold = 90.0  # Memory usage threshold
        self.disk_threshold = 90.0  # Disk usage threshold
        
        # Cloud platform integration
        self.cloud_detector = CloudDetector()
        self.resource_assessor = ResourceAssessor()
        self.platform_info = self.cloud_detector.detect_platform()
        self.system_resources = self.resource_assessor.assess_resources()
        
        # Performance metrics
        self.system_metrics: Dict[str, Any] = {}
        self.alert_callbacks: List[callable] = []
        
        # GPU monitoring (if available)
        self.gpu_available = self._check_gpu_availability()
        
        print(f"[ProcessTracker] Initialized for platform: {self.platform_info.platform}")
        print(f"[ProcessTracker] System resources: CPU={self.system_resources.cpu.cores_logical}, "
              f"RAM={self.system_resources.memory.total_gb:.1f}GB, "
              f"GPU={self.gpu_available}")
    
    def track_process(self, pid: int, app_name: str) -> None:
        """
        Start tracking a specific process.
        
        Args:
            pid: Process ID to track
            app_name: Name of the application this process belongs to
        """
        with self.process_lock:
            try:
                process = psutil.Process(pid)
                
                # Create process info
                process_info = ProcessInfo(
                    pid=pid,
                    ppid=process.ppid(),
                    name=process.name(),
                    cmdline=process.cmdline(),
                    status=ProcessStatus(process.status()),
                    username=process.username(),
                    create_time=datetime.fromtimestamp(process.create_time()),
                    cwd=process.cwd(),
                    exe=process.exe(),
                    app_name=app_name
                )
                
                # Track child processes
                try:
                    children = process.children(recursive=True)
                    process_info.children_pids = [child.pid for child in children]
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                # Add to tracking
                self.tracked_processes[pid] = process_info
                self.app_processes[app_name].add(pid)
                
                # Start monitoring if not already active
                if not self.monitoring_active:
                    self.start_monitoring()
                
                print(f"[ProcessTracker] Started tracking PID {pid} for app {app_name}")
                
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"[ProcessTracker] Cannot track PID {pid}: {e}")
                raise
    
    def untrack_process(self, pid: int) -> bool:
        """
        Stop tracking a specific process.
        
        Args:
            pid: Process ID to stop tracking
        
        Returns:
            bool: True if successfully untracked
        """
        with self.process_lock:
            if pid not in self.tracked_processes:
                return False
            
            process_info = self.tracked_processes[pid]
            app_name = process_info.app_name
            
            # Remove from tracking
            del self.tracked_processes[pid]
            
            if app_name and pid in self.app_processes[app_name]:
                self.app_processes[app_name].discard(pid)
                if not self.app_processes[app_name]:
                    del self.app_processes[app_name]
            
            print(f"[ProcessTracker] Stopped tracking PID {pid}")
            return True
    
    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """
        Get detailed information about a tracked process.
        
        Args:
            pid: Process ID
        
        Returns:
            Optional[ProcessInfo]: Process information if tracked
        """
        return self.tracked_processes.get(pid)
    
    def get_app_processes(self, app_name: str) -> List[ProcessInfo]:
        """
        Get all processes for a specific application.
        
        Args:
            app_name: Name of the application
        
        Returns:
            List[ProcessInfo]: List of processes for the application
        """
        app_pids = self.app_processes.get(app_name, set())
        return [self.tracked_processes[pid] for pid in app_pids 
                if pid in self.tracked_processes]
    
    def monitor_resources(self, pid: int) -> Optional[ResourceUsage]:
        """
        Get current resource usage for a specific process.
        
        Args:
            pid: Process ID
        
        Returns:
            Optional[ResourceUsage]: Current resource usage
        """
        try:
            process = psutil.Process(pid)
            
            # Get CPU and memory info
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # Get I/O info
            try:
                io_counters = process.io_counters()
                io_read_count = io_counters.read_count
                io_write_count = io_counters.write_count
                io_read_bytes = io_counters.read_bytes
                io_write_bytes = io_counters.write_bytes
            except (AttributeError, psutil.AccessDenied):
                io_read_count = io_write_count = 0
                io_read_bytes = io_write_bytes = 0
            
            # Get file descriptors count
            try:
                num_fds = process.num_fds()
            except (AttributeError, psutil.AccessDenied):
                num_fds = 0
            
            # Create resource usage object
            resource_usage = ResourceUsage(
                pid=pid,
                cpu_percent=cpu_percent,
                memory_rss=memory_info.rss,
                memory_vms=memory_info.vms,
                memory_percent=memory_percent,
                num_threads=process.num_threads(),
                num_fds=num_fds,
                io_read_count=io_read_count,
                io_write_count=io_write_count,
                io_read_bytes=io_read_bytes,
                io_write_bytes=io_write_bytes
            )
            
            # Add GPU monitoring if available
            if self.gpu_available:
                gpu_info = self._get_gpu_usage(pid)
                resource_usage.gpu_memory_used = gpu_info.get('memory_used', 0)
                resource_usage.gpu_utilization = gpu_info.get('utilization', 0.0)
            
            # Add network monitoring
            network_info = self._get_network_usage(pid)
            resource_usage.network_bytes_sent = network_info.get('bytes_sent', 0)
            resource_usage.network_bytes_recv = network_info.get('bytes_recv', 0)
            
            return resource_usage
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def get_all_tracked_processes(self) -> Dict[int, ProcessInfo]:
        """
        Get all tracked processes.
        
        Returns:
            Dict[int, ProcessInfo]: Dictionary of all tracked processes
        """
        with self.process_lock:
            return self.tracked_processes.copy()
    
    def cleanup_dead_processes(self) -> List[int]:
        """
        Remove dead processes from tracking.
        
        Returns:
            List[int]: List of PIDs that were cleaned up
        """
        dead_pids = []
        
        with self.process_lock:
            for pid in list(self.tracked_processes.keys()):
                try:
                    process = psutil.Process(pid)
                    if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
                        dead_pids.append(pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    dead_pids.append(pid)
            
            # Remove dead processes
            for pid in dead_pids:
                self.untrack_process(pid)
        
        if dead_pids:
            print(f"[ProcessTracker] Cleaned up {len(dead_pids)} dead processes")
        
        return dead_pids
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get current system-wide metrics.
        
        Returns:
            Dict[str, Any]: System metrics
        """
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu.cores_logical()
        cpu_freq = psutil.cpu_freq()
        
        # Memory usage
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk usage
        disk_usage = psutil.disk_usage('/')
        
        # Network stats
        network = psutil.net_io_counters()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'frequency': cpu_freq.current if cpu_freq else None
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free
            },
            'swap': {
                'total': swap.total,
                'used': swap.used,
                'free': swap.free,
                'percent': swap.percent
            },
            'disk': {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': (disk_usage.used / disk_usage.total) * 100
            },
            'network': {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            },
            'processes': {
                'total': len(psutil.pids()),
                'tracked': len(self.tracked_processes)
            }
        }
        
        # Add GPU metrics if available
        if self.gpu_available:
            metrics['gpu'] = self._get_system_gpu_usage()
        
        # Update stored metrics
        self.system_metrics = metrics
        
        return metrics
    
    def get_resource_alerts(self) -> List[Dict[str, Any]]:
        """
        Get current resource alerts based on thresholds.
        
        Returns:
            List[Dict[str, Any]]: List of active alerts
        """
        alerts = []
        metrics = self.get_system_metrics()
        
        # CPU alert
        if metrics['cpu']['percent'] > self.cpu_threshold:
            alerts.append({
                'type': 'cpu',
                'severity': 'high',
                'message': f"High CPU usage: {metrics['cpu']['percent']:.1f}%",
                'threshold': self.cpu_threshold,
                'current': metrics['cpu']['percent'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Memory alert
        if metrics['memory']['percent'] > self.memory_threshold:
            alerts.append({
                'type': 'memory',
                'severity': 'high',
                'message': f"High memory usage: {metrics['memory']['percent']:.1f}%",
                'threshold': self.memory_threshold,
                'current': metrics['memory']['percent'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Disk alert
        if metrics['disk']['percent'] > self.disk_threshold:
            alerts.append({
                'type': 'disk',
                'severity': 'high',
                'message': f"High disk usage: {metrics['disk']['percent']:.1f}%",
                'threshold': self.disk_threshold,
                'current': metrics['disk']['percent'],
                'timestamp': datetime.now().isoformat()
            })
        
        # Process-specific alerts
        for pid, process_info in self.tracked_processes.items():
            if process_info.resource_history:
                latest_usage = process_info.resource_history[-1]
                
                # High CPU usage for individual process
                if latest_usage.cpu_percent > 80.0:
                    alerts.append({
                        'type': 'process_cpu',
                        'severity': 'medium',
                        'message': f"Process {process_info.app_name or process_info.name} "
                                 f"(PID {pid}) high CPU: {latest_usage.cpu_percent:.1f}%",
                        'pid': pid,
                        'app_name': process_info.app_name,
                        'current': latest_usage.cpu_percent,
                        'timestamp': datetime.now().isoformat()
                    })
                
                # High memory usage for individual process
                if latest_usage.memory_percent > 50.0:
                    alerts.append({
                        'type': 'process_memory',
                        'severity': 'medium',
                        'message': f"Process {process_info.app_name or process_info.name} "
                                 f"(PID {pid}) high memory: {latest_usage.memory_percent:.1f}%",
                        'pid': pid,
                        'app_name': process_info.app_name,
                        'current': latest_usage.memory_percent,
                        'timestamp': datetime.now().isoformat()
                    })
        
        return alerts
    
    def start_monitoring(self) -> None:
        """Start the monitoring thread."""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            print("[ProcessTracker] Started resource monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring thread."""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        print("[ProcessTracker] Stopped resource monitoring")
    
    def add_alert_callback(self, callback: callable) -> None:
        """Add a callback for resource alerts."""
        self.alert_callbacks.append(callback)
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Clean up dead processes
                self.cleanup_dead_processes()
                
                # Update resource usage for all tracked processes
                with self.process_lock:
                    for pid, process_info in self.tracked_processes.items():
                        resource_usage = self.monitor_resources(pid)
                        if resource_usage:
                            process_info.resource_history.append(resource_usage)
                            process_info.last_update = datetime.now()
                
                # Check for alerts
                alerts = self.get_resource_alerts()
                if alerts:
                    for callback in self.alert_callbacks:
                        try:
                            callback(alerts)
                        except Exception as e:
                            print(f"[ProcessTracker] Error in alert callback: {e}")
                
                # Clean up old history
                self._cleanup_old_history()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"[ProcessTracker] Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _cleanup_old_history(self) -> None:
        """Clean up old resource usage history."""
        cutoff_time = datetime.now() - self.history_retention
        
        for process_info in self.tracked_processes.values():
            # Remove old entries from history
            while (process_info.resource_history and 
                   process_info.resource_history[0].timestamp < cutoff_time):
                process_info.resource_history.popleft()
    
    def _check_gpu_availability(self) -> bool:
        """Check if GPU monitoring is available."""
        try:
            import pynvml
            pynvml.nvmlInit()
            return True
        except (ImportError, Exception):
            return False
    
    def _get_gpu_usage(self, pid: int) -> Dict[str, Any]:
        """Get GPU usage for a specific process."""
        if not self.gpu_available:
            return {}
        
        try:
            import pynvml
            
            device_count = pynvml.nvmlDeviceGetCount()
            total_memory = 0
            total_utilization = 0.0
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # Get processes running on this GPU
                try:
                    processes = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
                    for proc in processes:
                        if proc.pid == pid:
                            total_memory += proc.usedGpuMemory
                except:
                    pass
                
                # Get GPU utilization
                try:
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    total_utilization += utilization.gpu
                except:
                    pass
            
            return {
                'memory_used': total_memory,
                'utilization': total_utilization / device_count if device_count > 0 else 0.0
            }
            
        except Exception:
            return {}
    
    def _get_system_gpu_usage(self) -> Dict[str, Any]:
        """Get system-wide GPU usage."""
        if not self.gpu_available:
            return {}
        
        try:
            import pynvml
            
            device_count = pynvml.nvmlDeviceGetCount()
            gpus = []
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # Get memory info
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                # Get utilization
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                # Get temperature
                try:
                    temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except:
                    temperature = None
                
                gpus.append({
                    'index': i,
                    'memory_total': memory_info.total,
                    'memory_used': memory_info.used,
                    'memory_free': memory_info.free,
                    'memory_percent': (memory_info.used / memory_info.total) * 100,
                    'utilization': utilization.gpu,
                    'temperature': temperature
                })
            
            return {'devices': gpus, 'count': device_count}
            
        except Exception:
            return {}
    
    def _get_network_usage(self, pid: int) -> Dict[str, Any]:
        """Get network usage for a specific process."""
        try:
            process = psutil.Process(pid)
            connections = process.connections()
            
            # This is a simplified approach - full network monitoring per process
            # would require more complex system-level monitoring
            return {
                'connections': len(connections),
                'bytes_sent': 0,  # Would need system-level monitoring
                'bytes_recv': 0   # Would need system-level monitoring
            }
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_monitoring()


def main():
    """Test the process tracker functionality."""
    print("Testing ProcessTracker...")
    
    tracker = ProcessTracker()
    
    # Get system metrics
    metrics = tracker.get_system_metrics()
    print(f"System CPU: {metrics['cpu']['percent']:.1f}%")
    print(f"System Memory: {metrics['memory']['percent']:.1f}%")
    print(f"System Disk: {metrics['disk']['percent']:.1f}%")
    
    # Test tracking current process
    current_pid = os.getpid()
    tracker.track_process(current_pid, "test_app")
    
    # Monitor for a few seconds
    time.sleep(5)
    
    # Get process info
    process_info = tracker.get_process_info(current_pid)
    if process_info:
        print(f"Tracked process: {process_info.name} (PID: {process_info.pid})")
        if process_info.resource_history:
            latest = process_info.resource_history[-1]
            print(f"CPU: {latest.cpu_percent:.1f}%, Memory: {latest.memory_percent:.1f}%")
    
    # Check for alerts
    alerts = tracker.get_resource_alerts()
    print(f"Active alerts: {len(alerts)}")
    
    # Cleanup
    tracker.stop_monitoring()
    print("ProcessTracker test completed")


if __name__ == "__main__":
    main()