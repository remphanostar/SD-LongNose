#!/usr/bin/env python3
"""
Enhanced Windows Notebook Tester - Dual Method Testing with Iterative Debugging
Tests actual .ipynb files directly using two different execution methods until Pinokio loads
"""

import os
import sys
import json
import time
import subprocess
import logging
import nbformat
from pathlib import Path
from datetime import datetime
import requests
import threading
import queue
import tempfile
import shutil
from typing import List, Dict, Optional, Tuple
import jupyter_client
import signal

class EnhancedNotebookTester:
    def __init__(self, ngrok_token: str):
        self.project_root = Path(__file__).parent.parent
        self.test_output_dir = self.project_root / "windows_testing_env" / "test_outputs"
        self.test_output_dir.mkdir(exist_ok=True)
        
        self.ngrok_token = ngrok_token
        self.ngrok_process = None
        self.jupyter_processes = []
        self.kernel_manager = None
        self.kernel_client = None
        
        # Debug tracking
        self.current_attempt = 0
        self.max_attempts = 5
        self.last_error = None
        self.pinokio_detected_port = None
        
        self.setup_logging()
        self.setup_mock_environment()
        
        # Cleanup handler
        signal.signal(signal.SIGINT, self.cleanup_handler)
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.test_output_dir / f"enhanced_test_{timestamp}.log"
        
        # Create logger with multiple handlers
        self.logger = logging.getLogger('enhanced_tester')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Enhanced Notebook Tester Started - Log: {log_file}")
    
    def setup_mock_environment(self):
        """Setup mock GPU environment for Windows testing"""
        try:
            mock_env_path = self.project_root / "windows_testing_env" / "mock_gpu_env.py"
            if mock_env_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("mock_gpu_env", mock_env_path)
                mock_env = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mock_env)
                mock_env.setup_mock_environment()
                self.logger.info("Mock GPU environment activated")
            else:
                self.logger.warning("Mock GPU environment not found")
        except Exception as e:
            self.logger.error(f"Failed to setup mock environment: {e}")
    
    def install_ngrok(self) -> bool:
        """Install and setup ngrok - skip if failing and focus on Pinokio"""
        try:
            # Check if ngrok exists
            ngrok_path = self.project_root / "windows_testing_env" / "ngrok.exe"
            
            if not ngrok_path.exists():
                self.logger.warning("⚠️ Ngrok installation skipped - will use manual tunnel later")
                self.logger.info("Focusing on getting Pinokio running first...")
                return False  # Skip ngrok for now
            
            # Add to PATH if exists
            env_path = os.environ.get('PATH', '')
            ngrok_dir = str(ngrok_path.parent)
            if ngrok_dir not in env_path:
                os.environ['PATH'] = f"{ngrok_dir};{env_path}"
            
            # Authenticate if exists
            if self.ngrok_token:
                self.logger.info("Authenticating existing ngrok...")
                auth_cmd = [str(ngrok_path), 'config', 'add-authtoken', self.ngrok_token]
                result = subprocess.run(auth_cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.logger.info("✅ Ngrok authenticated successfully")
                    return True
                else:
                    self.logger.warning(f"Ngrok authentication failed: {result.stderr}")
                    return False
            
            return True
                
        except Exception as e:
            self.logger.warning(f"Ngrok setup failed: {e} - continuing without ngrok")
            return False
    
    def start_ngrok_tunnel(self, port: int) -> Optional[str]:
        """Start ngrok tunnel and return public URL"""
        try:
            ngrok_path = self.project_root / "windows_testing_env" / "ngrok.exe"
            
            self.logger.info(f"Starting ngrok tunnel for port {port}...")
            
            # Kill existing ngrok processes
            subprocess.run(['taskkill', '/F', '/IM', 'ngrok.exe'], capture_output=True)
            time.sleep(2)
            
            # Start ngrok
            self.ngrok_process = subprocess.Popen(
                [str(ngrok_path), 'http', str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for tunnel to establish
            for attempt in range(10):
                time.sleep(2)
                try:
                    response = requests.get('http://localhost:4040/api/tunnels', timeout=3)
                    if response.status_code == 200:
                        tunnels = response.json().get('tunnels', [])
                        if tunnels:
                            public_url = tunnels[0]['public_url']
                            self.logger.info(f"🎉 NGROK TUNNEL ACTIVE: {public_url}")
                            return public_url
                except:
                    continue
            
            self.logger.warning("Ngrok tunnel failed to establish")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to start ngrok: {e}")
            return None
    
    def method1_nbconvert_execution(self, notebook_path: Path) -> Tuple[bool, str, Optional[str]]:
        """
        METHOD 1: Direct nbconvert execution with real-time monitoring
        Returns: (success, output_path, error_message)
        """
        self.logger.info(f"🔍 METHOD 1: nbconvert execution of {notebook_path.name}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = self.test_output_dir / f"method1_{notebook_path.stem}_{timestamp}.ipynb"
        
        try:
            # Prepare execution command
            cmd = [
                'jupyter', 'nbconvert',
                '--to', 'notebook',
                '--execute',
                '--allow-errors',
                '--ExecutePreprocessor.timeout=1800',  # 30 minutes
                '--output', str(output_path),
                str(notebook_path)
            ]
            
            self.logger.info(f"Executing: {' '.join(cmd)}")
            
            # Start execution with real-time monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(notebook_path.parent)
            )
            
            # Monitor execution
            stdout_lines = []
            stderr_lines = []
            
            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self.monitor_pinokio_startup,
                args=(process,),
                daemon=True
            )
            monitor_thread.start()
            
            # Wait for completion
            stdout, stderr = process.communicate()
            
            stdout_lines.append(stdout)
            stderr_lines.append(stderr)
            
            if process.returncode == 0:
                self.logger.info(f"✅ METHOD 1 SUCCESS: {output_path}")
                return True, str(output_path), None
            else:
                error_msg = f"nbconvert failed: {stderr}"
                self.logger.error(f"❌ METHOD 1 FAILED: {error_msg}")
                return False, str(output_path), error_msg
                
        except Exception as e:
            error_msg = f"Method 1 exception: {str(e)}"
            self.logger.error(f"❌ METHOD 1 EXCEPTION: {error_msg}")
            return False, "", error_msg
    
    def method2_kernel_execution(self, notebook_path: Path) -> Tuple[bool, str, Optional[str]]:
        """
        METHOD 2: Jupyter kernel-based execution with cell-by-cell debugging
        Returns: (success, output_path, error_message)
        """
        self.logger.info(f"🔍 METHOD 2: Kernel execution of {notebook_path.name}")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = self.test_output_dir / f"method2_{notebook_path.stem}_{timestamp}.ipynb"
        
        try:
            # Load notebook
            with open(notebook_path, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            
            # Start kernel
            self.kernel_manager = jupyter_client.KernelManager(kernel_name='python3')
            self.kernel_manager.start_kernel()
            self.kernel_client = self.kernel_manager.client()
            
            self.logger.info("Jupyter kernel started")
            
            # Execute cells one by one
            executed_cells = 0
            total_cells = len([cell for cell in nb.cells if cell.cell_type == 'code'])
            
            for i, cell in enumerate(nb.cells):
                if cell.cell_type != 'code':
                    continue
                
                executed_cells += 1
                self.logger.info(f"Executing cell {executed_cells}/{total_cells}")
                
                # Execute cell
                msg_id = self.kernel_client.execute(cell.source)
                
                # Collect outputs
                outputs = []
                while True:
                    try:
                        msg = self.kernel_client.get_iopub_msg(timeout=60)
                        
                        if msg['parent_header'].get('msg_id') == msg_id:
                            msg_type = msg['header']['msg_type']
                            
                            if msg_type == 'execute_result':
                                outputs.append(nbformat.v4.new_output(
                                    output_type='execute_result',
                                    data=msg['content']['data'],
                                    execution_count=msg['content']['execution_count']
                                ))
                            elif msg_type == 'display_data':
                                outputs.append(nbformat.v4.new_output(
                                    output_type='display_data',
                                    data=msg['content']['data']
                                ))
                            elif msg_type == 'stream':
                                outputs.append(nbformat.v4.new_output(
                                    output_type='stream',
                                    name=msg['content']['name'],
                                    text=msg['content']['text']
                                ))
                            elif msg_type == 'error':
                                outputs.append(nbformat.v4.new_output(
                                    output_type='error',
                                    ename=msg['content']['ename'],
                                    evalue=msg['content']['evalue'],
                                    traceback=msg['content']['traceback']
                                ))
                            elif msg_type == 'status' and msg['content']['execution_state'] == 'idle':
                                break
                    except queue.Empty:
                        self.logger.warning(f"Cell {executed_cells} timeout")
                        break
                
                # Update cell with outputs
                cell.outputs = outputs
                
                # Check for Pinokio server startup
                if self.check_for_pinokio_in_outputs(outputs):
                    self.logger.info(f"🎯 Pinokio detected in cell {executed_cells} outputs!")
                    break
            
            # Save executed notebook
            with open(output_path, 'w', encoding='utf-8') as f:
                nbformat.write(nb, f)
            
            self.logger.info(f"✅ METHOD 2 SUCCESS: {output_path}")
            return True, str(output_path), None
            
        except Exception as e:
            error_msg = f"Method 2 exception: {str(e)}"
            self.logger.error(f"❌ METHOD 2 EXCEPTION: {error_msg}")
            return False, str(output_path) if 'output_path' in locals() else "", error_msg
        finally:
            # Cleanup kernel
            if hasattr(self, 'kernel_client') and self.kernel_client:
                self.kernel_client.stop_channels()
            if hasattr(self, 'kernel_manager') and self.kernel_manager:
                self.kernel_manager.shutdown_kernel()
    
    def check_for_pinokio_in_outputs(self, outputs: List) -> bool:
        """Check if Pinokio server startup is detected in cell outputs"""
        for output in outputs:
            if hasattr(output, 'text'):
                text = str(output.text).lower()
                if any(keyword in text for keyword in ['pinokio', 'server started', 'localhost', 'http://']):
                    return True
        return False
    
    def monitor_pinokio_startup(self, process):
        """Monitor for Pinokio server startup during execution"""
        ports_to_check = [8080, 3000, 5000, 7860, 8000, 8888, 9000]
        
        while process.poll() is None:  # While process is running
            for port in ports_to_check:
                try:
                    response = requests.get(f'http://localhost:{port}', timeout=1)
                    if response.status_code == 200:
                        content = response.text.lower()
                        if any(keyword in content for keyword in ['pinokio', 'dashboard', 'api']):
                            self.logger.info(f"🎯 PINOKIO SERVER DETECTED on port {port}!")
                            self.pinokio_detected_port = port
                            return port
                except:
                    continue
            time.sleep(5)
        
        return None
    
    def detect_active_pinokio_server(self) -> Optional[int]:
        """Scan for active Pinokio server"""
        ports_to_check = [8080, 3000, 5000, 7860, 8000, 8888, 9000]
        
        self.logger.info("Scanning for active Pinokio server...")
        
        for port in ports_to_check:
            try:
                response = requests.get(f'http://localhost:{port}', timeout=2)
                if response.status_code == 200:
                    content = response.text.lower()
                    self.logger.debug(f"Port {port} response preview: {content[:200]}...")
                    
                    if any(keyword in content for keyword in ['pinokio', 'dashboard', 'api', 'home']):
                        self.logger.info(f"🎯 ACTIVE PINOKIO SERVER FOUND on port {port}")
                        return port
                    else:
                        self.logger.debug(f"Port {port} active but not Pinokio")
                        
            except Exception as e:
                self.logger.debug(f"Port {port} check failed: {e}")
                continue
        
        self.logger.warning("No active Pinokio server detected")
        return None
    
    def iterative_debug_loop(self, notebook_path: Path) -> Dict:
        """Main iterative debugging loop until Pinokio loads"""
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"🚀 STARTING ITERATIVE DEBUG LOOP FOR: {notebook_path.name}")
        self.logger.info(f"{'='*80}")
        
        results = []
        
        for attempt in range(1, self.max_attempts + 1):
            self.current_attempt = attempt
            self.logger.info(f"\n🔄 ATTEMPT {attempt}/{self.max_attempts}")
            
            # Try Method 1: nbconvert
            self.logger.info(f"\n--- Attempt {attempt}: METHOD 1 (nbconvert) ---")
            method1_success, method1_output, method1_error = self.method1_nbconvert_execution(notebook_path)
            
            # Check for Pinokio after Method 1
            pinokio_port = self.detect_active_pinokio_server()
            
            if pinokio_port:
                self.logger.info(f"🎉 SUCCESS! Pinokio found on port {pinokio_port} after Method 1")
                
                # Start ngrok tunnel
                ngrok_url = self.start_ngrok_tunnel(pinokio_port)
                
                return {
                    'success': True,
                    'method': 'method1_nbconvert',
                    'attempt': attempt,
                    'pinokio_port': pinokio_port,
                    'ngrok_url': ngrok_url,
                    'output_file': method1_output,
                    'total_attempts': attempt
                }
            
            # Try Method 2: kernel execution
            self.logger.info(f"\n--- Attempt {attempt}: METHOD 2 (kernel) ---")
            method2_success, method2_output, method2_error = self.method2_kernel_execution(notebook_path)
            
            # Check for Pinokio after Method 2
            pinokio_port = self.detect_active_pinokio_server()
            
            if pinokio_port:
                self.logger.info(f"🎉 SUCCESS! Pinokio found on port {pinokio_port} after Method 2")
                
                # Start ngrok tunnel
                ngrok_url = self.start_ngrok_tunnel(pinokio_port)
                
                return {
                    'success': True,
                    'method': 'method2_kernel',
                    'attempt': attempt,
                    'pinokio_port': pinokio_port,
                    'ngrok_url': ngrok_url,
                    'output_file': method2_output,
                    'total_attempts': attempt
                }
            
            # Record attempt results
            attempt_result = {
                'attempt': attempt,
                'method1': {'success': method1_success, 'output': method1_output, 'error': method1_error},
                'method2': {'success': method2_success, 'output': method2_output, 'error': method2_error},
                'pinokio_detected': False
            }
            results.append(attempt_result)
            
            self.logger.warning(f"❌ Attempt {attempt} failed - Pinokio not detected")
            
            # Wait before next attempt
            if attempt < self.max_attempts:
                self.logger.info(f"⏳ Waiting 10 seconds before next attempt...")
                time.sleep(10)
        
        # All attempts failed
        self.logger.error(f"💥 ALL {self.max_attempts} ATTEMPTS FAILED")
        return {
            'success': False,
            'total_attempts': self.max_attempts,
            'results': results,
            'final_error': 'Pinokio server never started successfully'
        }
    
    def cleanup_handler(self, signum, frame):
        """Handle cleanup on interrupt"""
        self.logger.info("🛑 Interrupt received, cleaning up...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup all processes"""
        try:
            # Kill ngrok
            if self.ngrok_process:
                self.ngrok_process.terminate()
            
            # Kill any jupyter processes
            for proc in self.jupyter_processes:
                try:
                    proc.terminate()
                except:
                    pass
            
            # Cleanup kernel
            if hasattr(self, 'kernel_client') and self.kernel_client:
                self.kernel_client.stop_channels()
            if hasattr(self, 'kernel_manager') and self.kernel_manager:
                self.kernel_manager.shutdown_kernel()
            
            # Kill any remaining processes
            subprocess.run(['taskkill', '/F', '/IM', 'ngrok.exe'], capture_output=True)
            subprocess.run(['taskkill', '/F', '/IM', 'jupyter.exe'], capture_output=True)
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Windows Notebook Tester')
    parser.add_argument('notebook', help='Path to notebook file to test')
    parser.add_argument('--ngrok-token', '-t', required=True, help='Ngrok authentication token')
    parser.add_argument('--max-attempts', '-m', type=int, default=5, help='Maximum debug attempts')
    
    args = parser.parse_args()
    
    # Convert notebook path
    notebook_path = Path(args.notebook)
    if not notebook_path.is_absolute():
        notebook_path = Path.cwd() / notebook_path
    
    if not notebook_path.exists():
        print(f"❌ Notebook not found: {notebook_path}")
        return 1
    
    # Create tester
    tester = EnhancedNotebookTester(args.ngrok_token)
    tester.max_attempts = args.max_attempts
    
    # Install ngrok
    if not tester.install_ngrok():
        print("❌ Failed to setup ngrok")
        return 1
    
    try:
        # Run iterative debug loop
        result = tester.iterative_debug_loop(notebook_path)
        
        print(f"\n{'='*80}")
        print("🏁 FINAL RESULTS")
        print(f"{'='*80}")
        print(json.dumps(result, indent=2))
        
        if result['success']:
            print(f"\n🎉 SUCCESS! Pinokio UI accessible at: {result.get('ngrok_url', 'N/A')}")
            print(f"📊 Local server: http://localhost:{result.get('pinokio_port', 'N/A')}")
            print(f"🔄 Total attempts needed: {result.get('total_attempts', 'N/A')}")
            
            # Keep running to maintain tunnel
            print("\n⏳ Keeping tunnel active... Press Ctrl+C to stop")
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                print("\n🛑 Stopping...")
        else:
            print(f"\n💥 FAILED after {result.get('total_attempts', 'N/A')} attempts")
            return 1
    
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        return 1
    finally:
        tester.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
