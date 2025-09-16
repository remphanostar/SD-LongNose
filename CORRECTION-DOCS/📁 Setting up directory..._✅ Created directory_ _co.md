<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# 📁 Setting up directory...

✅ Created directory: /content/pinokio
📥 Downloading Pinokio...
✅ Pinokio already downloaded
🚀 Starting Pinokio web server...
⏳ Waiting for server startup...
⏳ Still waiting... (1/30)
⏳ Still waiting... (6/30)
⏳ Still waiting... (11/30)
⏳ Still waiting... (16/30)
⏳ Still waiting... (21/30)
⏳ Still waiting... (26/30)
❌ Server startup timeout - checking process...
❌ Process exited with code -5
Error: [1062:0901/065341.165768:ERROR:bus.cc(399)] Failed to connect to the bus: Failed to connect to socket /run/dbus/system_bus_socket: No such file or directory

❌ Setup failed: Failed to start Pinokio server

🔧 Troubleshooting:

1. Check if GPU runtime is enabled
2. Restart the notebook and try again
3. Check the status cell below for details

The **D-Bus connection error** you're seeing is because Electron (which Pinokio is built on) is trying to connect to system services that don't exist in Colab's containerized environment.

## 🔧 Quick Fix

**Find this code in your notebook:**

```python
self.server_process = subprocess.Popen([
    self.binary_path, 
    '--no-sandbox', 
    '--headless'
], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
```

**Replace with this:**

```python
self.server_process = subprocess.Popen([
    self.binary_path,
    '--no-sandbox',
    '--headless', 
    '--disable-dev-shm-usage',           # Fix container shared memory
    '--disable-gpu',                     # Disable UI GPU (not AI GPU)
    '--disable-software-rasterizer',     # Disable fallback rendering
    '--no-first-run',                    # Skip setup dialogs
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-features=TranslateUI',    # Disable extra features
    '--disable-ipc-flooding-protection', # Fix IPC issues in containers
    '--disable-extensions'               # Disable Chrome extensions
], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
```


## 🚀 Steps to Fix

1. **Edit your notebook** - Add the additional flags above
2. **Restart Colab runtime** - `Runtime → Restart runtime`
3. **Run setup cell again** - Should work without D-Bus errors
4. **Increase timeout** - Change `range(30)` to `range(45)` for container startup

## 💡 Why This Happens

- **Pinokio uses Electron** (Chrome-based framework)
- **Electron expects desktop services** like D-Bus, X11, etc.
- **Colab containers don't have these** system services
- **Additional flags disable** these system dependencies

This is a **very common issue** with Electron apps in containerized environments. The fix should resolve it completely!

Try the fix and let me know if the D-Bus error disappears! 🎯
<span style="display:none">[^1][^2][^3][^4][^5][^6][^7][^8][^9]</span>

<div style="text-align: center">⁂</div>

[^1]: CHANGELOG.md

[^2]: Pinokio_Cloud_Simple.ipynb

[^3]: pinokio_cloud_simple.py

[^4]: README.md

[^5]: requirements.txt

[^6]: advanced_usage.py

[^7]: basic_usage.py

[^8]: README.md

[^9]: https://ppl-ai-code-interpreter-files.s3.amazonaws.com/web/direct-files/1935f81dafef7ce08571232c9d93a74d/55a50be2-04c1-494d-9531-d65cd50037f5/05598bfe.md

