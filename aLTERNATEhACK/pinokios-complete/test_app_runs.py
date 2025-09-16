#!/usr/bin/env python3
"""
Test script to run all installed apps and check for CUDA/PyTorch dependency errors
"""
import asyncio
import sys
from pathlib import Path

# Add the pinokios module to the path
sys.path.append(str(Path(__file__).parent))

from pinokios.unified_engine import UnifiedPinokioEngine

async def test_app_run(engine, app_name):
    """Test running a single app"""
    print(f"\n{'='*50}")
    print(f"TESTING: {app_name}")
    print(f"{'='*50}")
    
    try:
        success, message = await engine.run_app(app_name)
        print(f"Result: success={success}")
        print(f"Message: {message}")
        
        # Check if we got the desired CUDA/PyTorch errors
        cuda_keywords = ['cuda', 'gpu', 'pytorch', 'torch', 'nvidia', 'cudnn']
        dependency_keywords = ['import', 'module', 'package', 'install', 'requirement']
        
        message_lower = message.lower()
        has_cuda_error = any(keyword in message_lower for keyword in cuda_keywords)
        has_dependency_error = any(keyword in message_lower for keyword in dependency_keywords)
        
        if has_cuda_error or has_dependency_error:
            print(f"✅ SUCCESS: {app_name} reached dependency/CUDA error stage!")
            return True
        elif success:
            print(f"✅ UNEXPECTED: {app_name} started successfully (no errors)")
            return True
        else:
            print(f"❌ FAILED: {app_name} failed before reaching dependency errors")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {app_name} - {str(e)}")
        return False

async def main():
    """Test all apps with start scripts"""
    print("Starting app run tests...")
    
    # Initialize engine
    engine = UnifiedPinokioEngine(base_path="./pinokio_apps")
    
    # Apps to test (have start scripts)
    apps_to_test = [
        "roop-unleashed",
        "RVC-realtime", 
        "comfyui.pinokio",
        "DiffuEraser",
        "bria-rmbg",
        "clarity-refiners-ui",
        "higgs-audio-v2-ui",
        "rvc.pinokio",
        "sillytavern",
        "dragnuwa"
    ]
    
    results = {}
    
    for app_name in apps_to_test:
        app_path = Path("./pinokio_apps") / app_name
        if app_path.exists():
            success = await test_app_run(engine, app_name)
            results[app_name] = success
        else:
            print(f"❌ SKIPPED: {app_name} - directory not found")
            results[app_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
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
    
    print(f"\nSUCCESSFUL APPS: {len(successful_apps)}")
    print(f"FAILED APPS: {len(failed_apps)}")
    
    if successful_apps:
        print(f"\nApps that reached dependency/CUDA errors (SUCCESS):")
        for app in successful_apps:
            print(f"  - {app}")

if __name__ == "__main__":
    asyncio.run(main())
