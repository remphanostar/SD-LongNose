#!/usr/bin/env python3
"""
PinokioCloud App Analyzer

This module serves as the main orchestrator for analyzing Pinokio applications.
It coordinates the detection of installation methods, web UI types, dependency
systems, and tunnel requirements for any Pinokio app.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import analysis modules
from .installer_detector import InstallerDetector, InstallerType, InstallerInfo
from .webui_detector import WebUIDetector, WebUIType, WebUIInfo
from .dependency_analyzer import DependencyAnalyzer, DependencyType, DependencyInfo
from .tunnel_requirements import TunnelRequirements, TunnelType, TunnelInfo
from .app_profiler import AppProfiler, AppProfile


class AnalysisStatus(Enum):
    """Enumeration of analysis statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class AppAnalysisResult:
    """Complete result of app analysis."""
    app_name: str
    app_path: str
    status: AnalysisStatus
    installer_info: Optional[InstallerInfo] = None
    webui_info: Optional[WebUIInfo] = None
    dependency_info: Optional[DependencyInfo] = None
    tunnel_info: Optional[TunnelInfo] = None
    app_profile: Optional[AppProfile] = None
    analysis_time: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AppAnalyzer:
    """
    Main app analysis orchestrator.
    
    Coordinates the analysis of Pinokio applications to determine:
    - Installation methods (install.js, install.json, requirements.txt, etc.)
    - Web UI types (Gradio, Streamlit, Flask, FastAPI, etc.)
    - Dependency systems (pip, conda, npm, system packages)
    - Tunnel requirements (ngrok, Cloudflare, LocalTunnel)
    - Complete app profiling and categorization
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the app analyzer.
        
        Args:
            base_path: Base path for app analysis
        """
        self.base_path = base_path
        self.apps_database_path = os.path.join(base_path, "cleaned_pinokio_apps.json")
        self.analysis_cache = {}
        self.analysis_results = {}
        self.progress_callback = None
        
        # Initialize analysis modules
        self.installer_detector = InstallerDetector(base_path)
        self.webui_detector = WebUIDetector(base_path)
        self.dependency_analyzer = DependencyAnalyzer(base_path)
        self.tunnel_requirements = TunnelRequirements(base_path)
        self.app_profiler = AppProfiler(base_path)
        
        # Load apps database
        self.apps_database = self._load_apps_database()
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def analyze_app(self, app_name: str, app_path: Optional[str] = None) -> AppAnalysisResult:
        """
        Perform complete analysis of a Pinokio application.
        
        Args:
            app_name: Name of the application to analyze
            app_path: Optional path to app directory (if None, will search)
            
        Returns:
            AppAnalysisResult: Complete analysis result
        """
        start_time = time.time()
        
        # Create analysis result
        result = AppAnalysisResult(
            app_name=app_name,
            app_path=app_path or "",
            status=AnalysisStatus.IN_PROGRESS
        )
        
        try:
            self._update_progress(f"Starting analysis of {app_name}")
            
            # Step 1: Find app path if not provided
            if not app_path:
                app_path = self._find_app_path(app_name)
                if not app_path:
                    result.status = AnalysisStatus.FAILED
                    result.error_message = f"App path not found for {app_name}"
                    return result
                result.app_path = app_path
            
            self._update_progress(f"Found app at: {app_path}")
            
            # Step 2: Analyze installer method
            self._update_progress("Analyzing installer method...")
            installer_info = self.installer_detector.detect_installer(app_path)
            result.installer_info = installer_info
            
            # Step 3: Analyze web UI type
            self._update_progress("Analyzing web UI type...")
            webui_info = self.webui_detector.detect_webui(app_path)
            result.webui_info = webui_info
            
            # Step 4: Analyze dependency system
            self._update_progress("Analyzing dependency system...")
            dependency_info = self.dependency_analyzer.analyze_dependencies(app_path)
            result.dependency_info = dependency_info
            
            # Step 5: Determine tunnel requirements
            self._update_progress("Determining tunnel requirements...")
            tunnel_info = self.tunnel_requirements.determine_requirements(
                webui_info, installer_info, dependency_info
            )
            result.tunnel_info = tunnel_info
            
            # Step 6: Create complete app profile
            self._update_progress("Creating app profile...")
            app_profile = self.app_profiler.create_profile(
                app_name, app_path, installer_info, webui_info, 
                dependency_info, tunnel_info
            )
            result.app_profile = app_profile
            
            # Step 7: Cache result
            self.analysis_cache[app_name] = result
            self.analysis_results[app_name] = result
            
            # Complete analysis
            result.status = AnalysisStatus.COMPLETED
            result.analysis_time = time.time() - start_time
            
            self._update_progress(f"Analysis complete for {app_name} in {result.analysis_time:.2f}s")
            
            return result
        
        except Exception as e:
            result.status = AnalysisStatus.FAILED
            result.error_message = str(e)
            result.analysis_time = time.time() - start_time
            self._update_progress(f"Analysis failed for {app_name}: {str(e)}")
            return result
    
    def analyze_apps_batch(self, app_names: List[str]) -> Dict[str, AppAnalysisResult]:
        """
        Analyze multiple applications in batch.
        
        Args:
            app_names: List of application names to analyze
            
        Returns:
            Dict mapping app names to analysis results
        """
        results = {}
        total_apps = len(app_names)
        
        for i, app_name in enumerate(app_names):
            self._update_progress(f"Analyzing {app_name} ({i+1}/{total_apps})")
            
            # Check cache first
            if app_name in self.analysis_cache:
                results[app_name] = self.analysis_cache[app_name]
                continue
            
            # Analyze app
            result = self.analyze_app(app_name)
            results[app_name] = result
        
        return results
    
    def analyze_apps_by_category(self, category: str) -> Dict[str, AppAnalysisResult]:
        """
        Analyze all applications in a specific category.
        
        Args:
            category: Category to analyze (e.g., "IMAGE", "VIDEO", "AUDIO", "LLM")
            
        Returns:
            Dict mapping app names to analysis results
        """
        # Get apps in category from database
        category_apps = []
        for app in self.apps_database:
            if app.get("category", "").upper() == category.upper():
                category_apps.append(app["name"])
        
        self._update_progress(f"Found {len(category_apps)} apps in category {category}")
        
        return self.analyze_apps_batch(category_apps)
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get summary of all analysis results.
        
        Returns:
            Dict containing analysis summary statistics
        """
        total_analyzed = len(self.analysis_results)
        completed = sum(1 for r in self.analysis_results.values() if r.status == AnalysisStatus.COMPLETED)
        failed = sum(1 for r in self.analysis_results.values() if r.status == AnalysisStatus.FAILED)
        
        # Count by installer type
        installer_types = {}
        for result in self.analysis_results.values():
            if result.installer_info:
                installer_type = result.installer_info.installer_type.value
                installer_types[installer_type] = installer_types.get(installer_type, 0) + 1
        
        # Count by web UI type
        webui_types = {}
        for result in self.analysis_results.values():
            if result.webui_info:
                webui_type = result.webui_info.webui_type.value
                webui_types[webui_type] = webui_types.get(webui_type, 0) + 1
        
        # Count by dependency type
        dependency_types = {}
        for result in self.analysis_results.values():
            if result.dependency_info:
                for dep_type in result.dependency_info.dependency_types:
                    dep_type_str = dep_type.value
                    dependency_types[dep_type_str] = dependency_types.get(dep_type_str, 0) + 1
        
        return {
            "total_analyzed": total_analyzed,
            "completed": completed,
            "failed": failed,
            "success_rate": (completed / total_analyzed * 100) if total_analyzed > 0 else 0,
            "installer_types": installer_types,
            "webui_types": webui_types,
            "dependency_types": dependency_types,
            "average_analysis_time": sum(r.analysis_time for r in self.analysis_results.values()) / total_analyzed if total_analyzed > 0 else 0
        }
    
    def save_analysis_results(self, output_path: str) -> bool:
        """
        Save analysis results to JSON file.
        
        Args:
            output_path: Path to save results
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert results to serializable format
            serializable_results = {}
            for app_name, result in self.analysis_results.items():
                serializable_results[app_name] = {
                    "app_name": result.app_name,
                    "app_path": result.app_path,
                    "status": result.status.value,
                    "analysis_time": result.analysis_time,
                    "error_message": result.error_message,
                    "installer_info": result.installer_info.__dict__ if result.installer_info else None,
                    "webui_info": result.webui_info.__dict__ if result.webui_info else None,
                    "dependency_info": result.dependency_info.__dict__ if result.dependency_info else None,
                    "tunnel_info": result.tunnel_info.__dict__ if result.tunnel_info else None,
                    "app_profile": result.app_profile.__dict__ if result.app_profile else None,
                    "metadata": result.metadata
                }
            
            # Save to file
            with open(output_path, 'w') as f:
                json.dump(serializable_results, f, indent=2, default=str)
            
            return True
        
        except Exception as e:
            return False
    
    def load_analysis_results(self, input_path: str) -> bool:
        """
        Load analysis results from JSON file.
        
        Args:
            input_path: Path to load results from
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(input_path, 'r') as f:
                data = json.load(f)
            
            # Convert back to AppAnalysisResult objects
            for app_name, result_data in data.items():
                result = AppAnalysisResult(
                    app_name=result_data["app_name"],
                    app_path=result_data["app_path"],
                    status=AnalysisStatus(result_data["status"]),
                    analysis_time=result_data["analysis_time"],
                    error_message=result_data.get("error_message"),
                    metadata=result_data.get("metadata", {})
                )
                
                # Reconstruct complex objects if present
                if result_data.get("installer_info"):
                    result.installer_info = InstallerInfo(**result_data["installer_info"])
                
                if result_data.get("webui_info"):
                    result.webui_info = WebUIInfo(**result_data["webui_info"])
                
                if result_data.get("dependency_info"):
                    result.dependency_info = DependencyInfo(**result_data["dependency_info"])
                
                if result_data.get("tunnel_info"):
                    result.tunnel_info = TunnelInfo(**result_data["tunnel_info"])
                
                if result_data.get("app_profile"):
                    result.app_profile = AppProfile(**result_data["app_profile"])
                
                self.analysis_results[app_name] = result
                self.analysis_cache[app_name] = result
            
            return True
        
        except Exception as e:
            return False
    
    def _load_apps_database(self) -> List[Dict[str, Any]]:
        """Load the Pinokio apps database."""
        try:
            if os.path.exists(self.apps_database_path):
                with open(self.apps_database_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            return []
    
    def _find_app_path(self, app_name: str) -> Optional[str]:
        """
        Find the path to an application.
        
        Args:
            app_name: Name of the application
            
        Returns:
            Path to app directory or None if not found
        """
        # Search in apps database first
        for app in self.apps_database:
            if app.get("name") == app_name:
                # Try to find the app in common locations
                possible_paths = [
                    os.path.join(self.base_path, "apps", app_name),
                    os.path.join(self.base_path, "applications", app_name),
                    os.path.join(self.base_path, app_name),
                    os.path.join("/tmp", app_name),
                    os.path.join("/workspace", app_name)
                ]
                
                for path in possible_paths:
                    if os.path.exists(path) and os.path.isdir(path):
                        return path
        
        return None
    
    def _update_progress(self, message: str):
        """Update progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(message)
            except:
                pass


def main():
    """Main function for testing app analyzer."""
    print("🧪 Testing App Analyzer")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = AppAnalyzer()
    
    # Set up progress callback
    def progress_callback(message):
        print(f"  {message}")
    
    analyzer.set_progress_callback(progress_callback)
    
    # Test with a sample app (if available)
    print("\n📱 Testing app analysis...")
    
    # Get first app from database for testing
    if analyzer.apps_database:
        test_app = analyzer.apps_database[0]
        app_name = test_app["name"]
        
        print(f"Testing with app: {app_name}")
        result = analyzer.analyze_app(app_name)
        
        if result.status == AnalysisStatus.COMPLETED:
            print("✅ App analysis completed successfully")
            print(f"   Installer: {result.installer_info.installer_type.value if result.installer_info else 'Unknown'}")
            print(f"   Web UI: {result.webui_info.webui_type.value if result.webui_info else 'Unknown'}")
            print(f"   Dependencies: {len(result.dependency_info.dependency_types) if result.dependency_info else 0} types")
            print(f"   Tunnel: {result.tunnel_info.tunnel_type.value if result.tunnel_info else 'Unknown'}")
            print(f"   Analysis time: {result.analysis_time:.2f}s")
        else:
            print(f"❌ App analysis failed: {result.error_message}")
    else:
        print("❌ No apps database found")
    
    # Test analysis summary
    print("\n📊 Testing analysis summary...")
    summary = analyzer.get_analysis_summary()
    print(f"✅ Analysis summary: {summary['total_analyzed']} apps analyzed")
    
    return True


if __name__ == "__main__":
    main()