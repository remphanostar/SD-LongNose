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
    page_title="🚀 PinokioCloud",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme CSS with cyberpunk styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
        color: #00ff9f;
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(45deg, #00ff9f, #00d4ff, #ff00ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(0, 255, 159, 0.5);
        margin-bottom: 2rem;
    }
    
    .stSelectbox > div > div {
        background-color: rgba(0, 255, 159, 0.1);
        border: 1px solid #00ff9f;
        color: #00ff9f;
    }
    
    .stButton > button {
        background: linear-gradient(45deg, #00ff9f, #00d4ff);
        color: #000;
        border: none;
        border-radius: 25px;
        font-weight: bold;
        box-shadow: 0 0 20px rgba(0, 255, 159, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #00d4ff, #ff00ff);
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
        transform: translateY(-2px);
    }
    
    .success-toast {
        background: linear-gradient(90deg, rgba(0, 255, 159, 0.2), rgba(0, 212, 255, 0.2));
        border-left: 4px solid #00ff9f;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .error-toast {
        background: linear-gradient(90deg, rgba(255, 0, 100, 0.2), rgba(255, 100, 0, 0.2));
        border-left: 4px solid #ff0064;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .app-card {
        background: rgba(0, 255, 159, 0.05);
        border: 1px solid rgba(0, 255, 159, 0.3);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 255, 159, 0.1);
    }
    
    .log-container {
        background: rgba(0, 0, 0, 0.8);
        border: 1px solid #00ff9f;
        border-radius: 10px;
        padding: 1rem;
        max-height: 400px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
    }
    
    .status-running {
        color: #00ff9f;
        text-shadow: 0 0 10px rgba(0, 255, 159, 0.5);
    }
    
    .status-installed {
        color: #00d4ff;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
    }
    
    .status-available {
        color: #ffffff;
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

# Toast notification system
def add_toast(message: str, toast_type: str = "info"):
    """Add toast notification"""
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.toasts.append({
        'message': message,
        'type': toast_type,
        'timestamp': timestamp
    })
    # Keep only last 10 toasts
    if len(st.session_state.toasts) > 10:
        st.session_state.toasts = st.session_state.toasts[-10:]

def display_toasts():
    """Display toast notifications"""
    if st.session_state.toasts:
        for toast in st.session_state.toasts[-3:]:  # Show last 3 toasts
            css_class = f"{toast['type']}-toast"
            st.markdown(f"""
                <div class="{css_class}">
                    <strong>[{toast['timestamp']}]</strong> {toast['message']}
                </div>
            """, unsafe_allow_html=True)

# Live logging system - Enhanced for MODULE 2
def add_log(app_name: str, message: str, log_type: str = "info"):
    """Add log entry with timestamp and color coding"""
    timestamp = time.strftime("%H:%M:%S")
    color_map = {
        'info': '#00d4ff',
        'success': '#00ff9f', 
        'error': '#ff0064',
        'warning': '#ffaa00',
        'git': '#00ff9f',
        'install': '#00d4ff',
        'python': '#ffaa00',
        'command': '#ffffff'
    }
    color = color_map.get(log_type, '#ffffff')
    
    log_entry = {
        'timestamp': timestamp,
        'app': app_name,
        'message': message,
        'type': log_type,
        'color': color
    }
    
    st.session_state.logs.append(log_entry)
    # Keep only last 200 logs for more history
    if len(st.session_state.logs) > 200:
        st.session_state.logs = st.session_state.logs[-200:]

# Revolutionary Raw Output System - MODULE 2
def add_raw_output(app_name: str, line: str, output_type: str = "info"):
    """Add raw output line for revolutionary streaming terminal - MODULE 2"""
    if "raw_output" not in st.session_state:
        st.session_state.raw_output = []
    
    timestamp = time.strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
    
    # Color mapping for different output types
    color_map = {
        'command': '#ffffff',
        'git': '#00ff9f',
        'install': '#00d4ff', 
        'python': '#ffaa00',
        'success': '#00ff9f',
        'error': '#ff0064',
        'warning': '#ffaa00',
        'info': '#cccccc'
    }
    
    raw_entry = {
        'timestamp': timestamp,
        'app': app_name,
        'line': line,
        'type': output_type,
        'color': color_map.get(output_type, '#cccccc')
    }
    
    st.session_state.raw_output.append(raw_entry)
    
    # Keep only last 500 lines for performance
    if len(st.session_state.raw_output) > 500:
        st.session_state.raw_output = st.session_state.raw_output[-500:]

def display_revolutionary_terminal():
    """Display the revolutionary raw output terminal - MODULE 2"""
    if "raw_output" not in st.session_state:
        st.session_state.raw_output = []
    
    st.markdown("### 🖥️ Live Terminal Output")
    
    # Terminal container with custom styling
    terminal_height = 400
    
    # Create scrollable terminal content
    if st.session_state.raw_output:
        terminal_content = ""
        for entry in st.session_state.raw_output[-100:]:  # Show last 100 lines
            terminal_content += f"""
                <div style="color: {entry['color']}; font-family: 'Courier New', monospace; font-size: 12px; margin: 1px 0; white-space: pre-wrap;">
                    <span style="color: #666; font-size: 10px;">[{entry['timestamp']}]</span> <strong>{entry['app']}:</strong> {entry['line']}
                </div>
            """
        
        # Terminal container with auto-scroll
        st.markdown(f"""
            <div class="terminal-container" style="
                background: rgba(0, 0, 0, 0.9);
                border: 2px solid #00ff9f;
                border-radius: 10px;
                padding: 15px;
                height: {terminal_height}px;
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                box-shadow: 0 0 20px rgba(0, 255, 159, 0.3);
            ">
                {terminal_content}
                <div id="terminal-bottom"></div>
            </div>
            <script>
                // Auto-scroll to bottom
                var element = document.getElementById("terminal-bottom");
                if (element) element.scrollIntoView();
            </script>
        """, unsafe_allow_html=True)
        
        # Copy button
        if st.button("📋 Copy Terminal Output"):
            terminal_text = "\n".join([f"[{entry['timestamp']}] {entry['app']}: {entry['line']}" 
                                     for entry in st.session_state.raw_output])
            st.code(terminal_text, language="bash")
            st.success("Terminal output copied!")
    else:
        st.markdown("""
            <div style="
                background: rgba(0, 0, 0, 0.9);
                border: 2px solid #00ff9f;
                border-radius: 10px;
                padding: 20px;
                height: 400px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #00ff9f;
                font-family: 'Courier New', monospace;
            ">
                <div style="text-align: center;">
                    <div style="font-size: 48px;">🖥️</div>
                    <div>Waiting for app operations...</div>
                    <div style="font-size: 12px; color: #666;">Real-time output will appear here</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

def progress_callback(app_name: str):
    """Create progress callback for app operations"""
    def callback(message: str):
        add_log(app_name, message, "info")
    return callback

def create_output_callback(app_name: str):
    """Create output streaming callback for revolutionary terminal - MODULE 2"""
    def callback(line: str, output_type: str = "info"):
        add_raw_output(app_name, line, output_type)
        # Also add to regular logs for compatibility
        add_log(app_name, line, output_type)
    return callback

# App management functions - Enhanced for MODULE 2
async def install_app_async(app_name: str):
    """Install app with revolutionary streaming output - MODULE 2"""
    add_log(app_name, f"Starting installation of {app_name}", "info")
    add_toast(f"Installing {app_name}...", "info")
    
    # Set up revolutionary streaming output
    output_callback = create_output_callback(app_name)
    st.session_state.engine.set_output_callback(output_callback)
    
    try:
        add_raw_output(app_name, f"🚀 INSTALLATION STARTED: {app_name}", "success")
        add_raw_output(app_name, f"📊 Initializing installation process...", "info")
        
        success = await st.session_state.engine.install_app(
            app_name, 
            progress_callback=progress_callback(app_name)
        )
        
        if success:
            add_log(app_name, f"Successfully installed {app_name}", "success")
            add_toast(f"✅ {app_name} installed successfully!", "success")
            add_raw_output(app_name, f"✅ INSTALLATION COMPLETED: {app_name}", "success")
        else:
            add_log(app_name, f"Failed to install {app_name}", "error")
            add_toast(f"❌ Failed to install {app_name}", "error")
            add_raw_output(app_name, f"❌ INSTALLATION FAILED: {app_name}", "error")
        
        return success
    except Exception as e:
        add_log(app_name, f"Installation error: {str(e)}", "error")
        add_toast(f"❌ Installation error: {str(e)}", "error")
        add_raw_output(app_name, f"💥 INSTALLATION ERROR: {str(e)}", "error")
        return False
    finally:
        # Clear output callback
        st.session_state.engine.clear_output_callback()

def install_app_sync(app_name: str):
    """Synchronous wrapper for install_app_async"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(install_app_async(app_name))
    except Exception as e:
        add_toast(f"❌ Installation failed: {str(e)}", "error")
        return False
    finally:
        try:
            loop.close()
        except:
            pass

async def run_app_async(app_name: str):
    """Run app with revolutionary streaming output - MODULE 2"""
    add_log(app_name, f"Starting {app_name}", "info")
    add_toast(f"Starting {app_name}...", "info")
    
    # Set up revolutionary streaming output
    output_callback = create_output_callback(app_name)
    st.session_state.engine.set_output_callback(output_callback)
    
    try:
        add_raw_output(app_name, f"🚀 APP STARTUP INITIATED: {app_name}", "success")
        add_raw_output(app_name, f"📋 Checking app status and requirements...", "info")
        
        success = await st.session_state.engine.run_app(
            app_name,
            progress_callback=progress_callback(app_name)
        )
        
        if success:
            add_log(app_name, f"Successfully started {app_name}", "success")
            add_toast(f"✅ {app_name} started successfully!", "success")
            add_raw_output(app_name, f"✅ APP STARTED SUCCESSFULLY: {app_name}", "success")
            
            # Show app URLs if available
            urls = st.session_state.engine.get_app_urls(app_name)
            if urls:
                add_raw_output(app_name, f"🌐 App accessible at: {urls[0]}", "success")
        else:
            add_log(app_name, f"Failed to start {app_name}", "error")
            add_toast(f"❌ Failed to start {app_name}", "error")
            add_raw_output(app_name, f"❌ APP STARTUP FAILED: {app_name}", "error")
        
        return success
    except Exception as e:
        add_log(app_name, f"Runtime error: {str(e)}", "error")
        add_toast(f"❌ Runtime error: {str(e)}", "error")
        add_raw_output(app_name, f"💥 RUNTIME ERROR: {str(e)}", "error")
        return False
    finally:
        # Clear output callback
        st.session_state.engine.clear_output_callback()

def run_app_sync(app_name: str):
    """Synchronous wrapper for run_app_async"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(run_app_async(app_name))
    except Exception as e:
        add_toast(f"❌ Failed to start app: {str(e)}", "error")
        return False
    finally:
        try:
            loop.close()
        except:
            pass

def stop_app_sync(app_name: str):
    """Stop running app"""
    add_log(app_name, f"Stopping {app_name}", "info")
    add_toast(f"Stopping {app_name}...", "info")
    
    try:
        success = st.session_state.engine.stop_app(app_name)
        if success:
            add_log(app_name, f"Successfully stopped {app_name}", "success")
            add_toast(f"✅ {app_name} stopped", "success")
        else:
            add_log(app_name, f"Failed to stop {app_name}", "error")
            add_toast(f"❌ Failed to stop {app_name}", "error")
        return success
    except Exception as e:
        add_log(app_name, f"Stop error: {str(e)}", "error")
        add_toast(f"❌ Stop error: {str(e)}", "error")
        return False

def uninstall_app_sync(app_name: str):
    """Uninstall app"""
    add_log(app_name, f"Uninstalling {app_name}", "info")
    add_toast(f"Uninstalling {app_name}...", "info")
    
    try:
        success = st.session_state.engine.uninstall_app(app_name)
        if success:
            add_log(app_name, f"Successfully uninstalled {app_name}", "success")
            add_toast(f"✅ {app_name} uninstalled", "success")
        else:
            add_log(app_name, f"Failed to uninstall {app_name}", "error")
            add_toast(f"❌ Failed to uninstall {app_name}", "error")
        return success
    except Exception as e:
        add_log(app_name, f"Uninstall error: {str(e)}", "error")
        add_toast(f"❌ Uninstall error: {str(e)}", "error")
        return False

# UI Pages
def dashboard_page():
    """Main dashboard page"""
    st.markdown('<h1 class="main-header">🚀 PinokioCloud Dashboard</h1>', unsafe_allow_html=True)
    
    # Display toasts
    display_toasts()
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        available_count = len(st.session_state.engine.list_available_apps())
        st.metric("📦 Available Apps", available_count)
    
    with col2:
        installed_count = len(st.session_state.engine.list_installed_apps())
        st.metric("✅ Installed Apps", installed_count)
    
    with col3:
        running_count = len([app for app in st.session_state.engine.list_installed_apps() 
                           if st.session_state.engine.is_app_running(app)])
        st.metric("🟢 Running Apps", running_count)
    
    with col4:
        logs_count = len(st.session_state.logs)
        st.metric("📝 Log Entries", logs_count)
    
    # System info
    st.subheader("🖥️ System Information")
    
    # GPU info
    try:
        gpu_info = st.session_state.engine.context.gpu_model
        if gpu_info:
            st.success(f"🎮 GPU Detected: {gpu_info}")
        else:
            st.warning("⚠️ No GPU detected - running in CPU mode")
    except:
        st.warning("⚠️ GPU detection failed")
    
    # Environment info  
    if 'google.colab' in sys.modules:
        st.info("☁️ Running in Google Colab environment")
    else:
        st.info("🖥️ Running in local environment")
    
    # Base path info
    st.info(f"📁 Apps Directory: {BASE_PATH}")

def browse_apps_page():
    """Browse and manage available apps with revolutionary split-screen UI - MODULE 2"""
    st.markdown('<h1 class="main-header">📚 Browse Apps</h1>', unsafe_allow_html=True)
    
    # Display toasts
    display_toasts()
    
    # Revolutionary Split-Screen Layout
    col_controls, col_terminal = st.columns([1, 1])
    
    with col_controls:
        st.markdown("### 🎮 App Management")
        
        # Get apps data
        available_apps = st.session_state.engine.list_available_apps()
        installed_apps = st.session_state.engine.list_installed_apps()
        
        # Search and filter
        search_term = st.text_input("🔍 Search Apps", placeholder="Search by name, description, or category...")
        categories = list(set([app.get('category', 'OTHER') for app in available_apps if app.get('category')]))
        category_filter = st.selectbox("📂 Category", ['All'] + sorted(categories))
        
        # Filter apps
        filtered_apps = available_apps
        if search_term:
            filtered_apps = [app for app in filtered_apps 
                            if search_term.lower() in app.get('name', '').lower() or
                               search_term.lower() in app.get('description', '').lower()]
        
        if category_filter != 'All':
            filtered_apps = [app for app in filtered_apps if app.get('category') == category_filter]
        
        st.write(f"📊 Showing {len(filtered_apps)} of {len(available_apps)} apps")
        
        # Compact app display for split screen
        for app in filtered_apps[:15]:  # Show fewer apps in split screen
            app_name = app.get('name', app.get('title', 'Unknown'))
            
            with st.expander(f"📱 {app_name}", expanded=False):
                # App info
                category = app.get('category', 'OTHER')
                st.markdown(f"**Category:** {category}")
                
                description = app.get('description', 'No description available')
                st.write(description[:150] + "..." if len(description) > 150 else description)
                
                # Status and actions
                is_installed = app_name in installed_apps
                is_running = st.session_state.engine.is_app_running(app_name) if is_installed else False
                
                # Action buttons in columns
                col1, col2, col3 = st.columns(3)
                
                if is_running:
                    with col1:
                        st.markdown('<p class="status-running">🟢 RUNNING</p>', unsafe_allow_html=True)
                        urls = st.session_state.engine.get_app_urls(app_name)
                        if urls:
                            st.markdown(f"[Open App]({urls[0]})")
                    
                    with col2:
                        if st.button(f"⏹️ Stop", key=f"stop_{app_name}"):
                            add_raw_output(app_name, f"🛑 STOP REQUEST: {app_name}", "warning")
                            stop_app_sync(app_name)
                            st.rerun()
                    
                    with col3:
                        if st.button(f"🔗 ngrok", key=f"ngrok_{app_name}"):
                            add_raw_output(app_name, f"🌐 Creating ngrok tunnel...", "info")
                            tunnel_url = st.session_state.engine.setup_ngrok_tunnel(app_name)
                            if tunnel_url:
                                add_raw_output(app_name, f"✅ Public URL: {tunnel_url}", "success")
                                st.success(f"Public URL: {tunnel_url}")
                            else:
                                add_raw_output(app_name, f"❌ Failed to create tunnel", "error")
                        
                elif is_installed:
                    with col1:
                        st.markdown('<p class="status-installed">📦 INSTALLED</p>', unsafe_allow_html=True)
                    
                    with col2:
                        if st.button(f"▶️ Run", key=f"run_{app_name}"):
                            run_app_sync(app_name)
                            st.rerun()
                    
                    with col3:
                        if st.button(f"🗑️ Remove", key=f"uninstall_{app_name}"):
                            add_raw_output(app_name, f"🗑️ UNINSTALL REQUEST: {app_name}", "warning")
                            uninstall_app_sync(app_name)
                            st.rerun()
                else:
                    with col1:
                        st.markdown('<p class="status-available">⬇️ AVAILABLE</p>', unsafe_allow_html=True)
                    
                    with col2:
                        if st.button(f"📥 Install", key=f"install_{app_name}"):
                            install_app_sync(app_name)
                            st.rerun()
    
    with col_terminal:
        # Revolutionary Raw Output Terminal
        display_revolutionary_terminal()

def logs_page():
    """Live logs and monitoring page"""
    st.markdown('<h1 class="main-header">📝 Live Logs</h1>', unsafe_allow_html=True)
    
    # Display toasts
    display_toasts()
    
    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        auto_refresh = st.checkbox("🔄 Auto Refresh (5s)", value=False)
    
    with col2:
        if st.button("🔄 Refresh Logs"):
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Logs"):
            st.session_state.logs = []
            add_toast("Logs cleared", "success")
            st.rerun()
    
    # Display logs
    st.subheader("📊 Recent Activity")
    
    if st.session_state.logs:
        # Create logs display
        logs_html = '<div class="log-container">'
        for log in st.session_state.logs[-50:]:  # Show last 50 logs
            logs_html += f'''
                <div style="color: {log['color']}; margin-bottom: 4px;">
                    <span style="color: #666;">[{log['timestamp']}]</span> 
                    <strong>{log['app']}:</strong> {log['message']}
                </div>
            '''
        logs_html += '</div>'
        st.markdown(logs_html, unsafe_allow_html=True)
    else:
        st.info("No logs available. App activities will appear here.")
    
    # Auto refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()

def settings_page():
    """Settings and configuration page"""
    st.markdown('<h1 class="main-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    
    # Display toasts
    display_toasts()
    
    # Engine info
    st.subheader("🔧 Engine Information")
    st.write(f"**Base Path:** {st.session_state.engine.base_path}")
    st.write(f"**Apps Database:** {len(st.session_state.engine.apps_data)} apps loaded")
    st.write(f"**Installed Apps:** {len(st.session_state.engine.installed_apps)}")
    
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
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### 🚀 PinokioCloud")
        
        # Navigation menu
        pages = {
            "📊 Dashboard": "Dashboard",
            "📚 Browse Apps": "Browse Apps", 
            "📝 Live Logs": "Logs",
            "⚙️ Settings": "Settings"
        }
        
        selected_page = st.selectbox("Navigation", list(pages.keys()))
        st.session_state.current_page = pages[selected_page]
        
        # Quick status
        st.markdown("---")
        st.markdown("### 📊 Quick Status")
        
        installed_apps = st.session_state.engine.list_installed_apps()
        if installed_apps:
            for app_name in list(installed_apps.keys())[:5]:  # Show first 5
                is_running = st.session_state.engine.is_app_running(app_name)
                status = "🟢" if is_running else "⚪"
                st.markdown(f"{status} {app_name}")
            
            if len(installed_apps) > 5:
                st.markdown(f"... and {len(installed_apps) - 5} more")
        else:
            st.markdown("No apps installed")
    
    # Main content area
    if st.session_state.current_page == "Dashboard":
        dashboard_page()
    elif st.session_state.current_page == "Browse Apps":
        browse_apps_page()
    elif st.session_state.current_page == "Logs":
        logs_page()
    elif st.session_state.current_page == "Settings":
        settings_page()

if __name__ == "__main__":
    main()