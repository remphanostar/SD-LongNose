#!/usr/bin/env python3
"""
Mock GPU/NVIDIA environment for testing Pinokio notebook without actual GPU
"""

import os
import sys
from unittest.mock import Mock, patch
import subprocess

class MockGPUEnvironment:
    """Mock GPU environment to simulate Colab/CUDA without actual hardware"""
    
    def __init__(self):
        self.setup_environment_variables()
        self.setup_mocks()
    
    def setup_environment_variables(self):
        """Set environment variables to simulate Colab/GPU environment"""
        # Simulate Google Colab environment
        os.environ['COLAB_GPU'] = '1'
        os.environ['COLAB_TPU_ADDR'] = ''
        os.environ['CUDA_VISIBLE_DEVICES'] = '0'
        os.environ['NVIDIA_VISIBLE_DEVICES'] = '0'
        os.environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
        
        # Mock NVIDIA driver info
        os.environ['NVIDIA_DRIVER_VERSION'] = '525.105.17'
        os.environ['CUDA_VERSION'] = '12.0'
        
        # Mock system paths
        os.environ['LD_LIBRARY_PATH'] = '/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64'
        
        # Simulate display for headless
        os.environ['DISPLAY'] = ':99'
        
        print("🔧 Mock GPU environment variables set")
    
    def setup_mocks(self):
        """Set up mocks for various system checks"""
        
        # Mock subprocess calls for system detection
        def mock_subprocess_run(cmd, *args, **kwargs):
            cmd_str = ' '.join(cmd) if isinstance(cmd, list) else str(cmd)
            
            # Mock nvidia-smi
            if 'nvidia-smi' in cmd_str:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = "Tesla T4\nCUDA Version: 12.0\nDriver Version: 525.105.17"
                return mock_result
            
            # Mock apt-get commands (succeed silently)
            if any(x in cmd_str for x in ['apt-get', 'apt']):
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = ""
                return mock_result
            
            # Mock xvfb commands
            if 'Xvfb' in cmd_str or 'xdpyinfo' in cmd_str:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stdout = "display :99 ready"
                return mock_result
            
            # Mock wget/curl downloads (simulate success)
            if any(x in cmd_str for x in ['wget', 'curl']):
                mock_result = Mock()
                mock_result.returncode = 0
                return mock_result
            
            # Default success for other commands
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            return mock_result
        
        # Apply the subprocess mock
        subprocess.run = mock_subprocess_run
        subprocess.Popen = Mock()
        
        print("🔧 Mock subprocess calls configured")
    
    def mock_torch_cuda(self):
        """Mock PyTorch CUDA availability"""
        try:
            import torch
            # Patch torch.cuda methods
            torch.cuda.is_available = lambda: True
            torch.cuda.device_count = lambda: 1
            torch.cuda.get_device_name = lambda x=0: "Tesla T4"
            torch.cuda.current_device = lambda: 0
            print("🔧 PyTorch CUDA methods mocked")
        except ImportError:
            print("⚠️  PyTorch not available to mock")
    
    def mock_colab_drive(self):
        """Mock Google Drive mounting"""
        drive_path = "/content/drive"
        os.makedirs(drive_path, exist_ok=True)
        os.makedirs(f"{drive_path}/MyDrive", exist_ok=True)
        print(f"🔧 Mock Google Drive created at {drive_path}")
    
    def create_test_directories(self):
        """Create test directories that would exist in Colab"""
        test_dirs = [
            "/content",
            "/content/pinokio", 
            "/tmp/test_pinokio",
            "/usr/local/cuda/bin",
            "/usr/local/cuda/lib64"
        ]
        
        for dir_path in test_dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        print("🔧 Test directories created")
    
    def apply_all_mocks(self):
        """Apply all mocks for comprehensive testing"""
        self.mock_torch_cuda()
        self.mock_colab_drive()
        self.create_test_directories()
        print("✅ All mocks applied successfully")
    
    def setup_mock_environment(self):
        """Alias for apply_all_mocks for compatibility"""
        self.apply_all_mocks()

# Global function for external access
def setup_mock_environment():
    """Global function to setup mock environment"""
    mock_env = MockGPUEnvironment()
    mock_env.apply_all_mocks()
    return mock_env

# Auto-apply mocks when imported
if __name__ == "__main__":
    print("🧪 Setting up mock GPU environment...")
    mock_env = MockGPUEnvironment() 
    mock_env.apply_all_mocks()
    print("🎯 Mock environment ready for testing!")
else:
    # Apply when imported
    mock_env = MockGPUEnvironment()
    mock_env.apply_all_mocks()
