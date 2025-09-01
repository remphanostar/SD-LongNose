"""
Fixed notebook setup script for Pinokio Cloud GPU deployment
This script addresses the import path issues in the Jupyter notebook
"""

import os
import sys
import subprocess

def setup_repository():
    """Clone repository and setup paths correctly"""
    # Correct repository URL for Pinokio Cloud GPU
    repo_url = "https://github.com/yourusername/PinokioNotebook.git"  # Update with actual repo
    repo_dir = "PinokioNotebook"
    
    # Alternative: If running from already cloned repo, detect current directory
    current_dir = os.getcwd()
    if "PinokioNotebook" in current_dir or os.path.exists("modules"):
        print("✅ Running from repository directory")
        repo_dir = current_dir
    else:
        # Clone repository if not exists
        if not os.path.exists(repo_dir):
            print("📥 Cloning repository...")
            try:
                subprocess.run(["git", "clone", repo_url], check=True)
                print("✅ Repository cloned")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to clone repository: {e}")
                print("📁 Please clone manually or ensure you're in the correct directory")
                return None
        else:
            print("✅ Repository already exists")
    
    # Add modules directory to Python path
    modules_path = os.path.join(repo_dir, "modules") if repo_dir != current_dir else "modules"
    if os.path.exists(modules_path):
        if modules_path not in sys.path:
            sys.path.insert(0, modules_path)
        print(f"✅ Added modules path: {modules_path}")
    else:
        print(f"❌ Modules directory not found at: {modules_path}")
        return None
    
    # Also add the main directory for importing pinokio_cloud_main
    main_path = repo_dir if repo_dir != current_dir else "."
    if main_path not in sys.path:
        sys.path.insert(0, main_path)
    
    return repo_dir

def install_dependencies():
    """Install required packages"""
    packages = [
        "requests",
        "pyngrok", 
        "psutil",
        "cloud-detect"
    ]
    
    print("📦 Installing dependencies...")
    for package in packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", package], 
                         check=True, capture_output=True)
            print(f"✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"⚠️ Failed to install {package}")
    
    print("✅ Dependencies installation complete")

def test_imports():
    """Test if imports work correctly"""
    try:
        # Test module imports
        from platform_detector import PlatformDetector
        from pinokio_installer import PinokioInstaller  
        from tunnel_manager import TunnelManager
        from pinokio_controller import PinokioController
        print("✅ Module imports successful")
        
        # Test main module import
        import pinokio_cloud_main
        print("✅ Main module import successful")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def quick_start_notebook(ngrok_token=None, install_tools=None):
    """
    Quick start function for notebooks with corrected imports
    
    Args:
        ngrok_token: Optional ngrok auth token for tunneling
        install_tools: List of tools to install (e.g., ["stable-diffusion", "comfyui"])
    """
    try:
        # Setup repository and paths
        repo_dir = setup_repository()
        if not repo_dir:
            return None, None
        
        # Install dependencies
        install_dependencies()
        
        # Test imports
        if not test_imports():
            return None, None
        
        # Import after path setup
        from pinokio_cloud_main import quick_start_notebook
        
        # Run the enhanced quick start
        config = {}
        if install_tools:
            config['auto_install_tools'] = install_tools
        
        return quick_start_notebook(config=config)
        
    except Exception as e:
        print(f"❌ Quick start failed: {e}")
        return None, None

# For direct execution in notebooks
if __name__ == "__main__":
    # Run setup
    setup_repository()
    install_dependencies()
    test_imports()
