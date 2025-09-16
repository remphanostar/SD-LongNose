# 🔧 CRITICAL FIX: D-Bus Error Resolution

## 🚨 Problem Identified

The error you're seeing is:
```
❌ Process exited with code -5
Error: Failed to connect to the bus: Failed to connect to socket /run/dbus/system_bus_socket: No such file or directory
```

This happens because Electron (which Pinokio uses) tries to connect to system services (D-Bus) that don't exist in Colab's containerized environment.

## ✅ Solution: Additional Electron Flags

Replace the server startup code with these additional flags:

### In the Notebook (Cell 2, `start_pinokio_server` method):

```python
def start_pinokio_server(self):
    """Start Pinokio web server - FIXED FOR COLAB CONTAINERS"""
    print("🚀 Starting Pinokio web server...")
    
    if not self.binary_path or not os.path.exists(self.binary_path):
        print("❌ Pinokio binary not found")
        return False
    
    try:
        # Environment setup
        env = os.environ.copy()
        env['PINOKIO_APP_PORT'] = '42000'
        
        # CRITICAL FIX: Add container-friendly Electron flags
        self.server_process = subprocess.Popen([
            self.binary_path,
            '--no-sandbox',                           # Disable Chrome sandbox
            '--headless',                             # No GUI
            '--disable-dev-shm-usage',               # Fix shared memory issues
            '--disable-gpu',                         # Disable GPU for UI (not AI models)  
            '--disable-software-rasterizer',         # Disable fallback rendering
            '--no-first-run',                        # Skip first run setup
            '--disable-background-timer-throttling', # Prevent throttling
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',        # Disable extra features
            '--disable-ipc-flooding-protection',     # Fix IPC issues
            '--disable-extensions',                  # Disable Chrome extensions
            '--disable-plugins',                     # Disable plugins
            '--disable-sync',                        # Disable Chrome sync
            '--disable-default-apps'                 # Disable default apps
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for server to start
        print("⏳ Waiting for server startup...")
        for i in range(45):  # Increased timeout to 45 seconds
            try:
                response = requests.get('http://localhost:42000', timeout=3)
                if response.status_code == 200:
                    print("✅ Pinokio web server running on port 42000")
                    return True
            except requests.exceptions.RequestException:
                time.sleep(1)
                if i % 5 == 0:  # Show progress every 5 seconds
                    print(f"⏳ Still waiting... ({i+1}/45)")
        
        print("❌ Server startup timeout - checking process...")
        if self.server_process.poll() is not None:
            stdout, stderr = self.server_process.communicate()
            print(f"❌ Process exited with code {self.server_process.returncode}")
            print(f"Error: {stderr[:500]}")  # First 500 chars of error
        return False
        
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        return False
```

### Alternative: Quick Fix for Existing Code

If you want to quickly fix your current notebook, just replace this line:

**FIND THIS:**
```python
self.server_process = subprocess.Popen([
    self.binary_path, 
    '--no-sandbox', 
    '--headless'
], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
```

**REPLACE WITH:**
```python
self.server_process = subprocess.Popen([
    self.binary_path,
    '--no-sandbox',
    '--headless', 
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--disable-software-rasterizer',
    '--no-first-run',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-features=TranslateUI',
    '--disable-ipc-flooding-protection',
    '--disable-extensions',
    '--disable-plugins'
], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
```

## 🧪 Test This Fix

1. **Update your notebook** with the new flags
2. **Restart runtime** (to clear any hung processes)
3. **Run the setup cell again**
4. **Should work without D-Bus errors**

## 🔍 Why This Works

- `--disable-dev-shm-usage`: Fixes shared memory issues in containers
- `--disable-gpu`: Disables GPU for UI rendering (not AI model GPU usage)
- `--disable-*` flags: Prevent Electron from trying to connect to system services
- These flags make Electron work in containerized environments like Colab

## ⚡ Expected Output After Fix

```
🚀 Starting Pinokio web server...
⏳ Waiting for server startup...
⏳ Still waiting... (1/45)
⏳ Still waiting... (6/45)
✅ Pinokio web server running on port 42000
🌐 Setting up Cloudflare tunnel...
✅ Tunnel ready: https://abc123.trycloudflare.com
```

Try this fix and let me know if it resolves the D-Bus connection error!