"""
Pinokio Controller Module - JSON-RPC API integration for AI tool management
"""

import os
import subprocess
import requests
import json
import time
import logging
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path
from functools import wraps
from dataclasses import dataclass
from datetime import datetime
import socket


@dataclass
class AppInfo:
    """Information about an installed app"""
    name: str
    status: str
    url: Optional[str] = None
    port: Optional[int] = None
    pid: Optional[int] = None
    description: Optional[str] = None
    installed_at: Optional[datetime] = None
    last_launched: Optional[datetime] = None


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
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


class PinokioController:
    """Controls Pinokio via JSON-RPC API with enhanced error handling"""
    
    def __init__(self, pinokio_path: str, api_port: int = 42000, timeout: int = 30):
        self.pinokio_path = pinokio_path
        self.api_port = api_port
        self.api_url = f"http://localhost:{api_port}/api"
        self.pinokio_process = None
        self.timeout = timeout
        self.session = requests.Session()  # Connection pooling
        self.session.headers.update({"Content-Type": "application/json"})
        self.installed_apps = {}  # Cache of installed apps
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
    @retry_on_failure(max_retries=3, delay=2.0)
    def start_server(self, headless: bool = True, port: int = None) -> bool:
        """Start Pinokio server with retry logic"""
        try:
            if port:
                self.api_port = port
                self.api_url = f"http://localhost:{port}/api"
            
            # Check if port is available
            if not self._is_port_available(self.api_port):
                # Check if it's our server
                if self.is_running():
                    self.logger.info("✅ Pinokio server already running")
                    return True
                else:
                    raise Exception(f"Port {self.api_port} is already in use by another process")
            
            self.logger.info(f"🚀 Starting Pinokio server on port {self.api_port}...")
            
            # Build command based on platform
            pinokio_binary = self._get_pinokio_binary()
            if not os.path.exists(pinokio_binary):
                raise FileNotFoundError(f"Pinokio binary not found at {pinokio_binary}")
            
            cmd = [
                pinokio_binary,
                "--no-sandbox",
                f"--api-port={self.api_port}"
            ]
            
            if headless:
                cmd.append("--headless")
            
            # Set environment
            env = os.environ.copy()
            if headless and not env.get('DISPLAY'):
                env['DISPLAY'] = ':99'
            
            # Ensure Xvfb is running if needed
            if headless and not self._check_xvfb():
                self._start_xvfb()
            
            # Start Pinokio
            self.pinokio_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True
            )
            
            # Wait for server to start with better feedback
            startup_timeout = self.timeout
            start_time = time.time()
            
            while time.time() - start_time < startup_timeout:
                if self.is_running():
                    self.logger.info("✅ Pinokio server started successfully")
                    return True
                
                # Check if process died
                if self.pinokio_process.poll() is not None:
                    stdout, stderr = self.pinokio_process.communicate()
                    error_msg = f"Pinokio process died. Stderr: {stderr}"
                    self.logger.error(error_msg)
                    raise Exception(error_msg)
                
                time.sleep(1)
            
            raise TimeoutError(f"Pinokio server startup timeout after {startup_timeout}s")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start Pinokio server: {e}")
            # Clean up process if it exists
            if self.pinokio_process and self.pinokio_process.poll() is None:
                self.pinokio_process.terminate()
                self.pinokio_process = None
            raise
    
    def stop_server(self) -> bool:
        """Stop Pinokio server with cleanup"""
        try:
            stopped = False
            
            # Try graceful shutdown via API first
            if self.is_running():
                try:
                    self.rpc_call("server.shutdown")
                    time.sleep(2)
                    stopped = True
                except:
                    pass
            
            # Stop process if still running
            if self.pinokio_process:
                if self.pinokio_process.poll() is None:
                    self.logger.info("Terminating Pinokio process...")
                    self.pinokio_process.terminate()
                    try:
                        self.pinokio_process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        self.logger.warning("Force killing Pinokio process")
                        self.pinokio_process.kill()
                        self.pinokio_process.wait(timeout=5)
                
                self.pinokio_process = None
                stopped = True
            
            # Clear session
            self.session.close()
            self.session = requests.Session()
            self.session.headers.update({"Content-Type": "application/json"})
            
            if stopped:
                self.logger.info("🛑 Pinokio server stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"⚠️ Error stopping server: {e}")
            return False
    
    def is_running(self) -> bool:
        """Check if Pinokio server is running and responsive"""
        try:
            response = self.session.get(
                f"{self.api_url}/status", 
                timeout=2
            )
            if response.status_code == 200:
                # Verify it's actually Pinokio
                data = response.json()
                return data.get("pinokio", False) or "version" in data
            return False
        except requests.exceptions.RequestException:
            return False
        except Exception as e:
            self.logger.debug(f"Error checking server status: {e}")
            return False
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def rpc_call(self, method: str, params: Dict = None, timeout: int = None) -> Optional[Dict]:
        """Make JSON-RPC API call with retry and error handling"""
        if not self.is_running():
            raise ConnectionError("Pinokio server is not running")
        
        try:
            # Generate unique request ID
            request_id = int(time.time() * 1000) % 1000000
            
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
                "id": request_id
            }
            
            self.logger.debug(f"RPC call: {method} with params: {params}")
            
            response = self.session.post(
                self.api_url,
                json=payload,
                timeout=timeout or self.timeout
            )
            
            # Check HTTP status
            if response.status_code == 404:
                raise Exception(f"Method not found: {method}")
            elif response.status_code == 500:
                raise Exception(f"Server error for method: {method}")
            
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Check for JSON-RPC error
            if "error" in data:
                error = data["error"]
                error_msg = error.get("message", "Unknown error")
                error_code = error.get("code", -1)
                
                # Handle specific error codes
                if error_code == -32601:
                    raise Exception(f"Method not found: {method}")
                elif error_code == -32602:
                    raise ValueError(f"Invalid params for {method}: {params}")
                elif error_code == -32603:
                    raise Exception(f"Internal error: {error_msg}")
                else:
                    raise Exception(f"RPC Error ({error_code}): {error_msg}")
            
            # Verify response ID matches
            if data.get("id") != request_id:
                self.logger.warning(f"Response ID mismatch: expected {request_id}, got {data.get('id')}")
            
            result = data.get("result")
            self.logger.debug(f"RPC response: {result}")
            return result
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"RPC call {method} timed out after {timeout or self.timeout}s")
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to Pinokio server: {e}")
        except Exception as e:
            self.logger.error(f"RPC call {method} failed: {e}")
            raise
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('localhost', port))
                return True
            except OSError:
                return False
    
    def _get_pinokio_binary(self) -> str:
        """Get the correct Pinokio binary path based on platform"""
        import platform
        system = platform.system().lower()
        
        if system == "linux":
            return os.path.join(self.pinokio_path, "Pinokio-linux.AppImage")
        elif system == "darwin":
            return os.path.join(self.pinokio_path, "Pinokio.app", "Contents", "MacOS", "Pinokio")
        elif system == "windows":
            return os.path.join(self.pinokio_path, "Pinokio.exe")
        else:
            # Default to Linux AppImage
            return os.path.join(self.pinokio_path, "Pinokio-linux.AppImage")
    
    def _check_xvfb(self) -> bool:
        """Check if Xvfb is running"""
        try:
            result = subprocess.run(['pgrep', 'Xvfb'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _start_xvfb(self) -> bool:
        """Start Xvfb virtual display"""
        try:
            subprocess.run([
                'Xvfb', ':99', '-screen', '0', '1024x768x24', '-ac', '+extension', 'GLX'
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
            return self._check_xvfb()
        except Exception as e:
            self.logger.warning(f"Failed to start Xvfb: {e}")
            return False
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def list_apps(self) -> Optional[List[AppInfo]]:
        """List available AI applications with caching"""
        try:
            result = self.rpc_call("apps.list")
            if result:
                apps = []
                for app_data in result:
                    app_info = AppInfo(
                        name=app_data.get('name', 'Unknown'),
                        status=app_data.get('status', 'unknown'),
                        url=app_data.get('url'),
                        port=app_data.get('port'),
                        pid=app_data.get('pid'),
                        description=app_data.get('description', ''),
                        installed_at=datetime.now() if app_data.get('installed') else None
                    )
                    apps.append(app_info)
                    # Cache the app info
                    self.installed_apps[app_info.name] = app_info
                
                self.logger.info(f"📱 Found {len(apps)} available apps")
                for app in apps:
                    self.logger.info(f"  - {app.name}: {app.description}")
                return apps
            return []
        except Exception as e:
            self.logger.error(f"Failed to list apps: {e}")
            return None
    
    @retry_on_failure(max_retries=2, delay=2.0)
    def install_app(self, app_url: str, name: str = None, timeout: int = 300) -> Optional[AppInfo]:
        """Install an AI application from URL with progress tracking"""
        try:
            self.logger.info(f"📦 Installing app from {app_url}...")
            
            # Validate URL
            if not app_url.startswith(('http://', 'https://', 'git://')):
                raise ValueError(f"Invalid app URL: {app_url}")
            
            params = {
                "url": app_url,
                "method": "fs.download"
            }
            
            if name:
                params["name"] = name
            
            # Start installation
            result = self.rpc_call("app.install", params, timeout=timeout)
            
            if result:
                app_name = result.get('name', name or 'Unknown')
                app_info = AppInfo(
                    name=app_name,
                    status='installed',
                    description=result.get('description', ''),
                    installed_at=datetime.now()
                )
                
                # Cache the app info
                self.installed_apps[app_name] = app_info
                
                self.logger.info(f"✅ App installed: {app_name}")
                return app_info
            
            raise Exception("Installation returned no result")
            
        except Exception as e:
            self.logger.error(f"❌ App installation failed: {e}")
            raise
    
    @retry_on_failure(max_retries=2, delay=3.0)
    def launch_app(self, app_name: str, config: Dict = None, wait_for_ready: bool = True) -> Optional[AppInfo]:
        """Launch an installed AI application with readiness check"""
        try:
            self.logger.info(f"🚀 Launching {app_name}...")
            
            # Check if app is already running
            if app_name in self.installed_apps:
                app_info = self.installed_apps[app_name]
                if app_info.status == 'running' and app_info.url:
                    self.logger.info(f"App {app_name} is already running at {app_info.url}")
                    return app_info
            
            params = {
                "name": app_name,
                "config": config or {}
            }
            
            result = self.rpc_call("app.launch", params, timeout=60)
            
            if result:
                app_info = AppInfo(
                    name=app_name,
                    status='running',
                    url=result.get('url'),
                    port=result.get('port'),
                    pid=result.get('pid'),
                    last_launched=datetime.now()
                )
                
                # Update cached info
                if app_name in self.installed_apps:
                    cached_info = self.installed_apps[app_name]
                    app_info.description = cached_info.description
                    app_info.installed_at = cached_info.installed_at
                
                self.installed_apps[app_name] = app_info
                
                self.logger.info(f"✅ App launched: {app_name}")
                if app_info.url:
                    self.logger.info(f"📍 Access at: {app_info.url}")
                
                # Wait for app to be ready if requested
                if wait_for_ready and app_info.url:
                    self._wait_for_app_ready(app_info.url)
                
                return app_info
            
            raise Exception("Launch returned no result")
            
        except Exception as e:
            self.logger.error(f"❌ App launch failed: {e}")
            raise
    
    def _wait_for_app_ready(self, url: str, timeout: int = 60) -> bool:
        """Wait for app to be ready by checking its URL"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.logger.info(f"App is ready at {url}")
                    return True
            except:
                pass
            time.sleep(2)
        
        self.logger.warning(f"App at {url} may not be ready after {timeout}s")
        return False
    
    @retry_on_failure(max_retries=2, delay=2.0)
    def stop_app(self, app_name: str) -> bool:
        """Stop a running AI application with cleanup"""
        try:
            self.logger.info(f"🛑 Stopping {app_name}...")
            
            result = self.rpc_call("app.stop", {"name": app_name}, timeout=30)
            
            if result:
                # Update cached info
                if app_name in self.installed_apps:
                    self.installed_apps[app_name].status = 'stopped'
                    self.installed_apps[app_name].url = None
                    self.installed_apps[app_name].pid = None
                
                self.logger.info(f"✅ App stopped: {app_name}")
                return True
            
            raise Exception("Stop command returned no result")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to stop app: {e}")
            raise
    
    def get_app_status(self, app_name: str) -> Optional[AppInfo]:
        """Get status of an AI application with caching"""
        try:
            result = self.rpc_call("app.status", {"name": app_name})
            if result:
                status = result.get("status", "unknown")
                
                # Update or create app info
                if app_name in self.installed_apps:
                    app_info = self.installed_apps[app_name]
                    app_info.status = status
                    app_info.url = result.get('url')
                    app_info.port = result.get('port')
                    app_info.pid = result.get('pid')
                else:
                    app_info = AppInfo(
                        name=app_name,
                        status=status,
                        url=result.get('url'),
                        port=result.get('port'),
                        pid=result.get('pid')
                    )
                    self.installed_apps[app_name] = app_info
                
                self.logger.info(f"📊 {app_name} status: {status}")
                return app_info
            
            return None
        except Exception as e:
            self.logger.error(f"Failed to get app status: {e}")
            return None
    
    @retry_on_failure(max_retries=2, delay=2.0)
    def execute_script(self, script_path: str, params: Dict = None, timeout: int = 120) -> Optional[Dict]:
        """Execute a Pinokio script with validation and error handling"""
        try:
            self.logger.info(f"📜 Executing script: {script_path}")
            
            # Validate script file exists
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"Script file not found: {script_path}")
            
            # Load and validate script
            with open(script_path, 'r', encoding='utf-8') as f:
                try:
                    script = json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in script file: {e}")
            
            # Basic script validation
            if not isinstance(script, (dict, list)):
                raise ValueError("Script must be a JSON object or array")
            
            rpc_params = {
                "script": script,
                "params": params or {}
            }
            
            result = self.rpc_call("script.run", rpc_params, timeout=timeout)
            
            if result:
                self.logger.info(f"✅ Script executed successfully")
                return result
            
            raise Exception("Script execution returned no result")
            
        except Exception as e:
            self.logger.error(f"❌ Script execution failed: {e}")
            raise
    
    def install_popular_tools(self, tools: List[str] = None, parallel: bool = False) -> Dict[str, AppInfo]:
        """Install popular AI tools with progress tracking"""
        available_tools = {
            "stable-diffusion": "https://github.com/AUTOMATIC1111/stable-diffusion-webui",
            "comfyui": "https://github.com/comfyanonymous/ComfyUI",
            "text-generation-webui": "https://github.com/oobabooga/text-generation-webui",
            "kohya-ss": "https://github.com/bmaltais/kohya_ss",
            "invokeai": "https://github.com/invoke-ai/InvokeAI",
            "fooocus": "https://github.com/lllyasviel/Fooocus",
            "controlnet": "https://github.com/lllyasviel/ControlNet"
        }
        
        # Use provided tools or install all popular ones
        tools_to_install = tools or list(available_tools.keys())
        
        # Validate tool names
        invalid_tools = [t for t in tools_to_install if t not in available_tools]
        if invalid_tools:
            self.logger.warning(f"Unknown tools will be skipped: {invalid_tools}")
            tools_to_install = [t for t in tools_to_install if t in available_tools]
        
        self.logger.info(f"Installing {len(tools_to_install)} AI tools...")
        
        results = {}
        failed_count = 0
        
        for i, name in enumerate(tools_to_install, 1):
            try:
                url = available_tools[name]
                self.logger.info(f"\n🔧 Installing {name} ({i}/{len(tools_to_install)})...")
                
                app_info = self.install_app(url, name)
                results[name] = app_info
                
                if not parallel:
                    time.sleep(3)  # Rate limiting for sequential installs
                    
            except Exception as e:
                self.logger.error(f"Failed to install {name}: {e}")
                failed_count += 1
                results[name] = None
        
        success_count = len([r for r in results.values() if r is not None])
        self.logger.info(f"\n📊 Installation complete: {success_count}/{len(tools_to_install)} successful")
        
        if failed_count > 0:
            self.logger.warning(f"⚠️ {failed_count} installations failed")
        
        return results
    
    def quick_install_and_launch(self, tool_name: str, config: Dict = None, wait_for_ready: bool = True) -> Optional[str]:
        """Quick install and launch a tool by name with enhanced error handling"""
        # Tool repository mappings with aliases
        tool_repos = {
            "stable-diffusion": "https://github.com/AUTOMATIC1111/stable-diffusion-webui",
            "sd-webui": "https://github.com/AUTOMATIC1111/stable-diffusion-webui",
            "automatic1111": "https://github.com/AUTOMATIC1111/stable-diffusion-webui",
            "a1111": "https://github.com/AUTOMATIC1111/stable-diffusion-webui",
            "comfyui": "https://github.com/comfyanonymous/ComfyUI",
            "comfy": "https://github.com/comfyanonymous/ComfyUI",
            "text-generation": "https://github.com/oobabooga/text-generation-webui",
            "oobabooga": "https://github.com/oobabooga/text-generation-webui",
            "tgwui": "https://github.com/oobabooga/text-generation-webui",
            "kohya": "https://github.com/bmaltais/kohya_ss",
            "kohya-ss": "https://github.com/bmaltais/kohya_ss",
            "invokeai": "https://github.com/invoke-ai/InvokeAI",
            "invoke": "https://github.com/invoke-ai/InvokeAI",
            "fooocus": "https://github.com/lllyasviel/Fooocus"
        }
        
        try:
            # Normalize tool name
            tool_key = tool_name.lower().replace("_", "-").replace(" ", "-")
            
            if tool_key not in tool_repos:
                available = ', '.join(sorted(set(tool_repos.keys())))
                raise ValueError(f"Unknown tool: {tool_name}. Available tools: {available}")
            
            self.logger.info(f"🚀 Quick install and launch: {tool_name}")
            
            # Check if already installed and running
            if tool_key in self.installed_apps:
                app_info = self.installed_apps[tool_key]
                if app_info.status == 'running' and app_info.url:
                    self.logger.info(f"✅ {tool_name} is already running at {app_info.url}")
                    return app_info.url
            
            # Install the tool
            repo_url = tool_repos[tool_key]
            app_info = self.install_app(repo_url, tool_key)
            
            if not app_info:
                raise Exception(f"Failed to install {tool_name}")
            
            # Wait for installation to settle
            self.logger.info("Waiting for installation to complete...")
            time.sleep(3)
            
            # Launch the tool
            launched_app = self.launch_app(tool_key, config, wait_for_ready)
            
            if launched_app and launched_app.url:
                self.logger.info(f"✅ {tool_name} is ready at {launched_app.url}")
                return launched_app.url
            
            raise Exception(f"Failed to launch {tool_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Quick install and launch failed for {tool_name}: {e}")
            return None
    
    def cleanup(self):
        """Clean up resources and close connections"""
        try:
            self.stop_server()
            if hasattr(self, 'session'):
                self.session.close()
            self.logger.info("🧹 PinokioController cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.cleanup()
