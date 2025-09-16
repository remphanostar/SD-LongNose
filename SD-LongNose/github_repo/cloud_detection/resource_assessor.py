#!/usr/bin/env python3
"""
PinokioCloud Resource Assessment System

This module assesses available system resources including GPU, CPU, memory, storage,
and network capabilities. Provides detailed resource information for optimization
and capacity planning.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import subprocess
import platform
import psutil
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class ResourceType(Enum):
    """Enumeration of resource types."""
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    SYSTEM = "system"


@dataclass
class CPUInfo:
    """CPU information and capabilities."""
    cores_physical: int
    cores_logical: int
    max_frequency_mhz: float
    current_frequency_mhz: float
    architecture: str
    model_name: str
    vendor: str
    cache_size_kb: int
    usage_percent: float
    load_average: Tuple[float, float, float]


@dataclass
class GPUInfo:
    """GPU information and capabilities."""
    count: int
    devices: List[Dict[str, Any]] = field(default_factory=list)
    total_memory_mb: int = 0
    available_memory_mb: int = 0
    driver_version: str = ""
    cuda_version: str = ""
    cudnn_version: str = ""


@dataclass
class MemoryInfo:
    """Memory information and usage."""
    total_gb: float
    available_gb: float
    used_gb: float
    free_gb: float
    cached_gb: float
    buffers_gb: float
    swap_total_gb: float
    swap_used_gb: float
    swap_free_gb: float
    usage_percent: float


@dataclass
class StorageInfo:
    """Storage information and usage."""
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    mount_point: str
    filesystem_type: str
    device_name: str
    read_speed_mbps: float = 0.0
    write_speed_mbps: float = 0.0


@dataclass
class NetworkInfo:
    """Network information and capabilities."""
    interfaces: List[Dict[str, Any]] = field(default_factory=list)
    public_ip: str = ""
    private_ip: str = ""
    bandwidth_mbps: float = 0.0
    latency_ms: float = 0.0
    dns_servers: List[str] = field(default_factory=list)
    can_access_internet: bool = False


@dataclass
class SystemInfo:
    """System information and capabilities."""
    platform: str
    platform_version: str
    architecture: str
    hostname: str
    kernel_version: str
    python_version: str
    uptime_seconds: float
    boot_time: float
    timezone: str
    locale: str


@dataclass
class ResourceAssessment:
    """Complete resource assessment result."""
    timestamp: float
    cpu: CPUInfo
    gpu: GPUInfo
    memory: MemoryInfo
    storage: List[StorageInfo]
    network: NetworkInfo
    system: SystemInfo
    overall_score: float
    recommendations: List[str] = field(default_factory=list)


class ResourceAssessor:
    """
    System resource assessment and analysis.
    
    Provides comprehensive analysis of system resources including:
    - CPU capabilities and usage
    - GPU availability and specifications
    - Memory usage and availability
    - Storage capacity and performance
    - Network connectivity and speed
    - System information and capabilities
    """
    
    def __init__(self):
        """Initialize the resource assessor."""
        self.assessment_cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def assess_resources(self, force_refresh: bool = False) -> ResourceAssessment:
        """
        Perform comprehensive resource assessment.
        
        Args:
            force_refresh: Force refresh of cached data
            
        Returns:
            ResourceAssessment: Complete resource assessment
        """
        cache_key = "full_assessment"
        current_time = time.time()
        
        # Check cache if not forcing refresh
        if not force_refresh and cache_key in self.assessment_cache:
            cached_data = self.assessment_cache[cache_key]
            if current_time - cached_data['timestamp'] < self.cache_duration:
                return cached_data['data']
        
        # Perform fresh assessment
        cpu_info = self._assess_cpu()
        gpu_info = self._assess_gpu()
        memory_info = self._assess_memory()
        storage_info = self._assess_storage()
        network_info = self._assess_network()
        system_info = self._assess_system()
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(
            cpu_info, gpu_info, memory_info, storage_info, network_info
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            cpu_info, gpu_info, memory_info, storage_info, network_info
        )
        
        assessment = ResourceAssessment(
            timestamp=current_time,
            cpu=cpu_info,
            gpu=gpu_info,
            memory=memory_info,
            storage=storage_info,
            network=network_info,
            system=system_info,
            overall_score=overall_score,
            recommendations=recommendations
        )
        
        # Cache the result
        self.assessment_cache[cache_key] = {
            'timestamp': current_time,
            'data': assessment
        }
        
        return assessment
    
    def _assess_cpu(self) -> CPUInfo:
        """Assess CPU capabilities and usage."""
        try:
            # Get CPU information
            cores_physical = psutil.cpu.cores_logical(logical=False)
            cores_logical = psutil.cpu.cores_logical(logical=True)
            
            # Get CPU frequency information
            cpu_freq = psutil.cpu_freq()
            max_frequency = cpu_freq.max if cpu_freq else 0.0
            current_frequency = cpu_freq.current if cpu_freq else 0.0
            
            # Get CPU usage
            usage_percent = psutil.cpu_percent(interval=1)
            
            # Get load average
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0.0, 0.0, 0.0)
            
            # Get detailed CPU information
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    model_name = "Unknown"
                    vendor = "Unknown"
                    cache_size = 0
                    
                    for line in cpuinfo.split('\n'):
                        if line.startswith('model name'):
                            model_name = line.split(':')[1].strip()
                        elif line.startswith('vendor_id'):
                            vendor = line.split(':')[1].strip()
                        elif line.startswith('cache size'):
                            cache_str = line.split(':')[1].strip()
                            if 'KB' in cache_str:
                                cache_size = int(cache_str.replace('KB', '').strip())
            except:
                model_name = platform.processor()
                vendor = "Unknown"
                cache_size = 0
            
            return CPUInfo(
                cores_physical=cores_physical or 1,
                cores_logical=cores_logical or 1,
                max_frequency_mhz=max_frequency,
                current_frequency_mhz=current_frequency,
                architecture=platform.machine(),
                model_name=model_name,
                vendor=vendor,
                cache_size_kb=cache_size,
                usage_percent=usage_percent,
                load_average=load_avg
            )
        except Exception as e:
            # Fallback to basic information
            return CPUInfo(
                cores_physical=1,
                cores_logical=1,
                max_frequency_mhz=0.0,
                current_frequency_mhz=0.0,
                architecture=platform.machine(),
                model_name=platform.processor(),
                vendor="Unknown",
                cache_size_kb=0,
                usage_percent=0.0,
                load_average=(0.0, 0.0, 0.0)
            )
    
    def _assess_gpu(self) -> GPUInfo:
        """Assess GPU capabilities and availability."""
        gpu_info = GPUInfo(count=0)
        
        try:
            # Try to get GPU information using nvidia-smi
            result = subprocess.run([
                'nvidia-smi', '--query-gpu=index,name,memory.total,memory.free,driver_version',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpu_info.count = len(lines)
                gpu_info.total_memory_mb = 0
                gpu_info.available_memory_mb = 0
                
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 5:
                            device = {
                                'index': int(parts[0]),
                                'name': parts[1],
                                'memory_total_mb': int(parts[2]),
                                'memory_free_mb': int(parts[3]),
                                'driver_version': parts[4]
                            }
                            gpu_info.devices.append(device)
                            gpu_info.total_memory_mb += device['memory_total_mb']
                            gpu_info.available_memory_mb += device['memory_free_mb']
                
                # Get CUDA version
                try:
                    cuda_result = subprocess.run([
                        'nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'
                    ], capture_output=True, text=True, timeout=5)
                    if cuda_result.returncode == 0:
                        gpu_info.driver_version = cuda_result.stdout.strip()
                except:
                    pass
                
                # Try to get CUDA version from nvcc
                try:
                    cuda_result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=5)
                    if cuda_result.returncode == 0:
                        for line in cuda_result.stdout.split('\n'):
                            if 'release' in line.lower():
                                gpu_info.cuda_version = line.strip()
                                break
                except:
                    pass
                
                # Try to get cuDNN version
                try:
                    import torch
                    if torch.cuda.is_available():
                        gpu_info.cudnn_version = str(torch.backends.cudnn.version())
                except:
                    pass
        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # GPU not available or nvidia-smi not found
            pass
        
        return gpu_info
    
    def _assess_memory(self) -> MemoryInfo:
        """Assess memory usage and availability."""
        try:
            # Get memory information
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return MemoryInfo(
                total_gb=memory.total / (1024**3),
                available_gb=memory.available / (1024**3),
                used_gb=memory.used / (1024**3),
                free_gb=memory.free / (1024**3),
                cached_gb=getattr(memory, 'cached', 0) / (1024**3),
                buffers_gb=getattr(memory, 'buffers', 0) / (1024**3),
                swap_total_gb=swap.total / (1024**3),
                swap_used_gb=swap.used / (1024**3),
                swap_free_gb=swap.free / (1024**3),
                usage_percent=memory.percent
            )
        except Exception as e:
            # Fallback to basic information
            return MemoryInfo(
                total_gb=0.0,
                available_gb=0.0,
                used_gb=0.0,
                free_gb=0.0,
                cached_gb=0.0,
                buffers_gb=0.0,
                swap_total_gb=0.0,
                swap_used_gb=0.0,
                swap_free_gb=0.0,
                usage_percent=0.0
            )
    
    def _assess_storage(self) -> List[StorageInfo]:
        """Assess storage capacity and performance."""
        storage_info = []
        
        try:
            # Get disk usage for all mount points
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    # Get filesystem information
                    device_name = partition.device
                    filesystem_type = partition.fstype
                    
                    # Test read/write speed (basic test)
                    read_speed, write_speed = self._test_disk_speed(partition.mountpoint)
                    
                    storage_info.append(StorageInfo(
                        total_gb=usage.total / (1024**3),
                        used_gb=usage.used / (1024**3),
                        free_gb=usage.free / (1024**3),
                        usage_percent=(usage.used / usage.total) * 100,
                        mount_point=partition.mountpoint,
                        filesystem_type=filesystem_type,
                        device_name=device_name,
                        read_speed_mbps=read_speed,
                        write_speed_mbps=write_speed
                    ))
                except (PermissionError, OSError):
                    # Skip inaccessible partitions
                    continue
        
        except Exception as e:
            # Fallback to basic information
            try:
                usage = psutil.disk_usage('/')
                storage_info.append(StorageInfo(
                    total_gb=usage.total / (1024**3),
                    used_gb=usage.used / (1024**3),
                    free_gb=usage.free / (1024**3),
                    usage_percent=(usage.used / usage.total) * 100,
                    mount_point='/',
                    filesystem_type='unknown',
                    device_name='unknown'
                ))
            except:
                pass
        
        return storage_info
    
    def _test_disk_speed(self, mount_point: str) -> Tuple[float, float]:
        """Test disk read/write speed."""
        try:
            test_file = os.path.join(mount_point, '.speed_test')
            test_data = b'0' * (1024 * 1024)  # 1MB test data
            
            # Test write speed
            start_time = time.time()
            with open(test_file, 'wb') as f:
                f.write(test_data)
            write_time = time.time() - start_time
            write_speed = 1.0 / write_time if write_time > 0 else 0.0
            
            # Test read speed
            start_time = time.time()
            with open(test_file, 'rb') as f:
                f.read()
            read_time = time.time() - start_time
            read_speed = 1.0 / read_time if read_time > 0 else 0.0
            
            # Clean up test file
            try:
                os.remove(test_file)
            except:
                pass
            
            return read_speed, write_speed
        
        except:
            return 0.0, 0.0
    
    def _assess_network(self) -> NetworkInfo:
        """Assess network connectivity and capabilities."""
        network_info = NetworkInfo()
        
        try:
            # Get network interfaces
            interfaces = psutil.net_if_addrs()
            for interface_name, addresses in interfaces.items():
                interface_info = {
                    'name': interface_name,
                    'addresses': [],
                    'is_up': False
                }
                
                for address in addresses:
                    interface_info['addresses'].append({
                        'family': str(address.family),
                        'address': address.address,
                        'netmask': address.netmask,
                        'broadcast': address.broadcast
                    })
                    
                    # Check if interface is up
                    try:
                        stats = psutil.net_if_stats()[interface_name]
                        interface_info['is_up'] = stats.isup
                    except:
                        pass
                
                network_info.interfaces.append(interface_info)
            
            # Get public IP
            try:
                import requests
                response = requests.get('https://api.ipify.org', timeout=5)
                if response.status_code == 200:
                    network_info.public_ip = response.text.strip()
            except:
                pass
            
            # Get private IP
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                network_info.private_ip = s.getsockname()[0]
                s.close()
            except:
                pass
            
            # Test internet connectivity
            try:
                import requests
                response = requests.get('https://www.google.com', timeout=5)
                network_info.can_access_internet = response.status_code == 200
            except:
                network_info.can_access_internet = False
            
            # Get DNS servers
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            dns_server = line.split()[1]
                            network_info.dns_servers.append(dns_server)
            except:
                pass
        
        except Exception as e:
            # Fallback to basic information
            pass
        
        return network_info
    
    def _assess_system(self) -> SystemInfo:
        """Assess system information and capabilities."""
        try:
            # Get system information
            system_platform = platform.system()
            platform_version = platform.version()
            architecture = platform.machine()
            hostname = platform.node()
            
            # Get kernel version
            try:
                kernel_version = platform.release()
            except:
                kernel_version = "Unknown"
            
            # Get Python version
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            # Get uptime
            try:
                uptime_seconds = time.time() - psutil.boot_time()
            except:
                uptime_seconds = 0.0
            
            # Get boot time
            try:
                boot_time = psutil.boot_time()
            except:
                boot_time = 0.0
            
            # Get timezone
            try:
                timezone = time.tzname[0]
            except:
                timezone = "UTC"
            
            # Get locale
            try:
                import locale
                locale_info = locale.getlocale()
                locale_str = f"{locale_info[0]}_{locale_info[1]}" if locale_info[0] else "C"
            except:
                locale_str = "C"
            
            return SystemInfo(
                platform=system_platform,
                platform_version=platform_version,
                architecture=architecture,
                hostname=hostname,
                kernel_version=kernel_version,
                python_version=python_version,
                uptime_seconds=uptime_seconds,
                boot_time=boot_time,
                timezone=timezone,
                locale=locale_str
            )
        
        except Exception as e:
            # Fallback to basic information
            return SystemInfo(
                platform=platform.system(),
                platform_version=platform.version(),
                architecture=platform.machine(),
                hostname=platform.node(),
                kernel_version="Unknown",
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                uptime_seconds=0.0,
                boot_time=0.0,
                timezone="UTC",
                locale="C"
            )
    
    def _calculate_overall_score(self, cpu: CPUInfo, gpu: GPUInfo, memory: MemoryInfo, 
                                storage: List[StorageInfo], network: NetworkInfo) -> float:
        """Calculate overall system performance score."""
        score = 0.0
        
        # CPU score (0-25 points)
        cpu_score = min(25, (cpu.cores_logical * 2) + (cpu.usage_percent < 80 and 5 or 0))
        score += cpu_score
        
        # GPU score (0-25 points)
        gpu_score = min(25, gpu.count * 10 + (gpu.total_memory_mb > 8000 and 5 or 0))
        score += gpu_score
        
        # Memory score (0-20 points)
        memory_score = min(20, (memory.total_gb * 2) + (memory.usage_percent < 80 and 5 or 0))
        score += memory_score
        
        # Storage score (0-15 points)
        if storage:
            main_storage = storage[0]  # Use first storage device
            storage_score = min(15, (main_storage.total_gb / 10) + (main_storage.usage_percent < 80 and 5 or 0))
            score += storage_score
        
        # Network score (0-15 points)
        network_score = 5  # Base score
        if network.can_access_internet:
            network_score += 5
        if network.public_ip:
            network_score += 5
        score += min(15, network_score)
        
        return min(100, score)
    
    def _generate_recommendations(self, cpu: CPUInfo, gpu: GPUInfo, memory: MemoryInfo,
                                 storage: List[StorageInfo], network: NetworkInfo) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # CPU recommendations
        if cpu.usage_percent > 80:
            recommendations.append("High CPU usage detected. Consider reducing concurrent processes.")
        if cpu.cores_logical < 4:
            recommendations.append("Limited CPU cores available. Optimize for single-threaded performance.")
        
        # GPU recommendations
        if gpu.count == 0:
            recommendations.append("No GPU detected. CPU-only mode will be used.")
        elif gpu.available_memory_mb < 4000:
            recommendations.append("Limited GPU memory available. Consider using smaller models.")
        
        # Memory recommendations
        if memory.usage_percent > 80:
            recommendations.append("High memory usage detected. Consider freeing up memory.")
        if memory.total_gb < 8:
            recommendations.append("Limited system memory. Consider using memory-efficient models.")
        
        # Storage recommendations
        if storage:
            main_storage = storage[0]
            if main_storage.usage_percent > 80:
                recommendations.append("High disk usage detected. Consider cleaning up temporary files.")
            if main_storage.free_gb < 10:
                recommendations.append("Low disk space available. Consider freeing up storage.")
        
        # Network recommendations
        if not network.can_access_internet:
            recommendations.append("No internet connectivity detected. Some features may be limited.")
        
        return recommendations
    
    def get_resource_summary(self, assessment: ResourceAssessment) -> str:
        """Get a human-readable summary of resource assessment."""
        summary = f"Resource Assessment Summary (Score: {assessment.overall_score:.1f}/100)\n"
        summary += f"Timestamp: {time.ctime(assessment.timestamp)}\n\n"
        
        # CPU Summary
        summary += f"CPU: {assessment.cpu.cores_logical} cores, {assessment.cpu.usage_percent:.1f}% usage\n"
        summary += f"  Model: {assessment.cpu.model_name}\n"
        summary += f"  Architecture: {assessment.cpu.architecture}\n"
        
        # GPU Summary
        if assessment.gpu.count > 0:
            summary += f"GPU: {assessment.gpu.count} device(s), {assessment.gpu.total_memory_mb}MB total\n"
            for i, device in enumerate(assessment.gpu.devices):
                summary += f"  Device {i}: {device['name']}, {device['memory_free_mb']}MB free\n"
        else:
            summary += "GPU: No GPU detected\n"
        
        # Memory Summary
        summary += f"Memory: {assessment.memory.total_gb:.1f}GB total, {assessment.memory.usage_percent:.1f}% used\n"
        summary += f"  Available: {assessment.memory.available_gb:.1f}GB\n"
        
        # Storage Summary
        if assessment.storage:
            main_storage = assessment.storage[0]
            summary += f"Storage: {main_storage.total_gb:.1f}GB total, {main_storage.usage_percent:.1f}% used\n"
            summary += f"  Free: {main_storage.free_gb:.1f}GB\n"
        
        # Network Summary
        summary += f"Network: {'Connected' if assessment.network.can_access_internet else 'No internet'}\n"
        if assessment.network.public_ip:
            summary += f"  Public IP: {assessment.network.public_ip}\n"
        
        # Recommendations
        if assessment.recommendations:
            summary += "\nRecommendations:\n"
            for rec in assessment.recommendations:
                summary += f"  - {rec}\n"
        
        return summary


def main():
    """Main function for testing resource assessment."""
    assessor = ResourceAssessor()
    assessment = assessor.assess_resources()
    
    print(assessor.get_resource_summary(assessment))
    
    # Return assessment as JSON for programmatic use
    return {
        'timestamp': assessment.timestamp,
        'overall_score': assessment.overall_score,
        'cpu': {
            'cores_logical': assessment.cpu.cores_logical,
            'usage_percent': assessment.cpu.usage_percent,
            'model_name': assessment.cpu.model_name
        },
        'gpu': {
            'count': assessment.gpu.count,
            'total_memory_mb': assessment.gpu.total_memory_mb,
            'available_memory_mb': assessment.gpu.available_memory_mb
        },
        'memory': {
            'total_gb': assessment.memory.total_gb,
            'usage_percent': assessment.memory.usage_percent,
            'available_gb': assessment.memory.available_gb
        },
        'storage': [
            {
                'total_gb': s.total_gb,
                'usage_percent': s.usage_percent,
                'free_gb': s.free_gb,
                'mount_point': s.mount_point
            } for s in assessment.storage
        ],
        'network': {
            'can_access_internet': assessment.network.can_access_internet,
            'public_ip': assessment.network.public_ip
        },
        'recommendations': assessment.recommendations
    }


if __name__ == "__main__":
    main()