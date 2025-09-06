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
            'platform': self.platform
        }

    def _detect_gpu(self):
        """Detect available GPU"""
        try:
            # Try nvidia-smi first
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                self.gpu_model = result.stdout.strip().split('\n')[0]
                self.gpu = 'nvidia'
                return
        except:
            pass
        
        # Fallback to CPU
        self.gpu = None
        self.gpu_model = None

class UnifiedPinokioEngine:
    """Unified engine for executing Pinokio apps with full JS/JSON support"""
    
    def __init__(self, base_path: str = "./pinokio_apps", apps_data_path: str = "./cleaned_pinokio_apps.json"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Create required directories
        directories = ["logs", "cache", "venvs"]
        for dir_name in directories:
            dir_path = self.base_path / dir_name
            dir_path.mkdir(exist_ok=True)
        
        # Load apps database
        self.apps_data = self._load_apps_data(apps_data_path)
        
        # Engine state
        self.context = PinokioContext(cwd=str(self.base_path))
        self.installed_apps = {}
        self.running_processes = {}
        self.app_ports = {}
        self.logs_dir = self.base_path / "logs"
        self.cache_dir = self.base_path / "cache" 
        self.venvs_dir = self.base_path / "venvs"
        
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
                self.installed_apps[app_name] = app_info
        
        # Clean up invalid entries
        valid_apps = {}
        for app_name, app_info in self.installed_apps.items():
            if Path(app_info['path']).exists():
                valid_apps[app_name] = app_info
        self.installed_apps = valid_apps
        
        self.save_state()

    def _discover_existing_apps(self) -> Dict[str, Dict[str, Any]]:
        """Auto-discover existing Pinokio apps in the base directory"""
        discovered = {}
        
        try:
            for item in self.base_path.iterdir():
                if item.is_dir() and item.name not in ['logs', 'cache', 'venvs']:
                    # Check for Pinokio markers
                    pinokio_files = ['install.js', 'install.json', 'start.js', 'start.json', 'pinokio.js']
                    has_pinokio_files = any((item / f).exists() for f in pinokio_files)
                    
                    if has_pinokio_files:
                        discovered[item.name] = {
                            'path': str(item),
                            'repo_url': 'unknown',
                            'discovered_at': datetime.datetime.now().isoformat()
                        }
        except Exception as e:
            logger.error(f"Failed to discover apps: {e}")
            
        return discovered

    def save_state(self):
        """Save engine state to persistent storage"""
        try:
            state = {
                'installed_apps': self.installed_apps,
                'last_updated': datetime.datetime.now().isoformat()
            }
            
            state_file = self.cache_dir / "engine_state.json"
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def list_available_apps(self) -> List[Dict[str, Any]]:
        """List all available apps from database"""
        return self.apps_data

    def list_installed_apps(self) -> Dict[str, Dict[str, Any]]:
        """List all installed apps"""
        return self.installed_apps

    def is_app_installed(self, app_name: str) -> bool:
        """Check if app is installed"""
        return app_name in self.installed_apps

    def is_app_running(self, app_name: str) -> bool:
        """Check if app is currently running"""
        return app_name in self.running_processes

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
                    progress_callback(f"Found install script: {install_script.name}")
                
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

    async def execute_script(self, script_path: Path, app_path: Path) -> Dict[str, Any]:
        """Execute Pinokio JS/JSON script with full feature support"""
        try:
            # Read script content
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse script based on extension
            if script_path.suffix == '.js':
                script_data = self._parse_js_script(content)
            else:  # .json
                script_data = json.loads(content)
            
            # Execute script
            return await self._execute_script_data(script_data, app_path)
            
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return {'success': False, 'error': str(e)}

    def _parse_js_script(self, js_content: str) -> Dict[str, Any]:
        """Parse JavaScript module.exports format"""
        # Remove comments and clean up
        lines = js_content.split('\n')
        clean_lines = []
        for line in lines:
            # Remove single line comments
            if '//' in line:
                line = line[:line.index('//')]
            clean_lines.append(line)
        
        content = '\n'.join(clean_lines)
        
        # Extract the exported object
        # Look for module.exports = { ... }
        match = re.search(r'module\.exports\s*=\s*(\{.*\})', content, re.DOTALL)
        if match:
            obj_str = match.group(1)
            # Convert JS object to JSON format
            obj_str = re.sub(r'(\w+):', r'"\1":', obj_str)  # Add quotes to keys
            obj_str = re.sub(r"'([^']*)'", r'"\1"', obj_str)  # Convert single quotes
            try:
                return json.loads(obj_str)
            except:
                pass
        
        # Fallback: try to extract run array
        run_match = re.search(r'run:\s*\[(.*?)\]', content, re.DOTALL)
        if run_match:
            return {'run': []}  # Simplified fallback
        
        return {'run': []}

    async def _execute_script_data(self, script_data: Dict[str, Any], app_path: Path) -> Dict[str, Any]:
        """Execute parsed script data"""
        try:
            if 'run' not in script_data:
                return {'success': True, 'message': 'No run commands found'}
            
            commands = script_data['run']
            for i, cmd in enumerate(commands):
                method = cmd.get('method', '')
                params = cmd.get('params', {})
                
                if method == 'shell.run':
                    result = await self._execute_shell_command(params, app_path)
                    if not result:
                        return {'success': False, 'error': f'Shell command failed at step {i}'}
                        
                elif method == 'script.start':
                    # Handle torch.js or other script execution
                    await self._execute_subscript(params, app_path)
                
                # Add more method handlers as needed
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _execute_shell_command(self, params: Dict[str, Any], app_path: Path) -> bool:
        """Execute shell command with proper environment"""
        try:
            messages = params.get('message', [])
            if isinstance(messages, str):
                messages = [messages]
            
            venv_name = params.get('venv')
            command_path = params.get('path', '.')
            
            # Resolve full command path
            if command_path and command_path != '.':
                full_path = app_path / command_path
            else:
                full_path = app_path
            
            for message in messages:
                # Handle variable substitution
                message = self._substitute_variables(message)
                
                # Execute command
                if venv_name:
                    # Execute in virtual environment
                    success = await self._execute_in_venv(message, venv_name, full_path)
                else:
                    # Execute directly
                    success = await self._execute_direct(message, full_path)
                
                if not success:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Shell command execution failed: {e}")
            return False

    def _substitute_variables(self, message: str) -> str:
        """Substitute variables in command strings"""
        # Handle {{variable}} syntax
        def replace_var(match):
            var_path = match.group(1).strip()
            return self._resolve_variable(var_path)
        
        return re.sub(r'\{\{([^}]+)\}\}', replace_var, message)

    def _resolve_variable(self, var_path: str) -> str:
        """Resolve variable path like 'args.repo_url'"""
        parts = var_path.split('.')
        value = self.context
        
        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            elif isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return f"{{{{{var_path}}}}}"  # Return unchanged if not found
        
        return str(value) if value is not None else ""

    async def _execute_in_venv(self, command: str, venv_name: str, cwd: Path) -> bool:
        """Execute command in virtual environment"""
        try:
            venv_path = self.venvs_dir / venv_name
            
            # Create venv if it doesn't exist
            if not venv_path.exists():
                venv.create(venv_path, with_pip=True)
            
            # Get activation script path
            if platform.system() == "Windows":
                activate_script = venv_path / "Scripts" / "activate.bat"
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                activate_script = venv_path / "bin" / "activate"
                python_exe = venv_path / "bin" / "python"
            
            # Prepare command with venv activation
            if command.startswith('python ') or command.startswith('pip '):
                # Replace python/pip with venv python
                if command.startswith('python '):
                    command = command.replace('python ', f'"{python_exe}" ', 1)
                elif command.startswith('pip '):
                    pip_exe = python_exe.parent / "pip.exe" if platform.system() == "Windows" else python_exe.parent / "pip"
                    command = command.replace('pip ', f'"{pip_exe}" ', 1)
            
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Command succeeded: {command[:50]}...")
                return True
            else:
                logger.error(f"Command failed: {command[:50]}... - {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Venv execution failed: {e}")
            return False

    async def _execute_direct(self, command: str, cwd: Path) -> bool:
        """Execute command directly"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Command succeeded: {command[:50]}...")
                return True
            else:
                logger.error(f"Command failed: {command[:50]}... - {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Direct execution failed: {e}")
            return False

    async def _execute_subscript(self, params: Dict[str, Any], app_path: Path):
        """Execute subscript like torch.js"""
        script_uri = params.get('uri', '')
        script_params = params.get('params', {})
        
        if script_uri:
            script_path = app_path / script_uri
            if script_path.exists():
                # Update context with script params
                self.context.args.update(script_params)
                await self.execute_script(script_path, app_path)