#!/usr/bin/env python3
"""
PinokioCloud Cloudflare Manager

This module creates and manages Cloudflare tunnels as a backup to ngrok.
It provides comprehensive Cloudflare tunnel management with health monitoring,
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


class CloudflareStatus(Enum):
    """Enumeration of Cloudflare tunnel statuses."""
    STARTING = "starting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    RECONNECTING = "reconnecting"
    STOPPED = "stopped"


class CloudflareProtocol(Enum):
    """Enumeration of Cloudflare protocols."""
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    SSH = "ssh"
    RDP = "rdp"


@dataclass
class CloudflareTunnel:
    """Information about a Cloudflare tunnel."""
    tunnel_id: str
    name: str
    local_port: int
    protocol: CloudflareProtocol = CloudflareProtocol.HTTP
    public_url: str = ""
    status: CloudflareStatus = CloudflareStatus.STARTING
    created_at: datetime = field(default_factory=datetime.now)
    last_check: datetime = field(default_factory=datetime.now)
    app_name: Optional[str] = None
    process_pid: Optional[int] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    reconnect_count: int = 0
    max_reconnects: int = 3
    cloudflare_tunnel_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert CloudflareTunnel to dictionary."""
        data = asdict(self)
        data['protocol'] = self.protocol.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['last_check'] = self.last_check.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CloudflareTunnel':
        """Create CloudflareTunnel from dictionary."""
        data['protocol'] = CloudflareProtocol(data['protocol'])
        data['status'] = CloudflareStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_check'] = datetime.fromisoformat(data['last_check'])
        return cls(**data)


class CloudflareManager:
    """
    Creates and manages Cloudflare tunnels as a backup to ngrok.
    
    This class provides comprehensive Cloudflare tunnel management with health monitoring,
    automatic reconnection, and integration with cloud platforms.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the Cloudflare manager."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.cloudflare_storage_path = self.base_path / "cloudflare_storage"
        self.cloudflare_storage_path.mkdir(exist_ok=True)
        
        # Tunnel tracking
        self.active_tunnels: Dict[str, CloudflareTunnel] = {}
        self.tunnel_lock = threading.RLock()
        
        # Cloudflare configuration
        self.cloudflared_binary = "cloudflared"
        self.cloudflare_processes: Dict[str, subprocess.Popen] = {}
        
        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 15.0  # seconds
        
        # Initialize dependencies
        self.shell_runner = ShellRunner(str(self.base_path))
        self.json_handler = JSONHandler(str(self.base_path))
        self.cloud_detector = CloudDetector()
        
        # Cloud platform info
        self.platform_info = self.cloud_detector.detect_platform()
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[callable]] = {
            'tunnel_created': [],
            'tunnel_connected': [],
            'tunnel_disconnected': [],
            'tunnel_error': [],
            'tunnel_reconnected': []
        }
        
        # Initialize cloudflared
        self._initialize_cloudflared()
        
        print(f"[CloudflareManager] Initialized for platform: {self.platform_info.platform}")
    
    def create_tunnel(self, local_port: int, app_name: str = None,
                     protocol: CloudflareProtocol = CloudflareProtocol.HTTP,
                     config: Dict[str, Any] = None) -> CloudflareTunnel:
        """
        Create a new Cloudflare tunnel.
        
        Args:
            local_port: Local port to expose
            app_name: Name of the application (optional)
            protocol: Protocol to use (HTTP, HTTPS, TCP, etc.)
            config: Additional tunnel configuration
        
        Returns:
            CloudflareTunnel: Created tunnel information
        """
        print(f"[CloudflareManager] Creating tunnel for port {local_port}")
        
        # Generate unique tunnel ID
        tunnel_id = f"cf_tunnel_{uuid.uuid4().hex[:8]}"
        tunnel_name = f"{app_name or 'app'}_{local_port}"
        
        # Create tunnel object
        tunnel = CloudflareTunnel(
            tunnel_id=tunnel_id,
            name=tunnel_name,
            local_port=local_port,
            protocol=protocol,
            app_name=app_name,
            config=config or {}
        )
        
        try:
            # Create tunnel using cloudflared
            if protocol == CloudflareProtocol.HTTP:
                # Use quick tunnel for HTTP
                tunnel_url = self._create_quick_tunnel(local_port, tunnel_name)
                tunnel.public_url = tunnel_url
            else:
                # Use named tunnel for other protocols
                cf_tunnel_id = self._create_named_tunnel(tunnel_name, local_port, protocol)
                tunnel.cloudflare_tunnel_id = cf_tunnel_id
                tunnel.public_url = self._get_tunnel_url(cf_tunnel_id, tunnel_name)
            
            tunnel.status = CloudflareStatus.CONNECTED
            
            # Register tunnel
            with self.tunnel_lock:
                self.active_tunnels[tunnel_id] = tunnel
            
            # Save tunnel configuration
            self._save_tunnel_config(tunnel)
            
            # Start monitoring if not already active
            if not self.monitoring_active:
                self.start_monitoring()
            
            # Emit events
            self._emit_event('tunnel_created', tunnel)
            self._emit_event('tunnel_connected', tunnel)
            
            print(f"[CloudflareManager] Tunnel created: {tunnel.public_url}")
            return tunnel
            
        except Exception as e:
            tunnel.status = CloudflareStatus.ERROR
            tunnel.error_message = str(e)
            print(f"[CloudflareManager] Error creating tunnel: {e}")
            raise
    
    def close_tunnel(self, tunnel_id: str) -> bool:
        """
        Close a Cloudflare tunnel.
        
        Args:
            tunnel_id: ID of the tunnel to close
        
        Returns:
            bool: True if successfully closed
        """
        print(f"[CloudflareManager] Closing tunnel: {tunnel_id}")
        
        with self.tunnel_lock:
            if tunnel_id not in self.active_tunnels:
                print(f"[CloudflareManager] Tunnel {tunnel_id} not found")
                return False
            
            tunnel = self.active_tunnels[tunnel_id]
            
            try:
                # Stop the cloudflared process
                if tunnel_id in self.cloudflare_processes:
                    process = self.cloudflare_processes[tunnel_id]
                    process.terminate()
                    
                    # Wait for process to terminate
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    
                    del self.cloudflare_processes[tunnel_id]
                
                # Clean up named tunnel if it exists
                if tunnel.cloudflare_tunnel_id:
                    self._cleanup_named_tunnel(tunnel.cloudflare_tunnel_id)
                
                tunnel.status = CloudflareStatus.STOPPED
                
                # Remove from active tunnels
                del self.active_tunnels[tunnel_id]
                
                # Remove tunnel configuration
                self._remove_tunnel_config(tunnel_id)
                
                # Emit event
                self._emit_event('tunnel_disconnected', tunnel)
                
                print(f"[CloudflareManager] Tunnel {tunnel_id} closed successfully")
                return True
                
            except Exception as e:
                print(f"[CloudflareManager] Error closing tunnel {tunnel_id}: {e}")
                return False
    
    def get_tunnel_info(self, tunnel_id: str) -> Optional[CloudflareTunnel]:
        """
        Get information about a specific tunnel.
        
        Args:
            tunnel_id: ID of the tunnel
        
        Returns:
            Optional[CloudflareTunnel]: Tunnel information if found
        """
        return self.active_tunnels.get(tunnel_id)
    
    def list_active_tunnels(self) -> List[CloudflareTunnel]:
        """
        Get list of all active tunnels.
        
        Returns:
            List[CloudflareTunnel]: List of active tunnels
        """
        with self.tunnel_lock:
            return list(self.active_tunnels.values())
    
    def get_tunnels_for_app(self, app_name: str) -> List[CloudflareTunnel]:
        """
        Get all tunnels for a specific application.
        
        Args:
            app_name: Name of the application
        
        Returns:
            List[CloudflareTunnel]: List of tunnels for the application
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
            # Check if the cloudflared process is still running
            if tunnel_id in self.cloudflare_processes:
                process = self.cloudflare_processes[tunnel_id]
                if process.poll() is None:
                    # Process is still running
                    tunnel.status = CloudflareStatus.CONNECTED
                    tunnel.last_check = datetime.now()
                    return True
                else:
                    # Process has terminated
                    tunnel.status = CloudflareStatus.DISCONNECTED
                    del self.cloudflare_processes[tunnel_id]
                    return False
            
            # Try to access the tunnel URL
            if tunnel.public_url:
                try:
                    response = requests.get(tunnel.public_url, timeout=10.0)
                    if response.status_code < 500:  # Accept any non-server-error response
                        tunnel.status = CloudflareStatus.CONNECTED
                        tunnel.last_check = datetime.now()
                        return True
                except requests.exceptions.RequestException:
                    pass
            
            tunnel.status = CloudflareStatus.DISCONNECTED
            return False
            
        except Exception as e:
            print(f"[CloudflareManager] Error checking tunnel health: {e}")
            tunnel.status = CloudflareStatus.ERROR
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
            print(f"[CloudflareManager] Tunnel {tunnel_id} exceeded max reconnections")
            tunnel.status = CloudflareStatus.ERROR
            tunnel.error_message = "Exceeded maximum reconnection attempts"
            return False
        
        print(f"[CloudflareManager] Attempting to reconnect tunnel: {tunnel_id}")
        
        try:
            tunnel.status = CloudflareStatus.RECONNECTING
            tunnel.reconnect_count += 1
            
            # Stop existing process
            if tunnel_id in self.cloudflare_processes:
                process = self.cloudflare_processes[tunnel_id]
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                del self.cloudflare_processes[tunnel_id]
            
            # Wait a moment
            time.sleep(3.0)
            
            # Recreate tunnel
            if tunnel.protocol == CloudflareProtocol.HTTP:
                # Recreate quick tunnel
                tunnel_url = self._create_quick_tunnel(tunnel.local_port, tunnel.name)
                tunnel.public_url = tunnel_url
            else:
                # Recreate named tunnel
                cf_tunnel_id = self._create_named_tunnel(tunnel.name, tunnel.local_port, tunnel.protocol)
                tunnel.cloudflare_tunnel_id = cf_tunnel_id
                tunnel.public_url = self._get_tunnel_url(cf_tunnel_id, tunnel.name)
            
            tunnel.status = CloudflareStatus.CONNECTED
            tunnel.last_check = datetime.now()
            tunnel.error_message = None
            
            # Save updated configuration
            self._save_tunnel_config(tunnel)
            
            # Emit event
            self._emit_event('tunnel_reconnected', tunnel)
            
            print(f"[CloudflareManager] Tunnel {tunnel_id} reconnected: {tunnel.public_url}")
            return True
            
        except Exception as e:
            tunnel.status = CloudflareStatus.ERROR
            tunnel.error_message = f"Reconnection error: {e}"
            print(f"[CloudflareManager] Error reconnecting tunnel {tunnel_id}: {e}")
            return False
    
    def get_cloudflared_status(self) -> Dict[str, Any]:
        """
        Get cloudflared service status and information.
        
        Returns:
            Dict[str, Any]: Cloudflared status information
        """
        try:
            # Check if cloudflared is available
            result = self.shell_runner.run_command(
                f"{self.cloudflared_binary} version",
                capture_output=True
            )
            
            if result.returncode == 0:
                version_info = result.stdout.strip()
                
                return {
                    'available': True,
                    'version': version_info,
                    'active_tunnels': len(self.active_tunnels),
                    'running_processes': len(self.cloudflare_processes)
                }
            else:
                return {
                    'available': False,
                    'error': 'Cloudflared not found or not working',
                    'active_tunnels': len(self.active_tunnels)
                }
                
        except Exception as e:
            return {
                'available': False,
                'error': str(e),
                'active_tunnels': len(self.active_tunnels)
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
            print("[CloudflareManager] Started tunnel monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop tunnel monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        print("[CloudflareManager] Stopped tunnel monitoring")
    
    def add_event_callback(self, event: str, callback: callable) -> None:
        """Add a callback for tunnel events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def _initialize_cloudflared(self) -> None:
        """Initialize cloudflared and check availability."""
        try:
            # Check if cloudflared is installed
            result = self.shell_runner.run_command(
                f"{self.cloudflared_binary} version",
                capture_output=True
            )
            
            if result.returncode != 0:
                print("[CloudflareManager] Cloudflared not found, attempting to install...")
                self._install_cloudflared()
            else:
                print(f"[CloudflareManager] Cloudflared found: {result.stdout.strip()}")
            
        except Exception as e:
            print(f"[CloudflareManager] Error initializing cloudflared: {e}")
    
    def _install_cloudflared(self) -> None:
        """Install cloudflared if not available."""
        try:
            print("[CloudflareManager] Installing cloudflared...")
            
            # Install cloudflared based on platform
            if self.platform_info.platform in ["google_colab", "jupyter"]:
                # Download cloudflared binary for Colab/Jupyter
                install_commands = [
                    "wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb",
                    "sudo dpkg -i cloudflared-linux-amd64.deb",
                    "rm cloudflared-linux-amd64.deb"
                ]
            else:
                # Use system package manager
                install_commands = [
                    "curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb",
                    "sudo dpkg -i cloudflared.deb",
                    "rm cloudflared.deb"
                ]
            
            for cmd in install_commands:
                result = self.shell_runner.run_command(cmd, capture_output=True)
                if result.returncode != 0:
                    print(f"[CloudflareManager] Command failed: {cmd}")
                    print(f"Error: {result.stderr}")
                    break
            else:
                print("[CloudflareManager] Cloudflared installed successfully")
                
        except Exception as e:
            print(f"[CloudflareManager] Error installing cloudflared: {e}")
    
    def _create_quick_tunnel(self, local_port: int, tunnel_name: str) -> str:
        """Create a quick Cloudflare tunnel (temporary)."""
        try:
            print(f"[CloudflareManager] Creating quick tunnel for port {local_port}")
            
            # Start cloudflared tunnel
            cmd = [
                self.cloudflared_binary,
                "tunnel",
                "--url", f"http://localhost:{local_port}",
                "--no-autoupdate"
            ]
            
            # Create log file for this tunnel
            log_file = self.cloudflare_storage_path / f"{tunnel_name}.log"
            
            with open(log_file, 'w') as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid
                )
            
            # Store process
            tunnel_id = tunnel_name  # Use tunnel name as temporary ID
            self.cloudflare_processes[tunnel_id] = process
            
            # Wait for tunnel to establish and extract URL
            tunnel_url = self._extract_tunnel_url(log_file, timeout=30)
            
            if tunnel_url:
                return tunnel_url
            else:
                raise RuntimeError("Failed to extract tunnel URL from logs")
                
        except Exception as e:
            print(f"[CloudflareManager] Error creating quick tunnel: {e}")
            raise
    
    def _create_named_tunnel(self, tunnel_name: str, local_port: int, 
                           protocol: CloudflareProtocol) -> str:
        """Create a named Cloudflare tunnel (persistent)."""
        try:
            print(f"[CloudflareManager] Creating named tunnel: {tunnel_name}")
            
            # Create tunnel
            result = self.shell_runner.run_command(
                f"{self.cloudflared_binary} tunnel create {tunnel_name}",
                capture_output=True
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to create tunnel: {result.stderr}")
            
            # Extract tunnel ID from output
            tunnel_id = self._extract_tunnel_id(result.stdout)
            
            # Create configuration file
            config_file = self.cloudflare_storage_path / f"{tunnel_name}.yml"
            self._create_tunnel_config(config_file, tunnel_id, local_port, protocol)
            
            # Start tunnel
            cmd = [
                self.cloudflared_binary,
                "tunnel",
                "--config", str(config_file),
                "run", tunnel_name
            ]
            
            log_file = self.cloudflare_storage_path / f"{tunnel_name}_named.log"
            
            with open(log_file, 'w') as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid
                )
            
            # Store process
            self.cloudflare_processes[tunnel_name] = process
            
            return tunnel_id
            
        except Exception as e:
            print(f"[CloudflareManager] Error creating named tunnel: {e}")
            raise
    
    def _extract_tunnel_url(self, log_file: Path, timeout: int = 30) -> Optional[str]:
        """Extract tunnel URL from cloudflared logs."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if log_file.exists():
                    content = log_file.read_text()
                    
                    # Look for tunnel URL patterns
                    patterns = [
                        r'https://[a-zA-Z0-9-]+\.trycloudflare\.com',
                        r'https://[a-zA-Z0-9-]+\.cfargotunnel\.com'
                    ]
                    
                    import re
                    for pattern in patterns:
                        match = re.search(pattern, content)
                        if match:
                            return match.group(0)
                
                time.sleep(1)
                
            except Exception as e:
                print(f"[CloudflareManager] Error reading log file: {e}")
                time.sleep(1)
        
        return None
    
    def _extract_tunnel_id(self, output: str) -> str:
        """Extract tunnel ID from cloudflared output."""
        import re
        
        # Look for tunnel ID pattern
        match = re.search(r'tunnel ([a-f0-9-]+)', output)
        if match:
            return match.group(1)
        
        # Look for alternative patterns
        match = re.search(r'Created tunnel ([a-f0-9-]+)', output)
        if match:
            return match.group(1)
        
        raise RuntimeError("Could not extract tunnel ID from output")
    
    def _create_tunnel_config(self, config_file: Path, tunnel_id: str, 
                            local_port: int, protocol: CloudflareProtocol) -> None:
        """Create tunnel configuration file."""
        config = {
            'tunnel': tunnel_id,
            'credentials-file': f'/home/{os.getenv("USER", "user")}/.cloudflared/{tunnel_id}.json',
            'ingress': [
                {
                    'hostname': '*',
                    'service': f'{protocol.value}://localhost:{local_port}'
                },
                {
                    'service': 'http_status:404'
                }
            ]
        }
        
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def _get_tunnel_url(self, tunnel_id: str, tunnel_name: str) -> str:
        """Get the public URL for a named tunnel."""
        # For named tunnels, the URL is typically based on the tunnel ID
        return f"https://{tunnel_id}.cfargotunnel.com"
    
    def _cleanup_named_tunnel(self, tunnel_id: str) -> None:
        """Clean up a named tunnel."""
        try:
            # Delete the tunnel
            result = self.shell_runner.run_command(
                f"{self.cloudflared_binary} tunnel delete {tunnel_id}",
                capture_output=True
            )
            
            if result.returncode == 0:
                print(f"[CloudflareManager] Named tunnel {tunnel_id} deleted")
            else:
                print(f"[CloudflareManager] Failed to delete tunnel: {result.stderr}")
                
        except Exception as e:
            print(f"[CloudflareManager] Error cleaning up tunnel: {e}")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                with self.tunnel_lock:
                    for tunnel_id in list(self.active_tunnels.keys()):
                        tunnel = self.active_tunnels[tunnel_id]
                        
                        # Check tunnel health
                        is_healthy = self.check_tunnel_health(tunnel_id)
                        
                        if not is_healthy and tunnel.status == CloudflareStatus.CONNECTED:
                            # Tunnel went offline
                            tunnel.status = CloudflareStatus.DISCONNECTED
                            self._emit_event('tunnel_disconnected', tunnel)
                            
                            # Attempt automatic reconnection
                            if tunnel.reconnect_count < tunnel.max_reconnects:
                                print(f"[CloudflareManager] Attempting auto-reconnect for {tunnel_id}")
                                self.reconnect_tunnel(tunnel_id)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"[CloudflareManager] Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _save_tunnel_config(self, tunnel: CloudflareTunnel) -> None:
        """Save tunnel configuration to disk."""
        config_file = self.cloudflare_storage_path / f"{tunnel.tunnel_id}.json"
        try:
            self.json_handler.write_json_file(str(config_file), tunnel.to_dict())
        except Exception as e:
            print(f"[CloudflareManager] Error saving tunnel config: {e}")
    
    def _remove_tunnel_config(self, tunnel_id: str) -> None:
        """Remove tunnel configuration from disk."""
        config_file = self.cloudflare_storage_path / f"{tunnel_id}.json"
        try:
            if config_file.exists():
                config_file.unlink()
        except Exception as e:
            print(f"[CloudflareManager] Error removing tunnel config: {e}")
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[CloudflareManager] Error in event callback: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_monitoring()
        
        # Stop all cloudflared processes
        for tunnel_id, process in self.cloudflare_processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass


def main():
    """Test the Cloudflare manager functionality."""
    print("Testing CloudflareManager...")
    
    manager = CloudflareManager()
    
    # Get cloudflared status
    status = manager.get_cloudflared_status()
    print(f"Cloudflared status: {status}")
    
    # Test creating a tunnel (would need a running web server)
    try:
        # This would create a tunnel for a web server on port 8000
        # tunnel = manager.create_tunnel(8000, "test_app")
        # print(f"Created tunnel: {tunnel.public_url}")
        
        # List active tunnels
        tunnels = manager.list_active_tunnels()
        print(f"Active tunnels: {len(tunnels)}")
        
        print("CloudflareManager test completed")
        
    except Exception as e:
        print(f"CloudflareManager test error: {e}")


if __name__ == "__main__":
    main()