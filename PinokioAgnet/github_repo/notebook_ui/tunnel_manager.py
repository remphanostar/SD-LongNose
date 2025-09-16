#!/usr/bin/env python3
"""
PinokioCloud Tunnel Manager for Notebook
Simple tunnel creation and management using ipywidgets
"""

import subprocess
import ipywidgets as widgets
from IPython.display import display
import time

class TunnelManager:
    """Simple tunnel manager for notebook."""
    
    def __init__(self):
        self.active_tunnels = {}
        
    def create_tunnel_manager(self):
        """Create tunnel management interface."""
        
        # Header
        header = widgets.HTML(value="""
        <div style='background: linear-gradient(45deg, #17a2b8, #20c997); 
                   padding: 15px; border-radius: 10px; color: white; text-align: center; margin-bottom: 15px;'>
            <h3>🌐 Tunnel Manager</h3>
            <p>Create public access for applications</p>
        </div>
        """)
        
        # Port input
        self.port_input = widgets.IntText(
            value=8501,
            description='Port:',
            layout=widgets.Layout(width='150px')
        )
        
        # Tunnel type selector
        tunnel_type = widgets.Dropdown(
            options=['ngrok', 'cloudflare'],
            value='ngrok',
            description='Type:',
            layout=widgets.Layout(width='150px')
        )
        
        # Create tunnel button
        create_btn = widgets.Button(
            description='🌐 Create Tunnel',
            button_style='success',
            layout=widgets.Layout(width='150px')
        )
        
        # Active tunnels display
        self.tunnels_display = widgets.HTML(value=self.get_tunnels_html())
        
        # Output area
        self.output = widgets.Output()
        
        # Bind events
        create_btn.on_click(lambda b: self.create_tunnel(self.port_input.value, tunnel_type.value))
        
        # Layout
        controls = widgets.HBox([self.port_input, tunnel_type, create_btn])
        
        return widgets.VBox([header, controls, self.tunnels_display, self.output])
    
    def create_tunnel(self, port, tunnel_type):
        """Create a new tunnel."""
        with self.output:
            print(f"🌐 Creating {tunnel_type} tunnel for port {port}...")
        
        try:
            if tunnel_type == 'ngrok':
                self.create_ngrok_tunnel(port)
            else:
                self.create_cloudflare_tunnel(port)
        except Exception as e:
            with self.output:
                print(f"❌ Tunnel creation failed: {e}")
    
    def create_ngrok_tunnel(self, port):
        """Create ngrok tunnel."""
        try:
            from pyngrok import ngrok
            
            # Set token
            ngrok.set_auth_token("2tjxIXifSaGR3dMhkvhk6sZqbGo_6ZfBZLZHMbtAjfRmfoDW5")
            
            # Create tunnel
            tunnel = ngrok.connect(port)
            
            # Save tunnel info
            tunnel_id = f"ngrok_{port}_{int(time.time())}"
            self.active_tunnels[tunnel_id] = {
                'type': 'ngrok',
                'port': port,
                'url': tunnel.public_url,
                'status': 'Active'
            }
            
            # Update display
            self.tunnels_display.value = self.get_tunnels_html()
            
            with self.output:
                print(f"✅ Ngrok tunnel created: {tunnel.public_url}")
                
        except Exception as e:
            with self.output:
                print(f"❌ Ngrok failed: {e}")
                print("🔄 Try cloudflare instead")
    
    def create_cloudflare_tunnel(self, port):
        """Create cloudflare tunnel."""
        try:
            with self.output:
                print(f"🔄 Starting cloudflare tunnel for port {port}...")
                print("💡 Check terminal for public URL")
            
            # Start cloudflare tunnel
            subprocess.Popen([
                'cloudflared', 'tunnel', '--url', f'http://localhost:{port}'
            ])
            
            # Add to display (URL will be shown in terminal)
            tunnel_id = f"cloudflare_{port}_{int(time.time())}"
            self.active_tunnels[tunnel_id] = {
                'type': 'cloudflare',
                'port': port,
                'url': 'Check terminal for URL',
                'status': 'Starting'
            }
            
            self.tunnels_display.value = self.get_tunnels_html()
            
        except Exception as e:
            with self.output:
                print(f"❌ Cloudflare failed: {e}")
    
    def get_tunnels_html(self):
        """Get HTML for active tunnels display."""
        if not self.active_tunnels:
            return """
            <div style='background: #fff3cd; padding: 15px; border-radius: 8px; border: 1px solid #ffeeba; margin: 10px 0;'>
                <h4>🌐 Active Tunnels</h4>
                <p>No active tunnels. Create one above to share your applications.</p>
            </div>
            """
        
        tunnel_cards = []
        for tunnel_id, info in self.active_tunnels.items():
            card = f"""
            <div style='background: #d1ecf1; padding: 10px; border-radius: 5px; margin: 5px 0; border: 1px solid #bee5eb;'>
                <strong>🌐 {info['type'].title()} Tunnel</strong><br/>
                <strong>Port:</strong> {info['port']} | <strong>Status:</strong> {info['status']}<br/>
                <strong>URL:</strong> <a href="{info['url']}" target="_blank">{info['url']}</a>
            </div>
            """
            tunnel_cards.append(card)
        
        return f"""
        <div style='background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 10px 0;'>
            <h4>🌐 Active Tunnels ({len(self.active_tunnels)})</h4>
            {''.join(tunnel_cards)}
        </div>
        """

def create_tunnel_manager():
    """Create and return tunnel manager widget."""
    manager = TunnelManager()
    return manager.create_tunnel_manager()

# Usage: tunnel_widget = create_tunnel_manager()