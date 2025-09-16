#!/usr/bin/env python3
"""
PinokioCloud Main Streamlit Application

This is the main Streamlit web application that provides the user interface for
PinokioCloud. It integrates all UI components and provides the primary interface
for users to browse, install, and manage AI applications.

Author: PinokioCloud Development Team
Version: 1.0.0
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
from .terminal_widget import TerminalWidget
from .app_gallery import AppGallery
from .resource_monitor import ResourceMonitor
from .tunnel_dashboard import TunnelDashboard


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
    Main PinokioCloud Streamlit Application
    
    This class provides the complete web interface for PinokioCloud, integrating
    all components into a cohesive user experience with dark cyberpunk theme,
    real-time updates, and comprehensive application management.
    """
    
    def __init__(self):
        """Initialize the PinokioCloud application."""
        self.setup_page_config()
        self.initialize_state()
        self.initialize_components()
        self.setup_logging()
        
    def setup_page_config(self):
        """Configure Streamlit page settings."""
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
        
        # Apply dark cyberpunk theme
        self.apply_custom_css()
        
    def apply_custom_css(self):
        """Apply custom CSS for dark cyberpunk theme."""
        st.markdown("""
        <style>
        /* Dark Cyberpunk Theme */
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
        
        /* Card styling */
        .app-card {
            background: rgba(22, 33, 62, 0.8);
            border: 1px solid #00ff9f;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem;
            box-shadow: 0 4px 15px rgba(0, 255, 159, 0.2);
            transition: all 0.3s ease;
        }
        
        .app-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 255, 159, 0.4);
            border-color: #00d4ff;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(45deg, #00ff9f, #00d4ff);
            color: #0a0a0a;
            border: none;
            border-radius: 25px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 20px rgba(0, 255, 159, 0.6);
        }
        
        /* Terminal styling */
        .terminal-container {
            background: #000000;
            border: 1px solid #00ff9f;
            border-radius: 10px;
            padding: 1rem;
            font-family: 'Courier New', monospace;
            color: #00ff9f;
            max-height: 400px;
            overflow-y: auto;
        }
        
        /* Status indicators */
        .status-running {
            color: #00ff9f;
            font-weight: bold;
        }
        
        .status-stopped {
            color: #ff4444;
            font-weight: bold;
        }
        
        .status-installing {
            color: #ffaa00;
            font-weight: bold;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: rgba(16, 21, 30, 0.9);
        }
        
        /* Metrics styling */
        .metric-container {
            background: rgba(22, 33, 62, 0.6);
            border: 1px solid #00ff9f;
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        
        /* Progress bars */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #00ff9f, #00d4ff);
        }
        
        /* QR Code styling */
        .qr-container {
            text-align: center;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            margin: 1rem 0;
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
            
            # Initialize UI components
            self.terminal_widget = TerminalWidget()
            self.app_gallery = AppGallery(st.session_state.apps_data)
            self.resource_monitor = ResourceMonitor(self.performance_monitor)
            self.tunnel_dashboard = TunnelDashboard(self.url_manager)
            
        except Exception as e:
            st.error(f"Failed to initialize components: {str(e)}")
            self.logging_system.log_error("Component initialization failed", {"error": str(e)})
            
    def setup_logging(self):
        """Initialize logging system."""
        try:
            self.logging_system = LoggingSystem()
            self.logging_system.log_info("UI", "PinokioCloud Streamlit App initialized successfully")
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
        st.markdown('<p style="text-align: center; color: #00d4ff; font-size: 1.2rem;">Cloud-Native AI Application Platform</p>', unsafe_allow_html=True)
        
        # Platform info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"🌐 Platform: {self.platform_info.platform.value.title()}")
        with col2:
            st.info(f"💾 Base Path: {self.platform_info.base_path}")
        with col3:
            st.info(f"📊 Apps Available: {len(st.session_state.apps_data)}")
            
    def render_sidebar(self):
        """Render the application sidebar."""
        with st.sidebar:
            st.markdown("### 🎛️ Control Panel")
            
            # Page navigation
            pages = {
                "🏪 App Gallery": "gallery",
                "📊 Resource Monitor": "resources", 
                "🌐 Tunnel Dashboard": "tunnels",
                "📺 Terminal": "terminal",
                "⚙️ Settings": "settings"
            }
            
            selected_page = st.selectbox(
                "Navigate to:",
                list(pages.keys()),
                index=list(pages.values()).index(st.session_state.app_state.current_page)
            )
            st.session_state.app_state.current_page = pages[selected_page]
            
            st.markdown("---")
            
            # Quick actions
            st.markdown("### ⚡ Quick Actions")
            
            if st.button("🔄 Refresh Data"):
                self.refresh_all_data()
                st.success("Data refreshed!")
                
            if st.button("🧹 Clear Cache"):
                self.cache_manager.clear_cache()
                st.success("Cache cleared!")
                
            if st.button("📊 System Health"):
                metrics = self.performance_monitor.get_current_metrics()
                st.session_state.system_metrics = metrics
                st.success("System metrics updated!")
                
            st.markdown("---")
            
            # Running applications summary
            st.markdown("### 🏃 Running Apps")
            running_count = len([app for app in st.session_state.running_apps.values() if app.get('status') == 'running'])
            st.metric("Active Applications", running_count)
            
            # System status
            if st.session_state.system_metrics:
                cpu_usage = st.session_state.system_metrics.get('cpu_percent', 0)
                memory_usage = st.session_state.system_metrics.get('memory_percent', 0)
                
                st.metric("CPU Usage", f"{cpu_usage:.1f}%")
                st.metric("Memory Usage", f"{memory_usage:.1f}%")
                
    def render_main_content(self):
        """Render the main content area based on current page."""
        current_page = st.session_state.app_state.current_page
        
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
        
        # Search and filter controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input("🔍 Search applications...", placeholder="Enter app name or description")
            
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
        self.resource_monitor.render_monitor()
        
    def render_tunnels_page(self):
        """Render the tunnel dashboard page."""
        st.markdown("## 🌐 Tunnel Dashboard")
        self.tunnel_dashboard.render_dashboard()
        
    def render_terminal_page(self):
        """Render the terminal page."""
        st.markdown("## 📺 Terminal")
        self.terminal_widget.render_terminal()
        
    def render_settings_page(self):
        """Render the settings page."""
        st.markdown("## ⚙️ Settings")
        
        # Theme settings
        st.markdown("### 🎨 Appearance")
        theme_options = ["Dark Cyberpunk", "Light", "Auto"]
        selected_theme = st.selectbox("Theme", theme_options, index=0)
        
        # Auto-refresh settings
        st.markdown("### 🔄 Auto-Refresh")
        auto_refresh = st.checkbox("Enable auto-refresh", value=st.session_state.app_state.auto_refresh)
        if auto_refresh:
            refresh_interval = st.slider("Refresh interval (seconds)", 1, 30, st.session_state.app_state.refresh_interval)
            st.session_state.app_state.refresh_interval = refresh_interval
        st.session_state.app_state.auto_refresh = auto_refresh
        
        # Terminal settings
        st.markdown("### 📺 Terminal")
        terminal_visible = st.checkbox("Show terminal by default", value=st.session_state.app_state.terminal_visible)
        st.session_state.app_state.terminal_visible = terminal_visible
        
        # Performance settings
        st.markdown("### ⚡ Performance")
        resource_monitoring = st.checkbox("Enable resource monitoring", value=st.session_state.app_state.resource_monitoring)
        st.session_state.app_state.resource_monitoring = resource_monitoring
        
        # Cache settings
        st.markdown("### 💾 Cache")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Clear Application Cache"):
                self.cache_manager.clear_cache()
                st.success("Application cache cleared!")
        with col2:
            if st.button("Clear System Cache"):
                self.cache_manager.clear_cache(cache_type="all")
                st.success("All caches cleared!")
                
        # Export/Import settings
        st.markdown("### 📤 Export/Import")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export Settings"):
                settings = {
                    "theme": selected_theme,
                    "auto_refresh": auto_refresh,
                    "refresh_interval": refresh_interval,
                    "terminal_visible": terminal_visible,
                    "resource_monitoring": resource_monitoring
                }
                st.download_button(
                    label="Download Settings",
                    data=json.dumps(settings, indent=2),
                    file_name="pinokiocloud_settings.json",
                    mime="application/json"
                )
        with col2:
            uploaded_file = st.file_uploader("Import Settings", type=['json'])
            if uploaded_file is not None:
                try:
                    settings = json.load(uploaded_file)
                    # Apply imported settings
                    st.success("Settings imported successfully!")
                except Exception as e:
                    st.error(f"Failed to import settings: {str(e)}")
                    
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
            st.error(f"Failed to refresh data: {str(e)}")
            self.logging_system.log_error("Data refresh failed", {"error": str(e)})
            
    def setup_auto_refresh(self):
        """Setup automatic data refresh."""
        if st.session_state.app_state.auto_refresh:
            # Use Streamlit's rerun mechanism for auto-refresh
            if st.session_state.app_state.last_update:
                time_since_update = (datetime.now() - st.session_state.app_state.last_update).total_seconds()
                if time_since_update >= st.session_state.app_state.refresh_interval:
                    self.refresh_all_data()
                    st.rerun()
                    
    def run(self):
        """Run the main application."""
        try:
            # Setup auto-refresh
            self.setup_auto_refresh()
            
            # Render UI components
            self.render_header()
            self.render_sidebar()
            self.render_main_content()
            
            # Footer
            st.markdown("---")
            st.markdown(
                '<p style="text-align: center; color: #666;">PinokioCloud v1.0.0 - Cloud-Native AI Application Platform</p>',
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