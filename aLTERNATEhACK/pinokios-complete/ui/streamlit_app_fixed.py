"""
PinokioCloud Streamlit Interface
Clean, working Streamlit UI for Pinokio apps in cloud environments
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

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import the unified engine
from pinokios.unified_engine import UnifiedPinokioEngine

# Page configuration with dark theme as default
st.set_page_config(
    page_title="PinokioCloud - AI App Manager",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set dark theme as default
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# Beautiful Dark Mode CSS with Live Log and Toast Support
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
    
    /* Glassmorphism app cards */
    .app-card {
        background: rgba(42, 42, 66, 0.8);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.5rem;
        border-left: 4px solid #667eea;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        color: #e0e6ed;
    }
    
    .app-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
        border-left: 4px solid #f093fb;
    }
    
    .app-card h4 {
        color: #ffffff;
        margin-bottom: 0.8rem;
        font-weight: 600;
        font-size: 1.3rem;
    }
    
    .app-card p {
        color: #b8c5d6;
        margin-bottom: 0.8rem;
        line-height: 1.6;
    }
    
    .app-card small {
        color: #8892a6;
        font-size: 0.9rem;
    }
    
    /* Enhanced status badges */
    .status-badge {
        padding: 0.4rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-installed {
        background: linear-gradient(135deg, #4ade80, #22c55e);
        color: #ffffff;
        box-shadow: 0 4px 15px rgba(74, 222, 128, 0.3);
    }
    
    .status-running {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: #ffffff;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        animation: pulse 2s infinite;
    }
    
    .status-stopped {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: #ffffff;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Live log container */
    .live-log-container {
        background: rgba(26, 26, 46, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        max-height: 400px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        backdrop-filter: blur(10px);
    }
    
    .log-entry {
        padding: 0.3rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 0.85rem;
        line-height: 1.4;
    }
    
    .log-info { color: #60a5fa; }
    .log-success { color: #34d399; }
    .log-warning { color: #fbbf24; }
    .log-error { color: #f87171; }
    
    /* Toast notification styles */
    .toast {
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 8px 32px rgba(239, 68, 68, 0.3);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        max-width: 400px;
    }
    
    .toast-success {
        background: linear-gradient(135deg, #22c55e, #16a34a);
        box-shadow: 0 8px 32px rgba(34, 197, 94, 0.3);
    }
    
    .toast-warning {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        box-shadow: 0 8px 32px rgba(245, 158, 11, 0.3);
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #5a6fd8, #6a42a0);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Sidebar elements */
    .css-1d391kg .stRadio > label {
        color: #e0e6ed;
        font-weight: 500;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(26, 26, 46, 0.3);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a6fd8, #6a42a0);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'engine' not in st.session_state:
    base_path = os.environ.get('PINOKIO_BASE_PATH', './pinokio_apps')
    st.session_state.engine = UnifiedPinokioEngine(base_path=base_path)

# Force engine recreation to pick up code changes
if st.button("🔄 Reset Engine", help="Reset engine to pick up code changes"):
    base_path = os.environ.get('PINOKIO_BASE_PATH', './pinokio_apps')
    st.session_state.engine = UnifiedPinokioEngine(base_path=base_path)
    st.success("Engine reset with updated code!")

if 'app_database' not in st.session_state:
    # Load app database from AppData.json
    db_path = Path('cleaned_pinokio_apps.json')
    if db_path.exists():
        with open(db_path, 'r') as f:
            data = json.load(f)
            # Convert to expected format
            apps = []
            for key, app_data in data.items():
                apps.append({
                    'Appname': app_data.get('name', key),
                    'entryURL': app_data.get('repo_url', ''),
                    'Category': app_data.get('category', 'Unknown').title(),
                    'tag': ', '.join(app_data.get('tags', [])),
                    'description': app_data.get('description', 'No description'),
                    'InstallerType': app_data.get('installer_type', 'unknown')
                })
            st.session_state.app_database = apps
    else:
        st.session_state.app_database = []

if 'installed_apps' not in st.session_state:
    st.session_state.installed_apps = {}

def sync_installed_apps_with_engine():
    """Sync UI session state with engine's installed_apps state"""
    if 'engine' in st.session_state:
        # Get the engine's view of installed apps
        engine_installed = st.session_state.engine.installed_apps
        
        # Sync session state to match engine state exactly
        st.session_state.installed_apps = {}
        
        for app_name, app_info in engine_installed.items():
            st.session_state.installed_apps[app_name] = {
                'status': st.session_state.engine.get_app_status(app_name),
                'description': f'Installed app: {app_name}',
                'path': app_info.get('path', ''),
                'repo_url': app_info.get('repo_url', '')
            }

# Sync installed apps with engine state on startup
if 'engine' in st.session_state:
    sync_installed_apps_with_engine()

if 'installation_logs' not in st.session_state:
    st.session_state.installation_logs = []

if 'live_logs' not in st.session_state:
    st.session_state.live_logs = []

if 'toast_messages' not in st.session_state:
    st.session_state.toast_messages = []

if 'current_installation' not in st.session_state:
    st.session_state.current_installation = None

def add_toast(message: str, toast_type: str = "error"):
    """Add a toast notification"""
    toast = {
        "message": message,
        "type": toast_type,
        "timestamp": time.time()
    }
    st.session_state.toast_messages.append(toast)
    
    # Keep only last 5 toasts
    if len(st.session_state.toast_messages) > 5:
        st.session_state.toast_messages = st.session_state.toast_messages[-5:]

def add_live_log(message: str, log_type: str = "info", app_name: str = None):
    """Add entry to live log"""
    timestamp = time.strftime("%H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "message": message,
        "type": log_type,
        "app_name": app_name
    }
    st.session_state.live_logs.append(log_entry)
    
    # Keep only last 100 log entries
    if len(st.session_state.live_logs) > 100:
        st.session_state.live_logs = st.session_state.live_logs[-100:]

def display_toasts():
    """Display active toast notifications"""
    current_time = time.time()
    active_toasts = []
    
    for toast in st.session_state.toast_messages:
        # Show toasts for 5 seconds
        if current_time - toast["timestamp"] < 5:
            active_toasts.append(toast)
    
    st.session_state.toast_messages = active_toasts
    
    for i, toast in enumerate(active_toasts):
        toast_class = f"toast toast-{toast['type']}"
        st.markdown(f"""
        <div class="{toast_class}" style="top: {20 + i * 80}px;">
            <strong>{toast['type'].upper()}:</strong> {toast['message']}
        </div>
        """, unsafe_allow_html=True)

def display_live_log():
    """Display live log in sidebar"""
    st.markdown("### 📜 Live Log")
    
    if st.session_state.live_logs:
        log_html = '<div class="live-log-container">'
        
        # Show last 20 log entries
        recent_logs = st.session_state.live_logs[-20:]
        
        for log in reversed(recent_logs):  # Show newest first
            app_prefix = f"[{log['app_name']}] " if log['app_name'] else ""
            log_html += f"""
            <div class="log-entry log-{log['type']}">
                <span style="opacity: 0.7;">{log['timestamp']}</span> 
                {app_prefix}{log['message']}
            </div>
            """
        
        log_html += '</div>'
        st.markdown(log_html, unsafe_allow_html=True)
        
        # Auto-refresh every 2 seconds
        time.sleep(2)
        st.rerun()
    else:
        st.info("💬 No logs yet")

def main():
    """Main Streamlit application"""
    
    # Display toasts
    display_toasts()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 PinokioCloud</h1>
        <p>AI App Manager for Cloud GPUs</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add startup log
    if len(st.session_state.live_logs) == 0:
        add_live_log("🚀 PinokioCloud started", "success")
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🧿 Navigation")
        page = st.radio(
            "Select Page",
            ["🏠 Dashboard", "🔍 Browse Apps", "📦 Installed", "📋 Installation Log", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Live log display
        display_live_log()
        
        # Quick stats
        st.markdown("### 📊 Quick Stats")
        total_apps = len(st.session_state.app_database)
        installed = len(st.session_state.installed_apps)
        
        st.metric("Total Apps", total_apps)
        st.metric("Installed", installed)
        st.metric("Running", sum(1 for app in st.session_state.installed_apps.values() if app.get('status') == 'running'))
        
        # GPU info
        gpu = detect_gpu()
        if gpu['available']:
            st.success(f"🎮 GPU: {gpu['model']}")
        else:
            st.info("💻 CPU Mode")
        
    # Main content area
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🔍 Browse Apps":
        show_browse_apps()
    elif page == "📦 Installed":
        show_installed_apps()
    elif page == "📋 Installation Log":
        show_installation_log()
    elif page == "⚙️ Settings":
        show_settings()

def run_app(app_name):
    """Run an installed app"""
    
    with st.spinner(f"Starting {app_name}..."):
        
        # Log running start
        log_running_step(app_name, f"=== STARTING {app_name.upper()} ===", "info")
        add_live_log(f"Starting {app_name}", "info", app_name)
        log_running_step(app_name, f"Checking app directory and files...", "info")
        
        app_path = st.session_state.engine.base_path / app_name
        
        if app_path.exists():
            log_running_step(app_name, f"\u2705 App directory exists: {app_path}", "info")
            add_live_log(f"App directory found", "info", app_name)
            
            # Check for start files
            start_js = app_path / 'start.js'
            start_json = app_path / 'start.json'
            
            log_running_step(app_name, f"Looking for start scripts...", "info")
            
            if start_js.exists():
                try:
                    content = start_js.read_text(encoding='utf-8')
                    log_running_step(app_name, f"start.js content preview: {content[:200]}...", "info")
                    add_live_log(f"Found start.js script", "info", app_name)
                except Exception as e:
                    log_running_step(app_name, f"Error reading start.js: {e}", "error")
                    add_live_log(f"Error reading start.js: {e}", "error", app_name)
                    
            if start_json.exists():
                try:
                    content = start_json.read_text(encoding='utf-8')
                    log_running_step(app_name, f"start.json content preview: {content[:200]}...", "info")
                    add_live_log(f"Found start.json script", "info", app_name)
                except Exception as e:
                    log_running_step(app_name, f"Error reading start.json: {e}", "error")
                    add_live_log(f"Error reading start.json: {e}", "error", app_name)
        else:
            log_running_step(app_name, "\u274c App directory does not exist", "error")
            add_live_log(f"\u274c App directory not found", "error", app_name)
            add_toast(f"App directory not found for {app_name}", "error")
        
        # Show basic debug info in UI
        st.info(f"🔍 Debug: Looking for app in {app_path}")
        st.info(f"🔍 Debug: Directory exists: {app_path.exists()}")
        
        if app_path.exists():
            start_js = app_path / 'start.js'
            start_json = app_path / 'start.json'
            st.info(f"🔍 Debug: start.js exists: {start_js.exists()}")
            st.info(f"🔍 Debug: start.json exists: {start_json.exists()}")
        
        log_running_step(app_name, "Calling engine.run_app() method...", "info")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def do_run():
            return await st.session_state.engine.run_app(app_name)
        
        try:
            success, message = loop.run_until_complete(do_run())
            
            log_running_step(app_name, f"Engine run_app returned: success={success}, message='{message}'", "info")
            
            if success:
                log_running_step(app_name, "✅ App started successfully!", "success")
                st.session_state.installed_apps[app_name]['status'] = 'running'
                st.success(f"✅ {app_name} started!")
                st.rerun()
            else:
                log_running_step(app_name, f"❌ App failed to start: {message}", "error")
                st.error(f"Failed to start: {message}")
        except Exception as e:
            log_running_step(app_name, f"❌ Exception during app run: {str(e)}", "error")
            import traceback
            traceback_str = traceback.format_exc()
            log_running_step(app_name, f"Full traceback: {traceback_str}", "error")
            st.error(f"Error: {str(e)}")
            st.error(f"Full traceback: {traceback_str}")
        finally:
            log_running_step(app_name, "=== APP RUN PROCESS COMPLETED ===", "info")
            loop.close()

def install_app(app_name, repo_url):
    """Install an app using the engine"""
    with st.spinner(f"Installing {app_name}..."):
        
        # Log installation start
        log_installation_step(app_name, f"Starting installation of {app_name}", "info")
        add_live_log(f"Starting installation of {app_name}", "info", app_name)
        log_installation_step(app_name, f"Repository: {repo_url}", "info")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def do_install():
            return await st.session_state.engine.install_app(app_name, repo_url)
        
        try:
            success, message = loop.run_until_complete(do_install())
            
            if success:
                log_installation_step(app_name, f"\u2705 {app_name} installed successfully!", "success")
                add_live_log(f"\u2705 {app_name} installed successfully!", "success", app_name)
                st.session_state.installed_apps[app_name] = {
                    'status': 'installed',
                    'description': f'Installed app: {app_name}',
                    'repo_url': repo_url,
                    'path': str(st.session_state.engine.base_path / app_name)
                }
                st.success(f"\u2705 {app_name} installed!")
                add_toast(f"{app_name} installed successfully!", "success")
                st.rerun()
            else:
                log_installation_step(app_name, f"\u274c Installation failed: {message}", "error")
                add_live_log(f"\u274c Installation failed: {message}", "error", app_name)
                add_toast(f"Installation failed: {message}", "error")
                st.error(f"Installation failed: {message}")
        except Exception as e:
            log_installation_step(app_name, f"\u274c Exception during installation: {str(e)}", "error")
            add_live_log(f"\u274c Installation error: {str(e)}", "error", app_name)
            add_toast(f"Installation error: {str(e)}", "error")
            import traceback
            traceback_str = traceback.format_exc()
            log_installation_step(app_name, f"Full traceback: {traceback_str}", "error")
            st.error(f"Error: {str(e)}")
            st.error(f"Full traceback: {traceback_str}")
        finally:
            loop.close()

def stop_app(app_name):
    """Stop a running app"""
    with st.spinner(f"Stopping {app_name}..."):
        add_live_log(f"Stopping {app_name}", "warning", app_name)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def do_stop():
            return await st.session_state.engine.stop_app(app_name)
        
        try:
            success, message = loop.run_until_complete(do_stop())
            
            if success:
                st.session_state.installed_apps[app_name]['status'] = 'stopped'
                add_live_log(f"✅ {app_name} stopped", "success", app_name)
                add_toast(f"{app_name} stopped successfully!", "success")
                st.success(f"✅ {app_name} stopped")
                st.rerun()
            else:
                add_live_log(f"❌ Stop failed: {message}", "error", app_name)
                add_toast(f"Failed to stop {app_name}: {message}", "error")
                st.error(f"Failed to stop: {message}")
        except Exception as e:
            add_live_log(f"❌ Stop error: {str(e)}", "error", app_name)
            add_toast(f"Stop error: {str(e)}", "error")
            st.error(f"Error: {str(e)}")
        finally:
            loop.close()

def uninstall_app(app_name):
    """Uninstall an app - directly execute without confirmation prompt"""
    with st.spinner(f"Uninstalling {app_name}..."):
        add_live_log(f"Uninstalling {app_name}", "warning", app_name)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def do_uninstall():
            return await st.session_state.engine.uninstall_app(app_name)
        
        try:
            success, message = loop.run_until_complete(do_uninstall())
            
            if success:
                # Sync session state with engine state after uninstall
                sync_installed_apps_with_engine()
                add_live_log(f"\u2705 {app_name} uninstalled successfully", "success", app_name)
                add_toast(f"{app_name} uninstalled successfully!", "success")
                
                st.success(f"\u2705 {app_name} uninstalled successfully! {message}")
                time.sleep(1)  # Brief delay to show success message
                st.rerun()
            else:
                add_live_log(f"\u274c Uninstall failed: {message}", "error", app_name)
                add_toast(f"Failed to uninstall {app_name}: {message}", "error")
                st.error(f"\u274c Failed to uninstall {app_name}: {message}")
        except Exception as e:
            import traceback
            error_msg = f"Error during uninstall: {str(e)}"
            add_live_log(f"\u274c Uninstall error: {str(e)}", "error", app_name)
            add_toast(f"Uninstall error: {str(e)}", "error")
            st.error(error_msg)
            st.error(f"Traceback: {traceback.format_exc()}")
        finally:
            loop.close()

def detect_gpu():
    """Detect GPU availability"""
    gpu_info = {
        'available': False,
        'model': 'None',
        'memory': 0
    }
    
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            gpu_info['available'] = True
            # Extract GPU model
            import re
            match = re.search(r'(Tesla \w+|A100|V100|T4|P100|K80)', result.stdout)
            if match:
                gpu_info['model'] = match.group(1)
    except:
        pass
    
    return gpu_info

# Page functions
def show_dashboard():
    """Show dashboard page"""
    st.markdown("## 🏠 Dashboard")
    
    # Quick overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Apps", len(st.session_state.app_database))
    with col2:
        st.metric("Installed", len(st.session_state.installed_apps))
    with col3:
        running = sum(1 for app in st.session_state.installed_apps.values() if app.get('status') == 'running')
        st.metric("Running", running)
    with col4:
        gpu = detect_gpu()
        gpu_text = gpu['model'] if gpu['available'] else 'None'
        st.metric("GPU", gpu_text)
    
    # Recent activity
    if st.session_state.live_logs:
        st.markdown("### 📈 Recent Activity")
        recent_logs = st.session_state.live_logs[-10:]
        for log in reversed(recent_logs):
            status_icon = {
                'success': '✅',
                'error': '❌', 
                'warning': '⚠️',
                'info': 'ℹ️'
            }.get(log['type'], 'ℹ️')
            
            app_text = f"[{log['app_name']}] " if log['app_name'] else ""
            st.write(f"{status_icon} {log['timestamp']} - {app_text}{log['message']}")

def show_browse_apps():
    """Show browse apps page"""
    st.markdown("## 🔍 Browse Apps")
    
    # Search and filter
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search apps", placeholder="Search by name, category, or tags...")
    
    with col2:
        categories = list(set(app.get('Category', 'Unknown') for app in st.session_state.app_database))
        category_filter = st.selectbox("Category", ['All'] + categories)
    
    # Filter apps
    filtered_apps = st.session_state.app_database
    
    if search_term:
        filtered_apps = [
            app for app in filtered_apps
            if search_term.lower() in app.get('Appname', '').lower() or
               search_term.lower() in app.get('description', '').lower() or
               search_term.lower() in app.get('tag', '').lower()
        ]
    
    if category_filter != 'All':
        filtered_apps = [app for app in filtered_apps if app.get('Category', '') == category_filter]
    
    st.write(f"Found {len(filtered_apps)} apps")
    
    # Display apps
    for app in filtered_apps[:20]:  # Limit to 20 apps for performance
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class="app-card">
                    <h4>{app.get('Appname', 'Unknown')}</h4>
                    <p>{app.get('description', 'No description available')[:200]}...</p>
                    <small>Category: {app.get('Category', 'Unknown')} | Tags: {app.get('tag', 'None')}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                app_name = app.get('Appname', '')
                repo_url = app.get('entryURL', '')
                
                if app_name in st.session_state.installed_apps:
                    st.success("✅ Installed")
                else:
                    if st.button(f"Install {app_name}", key=f"install_{app_name}"):
                        install_app(app_name, repo_url)

def show_installed_apps():
    """Show installed apps page"""
    st.markdown("## 📦 Installed Apps")
    
    if not st.session_state.installed_apps:
        st.info("No apps installed yet. Go to Browse Apps to install some!")
        return
    
    for app_name, app_info in st.session_state.installed_apps.items():
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                status = app_info.get('status', 'unknown')
                status_class = {
                    'running': 'status-running',
                    'stopped': 'status-stopped', 
                    'installed': 'status-installed'
                }.get(status, 'status-stopped')
                
                st.markdown(f"""
                <div class="app-card">
                    <h4>{app_name}</h4>
                    <span class="status-badge {status_class}">{status.upper()}</span>
                    <p>{app_info.get('description', 'Installed app')}</p>
                    <small>Path: {app_info.get('path', 'Unknown')}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if status == 'running':
                    if st.button(f"Stop {app_name}", key=f"stop_{app_name}"):
                        stop_app(app_name)
                else:
                    if st.button(f"Run {app_name}", key=f"run_{app_name}"):
                        run_app(app_name)
                
                if st.button(f"Uninstall {app_name}", key=f"uninstall_{app_name}"):
                    uninstall_app(app_name)

def show_installation_log():
    """Show installation log page"""
    st.markdown("## 📋 Installation Log")
    
    if st.session_state.installation_logs:
        for log_entry in reversed(st.session_state.installation_logs):
            timestamp = log_entry.get('timestamp', 'Unknown')
            app_name = log_entry.get('app_name', 'Unknown')
            message = log_entry.get('message', '')
            log_type = log_entry.get('type', 'info')
            
            if log_type == 'error':
                st.error(f"[{timestamp}] {app_name}: {message}")
            elif log_type == 'success':
                st.success(f"[{timestamp}] {app_name}: {message}")
            elif log_type == 'warning':
                st.warning(f"[{timestamp}] {app_name}: {message}")
            else:
                st.info(f"[{timestamp}] {app_name}: {message}")
    else:
        st.info("No installation logs yet")

def show_settings():
    """Show settings page"""
    st.markdown("## ⚙️ Settings")
    
    # Theme settings
    st.markdown("### 🎨 Theme")
    theme = st.selectbox("Theme", ["Dark", "Light"], index=0)
    st.session_state.theme = theme.lower()
    
    # Engine settings
    st.markdown("### 🔧 Engine Settings")
    
    current_path = st.session_state.engine.base_path
    st.text_input("Base Path", value=str(current_path), disabled=True)
    
    if st.button("🔄 Reset Engine"):
        base_path = os.environ.get('PINOKIO_BASE_PATH', './pinokio_apps')
        st.session_state.engine = UnifiedPinokioEngine(base_path=base_path)
        add_toast("Engine reset successfully!", "success")
        st.rerun()
    
    # Debug info
    st.markdown("### 🐛 Debug Info")
    
    if st.button("Clear Logs"):
        st.session_state.live_logs = []
        st.session_state.installation_logs = []
        add_toast("Logs cleared!", "success")
        st.rerun()
    
    with st.expander("System Information"):
        gpu = detect_gpu()
        st.json({
            "GPU Available": gpu['available'],
            "GPU Model": gpu['model'],
            "Python Path": sys.executable,
            "Working Directory": os.getcwd(),
            "Total Apps": len(st.session_state.app_database),
            "Installed Apps": len(st.session_state.installed_apps),
            "Live Log Entries": len(st.session_state.live_logs)
        })

if __name__ == "__main__":
    main()
