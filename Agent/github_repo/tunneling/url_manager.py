#!/usr/bin/env python3
"""
PinokioCloud URL Manager

This module manages and displays all public URLs with QR code generation,
analytics tracking, and comprehensive tunnel management. It provides a centralized
system for tracking all active tunnels and their accessibility.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import time
import json
import threading
import requests
import qrcode
import io
import base64
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse
import uuid

# Import previous phase modules
sys.path.append('/workspace/SD-LongNose/github_repo')
from environment_management.json_handler import JSONHandler
from running.health_monitor import HealthMonitor


class TunnelType(Enum):
    """Types of tunnels."""
    NGROK = "ngrok"
    CLOUDFLARE = "cloudflare"
    GRADIO_SHARE = "gradio_share"
    LOCALTUNNEL = "localtunnel"
    CUSTOM = "custom"


class URLStatus(Enum):
    """Status of URLs."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CHECKING = "checking"
    UNKNOWN = "unknown"


@dataclass
class TunnelURL:
    """Information about a tunnel URL."""
    url_id: str
    url: str
    tunnel_type: TunnelType
    local_port: int
    app_name: str
    status: URLStatus = URLStatus.UNKNOWN
    created_at: datetime = field(default_factory=datetime.now)
    last_check: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    response_time: float = 0.0
    qr_code_data: Optional[str] = None
    short_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    health_checks: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert TunnelURL to dictionary."""
        data = asdict(self)
        data['tunnel_type'] = self.tunnel_type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['last_check'] = self.last_check.isoformat()
        data['last_accessed'] = self.last_accessed.isoformat() if self.last_accessed else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TunnelURL':
        """Create TunnelURL from dictionary."""
        data['tunnel_type'] = TunnelType(data['tunnel_type'])
        data['status'] = URLStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_check'] = datetime.fromisoformat(data['last_check'])
        data['last_accessed'] = datetime.fromisoformat(data['last_accessed']) if data['last_accessed'] else None
        return cls(**data)


class QRCodeGenerator:
    """
    Generates QR codes for tunnel URLs.
    
    This class provides QR code generation with various formats and customization options.
    """
    
    def __init__(self):
        """Initialize the QR code generator."""
        self.default_config = {
            'version': 1,
            'error_correction': qrcode.constants.ERROR_CORRECT_L,
            'box_size': 10,
            'border': 4
        }
    
    def generate_qr_code(self, url: str, format: str = 'PNG') -> str:
        """
        Generate QR code for a URL.
        
        Args:
            url: URL to encode
            format: Output format (PNG, SVG, etc.)
        
        Returns:
            str: Base64-encoded QR code image
        """
        try:
            # Create QR code
            qr = qrcode.QRCode(**self.default_config)
            qr.add_data(url)
            qr.make(fit=True)
            
            # Generate image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format=format)
            buffer.seek(0)
            
            qr_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            return f"data:image/{format.lower()};base64,{qr_data}"
            
        except Exception as e:
            print(f"[QRCodeGenerator] Error generating QR code: {e}")
            return ""
    
    def generate_qr_code_svg(self, url: str) -> str:
        """
        Generate SVG QR code for a URL.
        
        Args:
            url: URL to encode
        
        Returns:
            str: SVG QR code as string
        """
        try:
            import qrcode.image.svg
            
            factory = qrcode.image.svg.SvgPathImage
            qr = qrcode.QRCode(image_factory=factory, **self.default_config)
            qr.add_data(url)
            qr.make(fit=True)
            
            img = qr.make_image()
            return img.to_string(encoding='unicode')
            
        except Exception as e:
            print(f"[QRCodeGenerator] Error generating SVG QR code: {e}")
            return ""


class URLManager:
    """
    Manages and displays all public URLs with QR codes and analytics.
    
    This class provides comprehensive URL management with health monitoring,
    analytics tracking, and QR code generation.
    """
    
    def __init__(self, base_path: str = "/workspace/SD-LongNose"):
        """Initialize the URL manager."""
        self.base_path = Path(base_path)
        self.github_repo_path = self.base_path / "github_repo"
        self.url_storage_path = self.base_path / "url_storage"
        self.url_storage_path.mkdir(exist_ok=True)
        
        # URL tracking
        self.active_urls: Dict[str, TunnelURL] = {}
        self.url_lock = threading.RLock()
        
        # Monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 30.0  # seconds
        
        # QR code generator
        self.qr_generator = QRCodeGenerator()
        
        # Initialize dependencies
        self.json_handler = JSONHandler(str(self.base_path))
        
        # Analytics
        self.analytics_data: Dict[str, Any] = {
            'total_urls_created': 0,
            'total_access_count': 0,
            'urls_by_type': {},
            'apps_with_urls': set(),
            'daily_stats': {}
        }
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[callable]] = {
            'url_registered': [],
            'url_accessed': [],
            'url_health_changed': [],
            'url_removed': []
        }
        
        # Load existing configurations
        self._load_url_configs()
        self._load_analytics()
        
        print(f"[URLManager] Initialized with {len(self.active_urls)} existing URLs")
    
    def register_url(self, url: str, tunnel_type: TunnelType, local_port: int,
                    app_name: str, metadata: Dict[str, Any] = None) -> TunnelURL:
        """
        Register a new tunnel URL.
        
        Args:
            url: Public URL of the tunnel
            tunnel_type: Type of tunnel (ngrok, cloudflare, etc.)
            local_port: Local port being tunneled
            app_name: Name of the application
            metadata: Additional metadata
        
        Returns:
            TunnelURL: Registered URL information
        """
        print(f"[URLManager] Registering URL: {url} for app {app_name}")
        
        # Generate unique URL ID
        url_id = f"url_{uuid.uuid4().hex[:8]}"
        
        # Create tunnel URL object
        tunnel_url = TunnelURL(
            url_id=url_id,
            url=url,
            tunnel_type=tunnel_type,
            local_port=local_port,
            app_name=app_name,
            metadata=metadata or {}
        )
        
        # Generate QR code
        tunnel_url.qr_code_data = self.qr_generator.generate_qr_code(url)
        
        # Check initial URL health
        self._check_url_health(tunnel_url)
        
        # Register URL
        with self.url_lock:
            self.active_urls[url_id] = tunnel_url
        
        # Update analytics
        self._update_analytics('url_created', tunnel_url)
        
        # Save configuration
        self._save_url_config(tunnel_url)
        
        # Start monitoring if not already active
        if not self.monitoring_active:
            self.start_monitoring()
        
        # Emit event
        self._emit_event('url_registered', tunnel_url)
        
        print(f"[URLManager] Registered URL {url_id}: {url}")
        return tunnel_url
    
    def unregister_url(self, url_id: str) -> bool:
        """
        Unregister a tunnel URL.
        
        Args:
            url_id: ID of the URL to unregister
        
        Returns:
            bool: True if successfully unregistered
        """
        print(f"[URLManager] Unregistering URL: {url_id}")
        
        with self.url_lock:
            if url_id not in self.active_urls:
                return False
            
            tunnel_url = self.active_urls[url_id]
            
            # Remove from active URLs
            del self.active_urls[url_id]
            
            # Remove configuration
            self._remove_url_config(url_id)
            
            # Update analytics
            self._update_analytics('url_removed', tunnel_url)
            
            # Emit event
            self._emit_event('url_removed', tunnel_url)
            
            print(f"[URLManager] Unregistered URL {url_id}")
            return True
    
    def get_url_info(self, url_id: str) -> Optional[TunnelURL]:
        """
        Get information about a specific URL.
        
        Args:
            url_id: ID of the URL
        
        Returns:
            Optional[TunnelURL]: URL information if found
        """
        return self.active_urls.get(url_id)
    
    def get_urls_for_app(self, app_name: str) -> List[TunnelURL]:
        """
        Get all URLs for a specific application.
        
        Args:
            app_name: Name of the application
        
        Returns:
            List[TunnelURL]: List of URLs for the application
        """
        return [url for url in self.active_urls.values() 
                if url.app_name == app_name]
    
    def get_urls_by_type(self, tunnel_type: TunnelType) -> List[TunnelURL]:
        """
        Get all URLs of a specific tunnel type.
        
        Args:
            tunnel_type: Type of tunnel to filter by
        
        Returns:
            List[TunnelURL]: List of URLs with matching type
        """
        return [url for url in self.active_urls.values() 
                if url.tunnel_type == tunnel_type]
    
    def list_all_urls(self) -> List[TunnelURL]:
        """
        Get list of all registered URLs.
        
        Returns:
            List[TunnelURL]: List of all URLs
        """
        with self.url_lock:
            return list(self.active_urls.values())
    
    def check_url_health(self, url_id: str) -> URLStatus:
        """
        Check the health of a specific URL.
        
        Args:
            url_id: ID of the URL to check
        
        Returns:
            URLStatus: Current status of the URL
        """
        if url_id not in self.active_urls:
            return URLStatus.UNKNOWN
        
        tunnel_url = self.active_urls[url_id]
        old_status = tunnel_url.status
        
        # Perform health check
        self._check_url_health(tunnel_url)
        
        # Emit event if status changed
        if old_status != tunnel_url.status:
            self._emit_event('url_health_changed', tunnel_url, old_status)
        
        return tunnel_url.status
    
    def record_url_access(self, url_id: str) -> None:
        """
        Record an access to a URL for analytics.
        
        Args:
            url_id: ID of the URL that was accessed
        """
        if url_id in self.active_urls:
            tunnel_url = self.active_urls[url_id]
            tunnel_url.access_count += 1
            tunnel_url.last_accessed = datetime.now()
            
            # Update analytics
            self._update_analytics('url_accessed', tunnel_url)
            
            # Save updated configuration
            self._save_url_config(tunnel_url)
            
            # Emit event
            self._emit_event('url_accessed', tunnel_url)
    
    def get_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive URL analytics.
        
        Returns:
            Dict[str, Any]: Analytics data
        """
        with self.url_lock:
            # Calculate current stats
            total_urls = len(self.active_urls)
            active_urls = len([url for url in self.active_urls.values() 
                             if url.status == URLStatus.ACTIVE])
            
            # URLs by type
            urls_by_type = {}
            for tunnel_type in TunnelType:
                count = len(self.get_urls_by_type(tunnel_type))
                if count > 0:
                    urls_by_type[tunnel_type.value] = count
            
            # Apps with URLs
            apps_with_urls = set(url.app_name for url in self.active_urls.values())
            
            # Total access count
            total_accesses = sum(url.access_count for url in self.active_urls.values())
            
            # Average response time
            response_times = [url.response_time for url in self.active_urls.values() 
                            if url.response_time > 0]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            analytics = {
                'timestamp': datetime.now().isoformat(),
                'total_urls': total_urls,
                'active_urls': active_urls,
                'inactive_urls': total_urls - active_urls,
                'urls_by_type': urls_by_type,
                'apps_with_urls': len(apps_with_urls),
                'total_accesses': total_accesses,
                'avg_response_time': avg_response_time,
                'uptime_stats': self._calculate_uptime_stats(),
                'daily_stats': self._get_daily_stats()
            }
            
            return analytics
    
    def generate_url_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive URL report.
        
        Returns:
            Dict[str, Any]: Detailed URL report
        """
        with self.url_lock:
            urls_data = []
            
            for url in self.active_urls.values():
                url_data = {
                    'url_id': url.url_id,
                    'url': url.url,
                    'app_name': url.app_name,
                    'tunnel_type': url.tunnel_type.value,
                    'status': url.status.value,
                    'local_port': url.local_port,
                    'created_at': url.created_at.isoformat(),
                    'last_check': url.last_check.isoformat(),
                    'access_count': url.access_count,
                    'response_time': url.response_time,
                    'has_qr_code': bool(url.qr_code_data),
                    'health_checks_count': len(url.health_checks)
                }
                
                if url.last_accessed:
                    url_data['last_accessed'] = url.last_accessed.isoformat()
                
                urls_data.append(url_data)
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'total_urls': len(urls_data),
                'urls': urls_data,
                'analytics': self.get_analytics(),
                'summary': {
                    'most_accessed_app': self._get_most_accessed_app(),
                    'fastest_tunnel_type': self._get_fastest_tunnel_type(),
                    'most_reliable_tunnel_type': self._get_most_reliable_tunnel_type()
                }
            }
            
            return report
    
    def start_monitoring(self) -> None:
        """Start URL health monitoring."""
        if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                daemon=True
            )
            self.monitoring_thread.start()
            print("[URLManager] Started URL monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop URL monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)
        print("[URLManager] Stopped URL monitoring")
    
    def add_event_callback(self, event: str, callback: callable) -> None:
        """Add a callback for URL events."""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
    
    def _check_url_health(self, tunnel_url: TunnelURL) -> None:
        """Check the health of a URL."""
        try:
            tunnel_url.status = URLStatus.CHECKING
            start_time = time.time()
            
            # Make HTTP request to check URL
            response = requests.get(
                tunnel_url.url,
                timeout=10.0,
                allow_redirects=True
            )
            
            response_time = time.time() - start_time
            tunnel_url.response_time = response_time
            tunnel_url.last_check = datetime.now()
            
            # Determine status based on response
            if response.status_code < 400:
                tunnel_url.status = URLStatus.ACTIVE
                tunnel_url.error_message = None
            else:
                tunnel_url.status = URLStatus.ERROR
                tunnel_url.error_message = f"HTTP {response.status_code}"
            
            # Record health check
            health_check = {
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'response_time': response_time,
                'content_length': len(response.content),
                'headers': dict(response.headers)
            }
            
            tunnel_url.health_checks.append(health_check)
            
            # Keep only last 50 health checks
            if len(tunnel_url.health_checks) > 50:
                tunnel_url.health_checks = tunnel_url.health_checks[-50:]
            
        except requests.exceptions.RequestException as e:
            tunnel_url.status = URLStatus.INACTIVE
            tunnel_url.error_message = str(e)
            tunnel_url.last_check = datetime.now()
            
            # Record failed health check
            health_check = {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'response_time': 0.0
            }
            tunnel_url.health_checks.append(health_check)
        
        except Exception as e:
            tunnel_url.status = URLStatus.ERROR
            tunnel_url.error_message = str(e)
            tunnel_url.last_check = datetime.now()
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                with self.url_lock:
                    for url_id in list(self.active_urls.keys()):
                        tunnel_url = self.active_urls[url_id]
                        
                        # Check if it's time for health check
                        time_since_check = datetime.now() - tunnel_url.last_check
                        if time_since_check.total_seconds() >= self.monitoring_interval:
                            self._check_url_health(tunnel_url)
                            
                            # Save updated configuration
                            self._save_url_config(tunnel_url)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                print(f"[URLManager] Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _update_analytics(self, event: str, tunnel_url: TunnelURL) -> None:
        """Update analytics data."""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            if event == 'url_created':
                self.analytics_data['total_urls_created'] += 1
                self.analytics_data['apps_with_urls'].add(tunnel_url.app_name)
                
                # Update daily stats
                if today not in self.analytics_data['daily_stats']:
                    self.analytics_data['daily_stats'][today] = {
                        'urls_created': 0,
                        'total_accesses': 0
                    }
                self.analytics_data['daily_stats'][today]['urls_created'] += 1
                
                # Update by type
                tunnel_type = tunnel_url.tunnel_type.value
                if tunnel_type not in self.analytics_data['urls_by_type']:
                    self.analytics_data['urls_by_type'][tunnel_type] = 0
                self.analytics_data['urls_by_type'][tunnel_type] += 1
            
            elif event == 'url_accessed':
                self.analytics_data['total_access_count'] += 1
                
                # Update daily stats
                if today not in self.analytics_data['daily_stats']:
                    self.analytics_data['daily_stats'][today] = {
                        'urls_created': 0,
                        'total_accesses': 0
                    }
                self.analytics_data['daily_stats'][today]['total_accesses'] += 1
            
            # Save analytics
            self._save_analytics()
            
        except Exception as e:
            print(f"[URLManager] Error updating analytics: {e}")
    
    def _calculate_uptime_stats(self) -> Dict[str, float]:
        """Calculate uptime statistics for all URLs."""
        try:
            if not self.active_urls:
                return {}
            
            total_uptime = 0.0
            total_urls = 0
            uptime_by_type = {}
            
            for tunnel_url in self.active_urls.values():
                if tunnel_url.health_checks:
                    # Calculate uptime based on health checks
                    successful_checks = sum(1 for check in tunnel_url.health_checks 
                                          if 'status_code' in check and check['status_code'] < 400)
                    total_checks = len(tunnel_url.health_checks)
                    
                    if total_checks > 0:
                        uptime = (successful_checks / total_checks) * 100
                        total_uptime += uptime
                        total_urls += 1
                        
                        # Track by type
                        tunnel_type = tunnel_url.tunnel_type.value
                        if tunnel_type not in uptime_by_type:
                            uptime_by_type[tunnel_type] = []
                        uptime_by_type[tunnel_type].append(uptime)
            
            # Calculate averages
            avg_uptime = total_uptime / total_urls if total_urls > 0 else 0
            
            # Calculate averages by type
            avg_uptime_by_type = {}
            for tunnel_type, uptimes in uptime_by_type.items():
                avg_uptime_by_type[tunnel_type] = sum(uptimes) / len(uptimes)
            
            return {
                'overall_uptime': avg_uptime,
                'uptime_by_type': avg_uptime_by_type,
                'total_monitored_urls': total_urls
            }
            
        except Exception as e:
            print(f"[URLManager] Error calculating uptime stats: {e}")
            return {}
    
    def _get_daily_stats(self) -> Dict[str, Any]:
        """Get daily statistics."""
        return self.analytics_data.get('daily_stats', {})
    
    def _get_most_accessed_app(self) -> Optional[str]:
        """Get the most accessed application."""
        try:
            app_accesses = {}
            
            for tunnel_url in self.active_urls.values():
                app_name = tunnel_url.app_name
                if app_name not in app_accesses:
                    app_accesses[app_name] = 0
                app_accesses[app_name] += tunnel_url.access_count
            
            if app_accesses:
                return max(app_accesses, key=app_accesses.get)
            
            return None
            
        except Exception:
            return None
    
    def _get_fastest_tunnel_type(self) -> Optional[str]:
        """Get the tunnel type with fastest average response time."""
        try:
            type_response_times = {}
            
            for tunnel_url in self.active_urls.values():
                tunnel_type = tunnel_url.tunnel_type.value
                if tunnel_url.response_time > 0:
                    if tunnel_type not in type_response_times:
                        type_response_times[tunnel_type] = []
                    type_response_times[tunnel_type].append(tunnel_url.response_time)
            
            if type_response_times:
                # Calculate averages
                avg_times = {}
                for tunnel_type, times in type_response_times.items():
                    avg_times[tunnel_type] = sum(times) / len(times)
                
                return min(avg_times, key=avg_times.get)
            
            return None
            
        except Exception:
            return None
    
    def _get_most_reliable_tunnel_type(self) -> Optional[str]:
        """Get the most reliable tunnel type based on uptime."""
        try:
            uptime_stats = self._calculate_uptime_stats()
            uptime_by_type = uptime_stats.get('uptime_by_type', {})
            
            if uptime_by_type:
                return max(uptime_by_type, key=uptime_by_type.get)
            
            return None
            
        except Exception:
            return None
    
    def _save_url_config(self, tunnel_url: TunnelURL) -> None:
        """Save URL configuration to disk."""
        config_file = self.url_storage_path / f"{tunnel_url.url_id}.json"
        try:
            self.json_handler.write_json_file(str(config_file), tunnel_url.to_dict())
        except Exception as e:
            print(f"[URLManager] Error saving URL config: {e}")
    
    def _load_url_configs(self) -> None:
        """Load existing URL configurations."""
        try:
            for config_file in self.url_storage_path.glob("*.json"):
                if config_file.name == "analytics.json":
                    continue  # Skip analytics file
                
                try:
                    config_data = self.json_handler.read_json_file(str(config_file))
                    tunnel_url = TunnelURL.from_dict(config_data)
                    
                    # Only load if URL is still reachable (basic check)
                    self._check_url_health(tunnel_url)
                    
                    self.active_urls[tunnel_url.url_id] = tunnel_url
                    print(f"[URLManager] Loaded URL config: {tunnel_url.url}")
                    
                except Exception as e:
                    print(f"[URLManager] Error loading URL config {config_file}: {e}")
                    
        except Exception as e:
            print(f"[URLManager] Error loading URL configurations: {e}")
    
    def _remove_url_config(self, url_id: str) -> None:
        """Remove URL configuration from disk."""
        config_file = self.url_storage_path / f"{url_id}.json"
        try:
            if config_file.exists():
                config_file.unlink()
        except Exception as e:
            print(f"[URLManager] Error removing URL config: {e}")
    
    def _save_analytics(self) -> None:
        """Save analytics data to disk."""
        analytics_file = self.url_storage_path / "analytics.json"
        try:
            # Convert sets to lists for JSON serialization
            analytics_copy = self.analytics_data.copy()
            analytics_copy['apps_with_urls'] = list(analytics_copy['apps_with_urls'])
            
            self.json_handler.write_json_file(str(analytics_file), analytics_copy)
        except Exception as e:
            print(f"[URLManager] Error saving analytics: {e}")
    
    def _load_analytics(self) -> None:
        """Load analytics data from disk."""
        analytics_file = self.url_storage_path / "analytics.json"
        try:
            if analytics_file.exists():
                analytics_data = self.json_handler.read_json_file(str(analytics_file))
                
                # Convert lists back to sets
                if 'apps_with_urls' in analytics_data:
                    analytics_data['apps_with_urls'] = set(analytics_data['apps_with_urls'])
                
                self.analytics_data.update(analytics_data)
                print("[URLManager] Loaded analytics data")
        except Exception as e:
            print(f"[URLManager] Error loading analytics: {e}")
    
    def _emit_event(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all callbacks."""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[URLManager] Error in event callback: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_monitoring()


def main():
    """Test the URL manager functionality."""
    print("Testing URLManager...")
    
    manager = URLManager()
    
    # Test registering a URL
    test_url = manager.register_url(
        url="https://example.ngrok.io",
        tunnel_type=TunnelType.NGROK,
        local_port=7860,
        app_name="test_app"
    )
    
    print(f"Registered URL: {test_url.url_id}")
    print(f"QR Code generated: {bool(test_url.qr_code_data)}")
    
    # Get analytics
    analytics = manager.get_analytics()
    print(f"Analytics: {analytics['total_urls']} URLs")
    
    # Generate report
    report = manager.generate_url_report()
    print(f"Report generated with {len(report['urls'])} URLs")
    
    # Cleanup
    manager.unregister_url(test_url.url_id)
    
    print("URLManager test completed")


if __name__ == "__main__":
    main()