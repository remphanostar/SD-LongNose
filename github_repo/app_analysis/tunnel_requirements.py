#!/usr/bin/env python3
"""
PinokioCloud Tunnel Requirements

This module determines tunnel requirements for Pinokio applications.
It analyzes web UI types, installer configurations, and dependency systems
to determine what tunneling solutions are needed.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import analysis modules
from .webui_detector import WebUIType, WebUIInfo
from .installer_detector import InstallerType, InstallerInfo
from .dependency_analyzer import DependencyType, DependencyInfo


class TunnelType(Enum):
    """Enumeration of tunnel types."""
    NGROK = "ngrok"
    CLOUDFLARE = "cloudflare"
    LOCALTUNNEL = "localtunnel"
    SSH = "ssh"
    NONE = "none"
    UNKNOWN = "unknown"


class TunnelPriority(Enum):
    """Enumeration of tunnel priorities."""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    BACKUP = "backup"
    OPTIONAL = "optional"


@dataclass
class TunnelInfo:
    """Information about tunnel requirements."""
    tunnel_type: TunnelType
    priority: TunnelPriority
    required: bool = False
    port: Optional[int] = None
    host: str = "localhost"
    share_enabled: bool = False
    auto_launch: bool = True
    authentication_required: bool = False
    custom_domain: Optional[str] = None
    subdomain: Optional[str] = None
    protocol: str = "http"
    ssl_enabled: bool = False
    tunnel_arguments: Dict[str, Any] = field(default_factory=dict)
    fallback_tunnels: List[TunnelType] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TunnelRequirements:
    """
    Determines tunnel requirements for Pinokio applications.
    
    Analyzes web UI types, installer configurations, and dependencies to determine:
    - Required tunnel types (ngrok, Cloudflare, LocalTunnel)
    - Tunnel configuration and arguments
    - Port and host requirements
    - Authentication and security needs
    - Fallback tunnel options
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the tunnel requirements analyzer.
        
        Args:
            base_path: Base path for analysis
        """
        self.base_path = base_path
        
        # Tunnel configuration mappings
        self.tunnel_configs = {
            TunnelType.NGROK: {
                "default_port": 7860,
                "protocols": ["http", "https"],
                "authentication": True,
                "custom_domain": True,
                "subdomain": True,
                "ssl": True
            },
            TunnelType.CLOUDFLARE: {
                "default_port": 8080,
                "protocols": ["http", "https"],
                "authentication": True,
                "custom_domain": True,
                "subdomain": False,
                "ssl": True
            },
            TunnelType.LOCALTUNNEL: {
                "default_port": 3000,
                "protocols": ["http"],
                "authentication": False,
                "custom_domain": False,
                "subdomain": True,
                "ssl": False
            },
            TunnelType.SSH: {
                "default_port": 22,
                "protocols": ["ssh"],
                "authentication": True,
                "custom_domain": False,
                "subdomain": False,
                "ssl": False
            }
        }
        
        # Web UI tunnel requirements
        self.webui_tunnel_requirements = {
            WebUIType.GRADIO: {
                "primary": TunnelType.NGROK,
                "secondary": TunnelType.CLOUDFLARE,
                "required": True,
                "share_support": True,
                "default_port": 7860
            },
            WebUIType.STREAMLIT: {
                "primary": TunnelType.NGROK,
                "secondary": TunnelType.CLOUDFLARE,
                "required": True,
                "share_support": False,
                "default_port": 8501
            },
            WebUIType.FLASK: {
                "primary": TunnelType.NGROK,
                "secondary": TunnelType.CLOUDFLARE,
                "required": True,
                "share_support": False,
                "default_port": 5000
            },
            WebUIType.FASTAPI: {
                "primary": TunnelType.NGROK,
                "secondary": TunnelType.CLOUDFLARE,
                "required": True,
                "share_support": False,
                "default_port": 8000
            },
            WebUIType.DJANGO: {
                "primary": TunnelType.NGROK,
                "secondary": TunnelType.CLOUDFLARE,
                "required": True,
                "share_support": False,
                "default_port": 8000
            },
            WebUIType.TORNADO: {
                "primary": TunnelType.NGROK,
                "secondary": TunnelType.CLOUDFLARE,
                "required": True,
                "share_support": False,
                "default_port": 8888
            },
            WebUIType.BOKEH: {
                "primary": TunnelType.NGROK,
                "secondary": TunnelType.CLOUDFLARE,
                "required": True,
                "share_support": False,
                "default_port": 5006
            },
            WebUIType.DASH: {
                "primary": TunnelType.NGROK,
                "secondary": TunnelType.CLOUDFLARE,
                "required": True,
                "share_support": False,
                "default_port": 8050
            },
            WebUIType.JUPYTER: {
                "primary": TunnelType.NGROK,
                "secondary": TunnelType.CLOUDFLARE,
                "required": True,
                "share_support": False,
                "default_port": 8888
            },
            WebUIType.CUSTOM: {
                "primary": TunnelType.NGROK,
                "secondary": TunnelType.CLOUDFLARE,
                "required": True,
                "share_support": False,
                "default_port": 8080
            },
            WebUIType.NONE: {
                "primary": TunnelType.NONE,
                "secondary": TunnelType.NONE,
                "required": False,
                "share_support": False,
                "default_port": None
            }
        }
    
    def determine_requirements(self, webui_info: Optional[WebUIInfo], 
                             installer_info: Optional[InstallerInfo],
                             dependency_info: Optional[DependencyInfo]) -> TunnelInfo:
        """
        Determine tunnel requirements based on app analysis.
        
        Args:
            webui_info: Web UI analysis information
            installer_info: Installer analysis information
            dependency_info: Dependency analysis information
            
        Returns:
            TunnelInfo: Tunnel requirements information
        """
        try:
            # Start with default tunnel info
            tunnel_info = TunnelInfo(
                tunnel_type=TunnelType.NONE,
                priority=TunnelPriority.OPTIONAL,
                required=False
            )
            
            # Determine requirements based on web UI
            if webui_info and webui_info.webui_type != WebUIType.UNKNOWN:
                tunnel_info = self._analyze_webui_requirements(webui_info, tunnel_info)
            
            # Adjust based on installer configuration
            if installer_info:
                tunnel_info = self._analyze_installer_requirements(installer_info, tunnel_info)
            
            # Adjust based on dependencies
            if dependency_info:
                tunnel_info = self._analyze_dependency_requirements(dependency_info, tunnel_info)
            
            # Set tunnel arguments
            tunnel_info.tunnel_arguments = self._get_tunnel_arguments(tunnel_info)
            
            # Set fallback tunnels
            tunnel_info.fallback_tunnels = self._get_fallback_tunnels(tunnel_info)
            
            # Update metadata
            tunnel_info.metadata = {
                "webui_type": webui_info.webui_type.value if webui_info else "unknown",
                "installer_type": installer_info.installer_type.value if installer_info else "unknown",
                "dependency_types": [dt.value for dt in dependency_info.dependency_types] if dependency_info else [],
                "analysis_timestamp": self._get_timestamp()
            }
            
            return tunnel_info
        
        except Exception as e:
            return TunnelInfo(
                tunnel_type=TunnelType.UNKNOWN,
                priority=TunnelPriority.OPTIONAL,
                metadata={"error": str(e)}
            )
    
    def _analyze_webui_requirements(self, webui_info: WebUIInfo, tunnel_info: TunnelInfo) -> TunnelInfo:
        """Analyze web UI requirements for tunneling."""
        try:
            webui_type = webui_info.webui_type
            requirements = self.webui_tunnel_requirements.get(webui_type, {})
            
            if not requirements:
                return tunnel_info
            
            # Set primary tunnel type
            primary_tunnel = requirements.get("primary", TunnelType.NONE)
            if primary_tunnel != TunnelType.NONE:
                tunnel_info.tunnel_type = primary_tunnel
                tunnel_info.priority = TunnelPriority.PRIMARY
                tunnel_info.required = requirements.get("required", False)
            
            # Set port
            if webui_info.port:
                tunnel_info.port = webui_info.port
            else:
                tunnel_info.port = requirements.get("default_port", 8080)
            
            # Set host
            tunnel_info.host = webui_info.host
            
            # Set share enabled
            tunnel_info.share_enabled = webui_info.share_enabled
            
            # Set auto launch
            tunnel_info.auto_launch = webui_info.auto_launch
            
            # Set protocol
            if webui_info.port and webui_info.port in [443, 8443]:
                tunnel_info.protocol = "https"
                tunnel_info.ssl_enabled = True
            else:
                tunnel_info.protocol = "http"
                tunnel_info.ssl_enabled = False
            
            # Set authentication requirement
            tunnel_config = self.tunnel_configs.get(primary_tunnel, {})
            tunnel_info.authentication_required = tunnel_config.get("authentication", False)
            
            # Set SSL capability
            tunnel_info.ssl_enabled = tunnel_config.get("ssl", False)
            
            return tunnel_info
        
        except Exception as e:
            return tunnel_info
    
    def _analyze_installer_requirements(self, installer_info: InstallerInfo, tunnel_info: TunnelInfo) -> TunnelInfo:
        """Analyze installer requirements for tunneling."""
        try:
            # Check for tunnel-related commands in installer
            installer_content = installer_info.installer_content.lower()
            
            # Check for ngrok references
            if "ngrok" in installer_content:
                if tunnel_info.tunnel_type == TunnelType.NONE:
                    tunnel_info.tunnel_type = TunnelType.NGROK
                    tunnel_info.priority = TunnelPriority.PRIMARY
                    tunnel_info.required = True
            
            # Check for Cloudflare references
            if "cloudflare" in installer_content or "cloudflared" in installer_content:
                if tunnel_info.tunnel_type == TunnelType.NONE:
                    tunnel_info.tunnel_type = TunnelType.CLOUDFLARE
                    tunnel_info.priority = TunnelPriority.PRIMARY
                    tunnel_info.required = True
            
            # Check for LocalTunnel references
            if "localtunnel" in installer_content:
                if tunnel_info.tunnel_type == TunnelType.NONE:
                    tunnel_info.tunnel_type = TunnelType.LOCALTUNNEL
                    tunnel_info.priority = TunnelPriority.PRIMARY
                    tunnel_info.required = True
            
            # Check for SSH tunnel references
            if "ssh" in installer_content and "tunnel" in installer_content:
                if tunnel_info.tunnel_type == TunnelType.NONE:
                    tunnel_info.tunnel_type = TunnelType.SSH
                    tunnel_info.priority = TunnelPriority.PRIMARY
                    tunnel_info.required = True
            
            # Check for port configuration in installer
            port_patterns = [
                r'port\s*=\s*(\d+)',
                r'listen\((\d+)',
                r'run\([^)]*port\s*=\s*(\d+)',
                r'launch\([^)]*server_port\s*=\s*(\d+)'
            ]
            
            for pattern in port_patterns:
                match = re.search(pattern, installer_info.installer_content, re.IGNORECASE)
                if match:
                    tunnel_info.port = int(match.group(1))
                    break
            
            # Check for host configuration
            host_patterns = [
                r'host\s*=\s*["\']([^"\']+)["\']',
                r'listen\([^,]*,\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in host_patterns:
                match = re.search(pattern, installer_info.installer_content, re.IGNORECASE)
                if match:
                    tunnel_info.host = match.group(1)
                    break
            
            return tunnel_info
        
        except Exception as e:
            return tunnel_info
    
    def _analyze_dependency_requirements(self, dependency_info: DependencyInfo, tunnel_info: TunnelInfo) -> TunnelInfo:
        """Analyze dependency requirements for tunneling."""
        try:
            all_deps = (dependency_info.pip_dependencies + dependency_info.conda_dependencies + 
                       dependency_info.npm_dependencies + dependency_info.system_dependencies)
            
            # Check for tunnel-related dependencies
            tunnel_deps = {
                "ngrok": TunnelType.NGROK,
                "cloudflare": TunnelType.CLOUDFLARE,
                "cloudflared": TunnelType.CLOUDFLARE,
                "localtunnel": TunnelType.LOCALTUNNEL,
                "ssh": TunnelType.SSH
            }
            
            for dep in all_deps:
                dep_lower = dep.lower()
                for tunnel_dep, tunnel_type in tunnel_deps.items():
                    if tunnel_dep in dep_lower:
                        if tunnel_info.tunnel_type == TunnelType.NONE:
                            tunnel_info.tunnel_type = tunnel_type
                            tunnel_info.priority = TunnelPriority.PRIMARY
                            tunnel_info.required = True
                        break
            
            # Check for web server dependencies that might need tunneling
            web_server_deps = ["gunicorn", "uvicorn", "waitress", "cherrypy", "bjoern"]
            for dep in all_deps:
                dep_lower = dep.lower()
                for web_dep in web_server_deps:
                    if web_dep in dep_lower:
                        if tunnel_info.tunnel_type == TunnelType.NONE:
                            tunnel_info.tunnel_type = TunnelType.NGROK
                            tunnel_info.priority = TunnelPriority.PRIMARY
                            tunnel_info.required = True
                        break
            
            return tunnel_info
        
        except Exception as e:
            return tunnel_info
    
    def _get_tunnel_arguments(self, tunnel_info: TunnelInfo) -> Dict[str, Any]:
        """Get tunnel-specific arguments."""
        try:
            args = {}
            
            if tunnel_info.tunnel_type == TunnelType.NGROK:
                args = {
                    "port": tunnel_info.port or 7860,
                    "host": tunnel_info.host,
                    "protocol": tunnel_info.protocol,
                    "subdomain": tunnel_info.subdomain,
                    "authtoken": None,  # Will be set from environment
                    "region": "us",
                    "log_level": "info"
                }
                
                if tunnel_info.share_enabled:
                    args["share"] = True
                
                if tunnel_info.ssl_enabled:
                    args["protocol"] = "https"
            
            elif tunnel_info.tunnel_type == TunnelType.CLOUDFLARE:
                args = {
                    "port": tunnel_info.port or 8080,
                    "host": tunnel_info.host,
                    "protocol": tunnel_info.protocol,
                    "hostname": tunnel_info.custom_domain,
                    "url": f"{tunnel_info.protocol}://{tunnel_info.host}:{tunnel_info.port or 8080}"
                }
            
            elif tunnel_info.tunnel_type == TunnelType.LOCALTUNNEL:
                args = {
                    "port": tunnel_info.port or 3000,
                    "host": tunnel_info.host,
                    "subdomain": tunnel_info.subdomain
                }
            
            elif tunnel_info.tunnel_type == TunnelType.SSH:
                args = {
                    "port": tunnel_info.port or 22,
                    "host": tunnel_info.host,
                    "remote_port": tunnel_info.port or 8080,
                    "local_port": tunnel_info.port or 8080
                }
            
            return args
        
        except Exception as e:
            return {}
    
    def _get_fallback_tunnels(self, tunnel_info: TunnelInfo) -> List[TunnelType]:
        """Get fallback tunnel options."""
        try:
            fallbacks = []
            
            if tunnel_info.tunnel_type == TunnelType.NGROK:
                fallbacks = [TunnelType.CLOUDFLARE, TunnelType.LOCALTUNNEL]
            elif tunnel_info.tunnel_type == TunnelType.CLOUDFLARE:
                fallbacks = [TunnelType.NGROK, TunnelType.LOCALTUNNEL]
            elif tunnel_info.tunnel_type == TunnelType.LOCALTUNNEL:
                fallbacks = [TunnelType.NGROK, TunnelType.CLOUDFLARE]
            elif tunnel_info.tunnel_type == TunnelType.SSH:
                fallbacks = [TunnelType.NGROK, TunnelType.CLOUDFLARE]
            elif tunnel_info.tunnel_type == TunnelType.NONE:
                fallbacks = [TunnelType.NGROK, TunnelType.CLOUDFLARE, TunnelType.LOCALTUNNEL]
            
            return fallbacks
        
        except Exception as e:
            return []
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def get_tunnel_launch_command(self, tunnel_info: TunnelInfo) -> str:
        """
        Get the command to launch the tunnel.
        
        Args:
            tunnel_info: Tunnel information
            
        Returns:
            Command string to launch tunnel
        """
        try:
            if tunnel_info.tunnel_type == TunnelType.NGROK:
                cmd = f"ngrok {tunnel_info.protocol} {tunnel_info.port or 7860}"
                
                if tunnel_info.subdomain:
                    cmd += f" --subdomain={tunnel_info.subdomain}"
                
                if tunnel_info.authentication_required:
                    cmd += " --authtoken=$NGROK_AUTHTOKEN"
                
                return cmd
            
            elif tunnel_info.tunnel_type == TunnelType.CLOUDFLARE:
                cmd = f"cloudflared tunnel --url {tunnel_info.protocol}://{tunnel_info.host}:{tunnel_info.port or 8080}"
                
                if tunnel_info.custom_domain:
                    cmd += f" --hostname={tunnel_info.custom_domain}"
                
                return cmd
            
            elif tunnel_info.tunnel_type == TunnelType.LOCALTUNNEL:
                cmd = f"lt --port {tunnel_info.port or 3000}"
                
                if tunnel_info.subdomain:
                    cmd += f" --subdomain={tunnel_info.subdomain}"
                
                return cmd
            
            elif tunnel_info.tunnel_type == TunnelType.SSH:
                cmd = f"ssh -L {tunnel_info.port or 8080}:{tunnel_info.host}:{tunnel_info.port or 8080} {tunnel_info.host}"
                return cmd
            
            else:
                return ""
        
        except Exception as e:
            return ""
    
    def validate_tunnel_config(self, tunnel_info: TunnelInfo) -> Dict[str, Any]:
        """
        Validate tunnel configuration.
        
        Args:
            tunnel_info: Tunnel information
            
        Returns:
            Validation results
        """
        try:
            validation = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": []
            }
            
            # Check if tunnel type is supported
            if tunnel_info.tunnel_type not in self.tunnel_configs:
                validation["valid"] = False
                validation["errors"].append(f"Unsupported tunnel type: {tunnel_info.tunnel_type.value}")
            
            # Check port configuration
            if tunnel_info.port is None:
                validation["warnings"].append("No port specified, using default")
            elif tunnel_info.port < 1 or tunnel_info.port > 65535:
                validation["valid"] = False
                validation["errors"].append(f"Invalid port number: {tunnel_info.port}")
            
            # Check host configuration
            if not tunnel_info.host:
                validation["warnings"].append("No host specified, using localhost")
            
            # Check authentication requirements
            if tunnel_info.authentication_required:
                if tunnel_info.tunnel_type == TunnelType.NGROK:
                    validation["suggestions"].append("Ensure NGROK_AUTHTOKEN environment variable is set")
                elif tunnel_info.tunnel_type == TunnelType.CLOUDFLARE:
                    validation["suggestions"].append("Ensure Cloudflare credentials are configured")
            
            # Check SSL configuration
            if tunnel_info.ssl_enabled:
                tunnel_config = self.tunnel_configs.get(tunnel_info.tunnel_type, {})
                if not tunnel_config.get("ssl", False):
                    validation["warnings"].append(f"SSL not supported by {tunnel_info.tunnel_type.value}")
            
            return validation
        
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "suggestions": []
            }


def main():
    """Main function for testing tunnel requirements."""
    print("🧪 Testing Tunnel Requirements")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = TunnelRequirements()
    
    # Test with sample web UI info
    from .webui_detector import WebUIInfo, WebUIType
    
    webui_info = WebUIInfo(
        webui_type=WebUIType.GRADIO,
        main_file="app.py",
        port=7860,
        host="localhost",
        share_enabled=True,
        auto_launch=True
    )
    
    # Test tunnel requirements determination
    print("\n🌐 Testing tunnel requirements determination...")
    result = analyzer.determine_requirements(webui_info, None, None)
    
    print(f"✅ Tunnel type: {result.tunnel_type.value}")
    print(f"✅ Priority: {result.priority.value}")
    print(f"✅ Required: {result.required}")
    print(f"✅ Port: {result.port}")
    print(f"✅ Host: {result.host}")
    print(f"✅ Share enabled: {result.share_enabled}")
    print(f"✅ Auto launch: {result.auto_launch}")
    print(f"✅ Authentication required: {result.authentication_required}")
    print(f"✅ Protocol: {result.protocol}")
    print(f"✅ SSL enabled: {result.ssl_enabled}")
    print(f"✅ Fallback tunnels: {[t.value for t in result.fallback_tunnels]}")
    print(f"✅ Tunnel arguments: {result.tunnel_arguments}")
    
    # Test launch command
    print("\n🚀 Testing tunnel launch command...")
    launch_cmd = analyzer.get_tunnel_launch_command(result)
    print(f"✅ Launch command: {launch_cmd}")
    
    # Test validation
    print("\n✅ Testing tunnel validation...")
    validation = analyzer.validate_tunnel_config(result)
    print(f"✅ Valid: {validation['valid']}")
    if validation["errors"]:
        print(f"   Errors: {', '.join(validation['errors'])}")
    if validation["warnings"]:
        print(f"   Warnings: {', '.join(validation['warnings'])}")
    if validation["suggestions"]:
        print(f"   Suggestions: {', '.join(validation['suggestions'])}")
    
    return True


if __name__ == "__main__":
    main()