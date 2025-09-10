#!/usr/bin/env python3
"""
PinokioCloud Installer Detector

This module detects the installation method used by Pinokio applications.
It identifies whether an app uses install.js, install.json, requirements.txt,
setup.py, or other installation methods.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class InstallerType(Enum):
    """Enumeration of installer types."""
    JAVASCRIPT = "javascript"
    JSON = "json"
    REQUIREMENTS_TXT = "requirements_txt"
    SETUP_PY = "setup_py"
    PACKAGE_JSON = "package_json"
    ENVIRONMENT_YML = "environment_yml"
    DOCKERFILE = "dockerfile"
    SHELL_SCRIPT = "shell_script"
    PYTHON_SCRIPT = "python_script"
    UNKNOWN = "unknown"


@dataclass
class InstallerInfo:
    """Information about an application's installer."""
    installer_type: InstallerType
    installer_path: str
    installer_content: str
    dependencies: List[str] = field(default_factory=list)
    install_commands: List[str] = field(default_factory=list)
    python_version: Optional[str] = None
    node_version: Optional[str] = None
    system_requirements: List[str] = field(default_factory=list)
    custom_installer: bool = False
    has_venv_creation: bool = False
    has_conda_creation: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class InstallerDetector:
    """
    Detects installation methods for Pinokio applications.
    
    Analyzes application directories to determine:
    - Type of installer (JS, JSON, requirements.txt, etc.)
    - Installation commands and dependencies
    - Python/Node version requirements
    - System requirements
    - Virtual environment creation
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the installer detector.
        
        Args:
            base_path: Base path for detection
        """
        self.base_path = base_path
        self.installer_patterns = {
            InstallerType.JAVASCRIPT: ["install.js", "installer.js", "setup.js"],
            InstallerType.JSON: ["install.json", "installer.json", "setup.json"],
            InstallerType.REQUIREMENTS_TXT: ["requirements.txt", "requirements-dev.txt"],
            InstallerType.SETUP_PY: ["setup.py"],
            InstallerType.PACKAGE_JSON: ["package.json"],
            InstallerType.ENVIRONMENT_YML: ["environment.yml", "environment.yaml"],
            InstallerType.DOCKERFILE: ["Dockerfile", "dockerfile"],
            InstallerType.SHELL_SCRIPT: ["install.sh", "setup.sh", "install.bat", "setup.bat"],
            InstallerType.PYTHON_SCRIPT: ["install.py", "setup.py", "installer.py"]
        }
    
    def detect_installer(self, app_path: str) -> InstallerInfo:
        """
        Detect the installer method for an application.
        
        Args:
            app_path: Path to the application directory
            
        Returns:
            InstallerInfo: Information about the installer
        """
        try:
            if not os.path.exists(app_path) or not os.path.isdir(app_path):
                return InstallerInfo(
                    installer_type=InstallerType.UNKNOWN,
                    installer_path="",
                    installer_content=""
                )
            
            # Search for installer files
            installer_files = self._find_installer_files(app_path)
            
            if not installer_files:
                return InstallerInfo(
                    installer_type=InstallerType.UNKNOWN,
                    installer_path="",
                    installer_content=""
                )
            
            # Analyze the primary installer
            primary_installer = installer_files[0]
            installer_type = primary_installer["type"]
            installer_path = primary_installer["path"]
            
            # Read installer content
            installer_content = self._read_installer_content(installer_path)
            
            # Analyze installer content
            dependencies = self._extract_dependencies(installer_content, installer_type)
            install_commands = self._extract_install_commands(installer_content, installer_type)
            python_version = self._extract_python_version(installer_content, installer_type)
            node_version = self._extract_node_version(installer_content, installer_type)
            system_requirements = self._extract_system_requirements(installer_content, installer_type)
            
            # Check for virtual environment creation
            has_venv_creation = self._check_venv_creation(installer_content, installer_type)
            has_conda_creation = self._check_conda_creation(installer_content, installer_type)
            
            # Check if it's a custom installer
            custom_installer = self._is_custom_installer(installer_content, installer_type)
            
            return InstallerInfo(
                installer_type=installer_type,
                installer_path=installer_path,
                installer_content=installer_content,
                dependencies=dependencies,
                install_commands=install_commands,
                python_version=python_version,
                node_version=node_version,
                system_requirements=system_requirements,
                custom_installer=custom_installer,
                has_venv_creation=has_venv_creation,
                has_conda_creation=has_conda_creation,
                metadata={
                    "all_installer_files": installer_files,
                    "installer_size": len(installer_content),
                    "has_multiple_installers": len(installer_files) > 1
                }
            )
        
        except Exception as e:
            return InstallerInfo(
                installer_type=InstallerType.UNKNOWN,
                installer_path="",
                installer_content="",
                metadata={"error": str(e)}
            )
    
    def _find_installer_files(self, app_path: str) -> List[Dict[str, Any]]:
        """
        Find all installer files in the application directory.
        
        Args:
            app_path: Path to the application directory
            
        Returns:
            List of installer file information
        """
        installer_files = []
        
        try:
            for root, dirs, files in os.walk(app_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, app_path)
                    
                    # Check against installer patterns
                    for installer_type, patterns in self.installer_patterns.items():
                        for pattern in patterns:
                            if file.lower() == pattern.lower():
                                installer_files.append({
                                    "type": installer_type,
                                    "path": file_path,
                                    "relative_path": relative_path,
                                    "filename": file
                                })
                                break
                
                # Don't search in hidden directories or common ignore directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', 'env']]
        
        except Exception as e:
            pass
        
        # Sort by priority (JavaScript and JSON installers first)
        priority_order = [
            InstallerType.JAVASCRIPT,
            InstallerType.JSON,
            InstallerType.REQUIREMENTS_TXT,
            InstallerType.SETUP_PY,
            InstallerType.PACKAGE_JSON,
            InstallerType.ENVIRONMENT_YML,
            InstallerType.DOCKERFILE,
            InstallerType.SHELL_SCRIPT,
            InstallerType.PYTHON_SCRIPT
        ]
        
        installer_files.sort(key=lambda x: priority_order.index(x["type"]) if x["type"] in priority_order else 999)
        
        return installer_files
    
    def _read_installer_content(self, installer_path: str) -> str:
        """
        Read the content of an installer file.
        
        Args:
            installer_path: Path to the installer file
            
        Returns:
            Content of the installer file
        """
        try:
            with open(installer_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(installer_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except:
                return ""
        except Exception:
            return ""
    
    def _extract_dependencies(self, content: str, installer_type: InstallerType) -> List[str]:
        """
        Extract dependencies from installer content.
        
        Args:
            content: Installer content
            installer_type: Type of installer
            
        Returns:
            List of dependencies
        """
        dependencies = []
        
        try:
            if installer_type == InstallerType.REQUIREMENTS_TXT:
                # Parse requirements.txt format
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Remove version specifiers for now
                        dep = re.split(r'[>=<!=]', line)[0].strip()
                        if dep:
                            dependencies.append(dep)
            
            elif installer_type == InstallerType.PACKAGE_JSON:
                # Parse package.json
                try:
                    data = json.loads(content)
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})
                    all_deps = {**deps, **dev_deps}
                    dependencies = list(all_deps.keys())
                except:
                    pass
            
            elif installer_type == InstallerType.ENVIRONMENT_yml:
                # Parse environment.yml
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('- ') and not line.startswith('- pip:'):
                        dep = line[2:].strip()
                        if dep:
                            dependencies.append(dep)
            
            elif installer_type in [InstallerType.JAVASCRIPT, InstallerType.PYTHON_SCRIPT]:
                # Extract pip install commands
                pip_pattern = r'pip\s+install\s+([^\s\n]+)'
                matches = re.findall(pip_pattern, content, re.IGNORECASE)
                dependencies.extend(matches)
                
                # Extract npm install commands
                npm_pattern = r'npm\s+install\s+([^\s\n]+)'
                matches = re.findall(npm_pattern, content, re.IGNORECASE)
                dependencies.extend(matches)
            
            elif installer_type == InstallerType.SETUP_PY:
                # Extract install_requires
                requires_pattern = r'install_requires\s*=\s*\[(.*?)\]'
                match = re.search(requires_pattern, content, re.DOTALL)
                if match:
                    requires_content = match.group(1)
                    # Simple parsing of the requirements list
                    for line in requires_content.split(','):
                        line = line.strip().strip('"\'')
                        if line:
                            dependencies.append(line)
        
        except Exception as e:
            pass
        
        return list(set(dependencies))  # Remove duplicates
    
    def _extract_install_commands(self, content: str, installer_type: InstallerType) -> List[str]:
        """
        Extract installation commands from installer content.
        
        Args:
            content: Installer content
            installer_type: Type of installer
            
        Returns:
            List of installation commands
        """
        commands = []
        
        try:
            if installer_type in [InstallerType.JAVASCRIPT, InstallerType.PYTHON_SCRIPT]:
                # Extract shell commands
                command_patterns = [
                    r'exec\s*\(\s*["\']([^"\']+)["\']',
                    r'shell\.run\s*\(\s*["\']([^"\']+)["\']',
                    r'subprocess\.run\s*\(\s*\[([^\]]+)\]',
                    r'os\.system\s*\(\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in command_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    commands.extend(matches)
            
            elif installer_type == InstallerType.SHELL_SCRIPT:
                # Extract commands from shell script
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('echo'):
                        commands.append(line)
            
            elif installer_type == InstallerType.JSON:
                # Extract commands from JSON installer
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        # Look for common command fields
                        for key in ['commands', 'install', 'setup', 'run']:
                            if key in data:
                                if isinstance(data[key], list):
                                    commands.extend(data[key])
                                elif isinstance(data[key], str):
                                    commands.append(data[key])
                except:
                    pass
        
        except Exception as e:
            pass
        
        return commands
    
    def _extract_python_version(self, content: str, installer_type: InstallerType) -> Optional[str]:
        """
        Extract Python version requirement from installer content.
        
        Args:
            content: Installer content
            installer_type: Type of installer
            
        Returns:
            Python version requirement or None
        """
        try:
            # Common Python version patterns
            patterns = [
                r'python\s*([0-9]+\.[0-9]+)',
                r'python_version\s*=\s*["\']([^"\']+)["\']',
                r'python_requires\s*=\s*["\']([^"\']+)["\']',
                r'python\s*>=?\s*([0-9]+\.[0-9]+)',
                r'python\s*==\s*([0-9]+\.[0-9]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        except Exception as e:
            pass
        
        return None
    
    def _extract_node_version(self, content: str, installer_type: InstallerType) -> Optional[str]:
        """
        Extract Node.js version requirement from installer content.
        
        Args:
            content: Installer content
            installer_type: Type of installer
            
        Returns:
            Node.js version requirement or None
        """
        try:
            # Common Node.js version patterns
            patterns = [
                r'node\s*([0-9]+\.[0-9]+)',
                r'node_version\s*=\s*["\']([^"\']+)["\']',
                r'engines.*?node.*?["\']([^"\']+)["\']',
                r'node\s*>=?\s*([0-9]+\.[0-9]+)',
                r'node\s*==\s*([0-9]+\.[0-9]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        except Exception as e:
            pass
        
        return None
    
    def _extract_system_requirements(self, content: str, installer_type: InstallerType) -> List[str]:
        """
        Extract system requirements from installer content.
        
        Args:
            content: Installer content
            installer_type: Type of installer
            
        Returns:
            List of system requirements
        """
        requirements = []
        
        try:
            # Common system requirement patterns
            patterns = [
                r'apt\s+install\s+([^\s\n]+)',
                r'yum\s+install\s+([^\s\n]+)',
                r'brew\s+install\s+([^\s\n]+)',
                r'apt-get\s+install\s+([^\s\n]+)',
                r'dnf\s+install\s+([^\s\n]+)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                requirements.extend(matches)
        
        except Exception as e:
            pass
        
        return list(set(requirements))  # Remove duplicates
    
    def _check_venv_creation(self, content: str, installer_type: InstallerType) -> bool:
        """
        Check if installer creates a virtual environment.
        
        Args:
            content: Installer content
            installer_type: Type of installer
            
        Returns:
            True if venv creation is detected
        """
        try:
            venv_patterns = [
                r'python\s+-m\s+venv',
                r'virtualenv',
                r'venv\s+create',
                r'python\s+-m\s+virtualenv'
            ]
            
            for pattern in venv_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
        
        except Exception as e:
            pass
        
        return False
    
    def _check_conda_creation(self, content: str, installer_type: InstallerType) -> bool:
        """
        Check if installer creates a conda environment.
        
        Args:
            content: Installer content
            installer_type: Type of installer
            
        Returns:
            True if conda creation is detected
        """
        try:
            conda_patterns = [
                r'conda\s+create',
                r'conda\s+env\s+create',
                r'conda\s+install',
                r'mamba\s+create',
                r'mamba\s+install'
            ]
            
            for pattern in conda_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
        
        except Exception as e:
            pass
        
        return False
    
    def _is_custom_installer(self, content: str, installer_type: InstallerType) -> bool:
        """
        Check if installer is a custom implementation.
        
        Args:
            content: Installer content
            installer_type: Type of installer
            
        Returns:
            True if custom installer is detected
        """
        try:
            # Check for custom installer indicators
            custom_indicators = [
                r'pinokio\.',
                r'fs\.',
                r'shell\.',
                r'custom',
                r'installer',
                r'setup'
            ]
            
            indicator_count = 0
            for pattern in custom_indicators:
                if re.search(pattern, content, re.IGNORECASE):
                    indicator_count += 1
            
            # If multiple indicators found, likely custom
            return indicator_count >= 2
        
        except Exception as e:
            pass
        
        return False


def main():
    """Main function for testing installer detector."""
    print("🧪 Testing Installer Detector")
    print("=" * 50)
    
    # Initialize detector
    detector = InstallerDetector()
    
    # Test with a sample directory
    test_path = "/tmp/test_app"
    os.makedirs(test_path, exist_ok=True)
    
    # Create test requirements.txt
    requirements_content = """
torch>=1.9.0
numpy>=1.21.0
opencv-python>=4.5.0
# This is a comment
requests>=2.25.0
"""
    
    with open(os.path.join(test_path, "requirements.txt"), 'w') as f:
        f.write(requirements_content)
    
    # Create test install.js
    install_js_content = """
const fs = require('fs');
const { exec } = require('child_process');

// Install Python dependencies
exec('pip install torch numpy opencv-python', (error, stdout, stderr) => {
    if (error) {
        console.error('Installation failed:', error);
        return;
    }
    console.log('Installation completed');
});

// Create virtual environment
exec('python -m venv venv', (error, stdout, stderr) => {
    if (error) {
        console.error('Venv creation failed:', error);
        return;
    }
    console.log('Virtual environment created');
});
"""
    
    with open(os.path.join(test_path, "install.js"), 'w') as f:
        f.write(install_js_content)
    
    # Test detection
    print("\n📦 Testing installer detection...")
    result = detector.detect_installer(test_path)
    
    print(f"✅ Installer type: {result.installer_type.value}")
    print(f"✅ Installer path: {result.installer_path}")
    print(f"✅ Dependencies: {len(result.dependencies)} found")
    print(f"✅ Install commands: {len(result.install_commands)} found")
    print(f"✅ Python version: {result.python_version}")
    print(f"✅ Has venv creation: {result.has_venv_creation}")
    print(f"✅ Custom installer: {result.custom_installer}")
    
    if result.dependencies:
        print(f"   Dependencies: {', '.join(result.dependencies[:5])}{'...' if len(result.dependencies) > 5 else ''}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_path, ignore_errors=True)
    
    return True


if __name__ == "__main__":
    main()