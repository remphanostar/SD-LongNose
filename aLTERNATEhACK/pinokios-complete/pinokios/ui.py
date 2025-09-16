#!/usr/bin/env python3
"""
Enhanced Streamlit UI - Compatible with Improved Database Schema
Automatically detects and adapts to database format changes
"""

import streamlit as st
import json
import os
import sys
import time
import threading
from pathlib import Path
import queue
from datetime import datetime

# Add current directory to Python path
sys.path.append('.')

# Import enhanced components
try:
    from .core import (
        EnhancedPinokioDatabase, 
        EnhancedPinokioInstaller
    )
    from .database import (
        get_all_apps,
        search_apps,
        get_stats
    )
    SYSTEM_READY = True
except Exception as e:
    st.error(f"Failed to import enhanced components: {e}")
    SYSTEM_READY = False

# Page config
st.set_page_config(
    page_title="PinokiOS Enhanced - Improved Database Support",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'log_buffer' not in st.session_state:
    st.session_state.log_buffer = []
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False
if 'current_database' not in st.session_state:
    st.session_state.current_database = None

# Initialize enhanced system
@st.cache_resource
def init_enhanced_system():
    if not SYSTEM_READY:
        return None, None
    
    database = EnhancedPinokioDatabase()
    installer = EnhancedPinokioInstaller()
    
    return database, installer

database, installer = init_enhanced_system()

# Start background monitoring
def start_monitoring():
    def monitor():
        while st.session_state.monitoring_active:
            if installer:
                logs = installer.get_log_stream()
                st.session_state.log_buffer.extend(logs)
                if len(st.session_state.log_buffer) > 500:
                    st.session_state.log_buffer = st.session_state.log_buffer[-500:]
            time.sleep(1)
    
    if SYSTEM_READY and not st.session_state.monitoring_active:
        st.session_state.monitoring_active = True
        threading.Thread(target=monitor, daemon=True).start()

start_monitoring()

# Header
st.title("🔥 PinokiOS Enhanced - Database Compatibility Layer")
st.markdown("**Supports Both Legacy and Improved Database Schemas**")

# System status
if SYSTEM_READY and database:
    col1, col2, col3, col4 = st.columns(4)
    
    stats = database.get_stats()
    
    with col1:
        st.metric("System", "🟢 ENHANCED")
    with col2:
        st.metric("Total Apps", stats.get('total_apps', 0))
    with col3:
        st.metric("Database Version", stats.get('db_version', 'Legacy'))
    with col4:
        st.metric("Verified Apps", stats.get('verified_count', 0))
    
    # Database info
    if stats.get('last_update'):
        st.info(f"📅 Database last updated: {stats.get('last_update')}")
else:
    st.error("🔴 Enhanced system not ready")

# Sidebar
with st.sidebar:
    st.title("🎛️ Enhanced Control Panel")
    
    page = st.radio("Choose Page:", [
        "🔍 Enhanced Discovery",
        "📊 Database Analytics", 
        "⚙️ Configuration",
        "🛠️ Debug Console"
    ])
    
    st.markdown("---")
    st.markdown("### 📈 Database Stats")
    
    if database:
        stats = database.get_stats()
        st.metric("Total Stars", f"{stats.get('total_stars', 0):,}")
        st.metric("Avg Stars", f"{stats.get('avg_stars', 0):.1f}")

# Main content based on selected page
if page == "🔍 Enhanced Discovery":
    st.header("🔍 Enhanced App Discovery")
    
    if not database:
        st.error("Database not loaded")
        st.stop()
    
    # Enhanced search interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search apps", placeholder="Enter app name, description, or tags...")
    
    with col2:
        verified_only = st.checkbox("✅ Verified only", value=True)
    
    # Advanced filters in expandable section
    with st.expander("🔧 Advanced Filters"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            categories = database.get_categories()
            selected_category = st.selectbox("Category", ["All"] + categories)
            if selected_category == "All":
                selected_category = ""
        
        with col2:
            authors = database.get_authors()
            selected_author = st.selectbox("Author", ["All"] + authors)
            if selected_author == "All":
                selected_author = ""
        
        with col3:
            min_stars = st.number_input("Minimum Stars", min_value=0, value=0, step=1)
        
        # Enhanced filters for new schema
        col4, col5 = st.columns(2)
        with col4:
            min_vram = st.text_input("Min VRAM (e.g., 6GB)", placeholder="Optional")
        with col5:
            min_ram = st.text_input("Min RAM (e.g., 16GB)", placeholder="Optional")
    
    # Search and display results
    if st.button("🔍 Search Apps") or search_query:
        with st.spinner("Searching apps..."):
            results = database.search_apps(
                query=search_query,
                category=selected_category,
                author=selected_author,
                verified_only=verified_only,
                min_stars=min_stars,
                min_vram=min_vram,
                min_ram=min_ram
            )
        
        st.write(f"Found **{len(results)}** apps")
        
        # Display results
        for app in results[:20]:  # Limit to 20 results
            with st.expander(f"⭐ {database.get_app_field(app, 'name', 'Unknown')} ({database.get_app_field(app, 'stars', 0)} stars)"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Description:** {database.get_app_field(app, 'description', 'No description')}")
                    st.write(f"**Author:** {database.get_app_field(app, 'author', 'Unknown')}")
                    st.write(f"**Category:** {database.get_app_field(app, 'category', 'Other')}")
                    
                    # Enhanced fields if available
                    min_vram = database.get_app_field(app, 'min_vram')
                    min_ram = database.get_app_field(app, 'min_ram')
                    if min_vram or min_ram:
                        st.write(f"**Requirements:** VRAM: {min_vram or 'N/A'}, RAM: {min_ram or 'N/A'}")
                    
                    tags = database.get_app_field(app, 'tags', [])
                    if tags:
                        st.write(f"**Tags:** {', '.join(tags)}")
                
                with col2:
                    verified = database.get_app_field(app, 'verified', False)
                    install_verified = database.get_app_field(app, 'install_verified', False)
                    
                    if verified:
                        st.success("✅ Verified")
                    if install_verified:
                        st.success("🔧 Install Tested")
                    
                    repo_url = database.get_app_field(app, 'repo_url', '')
                    if repo_url:
                        st.link_button("GitHub", repo_url)
                    
                    if st.button(f"📦 Install", key=f"install_{app['id']}"):
                        if installer:
                            with st.spinner(f"Installing {database.get_app_field(app, 'name')}..."):
                                success = installer.install_app_enhanced(app['id'])
                                if success:
                                    st.success("Installation completed!")
                                else:
                                    st.error("Installation failed!")
                        else:
                            st.error("Installer not available")

elif page == "📊 Database Analytics":
    st.header("📊 Database Analytics")
    
    if not database:
        st.error("Database not loaded")
        st.stop()
    
    stats = database.get_stats()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Apps", stats['total_apps'])
    with col2:
        st.metric("Total Stars", f"{stats['total_stars']:,}")
    with col3:
        st.metric("Verified Apps", stats['verified_count'])
    with col4:
        st.metric("Install Tested", stats['install_verified_count'])
    
    # Categories breakdown
    st.subheader("📋 Categories")
    categories = stats.get('categories', {})
    if categories:
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            st.write(f"**{category}:** {count} apps")
    
    # Top authors
    st.subheader("👥 Top Authors")
    authors = stats.get('authors', {})
    if authors:
        top_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]
        for author, count in top_authors:
            st.write(f"**{author}:** {count} apps")

elif page == "⚙️ Configuration":
    st.header("⚙️ Configuration")
    
    st.subheader("🗄️ Database Configuration")
    
    # Database module selection
    current_module = st.text_input(
        "Database Module", 
        value="complete_real_pinokio_database",
        help="Name of the Python module containing PINOKIO_APPS"
    )
    
    if st.button("🔄 Reload Database"):
        try:
            # Clear cache and reload
            st.cache_resource.clear()
            st.session_state.current_database = None
            
            new_database = EnhancedPinokioDatabase(current_module)
            stats = new_database.get_stats()
            
            st.success(f"✅ Reloaded {stats['total_apps']} apps from {current_module}")
            if stats.get('db_version'):
                st.info(f"Database version: {stats['db_version']}")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to reload database: {e}")
    
    # Database schema info
    if database:
        st.subheader("📋 Current Schema")
        sample_app = next(iter(database.apps_data.values()), {})
        if sample_app:
            st.json({k: f"<{type(v).__name__}>" for k, v in sample_app.items()})

elif page == "🛠️ Debug Console":
    st.header("🛠️ Debug Console")
    
    # Live logs
    st.subheader("📜 Live Logs")
    
    if st.session_state.log_buffer:
        log_container = st.container()
        with log_container:
            for log in st.session_state.log_buffer[-20:]:  # Show last 20 logs
                timestamp = log.get('timestamp', '')
                app_name = log.get('app_name', '')
                message = log.get('message', '')
                level = log.get('level', 'INFO')
                
                if level == 'ERROR':
                    st.error(f"[{timestamp}] [{app_name}] {message}")
                elif level == 'WARNING':
                    st.warning(f"[{timestamp}] [{app_name}] {message}")
                else:
                    st.info(f"[{timestamp}] [{app_name}] {message}")
    else:
        st.info("No logs available")
    
    # System info
    st.subheader("🖥️ System Information")
    st.write(f"**Python Version:** {sys.version}")
    st.write(f"**Working Directory:** {os.getcwd()}")
    st.write(f"**System Ready:** {SYSTEM_READY}")
    
    if database:
        st.write(f"**Database Module:** {database.database_module_name}")
        st.write(f"**Database Version:** {database.db_version or 'Legacy'}")
        st.write(f"**Last Update:** {database.last_update or 'Unknown'}")

# Auto-refresh for live monitoring
if st.session_state.monitoring_active:
    time.sleep(2)
    st.rerun()
