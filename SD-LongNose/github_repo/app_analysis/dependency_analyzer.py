#!/usr/bin/env python3
"""
PinokioCloud Dependency Analyzer

This module analyzes dependency systems for Pinokio applications.
It identifies and categorizes dependencies including pip, conda, npm,
system packages, and other dependency management systems.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class DependencyType(Enum):
    """Enumeration of dependency types."""
    PIP = "pip"
    CONDA = "conda"
    NPM = "npm"
    SYSTEM = "system"
    DOCKER = "docker"
    GIT = "git"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class DependencyCategory(Enum):
    """Enumeration of dependency categories."""
    CORE = "core"
    ML_AI = "ml_ai"
    WEB = "web"
    DATA = "data"
    VISION = "vision"
    AUDIO = "audio"
    TEXT = "text"
    UTILITY = "utility"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class DependencyInfo:
    """Information about application dependencies."""
    dependency_types: List[DependencyType] = field(default_factory=list)
    pip_dependencies: List[str] = field(default_factory=list)
    conda_dependencies: List[str] = field(default_factory=list)
    npm_dependencies: List[str] = field(default_factory=list)
    system_dependencies: List[str] = field(default_factory=list)
    git_dependencies: List[str] = field(default_factory=list)
    docker_dependencies: List[str] = field(default_factory=list)
    dependency_categories: Dict[DependencyCategory, List[str]] = field(default_factory=dict)
    python_version_requirement: Optional[str] = None
    node_version_requirement: Optional[str] = None
    system_requirements: List[str] = field(default_factory=list)
    conflict_potential: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DependencyAnalyzer:
    """
    Analyzes dependency systems for Pinokio applications.
    
    Analyzes application directories to determine:
    - Types of dependency systems used (pip, conda, npm, etc.)
    - Specific dependencies and their versions
    - Dependency categories and purposes
    - Version requirements and conflicts
    - System requirements and dependencies
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the dependency analyzer.
        
        Args:
            base_path: Base path for analysis
        """
        self.base_path = base_path
        
        # Dependency categorization patterns
        self.dependency_categories = {
            DependencyCategory.ML_AI: [
                "torch", "tensorflow", "keras", "scikit-learn", "numpy", "pandas",
                "opencv-python", "pillow", "matplotlib", "seaborn", "plotly",
                "transformers", "huggingface", "diffusers", "accelerate",
                "xformers", "bitsandbytes", "peft", "trl"
            ],
            DependencyCategory.WEB: [
                "flask", "fastapi", "django", "streamlit", "gradio", "dash",
                "tornado", "bokeh", "jupyter", "uvicorn", "gunicorn"
            ],
            DependencyCategory.DATA: [
                "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
                "bokeh", "altair", "dash", "jupyter", "ipython"
            ],
            DependencyCategory.VISION: [
                "opencv-python", "pillow", "imageio", "scikit-image", "albumentations",
                "torchvision", "tensorflow", "keras", "mediapipe", "face-recognition"
            ],
            DependencyCategory.AUDIO: [
                "librosa", "soundfile", "pyaudio", "pydub", "webrtcvad",
                "speechrecognition", "pocketsphinx", "whisper", "torchaudio"
            ],
            DependencyCategory.TEXT: [
                "transformers", "tokenizers", "nltk", "spacy", "textblob",
                "gensim", "word2vec", "sentence-transformers", "langchain"
            ],
            DependencyCategory.UTILITY: [
                "requests", "urllib3", "httpx", "aiohttp", "click", "typer",
                "rich", "tqdm", "colorama", "python-dotenv", "pyyaml"
            ],
            DependencyCategory.SYSTEM: [
                "psutil", "GPUtil", "nvidia-ml-py", "pynvml", "py-cpuinfo",
                "distro", "platform", "os", "sys", "subprocess"
            ]
        }
        
        # Common system packages
        self.system_packages = [
            "apt", "yum", "dnf", "brew", "pacman", "zypper", "emerge",
            "apt-get", "aptitude", "dpkg", "rpm", "yum", "dnf", "zypper"
        ]
    
    def analyze_dependencies(self, app_path: str) -> DependencyInfo:
        """
        Analyze dependencies for an application.
        
        Args:
            app_path: Path to the application directory
            
        Returns:
            DependencyInfo: Information about dependencies
        """
        try:
            if not os.path.exists(app_path) or not os.path.isdir(app_path):
                return DependencyInfo()
            
            # Initialize dependency info
            dep_info = DependencyInfo()
            
            # Analyze different dependency files
            self._analyze_pip_dependencies(app_path, dep_info)
            self._analyze_conda_dependencies(app_path, dep_info)
            self._analyze_npm_dependencies(app_path, dep_info)
            self._analyze_system_dependencies(app_path, dep_info)
            self._analyze_git_dependencies(app_path, dep_info)
            self._analyze_docker_dependencies(app_path, dep_info)
            
            # Categorize dependencies
            self._categorize_dependencies(dep_info)
            
            # Analyze version requirements
            self._analyze_version_requirements(app_path, dep_info)
            
            # Check for conflicts
            self._check_dependency_conflicts(dep_info)
            
            # Update metadata
            dep_info.metadata = {
                "total_dependencies": len(dep_info.pip_dependencies) + len(dep_info.conda_dependencies) + 
                                   len(dep_info.npm_dependencies) + len(dep_info.system_dependencies),
                "dependency_types_count": len(dep_info.dependency_types),
                "categories_count": len(dep_info.dependency_categories)
            }
            
            return dep_info
        
        except Exception as e:
            return DependencyInfo(metadata={"error": str(e)})
    
    def _analyze_pip_dependencies(self, app_path: str, dep_info: DependencyInfo):
        """Analyze pip dependencies from requirements files."""
        try:
            requirements_files = [
                "requirements.txt", "requirements-dev.txt", "requirements-test.txt",
                "requirements-prod.txt", "requirements-lock.txt"
            ]
            
            for req_file in requirements_files:
                req_path = os.path.join(app_path, req_file)
                if os.path.exists(req_path):
                    with open(req_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse requirements
                    dependencies = self._parse_requirements_txt(content)
                    dep_info.pip_dependencies.extend(dependencies)
                    
                    if DependencyType.PIP not in dep_info.dependency_types:
                        dep_info.dependency_types.append(DependencyType.PIP)
            
            # Also check for pip install commands in scripts
            self._extract_pip_from_scripts(app_path, dep_info)
        
        except Exception as e:
            pass
    
    def _analyze_conda_dependencies(self, app_path: str, dep_info: DependencyInfo):
        """Analyze conda dependencies from environment files."""
        try:
            conda_files = [
                "environment.yml", "environment.yaml", "conda.yml", "conda.yaml"
            ]
            
            for conda_file in conda_files:
                conda_path = os.path.join(app_path, conda_file)
                if os.path.exists(conda_path):
                    with open(conda_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse conda environment
                    dependencies = self._parse_conda_environment(content)
                    dep_info.conda_dependencies.extend(dependencies)
                    
                    if DependencyType.CONDA not in dep_info.dependency_types:
                        dep_info.dependency_types.append(DependencyType.CONDA)
            
            # Also check for conda install commands in scripts
            self._extract_conda_from_scripts(app_path, dep_info)
        
        except Exception as e:
            pass
    
    def _analyze_npm_dependencies(self, app_path: str, dep_info: DependencyInfo):
        """Analyze npm dependencies from package.json."""
        try:
            package_json_path = os.path.join(app_path, "package.json")
            if os.path.exists(package_json_path):
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract dependencies
                dependencies = data.get("dependencies", {})
                dev_dependencies = data.get("devDependencies", {})
                all_deps = {**dependencies, **dev_dependencies}
                
                dep_info.npm_dependencies = list(all_deps.keys())
                
                if DependencyType.NPM not in dep_info.dependency_types:
                    dep_info.dependency_types.append(DependencyType.NPM)
            
            # Also check for npm install commands in scripts
            self._extract_npm_from_scripts(app_path, dep_info)
        
        except Exception as e:
            pass
    
    def _analyze_system_dependencies(self, app_path: str, dep_info: DependencyInfo):
        """Analyze system dependencies from scripts and files."""
        try:
            # Search for system package installation commands
            for root, dirs, files in os.walk(app_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.sh', '.bat', '.yml', '.yaml')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Extract system package commands
                            system_deps = self._extract_system_packages(content)
                            dep_info.system_dependencies.extend(system_deps)
                            
                        except:
                            continue
            
            # Remove duplicates
            dep_info.system_dependencies = list(set(dep_info.system_dependencies))
            
            if dep_info.system_dependencies and DependencyType.SYSTEM not in dep_info.dependency_types:
                dep_info.dependency_types.append(DependencyType.SYSTEM)
        
        except Exception as e:
            pass
    
    def _analyze_git_dependencies(self, app_path: str, dep_info: DependencyInfo):
        """Analyze git dependencies from scripts and files."""
        try:
            # Search for git clone commands
            for root, dirs, files in os.walk(app_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.sh', '.bat')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Extract git clone commands
                            git_deps = self._extract_git_repositories(content)
                            dep_info.git_dependencies.extend(git_deps)
                            
                        except:
                            continue
            
            # Remove duplicates
            dep_info.git_dependencies = list(set(dep_info.git_dependencies))
            
            if dep_info.git_dependencies and DependencyType.GIT not in dep_info.dependency_types:
                dep_info.dependency_types.append(DependencyType.GIT)
        
        except Exception as e:
            pass
    
    def _analyze_docker_dependencies(self, app_path: str, dep_info: DependencyInfo):
        """Analyze docker dependencies from Dockerfile."""
        try:
            docker_files = ["Dockerfile", "dockerfile", "Dockerfile.dev", "Dockerfile.prod"]
            
            for docker_file in docker_files:
                docker_path = os.path.join(app_path, docker_file)
                if os.path.exists(docker_path):
                    with open(docker_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract docker dependencies
                    docker_deps = self._extract_docker_dependencies(content)
                    dep_info.docker_dependencies.extend(docker_deps)
                    
                    if DependencyType.DOCKER not in dep_info.dependency_types:
                        dep_info.dependency_types.append(DependencyType.DOCKER)
        
        except Exception as e:
            pass
    
    def _parse_requirements_txt(self, content: str) -> List[str]:
        """Parse requirements.txt content."""
        dependencies = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove version specifiers for now
                dep = re.split(r'[>=<!=]', line)[0].strip()
                if dep:
                    dependencies.append(dep)
        
        return dependencies
    
    def _parse_conda_environment(self, content: str) -> List[str]:
        """Parse conda environment.yml content."""
        dependencies = []
        
        try:
            # Simple YAML parsing for dependencies
            in_dependencies = False
            for line in content.split('\n'):
                line = line.strip()
                
                if line.startswith('dependencies:'):
                    in_dependencies = True
                    continue
                
                if in_dependencies:
                    if line.startswith('- ') and not line.startswith('- pip:'):
                        dep = line[2:].strip()
                        if dep:
                            dependencies.append(dep)
                    elif line and not line.startswith('- ') and not line.startswith(' '):
                        # End of dependencies section
                        break
        
        except Exception as e:
            pass
        
        return dependencies
    
    def _extract_pip_from_scripts(self, app_path: str, dep_info: DependencyInfo):
        """Extract pip install commands from scripts."""
        try:
            for root, dirs, files in os.walk(app_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.sh', '.bat')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Extract pip install commands
                            pip_pattern = r'pip\s+install\s+([^\s\n]+)'
                            matches = re.findall(pip_pattern, content, re.IGNORECASE)
                            
                            for match in matches:
                                # Handle multiple packages in one command
                                packages = match.split()
                                dep_info.pip_dependencies.extend(packages)
                            
                        except:
                            continue
        
        except Exception as e:
            pass
    
    def _extract_conda_from_scripts(self, app_path: str, dep_info: DependencyInfo):
        """Extract conda install commands from scripts."""
        try:
            for root, dirs, files in os.walk(app_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.sh', '.bat')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Extract conda install commands
                            conda_pattern = r'conda\s+install\s+([^\s\n]+)'
                            matches = re.findall(conda_pattern, content, re.IGNORECASE)
                            
                            for match in matches:
                                packages = match.split()
                                dep_info.conda_dependencies.extend(packages)
                            
                        except:
                            continue
        
        except Exception as e:
            pass
    
    def _extract_npm_from_scripts(self, app_path: str, dep_info: DependencyInfo):
        """Extract npm install commands from scripts."""
        try:
            for root, dirs, files in os.walk(app_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                for file in files:
                    if file.endswith(('.py', '.js', '.sh', '.bat')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Extract npm install commands
                            npm_pattern = r'npm\s+install\s+([^\s\n]+)'
                            matches = re.findall(npm_pattern, content, re.IGNORECASE)
                            
                            for match in matches:
                                packages = match.split()
                                dep_info.npm_dependencies.extend(packages)
                            
                        except:
                            continue
        
        except Exception as e:
            pass
    
    def _extract_system_packages(self, content: str) -> List[str]:
        """Extract system package installation commands."""
        system_deps = []
        
        try:
            # Common system package installation patterns
            patterns = [
                r'apt\s+install\s+([^\s\n]+)',
                r'apt-get\s+install\s+([^\s\n]+)',
                r'yum\s+install\s+([^\s\n]+)',
                r'dnf\s+install\s+([^\s\n]+)',
                r'brew\s+install\s+([^\s\n]+)',
                r'pacman\s+-S\s+([^\s\n]+)',
                r'zypper\s+install\s+([^\s\n]+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                system_deps.extend(matches)
        
        except Exception as e:
            pass
        
        return system_deps
    
    def _extract_git_repositories(self, content: str) -> List[str]:
        """Extract git clone commands."""
        git_deps = []
        
        try:
            # Git clone patterns
            patterns = [
                r'git\s+clone\s+([^\s\n]+)',
                r'git\s+submodule\s+add\s+([^\s\n]+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                git_deps.extend(matches)
        
        except Exception as e:
            pass
        
        return git_deps
    
    def _extract_docker_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from Dockerfile."""
        docker_deps = []
        
        try:
            # Docker patterns
            patterns = [
                r'FROM\s+([^\s\n]+)',
                r'RUN\s+apt-get\s+install\s+([^\s\n]+)',
                r'RUN\s+pip\s+install\s+([^\s\n]+)',
                r'RUN\s+conda\s+install\s+([^\s\n]+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                docker_deps.extend(matches)
        
        except Exception as e:
            pass
        
        return docker_deps
    
    def _categorize_dependencies(self, dep_info: DependencyInfo):
        """Categorize dependencies by purpose."""
        try:
            all_deps = (dep_info.pip_dependencies + dep_info.conda_dependencies + 
                       dep_info.npm_dependencies + dep_info.system_dependencies)
            
            for category, patterns in self.dependency_categories.items():
                category_deps = []
                
                for dep in all_deps:
                    dep_lower = dep.lower()
                    for pattern in patterns:
                        if pattern.lower() in dep_lower or dep_lower in pattern.lower():
                            category_deps.append(dep)
                            break
                
                if category_deps:
                    dep_info.dependency_categories[category] = list(set(category_deps))
        
        except Exception as e:
            pass
    
    def _analyze_version_requirements(self, app_path: str, dep_info: DependencyInfo):
        """Analyze version requirements from files."""
        try:
            # Check for Python version requirements
            for root, dirs, files in os.walk(app_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
                
                for file in files:
                    if file.endswith(('.py', '.txt', '.yml', '.yaml', '.json')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Extract Python version
                            python_patterns = [
                                r'python_requires\s*=\s*["\']([^"\']+)["\']',
                                r'python\s*([0-9]+\.[0-9]+)',
                                r'python_version\s*=\s*["\']([^"\']+)["\']'
                            ]
                            
                            for pattern in python_patterns:
                                match = re.search(pattern, content, re.IGNORECASE)
                                if match:
                                    dep_info.python_version_requirement = match.group(1)
                                    break
                            
                            # Extract Node version
                            node_patterns = [
                                r'engines.*?node.*?["\']([^"\']+)["\']',
                                r'node\s*([0-9]+\.[0-9]+)',
                                r'node_version\s*=\s*["\']([^"\']+)["\']'
                            ]
                            
                            for pattern in node_patterns:
                                match = re.search(pattern, content, re.IGNORECASE)
                                if match:
                                    dep_info.node_version_requirement = match.group(1)
                                    break
                            
                        except:
                            continue
        
        except Exception as e:
            pass
    
    def _check_dependency_conflicts(self, dep_info: DependencyInfo):
        """Check for potential dependency conflicts."""
        try:
            conflicts = []
            
            # Check for conflicting ML frameworks
            ml_frameworks = ["torch", "tensorflow", "keras", "jax"]
            found_frameworks = []
            
            all_deps = (dep_info.pip_dependencies + dep_info.conda_dependencies + 
                       dep_info.npm_dependencies)
            
            for dep in all_deps:
                dep_lower = dep.lower()
                for framework in ml_frameworks:
                    if framework in dep_lower:
                        found_frameworks.append(framework)
            
            if len(found_frameworks) > 1:
                conflicts.append(f"Multiple ML frameworks detected: {', '.join(found_frameworks)}")
            
            # Check for conflicting web frameworks
            web_frameworks = ["flask", "django", "fastapi", "tornado"]
            found_web = []
            
            for dep in all_deps:
                dep_lower = dep.lower()
                for framework in web_frameworks:
                    if framework in dep_lower:
                        found_web.append(framework)
            
            if len(found_web) > 1:
                conflicts.append(f"Multiple web frameworks detected: {', '.join(found_web)}")
            
            dep_info.conflict_potential = conflicts
        
        except Exception as e:
            pass


def main():
    """Main function for testing dependency analyzer."""
    print("🧪 Testing Dependency Analyzer")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = DependencyAnalyzer()
    
    # Test with a sample directory
    test_path = "/tmp/test_deps_app"
    os.makedirs(test_path, exist_ok=True)
    
    # Create test requirements.txt
    requirements_content = """
torch>=1.9.0
numpy>=1.21.0
opencv-python>=4.5.0
requests>=2.25.0
flask>=2.0.0
"""
    
    with open(os.path.join(test_path, "requirements.txt"), 'w') as f:
        f.write(requirements_content)
    
    # Create test environment.yml
    environment_content = """
name: test_env
dependencies:
  - python=3.9
  - pip
  - pip:
    - transformers
    - diffusers
"""
    
    with open(os.path.join(test_path, "environment.yml"), 'w') as f:
        f.write(environment_content)
    
    # Create test package.json
    package_json = {
        "name": "test-app",
        "dependencies": {
            "express": "^4.18.0",
            "axios": "^1.0.0"
        },
        "devDependencies": {
            "nodemon": "^2.0.0"
        }
    }
    
    with open(os.path.join(test_path, "package.json"), 'w') as f:
        json.dump(package_json, f, indent=2)
    
    # Test analysis
    print("\n📦 Testing dependency analysis...")
    result = analyzer.analyze_dependencies(test_path)
    
    print(f"✅ Dependency types: {[dt.value for dt in result.dependency_types]}")
    print(f"✅ Pip dependencies: {len(result.pip_dependencies)} found")
    print(f"✅ Conda dependencies: {len(result.conda_dependencies)} found")
    print(f"✅ NPM dependencies: {len(result.npm_dependencies)} found")
    print(f"✅ System dependencies: {len(result.system_dependencies)} found")
    print(f"✅ Git dependencies: {len(result.git_dependencies)} found")
    print(f"✅ Docker dependencies: {len(result.docker_dependencies)} found")
    print(f"✅ Python version requirement: {result.python_version_requirement}")
    print(f"✅ Node version requirement: {result.node_version_requirement}")
    print(f"✅ Dependency categories: {len(result.dependency_categories)} found")
    print(f"✅ Potential conflicts: {len(result.conflict_potential)} found")
    
    if result.pip_dependencies:
        print(f"   Pip deps: {', '.join(result.pip_dependencies[:5])}{'...' if len(result.pip_dependencies) > 5 else ''}")
    
    if result.dependency_categories:
        for category, deps in result.dependency_categories.items():
            print(f"   {category.value}: {', '.join(deps[:3])}{'...' if len(deps) > 3 else ''}")
    
    if result.conflict_potential:
        print(f"   Conflicts: {', '.join(result.conflict_potential)}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_path, ignore_errors=True)
    
    return True


if __name__ == "__main__":
    main()