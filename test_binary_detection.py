#!/usr/bin/env python3
"""
Test binary detection logic to confirm the fix works
"""

import os
import sys
import tempfile

# Add modules to path
sys.path.insert(0, 'github_upload/modules')
sys.path.insert(0, 'github_upload/SD-LongNose/modules')

def test_binary_detection():
    """Test that binary detection works correctly"""
    from pinokio_controller import PinokioController
    
    # Create temp directory with versioned AppImage
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mock AppImage file
        mock_appimage = os.path.join(temp_dir, "Pinokio-3.9.0.AppImage")
        with open(mock_appimage, 'w') as f:
            f.write("mock")
        
        # Test controller
        controller = PinokioController(temp_dir, 42000)
        detected_path = controller.get_pinokio_binary_path()
        
        print(f"Temp dir: {temp_dir}")
        print(f"Created file: {mock_appimage}")
        print(f"Detected path: {detected_path}")
        print(f"File exists: {os.path.exists(detected_path)}")
        
        if detected_path == mock_appimage and os.path.exists(detected_path):
            print("✅ BINARY DETECTION WORKS!")
            return True
        else:
            print("❌ Binary detection failed")
            return False

def test_colab_path():
    """Test with Colab-style path"""
    from pinokio_controller import PinokioController
    
    controller = PinokioController('/content/pinokio', 42000)
    detected_path = controller.get_pinokio_binary_path()
    
    print(f"Colab path detected: {detected_path}")
    print(f"Expected: /content/pinokio/Pinokio-3.9.0.AppImage")
    
    if detected_path == "/content/pinokio/Pinokio-3.9.0.AppImage":
        print("✅ COLAB PATH DETECTION WORKS!")
        return True
    else:
        print("❌ Colab path detection failed")
        return False

if __name__ == "__main__":
    print("🧪 Testing binary detection logic...")
    print("=" * 50)
    
    success = True
    
    print("🔧 Testing with mock AppImage file...")
    if not test_binary_detection():
        success = False
    
    print("\n🔧 Testing with Colab path...")
    if not test_colab_path():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ ALL BINARY DETECTION TESTS PASSED!")
    else:
        print("❌ Binary detection tests failed")
