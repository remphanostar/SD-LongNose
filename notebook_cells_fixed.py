"""
Fixed Jupyter notebook cells for Pinokio Cloud GPU deployment
Copy these cells into your notebook to replace the problematic ones
"""

# Cell 1: Repository Setup (Fixed)
setup_cell = '''
import os
import sys
import subprocess

# Setup repository paths correctly
def setup_pinokio_environment():
    """Setup paths and clone if needed"""
    current_dir = os.getcwd()
    
    # Check if we're already in the repository
    if os.path.exists("modules") and os.path.exists("pinokio_cloud_main.py"):
        print("✅ Running from repository directory")
        repo_dir = current_dir
    else:
        # Try to find the notebook setup script
        if os.path.exists("notebook_setup.py"):
            exec(open("notebook_setup.py").read())
            return
        else:
            print("❌ Please ensure you're in the PinokioNotebook directory")
            print("📁 Current directory:", current_dir)
            return False
    
    # Add paths
    modules_path = os.path.join(repo_dir, "modules")
    if os.path.exists(modules_path) and modules_path not in sys.path:
        sys.path.insert(0, modules_path)
        sys.path.insert(0, repo_dir)
        print("✅ Python paths configured")
    
    return True

# Run setup
setup_pinokio_environment()
'''

# Cell 2: Dependencies Installation (Fixed)
dependencies_cell = '''
# Install required packages with error handling
packages = [
    "requests>=2.25.0",
    "pyngrok>=5.0.0", 
    "psutil>=5.7.0"
]

for package in packages:
    try:
        print(f"Installing {package}...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", package], 
                      check=True, capture_output=True, text=True)
        print(f"✅ {package} installed")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to install {package}: {e}")

print("✅ Dependencies installation complete")
'''

# Cell 3: Import Modules (Fixed)
import_cell = '''
# Import modules with error handling
try:
    from platform_detector import PlatformDetector
    from pinokio_installer import PinokioInstaller
    from tunnel_manager import TunnelManager
    from pinokio_controller import PinokioController
    import pinokio_cloud_main
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're running from the correct directory")
    print("📁 Expected files: modules/, pinokio_cloud_main.py")
'''

# Cell 4: Enhanced Quick Start (Fixed)
quick_start_cell = '''
def enhanced_quick_start(ngrok_token=None, tunnel_service="auto", install_tools=None):
    """
    Enhanced quick start with better error handling
    
    Args:
        ngrok_token: Optional ngrok auth token
        tunnel_service: "auto", "cloudflare", "ngrok", or "localtunnel"  
        install_tools: List of tools to install automatically
    """
    try:
        # Use the enhanced quick start from main module
        config = {
            "tunnel_service": tunnel_service,
            "headless": True
        }
        
        if install_tools:
            config["auto_install_tools"] = install_tools
        
        # Call the enhanced quick start function
        pinokio_instance, tunnel_url = pinokio_cloud_main.quick_start_notebook(
            config=config, 
            log_level="INFO"
        )
        
        if pinokio_instance and tunnel_url:
            print(f"\\n🎉 SUCCESS! Pinokio is accessible at:")
            print(f"🔗 {tunnel_url}")
            print(f"📱 Open this URL in your browser")
            
            # Show status
            pinokio_instance.print_status()
            
            return pinokio_instance, tunnel_url
        else:
            print("❌ Quick start failed")
            return None, None
            
    except Exception as e:
        print(f"❌ Error during quick start: {e}")
        return None, None

# Run enhanced quick start
# Uncomment and customize as needed:
# pinokio, url = enhanced_quick_start(
#     tunnel_service="cloudflare",  # or "ngrok", "localtunnel", "auto"
#     install_tools=["stable-diffusion", "comfyui"]  # optional
# )
'''

# Cell 5: Manual Step-by-Step (Fixed)
manual_setup_cell = '''
# Manual setup with enhanced error handling
def manual_setup():
    """Manual step-by-step setup"""
    try:
        # Initialize with enhanced orchestrator
        pinokio = pinokio_cloud_main.PinokioCloudGPU(log_level="INFO")
        
        # Step 1: Setup environment
        print("🔍 Setting up environment...")
        if not pinokio.setup():
            print("❌ Environment setup failed")
            return None
        
        # Step 2: Install Pinokio
        print("📦 Installing Pinokio...")
        if not pinokio.install_pinokio():
            print("❌ Pinokio installation failed")
            return None
        
        # Step 3: Start server
        print("🚀 Starting Pinokio server...")
        if not pinokio.start_pinokio():
            print("❌ Server startup failed")
            return None
        
        # Step 4: Setup tunnel
        print("🌐 Setting up tunnel...")
        tunnel_url = pinokio.setup_tunnel(service="auto")
        
        if tunnel_url:
            print(f"\\n✅ Setup complete!")
            pinokio.print_status()
            return pinokio, tunnel_url
        else:
            print("⚠️ Tunnel setup failed, but server is running locally")
            return pinokio, None
            
    except Exception as e:
        print(f"❌ Manual setup failed: {e}")
        return None

# Uncomment to run manual setup:
# pinokio, url = manual_setup()
'''

# Cell 6: Tool Management (Fixed)
tool_management_cell = '''
# Enhanced tool management
def install_ai_tool(pinokio_instance, tool_name, auto_launch=True):
    """Install AI tool with error handling"""
    if not pinokio_instance:
        print("❌ No Pinokio instance available. Run setup first.")
        return None
    
    try:
        print(f"🤖 Installing {tool_name}...")
        tool_url = pinokio_instance.install_ai_tool(
            tool_name, 
            auto_launch=auto_launch
        )
        
        if tool_url:
            print(f"✅ {tool_name} is ready at: {tool_url}")
            return tool_url
        else:
            print(f"⚠️ {tool_name} installed but not launched")
            return True
            
    except Exception as e:
        print(f"❌ Failed to install {tool_name}: {e}")
        return None

def list_available_tools():
    """List available AI tools"""
    tools = {
        "stable-diffusion": "Stable Diffusion WebUI by AUTOMATIC1111",
        "comfyui": "ComfyUI for node-based workflows", 
        "text-generation": "Text Generation WebUI by oobabooga",
        "kohya-ss": "Kohya SS for model training",
        "invokeai": "InvokeAI for advanced image generation",
        "fooocus": "Fooocus for simplified AI art generation"
    }
    
    print("🤖 Available AI Tools:")
    for name, desc in tools.items():
        print(f"  • {name}: {desc}")
    
    return tools

# List available tools
list_available_tools()

# Example usage:
# install_ai_tool(pinokio, "stable-diffusion")
# install_ai_tool(pinokio, "comfyui", auto_launch=False)
'''

# Cell 7: Status and Monitoring (Fixed)
status_cell = '''
def show_status(pinokio_instance):
    """Show comprehensive status"""
    if not pinokio_instance:
        print("❌ No Pinokio instance available")
        return
    
    try:
        pinokio_instance.print_status()
        return pinokio_instance.get_status()
    except Exception as e:
        print(f"❌ Failed to get status: {e}")

def recovery_mode(pinokio_instance):
    """Attempt recovery from errors"""
    if not pinokio_instance:
        print("❌ No Pinokio instance available")
        return False
    
    try:
        print("🔄 Attempting recovery...")
        return pinokio_instance.recover_from_error()
    except Exception as e:
        print(f"❌ Recovery failed: {e}")
        return False

# Example usage:
# status = show_status(pinokio)
# recovery_mode(pinokio)
'''

# Cell 8: Cleanup (Fixed)
cleanup_cell = '''
def enhanced_cleanup(pinokio_instance):
    """Enhanced cleanup with error handling"""
    if not pinokio_instance:
        print("❌ No Pinokio instance to cleanup")
        return
    
    try:
        print("🧹 Cleaning up services...")
        pinokio_instance.cleanup()
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"⚠️ Cleanup error: {e}")

# Uncomment to run cleanup:
# enhanced_cleanup(pinokio)
'''

print("✅ Fixed notebook cells created")
print("📝 Copy these cells into your Jupyter notebook to replace the problematic ones")
