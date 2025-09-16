"""
Tunnel Manager Module - Handles ngrok and alternative tunneling solutions
"""

import os
import subprocess
import requests
import json
import time
import zipfile
import logging
import threading
import platform
import socket
from pathlib import Path
from typing import Optional, Dict, Any, List
from functools import wraps
from dataclasses import dataclass


@dataclass
class TunnelInfo:
    """Information about an active tunnel"""
    service: str
    url: str
    port: int
    process: Optional[subprocess.Popen] = None
    tunnel_object: Optional[Any] = None
    status: str = "active"
    created_at: float = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


def retry_on_failure(max_attempts=3, delay=2, backoff=2):
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


class TunnelManager:
    """Manages tunneling services for remote access with robust error handling"""
    
    TUNNEL_SERVICES = ['ngrok', 'cloudflare', 'localtunnel', 'bore', 'pagekite']
    NGROK_DOWNLOAD_URLS = {
        'linux': 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip',
        'darwin': 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-darwin-amd64.zip',
        'windows': 'https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip'
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.active_tunnels: Dict[str, TunnelInfo] = {}
        self.ngrok_process = None
        self.cloudflared_process = None
        self.localtunnel_process = None
        self.logger = logger or self._setup_logger()
        self.tunnel_monitor_thread = None
        self.monitoring = False

    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger('TunnelManager')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _check_port_availability(self, port: int) -> bool:
        """Check if a port is available for binding"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False

    def _verify_tunnel_connectivity(self, url: str, timeout: int = 10) -> bool:
        """Verify that a tunnel URL is accessible"""
        try:
            response = requests.get(url, timeout=timeout)
            return response.status_code < 500
        except:
            return False

    @retry_on_failure(max_attempts=3, delay=2)
    def install_ngrok(self) -> bool:
        """Install ngrok binary with platform detection"""
        try:
            self.logger.info("📥 Installing ngrok...")

            # Detect platform
            system = platform.system().lower()
            if system == 'linux':
                url = self.NGROK_DOWNLOAD_URLS['linux']
            elif system == 'darwin':
                url = self.NGROK_DOWNLOAD_URLS['darwin']
            elif system == 'windows':
                url = self.NGROK_DOWNLOAD_URLS['windows']
            else:
                self.logger.error(f"Unsupported platform: {system}")
                return False

            # Create temp directory
            temp_dir = Path("/tmp") if system != 'windows' else Path(os.environ.get('TEMP', '/tmp'))
            temp_dir.mkdir(exist_ok=True)

            # Download ngrok with progress
            self.logger.info(f"Downloading from {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            zip_path = temp_dir / "ngrok.zip"

            with open(zip_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"Download progress: {progress:.1f}%", end='\r')
            print()  # New line after progress

            # Extract ngrok
            install_dir = Path("/usr/local/bin") if system != 'windows' else Path.home() / "bin"
            install_dir.mkdir(exist_ok=True, parents=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(install_dir)

            # Make executable
            ngrok_path = install_dir / "ngrok"
            if system != 'windows':
                os.chmod(ngrok_path, 0o755)

            # Verify installation
            try:
                result = subprocess.run([str(ngrok_path), "version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.logger.info(f"✅ ngrok installed: {result.stdout.strip()}")
                    return True
            except:
                pass

            self.logger.error("ngrok installation verification failed")
            return False

        except Exception as e:
            self.logger.error(f"⚠️ ngrok installation failed: {e}")
            raise

    def setup_ngrok(self, auth_token: str = None) -> bool:
        """Setup ngrok with authentication token"""
        try:
            # Find ngrok binary
            ngrok_paths = [
                "/usr/local/bin/ngrok",
                str(Path.home() / "bin" / "ngrok"),
                "ngrok"  # In PATH
            ]

            ngrok_path = None
            for path in ngrok_paths:
                if subprocess.run(["which", path], capture_output=True).returncode == 0:
                    ngrok_path = path
                    break

            # Install if not present
            if not ngrok_path:
                if not self.install_ngrok():
                    return False
                ngrok_path = ngrok_paths[0]

            # Set auth token if provided
            if auth_token:
                self.logger.info("Configuring ngrok auth token...")
                result = subprocess.run(
                    [ngrok_path, "config", "add-authtoken", auth_token],
                    capture_output=True, text=True
                )

                if result.returncode == 0:
                    self.logger.info("✅ ngrok auth token configured")
                else:
                    self.logger.warning(f"Failed to set auth token: {result.stderr}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"❌ ngrok setup failed: {e}")
            return False

    @retry_on_failure(max_attempts=2, delay=3)
    def start_ngrok_tunnel(self, port: int, auth_token: str = None, region: str = None, subdomain: str = None) -> Optional[str]:
        """Start ngrok tunnel with enhanced options and error handling"""
        try:
            # Check port availability
            if not self._check_port_availability(port):
                self.logger.warning(f"Port {port} is not available")
                # Don't raise, let the tunnel try anyway

            # Setup ngrok if needed
            if auth_token:
                if not self.setup_ngrok(auth_token):
                    self.logger.warning("ngrok setup failed, trying anyway")

            # Try using pyngrok library first
            try:
                from pyngrok import ngrok as pyngrok, conf

                # Configure pyngrok
                pyngrok_config = conf.PyngrokConfig()
                if auth_token:
                    pyngrok.set_auth_token(auth_token)
                if region:
                    pyngrok_config.region = region

                # Start tunnel with options
                options = {"bind_tls": True}
                if subdomain and auth_token:  # Subdomain requires auth
                    options["subdomain"] = subdomain

                tunnel = pyngrok.connect(port, "http", options=options, pyngrok_config=pyngrok_config)

                # Get HTTPS URL
                url = tunnel.public_url
                if url.startswith("http://"):
                    url = url.replace("http://", "https://")

                # Verify tunnel is working
                time.sleep(2)
                if self._verify_tunnel_connectivity(url):
                    self.logger.info(f"✅ Tunnel verified as working")

                # Store tunnel info
                tunnel_info = TunnelInfo(
                    service="ngrok",
                    url=url,
                    port=port,
                    tunnel_object=tunnel
                )
                self.active_tunnels['ngrok'] = tunnel_info

                self.logger.info(f"🌐 ngrok tunnel started: {url}")
                return url

            except ImportError:
                self.logger.info("pyngrok not available, using binary fallback")

                # Find ngrok binary
                ngrok_path = None
                for path in ["/usr/local/bin/ngrok", "ngrok"]:
                    if subprocess.run(["which", path], capture_output=True).returncode == 0:
                        ngrok_path = path
                        break

                if not ngrok_path:
                    raise Exception("ngrok binary not found")

                # Build command
                cmd = [ngrok_path, "http", str(port), "--log-level", "info"]
                if region:
                    cmd.extend(["--region", region])
                if subdomain and auth_token:
                    cmd.extend(["--subdomain", subdomain])

                # Start ngrok
                self.ngrok_process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                # Wait for tunnel to establish
                max_wait = 10
                for i in range(max_wait):
                    time.sleep(1)
                    try:
                        response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
                        data = response.json()

                        for tunnel in data.get('tunnels', []):
                            if tunnel.get('proto') == 'https':
                                url = tunnel['public_url']

                                # Store tunnel info
                                tunnel_info = TunnelInfo(
                                    service="ngrok",
                                    url=url,
                                    port=port,
                                    process=self.ngrok_process
                                )
                                self.active_tunnels['ngrok'] = tunnel_info

                                self.logger.info(f"🌐 ngrok tunnel started: {url}")
                                return url
                    except:
                        if i == max_wait - 1:
                            raise
                raise Exception("Could not get ngrok URL after waiting")

        except Exception as e:
            self.logger.error(f"❌ ngrok tunnel failed: {e}")
            raise

    @retry_on_failure(max_attempts=3, delay=2)
    def install_cloudflared(self) -> bool:
        """Install Cloudflare Tunnel (cloudflared) with platform detection"""
        try:
            self.logger.info("📥 Installing cloudflared...")
            
            # Detect platform
            system = platform.system().lower()
            if system == 'linux':
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
            elif system == 'darwin':
                url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
            else:
                self.logger.error(f"Unsupported platform: {system}")
                return False
            
            # Download
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Save binary
            binary_path = "/usr/local/bin/cloudflared" if system != 'windows' else str(Path.home() / "bin" / "cloudflared.exe")
            Path(binary_path).parent.mkdir(exist_ok=True, parents=True)
            
            with open(binary_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Make executable
            if system != 'windows':
                os.chmod(binary_path, 0o755)
            
            self.logger.info("✅ cloudflared installed")
            return True
            
        except Exception as e:
            self.logger.error(f"⚠️ cloudflared installation failed: {e}")
            raise
    
    @retry_on_failure(max_attempts=2, delay=3)
    def start_cloudflare_tunnel(self, port: int, hostname: str = None) -> Optional[str]:
        """Start Cloudflare Tunnel with enhanced error handling"""
        try:
            # Check port availability
            if not self._check_port_availability(port):
                self.logger.warning(f"Port {port} is not available")
            
            # Find cloudflared binary
            cloudflared_paths = [
                "/usr/local/bin/cloudflared",
                str(Path.home() / "bin" / "cloudflared"),
                "cloudflared"  # In PATH
            ]
            
            cloudflared_path = None
            for path in cloudflared_paths:
                try:
                    result = subprocess.run([path, "version"], capture_output=True, timeout=2)
                    if result.returncode == 0:
                        cloudflared_path = path
                        break
                except:
                    continue
            
            # Install if not present
            if not cloudflared_path:
                if not self.install_cloudflared():
                    raise Exception("Failed to install cloudflared")
                cloudflared_path = cloudflared_paths[0]
            
            self.logger.info("🚇 Starting Cloudflare Tunnel...")
            
            # Build command
            cmd = [
                cloudflared_path, "tunnel",
                "--url", f"http://localhost:{port}",
                "--no-autoupdate",
                "--metrics", "localhost:0"  # Disable metrics server
            ]
            
            if hostname:
                cmd.extend(["--hostname", hostname])
            
            # Start cloudflared
            self.cloudflared_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Parse output for URL with timeout
            import re
            url_pattern = re.compile(r'https://[^\s]+\.trycloudflare\.com')
            
            start_time = time.time()
            timeout = 30  # 30 seconds timeout
            
            while time.time() - start_time < timeout:
                if self.cloudflared_process.poll() is not None:
                    # Process ended
                    stderr = self.cloudflared_process.stderr.read()
                    raise Exception(f"cloudflared process ended unexpectedly: {stderr}")
                
                line = self.cloudflared_process.stderr.readline()
                if line:
                    self.logger.debug(f"cloudflared: {line.strip()}")
                    
                    if "https://" in line and ".trycloudflare.com" in line:
                        match = url_pattern.search(line)
                        if match:
                            url = match.group(0)
                            
                            # Verify tunnel is working
                            time.sleep(2)
                            if self._verify_tunnel_connectivity(url):
                                self.logger.info("✅ Tunnel verified as working")
                            
                            # Store tunnel info
                            tunnel_info = TunnelInfo(
                                service="cloudflare",
                                url=url,
                                port=port,
                                process=self.cloudflared_process
                            )
                            self.active_tunnels['cloudflare'] = tunnel_info
                            
                            self.logger.info(f"🌐 Cloudflare tunnel started: {url}")
                            return url
                
                time.sleep(0.1)  # Small sleep to avoid busy waiting
            
            raise Exception(f"Timeout waiting for Cloudflare tunnel URL after {timeout} seconds")
            
        except Exception as e:
            self.logger.error(f"❌ Cloudflare tunnel failed: {e}")
            # Clean up process if it's still running
            if self.cloudflared_process and self.cloudflared_process.poll() is None:
                self.cloudflared_process.terminate()
                self.cloudflared_process = None
            raise
    
    @retry_on_failure(max_attempts=2, delay=3)
    def start_localtunnel(self, port: int, subdomain: str = None, host: str = "https://localtunnel.me") -> Optional[str]:
        """Start LocalTunnel with enhanced error handling"""
        try:
            self.logger.info("🚇 Starting LocalTunnel...")
            
            # Check if npm/npx is available
            npm_available = subprocess.run(["which", "npm"], capture_output=True).returncode == 0
            
            if not npm_available:
                self.logger.warning("npm not found, trying to install Node.js dependencies...")
                # Try to install Node.js if not present
                try:
                    subprocess.run(["apt-get", "install", "-y", "nodejs", "npm"], 
                                 capture_output=True, check=False)
                except:
                    raise Exception("Node.js/npm not available and could not be installed")
            
            # Install localtunnel if not present
            self.logger.info("Installing localtunnel package...")
            install_result = subprocess.run(
                ["npm", "install", "-g", "localtunnel"],
                capture_output=True,
                text=True
            )
            
            if install_result.returncode != 0:
                self.logger.warning(f"Global install failed: {install_result.stderr}")
                # Try local install
                subprocess.run(["npm", "install", "localtunnel"], capture_output=True)
                lt_cmd = ["npx", "localtunnel"]
            else:
                lt_cmd = ["lt"]  # Global install successful
            
            # Build command
            cmd = lt_cmd + ["--port", str(port), "--host", host]
            if subdomain:
                cmd.extend(["--subdomain", subdomain])
            
            self.logger.debug(f"Running command: {' '.join(cmd)}")
            
            # Start localtunnel
            self.localtunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Parse output for URL with timeout
            import re
            url_pattern = re.compile(r'https://[^\s]+\.(loca\.lt|localtunnel\.me)')
            
            start_time = time.time()
            timeout = 20
            
            while time.time() - start_time < timeout:
                if self.localtunnel_process.poll() is not None:
                    # Process ended
                    stderr = self.localtunnel_process.stderr.read()
                    stdout = self.localtunnel_process.stdout.read()
                    raise Exception(f"LocalTunnel process ended: stdout={stdout}, stderr={stderr}")
                
                line = self.localtunnel_process.stdout.readline()
                if line:
                    self.logger.debug(f"LocalTunnel: {line.strip()}")
                    
                    if "https://" in line:
                        match = url_pattern.search(line)
                        if match:
                            url = match.group(0)
                            
                            # Store tunnel info
                            tunnel_info = TunnelInfo(
                                service="localtunnel",
                                url=url,
                                port=port,
                                process=self.localtunnel_process
                            )
                            self.active_tunnels['localtunnel'] = tunnel_info
                            
                            self.logger.info(f"🌐 LocalTunnel started: {url}")
                            self.logger.info("Note: LocalTunnel may require password authentication")
                            return url
                
                time.sleep(0.1)
            
            raise Exception(f"Timeout waiting for LocalTunnel URL after {timeout} seconds")
            
        except Exception as e:
            self.logger.error(f"❌ LocalTunnel failed: {e}")
            # Clean up process
            if self.localtunnel_process and self.localtunnel_process.poll() is None:
                self.localtunnel_process.terminate()
                self.localtunnel_process = None
            raise
    
    def start_tunnel(self, port: int, service: str = "auto", 
                    ngrok_token: str = None, subdomain: str = None,
                    region: str = None, hostname: str = None) -> Optional[str]:
        """Start tunnel with specified or auto-selected service and fallback support"""
        
        if service == "auto":
            # Try services in order of preference
            services = ["cloudflare", "ngrok", "localtunnel"]  # Cloudflare first (no auth needed)
        else:
            services = [service]
        
        # Add fallback services if specific service requested
        if service != "auto" and len(services) == 1:
            # Add other services as fallbacks
            all_services = ["cloudflare", "ngrok", "localtunnel"]
            for svc in all_services:
                if svc != service:
                    services.append(svc)
        
        last_error = None
        
        for i, svc in enumerate(services):
            try:
                self.logger.info(f"Attempting to start {svc} tunnel (attempt {i+1}/{len(services)})...")
                url = None
                
                if svc == "ngrok":
                    if not ngrok_token and i > 0:
                        self.logger.warning("Skipping ngrok (no auth token provided)")
                        continue
                    url = self.start_ngrok_tunnel(port, ngrok_token, region, subdomain)
                    
                elif svc == "cloudflare":
                    url = self.start_cloudflare_tunnel(port, hostname)
                    
                elif svc == "localtunnel":
                    url = self.start_localtunnel(port, subdomain)
                
                if url:
                    self.logger.info(f"✅ Successfully started {svc} tunnel")
                    return url
                    
            except Exception as e:
                last_error = e
                self.logger.warning(f"{svc} tunnel failed: {e}")
                if i < len(services) - 1:
                    self.logger.info("Trying next tunneling service...")
        
        error_msg = f"No tunneling service could be started. Last error: {last_error}"
        self.logger.error(f"❌ {error_msg}")
        raise Exception(error_msg)
    
    def stop_tunnel(self, service: str = None) -> bool:
        """Stop active tunnel(s) with proper cleanup"""
        if service:
            services = [service]
        else:
            services = list(self.active_tunnels.keys())
        
        stopped_count = 0
        
        for svc in services:
            if svc in self.active_tunnels:
                tunnel_info = self.active_tunnels[svc]
                
                try:
                    # Stop pyngrok tunnel
                    if tunnel_info.tunnel_object:
                        try:
                            from pyngrok import ngrok as pyngrok
                            pyngrok.disconnect(tunnel_info.tunnel_object.public_url)
                            self.logger.debug(f"Disconnected pyngrok tunnel for {svc}")
                        except Exception as e:
                            self.logger.debug(f"Error disconnecting pyngrok: {e}")
                    
                    # Stop subprocess
                    if tunnel_info.process:
                        if tunnel_info.process.poll() is None:
                            tunnel_info.process.terminate()
                            try:
                                tunnel_info.process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                # Force kill if terminate doesn't work
                                tunnel_info.process.kill()
                                tunnel_info.process.wait(timeout=2)
                            self.logger.debug(f"Terminated process for {svc}")
                    
                    # Update status
                    tunnel_info.status = "stopped"
                    
                    # Remove from active tunnels
                    del self.active_tunnels[svc]
                    self.logger.info(f"🛑 Stopped {svc} tunnel")
                    stopped_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error stopping {svc} tunnel: {e}")
        
        return stopped_count > 0
    
    def get_active_tunnels(self) -> Dict[str, TunnelInfo]:
        """Get information about active tunnels"""
        # Clean up any dead tunnels
        dead_tunnels = []
        for name, info in self.active_tunnels.items():
            if info.process and info.process.poll() is not None:
                dead_tunnels.append(name)
                info.status = "dead"
        
        for name in dead_tunnels:
            self.logger.warning(f"Tunnel {name} found dead, removing")
            del self.active_tunnels[name]
        
        return self.active_tunnels
    
    def stop_all_tunnels(self) -> bool:
        """Stop all active tunnels with cleanup"""
        self.logger.info("Stopping all tunnels...")
        
        # Stop monitoring if active
        if self.monitoring:
            self.monitoring = False
            if self.tunnel_monitor_thread:
                self.tunnel_monitor_thread.join(timeout=2)
        
        # Stop all registered tunnels
        success = self.stop_tunnel()
        
        # Kill any remaining processes (cleanup)
        processes_to_kill = [
            (self.ngrok_process, "ngrok"),
            (self.cloudflared_process, "cloudflared"),
            (self.localtunnel_process, "localtunnel")
        ]
        
        for process, name in processes_to_kill:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=3)
                    self.logger.debug(f"Terminated orphaned {name} process")
                except:
                    try:
                        process.kill()
                        self.logger.debug(f"Force killed orphaned {name} process")
                    except:
                        pass
        
        # Clear process references
        self.ngrok_process = None
        self.cloudflared_process = None
        self.localtunnel_process = None
        
        self.logger.info("🛑 All tunnels stopped")
        return success
    
    def monitor_tunnels(self, check_interval: int = 30) -> None:
        """Monitor active tunnels and restart if needed"""
        def monitor_loop():
            while self.monitoring:
                for name, info in list(self.active_tunnels.items()):
                    if info.process and info.process.poll() is not None:
                        self.logger.warning(f"Tunnel {name} died, attempting restart...")
                        # Try to restart the tunnel
                        try:
                            if name == "ngrok":
                                url = self.start_ngrok_tunnel(info.port)
                            elif name == "cloudflare":
                                url = self.start_cloudflare_tunnel(info.port)
                            elif name == "localtunnel":
                                url = self.start_localtunnel(info.port)
                            
                            if url:
                                self.logger.info(f"Successfully restarted {name} tunnel")
                        except Exception as e:
                            self.logger.error(f"Failed to restart {name} tunnel: {e}")
                
                time.sleep(check_interval)
        
        if not self.monitoring:
            self.monitoring = True
            self.tunnel_monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            self.tunnel_monitor_thread.start()
            self.logger.info(f"Started tunnel monitoring (checking every {check_interval}s)")
        else:
            self.logger.info("Tunnel monitoring already active")
