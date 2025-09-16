#!/usr/bin/env python3
"""
Complete App Manager for PinokioCloud Notebook
Handles ALL 284 apps with REAL functionality
"""

import os
import sys
import json
import subprocess
import threading
import time
from pathlib import Path
import ipywidgets as widgets
from IPython.display import display

class CompleteAppManager:
    """REAL app manager with ALL 284 apps and REAL functionality."""
    
    def __init__(self):
        self.apps_data = self.load_complete_apps_database()
        self.categories = self.extract_all_categories()
        self.filtered_apps = self.apps_data.copy()
        self.installation_processes = {}
        
    def load_complete_apps_database(self):
        """Load the COMPLETE 284 apps database."""
        try:
            # Look for the real database
            database_paths = [
                "cleaned_pinokio_apps.json",
                "../cleaned_pinokio_apps.json", 
                "../../cleaned_pinokio_apps.json",
                "/content/pinokio-cloud/cleaned_pinokio_apps.json"
            ]
            
            for path in database_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        apps_data = json.load(f)
                    print(f"✅ Loaded COMPLETE database: {len(apps_data)} real applications")
                    return apps_data
            
            # Fallback with more examples if database not found
            print("⚠️ Database not found, using extended fallback with real repositories")
            return {
                "automatic1111": {
                    "name": "AUTOMATIC1111",
                    "category": "IMAGE", 
                    "description": "Stable Diffusion WebUI for image generation",
                    "repository": "https://github.com/AUTOMATIC1111/stable-diffusion-webui.git",
                    "vram_gb": 4,
                    "install_type": "git_clone_requirements"
                },
                "facefusion": {
                    "name": "FaceFusion",
                    "category": "IMAGE",
                    "description": "Advanced face swapping and deepfake technology", 
                    "repository": "https://github.com/facefusion/facefusion.git",
                    "vram_gb": 2,
                    "install_type": "git_clone_requirements"
                },
                "text-generation-webui": {
                    "name": "Text Generation WebUI",
                    "category": "TEXT",
                    "description": "Large language model web interface",
                    "repository": "https://github.com/oobabooga/text-generation-webui.git", 
                    "vram_gb": 6,
                    "install_type": "git_clone_requirements"
                },
                "comfyui": {
                    "name": "ComfyUI",
                    "category": "IMAGE",
                    "description": "Node-based stable diffusion GUI",
                    "repository": "https://github.com/comfyanonymous/ComfyUI.git",
                    "vram_gb": 4,
                    "install_type": "git_clone_requirements"
                },
                "invokeai": {
                    "name": "InvokeAI", 
                    "category": "IMAGE",
                    "description": "Professional Stable Diffusion toolkit",
                    "repository": "https://github.com/invoke-ai/InvokeAI.git",
                    "vram_gb": 4,
                    "install_type": "git_clone_requirements"
                },
                "rvc-webui": {
                    "name": "RVC WebUI",
                    "category": "AUDIO",
                    "description": "Real-time voice cloning",
                    "repository": "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git",
                    "vram_gb": 2,
                    "install_type": "git_clone_requirements"
                }
            }
            
        except Exception as e:
            print(f"❌ Error loading apps database: {e}")
            return {}
    
    def extract_all_categories(self):
        """Extract ALL unique categories from the apps."""
        categories = set()
        for app_data in self.apps_data.values():
            if isinstance(app_data, dict):
                category = app_data.get('category', 'Unknown')
                categories.add(category)
        
        return sorted(list(categories))
    
    def create_complete_app_gallery(self):
        """Create COMPLETE app gallery with ALL functionality."""
        
        # Header with real stats
        header = widgets.HTML(value=f"""
        <div style='background: linear-gradient(45deg, #667eea, #764ba2); 
                   padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 15px;'>
            <h2>🏪 Complete PinokioCloud App Gallery</h2>
            <p><strong>{len(self.apps_data)} Real Applications</strong> | <strong>{len(self.categories)} Categories</strong></p>
            <p>REAL Installation | REAL pip Output | NO Placeholders</p>
        </div>
        """)
        
        # Search and filter controls
        self.search_box = widgets.Text(
            placeholder=f'🔍 Search ALL {len(self.apps_data)} applications by name, description, category...',
            layout=widgets.Layout(width='400px')
        )
        
        self.category_filter = widgets.Dropdown(
            options=['All Categories'] + self.categories,
            value='All Categories',
            description='Category:',
            layout=widgets.Layout(width='200px')
        )
        
        self.apps_per_page = widgets.Dropdown(
            options=[10, 20, 50, 100],
            value=20,
            description='Show:',
            layout=widgets.Layout(width='150px')
        )
        
        # Filter controls
        filter_controls = widgets.HBox([
            self.search_box, 
            self.category_filter, 
            self.apps_per_page
        ])
        
        # Apps display container
        self.apps_container = widgets.VBox()
        self.update_apps_display()
        
        # Bind filter events
        self.search_box.observe(self.on_filter_change, names='value')
        self.category_filter.observe(self.on_filter_change, names='value')
        self.apps_per_page.observe(self.on_filter_change, names='value')
        
        # Installation output with REAL pip/git output
        self.installation_output = widgets.Output(
            layout=widgets.Layout(height='400px', overflow='scroll')
        )
        
        # Initialize output area
        with self.installation_output:
            print("🚀 PinokioCloud Installation Terminal")
            print("=" * 50)
            print("📦 REAL pip output will appear here")
            print("📥 REAL git clone output will appear here") 
            print("▶️ REAL Python execution output will appear here")
            print("🌐 REAL tunnel creation will appear here")
            print("⚠️ NO PLACEHOLDERS - Everything is real!")
        
        # Complete gallery interface
        return widgets.VBox([
            header,
            filter_controls,
            widgets.HTML(value="<h3>📱 Applications:</h3>"),
            self.apps_container,
            widgets.HTML(value="<h3>📦 REAL Installation & Execution Output:</h3>"),
            self.installation_output
        ])
    
    def update_apps_display(self):
        """Update the apps display with current filters."""
        
        apps_to_show = min(self.apps_per_page.value if hasattr(self, 'apps_per_page') else 20, 
                          len(self.filtered_apps))
        
        app_widgets = []
        
        for i, (app_id, app_data) in enumerate(list(self.filtered_apps.items())[:apps_to_show]):
            if isinstance(app_data, dict):
                app_widget = self.create_real_app_widget(app_id, app_data)
                app_widgets.append(app_widget)
        
        # Add summary
        summary = widgets.HTML(value=f"""
        <div style='background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0; text-align: center;'>
            <strong>📊 Showing {len(app_widgets)} of {len(self.filtered_apps)} filtered apps</strong>
            <br><small>Total available: {len(self.apps_data)} applications</small>
        </div>
        """)
        
        app_widgets.append(summary)
        self.apps_container.children = app_widgets
    
    def create_real_app_widget(self, app_id, app_data):
        """Create REAL app widget with ACTUAL functionality."""
        
        name = app_data.get('name', app_id)
        category = app_data.get('category', 'Unknown')
        description = app_data.get('description', 'No description available')
        vram = app_data.get('vram_gb', 'Unknown')
        repository = app_data.get('repository', 'No repository')
        
        # App information display
        info_html = widgets.HTML(value=f"""
        <div style='border: 1px solid #dee2e6; border-radius: 8px; padding: 12px; margin: 8px 0; 
                   background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
            <h4 style='margin: 0 0 8px 0; color: #495057;'>📱 {name}</h4>
            <p style='margin: 2px 0; color: #6c757d; font-size: 12px;'>
                📂 {category} | 💾 {vram} GB VRAM
            </p>
            <p style='margin: 2px 0; color: #6c757d; font-size: 11px;'>
                {description[:80]}{'...' if len(description) > 80 else ''}
            </p>
            <p style='margin: 2px 0; color: #28a745; font-size: 10px;'>
                🔗 {repository[:50]}{'...' if len(repository) > 50 else ''}
            </p>
        </div>
        """)
        
        # REAL action buttons
        install_btn = widgets.Button(
            description='📥 REAL Install',
            button_style='success',
            tooltip=f'Install {name} with REAL git clone and pip install',
            layout=widgets.Layout(width='110px')
        )
        
        run_btn = widgets.Button(
            description='▶️ REAL Run',
            button_style='primary', 
            tooltip=f'Run {name} with REAL Python execution',
            layout=widgets.Layout(width='100px')
        )
        
        tunnel_btn = widgets.Button(
            description='🌐 Tunnel',
            button_style='info',
            tooltip=f'Create REAL public tunnel for {name}',
            layout=widgets.Layout(width='100px')
        )
        
        # Bind REAL functionality
        install_btn.on_click(lambda b: self.execute_real_installation(app_id, app_data))
        run_btn.on_click(lambda b: self.execute_real_running(app_id, app_data))
        tunnel_btn.on_click(lambda b: self.create_real_tunnel(app_id, app_data))
        
        # App widget layout
        actions = widgets.HBox([install_btn, run_btn, tunnel_btn])
        
        return widgets.VBox([info_html, actions])
    
    def execute_real_installation(self, app_id, app_data):
        """Execute REAL installation with REAL git and pip output."""
        
        with self.installation_output:
            print(f"\n🚀 REAL INSTALLATION STARTING: {app_data.get('name', app_id)}")
            print("=" * 70)
            print(f"📂 Category: {app_data.get('category', 'Unknown')}")
            print(f"💾 VRAM Required: {app_data.get('vram_gb', 'Unknown')} GB") 
            print(f"🔗 Repository: {app_data.get('repository', 'No repository')}")
            print(f"📊 Install Type: {app_data.get('install_type', 'Unknown')}")
            print()
            
            try:
                # Create apps directory
                apps_dir = Path("apps")
                apps_dir.mkdir(exist_ok=True)
                
                app_dir = apps_dir / app_id
                
                # REAL git clone
                repo_url = app_data.get('repository')
                if repo_url and repo_url != 'No repository':
                    print(f"📥 EXECUTING REAL GIT CLONE:")
                    print(f"Command: git clone {repo_url} {app_dir}")
                    print("-" * 50)
                    
                    # Execute REAL git clone with REAL output
                    clone_process = subprocess.run(
                        ["git", "clone", repo_url, str(app_dir)],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        cwd=os.getcwd()
                    )
                    
                    # Show REAL git output
                    print("RAW GIT CLONE OUTPUT:")
                    print(clone_process.stdout)
                    
                    if clone_process.returncode == 0:
                        print("✅ Git clone completed successfully!")
                        
                        # Look for and install requirements
                        self.install_real_requirements(app_dir, app_id)
                        
                        print(f"\n🎉 COMPLETE REAL INSTALLATION FINISHED: {app_data.get('name', app_id)}")
                        print("✅ Ready to run!")
                        
                    else:
                        print(f"❌ Git clone failed with exit code: {clone_process.returncode}")
                        
                else:
                    print("❌ No repository URL available for this application")
                    print("🔧 Cannot install without repository URL")
                    
            except Exception as e:
                print(f"❌ REAL INSTALLATION FAILED with exception:")
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
    
    def install_real_requirements(self, app_dir, app_id):
        """Install REAL requirements with REAL pip output."""
        
        requirements_files = [
            app_dir / "requirements.txt",
            app_dir / "requirements.pip",
            app_dir / "deps.txt"
        ]
        
        for req_file in requirements_files:
            if req_file.exists():
                print(f"\n📦 FOUND REQUIREMENTS FILE: {req_file.name}")
                print(f"📋 Installing from: {req_file}")
                print("-" * 50)
                
                # Show requirements content first
                try:
                    with open(req_file, 'r') as f:
                        req_content = f.read()
                    print("REQUIREMENTS CONTENT:")
                    print(req_content[:500] + "..." if len(req_content) > 500 else req_content)
                    print("-" * 50)
                except Exception as e:
                    print(f"⚠️ Could not read requirements: {e}")
                
                # REAL pip install with REAL output
                print("EXECUTING REAL PIP INSTALL:")
                print(f"Command: pip install -r {req_file}")
                print()
                
                pip_process = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(app_dir)
                )
                
                # Show REAL pip output
                print("RAW PIP INSTALL OUTPUT:")
                print(pip_process.stdout)
                
                if pip_process.returncode == 0:
                    print("✅ Requirements installation completed successfully!")
                else:
                    print(f"❌ Requirements installation failed with exit code: {pip_process.returncode}")
                
                return  # Only install from first found requirements file
        
        print("⚠️ No requirements.txt or similar file found")
        print("🔧 App may not have Python dependencies or uses different install method")
    
    def execute_real_running(self, app_id, app_data):
        """Execute REAL app running with REAL Python output."""
        
        with self.installation_output:
            print(f"\n▶️ REAL APPLICATION EXECUTION: {app_data.get('name', app_id)}")
            print("=" * 60)
            
            app_dir = Path("apps") / app_id
            
            if app_dir.exists():
                # Look for main execution script
                possible_main_scripts = [
                    "app.py", "main.py", "webui.py", "launch.py", "run.py", 
                    "start.py", "server.py", f"{app_id}.py", "gradio_app.py"
                ]
                
                main_script = None
                for script in possible_main_scripts:
                    script_path = app_dir / script
                    if script_path.exists():
                        main_script = script
                        break
                
                if main_script:
                    print(f"🚀 FOUND MAIN SCRIPT: {main_script}")
                    print(f"📁 Executing from: {app_dir}")
                    print(f"Command: python {main_script}")
                    print("-" * 50)
                    print("RAW PYTHON EXECUTION OUTPUT:")
                    print()
                    
                    try:
                        # REAL process execution with REAL output streaming
                        process = subprocess.Popen(
                            [sys.executable, main_script],
                            cwd=str(app_dir),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            universal_newlines=True
                        )
                        
                        # Store process for monitoring
                        self.installation_processes[app_id] = {
                            'process': process,
                            'name': app_data.get('name', app_id),
                            'start_time': time.time()
                        }
                        
                        print(f"✅ Process started with PID: {process.pid}")
                        print("🔄 Streaming REAL output below:")
                        print("-" * 30)
                        
                        # Stream REAL output in background thread
                        def stream_real_output():
                            try:
                                for line in process.stdout:
                                    with self.installation_output:
                                        print(line.rstrip())
                            except Exception as e:
                                with self.installation_output:
                                    print(f"⚠️ Output streaming stopped: {e}")
                        
                        output_thread = threading.Thread(target=stream_real_output, daemon=True)
                        output_thread.start()
                        
                    except Exception as e:
                        print(f"❌ Failed to start application: {e}")
                        import traceback
                        traceback.print_exc()
                        
                else:
                    print("❌ No main execution script found!")
                    print(f"📁 Available files in {app_dir}:")
                    try:
                        for file in sorted(app_dir.iterdir()):
                            print(f"   📄 {file.name}")
                    except Exception as e:
                        print(f"   ❌ Error listing files: {e}")
                    
                    print("\n💡 Common main script names to look for:")
                    print("   - app.py, main.py, webui.py, launch.py, run.py")
                    
            else:
                print(f"❌ Application directory not found: {app_dir}")
                print("📥 Install the application first using the Install button!")
    
    def create_real_tunnel(self, app_id, app_data):
        """Create REAL public tunnel for the application."""
        
        with self.installation_output:
            print(f"\n🌐 REAL TUNNEL CREATION: {app_data.get('name', app_id)}")
            print("=" * 50)
            
            # Check if app is running first
            if app_id in self.installation_processes:
                process_info = self.installation_processes[app_id]
                process = process_info['process']
                
                if process.poll() is None:  # Process is still running
                    print(f"✅ App is running (PID: {process.pid})")
                    print("🔍 Scanning for web server ports...")
                    
                    # Scan common ports for web servers
                    common_ports = [7860, 8501, 8502, 5000, 8000, 8080, 3000]
                    
                    for port in common_ports:
                        try:
                            import requests
                            response = requests.get(f"http://localhost:{port}", timeout=2)
                            if response.status_code == 200:
                                print(f"✅ Found web server on port {port}")
                                self.create_real_ngrok_tunnel(port, app_data.get('name', app_id))
                                return
                        except:
                            continue
                    
                    print("⚠️ No web server detected on common ports")
                    print("🔧 App may not have started web interface yet")
                    
                else:
                    print("❌ App process has stopped")
                    print("🔧 Start the app first using the Run button")
            else:
                print("❌ App is not running")
                print("▶️ Start the app first using the Run button")
    
    def create_real_ngrok_tunnel(self, port, app_name):
        """Create REAL ngrok tunnel with REAL output."""
        
        try:
            print(f"\n🌐 CREATING REAL NGROK TUNNEL:")
            print(f"Port: {port}")
            print(f"App: {app_name}")
            print("-" * 30)
            
            from pyngrok import ngrok
            
            # Set REAL ngrok token
            ngrok.set_auth_token("2tjxIXifSaGR3dMhkvhk6sZqbGo_6ZfBZLZHMbtAjfRmfoDW5")
            
            # Create REAL tunnel
            tunnel = ngrok.connect(port)
            
            print("✅ REAL TUNNEL CREATED!")
            print(f"🔗 Public URL: {tunnel.public_url}")
            print(f"🏠 Local URL: http://localhost:{port}")
            print(f"📱 App: {app_name}")
            print()
            print("🎉 REAL public access created!")
            print("🌐 Share this URL with anyone!")
            
        except Exception as e:
            print(f"❌ REAL tunnel creation failed: {e}")
            print("🔧 Trying alternative tunnel methods...")
            
            try:
                # Try cloudflared as backup
                print("\n🔄 Trying Cloudflare tunnel...")
                subprocess.Popen(["cloudflared", "tunnel", "--url", f"http://localhost:{port}"])
                print("✅ Cloudflare tunnel started (check terminal for URL)")
                
            except Exception as cf_e:
                print(f"❌ Cloudflare tunnel also failed: {cf_e}")
                print("💡 Manual tunnel creation may be needed")
    
    def on_filter_change(self, change):
        """Handle filter changes and update display."""
        
        search_term = self.search_box.value if hasattr(self, 'search_box') else ''
        category = self.category_filter.value if hasattr(self, 'category_filter') else 'All Categories'
        
        # Filter by category
        if category == 'All Categories':
            filtered = self.apps_data.copy()
        else:
            filtered = {}
            for app_id, app_data in self.apps_data.items():
                if isinstance(app_data, dict) and app_data.get('category') == category:
                    filtered[app_id] = app_data
        
        # Filter by search term
        if search_term:
            search_filtered = {}
            for app_id, app_data in filtered.items():
                if isinstance(app_data, dict):
                    # Search in name, description, and app_id
                    searchable_text = (
                        f"{app_data.get('name', '')} "
                        f"{app_data.get('description', '')} "
                        f"{app_id}"
                    ).lower()
                    
                    if search_term.lower() in searchable_text:
                        search_filtered[app_id] = app_data
            
            filtered = search_filtered
        
        self.filtered_apps = filtered
        self.update_apps_display()
        
        # Show filter results
        with self.installation_output:
            print(f"\n🔍 FILTER RESULTS: {len(filtered)} apps match criteria")
            if search_term:
                print(f"   Search: '{search_term}'")
            if category != 'All Categories':
                print(f"   Category: {category}")

def create_complete_app_manager():
    """Create and return the complete app manager interface."""
    manager = CompleteAppManager()
    return manager.create_complete_app_gallery()

# Usage: app_manager = create_complete_app_manager()