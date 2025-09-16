#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PinokioCloud - Windows Version with Proper Process Management
Fixed with timeouts and error handling
"""

import os
import sys
import subprocess
import json
import time
import threading
from pathlib import Path
import platform
import psutil
from pyngrok import ngrok
import signal

def setup_environment():
    """Setup PinokioCloud environment with timeout handling"""
    print('🖥️ PinokioCloud - Windows Setup')
    print(f'   Platform: {platform.system()} {platform.release()}')
    
    # Get current working directory (should be the repo root)
    repo_dir = Path.cwd()
    print(f'📁 Working directory: {repo_dir}')
    
    # Add repo to Python path
    if str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))
    
    # Install dependencies with timeout
    print('\n📦 Installing dependencies...')
    deps = [
        'streamlit', 'gitpython', 'psutil', 'pyngrok', 
        'nest_asyncio', 'pandas', 'requests'
    ]
    
    for dep in deps:
        print(f'  Installing {dep}...')
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-q', dep], 
                capture_output=True, text=True, timeout=120  # 2 minute timeout
            )
            if result.returncode != 0:
                print(f'  ❌ Failed to install {dep}: {result.stderr}')
            else:
                print(f'  ✅ {dep} installed')
        except subprocess.TimeoutExpired:
            print(f'  ⏰ Timeout installing {dep}')
        except Exception as e:
            print(f'  ❌ Error installing {dep}: {e}')
    
    # Enable nested asyncio
    import nest_asyncio
    nest_asyncio.apply()
    
    print('✅ Environment setup complete')
    return repo_dir

def detect_gpu():
    """Detect GPU with timeout handling"""
    gpu_info = {
        'available': False,
        'type': None,
        'model': None,
        'cuda_version': None
    }
    
    try:
        result = subprocess.run(
            ['nvidia-smi'], 
            capture_output=True, text=True, 
            shell=True, timeout=10  # 10 second timeout
        )
        if result.returncode == 0:
            gpu_info['available'] = True
            gpu_info['type'] = 'nvidia'
            
            # Extract GPU model
            import re
            match = re.search(r'(GeForce \w+|RTX \w+|GTX \w+|Tesla \w+|A100|V100|T4|P100|K80)', result.stdout)
            if match:
                gpu_info['model'] = match.group(1)
            
            # Get CUDA version
            match = re.search(r'CUDA Version: ([\d.]+)', result.stdout)
            if match:
                gpu_info['cuda_version'] = match.group(1)
    except subprocess.TimeoutExpired:
        print('⏰ GPU detection timeout')
    except Exception as e:
        print(f'GPU detection error: {e}')
    
    return gpu_info

def kill_streamlit_windows_timeout():
    """Kill Streamlit processes on Windows with timeout"""
    print('🛑 Stopping existing Streamlit processes...')
    killed = False
    
    try:
        # Use taskkill with timeout
        result = subprocess.run(
            ['taskkill', '/f', '/im', 'python.exe', '/fi', 'WINDOWTITLE eq streamlit*'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            print('  ✅ Process termination completed')
            killed = True
        
        # Also try psutil method with timeout
        start_time = time.time()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if time.time() - start_time > 10:  # 10 second timeout
                break
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('streamlit' in str(cmd) for cmd in cmdline):
                        print(f'  Terminating PID {proc.info["pid"]}')
                        proc.terminate()
                        proc.wait(timeout=5)  # Wait max 5 seconds
                        killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue
            except Exception as e:
                print(f'  Warning: {e}')
                
    except subprocess.TimeoutExpired:
        print('  ⏰ Process termination timeout')
    except Exception as e:
        print(f'  Error in process termination: {e}')
    
    return killed

def launch_streamlit_with_timeout(repo_dir):
    """Launch Streamlit with proper timeout handling"""
    
    # Create runner script
    runner_path = repo_dir / 'run_streamlit_windows.py'
    streamlit_script = f'''
import streamlit as st
import sys
import os
from pathlib import Path

# Set paths for Windows
repo_path = Path(r"{repo_dir}")
sys.path.insert(0, str(repo_path))
os.chdir(repo_path)

# Import and run the FIXED Streamlit app
from ui.streamlit_app_fixed import main

if __name__ == "__main__":
    main()
'''
    
    with open(runner_path, 'w', encoding='utf-8') as f:
        f.write(streamlit_script)
    
    print('✅ Runner script created')
    
    # Kill existing processes first
    if kill_streamlit_windows_timeout():
        time.sleep(3)
    
    # Configure environment
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    print('🚀 Starting Streamlit server...')
    
    # Start Streamlit with timeout handling
    def run_streamlit():
        try:
            subprocess.run([
                sys.executable, '-m', 'streamlit', 'run',
                str(runner_path),
                '--server.port', '8501',
                '--server.address', '0.0.0.0',
                '--server.headless', 'true',
                '--browser.gatherUsageStats', 'false',
                '--theme.base', 'light'
            ], cwd=repo_dir, shell=True, timeout=300)  # 5 minute timeout
        except subprocess.TimeoutExpired:
            print('⏰ Streamlit startup timeout')
        except Exception as e:
            print(f'❌ Streamlit error: {e}')
    
    # Start in daemon thread
    thread = threading.Thread(target=run_streamlit, daemon=True)
    thread.start()
    
    # Wait with timeout for server startup
    print('⏳ Waiting for server (max 15 seconds)...')
    for i in range(15):
        time.sleep(1)
        try:
            import requests
            response = requests.get('http://localhost:8501', timeout=2)
            if response.status_code == 200:
                print('✅ Server is running!')
                break
        except:
            continue
    else:
        print('⚠️ Server may still be starting...')
    
    # Create ngrok tunnel with timeout
    print('🌐 Creating tunnel...')
    try:
        public_url = ngrok.connect(8501, "http")
        
        print('\n' + '='*60)
        print('✅ PinokioCloud is running!')
        print('='*60)
        print(f'🔗 Public URL: {public_url}')
        print(f'🏠 Local URL: http://localhost:8501')
        print('📱 Open either URL in your browser')
        print('\n⚠️ Press Ctrl+C to stop')
        
        return public_url
        
    except Exception as e:
        print(f'⚠️ Tunnel creation failed: {e}')
        print('🏠 Access locally at: http://localhost:8501')
        return None

def cleanup_with_timeout():
    """Cleanup all services with timeout"""
    print('\n🛑 Cleaning up services...')
    
    try:
        # Disconnect ngrok with timeout
        ngrok.disconnect_all()
        ngrok.kill()
        print('  ✅ ngrok stopped')
    except Exception as e:
        print(f'  ⚠️ ngrok cleanup: {e}')
    
    # Kill processes with timeout
    if kill_streamlit_windows_timeout():
        print('  ✅ Streamlit stopped')
    else:
        print('  ℹ️ No processes to stop')
    
    print('✅ Cleanup complete')

def main():
    """Main execution with signal handling"""
    
    def signal_handler(sig, frame):
        print('\n\n🛑 Interrupt received, cleaning up...')
        cleanup_with_timeout()
        sys.exit(0)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Setup environment
        repo_dir = setup_environment()
        
        # Show GPU info
        gpu = detect_gpu()
        print(f'\n🖥️ GPU Status: {"✅ " + gpu["model"] if gpu["available"] else "❌ No GPU"}')
        
        # Launch Streamlit
        public_url = launch_streamlit_with_timeout(repo_dir)
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(60)  # Check every minute
                
                # Verify server is still running
                try:
                    import requests
                    requests.get('http://localhost:8501', timeout=5)
                except:
                    print('⚠️ Server may have stopped, restarting...')
                    launch_streamlit_with_timeout(repo_dir)
                    
        except KeyboardInterrupt:
            pass
            
    except Exception as e:
        print(f'❌ Fatal error: {e}')
    finally:
        cleanup_with_timeout()

if __name__ == "__main__":
    main()
