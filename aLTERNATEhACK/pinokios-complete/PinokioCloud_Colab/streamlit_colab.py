"""
PinokioCloud Streamlit Interface - Google Colab Optimized
Cloud-native Streamlit UI for Pinokio apps in Google Colab environment
"""

import streamlit as st
import json
import asyncio
import subprocess
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# Colab-specific path handling
if 'google.colab' in sys.modules:
    # Running in Google Colab
    sys.path.append('/content')
    BASE_PATH = '/content/pinokio_apps'
else:
    # Local development
    sys.path.append(str(Path(__file__).parent))
    BASE_PATH = './pinokio_apps'

# Import the unified engine
from unified_engine import UnifiedPinokioEngine

# Page configuration with dark theme as default
st.set_page_config(
    page_title="PinokioCloud - AI App Manager (Colab)",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set dark theme as default
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# Beautiful Dark Mode CSS optimized for Colab
st.markdown("""
<style>
    /* Override Streamlit's default theme */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #e0e6ed;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 2px solid #0f3460;
    }
    
    /* Main header with cyberpunk gradient */
    .main-header {
        text-align: center;
        padding: 3rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        text-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for Colab environment
def init_session_state():
    """Initialize session state variables for Colab"""
    if "engine" not in st.session_state:
        # Initialize with Colab-specific paths
        # Use absolute path to ensure we're using the right JSON file
        colab_apps_path = "/content/SD-LongNose/PinokioCloud_Colab/cleaned_pinokio_apps.json" if 'google.colab' in sys.modules else str(Path(__file__).parent / "cleaned_pinokio_apps.json")
        st.session_state.engine = UnifiedPinokioEngine(
            base_path=BASE_PATH,
            apps_data_path=colab_apps_path
        )
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    if "logs" not in st.session_state:
        st.session_state.logs = []
    
    if "toasts" not in st.session_state:
        st.session_state.toasts = []
    
    if "selected_app" not in st.session_state:
        st.session_state.selected_app = None

# Toast notification system
def add_toast(message: str, toast_type: str = "info"):
    """Add toast notification"""
    timestamp = time.time()
    st.session_state.toasts.append({
        "message": message,
        "type": toast_type,
        "timestamp": timestamp
    })
    
    # Keep only last 5 toasts
    if len(st.session_state.toasts) > 5:
        st.session_state.toasts = st.session_state.toasts[-5:]

def display_toasts():
    """Display active toast notifications"""
    current_time = time.time()
    active_toasts = []
    
    for toast in st.session_state.toasts:
        # Remove toasts older than 5 seconds
        if current_time - toast["timestamp"] < 5:
            active_toasts.append(toast)
    
    st.session_state.toasts = active_toasts
    
    # Display toasts
    for toast in active_toasts:
        if toast["type"] == "success":
            st.success(toast["message"])
        elif toast["type"] == "error": 
            st.error(toast["message"])
        elif toast["type"] == "warning":
            st.warning(toast["message"])
        else:
            st.info(toast["message"])

# Main app lifecycle functions
async def install_app_async(app_name: str):
    """Install app asynchronously with Colab optimization"""
    try:
        add_toast(f"🚀 Starting installation of {app_name}...", "info")
        
        # Install with progress callback
        def progress_callback(message):
            st.session_state.logs.append({
                "timestamp": time.strftime("%H:%M:%S"),
                "app": app_name,
                "level": "INFO",
                "message": message
            })
        
        success = await st.session_state.engine.install_app(app_name, progress_callback)
        
        if success:
            add_toast(f"✅ {app_name} installed successfully!", "success")
            st.session_state.engine.save_state()
            return True
        else:
            add_toast(f"❌ Failed to install {app_name}", "error")
            return False
            
    except Exception as e:
        add_toast(f"❌ Installation error: {str(e)}", "error")
        return False

def install_app(app_name: str):
    """Wrapper for install_app_async"""
    return asyncio.run(install_app_async(app_name))

async def run_app_async(app_name: str):
    """Run app asynchronously"""
    try:
        add_toast(f"▶️ Starting {app_name}...", "info")
        
        def progress_callback(message):
            st.session_state.logs.append({
                "timestamp": time.strftime("%H:%M:%S"),
                "app": app_name,
                "level": "INFO", 
                "message": message
            })
        
        success = await st.session_state.engine.run_app(app_name, progress_callback)
        
        if success:
            add_toast(f"🎯 {app_name} is now running!", "success")
            return True
        else:
            add_toast(f"❌ Failed to start {app_name}", "error")
            return False
            
    except Exception as e:
        add_toast(f"❌ Runtime error: {str(e)}", "error")
        return False

def run_app(app_name: str):
    """Wrapper for run_app_async"""
    return asyncio.run(run_app_async(app_name))

def stop_app(app_name: str):
    """Stop running app"""
    try:
        add_toast(f"⏹️ Stopping {app_name}...", "info")
        success = st.session_state.engine.stop_app(app_name)
        
        if success:
            add_toast(f"🛑 {app_name} stopped successfully!", "success")
        else:
            add_toast(f"❌ Failed to stop {app_name}", "error")
        return success
    except Exception as e:
        add_toast(f"❌ Stop error: {str(e)}", "error")
        return False

def uninstall_app(app_name: str):
    """Uninstall app completely"""
    try:
        add_toast(f"🗑️ Uninstalling {app_name}...", "info")
        success = st.session_state.engine.uninstall_app(app_name)
        
        if success:
            add_toast(f"✅ {app_name} uninstalled successfully!", "success")
            st.session_state.engine.save_state()
        else:
            add_toast(f"❌ Failed to uninstall {app_name}", "error")
        return success
    except Exception as e:
        add_toast(f"❌ Uninstall error: {str(e)}", "error")
        return False

# Page Functions
def dashboard_page():
    """Dashboard page with stats and quick actions"""
    st.markdown('<div class="main-header"><h1>🚀 PinokioCloud</h1><p>AI App Manager for Google Colab</p></div>', unsafe_allow_html=True)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    installed_apps = st.session_state.engine.get_installed_apps()
    running_apps = st.session_state.engine.get_running_apps()
    available_apps = len(st.session_state.engine.apps_data)
    
    with col1:
        st.metric("Available Apps", available_apps)
    with col2:
        st.metric("Installed Apps", len(installed_apps))
    with col3:
        st.metric("Running Apps", len(running_apps))
    with col4:
        if 'google.colab' in sys.modules:
            st.metric("Environment", "Google Colab")
        else:
            st.metric("Environment", "Local")
    
    # GPU info for Colab
    if 'google.colab' in sys.modules:
        st.subheader("🎮 GPU Information")
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,memory.used', '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                gpu_info = result.stdout.strip()
                st.success(f"GPU Detected: {gpu_info}")
            else:
                st.warning("No GPU detected or nvidia-smi not available")
        except Exception as e:
            st.error(f"Error checking GPU: {str(e)}")
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📱 Browse Apps", use_container_width=True):
            st.session_state.current_page = "Browse Apps"
            st.rerun()
    
    with col2:
        if st.button("💾 Installed Apps", use_container_width=True):
            st.session_state.current_page = "Installed Apps"
            st.rerun()

def browse_apps_page():
    """Browse available apps page"""
    st.header("📱 Browse AI Apps")
    
    # Search and filter
    search_term = st.text_input("🔍 Search apps...", placeholder="Search by name, description, or category")
    
    # Category filter
    categories = set()
    for app in st.session_state.engine.apps_data:
        if 'category' in app:
            categories.add(app['category'])
    
    selected_category = st.selectbox("📂 Filter by category", ["All"] + sorted(list(categories)))
    
    # Filter apps
    filtered_apps = []
    for app in st.session_state.engine.apps_data:
        # Search filter
        if search_term:
            if not (search_term.lower() in app.get('title', '').lower() or 
                   search_term.lower() in app.get('description', '').lower()):
                continue
        
        # Category filter
        if selected_category != "All" and app.get('category') != selected_category:
            continue
            
        filtered_apps.append(app)
    
    st.write(f"Found {len(filtered_apps)} apps")
    
    # Display apps in grid
    cols = st.columns(3)
    for i, app in enumerate(filtered_apps[:30]):  # Limit to first 30 for performance
        with cols[i % 3]:
            with st.container():
                st.subheader(app.get('title', 'Unknown App'))
                st.write(app.get('description', 'No description available')[:100] + "...")
                
                # Check if installed
                is_installed = app.get('title') in st.session_state.engine.get_installed_apps()
                
                if is_installed:
                    st.success("✅ Installed")
                    if st.button(f"View Details", key=f"view_{i}"):
                        st.session_state.selected_app = app.get('title')
                        st.session_state.current_page = "Installed Apps"
                        st.rerun()
                else:
                    if st.button(f"Install {app.get('title')}", key=f"install_{i}"):
                        with st.spinner(f"Installing {app.get('title')}..."):
                            success = install_app(app.get('title'))
                        if success:
                            st.rerun()

def installed_apps_page():
    """Installed apps management page"""
    st.header("💾 Installed Apps")
    
    installed_apps = st.session_state.engine.get_installed_apps()
    running_apps = st.session_state.engine.get_running_apps()
    
    if not installed_apps:
        st.info("No apps installed yet. Go to Browse Apps to install some!")
        return
    
    for app_name in installed_apps:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.subheader(app_name)
                
                # App status
                if app_name in running_apps:
                    st.success("🟢 Running")
                    # Show URLs if available
                    app_urls = st.session_state.engine.get_app_urls(app_name)
                    if app_urls:
                        for url in app_urls:
                            st.write(f"🌐 [Access App]({url})")
                else:
                    st.info("⚪ Stopped")
            
            with col2:
                if app_name in running_apps:
                    if st.button("⏹️ Stop", key=f"stop_{app_name}"):
                        success = stop_app(app_name)
                        if success:
                            st.rerun()
                else:
                    if st.button("▶️ Run", key=f"run_{app_name}"):
                        with st.spinner(f"Starting {app_name}..."):
                            success = run_app(app_name)
                        if success:
                            st.rerun()
            
            with col3:
                if st.button("📋 Logs", key=f"logs_{app_name}"):
                    st.session_state.selected_app = app_name
                    st.session_state.current_page = "Installation Log"
                    st.rerun()
            
            with col4:
                if st.button("🗑️ Uninstall", key=f"uninstall_{app_name}"):
                    success = uninstall_app(app_name)
                    if success:
                        st.rerun()
            
            st.divider()

def logs_page():
    """Installation and runtime logs page"""
    st.header("📋 System Logs")
    
    if st.session_state.selected_app:
        st.subheader(f"Logs for {st.session_state.selected_app}")
    
    # Display logs
    if st.session_state.logs:
        # Reverse to show newest first
        for log in reversed(st.session_state.logs[-100:]):  # Show last 100 logs
            timestamp = log.get("timestamp", "")
            app = log.get("app", "System")
            level = log.get("level", "INFO")
            message = log.get("message", "")
            
            # Color code by level
            if level == "ERROR":
                st.error(f"[{timestamp}] {app}: {message}")
            elif level == "WARNING":
                st.warning(f"[{timestamp}] {app}: {message}")
            elif level == "SUCCESS":
                st.success(f"[{timestamp}] {app}: {message}")
            else:
                st.info(f"[{timestamp}] {app}: {message}")
    else:
        st.info("No logs available yet.")
    
    # Clear logs button
    if st.button("🗑️ Clear Logs"):
        st.session_state.logs = []
        st.rerun()

def settings_page():
    """Settings and configuration page"""
    st.header("⚙️ Settings")
    
    # Environment info
    st.subheader("🌍 Environment Information")
    st.info(f"Base Path: {BASE_PATH}")
    st.info(f"Python Path: {sys.path[0]}")
    
    if 'google.colab' in sys.modules:
        st.success("Running in Google Colab")
    else:
        st.info("Running locally")
    
    # Engine status
    st.subheader("🔧 Engine Status")
    try:
        apps_count = len(st.session_state.engine.apps_data)
        st.success(f"✅ Engine loaded with {apps_count} apps")
    except Exception as e:
        st.error(f"❌ Engine error: {str(e)}")
    
    # Reset options
    st.subheader("🔄 Reset Options")
    if st.button("🗑️ Clear All Logs"):
        st.session_state.logs = []
        add_toast("Logs cleared", "success")
        st.rerun()
    
    if st.button("🔄 Restart Engine"):
        try:
            # Use same absolute path logic as initialization
            colab_apps_path = "/content/SD-LongNose/PinokioCloud_Colab/cleaned_pinokio_apps.json" if 'google.colab' in sys.modules else str(Path(__file__).parent / "cleaned_pinokio_apps.json")
            st.session_state.engine = UnifiedPinokioEngine(
                base_path=BASE_PATH,
                apps_data_path=colab_apps_path
            )
            add_toast("Engine restarted", "success")
            st.rerun()
        except Exception as e:
            add_toast(f"Failed to restart engine: {str(e)}", "error")

# Main Application
def main():
    """Main Streamlit application"""
    # Initialize session state
    init_session_state()
    
    # Display toasts
    display_toasts()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🚀 Navigation")
        
        pages = ["Dashboard", "Browse Apps", "Installed Apps", "Installation Log", "Settings"]
        
        for page in pages:
            if st.button(page, use_container_width=True, 
                        type="primary" if st.session_state.current_page == page else "secondary"):
                st.session_state.current_page = page
                st.rerun()
        
        st.divider()
        
        # Live logs in sidebar
        st.markdown("### 📋 Live Logs")
        
        if st.session_state.logs:
            # Show last 5 logs in sidebar
            recent_logs = st.session_state.logs[-5:]
            for log in reversed(recent_logs):
                level = log.get("level", "INFO")
                message = log.get("message", "")[:50] + "..."
                app = log.get("app", "System")
                
                if level == "ERROR":
                    st.error(f"{app}: {message}")
                elif level == "WARNING":
                    st.warning(f"{app}: {message}")
                else:
                    st.info(f"{app}: {message}")
        else:
            st.info("No recent activity")
        
        # Manual refresh button instead of auto-refresh
        if st.button("🔄 Refresh Logs", key="refresh_logs"):
            st.rerun()
    
    # Main content area
    if st.session_state.current_page == "Dashboard":
        dashboard_page()
    elif st.session_state.current_page == "Browse Apps":
        browse_apps_page()
    elif st.session_state.current_page == "Installed Apps":
        installed_apps_page()
    elif st.session_state.current_page == "Installation Log":
        logs_page()
    elif st.session_state.current_page == "Settings":
        settings_page()

if __name__ == "__main__":
    main()
