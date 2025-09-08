#!/usr/bin/env python3
"""
Cloud Environment Manager - MINI MODULE 3
Handles cloud GPU service specific constraints and environment validation
Supports: Google Colab, Lightning AI, Vast.AI, Paperspace, etc.
"""

import os
import sys
import platform
import subprocess
import json
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class CloudEnvironmentManager:
    """Cloud-specific environment management with service constraints"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.platform_info = self._detect_cloud_platform()
        self.constraints = self._get_platform_constraints()
        
    def _detect_cloud_platform(self) -> Dict[str, Any]:
        """Detect specific cloud platform and its constraints"""
        platform_info = {
            'platform': 'unknown',
            'is_cloud': False,
            'supports_venv': True,
            'supports_conda': True,
            'supports_system_packages': True,
            'has_sudo': False,
            'environment_restrictions': []
        }
        
        # Google Colab detection
        if 'google.colab' in sys.modules:
            platform_info.update({
                'platform': 'google_colab',
                'is_cloud': True,
                'supports_venv': True,
                'supports_conda': True,  # Limited conda support
                'supports_system_packages': True,  # Can install with apt
                'has_sudo': False,  # No sudo in Colab
                'environment_restrictions': [
                    'limited_conda_envs',
                    'no_sudo_access',
                    'session_temporary',
                    'preinstalled_packages_conflict'
                ],
                'base_python': '/usr/bin/python3',
                'preinstalled_packages': self._get_colab_preinstalled(),
                'gpu_optimized': True
            })
            
        # Lightning AI detection (no conda/venv typically)
        elif 'LIGHTNING_CLOUD_PROJECT_ID' in os.environ or 'LIGHTNING_STUDIO' in os.environ:
            platform_info.update({
                'platform': 'lightning_ai',
                'is_cloud': True,
                'supports_venv': False,  # Lightning AI restricts venv creation
                'supports_conda': False,  # No conda in Lightning AI
                'supports_system_packages': False,  # No system package install
                'has_sudo': False,
                'environment_restrictions': [
                    'no_venv_creation',
                    'no_conda',
                    'no_system_packages',
                    'user_packages_only'
                ],
                'base_python': sys.executable,
                'package_install_method': 'user_pip_only'
            })
            
        # Vast.AI / Paperspace detection
        elif 'PAPERSPACE' in os.environ or self._is_vast_ai():
            platform_info.update({
                'platform': 'vast_ai_paperspace',
                'is_cloud': True,
                'supports_venv': True,
                'supports_conda': True,
                'supports_system_packages': True,  # Usually have sudo
                'has_sudo': True,
                'environment_restrictions': [
                    'persistent_storage_limited'
                ]
            })
            
        # Local development
        else:
            platform_info.update({
                'platform': 'local',
                'is_cloud': False,
                'supports_venv': True,
                'supports_conda': True,
                'supports_system_packages': True,
                'has_sudo': True,
                'environment_restrictions': []
            })
        
        logger.info(f"Detected platform: {platform_info['platform']}")
        return platform_info
    
    def _is_vast_ai(self) -> bool:
        """Detect Vast.AI or similar cloud GPU platforms"""
        # Check for common Vast.AI indicators
        vast_indicators = [
            '/workspace' in os.getcwd(),
            'vast.ai' in os.environ.get('HOSTNAME', '').lower(),
            os.path.exists('/opt/miniconda3'),  # Common in Vast.AI
            'cuda' in os.environ.get('PATH', '').lower()
        ]
        return sum(vast_indicators) >= 2
    
    def _get_colab_preinstalled(self) -> List[str]:
        """Get list of pre-installed packages in Colab that may cause conflicts"""
        return [
            'torch', 'torchvision', 'torchaudio',  # PyTorch suite
            'tensorflow', 'tensorflow-gpu',        # TensorFlow
            'numpy', 'scipy', 'matplotlib',        # Scientific computing
            'pandas', 'sklearn', 'opencv-python',  # Data science
            'pillow', 'requests', 'beautifulsoup4' # Common utilities
        ]
    
    def _get_platform_constraints(self) -> Dict[str, Any]:
        """Get platform-specific constraints and workarounds"""
        platform = self.platform_info['platform']
        
        constraints = {
            'google_colab': {
                'venv_strategy': 'isolated_user_install',  # Use --user installs in isolated dirs
                'conda_strategy': 'limited_use',          # Only for specific packages
                'conflict_resolution': 'version_pinning', # Pin versions to avoid conflicts
                'temp_session_handling': 'state_persistence', # Save state for session restarts
                'gpu_optimization': 'cuda_precheck',      # Verify CUDA before GPU packages
                'install_method': 'pip_with_user_flag'
            },
            'lightning_ai': {
                'venv_strategy': 'disabled',              # Cannot create venvs
                'conda_strategy': 'disabled',             # No conda available
                'conflict_resolution': 'careful_user_install', # Only --user installs
                'environment_isolation': 'import_path_manipulation', # Use sys.path instead
                'install_method': 'pip_user_only',
                'package_validation': 'strict_prereq_check'
            },
            'vast_ai_paperspace': {
                'venv_strategy': 'full_isolation',        # Full venv support
                'conda_strategy': 'recommended',          # Conda available and recommended
                'conflict_resolution': 'environment_isolation', # Separate envs per app
                'install_method': 'venv_or_conda',
                'sudo_available': True
            },
            'local': {
                'venv_strategy': 'full_support',
                'conda_strategy': 'full_support',
                'conflict_resolution': 'environment_isolation',
                'install_method': 'any'
            }
        }
        
        return constraints.get(platform, constraints['local'])
    
    async def create_app_environment(self, app_name: str, requirements: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create optimal environment for app based on platform constraints"""
        try:
            platform = self.platform_info['platform']
            constraints = self.constraints
            
            logger.info(f"Creating environment for {app_name} on {platform}")
            
            if platform == 'lightning_ai':
                # Lightning AI: No venv/conda, use sys.path manipulation
                return await self._create_lightning_ai_environment(app_name, requirements)
                
            elif platform == 'google_colab':
                # Colab: Careful venv with conflict avoidance
                return await self._create_colab_environment(app_name, requirements)
                
            else:
                # Vast.AI, Paperspace, Local: Full environment support
                return await self._create_standard_environment(app_name, requirements)
                
        except Exception as e:
            logger.error(f"Environment creation failed for {app_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _create_lightning_ai_environment(self, app_name: str, requirements: Optional[List[str]]) -> Dict[str, Any]:
        """Create environment for Lightning AI (no venv/conda)"""
        try:
            logger.info(f"Lightning AI environment setup for {app_name}")
            
            # Create app-specific directory for package management
            app_env_dir = self.base_path / "environments" / app_name
            app_env_dir.mkdir(parents=True, exist_ok=True)
            
            # Lightning AI strategy: --user installs with PYTHONPATH manipulation
            env_config = {
                'platform': 'lightning_ai',
                'method': 'user_install_with_path',
                'python_path': str(app_env_dir),
                'install_command_prefix': f'pip install --user --target {app_env_dir}',
                'activation_method': 'pythonpath_prepend',
                'environment_vars': {
                    'PYTHONPATH': f"{app_env_dir}:{os.environ.get('PYTHONPATH', '')}"
                }
            }
            
            logger.info(f"Lightning AI environment configured: {env_config}")
            return {'success': True, 'config': env_config}
            
        except Exception as e:
            return {'success': False, 'error': f"Lightning AI environment failed: {e}"}
    
    async def _create_colab_environment(self, app_name: str, requirements: Optional[List[str]]) -> Dict[str, Any]:
        """Create environment for Google Colab with conflict avoidance"""
        try:
            logger.info(f"Google Colab environment setup for {app_name}")
            
            # Check for potential conflicts with pre-installed packages
            conflicts = []
            if requirements:
                preinstalled = self.platform_info.get('preinstalled_packages', [])
                conflicts = [req for req in requirements if any(req.startswith(pkg) for pkg in preinstalled)]
                
                if conflicts:
                    logger.warning(f"Potential conflicts detected: {conflicts}")
            
            # Create isolated venv for apps
            venv_path = self.base_path / "venvs" / app_name
            
            env_config = {
                'platform': 'google_colab',
                'method': 'isolated_venv',
                'venv_path': str(venv_path),
                'python_executable': str(venv_path / 'bin' / 'python'),
                'potential_conflicts': conflicts,
                'install_strategy': 'venv_isolated',
                'gpu_optimized': True,
                'environment_vars': {
                    'CUDA_VISIBLE_DEVICES': '0',
                    'COLAB_GPU': '1'
                }
            }
            
            # Create venv if doesn't exist
            if not venv_path.exists():
                import venv
                venv.create(venv_path, with_pip=True, clear=True)
                logger.info(f"Created Colab venv: {venv_path}")
            
            return {'success': True, 'config': env_config}
            
        except Exception as e:
            return {'success': False, 'error': f"Colab environment failed: {e}"}
    
    async def _create_standard_environment(self, app_name: str, requirements: Optional[List[str]]) -> Dict[str, Any]:
        """Create standard environment (Vast.AI, Paperspace, Local)"""
        try:
            logger.info(f"Standard environment setup for {app_name}")
            
            # Prefer conda if available, fallback to venv
            if self.platform_info['supports_conda'] and self._is_conda_available():
                return await self._create_conda_environment(app_name, requirements)
            else:
                return await self._create_venv_environment(app_name, requirements)
                
        except Exception as e:
            return {'success': False, 'error': f"Standard environment failed: {e}"}
    
    async def _create_conda_environment(self, app_name: str, requirements: Optional[List[str]]) -> Dict[str, Any]:
        """Create conda environment (preferred for GPU packages)"""
        try:
            conda_env_name = f"pinokio_{app_name}"
            
            # Create conda environment
            create_cmd = ['conda', 'create', '-n', conda_env_name, 'python=3.10', '-y']
            result = await self._run_command(create_cmd)
            
            if not result['success']:
                logger.warning("Conda environment creation failed, falling back to venv")
                return await self._create_venv_environment(app_name, requirements)
            
            env_config = {
                'platform': self.platform_info['platform'],
                'method': 'conda_environment',
                'env_name': conda_env_name,
                'activation': f'conda activate {conda_env_name}',
                'install_command_prefix': f'conda run -n {conda_env_name} pip install',
                'python_executable': f'conda run -n {conda_env_name} python',
                'gpu_optimized': True
            }
            
            logger.info(f"Conda environment created: {conda_env_name}")
            return {'success': True, 'config': env_config}
            
        except Exception as e:
            return {'success': False, 'error': f"Conda environment failed: {e}"}
    
    async def _create_venv_environment(self, app_name: str, requirements: Optional[List[str]]) -> Dict[str, Any]:
        """Create virtual environment with enhanced validation"""
        try:
            venv_path = self.base_path / "venvs" / app_name
            
            import venv
            venv.create(venv_path, with_pip=True, clear=True)
            
            env_config = {
                'platform': self.platform_info['platform'],
                'method': 'virtual_environment',
                'venv_path': str(venv_path),
                'python_executable': str(venv_path / 'bin' / 'python'),
                'install_command_prefix': f'"{venv_path / "bin" / "python"}" -m pip install',
                'activation_script': str(venv_path / 'bin' / 'activate')
            }
            
            logger.info(f"Virtual environment created: {venv_path}")
            return {'success': True, 'config': env_config}
            
        except Exception as e:
            return {'success': False, 'error': f"Venv creation failed: {e}"}
    
    def validate_requirements_compatibility(self, requirements: List[str], app_name: str) -> Dict[str, Any]:
        """Pre-validate requirements against platform constraints - ENHANCED ERROR MESSAGES"""
        validation_result = {
            'compatible': True,
            'warnings': [],
            'errors': [],
            'recommendations': [],
            'install_strategy': 'standard'
        }
        
        platform = self.platform_info['platform']
        
        # Platform-specific validation
        if platform == 'lightning_ai':
            validation_result.update(self._validate_lightning_ai_requirements(requirements, app_name))
        elif platform == 'google_colab':
            validation_result.update(self._validate_colab_requirements(requirements, app_name))
        else:
            validation_result.update(self._validate_standard_requirements(requirements, app_name))
        
        return validation_result
    
    def _validate_lightning_ai_requirements(self, requirements: List[str], app_name: str) -> Dict[str, Any]:
        """Validate requirements for Lightning AI constraints"""
        result = {'warnings': [], 'errors': [], 'recommendations': []}
        
        # Lightning AI specific checks
        problematic_packages = ['conda', 'mamba', 'nvidia-ml-py']
        
        for req in requirements:
            package_name = req.split('>=')[0].split('==')[0].strip()
            
            if package_name in problematic_packages:
                result['errors'].append(
                    f"🚫 {package_name} not supported on Lightning AI - "
                    f"Lightning AI doesn't allow conda or system GPU packages"
                )
                result['recommendations'].append(
                    f"💡 For {app_name}: Use pip-installable alternative or pre-installed packages"
                )
            
            # Check for GPU packages that need special handling
            if any(gpu_term in package_name.lower() for gpu_term in ['cuda', 'torch', 'tensorflow']):
                result['warnings'].append(
                    f"⚠️ {package_name} is a GPU package - verify Lightning AI compatibility"
                )
                result['recommendations'].append(
                    f"💡 Lightning AI may have {package_name} pre-installed - check before installing"
                )
        
        return result
    
    def _validate_colab_requirements(self, requirements: List[str], app_name: str) -> Dict[str, Any]:
        """Validate requirements for Google Colab constraints"""
        result = {'warnings': [], 'errors': [], 'recommendations': []}
        
        preinstalled = self.platform_info.get('preinstalled_packages', [])
        
        for req in requirements:
            package_name = req.split('>=')[0].split('==')[0].strip()
            
            # Check for conflicts with pre-installed packages
            if package_name in preinstalled:
                result['warnings'].append(
                    f"⚠️ {package_name} is pre-installed in Colab - version conflicts possible"
                )
                result['recommendations'].append(
                    f"💡 For {app_name}: Use isolated venv or pin exact version to match Colab"
                )
            
            # Check for packages that need special Colab handling
            if package_name in ['torch', 'torchvision', 'tensorflow']:
                result['recommendations'].append(
                    f"💡 {package_name}: Use Colab's pre-installed version or install with --upgrade --force-reinstall"
                )
        
        return result
    
    def _validate_standard_requirements(self, requirements: List[str], app_name: str) -> Dict[str, Any]:
        """Validate requirements for standard cloud platforms"""
        result = {'warnings': [], 'errors': [], 'recommendations': []}
        
        # Check for common problematic packages
        for req in requirements:
            package_name = req.split('>=')[0].split('==')[0].strip()
            
            # Packages that commonly cause issues
            if package_name in ['opencv-python', 'opencv-contrib-python']:
                result['recommendations'].append(
                    f"💡 {package_name}: May need system dependencies (libgl1-mesa-glx)"
                )
            elif package_name in ['torch', 'torchvision']:
                result['recommendations'].append(
                    f"💡 {package_name}: Consider CUDA-specific version for GPU acceleration"
                )
        
        return result
    
    def _is_conda_available(self) -> bool:
        """Check if conda is available on the system"""
        try:
            result = subprocess.run(['conda', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    async def _run_command(self, command: List[str]) -> Dict[str, Any]:
        """Run command with proper error handling"""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'success': process.returncode == 0,
                'stdout': stdout.decode(),
                'stderr': stderr.decode(),
                'returncode': process.returncode
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': '',
                'returncode': -1
            }
    
    def get_install_command_for_platform(self, package: str, app_name: str) -> str:
        """Get platform-optimized install command with enhanced error messages"""
        platform = self.platform_info['platform']
        constraints = self.constraints
        
        if platform == 'lightning_ai':
            # Lightning AI: User-only installs
            app_env_dir = self.base_path / "environments" / app_name
            return f'pip install --user --target {app_env_dir} {package}'
            
        elif platform == 'google_colab':
            # Colab: Isolated venv installs
            venv_path = self.base_path / "venvs" / app_name
            python_exe = venv_path / 'bin' / 'python'
            return f'"{python_exe}" -m pip install {package}'
            
        else:
            # Standard platforms: venv or conda
            if self._is_conda_available():
                return f'conda run -n pinokio_{app_name} pip install {package}'
            else:
                venv_path = self.base_path / "venvs" / app_name
                python_exe = venv_path / 'bin' / 'python'
                return f'"{python_exe}" -m pip install {package}'
    
    def get_python_executable_for_app(self, app_name: str) -> str:
        """Get correct Python executable for app environment"""
        platform = self.platform_info['platform']
        
        if platform == 'lightning_ai':
            return sys.executable  # Use current Python
            
        elif platform == 'google_colab':
            venv_path = self.base_path / "venvs" / app_name
            return str(venv_path / 'bin' / 'python')
            
        else:
            if self._is_conda_available():
                return f'conda run -n pinokio_{app_name} python'
            else:
                venv_path = self.base_path / "venvs" / app_name  
                return str(venv_path / 'bin' / 'python')
    
    def generate_detailed_error_message(self, error_type: str, details: Dict[str, Any]) -> str:
        """Generate enhanced error messages for users - MINI MODULE 3"""
        platform = self.platform_info['platform']
        
        error_templates = {
            'app_not_found': {
                'lightning_ai': f"""
🚫 App not found: {details.get('app_name', 'Unknown')}

🔍 Search Tips for Lightning AI:
   • Check app name spelling exactly
   • Try searching by category instead
   • Lightning AI works best with simple Python apps

📱 Available apps (sample): {', '.join(details.get('available_apps_sample', [])[:3])}
💡 Tip: Browse all apps to find similar alternatives
""",
                'google_colab': f"""
🚫 App not found: {details.get('app_name', 'Unknown')}

🔍 Search Tips for Google Colab:
   • App names are case-sensitive
   • Try partial name matches in the search box
   • Most AI apps work well in Colab GPU environment

📱 Available apps (sample): {', '.join(details.get('available_apps_sample', [])[:3])}
🎮 Tip: GPU-optimized apps work best in Colab
""",
                'default': f"""
🚫 App not found: {details.get('app_name', 'Unknown')}

📱 Available apps (sample): {', '.join(details.get('available_apps_sample', [])[:3])}
💡 Tip: Use the search function to find similar apps
"""
            },
            'environment_setup_failed': {
                'lightning_ai': f"""
🚫 Environment setup failed on Lightning AI

❌ Error: {details.get('error', 'Unknown error')}
🔧 Lightning AI Constraints:
   • No virtual environments allowed
   • No conda package manager
   • Only --user pip installs supported
   • Limited system package access

💡 Solutions for {details.get('app_name', 'this app')}:
   1. App will use --user pip installs automatically
   2. Check if app has Lightning AI specific requirements
   3. Some GPU packages may be pre-installed
   4. Try alternative apps if this one requires conda/venv

📚 Note: Lightning AI is restrictive but fast for simple Python apps
""",
                'google_colab': f"""
🚫 Environment setup failed on Google Colab

❌ Error: {details.get('error', 'Unknown error')}
🔧 Google Colab Notes:
   • Virtual environments supported but may be slow
   • Some packages are pre-installed
   • Session storage is temporary (12 hours max)
   • CUDA packages need special handling

💡 Solutions for {details.get('app_name', 'this app')}:
   1. Restart runtime and try again
   2. Clear output and run installation cell again
   3. Check if app conflicts with pre-installed packages
   4. Try using isolated virtual environment

📚 Note: Colab is very compatible but has pre-installed packages
""",
                'default': f"""
🚫 Environment setup failed

❌ Error: {details.get('error', 'Unknown error')}
💡 General Solutions:
   1. Check available disk space
   2. Verify Python version compatibility  
   3. Ensure write permissions to installation directory
   4. Try restarting and running setup again
"""
            },
            'install_script_failed': {
                'lightning_ai': f"""
🚫 Installation script failed on Lightning AI

❌ Error: {details.get('error', 'Unknown error')}
📜 Script: {details.get('script', 'Unknown')}
📊 Failed at step: {details.get('step', 'Unknown')}

🔧 Lightning AI Troubleshooting:
   • App may require conda/venv (not supported)
   • GPU packages may need to use pre-installed versions
   • System packages cannot be installed
   • Some apps are not Lightning AI compatible

💡 Solutions for {details.get('app_name', 'this app')}:
   1. Check app documentation for Lightning AI support
   2. Try alternative apps with simpler requirements
   3. Contact app developer for Lightning AI compatibility
   4. Consider switching to Google Colab for broader compatibility

📚 Recommendation: Use Google Colab for maximum app compatibility
""",
                'google_colab': f"""
🚫 Installation script failed on Google Colab

❌ Error: {details.get('error', 'Unknown error')}
📜 Script: {details.get('script', 'Unknown')}
📊 Failed at step: {details.get('step', 'Unknown')}

🔧 Google Colab Troubleshooting:
   • May be a package conflict with pre-installed libraries
   • Could be a temporary network or disk space issue
   • Some packages need specific versions for Colab

💡 Solutions for {details.get('app_name', 'this app')}:
   1. Restart runtime (Runtime → Restart runtime)
   2. Clear all outputs and try installation again
   3. Check if app has Colab-specific installation instructions
   4. Try installing in a fresh session

📚 Note: Colab is very compatible - failures are usually temporary
""",
                'default': f"""
🚫 Installation script failed

❌ Error: {details.get('error', 'Unknown error')}
📜 Script: {details.get('script', 'Unknown')}
📊 Failed at step: {details.get('step', 'Unknown')}

💡 General Solutions:
   1. Check internet connection for downloads
   2. Verify all dependencies are available
   3. Check installation logs for specific error details
   4. Try running installation script manually for debugging
"""
            },
            'install_exception': {
                'lightning_ai': f"""
💥 Installation exception on Lightning AI

❌ Error: {details.get('error', 'Unknown error')}

⚡ Lightning AI Quick Fixes:
   • This platform has strict limitations
   • Try apps marked as "Lightning AI compatible"
   • Consider using Google Colab for better compatibility
   
💡 For {details.get('app_name', 'this app')}:
   1. Check if app supports Lightning AI
   2. Try simpler alternative apps
   3. Use Colab instead for complex GPU apps
""",
                'default': f"""
💥 Installation exception

❌ Error: {details.get('error', 'Unknown error')}
💡 Try restarting and attempting installation again
"""
            },
            'dependency_install_failed': {
                'lightning_ai': f"""
🚫 Package installation failed on Lightning AI

❌ Error: {details.get('error', 'Unknown error')}
🔧 Lightning AI Constraints:
   • No virtual environments allowed
   • No conda package manager  
   • Only --user pip installs supported

💡 Solutions:
   1. Try: pip install --user {details.get('package', 'package')}
   2. Check if package is already available
   3. Use alternative package if available
   4. Contact app developer for Lightning AI support

📚 More info: Lightning AI has strict package limitations
""",
                'google_colab': f"""
🚫 Package installation failed on Google Colab

❌ Error: {details.get('error', 'Unknown error')}
🔧 Google Colab Notes:
   • Some packages are pre-installed (may conflict)
   • CUDA packages need special handling
   • Session storage is temporary

💡 Solutions:
   1. Try: pip install --force-reinstall {details.get('package', 'package')}
   2. Use isolated virtual environment
   3. Check Colab pre-installed packages
   4. Restart runtime if conflicts persist

📚 More info: Colab has pre-installed ML packages
""",
                'default': f"""
🚫 Package installation failed

❌ Error: {details.get('error', 'Unknown error')}
💡 General Solutions:
   1. Check internet connection
   2. Verify package name spelling
   3. Try updating pip: python -m pip install --upgrade pip
   4. Check virtual environment is activated
"""
            }
        }
        
        template_key = platform if platform in ['lightning_ai', 'google_colab'] else 'default'
        return error_templates[error_type].get(template_key, error_templates[error_type]['default'])