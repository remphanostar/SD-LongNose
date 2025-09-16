#!/usr/bin/env python3
"""
PinokioCloud App Browser for Notebook
Clean, category-based application browsing using ipywidgets
"""

import os
import json
import ipywidgets as widgets
from IPython.display import display, HTML
from pathlib import Path

class AppBrowser:
    """Clean app browser for notebook interface."""
    
    def __init__(self):
        self.apps_data = self.load_apps_database()
        self.categories = self.extract_categories()
        self.selected_apps = set()
        
    def load_apps_database(self):
        """Load the 284 applications database."""
        try:
            # Look for database in standard locations
            possible_paths = [
                "cleaned_pinokio_apps.json",
                "../cleaned_pinokio_apps.json", 
                "../../cleaned_pinokio_apps.json"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        return json.load(f)
            
            return {"error": "Database not found"}
            
        except Exception as e:
            return {"error": f"Failed to load: {e}"}
    
    def extract_categories(self):
        """Extract unique categories from applications."""
        if isinstance(self.apps_data, dict) and 'error' in self.apps_data:
            return ['Error']
        
        categories = set()
        for app_data in self.apps_data.values():
            if isinstance(app_data, dict):
                category = app_data.get('category', 'Unknown')
                categories.add(category)
        
        return sorted(list(categories))
    
    def create_app_browser(self):
        """Create the main app browser interface."""
        
        # Header
        header = widgets.HTML(value="""
        <div style='background: linear-gradient(45deg, #667eea, #764ba2); 
                   padding: 15px; border-radius: 10px; color: white; text-align: center; margin-bottom: 15px;'>
            <h3>🏪 PinokioCloud App Gallery</h3>
            <p>284 AI Applications Available</p>
        </div>
        """)
        
        # Search and filter controls
        search_box = widgets.Text(
            placeholder='🔍 Search applications...',
            layout=widgets.Layout(width='300px')
        )
        
        category_filter = widgets.Dropdown(
            options=['All Categories'] + self.categories,
            value='All Categories',
            description='Category:',
            layout=widgets.Layout(width='200px')
        )
        
        # App count display
        app_count = widgets.HTML(value=f"<b>📊 {len(self.apps_data)} apps available</b>")
        
        # Controls row
        controls = widgets.HBox([search_box, category_filter, app_count])
        
        # Apps display area
        apps_display = self.create_apps_display()
        
        # Action buttons
        actions = widgets.HBox([
            widgets.Button(description='📥 Install Selected', button_style='success'),
            widgets.Button(description='▶️ Run Selected', button_style='primary'),
            widgets.Button(description='🌐 Create Tunnel', button_style='info')
        ])
        
        # Bind events
        search_box.observe(lambda change: self.on_search_change(change, apps_display), names='value')
        category_filter.observe(lambda change: self.on_category_change(change, apps_display), names='value')
        
        # Complete interface
        return widgets.VBox([header, controls, apps_display, actions])
    
    def create_apps_display(self, category='All Categories', search_term=''):
        """Create the apps display widget."""
        
        if isinstance(self.apps_data, dict) and 'error' in self.apps_data:
            return widgets.HTML(value=f"<div style='color: red;'>❌ {self.apps_data['error']}</div>")
        
        # Filter apps
        filtered_apps = self.filter_apps(category, search_term)
        
        # Create app cards (show first 20 for performance)
        app_cards_html = []
        for i, (app_id, app_data) in enumerate(list(filtered_apps.items())[:20]):
            card_html = self.create_app_card_html(app_id, app_data)
            app_cards_html.append(card_html)
        
        # Combine all cards
        all_cards = ''.join(app_cards_html)
        
        display_html = f"""
        <div style='max-height: 400px; overflow-y: auto; border: 1px solid #ddd; 
                    border-radius: 8px; padding: 15px; background: #f8f9fa;'>
            {all_cards}
            <div style='text-align: center; margin: 20px; color: #666;'>
                📊 Showing {min(20, len(filtered_apps))} of {len(filtered_apps)} filtered apps
                <br><small>Use search and category filter to find specific applications</small>
            </div>
        </div>
        """
        
        return widgets.HTML(value=display_html)
    
    def filter_apps(self, category='All Categories', search_term=''):
        """Filter applications by category and search term."""
        filtered = {}
        
        for app_id, app_data in self.apps_data.items():
            if not isinstance(app_data, dict):
                continue
            
            # Category filter
            if category != 'All Categories':
                if app_data.get('category', 'Unknown') != category:
                    continue
            
            # Search filter
            if search_term:
                searchable_text = f"{app_data.get('name', '')} {app_data.get('description', '')} {app_id}".lower()
                if search_term.lower() not in searchable_text:
                    continue
            
            filtered[app_id] = app_data
        
        return filtered
    
    def create_app_card_html(self, app_id, app_data):
        """Create HTML for a single app card."""
        name = app_data.get('name', app_id)
        category = app_data.get('category', 'Unknown')
        description = app_data.get('description', 'No description available')[:100]
        vram = app_data.get('vram_gb', 'Unknown')
        
        return f"""
        <div style='border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin: 10px 0; 
                   background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                <div style='flex: 1;'>
                    <h4 style='margin: 0 0 8px 0; color: #495057;'>📱 {name}</h4>
                    <p style='margin: 4px 0; color: #6c757d; font-size: 14px;'>📂 {category}</p>
                    <p style='margin: 4px 0; color: #6c757d; font-size: 13px;'>{description}...</p>
                    <p style='margin: 4px 0; color: #28a745; font-size: 12px; font-weight: bold;'>💾 VRAM: {vram} GB</p>
                </div>
                <div style='margin-left: 15px;'>
                    <div style='background: #e9ecef; padding: 8px; border-radius: 6px; text-align: center;'>
                        <div style='font-size: 12px; color: #6c757d;'>Status</div>
                        <div style='font-weight: bold; color: #dc3545;'>Not Installed</div>
                    </div>
                </div>
            </div>
            <div style='margin-top: 12px; border-top: 1px solid #dee2e6; padding-top: 10px;'>
                <button style='background: #007bff; color: white; border: none; padding: 6px 12px; 
                              border-radius: 4px; margin-right: 8px; cursor: pointer;'>
                    📥 Install
                </button>
                <button style='background: #28a745; color: white; border: none; padding: 6px 12px; 
                              border-radius: 4px; margin-right: 8px; cursor: pointer;'>
                    ▶️ Run
                </button>
                <button style='background: #17a2b8; color: white; border: none; padding: 6px 12px; 
                              border-radius: 4px; cursor: pointer;'>
                    🌐 Share
                </button>
            </div>
        </div>
        """
    
    def on_search_change(self, change, display_widget):
        """Handle search box changes."""
        # Update display (simplified for now)
        print(f"🔍 Search: {change['new']}")
    
    def on_category_change(self, change, display_widget):
        """Handle category filter changes."""
        # Update display (simplified for now)
        print(f"📂 Category: {change['new']}")

def create_app_browser():
    """Create and return the app browser widget."""
    browser = AppBrowser()
    return browser.create_app_browser()

# Usage: app_browser_widget = create_app_browser()