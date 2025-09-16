#!/usr/bin/env python3
"""
🚀 Pinokio Cloud GPU - Simple Python Class

Reliable one-click Pinokio setup for Google Colab and cloud platforms.

Usage:
    python pinokio_cloud_simple.py              # Auto setup
    python pinokio_cloud_simple.py --setup      # Manual setup
    python pinokio_cloud_simple.py --status     # Check status
    python pinokio_cloud_simple.py --cleanup    # Stop services
"""

import os
import subprocess
import requests
import time
import json
import argparse
from pathlib import Path


class PinokioCloudSimple:
    def __init__(self, base_path="/content/pinokio"):
        self.pinokio_path = base_path
        self.binary_path = None
        self.server_process = None
        self.tunnel_process = None
        self.tunnel_url = None
        
    def setup_directory(self):
        """Create Pinokio directory structure"""
        print("📁 Setting up directory...")
        Path(self.pinokio_path).mkdir(parents=True, exist_ok=True)
        os.chdir(self.pinokio_path)
        print(f"✅ Created directory: {self.pinokio_path}")
        
    def download_pinokio(self):
        """Download Pinokio with correct naming - FIX THE MISMATCH!"""
        print("📥 Downloading Pinokio...")
        
        # CRITICAL FIX: Download with the name the controller expects
        self.binary_path = os.path.join(self.pinokio_path, "Pinokio-linux.AppImage")
        
        if os.path.exists(self.binary_path):
            print("✅ Pinokio already downloaded")
            return True
            
        try:
            # Use the actual download URL but save with correct name
            download_url = "https://github.com/pinokiocomputer/pinokio/releases/download/3.9.0/Pinokio-3.9.0.AppImage"
            
            result = subprocess.run([
                'wget', '-q', '--show-progress', 
                '-O', self.binary_path,  # Save as Pinokio-linux.AppImage
                download_url             # Download Pinokio-3.9.0.AppImage
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Download failed: {result.stderr}")
                return False
                
            # Make executable
            os.chmod(self.binary_path, 0o755)
            
            # Verify file exists and is executable
            if os.path.exists(self.binary_path) and os.access(self.binary_path, os.X_OK):
                print("✅ Pinokio downloaded and configured")
                return True
            else:
                print("❌ Binary not properly configured")
                return False
                
        except Exception as e:
            print(f"❌ Download error: {e}")
            return False
    
    def start_pinokio_server(self):
        """Start Pinokio web server - NO X11 NEEDED!"""
        print("🚀 Starting Pinokio web server...")
        
        if not self.binary_path or not os.path.exists(self.binary_path):
            print("❌ Pinokio binary not found")
            return False
            
        try:
            # Start in pure web server mode - NO X11 DEPENDENCIES!
            env = os.environ.copy()
            env['PINOKIO_APP_PORT'] = '42000'
            
            self.server_process = subprocess.Popen([
                self.binary_path, 
                '--no-sandbox',              # No sandboxing needed
                '--headless',                # Pure web interface
                '--disable-dev-shm-usage',   # Fix shared memory issues
                '--disable-gpu',             # No GPU access needed for server
                '--no-first-run',            # Skip first run setup
                '--disable-default-apps',    # No default apps
                '--disable-extensions',      # No extensions
                '--disable-features=VizDisplayCompositor'  # Fix D-Bus issues
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for server to start
            print("⏳ Waiting for server startup...")
            for i in range(30):  # 30 second timeout
                try:
                    response = requests.get('http://localhost:42000', timeout=2)
                    if response.status_code == 200:
                        print("✅ Pinokio web server running on port 42000")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)
                    if i % 5 == 0:  # Show progress every 5 seconds
                        print(f"⏳ Still waiting... ({i+1}/30)")
                        
            print("❌ Server startup timeout - checking process...")
            if self.server_process.poll() is not None:
                stdout, stderr = self.server_process.communicate()
                print(f"❌ Process exited with code {self.server_process.returncode}")
                print(f"Error: {stderr[:500]}")  # First 500 chars of error
            return False
            
        except Exception as e:
            print(f"❌ Server startup error: {e}")
            return False
    
    def setup_cloudflare_tunnel(self, port=42000):
        """Setup Cloudflare tunnel (no auth required)"""
        print("🌐 Setting up Cloudflare tunnel...")
        
        try:
            # Download cloudflared
            cf_path = '/tmp/cloudflared'
            if not os.path.exists(cf_path):
                print("📥 Downloading Cloudflare tunnel...")
                subprocess.run([
                    'wget', '-q', '-O', cf_path,
                    'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64'
                ])
                os.chmod(cf_path, 0o755)
            
            # Start tunnel
            self.tunnel_process = subprocess.Popen([
                cf_path, 'tunnel', '--url', f'http://localhost:{port}'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Extract tunnel URL
            print("⏳ Starting tunnel...")
            for _ in range(30):
                line = self.tunnel_process.stdout.readline()
                if 'trycloudflare.com' in line:
                    # Extract URL from line
                    for part in line.split():
                        if 'trycloudflare.com' in part:
                            self.tunnel_url = part.strip()
                            print(f"✅ Cloudflare tunnel created: {self.tunnel_url}")
                            return self.tunnel_url
                time.sleep(1)
            
            print("❌ Cloudflare tunnel setup failed")
            return None
            
        except Exception as e:
            print(f"❌ Cloudflare tunnel error: {e}")
            return None
    
    def setup_localtunnel(self, port=42000):
        """Setup LocalTunnel (no auth required)"""
        print("🌐 Setting up LocalTunnel...")
        
        try:
            # Install localtunnel via npm
            print("📥 Installing LocalTunnel...")
            result = subprocess.run(['npm', 'install', '-g', 'localtunnel'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ LocalTunnel install failed: {result.stderr}")
                return None
            
            # Start tunnel
            self.tunnel_process = subprocess.Popen([
                'lt', '--port', str(port)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Extract URL
            print("⏳ Starting LocalTunnel...")
            for _ in range(20):
                line = self.tunnel_process.stdout.readline()
                if 'https://' in line and 'loca.lt' in line:
                    self.tunnel_url = line.strip()
                    print(f"✅ LocalTunnel created: {self.tunnel_url}")
                    return self.tunnel_url
                time.sleep(1)
            
            print("❌ LocalTunnel setup failed")
            return None
            
        except Exception as e:
            print(f"❌ LocalTunnel error: {e}")
            return None
    
    def setup_tunnel(self):
        """Try multiple tunnel services with fallbacks"""
        print("🌐 Setting up public tunnel...")
        
        # Try Cloudflare first (most reliable, no auth)
        url = self.setup_cloudflare_tunnel()
        if url:
            return url
            
        print("⚠️ Cloudflare failed, trying LocalTunnel...")
        url = self.setup_localtunnel()
        if url:
            return url
            
        print("❌ All tunnel services failed")
        print("💡 Pinokio is still running locally at: http://localhost:42000")
        return None
    
    def get_status(self):
        """Get current status"""
        status = {
            'directory_ready': os.path.exists(self.pinokio_path),
            'binary_ready': self.binary_path and os.path.exists(self.binary_path),
            'server_running': False,
            'tunnel_active': self.tunnel_url is not None,
            'tunnel_url': self.tunnel_url
        }
        
        # Check if server is responding
        try:
            response = requests.get('http://localhost:42000', timeout=2)
            status['server_running'] = response.status_code == 200
        except:
            status['server_running'] = False
            
        return status
    
    def cleanup(self):
        """Stop all processes"""
        if self.server_process:
            print("🛑 Stopping Pinokio server...")
            self.server_process.terminate()
            self.server_process = None
        if self.tunnel_process:
            print("🛑 Stopping tunnel...")
            self.tunnel_process.terminate()  
            self.tunnel_process = None
        self.tunnel_url = None
        print("✅ Cleanup complete")
    
    def run_full_setup(self):
        """Complete setup process"""
        try:
            self.setup_directory()
            
            if not self.download_pinokio():
                raise Exception("Failed to download Pinokio")
            
            if not self.start_pinokio_server():
                raise Exception("Failed to start Pinokio server")
            
            tunnel_url = self.setup_tunnel()
            
            # Final results
            print("\n" + "🎉 SETUP COMPLETE! " + "🎉")
            print("=" * 50)
            
            if tunnel_url:
                print(f"🌍 Public URL: {tunnel_url}")
                print("📱 Click the link above to access Pinokio!")
            else:
                print("🖥️  Local URL: http://localhost:42000")
                print("💡 Access locally or setup port forwarding")
            
            print("\n📋 What you can do now:")
            print("• Browse the 'Discover' tab for 500+ AI tools")
            print("• Install Stable Diffusion, ComfyUI, etc. with one click")
            print("• Access all tools through the web interface")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            print("\n🔧 Troubleshooting:")
            print("1. Check if GPU runtime is enabled")
            print("2. Restart the notebook and try again")
            print("3. Check the status with --status flag")
            return False
    
    def print_status(self):
        """Print detailed status"""
        status = self.get_status()
        
        print("📊 PINOKIO STATUS")
        print("=" * 30)
        print(f"📁 Directory: {'✅' if status['directory_ready'] else '❌'}")
        print(f"📦 Binary: {'✅' if status['binary_ready'] else '❌'}")
        print(f"🚀 Server: {'✅ Running' if status['server_running'] else '❌ Stopped'}")
        print(f"🌐 Tunnel: {'✅ Active' if status['tunnel_active'] else '❌ Inactive'}")
        
        if status['tunnel_url']:
            print(f"\n🔗 Access URL: {status['tunnel_url']}")
        elif status['server_running']:
            print(f"\n🔗 Local URL: http://localhost:42000")
        else:
            print("\n💡 Run setup to start Pinokio")


def main():
    parser = argparse.ArgumentParser(description='Pinokio Cloud GPU Setup')
    parser.add_argument('--setup', action='store_true', help='Run full setup')
    parser.add_argument('--status', action='store_true', help='Show status')
    parser.add_argument('--cleanup', action='store_true', help='Stop all services')
    parser.add_argument('--path', default='/content/pinokio', help='Pinokio installation path')
    
    args = parser.parse_args()
    
    pinokio = PinokioCloudSimple(args.path)
    
    if args.status:
        pinokio.print_status()
    elif args.cleanup:
        pinokio.cleanup()
    elif args.setup:
        pinokio.run_full_setup()
    else:
        # Default: auto setup
        print("🚀 PINOKIO CLOUD GPU - SIMPLIFIED VERSION")
        print("=" * 50)
        print("✅ Fixed binary path issues")  
        print("✅ Removed X11 complexity")
        print("✅ Multiple tunnel options (no signup required)")
        print("✅ Better error handling")
        print("=" * 50)
        pinokio.run_full_setup()


if __name__ == "__main__":
    main()
