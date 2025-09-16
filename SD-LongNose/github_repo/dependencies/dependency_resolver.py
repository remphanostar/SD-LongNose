#!/usr/bin/env python3
"""
PinokioCloud Dependency Resolver

This module resolves conflicts between different dependency systems and package managers.
It provides comprehensive dependency conflict resolution including version conflicts,
package manager conflicts, and system-level dependency conflicts.

Author: PinokioCloud Development Team
Version: 1.0.0
"""

import os
import sys
import json
import re
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# Import dependency managers
from .pip_manager import PipManager, PipPackage, PipInstallStatus
from .conda_manager import CondaManager, CondaPackage, CondaInstallStatus
from .npm_manager import NpmManager, NpmPackage, NpmInstallStatus
from .system_manager import SystemManager, SystemPackage, SystemInstallStatus


class ConflictType(Enum):
    """Enumeration of conflict types."""
    VERSION_CONFLICT = "version_conflict"
    PACKAGE_MANAGER_CONFLICT = "package_manager_conflict"
    SYSTEM_CONFLICT = "system_conflict"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    PLATFORM_CONFLICT = "platform_conflict"
    UNKNOWN = "unknown"


class ResolutionStrategy(Enum):
    """Enumeration of resolution strategies."""
    PRIORITIZE_PIP = "prioritize_pip"
    PRIORITIZE_CONDA = "prioritize_conda"
    PRIORITIZE_NPM = "prioritize_npm"
    PRIORITIZE_SYSTEM = "prioritize_system"
    USE_LATEST = "use_latest"
    USE_SPECIFIC = "use_specific"
    SKIP_CONFLICTING = "skip_conflicting"
    MANUAL_RESOLUTION = "manual_resolution"


@dataclass
class DependencyConflict:
    """Information about a dependency conflict."""
    conflict_type: ConflictType
    package_name: str
    conflicting_versions: List[str] = field(default_factory=list)
    conflicting_managers: List[str] = field(default_factory=list)
    severity: str = "medium"  # low, medium, high, critical
    description: str = ""
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolutionResult:
    """Result of dependency conflict resolution."""
    success: bool
    conflicts_found: List[DependencyConflict] = field(default_factory=list)
    conflicts_resolved: List[DependencyConflict] = field(default_factory=list)
    conflicts_remaining: List[DependencyConflict] = field(default_factory=list)
    resolution_time: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DependencyResolver:
    """
    Resolves conflicts between different dependency systems and package managers.
    
    Provides comprehensive dependency conflict resolution including:
    - Version conflict detection and resolution
    - Package manager conflict resolution
    - System-level dependency conflict resolution
    - Platform-specific conflict resolution
    - Automated and manual resolution strategies
    """
    
    def __init__(self, base_path: str = "/workspace"):
        """
        Initialize the dependency resolver.
        
        Args:
            base_path: Base path for dependency resolution
        """
        self.base_path = base_path
        
        # Initialize dependency managers
        self.pip_manager = PipManager(base_path)
        self.conda_manager = CondaManager(base_path)
        self.npm_manager = NpmManager(base_path)
        self.system_manager = SystemManager(base_path)
        
        # Resolution strategies
        self.resolution_strategies = {
            ConflictType.VERSION_CONFLICT: [
                ResolutionStrategy.USE_LATEST,
                ResolutionStrategy.USE_SPECIFIC,
                ResolutionStrategy.PRIORITIZE_PIP,
                ResolutionStrategy.PRIORITIZE_CONDA
            ],
            ConflictType.PACKAGE_MANAGER_CONFLICT: [
                ResolutionStrategy.PRIORITIZE_PIP,
                ResolutionStrategy.PRIORITIZE_CONDA,
                ResolutionStrategy.PRIORITIZE_NPM,
                ResolutionStrategy.SKIP_CONFLICTING
            ],
            ConflictType.SYSTEM_CONFLICT: [
                ResolutionStrategy.PRIORITIZE_SYSTEM,
                ResolutionStrategy.SKIP_CONFLICTING,
                ResolutionStrategy.MANUAL_RESOLUTION
            ],
            ConflictType.DEPENDENCY_CONFLICT: [
                ResolutionStrategy.USE_LATEST,
                ResolutionStrategy.PRIORITIZE_PIP,
                ResolutionStrategy.MANUAL_RESOLUTION
            ]
        }
        
        # Package manager priorities (higher number = higher priority)
        self.manager_priorities = {
            'pip': 3,
            'conda': 4,
            'npm': 2,
            'system': 1
        }
        
        # Known problematic packages
        self.problematic_packages = {
            'torch': ['tensorflow', 'jax'],
            'tensorflow': ['torch', 'jax'],
            'jax': ['torch', 'tensorflow'],
            'opencv-python': ['opencv-contrib-python'],
            'opencv-contrib-python': ['opencv-python'],
            'flask': ['django', 'fastapi'],
            'django': ['flask', 'fastapi'],
            'fastapi': ['flask', 'django']
        }
        
        self.progress_callback = None
    
    def set_progress_callback(self, callback):
        """Set progress callback function."""
        self.progress_callback = callback
    
    def resolve_conflicts(self, app_path: str, 
                         strategy: Optional[ResolutionStrategy] = None) -> ResolutionResult:
        """
        Resolve all dependency conflicts for an application.
        
        Args:
            app_path: Path to the application
            strategy: Resolution strategy to use (optional)
            
        Returns:
            ResolutionResult: Resolution result
        """
        start_time = time.time()
        
        result = ResolutionResult(
            success=False
        )
        
        try:
            self._update_progress("Starting dependency conflict resolution...")
            
            # Detect conflicts
            conflicts = self._detect_conflicts(app_path)
            result.conflicts_found = conflicts
            
            if not conflicts:
                result.success = True
                result.resolution_time = time.time() - start_time
                self._update_progress("No conflicts detected")
                return result
            
            self._update_progress(f"Found {len(conflicts)} conflicts to resolve")
            
            # Resolve conflicts
            resolved_conflicts = []
            remaining_conflicts = []
            
            for conflict in conflicts:
                self._update_progress(f"Resolving conflict: {conflict.package_name}")
                
                # Use provided strategy or auto-select
                resolution_strategy = strategy or self._select_resolution_strategy(conflict)
                conflict.resolution_strategy = resolution_strategy
                
                # Attempt resolution
                resolution_success = self._resolve_single_conflict(conflict, resolution_strategy)
                
                if resolution_success:
                    conflict.resolved = True
                    resolved_conflicts.append(conflict)
                    self._update_progress(f"Resolved conflict: {conflict.package_name}")
                else:
                    remaining_conflicts.append(conflict)
                    self._update_progress(f"Failed to resolve conflict: {conflict.package_name}")
            
            result.conflicts_resolved = resolved_conflicts
            result.conflicts_remaining = remaining_conflicts
            result.success = len(remaining_conflicts) == 0
            result.resolution_time = time.time() - start_time
            
            self._update_progress(f"Resolution complete: {len(resolved_conflicts)}/{len(conflicts)} conflicts resolved")
            
            return result
        
        except Exception as e:
            result.error_messages.append(f"Error during conflict resolution: {str(e)}")
            result.resolution_time = time.time() - start_time
            return result
    
    def detect_conflicts(self, app_path: str) -> List[DependencyConflict]:
        """
        Detect dependency conflicts in an application.
        
        Args:
            app_path: Path to the application
            
        Returns:
            List of detected conflicts
        """
        return self._detect_conflicts(app_path)
    
    def resolve_version_conflict(self, package_name: str, 
                               versions: List[str],
                               strategy: ResolutionStrategy = ResolutionStrategy.USE_LATEST) -> bool:
        """
        Resolve a version conflict for a specific package.
        
        Args:
            package_name: Name of the package
            versions: List of conflicting versions
            strategy: Resolution strategy to use
            
        Returns:
            bool: True if resolved successfully
        """
        try:
            if strategy == ResolutionStrategy.USE_LATEST:
                # Use the latest version
                latest_version = self._get_latest_version(versions)
                return self._install_specific_version(package_name, latest_version)
            
            elif strategy == ResolutionStrategy.USE_SPECIFIC:
                # Use a specific version (first one)
                return self._install_specific_version(package_name, versions[0])
            
            elif strategy == ResolutionStrategy.PRIORITIZE_PIP:
                # Install via pip
                return self._install_via_pip(package_name)
            
            elif strategy == ResolutionStrategy.PRIORITIZE_CONDA:
                # Install via conda
                return self._install_via_conda(package_name)
            
            else:
                return False
        
        except Exception as e:
            return False
    
    def resolve_package_manager_conflict(self, package_name: str,
                                       managers: List[str],
                                       strategy: ResolutionStrategy = ResolutionStrategy.PRIORITIZE_PIP) -> bool:
        """
        Resolve a package manager conflict for a specific package.
        
        Args:
            package_name: Name of the package
            managers: List of conflicting package managers
            strategy: Resolution strategy to use
            
        Returns:
            bool: True if resolved successfully
        """
        try:
            if strategy == ResolutionStrategy.PRIORITIZE_PIP:
                return self._install_via_pip(package_name)
            
            elif strategy == ResolutionStrategy.PRIORITIZE_CONDA:
                return self._install_via_conda(package_name)
            
            elif strategy == ResolutionStrategy.PRIORITIZE_NPM:
                return self._install_via_npm(package_name)
            
            elif strategy == ResolutionStrategy.PRIORITIZE_SYSTEM:
                return self._install_via_system(package_name)
            
            elif strategy == ResolutionStrategy.SKIP_CONFLICTING:
                # Skip the conflicting package
                return True
            
            else:
                return False
        
        except Exception as e:
            return False
    
    def _detect_conflicts(self, app_path: str) -> List[DependencyConflict]:
        """
        Detect all dependency conflicts in an application.
        
        Args:
            app_path: Path to the application
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        try:
            # Get dependencies from all managers
            pip_deps = self._get_pip_dependencies(app_path)
            conda_deps = self._get_conda_dependencies(app_path)
            npm_deps = self._get_npm_dependencies(app_path)
            system_deps = self._get_system_dependencies(app_path)
            
            # Detect version conflicts
            version_conflicts = self._detect_version_conflicts(pip_deps, conda_deps, npm_deps)
            conflicts.extend(version_conflicts)
            
            # Detect package manager conflicts
            manager_conflicts = self._detect_package_manager_conflicts(pip_deps, conda_deps, npm_deps, system_deps)
            conflicts.extend(manager_conflicts)
            
            # Detect system conflicts
            system_conflicts = self._detect_system_conflicts(system_deps)
            conflicts.extend(system_conflicts)
            
            # Detect dependency conflicts
            dependency_conflicts = self._detect_dependency_conflicts(pip_deps, conda_deps, npm_deps)
            conflicts.extend(dependency_conflicts)
            
            return conflicts
        
        except Exception as e:
            return []
    
    def _get_pip_dependencies(self, app_path: str) -> Dict[str, str]:
        """Get pip dependencies from app path."""
        try:
            # Look for requirements files
            requirements_files = []
            for root, dirs, files in os.walk(app_path):
                for file in files:
                    if file.startswith('requirements') and file.endswith('.txt'):
                        requirements_files.append(os.path.join(root, file))
            
            dependencies = {}
            for req_file in requirements_files:
                with open(req_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '==' in line:
                                name, version = line.split('==', 1)
                                dependencies[name.strip()] = version.strip()
                            elif '>=' in line:
                                name, version = line.split('>=', 1)
                                dependencies[name.strip()] = f">={version.strip()}"
                            else:
                                dependencies[line] = "latest"
            
            return dependencies
        
        except Exception as e:
            return {}
    
    def _get_conda_dependencies(self, app_path: str) -> Dict[str, str]:
        """Get conda dependencies from app path."""
        try:
            # Look for environment files
            environment_files = []
            for root, dirs, files in os.walk(app_path):
                for file in files:
                    if file in ['environment.yml', 'environment.yaml', 'conda.yml', 'conda.yaml']:
                        environment_files.append(os.path.join(root, file))
            
            dependencies = {}
            for env_file in environment_files:
                with open(env_file, 'r') as f:
                    content = f.read()
                    # Simple parsing for conda environment files
                    in_dependencies = False
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('dependencies:'):
                            in_dependencies = True
                            continue
                        if in_dependencies:
                            if line.startswith('- ') and not line.startswith('- pip:'):
                                dep = line[2:].strip()
                                if '=' in dep:
                                    name, version = dep.split('=', 1)
                                    dependencies[name.strip()] = version.strip()
                                else:
                                    dependencies[dep] = "latest"
                            elif line and not line.startswith(' ') and not line.startswith('-'):
                                break
            
            return dependencies
        
        except Exception as e:
            return {}
    
    def _get_npm_dependencies(self, app_path: str) -> Dict[str, str]:
        """Get npm dependencies from app path."""
        try:
            package_json_path = os.path.join(app_path, 'package.json')
            if not os.path.exists(package_json_path):
                return {}
            
            with open(package_json_path, 'r') as f:
                package_config = json.load(f)
            
            dependencies = {}
            deps = package_config.get('dependencies', {})
            dev_deps = package_config.get('devDependencies', {})
            
            dependencies.update(deps)
            dependencies.update(dev_deps)
            
            return dependencies
        
        except Exception as e:
            return {}
    
    def _get_system_dependencies(self, app_path: str) -> Dict[str, str]:
        """Get system dependencies from app path."""
        try:
            # Look for system package references in scripts
            system_deps = {}
            
            for root, dirs, files in os.walk(app_path):
                for file in files:
                    if file.endswith(('.py', '.js', '.sh', '.bat')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                            
                            # Look for system package installation commands
                            patterns = [
                                r'apt\s+install\s+([^\s\n]+)',
                                r'yum\s+install\s+([^\s\n]+)',
                                r'dnf\s+install\s+([^\s\n]+)',
                                r'brew\s+install\s+([^\s\n]+)'
                            ]
                            
                            for pattern in patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    system_deps[match] = "system"
                        
                        except:
                            continue
            
            return system_deps
        
        except Exception as e:
            return {}
    
    def _detect_version_conflicts(self, pip_deps: Dict[str, str], 
                                conda_deps: Dict[str, str], 
                                npm_deps: Dict[str, str]) -> List[DependencyConflict]:
        """Detect version conflicts between package managers."""
        conflicts = []
        
        try:
            # Check for packages present in multiple managers
            all_packages = set(pip_deps.keys()) | set(conda_deps.keys()) | set(npm_deps.keys())
            
            for package in all_packages:
                versions = []
                managers = []
                
                if package in pip_deps:
                    versions.append(f"pip:{pip_deps[package]}")
                    managers.append("pip")
                
                if package in conda_deps:
                    versions.append(f"conda:{conda_deps[package]}")
                    managers.append("conda")
                
                if package in npm_deps:
                    versions.append(f"npm:{npm_deps[package]}")
                    managers.append("npm")
                
                # Check if there are version conflicts
                if len(versions) > 1:
                    # Extract actual versions
                    actual_versions = []
                    for version in versions:
                        if ':' in version:
                            actual_versions.append(version.split(':', 1)[1])
                    
                    # Check if versions are different
                    if len(set(actual_versions)) > 1:
                        conflict = DependencyConflict(
                            conflict_type=ConflictType.VERSION_CONFLICT,
                            package_name=package,
                            conflicting_versions=actual_versions,
                            conflicting_managers=managers,
                            severity=self._assess_conflict_severity(package, actual_versions),
                            description=f"Version conflict for {package}: {', '.join(versions)}"
                        )
                        conflicts.append(conflict)
        
        except Exception as e:
            pass
        
        return conflicts
    
    def _detect_package_manager_conflicts(self, pip_deps: Dict[str, str],
                                        conda_deps: Dict[str, str],
                                        npm_deps: Dict[str, str],
                                        system_deps: Dict[str, str]) -> List[DependencyConflict]:
        """Detect package manager conflicts."""
        conflicts = []
        
        try:
            # Check for packages that should only be installed via one manager
            for package in pip_deps.keys():
                if package in conda_deps and package in self.problematic_packages:
                    conflict = DependencyConflict(
                        conflict_type=ConflictType.PACKAGE_MANAGER_CONFLICT,
                        package_name=package,
                        conflicting_managers=["pip", "conda"],
                        severity="high",
                        description=f"Package {package} should not be installed via both pip and conda"
                    )
                    conflicts.append(conflict)
        
        except Exception as e:
            pass
        
        return conflicts
    
    def _detect_system_conflicts(self, system_deps: Dict[str, str]) -> List[DependencyConflict]:
        """Detect system-level conflicts."""
        conflicts = []
        
        try:
            # Check for conflicting system packages
            for package in system_deps.keys():
                if package in self.problematic_packages:
                    conflicting_packages = self.problematic_packages[package]
                    for conflicting_package in conflicting_packages:
                        if conflicting_package in system_deps:
                            conflict = DependencyConflict(
                                conflict_type=ConflictType.SYSTEM_CONFLICT,
                                package_name=package,
                                conflicting_managers=[package, conflicting_package],
                                severity="medium",
                                description=f"System packages {package} and {conflicting_package} may conflict"
                            )
                            conflicts.append(conflict)
        
        except Exception as e:
            pass
        
        return conflicts
    
    def _detect_dependency_conflicts(self, pip_deps: Dict[str, str],
                                   conda_deps: Dict[str, str],
                                   npm_deps: Dict[str, str]) -> List[DependencyConflict]:
        """Detect dependency conflicts."""
        conflicts = []
        
        try:
            # Check for known problematic package combinations
            all_packages = set(pip_deps.keys()) | set(conda_deps.keys()) | set(npm_deps.keys())
            
            for package in all_packages:
                if package in self.problematic_packages:
                    conflicting_packages = self.problematic_packages[package]
                    for conflicting_package in conflicting_packages:
                        if conflicting_package in all_packages:
                            conflict = DependencyConflict(
                                conflict_type=ConflictType.DEPENDENCY_CONFLICT,
                                package_name=package,
                                conflicting_managers=[package, conflicting_package],
                                severity="high",
                                description=f"Packages {package} and {conflicting_package} are known to conflict"
                            )
                            conflicts.append(conflict)
        
        except Exception as e:
            pass
        
        return conflicts
    
    def _select_resolution_strategy(self, conflict: DependencyConflict) -> ResolutionStrategy:
        """Select the best resolution strategy for a conflict."""
        try:
            strategies = self.resolution_strategies.get(conflict.conflict_type, [])
            
            if not strategies:
                return ResolutionStrategy.MANUAL_RESOLUTION
            
            # Select strategy based on conflict severity and type
            if conflict.severity == "critical":
                return ResolutionStrategy.MANUAL_RESOLUTION
            
            if conflict.conflict_type == ConflictType.VERSION_CONFLICT:
                return ResolutionStrategy.USE_LATEST
            
            if conflict.conflict_type == ConflictType.PACKAGE_MANAGER_CONFLICT:
                # Prioritize based on manager priorities
                if "pip" in conflict.conflicting_managers:
                    return ResolutionStrategy.PRIORITIZE_PIP
                elif "conda" in conflict.conflicting_managers:
                    return ResolutionStrategy.PRIORITIZE_CONDA
                else:
                    return ResolutionStrategy.SKIP_CONFLICTING
            
            return strategies[0]
        
        except Exception as e:
            return ResolutionStrategy.MANUAL_RESOLUTION
    
    def _resolve_single_conflict(self, conflict: DependencyConflict, 
                               strategy: ResolutionStrategy) -> bool:
        """Resolve a single conflict using the specified strategy."""
        try:
            if strategy == ResolutionStrategy.USE_LATEST:
                return self._resolve_with_latest_version(conflict)
            
            elif strategy == ResolutionStrategy.USE_SPECIFIC:
                return self._resolve_with_specific_version(conflict)
            
            elif strategy == ResolutionStrategy.PRIORITIZE_PIP:
                return self._resolve_with_pip(conflict)
            
            elif strategy == ResolutionStrategy.PRIORITIZE_CONDA:
                return self._resolve_with_conda(conflict)
            
            elif strategy == ResolutionStrategy.PRIORITIZE_NPM:
                return self._resolve_with_npm(conflict)
            
            elif strategy == ResolutionStrategy.PRIORITIZE_SYSTEM:
                return self._resolve_with_system(conflict)
            
            elif strategy == ResolutionStrategy.SKIP_CONFLICTING:
                return True  # Skip is always successful
            
            else:
                return False
        
        except Exception as e:
            return False
    
    def _resolve_with_latest_version(self, conflict: DependencyConflict) -> bool:
        """Resolve conflict by using the latest version."""
        try:
            if conflict.conflicting_versions:
                latest_version = self._get_latest_version(conflict.conflicting_versions)
                return self._install_specific_version(conflict.package_name, latest_version)
            return False
        
        except Exception as e:
            return False
    
    def _resolve_with_specific_version(self, conflict: DependencyConflict) -> bool:
        """Resolve conflict by using a specific version."""
        try:
            if conflict.conflicting_versions:
                return self._install_specific_version(conflict.package_name, conflict.conflicting_versions[0])
            return False
        
        except Exception as e:
            return False
    
    def _resolve_with_pip(self, conflict: DependencyConflict) -> bool:
        """Resolve conflict by installing via pip."""
        return self._install_via_pip(conflict.package_name)
    
    def _resolve_with_conda(self, conflict: DependencyConflict) -> bool:
        """Resolve conflict by installing via conda."""
        return self._install_via_conda(conflict.package_name)
    
    def _resolve_with_npm(self, conflict: DependencyConflict) -> bool:
        """Resolve conflict by installing via npm."""
        return self._install_via_npm(conflict.package_name)
    
    def _resolve_with_system(self, conflict: DependencyConflict) -> bool:
        """Resolve conflict by installing via system package manager."""
        return self._install_via_system(conflict.package_name)
    
    def _get_latest_version(self, versions: List[str]) -> str:
        """Get the latest version from a list of versions."""
        try:
            # Simple version comparison (can be enhanced)
            if not versions:
                return "latest"
            
            # Remove version specifiers for comparison
            clean_versions = []
            for version in versions:
                clean_version = re.sub(r'[>=<~!]', '', version)
                clean_versions.append(clean_version)
            
            # Sort versions (simple string sort for now)
            clean_versions.sort(reverse=True)
            return clean_versions[0]
        
        except Exception as e:
            return versions[0] if versions else "latest"
    
    def _install_specific_version(self, package_name: str, version: str) -> bool:
        """Install a specific version of a package."""
        try:
            # Try pip first
            package = self.pip_manager.install_package(f"{package_name}=={version}")
            return package.status == PipInstallStatus.SUCCESS
        
        except Exception as e:
            return False
    
    def _install_via_pip(self, package_name: str) -> bool:
        """Install package via pip."""
        try:
            package = self.pip_manager.install_package(package_name)
            return package.status == PipInstallStatus.SUCCESS
        
        except Exception as e:
            return False
    
    def _install_via_conda(self, package_name: str) -> bool:
        """Install package via conda."""
        try:
            result = self.conda_manager.install_packages("base", [package_name])
            return result.success
        
        except Exception as e:
            return False
    
    def _install_via_npm(self, package_name: str) -> bool:
        """Install package via npm."""
        try:
            package = self.npm_manager.install_package(package_name)
            return package.status == NpmInstallStatus.SUCCESS
        
        except Exception as e:
            return False
    
    def _install_via_system(self, package_name: str) -> bool:
        """Install package via system package manager."""
        try:
            package = self.system_manager.install_package(package_name)
            return package.status == SystemInstallStatus.SUCCESS
        
        except Exception as e:
            return False
    
    def _assess_conflict_severity(self, package_name: str, versions: List[str]) -> str:
        """Assess the severity of a conflict."""
        try:
            # Critical packages
            critical_packages = ['python', 'node', 'npm', 'pip', 'conda']
            if package_name.lower() in critical_packages:
                return "critical"
            
            # High severity packages
            high_severity_packages = ['torch', 'tensorflow', 'numpy', 'pandas']
            if package_name.lower() in high_severity_packages:
                return "high"
            
            # Medium severity packages
            medium_severity_packages = ['opencv', 'pillow', 'requests', 'flask']
            if any(medium_pkg in package_name.lower() for medium_pkg in medium_severity_packages):
                return "medium"
            
            return "low"
        
        except Exception as e:
            return "medium"
    
    def _update_progress(self, message: str):
        """Update progress and call callback if set."""
        if self.progress_callback:
            try:
                self.progress_callback(message)
            except:
                pass


def main():
    """Main function for testing dependency resolver."""
    print("🧪 Testing Dependency Resolver")
    print("=" * 50)
    
    # Initialize resolver
    resolver = DependencyResolver()
    
    # Set up progress callback
    def progress_callback(message):
        print(f"  {message}")
    
    resolver.set_progress_callback(progress_callback)
    
    # Test with a sample app directory
    test_path = "/tmp/test_conflict_app"
    os.makedirs(test_path, exist_ok=True)
    
    # Create conflicting requirements files
    requirements_txt = """
torch==1.9.0
numpy>=1.21.0
opencv-python>=4.5.0
"""
    
    environment_yml = """
name: test_env
dependencies:
  - python=3.9
  - torch=1.10.0
  - numpy=1.22.0
  - pip
  - pip:
    - opencv-python==4.6.0
"""
    
    package_json = {
        "name": "test-app",
        "dependencies": {
            "express": "^4.18.0"
        }
    }
    
    with open(os.path.join(test_path, "requirements.txt"), 'w') as f:
        f.write(requirements_txt)
    
    with open(os.path.join(test_path, "environment.yml"), 'w') as f:
        f.write(environment_yml)
    
    with open(os.path.join(test_path, "package.json"), 'w') as f:
        json.dump(package_json, f, indent=2)
    
    # Test conflict detection
    print("\n🔍 Testing conflict detection...")
    conflicts = resolver.detect_conflicts(test_path)
    
    print(f"✅ Conflicts detected: {len(conflicts)}")
    
    for conflict in conflicts:
        print(f"   - {conflict.package_name}: {conflict.conflict_type.value}")
        print(f"     Severity: {conflict.severity}")
        print(f"     Description: {conflict.description}")
        if conflict.conflicting_versions:
            print(f"     Versions: {', '.join(conflict.conflicting_versions)}")
        if conflict.conflicting_managers:
            print(f"     Managers: {', '.join(conflict.conflicting_managers)}")
    
    # Test conflict resolution
    print("\n🔧 Testing conflict resolution...")
    result = resolver.resolve_conflicts(test_path)
    
    print(f"✅ Resolution success: {result.success}")
    print(f"✅ Conflicts found: {len(result.conflicts_found)}")
    print(f"✅ Conflicts resolved: {len(result.conflicts_resolved)}")
    print(f"✅ Conflicts remaining: {len(result.conflicts_remaining)}")
    print(f"✅ Resolution time: {result.resolution_time:.2f}s")
    
    if result.conflicts_resolved:
        print("   Resolved conflicts:")
        for conflict in result.conflicts_resolved:
            print(f"     - {conflict.package_name}: {conflict.resolution_strategy.value}")
    
    if result.conflicts_remaining:
        print("   Remaining conflicts:")
        for conflict in result.conflicts_remaining:
            print(f"     - {conflict.package_name}: {conflict.description}")
    
    if result.error_messages:
        print("   Errors:")
        for error in result.error_messages:
            print(f"     - {error}")
    
    # Test specific conflict resolution
    print("\n🎯 Testing specific conflict resolution...")
    if conflicts:
        conflict = conflicts[0]
        success = resolver.resolve_version_conflict(
            conflict.package_name,
            conflict.conflicting_versions,
            ResolutionStrategy.USE_LATEST
        )
        print(f"✅ Specific resolution success: {success}")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_path, ignore_errors=True)
    
    return True


if __name__ == "__main__":
    main()