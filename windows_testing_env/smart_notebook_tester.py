#!/usr/bin/env python3
"""
Smart Notebook Tester with Ngrok Integration
Auto-discovers notebooks and provides comprehensive testing with UI access
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
from typing import List, Dict, Optional
import requests
import threading
import signal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class SmartNotebookTester:
    def __init__(self, ngrok_token: str = None):
        self.project_root = Path(__file__).parent.parent
        self.test_output_dir = self.project_root / "windows_testing_env" / "test_outputs"
        self.test_output_dir.mkdir(exist_ok=True)
        
        self.ngrok_token = ngrok_token
        self.ngrok_process = None
        self.pinokio_process = None
        self.ngrok_url = None
        
        # Setup logging
        self.setup_logging()
        
        # Setup signal handlers for cleanup
        signal.signal(signal.SIGINT, self.cleanup_handler)
        signal.signal(signal.SIGTERM, self.cleanup_handler)
    
    def setup_logging(self):
        """Setup logging with Unicode support"""
        log_file = self.test_output_dir / f"smart_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def discover_notebooks(self) -> List[Path]:
        """Auto-discover all notebook files in project"""
        notebooks = []
        
        # Search patterns and locations
        search_paths = [
            self.project_root,
            self.project_root / "github_upload",
            self.project_root / "archive"
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                for notebook_file in search_path.rglob("*.ipynb"):
                    # Skip checkpoint files
                    if ".ipynb_checkpoints" not in str(notebook_file):
                        notebooks.append(notebook_file)
        
        self.logger.info(f"Discovered {len(notebooks)} notebooks:")
        for nb in notebooks:
            self.logger.info(f"  - {nb.relative_to(self.project_root)}")
        
        return notebooks
    
    def analyze_notebook(self, notebook_path: Path) -> Dict:
        """Analyze notebook structure and content"""
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            
            analysis = {
                'path': str(notebook_path),
                'name': notebook_path.name,
                'cell_count': len(nb.cells),
                'code_cells': len([c for c in nb.cells if c.cell_type == 'code']),
                'markdown_cells': len([c for c in nb.cells if c.cell_type == 'markdown']),
                'has_pinokio_imports': False,
                'has_ngrok_setup': False,
                'has_ui_launch': False,
                'estimated_runtime': 'medium'
            }
            
            # Analyze content
            all_source = '\n'.join([cell.get('source', '') for cell in nb.cells if cell.cell_type == 'code'])
            
            if 'pinokio' in all_source.lower():
                analysis['has_pinokio_imports'] = True
            if 'ngrok' in all_source.lower():
                analysis['has_ngrok_setup'] = True
            if any(term in all_source.lower() for term in ['launch', 'start_server', 'run_ui']):
                analysis['has_ui_launch'] = True
            
            # Estimate runtime based on content
            if analysis['code_cells'] > 20 or 'install' in all_source.lower():
                analysis['estimated_runtime'] = 'long'
            elif analysis['code_cells'] < 5:
                analysis['estimated_runtime'] = 'short'
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze notebook {notebook_path}: {e}")
            return {'path': str(notebook_path), 'error': str(e)}
    
    def setup_ngrok(self) -> bool:
        """Setup ngrok with provided token"""
        if not self.ngrok_token:
            self.logger.warning("No ngrok token provided")
            return False
        
        try:
            # Install ngrok if not present
            try:
                subprocess.run(['ngrok', 'version'], check=True, capture_output=True)
                self.logger.info("Ngrok already installed")
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.logger.info("Installing ngrok...")
                # Download and install ngrok
                self.install_ngrok()
            
            # Authenticate ngrok
            self.logger.info("Authenticating ngrok...")
            result = subprocess.run(['ngrok', 'config', 'add-authtoken', self.ngrok_token], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Ngrok authentication successful")
                return True
            else:
                self.logger.error(f"Ngrok authentication failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to setup ngrok: {e}")
            return False
    
    def install_ngrok(self):
        """Install ngrok on Windows"""
        try:
            # Download ngrok for Windows
            ngrok_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
            
            import zipfile
            import tempfile
            
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / "ngrok.zip"
                
                self.logger.info("Downloading ngrok...")
                response = requests.get(ngrok_url)
                response.raise_for_status()
                
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                
                # Extract ngrok
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Move to system PATH or project directory
                ngrok_exe = Path(temp_dir) / "ngrok.exe"
                target_path = self.project_root / "windows_testing_env" / "ngrok.exe"
                
                import shutil
                shutil.move(str(ngrok_exe), str(target_path))
                
                # Add to PATH for this session
                env_path = os.environ.get('PATH', '')
                os.environ['PATH'] = f"{target_path.parent};{env_path}"
                
                self.logger.info(f"Ngrok installed to {target_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to install ngrok: {e}")
            raise
    
    def start_ngrok_tunnel(self, port: int = 8080) -> Optional[str]:
        """Start ngrok tunnel and return public URL"""
        try:
            self.logger.info(f"Starting ngrok tunnel for port {port}...")
            
            # Start ngrok in background
            self.ngrok_process = subprocess.Popen(
                ['ngrok', 'http', str(port), '--log=stdout'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for ngrok to start and get URL
            time.sleep(3)
            
            try:
                # Get tunnel info from ngrok API
                response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
                if response.status_code == 200:
                    tunnels = response.json()['tunnels']
                    if tunnels:
                        self.ngrok_url = tunnels[0]['public_url']
                        self.logger.info(f"Ngrok tunnel active: {self.ngrok_url}")
                        return self.ngrok_url
            except:
                pass
            
            # Fallback: parse from stdout
            if self.ngrok_process.poll() is None:
                # Process is running, try to get URL from output
                time.sleep(2)
                self.logger.info("Ngrok started, URL will be available shortly")
                return "http://pending.ngrok.url"
            
        except Exception as e:
            self.logger.error(f"Failed to start ngrok tunnel: {e}")
        
        return None
    
    def execute_notebook_with_mock_env(self, notebook_path: Path) -> Dict:
        """Execute notebook with mock GPU environment"""
        try:
            # Import and setup mock environment
            mock_env_path = self.project_root / "windows_testing_env" / "mock_gpu_env.py"
            if mock_env_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("mock_gpu_env", mock_env_path)
                mock_env = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mock_env)
                
                # Apply mocks
                mock_env.setup_mock_environment()
                self.logger.info("Mock GPU environment activated")
            
            # Execute using papermill if available
            try:
                import papermill as pm
                
                output_path = self.test_output_dir / f"executed_{notebook_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ipynb"
                
                self.logger.info(f"Executing notebook with papermill: {notebook_path.name}")
                
                pm.execute_notebook(
                    str(notebook_path),
                    str(output_path),
                    kernel_name='python3',
                    progress_bar=True
                )
                
                return {
                    'status': 'success',
                    'output_path': str(output_path),
                    'method': 'papermill'
                }
                
            except ImportError:
                self.logger.warning("Papermill not available, using jupyter nbconvert")
                return self.execute_with_nbconvert(notebook_path)
            
        except Exception as e:
            self.logger.error(f"Failed to execute notebook: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'method': 'failed'
            }
    
    def execute_with_nbconvert(self, notebook_path: Path) -> Dict:
        """Execute notebook using jupyter nbconvert"""
        try:
            output_path = self.test_output_dir / f"nbconvert_{notebook_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ipynb"
            
            cmd = [
                'jupyter', 'nbconvert',
                '--to', 'notebook',
                '--execute',
                '--output', str(output_path),
                str(notebook_path)
            ]
            
            self.logger.info(f"Executing with nbconvert: {notebook_path.name}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            if result.returncode == 0:
                return {
                    'status': 'success',
                    'output_path': str(output_path),
                    'method': 'nbconvert'
                }
            else:
                return {
                    'status': 'error',
                    'error': result.stderr,
                    'method': 'nbconvert'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'method': 'nbconvert'
            }
    
    def monitor_for_pinokio_server(self) -> Optional[int]:
        """Monitor for Pinokio server startup and return port"""
        self.logger.info("Monitoring for Pinokio server startup...")
        
        # Common ports Pinokio might use
        ports_to_check = [8080, 3000, 5000, 7860, 8000]
        
        for attempt in range(60):  # Check for 5 minutes
            for port in ports_to_check:
                try:
                    response = requests.get(f'http://localhost:{port}', timeout=2)
                    if response.status_code == 200 or 'pinokio' in response.text.lower():
                        self.logger.info(f"Pinokio server detected on port {port}")
                        return port
                except:
                    continue
            
            time.sleep(5)
        
        self.logger.warning("No Pinokio server detected")
        return None
    
    def cleanup_handler(self, signum, frame):
        """Handle cleanup on exit"""
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup processes"""
        self.logger.info("Cleaning up processes...")
        
        if self.ngrok_process:
            try:
                self.ngrok_process.terminate()
                self.ngrok_process.wait(timeout=5)
            except:
                try:
                    self.ngrok_process.kill()
                except:
                    pass
        
        if self.pinokio_process:
            try:
                self.pinokio_process.terminate()
                self.pinokio_process.wait(timeout=5)
            except:
                try:
                    self.pinokio_process.kill()
                except:
                    pass
    
    def run_comprehensive_test(self, target_notebook: str = None) -> Dict:
        """Run comprehensive test with ngrok integration"""
        try:
            # Discover notebooks
            notebooks = self.discover_notebooks()
            
            if target_notebook:
                # Filter to specific notebook
                target_path = Path(target_notebook)
                if not target_path.is_absolute():
                    target_path = self.project_root / target_notebook
                
                notebooks = [nb for nb in notebooks if nb.name == target_path.name or str(nb) == str(target_path)]
                
                if not notebooks:
                    self.logger.error(f"Target notebook not found: {target_notebook}")
                    return {'status': 'error', 'error': 'Notebook not found'}
            
            if not notebooks:
                self.logger.error("No notebooks found")
                return {'status': 'error', 'error': 'No notebooks found'}
            
            # Setup ngrok
            ngrok_ready = self.setup_ngrok()
            
            results = []
            
            for notebook in notebooks:
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"Testing notebook: {notebook.relative_to(self.project_root)}")
                self.logger.info(f"{'='*60}")
                
                # Analyze notebook
                analysis = self.analyze_notebook(notebook)
                self.logger.info(f"Notebook analysis: {json.dumps(analysis, indent=2)}")
                
                # Execute notebook
                execution_result = self.execute_notebook_with_mock_env(notebook)
                
                if execution_result['status'] == 'success':
                    # Monitor for server startup
                    server_port = self.monitor_for_pinokio_server()
                    
                    if server_port and ngrok_ready:
                        # Start ngrok tunnel
                        ngrok_url = self.start_ngrok_tunnel(server_port)
                        execution_result['ngrok_url'] = ngrok_url
                        execution_result['server_port'] = server_port
                        
                        if ngrok_url:
                            self.logger.info(f"\n🎉 SUCCESS! Pinokio UI accessible at: {ngrok_url}")
                            self.logger.info(f"Local server running on port: {server_port}")
                
                results.append({
                    'notebook': str(notebook.relative_to(self.project_root)),
                    'analysis': analysis,
                    'execution': execution_result
                })
            
            return {
                'status': 'completed',
                'results': results,
                'ngrok_url': self.ngrok_url
            }
            
        except Exception as e:
            self.logger.error(f"Comprehensive test failed: {e}")
            return {'status': 'error', 'error': str(e)}

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Notebook Tester with Ngrok Integration')
    parser.add_argument('--notebook', '-n', help='Specific notebook to test')
    parser.add_argument('--ngrok-token', '-t', help='Ngrok authentication token')
    parser.add_argument('--list-notebooks', '-l', action='store_true', help='List discovered notebooks')
    
    args = parser.parse_args()
    
    # Use provided token or environment variable
    ngrok_token = args.ngrok_token or os.environ.get('NGROK_TOKEN')
    
    tester = SmartNotebookTester(ngrok_token=ngrok_token)
    
    if args.list_notebooks:
        notebooks = tester.discover_notebooks()
        print(f"\nDiscovered {len(notebooks)} notebooks:")
        for nb in notebooks:
            print(f"  - {nb.relative_to(tester.project_root)}")
        return
    
    try:
        # Run comprehensive test
        result = tester.run_comprehensive_test(args.notebook)
        
        print(f"\n{'='*60}")
        print("TEST RESULTS")
        print(f"{'='*60}")
        print(json.dumps(result, indent=2))
        
        if result.get('ngrok_url'):
            print(f"\n🌐 Pinokio UI: {result['ngrok_url']}")
            print("Press Ctrl+C to stop...")
            
            # Keep running to maintain tunnel
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                print("\nShutting down...")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        tester.cleanup()

if __name__ == "__main__":
    main()
