#!/usr/bin/env python3
"""
PinokiOS Streamlit App - Beautiful & Feature-Rich Interface
Replicates Pinokio's functionality with modern web UI
"""

import streamlit as st
import time
import threading
from pathlib import Path
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import our modules
from pinokios.database import PINOKIO_APPS, search_apps, get_stats
from pinokios.engine import PinokioEngine

# Page config
st.set_page_config(
    page_title="🔥 PinokiOS - 267 Real Apps",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    .stApp > header {
        background-color: transparent;
    }
    
    .app-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .installed-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .running-card {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        color: #333;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        color: white;
        margin: 0.5rem 0;
    }
    
    .success-message {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        margin: 1rem 0;
    }
    
    .error-message {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        margin: 1rem 0;
    }
    
    .log-container {
        background: #1e1e1e;
        padding: 1rem;
        border-radius: 8px;
        color: #00ff00;
        font-family: 'Courier New', monospace;
        max-height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'engine' not in st.session_state:
    st.session_state.engine = PinokioEngine()

if 'selected_app' not in st.session_state:
    st.session_state.selected_app = None

if 'installation_progress' not in st.session_state:
    st.session_state.installation_progress = []

if 'current_page' not in st.session_state:
    st.session_state.current_page = "🔍 Discover Apps"

# Helper functions
def install_app(app_info):
    """Install an app with progress tracking"""
    with st.spinner(f"Installing {app_info['name']}..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        progress_messages = []
        
        def progress_callback(message):
            progress_messages.append(message)
            status_text.text(message)
            progress_bar.progress(len(progress_messages) / 10)  # Rough progress estimate
        
        success, message = st.session_state.engine.install_app(app_info, progress_callback)
        
        progress_bar.progress(1.0)
        
        if success:
            st.success(message)
            time.sleep(2)
            st.rerun()
        else:
            st.error(message)

def show_app_logs(app_name):
    """Show logs for an app"""
    st.markdown(f"### 📋 Logs for {app_name}")
    
    logs = st.session_state.engine.get_app_logs(app_name, max_lines=50)
    
    if logs:
        log_text = '\n'.join(logs)
        st.markdown(f"""
        <div class="log-container">
            <pre>{log_text}</pre>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No logs available for this app")

# Sidebar Navigation
st.sidebar.markdown("# 🔥 PinokiOS")
st.sidebar.markdown("*Real Pinokio App Manager*")

# Navigation
pages = [
    "🔍 Discover Apps",
    "📦 Installed Apps", 
    "🚀 Running Apps",
    "📊 System Status",
    "⚙️ Settings"
]

selected_page = st.sidebar.radio("Navigation", pages, index=pages.index(st.session_state.current_page))
st.session_state.current_page = selected_page

# System stats in sidebar
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    
    stats = get_stats()
    installed_apps = st.session_state.engine.get_installed_apps()
    running_apps = [app for app in installed_apps if st.session_state.engine.is_running(app['app_name'])]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Available", stats['total_apps'])
        st.metric("Installed", len(installed_apps))
    with col2:
        st.metric("Running", len(running_apps))
        st.metric("Categories", len(stats['categories']))

# Main content based on selected page
if selected_page == "🔍 Discover Apps":
    st.title("🔍 Discover Pinokio Apps")
    st.markdown("*Browse and install from 267 verified Pinokio applications*")
    
    # Get stats for main content area
    if 'stats' not in locals():
        stats = get_stats()
    
    # Search and filters
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search apps...", placeholder="Search by name, description, or tags")
    
    with col2:
        categories = ['ALL'] + list(stats['categories'])
        selected_category = st.selectbox("📂 Category", categories)
    
    with col3:
        min_stars = st.slider("⭐ Min Stars", 0, 100, 0)
    
    # Advanced filters in expander
    with st.expander("🔧 Advanced Filters"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            authors = ['ALL'] + stats['authors']
            selected_author = st.selectbox("👤 Author", authors)
        
        with col2:
            show_installed = st.checkbox("Show Installed", value=True)
            show_uninstalled = st.checkbox("Show Uninstalled", value=True)
        
        with col3:
            sort_by = st.selectbox("📊 Sort by", ["Name", "Stars", "Last Updated"])
    
    # Search apps
    search_params = {
        'query': search_term if search_term else None,
        'category': selected_category if selected_category != 'ALL' else None,
        'min_stars': min_stars,
        'author': selected_author if selected_author != 'ALL' else None
    }
    
    apps = search_apps(**{k: v for k, v in search_params.items() if v is not None})
    
    # Filter by installation status
    if not show_installed:
        apps = [app for app in apps if not st.session_state.engine.is_installed(app['name'])]
    if not show_uninstalled:
        apps = [app for app in apps if st.session_state.engine.is_installed(app['name'])]
    
    # Sort apps
    if sort_by == "Stars":
        apps = sorted(apps, key=lambda x: x['stars'], reverse=True)
    elif sort_by == "Last Updated":
        apps = sorted(apps, key=lambda x: x.get('last_update', ''), reverse=True)
    else:  # Name
        apps = sorted(apps, key=lambda x: x['name'])
    
    st.markdown(f"### Found {len(apps)} apps")
    
    # Display apps in cards
    for app in apps[:20]:  # Limit to 20 for performance
        is_installed = st.session_state.engine.is_installed(app['name'])
        is_running = st.session_state.engine.is_running(app['name']) if is_installed else False
        
        card_class = "installed-card" if is_installed else "app-card"
        
        with st.container():
            st.markdown(f"""
            <div class="{card_class}">
                <h3>🎯 {app['name']}</h3>
                <p><strong>Category:</strong> {app['category']} | <strong>Author:</strong> {app['author']} | <strong>⭐ Stars:</strong> {app['stars']}</p>
                <p>{app['description'][:200]}{'...' if len(app['description']) > 200 else ''}</p>
                <p><strong>Tags:</strong> {', '.join(app['tags'][:5])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            
            with col1:
                if st.button(f"📋 Details", key=f"details_{app['name']}"):
                    st.session_state.selected_app = app
            
            with col2:
                if is_installed:
                    if st.button(f"🗑️ Uninstall", key=f"uninstall_{app['name']}"):
                        success, message = st.session_state.engine.uninstall_app(app['name'])
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    if st.button(f"📦 Install", key=f"install_{app['name']}"):
                        install_app(app)
            
            with col3:
                if is_installed:
                    if is_running:
                        if st.button(f"⏹️ Stop", key=f"stop_{app['name']}"):
                            success, message = st.session_state.engine.stop_app(app['name'])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        if st.button(f"🚀 Run", key=f"run_{app['name']}"):
                            success, message = st.session_state.engine.run_app(app['name'])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
            
            with col4:
                if is_running:
                    st.markdown(f"<span style='color: #00ff00; font-weight: bold;'>🟢 RUNNING</span>", unsafe_allow_html=True)
                elif is_installed:
                    st.markdown(f"<span style='color: #ffa500; font-weight: bold;'>🟡 INSTALLED</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color: #666; font-weight: bold;'>⚪ AVAILABLE</span>", unsafe_allow_html=True)
            
            st.markdown("---")

elif selected_page == "📦 Installed Apps":
    st.title("📦 Installed Apps")
    st.markdown("*Manage your installed Pinokio applications*")
    
    installed_apps = st.session_state.engine.get_installed_apps()
    
    if not installed_apps:
        st.info("🤔 No apps installed yet. Go to 'Discover Apps' to install some!")
    else:
        st.markdown(f"### {len(installed_apps)} apps installed")
        
        for app in installed_apps:
            is_running = app.get('running', False)
            
            with st.container():
                st.markdown(f"""
                <div class="{'running-card' if is_running else 'installed-card'}">
                    <h3>{'🚀' if is_running else '📦'} {app['name']}</h3>
                    <p><strong>Category:</strong> {app['category']} | <strong>Author:</strong> {app['author']}</p>
                    <p>{app['description'][:150]}{'...' if len(app['description']) > 150 else ''}</p>
                    <p><strong>Installed:</strong> {time.strftime('%Y-%m-%d %H:%M', time.localtime(app.get('install_date', 0)))}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
                
                with col1:
                    if is_running:
                        if st.button(f"⏹️ Stop", key=f"stop_installed_{app['name']}"):
                            success, message = st.session_state.engine.stop_app(app['name'])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        if st.button(f"🚀 Run", key=f"run_installed_{app['name']}"):
                            success, message = st.session_state.engine.run_app(app['name'])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                
                with col2:
                    if st.button(f"📋 Logs", key=f"logs_{app['name']}"):
                        show_app_logs(app['name'])
                
                with col3:
                    if st.button(f"🗑️ Uninstall", key=f"uninstall_installed_{app['name']}"):
                        success, message = st.session_state.engine.uninstall_app(app['name'])
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                with col4:
                    if is_running:
                        st.markdown("<span style='color: #00ff00; font-weight: bold;'>🟢 RUNNING</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color: #ffa500; font-weight: bold;'>🟡 STOPPED</span>", unsafe_allow_html=True)
                
                st.markdown("---")

elif selected_page == "🚀 Running Apps":
    st.title("🚀 Running Apps")
    st.markdown("*Monitor and control your running applications*")
    
    installed_apps = st.session_state.engine.get_installed_apps()
    running_apps = [app for app in installed_apps if st.session_state.engine.is_running(app['app_name'])]
    
    if not running_apps:
        st.info("😴 No apps currently running. Start some from 'Installed Apps'!")
    else:
        st.markdown(f"### {len(running_apps)} apps running")
        
        for app in running_apps:
            with st.container():
                st.markdown(f"""
                <div class="running-card">
                    <h3>🚀 {app['name']}</h3>
                    <p><strong>Status:</strong> <span style='color: #00ff00; font-weight: bold;'>🟢 RUNNING</span></p>
                    <p><strong>Category:</strong> {app['category']} | <strong>Author:</strong> {app['author']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([1, 1, 2])
                
                with col1:
                    if st.button(f"⏹️ Stop", key=f"stop_running_{app['name']}"):
                        success, message = st.session_state.engine.stop_app(app['name'])
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                with col2:
                    if st.button(f"🔄 Restart", key=f"restart_{app['name']}"):
                        # Stop then start
                        st.session_state.engine.stop_app(app['name'])
                        time.sleep(2)
                        success, message = st.session_state.engine.run_app(app['name'])
                        if success:
                            st.success(f"✅ {app['name']} restarted")
                            st.rerun()
                        else:
                            st.error(message)
                
                # Live logs
                st.markdown("**📋 Live Logs:**")
                logs = st.session_state.engine.get_app_logs(app['app_name'], max_lines=10)
                
                if logs:
                    log_text = '\n'.join(logs[-10:])  # Last 10 lines
                    st.markdown(f"""
                    <div class="log-container">
                        <pre>{log_text}</pre>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("No logs available yet...")
                
                st.markdown("---")

elif selected_page == "📊 System Status":
    st.title("📊 System Status")
    st.markdown("*Monitor system resources and app statistics*")
    
    # System info
    system_info = st.session_state.engine.get_system_info()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{system_info['installed_apps']}</h3>
            <p>Installed Apps</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{system_info['running_apps']}</h3>
            <p>Running Apps</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{system_info['total_disk_usage']['total_gb']} GB</h3>
            <p>Disk Usage</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{system_info['cpu_usage']:.1f}%</h3>
            <p>CPU Usage</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Memory usage
    st.markdown("### 💾 Memory Usage")
    memory = system_info['memory_usage']
    memory_percent = (memory['used'] / memory['total']) * 100
    
    st.progress(memory_percent / 100)
    st.markdown(f"**Used:** {memory['used'] // (1024**3)} GB / {memory['total'] // (1024**3)} GB ({memory_percent:.1f}%)")
    
    # Directory info
    st.markdown("### 📁 Directory Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Apps Directory:**\n{system_info['apps_directory']}")
    
    with col2:
        st.info(f"**Logs Directory:**\n{system_info['logs_directory']}")
    
    # Database stats
    st.markdown("### 📊 Database Statistics")
    db_stats = get_stats()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.json({
            "Total Apps": db_stats['total_apps'],
            "Categories": len(db_stats['categories']),
            "Authors": len(db_stats['authors']),
            "Total Stars": db_stats['total_stars']
        })
    
    with col2:
        st.markdown("**Top Categories:**")
        for category, count in list(db_stats['categories'].items())[:10]:
            st.markdown(f"- **{category}:** {count} apps")

elif selected_page == "⚙️ Settings":
    st.title("⚙️ Settings")
    st.markdown("*Configure PinokiOS behavior and preferences*")
    
    # App directory settings
    st.markdown("### 📁 Directory Settings")
    current_dir = str(st.session_state.engine.base_dir)
    st.info(f"**Current Apps Directory:** {current_dir}")
    
    # Auto-start settings
    st.markdown("### 🚀 Auto-Start Settings")
    auto_start_apps = st.multiselect(
        "Select apps to auto-start",
        options=[app['app_name'] for app in st.session_state.engine.get_installed_apps()],
        help="These apps will start automatically when PinokiOS launches"
    )
    
    # Log settings
    st.markdown("### 📋 Log Settings")
    max_log_lines = st.slider("Maximum log lines per app", 50, 1000, 200)
    auto_clear_logs = st.checkbox("Auto-clear logs after 7 days")
    
    # Update settings
    st.markdown("### 🔄 Update Settings")
    auto_update_db = st.checkbox("Auto-update app database")
    check_updates = st.checkbox("Check for app updates")
    
    # Export/Import
    st.markdown("### 📤 Export/Import")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Export Installed Apps List"):
            installed_apps = st.session_state.engine.get_installed_apps()
            app_list = [{"name": app["app_name"], "repo": app.get("clone_url", "")} for app in installed_apps]
            
            st.download_button(
                "💾 Download Apps List",
                data=json.dumps(app_list, indent=2),
                file_name="pinokios_installed_apps.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_file = st.file_uploader("📥 Import Apps List", type=['json'])
        if uploaded_file and st.button("Import Apps"):
            try:
                app_list = json.loads(uploaded_file.read())
                st.success(f"Ready to install {len(app_list)} apps from import file")
            except Exception as e:
                st.error(f"Error reading import file: {e}")

# Auto-refresh for running apps
if selected_page == "🚀 Running Apps":
    time.sleep(1)
    st.rerun()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**🔥 PinokiOS v1.0**")
st.sidebar.markdown("*Real Pinokio App Manager*")
st.sidebar.markdown("267 verified apps available")
