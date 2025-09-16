#!/usr/bin/env python3
"""
PinokioCloud Performance Monitor

This module monitors system performance and resource usage in real-time.
It provides comprehensive performance tracking, optimization recommendations,
and integration with all PinokioCloud systems for optimal performance.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
from collections import deque
import json

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from cloud_detection.cloud_detector import CloudDetector
from cloud_detection.resource_assessor import ResourceAssessor
from running.process_tracker import ProcessTracker
from platforms.colab_optimizer import ColabOptimizer
from platforms.vast_optimizer import VastOptimizer
from platforms.lightning_optimizer import LightningOptimizer
from environment_management.json_handler import JSONHandler


class AlertSeverity(Enum):
    """Severity levels for performance alerts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of performance metrics."""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    GPU_USAGE = "gpu_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_USAGE = "network_usage"
    PROCESS_COUNT = "process_count"
    CACHE_PERFORMANCE = "cache_performance"
    TUNNEL_PERFORMANCE = "tunnel_performance"


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    gpu_percent: float = 0.0
    gpu_memory_percent: float = 0.0
    gpu_memory_used_gb: float = 0.0
    gpu_memory_total_gb: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    process_count: int = 0
    active_apps: int = 0
    cache_hit_rate: float = 0.0
    tunnel_count: int = 0
    platform_specific: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PerformanceMetrics to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetrics':
        """Create PerformanceMetrics from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class ResourceAlert:
    """Performance alert information."""
    alert_id: str
    severity: AlertSeverity
    metric_type: MetricType
    message: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ResourceAlert to dictionary."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['metric_type'] = self.metric_type.value
        data['timestamp'] = self.timestamp.isoformat()
        data['resolution_time'] = self.resolution_time.isoformat() if self.resolution_time else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceAlert':
        """Create ResourceAlert from dictionary."""
        data['severity'] = AlertSeverity(data['severity'])
        data['metric_type'] = MetricType(data['metric_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['resolution_time'] = datetime.fromisoformat(data['resolution_time']) if data['resolution_time'] else None
        return cls(**data)


class PerformanceMonitor:
    """
    Monitors system performance and resource usage in real-time.
    
    This class provides comprehensive performance monitoring with intelligent
    alerting, optimization recommendations, and integration with all PinokioCloud systems.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the performance monitor."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.performance_storage_path = self.base_path / "performance_storage"
        self.performance_storage_path.mkdir(exist_ok=True)
        
        # Performance monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 5.0  # seconds
        
        # Metrics storage
        self.metrics_history: deque = deque(maxlen=1000)  # Keep last 1000 metrics
        self.current_metrics: Optional[PerformanceMetrics] = None
        
        # Alert system
        self.active_alerts: Dict[str, ResourceAlert] = {}
        self.alert_history: List[ResourceAlert] = []
        self.alert_thresholds = self._setup_default_thresholds()
        
        # Initialize dependencies
        self.cloud_detector = CloudDetector()
        self.resource_assessor = ResourceAssessor()
        self.process_tracker = ProcessTracker(str(self.base_path))
        self.json_handler = JSONHandler(str(self.base_path))
        
        # Platform-specific optimizers
        self.platform_info = self.cloud_detector.detect_platform()
        self.platform_optimizers = self._initialize_platform_optimizers()
        
        # Performance optimization
        self.optimization_active = False
        self.optimization_thread = None
        self.optimization_interval = 300.0  # 5 minutes
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[callable]] = {
            'alert_triggered': [],
            'alert_resolved': [],
            'performance_degraded': [],
            'optimization_applied': [],
            'threshold_exceeded': []
        }
        
        # Load existing data
        self._load_performance_history()
        
        print(f"[PerformanceMonitor] Initialized for platform: {self.platform_info.platform}")
        print(f"[PerformanceMonitor] Alert thresholds: {len(self.alert_thresholds)} configured")
    
    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            print("[PerformanceMonitor] Started performance monitoring")
        
        # Start optimization thread
        if self.optimization_thread is None or not self.optimization_thread.is_alive():
            self.optimization_active = True
            self.optimization_thread = threading.Thread(
                target=self._optimization_loop,
                daemon=True
            )
            self.optimization_thread.start()
            print("[PerformanceMonitor] Started performance optimization")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        
        self.optimization_active = False
        if self.optimization_thread and self.optimization_thread.is_alive():
            self.optimization_thread.join(timeout=5.0)
        
        print("[PerformanceMonitor] Stopped performance monitoring")
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """
        Get current performance metrics.
        
        Returns:
            Optional[PerformanceMetrics]: Current metrics if available
        """
        return self.current_metrics
    
    def get_metrics_history(self, hours: int = 1) -> List[PerformanceMetrics]:
        """
        Get performance metrics history.
        
        Args:
            hours: Number of hours of history to return
        
        Returns:
            List[PerformanceMetrics]: Historical metrics
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [metrics for metrics in self.metrics_history 
                if metrics.timestamp >= cutoff_time]
    
    def get_active_alerts(self) -> List[ResourceAlert]:
        """
        Get all active performance alerts.
        
        Returns:
            List[ResourceAlert]: List of active alerts
        """
        return [alert for alert in self.active_alerts.values() if not alert.resolved]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dict[str, Any]: Performance summary
        """
        try:
            if not self.current_metrics:
                return {'error': 'No current metrics available'}
            
            metrics = self.current_metrics
            
            # Calculate performance trends
            recent_metrics = self.get_metrics_history(1)  # Last hour
            trends = self._calculate_performance_trends(recent_metrics)
            
            # Get resource recommendations
            recommendations = self._generate_performance_recommendations()
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'current_performance': {
                    'cpu_percent': metrics.cpu_percent,
                    'memory_percent': metrics.memory_percent,
                    'disk_percent': metrics.disk_percent,
                    'gpu_percent': metrics.gpu_percent,
                    'process_count': metrics.process_count,
                    'active_apps': metrics.active_apps
                },
                'resource_usage': {
                    'memory_used_gb': metrics.memory_used_gb,
                    'memory_total_gb': metrics.memory_total_gb,
                    'disk_used_gb': metrics.disk_used_gb,
                    'disk_total_gb': metrics.disk_total_gb,
                    'gpu_memory_used_gb': metrics.gpu_memory_used_gb,
                    'gpu_memory_total_gb': metrics.gpu_memory_total_gb
                },
                'performance_trends': trends,
                'active_alerts': len(self.get_active_alerts()),
                'recommendations': recommendations,
                'platform': self.platform_info.platform.value,
                'monitoring_uptime_hours': self._get_monitoring_uptime(),
                'cache_performance': {
                    'hit_rate': metrics.cache_hit_rate,
                    'tunnel_count': metrics.tunnel_count
                }
            }
            
            return summary
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error getting performance summary: {e}")
            return {'error': str(e)}
    
    def apply_performance_optimizations(self) -> Dict[str, bool]:
        """
        Apply intelligent performance optimizations.
        
        Returns:
            Dict[str, bool]: Results of optimization operations
        """
        print("[PerformanceMonitor] Applying performance optimizations...")
        
        results = {
            'memory_optimized': False,
            'cpu_optimized': False,
            'gpu_optimized': False,
            'disk_optimized': False,
            'platform_optimized': False
        }
        
        try:
            if not self.current_metrics:
                return results
            
            metrics = self.current_metrics
            
            # 1. Memory optimization
            if metrics.memory_percent > 80.0:
                results['memory_optimized'] = self._optimize_memory_usage()
            
            # 2. CPU optimization
            if metrics.cpu_percent > 85.0:
                results['cpu_optimized'] = self._optimize_cpu_usage()
            
            # 3. GPU optimization
            if metrics.gpu_percent > 90.0:
                results['gpu_optimized'] = self._optimize_gpu_usage()
            
            # 4. Disk optimization
            if metrics.disk_percent > 85.0:
                results['disk_optimized'] = self._optimize_disk_usage()
            
            # 5. Platform-specific optimization
            results['platform_optimized'] = self._apply_platform_optimizations()
            
            # Emit event if any optimizations were applied
            if any(results.values()):
                self._emit_event('optimization_applied', results)
            
            success_count = sum(results.values())
            print(f"[PerformanceMonitor] Optimization complete: {success_count}/5 optimizations applied")
            
            return results
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error applying optimizations: {e}")
            return results
    
    def add_custom_threshold(self, metric_type: MetricType, threshold: float,
                           severity: AlertSeverity = AlertSeverity.MEDIUM) -> None:
        """
        Add a custom performance threshold.
        
        Args:
            metric_type: Type of metric to monitor
            threshold: Threshold value
            severity: Alert severity when threshold is exceeded
        """
        self.alert_thresholds[metric_type] = {
            'threshold': threshold,
            'severity': severity
        }
        print(f"[PerformanceMonitor] Added custom threshold: {metric_type.value} > {threshold}")
    
    def add_event_callback(self, event: str, callback: callable) -> None:
        """Add a callback for performance events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        try:
            # Basic system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process_count = len(psutil.pids())
            
            # GPU metrics
            gpu_percent = 0.0
            gpu_memory_percent = 0.0
            gpu_memory_used_gb = 0.0
            gpu_memory_total_gb = 0.0
            
            try:
                import pynvml
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                
                if device_count > 0:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    
                    gpu_percent = utilization.gpu
                    gpu_memory_used_gb = memory_info.used / (1024**3)
                    gpu_memory_total_gb = memory_info.total / (1024**3)
                    gpu_memory_percent = (memory_info.used / memory_info.total) * 100
                    
            except (ImportError, Exception):
                pass  # GPU monitoring not available
            
            # Get app-specific metrics
            active_apps = 0
            cache_hit_rate = 0.0
            tunnel_count = 0
            
            try:
                # This would integrate with other systems
                # For now, use basic estimates
                active_apps = max(0, process_count - 50)  # Estimate active apps
                tunnel_count = 0  # Would get from tunnel managers
            except Exception:
                pass
            
            # Platform-specific metrics
            platform_specific = {}
            try:
                if self.platform_info.platform.value == "google_colab":
                    # Get Colab-specific metrics
                    if hasattr(self, 'colab_optimizer'):
                        session_info = self.colab_optimizer.get_session_info()
                        platform_specific['colab'] = session_info
                elif self.platform_info.platform.value == "vast_ai":
                    # Get Vast.ai-specific metrics
                    if hasattr(self, 'vast_optimizer'):
                        cost_info = self.vast_optimizer.get_cost_estimate()
                        platform_specific['vast'] = cost_info
                elif self.platform_info.platform.value == "lightning_ai":
                    # Get Lightning.ai-specific metrics
                    if hasattr(self, 'lightning_optimizer'):
                        workspace_info = self.lightning_optimizer.get_lightning_workspace_info()
                        platform_specific['lightning'] = workspace_info
            except Exception:
                pass
            
            # Create metrics object
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=memory.used / (1024**3),
                memory_total_gb=memory.total / (1024**3),
                disk_percent=(disk.used / disk.total) * 100,
                disk_used_gb=disk.used / (1024**3),
                disk_total_gb=disk.total / (1024**3),
                gpu_percent=gpu_percent,
                gpu_memory_percent=gpu_memory_percent,
                gpu_memory_used_gb=gpu_memory_used_gb,
                gpu_memory_total_gb=gpu_memory_total_gb,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                process_count=process_count,
                active_apps=active_apps,
                cache_hit_rate=cache_hit_rate,
                tunnel_count=tunnel_count,
                platform_specific=platform_specific
            )
            
            return metrics
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error collecting metrics: {e}")
            return PerformanceMetrics(timestamp=datetime.now(), cpu_percent=0, memory_percent=0,
                                    memory_used_gb=0, memory_total_gb=0, disk_percent=0,
                                    disk_used_gb=0, disk_total_gb=0)
    
    def _check_performance_alerts(self, metrics: PerformanceMetrics) -> None:
        """Check for performance alerts based on current metrics."""
        try:
            current_time = datetime.now()
            
            # Check each metric against thresholds
            metric_checks = [
                (MetricType.CPU_USAGE, metrics.cpu_percent),
                (MetricType.MEMORY_USAGE, metrics.memory_percent),
                (MetricType.GPU_USAGE, metrics.gpu_percent),
                (MetricType.DISK_USAGE, metrics.disk_percent),
                (MetricType.PROCESS_COUNT, metrics.process_count)
            ]
            
            for metric_type, current_value in metric_checks:
                if metric_type in self.alert_thresholds:
                    threshold_config = self.alert_thresholds[metric_type]
                    threshold = threshold_config['threshold']
                    severity = threshold_config['severity']
                    
                    alert_key = f"{metric_type.value}_alert"
                    
                    if current_value > threshold:
                        # Threshold exceeded
                        if alert_key not in self.active_alerts or self.active_alerts[alert_key].resolved:
                            # Create new alert
                            alert = ResourceAlert(
                                alert_id=f"{alert_key}_{int(current_time.timestamp())}",
                                severity=severity,
                                metric_type=metric_type,
                                message=f"{metric_type.value.replace('_', ' ').title()} is {current_value:.1f}%, exceeding threshold of {threshold}%",
                                current_value=current_value,
                                threshold_value=threshold,
                                timestamp=current_time,
                                recommendations=self._get_recommendations_for_metric(metric_type, current_value)
                            )
                            
                            self.active_alerts[alert_key] = alert
                            self.alert_history.append(alert)
                            
                            # Emit event
                            self._emit_event('alert_triggered', alert)
                            self._emit_event('threshold_exceeded', metric_type, current_value, threshold)
                            
                            print(f"[PerformanceMonitor] Alert triggered: {alert.message}")
                        else:
                            # Update existing alert
                            alert = self.active_alerts[alert_key]
                            alert.current_value = current_value
                            alert.timestamp = current_time
                    
                    else:
                        # Threshold not exceeded, resolve alert if exists
                        if alert_key in self.active_alerts and not self.active_alerts[alert_key].resolved:
                            alert = self.active_alerts[alert_key]
                            alert.resolved = True
                            alert.resolution_time = current_time
                            
                            # Emit event
                            self._emit_event('alert_resolved', alert)
                            
                            print(f"[PerformanceMonitor] Alert resolved: {metric_type.value}")
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error checking performance alerts: {e}")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect current metrics
                metrics = self._collect_metrics()
                self.current_metrics = metrics
                
                # Add to history
                self.metrics_history.append(metrics)
                
                # Check for alerts
                self._check_performance_alerts(metrics)
                
                # Save metrics periodically
                if len(self.metrics_history) % 60 == 0:  # Every 5 minutes
                    self._save_performance_history()
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"[PerformanceMonitor] Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _optimization_loop(self) -> None:
        """Main optimization loop."""
        while self.optimization_active:
            try:
                # Apply automatic optimizations
                if self.current_metrics:
                    optimization_results = self.apply_performance_optimizations()
                    
                    if any(optimization_results.values()):
                        print(f"[PerformanceMonitor] Auto-optimization applied: {optimization_results}")
                
                time.sleep(self.optimization_interval)
                
            except Exception as e:
                print(f"[PerformanceMonitor] Error in optimization loop: {e}")
                time.sleep(self.optimization_interval)
    
    def _setup_default_thresholds(self) -> Dict[MetricType, Dict[str, Any]]:
        """Set up default performance thresholds."""
        return {
            MetricType.CPU_USAGE: {'threshold': 85.0, 'severity': AlertSeverity.HIGH},
            MetricType.MEMORY_USAGE: {'threshold': 90.0, 'severity': AlertSeverity.CRITICAL},
            MetricType.GPU_USAGE: {'threshold': 95.0, 'severity': AlertSeverity.HIGH},
            MetricType.DISK_USAGE: {'threshold': 90.0, 'severity': AlertSeverity.CRITICAL},
            MetricType.PROCESS_COUNT: {'threshold': 200, 'severity': AlertSeverity.MEDIUM}
        }
    
    def _initialize_platform_optimizers(self) -> Dict[str, Any]:
        """Initialize platform-specific optimizers."""
        optimizers = {}
        
        try:
            platform = self.platform_info.platform.value
            
            if platform == "google_colab":
                self.colab_optimizer = ColabOptimizer(str(self.base_path))
                optimizers['colab'] = self.colab_optimizer
            elif platform == "vast_ai":
                self.vast_optimizer = VastOptimizer(str(self.base_path))
                optimizers['vast'] = self.vast_optimizer
            elif platform == "lightning_ai":
                self.lightning_optimizer = LightningOptimizer(str(self.base_path))
                optimizers['lightning'] = self.lightning_optimizer
            
            return optimizers
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error initializing platform optimizers: {e}")
            return {}
    
    def _calculate_performance_trends(self, recent_metrics: List[PerformanceMetrics]) -> Dict[str, str]:
        """Calculate performance trends from recent metrics."""
        try:
            if len(recent_metrics) < 2:
                return {}
            
            # Calculate trends for key metrics
            trends = {}
            
            # CPU trend
            cpu_values = [m.cpu_percent for m in recent_metrics]
            cpu_trend = "increasing" if cpu_values[-1] > cpu_values[0] else "decreasing"
            trends['cpu'] = cpu_trend
            
            # Memory trend
            memory_values = [m.memory_percent for m in recent_metrics]
            memory_trend = "increasing" if memory_values[-1] > memory_values[0] else "decreasing"
            trends['memory'] = memory_trend
            
            # GPU trend
            gpu_values = [m.gpu_percent for m in recent_metrics]
            gpu_trend = "increasing" if gpu_values[-1] > gpu_values[0] else "decreasing"
            trends['gpu'] = gpu_trend
            
            return trends
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error calculating trends: {e}")
            return {}
    
    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        try:
            if not self.current_metrics:
                return recommendations
            
            metrics = self.current_metrics
            
            # Memory recommendations
            if metrics.memory_percent > 85.0:
                recommendations.append("Consider closing unused applications to free memory")
                recommendations.append("Enable memory optimization in cache manager")
            
            # CPU recommendations
            if metrics.cpu_percent > 80.0:
                recommendations.append("Reduce concurrent processes for better CPU performance")
                recommendations.append("Consider upgrading to a higher-tier cloud instance")
            
            # GPU recommendations
            if metrics.gpu_percent > 90.0:
                recommendations.append("Optimize GPU memory usage by reducing batch sizes")
                recommendations.append("Consider using model quantization to reduce GPU load")
            
            # Disk recommendations
            if metrics.disk_percent > 85.0:
                recommendations.append("Clean up temporary files and unused models")
                recommendations.append("Enable aggressive cache cleanup")
            
            # Platform-specific recommendations
            platform = self.platform_info.platform.value
            if platform == "google_colab" and metrics.memory_percent > 80.0:
                recommendations.append("Consider upgrading to Colab Pro for more memory")
            elif platform == "vast_ai" and metrics.gpu_percent > 85.0:
                recommendations.append("Monitor billing costs as GPU usage is high")
            
            return recommendations
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error generating recommendations: {e}")
            return []
    
    def _get_recommendations_for_metric(self, metric_type: MetricType, current_value: float) -> List[str]:
        """Get specific recommendations for a metric type."""
        recommendations = []
        
        if metric_type == MetricType.CPU_USAGE:
            recommendations.extend([
                "Reduce number of concurrent processes",
                "Optimize CPU-intensive operations",
                "Consider process scheduling optimization"
            ])
        elif metric_type == MetricType.MEMORY_USAGE:
            recommendations.extend([
                "Close unused applications",
                "Clear memory caches",
                "Restart memory-heavy processes"
            ])
        elif metric_type == MetricType.GPU_USAGE:
            recommendations.extend([
                "Reduce GPU batch sizes",
                "Optimize GPU memory allocation",
                "Use model quantization"
            ])
        elif metric_type == MetricType.DISK_USAGE:
            recommendations.extend([
                "Clean up temporary files",
                "Remove unused models",
                "Enable cache cleanup"
            ])
        
        return recommendations
    
    def _optimize_memory_usage(self) -> bool:
        """Optimize memory usage."""
        try:
            # Clear Python caches
            import gc
            gc.collect()
            
            # This would integrate with cache manager to clear memory cache
            print("[PerformanceMonitor] Applied memory optimization")
            return True
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error optimizing memory: {e}")
            return False
    
    def _optimize_cpu_usage(self) -> bool:
        """Optimize CPU usage."""
        try:
            # Set CPU affinity for better performance
            current_process = psutil.Process()
            cpu_count = psutil.cpu.cores_logical()
            
            if cpu_count > 2:
                # Use all but one CPU core
                current_process.cpu_affinity(list(range(cpu_count - 1)))
            
            print("[PerformanceMonitor] Applied CPU optimization")
            return True
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error optimizing CPU: {e}")
            return False
    
    def _optimize_gpu_usage(self) -> bool:
        """Optimize GPU usage."""
        try:
            # Set GPU memory growth if TensorFlow is available
            try:
                import tensorflow as tf
                gpus = tf.config.experimental.list_physical_devices('GPU')
                if gpus:
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    print("[PerformanceMonitor] Applied GPU memory growth optimization")
                    return True
            except ImportError:
                pass
            
            return False
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error optimizing GPU: {e}")
            return False
    
    def _optimize_disk_usage(self) -> bool:
        """Optimize disk usage."""
        try:
            # Clean up temporary directories
            temp_dirs = ["/tmp", "/var/tmp", str(self.base_path / "temp")]
            
            for temp_dir in temp_dirs:
                temp_path = Path(temp_dir)
                if temp_path.exists():
                    # Remove files older than 1 hour
                    cutoff_time = time.time() - 3600
                    
                    for file_path in temp_path.rglob("*"):
                        try:
                            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                                file_path.unlink()
                        except Exception:
                            continue
            
            print("[PerformanceMonitor] Applied disk optimization")
            return True
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error optimizing disk: {e}")
            return False
    
    def _apply_platform_optimizations(self) -> bool:
        """Apply platform-specific optimizations."""
        try:
            platform = self.platform_info.platform.value
            
            if platform == "google_colab" and hasattr(self, 'colab_optimizer'):
                results = self.colab_optimizer.optimize_for_colab()
                return any(results.values())
            elif platform == "vast_ai" and hasattr(self, 'vast_optimizer'):
                results = self.vast_optimizer.optimize_for_vast()
                return any(results.values())
            elif platform == "lightning_ai" and hasattr(self, 'lightning_optimizer'):
                results = self.lightning_optimizer.optimize_for_lightning()
                return any(results.values())
            
            return False
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error applying platform optimizations: {e}")
            return False
    
    def _get_monitoring_uptime(self) -> float:
        """Get monitoring uptime in hours."""
        try:
            if self.metrics_history:
                first_metric = self.metrics_history[0]
                uptime = datetime.now() - first_metric.timestamp
                return uptime.total_seconds() / 3600
            return 0.0
        except Exception:
            return 0.0
    
    def _save_performance_history(self) -> None:
        """Save performance history to disk."""
        try:
            history_file = self.performance_storage_path / "metrics_history.json"
            
            # Convert to serializable format
            history_data = [metrics.to_dict() for metrics in list(self.metrics_history)[-100:]]  # Last 100 entries
            
            self.json_handler.write_json_file(str(history_file), {
                'metrics': history_data,
                'saved_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"[PerformanceMonitor] Error saving performance history: {e}")
    
    def _load_performance_history(self) -> None:
        """Load performance history from disk."""
        try:
            history_file = self.performance_storage_path / "metrics_history.json"
            
            if history_file.exists():
                history_data = self.json_handler.read_json_file(str(history_file))
                
                for metric_data in history_data.get('metrics', []):
                    try:
                        metric = PerformanceMetrics.from_dict(metric_data)
                        self.metrics_history.append(metric)
                    except Exception:
                        continue
                
                print(f"[PerformanceMonitor] Loaded {len(self.metrics_history)} historical metrics")
                
        except Exception as e:
            print(f"[PerformanceMonitor] Error loading performance history: {e}")
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[PerformanceMonitor] Error in event callback: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_monitoring()


def main():
    """Test the performance monitor functionality."""
    print("Testing PerformanceMonitor...")
    
    monitor = PerformanceMonitor()
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Wait for some metrics
    time.sleep(10)
    
    # Get current metrics
    current_metrics = monitor.get_current_metrics()
    if current_metrics:
        print(f"Current CPU: {current_metrics.cpu_percent:.1f}%")
        print(f"Current Memory: {current_metrics.memory_percent:.1f}%")
        print(f"Current GPU: {current_metrics.gpu_percent:.1f}%")
    
    # Get performance summary
    summary = monitor.get_performance_summary()
    print(f"Performance summary: {len(summary)} metrics")
    
    # Get active alerts
    alerts = monitor.get_active_alerts()
    print(f"Active alerts: {len(alerts)}")
    
    # Test optimization
    optimization_results = monitor.apply_performance_optimizations()
    print(f"Optimization results: {optimization_results}")
    
    # Stop monitoring
    monitor.stop_monitoring()
    
    print("PerformanceMonitor test completed")


if __name__ == "__main__":
    main()