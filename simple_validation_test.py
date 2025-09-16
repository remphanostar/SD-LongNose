import sys
import os

# Add paths
sys.path.insert(0, 'github_upload/SD-LongNose/modules')

print("COLAB FIX VALIDATION")
print("=" * 40)

# Test 1: Import works
try:
    from pinokio_controller import PinokioController
    print("✅ PinokioController import: SUCCESS")
except Exception as e:
    print(f"❌ Import failed: {e}")
    exit(1)

# Test 2: Method exists
try:
    controller = PinokioController('/content/pinokio', 42000)
    binary_path = controller.get_pinokio_binary_path()
    print(f"✅ get_pinokio_binary_path(): {binary_path}")
except Exception as e:
    print(f"❌ Method call failed: {e}")
    exit(1)

# Test 3: Binary detection logic
try:
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mock versioned AppImage
        mock_file = os.path.join(temp_dir, "Pinokio-3.9.0.AppImage")
        open(mock_file, 'a').close()
        
        controller = PinokioController(temp_dir, 42000)
        detected = controller.get_pinokio_binary_path()
        
        if detected == mock_file:
            print("✅ Binary detection: SUCCESS")
        else:
            print(f"❌ Binary detection failed: {detected}")
            exit(1)
except Exception as e:
    print(f"❌ Binary detection test failed: {e}")
    exit(1)

print("=" * 40)
print("🎉 ALL FIXES VALIDATED!")
print("Colab notebook should now work correctly.")
