# Step 3: Single-Class Alternative (Optional)

## 🎯 Objective
Provide an alternative Python file implementation as a single class for environments where notebook format is not preferred.

## 📋 Implementation Instructions for AI Agent

### Step 3.1: Create `pinokio_cloud_simple.py`
**Action**: Create a single Python file that can be imported or run directly.

```python
#!/usr/bin/env python3
"""
Pinokio Cloud GPU - Simplified Implementation
============================================

A single-class solution for running Pinokio on cloud GPU platforms.
Fixes all major issues from the original multi-module implementation.

Key improvements:
- Fixed binary path mismatch
- Removed unnecessary X11 complexity  
- Multiple tunnel options (no signup required)
- Better error handling and diagnostics

Usage:
    from pinokio_cloud_simple import PinokioCloudSimple
    
    pinokio = PinokioCloudSimple()
    success = pinokio.full_setup()
    if success:
        print(f"Access Pinokio at: {pinokio.get_access_url()}")
"""

import os
import subprocess
import requests
import time
import json
import signal
import sys
from pathlib import Path
from typing import Optional, Dict, Any


class PinokioCloudSimple:
    """Simplified Pinokio cloud deployment class"""
    
    def __init__(self, pinokio_path: str = "/content/pinokio"):
        """Initialize with configurable path"""
        self.pinokio_path = pinokio_path
        self.binary_path = None
        self.server_process = None
        self.tunnel_process = None
        self.tunnel_url = None
        self.port = 42000
        
        # Setup cleanup handler
        signal.signal(signal.SIGTERM, self._cleanup_handler)
        signal.signal(signal.SIGINT, self._cleanup_handler)
    
    def _cleanup_handler(self, signum, frame):
        """Handle cleanup on exit"""
        self.cleanup()
        sys.exit(0)
    
    def detect_platform(self) -> str:
        """Simple platform detection"""
        if os.path.exists("/content"):
            return "colab"
        elif os.path.exists("/kaggle"):
            return "kaggle"  
        elif os.path.exists("/notebooks"):
            return "paperspace"
        else:
            return "unknown"
    
    def setup_directory(self) -> bool:
        """Create Pinokio directory structure"""
        print("📁 Setting up directory structure...")
        try:
            Path(self.pinokio_path).mkdir(parents=True, exist_ok=True)
            os.chdir(self.pinokio_path)
            
            # Create subdirectories that Pinokio expects
            for subdir in ["api", "bin", "cache", "drive", "logs"]:
                Path(self.pinokio_path, subdir).mkdir(exist_ok=True)
                
            print(f"✅ Directory ready: {self.pinokio_path}")
            return True
        except Exception as e:
            print(f"❌ Directory setup failed: {e}")
            return False
    
    def download_pinokio(self) -> bool:
        """Download Pinokio binary with correct naming"""
        print("📥 Downloading Pinokio binary...")
        
        # Use the exact name that the code expects
        self.binary_path = os.path.join(self.pinokio_path, "Pinokio-linux.AppImage")
        
        if os.path.exists(self.binary_path):
            print("✅ Pinokio binary already exists")
            return True
        
        try:
            # Download with correct naming from the start
            download_url = "https://github.com/pinokiocomputer/pinokio/releases/download/3.9.0/Pinokio-3.9.0.AppImage"
            
            print("⏳ Downloading... (this may take 1-2 minutes)")
            result = subprocess.run([
                'wget', '--quiet', '--show-progress', '--progress=bar:force:noscroll',
                '-O', self.binary_path, 
                download_url
            ], capture_output=False)  # Show progress directly
            
            if result.returncode != 0:
                print("❌ Download failed")
                return False
            
            # Make executable
            os.chmod(self.binary_path, 0o755)
            
            # Verify download
            if os.path.exists(self.binary_path) and os.access(self.binary_path, os.X_OK):
                file_size = os.path.getsize(self.binary_path) / (1024*1024)  # MB
                print(f"✅ Pinokio downloaded successfully ({file_size:.1f} MB)")
                return True
            else:
                print("❌ Binary verification failed")
                return False
                
        except Exception as e:
            print(f"❌ Download error: {e}")
            return False
    
    def start_server(self, timeout: int = 60) -> bool:
        """Start Pinokio server in headless mode"""
        print("🚀 Starting Pinokio server...")
        
        if not self.binary_path or not os.path.exists(self.binary_path):
            print("❌ Binary not found")
            return False
        
        try:
            # Environment variables for headless operation
            env = os.environ.copy()
            env['PINOKIO_APP_PORT'] = str(self.port)
            env['DISPLAY'] = ':99'  # Dummy display (not actually used)
            
            # Start server process - NO X11 DEPENDENCIES
            print("⏳ Starting server process...")
            self.server_process = subprocess.Popen([
                self.binary_path, 
                '--no-sandbox',
                '--headless'
            ], 
            env=env, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
            )
            
            # Wait for server to become ready
            print(f"⏳ Waiting for server on port {self.port}...")
            for i in range(timeout):
                try:
                    response = requests.get(f'http://localhost:{self.port}', timeout=3)
                    if response.status_code == 200:
                        print("✅ Pinokio server is running!")
                        return True
                except requests.exceptions.RequestException:
                    pass
                
                # Show progress and check if process crashed
                if i % 10 == 0 and i > 0:
                    print(f"⏳ Still waiting... ({i}/{timeout}s)")
                
                if self.server_process.poll() is not None:
                    # Process ended unexpectedly
                    stdout, stderr = self.server_process.communicate()
                    print("❌ Server process crashed:")
                    print(f"Exit code: {self.server_process.returncode}")
                    if stderr:
                        print(f"Error output: {stderr[:500]}...")
                    return False
                
                time.sleep(1)
            
            print("❌ Server startup timeout")
            return False
            
        except Exception as e:
            print(f"❌ Server startup error: {e}")
            return False
    
    def setup_cloudflare_tunnel(self) -> Optional[str]:
        """Setup Cloudflare tunnel - no authentication required"""
        print("🌐 Setting up Cloudflare tunnel...")
        
        try:
            # Download cloudflared binary
            cf_path = '/tmp/cloudflared'
            if not os.path.exists(cf_path):
                print("📥 Downloading Cloudflare tunnel client...")
                result = subprocess.run([
                    'wget', '-q', '-O', cf_path,
                    'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64'
                ], timeout=30)
                
                if result.returncode != 0:
                    print("❌ Failed to download cloudflared")
                    return None
                    
                os.chmod(cf_path, 0o755)
            
            # Start tunnel
            print("⏳ Creating tunnel...")
            self.tunnel_process = subprocess.Popen([
                cf_path, 'tunnel', '--url', f'http://localhost:{self.port}'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Parse output for tunnel URL
            for _ in range(30):  # 30 second timeout
                line = self.tunnel_process.stdout.readline()
                if not line:
                    time.sleep(1)
                    continue
                    
                # Look for the tunnel URL
                if 'trycloudflare.com' in line:
                    words = line.split()
                    for word in words:
                        if 'trycloudflare.com' in word and word.startswith('http'):
                            self.tunnel_url = word.strip()
                            print(f"✅ Tunnel ready: {self.tunnel_url}")
                            return self.tunnel_url
            
            print("❌ Cloudflare tunnel setup failed")
            return None
            
        except Exception as e:
            print(f"❌ Cloudflare tunnel error: {e}")
            return None
    
    def setup_localtunnel(self) -> Optional[str]:
        """Setup LocalTunnel alternative"""
        print("🌐 Setting up LocalTunnel...")
        
        try:
            # Check if Node.js is available
            result = subprocess.run(['node', '--version'], capture_output=True)
            if result.returncode != 0:
                print("❌ Node.js not available for LocalTunnel")
                return None
            
            # Install localtunnel
            print("📥 Installing LocalTunnel...")
            result = subprocess.run(['npm', 'install', '-g', 'localtunnel'], 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"❌ LocalTunnel install failed: {result.stderr}")
                return None
            
            # Start tunnel
            print("⏳ Starting LocalTunnel...")
            self.tunnel_process = subprocess.Popen([
                'lt', '--port', str(self.port)
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Parse output for URL
            for _ in range(20):
                line = self.tunnel_process.stdout.readline()
                if 'https://' in line and 'loca.lt' in line:
                    url = line.strip().split()[-1]  # Last word should be URL
                    if url.startswith('https://'):
                        self.tunnel_url = url
                        print(f"✅ LocalTunnel ready: {self.tunnel_url}")
                        return self.tunnel_url
                time.sleep(1)
            
            print("❌ LocalTunnel setup failed")
            return None
            
        except Exception as e:
            print(f"❌ LocalTunnel error: {e}")
            return None
    
    def setup_tunnel(self) -> Optional[str]:
        """Try multiple tunnel services in order of preference"""
        print("🌐 Setting up public tunnel access...")
        
        # Try Cloudflare first (most reliable)
        url = self.setup_cloudflare_tunnel()
        if url:
            return url
        
        print("⚠️ Cloudflare failed, trying LocalTunnel...")
        url = self.setup_localtunnel()
        if url:
            return url
        
        print("❌ All tunnel services failed")
        print("💡 Server is still accessible locally")
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information"""
        status = {
            'platform': self.detect_platform(),
            'directory_exists': os.path.exists(self.pinokio_path),
            'binary_exists': self.binary_path and os.path.exists(self.binary_path),
            'server_running': False,
            'server_responsive': False,
            'tunnel_active': self.tunnel_url is not None,
            'tunnel_url': self.tunnel_url,
            'local_url': f'http://localhost:{self.port}',
            'processes': {
                'server_pid': self.server_process.pid if self.server_process else None,
                'tunnel_pid': self.tunnel_process.pid if self.tunnel_process else None
            }
        }
        
        # Check server status
        if self.server_process:
            status['server_running'] = self.server_process.poll() is None
        
        # Check server responsiveness
        try:
            response = requests.get(f'http://localhost:{self.port}', timeout=3)
            status['server_responsive'] = response.status_code == 200
        except:
            status['server_responsive'] = False
        
        return status
    
    def get_access_url(self) -> str:
        """Get the best URL to access Pinokio"""
        if self.tunnel_url:
            return self.tunnel_url
        else:
            return f'http://localhost:{self.port}'
    
    def full_setup(self) -> bool:
        """Complete setup process"""
        print("🚀 PINOKIO CLOUD SETUP - SIMPLIFIED")
        print("=" * 50)
        
        # Step-by-step setup
        if not self.setup_directory():
            return False
        
        if not self.download_pinokio():
            return False
        
        if not self.start_server():
            return False
        
        # Tunnel setup (optional - server works without it)
        tunnel_url = self.setup_tunnel()
        
        # Results
        print("\n🎉 SETUP COMPLETE!")
        print("=" * 30)
        
        if tunnel_url:
            print(f"🌍 Public Access: {tunnel_url}")
        else:
            print(f"🖥️  Local Access: http://localhost:{self.port}")
        
        print("\n📋 Next Steps:")
        print("• Open the URL above in your browser")
        print("• Click 'Discover' to browse AI tools")
        print("• Install tools with one-click setup")
        
        return True
    
    def cleanup(self):
        """Stop all processes and cleanup"""
        print("🧹 Cleaning up processes...")
        
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("✅ Server process stopped")
            except:
                self.server_process.kill()
        
        if self.tunnel_process:
            try:
                self.tunnel_process.terminate()
                self.tunnel_process.wait(timeout=5)
                print("✅ Tunnel process stopped")
            except:
                self.tunnel_process.kill()


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Pinokio Cloud GPU Setup')
    parser.add_argument('--path', default='/content/pinokio', 
                       help='Installation path (default: /content/pinokio)')
    parser.add_argument('--port', type=int, default=42000,
                       help='Server port (default: 42000)')
    parser.add_argument('--no-tunnel', action='store_true',
                       help='Skip tunnel setup')
    parser.add_argument('--status', action='store_true',
                       help='Show status only')
    
    args = parser.parse_args()
    
    pinokio = PinokioCloudSimple(args.path)
    pinokio.port = args.port
    
    if args.status:
        status = pinokio.get_status()
        print(json.dumps(status, indent=2))
    else:
        try:
            if pinokio.full_setup():
                print("\n✅ Setup completed successfully!")
                print("Press Ctrl+C to stop")
                
                # Keep running
                while True:
                    time.sleep(60)
                    if pinokio.server_process and pinokio.server_process.poll() is not None:
                        print("❌ Server process died unexpectedly")
                        break
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        finally:
            pinokio.cleanup()
```

### Step 3.2: Usage Examples

#### Jupyter Notebook Usage
```python
# Cell 1: Import and setup
from pinokio_cloud_simple import PinokioCloudSimple

pinokio = PinokioCloudSimple()
success = pinokio.full_setup()

# Cell 2: Check status
status = pinokio.get_status()
print(f"Status: {status}")

# Cell 3: Get access URL
if success:
    print(f"Access Pinokio at: {pinokio.get_access_url()}")
```

#### Command Line Usage  
```bash
# Basic setup
python pinokio_cloud_simple.py

# Custom path and port
python pinokio_cloud_simple.py --path /custom/path --port 8080

# Skip tunnel setup (local only)
python pinokio_cloud_simple.py --no-tunnel

# Check status
python pinokio_cloud_simple.py --status
```

#### Python Script Usage
```python
#!/usr/bin/env python3
from pinokio_cloud_simple import PinokioCloudSimple
import time

def main():
    # Setup Pinokio
    pinokio = PinokioCloudSimple("/tmp/pinokio")
    
    if not pinokio.full_setup():
        print("Setup failed!")
        return 1
    
    # Keep running and monitor
    try:
        print("Pinokio is running. Press Ctrl+C to stop.")
        while True:
            status = pinokio.get_status()
            if not status['server_responsive']:
                print("⚠️ Server not responding, restarting...")
                pinokio.start_server()
            time.sleep(30)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        pinokio.cleanup()
    
    return 0

if __name__ == "__main__":
    exit(main())
```

## 📋 Step 3.3: Advantages of Single-Class Approach

### ✅ Benefits
- **Importable**: Can be used as a module in other projects
- **CLI Support**: Direct command-line execution
- **Better IDE Support**: Full IDE features (debugging, autocomplete)
- **Type Hints**: Better code documentation and validation
- **Testable**: Easier to write unit tests
- **Reusable**: Can be integrated into larger applications

### ✅ Use Cases
- Integration into existing Python projects
- Automated deployment scripts  
- CI/CD pipeline integration
- Custom cloud platform adaptations
- Local development environment setup

### ⚠️ Considerations
- Requires Python environment setup
- Less user-friendly than notebook for beginners
- More setup overhead for simple use cases

## 📋 Step 3.4: Integration with Original Notebook

### Option A: Replace Notebook Entirely
- Delete original complex notebook
- Replace with simple notebook calling this class
- Benefits: Cleaner, more maintainable

### Option B: Provide Both Options
- Keep simplified notebook for beginners
- Provide class file for advanced users
- Benefits: Flexibility for different use cases

### Recommended Structure
```
pinokio-cloud-fixed/
├── Pinokio_Cloud_Simple.ipynb      # Beginner-friendly notebook
├── pinokio_cloud_simple.py         # Advanced Python class
├── requirements.txt                 # Minimal dependencies  
├── README.md                        # Usage instructions
└── examples/
    ├── basic_usage.py
    ├── custom_integration.py
    └── monitoring_script.py
```

## ✅ Step 3 Completion Criteria
- [ ] Single class handles all functionality
- [ ] CLI interface works correctly
- [ ] Can be imported as module  
- [ ] Type hints and documentation complete
- [ ] Examples demonstrate key use cases
- [ ] Integration path with notebook defined

---

**Status**: Ready for Step 4 (Testing and Validation)