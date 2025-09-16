#!/usr/bin/env python3
"""
PinokioCloud Server Detector

This module finds web servers running on the system and detects their framework types.
It provides comprehensive web server detection for 15+ web frameworks including
Gradio, Streamlit, Flask, FastAPI, and other popular frameworks.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import socket
import requests
import psutil
import threading
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime
import re
import json

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from running.process_tracker import ProcessTracker
from running.script_manager import ScriptManager
from app_analysis.webui_detector import WebUIDetector, WebUIType


class WebFrameworkType(Enum):
    """Enumeration of supported web framework types."""
    GRADIO = "gradio"
    STREAMLIT = "streamlit"
    FLASK = "flask"
    FASTAPI = "fastapi"
    DJANGO = "django"
    JUPYTER = "jupyter"
    DASH = "dash"
    BOKEH = "bokeh"
    PLOTLY = "plotly"
    CHAINLIT = "chainlit"
    NICEGUI = "nicegui"
    REFLEX = "reflex"
    PANEL = "panel"
    VOILA = "voila"
    SOLARA = "solara"
    UNKNOWN = "unknown"


class ServerStatus(Enum):
    """Enumeration of server statuses."""
    RUNNING = "running"
    STARTING = "starting"
    STOPPED = "stopped"
    ERROR = "error"
    UNREACHABLE = "unreachable"


@dataclass
class WebServerInfo:
    """Information about a detected web server."""
    port: int
    host: str = "localhost"
    framework: WebFrameworkType = WebFrameworkType.UNKNOWN
    status: ServerStatus = ServerStatus.STOPPED
    pid: Optional[int] = None
    app_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    url: str = ""
    process_name: Optional[str] = None
    command_line: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)
    last_check: datetime = field(default_factory=datetime.now)
    response_time: float = 0.0
    headers: Dict[str, str] = field(default_factory=dict)
    framework_version: Optional[str] = None
    capabilities: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Set URL after initialization."""
        if not self.url:
            self.url = f"http://{self.host}:{self.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert WebServerInfo to dictionary."""
        data = asdict(self)
        data['framework'] = self.framework.value
        data['status'] = self.status.value
        data['detected_at'] = self.detected_at.isoformat()
        data['last_check'] = self.last_check.isoformat()
        data['capabilities'] = list(self.capabilities)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebServerInfo':
        """Create WebServerInfo from dictionary."""
        data['framework'] = WebFrameworkType(data['framework'])
        data['status'] = ServerStatus(data['status'])
        data['detected_at'] = datetime.fromisoformat(data['detected_at'])
        data['last_check'] = datetime.fromisoformat(data['last_check'])
        data['capabilities'] = set(data['capabilities'])
        return cls(**data)


class ServerDetector:
    """
    Finds web servers running on the system and detects their framework types.
    
    This class provides comprehensive web server detection with framework identification,
    process tracking, and integration with the PinokioCloud system.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the server detector."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        
        # Server tracking
        self.detected_servers: Dict[int, WebServerInfo] = {}
        self.detection_lock = threading.RLock()
        
        # Detection configuration
        self.scan_ports = list(range(3000, 3010)) + list(range(5000, 5010)) + \
                         list(range(7860, 7870)) + list(range(8000, 8020)) + \
                         [8080, 8888, 9090, 9999, 10000]
        self.detection_interval = 30.0  # seconds
        self.timeout = 5.0  # seconds
        
        # Framework detection patterns
        self.framework_patterns = self._setup_framework_patterns()
        
        # Integration with previous phases
        self.process_tracker = ProcessTracker(str(self.base_path))
        self.webui_detector = WebUIDetector(str(self.base_path))
        
        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[callable]] = {
            'server_detected': [],
            'server_lost': [],
            'server_updated': [],
            'framework_identified': []
        }
        
        print(f"[ServerDetector] Initialized with {len(self.scan_ports)} scan ports")
        print(f"[ServerDetector] Framework patterns: {len(self.framework_patterns)} types")
    
    def detect_servers(self, force_scan: bool = False) -> List[WebServerInfo]:
        """
        Detect all running web servers.
        
        Args:
            force_scan: Force a complete scan even if recently scanned
        
        Returns:
            List[WebServerInfo]: List of detected web servers
        """
        print("[ServerDetector] Starting web server detection...")
        
        detected_servers = []
        
        with self.detection_lock:
            # Scan all configured ports
            for port in self.scan_ports:
                try:
                    server_info = self._scan_port(port)
                    if server_info:
                        # Check if this is a new server or updated server
                        existing_server = self.detected_servers.get(port)
                        
                        if existing_server:
                            # Update existing server
                            if self._has_server_changed(existing_server, server_info):
                                self.detected_servers[port] = server_info
                                self._emit_event('server_updated', server_info)
                                print(f"[ServerDetector] Updated server on port {port}: {server_info.framework.value}")
                            else:
                                # Just update last check time
                                existing_server.last_check = datetime.now()
                                server_info = existing_server
                        else:
                            # New server detected
                            self.detected_servers[port] = server_info
                            self._emit_event('server_detected', server_info)
                            print(f"[ServerDetector] New server detected on port {port}: {server_info.framework.value}")
                        
                        detected_servers.append(server_info)
                        
                except Exception as e:
                    print(f"[ServerDetector] Error scanning port {port}: {e}")
            
            # Check for servers that are no longer running
            self._cleanup_dead_servers()
        
        print(f"[ServerDetector] Detection complete: {len(detected_servers)} servers found")
        return detected_servers
    
    def get_server_info(self, port: int) -> Optional[WebServerInfo]:
        """
        Get information about a server on a specific port.
        
        Args:
            port: Port number to check
        
        Returns:
            Optional[WebServerInfo]: Server information if found
        """
        return self.detected_servers.get(port)
    
    def get_all_servers(self) -> List[WebServerInfo]:
        """
        Get information about all detected servers.
        
        Returns:
            List[WebServerInfo]: List of all detected servers
        """
        with self.detection_lock:
            return list(self.detected_servers.values())
    
    def get_servers_by_framework(self, framework: WebFrameworkType) -> List[WebServerInfo]:
        """
        Get all servers of a specific framework type.
        
        Args:
            framework: Framework type to filter by
        
        Returns:
            List[WebServerInfo]: List of servers with matching framework
        """
        return [server for server in self.detected_servers.values() 
                if server.framework == framework]
    
    def get_gradio_servers(self) -> List[WebServerInfo]:
        """Get all Gradio servers."""
        return self.get_servers_by_framework(WebFrameworkType.GRADIO)
    
    def get_streamlit_servers(self) -> List[WebServerInfo]:
        """Get all Streamlit servers."""
        return self.get_servers_by_framework(WebFrameworkType.STREAMLIT)
    
    def is_port_available(self, port: int) -> bool:
        """
        Check if a port is available (not in use).
        
        Args:
            port: Port number to check
        
        Returns:
            bool: True if port is available
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0
        except Exception:
            return True
    
    def find_available_port(self, start_port: int = 7860, end_port: int = 7900) -> int:
        """
        Find the next available port in a range.
        
        Args:
            start_port: Starting port number
            end_port: Ending port number
        
        Returns:
            int: Available port number
        
        Raises:
            RuntimeError: If no available port is found
        """
        for port in range(start_port, end_port + 1):
            if self.is_port_available(port):
                return port
        
        raise RuntimeError(f"No available port found in range {start_port}-{end_port}")
    
    def start_monitoring(self) -> None:
        """Start continuous server monitoring."""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            print("[ServerDetector] Started server monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop server monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        print("[ServerDetector] Stopped server monitoring")
    
    def add_event_callback(self, event: str, callback: callable) -> None:
        """Add a callback for server events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def _scan_port(self, port: int) -> Optional[WebServerInfo]:
        """Scan a specific port for web servers."""
        try:
            # Check if port is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result != 0:
                return None  # Port is not open
            
            # Port is open, try to identify the web server
            server_info = WebServerInfo(port=port)
            
            # Get process information
            self._get_process_info(server_info)
            
            # Make HTTP request to identify framework
            self._identify_framework(server_info)
            
            # Get additional server details
            self._get_server_details(server_info)
            
            # Update status
            server_info.status = ServerStatus.RUNNING
            server_info.last_check = datetime.now()
            
            return server_info
            
        except Exception as e:
            print(f"[ServerDetector] Error scanning port {port}: {e}")
            return None
    
    def _get_process_info(self, server_info: WebServerInfo) -> None:
        """Get process information for the server."""
        try:
            # Find process listening on the port
            for conn in psutil.net_connections():
                if (conn.laddr and conn.laddr.port == server_info.port and 
                    conn.status == psutil.CONN_LISTEN):
                    
                    try:
                        process = psutil.Process(conn.pid)
                        server_info.pid = conn.pid
                        server_info.process_name = process.name()
                        server_info.command_line = process.cmdline()
                        
                        # Try to determine app name from command line
                        server_info.app_name = self._extract_app_name(server_info.command_line)
                        
                        break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                        
        except Exception as e:
            print(f"[ServerDetector] Error getting process info for port {server_info.port}: {e}")
    
    def _identify_framework(self, server_info: WebServerInfo) -> None:
        """Identify the web framework by making HTTP requests."""
        try:
            start_time = time.time()
            
            # Make HTTP request
            response = requests.get(
                server_info.url,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            server_info.response_time = time.time() - start_time
            server_info.headers = dict(response.headers)
            
            # Analyze response to identify framework
            framework = self._analyze_response_for_framework(response, server_info)
            server_info.framework = framework
            
            # Get framework version if possible
            server_info.framework_version = self._extract_framework_version(response, framework)
            
            # Extract title and description
            self._extract_page_info(response, server_info)
            
            # Determine capabilities
            server_info.capabilities = self._determine_capabilities(response, framework)
            
            if framework != WebFrameworkType.UNKNOWN:
                self._emit_event('framework_identified', server_info)
            
        except requests.exceptions.RequestException as e:
            print(f"[ServerDetector] HTTP request failed for {server_info.url}: {e}")
            server_info.status = ServerStatus.UNREACHABLE
        except Exception as e:
            print(f"[ServerDetector] Error identifying framework for {server_info.url}: {e}")
    
    def _analyze_response_for_framework(self, response: requests.Response, 
                                      server_info: WebServerInfo) -> WebFrameworkType:
        """Analyze HTTP response to identify framework."""
        content = response.text.lower()
        headers = {k.lower(): v.lower() for k, v in response.headers.items()}
        
        # Check headers first
        server_header = headers.get('server', '')
        
        # Gradio detection
        if ('gradio' in content or 'gradio' in server_header or
            'gradio-app' in content or '/gradio_api/' in content or
            'gradio.interface' in content):
            return WebFrameworkType.GRADIO
        
        # Streamlit detection
        if ('streamlit' in content or 'streamlit' in server_header or
            '_streamlit' in content or 'streamlit.main' in content or
            'streamlit-container' in content):
            return WebFrameworkType.STREAMLIT
        
        # FastAPI detection
        if ('fastapi' in server_header or 'uvicorn' in server_header or
            '/docs' in content and '/redoc' in content or
            'openapi.json' in content):
            return WebFrameworkType.FASTAPI
        
        # Flask detection
        if ('flask' in server_header or 'werkzeug' in server_header or
            'flask' in content):
            return WebFrameworkType.FLASK
        
        # Django detection
        if ('django' in content or 'csrfmiddlewaretoken' in content or
            'django' in server_header):
            return WebFrameworkType.DJANGO
        
        # Jupyter detection
        if ('jupyter' in content or 'notebook' in content or
            'jupyter-notebook' in content or '/tree' in response.url):
            return WebFrameworkType.JUPYTER
        
        # Dash detection
        if ('dash' in content or '_dash-' in content or
            'dash.dependencies' in content):
            return WebFrameworkType.DASH
        
        # Bokeh detection
        if ('bokeh' in content or 'bokeh-' in content or
            'bokeh.models' in content):
            return WebFrameworkType.BOKEH
        
        # Plotly detection
        if ('plotly' in content and 'dash' not in content):
            return WebFrameworkType.PLOTLY
        
        # Chainlit detection
        if ('chainlit' in content or 'chainlit-' in content):
            return WebFrameworkType.CHAINLIT
        
        # NiceGUI detection
        if ('nicegui' in content or 'nicegui-' in content):
            return WebFrameworkType.NICEGUI
        
        # Reflex detection
        if ('reflex' in content or 'reflex-' in content):
            return WebFrameworkType.REFLEX
        
        # Panel detection
        if ('panel' in content and 'bokeh' in content):
            return WebFrameworkType.PANEL
        
        # Voilà detection
        if ('voila' in content or 'voila-' in content):
            return WebFrameworkType.VOILA
        
        # Solara detection
        if ('solara' in content or 'solara-' in content):
            return WebFrameworkType.SOLARA
        
        # Check command line for additional clues
        if server_info.command_line:
            cmd_str = ' '.join(server_info.command_line).lower()
            
            for framework_name in ['gradio', 'streamlit', 'flask', 'fastapi', 'django']:
                if framework_name in cmd_str:
                    return WebFrameworkType(framework_name)
        
        return WebFrameworkType.UNKNOWN
    
    def _extract_framework_version(self, response: requests.Response, 
                                 framework: WebFrameworkType) -> Optional[str]:
        """Extract framework version from response."""
        try:
            content = response.text
            
            # Look for version patterns
            version_patterns = {
                WebFrameworkType.GRADIO: [r'gradio["\s]*:[\s]*["\s]*([0-9\.]+)', r'gradio-([0-9\.]+)'],
                WebFrameworkType.STREAMLIT: [r'streamlit["\s]*:[\s]*["\s]*([0-9\.]+)', r'streamlit-([0-9\.]+)'],
                WebFrameworkType.FASTAPI: [r'fastapi["\s]*:[\s]*["\s]*([0-9\.]+)', r'fastapi-([0-9\.]+)'],
                WebFrameworkType.FLASK: [r'flask["\s]*:[\s]*["\s]*([0-9\.]+)', r'flask-([0-9\.]+)']
            }
            
            patterns = version_patterns.get(framework, [])
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def _extract_page_info(self, response: requests.Response, server_info: WebServerInfo) -> None:
        """Extract title and description from the page."""
        try:
            content = response.text
            
            # Extract title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                server_info.title = title_match.group(1).strip()
            
            # Extract description
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', 
                                 content, re.IGNORECASE)
            if desc_match:
                server_info.description = desc_match.group(1).strip()
            
        except Exception as e:
            print(f"[ServerDetector] Error extracting page info: {e}")
    
    def _determine_capabilities(self, response: requests.Response, 
                              framework: WebFrameworkType) -> Set[str]:
        """Determine server capabilities based on framework and response."""
        capabilities = set()
        content = response.text.lower()
        
        # Framework-specific capabilities
        if framework == WebFrameworkType.GRADIO:
            capabilities.add('gradio_share')
            capabilities.add('real_time')
            if 'upload' in content:
                capabilities.add('file_upload')
            if 'download' in content:
                capabilities.add('file_download')
        
        elif framework == WebFrameworkType.STREAMLIT:
            capabilities.add('real_time')
            if 'file_uploader' in content:
                capabilities.add('file_upload')
            if 'download' in content:
                capabilities.add('file_download')
        
        elif framework == WebFrameworkType.FASTAPI:
            capabilities.add('api')
            capabilities.add('swagger_docs')
            if '/docs' in content:
                capabilities.add('interactive_docs')
        
        elif framework == WebFrameworkType.FLASK:
            capabilities.add('api')
            if 'websocket' in content:
                capabilities.add('websockets')
        
        # Common capabilities
        if 'websocket' in content or 'ws://' in content:
            capabilities.add('websockets')
        
        if 'api' in content or '/api/' in content:
            capabilities.add('api')
        
        if 'upload' in content:
            capabilities.add('file_upload')
        
        if 'download' in content:
            capabilities.add('file_download')
        
        return capabilities
    
    def _extract_app_name(self, command_line: List[str]) -> Optional[str]:
        """Extract application name from command line."""
        if not command_line:
            return None
        
        # Look for common patterns
        cmd_str = ' '.join(command_line)
        
        # Look for Python script names
        for arg in command_line:
            if arg.endswith('.py'):
                return Path(arg).stem
        
        # Look for app names in arguments
        app_indicators = ['--app', '--name', '--title']
        for i, arg in enumerate(command_line):
            if arg in app_indicators and i + 1 < len(command_line):
                return command_line[i + 1]
        
        # Look for directory names that might indicate app names
        for arg in command_line:
            if '/' in arg:
                path_parts = arg.split('/')
                for part in reversed(path_parts):
                    if part and part not in ['bin', 'python', 'python3', 'scripts']:
                        return part
        
        return None
    
    def _get_server_details(self, server_info: WebServerInfo) -> None:
        """Get additional server details."""
        try:
            # Try to get more information via additional endpoints
            common_endpoints = ['/health', '/status', '/info', '/version', '/api/info']
            
            for endpoint in common_endpoints:
                try:
                    response = requests.get(
                        f"{server_info.url}{endpoint}",
                        timeout=2.0
                    )
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            # Extract useful information from the response
                            if 'version' in data:
                                server_info.framework_version = str(data['version'])
                            if 'title' in data:
                                server_info.title = str(data['title'])
                            if 'description' in data:
                                server_info.description = str(data['description'])
                        except:
                            pass  # Not JSON or no useful info
                        
                        break  # Found a working endpoint
                        
                except requests.exceptions.RequestException:
                    continue  # Try next endpoint
                    
        except Exception as e:
            print(f"[ServerDetector] Error getting server details: {e}")
    
    def _has_server_changed(self, old_server: WebServerInfo, 
                          new_server: WebServerInfo) -> bool:
        """Check if server information has changed significantly."""
        return (old_server.framework != new_server.framework or
                old_server.status != new_server.status or
                old_server.pid != new_server.pid or
                old_server.title != new_server.title)
    
    def _cleanup_dead_servers(self) -> None:
        """Remove servers that are no longer running."""
        dead_ports = []
        
        for port, server_info in self.detected_servers.items():
            # Check if port is still open
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result != 0:
                    # Port is no longer open
                    dead_ports.append(port)
                    self._emit_event('server_lost', server_info)
                    
            except Exception:
                dead_ports.append(port)
                self._emit_event('server_lost', server_info)
        
        # Remove dead servers
        for port in dead_ports:
            if port in self.detected_servers:
                server_info = self.detected_servers[port]
                del self.detected_servers[port]
                print(f"[ServerDetector] Removed dead server on port {port}: {server_info.framework.value}")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                self.detect_servers()
                time.sleep(self.detection_interval)
                
            except Exception as e:
                print(f"[ServerDetector] Error in monitoring loop: {e}")
                time.sleep(self.detection_interval)
    
    def _setup_framework_patterns(self) -> Dict[WebFrameworkType, List[str]]:
        """Set up framework detection patterns."""
        return {
            WebFrameworkType.GRADIO: [
                'gradio', 'gradio-app', '/gradio_api/', 'gradio.interface'
            ],
            WebFrameworkType.STREAMLIT: [
                'streamlit', '_streamlit', 'streamlit.main', 'streamlit-container'
            ],
            WebFrameworkType.FASTAPI: [
                'fastapi', 'uvicorn', '/docs', '/redoc', 'openapi.json'
            ],
            WebFrameworkType.FLASK: [
                'flask', 'werkzeug'
            ],
            WebFrameworkType.DJANGO: [
                'django', 'csrfmiddlewaretoken'
            ],
            WebFrameworkType.JUPYTER: [
                'jupyter', 'notebook', 'jupyter-notebook', '/tree'
            ],
            WebFrameworkType.DASH: [
                'dash', '_dash-', 'dash.dependencies'
            ],
            WebFrameworkType.BOKEH: [
                'bokeh', 'bokeh-', 'bokeh.models'
            ]
        }
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[ServerDetector] Error in event callback: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_monitoring()


def main():
    """Test the server detector functionality."""
    print("Testing ServerDetector...")
    
    detector = ServerDetector()
    
    # Detect servers
    servers = detector.detect_servers()
    print(f"Detected {len(servers)} servers:")
    
    for server in servers:
        print(f"  - Port {server.port}: {server.framework.value}")
        print(f"    Status: {server.status.value}")
        print(f"    Title: {server.title}")
        print(f"    Process: {server.process_name} (PID: {server.pid})")
        print(f"    Capabilities: {', '.join(server.capabilities)}")
        print()
    
    # Test specific framework detection
    gradio_servers = detector.get_gradio_servers()
    print(f"Gradio servers: {len(gradio_servers)}")
    
    streamlit_servers = detector.get_streamlit_servers()
    print(f"Streamlit servers: {len(streamlit_servers)}")
    
    # Test port availability
    available_port = detector.find_available_port()
    print(f"Next available port: {available_port}")
    
    print("ServerDetector test completed")


if __name__ == "__main__":
    main()