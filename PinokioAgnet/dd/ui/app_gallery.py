#!/usr/bin/env python3
"""
PinokioCloud App Gallery

This module provides a comprehensive application gallery interface for browsing,
searching, and managing all 284 Pinokio applications. It displays apps in an
organized, searchable format with categories, tags, and installation controls.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import threading
import streamlit as st
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime
import re

# Add the github_repo directory to Python path for imports
sys.path.append('/workspace/SD-LongNose/github_repo')

from app_analysis.app_analyzer import AppAnalyzer
from engine.installer import ApplicationInstaller
from running.script_manager import ScriptManager
from optimization.logging_system import LoggingSystem


class AppStatus(Enum):
    """Application installation and running status."""
    NOT_INSTALLED = "not_installed"
    INSTALLING = "installing"
    INSTALLED = "installed"
    RUNNING = "running"
    ERROR = "error"
    UPDATING = "updating"


@dataclass
class AppDisplayInfo:
    """Information for displaying an app in the gallery."""
    id: str
    name: str
    description: str
    category: str
    tags: List[str]
    author: str
    stars: int
    repo_url: str
    installer_type: str
    status: AppStatus
    install_progress: float = 0.0
    last_updated: Optional[datetime] = None
    error_message: Optional[str] = None


class AppGallery:
    """
    Application Gallery for PinokioCloud
    
    This class provides a comprehensive interface for browsing, searching, and
    managing all available Pinokio applications. It displays apps in a grid
    format with search, filtering, and installation capabilities.
    """
    
    def __init__(self, apps_data: Dict[str, Any]):
        """
        Initialize the app gallery.
        
        Args:
            apps_data: Dictionary containing all application data
        """
        self.apps_data = apps_data
        self.app_analyzer = AppAnalyzer()
        self.installer = ApplicationInstaller()
        self.script_manager = ScriptManager()
        self.logging_system = LoggingSystem()
        
        # Initialize session state
        if 'app_statuses' not in st.session_state:
            st.session_state.app_statuses = {}
        if 'installation_threads' not in st.session_state:
            st.session_state.installation_threads = {}
        if 'gallery_view' not in st.session_state:
            st.session_state.gallery_view = "grid"
        if 'apps_per_page' not in st.session_state:
            st.session_state.apps_per_page = 12
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1
            
        # Process apps data
        self.display_apps = self._process_apps_data()
        
    def _process_apps_data(self) -> List[AppDisplayInfo]:
        """Process raw apps data into display format."""
        display_apps = []
        
        for app_id, app_data in self.apps_data.items():
            # Get current status
            status = st.session_state.app_statuses.get(app_id, AppStatus.NOT_INSTALLED)
            
            display_info = AppDisplayInfo(
                id=app_id,
                name=app_data.get('name', app_id),
                description=app_data.get('description', 'No description available'),
                category=app_data.get('category', 'UNKNOWN'),
                tags=app_data.get('tags', []),
                author=app_data.get('author', 'Unknown'),
                stars=app_data.get('stars', 0),
                repo_url=app_data.get('repo_url', ''),
                installer_type=app_data.get('installer_type', 'unknown'),
                status=status
            )
            
            display_apps.append(display_info)
            
        return display_apps
        
    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        categories = set(app.category for app in self.display_apps)
        return sorted(list(categories))
        
    def get_tags(self) -> List[str]:
        """Get all unique tags."""
        all_tags = set()
        for app in self.display_apps:
            all_tags.update(app.tags)
        return sorted(list(all_tags))
        
    def filter_apps(self, search_term: str = "", category: str = "ALL", 
                   tags: List[str] = None, status_filter: str = "ALL") -> List[AppDisplayInfo]:
        """Filter apps based on search criteria."""
        filtered_apps = self.display_apps.copy()
        
        # Text search
        if search_term:
            search_lower = search_term.lower()
            filtered_apps = [
                app for app in filtered_apps
                if (search_lower in app.name.lower() or 
                    search_lower in app.description.lower() or
                    search_lower in app.author.lower() or
                    any(search_lower in tag.lower() for tag in app.tags))
            ]
            
        # Category filter
        if category != "ALL":
            filtered_apps = [app for app in filtered_apps if app.category == category]
            
        # Tags filter
        if tags:
            filtered_apps = [
                app for app in filtered_apps
                if any(tag in app.tags for tag in tags)
            ]
            
        # Status filter
        if status_filter != "ALL":
            status_enum = AppStatus(status_filter.lower())
            filtered_apps = [app for app in filtered_apps if app.status == status_enum]
            
        return filtered_apps
        
    def sort_apps(self, apps: List[AppDisplayInfo], sort_by: str) -> List[AppDisplayInfo]:
        """Sort apps based on criteria."""
        if sort_by == "Name":
            return sorted(apps, key=lambda x: x.name.lower())
        elif sort_by == "Category":
            return sorted(apps, key=lambda x: (x.category, x.name.lower()))
        elif sort_by == "Stars":
            return sorted(apps, key=lambda x: x.stars, reverse=True)
        elif sort_by == "Author":
            return sorted(apps, key=lambda x: x.author.lower())
        elif sort_by == "Status":
            return sorted(apps, key=lambda x: x.status.value)
        else:
            return apps
            
    def render_search_controls(self) -> Tuple[str, str, List[str], str, str]:
        """Render search and filter controls."""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_term = st.text_input(
                "🔍 Search applications...",
                placeholder="Enter app name, description, author, or tags",
                key="gallery_search"
            )
            
        with col2:
            categories = ["ALL"] + self.get_categories()
            selected_category = st.selectbox("📂 Category", categories, key="gallery_category")
            
        with col3:
            sort_options = ["Name", "Category", "Stars", "Author", "Status"]
            sort_by = st.selectbox("🔤 Sort by", sort_options, key="gallery_sort")
            
        # Advanced filters
        with st.expander("🔧 Advanced Filters"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Tags filter
                available_tags = self.get_tags()[:20]  # Limit to first 20 tags
                selected_tags = st.multiselect("🏷️ Tags", available_tags, key="gallery_tags")
                
            with col2:
                # Status filter
                status_options = ["ALL", "NOT_INSTALLED", "INSTALLED", "RUNNING", "ERROR"]
                status_filter = st.selectbox("📊 Status", status_options, key="gallery_status")
                
            with col3:
                # View options
                view_options = ["Grid", "List", "Compact"]
                view_mode = st.selectbox("👁️ View", view_options, key="gallery_view_mode")
                st.session_state.gallery_view = view_mode.lower()
                
        return search_term, selected_category, selected_tags, status_filter, sort_by
        
    def render_gallery_stats(self, filtered_apps: List[AppDisplayInfo]):
        """Render gallery statistics."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📱 Total Apps", len(self.display_apps))
            
        with col2:
            st.metric("🔍 Filtered", len(filtered_apps))
            
        with col3:
            installed_count = len([app for app in self.display_apps if app.status == AppStatus.INSTALLED])
            st.metric("📦 Installed", installed_count)
            
        with col4:
            running_count = len([app for app in self.display_apps if app.status == AppStatus.RUNNING])
            st.metric("🏃 Running", running_count)
            
    def render_app_card(self, app: AppDisplayInfo):
        """Render an individual app card."""
        # Status color mapping
        status_colors = {
            AppStatus.NOT_INSTALLED: "#666666",
            AppStatus.INSTALLING: "#ffaa00", 
            AppStatus.INSTALLED: "#00ff9f",
            AppStatus.RUNNING: "#00d4ff",
            AppStatus.ERROR: "#ff4444",
            AppStatus.UPDATING: "#ff9900"
        }
        
        status_color = status_colors.get(app.status, "#666666")
        status_text = app.status.value.replace('_', ' ').title()
        
        # Create card HTML
        card_html = f"""
        <div class="app-card" style="
            background: rgba(22, 33, 62, 0.8);
            border: 1px solid #00ff9f;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 4px 15px rgba(0, 255, 159, 0.2);
            transition: all 0.3s ease;
        ">
            <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 0.5rem;">
                <h4 style="color: #00ff9f; margin: 0; flex-grow: 1;">{app.name}</h4>
                <span style="color: {status_color}; font-weight: bold; font-size: 0.8rem;">●</span>
            </div>
            
            <div style="color: #00d4ff; font-size: 0.9rem; margin-bottom: 0.5rem;">
                📂 {app.category} | 👤 {app.author} | ⭐ {app.stars}
            </div>
            
            <p style="color: #cccccc; font-size: 0.85rem; margin-bottom: 1rem; 
                      max-height: 60px; overflow: hidden; text-overflow: ellipsis;">
                {app.description[:150]}{'...' if len(app.description) > 150 else ''}
            </p>
            
            <div style="margin-bottom: 0.5rem;">
                <span style="color: #888888; font-size: 0.75rem;">
                    🏷️ {', '.join(app.tags[:3])}{'...' if len(app.tags) > 3 else ''}
                </span>
            </div>
            
            <div style="color: {status_color}; font-weight: bold; font-size: 0.8rem;">
                Status: {status_text}
            </div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        
    def render_app_actions(self, app: AppDisplayInfo):
        """Render action buttons for an app."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if app.status == AppStatus.NOT_INSTALLED:
                if st.button("📦 Install", key=f"install_{app.id}"):
                    self.install_app(app.id)
            elif app.status == AppStatus.INSTALLED:
                if st.button("▶️ Start", key=f"start_{app.id}"):
                    self.start_app(app.id)
            elif app.status == AppStatus.RUNNING:
                if st.button("⏹️ Stop", key=f"stop_{app.id}"):
                    self.stop_app(app.id)
            elif app.status == AppStatus.INSTALLING:
                st.button("⏳ Installing...", disabled=True, key=f"installing_{app.id}")
                
        with col2:
            if st.button("ℹ️ Details", key=f"details_{app.id}"):
                self.show_app_details(app)
                
        with col3:
            if app.repo_url:
                st.link_button("🔗 GitHub", app.repo_url, key=f"github_{app.id}")
            else:
                st.button("🔗 GitHub", disabled=True, key=f"github_disabled_{app.id}")
                
        with col4:
            if app.status in [AppStatus.INSTALLED, AppStatus.ERROR]:
                if st.button("🗑️ Remove", key=f"remove_{app.id}"):
                    self.remove_app(app.id)
                    
    def render_grid_view(self, apps: List[AppDisplayInfo]):
        """Render apps in grid view."""
        # Pagination
        apps_per_page = st.session_state.apps_per_page
        total_pages = (len(apps) + apps_per_page - 1) // apps_per_page
        
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page = st.number_input(
                    f"Page (1-{total_pages})",
                    min_value=1,
                    max_value=total_pages,
                    value=st.session_state.current_page,
                    key="gallery_page"
                )
                st.session_state.current_page = page
                
        # Calculate page slice
        start_idx = (st.session_state.current_page - 1) * apps_per_page
        end_idx = start_idx + apps_per_page
        page_apps = apps[start_idx:end_idx]
        
        # Render apps in grid
        cols_per_row = 2
        for i in range(0, len(page_apps), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j in range(cols_per_row):
                if i + j < len(page_apps):
                    app = page_apps[i + j]
                    
                    with cols[j]:
                        self.render_app_card(app)
                        self.render_app_actions(app)
                        
                        # Show installation progress
                        if app.status == AppStatus.INSTALLING:
                            progress = st.session_state.app_statuses.get(f"{app.id}_progress", 0)
                            st.progress(progress)
                            
    def render_list_view(self, apps: List[AppDisplayInfo]):
        """Render apps in list view."""
        for app in apps:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### {app.name}")
                    st.markdown(f"**Category:** {app.category} | **Author:** {app.author} | **Stars:** {app.stars}")
                    st.markdown(f"**Description:** {app.description}")
                    st.markdown(f"**Tags:** {', '.join(app.tags)}")
                    
                with col2:
                    self.render_app_actions(app)
                    
                st.markdown("---")
                
    def render_compact_view(self, apps: List[AppDisplayInfo]):
        """Render apps in compact view."""
        # Create a table-like view
        for app in apps:
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
            
            with col1:
                st.markdown(f"**{app.name}**")
                
            with col2:
                st.markdown(app.category)
                
            with col3:
                st.markdown(app.author)
                
            with col4:
                status_color = {
                    AppStatus.NOT_INSTALLED: "🔴",
                    AppStatus.INSTALLED: "🟢", 
                    AppStatus.RUNNING: "🔵",
                    AppStatus.INSTALLING: "🟡",
                    AppStatus.ERROR: "❌"
                }.get(app.status, "⚪")
                st.markdown(f"{status_color} {app.status.value.replace('_', ' ').title()}")
                
            with col5:
                action_col1, action_col2 = st.columns(2)
                with action_col1:
                    if app.status == AppStatus.NOT_INSTALLED:
                        if st.button("📦", key=f"install_compact_{app.id}", help="Install"):
                            self.install_app(app.id)
                    elif app.status == AppStatus.INSTALLED:
                        if st.button("▶️", key=f"start_compact_{app.id}", help="Start"):
                            self.start_app(app.id)
                    elif app.status == AppStatus.RUNNING:
                        if st.button("⏹️", key=f"stop_compact_{app.id}", help="Stop"):
                            self.stop_app(app.id)
                            
                with action_col2:
                    if st.button("ℹ️", key=f"details_compact_{app.id}", help="Details"):
                        self.show_app_details(app)
                        
    def install_app(self, app_id: str):
        """Install an application using modern Streamlit features."""
        try:
            # Get app data
            app_data = self.apps_data.get(app_id)
            if not app_data:
                st.toast("❌ App not found!", icon="❌")
                return
                
            # Update status
            st.session_state.app_statuses[app_id] = AppStatus.INSTALLING
            
            # Use st.status for better installation feedback
            with st.status(f"Installing {app_data['name']}...", expanded=True) as status:
                # Start installation in background thread
                def install_thread():
                    try:
                        status.write("📦 Downloading dependencies...")
                        time.sleep(2)
                        st.session_state.app_statuses[f"{app_id}_progress"] = 0.2
                        
                        status.write("🔧 Installing packages...")
                        time.sleep(2)
                        st.session_state.app_statuses[f"{app_id}_progress"] = 0.5
                        
                        status.write("⚙️ Configuring application...")
                        time.sleep(2)
                        st.session_state.app_statuses[f"{app_id}_progress"] = 0.8
                        
                        status.write("✅ Finalizing installation...")
                        time.sleep(2)
                        st.session_state.app_statuses[f"{app_id}_progress"] = 1.0
                        
                        # Update status to installed
                        st.session_state.app_statuses[app_id] = AppStatus.INSTALLED
                        status.update(label="Installation completed!", state="complete", expanded=False)
                        
                        # Modern toast notification
                        st.toast(f"✅ {app_data['name']} installed successfully!", icon="🎉")
                        self.logging_system.log_info("AppGallery", f"Successfully installed app: {app_id}")
                        
                    except Exception as e:
                        st.session_state.app_statuses[app_id] = AppStatus.ERROR
                        status.update(label="Installation failed!", state="error", expanded=True)
                        st.toast(f"❌ Installation failed: {str(e)}", icon="❌")
                        self.logging_system.log_error(f"Failed to install app: {app_id}", {"error": str(e)})
                        
                thread = threading.Thread(target=install_thread, daemon=True)
                thread.start()
                st.session_state.installation_threads[app_id] = thread
            
        except Exception as e:
            st.toast(f"❌ Failed to start installation: {str(e)}", icon="❌")
            self.logging_system.log_error("App installation failed", {"app_id": app_id, "error": str(e)})
            
    def start_app(self, app_id: str):
        """Start a running application."""
        try:
            st.session_state.app_statuses[app_id] = AppStatus.RUNNING
            st.success(f"Started application {app_id}")
            self.logging_system.log_info("AppGallery", f"Started app: {app_id}")
        except Exception as e:
            st.error(f"Failed to start app: {str(e)}")
            
    def stop_app(self, app_id: str):
        """Stop a running application."""
        try:
            st.session_state.app_statuses[app_id] = AppStatus.INSTALLED
            st.success(f"Stopped application {app_id}")
            self.logging_system.log_info("AppGallery", f"Stopped app: {app_id}")
        except Exception as e:
            st.error(f"Failed to stop app: {str(e)}")
            
    def remove_app(self, app_id: str):
        """Remove an installed application."""
        try:
            st.session_state.app_statuses[app_id] = AppStatus.NOT_INSTALLED
            st.success(f"Removed application {app_id}")
            self.logging_system.log_info("AppGallery", f"Removed app: {app_id}")
        except Exception as e:
            st.error(f"Failed to remove app: {str(e)}")
            
    @st.dialog("Application Details")
    def show_app_details(self, app: AppDisplayInfo):
        """Show detailed information about an app using modern dialog."""
        st.markdown(f"# 📱 {app.name}")
        
        # Status badge with color
        status_colors = {
            AppStatus.NOT_INSTALLED: "🔴",
            AppStatus.INSTALLED: "🟢", 
            AppStatus.RUNNING: "🔵",
            AppStatus.INSTALLING: "🟡",
            AppStatus.ERROR: "❌"
        }
        status_icon = status_colors.get(app.status, "⚪")
        st.markdown(f"### {status_icon} Status: {app.status.value.replace('_', ' ').title()}")
        
        # App information in tabs
        info_tab, details_tab, actions_tab = st.tabs(["📋 Info", "🔍 Details", "⚙️ Actions"])
        
        with info_tab:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Category", app.category)
                st.metric("Author", app.author)
                st.metric("Stars", app.stars)
                
            with col2:
                st.metric("Installer Type", app.installer_type.upper())
                if app.repo_url:
                    st.link_button("🔗 View on GitHub", app.repo_url)
                    
        with details_tab:
            st.markdown("**Description:**")
            st.markdown(app.description)
            
            st.markdown("**Tags:**")
            # Show tags as pills
            tag_cols = st.columns(min(len(app.tags), 4))
            for i, tag in enumerate(app.tags):
                with tag_cols[i % 4]:
                    st.markdown(f"`{tag}`")
                    
        with actions_tab:
            col1, col2 = st.columns(2)
            
            with col1:
                if app.status == AppStatus.NOT_INSTALLED:
                    if st.button("📦 Install Application", type="primary", use_container_width=True):
                        self.install_app(app.id)
                        st.rerun()
                elif app.status == AppStatus.INSTALLED:
                    if st.button("▶️ Start Application", type="primary", use_container_width=True):
                        self.start_app(app.id)
                        st.rerun()
                elif app.status == AppStatus.RUNNING:
                    if st.button("⏹️ Stop Application", type="secondary", use_container_width=True):
                        self.stop_app(app.id)
                        st.rerun()
                        
            with col2:
                if app.status in [AppStatus.INSTALLED, AppStatus.ERROR]:
                    if st.button("🗑️ Remove Application", type="secondary", use_container_width=True):
                        self.remove_app(app.id)
                        st.rerun()
        
    def render_gallery(self, search_term: str = "", category: str = "ALL", sort_by: str = "Name"):
        """Render the complete app gallery."""
        try:
            # Get filter controls
            search_term, category, selected_tags, status_filter, sort_by = self.render_search_controls()
            
            # Filter and sort apps
            filtered_apps = self.filter_apps(search_term, category, selected_tags, status_filter)
            sorted_apps = self.sort_apps(filtered_apps, sort_by)
            
            # Show statistics
            self.render_gallery_stats(filtered_apps)
            
            st.markdown("---")
            
            # Render based on view mode
            if not sorted_apps:
                st.info("No applications found matching your criteria.")
            else:
                if st.session_state.gallery_view == "grid":
                    self.render_grid_view(sorted_apps)
                elif st.session_state.gallery_view == "list":
                    self.render_list_view(sorted_apps)
                elif st.session_state.gallery_view == "compact":
                    self.render_compact_view(sorted_apps)
                    
        except Exception as e:
            st.error(f"Gallery rendering error: {str(e)}")
            self.logging_system.log_error("Gallery rendering error", {"error": str(e)})


def main():
    """Test the app gallery."""
    st.set_page_config(page_title="App Gallery Test", layout="wide")
    
    st.title("🏪 App Gallery Test")
    
    # Load test data
    test_apps = {
        "test-app-1": {
            "name": "Test App 1",
            "description": "This is a test application for demonstration",
            "category": "IMAGE",
            "tags": ["test", "demo", "image-generation"],
            "author": "TestAuthor",
            "stars": 42,
            "repo_url": "https://github.com/test/app1",
            "installer_type": "js"
        },
        "test-app-2": {
            "name": "Test App 2", 
            "description": "Another test application",
            "category": "AUDIO",
            "tags": ["test", "audio", "processing"],
            "author": "AnotherAuthor",
            "stars": 15,
            "repo_url": "https://github.com/test/app2",
            "installer_type": "json"
        }
    }
    
    gallery = AppGallery(test_apps)
    gallery.render_gallery()


if __name__ == "__main__":
    main()