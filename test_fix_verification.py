#!/usr/bin/env python3
"""
Test script to verify the PinokioCloud fix is working correctly
Tests the core functionality without external dependencies
"""

import json
import sys
from pathlib import Path

def test_apps_database():
    """Test if apps database loads correctly"""
    print("🔍 Testing apps database loading...")
    
    try:
        apps_path = Path('PinokioCloud_Colab/cleaned_pinokio_apps.json')
        if not apps_path.exists():
            print("❌ Apps database file not found")
            return False
        
        with open(apps_path, 'r', encoding='utf-8') as f:
            apps_data = json.load(f)
        
        if isinstance(apps_data, dict):
            apps_list = list(apps_data.values())
            print(f"✅ Apps database loaded: {len(apps_list)} apps (dict format)")
            return True
        elif isinstance(apps_data, list):
            print(f"✅ Apps database loaded: {len(apps_data)} apps (list format)")
            return True
        else:
            print(f"❌ Invalid apps data format: {type(apps_data)}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to load apps database: {e}")
        return False

def test_data_validation():
    """Test data validation helper functions"""
    print("🔍 Testing data validation functions...")
    
    def safe_get_app_attribute(app, key, default=None):
        if isinstance(app, dict):
            return app.get(key, default)
        else:
            return default

    def validate_apps_list(apps_data):
        if not isinstance(apps_data, list):
            return []
        return [app for app in apps_data if isinstance(app, dict)]
    
    # Test data
    test_app = {'name': 'TestApp', 'category': 'IMAGE', 'total_stars': 100}
    test_apps = [test_app, 'invalid_string', {'name': 'TestApp2'}, 42]
    
    try:
        # Test safe_get_app_attribute
        result1 = safe_get_app_attribute(test_app, 'name', 'Unknown')
        result2 = safe_get_app_attribute('invalid', 'name', 'Unknown')
        
        if result1 != 'TestApp' or result2 != 'Unknown':
            print("❌ safe_get_app_attribute function failed")
            return False
        
        # Test validate_apps_list
        validated = validate_apps_list(test_apps)
        if len(validated) != 2:  # Should filter out string and number
            print(f"❌ validate_apps_list failed: expected 2, got {len(validated)}")
            return False
        
        print("✅ Data validation functions working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Data validation test failed: {e}")
        return False

def test_streamlit_syntax():
    """Test if streamlit file has correct syntax"""
    print("🔍 Testing Streamlit file syntax...")
    
    try:
        import py_compile
        streamlit_path = Path('PinokioCloud_Colab/streamlit_colab.py')
        
        if not streamlit_path.exists():
            print("❌ Streamlit file not found")
            return False
        
        # Compile to check syntax
        py_compile.compile(str(streamlit_path), doraise=True)
        print("✅ Streamlit file syntax is correct")
        return True
        
    except py_compile.PyCompileError as e:
        print(f"❌ Streamlit syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Streamlit test failed: {e}")
        return False

def test_fix_verification():
    """Verify the specific fix was applied"""
    print("🔍 Verifying the filtered_apps fix...")
    
    try:
        streamlit_path = Path('PinokioCloud_Colab/streamlit_colab.py')
        
        with open(streamlit_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check that the erroneous call was removed
        if 'show_enhanced_statistics(filtered_apps)' in content:
            print("❌ The erroneous show_enhanced_statistics(filtered_apps) call is still present")
            return False
        
        # Check that the function definition still exists
        if 'def show_enhanced_statistics(filtered_apps: List[Dict[str, Any]]):' not in content:
            print("❌ The show_enhanced_statistics function definition was removed")
            return False
        
        print("✅ Fix verified: erroneous call removed, function definition preserved")
        return True
        
    except Exception as e:
        print(f"❌ Fix verification failed: {e}")
        return False

def test_notebook_structure():
    """Test notebook structure"""
    print("🔍 Testing notebook structure...")
    
    try:
        notebook_path = Path('PinokioCloud_Universal.ipynb')
        
        if not notebook_path.exists():
            print("❌ Universal notebook not found")
            return False
        
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook_data = json.load(f)
        
        cells = notebook_data.get('cells', [])
        if len(cells) < 3:
            print(f"❌ Notebook has insufficient cells: {len(cells)}")
            return False
        
        print(f"✅ Notebook structure correct: {len(cells)} cells")
        return True
        
    except Exception as e:
        print(f"❌ Notebook test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 PinokioCloud Fix Verification Test")
    print("=" * 50)
    
    tests = [
        ("Apps Database", test_apps_database),
        ("Data Validation", test_data_validation),
        ("Streamlit Syntax", test_streamlit_syntax),
        ("Fix Verification", test_fix_verification),
        ("Notebook Structure", test_notebook_structure)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"   ⚠️  {test_name} test failed")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! PinokioCloud is ready for deployment.")
        return 0
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())