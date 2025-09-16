#!/usr/bin/env python3
"""
PinokioCloud Main Notebook Interface
Orchestrates all notebook UI components with organized scripts
"""

import ipywidgets as widgets
from IPython.display import display, HTML

def create_complete_interface():
    """Create the complete PinokioCloud notebook interface."""
    
    # Import the organized components
    try:
        from notebook_ui.app_browser import create_app_browser
        from notebook_ui.system_monitor import create_system_monitor
        from notebook_ui.terminal_widget import create_terminal
        from notebook_ui.tunnel_manager import create_tunnel_manager
        
        # Create tabbed interface
        tab_contents = [
            create_app_browser(),
            create_system_monitor(), 
            create_terminal(),
            create_tunnel_manager()
        ]
        
        tabs = widgets.Tab(children=tab_contents)
        tabs.set_title(0, '🏪 Apps')
        tabs.set_title(1, '📊 Monitor')
        tabs.set_title(2, '💻 Terminal')
        tabs.set_title(3, '🌐 Tunnels')
        
        # Main header
        main_header = widgets.HTML(value="""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;'>
            <h2>🚀 PinokioCloud Complete Interface</h2>
            <p>284 AI Applications | Multi-Cloud Support | Real-time Monitoring</p>
        </div>
        """)
        
        # Status bar
        status_bar = widgets.HTML(value="""
        <div style='background: #d4edda; padding: 10px; border-radius: 5px; border: 1px solid #c3e6cb; margin-bottom: 15px;'>
            <strong>📍 Status:</strong> PinokioCloud active | 
            <strong>🎯 Ready:</strong> Browse, install, and run AI applications
        </div>
        """)
        
        # Complete interface
        complete_ui = widgets.VBox([main_header, status_bar, tabs])
        
        display(complete_ui)
        
        return complete_ui
        
    except ImportError as e:
        # Fallback simple interface
        print(f"⚠️ Organized components not available: {e}")
        print("🔧 Using simple fallback interface...")
        
        return create_simple_fallback()

def create_simple_fallback():
    """Create simple fallback interface if organized scripts fail."""
    
    # Simple header
    header = widgets.HTML(value="""
    <div style='background: #667eea; padding: 15px; border-radius: 10px; color: white; text-align: center;'>
        <h3>🚀 PinokioCloud Simple Interface</h3>
        <p>Fallback mode - Basic functionality</p>
    </div>
    """)
    
    # Simple app selector
    app_selector = widgets.Dropdown(
        options=[
            'Select Application...',
            '🎨 AUTOMATIC1111 (Stable Diffusion)',
            '🎭 FaceFusion (Face Swapping)',
            '📝 Text-Generation-WebUI',
            '🎵 RVC (Voice Cloning)',
            '🎬 ComfyUI (Advanced Image Generation)'
        ],
        description='App:',
        layout=widgets.Layout(width='400px')
    )
    
    # Action buttons
    install_btn = widgets.Button(description='📥 Install', button_style='success')
    run_btn = widgets.Button(description='▶️ Run', button_style='primary')
    tunnel_btn = widgets.Button(description='🌐 Tunnel', button_style='info')
    
    # Output area
    output = widgets.Output()
    
    # Button handlers
    def on_install(b):
        with output:
            print(f"📥 Installing: {app_selector.value}")
            print("⏳ This would install the selected application...")
            print("✅ Installation simulation complete!")
    
    def on_run(b):
        with output:
            print(f"▶️ Running: {app_selector.value}")
            print("🚀 This would start the application...")
            print("🌐 Public URL would be created...")
    
    def on_tunnel(b):
        with output:
            print("🌐 Creating tunnel for port 8501...")
            print("🔗 Public URL would appear here...")
    
    install_btn.on_click(on_install)
    run_btn.on_click(on_run)
    tunnel_btn.on_click(on_tunnel)
    
    # Layout
    controls = widgets.HBox([app_selector])
    actions = widgets.HBox([install_btn, run_btn, tunnel_btn])
    
    fallback_ui = widgets.VBox([header, controls, actions, output])
    
    display(fallback_ui)
    return fallback_ui

# Main function for notebook cells
def launch_notebook_ui():
    """Main function to launch the complete notebook UI."""
    print("📱 Loading PinokioCloud Notebook Interface...")
    print("=" * 45)
    
    try:
        ui = create_complete_interface()
        print("✅ Complete interface loaded successfully!")
        return ui
    except Exception as e:
        print(f"⚠️ Complete interface failed: {e}")
        print("🔧 Loading fallback interface...")
        ui = create_simple_fallback()
        print("✅ Fallback interface loaded!")
        return ui

# Usage in notebook: exec(open('github_repo/notebook_ui/main_interface.py').read()); launch_notebook_ui()