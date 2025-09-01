"""Pinokio Installer Module - Handles downloading and installation
"""

import os
import sys
import subprocess
import requests
import tarfile
import zipfile
import hashlib
import logging
import time
import json
from pathlib import Path
from typing import Optional, Dict, List
from functools import wraps


def retry_on_failure(max_attempts=3, delay=2, backoff=2):
    """Decorator for retrying functions on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 1
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        logging.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    logging.warning(f"{func.__name__} attempt {attempt} failed: {e}. Retrying...")
                    time.sleep(delay * (backoff ** (attempt - 1)))
                    attempt += 1
            return None
        return wrapper
    return decorator


class PinokioInstaller:
    """Manages Pinokio installation and updates with robust error handling"""
    
    GITHUB_API_URL = "https://api.github.com/repos/pinokiocomputer/pinokio/releases/latest"
    FALLBACK_DOWNLOAD_URL = "https://github.com/pinokiocomputer/pinokio/releases/download/3.9.0/Pinokio-3.9.0.AppImage"
    
    def __init__(self, install_path: str, logger: Optional[logging.Logger] = None):
        self.install_path = install_path
        self.executable_path = None
        self.version = None
        self.logger = logger or self._setup_logger()
        self.config = {}
        self.installation_info = {}
        
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger('PinokioInstaller')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
        
    def is_installed(self) -> bool:
        """Check if Pinokio is installed with verification"""
        # Look for any Pinokio AppImage file (versioned format)
        appimage_path = None
        for file in os.listdir(self.install_path) if os.path.exists(self.install_path) else []:
            if file.startswith("Pinokio-") and file.endswith(".AppImage"):
                appimage_path = os.path.join(self.install_path, file)
                break
        
        # Fallback to legacy naming
        if not appimage_path:
            appimage_path = os.path.join(self.install_path, "Pinokio-linux.AppImage")
        
        if os.path.exists(appimage_path):
            # Verify file is valid and executable
            if os.path.isfile(appimage_path) and os.access(appimage_path, os.X_OK):
                self.executable_path = appimage_path
                
                # Check file size (should be at least 50MB)
                file_size = os.path.getsize(appimage_path)
                if file_size < 50 * 1024 * 1024:
                    self.logger.warning(f"AppImage seems too small: {file_size / (1024*1024):.1f}MB")
                    return False
                
                # Load installation info if available
                self._load_installation_info()
                
                return True
            else:
                self.logger.warning("AppImage exists but is not executable")
                return False
        return False
    
    def _load_installation_info(self) -> bool:
        """Load installation information from metadata file"""
        info_file = os.path.join(self.install_path, "installation_info.json")
        if os.path.exists(info_file):
            try:
                with open(info_file, 'r') as f:
                    self.installation_info = json.load(f)
                    self.version = self.installation_info.get('version')
                return True
            except Exception as e:
                self.logger.debug(f"Could not load installation info: {e}")
        return False
    
    def _save_installation_info(self, info: Dict) -> bool:
        """Save installation information to metadata file"""
        info_file = os.path.join(self.install_path, "installation_info.json")
        try:
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Could not save installation info: {e}")
            return False
    
    @retry_on_failure(max_attempts=3, delay=1)
    def get_latest_release_info(self) -> Dict:
        """Get the latest Pinokio release information from GitHub"""
        try:
            headers = {'Accept': 'application/vnd.github.v3+json'}
            response = requests.get(self.GITHUB_API_URL, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Find Linux AppImage asset
            for asset in data.get('assets', []):
                if 'linux' in asset['name'].lower() and 'AppImage' in asset['name']:
                    return {
                        'version': data.get('tag_name', 'unknown'),
                        'download_url': asset['browser_download_url'],
                        'size': asset.get('size', 0),
                        'created_at': asset.get('created_at'),
                        'name': asset['name']
                    }
            
            # No AppImage found, use fallback
            self.logger.warning("No Linux AppImage found in latest release")
            return {
                'version': 'latest',
                'download_url': self.FALLBACK_DOWNLOAD_URL,
                'size': 0
            }
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch release info: {e}")
            return {
                'version': 'latest',
                'download_url': self.FALLBACK_DOWNLOAD_URL,
                'size': 0
            }
    
    @retry_on_failure(max_attempts=3, delay=5)
    def download_pinokio(self, release_info: Dict = None) -> bool:
        """Download Pinokio AppImage with verification and progress"""
        if release_info is None:
            release_info = self.get_latest_release_info()
        
        url = release_info['download_url']
        expected_size = release_info.get('size', 0)
        
        try:
            self.logger.info(f"📥 Downloading Pinokio from {url}")
            
            # Create temp file for download using correct filename from URL
            filename = url.split('/')[-1]  # Extract filename from URL
            if not filename.endswith('.AppImage'):
                filename = "Pinokio-linux.AppImage"  # Fallback
            temp_path = os.path.join(self.install_path, f"{filename}.tmp")
            appimage_path = os.path.join(self.install_path, filename)
            
            # Download with progress and resume support
            headers = {}
            downloaded = 0
            
            # Check if partial download exists
            if os.path.exists(temp_path):
                downloaded = os.path.getsize(temp_path)
                headers['Range'] = f'bytes={downloaded}-'
                self.logger.info(f"Resuming download from {downloaded / (1024*1024):.1f}MB")
            
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0)) + downloaded
            
            # Write to temp file
            mode = 'ab' if downloaded > 0 else 'wb'
            with open(temp_path, mode) as f:
                for chunk in response.iter_content(chunk_size=32768):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            speed = downloaded / (1024 * 1024)  # MB
                            print(f"Progress: {progress:.1f}% ({speed:.1f}MB / {total_size/(1024*1024):.1f}MB)", end='\r')
            
            print()  # New line after progress
            
            # Verify download size
            actual_size = os.path.getsize(temp_path)
            if expected_size > 0 and abs(actual_size - expected_size) > 1024:
                self.logger.warning(f"Downloaded size ({actual_size}) doesn't match expected ({expected_size})")
            
            # Move temp file to final location
            if os.path.exists(appimage_path):
                os.remove(appimage_path)
            os.rename(temp_path, appimage_path)
            
            # Make executable
            os.chmod(appimage_path, 0o755)
            self.executable_path = appimage_path
            
            # Save installation info
            self._save_installation_info({
                'version': release_info.get('version', 'unknown'),
                'downloaded_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'size': actual_size,
                'url': url
            })
            
            self.logger.info("✅ Download complete and verified")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Download failed: {e}")
            # Clean up partial download on final failure
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            raise
    
    @retry_on_failure(max_attempts=2, delay=3)
    def setup_virtual_display(self) -> bool:
        """Setup Xvfb virtual display for headless operation with verification"""
        try:
            self.logger.info("📺 Setting up virtual display...")
            
            # Check if already running
            try:
                result = subprocess.run(['pgrep', '-f', 'Xvfb.*:99'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.logger.info("Virtual display already running")
                    os.environ['DISPLAY'] = ':99'
                    return True
            except:
                pass
            
            # Check if Xvfb is installed
            result = subprocess.run(['which', 'Xvfb'], capture_output=True)
            if result.returncode != 0:
                self.logger.info("Installing Xvfb and dependencies...")
                
                # Update package list
                subprocess.run(['apt-get', 'update', '-qq'], 
                             capture_output=True, check=False)
                
                # Install X11 dependencies
                x11_packages = [
                    'xvfb', 'x11-utils', 'x11-xserver-utils',
                    'libxrender1', 'libxtst6', 'libxi6', 'libxss1',
                    'libgconf-2-4', 'libnss3', 'libasound2',
                    'libatk-bridge2.0-0', 'libgtk-3-0', 'libgbm1'
                ]
                
                for package in x11_packages:
                    subprocess.run(
                        ['apt-get', 'install', '-y', '-qq', package],
                        capture_output=True, check=False
                    )
            
            # Kill any existing Xvfb on :99
            subprocess.run(['pkill', '-f', 'Xvfb.*:99'], check=False)
            time.sleep(1)
            
            # Start Xvfb with error checking
            xvfb_cmd = [
                'Xvfb', ':99',
                '-screen', '0', '1920x1080x24',
                '-ac',
                '+extension', 'GLX',
                '+render',
                '-noreset'
            ]
            
            xvfb_process = subprocess.Popen(
                xvfb_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait and verify Xvfb started
            time.sleep(2)
            if xvfb_process.poll() is not None:
                stderr = xvfb_process.stderr.read().decode() if xvfb_process.stderr else "Unknown error"
                raise Exception(f"Xvfb failed to start: {stderr}")
            
            # Set display environment variable
            os.environ['DISPLAY'] = ':99'
            
            # Verify display is working
            test_result = subprocess.run(
                ['xdpyinfo', '-display', ':99'],
                capture_output=True,
                timeout=5
            )
            
            if test_result.returncode != 0:
                raise Exception("Virtual display verification failed")
            
            self.logger.info("✅ Virtual display setup complete and verified")
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("Virtual display verification timed out")
            return False
        except Exception as e:
            self.logger.error(f"⚠️ Virtual display setup failed: {e}")
            return False
    
    def install_dependencies(self) -> bool:
        """Install system dependencies for Pinokio with verification"""
        try:
            self.logger.info("📦 Installing system dependencies...")
            
            # Essential dependencies
            essential_deps = {
                'wget': 'wget --version',
                'curl': 'curl --version',
                'git': 'git --version',
                'python3': 'python3 --version',
                'python3-pip': 'pip3 --version'
            }
            
            # Optional but recommended dependencies
            optional_deps = {
                'nodejs': 'node --version',
                'npm': 'npm --version',
                'ffmpeg': 'ffmpeg -version',
                'libgomp1': None,  # Library, no version check
                'build-essential': 'gcc --version'
            }
            
            # Update package list once
            self.logger.info("Updating package list...")
            update_result = subprocess.run(
                ['apt-get', 'update', '-qq'],
                capture_output=True,
                text=True
            )
            
            if update_result.returncode != 0:
                self.logger.warning("Package list update failed, continuing anyway")
            
            installed = []
            failed = []
            
            # Install essential dependencies
            for dep, check_cmd in essential_deps.items():
                if self._install_and_verify_package(dep, check_cmd):
                    installed.append(dep)
                else:
                    failed.append(dep)
            
            # Install optional dependencies (don't fail if these don't install)
            for dep, check_cmd in optional_deps.items():
                if self._install_and_verify_package(dep, check_cmd, required=False):
                    installed.append(dep)
            
            # Check if essential dependencies failed
            essential_failed = [d for d in failed if d in essential_deps]
            if essential_failed:
                self.logger.error(f"Failed to install essential dependencies: {essential_failed}")
                return False
            
            self.logger.info(f"✅ Installed {len(installed)} dependencies")
            if failed:
                self.logger.warning(f"⚠️ Some optional dependencies failed: {failed}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Dependency installation failed: {e}")
            return False
    
    def _install_and_verify_package(self, package: str, check_cmd: Optional[str], required: bool = True) -> bool:
        """Install a package and verify it's working"""
        try:
            # Check if already installed
            if check_cmd:
                check_parts = check_cmd.split()
                result = subprocess.run(check_parts, capture_output=True, timeout=5)
                if result.returncode == 0:
                    self.logger.debug(f"{package} already installed")
                    return True
            
            # Install package
            self.logger.debug(f"Installing {package}...")
            install_result = subprocess.run(
                ['apt-get', 'install', '-y', '-qq', package],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if install_result.returncode != 0:
                if required:
                    self.logger.error(f"Failed to install {package}: {install_result.stderr}")
                else:
                    self.logger.debug(f"Optional package {package} failed to install")
                return False
            
            # Verify installation
            if check_cmd:
                check_parts = check_cmd.split()
                result = subprocess.run(check_parts, capture_output=True, timeout=5)
                if result.returncode != 0:
                    if required:
                        self.logger.error(f"{package} installed but verification failed")
                    return False
            
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Installation of {package} timed out")
            return False
        except Exception as e:
            self.logger.debug(f"Error installing {package}: {e}")
            return False
    
    def install(self, version: str = "latest", headless: bool = True, skip_deps: bool = False) -> bool:
        """Complete Pinokio installation with verification"""
        try:
            # Check if already installed
            if self.is_installed():
                self.logger.info("✅ Pinokio already installed")
                
                # Check if update is needed
                if version != "latest":
                    current_version = self.installation_info.get('version', 'unknown')
                    if current_version != version:
                        self.logger.info(f"Version mismatch: {current_version} != {version}")
                        return self.update()
                
                return True
            
            self.logger.info("Starting Pinokio installation...")
            
            # Create installation directory with proper permissions
            Path(self.install_path).mkdir(parents=True, exist_ok=True, mode=0o755)
            
            # Verify directory is writable
            test_file = os.path.join(self.install_path, '.write_test')
            try:
                Path(test_file).touch()
                os.remove(test_file)
            except:
                self.logger.error(f"Installation directory not writable: {self.install_path}")
                return False
            
            # Install dependencies unless skipped
            if not skip_deps:
                if not self.install_dependencies():
                    self.logger.warning("Some dependencies failed to install, continuing anyway")
            
            # Setup virtual display if headless
            if headless:
                if not self.setup_virtual_display():
                    self.logger.warning("Virtual display setup failed, continuing anyway")
            
            # Get release info
            release_info = self.get_latest_release_info()
            if version != "latest" and release_info['version'] != version:
                self.logger.warning(f"Requested version {version} not available, using {release_info['version']}")
            
            # Download Pinokio with retries
            try:
                if not self.download_pinokio(release_info):
                    return False
            except Exception as e:
                self.logger.error(f"Download failed after retries: {e}")
                return False
            
            # Verify installation
            if self.is_installed():
                self.logger.info("✅ Pinokio installation complete and verified!")
                
                # Run a quick test if possible
                if self._test_installation():
                    self.logger.info("✅ Installation test passed")
                else:
                    self.logger.warning("⚠️ Installation test failed, but Pinokio is installed")
                
                return True
            else:
                self.logger.error("❌ Installation verification failed")
                return False
                
        except PermissionError as e:
            self.logger.error(f"❌ Permission denied: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Installation failed: {e}")
            return False
    
    def _test_installation(self) -> bool:
        """Run a quick test of the Pinokio installation"""
        try:
            if not self.executable_path:
                return False
            
            # Try to run Pinokio with version flag
            test_cmd = [self.executable_path, '--version']
            result = subprocess.run(
                test_cmd,
                capture_output=True,
                text=True,
                timeout=10,
                env=dict(os.environ, DISPLAY=':99')
            )
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.debug(f"Installation test failed: {e}")
            return False
    
    def update(self, force: bool = False) -> bool:
        """Update Pinokio to latest version with rollback support"""
        try:
            self.logger.info("🔄 Checking for Pinokio updates...")
            
            # Get latest release info
            latest_info = self.get_latest_release_info()
            latest_version = latest_info.get('version', 'unknown')
            
            # Check current version
            current_version = self.installation_info.get('version', 'unknown')
            
            if not force and current_version == latest_version:
                self.logger.info(f"Already on latest version: {latest_version}")
                return True
            
            self.logger.info(f"Updating from {current_version} to {latest_version}")
            
            # Ensure we have current installation
            if not self.is_installed():
                self.logger.info("No existing installation found, performing fresh install")
                return self.install()
            
            # Create backup with timestamp
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.executable_path}.backup_{timestamp}"
            backup_info_path = os.path.join(self.install_path, f"installation_info.backup_{timestamp}.json")
            
            try:
                # Backup current installation
                self.logger.info("Creating backup of current installation...")
                import shutil
                shutil.copy2(self.executable_path, backup_path)
                
                # Backup installation info
                info_file = os.path.join(self.install_path, "installation_info.json")
                if os.path.exists(info_file):
                    shutil.copy2(info_file, backup_info_path)
                
                # Download new version
                self.logger.info("Downloading new version...")
                if self.download_pinokio(latest_info):
                    # Verify new installation
                    if self._test_installation():
                        # Clean up old backups (keep last 3)
                        self._cleanup_old_backups()
                        
                        self.logger.info(f"✅ Update complete! Now on version {latest_version}")
                        return True
                    else:
                        raise Exception("New version verification failed")
                else:
                    raise Exception("Download failed")
                    
            except Exception as e:
                # Restore backup on failure
                self.logger.error(f"Update failed: {e}")
                self.logger.info("Rolling back to previous version...")
                
                if os.path.exists(backup_path):
                    # Remove failed update
                    if os.path.exists(self.executable_path):
                        os.remove(self.executable_path)
                    
                    # Restore backup
                    shutil.move(backup_path, self.executable_path)
                    
                    # Restore info file
                    if os.path.exists(backup_info_path):
                        info_file = os.path.join(self.install_path, "installation_info.json")
                        if os.path.exists(info_file):
                            os.remove(info_file)
                        shutil.move(backup_info_path, info_file)
                    
                    self.logger.info("✅ Rollback successful")
                else:
                    self.logger.error("Backup not found, cannot rollback")
                
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Update error: {e}")
            return False
    
    def _cleanup_old_backups(self, keep: int = 3) -> None:
        """Clean up old backup files, keeping only the most recent ones"""
        try:
            # Find all backup files
            backup_pattern = f"{os.path.basename(self.executable_path)}.backup_*"
            backups = []
            
            for file in os.listdir(self.install_path):
                if file.startswith(f"{os.path.basename(self.executable_path)}.backup_"):
                    file_path = os.path.join(self.install_path, file)
                    backups.append((file_path, os.path.getmtime(file_path)))
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old backups
            for backup_path, _ in backups[keep:]:
                try:
                    os.remove(backup_path)
                    self.logger.debug(f"Removed old backup: {backup_path}")
                    
                    # Also remove corresponding info file
                    timestamp = backup_path.split('backup_')[1]
                    info_backup = os.path.join(self.install_path, f"installation_info.backup_{timestamp}.json")
                    if os.path.exists(info_backup):
                        os.remove(info_backup)
                except:
                    pass
                    
        except Exception as e:
            self.logger.debug(f"Error cleaning up backups: {e}")
    
    def get_executable_command(self, args: List[str] = None) -> List[str]:
        """Get the command to execute Pinokio with optional arguments"""
        if not self.executable_path:
            return None
        
        cmd = [self.executable_path]
        
        # Add default arguments for headless operation
        if os.environ.get('DISPLAY'):
            cmd.extend(['--no-sandbox', '--disable-setuid-sandbox'])
        
        # Add user-provided arguments
        if args:
            cmd.extend(args)
        
        return cmd
    
    def uninstall(self, remove_data: bool = False) -> bool:
        """Uninstall Pinokio with optional data removal"""
        try:
            self.logger.info("Uninstalling Pinokio...")
            
            # Remove executable
            if self.executable_path and os.path.exists(self.executable_path):
                os.remove(self.executable_path)
                self.logger.info("Removed Pinokio executable")
            
            # Remove backups
            for file in os.listdir(self.install_path):
                if file.startswith("Pinokio-linux.AppImage.backup"):
                    os.remove(os.path.join(self.install_path, file))
            
            # Remove installation info
            info_file = os.path.join(self.install_path, "installation_info.json")
            if os.path.exists(info_file):
                os.remove(info_file)
            
            # Remove data if requested
            if remove_data:
                data_paths = [
                    os.path.expanduser("~/.pinokio"),
                    os.path.expanduser("~/.config/pinokio"),
                    os.path.expanduser("~/.local/share/pinokio")
                ]
                
                for path in data_paths:
                    if os.path.exists(path):
                        import shutil
                        shutil.rmtree(path)
                        self.logger.info(f"Removed data directory: {path}")
            
            self.logger.info("✅ Pinokio uninstalled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Uninstall failed: {e}")
            return False
    
    def get_executable_command(self) -> list:
        """Get the command to run Pinokio"""
        if not self.executable_path:
            return []
        
        cmd = [self.executable_path, '--no-sandbox']
        
        # Add headless flag if display not available
        if not os.environ.get('DISPLAY'):
            cmd.append('--headless')
        
        return cmd
