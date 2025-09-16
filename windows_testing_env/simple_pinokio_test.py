#!/usr/bin/env python3
"""
Simple Pinokio Test - Minimal approach to execute notebook and monitor for server
"""

import os
import sys
import subprocess
import time
import requests
import threading
from pathlib import Path

def setup_environment():
    """Quick environment setup"""
    os.environ['COLAB_GPU'] = '1'
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    os.environ['DISPLAY'] = ':99'
    print("✅ Environment variables set")

def check_ports():
    """Check for active servers on common ports"""
    ports = [3000, 5000, 7860, 8000, 8080, 8888, 9000]
    active_servers = []
    
    for port in ports:
        try:
            response = requests.get(f'http://localhost:{port}', timeout=2)
            if response.status_code == 200:
                print(f"🌐 Server found on port {port}")
                print(f"📄 Content preview: {response.text[:100]}...")
                active_servers.append(port)
        except:
            continue
    
    return active_servers

def monitor_ports_thread():
    """Monitor ports in background"""
    print("🔍 Starting port monitoring...")
    
    while True:
        active = check_ports()
        if active:
            for port in active:
                print(f"🎯 ACTIVE SERVER: http://localhost:{port}")
        
        time.sleep(10)

def main():
    print("🚀 Simple Pinokio Test Starting...")
    
    # Setup
    setup_environment()
    
    # Check current state
    print("\n📊 Current server status:")
    active_servers = check_ports()
    
    if active_servers:
        print(f"🎉 Found {len(active_servers)} active servers!")
        for port in active_servers:
            print(f"🌐 http://localhost:{port}")
        
        # Keep monitoring
        print("\n⏳ Monitoring for changes... Press Ctrl+C to stop")
        try:
            monitor_thread = threading.Thread(target=monitor_ports_thread, daemon=True)
            monitor_thread.start()
            
            while True:
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
    else:
        print("❌ No active servers found")
        
        # Try to execute notebook directly
        notebook_path = Path(__file__).parent.parent / "github_upload" / "Pinokio_Colab_Final.ipynb"
        output_path = Path(__file__).parent / "test_outputs" / "simple_test.ipynb"
        
        print(f"\n📝 Executing notebook: {notebook_path}")
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=monitor_ports_thread, daemon=True)
        monitor_thread.start()
        
        cmd = [
            'jupyter', 'nbconvert',
            '--to', 'notebook',
            '--execute',
            '--allow-errors',
            '--ExecutePreprocessor.timeout=900',
            '--output', str(output_path),
            str(notebook_path)
        ]
        
        try:
            print("🏃 Executing notebook...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                print(f"✅ Notebook executed: {output_path}")
            else:
                print(f"❌ Execution failed: {result.stderr}")
            
            # Wait and check for servers
            print("\n⏳ Waiting for server startup...")
            for i in range(12):  # Wait up to 2 minutes
                active = check_ports()
                if active:
                    print(f"🎉 SERVER STARTED on ports: {active}")
                    for port in active:
                        print(f"🌐 Access Pinokio at: http://localhost:{port}")
                    break
                time.sleep(10)
                print(f"⏳ Still waiting... ({i+1}/12)")
            else:
                print("⏰ Timeout - no server detected")
            
        except subprocess.TimeoutExpired:
            print("⏰ Notebook execution timed out after 10 minutes")
        except Exception as e:
            print(f"💥 Error: {e}")

if __name__ == "__main__":
    main()
