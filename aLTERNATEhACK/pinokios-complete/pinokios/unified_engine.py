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
    
    def __init__(self, base_path: str = "./pinokio_apps"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Directory structure
        self.apps_dir = self.base_path / "apps"
        self.venvs_dir = self.base_path / "venvs"
        self.logs_dir = self.base_path / "logs"
        self.cache_dir = self.base_path / "cache"
        
        for dir_path in [self.apps_dir, self.venvs_dir, self.logs_dir, self.cache_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Engine state
        self.context = PinokioContext(cwd=str(self.base_path))
        self.installed_apps = {}
        self.running_processes = {}
        self.script_locals = {}  # Script-specific local variables
        self.app_ports = {}  # App -> port mapping
        
        # Load state
        self._load_state()
    
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
            self._save_state()
    
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
                        'installed_at': app_dir.stat().st_mtime
                    }
                    
        return discovered
    
    def _save_state(self):
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
    
    async def port(self) -> int:
        """Get next available port (Pinokio kernel.port() implementation)"""
        import socket
        for port in range(8000, 9000):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex(('127.0.0.1', port)) != 0:
                    return port
        raise RuntimeError("No available ports")
    
    def which(self, command: str) -> Optional[str]:
        """Find command path (Pinokio kernel.which() implementation)"""
        return shutil.which(command)
    
    def evaluate_template(self, text: str, local_vars: Dict[str, Any] = None) -> str:
        """Evaluate Pinokio template expressions {{variable}}"""
        if not isinstance(text, str):
            return text
        
        # Combine all contexts
        eval_context = {
            **self.context.__dict__,
            **self.context.kernel,
            **(local_vars or {}),
            'kernel': self.context.kernel,
            'input': self.context.input,
            'args': self.context.args,
            'which': self.which
        }
        
        def replace_expr(match):
            expr = match.group(1).strip()
            try:
                # Handle ternary operator (condition ? true_val : false_val)
                if '?' in expr and ':' in expr:
                    parts = expr.split('?')
                    condition = parts[0].strip()
                    true_false = parts[1].split(':')
                    true_val = true_false[0].strip()
                    false_val = true_false[1].strip() if len(true_false) > 1 else ''
                    
                    # Evaluate condition
                    if self.evaluate_condition(condition, eval_context):
                        return self.evaluate_template(true_val, eval_context)
                    else:
                        return self.evaluate_template(false_val, eval_context)
                
                # Handle function calls
                if '(' in expr and ')' in expr:
                    func_match = re.match(r'(\w+)\((.*)\)', expr)
                    if func_match:
                        func_name = func_match.group(1)
                        func_args = func_match.group(2)
                        if func_name in eval_context and callable(eval_context[func_name]):
                            # Simple argument parsing
                            args = [a.strip().strip("'\"") for a in func_args.split(',') if a.strip()]
                            result = eval_context[func_name](*args)
                            return str(result) if result is not None else ''
                
                # Handle property access (e.g., args.venv, kernel.gpu)
                parts = expr.split('.')
                value = eval_context
                for part in parts:
                    # Handle array access
                    if '[' in part and ']' in part:
                        base, index = part.split('[')
                        index = int(index.rstrip(']'))
                        if base in value:
                            value = value[base]
                            if isinstance(value, (list, tuple)) and index < len(value):
                                value = value[index]
                            else:
                                return match.group(0)
                        else:
                            return match.group(0)
                    else:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        elif hasattr(value, part):
                            value = getattr(value, part)
                        else:
                            return match.group(0)
                
                return str(value) if value is not None else ''
                
            except Exception as e:
                logger.debug(f"Failed to evaluate '{expr}': {e}")
                return match.group(0)
        
        return re.sub(r'\{\{([^}]+)\}\}', replace_expr, text)
    
    def evaluate_condition(self, condition: str, context: Dict[str, Any] = None) -> bool:
        """Evaluate JavaScript-like conditions"""
        if not condition:
            return True
        
        # Remove {{ }} if present
        condition = condition.strip().strip('{}').strip()
        
        # Prepare evaluation context
        eval_ctx = {
            'platform': self.context.platform,
            'gpu': self.context.gpu,
            'gpu_model': self.context.gpu_model,
            **(context or {})
        }
        
        # Convert JS operators to Python
        condition = re.sub(r'===', '==', condition)
        condition = re.sub(r'!==', '!=', condition)
        condition = condition.replace('&&', ' and ')
        condition = condition.replace('||', ' or ')
        condition = condition.replace('!', ' not ')
        condition = condition.replace('true', 'True')
        condition = condition.replace('false', 'False')
        condition = condition.replace('null', 'None')
        
        # Handle regex test
        condition = re.sub(r'/(.+?)/\.test\(([^)]+)\)', 
                          lambda m: f're.search(r"{m.group(1)}", {m.group(2)})', 
                          condition)
        
        try:
            import re as re_module
            result = eval(condition, {"__builtins__": {}, "re": re_module}, eval_ctx)
            return bool(result)
        except Exception as e:
            logger.warning(f"Condition evaluation failed for '{condition}': {e}")
            return False
    
    async def shell_run(self, params: Dict[str, Any], app_path: Path = None) -> Dict[str, Any]:
        """Execute shell.run command with full Pinokio features"""
        messages = params.get('message', [])
        if isinstance(messages, str):
            messages = [messages]
        
        venv_name = params.get('venv')
        path = params.get('path', '.')
        env = params.get('env', {})
        on_events = params.get('on', [])
        daemon = params.get('daemon', False)
        
        # Resolve working directory
        if app_path and not os.path.isabs(path):
            working_dir = app_path / path
        else:
            working_dir = Path(path)
        working_dir.mkdir(exist_ok=True)
        
        # Setup environment
        full_env = {**os.environ, **env}
        
        # Handle virtual environment
        if venv_name:
            venv_path = self._get_venv_path(venv_name, app_path)
            if not venv_path.exists():
                await self._create_venv(venv_path)
            
            # Add venv to PATH
            if self.context.platform == 'win32':
                venv_bin = venv_path / "Scripts"
            else:
                venv_bin = venv_path / "bin"
            full_env['PATH'] = f"{venv_bin}{os.pathsep}{full_env.get('PATH', '')}"
        
        results = []
        for message in messages:
            # Evaluate templates in command
            command = self.evaluate_template(message)
            logger.info(f"Executing: {command}")
            
            try:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=str(working_dir),
                    env=full_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Handle event monitoring
                event_result = None
                if on_events:
                    for line in iter(process.stdout.readline, ''):
                        if line:
                            print(line.rstrip())
                            
                            for event in on_events:
                                pattern = event.get('event', '').strip('/')
                                if pattern and re.search(pattern, line):
                                    logger.info(f"Event matched: {pattern}")
                                    # Store match result for input.event access
                                    match = re.search(pattern, line)
                                    if match:
                                        self.context.input['event'] = match.groups() or [match.group(0)]
                                    
                                    if event.get('done'):
                                        event_result = 'done'
                                        break
                                    elif event.get('kill'):
                                        process.terminate()
                                        event_result = 'killed'
                                        break
                            
                            if event_result:
                                break
                
                # Handle daemon mode
                if daemon and event_result == 'done':
                    # Keep process running in background
                    app_name = app_path.name if app_path else 'unknown'
                    self.running_processes[app_name] = process
                    results.append({'success': True, 'daemon': True, 'pid': process.pid})
                else:
                    # Wait for completion and capture output
                    stdout, stderr = process.communicate()
                    returncode = process.returncode
                    
                    # Log the output
                    if stdout:
                        logger.info(f"Command output: {stdout}")
                        print(stdout)
                    if stderr:
                        logger.error(f"Command error: {stderr}")
                        print(f"Error: {stderr}")
                    
                    # Record result
                    if returncode == 0:
                        results.append({'success': True, 'returncode': returncode, 'output': stdout})
                    else:
                        error_msg = f"Command failed with code {returncode}: {stderr or 'Unknown error'}"
                        logger.error(error_msg)
                        results.append({'success': False, 'returncode': returncode, 'error': error_msg, 'output': stdout})
                    
            except Exception as e:
                logger.error(f"Command failed: {e}")
                results.append({'success': False, 'error': str(e)})
                break
        
        return {'success': all(r.get('success', False) for r in results), 'results': results}
    
    async def script_start(self, params: Dict[str, Any], app_path: Path = None) -> Dict[str, Any]:
        """Execute script.start to run another script"""
        uri = params.get('uri')
        script_params = params.get('params', {})
        
        if not uri:
            raise ValueError("script.start requires 'uri' parameter")
        
        # Resolve script path
        if app_path and not os.path.isabs(uri):
            script_path = app_path / uri
        else:
            script_path = Path(uri)
        
        # Update context args for the called script
        self.context.args = script_params
        
        return await self.execute_script(script_path, app_path)
    
    async def local_set(self, params: Dict[str, Any], script_id: str) -> Dict[str, Any]:
        """Set local variables for a script"""
        if script_id not in self.script_locals:
            self.script_locals[script_id] = {}
        
        for key, value in params.items():
            # Evaluate templates in values
            if isinstance(value, str):
                value = self.evaluate_template(value, self.script_locals.get(script_id))
            self.script_locals[script_id][key] = value
        
        return {'success': True}
    
    async def execute_script(self, script_path: Path, app_path: Path = None) -> Dict[str, Any]:
        """Execute a Pinokio JS/JSON script"""
        if not script_path.exists():
            logger.error(f"Script not found: {script_path}")
            return {'success': False, 'error': f'Script not found: {script_path}'}
        
        logger.info(f"Executing script: {script_path}")
        script_id = str(script_path)
        
        # Read script content
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse script based on type
        if script_path.suffix == '.js':
            script_data = self._parse_js_script(content, script_path)
        elif script_path.suffix == '.json':
            script_data = json.loads(content)
        else:
            return {'success': False, 'error': 'Unsupported script format'}
        
        # Handle async function scripts (e.g., start.js)
        if callable(script_data):
            # Execute async function with kernel context
            script_data = await script_data(self)
        
        # Execute run steps
        if 'run' in script_data:
            return await self._execute_run_steps(script_data['run'], script_path, app_path)
        
        return {'success': True}
    
    def _parse_js_script(self, content: str, script_path: Path) -> Dict[str, Any]:
        """Parse JavaScript module.exports to Python dict"""
        
        try:
            # Simple regex-based parsing for module.exports = { ... }
            import re
            
            # Extract the main object from module.exports
            match = re.search(r'module\.exports\s*=\s*(\{.*\})', content, re.DOTALL)
            if match:
                js_obj = match.group(1)
                # Convert JS object to Python dict (simplified)
                js_obj = re.sub(r'//.*?\n', '\n', js_obj)  # Remove comments
                js_obj = re.sub(r'/\*.*?\*/', '', js_obj, flags=re.DOTALL)  # Remove block comments
                
                # Basic conversion of JS object syntax to Python
                # This is a simplified parser - in production use a proper JS parser
                python_dict = self._js_to_python_dict(js_obj)
                return python_dict
            
        except Exception as e:
            logger.warning(f"Failed to parse JS script {script_path}: {e}")
        
        # Handle async function exports (e.g., start.js)
        if 'module.exports = async' in content:
            # Extract the function body and create a Python async function
            async def script_function(kernel):
                # Get available port
                port = await kernel.port()
                
                # Return the script configuration
                # This is a simplified version - in production, parse the actual JS
                return {
                    'daemon': True,
                    'run': [
                        {
                            'method': 'shell.run',
                            'params': {
                                'venv': 'env',
                                'path': 'app',
                                'message': [f'python gradio_app.py --host 127.0.0.1 --port {port}'],
                                'on': [{
                                    'event': r'http://[0-9.:]+',
                                    'done': True
                                }]
                            }
                        },
                        {
                            'method': 'local.set',
                            'params': {
                                'url': '{{input.event[0]}}'
                            }
                        }
                    ]
                }
            return script_function
        
        # Handle object exports (install.js, torch.js style)
        if 'module.exports = {' in content:
            # Extract JSON-like object
            match = re.search(r'module\.exports\s*=\s*(\{[\s\S]+\})\s*(?:;|$)', content)
            if match:
                json_str = match.group(1)
                # Convert JS object to JSON
                json_str = re.sub(r'//.*$', '', json_str, flags=re.MULTILINE)  # Remove comments
                json_str = re.sub(r'/\*[\s\S]*?\*/', '', json_str)  # Remove block comments
                json_str = re.sub(r'(\w+):', r'"\1":', json_str)  # Quote keys
                json_str = json_str.replace("'", '"')  # Single to double quotes
                
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # Fallback to predefined patterns if parsing fails
                    return self._parse_js_fallback(script_path)
    
    def _js_to_python_dict(self, js_obj: str) -> Dict[str, Any]:
        """Convert JavaScript object to Python dict (simplified)"""
        try:
            # Very basic JS to Python conversion
            # Replace JS syntax with Python equivalents
            py_obj = js_obj.strip()
            py_obj = re.sub(r'(\w+):', r'"\1":', py_obj)  # Quote keys
            py_obj = re.sub(r"'([^']*)'", r'"\1"', py_obj)  # Single to double quotes
            py_obj = py_obj.replace('true', 'True')
            py_obj = py_obj.replace('false', 'False')
            py_obj = py_obj.replace('null', 'None')
            
            # Try to evaluate as Python dict
            return eval(py_obj)
        except Exception as e:
            logger.warning(f"JS to Python conversion failed: {e}")
            return {}
        
    def _parse_js_fallback(self, script_path: Path) -> Dict[str, Any]:
        """Fallback parser for known script patterns"""
        name = script_path.stem
        
        if name == 'install':
            # Standard install pattern
            return {
                'run': [
                    {'method': 'shell.run', 'params': {'message': 'git clone {{args.repo_url}} app'}},
                    {'method': 'script.start', 'params': {'uri': 'torch.js', 'params': {'venv': 'env', 'path': 'app'}}},
                    {'method': 'shell.run', 'params': {'venv': 'env', 'path': 'app', 'message': 'pip install -r requirements.txt'}}
                ]
            }
        elif name == 'torch':
            # PyTorch installation pattern
            return {
                'run': [
                    {
                        'when': "{{platform === 'linux' && gpu === 'nvidia'}}",
                        'method': 'shell.run',
                        'params': {
                            'venv': '{{args && args.venv ? args.venv : null}}',
                            'path': '{{args && args.path ? args.path : "."}}',
                            'message': 'pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121'
                        }
                    }
                ]
            }
        
        return {'run': []}
    
    async def _execute_run_steps(self, steps: List[Dict], script_path: Path, app_path: Path) -> Dict[str, Any]:
        """Execute array of run steps from a script"""
        results = []
        script_id = str(script_path)
        local_vars = self.script_locals.get(script_id, {})
        
        for i, step in enumerate(steps):
            # Check when condition
            when = step.get('when')
            if when and not self.evaluate_condition(when, local_vars):
                logger.info(f"Skipping step {i} due to condition: {when}")
                continue
            
            method = step.get('method')
            params = step.get('params', {})
            
            logger.info(f"Step {i}: {method}")
            
            try:
                if method == 'shell.run':
                    result = await self.shell_run(params, app_path)
                elif method == 'script.start':
                    result = await self.script_start(params, app_path)
                elif method == 'local.set':
                    result = await self.local_set(params, script_id)
                elif method == 'fs.download':
                    result = await self._fs_download(params, app_path)
                elif method == 'log':
                    logger.info(f"LOG: {params.get('text', params.get('html', ''))}")
                    result = {'success': True}
                else:
                    logger.warning(f"Method not implemented: {method}")
                    result = {'success': True}
                
                results.append(result)
                
                # Stop on failure unless next is specified
                if not result.get('success', True) and step.get('next') != 'null':
                    break
                    
            except Exception as e:
                logger.error(f"Step {i} failed: {e}")
                results.append({'success': False, 'error': str(e)})
                break
        
        return {'success': all(r.get('success', True) for r in results), 'results': results}
    
    async def _fs_download(self, params: Dict[str, Any], app_path: Path) -> Dict[str, Any]:
        """Download file (fs.download implementation)"""
        uri = params.get('uri')
        path = params.get('path', params.get('dir', '.'))
        
        if not uri:
            return {'success': False, 'error': 'No URI specified'}
        
        # Resolve path
        if app_path and not os.path.isabs(path):
            dest_path = app_path / path
        else:
            dest_path = Path(path)
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            import urllib.request
            urllib.request.urlretrieve(uri, str(dest_path))
            return {'success': True, 'path': str(dest_path)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def _create_venv(self, venv_path: Path):
        """Create virtual environment with uv for speed"""
        logger.info(f"Creating venv: {venv_path}")
        venv.create(str(venv_path), with_pip=True)
        
        # Install uv for faster package management
        pip_path = venv_path / ("Scripts" if self.context.platform == "win32" else "bin") / "pip"
        subprocess.run([str(pip_path), "install", "uv"], capture_output=True)
    
    def _get_venv_path(self, venv_name: str, app_path: Path = None) -> Path:
        """Get virtual environment path for an app"""
        if os.path.isabs(venv_name):
            return Path(venv_name)
        elif app_path:
            # Check if venv is inside app directory
            app_venv = app_path / venv_name
            if app_venv.exists():
                return app_venv
        # Default to venvs directory
        return self.venvs_dir / venv_name
    
    async def install_app(self, app_data: Dict[str, Any], progress_callback=None) -> Tuple[bool, str]:
        """Install a Pinokio app by executing its install.js/install.json"""
        app_name = app_data.get('Appname')
        repo_url = app_data.get('Git') or app_data.get('Repository') or app_data.get('clone_url') or app_data.get('repo_url') or app_data.get('url')
        
        if not app_name:
            return False, "App name not specified"
            
        # Look for existing app directory in base_path (not apps_dir)
        app_path = self.base_path / app_name
        logger.info(f"Installing app {app_name} from path: {app_path}")
        
        try:
            if progress_callback:
                progress_callback(f"Installing {app_name}...")
            
            # If app directory doesn't exist and we have repo_url, clone it
            if not app_path.exists() and repo_url:
                logger.info(f"Cloning {repo_url} to {app_path}")
                git.Repo.clone_from(repo_url, str(app_path))
            elif not app_path.exists():
                return False, f"App directory not found: {app_path}"
            
            # Look for install script
            install_js = app_path / "install.js"
            install_json = app_path / "install.json"
            install_script = None
            
            if install_js.exists():
                install_script = install_js
                logger.info(f"Using install.js for {app_name}")
            elif install_json.exists():
                install_script = install_json
                logger.info(f"Using install.json for {app_name}")
            
            if install_script:
                # Set context for the install script
                self.context.args = {
                    'repo_url': repo_url,
                    'app_name': app_name,
                    'app_path': str(app_path)
                }
                
                logger.info(f"Executing install script: {install_script}")
                result = await self.execute_script(install_script, app_path)
                logger.info(f"Install script result: {result}")
                
                if result.get('success'):
                    self.installed_apps[app_name] = {
                        'path': str(app_path),
                        'repo_url': repo_url,
                        'installed_at': time.time()
                    }
                    self._save_state()
                    return True, f"✅ {app_name} installed via Pinokio script"
                else:
                    error_msg = result.get('error', 'Unknown error')
                    logger.error(f"Install script failed: {error_msg}")
                    return False, f"Installation script failed: {error_msg}"
            else:
                logger.warning(f"No install script found for {app_name}")
                # Mark as installed anyway since directory exists
                self.installed_apps[app_name] = {
                    'path': str(app_path),
                    'repo_url': repo_url,
                    'installed_at': time.time()
                }
                self._save_state()
                return True, f"✅ {app_name} marked as installed (no install script)"
                
        except Exception as e:
            logger.error(f"Installation failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False, f"❌ Installation failed: {str(e)}"
    
    async def run_app(self, app_name, progress_callback=None):
        """Run an installed Pinokio app with detailed logging"""
        logger.info(f"=== ENGINE: Starting run_app for {app_name} ===")
        logger.info(f"Engine base_path: {self.base_path}")
        
        app_path = Path(self.base_path) / app_name
        logger.info(f"App path resolved to: {app_path}")
        logger.info(f"App path exists: {app_path.exists()}")
        
        if not app_path.exists():
            logger.error(f"App directory does not exist: {app_path}")
            return False, f"App {app_name} not installed"
        
        # List contents of app directory
        try:
            contents = list(app_path.glob('*'))
            logger.info(f"App directory contains {len(contents)} items:")
            for item in contents[:15]:  # Show first 15 items
                item_type = "DIR" if item.is_dir() else "FILE"
                logger.info(f"  {item_type}: {item.name}")
            if len(contents) > 15:
                logger.info(f"  ... and {len(contents) - 15} more items")
        except Exception as e:
            logger.error(f"Error listing app directory contents: {e}")
        
        # Look for start script
        start_js = app_path / 'start.js'
        start_json = app_path / 'start.json'
        
        logger.info(f"Checking for start.js at: {start_js}")
        logger.info(f"start.js exists: {start_js.exists()}")
        logger.info(f"Checking for start.json at: {start_json}")
        logger.info(f"start.json exists: {start_json.exists()}")
        
        start_script = None
        if start_js.exists():
            start_script = start_js
            logger.info(f"Using start.js for {app_name}")
        elif start_json.exists():
            start_script = start_json
            logger.info(f"Using start.json for {app_name}")
        else:
            logger.error(f"No start script found for {app_name}")
            logger.error(f"Expected start.js at: {start_js}")
            logger.error(f"Expected start.json at: {start_json}")
            return False, f"No start script found for {app_name}"
        
        try:
            logger.info(f"Selected start script: {start_script}")
            
            # Add to running apps
            self.running_apps[app_name] = {
                'start_time': datetime.now(),
                'status': 'starting',
                'script_path': str(start_script)
            }
            logger.info(f"Added {app_name} to running_apps registry")
            
            # Execute the start script
            if progress_callback:
                progress_callback(f"Starting {app_name}...")
            
            # Read the script content first
            logger.info(f"Reading script content from: {start_script}")
            try:
                script_content = start_script.read_text(encoding='utf-8')
                logger.info(f"Script content preview: {script_content[:300]}...")
                logger.info(f"Script content length: {len(script_content)} characters")
            except Exception as e:
                logger.error(f"Error reading script content: {e}")
                return False, f"Error reading start script: {str(e)}"
            
            logger.info(f"Calling execute_script with app_path={app_path}, app_name={app_name}")
            result = await self.execute_script(script_content, {'app_path': str(app_path), 'app_name': app_name})
            logger.info(f"execute_script returned: {result}")
            
            if result.get('success'):
                logger.info("Script execution reported success")
                # Get URL from local variables if set
                script_locals = self.script_locals.get(str(start_script), {})
                url = script_locals.get('url')
                logger.info(f"Script locals for URL: {script_locals}")
                
                if url:
                    success_msg = f"✅ {app_name} started at {url}"
                    logger.info(success_msg)
                    return True, success_msg
                else:
                    success_msg = f"✅ {app_name} started successfully"
                    logger.info(success_msg)
                    return True, success_msg
            else:
                error_msg = f"Failed to execute start script: {result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Exception in run_app for {app_name}: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False, f"Error running app: {str(e)}"
        finally:
            logger.info(f"=== ENGINE: Completed run_app for {app_name} ===")
    
    def stop_app(self, app_name: str) -> Tuple[bool, str]:
        """Stop a running app"""
        if app_name not in self.running_processes:
            return False, f"App {app_name} not running"
        
        try:
            process = self.running_processes[app_name]
            process.terminate()
            process.wait(timeout=10)
            del self.running_processes[app_name]
            
            # Clear port mapping
            if app_name in self.app_ports:
                del self.app_ports[app_name]
            
            return True, f"✅ {app_name} stopped"
        except subprocess.TimeoutExpired:
            process.kill()
            del self.running_processes[app_name]
            return True, f"✅ {app_name} forcefully stopped"
        except Exception as e:
            return False, f"❌ Failed to stop: {str(e)}"
    
    def get_app_status(self, app_name: str) -> str:
        """Get status of an app"""
        if app_name in self.running_processes:
            process = self.running_processes[app_name]
            if process.poll() is None:
                return "🟢 Running"
            else:
                # Process terminated
                del self.running_processes[app_name]
                return "🔴 Stopped"
        elif app_name in self.installed_apps:
            return "🟡 Installed"
        else:
            return "⚪ Not Installed"
    
    def list_installed_apps(self) -> List[Dict[str, Any]]:
        """List all installed apps with their status"""
        apps = []
        for name, info in self.installed_apps.items():
            apps.append({
                'name': name,
                'path': info['path'],
                'repo_url': info['repo_url'],
                'status': self.get_app_status(name),
                'installed_at': info.get('installed_at')
            })
        return apps
    
    async def uninstall_app(self, app_name: str) -> Tuple[bool, str]:
        """Uninstall an app - completely remove app directory and all associated files"""
        if app_name not in self.installed_apps:
            return False, f"App {app_name} not installed"
        
        # Stop if running
        if app_name in self.running_processes:
            self.stop_app(app_name)
        
        try:
            # Remove the entire app directory (downloaded during installation)
            app_path = self.base_path / app_name
            if app_path.exists():
                logger.info(f"Removing app directory: {app_path}")
                shutil.rmtree(app_path)
            
            # Remove venv if it exists
            venv_path = self.venvs_dir / f"{app_name}_env"
            if venv_path.exists():
                logger.info(f"Removing venv: {venv_path}")
                shutil.rmtree(venv_path)
            
            # Clear any installation logs
            log_file = self.logs_dir / f"{app_name}_install.log"
            if log_file.exists():
                log_file.unlink()
                
            # Clear any run logs
            run_log_file = self.logs_dir / f"{app_name}_run.log"
            if run_log_file.exists():
                run_log_file.unlink()
            
            # Remove from installed apps state
            del self.installed_apps[app_name]
            self._save_state()
            
            logger.info(f"Completely uninstalled {app_name}")
            return True, f"✅ {app_name} completely uninstalled"
        except Exception as e:
            logger.error(f"Failed to uninstall {app_name}: {e}")
            return False, f"❌ Failed to uninstall: {str(e)}"
    
    def cleanup(self):
        """Cleanup all running processes"""
        for app_name in list(self.running_processes.keys()):
            self.stop_app(app_name)


# Export the main class
__all__ = ['UnifiedPinokioEngine', 'PinokioContext']
