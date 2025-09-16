#!/usr/bin/env python3
"""
Direct Pinokio Notebook Executor - Simple and Direct Approach
Execute notebook and get Pinokio running with minimal complexity
"""

import os
import sys
import time
import subprocess
import threading
import requests
import json
from pathlib import Path
from datetime import datetime

class DirectPinokioExecutor:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.notebook_path = self.project_root / "github_upload" / "Pinokio_Colab_Final.ipynb"
        self.output_dir = self.project_root / "windows_testing_env" / "test_outputs"
        self.output_dir.mkdir(exist_ok=True)
        
        # Server monitoring
        self.pinokio_port = None
        self.monitoring = False
        
        print(f"🚀 Direct Pinokio Executor initialized")
        print(f"📝 Notebook: {self.notebook_path}")
        
    def setup_environment(self):
        """Setup mock environment quickly"""
        try:
            # Setup basic environment variables
            os.environ['COLAB_GPU'] = '1'
            os.environ['CUDA_VISIBLE_DEVICES'] = '0'
            os.environ['DISPLAY'] = ':99'
            
            # Import mock env if available
            mock_env_path = self.project_root / "windows_testing_env" / "mock_gpu_env.py"
            if mock_env_path.exists():
                sys.path.insert(0, str(mock_env_path.parent))
                import mock_gpu_env
                mock_gpu_env.setup_mock_environment()
                print("✅ Mock GPU environment activated")
            
        except Exception as e:
            print(f"⚠️ Environment setup issue: {e}")
    
    def monitor_ports(self):
        """Monitor common ports for Pinokio server"""
        ports = [8080, 3000, 5000, 7860, 8000, 8888, 9000, 7000]
        self.monitoring = True
        
        print("🔍 Starting port monitoring...")
        
        while self.monitoring:
            for port in ports:
                try:
                    response = requests.get(f'http://localhost:{port}', timeout=1)
                    if response.status_code == 200:
                        content = response.text.lower()
                        
                        # Check for Pinokio-related content
                        pinokio_indicators = ['pinokio', 'dashboard', 'home', 'api', 'script']
                        if any(indicator in content for indicator in pinokio_indicators):
                            print(f"🎯 PINOKIO SERVER DETECTED on port {port}!")
                            print(f"🌐 Local URL: http://localhost:{port}")
                            self.pinokio_port = port
                            return port
                        
                        # Generic web server
                        if len(content) > 100:  # Has actual content
                            print(f"📡 Web server detected on port {port} (checking if Pinokio...)")
                            
                except:
                    continue
            
            time.sleep(3)
        
        return None
    
    def execute_with_jupyter(self):
        """Execute notebook using jupyter nbconvert"""
        print("\n🔧 METHOD 1: Executing with jupyter nbconvert...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f"direct_exec_{timestamp}.ipynb"
        
        cmd = [
            'jupyter', 'nbconvert',
            '--to', 'notebook',
            '--execute',
            '--allow-errors',
            '--ExecutePreprocessor.timeout=1800',
            '--output', str(output_file),
            str(self.notebook_path)
        ]
        
        print(f"Executing: {' '.join(cmd)}")
        
        # Start monitoring in background
        monitor_thread = threading.Thread(target=self.monitor_ports, daemon=True)
        monitor_thread.start()
        
        try:
            # Execute notebook
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.notebook_path.parent))
            
            if result.returncode == 0:
                print(f"✅ Notebook executed successfully: {output_file}")
                return True, str(output_file)
            else:
                print(f"❌ Execution failed: {result.stderr}")
                return False, result.stderr
                
        except Exception as e:
            print(f"❌ Execution exception: {e}")
            return False, str(e)
    
    def execute_with_python(self):
        """Execute notebook by converting to Python and running"""
        print("\n🔧 METHOD 2: Converting to Python and executing...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        py_file = self.output_dir / f"converted_{timestamp}.py"
        
        # Convert notebook to Python
        convert_cmd = [
            'jupyter', 'nbconvert',
            '--to', 'python',
            '--output', str(py_file),
            str(self.notebook_path)
        ]
        
        try:
            print("Converting notebook to Python...")
            result = subprocess.run(convert_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Conversion failed: {result.stderr}")
                return False, result.stderr
            
            print(f"✅ Converted to: {py_file}")
            
            # Start monitoring
            monitor_thread = threading.Thread(target=self.monitor_ports, daemon=True)
            monitor_thread.start()
            
            # Execute Python file
            print("Executing Python script...")
            exec_result = subprocess.run([sys.executable, str(py_file)], 
                                       capture_output=True, text=True, 
                                       cwd=str(py_file.parent))
            
            if exec_result.returncode == 0:
                print("✅ Python execution completed")
                return True, str(py_file)
            else:
                print(f"⚠️ Python execution had issues: {exec_result.stderr}")
                return True, f"Completed with warnings: {exec_result.stderr}"
                
        except Exception as e:
            print(f"❌ Python execution exception: {e}")
            return False, str(e)
    
    def wait_for_server(self, timeout=300):
        """Wait for Pinokio server to start"""
        print(f"\n⏳ Waiting for Pinokio server (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.pinokio_port:
                print(f"🎉 SUCCESS! Pinokio server running on port {self.pinokio_port}")
                return self.pinokio_port
            
            # Manual check
            ports = [8080, 3000, 5000, 7860, 8000]
            for port in ports:
                try:
                    response = requests.get(f'http://localhost:{port}', timeout=2)
                    if response.status_code == 200:
                        print(f"🌐 Server found on port {port}! Checking if it's Pinokio...")
                        print(f"🔗 Try this URL: http://localhost:{port}")
                        
                        # Basic content check
                        content = response.text[:500].lower()
                        if 'pinokio' in content or 'dashboard' in content:
                            print(f"🎯 CONFIRMED: Pinokio server on port {port}!")
                            self.pinokio_port = port
                            return port
                        else:
                            print(f"📄 Content preview: {content[:100]}...")
                            
                except:
                    continue
            
            print(f"⏳ Still waiting... ({int(time.time() - start_time)}s elapsed)")
            time.sleep(10)
        
        print("⏰ Timeout reached")
        return None
    
    def run_full_test(self):
        """Run complete test sequence"""
        print(f"\n{'='*60}")
        print("🚀 STARTING DIRECT PINOKIO EXECUTION TEST")
        print(f"{'='*60}")
        
        # Setup environment
        self.setup_environment()
        
        # Try Method 1: jupyter nbconvert
        method1_success, method1_result = self.execute_with_jupyter()
        
        # Wait a bit for server startup
        time.sleep(15)
        
        # Check for server
        server_port = self.wait_for_server(timeout=120)
        
        if server_port:
            print(f"\n🎉 SUCCESS WITH METHOD 1!")
            print(f"🌐 Pinokio UI: http://localhost:{server_port}")
            return {
                'success': True,
                'method': 'jupyter_nbconvert',
                'port': server_port,
                'url': f'http://localhost:{server_port}'
            }
        
        print("\n🔄 Method 1 didn't start server, trying Method 2...")
        
        # Try Method 2: Python conversion
        method2_success, method2_result = self.execute_with_python()
        
        # Wait for server again
        time.sleep(15)
        server_port = self.wait_for_server(timeout=120)
        
        if server_port:
            print(f"\n🎉 SUCCESS WITH METHOD 2!")
            print(f"🌐 Pinokio UI: http://localhost:{server_port}")
            return {
                'success': True,
                'method': 'python_conversion',
                'port': server_port,
                'url': f'http://localhost:{server_port}'
            }
        
        # Final attempt - scan all ports manually
        print("\n🔍 Final scan for any web servers...")
        for port in range(3000, 9001, 100):
            try:
                response = requests.get(f'http://localhost:{port}', timeout=1)
                if response.status_code == 200:
                    print(f"🌐 Found server on port {port}: http://localhost:{port}")
            except:
                continue
        
        return {
            'success': False,
            'method1_result': method1_result,
            'method2_result': method2_result,
            'message': 'Pinokio server not detected'
        }
    
    def cleanup(self):
        """Stop monitoring"""
        self.monitoring = False

def main():
    executor = DirectPinokioExecutor()
    
    try:
        result = executor.run_full_test()
        
        print(f"\n{'='*60}")
        print("🏁 FINAL RESULTS")
        print(f"{'='*60}")
        print(json.dumps(result, indent=2))
        
        if result['success']:
            print(f"\n🎉 PINOKIO IS RUNNING!")
            print(f"🌐 Access at: {result['url']}")
            print("\n⏳ Keeping server alive... Press Ctrl+C to stop")
            
            try:
                while True:
                    time.sleep(10)
                    # Keep checking server is still alive
                    try:
                        response = requests.get(result['url'], timeout=5)
                        if response.status_code != 200:
                            print("⚠️ Server might have stopped")
                            break
                    except:
                        print("⚠️ Server connection lost")
                        break
            except KeyboardInterrupt:
                print("\n🛑 Stopping...")
        else:
            print("\n💥 FAILED TO START PINOKIO SERVER")
            print("Check the execution logs above for errors")
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    finally:
        executor.cleanup()

if __name__ == "__main__":
    main()
