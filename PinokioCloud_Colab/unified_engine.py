"""
Unified Pinokio Engine - Google Colab Optimized
Simplified unified engine for managing Pinokio apps in cloud environment
"""

import json
import os
import sys
import subprocess
import asyncio
import shutil
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import tempfile
import time

class UnifiedPinokioEngine:
    """Unified engine for Pinokio app management in Google Colab"""
    
    def __init__(self, base_path: str = "/content/pinokio_apps", apps_data_path: str = None):
        """Initialize the unified engine with Colab-specific paths"""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load apps data
        if apps_data_path and Path(apps_data_path).exists():
            self.apps_data_path = Path(apps_data_path)
            self.apps_data = self.load_apps_data()
        else:
            self.apps_data = []
            self.logger.warning(f"Apps data file not found: {apps_data_path}")
        
        # State management
        self.state_file = self.base_path / "engine_state.json"
        self.installed_apps = {}
        self.running_processes = {}
        self.app_urls = {}
        
        # Load existing state
        self.load_state()
        
        self.logger.info(f"UnifiedPinokioEngine initialized")
        self.logger.info(f"Base path: {self.base_path}")
        self.logger.info(f"Apps loaded: {len(self.apps_data)}")
    
    def load_apps_data(self) -> List[Dict]:
        """Load apps data from JSON file"""
        try:
            with open(self.apps_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.logger.info(f"Loaded {len(data)} apps from {self.apps_data_path}")
                return data
        except Exception as e:
            self.logger.error(f"Failed to load apps data: {e}")
            return []
    
    def load_state(self):
        """Load engine state from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.installed_apps = state.get('installed_apps', {})
                    self.app_urls = state.get('app_urls', {})
                    self.logger.info(f"Loaded state: {len(self.installed_apps)} installed apps")
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
    
    def save_state(self):
        """Save engine state to file"""
        try:
            state = {
                'installed_apps': self.installed_apps,
                'app_urls': self.app_urls,
                'last_updated': datetime.datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    def get_app_info(self, app_name: str) -> Optional[Dict]:
        """Get app information by name"""
        for app in self.apps_data:
            if app.get('title') == app_name:
                return app
        return None
    
    def get_installed_apps(self) -> List[str]:
        """Get list of installed app names"""
        return list(self.installed_apps.keys())
    
    def get_running_apps(self) -> List[str]:
        """Get list of currently running app names"""
        running = []
        for app_name, process in self.running_processes.items():
            if process and process.poll() is None:
                running.append(app_name)
        return running
    
    def get_app_urls(self, app_name: str) -> List[str]:
        """Get URLs for a running app"""
        return self.app_urls.get(app_name, [])
    
    async def install_app(self, app_name: str, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Install an app by cloning its repository and running install script"""
        try:
            if progress_callback:
                progress_callback(f"Starting installation of {app_name}")
            
            # Get app info
            app_info = self.get_app_info(app_name)
            if not app_info:
                if progress_callback:
                    progress_callback(f"App {app_name} not found in database")
                return False
            
            # Get repository URL
            repo_url = app_info.get('url')
            if not repo_url:
                if progress_callback:
                    progress_callback(f"No repository URL found for {app_name}")
                return False
            
            # Set up app directory
            app_path = self.base_path / app_name
            
            # Clone repository if it doesn't exist
            if not app_path.exists():
                if progress_callback:
                    progress_callback(f"Cloning repository: {repo_url}")
                
                try:
                    # Use subprocess for better Colab compatibility
                    result = subprocess.run([
                        'git', 'clone', '--depth', '1', repo_url, str(app_path)
                    ], capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        if progress_callback:
                            progress_callback(f"Repository cloned successfully")
                    else:
                        if progress_callback:
                            progress_callback(f"Git clone failed: {result.stderr}")
                        return False
                        
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"Failed to clone repository: {str(e)}")
                    return False
            
            # Look for install script
            install_script = None
            for script_name in ['install.js', 'install.json']:
                script_path = app_path / script_name
                if script_path.exists():
                    install_script = script_path
                    break
            
            if install_script:
                if progress_callback:
                    progress_callback(f"Found install script: {install_script.name}")
                
                # Execute install script
                result = await self.execute_script(install_script, app_path)
                
                if result.get('success'):
                    if progress_callback:
                        progress_callback("Installation completed successfully")
                else:
                    if progress_callback:
                        progress_callback(f"Installation failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                if progress_callback:
                    progress_callback("No install script found, marking as installed")
            
            # Mark as installed
            self.installed_apps[app_name] = {
                'path': str(app_path),
                'repo_url': repo_url,
                'installed_at': datetime.datetime.now().isoformat()
            }
            
            self.save_state()
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Installation error: {str(e)}")
            self.logger.error(f"Failed to install {app_name}: {e}")
            return False
    
    async def run_app(self, app_name: str, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Run an installed app"""
        try:
            if app_name not in self.installed_apps:
                if progress_callback:
                    progress_callback(f"App {app_name} is not installed")
                return False
            
            app_path = Path(self.installed_apps[app_name]['path'])
            if not app_path.exists():
                if progress_callback:
                    progress_callback(f"App directory not found: {app_path}")
                return False
            
            # Look for start script
            start_script = None
            for script_name in ['start.js', 'start.json', 'run.js', 'run.json']:
                script_path = app_path / script_name
                if script_path.exists():
                    start_script = script_path
                    break
            
            if not start_script:
                if progress_callback:
                    progress_callback(f"No start script found for {app_name}")
                return False
            
            if progress_callback:
                progress_callback(f"Found start script: {start_script.name}")
            
            # Execute start script
            result = await self.execute_script(start_script, app_path, daemon=True)
            
            if result.get('success'):
                if progress_callback:
                    progress_callback(f"{app_name} started successfully")
                
                # Store process reference if available
                if 'process' in result:
                    self.running_processes[app_name] = result['process']
                
                # Extract URLs if available
                if 'urls' in result:
                    self.app_urls[app_name] = result['urls']
                    self.save_state()
                
                return True
            else:
                if progress_callback:
                    progress_callback(f"Failed to start {app_name}: {result.get('error')}")
                return False
                
        except Exception as e:
            if progress_callback:
                progress_callback(f"Runtime error: {str(e)}")
            self.logger.error(f"Failed to run {app_name}: {e}")
            return False
    
    def stop_app(self, app_name: str) -> bool:
        """Stop a running app"""
        try:
            if app_name in self.running_processes:
                process = self.running_processes[app_name]
                if process and process.poll() is None:
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
                    del self.running_processes[app_name]
                    
                    # Clear URLs
                    if app_name in self.app_urls:
                        del self.app_urls[app_name]
                        self.save_state()
                    
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to stop {app_name}: {e}")
            return False
    
    def uninstall_app(self, app_name: str) -> bool:
        """Uninstall an app completely"""
        try:
            # Stop if running
            self.stop_app(app_name)
            
            # Remove from installed apps
            if app_name in self.installed_apps:
                app_path = Path(self.installed_apps[app_name]['path'])
                
                # Remove directory
                if app_path.exists():
                    shutil.rmtree(app_path)
                
                del self.installed_apps[app_name]
                self.save_state()
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Failed to uninstall {app_name}: {e}")
            return False
    
    async def execute_script(self, script_path: Path, working_dir: Path, daemon: bool = False) -> Dict[str, Any]:
        """Execute a Pinokio script (JS or JSON)"""
        try:
            # Read script content
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse script
            if script_path.suffix == '.json':
                script_data = json.loads(content)
            else:
                # For .js files, try to extract JSON-like structure
                # This is a simplified approach - in real Pinokio, this would be more complex
                try:
                    # Remove exports and module syntax for basic parsing
                    clean_content = content.replace('module.exports = ', '').replace('export default ', '')
                    script_data = json.loads(clean_content)
                except:
                    # If we can't parse as JSON, create a basic structure
                    script_data = {"run": [{"method": "shell.run", "params": {"message": f"node {script_path.name}"}}]}
            
            # Execute script steps
            return await self.execute_script_steps(script_data, working_dir, daemon)
            
        except Exception as e:
            self.logger.error(f"Failed to execute script {script_path}: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute_script_steps(self, script_data: Dict, working_dir: Path, daemon: bool = False) -> Dict[str, Any]:
        """Execute the steps in a Pinokio script"""
        try:
            steps = script_data.get('run', [])
            urls = []
            last_process = None
            
            for step in steps:
                method = step.get('method', '')
                params = step.get('params', {})
                
                if method == 'shell.run':
                    message = params.get('message', '')
                    if message:
                        # Execute shell command
                        result = await self.shell_run(message, working_dir, daemon)
                        if not result['success']:
                            return result
                        if 'process' in result:
                            last_process = result['process']
                
                elif method == 'shell.start':
                    message = params.get('message', '')
                    if message:
                        # Start process in background
                        result = await self.shell_run(message, working_dir, daemon=True)
                        if not result['success']:
                            return result
                        if 'process' in result:
                            last_process = result['process']
                
                elif method == 'fs.download':
                    url = params.get('url', '')
                    dest = params.get('dest', '')
                    if url and dest:
                        result = await self.fs_download(url, working_dir / dest)
                        if not result['success']:
                            return result
                
                # Extract URLs from events
                events = step.get('on', [])
                for event in events:
                    if 'http://localhost:' in str(event) or 'https://' in str(event):
                        # Extract URL pattern
                        import re
                        url_pattern = re.search(r'https?://[^\s\'"]+', str(event))
                        if url_pattern:
                            urls.append(url_pattern.group())
            
            result = {"success": True}
            if urls:
                result["urls"] = urls
            if last_process:
                result["process"] = last_process
                
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to execute script steps: {e}")
            return {"success": False, "error": str(e)}
    
    async def shell_run(self, command: str, working_dir: Path, daemon: bool = False) -> Dict[str, Any]:
        """Execute a shell command"""
        try:
            # Basic command execution - in Colab environment
            if daemon:
                # Start process in background
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=str(working_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                return {"success": True, "process": process}
            else:
                # Run and wait for completion
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(working_dir),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    return {"success": True, "stdout": result.stdout}
                else:
                    return {"success": False, "error": result.stderr}
        
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fs_download(self, url: str, dest_path: Path) -> Dict[str, Any]:
        """Download a file from URL"""
        try:
            import requests
            
            # Create destination directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}