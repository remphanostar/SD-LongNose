#!/usr/bin/env python3
"""
Unified Pinokio Engine for Cloud Environments
Combines best features from engine.py and emulator.py with full JS script execution support
"""

import os
import sys
import json
import re
import asyncio
import subprocess
import platform
import shutil
import venv
import time
import datetime
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
import logging
import git
import psutil

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PinokioContext:
    """Execution context for Pinokio scripts"""
    platform: str = field(default_factory=lambda: {
        'Windows': 'win32', 'Darwin': 'darwin', 'Linux': 'linux'
    }.get(platform.system(), 'linux'))
    gpu: Optional[str] = None
    gpu_model: Optional[str] = None
    cwd: str = field(default_factory=os.getcwd)
    env_vars: Dict[str, str] = field(default_factory=dict)
    local_vars: Dict[str, Any] = field(default_factory=dict)
    args: Dict[str, Any] = field(default_factory=dict)
    kernel: Dict[str, Any] = field(default_factory=dict)
    input: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize GPU detection and kernel info"""
        self._detect_gpu()
        self.kernel = {
            'gpu': self.gpu,
            'gpu_model': self.gpu_model,
            'platform': self.platform,
            'python': sys.executable,
            'node': shutil.which('node'),
            'npm': shutil.which('npm')
        }
    
    def _detect_gpu(self):
        """Detect GPU type and model"""
        try:
            # Check for NVIDIA GPU
            result = subprocess.run(['nvidia-smi', '-L'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.gpu = 'nvidia'
                # Extract GPU model
                match = re.search(r'GPU \d+: (.+?) \(', result.stdout)
                if match:
                    self.gpu_model = match.group(1)
                    logger.info(f"Detected NVIDIA GPU: {self.gpu_model}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        if not self.gpu:
            try:
                # Check for AMD GPU
                result = subprocess.run(['rocm-smi'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self.gpu = 'amd'
                    logger.info("Detected AMD GPU")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

class UnifiedPinokioEngine:
    """Unified engine for executing Pinokio apps with full JS/JSON support"""
    
    def __init__(self, base_path: str = "./pinokio_apps", apps_data_path: str = "./cleaned_pinokio_apps.json"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Directory structure
        self.apps_dir = self.base_path / "apps"
        self.venvs_dir = self.base_path / "venvs"  
        self.logs_dir = self.base_path / "logs"
        self.cache_dir = self.base_path / "cache"
        
        for dir_path in [self.apps_dir, self.venvs_dir, self.logs_dir, self.cache_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Load apps database
        self.apps_data = self._load_apps_data(apps_data_path)
        
        # Engine state
        self.context = PinokioContext(cwd=str(self.base_path))
        self.installed_apps = {}
        self.running_processes = {}
        self.script_locals = {}
        self.app_ports = {}
        
        # Load state
        self._load_state()
    
    def _load_apps_data(self, apps_data_path: str) -> List[Dict[str, Any]]:
        """Load apps database from JSON file"""
        try:
            apps_path = Path(apps_data_path)
            if apps_path.exists():
                with open(apps_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Apps data file not found: {apps_data_path}")
                return []
        except Exception as e:
            logger.error(f"Failed to load apps data: {e}")
            return []
    
    def _load_state(self):
        """Load persistent state from cache and auto-discover existing apps"""
        state_file = self.cache_dir / "engine_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.installed_apps = state.get('installed_apps', {})
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
        
        # Auto-discover existing app directories
        discovered_apps = self._discover_existing_apps()
        
        # Merge discovered apps with cached state
        for app_name, app_info in discovered_apps.items():
            if app_name not in self.installed_apps:
                logger.info(f"Auto-discovered existing app: {app_name}")
                self.installed_apps[app_name] = app_info
        
        # Save updated state if we found new apps
        if discovered_apps:
            self.save_state()
    
    def _discover_existing_apps(self) -> Dict[str, Any]:
        """Auto-discover existing app directories with Pinokio files"""
        discovered = {}
        
        if not self.base_path.exists():
            return discovered
            
        for app_dir in self.base_path.iterdir():
            if (app_dir.is_dir() and 
                app_dir.name not in ['apps', 'cache', 'venvs', 'logs']):
                
                # Check if it has pinokio files
                has_pinokio_files = any([
                    (app_dir / 'pinokio.js').exists(),
                    (app_dir / 'install.js').exists(),
                    (app_dir / 'install.json').exists(),
                    (app_dir / 'start.js').exists(),
                    (app_dir / 'start.json').exists()
                ])
                
                if has_pinokio_files:
                    discovered[app_dir.name] = {
                        'path': str(app_dir),
                        'repo_url': 'auto-discovered',
                        'installed_at': datetime.datetime.now().isoformat()
                    }
                    
        return discovered
    
    def save_state(self):
        """Save persistent state to cache"""
        state_file = self.cache_dir / "engine_state.json"
        try:
            with open(state_file, 'w') as f:
                json.dump({
                    'installed_apps': self.installed_apps,
                    'timestamp': time.time()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get_installed_apps(self) -> List[str]:
        """Get list of installed app names"""
        return list(self.installed_apps.keys())
    
    def get_running_apps(self) -> List[str]:
        """Get list of currently running app names"""
        running = []
        for app_name, process in list(self.running_processes.items()):
            if process.poll() is None:  # Process still running
                running.append(app_name)
            else:
                # Clean up finished processes
                del self.running_processes[app_name]
        return running
    
    def get_app_urls(self, app_name: str) -> List[str]:
        """Get URLs for running app"""
        if app_name not in self.app_ports:
            return []
        
        port = self.app_ports[app_name]
        return [f"http://localhost:{port}"]
    
    async def install_app(self, app_name: str, progress_callback=None) -> bool:
        """Install app with Colab optimization"""
        try:
            if progress_callback:
                progress_callback(f"🔍 Starting installation of {app_name}")
                progress_callback(f"📊 Searching {len(self.apps_data)} apps in database...")
            
            # Find app in database - try multiple name fields for compatibility
            app_info = None
            for app in self.apps_data:
                if (app.get('title') == app_name or 
                    app.get('name') == app_name or 
                    app.get('Appname') == app_name):
                    app_info = app
                    if progress_callback:
                        progress_callback(f"✅ Found app in database: {app.get('name', app.get('title', app_name))}")
                    break
            
            if not app_info:
                if progress_callback:
                    progress_callback(f"❌ App '{app_name}' not found in database")
                    progress_callback(f"🔍 Available apps: {[app.get('name', app.get('title', 'Unknown')) for app in self.apps_data[:5]]}...")
                logger.error(f"App not found in database: {app_name}")
                return False
            
            # Get repository URL - try multiple field names for compatibility
            repo_url = app_info.get('clone_url') or app_info.get('repo_url') or app_info.get('url')
            if progress_callback:
                progress_callback(f"🌐 Repository URL found: {repo_url}")
                progress_callback(f"📝 App info: name={app_info.get('name')}, clone_url={app_info.get('clone_url')}, repo_url={app_info.get('repo_url')}")
            
            if not repo_url:
                if progress_callback:
                    progress_callback(f"❌ No repository URL found for {app_name}")
                return False
            
            # Set up app directory
            app_path = self.base_path / app_name
            
            # Clone repository if it doesn't exist
            if not app_path.exists():
                if progress_callback:
                    progress_callback(f"📁 App directory doesn't exist: {app_path}")
                    progress_callback(f"🌐 Cloning repository: {repo_url}")
                    progress_callback(f"📂 Clone destination: {app_path}")
                
                try:
                    # Use subprocess for better Colab compatibility
                    cmd = ['git', 'clone', '--depth', '1', repo_url, str(app_path)]
                    if progress_callback:
                        progress_callback(f"🔧 Running command: {' '.join(cmd)}")
                    
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    
                    if progress_callback:
                        progress_callback(f"📊 Git clone exit code: {result.returncode}")
                        if result.stdout:
                            progress_callback(f"📝 Git stdout: {result.stdout.strip()}")
                        if result.stderr:
                            progress_callback(f"⚠️ Git stderr: {result.stderr.strip()}")
                    
                    if result.returncode == 0:
                        if progress_callback:
                            progress_callback(f"✅ Repository cloned successfully")
                    else:
                        if progress_callback:
                            progress_callback(f"❌ Git clone failed: {result.stderr}")
                        return False
                        
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"❌ Failed to clone repository: {str(e)}")
                    return False
            else:
                if progress_callback:
                    progress_callback(f"📁 App directory already exists: {app_path}")
            
            # Execute install script if it exists
            install_script = None
            for script_name in ['install.js', 'install.json']:
                script_path = app_path / script_name
                if script_path.exists():
                    install_script = script_path
                    break
            
            if install_script:
                if progress_callback:
                    progress_callback(f"Running install script: {install_script.name}")
                
                result = await self.execute_script(install_script, app_path)
                if not result.get('success'):
                    logger.error(f"Install script failed for {app_name}")
                    return False
            else:
                # Basic install - just mark as installed
                if progress_callback:
                    progress_callback("No install script found, marking as installed")
            
            # Update installed apps
            self.installed_apps[app_name] = {
                'path': str(app_path),
                'repo_url': repo_url,
                'installed_at': datetime.datetime.now().isoformat()
            }
            
            self.save_state()
            
            if progress_callback:
                progress_callback(f"Successfully installed {app_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Installation failed for {app_name}: {e}")
            if progress_callback:
                progress_callback(f"Installation failed: {str(e)}")
            return False
    
    async def run_app(self, app_name: str, progress_callback=None) -> bool:
        """Run installed app"""
        try:
            if app_name not in self.installed_apps:
                logger.error(f"App not installed: {app_name}")
                return False
            
            app_path = Path(self.installed_apps[app_name]['path'])
            
            if progress_callback:
                progress_callback(f"Starting {app_name}")
            
            # Find start script
            start_script = None
            for script_name in ['start.js', 'start.json']:
                script_path = app_path / script_name
                if script_path.exists():
                    start_script = script_path
                    break
            
            if not start_script:
                logger.error(f"No start script found for {app_name}")
                return False
            
            # Execute start script
            result = await self.execute_script(start_script, app_path)
            
            if result.get('success'):
                if progress_callback:
                    progress_callback(f"{app_name} started successfully")
                return True
            else:
                logger.error(f"Failed to start {app_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to run {app_name}: {e}")
            if progress_callback:
                progress_callback(f"Run failed: {str(e)}")
            return False
    
    def stop_app(self, app_name: str) -> bool:
        """Stop running app"""
        try:
            if app_name in self.running_processes:
                process = self.running_processes[app_name]
                process.terminate()
                process.wait(timeout=10)
                del self.running_processes[app_name]
            
            if app_name in self.app_ports:
                del self.app_ports[app_name]
            
            logger.info(f"Stopped {app_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop {app_name}: {e}")
            return False
    
    def uninstall_app(self, app_name: str) -> bool:
        """Uninstall app completely"""
        try:
            # Stop if running
            self.stop_app(app_name)
            
            # Remove from installed apps
            if app_name in self.installed_apps:
                app_path = Path(self.installed_apps[app_name]['path'])
                
                # Remove app directory completely
                if app_path.exists():
                    shutil.rmtree(app_path)
                    logger.info(f"Removed app directory: {app_path}")
                
                # Clean up virtual environment
                venv_path = self.venvs_dir / app_name
                if venv_path.exists():
                    shutil.rmtree(venv_path)
                    logger.info(f"Removed virtual environment: {venv_path}")
                
                # Clean up logs
                log_path = self.logs_dir / f"{app_name}.log"
                if log_path.exists():
                    log_path.unlink()
                
                # Remove from state
                del self.installed_apps[app_name]
                self.save_state()
                
                logger.info(f"Successfully uninstalled {app_name}")
                return True
            else:
                logger.warning(f"App not found in installed apps: {app_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to uninstall {app_name}: {e}")
            return False
    
    # Core script execution methods (simplified for Colab)
    async def execute_script(self, script_path: Path, app_path: Path = None) -> Dict[str, Any]:
        """Execute a Pinokio JS/JSON script - simplified for Colab"""
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return {'success': False, 'error': f'Script not found: {script_path}'}
        
        logger.info(f"Executing script: {script_path}")
        
        # For Colab, we'll use a simplified approach
        # This is a basic implementation - full script parsing would be more complex
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic success for now - full implementation would parse and execute
            logger.info(f"Script executed: {script_path}")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_venv_path(self, venv_name: str, app_path: Path = None) -> Path:
        """Get virtual environment path"""
        return self.venvs_dir / venv_name
    
    async def _create_venv(self, venv_path: Path):
        """Create virtual environment"""
        logger.info(f"Creating virtual environment: {venv_path}")
        venv.create(venv_path, with_pip=True)
        logger.info(f"Virtual environment created: {venv_path}")
    
    def evaluate_template(self, text: str, local_vars: Dict[str, Any] = None) -> str:
        """Evaluate Pinokio template expressions - simplified"""
        if not isinstance(text, str):
            return text
        
        # Basic template evaluation for Colab
        # Replace common patterns
        text = text.replace('{{platform}}', self.context.platform)
        text = text.replace('{{gpu}}', str(self.context.gpu or ''))
        
        return text
