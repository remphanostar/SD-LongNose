#!/usr/bin/env python
# coding: utf-8

# # 🚀 PinokioCloud - Complete AI App Manager for Colab
# 
# **Run Pinokio apps in Google Colab with full JS/JSON script execution support**
# 
# Features:
# - ✅ Full Pinokio JS/JSON script execution
# - ✅ Virtual environment isolation per app
# - ✅ GPU detection and optimization
# - ✅ ngrok tunneling for public access
# - ✅ 284+ verified AI apps from AppData.json
# - ✅ Event-driven app lifecycle management

# In[ ]:


#@title Cell 1: Clone Repository & Install Core Dependencies
import os
import sys
import subprocess
from pathlib import Path

# Clone repository if not exists
repo_url = 'https://github.com/remphanostar/SD-LongNose.git'
repo_dir = Path('/content/pinokios-complete')

if not repo_dir.exists():
    print('🔄 Cloning repository...')
    result = subprocess.run(['git', 'clone', repo_url, str(repo_dir)], capture_output=True, text=True)
    if result.returncode == 0:
        print('✅ Repository cloned')
    else:
        print(f'❌ Clone failed: {result.stderr}')
        raise Exception(f'Git clone failed: {result.stderr}')
else:
    print('✅ Repository already exists')

# Change to repo directory
os.chdir(repo_dir)
sys.path.insert(0, str(repo_dir))

# Install core dependencies
print('\n📦 Installing dependencies...')
deps = ['gitpython', 'psutil', 'pyngrok', 'ipywidgets', 'nest_asyncio']
for dep in deps:
    result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', dep], capture_output=True, text=True)
    if result.returncode != 0:
        print(f'❌ Failed to install {dep}: {result.stderr}')

# Enable nested asyncio for notebooks
import nest_asyncio
nest_asyncio.apply()

print('✅ Core dependencies installed')


# In[ ]:


#@title Cell 2: GPU Detection & Environment Setup
import platform
import shutil

def detect_environment():
    """Detect GPU and environment capabilities"""
    env_info = {
        'platform': platform.system().lower(),
        'python': sys.executable,
        'gpu': None,
        'gpu_model': None,
        'cuda_version': None
    }
    
    # Check for NVIDIA GPU
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            env_info['gpu'] = 'nvidia'
            # Extract GPU model
            import re
            match = re.search(r'(Tesla \w+|A100|V100|T4|P100|K80)', result.stdout)
            if match:
                env_info['gpu_model'] = match.group(1)
            
            # Get CUDA version
            match = re.search(r'CUDA Version: ([\d.]+)', result.stdout)
            if match:
                env_info['cuda_version'] = match.group(1)
    except FileNotFoundError:
        pass
    
    return env_info

# Detect environment
env = detect_environment()
print('🖥️  Environment Information:')
print(f'  Platform: {env["platform"]}')
print(f'  Python: {env["python"]}')
if env['gpu']:
    print(f'  🎮 GPU: {env["gpu_model"]} ({env["gpu"]})')
    print(f'  CUDA: {env["cuda_version"]}')
else:
    print('  ⚠️  No GPU detected - CPU mode only')


# In[ ]:


#@title Cell 3: Load Unified Pinokio Engine
try:
    # Import the unified engine
    from pinokios.unified_engine import UnifiedPinokioEngine, PinokioContext
    import asyncio
    import json

    # Initialize engine
    engine = UnifiedPinokioEngine(base_path='/content/pinokio_apps')
    print('✅ Pinokio Engine initialized')
    print(f'📂 Base path: {engine.base_path}')
    print(f'🎮 GPU: {engine.context.gpu or "Not detected"}')
    print(f'🖥️  Platform: {engine.context.platform}')
except ImportError as e:
    print(f'❌ Failed to import unified engine: {e}')
    print('Available files:')
    for file in Path('.').rglob('*.py'):
        print(f'  {file}')
    raise


# In[ ]:


#@title Cell 4: Load App Database
# Load app database
app_data_file = repo_dir / 'cleaned_pinokio_apps.json'

if app_data_file.exists():
    try:
        with open(app_data_file, 'r') as f:
            app_database = json.load(f)
        
        # Convert to list if it's a dict
        if isinstance(app_database, dict):
            app_database = list(app_database.values())
            
        print(f'✅ Loaded {len(app_database)} apps from database')
        
        # Extract unique categories
        categories = set()
        for app in app_database:
            if 'category' in app:
                categories.add(app['category'])
        
        print(f'\n📚 Available Categories: {len(categories)}')
        for cat in sorted(categories):
            count = sum(1 for app in app_database if app.get('category') == cat)
            print(f'  • {cat}: {count} apps')
    except json.JSONDecodeError as e:
        print(f'❌ Invalid JSON in app database: {e}')
        app_database = []
else:
    print('⚠️  App database not found, creating sample data...')
    app_database = [
        {
            'name': 'Stable Diffusion WebUI',
            'repo_url': 'https://github.com/AUTOMATIC1111/stable-diffusion-webui',
            'category': 'IMAGE',
            'description': 'Popular Stable Diffusion WebUI'
        },
        {
            'name': 'ComfyUI',
            'repo_url': 'https://github.com/comfyanonymous/ComfyUI', 
            'category': 'IMAGE',
            'description': 'Node-based Stable Diffusion UI'
        }
    ]


# In[ ]:


#@title Cell 5: Basic Test - Install Simple App
async def test_install():
    """Test basic installation functionality"""
    app_name = 'test-app'
    repo_url = 'https://github.com/AUTOMATIC1111/stable-diffusion-webui'
    
    print(f'🧪 Testing installation of {app_name}...')
    
    try:
        success, message = await engine.install_app(app_name, repo_url)
        if success:
            print('✅ Installation test passed')
        else:
            print(f'❌ Installation test failed: {message}')
    except Exception as e:
        print(f'❌ Installation test error: {e}')

# Run the test
await test_install()


# In[ ]:


#@title Utility: List All Installed Apps
try:
    installed = engine.list_installed_apps()

    if installed:
        print('📦 Installed Apps:')
        for app in installed:
            print(f"  • {app['name']}: {app['status']}")
            print(f"    Path: {app['path']}")
    else:
        print('No apps installed yet')
except Exception as e:
    print(f'❌ Error listing apps: {e}')


# In[ ]:


#@title Utility: Stop All Running Apps
print('🛑 Stopping all running apps...')
try:
    engine.cleanup()
    print('✅ All apps stopped')
except Exception as e:
    print(f'❌ Error during cleanup: {e}')

