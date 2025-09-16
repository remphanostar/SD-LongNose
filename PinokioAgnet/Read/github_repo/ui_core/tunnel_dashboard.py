#!/usr/bin/env python3
"""
PinokioCloud Core Tunnel Dashboard

This module provides core tunnel management functionality with modern Streamlit
features including st.metric, st.status, st.toast, and QR code generation
for comprehensive tunnel monitoring and management.

Author: PinokioCloud Development Team
Version: 1.0.0 (Core)
"""

import os
import sys
import time
import threading
import streamlit as st
import qrcode
import io
import base64
from PIL import Image
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import requests

# Add the github_repo directory to Python path for imports
sys.path.append('/workspace/SD-LongNose/github_repo')

from tunneling.url_manager import URLManager, TunnelType, URLStatus
from tunneling.ngrok_manager import NgrokManager
from tunneling.cloudflare_manager import CloudflareManager
from optimization.logging_system import LoggingSystem


class TunnelHealth(Enum):
    """Tunnel health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class TunnelInfo:
    """Information about an active tunnel."""
    id: str
    name: str
    url: str
    tunnel_type: TunnelType
    status: URLStatus
    health: TunnelHealth
    app_name: str
    port: int
    created_at: datetime
    last_checked: datetime
    response_time: float
    error_count: int
    total_requests: int
    qr_code: Optional[str] = None


class TunnelDashboard:
    """
    Core Tunnel Dashboard for PinokioCloud
    
    This class provides essential tunnel monitoring and management with modern
    Streamlit features including real-time status, QR codes, metrics, and
    comprehensive tunnel analytics.
    """
    
    def __init__(self, url_manager: URLManager):
        """
        Initialize the tunnel dashboard.
        
        Args:
            url_manager: URL management system
        """
        self.url_manager = url_manager
        self.ngrok_manager = NgrokManager()
        self.cloudflare_manager = CloudflareManager()
        self.logging_system = LoggingSystem()
        
        # Initialize session state
        if 'active_tunnels' not in st.session_state:
            st.session_state.active_tunnels = {}
        if 'tunnel_history' not in st.session_state:
            st.session_state.tunnel_history = []
        if 'tunnel_analytics' not in st.session_state:
            st.session_state.tunnel_analytics = {}
        if 'auto_refresh_tunnels' not in st.session_state:
            st.session_state.auto_refresh_tunnels = True
        if 'tunnel_refresh_interval' not in st.session_state:
            st.session_state.tunnel_refresh_interval = 10
        if 'show_qr_codes' not in st.session_state:
            st.session_state.show_qr_codes = True
            
    def generate_qr_code(self, url: str, size: int = 200) -> str:
        """Generate QR code for a URL with modern styling."""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            # Create QR code image with cyberpunk colors
            img = qr.make_image(fill_color="#00ff9f", back_color="#0a0a0a")
            img = img.resize((size, size))
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            self.logging_system.log_error("Failed to generate QR code", {"url": url, "error": str(e)})
            return None
            
    def check_tunnel_health(self, url: str) -> Tuple[TunnelHealth, float]:
        """Check the health of a tunnel."""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10, allow_redirects=True)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code == 200:
                return TunnelHealth.HEALTHY, response_time
            elif 200 <= response.status_code < 400:
                return TunnelHealth.DEGRADED, response_time
            else:
                return TunnelHealth.UNHEALTHY, response_time
                
        except requests.exceptions.Timeout:
            return TunnelHealth.DEGRADED, 10000  # 10 second timeout
        except requests.exceptions.ConnectionError:
            return TunnelHealth.OFFLINE, 0
        except Exception as e:
            self.logging_system.log_error("Tunnel health check failed", {"url": url, "error": str(e)})
            return TunnelHealth.UNKNOWN, 0
            
    def update_tunnel_status(self):
        """Update the status of all active tunnels."""
        try:
            # Get active URLs from URL manager
            urls = self.url_manager.get_active_urls()
            
            updated_tunnels = {}
            
            for url_info in urls:
                tunnel_id = url_info.get('id', '')
                tunnel_url = url_info.get('url', '')
                
                if not tunnel_id or not tunnel_url:
                    continue
                    
                # Check tunnel health
                health, response_time = self.check_tunnel_health(tunnel_url)
                
                # Generate QR code if needed
                qr_code = None
                if st.session_state.show_qr_codes:
                    qr_code = self.generate_qr_code(tunnel_url)
                    
                # Create tunnel info
                tunnel_info = TunnelInfo(
                    id=tunnel_id,
                    name=url_info.get('name', f"Tunnel {tunnel_id[:8]}"),
                    url=tunnel_url,
                    tunnel_type=TunnelType(url_info.get('type', 'ngrok')),
                    status=URLStatus(url_info.get('status', 'active')),
                    health=health,
                    app_name=url_info.get('app_name', 'Unknown'),
                    port=url_info.get('port', 0),
                    created_at=datetime.fromisoformat(url_info.get('created_at', datetime.now().isoformat())),
                    last_checked=datetime.now(),
                    response_time=response_time,
                    error_count=url_info.get('error_count', 0),
                    total_requests=url_info.get('total_requests', 0),
                    qr_code=qr_code
                )
                
                updated_tunnels[tunnel_id] = tunnel_info
                
            # Update session state
            st.session_state.active_tunnels = updated_tunnels
            
            # Update analytics
            self.update_tunnel_analytics()
            
        except Exception as e:
            st.toast(f"❌ Failed to update tunnel status: {str(e)}", icon="❌")
            self.logging_system.log_error("Tunnel status update failed", {"error": str(e)})
            
    def update_tunnel_analytics(self):
        """Update tunnel analytics data."""
        try:
            analytics = {
                'total_tunnels': len(st.session_state.active_tunnels),
                'healthy_tunnels': len([t for t in st.session_state.active_tunnels.values() if t.health == TunnelHealth.HEALTHY]),
                'degraded_tunnels': len([t for t in st.session_state.active_tunnels.values() if t.health == TunnelHealth.DEGRADED]),
                'unhealthy_tunnels': len([t for t in st.session_state.active_tunnels.values() if t.health == TunnelHealth.UNHEALTHY]),
                'offline_tunnels': len([t for t in st.session_state.active_tunnels.values() if t.health == TunnelHealth.OFFLINE]),
                'average_response_time': 0,
                'tunnel_types': {},
                'last_updated': datetime.now()
            }
            
            # Calculate average response time
            if st.session_state.active_tunnels:
                total_response_time = sum(t.response_time for t in st.session_state.active_tunnels.values())
                analytics['average_response_time'] = total_response_time / len(st.session_state.active_tunnels)
                
            # Count tunnel types
            for tunnel in st.session_state.active_tunnels.values():
                tunnel_type = tunnel.tunnel_type.value
                analytics['tunnel_types'][tunnel_type] = analytics['tunnel_types'].get(tunnel_type, 0) + 1
                
            st.session_state.tunnel_analytics = analytics
            
        except Exception as e:
            self.logging_system.log_error("Tunnel analytics update failed", {"error": str(e)})
            
    def render_tunnel_overview(self):
        """Render tunnel overview metrics with modern Streamlit features."""
        st.markdown("### 🌐 Tunnel Overview")
        
        analytics = st.session_state.tunnel_analytics
        
        if not analytics:
            st.info("📊 No tunnel analytics available yet.")
            return
            
        # Overview metrics with modern styling
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_tunnels = analytics.get('total_tunnels', 0)
            st.metric(
                label="🚇 Total Tunnels",
                value=total_tunnels,
                help="Total number of active tunnels"
            )
            
        with col2:
            healthy_tunnels = analytics.get('healthy_tunnels', 0)
            health_percentage = (healthy_tunnels/max(total_tunnels, 1)*100) if total_tunnels > 0 else 0
            st.metric(
                label="✅ Healthy",
                value=healthy_tunnels,
                delta=f"{health_percentage:.1f}%",
                help="Number of healthy tunnels"
            )
            
        with col3:
            avg_response_time = analytics.get('average_response_time', 0)
            st.metric(
                label="⚡ Avg Response",
                value=f"{avg_response_time:.0f}ms",
                help="Average response time across all tunnels"
            )
            
        with col4:
            offline_tunnels = analytics.get('offline_tunnels', 0)
            st.metric(
                label="🔴 Offline",
                value=offline_tunnels,
                delta=f"-{offline_tunnels}" if offline_tunnels > 0 else None,
                help="Number of offline tunnels"
            )
            
        # Health status chart
        if total_tunnels > 0:
            health_data = {
                'Healthy': analytics.get('healthy_tunnels', 0),
                'Degraded': analytics.get('degraded_tunnels', 0),
                'Unhealthy': analytics.get('unhealthy_tunnels', 0),
                'Offline': analytics.get('offline_tunnels', 0)
            }
            
            # Filter out zero values
            health_data = {k: v for k, v in health_data.items() if v > 0}
            
            if health_data:
                fig_health = px.pie(
                    values=list(health_data.values()),
                    names=list(health_data.keys()),
                    title="Tunnel Health Distribution",
                    color_discrete_map={
                        'Healthy': '#00ff9f',
                        'Degraded': '#ffaa00',
                        'Unhealthy': '#ff6b6b',
                        'Offline': '#666666'
                    }
                )
                fig_health.update_layout(
                    height=300, 
                    template='plotly_dark',
                    title_font_color='#00ff9f',
                    title_x=0.5
                )
                st.plotly_chart(fig_health, use_container_width=True)
                
    def render_active_tunnels(self):
        """Render active tunnels list with modern cards."""
        st.markdown("### 🚇 Active Tunnels")
        
        if not st.session_state.active_tunnels:
            st.info("🌐 No active tunnels found. Start an application to create tunnels.")
            
            # Show example of how to create tunnels
            with st.expander("💡 How to create tunnels", expanded=False):
                st.markdown("""
                **To create tunnels:**
                1. Go to **App Gallery** and install an application
                2. Start the application - it will automatically create tunnels
                3. Tunnels will appear here with QR codes for mobile access
                """)
            return
            
        # Sort tunnels by health and name
        sorted_tunnels = sorted(
            st.session_state.active_tunnels.values(),
            key=lambda t: (t.health.value, t.name)
        )
        
        for tunnel in sorted_tunnels:
            self.render_tunnel_card(tunnel)
            
    def render_tunnel_card(self, tunnel: TunnelInfo):
        """Render an individual tunnel card with modern styling."""
        # Health status colors and icons
        health_colors = {
            TunnelHealth.HEALTHY: "#00ff9f",
            TunnelHealth.DEGRADED: "#ffaa00",
            TunnelHealth.UNHEALTHY: "#ff6b6b",
            TunnelHealth.OFFLINE: "#666666",
            TunnelHealth.UNKNOWN: "#888888"
        }
        
        health_icons = {
            TunnelHealth.HEALTHY: "✅",
            TunnelHealth.DEGRADED: "⚠️",
            TunnelHealth.UNHEALTHY: "❌",
            TunnelHealth.OFFLINE: "🔴",
            TunnelHealth.UNKNOWN: "❓"
        }
        
        health_color = health_colors.get(tunnel.health, "#888888")
        health_icon = health_icons.get(tunnel.health, "❓")
        
        # Create modern tunnel card
        with st.container():
            # Card header
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {health_icon} {tunnel.name}")
                st.markdown(f"**📱 App:** {tunnel.app_name} | **🔌 Port:** {tunnel.port}")
            with col2:
                st.markdown(f'<div style="text-align: right; color: {health_color}; font-weight: bold; font-size: 1.2rem;">{tunnel.health.value.title()}</div>', unsafe_allow_html=True)
                
            # Tunnel details and actions
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                # Tunnel information
                st.markdown(f"**🌐 URL:** `{tunnel.url}`")
                st.markdown(f"**🔗 Type:** {tunnel.tunnel_type.value.title()}")
                
                # Response time with color coding
                if tunnel.response_time < 500:
                    st.success(f"⚡ Response: {tunnel.response_time:.0f}ms")
                elif tunnel.response_time < 2000:
                    st.warning(f"⚡ Response: {tunnel.response_time:.0f}ms")
                else:
                    st.error(f"⚡ Response: {tunnel.response_time:.0f}ms")
                
                st.markdown(f"**🕒 Created:** {tunnel.created_at.strftime('%H:%M:%S')}")
                
            with col2:
                # Action buttons with modern styling
                st.markdown("**🛠️ Actions:**")
                
                # Open URL button
                st.link_button("🔗 Open", tunnel.url, use_container_width=True)
                
                # Health check button
                if st.button("🔍 Check", key=f"health_{tunnel.id}", use_container_width=True):
                    with st.status("Checking tunnel health...", expanded=False) as status:
                        health, response_time = self.check_tunnel_health(tunnel.url)
                        if health == TunnelHealth.HEALTHY:
                            status.update(label="✅ Tunnel is healthy", state="complete")
                            st.toast(f"✅ Tunnel healthy ({response_time:.0f}ms)", icon="✅")
                        elif health == TunnelHealth.DEGRADED:
                            status.update(label="⚠️ Tunnel degraded", state="error")
                            st.toast(f"⚠️ Tunnel degraded ({response_time:.0f}ms)", icon="⚠️")
                        else:
                            status.update(label="❌ Tunnel unhealthy", state="error")
                            st.toast(f"❌ Tunnel {health.value}", icon="❌")
                            
                # Remove tunnel button
                if st.button("🗑️ Remove", key=f"remove_{tunnel.id}", type="secondary", use_container_width=True):
                    if tunnel.id in st.session_state.active_tunnels:
                        del st.session_state.active_tunnels[tunnel.id]
                        st.toast(f"🗑️ Removed tunnel {tunnel.name}", icon="🗑️")
                        st.rerun()
                        
            with col3:
                # QR Code and statistics
                if tunnel.qr_code and st.session_state.show_qr_codes:
                    st.markdown("**📱 QR Code:**")
                    st.markdown(
                        f'''
                        <div style="text-align: center; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 10px;">
                            <img src="{tunnel.qr_code}" alt="QR Code" style="width: 120px; height: 120px; border: 2px solid #00ff9f; border-radius: 8px;">
                            <p style="margin: 5px 0 0 0; font-size: 0.8rem; color: #888;">Scan for mobile access</p>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )
                else:
                    st.info("📱 QR codes disabled")
                    
                # Statistics
                st.markdown("**📊 Statistics:**")
                st.metric("Requests", tunnel.total_requests)
                st.metric("Errors", tunnel.error_count)
                if tunnel.total_requests > 0:
                    error_rate = (tunnel.error_count / tunnel.total_requests) * 100
                    st.metric("Error Rate", f"{error_rate:.1f}%")
                    
            st.markdown("---")
            
    def render_tunnel_controls(self):
        """Render tunnel management controls with modern interface."""
        st.markdown("### 🛠️ Tunnel Management")
        
        # Create tunnel section
        with st.expander("🚀 Create New Tunnel", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                app_name = st.text_input(
                    "Application Name", 
                    placeholder="my-awesome-app",
                    help="Name of the application to tunnel"
                )
                port = st.number_input(
                    "Port", 
                    min_value=1, 
                    max_value=65535, 
                    value=7860,
                    help="Port number where the application is running"
                )
                
            with col2:
                tunnel_type = st.selectbox(
                    "Tunnel Provider",
                    ["ngrok", "cloudflare"],
                    index=0,
                    help="Choose tunnel provider"
                )
                
                if st.button("🚀 Create Tunnel", type="primary", use_container_width=True):
                    if app_name and port:
                        with st.status(f"Creating {tunnel_type} tunnel...", expanded=True) as status:
                            try:
                                if tunnel_type == "ngrok":
                                    status.write("🔗 Connecting to ngrok...")
                                    result = self.ngrok_manager.create_tunnel(port, f"http://localhost:{port}")
                                    if result and result.get('success'):
                                        status.update(label="✅ Ngrok tunnel created!", state="complete")
                                        st.toast(f"✅ Ngrok tunnel created: {result.get('url')}", icon="🚀")
                                    else:
                                        status.update(label="❌ Failed to create ngrok tunnel", state="error")
                                        st.toast("❌ Failed to create ngrok tunnel", icon="❌")
                                else:
                                    status.write("☁️ Connecting to Cloudflare...")
                                    result = self.cloudflare_manager.create_tunnel(port, f"http://localhost:{port}")
                                    if result and result.get('success'):
                                        status.update(label="✅ Cloudflare tunnel created!", state="complete")
                                        st.toast(f"✅ Cloudflare tunnel created: {result.get('url')}", icon="☁️")
                                    else:
                                        status.update(label="❌ Failed to create cloudflare tunnel", state="error")
                                        st.toast("❌ Failed to create cloudflare tunnel", icon="❌")
                                        
                                # Refresh tunnels
                                self.update_tunnel_status()
                                st.rerun()
                                
                            except Exception as e:
                                status.update(label="🚨 Tunnel creation error", state="error")
                                st.toast(f"🚨 Failed to create tunnel: {str(e)}", icon="🚨")
                    else:
                        st.toast("⚠️ Please provide app name and port", icon="⚠️")
        
        # Dashboard controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🔄 Refresh")
            auto_refresh = st.toggle(
                "Auto-refresh tunnels",
                value=st.session_state.auto_refresh_tunnels,
                help="Automatically refresh tunnel status"
            )
            st.session_state.auto_refresh_tunnels = auto_refresh
            
            if auto_refresh:
                refresh_interval = st.slider(
                    "Interval (seconds)",
                    min_value=5,
                    max_value=60,
                    value=st.session_state.tunnel_refresh_interval,
                    help="Auto-refresh interval"
                )
                st.session_state.tunnel_refresh_interval = refresh_interval
                
        with col2:
            st.markdown("#### 📱 Display")
            show_qr_codes = st.toggle(
                "Show QR codes",
                value=st.session_state.show_qr_codes,
                help="Display QR codes for mobile access"
            )
            st.session_state.show_qr_codes = show_qr_codes
            
            if st.button("🔄 Refresh All", type="primary", use_container_width=True):
                with st.spinner("Refreshing all tunnels..."):
                    self.update_tunnel_status()
                    st.toast("✅ All tunnels refreshed!", icon="🔄")
                    st.rerun()
                    
        with col3:
            st.markdown("#### 📤 Export")
            
            if st.button("🧹 Clear All", type="secondary", use_container_width=True):
                st.session_state.active_tunnels = {}
                st.session_state.tunnel_analytics = {}
                st.toast("🧹 All tunnels cleared!", icon="🧹")
                st.rerun()
                
            # Export tunnel data
            if st.session_state.active_tunnels:
                tunnel_data = []
                for tunnel in st.session_state.active_tunnels.values():
                    tunnel_data.append({
                        'name': tunnel.name,
                        'url': tunnel.url,
                        'type': tunnel.tunnel_type.value,
                        'app': tunnel.app_name,
                        'port': tunnel.port,
                        'health': tunnel.health.value,
                        'response_time': tunnel.response_time,
                        'created_at': tunnel.created_at.isoformat()
                    })
                    
                tunnel_json = json.dumps(tunnel_data, indent=2)
                st.download_button(
                    label="📥 Export Data",
                    data=tunnel_json,
                    file_name=f"tunnel_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    type="secondary"
                )
                
    def render_dashboard(self):
        """Render the complete tunnel dashboard."""
        try:
            # Update tunnel status if auto-refresh is enabled
            if st.session_state.auto_refresh_tunnels:
                self.update_tunnel_status()
                
            # Render all dashboard components
            self.render_tunnel_overview()
            
            st.markdown("---")
            
            self.render_active_tunnels()
            
            st.markdown("---")
            
            self.render_tunnel_controls()
            
            # Auto-refresh functionality
            if st.session_state.auto_refresh_tunnels:
                time.sleep(st.session_state.tunnel_refresh_interval)
                st.rerun()
                
        except Exception as e:
            st.error(f"Tunnel dashboard error: {str(e)}")
            st.toast(f"❌ Dashboard error: {str(e)}", icon="❌")
            self.logging_system.log_error("Tunnel dashboard error", {"error": str(e)})


def main():
    """Test the core tunnel dashboard."""
    st.set_page_config(page_title="Core Tunnel Dashboard Test", layout="wide")
    
    st.title("🌐 Core Tunnel Dashboard Test")
    
    # Mock URL manager for testing
    class MockURLManager:
        def get_active_urls(self):
            return [
                {
                    'id': 'tunnel-1',
                    'name': 'Test App 1',
                    'url': 'https://abc123.ngrok.io',
                    'type': 'ngrok',
                    'status': 'active',
                    'app_name': 'Stable Diffusion',
                    'port': 7860,
                    'created_at': datetime.now().isoformat(),
                    'error_count': 0,
                    'total_requests': 42
                }
            ]
    
    mock_url_manager = MockURLManager()
    dashboard = TunnelDashboard(mock_url_manager)
    dashboard.render_dashboard()


if __name__ == "__main__":
    main()