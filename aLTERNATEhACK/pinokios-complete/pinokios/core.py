#!/usr/bin/env python3
"""
Enhanced Pinokio System - Compatible with Improved Database Schema
Supports both legacy and enhanced database formats with graceful fallbacks
"""

import os
import json
import subprocess
import sys
import threading
import time
import queue
import shutil
from pathlib import Path
from datetime import datetime
import sqlite3
import requests

try:
    import psutil
except ImportError:
    psutil = None

class EnhancedPinokioDatabase:
    """
    Enhanced database handler that supports both legacy and improved schemas
    """
    
    def __init__(self, database_module_name="complete_real_pinokio_database"):
        self.database_module_name = database_module_name
        self.apps_data = {}
        self.db_version = None
        self.last_update = None
        self.load_database()
    
    def load_database(self):
        """Load database with fallback support for different formats"""
        try:
            # Try to import the database module
            import importlib
            db_module = importlib.import_module(self.database_module_name)
            
            # Get the apps data
            if hasattr(db_module, 'PINOKIO_APPS'):
                self.apps_data = db_module.PINOKIO_APPS
                
            # Get version info if available
            if hasattr(db_module, 'PINOKIO_DB_VERSION'):
                self.db_version = db_module.PINOKIO_DB_VERSION
            if hasattr(db_module, 'PINOKIO_DB_LAST_UPDATE'):
                self.last_update = db_module.PINOKIO_DB_LAST_UPDATE
                
            print(f"✅ Loaded {len(self.apps_data)} apps from {self.database_module_name}")
            if self.db_version:
                print(f"📊 Database version: {self.db_version}")
                
        except Exception as e:
            print(f"⚠️ Failed to load {self.database_module_name}: {e}")
            self.apps_data = {}
    
    def get_app_field(self, app_data, field, default=None):
        """Get field from app with fallback to default"""
        return app_data.get(field, default)
    
    def search_apps(self, query="", category="", author="", verified_only=False, 
                   min_stars=0, min_vram="", min_ram="", tags=None):
        """Enhanced search with support for new fields"""
        results = []
        query_lower = query.lower() if query else ""
        tags = tags or []
        
        for app_id, app_data in self.apps_data.items():
            # Basic filters
            if verified_only and not self.get_app_field(app_data, 'verified', False):
                continue
            if category and self.get_app_field(app_data, 'category', '').lower() != category.lower():
                continue
            if author and self.get_app_field(app_data, 'author', '').lower() != author.lower():
                continue
            if self.get_app_field(app_data, 'stars', 0) < min_stars:
                continue
            
            # Enhanced filters for new schema
            if min_vram:
                app_vram = self.get_app_field(app_data, 'min_vram', '')
                if app_vram and not self._compare_memory(app_vram, min_vram):
                    continue
            
            if min_ram:
                app_ram = self.get_app_field(app_data, 'min_ram', '')
                if app_ram and not self._compare_memory(app_ram, min_ram):
                    continue
            
            # Tag filtering
            if tags:
                app_tags = self.get_app_field(app_data, 'tags', [])
                if not any(tag.lower() in [t.lower() for t in app_tags] for tag in tags):
                    continue
            
            # Text search
            if query:
                searchable_text = ' '.join([
                    self.get_app_field(app_data, 'name', ''),
                    self.get_app_field(app_data, 'description', ''),
                    ' '.join(self.get_app_field(app_data, 'tags', []))
                ]).lower()
                
                if query_lower not in searchable_text:
                    continue
            
            # Add to results with enhanced data
            result = {'id': app_id, **app_data}
            results.append(result)
        
        # Sort by stars (desc) then name (asc)
        results.sort(key=lambda x: (-self.get_app_field(x, 'stars', 0), 
                                   self.get_app_field(x, 'name', '')))
        return results
    
    def _compare_memory(self, app_mem, min_mem):
        """Compare memory requirements (GB)"""
        try:
            app_val = float(app_mem.replace('GB', '').replace('gb', '').strip())
            min_val = float(min_mem.replace('GB', '').replace('gb', '').strip())
            return app_val >= min_val
        except:
            return True  # If can't parse, assume it's fine
    
    def get_categories(self):
        """Get all unique categories"""
        categories = set()
        for app_data in self.apps_data.values():
            cat = self.get_app_field(app_data, 'category', 'Other')
            if cat:
                categories.add(cat)
        return sorted(list(categories))
    
    def get_authors(self):
        """Get all unique authors"""
        authors = set()
        for app_data in self.apps_data.values():
            author = self.get_app_field(app_data, 'author', '')
            if author:
                authors.add(author)
        return sorted(list(authors))
    
    def get_all_tags(self):
        """Get all unique tags"""
        tags = set()
        for app_data in self.apps_data.values():
            app_tags = self.get_app_field(app_data, 'tags', [])
            tags.update(app_tags)
        return sorted(list(tags))
    
    def get_stats(self):
        """Get comprehensive database statistics"""
        total_apps = len(self.apps_data)
        if total_apps == 0:
            return {
                'total_apps': 0,
                'total_stars': 0,
                'avg_stars': 0,
                'categories': {},
                'authors': {},
                'verified_count': 0,
                'install_verified_count': 0
            }
        
        total_stars = sum(self.get_app_field(app, 'stars', 0) for app in self.apps_data.values())
        categories = {}
        authors = {}
        verified_count = 0
        install_verified_count = 0
        
        for app in self.apps_data.values():
            # Categories
            category = self.get_app_field(app, 'category', 'Other')
            categories[category] = categories.get(category, 0) + 1
            
            # Authors
            author = self.get_app_field(app, 'author', 'Unknown')
            authors[author] = authors.get(author, 0) + 1
            
            # Verification counts
            if self.get_app_field(app, 'verified', False):
                verified_count += 1
            if self.get_app_field(app, 'install_verified', False):
                install_verified_count += 1
        
        return {
            'total_apps': total_apps,
            'total_stars': total_stars,
            'avg_stars': total_stars / total_apps,
            'categories': categories,
            'authors': authors,
            'verified_count': verified_count,
            'install_verified_count': install_verified_count,
            'db_version': self.db_version,
            'last_update': self.last_update
        }

class EnhancedPinokioInstaller:
    """Enhanced installer that works with improved database schema"""
    
    def __init__(self, base_path="/content/pinokios"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.log_queue = queue.Queue()
        self.install_log = []
        
        # Initialize database
        self.database = EnhancedPinokioDatabase()
        
    def log(self, message, app_name="INSTALLER", level="INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'app_name': app_name,
            'message': message,
            'level': level
        }
        self.log_queue.put(log_entry)
        self.install_log.append(log_entry)
        print(f"[{timestamp}] [{app_name}] {message}")
    
    def validate_app_data(self, app_data):
        """Validate app data structure for both legacy and enhanced schemas"""
        required_fields = ['name', 'clone_url', 'repo_url']
        
        for field in required_fields:
            if not self.database.get_app_field(app_data, field):
                return False, f"Missing required field: {field}"
        
        return True, "Valid"
    
    def get_system_requirements(self, app_data):
        """Extract system requirements from app data"""
        requirements = {
            'min_vram': self.database.get_app_field(app_data, 'min_vram', ''),
            'min_ram': self.database.get_app_field(app_data, 'min_ram', ''),
            'requirements': self.database.get_app_field(app_data, 'requirements', []),
            'language': self.database.get_app_field(app_data, 'language', 'Unknown')
        }
        return requirements
    
    def install_app_enhanced(self, app_id, progress_callback=None):
        """Enhanced installation with improved validation and requirements handling"""
        
        if app_id not in self.database.apps_data:
            self.log(f"App {app_id} not found in database", level="ERROR")
            return False
        
        app_data = self.database.apps_data[app_id]
        app_name = self.database.get_app_field(app_data, 'name', app_id)
        
        def progress(step, message):
            if progress_callback:
                progress_callback(step, message)
            self.log(message, app_name)
        
        try:
            # Validate app data
            progress("VALIDATING", "Validating app data...")
            valid, error = self.validate_app_data(app_data)
            if not valid:
                progress("ERROR", f"Validation failed: {error}")
                return False
            
            # Check system requirements
            progress("REQUIREMENTS", "Checking system requirements...")
            requirements = self.get_system_requirements(app_data)
            
            if requirements['min_vram']:
                progress("REQUIREMENTS", f"Required VRAM: {requirements['min_vram']}")
            if requirements['min_ram']:
                progress("REQUIREMENTS", f"Required RAM: {requirements['min_ram']}")
            
            # Clone repository
            progress("CLONE", "Cloning repository...")
            clone_url = self.database.get_app_field(app_data, 'clone_url')
            app_dir = self.base_path / app_name
            
            if app_dir.exists():
                shutil.rmtree(app_dir)
            
            result = subprocess.run(
                ["git", "clone", clone_url, str(app_dir)],
                capture_output=True, text=True, timeout=300
            )
            
            if result.returncode != 0:
                progress("ERROR", f"Clone failed: {result.stderr}")
                return False
            
            # Install dependencies if specified
            if requirements['requirements']:
                progress("INSTALL_DEPS", "Installing specified requirements...")
                for req in requirements['requirements']:
                    self.log(f"Installing: {req}", app_name)
            
            # Save enhanced configuration
            config = {
                'app_id': app_id,
                'name': app_name,
                'install_date': datetime.now().isoformat(),
                'app_data': app_data,
                'requirements': requirements,
                'working_directory': str(app_dir),
                'database_version': self.database.db_version
            }
            
            with open(app_dir / 'pinokios_enhanced_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            progress("SUCCESS", f"Installation completed successfully!")
            return True
            
        except Exception as e:
            progress("ERROR", f"Installation failed: {e}")
            return False
    
    def get_log_stream(self):
        """Get streaming logs"""
        logs = []
        try:
            while not self.log_queue.empty():
                logs.append(self.log_queue.get_nowait())
        except queue.Empty:
            pass
        return logs

# Compatibility functions for existing notebooks
def get_all_apps():
    """Compatibility function"""
    db = EnhancedPinokioDatabase()
    return db.apps_data

def search_apps(query="", category="", author="", verified_only=False, min_stars=0, **kwargs):
    """Compatibility function with enhanced search"""
    db = EnhancedPinokioDatabase()
    return db.search_apps(query, category, author, verified_only, min_stars, **kwargs)

def get_stats():
    """Compatibility function"""
    db = EnhancedPinokioDatabase()
    return db.get_stats()

__all__ = [
    'EnhancedPinokioDatabase', 'EnhancedPinokioInstaller',
    'get_all_apps', 'search_apps', 'get_stats'
]
