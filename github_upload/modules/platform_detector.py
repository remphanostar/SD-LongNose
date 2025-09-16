"""Platform Detection Module for Pinokio Cloud GPU Deployment
"""

import os
import sys
import subprocess
import requests
import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from functools import wraps


def retry_on_failure(max_attempts=3, delay=1, backoff=2):
    """Decorator for retrying functions on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        logging.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    logging.warning(f"{func.__name__} attempt {attempt} failed: {e}. Retrying...")
                    time.sleep(delay * (backoff ** (attempt - 1)))
                    attempt += 1
            return None
        return wrapper
    return decorator


class PlatformDetector:
    """Detects cloud platform and configures paths for Pinokio deployment"""
    
    PLATFORM_MARKERS = {
        'colab': ['COLAB_GPU', 'COLAB_TPU_ADDR'],
        'kaggle': ['KAGGLE_URL_BASE', 'KAGGLE_KERNEL_RUN_TYPE'],
        'paperspace': ['PAPERSPACE_CLUSTER_ID', 'PS_API_KEY'],
        'runpod': ['RUNPOD_POD_ID', 'RUNPOD_API_KEY'],
        'vastai': ['VAST_CONTAINERLABEL'],
        'lightning': ['LIGHTNING_CLOUD_URL', 'LIGHTNING_GRID_URL'],
        'sagemaker': ['SM_TRAINING_ENV', 'AWS_SAGEMAKER_JOB_NAME'],
        'azure': ['AZUREML_RUN_ID', 'AZUREML_EXPERIMENT_NAME']
    }
    
    def __init__(self, config_path: Optional[str] = None, logger: Optional[logging.Logger] = None):
        self.platform = None
        self.pinokio_path = None
        self.data_path = None
        self.is_gpu_available = False
        self.gpu_info = {}
        self.config = {}
        self.logger = logger or self._setup_logger()
        
        # Load configuration if provided
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
    
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger('PlatformDetector')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def load_config(self, config_path: str) -> bool:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
            self.logger.info(f"Loaded configuration from {config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            return False
        
    def detect_platform(self) -> str:
        """Automatically detect the cloud platform with multiple detection methods"""
        # Check for forced platform from environment or config
        platform = os.environ.get('FORCE_PLATFORM') or self.config.get('platform')
        if platform:
            self.logger.info(f"Using forced platform: {platform}")
            self.platform = platform
            return platform
        
        # Try multiple detection methods
        detection_methods = [
            self._detect_by_cloud_library,
            self._detect_by_env_vars,
            self._detect_by_filesystem,
            self._detect_by_metadata_endpoints
        ]
        
        for method in detection_methods:
            try:
                platform = method()
                if platform and platform != "unknown":
                    self.logger.info(f"Platform detected by {method.__name__}: {platform}")
                    self.platform = platform
                    return platform
            except Exception as e:
                self.logger.debug(f"Detection method {method.__name__} failed: {e}")
        
        # Default to unknown
        self.logger.warning("Could not detect platform, using 'unknown'")
        self.platform = "unknown"
        return "unknown"
    
    def _detect_by_cloud_library(self) -> Optional[str]:
        """Detect using cloud-detect library"""
        try:
            from cloud_detect import provider
            detected = provider()
            if detected:
                return detected.lower()
        except ImportError:
            self.logger.debug("cloud-detect library not available")
        except Exception as e:
            self.logger.debug(f"cloud-detect failed: {e}")
        return None
    
    def _detect_by_env_vars(self) -> Optional[str]:
        """Detect by checking environment variables"""
        for platform, env_vars in self.PLATFORM_MARKERS.items():
            if any(var in os.environ for var in env_vars):
                return platform
        return None
    
    def _detect_by_filesystem(self) -> Optional[str]:
        """Detect by checking filesystem markers"""
        # Override: If we're on Windows, always return 'local'
        if os.name == 'nt':
            return 'local'
            
        # Check for Google Colab directory structure
        if os.path.exists('/content') and os.path.exists('/usr/local/bin'):
            return 'colab'
        
        # Check for Kaggle structure  
        if os.path.exists('/kaggle'):
            return 'kaggle'
            
        # Check for common cloud patterns
        if os.path.exists('/workspace'):
            return 'paperspace'
            
        return 'local'
    
    @retry_on_failure(max_attempts=2, delay=0.5)
    def _detect_by_metadata_endpoints(self) -> Optional[str]:
        """Detect by querying cloud metadata endpoints"""
        metadata_endpoints = [
            ("http://metadata.google.internal", {"Metadata-Flavor": "Google"}, "gcp"),
            ("http://169.254.169.254/latest/meta-data/", {}, "aws"),
            ("http://169.254.169.254/metadata/instance", {"Metadata": "true"}, "azure")
        ]
        
        for url, headers, platform in metadata_endpoints:
            try:
                resp = requests.get(url, headers=headers, timeout=0.5)
                if resp.status_code == 200:
                    return platform
            except requests.RequestException:
                continue
        return None
    
    def setup_paths(self, platform: str = None) -> Dict[str, str]:
        """Setup dynamic file paths based on platform"""
        if platform is None:
            platform = self.platform or self.detect_platform()
        
        paths = {}
        
        # Platform-specific path configuration
        if platform == "colab":
            paths['data'] = "/content"
            paths['pinokio'] = "/content/pinokio"
            paths['persistent'] = "/content/drive/MyDrive/pinokio"
        elif platform == "kaggle":
            paths['data'] = "/kaggle/working"
            paths['pinokio'] = "/kaggle/working/pinokio"
            paths['persistent'] = "/kaggle/working/pinokio_persistent"
        elif platform == "paperspace":
            paths['data'] = "/notebooks"
            paths['pinokio'] = "/notebooks/pinokio"
            paths['persistent'] = "/storage/pinokio"
        elif platform == "digitalocean":
            paths['data'] = "/notebooks"
            paths['pinokio'] = "/notebooks/pinokio"
            paths['persistent'] = "/notebooks/pinokio_persistent"
        elif platform == "lightning":
            paths['data'] = "/teamspace/studios/this_studio"
            paths['pinokio'] = "/teamspace/studios/this_studio/pinokio"
            paths['persistent'] = "/teamspace/studios/this_studio/pinokio_persistent"
        elif platform == "runpod":
            paths['data'] = "/workspace"
            paths['pinokio'] = "/workspace/pinokio"
            paths['persistent'] = "/workspace/pinokio_persistent"
        elif platform == "vastai":
            paths['data'] = "/workspace"
            paths['pinokio'] = "/workspace/pinokio"
            paths['persistent'] = "/workspace/pinokio_persistent"
        else:
            # Default paths
            home = os.path.expanduser("~")
            paths['data'] = home
            paths['pinokio'] = os.path.join(home, "pinokio")
            paths['persistent'] = os.path.join(home, "pinokio_persistent")
        
        self.pinokio_path = paths['pinokio']
        self.data_path = paths['data']
        
        return paths
    
    @retry_on_failure(max_attempts=2, delay=1)
    def detect_gpu(self) -> Dict:
        """Detect GPU availability and specifications with comprehensive checks"""
        gpu_info = {
            'available': False,
            'cuda_available': False,
            'devices': [],
            'driver_version': None,
            'cuda_version': None,
            'total_memory': 0
        }
        
        # Check NVIDIA GPU with extended query
        try:
            query_fields = 'name,memory.total,memory.free,utilization.gpu,driver_version'
            result = subprocess.run(
                ['nvidia-smi', f'--query-gpu={query_fields}', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=10,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='')
            )
            
            if result.returncode == 0:
                gpu_info['available'] = True
                total_memory_mb = 0
                
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 2:
                            device = {
                                'name': parts[0],
                                'memory_total': f"{parts[1]} MiB",
                                'memory_free': f"{parts[2]} MiB" if len(parts) > 2 else 'Unknown',
                                'utilization': f"{parts[3]}%" if len(parts) > 3 else '0%'
                            }
                            gpu_info['devices'].append(device)
                            
                            try:
                                total_memory_mb += float(parts[1])
                            except (ValueError, IndexError):
                                pass
                            
                            if len(parts) > 4 and not gpu_info['driver_version']:
                                gpu_info['driver_version'] = parts[4]
                
                gpu_info['total_memory'] = f"{total_memory_mb:.0f} MiB"
                self.logger.info(f"Detected {len(gpu_info['devices'])} NVIDIA GPU(s)")
                
        except FileNotFoundError:
            self.logger.debug("nvidia-smi not found")
        except subprocess.TimeoutExpired:
            self.logger.warning("nvidia-smi timed out")
        except Exception as e:
            self.logger.debug(f"Error detecting NVIDIA GPU: {e}")
        
        # Check CUDA
        try:
            result = subprocess.run(
                ['nvcc', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                gpu_info['cuda_available'] = True
                output = result.stdout
                if 'release' in output:
                    version_line = [l for l in output.split('\n') if 'release' in l][0]
                    version = version_line.split('release ')[-1].split(',')[0]
                    gpu_info['cuda_version'] = version
                    self.logger.info(f"CUDA version: {version}")
        except FileNotFoundError:
            self.logger.debug("nvcc not found")
        except Exception as e:
            self.logger.debug(f"Error checking CUDA: {e}")
        
        # Check PyTorch CUDA availability
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info['cuda_available'] = True
                gpu_info['pytorch_cuda'] = torch.version.cuda
                gpu_info['pytorch_device_count'] = torch.cuda.device_count()
                self.logger.info(f"PyTorch CUDA available: {torch.version.cuda}")
        except ImportError:
            self.logger.debug("PyTorch not installed")
        except Exception as e:
            self.logger.debug(f"Error checking PyTorch CUDA: {e}")
        
        # Check TensorFlow GPU availability
        try:
            import tensorflow as tf
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                gpu_info['tensorflow_gpus'] = len(gpus)
                self.logger.info(f"TensorFlow detected {len(gpus)} GPU(s)")
        except ImportError:
            self.logger.debug("TensorFlow not installed")
        except Exception as e:
            self.logger.debug(f"Error checking TensorFlow GPU: {e}")
        
        self.is_gpu_available = gpu_info['available']
        self.gpu_info = gpu_info
        
        return gpu_info
    
    @retry_on_failure(max_attempts=3, delay=2)
    def mount_google_drive(self, mount_point: str = '/content/drive') -> bool:
        """Mount Google Drive for Colab persistent storage"""
        if self.platform != "colab":
            self.logger.info("Not on Colab, skipping Google Drive mount")
            return False
        
        try:
            from google.colab import drive
            drive.mount(mount_point, force_remount=True)
            self.logger.info(f"✅ Google Drive mounted successfully at {mount_point}")
            
            # Verify mount
            if os.path.exists(mount_point):
                return True
            else:
                raise Exception("Mount point does not exist after mounting")
                
        except ImportError:
            self.logger.error("google.colab module not available")
            return False
        except Exception as e:
            self.logger.error(f"⚠️ Could not mount Google Drive: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories for Pinokio with proper permissions"""
        if not self.pinokio_path:
            self.logger.error("Pinokio path not set")
            return False
            
        try:
            directories = [
                "",  # Base directory
                "api",
                "bin",
                "cache",
                "drive",
                "logs",
                "apps",
                "models",
                "outputs",
                "temp"
            ]
            
            created = []
            for dir_name in directories:
                path = os.path.join(self.pinokio_path, dir_name) if dir_name else self.pinokio_path
                Path(path).mkdir(parents=True, exist_ok=True, mode=0o755)
                
                # Verify directory was created
                if os.path.exists(path) and os.path.isdir(path):
                    created.append(dir_name or "base")
                else:
                    self.logger.warning(f"Failed to verify directory: {path}")
            
            self.logger.info(f"✅ Created {len(created)} Pinokio directories at {self.pinokio_path}")
            return True
            
        except PermissionError as e:
            self.logger.error(f"❌ Permission denied creating directories: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error creating directories: {e}")
            return False
    
    def get_system_info(self) -> Dict:
        """Get comprehensive system information"""
        info = {
            'platform': self.platform,
            'pinokio_path': self.pinokio_path,
            'data_path': self.data_path,
            'gpu': self.gpu_info,
            'os': os.name,
            'python_version': sys.version,
            'cpu_count': os.cpu_count(),
        }
        
        # Get memory info with error handling
        try:
            import psutil
            mem = psutil.virtual_memory()
            info['memory'] = {
                'total': f"{mem.total / (1024**3):.1f} GB",
                'available': f"{mem.available / (1024**3):.1f} GB",
                'percent': mem.percent
            }
        except ImportError:
            self.logger.debug("psutil not available, skipping memory info")
            info['memory'] = {'error': 'psutil not available'}
        except Exception as e:
            self.logger.debug(f"Error getting memory info: {e}")
            info['memory'] = {'error': str(e)}
        
        # Get disk space with error handling
        try:
            import shutil
            disk = shutil.disk_usage(self.data_path or "/")
            info['disk'] = {
                'total': f"{disk.total / (1024**3):.1f} GB",
                'free': f"{disk.free / (1024**3):.1f} GB",
                'used_percent': f"{(disk.used / disk.total) * 100:.1f}%"
            }
        except Exception as e:
            self.logger.debug(f"Error getting disk info: {e}")
            info['disk'] = {'error': str(e)}
        
        return info
    
    def print_summary(self):
        """Print platform detection summary"""
        print("=" * 60)
        print("🔍 PLATFORM DETECTION SUMMARY")
        print("=" * 60)
        print(f"Platform: {self.platform}")
        print(f"Pinokio Path: {self.pinokio_path}")
        print(f"Data Path: {self.data_path}")
        
        if self.gpu_info:
            print("\n📊 GPU Information:")
            print(f"  Available: {self.gpu_info.get('available', False)}")
            if self.gpu_info.get('devices'):
                for i, device in enumerate(self.gpu_info['devices']):
                    # Handle missing memory info gracefully
                    device_memory = device.get('memory', device.get('memory_total', 'Unknown'))
                    print(f"  Device {i}: {device['name']} ({device_memory})")
            if self.gpu_info.get('cuda_version'):
                print(f"  CUDA Version: {self.gpu_info['cuda_version']}")
        
        # Print system info if available
        try:
            sys_info = self.get_system_info()
            if 'memory' in sys_info and 'total' in sys_info['memory']:
                print(f"\n💾 Memory: {sys_info['memory']['total']}")
            if 'disk' in sys_info and 'total' in sys_info['disk']:
                print(f"💿 Disk: {sys_info['disk']['free']} free of {sys_info['disk']['total']}")
        except Exception as e:
            self.logger.debug(f"Could not get system info for summary: {e}")
        
        print("=" * 60)
