#!/usr/bin/env python3
"""
JavaScript to Python Converter for Pinokio Scripts
Converts Pinokio JS install/start scripts to executable Python equivalents
"""

import re
import json
import ast
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class JSPinokioConverter:
    """Converts Pinokio JavaScript scripts to Python equivalents"""
    
    def __init__(self):
        self.method_mappings = {
            'shell.run': 'await emulator.shell_run',
            'script.start': 'await emulator.script_start', 
            'fs.download': 'await emulator.fs_download',
            'fs.write': 'await emulator.fs_write',
            'fs.read': 'await emulator.fs_read',
            'local.set': 'await emulator.local_set',
            'log': 'logger.info',
        }
    
    def convert_js_script(self, js_content: str) -> Dict[str, Any]:
        """Convert JS Pinokio script to Python-executable format"""
        
        # Handle module.exports patterns
        if 'module.exports = {' in js_content:
            return self._parse_object_export(js_content)
        elif 'module.exports = async' in js_content:
            return self._parse_function_export(js_content)
        else:
            raise ValueError("Unsupported JS export pattern")
    
    def _parse_object_export(self, js_content: str) -> Dict[str, Any]:
        """Parse module.exports = { ... } pattern"""
        
        # Extract the exported object
        start_idx = js_content.find('module.exports = {')
        if start_idx == -1:
            raise ValueError("Could not find module.exports object")
        
        # Find matching closing brace
        brace_count = 0
        content_start = js_content.find('{', start_idx) + 1
        
        for i, char in enumerate(js_content[content_start:], content_start):
            if char == '{':
                brace_count += 1
            elif char == '}':
                if brace_count == 0:
                    object_content = js_content[content_start:i]
                    break
                brace_count -= 1
        else:
            raise ValueError("Could not find matching closing brace")
        
        # Parse the object content
        return self._parse_js_object(object_content)
    
    def _parse_function_export(self, js_content: str) -> Dict[str, Any]:
        """Parse module.exports = async (kernel) => { ... } pattern"""
        
        # Extract function body
        func_start = js_content.find('=>')
        if func_start == -1:
            raise ValueError("Could not find arrow function")
        
        # Find the return statement with the object
        return_match = re.search(r'return\s*({.*?})\s*}', js_content, re.DOTALL)
        if not return_match:
            raise ValueError("Could not find return statement")
        
        object_content = return_match.group(1)
        
        # Parse the returned object
        return self._parse_js_object(object_content)
    
    def _parse_js_object(self, object_str: str) -> Dict[str, Any]:
        """Parse JavaScript object syntax to Python dict"""
        
        # Clean up the object string
        object_str = object_str.strip()
        if object_str.startswith('{'):
            object_str = object_str[1:]
        if object_str.endswith('}'):
            object_str = object_str[:-1]
        
        # Convert JS syntax to valid JSON
        # Handle run arrays
        run_match = re.search(r'run:\s*\[(.*?)\]', object_str, re.DOTALL)
        if run_match:
            run_content = run_match.group(1)
            run_steps = self._parse_run_array(run_content)
            
            return {
                'run': run_steps,
                'daemon': self._extract_boolean_field(object_str, 'daemon'),
                'version': self._extract_string_field(object_str, 'version')
            }
        
        return {}
    
    def _parse_run_array(self, run_content: str) -> List[Dict[str, Any]]:
        """Parse the run array from JS to Python format"""
        steps = []
        
        # Split by objects (simplified parsing)
        # In production, you'd want a proper JS parser
        step_pattern = r'\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
        
        for match in re.finditer(step_pattern, run_content):
            step_content = match.group(1)
            step = self._parse_step_object(step_content)
            if step:
                steps.append(step)
        
        return steps
    
    def _parse_step_object(self, step_content: str) -> Optional[Dict[str, Any]]:
        """Parse individual step object"""
        step = {}
        
        # Extract when condition
        when_match = re.search(r'when:\s*["\']([^"\']*)["\']', step_content)
        if when_match:
            step['when'] = when_match.group(1)
        
        # Extract method
        method_match = re.search(r'method:\s*["\']([^"\']*)["\']', step_content)
        if method_match:
            step['method'] = method_match.group(1)
        
        # Extract params object
        params_match = re.search(r'params:\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', step_content)
        if params_match:
            params_content = params_match.group(1)
            step['params'] = self._parse_params_object(params_content)
        
        return step if step else None
    
    def _parse_params_object(self, params_content: str) -> Dict[str, Any]:
        """Parse params object"""
        params = {}
        
        # Extract simple string fields
        for field in ['venv', 'path', 'uri']:
            pattern = rf'{field}:\s*["\']([^"\']*)["\']'
            match = re.search(pattern, params_content)
            if match:
                params[field] = match.group(1)
        
        # Extract message array
        message_match = re.search(r'message:\s*\[(.*?)\]', params_content, re.DOTALL)
        if message_match:
            message_content = message_match.group(1)
            messages = []
            for msg_match in re.finditer(r'["\']([^"\']*)["\']', message_content):
                messages.append(msg_match.group(1))
            params['message'] = messages
        else:
            # Single message
            message_match = re.search(r'message:\s*["\']([^"\']*)["\']', params_content)
            if message_match:
                params['message'] = message_match.group(1)
        
        # Extract env object
        env_match = re.search(r'env:\s*\{([^{}]*)\}', params_content)
        if env_match:
            env_content = env_match.group(1)
            env_vars = {}
            for env_var_match in re.finditer(r'(\w+):\s*["\']?([^"\']*)["\']?', env_content):
                key, value = env_var_match.groups()
                env_vars[key] = value
            params['env'] = env_vars
        
        return params
    
    def _extract_string_field(self, content: str, field: str) -> Optional[str]:
        """Extract string field from JS object"""
        pattern = rf'{field}:\s*["\']([^"\']*)["\']'
        match = re.search(pattern, content)
        return match.group(1) if match else None
    
    def _extract_boolean_field(self, content: str, field: str) -> Optional[bool]:
        """Extract boolean field from JS object"""
        pattern = rf'{field}:\s*(true|false)'
        match = re.search(pattern, content)
        if match:
            return match.group(1) == 'true'
        return None
    
    def convert_hunyuan3d_install(self) -> Dict[str, Any]:
        """Convert the Hunyuan3D-2 install.js to Python format"""
        
        # Based on the install.js we examined
        return {
            "run": [
                {
                    "when": "{{platform === 'win32'}}",
                    "method": "shell.run",
                    "params": {"message": "set"}
                },
                {
                    "method": "shell.run", 
                    "params": {
                        "message": ["git clone https://github.com/Tencent/Hunyuan3D-2 app"]
                    }
                },
                {
                    "method": "script.start",
                    "params": {
                        "uri": "torch.js",
                        "params": {
                            "venv": "env",
                            "path": "app"
                        }
                    }
                },
                {
                    "method": "shell.run",
                    "params": {
                        "venv": "env",
                        "path": "app", 
                        "message": ["uv pip install -r requirements.txt"]
                    }
                },
                {
                    "when": "{{platform === 'linux'}}",
                    "method": "shell.run",
                    "params": {
                        "message": [
                            "conda install -y -c conda-forge 'gxx<12'",
                            "which g++"
                        ]
                    }
                },
                {
                    "when": "{{platform === 'linux'}}",
                    "method": "shell.run",
                    "params": {
                        "build": True,
                        "venv": "../../../env",
                        "env": {
                            "USE_NINJA": "0",
                            "DISTUTILS_USE_SDK": "1", 
                            "NVCC_PREPEND_FLAGS": "-ccbin {{which('g++')}}"
                        },
                        "path": "app/hy3dgen/texgen/custom_rasterizer",
                        "message": ["python setup.py install"]
                    }
                },
                {
                    "when": "{{platform !== 'linux'}}",
                    "method": "shell.run", 
                    "params": {
                        "build": True,
                        "venv": "../../../env",
                        "env": {
                            "USE_NINJA": "0",
                            "DISTUTILS_USE_SDK": "1"
                        },
                        "path": "app/hy3dgen/texgen/custom_rasterizer",
                        "message": ["python setup.py install"]
                    }
                },
                {
                    "when": "{{platform === 'linux'}}",
                    "method": "shell.run",
                    "params": {
                        "build": True,
                        "venv": "../../../env", 
                        "env": {
                            "USE_NINJA": "0",
                            "DISTUTILS_USE_SDK": "1",
                            "NVCC_PREPEND_FLAGS": "-ccbin {{which('g++')}}"
                        },
                        "path": "app/hy3dgen/texgen/differentiable_renderer",
                        "message": ["python setup.py install"]
                    }
                },
                {
                    "when": "{{platform !== 'linux'}}",
                    "method": "shell.run",
                    "params": {
                        "build": True,
                        "venv": "../../../env",
                        "env": {
                            "USE_NINJA": "0", 
                            "DISTUTILS_USE_SDK": "1"
                        },
                        "path": "app/hy3dgen/texgen/differentiable_renderer",
                        "message": ["python setup.py install"]
                    }
                }
            ]
        }
    
    def convert_torch_install(self) -> Dict[str, Any]:
        """Convert the torch.js installation script to Python format"""
        
        return {
            "run": [
                {
                    "when": "{{gpu === 'nvidia' && kernel.gpu_model && / 50.+/.test(kernel.gpu_model) }}",
                    "method": "shell.run",
                    "params": {
                        "venv": "{{args && args.venv ? args.venv : null}}",
                        "path": "{{args && args.path ? args.path : '.'}}",
                        "message": [
                            "uv pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128"
                        ]
                    }
                },
                {
                    "when": "{{platform === 'win32' && gpu === 'nvidia'}}",
                    "method": "shell.run",
                    "params": {
                        "venv": "{{args && args.venv ? args.venv : null}}",
                        "path": "{{args && args.path ? args.path : '.'}}",
                        "message": "uv pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 {{args && args.xformers ? 'xformers' : ''}} --index-url https://download.pytorch.org/whl/cu121"
                    }
                },
                {
                    "when": "{{platform === 'win32' && gpu === 'amd'}}",
                    "method": "shell.run",
                    "params": {
                        "venv": "{{args && args.venv ? args.venv : null}}",
                        "path": "{{args && args.path ? args.path : '.'}}",
                        "message": "uv pip install torch-directml torchaudio torchvision numpy==1.26.4"
                    }
                },
                {
                    "when": "{{platform === 'win32' && (gpu !== 'nvidia' && gpu !== 'amd')}}",
                    "method": "shell.run",
                    "params": {
                        "venv": "{{args && args.venv ? args.venv : null}}",
                        "path": "{{args && args.path ? args.path : '.'}}",
                        "message": "uv pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 numpy==1.26.4"
                    }
                },
                {
                    "when": "{{platform === 'darwin'}}",
                    "method": "shell.run",
                    "params": {
                        "venv": "{{args && args.venv ? args.venv : null}}",
                        "path": "{{args && args.path ? args.path : '.'}}",
                        "message": "uv pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1"
                    }
                },
                {
                    "when": "{{platform === 'linux' && gpu === 'nvidia'}}",
                    "method": "shell.run",
                    "params": {
                        "venv": "{{args && args.venv ? args.venv : null}}",
                        "path": "{{args && args.path ? args.path : '.'}}",
                        "message": "uv pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 {{args && args.xformers ? 'xformers' : ''}} --index-url https://download.pytorch.org/whl/cu121"
                    }
                },
                {
                    "when": "{{platform === 'linux' && gpu === 'amd'}}",
                    "method": "shell.run",
                    "params": {
                        "venv": "{{args && args.venv ? args.venv : null}}",
                        "path": "{{args && args.path ? args.path : '.'}}",
                        "message": "uv pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/rocm6.0"
                    }
                },
                {
                    "when": "{{platform === 'linux' && (gpu !== 'amd' && gpu !=='nvidia')}}",
                    "method": "shell.run",
                    "params": {
                        "venv": "{{args && args.venv ? args.venv : null}}",
                        "path": "{{args && args.path ? args.path : '.'}}",
                        "message": "uv pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu"
                    }
                }
            ]
        }


def test_converter():
    """Test the JS converter with sample content"""
    converter = JSPinokioConverter()
    
    # Test Hunyuan3D conversion
    hunyuan_config = converter.convert_hunyuan3d_install()
    print("Hunyuan3D Install Config:")
    print(json.dumps(hunyuan_config, indent=2))
    
    # Test torch conversion  
    torch_config = converter.convert_torch_install()
    print("\nTorch Install Config:")
    print(json.dumps(torch_config, indent=2))

if __name__ == "__main__":
    test_converter()
