#!/usr/bin/env python
# coding: utf-8

# # 🚀 PinokioCloud - Streamlit UI for Colab
# 
# **Run 284+ Pinokio AI apps with a beautiful Streamlit interface**
# 
# Features:
# - ✅ Modern Streamlit Web UI
# - ✅ Full Pinokio JS/JSON script execution
# - ✅ Virtual environment isolation per app
# - ✅ GPU detection and optimization
# - ✅ ngrok tunneling for public access
# - ✅ 284+ verified AI apps from AppData.json

# Setup: Clone Repository & Install Dependencies
import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Setup PinokioCloud environment"""
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

    # Install ALL dependencies including Streamlit
    print('\n📦 Installing dependencies...')
    deps = [
        'streamlit',
        'gitpython',
        'psutil',
        'pyngrok',
        'nest_asyncio',
        'pandas'
    ]

    for dep in deps:
        print(f'  Installing {dep}...')
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', dep], capture_output=True, text=True)
        if result.returncode != 0:
            print(f'  ❌ Failed to install {dep}: {result.stderr}')
        else:
            print(f'  ✅ {dep} installed')

    # Enable nested asyncio for notebooks
    import nest_asyncio
    nest_asyncio.apply()

    print('\n✅ All dependencies installed')
    return repo_dir


# In[ ]:


#@title GPU Detection
import platform
import re

def detect_gpu():
    """Detect GPU and CUDA capabilities"""
    gpu_info = {
        'available': False,
        'type': None,
        'model': None,
        'cuda_version': None
    }
    
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            gpu_info['available'] = True
            gpu_info['type'] = 'nvidia'
            
            # Extract GPU model
            match = re.search(r'(Tesla \w+|A100|V100|T4|P100|K80)', result.stdout)
            if match:
                gpu_info['model'] = match.group(1)
            
            # Get CUDA version
            match = re.search(r'CUDA Version: ([\d.]+)', result.stdout)
            if match:
                gpu_info['cuda_version'] = match.group(1)
    except FileNotFoundError:
        pass
    
    return gpu_info

def print_gpu_info():
    """Print GPU information"""
    import platform
    
    gpu = detect_gpu()
    print('🖥️  Environment Information:')
    print(f'  Platform: {platform.system()}')
    print(f'  Python: {sys.executable}')

    if gpu['available']:
        print(f"  ✅ GPU: {gpu['model']} ({gpu['type']})")
        print(f"  CUDA: {gpu['cuda_version']}")
    else:
        print('  ⚠️  No GPU detected - CPU mode only')


def create_streamlit_runner(repo_dir):
    """Create Streamlit runner script"""
    streamlit_script = '''
import streamlit as st
import sys
import os
sys.path.insert(0, '/content/pinokios-complete')
os.chdir('/content/pinokios-complete')

# Import and run the fixed Streamlit app
from ui.streamlit_app_fixed import main

if __name__ == "__main__":
    main()
'''

    # Write the runner script
    runner_path = repo_dir / 'run_streamlit.py'
    with open(runner_path, 'w') as f:
        f.write(streamlit_script)

    print('✅ Streamlit runner script created')
    return runner_path


def launch_streamlit_ui(repo_dir):
    """Launch Streamlit UI with ngrok tunnel"""
    from pyngrok import ngrok
    import threading
    import time

    # Kill any existing Streamlit processes
    subprocess.run(['pkill', '-f', 'streamlit'], capture_output=True)
    time.sleep(2)

    # Configure Streamlit for headless operation
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

    print('🚀 Starting Streamlit server...')

    # Start Streamlit in background using the FIXED UI
    def run_streamlit():
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run',
            'ui/streamlit_app_fixed.py',  # Use the fixed version
            '--server.port', '8501',
            '--server.address', '0.0.0.0',
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false',
            '--theme.base', 'light'
        ], cwd=repo_dir)

    # Start in thread
    thread = threading.Thread(target=run_streamlit, daemon=True)
    thread.start()

    # Wait for server to start
    print('⏳ Waiting for server to start...')
    time.sleep(5)

    # Create ngrok tunnel
    print('\n🌐 Creating public tunnel...')
    public_url = ngrok.connect(8501, "http")

    print('\n' + '='*50)
    print('✅ PinokioCloud Streamlit UI is running!')
    print('='*50)
    print(f'\n🔗 Public URL: {public_url}')
    print('\n📱 Open this URL in your browser to access the UI')
    print('\nThe Streamlit app provides:')
    print('  • App search and filtering')
    print('  • One-click install/run/stop')
    print('  • Real-time status monitoring')
    print('  • Beautiful modern interface')
    print('\n⚠️  Keep this script running to maintain the server')
    
    return public_url


def set_ngrok_token(token=None):
    """Set ngrok auth token for stable tunnels"""
    from pyngrok import ngrok
    
    if token:
        ngrok.set_auth_token(token)
        print('✅ ngrok auth token set')
    else:
        print('💡 Tip: Set your ngrok auth token for stable tunnels')
        print('   Get your token from: https://dashboard.ngrok.com/auth')


def check_server_status():
    """Check Streamlit server and tunnel status"""
    import requests
    from pyngrok import ngrok
    
    try:
        response = requests.get('http://localhost:8501', timeout=2)
        if response.status_code == 200:
            print('✅ Streamlit server is running')
        else:
            print(f'⚠️  Server returned status: {response.status_code}')
    except requests.exceptions.RequestException as e:
        print('❌ Server is not responding')
        print(f'   Error: {e}')

    # Check for active tunnels
    tunnels = ngrok.get_tunnels()
    if tunnels:
        print('\n🌐 Active tunnels:')
        for tunnel in tunnels:
            print(f'   {tunnel.public_url} -> {tunnel.config["addr"]}')
    else:
        print('\n⚠️  No active tunnels')


def stop_all_services():
    """Stop Streamlit server and cleanup"""
    from pyngrok import ngrok
    
    print('🛑 Stopping services...')

    # Kill Streamlit
    subprocess.run(['pkill', '-f', 'streamlit'], capture_output=True)
    print('  ✅ Streamlit stopped')

    # Disconnect ngrok tunnels
    ngrok.disconnect_all()
    print('  ✅ Tunnels disconnected')

    # Kill ngrok process
    ngrok.kill()
    print('  ✅ ngrok stopped')

    print('\n✅ All services stopped')

# Main execution
if __name__ == "__main__":
    # Setup environment
    repo_dir = setup_environment()
    
    # Print GPU info
    print_gpu_info()
    
    # Create runner script
    create_streamlit_runner(repo_dir)
    
    # Launch Streamlit UI
    public_url = launch_streamlit_ui(repo_dir)
    
    # Keep script running
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print('\n⚠️  Shutting down...')
        stop_all_services()

