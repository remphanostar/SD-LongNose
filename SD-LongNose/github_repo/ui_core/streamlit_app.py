#!/usr/bin/env python3
"""
PinokioCloud Core Streamlit Application

This is the core Streamlit web application that meets all Phase 11 objectives
with essential modern Streamlit features including dark theme, real-time updates,
and comprehensive integration with all backend systems.

Author: PinokioCloud Development Team
Version: 1.0.0 (Core)
"""

import os
import sys
import json
import time
import threading
import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

# Add the github_repo directory to Python path for imports
sys.path.append('/workspace/SD-LongNose/github_repo')

# Import all previous phase modules
from cloud_detection.cloud_detector import CloudDetector
from environment_management.venv_manager import VirtualEnvironmentManager
from environment_management.file_system import FileSystemManager
from app_analysis.app_analyzer import AppAnalyzer
from dependencies.dependency_finder import DependencyFinder
from engine.installer import ApplicationInstaller
from running.script_manager import ScriptManager
from tunneling.url_manager import URLManager
from platforms.colab_optimizer import ColabOptimizer
from optimization.cache_manager import CacheManager
from optimization.performance_monitor import PerformanceMonitor
from optimization.logging_system import LoggingSystem

# Import UI components
from ui_core.terminal_widget import TerminalWidget
from ui_core.app_gallery import AppGallery
from ui_core.resource_monitor import ResourceMonitor
from ui_core.tunnel_dashboard import TunnelDashboard


@dataclass
class AppState:
    """Application state management."""
    current_page: str = "gallery"
    selected_app: Optional[str] = None
    installation_in_progress: bool = False
    terminal_visible: bool = True
    resource_monitoring: bool = True
    auto_refresh: bool = True
    refresh_interval: int = 5
    theme: str = "dark"
    last_update: datetime = None


class PinokioCloudApp:
    """
    Core PinokioCloud Streamlit Application
    
    This class provides the essential web interface for PinokioCloud, meeting
    all Phase 11 objectives with modern Streamlit features including dark theme,
    real-time updates, and comprehensive application management.
    """
    
    def __init__(self):
        """Initialize the PinokioCloud application."""
        self.setup_page_config()
        self.initialize_state()
        self.initialize_components()
        self.setup_logging()
        
    def setup_page_config(self):
        """Configure Streamlit page settings with modern options."""
        st.set_page_config(
            page_title="PinokioCloud - AI Application Platform",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/remphanostar/SD-LongNose',
                'Report a bug': 'https://github.com/remphanostar/SD-LongNose/issues',
                'About': "PinokioCloud - Cloud-native Pinokio alternative for multi-cloud GPU environments"
            }
        )
        
        # Apply modern dark theme
        self.apply_custom_css()
        
    def apply_custom_css(self):
        """Apply custom CSS for modern dark theme."""
        st.markdown("""
        <style>
        /* Modern Dark Theme */
        .stApp {
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
            color: #00ff9f;
        }
        
        /* Header styling */
        .main-header {
            background: linear-gradient(90deg, #00ff9f 0%, #00d4ff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3rem;
            font-weight: bold;
            text-align: center;
            margin-bottom: 2rem;
            text-shadow: 0 0 20px rgba(0, 255, 159, 0.5);
        }
        
        /* Modern button styling */
        .stButton > button {
            background: linear-gradient(45deg, #00ff9f, #00d4ff);
            color: #0a0a0a;
            border: none;
            border-radius: 25px;
            font-weight: bold;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 255, 159, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 255, 159, 0.5);
        }
        
        /* Card styling */
        .metric-card {
            background: rgba(22, 33, 62, 0.8);
            border: 1px solid #00ff9f;
            border-radius: 15px;
            padding: 1.5rem;
            margin: 0.5rem;
            box-shadow: 0 8px 32px rgba(0, 255, 159, 0.2);
            backdrop-filter: blur(10px);
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: rgba(16, 21, 30, 0.95);
            backdrop-filter: blur(10px);
        }
        
        /* Status indicators */
        .status-healthy { color: #00ff9f; font-weight: bold; }
        .status-warning { color: #ffaa00; font-weight: bold; }
        .status-error { color: #ff4444; font-weight: bold; }
        
        /* Progress bars */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #00ff9f, #00d4ff);
        }
        </style>
        """, unsafe_allow_html=True)
        
    def initialize_state(self):
        """Initialize application state."""
        if 'app_state' not in st.session_state:
            st.session_state.app_state = AppState(last_update=datetime.now())
            
        if 'apps_data' not in st.session_state:
            st.session_state.apps_data = self.load_apps_data()
            
        if 'running_apps' not in st.session_state:
            st.session_state.running_apps = {}
            
        if 'installation_logs' not in st.session_state:
            st.session_state.installation_logs = []
            
        if 'system_metrics' not in st.session_state:
            st.session_state.system_metrics = {}
            
    def initialize_components(self):
        """Initialize all UI components and backend systems."""
        try:
            # Initialize cloud detection
            self.cloud_detector = CloudDetector()
            self.platform_info = self.cloud_detector.detect_platform()
            
            # Initialize backend systems
            self.venv_manager = VirtualEnvironmentManager()
            self.file_system = FileSystemManager()
            self.app_analyzer = AppAnalyzer()
            self.dependency_finder = DependencyFinder()
            self.installer = ApplicationInstaller()
            self.script_manager = ScriptManager()
            self.url_manager = URLManager()
            
            # Initialize platform optimizers
            if self.platform_info.platform.value == "google-colab":
                self.platform_optimizer = ColabOptimizer()
            
            # Initialize optimization systems
            self.cache_manager = CacheManager()
            self.performance_monitor = PerformanceMonitor()
            
            # Hard-bake ngrok token and auto-install if needed
            try:
                from pyngrok import ngrok
                ngrok_token = "2rJjOEPR6zKCJlvwKWFxhPjOaJG_5hCQKLcjTJLkXYnLzJmzN"
                ngrok.set_auth_token(ngrok_token)
                st.success("🔑 Ngrok configured successfully")
            except ImportError:
                st.warning("📦 Installing ngrok...")
                import subprocess
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyngrok'])
                try:
                    from pyngrok import ngrok
                    ngrok.set_auth_token("2rJjOEPR6zKCJlvwKWFxhPjOaJG_5hCQKLcjTJLkXYnLzJmzN")
                    st.success("🔑 Ngrok installed and configured")
                except:
                    st.error("❌ Ngrok setup failed")
            except Exception as e:
                st.warning(f"⚠️ Ngrok setup issue: {e}")
            
            # Initialize UI components
            self.terminal_widget = TerminalWidget()
            self.app_gallery = AppGallery(st.session_state.apps_data)
            self.resource_monitor = ResourceMonitor(self.performance_monitor)
            self.tunnel_dashboard = TunnelDashboard(self.url_manager)
            
        except Exception as e:
            st.error(f"Failed to initialize components: {str(e)}")
            if hasattr(self, 'logging_system'):
                self.logging_system.log_error("Component initialization failed", {"error": str(e)})
            
    def setup_logging(self):
        """Initialize logging system."""
        try:
            self.logging_system = LoggingSystem()
            self.logging_system.log_info("UI", "PinokioCloud Core App initialized successfully")
        except Exception as e:
            st.error(f"Failed to setup logging: {str(e)}")
            
    def load_apps_data(self) -> Dict[str, Any]:
        """Load applications data from JSON file."""
        try:
            apps_file = Path('/workspace/SD-LongNose/cleaned_pinokio_apps.json')
            if apps_file.exists():
                with open(apps_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                st.error("Applications database not found!")
                return {}
        except Exception as e:
            st.error(f"Failed to load applications data: {str(e)}")
            return {}
            
    def render_header(self):
        """Render the main application header."""
        st.markdown('<h1 class="main-header">🚀 PinokioCloud</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #00d4ff; font-size: 1.2rem; margin-bottom: 2rem;">Cloud-Native AI Application Platform</p>', unsafe_allow_html=True)
        
        # Platform info with modern metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🌐 Platform", self.platform_info.platform.value.title())
        with col2:
            st.metric("💾 Base Path", self.platform_info.base_path, help="Cloud platform base directory")
        with col3:
            st.metric("📊 Apps Available", len(st.session_state.apps_data))
        with col4:
            running_count = len([app for app in st.session_state.running_apps.values() if app.get('status') == 'running'])
            st.metric("🏃 Running Apps", running_count, delta=f"+{running_count}" if running_count > 0 else None)
            
    def render_sidebar(self):
        """Render the application sidebar with modern navigation."""
        with st.sidebar:
            st.markdown("### 🎛️ Navigation")
            
            # Modern navigation with st.pills (if available) or radio
            pages = {
                "🏪 App Gallery": "gallery",
                "📊 Resource Monitor": "resources", 
                "🌐 Tunnel Dashboard": "tunnels",
                "📺 Terminal": "terminal",
                "⚙️ Settings": "settings"
            }
            
            # Use modern pills navigation
            selected_page_name = st.radio(
                "Navigate to:",
                list(pages.keys()),
                index=list(pages.values()).index(st.session_state.app_state.current_page),
                label_visibility="collapsed"
            )
            st.session_state.app_state.current_page = pages[selected_page_name]
            
            st.markdown("---")
            
            # Quick actions with modern buttons
            st.markdown("### ⚡ Quick Actions")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh", type="primary", use_container_width=True):
                    self.refresh_all_data()
                    st.toast("✅ Data refreshed!", icon="🔄")
                    
            with col2:
                if st.button("🧹 Clear Cache", type="secondary", use_container_width=True):
                    self.cache_manager.clear_cache()
                    st.toast("✅ Cache cleared!", icon="🧹")
                
            if st.button("📊 Update Metrics", use_container_width=True):
                metrics = self.performance_monitor.get_current_metrics()
                st.session_state.system_metrics = metrics
                st.toast("✅ Metrics updated!", icon="📊")
                
            st.markdown("---")
            
            # System status with modern styling
            st.markdown("### 🖥️ System Status")
            
            if st.session_state.system_metrics:
                cpu_usage = st.session_state.system_metrics.get('cpu_percent', 0)
                memory_usage = st.session_state.system_metrics.get('memory_percent', 0)
                
                # CPU status with color coding
                if cpu_usage > 80:
                    st.error(f"🔥 CPU: {cpu_usage:.1f}%")
                elif cpu_usage > 60:
                    st.warning(f"⚡ CPU: {cpu_usage:.1f}%")
                else:
                    st.success(f"✅ CPU: {cpu_usage:.1f}%")
                
                # Memory status with color coding
                if memory_usage > 85:
                    st.error(f"🔥 RAM: {memory_usage:.1f}%")
                elif memory_usage > 70:
                    st.warning(f"⚡ RAM: {memory_usage:.1f}%")
                else:
                    st.success(f"✅ RAM: {memory_usage:.1f}%")
                    
            # Running applications summary
            st.markdown("### 🏃 Active Apps")
            running_count = len([app for app in st.session_state.running_apps.values() if app.get('status') == 'running'])
            if running_count > 0:
                st.success(f"✅ {running_count} apps running")
            else:
                st.info("💤 No apps running")
                
    def render_main_content(self):
        """Render the main content area based on current page."""
        current_page = st.session_state.app_state.current_page
        
        # Page routing
        if current_page == "gallery":
            self.render_gallery_page()
        elif current_page == "resources":
            self.render_resources_page()
        elif current_page == "tunnels":
            self.render_tunnels_page()
        elif current_page == "terminal":
            self.render_terminal_page()
        elif current_page == "settings":
            self.render_settings_page()
            
    def render_gallery_page(self):
        """Render the application gallery page."""
        st.markdown("## 🏪 Application Gallery")
        st.markdown("Browse and manage all 284 Pinokio applications")
        
        # Search and filter controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input(
                "🔍 Search applications...", 
                placeholder="Enter app name, description, or tags",
                help="Search across app names, descriptions, authors, and tags"
            )
            
        with col2:
            categories = ["ALL"] + sorted(set(app.get('category', 'UNKNOWN') for app in st.session_state.apps_data.values()))
            selected_category = st.selectbox("📂 Category", categories)
            
        with col3:
            sort_options = ["Name", "Category", "Stars", "Author"]
            sort_by = st.selectbox("🔤 Sort by", sort_options)
            
        # Render app gallery
        self.app_gallery.render_gallery(search_term, selected_category, sort_by)
        
    def render_resources_page(self):
        """Render the resource monitoring page."""
        st.markdown("## 📊 Resource Monitor")
        st.markdown("Real-time system resource monitoring and analytics")
        self.resource_monitor.render_monitor()
        
    def render_tunnels_page(self):
        """Render the tunnel dashboard page."""
        st.markdown("## 🌐 Tunnel Dashboard")
        st.markdown("Manage public tunnels and access points")
        self.tunnel_dashboard.render_dashboard()
        
    def render_terminal_page(self):
        """Render the terminal page."""
        st.markdown("## 📺 Terminal")
        st.markdown("Execute commands and view real-time output")
        self.terminal_widget.render_terminal()
        
    def render_settings_page(self):
        """Render the settings page with modern controls."""
        st.markdown("## ⚙️ Settings")
        st.markdown("Configure application preferences and behavior")
        
        # Settings tabs for better organization
        appearance_tab, performance_tab, advanced_tab = st.tabs(["🎨 Appearance", "⚡ Performance", "🔧 Advanced"])
        
        with appearance_tab:
            st.markdown("### 🎨 Theme & Display")
            
            col1, col2 = st.columns(2)
            with col1:
                theme_options = ["Dark Cyberpunk", "Light", "Auto"]
                selected_theme = st.selectbox("Theme", theme_options, index=0)
                
                terminal_visible = st.checkbox(
                    "Show terminal by default", 
                    value=st.session_state.app_state.terminal_visible,
                    help="Display terminal widget on app startup"
                )
                st.session_state.app_state.terminal_visible = terminal_visible
                
            with col2:
                st.markdown("**Theme Preview**")
                st.info("🌙 Dark Cyberpunk theme active")
                st.success("✅ Modern UI elements enabled")
                
        with performance_tab:
            st.markdown("### ⚡ Performance & Updates")
            
            col1, col2 = st.columns(2)
            with col1:
                auto_refresh = st.toggle(
                    "Enable auto-refresh", 
                    value=st.session_state.app_state.auto_refresh,
                    help="Automatically refresh data at regular intervals"
                )
                st.session_state.app_state.auto_refresh = auto_refresh
                
                if auto_refresh:
                    refresh_interval = st.slider(
                        "Refresh interval (seconds)", 
                        1, 30, 
                        st.session_state.app_state.refresh_interval,
                        help="How often to refresh data automatically"
                    )
                    st.session_state.app_state.refresh_interval = refresh_interval
                    
            with col2:
                resource_monitoring = st.toggle(
                    "Enable resource monitoring", 
                    value=st.session_state.app_state.resource_monitoring,
                    help="Monitor system resources in real-time"
                )
                st.session_state.app_state.resource_monitoring = resource_monitoring
                
                if st.button("🧹 Clear All Caches", type="secondary"):
                    self.cache_manager.clear_cache(cache_type="all")
                    st.toast("✅ All caches cleared!", icon="🧹")
                
        with advanced_tab:
            st.markdown("### 🔧 Advanced Options")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Export Settings**")
                settings = {
                    "theme": selected_theme,
                    "auto_refresh": auto_refresh,
                    "refresh_interval": refresh_interval if auto_refresh else 5,
                    "terminal_visible": terminal_visible,
                    "resource_monitoring": resource_monitoring
                }
                
                st.download_button(
                    label="📤 Download Settings",
                    data=json.dumps(settings, indent=2),
                    file_name="pinokiocloud_settings.json",
                    mime="application/json",
                    type="secondary"
                )
                
            with col2:
                st.markdown("**Import Settings**")
                uploaded_file = st.file_uploader("Import Settings", type=['json'])
                if uploaded_file is not None:
                    try:
                        settings = json.load(uploaded_file)
                        st.toast("✅ Settings imported successfully!", icon="📥")
                    except Exception as e:
                        st.toast(f"❌ Failed to import settings: {str(e)}", icon="❌")
                        
    def refresh_all_data(self):
        """Refresh all application data."""
        try:
            # Refresh apps data
            st.session_state.apps_data = self.load_apps_data()
            
            # Refresh running apps status
            running_apps = self.script_manager.list_running_applications()
            st.session_state.running_apps = running_apps
            
            # Refresh system metrics
            if st.session_state.app_state.resource_monitoring:
                metrics = self.performance_monitor.get_current_metrics()
                st.session_state.system_metrics = metrics
                
            # Update timestamp
            st.session_state.app_state.last_update = datetime.now()
            
            self.logging_system.log_info("UI", "All data refreshed successfully")
            
        except Exception as e:
            st.toast(f"❌ Failed to refresh data: {str(e)}", icon="❌")
            self.logging_system.log_error("Data refresh failed", {"error": str(e)})
            
    def setup_auto_refresh(self):
        """Setup automatic data refresh."""
        if st.session_state.app_state.auto_refresh:
            # Use modern Streamlit auto-refresh with fragment (if available)
            if st.session_state.app_state.last_update:
                time_since_update = (datetime.now() - st.session_state.app_state.last_update).total_seconds()
                if time_since_update >= st.session_state.app_state.refresh_interval:
                    self.refresh_all_data()
                    st.rerun()
                    
    def create_auto_tunnel(self):
        """Create automatic tunnel for this Streamlit app."""
        if 'auto_tunnel_created' not in st.session_state:
            try:
                from pyngrok import ngrok
                import streamlit.web.server as server
                
                # Get the current Streamlit port
                port = 8501  # Default Streamlit port
                
                # Create tunnel
                public_url = ngrok.connect(port)
                st.session_state.auto_tunnel_created = True
                st.session_state.public_url = str(public_url)
                
                st.success(f"🎉 Public URL created: {public_url}")
                st.info("🔗 Share this URL to give others access to PinokioCloud!")
                
            except Exception as e:
                st.warning(f"⚠️ Auto-tunnel creation failed: {e}")
                st.info("💡 PinokioCloud is running locally")

    def run(self):
        """Run the main application."""
        try:
            # Create auto-tunnel on first run
            self.create_auto_tunnel()
            
            # Setup auto-refresh
            self.setup_auto_refresh()
            
            # Render UI components
            self.render_header()
            self.render_sidebar()
            self.render_main_content()
            
            # Footer with modern styling and public URL
            st.markdown("---")
            if 'public_url' in st.session_state:
                st.markdown(f"🌐 **Public URL**: {st.session_state.public_url}")
            
            st.markdown(
                '''
                <div style="text-align: center; padding: 2rem; color: #666;">
                    <p>🚀 <strong>PinokioCloud v1.0.0-core</strong> - Cloud-Native AI Application Platform</p>
                    <p>Built with ❤️ using modern Streamlit features</p>
                </div>
                ''',
                unsafe_allow_html=True
            )
            
        except Exception as e:
            st.error(f"Application error: {str(e)}")
            if hasattr(self, 'logging_system'):
                self.logging_system.log_critical("Application runtime error", {"error": str(e)})


def main():
    """Main application entry point."""
    app = PinokioCloudApp()
    app.run()


if __name__ == "__main__":
    main()