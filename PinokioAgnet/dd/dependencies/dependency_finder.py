#!/usr/bin/env python3
"""
PinokioCloud Dependency Finder

This module finds and identifies all dependency files in Pinokio applications.
It searches for requirements.txt, environment.yml, package.json, setup.py,
and other dependency management files to provide comprehensive dependency detection.

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


class DependencyFileType(Enum):
    """Enumeration of dependency file types."""
    REQUIREMENTS_TXT = "requirements_txt"
    REQUIREMENTS_DEV_TXT = "requirements_dev_txt"
    REQUIREMENTS_PROD_TXT = "requirements_prod_txt"
    REQUIREMENTS_TEST_TXT = "requirements_test_txt"
    REQUIREMENTS_LOCK_TXT = "requirements_lock_txt"
    ENVIRONMENT_YML = "environment_yml"
    ENVIRONMENT_YAML = "environment_yaml"
    CONDA_YML = "conda_yml"
    CONDA_YAML = "conda_yaml"
    PACKAGE_JSON = "package_json"
    SETUP_PY = "setup_py"
    SETUP_CFG = "setup_cfg"
    PYPROJECT_TOML = "pyproject_toml"
    PIPFILE = "pipfile"
    PIPFILE_LOCK = "pipfile_lock"
    POETRY_LOCK = "poetry_lock"
    DOCKERFILE = "dockerfile"
    DOCKER_COMPOSE_YML = "docker_compose_yml"
    DOCKER_COMPOSE_YAML = "docker_compose_yaml"
    MAKEFILE = "makefile"
    CMAKE_LISTS = "cmake_lists"
    UNKNOWN = "unknown"


@dataclass
class DependencyFile:
    """Information about a dependency file."""
    file_type: DependencyFileType
    file_path: str
    relative_path: str
    file_size: int
    last_modified: float
    content_preview: str
    dependency_count: int = 0
    has_version_pins: bool = False
    has_dev_dependencies: bool = False
    has_optional_dependencies: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencySearchResult:
    """Result of dependency file search."""
    app_path: str
    total_files_found: int
    dependency_files: List[DependencyFile] = field(default_factory=list)
    search_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DependencyFinder:
    """
    Finds and identifies dependency files in Pinokio applications.
    
    Searches application directories for various dependency management files:
    - Python: requirements.txt, environment.yml, setup.py, pyproject.toml, Pipfile
    - Node.js: package.json, package-lock.json
    - System: Dockerfile, Makefile, CMakeLists.txt
    - Other: Various configuration and dependency files
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the dependency finder.
        
        Args:
            base_path: Base path for dependency search
        """
        self.base_path = base_path
        
        # Dependency file patterns
        self.dependency_patterns = {
            DependencyFileType.REQUIREMENTS_TXT: [
                "requirements.txt", "requirements-dev.txt", "requirements-prod.txt",
                "requirements-test.txt", "requirements-lock.txt", "requirements.in"
            ],
            DependencyFileType.ENVIRONMENT_YML: [
                "environment.yml", "environment.yaml", "conda.yml", "conda.yaml"
            ],
            DependencyFileType.PACKAGE_JSON: [
                "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"
            ],
            DependencyFileType.SETUP_PY: [
                "setup.py", "setup.cfg", "pyproject.toml"
            ],
            DependencyFileType.PIPFILE: [
                "Pipfile", "Pipfile.lock", "poetry.lock"
            ],
            DependencyFileType.DOCKERFILE: [
                "Dockerfile", "dockerfile", "Dockerfile.dev", "Dockerfile.prod",
                "docker-compose.yml", "docker-compose.yaml"
            ],
            DependencyFileType.MAKEFILE: [
                "Makefile", "makefile", "CMakeLists.txt", "CMakeLists"
            ]
        }
        
        # File extensions to search
        self.search_extensions = {
            '.txt', '.yml', '.yaml', '.json', '.py', '.cfg', '.toml',
            '.lock', '.in', 'Dockerfile', 'Makefile', 'CMakeLists.txt'
        }
        
        # Directories to ignore
        self.ignore_directories = {
            '.git', '.svn', '.hg', '__pycache__', 'node_modules', 'venv', 'env',
            '.venv', '.env', 'build', 'dist', '.pytest_cache', '.mypy_cache',
            '.coverage', 'htmlcov', '.tox', '.eggs', '*.egg-info', '.idea',
            '.vscode', '.DS_Store', 'Thumbs.db'
        }
    
    def find_dependencies(self, app_path: str) -> DependencySearchResult:
        """
        Find all dependency files in an application directory.
        
        Args:
            app_path: Path to the application directory
            
        Returns:
            DependencySearchResult: Complete search results
        """
        start_time = time.time()
        
        result = DependencySearchResult(
            app_path=app_path,
            total_files_found=0
        )
        
        try:
            if not os.path.exists(app_path) or not os.path.isdir(app_path):
                result.errors.append(f"App path does not exist or is not a directory: {app_path}")
                return result
            
            # Search for dependency files
            dependency_files = self._search_dependency_files(app_path)
            result.dependency_files = dependency_files
            result.total_files_found = len(dependency_files)
            
            # Analyze each dependency file
            for dep_file in dependency_files:
                self._analyze_dependency_file(dep_file)
            
            # Calculate search time
            result.search_time = time.time() - start_time
            
            # Generate metadata
            result.metadata = self._generate_search_metadata(result)
            
            return result
        
        except Exception as e:
            result.errors.append(f"Error during dependency search: {str(e)}")
            result.search_time = time.time() - start_time
            return result
    
    def _search_dependency_files(self, app_path: str) -> List[DependencyFile]:
        """
        Search for dependency files in the application directory.
        
        Args:
            app_path: Path to the application directory
            
        Returns:
            List of found dependency files
        """
        dependency_files = []
        
        try:
            for root, dirs, files in os.walk(app_path):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not self._should_ignore_directory(d)]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, app_path)
                    
                    # Check if file matches dependency patterns
                    file_type = self._identify_dependency_file_type(file)
                    
                    if file_type != DependencyFileType.UNKNOWN:
                        # Get file information
                        try:
                            stat_info = os.stat(file_path)
                            file_size = stat_info.st_size
                            last_modified = stat_info.st_mtime
                            
                            # Read content preview
                            content_preview = self._read_content_preview(file_path)
                            
                            dependency_file = DependencyFile(
                                file_type=file_type,
                                file_path=file_path,
                                relative_path=relative_path,
                                file_size=file_size,
                                last_modified=last_modified,
                                content_preview=content_preview
                            )
                            
                            dependency_files.append(dependency_file)
                        
                        except Exception as e:
                            # Skip files that can't be read
                            continue
        
        except Exception as e:
            # Handle permission errors or other issues
            pass
        
        return dependency_files
    
    def _should_ignore_directory(self, dir_name: str) -> bool:
        """
        Check if directory should be ignored.
        
        Args:
            dir_name: Directory name to check
            
        Returns:
            True if directory should be ignored
        """
        return dir_name in self.ignore_directories or dir_name.startswith('.')
    
    def _identify_dependency_file_type(self, filename: str) -> DependencyFileType:
        """
        Identify the type of dependency file.
        
        Args:
            filename: Name of the file
            
        Returns:
            DependencyFileType: Type of dependency file
        """
        filename_lower = filename.lower()
        
        # Check against all patterns
        for file_type, patterns in self.dependency_patterns.items():
            for pattern in patterns:
                if filename_lower == pattern.lower():
                    return file_type
        
        # Check for specific extensions
        if filename_lower.endswith('.txt') and 'requirements' in filename_lower:
            return DependencyFileType.REQUIREMENTS_TXT
        
        if filename_lower.endswith(('.yml', '.yaml')) and 'environment' in filename_lower:
            return DependencyFileType.ENVIRONMENT_YML
        
        if filename_lower == 'package.json':
            return DependencyFileType.PACKAGE_JSON
        
        if filename_lower == 'setup.py':
            return DependencyFileType.SETUP_PY
        
        if filename_lower == 'pyproject.toml':
            return DependencyFileType.SETUP_PY
        
        if filename_lower == 'pipfile':
            return DependencyFileType.PIPFILE
        
        if filename_lower == 'dockerfile':
            return DependencyFileType.DOCKERFILE
        
        if filename_lower == 'makefile':
            return DependencyFileType.MAKEFILE
        
        return DependencyFileType.UNKNOWN
    
    def _read_content_preview(self, file_path: str, max_lines: int = 20) -> str:
        """
        Read a preview of the file content.
        
        Args:
            file_path: Path to the file
            max_lines: Maximum number of lines to read
            
        Returns:
            Content preview string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip())
                
                return '\n'.join(lines)
        
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= max_lines:
                            break
                        lines.append(line.rstrip())
                    
                    return '\n'.join(lines)
            except:
                return ""
        
        except Exception:
            return ""
    
    def _analyze_dependency_file(self, dep_file: DependencyFile):
        """
        Analyze a dependency file for additional information.
        
        Args:
            dep_file: Dependency file to analyze
        """
        try:
            content = dep_file.content_preview
            
            if dep_file.file_type in [DependencyFileType.REQUIREMENTS_TXT, DependencyFileType.REQUIREMENTS_DEV_TXT]:
                self._analyze_requirements_file(dep_file, content)
            
            elif dep_file.file_type in [DependencyFileType.ENVIRONMENT_YML, DependencyFileType.ENVIRONMENT_YAML]:
                self._analyze_environment_file(dep_file, content)
            
            elif dep_file.file_type == DependencyFileType.PACKAGE_JSON:
                self._analyze_package_json_file(dep_file, content)
            
            elif dep_file.file_type == DependencyFileType.SETUP_PY:
                self._analyze_setup_py_file(dep_file, content)
            
            elif dep_file.file_type == DependencyFileType.PIPFILE:
                self._analyze_pipfile(dep_file, content)
            
            elif dep_file.file_type == DependencyFileType.DOCKERFILE:
                self._analyze_dockerfile(dep_file, content)
        
        except Exception as e:
            dep_file.metadata['analysis_error'] = str(e)
    
    def _analyze_requirements_file(self, dep_file: DependencyFile, content: str):
        """Analyze requirements.txt file."""
        try:
            lines = content.split('\n')
            dependencies = []
            has_version_pins = False
            has_dev_dependencies = False
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    dependencies.append(line)
                    
                    # Check for version pins
                    if any(op in line for op in ['==', '>=', '<=', '>', '<', '~=', '!=']):
                        has_version_pins = True
                    
                    # Check for dev dependencies
                    if line.startswith('-r') or 'dev' in line.lower():
                        has_dev_dependencies = True
            
            dep_file.dependency_count = len(dependencies)
            dep_file.has_version_pins = has_version_pins
            dep_file.has_dev_dependencies = has_dev_dependencies
            dep_file.metadata['dependencies'] = dependencies
        
        except Exception as e:
            dep_file.metadata['analysis_error'] = str(e)
    
    def _analyze_environment_file(self, dep_file: DependencyFile, content: str):
        """Analyze environment.yml file."""
        try:
            lines = content.split('\n')
            dependencies = []
            has_version_pins = False
            has_dev_dependencies = False
            
            in_dependencies = False
            for line in lines:
                line = line.strip()
                
                if line.startswith('dependencies:'):
                    in_dependencies = True
                    continue
                
                if in_dependencies:
                    if line.startswith('- ') and not line.startswith('- pip:'):
                        dep = line[2:].strip()
                        dependencies.append(dep)
                        
                        # Check for version pins
                        if any(op in dep for op in ['=', '>=', '<=', '>', '<']):
                            has_version_pins = True
                    
                    elif line and not line.startswith(' ') and not line.startswith('-'):
                        # End of dependencies section
                        break
            
            dep_file.dependency_count = len(dependencies)
            dep_file.has_version_pins = has_version_pins
            dep_file.has_dev_dependencies = has_dev_dependencies
            dep_file.metadata['dependencies'] = dependencies
        
        except Exception as e:
            dep_file.metadata['analysis_error'] = str(e)
    
    def _analyze_package_json_file(self, dep_file: DependencyFile, content: str):
        """Analyze package.json file."""
        try:
            data = json.loads(content)
            
            dependencies = data.get('dependencies', {})
            dev_dependencies = data.get('devDependencies', {})
            peer_dependencies = data.get('peerDependencies', {})
            
            total_deps = len(dependencies) + len(dev_dependencies) + len(peer_dependencies)
            
            dep_file.dependency_count = total_deps
            dep_file.has_dev_dependencies = len(dev_dependencies) > 0
            dep_file.has_version_pins = True  # npm always has version pins
            
            dep_file.metadata.update({
                'dependencies': list(dependencies.keys()),
                'dev_dependencies': list(dev_dependencies.keys()),
                'peer_dependencies': list(peer_dependencies.keys()),
                'scripts': data.get('scripts', {}),
                'engines': data.get('engines', {})
            })
        
        except Exception as e:
            dep_file.metadata['analysis_error'] = str(e)
    
    def _analyze_setup_py_file(self, dep_file: DependencyFile, content: str):
        """Analyze setup.py file."""
        try:
            # Look for install_requires
            install_requires_pattern = r'install_requires\s*=\s*\[(.*?)\]'
            match = re.search(install_requires_pattern, content, re.DOTALL)
            
            dependencies = []
            if match:
                requires_content = match.group(1)
                # Simple parsing of the requirements list
                for line in requires_content.split(','):
                    line = line.strip().strip('"\'')
                    if line:
                        dependencies.append(line)
            
            dep_file.dependency_count = len(dependencies)
            dep_file.has_version_pins = any(op in dep for dep in dependencies for op in ['==', '>=', '<=', '>', '<'])
            dep_file.metadata['dependencies'] = dependencies
        
        except Exception as e:
            dep_file.metadata['analysis_error'] = str(e)
    
    def _analyze_pipfile(self, dep_file: DependencyFile, content: str):
        """Analyze Pipfile."""
        try:
            # Simple analysis for Pipfile
            lines = content.split('\n')
            dependencies = []
            has_dev_dependencies = False
            
            in_packages = False
            in_dev_packages = False
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('[packages]'):
                    in_packages = True
                    in_dev_packages = False
                    continue
                
                if line.startswith('[dev-packages]'):
                    in_dev_packages = True
                    in_packages = False
                    has_dev_dependencies = True
                    continue
                
                if line.startswith('[') and not line.startswith('[packages]') and not line.startswith('[dev-packages]'):
                    in_packages = False
                    in_dev_packages = False
                    continue
                
                if (in_packages or in_dev_packages) and line and not line.startswith('#'):
                    if '=' in line:
                        dep_name = line.split('=')[0].strip()
                        dependencies.append(dep_name)
            
            dep_file.dependency_count = len(dependencies)
            dep_file.has_dev_dependencies = has_dev_dependencies
            dep_file.metadata['dependencies'] = dependencies
        
        except Exception as e:
            dep_file.metadata['analysis_error'] = str(e)
    
    def _analyze_dockerfile(self, dep_file: DependencyFile, content: str):
        """Analyze Dockerfile."""
        try:
            lines = content.split('\n')
            dependencies = []
            
            for line in lines:
                line = line.strip().upper()
                
                # Look for package installation commands
                if line.startswith('RUN'):
                    if any(cmd in line for cmd in ['APT', 'YUM', 'DNF', 'BREW', 'PIP', 'CONDA', 'NPM']):
                        # Extract package names (simplified)
                        if 'APT' in line:
                            dependencies.append('system_packages')
                        if 'PIP' in line:
                            dependencies.append('python_packages')
                        if 'CONDA' in line:
                            dependencies.append('conda_packages')
                        if 'NPM' in line:
                            dependencies.append('node_packages')
            
            dep_file.dependency_count = len(dependencies)
            dep_file.metadata['dependencies'] = dependencies
        
        except Exception as e:
            dep_file.metadata['analysis_error'] = str(e)
    
    def _generate_search_metadata(self, result: DependencySearchResult) -> Dict[str, Any]:
        """
        Generate metadata for the search result.
        
        Args:
            result: Search result to generate metadata for
            
        Returns:
            Dictionary of metadata
        """
        metadata = {
            'total_dependency_files': len(result.dependency_files),
            'file_types_found': list(set(df.file_type.value for df in result.dependency_files)),
            'total_dependencies': sum(df.dependency_count for df in result.dependency_files),
            'files_with_version_pins': sum(1 for df in result.dependency_files if df.has_version_pins),
            'files_with_dev_dependencies': sum(1 for df in result.dependency_files if df.has_dev_dependencies),
            'search_time_seconds': result.search_time,
            'errors_count': len(result.errors)
        }
        
        # Add file type breakdown
        file_type_breakdown = {}
        for dep_file in result.dependency_files:
            file_type = dep_file.file_type.value
            if file_type not in file_type_breakdown:
                file_type_breakdown[file_type] = 0
            file_type_breakdown[file_type] += 1
        
        metadata['file_type_breakdown'] = file_type_breakdown
        
        return metadata
    
    def get_dependency_summary(self, result: DependencySearchResult) -> Dict[str, Any]:
        """
        Get a summary of dependency findings.
        
        Args:
            result: Search result to summarize
            
        Returns:
            Dictionary containing summary information
        """
        summary = {
            'app_path': result.app_path,
            'total_files_found': result.total_files_found,
            'search_time': result.search_time,
            'has_errors': len(result.errors) > 0,
            'errors': result.errors,
            'dependency_files': []
        }
        
        for dep_file in result.dependency_files:
            file_summary = {
                'type': dep_file.file_type.value,
                'path': dep_file.relative_path,
                'size': dep_file.file_size,
                'dependencies_count': dep_file.dependency_count,
                'has_version_pins': dep_file.has_version_pins,
                'has_dev_dependencies': dep_file.has_dev_dependencies
            }
            summary['dependency_files'].append(file_summary)
        
        return summary


def main():
    """Main function for testing dependency finder."""
    print("🧪 Testing Dependency Finder")
    print("=" * 50)
    
    # Initialize finder
    finder = DependencyFinder()
    
    # Test with a sample directory
    test_path = "/tmp/test_deps_app"
    os.makedirs(test_path, exist_ok=True)
    
    # Create test files
    test_files = {
        "requirements.txt": "torch>=1.9.0\nnumpy>=1.21.0\nopencv-python>=4.5.0",
        "environment.yml": "name: test_env\ndependencies:\n  - python=3.9\n  - pip\n  - pip:\n    - transformers",
        "package.json": '{"name": "test-app", "dependencies": {"express": "^4.18.0"}, "devDependencies": {"nodemon": "^2.0.0"}}',
        "setup.py": "from setuptools import setup\nsetup(name='test', install_requires=['requests', 'numpy'])",
        "Dockerfile": "FROM python:3.9\nRUN pip install torch numpy\nRUN apt-get update && apt-get install -y ffmpeg"
    }
    
    for filename, content in test_files.items():
        with open(os.path.join(test_path, filename), 'w') as f:
            f.write(content)
    
    # Test dependency finding
    print("\n🔍 Testing dependency file finding...")
    result = finder.find_dependencies(test_path)
    
    print(f"✅ Total files found: {result.total_files_found}")
    print(f"✅ Search time: {result.search_time:.3f}s")
    print(f"✅ Errors: {len(result.errors)}")
    
    if result.errors:
        print(f"   Errors: {', '.join(result.errors)}")
    
    print(f"\n📁 Dependency files found:")
    for dep_file in result.dependency_files:
        print(f"   {dep_file.file_type.value}: {dep_file.relative_path}")
        print(f"     Dependencies: {dep_file.dependency_count}")
        print(f"     Version pins: {dep_file.has_version_pins}")
        print(f"     Dev deps: {dep_file.has_dev_dependencies}")
    
    # Test summary
    print("\n📊 Testing dependency summary...")
    summary = finder.get_dependency_summary(result)
    print(f"✅ Summary generated: {len(summary['dependency_files'])} files")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_path, ignore_errors=True)
    
    return True


if __name__ == "__main__":
    import time
    main()