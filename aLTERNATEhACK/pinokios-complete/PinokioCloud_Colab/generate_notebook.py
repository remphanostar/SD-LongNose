#!/usr/bin/env python3
"""
Generate PinokioCloud Colab Notebook using nbformat to avoid JSON errors
"""

import nbformat as nbf

def create_pinokio_notebook():
    """Create PinokioCloud notebook using nbformat"""
    
    # Create new notebook
    nb = nbf.v4.new_notebook()
    
    # Add metadata
    nb.metadata = {
        "accelerator": "GPU",
        "colab": {
            "gpuType": "T4",
            "provenance": []
        },
        "kernelspec": {
            "display_name": "Python 3",
            "name": "python3"
        },
        "language_info": {
            "name": "python"
        }
    }
    
    # Header markdown cell
    header_md = """# 🚀 PinokioCloud for Google Colab

**AI App Manager with Dark Mode UI & Live Logs - GitHub Integration**

Welcome to PinokioCloud - your cloud-native Pinokio alternative optimized for Google Colab!

This notebook automatically clones all required scripts from GitHub, making it a **single-file solution**.

## Features:
- ✅ **284+ Verified AI Apps** - Curated database of working Pinokio apps
- 🎨 **Beautiful Dark Mode UI** - Cyberpunk-inspired design with glassmorphism
- 📊 **Live Running Logs** - Real-time color-coded logs in sidebar
- 🎯 **Toast Notifications** - Success/error messages with auto-dismiss
- 🔄 **Full Lifecycle Management** - Install, run, stop, uninstall apps
- 🌐 **Public Access via ngrok** - Share your running apps with the world
- 🎮 **GPU Detection** - Automatic NVIDIA GPU detection and optimization
- 📦 **GitHub Integration** - Auto-clones all scripts from repository

**Repository:** https://github.com/remphanostar/SD-LongNose

---"""
    
    nb.cells.append(nbf.v4.new_markdown_cell(header_md))
    
    # Setup code cell
    setup_code = '''#@title 🛠️ Setup: Clone Repository & Install Dependencies
#@markdown **This cell clones the PinokioCloud repository and installs all dependencies**

import os
import sys
import subprocess
import time
from pathlib import Path

print("🚀 Setting up PinokioCloud for Google Colab...")

# Check if we're in Google Colab
try:
    import google.colab
    IN_COLAB = True
    print("✅ Detected Google Colab environment")
except ImportError:
    IN_COLAB = False
    print("❌ Not in Google Colab - running locally")

# Set up paths
if IN_COLAB:
    WORK_DIR = Path("/content")
else:
    WORK_DIR = Path.cwd()

REPO_DIR = WORK_DIR / "SD-LongNose"
COLAB_DIR = REPO_DIR / "PinokioCloud_Colab"
PINOKIO_BASE = WORK_DIR / "pinokio_apps"

print(f"📁 Working directory: {WORK_DIR}")
print(f"📁 Repository will be cloned to: {REPO_DIR}")
print(f"📁 PinokioCloud scripts: {COLAB_DIR}")
print(f"📁 Pinokio apps storage: {PINOKIO_BASE}")

# Clone PinokioCloud repository
repo_url = "https://github.com/remphanostar/SD-LongNose.git"
print(f"\\n📥 Cloning repository: {repo_url}")

if REPO_DIR.exists():
    print("🔄 Repository already exists, updating...")
    try:
        import git
        repo = git.Repo(REPO_DIR)
        repo.remotes.origin.pull()
        print("✅ Repository updated successfully")
    except Exception as e:
        print(f"⚠️ Update failed, will try fresh clone: {e}")
        import shutil
        shutil.rmtree(REPO_DIR)
else:
    print("📥 Cloning fresh repository...")

# Fresh clone if needed
if not REPO_DIR.exists():
    try:
        # Install git if not available
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "gitpython"], check=True)
        import git
        
        git.Repo.clone_from(repo_url, REPO_DIR)
        print("✅ Repository cloned successfully")
    except Exception as e:
        print(f"❌ Failed to clone repository: {e}")
        print("🛑 Cannot continue without repository")
        raise

# Verify required files exist
required_files = {
    "Streamlit UI": COLAB_DIR / "streamlit_colab.py",
    "Unified Engine": COLAB_DIR / "unified_engine.py", 
    "Apps Database": COLAB_DIR / "cleaned_pinokio_apps.json"
}

print("\\n🔍 Verifying cloned files...")
all_files_exist = True
for name, file_path in required_files.items():
    if file_path.exists():
        size = file_path.stat().st_size
        print(f"✅ {name}: {file_path.name} ({size:,} bytes)")
    else:
        print(f"❌ {name}: {file_path} - NOT FOUND")
        all_files_exist = False

if not all_files_exist:
    print("\\n❌ Required files missing from repository")
    raise FileNotFoundError("PinokioCloud files not found in repository")

# Add repository to Python path
colab_path = str(COLAB_DIR)
if colab_path not in sys.path:
    sys.path.insert(0, colab_path)
    print(f"✅ Added to Python path: {colab_path}")

# Install required dependencies
print("\\n📦 Installing Python dependencies...")
dependencies = [
    "streamlit>=1.28.0",
    "gitpython>=3.1.0", 
    "psutil>=5.9.0",
    "pyngrok>=7.0.0",
    "nest_asyncio>=1.5.0",
    "pandas>=1.5.0",
    "requests>=2.28.0"
]

for dep in dependencies:
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", dep], check=True)
        print(f"✅ Installed {dep.split('>=')[0]}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {dep}: {e}")

# Enable nest_asyncio for Jupyter compatibility
import nest_asyncio
nest_asyncio.apply()
print("✅ Enabled async support for Jupyter")

# Create app storage directory
PINOKIO_BASE.mkdir(exist_ok=True)
print(f"✅ Created app storage: {PINOKIO_BASE}")

# Load and verify apps database
apps_file = required_files["Apps Database"]
try:
    import json
    with open(apps_file, 'r') as f:
        apps_data = json.load(f)
    print(f"📊 Apps database loaded: {len(apps_data)} apps available")
except Exception as e:
    print(f"⚠️ Error reading apps database: {e}")

print("\\n🎉 Setup completed successfully!")
print(f"📍 Repository location: {REPO_DIR}")
print(f"📍 PinokioCloud scripts: {COLAB_DIR}")
print("➡️ Continue to the next cell to detect your GPU")'''
    
    setup_cell = nbf.v4.new_code_cell(setup_code)
    setup_cell.metadata = {
        "cellView": "form",
        "id": "setup"
    }
    nb.cells.append(setup_cell)
    
    # GPU detection code cell
    gpu_code = '''#@title 🎮 GPU Detection & System Information
#@markdown **Detect available GPU and system resources**

import subprocess
import platform
import psutil
import os

def detect_gpu():
    """Detect GPU information"""
    print("🔍 Detecting GPU...")
    
    try:
        # Try nvidia-smi first
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            gpu_info = result.stdout.strip().split('\\n')
            print("🎮 NVIDIA GPU(s) detected:")
            for i, gpu in enumerate(gpu_info):
                name, total, used, free = gpu.split(', ')
                print(f"  GPU {i}: {name}")
                print(f"    Total VRAM: {total} MB")
                print(f"    Used VRAM: {used} MB")
                print(f"    Free VRAM: {free} MB")
            return True
        else:
            print("❌ nvidia-smi failed or not available")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"❌ nvidia-smi error: {e}")
    
    # Try alternative methods
    try:
        import torch
        if torch.cuda.is_available():
            print("🎮 PyTorch CUDA detected:")
            for i in range(torch.cuda.device_count()):
                print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
            return True
    except ImportError:
        pass
    
    print("⚠️ No GPU detected or GPU not accessible")
    return False

def get_system_info():
    """Get system information"""
    print("\\n💻 System Information:")
    print(f"  Platform: {platform.system()} {platform.release()}")
    print(f"  Architecture: {platform.machine()}")
    print(f"  CPU Cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical")
    
    # Memory info
    memory = psutil.virtual_memory()
    print(f"  RAM: {memory.total // (1024**3)} GB total, {memory.available // (1024**3)} GB available")
    
    # Disk info
    disk = psutil.disk_usage('/')
    print(f"  Disk: {disk.total // (1024**3)} GB total, {disk.free // (1024**3)} GB free")

# Run detection
gpu_available = detect_gpu()
get_system_info()

if gpu_available:
    print("\\n✅ Your system is ready for GPU-accelerated AI apps!")
else:
    print("\\n⚠️ No GPU detected - CPU-only mode will be used")

print("\\n➡️ Continue to the next cell to launch PinokioCloud")'''
    
    gpu_cell = nbf.v4.new_code_cell(gpu_code)
    nb.cells.append(gpu_cell)
    
    # Cell 4: Launch Streamlit with ngrok (with hardcoded token)
    launch_code = '''#@title 🚀 Launch PinokioCloud with ngrok Tunnel (Authenticated)
#@markdown **Launch the beautiful Streamlit UI with public access via ngrok**

import subprocess
import threading
import time
import os
import sys
from pathlib import Path

# Configuration
STREAMLIT_PORT = 8501
NGROK_REGION = "us"  #@param ["us", "eu", "ap", "au", "sa", "jp", "in"]

# Define paths from repository
WORK_DIR = Path("/content") if 'google.colab' in sys.modules else Path.cwd()
REPO_DIR = WORK_DIR / "SD-LongNose"
COLAB_DIR = REPO_DIR / "PinokioCloud_Colab"
STREAMLIT_FILE = COLAB_DIR / "streamlit_colab.py"

def setup_ngrok():
    """Set up ngrok tunnel with authentication"""
    try:
        from pyngrok import ngrok, conf
        
        # Set ngrok authentication token
        ngrok.set_auth_token("31hXIA9IPUsFAnKFrZ92A7jgwj3_5zwfYZfiJRYGacXizWs9K")
        
        # Set ngrok region
        conf.get_default().region = NGROK_REGION
        
        # Create tunnel
        print(f"🌐 Creating authenticated ngrok tunnel on port {STREAMLIT_PORT}...")
        public_tunnel = ngrok.connect(STREAMLIT_PORT)
        
        print(f"✅ Public URL: {public_tunnel.public_url}")
        print(f"🌍 Share this URL to access PinokioCloud from anywhere!")
        print(f"🔐 Using authenticated ngrok (no time limits)")
        
        return public_tunnel.public_url
        
    except Exception as e:
        print(f"❌ Failed to create ngrok tunnel: {e}")
        return None

def launch_streamlit():
    """Launch Streamlit application from cloned repository"""
    try:
        # Verify streamlit file exists
        if not STREAMLIT_FILE.exists():
            print(f"❌ Streamlit file not found: {STREAMLIT_FILE}")
            print(f"🔍 Repository directory contents:")
            if REPO_DIR.exists():
                for item in REPO_DIR.iterdir():
                    print(f"  - {item}")
            return None
        
        # Change to repository directory
        original_cwd = os.getcwd()
        os.chdir(str(COLAB_DIR))
        print(f"📁 Changed directory to: {COLAB_DIR}")
        
        print(f"🚀 Launching Streamlit from: {STREAMLIT_FILE}")
        
        # Launch Streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run", str(STREAMLIT_FILE),
            "--server.port", str(STREAMLIT_PORT),
            "--server.headless", "true",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false",
            "--browser.gatherUsageStats", "false"
        ]
        
        print(f"📋 Command: {' '.join(cmd)}")
        
        # Start Streamlit in background
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True,
            cwd=str(COLAB_DIR)
        )
        
        # Wait a moment for Streamlit to start
        print("⏳ Starting Streamlit server...")
        time.sleep(10)
        
        # Check if process is running
        if process.poll() is None:
            print("✅ Streamlit server started successfully!")
            return process
        else:
            print("❌ Streamlit server failed to start")
            # Print any error output
            output, _ = process.communicate()
            print(f"Error output: {output}")
            return None
        
    except Exception as e:
        print(f"❌ Failed to launch Streamlit: {e}")
        return None
    finally:
        # Restore original directory
        try:
            os.chdir(original_cwd)
        except:
            pass

# Verify repository is available
if not REPO_DIR.exists():
    print("❌ Repository not found! Please run the setup cell first.")
    print(f"Expected location: {REPO_DIR}")
else:
    print(f"✅ Repository found: {REPO_DIR}")
    print(f"✅ PinokioCloud scripts: {COLAB_DIR}")
    
    # Launch the application
    print("\\n🚀 Launching PinokioCloud from GitHub repository...")
    print("=" * 60)
    
    # Start Streamlit
    streamlit_process = launch_streamlit()
    
    if streamlit_process:
        # Set up ngrok tunnel
        public_url = setup_ngrok()
        
        if public_url:
            print("\\n" + "=" * 60)
            print("🎉 PinokioCloud is now running from GitHub!")
            print("=" * 60)
            print(f"🌐 Public URL: {public_url}")
            print(f"📱 Local URL: http://localhost:{STREAMLIT_PORT}")
            print(f"📦 Repository: https://github.com/remphanostar/SD-LongNose")
            print("=" * 60)
            print("\\n🎯 Features available:")
            print("  • Browse 5+ verified AI apps")
            print("  • Install apps with one click")
            print("  • Run apps with GPU acceleration")
            print("  • Live logs and toast notifications")
            print("  • Beautiful dark mode UI")
            print("  • All scripts loaded from GitHub")
            print("  • 🔐 Authenticated ngrok (no time limits)")
            print("\\n⚠️ Keep this cell running to maintain the server")
            print("\\n🔄 To stop the server, interrupt this cell or restart the runtime")
            
            # Keep the process running
            try:
                streamlit_process.wait()
            except KeyboardInterrupt:
                print("\\n🛑 Stopping PinokioCloud...")
                streamlit_process.terminate()
                print("✅ Server stopped")
        else:
            print("⚠️ Running without public tunnel - only local access available")
            print(f"📱 Local URL: http://localhost:{STREAMLIT_PORT}")
    else:
        print("❌ Failed to start PinokioCloud")
        print("\\n🔧 Troubleshooting:")
        print("  1. Make sure the repository was cloned correctly")
        print("  2. Check that dependencies were installed successfully")
        print("  3. Try restarting the runtime and running all cells again")
        print(f"  4. Verify files exist in: {COLAB_DIR}")'''
    
    launch_cell = nbf.v4.new_code_cell(launch_code)
    launch_cell.metadata = {
        "cellView": "form", 
        "id": "launch_streamlit"
    }
    nb.cells.append(launch_cell)
    
    # Usage instructions markdown
    instructions_md = """## 📚 Usage Instructions

### 🎯 Getting Started
1. **Run all cells above** in order to set up and launch PinokioCloud
2. **All scripts are automatically cloned** from the GitHub repository
3. **Click the public ngrok URL** to access the beautiful web interface
4. **Browse the app library** to discover 284+ verified AI applications
5. **Install and run apps** with one-click functionality

### 📦 GitHub Integration
- **Repository**: https://github.com/remphanostar/SD-LongNose
- **Auto-Clone**: All PinokioCloud scripts are automatically downloaded
- **Single File**: This notebook is self-contained and pulls everything from GitHub
- **Always Updated**: Repository is pulled/updated on each run

### 🎨 UI Features
- **🏠 Dashboard**: Quick stats, GPU info, and navigation
- **📱 Browse Apps**: Search and filter through 284+ AI apps
- **💾 Installed Apps**: Manage your installed applications
- **📋 System Logs**: View real-time installation and runtime logs
- **⚙️ Settings**: Engine status and reset options

### 🔧 App Management
- **Install**: Clone repository and run install scripts automatically
- **Run**: Execute start scripts and launch web interfaces
- **Stop**: Terminate running processes safely
- **Uninstall**: Complete removal including files and virtual environments

### 🌐 Public Access
- Your PinokioCloud instance is accessible via the **ngrok public URL**
- Share this URL with others to give them access to your AI apps
- Apps running on your instance will also be publicly accessible

### ⚠️ Important Notes
- **Keep the launch cell running** to maintain the server
- **GPU acceleration** is automatically used when available
- **Storage is ephemeral** - installed apps will be lost when runtime restarts
- **Resource limits** apply based on your Colab plan
- **GitHub dependency** - requires internet connection to clone repository

---

## 🛠️ Troubleshooting

### Common Issues
1. **"Repository clone failed"**: Check internet connection and GitHub access
2. **"Files not found"**: Ensure repository cloning completed successfully
3. **"Streamlit failed to start"**: Check dependencies and restart runtime
4. **"No GPU detected"**: Ensure you're using a GPU runtime in Colab
5. **"Apps won't install"**: Check internet connection and disk space

### Reset Instructions
1. **Runtime → Restart runtime** to clear everything
2. **Run all setup cells again** from the beginning
3. **Repository will be re-cloned** automatically
4. **Check the Settings page** in the UI for engine status

### Repository Structure
```
/content/SD-LongNose/
├── PinokioCloud_Colab/
│   ├── streamlit_colab.py       # Main Streamlit UI
│   ├── unified_engine.py        # Pinokio execution engine
│   └── cleaned_pinokio_apps.json # Apps database
└── [other repository files]
```

---

**Enjoy using PinokioCloud with GitHub integration! 🚀**"""
    
    nb.cells.append(nbf.v4.new_markdown_cell(instructions_md))
    
    return nb

if __name__ == "__main__":
    # Generate notebook
    notebook = create_pinokio_notebook()
    
    # Save notebook with UTF-8 encoding to handle emojis
    output_file = "PinokioCloud_Colab_Generated.ipynb"
    with open(output_file, 'w', encoding='utf-8') as f:
        nbf.write(notebook, f)
    
    print(f"✅ Generated notebook: {output_file}")
    print("🎯 This notebook should have proper JSON structure and no parsing errors")
