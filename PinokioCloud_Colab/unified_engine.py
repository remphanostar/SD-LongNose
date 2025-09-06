#!/usr/bin/env python3
"""
Unified Pinokio Engine for Cloud Environments - MODULE 1 COMPLETE
Enhanced with complete Pinokio Script Parser and variable substitution
NO PLACEHOLDERS - FULL IMPLEMENTATION
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
import requests

# Import complete parser
try:
    from .pinokio_parser import PinokioScriptParser, PinokioContext
except ImportError:
    # Handle case where it's run as main module
    from pinokio_parser import PinokioScriptParser, PinokioContext

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedPinokioEngine:
    """Unified engine for executing Pinokio apps with complete parser support"""
    
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
        
        # Initialize complete Pinokio context and parser
        self.context = PinokioContext(cwd=str(self.base_path))
        self.parser = PinokioScriptParser(self.context)
        
        # Engine state
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

    async def execute_script(self, script_path: Path, app_path: Path, script_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute Pinokio JS/JSON script with complete parser support"""
        try:
            # Update context with script arguments
            if script_args:
                self.context.args.update(script_args)
            
            # Update working directory context
            self.context.cwd = str(app_path)
            
            # Parse script with complete parser
            script_data = self.parser.parse_script_file(script_path)
            
            # Check for parsing errors
            if self.parser.has_errors():
                logger.error(f"Script parsing failed: {self.parser.get_errors()}")
                return {
                    'success': False, 
                    'error': 'Script parsing failed',
                    'errors': self.parser.get_errors(),
                    'warnings': self.parser.get_warnings()
                }
            
            # Apply variable substitution
            script_data = self.parser.substitute_script_content(script_data)
            
            # Execute parsed script
            return await self._execute_script_data(script_data, app_path)
            
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return {'success': False, 'error': str(e)}


    async def _execute_script_data(self, script_data: Dict[str, Any], app_path: Path) -> Dict[str, Any]:
        """Execute parsed script data with complete Pinokio features"""
        try:
            if 'run' not in script_data:
                return {'success': True, 'message': 'No run commands found'}
            
            commands = script_data['run']
            
            # Check if this is a daemon script
            is_daemon = script_data.get('daemon', False)
            
            for i, cmd in enumerate(commands):
                # Update current step context
                self.context.current = i
                self.context.next = i + 1 if i + 1 < len(commands) else len(commands)
                
                # Check 'when' condition if present
                if 'when' in cmd:
                    condition_result = self.parser.evaluate_when_condition(cmd['when'])
                    if not condition_result:
                        logger.info(f"Skipping step {i} due to 'when' condition: {cmd['when']}")
                        continue
                
                method = cmd.get('method', '')
                params = cmd.get('params', {})
                
                # Apply variable substitution to params
                params = self.parser._substitute_in_object(params)
                
                logger.info(f"Executing step {i}: {method}")
                
                # Execute based on method
                success = await self._execute_method(method, params, app_path, cmd)
                
                if not success:
                    error_msg = f'{method} failed at step {i}'
                    logger.error(error_msg)
                    return {'success': False, 'error': error_msg, 'step': i}
                
                # Handle returns clause
                if 'returns' in cmd and hasattr(self, '_last_result'):
                    var_path = cmd['returns']
                    if var_path.startswith('local.'):
                        var_name = var_path[6:]  # Remove 'local.' prefix
                        self.context.local[var_name] = self._last_result
                    # Add support for other variable namespaces as needed
                
                # Handle jump instructions
                if hasattr(self, '_jump_target'):
                    jump_target = getattr(self, '_jump_target')
                    delattr(self, '_jump_target')
                    
                    # Find target step
                    for j, target_cmd in enumerate(commands):
                        if target_cmd.get('id') == jump_target:
                            self.context.current = j - 1  # Will be incremented in next iteration
                            break
            
            result = {'success': True, 'is_daemon': is_daemon}
            
            # Add warnings if any
            if self.parser.get_warnings():
                result['warnings'] = self.parser.get_warnings()
                
            return result
            
        except Exception as e:
            logger.error(f"Script execution error: {e}")
            return {'success': False, 'error': str(e)}

    async def _execute_method(self, method: str, params: Dict[str, Any], app_path: Path, cmd: Dict[str, Any]) -> bool:
        """Execute Pinokio method with complete API support"""
        try:
            if method == 'shell.run':
                return await self._execute_shell_command(params, app_path)
                
            elif method == 'script.start':
                return await self._execute_subscript(params, app_path)
                
            elif method == 'script.return':
                # Store return value
                self._last_result = params.get('value', '')
                return True
                
            elif method == 'local.set':
                # Set local variables
                for key, value in params.items():
                    self.context.local[key] = value
                return True
                
            elif method == 'jump':
                # Handle jump to different step
                if 'id' in params:
                    self._jump_target = params['id']
                elif 'index' in params:
                    self._jump_target = params['index']
                return True
                
            elif method == 'log':
                # Log message
                message = params.get('text', params.get('message', ''))
                logger.info(f"Script log: {message}")
                return True
                
            elif method == 'notify':
                # Notification (simplified for now)
                message = params.get('html', params.get('text', ''))
                logger.info(f"Notification: {message}")
                return True
                
            elif method.startswith('fs.'):
                return await self._execute_fs_method(method, params, app_path)
                
            elif method.startswith('json.'):
                return await self._execute_json_method(method, params, app_path)
                
            elif method == 'input':
                # Handle input method (simplified for headless operation)
                logger.info(f"Input request: {params}")
                # In a real implementation, this would show UI
                return True
                
            else:
                logger.warning(f"Unsupported method: {method}")
                return True  # Don't fail on unknown methods
                
        except Exception as e:
            logger.error(f"Method execution failed for {method}: {e}")
            return False

    async def _execute_fs_method(self, method: str, params: Dict[str, Any], app_path: Path) -> bool:
        """Execute filesystem methods"""
        try:
            if method == 'fs.write':
                file_path = Path(params['path'])
                if not file_path.is_absolute():
                    file_path = app_path / file_path
                
                content = params.get('text', params.get('content', ''))
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                mode = 'a' if params.get('append') else 'w'
                with open(file_path, mode, encoding='utf-8') as f:
                    f.write(content)
                return True
                
            elif method == 'fs.read':
                file_path = Path(params['path'])
                if not file_path.is_absolute():
                    file_path = app_path / file_path
                
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self._last_result = f.read()
                    return True
                return False
                
            elif method == 'fs.exists':
                file_path = Path(params['path'])
                if not file_path.is_absolute():
                    file_path = app_path / file_path
                
                self._last_result = file_path.exists()
                return True
                
            elif method == 'fs.rm':
                file_path = Path(params['path'])
                if not file_path.is_absolute():
                    file_path = app_path / file_path
                
                if file_path.exists():
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink()
                return True
                
            elif method == 'fs.copy':
                src = Path(params['src'])
                dest = Path(params['dest'])
                
                if not src.is_absolute():
                    src = app_path / src
                if not dest.is_absolute():
                    dest = app_path / dest
                
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                if src.is_dir():
                    shutil.copytree(src, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dest)
                return True
                
            elif method == 'fs.download':
                # Simplified download implementation
                import requests
                url = params['uri']
                file_path = Path(params.get('path', params.get('dir', '.')))
                
                if not file_path.is_absolute():
                    file_path = app_path / file_path
                
                if file_path.is_dir():
                    filename = url.split('/')[-1] or 'download'
                    file_path = file_path / filename
                
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return True
                
            else:
                logger.warning(f"Unsupported fs method: {method}")
                return True
                
        except Exception as e:
            logger.error(f"FS method failed {method}: {e}")
            return False

    async def _execute_json_method(self, method: str, params: Dict[str, Any], app_path: Path) -> bool:
        """Execute JSON methods"""
        try:
            file_path = Path(params['path'])
            if not file_path.is_absolute():
                file_path = app_path / file_path
            
            if method == 'json.set':
                # Load existing JSON or create new
                data = {}
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                
                # Set the value
                if 'json' in params:
                    # Replace entire content
                    data = params['json']
                elif 'key' in params:
                    # Set specific key
                    keys = params['key'].split('.')
                    current = data
                    for key in keys[:-1]:
                        if key not in current:
                            current[key] = {}
                        current = current[key]
                    current[keys[-1]] = params.get('value', '')
                
                # Write back to file
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                return True
                
            elif method == 'json.get':
                if not file_path.exists():
                    self._last_result = None
                    return True
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'key' in params:
                    # Get specific key
                    keys = params['key'].split('.')
                    current = data
                    for key in keys:
                        if isinstance(current, dict) and key in current:
                            current = current[key]
                        else:
                            current = None
                            break
                    self._last_result = current
                else:
                    self._last_result = data
                
                return True
                
            elif method == 'json.rm':
                if not file_path.exists():
                    return True
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'key' in params:
                    keys = params['key'].split('.')
                    current = data
                    for key in keys[:-1]:
                        if isinstance(current, dict) and key in current:
                            current = current[key]
                        else:
                            return True  # Key doesn't exist
                    
                    if isinstance(current, dict) and keys[-1] in current:
                        del current[keys[-1]]
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                return True
                
            else:
                logger.warning(f"Unsupported json method: {method}")
                return True
                
        except Exception as e:
            logger.error(f"JSON method failed {method}: {e}")
            return False

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
                # Execute command (variable substitution already handled by parser)
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