# Step 2: Create Simplified Notebook

## 🎯 Objective
Create a single, self-contained Jupyter notebook that replaces the entire complex multi-module system with a simple, reliable implementation.

## 📋 Implementation Instructions for AI Agent

### Step 2.1: Create New Notebook File
**Action**: Create `Pinokio_Cloud_Fixed.ipynb` with the following structure:

### Cell 1: Title and Setup
```python
#@title 🚀 Pinokio Cloud GPU - Simplified (Fixed Version)
#@markdown **One-click Pinokio setup with AI tools access**
#@markdown 
#@markdown This notebook provides a simplified, reliable setup for Pinokio on cloud GPU platforms.
#@markdown **Key improvements**: Fixed binary paths, no X11 complexity, multiple tunnel options.

print("🚀 PINOKIO CLOUD GPU - SIMPLIFIED VERSION")
print("=" * 50)
print("✅ Fixed binary path issues")  
print("✅ Removed X11 complexity")
print("✅ Multiple tunnel options (no signup required)")
print("✅ Better error handling")
print("=" * 50)
```

### Cell 2: Core Implementation
```python
#@title 📦 Setup Pinokio (One-Click Solution)
#@markdown Click run to automatically setup Pinokio with tunnel access

import os
import subprocess
import requests
import time
import json
from pathlib import Path

class PinokioCloudSimple:
    def __init__(self):
        self.pinokio_path = "/content/pinokio"
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
        """Download Pinokio with correct naming"""
        print("📥 Downloading Pinokio...")
        
        # Download with the name the controller expects
        self.binary_path = os.path.join(self.pinokio_path, "Pinokio-linux.AppImage")
        
        if os.path.exists(self.binary_path):
            print("✅ Pinokio already downloaded")
            return True
            
        try:
            # Use the actual download URL but save with correct name
            download_url = "https://github.com/pinokiocomputer/pinokio/releases/download/3.9.0/Pinokio-3.9.0.AppImage"
            
            result = subprocess.run([
                'wget', '-q', '--show-progress', 
                '-O', self.binary_path, 
                download_url
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
        """Start Pinokio web server (no X11 needed)"""
        print("🚀 Starting Pinokio web server...")
        
        if not self.binary_path or not os.path.exists(self.binary_path):
            print("❌ Pinokio binary not found")
            return False
            
        try:
            # Start in pure web server mode - NO X11 NEEDED!
            env = os.environ.copy()
            env['PINOKIO_APP_PORT'] = '42000'
            
            self.server_process = subprocess.Popen([
                self.binary_path, 
                '--no-sandbox', 
                '--headless'
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
            self.server_process.terminate()
        if self.tunnel_process:
            self.tunnel_process.terminate()

# Main execution
try:
    pinokio = PinokioCloudSimple()
    
    # Step-by-step setup
    pinokio.setup_directory()
    
    if not pinokio.download_pinokio():
        raise Exception("Failed to download Pinokio")
    
    if not pinokio.start_pinokio_server():
        raise Exception("Failed to start Pinokio server")
    
    tunnel_url = pinokio.setup_tunnel()
    
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
    
    # Save status for later cells
    _pinokio_instance = pinokio
    _pinokio_url = tunnel_url or "http://localhost:42000"
    
except Exception as e:
    print(f"\n❌ Setup failed: {e}")
    print("\n🔧 Troubleshooting:")
    print("1. Check if GPU runtime is enabled")
    print("2. Restart the notebook and try again")
    print("3. Check the status cell below for details")
```

### Cell 3: Status Check
```python
#@title 📊 Status Check
#@markdown Run this cell to check current Pinokio status

if '_pinokio_instance' in locals():
    status = _pinokio_instance.get_status()
    
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
        print("\n💡 Run the setup cell above to start Pinokio")
        
else:
    print("❌ Pinokio not initialized. Run the setup cell first.")
```

### Cell 4: Cleanup
```python
#@title 🧹 Cleanup (Optional)
#@markdown Run this to stop all Pinokio processes

if '_pinokio_instance' in locals():
    print("🧹 Stopping Pinokio processes...")
    _pinokio_instance.cleanup()
    print("✅ Cleanup complete")
else:
    print("❌ No active Pinokio instance found")
```

### Cell 5: Help & Troubleshooting
```python
#@title 💡 Help & Troubleshooting
print("💡 HELP & TROUBLESHOOTING")
print("=" * 40)
print()
print("🎯 What this does:")
print("• Downloads and runs Pinokio AI tool browser")
print("• Creates public tunnel for remote access")
print("• Provides access to 500+ AI tools")
print()
print("🔧 Common issues:")
print("• Binary not found → Re-run setup cell")
print("• Server won't start → Check GPU runtime enabled")
print("• Tunnel fails → Try different tunnel service")
print("• Slow startup → Wait up to 60 seconds")
print()
print("🌐 Tunnel services tried:")
print("1. Cloudflare Tunnel (no signup required)")
print("2. LocalTunnel (no signup required)")
print("3. Manual port forwarding (if above fail)")
print()
print("📚 After setup:")
print("• Click 'Discover' tab in Pinokio interface")
print("• Search for tools like 'Stable Diffusion'")
print("• Click 'Install' then 'Launch' on any tool")
print("• Each tool gets its own web interface")
```

## 📋 Step 2.2: Key Improvements Implemented

### ✅ Fixed Binary Path Issue
```python
# OLD (broken):
download_url = "https://...Pinokio-3.9.0.AppImage"
binary_path = "/content/pinokio/Pinokio-linux.AppImage"  # Mismatch!

# NEW (fixed):
download_url = "https://...Pinokio-3.9.0.AppImage" 
binary_path = "/content/pinokio/Pinokio-linux.AppImage"  # Download with correct name
subprocess.run(['wget', '-O', binary_path, download_url])  # Direct naming
```

### ✅ Removed X11 Complexity
```python
# OLD (complex):
apt install xvfb x11-utils xdpyinfo mesa-utils...
export DISPLAY=:0
Xvfb :0 -screen 0 1280x720x24 &

# NEW (simplified):
# NO X11 CODE AT ALL - just use --headless flag
subprocess.Popen([binary_path, '--no-sandbox', '--headless'])
```

### ✅ Multiple Tunnel Options
```python
# OLD (limited):
ngrok.connect(42000)  # Requires signup

# NEW (multiple options):
1. Cloudflare Tunnel (no signup)
2. LocalTunnel (no signup) 
3. Graceful fallback with instructions
```

### ✅ Better Error Handling
```python
# OLD (vague):
except Exception as e:
    print(f"Error: {e}")

# NEW (specific):
except requests.exceptions.RequestException:
    print("❌ Server startup timeout - checking process...")
    if self.server_process.poll() is not None:
        stdout, stderr = self.server_process.communicate()
        print(f"❌ Process exited with code {self.server_process.returncode}")
```

## 📋 Step 2.3: Testing Instructions for AI Agent

### Test 1: Basic Functionality
1. Run Cell 2 (Setup)
2. Verify no X11 errors appear
3. Confirm server starts on port 42000
4. Check tunnel URL is generated

### Test 2: Error Handling
1. Delete binary file
2. Run setup again
3. Verify clear error messages
4. Confirm graceful fallback behavior

### Test 3: Tunnel Fallbacks
1. Block Cloudflare domains (simulate failure)
2. Run setup
3. Verify LocalTunnel attempt
4. Confirm local URL provided if all fail

## ✅ Step 2 Completion Criteria
- [ ] Notebook runs without any X11 dependencies
- [ ] Binary downloads with correct naming
- [ ] Server starts and responds on port 42000
- [ ] At least one tunnel service works
- [ ] Clear error messages for all failure modes
- [ ] Status check provides useful diagnostics

---

**Status**: Ready for Step 3 (Optional Single-Class Implementation)