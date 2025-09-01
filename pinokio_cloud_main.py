"""
Pinokio Cloud GPU - Main Orchestrator
Automated deployment of Pinokio on cloud GPU platforms
"""

import os
import sys
import subprocess
import time
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from functools import wraps
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

try:
    from platform_detector import PlatformDetector
    from pinokio_installer import PinokioInstaller
    from tunnel_manager import TunnelManager
    from pinokio_controller import PinokioController
except ImportError as e:
    print(f"⚠️ Module import failed: {e}")
    print("Please ensure all module files exist and run: pip install -r requirements.txt")
    sys.exit(1)


class DeploymentState(Enum):
    """Deployment state enumeration"""
    UNINITIALIZED = "uninitialized"
    SETTING_UP = "setting_up"
    SETUP_COMPLETE = "setup_complete"
    INSTALLING = "installing"
    INSTALLATION_COMPLETE = "installation_complete"
    STARTING_SERVER = "starting_server"
    SERVER_RUNNING = "server_running"
    SETTING_UP_TUNNEL = "setting_up_tunnel"
    READY = "ready"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class DeploymentStatus:
    """Deployment status information"""
    state: DeploymentState
    platform: Optional[str] = None
    pinokio_version: Optional[str] = None
    server_port: Optional[int] = None
    tunnel_url: Optional[str] = None
    tunnel_service: Optional[str] = None
    installed_tools: List[str] = None
    last_error: Optional[str] = None
    started_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.installed_tools is None:
            self.installed_tools = []
        if self.started_at is None:
            self.started_at = datetime.now()


def retry_on_failure(max_retries: int = 3, delay: float = 2.0, backoff: float = 1.5):
    """Decorator for retrying failed operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        if hasattr(args[0], 'logger'):
                            args[0].logger.warning(
                                f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                                f"Retrying in {current_delay:.1f}s..."
                            )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        if hasattr(args[0], 'logger'):
                            args[0].logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")
            
            if last_exception:
                raise last_exception
        return wrapper
    return decorator


class PinokioCloudGPU:
    """Main orchestrator for Pinokio Cloud GPU deployment with enhanced state management"""
    
    def __init__(self, config_path: str = None, log_level: str = "INFO"):
        # Core components
        self.detector = None
        self.installer = None
        self.tunnel = None
        self.controller = None
        
        # State management
        self.status = DeploymentStatus(state=DeploymentState.UNINITIALIZED)
        self.config_path = config_path or os.path.join(os.getcwd(), "pinokio_config.json")
        self.state_file = os.path.join(os.getcwd(), "pinokio_state.json")
        
        # Legacy compatibility
        self.platform = None
        self.paths = {}
        self.tunnel_url = None
        
        # Setup logging
        self.logger = self._setup_logging(log_level)
        
        # Load configuration and state
        self.config = self._load_config()
        self._load_state()
    
    def _setup_logging(self, log_level: str) -> logging.Logger:
        """Setup logging for the orchestrator"""
        logger = logging.getLogger('PinokioCloudGPU')
        logger.handlers.clear()  # Clear existing handlers
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        try:
            file_handler = logging.FileHandler('pinokio_cloud.log')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")
        
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        return logger
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "server_port": 42000,
            "tunnel_service": "auto",
            "max_retries": 3,
            "retry_delay": 2.0,
            "auto_install_tools": [],
            "headless": True,
            "enable_gpu": True,
            "backup_enabled": True
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    self.logger.info(f"Configuration loaded from {self.config_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}, using defaults")
        
        return default_config
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.debug(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
    
    def _load_state(self):
        """Load deployment state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state_data = json.load(f)
                    # Convert datetime strings back to objects
                    if state_data.get('started_at'):
                        state_data['started_at'] = datetime.fromisoformat(state_data['started_at'])
                    if state_data.get('ready_at'):
                        state_data['ready_at'] = datetime.fromisoformat(state_data['ready_at'])
                    # Reconstruct status object
                    self.status = DeploymentStatus(**state_data)
                    self.logger.info(f"State loaded: {self.status.state.value}")
            except Exception as e:
                self.logger.warning(f"Failed to load state: {e}, using fresh state")
    
    def _save_state(self):
        """Save deployment state to file"""
        try:
            state_dict = asdict(self.status)
            # Convert datetime objects to strings
            if state_dict.get('started_at'):
                state_dict['started_at'] = self.status.started_at.isoformat()
            if state_dict.get('ready_at'):
                state_dict['ready_at'] = self.status.ready_at.isoformat()
            # Convert enum to value
            state_dict['state'] = self.status.state.value
            
            with open(self.state_file, 'w') as f:
                json.dump(state_dict, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    def _update_state(self, new_state: DeploymentState, error: str = None):
        """Update deployment state and save to file"""
        self.status.state = new_state
        if error:
            self.status.last_error = error
        if new_state == DeploymentState.READY and not self.status.ready_at:
            self.status.ready_at = datetime.now()
        
        self._save_state()
        self.logger.info(f"State updated: {new_state.value}")
        
    @retry_on_failure(max_retries=3, delay=2.0)
    def setup(self) -> bool:
        """Setup environment and detect platform with retry logic"""
        try:
            self._update_state(DeploymentState.SETTING_UP)
            self.logger.info("🔍 Setting up Pinokio Cloud GPU environment...")
            
            # Initialize platform detector
            self.detector = PlatformDetector()
            
            # Detect platform and setup paths
            self.platform = self.detector.detect_platform()
            self.status.platform = self.platform
            self.paths = self.detector.setup_paths()
            
            # Mount persistent storage if Colab
            if self.platform == "colab":
                self.logger.info("Mounting Google Drive for Colab...")
                if not self.detector.mount_google_drive():
                    self.logger.warning("Google Drive mount failed, continuing anyway")
            
            # Create directories
            self.detector.create_directories()
            
            # Detect GPU
            gpu_info = self.detector.detect_gpu()
            if not gpu_info and self.config.get('enable_gpu', True):
                self.logger.warning("No GPU detected but GPU support is enabled")
            
            # Print summary
            self.detector.print_summary() 
            
            self._update_state(DeploymentState.SETUP_COMPLETE)
            self.logger.info("✅ Environment setup complete")
            return True
            
        except Exception as e:
            error_msg = f"Setup failed: {e}"
            self._update_state(DeploymentState.ERROR, error_msg)
            self.logger.error(error_msg)
            raise
    
    @retry_on_failure(max_retries=2, delay=3.0)
    def install_pinokio(self, force_reinstall: bool = False) -> bool:
        """Install Pinokio with enhanced error handling"""
        try:
            if self.status.state not in [DeploymentState.SETUP_COMPLETE, DeploymentState.ERROR]:
                raise Exception("Please run setup() first")
            
            self._update_state(DeploymentState.INSTALLING)
            self.logger.info("📦 Installing Pinokio...")
            
            # Initialize installer
            self.installer = PinokioInstaller(self.paths['pinokio'])
            
            # Check if already installed and force reinstall not requested
            if not force_reinstall and self.installer.is_installed():
                self.logger.info("Pinokio already installed, skipping installation")
                self._update_state(DeploymentState.INSTALLATION_COMPLETE)
                return True
            
            # Call install with correct arguments
            success = self.installer.install(headless=True)
            
            if success:
                # Get version info
                try:
                    version_info = self.installer.get_version()
                    self.status.pinokio_version = version_info
                except:
                    pass
                
                self._update_state(DeploymentState.INSTALLATION_COMPLETE)
                self.logger.info("✅ Pinokio installation complete")
            else:
                raise Exception("Installation returned failure status")
            
            return success
            
        except Exception as e:
            error_msg = f"Pinokio installation failed: {e}"
            self._update_state(DeploymentState.ERROR, error_msg)
            self.logger.error(error_msg)
            raise
    
    @retry_on_failure(max_retries=3, delay=5.0)
    def start_pinokio(self, port: int = None) -> bool:
        """Start Pinokio server with enhanced error handling"""
        try:
            if self.status.state not in [DeploymentState.INSTALLATION_COMPLETE, DeploymentState.ERROR]:
                raise Exception("Please install Pinokio first")
            
            port = port or self.config.get('server_port', 42000)
            self._update_state(DeploymentState.STARTING_SERVER)
            self.logger.info(f"🚀 Starting Pinokio server on port {port}...")
            
            # Initialize controller with timeout
            self.controller = PinokioController(
                self.paths['pinokio'], 
                port, 
                timeout=60
            )
            
            # Start server in headless mode
            success = self.controller.start_server(
                headless=self.config.get('headless', True), 
                port=port
            )
            
            if success:
                self.status.server_port = port
                self._update_state(DeploymentState.SERVER_RUNNING)
                self.logger.info(f"✅ Pinokio server running on port {port}")
                
                # Wait a moment for server to stabilize
                time.sleep(2)
                
                # Verify server is responsive
                if not self.controller.is_running():
                    raise Exception("Server started but is not responding")
            else:
                raise Exception("Server startup returned failure status")
            
            return success
            
        except Exception as e:
            error_msg = f"Failed to start Pinokio: {e}"
            self._update_state(DeploymentState.ERROR, error_msg)
            self.logger.error(error_msg)
            raise
    
    @retry_on_failure(max_retries=3, delay=3.0)
    def setup_tunnel(self, service: str = None, ngrok_token: str = None, 
                    region: str = None, subdomain: str = None) -> Optional[str]:
        """Setup tunneling for remote access with enhanced error handling"""
        try:
            if self.status.state not in [DeploymentState.SERVER_RUNNING, DeploymentState.ERROR]:
                raise Exception("Please start Pinokio server first")
            
            service = service or self.config.get('tunnel_service', 'auto')
            self._update_state(DeploymentState.SETTING_UP_TUNNEL)
            self.logger.info(f"🌐 Setting up {service} tunnel for remote access...")
            
            # Initialize tunnel manager
            self.tunnel = TunnelManager()
            
            # Start tunnel with enhanced options
            self.tunnel_url = self.tunnel.start_tunnel(
                port=self.controller.api_port,
                service=service,
                ngrok_token=ngrok_token,
                region=region,
                subdomain=subdomain
            )
            
            if self.tunnel_url:
                self.status.tunnel_url = self.tunnel_url
                self.status.tunnel_service = service
                self.tunnel_url = self.tunnel_url  # Legacy compatibility
                self._update_state(DeploymentState.READY)
                
                self.logger.info(f"\n🎉 SUCCESS! Pinokio is accessible at:")
                self.logger.info(f"🔗 {self.tunnel_url}")
                self.logger.info(f"📱 Open this URL in your browser to access Pinokio")
                
                # Start tunnel monitoring
                if hasattr(self.tunnel, 'monitor_tunnels'):
                    self.tunnel.monitor_tunnels(check_interval=30)
            else:
                raise Exception("Tunnel setup returned no URL")
            
            return self.tunnel_url
            
        except Exception as e:
            error_msg = f"Tunnel setup failed: {e}"
            self._update_state(DeploymentState.ERROR, error_msg)
            self.logger.error(error_msg)
            # Don't raise here - allow fallback to local access
            return None
    
    @retry_on_failure(max_retries=2, delay=5.0)
    def install_ai_tool(self, tool_name: str, config: Dict = None, 
                       auto_launch: bool = True) -> Optional[str]:
        """Install and optionally launch an AI tool with error handling"""
        try:
            if self.status.state not in [DeploymentState.READY, DeploymentState.SERVER_RUNNING, DeploymentState.ERROR]:
                raise Exception("Please start Pinokio server first")
            
            self.logger.info(f"🤖 Installing AI tool: {tool_name}")
            
            if auto_launch:
                # Install and launch tool
                tool_url = self.controller.quick_install_and_launch(
                    tool_name, config=config, wait_for_ready=True
                )
            else:
                # Just install
                app_info = self.controller.install_app(f"https://github.com/{tool_name}", tool_name)
                tool_url = None
                if app_info:
                    self.logger.info(f"✅ {tool_name} installed successfully")
            
            if tool_url:
                # Add to installed tools list
                if tool_name not in self.status.installed_tools:
                    self.status.installed_tools.append(tool_name)
                    self._save_state()
                
                self.logger.info(f"✅ {tool_name} installed and running")
                self.logger.info(f"🔗 Access at: {tool_url}")
            elif not auto_launch:
                # Tool installed but not launched
                if tool_name not in self.status.installed_tools:
                    self.status.installed_tools.append(tool_name)
                    self._save_state()
            else:
                raise Exception(f"Failed to install/launch {tool_name}")
            
            return tool_url
            
        except Exception as e:
            error_msg = f"Tool installation failed for {tool_name}: {e}"
            self.logger.error(error_msg)
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        # Update dynamic status
        pinokio_running = self.controller.is_running() if self.controller else False
        active_tunnels = self.tunnel.get_active_tunnels() if self.tunnel else {}
        
        status = {
            'deployment': {
                'state': self.status.state.value,
                'platform': self.status.platform,
                'started_at': self.status.started_at.isoformat() if self.status.started_at else None,
                'ready_at': self.status.ready_at.isoformat() if self.status.ready_at else None,
                'last_error': self.status.last_error
            },
            'pinokio': {
                'version': self.status.pinokio_version,
                'running': pinokio_running,
                'port': self.status.server_port,
                'installation_path': self.paths.get('pinokio') if self.paths else None
            },
            'tunnel': {
                'url': self.status.tunnel_url,
                'service': self.status.tunnel_service,
                'active_tunnels': active_tunnels
            },
            'tools': {
                'installed': self.status.installed_tools,
                'count': len(self.status.installed_tools)
            },
            'system': {
                'platform': self.platform,
                'paths': self.paths,
                'config': self.config
            }
        }
        return status
    
    def print_status(self):
        """Print formatted status information"""
        status = self.get_status()
        
        print("\n" + "=" * 50)
        print("📊 PINOKIO CLOUD GPU STATUS")
        print("=" * 50)
        
        # Deployment status
        deploy = status['deployment']
        print(f"🚀 State: {deploy['state']}")
        print(f"🖥️  Platform: {deploy['platform']}")
        if deploy['last_error']:
            print(f"❌ Last Error: {deploy['last_error']}")
        
        # Pinokio status
        pinokio = status['pinokio']
        running_status = "✅ Running" if pinokio['running'] else "❌ Stopped"
        print(f"📦 Pinokio: {running_status} (port: {pinokio['port']})")
        if pinokio['version']:
            print(f"📝 Version: {pinokio['version']}")
        
        # Tunnel status
        tunnel = status['tunnel']
        if tunnel['url']:
            print(f"🌐 Tunnel: {tunnel['url']} ({tunnel['service']})")
        else:
            print("🌐 Tunnel: Not configured")
        
        # Tools status
        tools = status['tools']
        print(f"🤖 Installed Tools: {tools['count']}")
        for tool in tools['installed']:
            print(f"  - {tool}")
        
        print("=" * 50)
    
    def recover_from_error(self) -> bool:
        """Attempt to recover from error state"""
        if self.status.state != DeploymentState.ERROR:
            self.logger.info("No error state to recover from")
            return True
        
        self.logger.info("🔄 Attempting error recovery...")
        
        try:
            # Check if components are still functional
            if self.controller and self.controller.is_running():
                self._update_state(DeploymentState.SERVER_RUNNING)
                self.logger.info("✅ Pinokio server is still running")
                
                # Check tunnel
                if self.tunnel and self.tunnel_url:
                    try:
                        import requests
                        response = requests.get(self.tunnel_url, timeout=5)
                        if response.status_code == 200:
                            self._update_state(DeploymentState.READY)
                            self.logger.info("✅ Tunnel is still accessible")
                            return True
                    except:
                        pass
                
                return True
            
            # Try to restart server if installation is complete
            if self.installer and self.installer.is_installed():
                self.logger.info("Attempting to restart Pinokio server...")
                if self.start_pinokio():
                    return True
            
            self.logger.warning("Manual intervention may be required")
            return False
            
        except Exception as e:
            self.logger.error(f"Recovery failed: {e}")
            return False
    
    def cleanup(self, save_state: bool = True):
        """Stop all services and cleanup with enhanced error handling"""
        try:
            self.logger.info("🧹 Cleaning up services...")
            
            # Stop Pinokio server
            if self.controller:
                try:
                    self.controller.cleanup()
                    self.logger.info("Pinokio server stopped")
                except Exception as e:
                    self.logger.error(f"Error stopping Pinokio server: {e}")
            
            # Stop tunnels
            if self.tunnel:
                try:
                    self.tunnel.stop_all_tunnels()
                    self.logger.info("All tunnels stopped")
                except Exception as e:
                    self.logger.error(f"Error stopping tunnels: {e}")
            
            # Update state
            if save_state:
                self._update_state(DeploymentState.STOPPED)
            
            self.logger.info("✅ Cleanup complete")
            
        except Exception as e:
            self.logger.error(f"⚠️ Cleanup error: {e}")
    
    def reset(self):
        """Reset deployment to initial state"""
        self.logger.info("🔄 Resetting deployment state...")
        
        # Cleanup first
        self.cleanup(save_state=False)
        
        # Reset state
        self.status = DeploymentStatus(state=DeploymentState.UNINITIALIZED)
        self._save_state()
        
        # Clear components
        self.detector = None
        self.installer = None
        self.tunnel = None
        self.controller = None
        self.platform = None
        self.paths = {}
        self.tunnel_url = None
        
        self.logger.info("✅ Reset complete")
    
    def auto_install_tools(self) -> Dict[str, str]:
        """Auto-install configured tools"""
        tools = self.config.get('auto_install_tools', [])
        if not tools:
            self.logger.info("No auto-install tools configured")
            return {}
        
        self.logger.info(f"Auto-installing {len(tools)} tools: {', '.join(tools)}")
        results = {}
        
        for tool in tools:
            try:
                url = self.install_ai_tool(tool, auto_launch=False)
                results[tool] = "installed" if url else "failed"
            except Exception as e:
                self.logger.error(f"Failed to auto-install {tool}: {e}")
                results[tool] = "failed"
        
        return results
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.cleanup()


def quick_start_notebook(config: Dict[str, Any] = None, log_level: str = "INFO") -> Tuple[Optional[PinokioCloudGPU], Optional[str]]:
    """Quick start function for Jupyter notebooks with enhanced error handling"""
    pinokio = None
    try:
        print("🚀 PINOKIO CLOUD GPU - QUICK START")
        print("=" * 50)
        
        # Initialize with configuration
        pinokio = PinokioCloudGPU(log_level=log_level)
        
        # Apply custom config if provided
        if config:
            pinokio.config.update(config)
            pinokio._save_config()
        
        # Setup environment
        if not pinokio.setup():
            return pinokio, None
        
        # Install Pinokio
        if not pinokio.install_pinokio():
            return pinokio, None
        
        # Start server
        if not pinokio.start_pinokio():
            return pinokio, None
        
        # Setup tunnel with fallback strategy
        tunnel_services = ["cloudflare", "ngrok", "localtunnel"]
        tunnel_url = None
        
        for service in tunnel_services:
            try:
                pinokio.logger.info(f"Trying {service} tunnel...")
                tunnel_url = pinokio.setup_tunnel(service=service)
                if tunnel_url:
                    break
            except Exception as e:
                pinokio.logger.warning(f"{service} tunnel failed: {e}")
                continue
        
        if not tunnel_url:
            pinokio.logger.warning("All tunnel services failed, manual configuration required")
        
        # Auto-install configured tools
        if pinokio.config.get('auto_install_tools'):
            pinokio.auto_install_tools()
        
        return pinokio, tunnel_url
        
    except Exception as e:
        error_msg = f"Quick start failed: {e}"
        if pinokio:
            pinokio.logger.error(error_msg)
        else:
            print(f"❌ {error_msg}")
        return pinokio, None


def create_default_config(config_path: str = "pinokio_config.json") -> Dict[str, Any]:
    """Create a default configuration file"""
    default_config = {
        "server_port": 42000,
        "tunnel_service": "auto",
        "max_retries": 3,
        "retry_delay": 2.0,
        "auto_install_tools": [
            "stable-diffusion",
            "comfyui"
        ],
        "headless": True,
        "enable_gpu": True,
        "backup_enabled": True,
        "tunnel_options": {
            "region": "us",
            "subdomain": null
        },
        "monitoring": {
            "enable_health_checks": True,
            "check_interval": 30,
            "auto_recovery": True
        }
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"✅ Default configuration created at {config_path}")
        return default_config
    except Exception as e:
        print(f"❌ Failed to create config file: {e}")
        return default_config


def advanced_start(config_file: str = None, recovery_mode: bool = False) -> Optional[PinokioCloudGPU]:
    """Advanced start with configuration file and recovery options"""
    try:
        # Initialize with config file
        pinokio = PinokioCloudGPU(config_path=config_file)
        
        # Recovery mode - try to recover from previous state
        if recovery_mode:
            if pinokio.status.state == DeploymentState.ERROR:
                pinokio.logger.info("Recovery mode: attempting to recover from error state")
                if pinokio.recover_from_error():
                    return pinokio
            elif pinokio.status.state in [DeploymentState.READY, DeploymentState.SERVER_RUNNING]:
                pinokio.logger.info("Recovery mode: previous deployment still active")
                return pinokio
        
        # Full deployment sequence
        pinokio.setup()
        pinokio.install_pinokio()
        pinokio.start_pinokio()
        pinokio.setup_tunnel()
        
        return pinokio
        
    except Exception as e:
        print(f"❌ Advanced start failed: {e}")
        return None


# Notebook helper functions for easy importing
def notebook_quick_start():
    """Simplified function for notebook imports"""
    return quick_start_notebook()


def notebook_install_tool(pinokio_instance, tool_name: str):
    """Helper function to install tools in notebooks"""
    if not pinokio_instance:
        print("❌ Please run quick_start_notebook() first")
        return None
    return pinokio_instance.install_ai_tool(tool_name)


def notebook_status(pinokio_instance):
    """Helper function to show status in notebooks"""
    if not pinokio_instance:
        print("❌ No Pinokio instance available")
        return None
    pinokio_instance.print_status()
    return pinokio_instance.get_status()


if __name__ == "__main__":
    # Enhanced command line interface
    import argparse
    import signal
    
    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully"""
        print("\n🛑 Shutdown signal received...")
        if 'pinokio' in globals():
            pinokio.cleanup()
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(
        description="Pinokio Cloud GPU Deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pinokio_cloud_main.py --quick-start
  python pinokio_cloud_main.py --config myconfig.json --recovery
  python pinokio_cloud_main.py --port 8080 --tunnel ngrok --install-tool stable-diffusion
  python pinokio_cloud_main.py --status
        """
    )
    
    # Deployment options
    parser.add_argument("--quick-start", action="store_true", help="Quick start with defaults")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--recovery", action="store_true", help="Enable recovery mode")
    parser.add_argument("--reset", action="store_true", help="Reset deployment state")
    
    # Server options
    parser.add_argument("--platform", help="Force platform detection")
    parser.add_argument("--port", type=int, help="API port (default: from config or 42000)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    
    # Tunnel options
    parser.add_argument("--tunnel", help="Tunnel service (auto|ngrok|cloudflare|localtunnel)")
    parser.add_argument("--ngrok-token", help="ngrok auth token")
    parser.add_argument("--region", help="Tunnel region")
    parser.add_argument("--subdomain", help="Custom subdomain")
    
    # Tool options
    parser.add_argument("--install-tool", action="append", help="AI tool to install (can be used multiple times)")
    parser.add_argument("--no-auto-launch", action="store_true", help="Install tools without launching")
    
    # Control options
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup and exit")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (no interactive mode)")
    
    args = parser.parse_args()
    
    try:
        # Initialize with configuration
        pinokio = PinokioCloudGPU(config_path=args.config, log_level=args.log_level)
        
        # Handle special commands first
        if args.reset:
            pinokio.reset()
            print("✅ Deployment state reset")
            sys.exit(0)
        
        if args.cleanup:
            pinokio.cleanup()
            print("✅ Cleanup completed")
            sys.exit(0)
        
        if args.status:
            pinokio.print_status()
            sys.exit(0)
        
        # Quick start mode
        if args.quick_start:
            config_overrides = {}
            if args.port:
                config_overrides['server_port'] = args.port
            if args.tunnel:
                config_overrides['tunnel_service'] = args.tunnel
            if args.headless:
                config_overrides['headless'] = True
            
            pinokio_instance, tunnel_url = quick_start_notebook(config_overrides, args.log_level)
            if not pinokio_instance:
                sys.exit(1)
            pinokio = pinokio_instance
        
        # Advanced start with recovery
        elif args.recovery:
            pinokio = advanced_start(args.config, recovery_mode=True)
            if not pinokio:
                sys.exit(1)
        
        # Manual setup mode
        else:
            # Override platform if specified
            if args.platform:
                os.environ['FORCE_PLATFORM'] = args.platform
            
            # Apply command line overrides to config
            if args.port:
                pinokio.config['server_port'] = args.port
            if args.tunnel:
                pinokio.config['tunnel_service'] = args.tunnel
            if args.headless:
                pinokio.config['headless'] = True
            
            # Run deployment sequence
            pinokio.setup()
            pinokio.install_pinokio()
            pinokio.start_pinokio()
            
            # Setup tunnel with options
            tunnel_url = pinokio.setup_tunnel(
                service=args.tunnel,
                ngrok_token=args.ngrok_token,
                region=args.region,
                subdomain=args.subdomain
            )
        
        # Install tools if specified
        if args.install_tool:
            for tool in args.install_tool:
                try:
                    pinokio.install_ai_tool(tool, auto_launch=not args.no_auto_launch)
                except Exception as e:
                    pinokio.logger.error(f"Failed to install {tool}: {e}")
        
        # Final status
        pinokio.print_status()
        
        # Keep running unless daemon mode
        if not args.daemon:
            print("\n📋 Press Ctrl+C to shutdown...")
            try:
                while True:
                    time.sleep(10)
                    # Periodic health check
                    if pinokio.status.state == DeploymentState.ERROR:
                        pinokio.logger.warning("Error state detected, attempting recovery...")
                        pinokio.recover_from_error()
            except KeyboardInterrupt:
                pass
        
        print("\n🛑 Shutting down...")
        pinokio.cleanup()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        if 'pinokio' in locals():
            pinokio.cleanup()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        if 'pinokio' in locals():
            try:
                pinokio.logger.error(f"Fatal error: {e}")
                pinokio.cleanup()
            except:
                pass
        sys.exit(1)
