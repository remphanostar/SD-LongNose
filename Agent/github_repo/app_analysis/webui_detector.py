#!/usr/bin/env python3
"""
PinokioCloud Web UI Detector

This module detects the web UI framework used by Pinokio applications.
It identifies whether an app uses Gradio, Streamlit, Flask, FastAPI,
or other web UI frameworks.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class WebUIType(Enum):
    """Enumeration of web UI types."""
    GRADIO = "gradio"
    STREAMLIT = "streamlit"
    FLASK = "flask"
    FASTAPI = "fastapi"
    DJANGO = "django"
    TORNADO = "tornado"
    BOKEH = "bokeh"
    DASH = "dash"
    JUPYTER = "jupyter"
    CUSTOM = "custom"
    NONE = "none"
    UNKNOWN = "unknown"


@dataclass
class WebUIInfo:
    """Information about an application's web UI."""
    webui_type: WebUIType
    main_file: str
    port: Optional[int] = None
    host: str = "localhost"
    share_enabled: bool = False
    auto_launch: bool = True
    debug_mode: bool = False
    static_files: List[str] = field(default_factory=list)
    templates: List[str] = field(default_factory=list)
    routes: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    launch_arguments: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WebUIDetector:
    """
    Detects web UI frameworks for Pinokio applications.
    
    Analyzes application directories to determine:
    - Type of web UI framework (Gradio, Streamlit, Flask, etc.)
    - Main application file
    - Port and host configuration
    - Launch arguments and options
    - Static files and templates
    - Routes and endpoints
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the web UI detector.
        
        Args:
            base_path: Base path for detection
        """
        self.base_path = base_path
        self.webui_patterns = {
            WebUIType.GRADIO: {
                "imports": ["import gradio", "from gradio", "gradio.Interface"],
                "files": ["app.py", "main.py", "gradio_app.py", "interface.py"],
                "keywords": ["gr.Interface", "gradio.Interface", "launch(", "share="]
            },
            WebUIType.STREAMLIT: {
                "imports": ["import streamlit", "from streamlit"],
                "files": ["app.py", "main.py", "streamlit_app.py", "ui.py"],
                "keywords": ["st.", "streamlit run", "st.title", "st.button"]
            },
            WebUIType.FLASK: {
                "imports": ["import flask", "from flask", "Flask("],
                "files": ["app.py", "main.py", "flask_app.py", "server.py"],
                "keywords": ["app.run(", "Flask(", "route(", "render_template"]
            },
            WebUIType.FASTAPI: {
                "imports": ["import fastapi", "from fastapi", "FastAPI("],
                "files": ["main.py", "app.py", "fastapi_app.py", "api.py"],
                "keywords": ["FastAPI(", "uvicorn.run", "@app.get", "@app.post"]
            },
            WebUIType.DJANGO: {
                "imports": ["import django", "from django"],
                "files": ["manage.py", "settings.py", "urls.py", "views.py"],
                "keywords": ["django-admin", "manage.py", "runserver"]
            },
            WebUIType.TORNADO: {
                "imports": ["import tornado", "from tornado"],
                "files": ["main.py", "app.py", "server.py"],
                "keywords": ["tornado.web", "Application(", "listen("]
            },
            WebUIType.BOKEH: {
                "imports": ["import bokeh", "from bokeh"],
                "files": ["main.py", "app.py", "bokeh_app.py"],
                "keywords": ["bokeh.server", "curdoc(", "show("]
            },
            WebUIType.DASH: {
                "imports": ["import dash", "from dash"],
                "files": ["app.py", "main.py", "dash_app.py"],
                "keywords": ["dash.Dash", "app.run_server", "@app.callback"]
            },
            WebUIType.JUPYTER: {
                "imports": ["import jupyter", "from jupyter", "import ipywidgets"],
                "files": ["*.ipynb", "notebook.ipynb", "app.ipynb"],
                "keywords": ["ipywidgets", "jupyter", "notebook", "widget"]
            }
        }
    
    def detect_webui(self, app_path: str) -> WebUIInfo:
        """
        Detect the web UI framework for an application.
        
        Args:
            app_path: Path to the application directory
            
        Returns:
            WebUIInfo: Information about the web UI
        """
        try:
            if not os.path.exists(app_path) or not os.path.isdir(app_path):
                return WebUIInfo(
                    webui_type=WebUIType.UNKNOWN,
                    main_file=""
                )
            
            # Search for web UI indicators
            webui_detections = self._detect_webui_indicators(app_path)
            
            if not webui_detections:
                return WebUIInfo(
                    webui_type=WebUIType.NONE,
                    main_file=""
                )
            
            # Get the most likely web UI type
            webui_type = self._determine_primary_webui(webui_detections)
            
            # Find main application file
            main_file = self._find_main_file(app_path, webui_type)
            
            # Analyze the main file for configuration
            port, host, share_enabled, auto_launch, debug_mode = self._analyze_main_file(main_file, webui_type)
            
            # Find static files and templates
            static_files = self._find_static_files(app_path)
            templates = self._find_templates(app_path)
            routes = self._find_routes(main_file, webui_type)
            
            # Get dependencies
            dependencies = self._get_webui_dependencies(webui_type)
            
            # Get launch arguments
            launch_arguments = self._get_launch_arguments(main_file, webui_type)
            
            return WebUIInfo(
                webui_type=webui_type,
                main_file=main_file,
                port=port,
                host=host,
                share_enabled=share_enabled,
                auto_launch=auto_launch,
                debug_mode=debug_mode,
                static_files=static_files,
                templates=templates,
                routes=routes,
                dependencies=dependencies,
                launch_arguments=launch_arguments,
                metadata={
                    "all_detections": webui_detections,
                    "confidence": self._calculate_confidence(webui_detections, webui_type)
                }
            )
        
        except Exception as e:
            return WebUIInfo(
                webui_type=WebUIType.UNKNOWN,
                main_file="",
                metadata={"error": str(e)}
            )
    
    def _detect_webui_indicators(self, app_path: str) -> Dict[WebUIType, Dict[str, Any]]:
        """
        Detect web UI indicators in the application directory.
        
        Args:
            app_path: Path to the application directory
            
        Returns:
            Dict mapping web UI types to their detection results
        """
        detections = {}
        
        try:
            for webui_type, patterns in self.webui_patterns.items():
                detection_score = 0
                found_files = []
                found_imports = []
                found_keywords = []
                
                # Search through all Python files
                for root, dirs, files in os.walk(app_path):
                    # Skip hidden directories and common ignore directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                    
                    for file in files:
                        if file.endswith('.py') or file.endswith('.ipynb'):
                            file_path = os.path.join(root, file)
                            relative_path = os.path.relpath(file_path, app_path)
                            
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                # Check for imports
                                for import_pattern in patterns["imports"]:
                                    if import_pattern in content:
                                        detection_score += 2
                                        found_imports.append(import_pattern)
                                
                                # Check for keywords
                                for keyword in patterns["keywords"]:
                                    if keyword in content:
                                        detection_score += 1
                                        found_keywords.append(keyword)
                                
                                # Check for specific files
                                for file_pattern in patterns["files"]:
                                    if file == file_pattern:
                                        detection_score += 3
                                        found_files.append(relative_path)
                                
                                # Special handling for Jupyter notebooks
                                if webui_type == WebUIType.JUPYTER and file.endswith('.ipynb'):
                                    detection_score += 5
                                    found_files.append(relative_path)
                            
                            except Exception:
                                continue
                
                if detection_score > 0:
                    detections[webui_type] = {
                        "score": detection_score,
                        "files": found_files,
                        "imports": found_imports,
                        "keywords": found_keywords
                    }
        
        except Exception as e:
            pass
        
        return detections
    
    def _determine_primary_webui(self, detections: Dict[WebUIType, Dict[str, Any]]) -> WebUIType:
        """
        Determine the primary web UI type from detections.
        
        Args:
            detections: Dictionary of web UI detections
            
        Returns:
            Primary web UI type
        """
        if not detections:
            return WebUIType.UNKNOWN
        
        # Sort by detection score
        sorted_detections = sorted(detections.items(), key=lambda x: x[1]["score"], reverse=True)
        
        # Return the highest scoring web UI type
        return sorted_detections[0][0]
    
    def _find_main_file(self, app_path: str, webui_type: WebUIType) -> str:
        """
        Find the main application file for the web UI.
        
        Args:
            app_path: Path to the application directory
            webui_type: Detected web UI type
            
        Returns:
            Path to main file
        """
        try:
            # Get preferred file names for this web UI type
            preferred_files = self.webui_patterns.get(webui_type, {}).get("files", [])
            
            # Search for preferred files first
            for file_name in preferred_files:
                file_path = os.path.join(app_path, file_name)
                if os.path.exists(file_path):
                    return file_path
            
            # Search for any Python file that might be the main file
            for root, dirs, files in os.walk(app_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Check if this file contains web UI code
                            if self._contains_webui_code(content, webui_type):
                                return file_path
                        except:
                            continue
            
            # Return first Python file if no specific main file found
            for root, dirs, files in os.walk(app_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                for file in files:
                    if file.endswith('.py'):
                        return os.path.join(root, file)
        
        except Exception as e:
            pass
        
        return ""
    
    def _contains_webui_code(self, content: str, webui_type: WebUIType) -> bool:
        """
        Check if content contains web UI code for the specified type.
        
        Args:
            content: File content
            webui_type: Web UI type to check for
            
        Returns:
            True if web UI code is found
        """
        try:
            patterns = self.webui_patterns.get(webui_type, {})
            
            # Check for imports
            for import_pattern in patterns.get("imports", []):
                if import_pattern in content:
                    return True
            
            # Check for keywords
            for keyword in patterns.get("keywords", []):
                if keyword in content:
                    return True
        
        except Exception as e:
            pass
        
        return False
    
    def _analyze_main_file(self, main_file: str, webui_type: WebUIType) -> Tuple[Optional[int], str, bool, bool, bool]:
        """
        Analyze the main file for configuration details.
        
        Args:
            main_file: Path to main file
            webui_type: Web UI type
            
        Returns:
            Tuple of (port, host, share_enabled, auto_launch, debug_mode)
        """
        port = None
        host = "localhost"
        share_enabled = False
        auto_launch = True
        debug_mode = False
        
        try:
            if not os.path.exists(main_file):
                return port, host, share_enabled, auto_launch, debug_mode
            
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract port
            port_patterns = [
                r'port\s*=\s*(\d+)',
                r'listen\((\d+)',
                r'run\([^)]*port\s*=\s*(\d+)',
                r'launch\([^)]*server_port\s*=\s*(\d+)'
            ]
            
            for pattern in port_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    port = int(match.group(1))
                    break
            
            # Extract host
            host_patterns = [
                r'host\s*=\s*["\']([^"\']+)["\']',
                r'listen\([^,]*,\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in host_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    host = match.group(1)
                    break
            
            # Check for share enabled (mainly for Gradio)
            if webui_type == WebUIType.GRADIO:
                share_patterns = [
                    r'share\s*=\s*True',
                    r'share\s*=\s*1',
                    r'share=True'
                ]
                
                for pattern in share_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        share_enabled = True
                        break
            
            # Check for auto launch
            auto_launch_patterns = [
                r'auto_launch\s*=\s*True',
                r'auto_launch\s*=\s*1',
                r'auto_launch=True'
            ]
            
            for pattern in auto_launch_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    auto_launch = True
                    break
            
            # Check for debug mode
            debug_patterns = [
                r'debug\s*=\s*True',
                r'debug\s*=\s*1',
                r'debug=True',
                r'debug_mode\s*=\s*True'
            ]
            
            for pattern in debug_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    debug_mode = True
                    break
        
        except Exception as e:
            pass
        
        return port, host, share_enabled, auto_launch, debug_mode
    
    def _find_static_files(self, app_path: str) -> List[str]:
        """
        Find static files in the application directory.
        
        Args:
            app_path: Path to the application directory
            
        Returns:
            List of static file paths
        """
        static_files = []
        static_dirs = ["static", "assets", "public", "www", "web"]
        
        try:
            for static_dir in static_dirs:
                static_path = os.path.join(app_path, static_dir)
                if os.path.exists(static_path) and os.path.isdir(static_path):
                    for root, dirs, files in os.walk(static_path):
                        for file in files:
                            if file.endswith(('.css', '.js', '.html', '.png', '.jpg', '.gif', '.svg')):
                                file_path = os.path.join(root, file)
                                relative_path = os.path.relpath(file_path, app_path)
                                static_files.append(relative_path)
        
        except Exception as e:
            pass
        
        return static_files
    
    def _find_templates(self, app_path: str) -> List[str]:
        """
        Find template files in the application directory.
        
        Args:
            app_path: Path to the application directory
            
        Returns:
            List of template file paths
        """
        templates = []
        template_dirs = ["templates", "views", "pages"]
        
        try:
            for template_dir in template_dirs:
                template_path = os.path.join(app_path, template_dir)
                if os.path.exists(template_path) and os.path.isdir(template_path):
                    for root, dirs, files in os.walk(template_path):
                        for file in files:
                            if file.endswith(('.html', '.jinja', '.jinja2', '.j2')):
                                file_path = os.path.join(root, file)
                                relative_path = os.path.relpath(file_path, app_path)
                                templates.append(relative_path)
        
        except Exception as e:
            pass
        
        return templates
    
    def _find_routes(self, main_file: str, webui_type: WebUIType) -> List[str]:
        """
        Find routes/endpoints in the main file.
        
        Args:
            main_file: Path to main file
            webui_type: Web UI type
            
        Returns:
            List of routes
        """
        routes = []
        
        try:
            if not os.path.exists(main_file):
                return routes
            
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract routes based on web UI type
            if webui_type in [WebUIType.FLASK, WebUIType.FASTAPI]:
                route_patterns = [
                    r'@app\.route\(["\']([^"\']+)["\']',
                    r'@app\.get\(["\']([^"\']+)["\']',
                    r'@app\.post\(["\']([^"\']+)["\']',
                    r'@app\.put\(["\']([^"\']+)["\']',
                    r'@app\.delete\(["\']([^"\']+)["\']'
                ]
                
                for pattern in route_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    routes.extend(matches)
            
            elif webui_type == WebUIType.TORNADO:
                route_patterns = [
                    r'\(["\']([^"\']+)["\']',
                    r'url\(["\']([^"\']+)["\']'
                ]
                
                for pattern in route_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    routes.extend(matches)
        
        except Exception as e:
            pass
        
        return list(set(routes))  # Remove duplicates
    
    def _get_webui_dependencies(self, webui_type: WebUIType) -> List[str]:
        """
        Get typical dependencies for a web UI type.
        
        Args:
            webui_type: Web UI type
            
        Returns:
            List of dependencies
        """
        dependencies_map = {
            WebUIType.GRADIO: ["gradio"],
            WebUIType.STREAMLIT: ["streamlit"],
            WebUIType.FLASK: ["flask"],
            WebUIType.FASTAPI: ["fastapi", "uvicorn"],
            WebUIType.DJANGO: ["django"],
            WebUIType.TORNADO: ["tornado"],
            WebUIType.BOKEH: ["bokeh"],
            WebUIType.DASH: ["dash"],
            WebUIType.JUPYTER: ["jupyter", "ipywidgets"]
        }
        
        return dependencies_map.get(webui_type, [])
    
    def _get_launch_arguments(self, main_file: str, webui_type: WebUIType) -> Dict[str, Any]:
        """
        Get launch arguments from the main file.
        
        Args:
            main_file: Path to main file
            webui_type: Web UI type
            
        Returns:
            Dictionary of launch arguments
        """
        launch_args = {}
        
        try:
            if not os.path.exists(main_file):
                return launch_args
            
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract common launch arguments
            if webui_type == WebUIType.GRADIO:
                # Gradio specific arguments
                gradio_args = ["share", "server_port", "server_name", "show_error", "quiet"]
                for arg in gradio_args:
                    pattern = f'{arg}\\s*=\\s*([^,\\n)]+)'
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip().strip('"\'')
                        launch_args[arg] = value
            
            elif webui_type == WebUIType.STREAMLIT:
                # Streamlit specific arguments
                streamlit_args = ["server.port", "server.address", "server.headless"]
                for arg in streamlit_args:
                    pattern = f'{arg}\\s*=\\s*([^,\\n)]+)'
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip().strip('"\'')
                        launch_args[arg] = value
            
            elif webui_type in [WebUIType.FLASK, WebUIType.FASTAPI]:
                # Flask/FastAPI specific arguments
                web_args = ["host", "port", "debug", "reload"]
                for arg in web_args:
                    pattern = f'{arg}\\s*=\\s*([^,\\n)]+)'
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip().strip('"\'')
                        launch_args[arg] = value
        
        except Exception as e:
            pass
        
        return launch_args
    
    def _calculate_confidence(self, detections: Dict[WebUIType, Dict[str, Any]], webui_type: WebUIType) -> float:
        """
        Calculate confidence score for web UI detection.
        
        Args:
            detections: All detections
            webui_type: Primary web UI type
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        try:
            if webui_type not in detections:
                return 0.0
            
            primary_score = detections[webui_type]["score"]
            total_score = sum(det["score"] for det in detections.values())
            
            if total_score == 0:
                return 0.0
            
            confidence = primary_score / total_score
            
            # Boost confidence based on number of indicators
            num_indicators = len(detections[webui_type]["files"]) + len(detections[webui_type]["imports"]) + len(detections[webui_type]["keywords"])
            confidence += min(0.2, num_indicators * 0.05)
            
            return min(1.0, confidence)
        
        except Exception as e:
            return 0.0


def main():
    """Main function for testing web UI detector."""
    print("🧪 Testing Web UI Detector")
    print("=" * 50)
    
    # Initialize detector
    detector = WebUIDetector()
    
    # Test with a sample directory
    test_path = "/tmp/test_webui_app"
    os.makedirs(test_path, exist_ok=True)
    
    # Create test Gradio app
    gradio_content = """
import gradio as gr

def greet(name):
    return f"Hello {name}!"

interface = gr.Interface(
    fn=greet,
    inputs="text",
    outputs="text",
    title="Test App"
)

if __name__ == "__main__":
    interface.launch(share=True, server_port=7860)
"""
    
    with open(os.path.join(test_path, "app.py"), 'w') as f:
        f.write(gradio_content)
    
    # Test detection
    print("\n🌐 Testing web UI detection...")
    result = detector.detect_webui(test_path)
    
    print(f"✅ Web UI type: {result.webui_type.value}")
    print(f"✅ Main file: {result.main_file}")
    print(f"✅ Port: {result.port}")
    print(f"✅ Host: {result.host}")
    print(f"✅ Share enabled: {result.share_enabled}")
    print(f"✅ Auto launch: {result.auto_launch}")
    print(f"✅ Debug mode: {result.debug_mode}")
    print(f"✅ Static files: {len(result.static_files)} found")
    print(f"✅ Templates: {len(result.templates)} found")
    print(f"✅ Routes: {len(result.routes)} found")
    print(f"✅ Dependencies: {', '.join(result.dependencies)}")
    print(f"✅ Launch arguments: {result.launch_arguments}")
    print(f"✅ Confidence: {result.metadata.get('confidence', 0):.2f}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_path, ignore_errors=True)
    
    return True


if __name__ == "__main__":
    main()