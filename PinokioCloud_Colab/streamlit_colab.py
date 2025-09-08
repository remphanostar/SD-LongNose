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
    """Display enhanced revolutionary terminal - MODULE 4 ENHANCED"""
    if "raw_output" not in st.session_state:
        st.session_state.raw_output = []
    
    # Enhanced terminal controls
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search Terminal", placeholder="Search output...", key="terminal_search")
    
    with col2:
        output_filter = st.selectbox("🎨 Filter Type", 
                                   ['All', 'Commands', 'Git', 'Install', 'Python', 'Errors', 'Success'],
                                   key="terminal_filter")
    
    with col3:
        if st.button("🧹 Clear", key="clear_terminal"):
            st.session_state.raw_output = []
            add_toast("Terminal cleared", "info")
            st.rerun()
    
    with col4:
        auto_scroll = st.checkbox("📜 Auto-scroll", value=True, key="auto_scroll")
    
    # Filter terminal output
    filtered_output = st.session_state.raw_output
    
    if search_term:
        filtered_output = [entry for entry in filtered_output 
                          if search_term.lower() in entry['line'].lower()]
    
    if output_filter != 'All':
        filter_map = {
            'Commands': 'command', 'Git': 'git', 'Install': 'install',
            'Python': 'python', 'Errors': 'error', 'Success': 'success'
        }
        filter_type = filter_map.get(output_filter, 'info')
        filtered_output = [entry for entry in filtered_output if entry['type'] == filter_type]
    
    # Enhanced terminal display
    terminal_height = 350
    
    if filtered_output:
        # Show terminal stats
        st.write(f"📊 Showing {len(filtered_output)} of {len(st.session_state.raw_output)} terminal lines")
        
        # Enhanced terminal content with syntax highlighting
        terminal_content = ""
        for entry in filtered_output[-80:]:  # Show last 80 lines
            # Enhanced styling based on type
            type_icons = {
                'command': '💻', 'git': '🌿', 'install': '📦', 'python': '🐍',
                'success': '✅', 'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'
            }
            icon = type_icons.get(entry['type'], '📝')
            
            # Enhanced color and formatting
            terminal_content += f"""
                <div style="
                    color: {entry['color']};
                    font-family: 'Courier New', monospace;
                    font-size: 11px;
                    margin: 2px 0;
                    padding: 2px 5px;
                    border-radius: 3px;
                    background: rgba(0, 0, 0, 0.3);
                    white-space: pre-wrap;
                    border-left: 3px solid {entry['color']};
                ">
                    <span style="color: #666; font-size: 9px;">[{entry['timestamp']}]</span>
                    <span style="color: #888;">{icon}</span>
                    <strong style="color: #00ff9f;">{entry['app']}:</strong>
                    <span>{entry['line']}</span>
                </div>
            """
        
        # Revolutionary terminal container with enhanced styling
        st.markdown(f"""
            <div class="revolutionary-terminal" style="
                background: linear-gradient(135deg, rgba(0, 0, 0, 0.95), rgba(0, 20, 20, 0.9));
                border: 2px solid #00ff9f;
                border-radius: 15px;
                padding: 15px;
                height: {terminal_height}px;
                overflow-y: auto;
                font-family: 'Courier New', monospace;
                box-shadow: 
                    0 0 30px rgba(0, 255, 159, 0.4),
                    inset 0 0 20px rgba(0, 255, 159, 0.1);
                position: relative;
            ">
                <div style="
                    position: absolute;
                    top: 5px;
                    right: 15px;
                    color: #00ff9f;
                    font-size: 10px;
                    opacity: 0.7;
                ">
                    LIVE TERMINAL v2.0
                </div>
                {terminal_content}
                <div id="terminal-bottom-enhanced"></div>
            </div>
            <script>
                // Enhanced auto-scroll
                if ({str(auto_scroll).lower()}) {{
                    var element = document.getElementById("terminal-bottom-enhanced");
                    if (element) element.scrollIntoView({{behavior: 'smooth'}});
                }}
            </script>
        """, unsafe_allow_html=True)
        
        # Enhanced controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy All Output", key="copy_terminal"):
                terminal_text = "\n".join([f"[{entry['timestamp']}] {entry['app']}: {entry['line']}" 
                                         for entry in filtered_output])
                st.code(terminal_text, language="bash")
                add_toast("Terminal output copied!", "success")
        
        with col2:
            if st.button("💾 Export to File", key="export_terminal"):
                export_terminal_to_file(filtered_output)
    else:
        # Enhanced empty state
        st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(0, 20, 40, 0.8));
                border: 2px solid #00ff9f;
                border-radius: 15px;
                padding: 30px;
                height: {terminal_height}px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #00ff9f;
                font-family: 'Courier New', monospace;
                text-align: center;
            ">
                <div>
                    <div style="font-size: 64px; margin-bottom: 20px; opacity: 0.7;">🖥️</div>
                    <div style="font-size: 18px; font-weight: bold;">Revolutionary Terminal Ready</div>
                    <div style="font-size: 14px; color: #666; margin-top: 10px;">
                        Start an app operation to see real-time output
                    </div>
                    <div style="font-size: 12px; color: #444; margin-top: 5px;">
                        Every git clone, pip install, and Python execution will appear here
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

def export_terminal_to_file(output_data: List[Dict[str, Any]]):
    """Export terminal output to downloadable file - MODULE 4"""
    try:
        import io
        
        # Create formatted output
        output_text = "PinokioCloud Terminal Export\n"
        output_text += "=" * 50 + "\n"
        output_text += f"Exported: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        output_text += f"Total Lines: {len(output_data)}\n\n"
        
        for entry in output_data:
            output_text += f"[{entry['timestamp']}] {entry['type'].upper()} | {entry['app']}: {entry['line']}\n"
        
        # Create download
        st.download_button(
            label="💾 Download Terminal Log",
            data=output_text,
            file_name=f"pinokio_terminal_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
        
        add_toast("Terminal log ready for download!", "success")
        
    except Exception as e:
        st.error(f"Export failed: {e}")

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

# MODULE 4 UI Enhancement Functions
def get_tag_color(tag: str) -> str:
    """Get color for tag based on content - MODULE 4"""
    tag_colors = {
        # Category-based colors
        'image': '#ff6b9d', 'audio': '#4ecdc4', 'video': '#45b7d1', 'llm': '#96ceb4',
        
        # Popularity colors
        'popular': '#ffd93d', 'well-liked': '#74b9ff', 'community-approved': '#a29bfe',
        
        # Language colors
        'lang-python': '#3776ab', 'lang-javascript': '#f7df1e', 'lang-typescript': '#3178c6',
        
        # Quality colors
        'recently-updated': '#00b894', 'actively-maintained': '#00cec9', 'licensed': '#6c5ce7',
        
        # Default colors
        'pinokio-tagged': '#00ff9f', 'community-forked': '#fd79a8'
    }
    
    tag_lower = tag.lower()
    
    # Check for direct matches
    if tag_lower in tag_colors:
        return tag_colors[tag_lower]
    
    # Check for pattern matches
    for pattern, color in tag_colors.items():
        if pattern in tag_lower or tag_lower in pattern:
            return color
    
    # Default color based on hash
    import hashlib
    hash_val = int(hashlib.md5(tag.encode()).hexdigest()[:6], 16)
    colors = ['#ff7675', '#74b9ff', '#a29bfe', '#fd79a8', '#fdcb6e', '#e17055', '#00b894', '#55a3ff']
    return colors[hash_val % len(colors)]

def is_app_compatible_with_platform(app: Dict[str, Any]) -> bool:
    """Check if app is compatible with current platform - MODULE 4"""
    try:
        # Get platform constraints from engine
        if hasattr(st.session_state.engine, 'cloud_env'):
            platform = st.session_state.engine.cloud_env.platform_info['platform']
            
            # Lightning AI compatibility check
            if platform == 'lightning_ai':
                # Check if app has known Lightning AI issues
                enhanced_tags = app.get('enhanced_tags', [])
                if any('conda' in tag.lower() or 'system' in tag.lower() for tag in enhanced_tags):
                    return False  # Likely requires conda or system packages
                
                # Check category - some are more compatible
                category = app.get('category', '')
                if category in ['UTILITY', 'LLM']:
                    return True  # Usually more compatible
                elif category in ['IMAGE', 'VIDEO']:
                    return False  # Often require complex dependencies
            
            # Google Colab - generally compatible
            elif platform == 'google_colab':
                return True  # Colab is very compatible
            
            # Other platforms - assume compatible
            else:
                return True
        
        return True  # Default to compatible
        
    except Exception:
        return True  # Default to compatible if check fails

def show_enhanced_statistics(filtered_apps: List[Dict[str, Any]]):
    """Show enhanced statistics for current app selection - MODULE 4"""
    try:
        if not filtered_apps:
            return
        
        with st.expander("📊 Enhanced Statistics", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**⭐ Star Distribution**")
                
                # Group by star ranges
                star_ranges = {
                    '🌟 1000+ stars': len([app for app in filtered_apps if app.get('total_stars', 0) >= 1000]),
                    '⭐ 100+ stars': len([app for app in filtered_apps if 100 <= app.get('total_stars', 0) < 1000]),
                    '✨ 10+ stars': len([app for app in filtered_apps if 10 <= app.get('total_stars', 0) < 100]),
                    '📍 <10 stars': len([app for app in filtered_apps if app.get('total_stars', 0) < 10])
                }
                
                for range_name, count in star_ranges.items():
                    if count > 0:
                        st.write(f"{range_name}: {count}")
            
            with col2:
                st.markdown("**📂 Category Breakdown**")
                
                categories = {}
                for app in filtered_apps:
                    cat = app.get('category', 'OTHER')
                    categories[cat] = categories.get(cat, 0) + 1
                
                for category, count in sorted(categories.items()):
                    category_icons = {'IMAGE': '🖼️', 'AUDIO': '🎵', 'VIDEO': '🎬', 'LLM': '🧠', 'UTILITY': '🔧', 'OTHER': '📦'}
                    icon = category_icons.get(category, '📦')
                    st.write(f"{icon} {category}: {count}")
            
            with col3:
                st.markdown("**💯 Quality Analysis**")
                
                if filtered_apps:
                    avg_quality = sum(app.get('quality_score', 0) for app in filtered_apps) / len(filtered_apps)
                    high_quality = len([app for app in filtered_apps if app.get('quality_score', 0) > 80])
                    good_quality = len([app for app in filtered_apps if 60 <= app.get('quality_score', 0) <= 80])
                    
                    st.write(f"📈 Average Quality: {avg_quality:.1f}")
                    st.write(f"🏆 High Quality: {high_quality}")
                    st.write(f"✅ Good Quality: {good_quality}")
    
    except Exception as e:
        st.warning(f"Statistics display failed: {e}")

def install_app_with_enhanced_feedback(app_name: str):
    """Install app with revolutionary real-time feedback - MODULE 4"""
    # Create enhanced progress container
    progress_container = st.empty()
    
    with progress_container.container():
        st.markdown(f"### 📥 Installing {app_name}")
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        steps_info = st.empty()
        
        # Enhanced progress callback
        def enhanced_progress(message: str):
            add_raw_output(app_name, message, "info")
            status_text.text(message)
            
            # Update progress bar based on message content
            progress = estimate_progress_from_message(message)
            progress_bar.progress(progress)
        
        # Start installation with enhanced feedback
        add_toast(f"🚀 Starting revolutionary installation of {app_name}", "info")
        
        try:
            success = install_app_sync_with_progress(app_name, enhanced_progress)
            
            if success:
                progress_bar.progress(100)
                status_text.text("✅ Installation completed successfully!")
                add_toast(f"✅ {app_name} installed with revolutionary feedback!", "success")
            else:
                status_text.text("❌ Installation failed - check terminal for details")
                add_toast(f"❌ Installation of {app_name} failed", "error")
                
        except Exception as e:
            status_text.text(f"💥 Installation error: {str(e)}")
            add_toast(f"💥 Installation error: {str(e)}", "error")

def run_app_with_enhanced_feedback(app_name: str):
    """Run app with revolutionary feedback - MODULE 4"""
    add_raw_output(app_name, f"🚀 ENHANCED APP STARTUP: {app_name}", "success")
    add_toast(f"🚀 Starting {app_name} with enhanced monitoring", "info")
    
    try:
        success = run_app_sync(app_name)
        if success:
            add_toast(f"✅ {app_name} launched successfully! Check for web UI.", "success")
        else:
            add_toast(f"❌ Failed to launch {app_name}", "error")
    except Exception as e:
        add_toast(f"💥 Launch error: {str(e)}", "error")

def uninstall_app_with_feedback(app_name: str):
    """Uninstall app with enhanced feedback - MODULE 4"""
    add_raw_output(app_name, f"🗑️ ENHANCED UNINSTALL: {app_name}", "warning")
    add_toast(f"🗑️ Removing {app_name} with cleanup", "info")
    
    try:
        success = uninstall_app_sync(app_name)
        if success:
            add_toast(f"✅ {app_name} removed completely", "success")
        else:
            add_toast(f"❌ Failed to remove {app_name}", "error")
    except Exception as e:
        add_toast(f"💥 Removal error: {str(e)}", "error")

def create_ngrok_tunnel_with_feedback(app_name: str):
    """Create ngrok tunnel with enhanced feedback - MODULE 4"""
    add_raw_output(app_name, f"🌐 ENHANCED TUNNEL CREATION: {app_name}", "info")
    
    try:
        tunnel_url = st.session_state.engine.setup_ngrok_tunnel(app_name)
        if tunnel_url:
            add_raw_output(app_name, f"✅ PUBLIC URL CREATED: {tunnel_url}", "success")
            
            # Enhanced tunnel display
            st.markdown(f"""
            <div style="
                background: linear-gradient(45deg, #00ff9f, #00d4ff);
                color: black;
                padding: 15px;
                border-radius: 15px;
                text-align: center;
                margin: 10px 0;
                box-shadow: 0 4px 20px rgba(0, 255, 159, 0.4);
            ">
                <div style="font-size: 18px; font-weight: bold;">🌐 Public Access Ready!</div>
                <div style="margin: 10px 0;">
                    <a href="{tunnel_url}" target="_blank" style="
                        color: black; 
                        text-decoration: none; 
                        font-weight: bold;
                        font-size: 16px;
                    ">{tunnel_url}</a>
                </div>
                <div style="font-size: 12px;">Share this URL with anyone!</div>
            </div>
            """, unsafe_allow_html=True)
            
            add_toast(f"🌐 {app_name} is now publicly accessible!", "success")
        else:
            add_raw_output(app_name, f"❌ TUNNEL CREATION FAILED", "error")
            st.error("❌ Failed to create public tunnel - check if app is running")
            
    except Exception as e:
        add_raw_output(app_name, f"💥 TUNNEL ERROR: {str(e)}", "error")
        st.error(f"💥 Tunnel error: {str(e)}")

def estimate_progress_from_message(message: str) -> float:
    """Estimate progress percentage from progress message - MODULE 4"""
    message_lower = message.lower()
    
    # Progress mapping based on typical installation steps
    progress_keywords = {
        'starting': 5, 'searching': 10, 'found app': 15, 'repository': 20,
        'cloning': 25, 'clone': 30, 'cloned': 40, 'environment': 45,
        'requirements': 50, 'installing': 60, 'download': 65, 'compile': 75,
        'configuring': 80, 'setup': 85, 'complete': 95, 'success': 100,
        'failed': 0, 'error': 0
    }
    
    for keyword, progress in progress_keywords.items():
        if keyword in message_lower:
            return progress
    
    # Default progress for unknown messages
    return 30

def install_app_sync_with_progress(app_name: str, progress_callback) -> bool:
    """Install app with enhanced progress tracking - MODULE 4"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Set up enhanced output callback
        output_callback = create_output_callback(app_name)
        st.session_state.engine.set_output_callback(output_callback)
        
        try:
            return loop.run_until_complete(install_app_async_with_progress(app_name, progress_callback))
        finally:
            st.session_state.engine.clear_output_callback()
            
    except Exception as e:
        add_toast(f"❌ Installation failed: {str(e)}", "error")
        return False
    finally:
        try:
            loop.close()
        except:
            pass

async def install_app_async_with_progress(app_name: str, progress_callback) -> bool:
    """Async install with revolutionary progress system - MODULE 4"""
    try:
        add_raw_output(app_name, f"🚀 REVOLUTIONARY INSTALL STARTED: {app_name}", "success")
        
        # Enhanced progress tracking
        progress_callback(f"🔍 Initializing revolutionary installation for {app_name}")
        
        success = await st.session_state.engine.install_app(app_name, progress_callback)
        
        if success:
            add_raw_output(app_name, f"✅ REVOLUTIONARY INSTALL COMPLETED: {app_name}", "success")
            progress_callback(f"✅ {app_name} installation completed successfully!")
        else:
            add_raw_output(app_name, f"❌ REVOLUTIONARY INSTALL FAILED: {app_name}", "error") 
            progress_callback(f"❌ {app_name} installation failed - check enhanced error messages")
        
        return success
        
    except Exception as e:
        add_raw_output(app_name, f"💥 INSTALL EXCEPTION: {str(e)}", "error")
        progress_callback(f"💥 Installation exception: {str(e)}")
        return False

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
    """Revolutionary dashboard with GitHub integration - MODULE 4 REWORK"""
    st.markdown('<h1 class="main-header">🚀 Revolutionary PinokioCloud Dashboard</h1>', unsafe_allow_html=True)
    
    # Display toasts
    display_toasts()
    
    # Enhanced quick stats with GitHub data
    col1, col2, col3, col4, col5 = st.columns(5)
    
    try:
        # Get enhanced apps data
        enhanced_apps = st.session_state.engine.get_enhanced_apps_with_sorting('total_stars')
        installed_apps = st.session_state.engine.list_installed_apps()
        running_apps = [app for app in installed_apps if st.session_state.engine.is_app_running(app)]
        
        with col1:
            st.metric("📱 Available Apps", len(enhanced_apps))
    
        with col2:
            st.metric("✅ Installed", len(installed_apps))
    
        with col3:
            st.metric("🟢 Running", len(running_apps))
        
        with col4:
            total_stars = sum(app.get('total_stars', 0) for app in enhanced_apps)
            st.metric("⭐ Total Stars", f"{total_stars:,}")
        
        with col5:
            enhanced_count = sum(1 for app in enhanced_apps if app.get('pinokio_stars', 0) > 0)
            st.metric("🌟 GitHub Enhanced", enhanced_count)
    
    except Exception as e:
        # Fallback to basic stats
        with col1:
            available_count = len(st.session_state.engine.list_available_apps())
            st.metric("📦 Available Apps", available_count)
        
        with col2:
            installed_count = len(st.session_state.engine.list_installed_apps())
            st.metric("✅ Installed Apps", installed_count)
        
        st.error(f"Enhanced stats failed: {e}")
    
    # Revolutionary system information panel
    with st.expander("🖥️ Enhanced System Information", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎮 Hardware Detection")
            
            # Enhanced GPU info
            try:
                gpu_info = st.session_state.engine.context.gpu
                if gpu_info and isinstance(gpu_info, dict):
                    gpu_name = gpu_info.get('name', 'Unknown GPU')
                    gpu_type = gpu_info.get('type', 'unknown')
                    st.success(f"🎮 GPU: {gpu_name} ({gpu_type.upper()})")
                    
                    # Show additional GPU details if available
                    if 'memory' in gpu_info and gpu_info['memory'] > 0:
                        st.info(f"💾 GPU Memory: {gpu_info['memory']}MB")
                else:
                    st.warning("⚠️ No GPU detected - running in CPU mode")
            except Exception as e:
                st.warning(f"⚠️ GPU detection failed: {e}")
            
            # Platform detection
            try:
                platform = st.session_state.engine.cloud_env.platform_info['platform']
                constraints = st.session_state.engine.cloud_env.platform_info['environment_restrictions']
                
                platform_names = {
                    'google_colab': '☁️ Google Colab',
                    'lightning_ai': '⚡ Lightning AI', 
                    'vast_ai_paperspace': '🖥️ Vast.AI/Paperspace',
                    'local': '🖥️ Local Environment'
                }
                
                platform_display = platform_names.get(platform, f'🌩️ {platform}')
                st.info(f"Platform: {platform_display}")
                
                if constraints:
                    st.warning(f"⚠️ Platform limitations: {', '.join(constraints)}")
                else:
                    st.success("✅ No platform limitations detected")
                    
            except Exception as e:
                st.warning(f"Platform detection failed: {e}")
        
        with col2:
            st.markdown("### 📊 Enhanced Statistics")
            
            # Show top apps by stars
            try:
                enhanced_apps = st.session_state.engine.get_enhanced_apps_with_sorting('total_stars')
                top_apps = enhanced_apps[:5]  # Top 5 by stars
                
                st.markdown("**⭐ Top Apps by Stars:**")
                for app in top_apps:
                    app_name = app.get('name', 'Unknown')
                    total_stars = app.get('total_stars', 0)
                    if total_stars > 0:
                        st.write(f"⭐ {app_name}: {total_stars:,} stars")
                    else:
                        st.write(f"📍 {app_name}: No GitHub data")
            
            except Exception as e:
                st.write("📊 Enhanced statistics not available")
            
            # Category distribution
            try:
                categories = st.session_state.engine.get_apps_by_category_enhanced()
                st.markdown("**📂 Category Distribution:**")
                
                category_icons = {'IMAGE': '🖼️', 'AUDIO': '🎵', 'VIDEO': '🎬', 'LLM': '🧠', 'UTILITY': '🔧', 'OTHER': '📦'}
                
                for category, apps in sorted(categories.items()):
                    icon = category_icons.get(category, '📦')
                    st.write(f"{icon} {category}: {len(apps)} apps")
            
            except Exception as e:
                st.write("📂 Category data not available")
    
    # Quick actions panel
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⭐ Enhance All Apps with GitHub Data", key="enhance_github"):
            enhance_database_with_progress()
    
    with col2:
        if st.button("🔄 Refresh Apps Database", key="refresh_db"):
            refresh_apps_database()
    
    with col3:
        if st.button("🧹 Clear All Logs", key="clear_all_logs"):
            st.session_state.logs = []
            st.session_state.raw_output = []
            add_toast("All logs cleared", "success")
            st.rerun()
    
    # Recently installed apps
    if installed_apps:
        st.markdown("### 📱 Recently Installed Apps")
        
        recent_apps = list(installed_apps.keys())[:6]  # Show 6 most recent
        cols = st.columns(3)
        
        for i, app_name in enumerate(recent_apps):
            col = cols[i % 3]
            
            with col:
                with st.container():
                    is_running = st.session_state.engine.is_app_running(app_name)
                    status_icon = "🟢" if is_running else "⚪"
                    
                    st.markdown(f"""
                    <div style="
                        background: rgba(0, 255, 159, 0.05);
                        border: 1px solid rgba(0, 255, 159, 0.2);
                        border-radius: 10px;
                        padding: 15px;
                        text-align: center;
                        margin: 10px 0;
                    ">
                        <div style="font-size: 24px;">{status_icon}</div>
                        <div style="font-weight: bold; color: #00ff9f;">{app_name}</div>
                        <div style="font-size: 12px; color: #666;">
                            {'Running' if is_running else 'Installed'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if is_running:
                        urls = st.session_state.engine.get_app_urls(app_name)
                        if urls and st.button(f"🌐 Open", key=f"dash_open_{app_name}"):
                            st.markdown(f'<script>window.open("{urls[0]}", "_blank");</script>', unsafe_allow_html=True)
    
    # Live terminal at bottom
    st.markdown("### 🖥️ Live Operations Monitor")
    display_revolutionary_terminal()

def enhance_database_with_progress():
    """Enhance database with GitHub data and show progress - MODULE 4"""
    progress_container = st.empty()
    
    with progress_container.container():
        st.markdown("### 🌟 Enhancing Apps with GitHub Stars")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(message: str):
            status_text.text(message)
            add_raw_output("GITHUB", message, "info")
            
            # Update progress based on message
            if "Processing GitHub data" in message:
                try:
                    # Extract progress from message like "10/284 apps (3.5%)"
                    import re
                    match = re.search(r'(\d+)/(\d+) apps \(([0-9.]+)%\)', message)
                    if match:
                        current, total, percent = match.groups()
                        progress_bar.progress(float(percent) / 100)
                except:
                    pass
        
        try:
            success = asyncio.run(st.session_state.engine.enhance_apps_database_with_github(progress_callback))
            
            if success:
                progress_bar.progress(100)
                status_text.text("✅ GitHub enhancement completed!")
                st.success("🌟 All apps enhanced with live GitHub data!")
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ GitHub enhancement failed - check logs")
                
        except Exception as e:
            st.error(f"💥 Enhancement error: {e}")

def refresh_apps_database():
    """Refresh apps database - MODULE 4"""
    add_toast("🔄 Refreshing apps database...", "info")
    
    try:
        # Reload apps database
        st.session_state.engine._load_apps_data(
            st.session_state.engine._load_apps_data.__defaults__[0] if hasattr(st.session_state.engine._load_apps_data, '__defaults__') 
            else "./cleaned_pinokio_apps.json"
        )
        
        add_toast("✅ Apps database refreshed!", "success")
        st.rerun()
        
    except Exception as e:
        add_toast(f"❌ Database refresh failed: {e}", "error")

def browse_apps_page():
    """Browse apps with revolutionary UI - MODULE 4 COMPLETE REWORK"""
    st.markdown('<h1 class="main-header">🌟 Revolutionary App Discovery</h1>', unsafe_allow_html=True)
    
    # Display toasts
    display_toasts()
    
    # Enhanced control panel
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input("🔍 Revolutionary Search", 
                                       placeholder="Search by name, description, tags, or GitHub topics...")
            
        with col2:
            # GitHub enhancement button
            if st.button("⭐ Enhance with GitHub Stars", help="Fetch live GitHub stars for all apps"):
                with st.spinner("🌟 Fetching GitHub data..."):
                    def enhancement_progress(msg):
                        st.write(f"📊 {msg}")
                        add_raw_output("SYSTEM", msg, "info")
                    
                    success = asyncio.run(st.session_state.engine.enhance_apps_database_with_github(enhancement_progress))
                    if success:
                        st.success("✅ GitHub enhancement complete!")
                        st.rerun()
                    else:
                        st.error("❌ GitHub enhancement failed - continuing with cached data")
        
        with col3:
            # Sort options
            sort_options = {
                'Total Stars ⭐': 'total_stars',
                'Pinokio Stars 🍴': 'pinokio_stars', 
                'Original Stars 🌟': 'original_stars',
                'Quality Score 💯': 'quality_score',
                'Recently Updated 📅': 'recently_updated',
                'Category 📂': 'category',
                'Name A-Z 🔤': 'name'
            }
            sort_by = st.selectbox("🔄 Sort By", list(sort_options.keys()))
            selected_sort = sort_options[sort_by]
    
    # Enhanced filters
    with st.expander("🎛️ Advanced Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Category filter
            available_apps = st.session_state.engine.get_enhanced_apps_with_sorting(selected_sort)
            categories = list(set([app.get('category', 'OTHER') for app in available_apps if app.get('category')]))
            category_filter = st.selectbox("📂 Category Filter", ['All'] + sorted(categories))
        
        with col2:
            # Quality filter
            min_quality = st.slider("💯 Minimum Quality Score", 0, 100, 0)
            
        with col3:
            # Stars filter
            min_stars = st.number_input("⭐ Minimum Total Stars", min_value=0, value=0)
    
    # Get enhanced apps with filters
    try:
        filtered_apps = st.session_state.engine.search_apps_enhanced(
            search_term, category_filter, None, selected_sort
        )
        
        # Apply additional filters
        if min_quality > 0:
            filtered_apps = [app for app in filtered_apps if app.get('quality_score', 0) >= min_quality]
        
        if min_stars > 0:
            filtered_apps = [app for app in filtered_apps if app.get('total_stars', 0) >= min_stars]
            
    except Exception as e:
        st.error(f"Search failed: {e}")
        filtered_apps = st.session_state.engine.list_available_apps()[:20]
    
    # Enhanced statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_available = len(st.session_state.engine.list_available_apps())
        st.metric("📱 Total Apps", total_available)
    
    with col2:
        showing_count = len(filtered_apps)
        st.metric("👁️ Showing", showing_count)
    
    with col3:
        if filtered_apps:
            avg_stars = sum(app.get('total_stars', 0) for app in filtered_apps) / len(filtered_apps)
            st.metric("⭐ Avg Stars", f"{avg_stars:.1f}")
        else:
            st.metric("⭐ Avg Stars", "0")
    
    with col4:
        enhanced_count = sum(1 for app in filtered_apps if app.get('pinokio_stars', 0) > 0)
        st.metric("🌟 GitHub Enhanced", enhanced_count)
    
    # Revolutionary Split-Screen Layout
    col_controls, col_terminal = st.columns([1.2, 0.8])
    
    with col_controls:
        st.markdown("### 🎮 Revolutionary App Cards")
        
        # Enhanced app cards with GitHub data
        for app in filtered_apps[:12]:  # Show top 12 apps
            display_revolutionary_app_card(app)
    
    with col_terminal:
        # Enhanced Revolutionary Terminal
        st.markdown("### 🖥️ Live Operations Monitor")
        display_revolutionary_terminal()
        
        # GitHub rate limit info
        try:
            rate_limit = st.session_state.engine.github.get_rate_limit_status()
            if 'error' not in rate_limit:
                core_limit = rate_limit.get('rate', {})
                remaining = core_limit.get('remaining', 'Unknown')
                limit = core_limit.get('limit', 'Unknown')
                reset_time = core_limit.get('reset', 0)
                
                if remaining != 'Unknown':
                    st.info(f"🐙 GitHub API: {remaining}/{limit} requests remaining")
        except:
            pass

def display_revolutionary_app_card(app: Dict[str, Any]):
    """Display revolutionary app card with GitHub stars and enhanced info - MODULE 4"""
    app_name = app.get('name', app.get('title', 'Unknown'))
    
    # Create enhanced app card with glassmorphism styling
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(0, 255, 159, 0.1), rgba(0, 212, 255, 0.05));
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 255, 159, 0.3);
        border-radius: 20px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 8px 32px rgba(0, 255, 159, 0.2);
    ">
    """, unsafe_allow_html=True)
    
    # App header with stars
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # App title with enhanced styling
        st.markdown(f"""
        <div style="margin-bottom: 10px;">
            <h3 style="color: #00ff9f; margin: 0; text-shadow: 0 0 10px rgba(0, 255, 159, 0.3);">
                📱 {app_name}
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Revolutionary star display
        pinokio_stars = app.get('pinokio_stars', 0)
        original_stars = app.get('original_stars', 0)
        total_stars = app.get('total_stars', 0)
        quality_score = app.get('quality_score', 0)
        
        if total_stars > 0:
            st.markdown(f"""
            <div style="margin: 10px 0;">
                <span style="color: #00d4ff;">⭐ Total: <strong>{total_stars:,}</strong></span>
                <span style="color: #666; margin: 0 10px;">|</span>
                <span style="color: #00ff9f;">🍴 Pinokio: {pinokio_stars}</span>
                <span style="color: #666; margin: 0 10px;">|</span>
                <span style="color: #ff6b9d;">🌟 Original: {original_stars}</span>
                <span style="color: #666; margin: 0 10px;">|</span>
                <span style="color: #ffaa00;">💯 Quality: {quality_score:.0f}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Category and tags
        category = app.get('category', 'OTHER')
        enhanced_tags = app.get('enhanced_tags', [])
        
        # Category with icon
        category_icons = {
            'IMAGE': '🖼️', 'AUDIO': '🎵', 'VIDEO': '🎬', 
            'LLM': '🧠', 'UTILITY': '🔧', 'OTHER': '📦'
        }
        category_icon = category_icons.get(category, '📦')
        
        st.markdown(f"**{category_icon} Category:** {category}")
        
        # Enhanced tags display
        if enhanced_tags:
            tags_html = ""
            for tag in enhanced_tags[:8]:  # Show first 8 tags
                tag_color = get_tag_color(tag)
                tags_html += f'<span style="background: {tag_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin: 2px;">{tag}</span> '
            
            st.markdown(f"**🏷️ Tags:** {tags_html}", unsafe_allow_html=True)
        
        # Description with better formatting
        description = app.get('description', 'No description available')
        if len(description) > 200:
            st.markdown(f"**📝 Description:** {description[:200]}...")
            with st.expander("Read more"):
                st.write(description)
        else:
            st.markdown(f"**📝 Description:** {description}")
        
        # Repository information with GitHub data
        repo_url = app.get('repo_url', app.get('clone_url', ''))
        original_url = app.get('original_url', '')
        
        if repo_url:
            st.markdown(f"**🐙 Pinokio Repo:** [GitHub]({repo_url})")
        
        if original_url:
            st.markdown(f"**🌟 Original Repo:** [GitHub]({original_url})")
        
        # Last updated info
        last_updated = app.get('pinokio_last_updated', '')
        if last_updated:
            try:
                from datetime import datetime
                updated_date = datetime.fromisoformat(last_updated.replace('Z', ''))
                days_ago = (datetime.now() - updated_date.replace(tzinfo=None)).days
                st.markdown(f"**📅 Last Updated:** {days_ago} days ago")
            except:
                pass
    
    with col2:
        # Enhanced status and actions
        installed_apps = st.session_state.engine.list_installed_apps()
        is_installed = app_name in installed_apps
        is_running = st.session_state.engine.is_app_running(app_name) if is_installed else False
        
        # Status display with enhanced styling
        if is_running:
            st.markdown('''
            <div style="text-align: center; padding: 10px; background: rgba(0, 255, 159, 0.2); border-radius: 15px; margin: 10px 0;">
                <div style="font-size: 24px;">🟢</div>
                <div style="color: #00ff9f; font-weight: bold;">RUNNING</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Get app URLs with enhanced display
            urls = st.session_state.engine.get_app_urls(app_name)
            if urls:
                st.markdown(f"""
                <div style="text-align: center; margin: 10px 0;">
                    <a href="{urls[0]}" target="_blank" style="
                        background: linear-gradient(45deg, #00ff9f, #00d4ff);
                        color: black;
                        padding: 8px 16px;
                        border-radius: 20px;
                        text-decoration: none;
                        font-weight: bold;
                        display: inline-block;
                        box-shadow: 0 4px 15px rgba(0, 255, 159, 0.3);
                    ">🌐 Open App</a>
                </div>
                """, unsafe_allow_html=True)
            
            # Action buttons
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(f"⏹️ Stop", key=f"stop_{app_name}_card"):
                    add_raw_output(app_name, f"🛑 STOP REQUEST: {app_name}", "warning")
                    stop_app_sync(app_name)
                    st.rerun()
            
            with col_b:
                if st.button(f"🔗 Share", key=f"ngrok_{app_name}_card"):
                    create_ngrok_tunnel_with_feedback(app_name)
                    
        elif is_installed:
            st.markdown('''
            <div style="text-align: center; padding: 10px; background: rgba(0, 212, 255, 0.2); border-radius: 15px; margin: 10px 0;">
                <div style="font-size: 24px;">📦</div>
                <div style="color: #00d4ff; font-weight: bold;">INSTALLED</div>
            </div>
            ''', unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(f"▶️ Launch", key=f"run_{app_name}_card"):
                    run_app_with_enhanced_feedback(app_name)
                    st.rerun()
            
            with col_b:
                if st.button(f"🗑️ Remove", key=f"uninstall_{app_name}_card"):
                    uninstall_app_with_feedback(app_name)
                    st.rerun()
        
        else:
            st.markdown('''
            <div style="text-align: center; padding: 10px; background: rgba(255, 255, 255, 0.1); border-radius: 15px; margin: 10px 0;">
                <div style="font-size: 24px;">⬇️</div>
                <div style="color: #ffffff; font-weight: bold;">AVAILABLE</div>
            </div>
            ''', unsafe_allow_html=True)
            
            if st.button(f"📥 Install with Real-time Feedback", key=f"install_{app_name}_card", use_container_width=True):
                install_app_with_enhanced_feedback(app_name)
                st.rerun()
        
        # Quality indicators
        if quality_score > 80:
            st.markdown('<div style="text-align: center; color: #00ff9f;">🏆 High Quality</div>', unsafe_allow_html=True)
        elif quality_score > 60:
            st.markdown('<div style="text-align: center; color: #00d4ff;">✅ Good Quality</div>', unsafe_allow_html=True)
        
        # Platform compatibility
        if is_app_compatible_with_platform(app):
            st.markdown('<div style="text-align: center; color: #00ff9f;">✅ Compatible</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align: center; color: #ffaa00;">⚠️ May have issues</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Show enhanced statistics
    show_enhanced_statistics(filtered_apps)
    
    # Revolutionary terminal at bottom with full width
    st.markdown("---")
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