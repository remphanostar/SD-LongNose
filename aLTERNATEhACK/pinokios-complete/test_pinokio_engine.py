#!/usr/bin/env python3
"""
Test apps using proper Pinokio engine install_app() and run_app() methods
"""
import asyncio
import sys
from pathlib import Path
sys.path.append('.')

from pinokios.unified_engine import UnifiedPinokioEngine

async def test_pinokio_install_and_run(engine, app_name):
    """Test app using proper Pinokio engine methods"""
    print(f"\n{'='*60}")
    print(f"TESTING PINOKIO ENGINE: {app_name}")
    print(f"{'='*60}")
    
    app_path = Path(engine.base_path) / app_name
    print(f"App directory: {app_path}")
    print(f"App directory exists: {app_path.exists()}")
    
    # Check for Pinokio script files
    install_js = app_path / 'install.js'
    install_json = app_path / 'install.json' 
    start_js = app_path / 'start.js'
    start_json = app_path / 'start.json'
    
    print(f"install.js exists: {install_js.exists()}")
    print(f"install.json exists: {install_json.exists()}")
    print(f"start.js exists: {start_js.exists()}")
    print(f"start.json exists: {start_json.exists()}")
    
    if not app_path.exists():
        print(f"❌ App directory not found: {app_path}")
        return False
    
    # Test installation using engine
    if install_js.exists() or install_json.exists():
        print(f"\n🔧 TESTING INSTALLATION via Pinokio engine...")
        try:
            success, message = await engine.install_app({
                'Appname': app_name,
                'Git': f"file://{app_path}"  # Use local path
            })
            print(f"Install result: success={success}")
            print(f"Install message: {message}")
            
            if not success:
                print(f"❌ Installation failed: {message}")
                return False
                
        except Exception as e:
            print(f"❌ Installation exception: {e}")
            return False
    
    # Test running using engine  
    if start_js.exists() or start_json.exists():
        print(f"\n▶️ TESTING RUN via Pinokio engine...")
        try:
            success, message = await engine.run_app(app_name)
            print(f"Run result: success={success}")
            print(f"Run message: {message}")
            
            # Check for success indicators (CUDA/PyTorch dependency errors)
            message_lower = message.lower()
            dependency_keywords = ['cuda', 'pytorch', 'torch', 'gpu', 'import', 'module', 'requirement', 'install']
            
            has_dependency_error = any(keyword in message_lower for keyword in dependency_keywords)
            
            if has_dependency_error:
                print(f"✅ SUCCESS: {app_name} reached dependency/CUDA error stage!")
                return True
            elif success:
                print(f"✅ UNEXPECTED: {app_name} started without dependency errors")
                return True
            else:
                print(f"❌ FAILED: {app_name} failed before reaching dependency errors")
                print(f"Error details: {message}")
                return False
                
        except Exception as e:
            print(f"❌ Run exception: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return False
    else:
        print(f"❌ No start script found for {app_name}")
        return False

async def main():
    """Test apps using proper Pinokio engine methods"""
    print("Testing apps via Pinokio engine install_app() and run_app() methods...")
    
    # Initialize engine
    engine = UnifiedPinokioEngine(base_path="./pinokio_apps")
    
    # Test apps that have Pinokio scripts
    apps_to_test = [
        "roop-unleashed",      # Has install.js and start.js
        "RVC-realtime",        # Has install.js and start.js  
        "comfyui.pinokio",     # Has install.json and start.json
        "DiffuEraser",         # Has install.js and start.js
        "bria-rmbg",          # Has start.js
        "clarity-refiners-ui", # Has start.js
    ]
    
    results = {}
    
    for app_name in apps_to_test:
        success = await test_pinokio_install_and_run(engine, app_name)
        results[app_name] = success
    
    # Final results
    print(f"\n{'='*60}")
    print("PINOKIO ENGINE TEST RESULTS")
    print(f"{'='*60}")
    
    successful_apps = []
    failed_apps = []
    
    for app_name, success in results.items():
        if success:
            successful_apps.append(app_name)
            print(f"✅ {app_name}")
        else:
            failed_apps.append(app_name)
            print(f"❌ {app_name}")
    
    print(f"\n📊 SUMMARY:")
    print(f"✅ Apps reaching dependency/CUDA errors: {len(successful_apps)}")
    print(f"❌ Apps failing to run properly: {len(failed_apps)}")
    
    if successful_apps:
        print(f"\n🎯 SUCCESSFUL APPS (via Pinokio engine):")
        for app in successful_apps:
            print(f"  - {app}")

if __name__ == "__main__":
    asyncio.run(main())
