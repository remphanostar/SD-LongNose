#!/usr/bin/env python3
"""
PinokioCloud Ngrok Manager

This module creates and manages ngrok tunnels for exposing local web applications
to the internet. It provides comprehensive tunnel management with health monitoring,
automatic reconnection, and integration with the PinokioCloud system.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import json
import subprocess
import threading
import requests
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from environment_management.shell_runner import ShellRunner
from environment_management.json_handler import JSONHandler
from cloud_detection.cloud_detector import CloudDetector


class NgrokStatus(Enum):
    """Enumeration of ngrok tunnel statuses."""
    STARTING = "starting"
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    RECONNECTING = "reconnecting"
    STOPPED = "stopped"


class NgrokProtocol(Enum):
    """Enumeration of ngrok protocols."""
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    TLS = "tls"


@dataclass
class NgrokTunnel:
    """Information about an ngrok tunnel."""
    tunnel_id: str
    name: str
    local_port: int
    protocol: NgrokProtocol = NgrokProtocol.HTTP
    public_url: str = ""
    status: NgrokStatus = NgrokStatus.STARTING
    created_at: datetime = field(default_factory=datetime.now)
    last_check: datetime = field(default_factory=datetime.now)
    app_name: Optional[str] = None
    process_pid: Optional[int] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    reconnect_count: int = 0
    max_reconnects: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert NgrokTunnel to dictionary."""
        data = asdict(self)
        data['protocol'] = self.protocol.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['last_check'] = self.last_check.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NgrokTunnel':
        """Create NgrokTunnel from dictionary."""
        data['protocol'] = NgrokProtocol(data['protocol'])
        data['status'] = NgrokStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_check'] = datetime.fromisoformat(data['last_check'])
        return cls(**data)


class NgrokManager:
    """
    Creates and manages ngrok tunnels for exposing local web applications.
    
    This class provides comprehensive ngrok tunnel management with health monitoring,
    automatic reconnection, and integration with cloud platforms.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the ngrok manager."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.ngrok_storage_path = self.base_path / "ngrok_storage"
        self.ngrok_storage_path.mkdir(exist_ok=True)
        
        # Tunnel tracking
        self.active_tunnels: Dict[str, NgrokTunnel] = {}
        self.tunnel_lock = threading.RLock()
        
        # Ngrok configuration
        self.ngrok_api_url = "http://localhost:4040/api"
        self.ngrok_process = None
        self.ngrok_config_path = self.ngrok_storage_path / "ngrok.yml"
        self.auth_token = None
        
        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 10.0  # seconds
        
        # Initialize dependencies
        self.shell_runner = ShellRunner(str(self.base_path))
        self.json_handler = JSONHandler(str(self.base_path))
        self.cloud_detector = CloudDetector()
        
        # Cloud platform info
        self.platform_info = self.cloud_detector.detect_platform()
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[callable]] = {
            'tunnel_created': [],
            'tunnel_online': [],
            'tunnel_offline': [],
            'tunnel_error': [],
            'tunnel_reconnected': []
        }
        
        # Initialize ngrok
        self._initialize_ngrok()
        
        print(f"[NgrokManager] Initialized for platform: {self.platform_info.platform}")
    
    def create_tunnel(self, local_port: int, app_name: str = None,
                     protocol: NgrokProtocol = NgrokProtocol.HTTP,
                     config: Dict[str, Any] = None) -> NgrokTunnel:
        """
        Create a new ngrok tunnel.
        
        Args:
            local_port: Local port to expose
            app_name: Name of the application (optional)
            protocol: Protocol to use (HTTP, HTTPS, TCP, TLS)
            config: Additional tunnel configuration
        
        Returns:
            NgrokTunnel: Created tunnel information
        """
        print(f"[NgrokManager] Creating tunnel for port {local_port}")
        
        # Generate unique tunnel ID
        tunnel_id = f"tunnel_{uuid.uuid4().hex[:8]}"
        tunnel_name = f"{app_name or 'app'}_{local_port}"
        
        # Create tunnel object
        tunnel = NgrokTunnel(
            tunnel_id=tunnel_id,
            name=tunnel_name,
            local_port=local_port,
            protocol=protocol,
            app_name=app_name,
            config=config or {}
        )
        
        try:
            # Ensure ngrok is running
            if not self._is_ngrok_running():
                self._start_ngrok()
                time.sleep(3)  # Wait for ngrok to start
            
            # Create tunnel via ngrok API
            tunnel_config = {
                "name": tunnel_name,
                "addr": f"localhost:{local_port}",
                "proto": protocol.value
            }
            
            # Add additional configuration
            if config:
                tunnel_config.update(config)
            
            # Make API request to create tunnel
            response = requests.post(
                f"{self.ngrok_api_url}/tunnels",
                json=tunnel_config,
                timeout=10.0
            )
            
            if response.status_code == 201:
                tunnel_data = response.json()
                tunnel.public_url = tunnel_data.get("public_url", "")
                tunnel.status = NgrokStatus.ONLINE
                
                # Register tunnel
                with self.tunnel_lock:
                    self.active_tunnels[tunnel_id] = tunnel
                
                # Save tunnel configuration
                self._save_tunnel_config(tunnel)
                
                # Start monitoring if not already active
                if not self.monitoring_active:
                    self.start_monitoring()
                
                # Emit event
                self._emit_event('tunnel_created', tunnel)
                self._emit_event('tunnel_online', tunnel)
                
                print(f"[NgrokManager] Tunnel created: {tunnel.public_url}")
                return tunnel
                
            else:
                error_msg = f"Failed to create tunnel: {response.status_code} - {response.text}"
                tunnel.status = NgrokStatus.ERROR
                tunnel.error_message = error_msg
                print(f"[NgrokManager] {error_msg}")
                raise RuntimeError(error_msg)
                
        except Exception as e:
            tunnel.status = NgrokStatus.ERROR
            tunnel.error_message = str(e)
            print(f"[NgrokManager] Error creating tunnel: {e}")
            raise
    
    def close_tunnel(self, tunnel_id: str) -> bool:
        """
        Close an ngrok tunnel.
        
        Args:
            tunnel_id: ID of the tunnel to close
        
        Returns:
            bool: True if successfully closed
        """
        print(f"[NgrokManager] Closing tunnel: {tunnel_id}")
        
        with self.tunnel_lock:
            if tunnel_id not in self.active_tunnels:
                print(f"[NgrokManager] Tunnel {tunnel_id} not found")
                return False
            
            tunnel = self.active_tunnels[tunnel_id]
            
            try:
                # Close tunnel via ngrok API
                response = requests.delete(
                    f"{self.ngrok_api_url}/tunnels/{tunnel.name}",
                    timeout=10.0
                )
                
                if response.status_code == 204:
                    tunnel.status = NgrokStatus.STOPPED
                    
                    # Remove from active tunnels
                    del self.active_tunnels[tunnel_id]
                    
                    # Remove tunnel configuration
                    self._remove_tunnel_config(tunnel_id)
                    
                    # Emit event
                    self._emit_event('tunnel_offline', tunnel)
                    
                    print(f"[NgrokManager] Tunnel {tunnel_id} closed successfully")
                    return True
                else:
                    print(f"[NgrokManager] Failed to close tunnel: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"[NgrokManager] Error closing tunnel {tunnel_id}: {e}")
                return False
    
    def get_tunnel_info(self, tunnel_id: str) -> Optional[NgrokTunnel]:
        """
        Get information about a specific tunnel.
        
        Args:
            tunnel_id: ID of the tunnel
        
        Returns:
            Optional[NgrokTunnel]: Tunnel information if found
        """
        return self.active_tunnels.get(tunnel_id)
    
    def list_active_tunnels(self) -> List[NgrokTunnel]:
        """
        Get list of all active tunnels.
        
        Returns:
            List[NgrokTunnel]: List of active tunnels
        """
        with self.tunnel_lock:
            return list(self.active_tunnels.values())
    
    def get_tunnels_for_app(self, app_name: str) -> List[NgrokTunnel]:
        """
        Get all tunnels for a specific application.
        
        Args:
            app_name: Name of the application
        
        Returns:
            List[NgrokTunnel]: List of tunnels for the application
        """
        return [tunnel for tunnel in self.active_tunnels.values() 
                if tunnel.app_name == app_name]
    
    def check_tunnel_health(self, tunnel_id: str) -> bool:
        """
        Check if a tunnel is healthy and accessible.
        
        Args:
            tunnel_id: ID of the tunnel to check
        
        Returns:
            bool: True if tunnel is healthy
        """
        if tunnel_id not in self.active_tunnels:
            return False
        
        tunnel = self.active_tunnels[tunnel_id]
        
        try:
            # Check if tunnel is still listed in ngrok API
            response = requests.get(
                f"{self.ngrok_api_url}/tunnels",
                timeout=5.0
            )
            
            if response.status_code == 200:
                tunnels_data = response.json()
                active_tunnels = tunnels_data.get("tunnels", [])
                
                # Check if our tunnel is in the list
                for tunnel_data in active_tunnels:
                    if tunnel_data.get("name") == tunnel.name:
                        # Update tunnel information
                        tunnel.public_url = tunnel_data.get("public_url", tunnel.public_url)
                        tunnel.status = NgrokStatus.ONLINE
                        tunnel.last_check = datetime.now()
                        
                        # Update metrics
                        tunnel.metrics = tunnel_data.get("metrics", {})
                        
                        return True
                
                # Tunnel not found in active list
                tunnel.status = NgrokStatus.OFFLINE
                return False
            else:
                return False
                
        except Exception as e:
            print(f"[NgrokManager] Error checking tunnel health: {e}")
            tunnel.status = NgrokStatus.ERROR
            tunnel.error_message = str(e)
            return False
    
    def reconnect_tunnel(self, tunnel_id: str) -> bool:
        """
        Attempt to reconnect a tunnel.
        
        Args:
            tunnel_id: ID of the tunnel to reconnect
        
        Returns:
            bool: True if successfully reconnected
        """
        if tunnel_id not in self.active_tunnels:
            return False
        
        tunnel = self.active_tunnels[tunnel_id]
        
        # Check reconnection limits
        if tunnel.reconnect_count >= tunnel.max_reconnects:
            print(f"[NgrokManager] Tunnel {tunnel_id} exceeded max reconnections")
            tunnel.status = NgrokStatus.ERROR
            tunnel.error_message = "Exceeded maximum reconnection attempts"
            return False
        
        print(f"[NgrokManager] Attempting to reconnect tunnel: {tunnel_id}")
        
        try:
            tunnel.status = NgrokStatus.RECONNECTING
            tunnel.reconnect_count += 1
            
            # Close existing tunnel
            try:
                requests.delete(
                    f"{self.ngrok_api_url}/tunnels/{tunnel.name}",
                    timeout=5.0
                )
            except:
                pass  # Ignore errors when closing
            
            # Wait a moment
            time.sleep(2.0)
            
            # Create new tunnel with same configuration
            tunnel_config = {
                "name": tunnel.name,
                "addr": f"localhost:{tunnel.local_port}",
                "proto": tunnel.protocol.value
            }
            
            if tunnel.config:
                tunnel_config.update(tunnel.config)
            
            # Make API request to recreate tunnel
            response = requests.post(
                f"{self.ngrok_api_url}/tunnels",
                json=tunnel_config,
                timeout=10.0
            )
            
            if response.status_code == 201:
                tunnel_data = response.json()
                tunnel.public_url = tunnel_data.get("public_url", "")
                tunnel.status = NgrokStatus.ONLINE
                tunnel.last_check = datetime.now()
                tunnel.error_message = None
                
                # Save updated configuration
                self._save_tunnel_config(tunnel)
                
                # Emit event
                self._emit_event('tunnel_reconnected', tunnel)
                
                print(f"[NgrokManager] Tunnel {tunnel_id} reconnected: {tunnel.public_url}")
                return True
            else:
                tunnel.status = NgrokStatus.ERROR
                tunnel.error_message = f"Reconnection failed: {response.status_code}"
                return False
                
        except Exception as e:
            tunnel.status = NgrokStatus.ERROR
            tunnel.error_message = f"Reconnection error: {e}"
            print(f"[NgrokManager] Error reconnecting tunnel {tunnel_id}: {e}")
            return False
    
    def set_auth_token(self, token: str) -> bool:
        """
        Set ngrok authentication token.
        
        Args:
            token: Ngrok auth token
        
        Returns:
            bool: True if successfully set
        """
        try:
            self.auth_token = token
            
            # Run ngrok authtoken command
            result = self.shell_runner.run_command(
                f"ngrok authtoken {token}",
                capture_output=True
            )
            
            if result.returncode == 0:
                print("[NgrokManager] Auth token set successfully")
                return True
            else:
                print(f"[NgrokManager] Failed to set auth token: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"[NgrokManager] Error setting auth token: {e}")
            return False
    
    def get_ngrok_status(self) -> Dict[str, Any]:
        """
        Get ngrok service status and information.
        
        Returns:
            Dict[str, Any]: Ngrok status information
        """
        try:
            if not self._is_ngrok_running():
                return {
                    'running': False,
                    'api_available': False,
                    'tunnels_count': 0,
                    'error': 'Ngrok is not running'
                }
            
            # Get ngrok API status
            response = requests.get(f"{self.ngrok_api_url}/status", timeout=5.0)
            
            if response.status_code == 200:
                status_data = response.json()
                
                # Get tunnels count
                tunnels_response = requests.get(f"{self.ngrok_api_url}/tunnels", timeout=5.0)
                tunnels_count = 0
                
                if tunnels_response.status_code == 200:
                    tunnels_data = tunnels_response.json()
                    tunnels_count = len(tunnels_data.get("tunnels", []))
                
                return {
                    'running': True,
                    'api_available': True,
                    'tunnels_count': tunnels_count,
                    'active_tunnels': len(self.active_tunnels),
                    'version': status_data.get('version', 'unknown'),
                    'client_id': status_data.get('client_id', 'unknown'),
                    'region': status_data.get('region', 'unknown')
                }
            else:
                return {
                    'running': True,
                    'api_available': False,
                    'error': f'API not available: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'running': False,
                'api_available': False,
                'error': str(e)
            }
    
    def start_monitoring(self) -> None:
        """Start tunnel health monitoring."""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            print("[NgrokManager] Started tunnel monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop tunnel monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        print("[NgrokManager] Stopped tunnel monitoring")
    
    def add_event_callback(self, event: str, callback: callable) -> None:
        """Add a callback for tunnel events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def _initialize_ngrok(self) -> None:
        """Initialize ngrok configuration and check availability."""
        try:
            # Check if ngrok is installed
            result = self.shell_runner.run_command(
                "ngrok version",
                capture_output=True
            )
            
            if result.returncode != 0:
                print("[NgrokManager] Ngrok not found, attempting to install...")
                self._install_ngrok()
            else:
                print(f"[NgrokManager] Ngrok found: {result.stdout.strip()}")
            
            # Create ngrok configuration file
            self._create_ngrok_config()
            
        except Exception as e:
            print(f"[NgrokManager] Error initializing ngrok: {e}")
    
    def _install_ngrok(self) -> None:
        """Install ngrok if not available."""
        try:
            print("[NgrokManager] Installing ngrok...")
            
            # Download and install ngrok
            if self.platform_info.platform in ["google_colab", "jupyter"]:
                # Use pip install for Colab/Jupyter environments
                result = self.shell_runner.run_command(
                    "pip install pyngrok",
                    capture_output=True
                )
                
                if result.returncode == 0:
                    print("[NgrokManager] Pyngrok installed successfully")
                else:
                    print(f"[NgrokManager] Failed to install pyngrok: {result.stderr}")
            else:
                # Use system package manager or direct download
                install_commands = [
                    "curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null",
                    "echo 'deb https://ngrok-agent.s3.amazonaws.com buster main' | sudo tee /etc/apt/sources.list.d/ngrok.list",
                    "sudo apt update",
                    "sudo apt install ngrok -y"
                ]
                
                for cmd in install_commands:
                    result = self.shell_runner.run_command(cmd, capture_output=True)
                    if result.returncode != 0:
                        print(f"[NgrokManager] Command failed: {cmd}")
                        break
                else:
                    print("[NgrokManager] Ngrok installed successfully")
                    
        except Exception as e:
            print(f"[NgrokManager] Error installing ngrok: {e}")
    
    def _create_ngrok_config(self) -> None:
        """Create ngrok configuration file."""
        try:
            config = {
                'version': '2',
                'web_addr': 'localhost:4040',
                'log_level': 'info',
                'log_format': 'json',
                'tunnels': {}
            }
            
            # Add auth token if available
            if self.auth_token:
                config['authtoken'] = self.auth_token
            
            # Write configuration file
            with open(self.ngrok_config_path, 'w') as f:
                import yaml
                yaml.dump(config, f, default_flow_style=False)
                
            print(f"[NgrokManager] Ngrok config created: {self.ngrok_config_path}")
            
        except Exception as e:
            print(f"[NgrokManager] Error creating ngrok config: {e}")
    
    def _start_ngrok(self) -> None:
        """Start ngrok service."""
        try:
            if self._is_ngrok_running():
                print("[NgrokManager] Ngrok is already running")
                return
            
            print("[NgrokManager] Starting ngrok service...")
            
            # Start ngrok with configuration
            cmd = f"ngrok start --config {self.ngrok_config_path} --none"
            
            self.ngrok_process = subprocess.Popen(
                cmd.split(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setsid
            )
            
            # Wait for ngrok to start
            for _ in range(10):  # Wait up to 10 seconds
                time.sleep(1)
                if self._is_ngrok_running():
                    print("[NgrokManager] Ngrok started successfully")
                    return
            
            print("[NgrokManager] Ngrok failed to start within timeout")
            
        except Exception as e:
            print(f"[NgrokManager] Error starting ngrok: {e}")
    
    def _is_ngrok_running(self) -> bool:
        """Check if ngrok is running."""
        try:
            response = requests.get(f"{self.ngrok_api_url}/status", timeout=2.0)
            return response.status_code == 200
        except:
            return False
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                with self.tunnel_lock:
                    for tunnel_id in list(self.active_tunnels.keys()):
                        tunnel = self.active_tunnels[tunnel_id]
                        
                        # Check tunnel health
                        is_healthy = self.check_tunnel_health(tunnel_id)
                        
                        if not is_healthy and tunnel.status == NgrokStatus.ONLINE:
                            # Tunnel went offline
                            tunnel.status = NgrokStatus.OFFLINE
                            self._emit_event('tunnel_offline', tunnel)
                            
                            # Attempt automatic reconnection
                            if tunnel.reconnect_count < tunnel.max_reconnects:
                                print(f"[NgrokManager] Attempting auto-reconnect for {tunnel_id}")
                                self.reconnect_tunnel(tunnel_id)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"[NgrokManager] Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _save_tunnel_config(self, tunnel: NgrokTunnel) -> None:
        """Save tunnel configuration to disk."""
        config_file = self.ngrok_storage_path / f"{tunnel.tunnel_id}.json"
        try:
            self.json_handler.write_json_file(str(config_file), tunnel.to_dict())
        except Exception as e:
            print(f"[NgrokManager] Error saving tunnel config: {e}")
    
    def _remove_tunnel_config(self, tunnel_id: str) -> None:
        """Remove tunnel configuration from disk."""
        config_file = self.ngrok_storage_path / f"{tunnel_id}.json"
        try:
            if config_file.exists():
                config_file.unlink()
        except Exception as e:
            print(f"[NgrokManager] Error removing tunnel config: {e}")
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[NgrokManager] Error in event callback: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_monitoring()
        
        # Stop ngrok process if we started it
        if self.ngrok_process:
            try:
                os.killpg(os.getpgid(self.ngrok_process.pid), 9)
            except:
                pass


def main():
    """Test the ngrok manager functionality."""
    print("Testing NgrokManager...")
    
    manager = NgrokManager()
    
    # Get ngrok status
    status = manager.get_ngrok_status()
    print(f"Ngrok status: {status}")
    
    # Test creating a tunnel (would need a running web server)
    try:
        # This would create a tunnel for a web server on port 8000
        # tunnel = manager.create_tunnel(8000, "test_app")
        # print(f"Created tunnel: {tunnel.public_url}")
        
        # List active tunnels
        tunnels = manager.list_active_tunnels()
        print(f"Active tunnels: {len(tunnels)}")
        
        print("NgrokManager test completed")
        
    except Exception as e:
        print(f"NgrokManager test error: {e}")


if __name__ == "__main__":
    main()