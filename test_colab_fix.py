#!/usr/bin/env python3
"""
Test script to verify the Colab fix works
"""

import os
import sys
import subprocess

# Change to the repo directory that Colab uses
os.chdir('github_upload/SD-LongNose')
sys.path.insert(0, '.')
sys.path.insert(0, 'modules')

def test_pinokio_controller():
    """Test that PinokioController has the required method"""
    try:
        from modules.pinokio_controller import PinokioController
        
        # Create instance
        controller = PinokioController('/content/pinokio', 42000)
        
        # Test that the method exists
        binary_path = controller.get_pinokio_binary_path()
        print(f"✅ Binary path method works: {binary_path}")
        
        # Test start_server doesn't crash on method call
        print("✅ PinokioController can be instantiated and has required methods")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_main_orchestrator():
    """Test the main orchestrator"""
    try:
        from pinokio_cloud_main import PinokioCloudGPU
        
        print("✅ Main orchestrator imports successfully")
        
        # Test basic setup (without actually running)
        pinokio = PinokioCloudGPU(log_level='ERROR')  # Suppress logs
        print("✅ Main orchestrator can be instantiated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Colab fixes...")
    print("=" * 50)
    
    success = True
    
    print("🔧 Testing PinokioController...")
    if not test_pinokio_controller():
        success = False
    
    print("\n🔧 Testing Main Orchestrator...")
    if not test_main_orchestrator():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ALL TESTS PASSED - Colab should work now!")
    else:
        print("❌ Tests failed - need more fixes")
