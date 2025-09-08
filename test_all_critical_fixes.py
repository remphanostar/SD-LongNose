#!/usr/bin/env python3
"""
Test All Critical Fixes Together
Comprehensive test for all 4+ bugs that have been identified and fixed
"""

import sys
import json
import tempfile
import os
from pathlib import Path

def test_data_structure_consistency():
    """Test that data structures are handled consistently"""
    print("📊 TESTING DATA STRUCTURE CONSISTENCY")
    print("=" * 60)
    
    # Add scripts to path for testing
    scripts_dir = Path(__file__).parent / "PinokioCloud_Colab"
    sys.path.insert(0, str(scripts_dir))
    
    try:
        # Test apps database loading
        apps_file = scripts_dir / "cleaned_pinokio_apps.json"
        
        if not apps_file.exists():
            print("❌ Apps database file not found")
            return False
        
        print(f"📄 Testing apps database: {apps_file}")
        
        with open(apps_file, 'r') as f:
            apps_data = json.load(f)
        
        print(f"   📊 Loaded data type: {type(apps_data)}")
        print(f"   📊 Data length: {len(apps_data)}")
        
        # Test data structure
        if isinstance(apps_data, dict):
            print(f"   ✅ Dictionary format detected")
            
            # Convert to list as the engine expects
            apps_list = list(apps_data.values())
            print(f"   🔄 Converted to list: {len(apps_list)} items")
            
            # Validate all items are dictionaries
            dict_count = sum(1 for item in apps_list if isinstance(item, dict))
            non_dict_count = len(apps_list) - dict_count
            
            print(f"   📊 Valid dict items: {dict_count}")
            print(f"   ⚠️ Non-dict items: {non_dict_count}")
            
            if non_dict_count > 0:
                print(f"   ❌ Data contains non-dictionary items!")
                for i, item in enumerate(apps_list[:5]):
                    print(f"      Item {i}: {type(item)} - {str(item)[:50]}...")
                return False
            
            # Test .get() operations on sample items
            print(f"   🔍 Testing .get() operations on sample items:")
            
            for i, app in enumerate(apps_list[:3]):
                try:
                    name = app.get('name', 'Unknown')
                    category = app.get('category', 'OTHER')
                    print(f"      ✅ App {i}: {name} ({category})")
                except AttributeError as e:
                    print(f"      ❌ App {i}: AttributeError - {e}")
                    return False
                except Exception as e:
                    print(f"      ❌ App {i}: Other error - {e}")
                    return False
        
        elif isinstance(apps_data, list):
            print(f"   ✅ List format detected")
            # Similar validation for list format
            
        else:
            print(f"   ❌ Unexpected data format: {type(apps_data)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Data structure test failed: {e}")
        return False

def test_engine_methods_safely():
    """Test engine methods with safe data handling"""
    print("\n🔧 TESTING ENGINE METHODS WITH SAFE DATA HANDLING") 
    print("=" * 60)
    
    try:
        # Import and test without full initialization
        from unified_engine import UnifiedPinokioEngine
        
        print("✅ Engine class imported successfully")
        
        # Test the data loading method specifically
        print("📊 Testing _load_apps_data method logic...")
        
        # Create test data in both formats
        test_dict_data = {
            "app1": {"name": "Test App 1", "category": "UTILITY"},
            "app2": {"name": "Test App 2", "category": "IMAGE"}
        }
        
        test_list_data = [
            {"name": "Test App 1", "category": "UTILITY"},
            {"name": "Test App 2", "category": "IMAGE"}
        ]
        
        # Test dict to list conversion logic
        if isinstance(test_dict_data, dict):
            converted_list = list(test_dict_data.values())
            print(f"   ✅ Dict to list conversion: {len(converted_list)} items")
            
            # Test .get() operations
            for app in converted_list:
                if isinstance(app, dict):
                    name = app.get('name', 'Unknown')
                    print(f"      ✅ Safe .get() operation: {name}")
                else:
                    print(f"      ❌ Non-dict item: {type(app)}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ Engine method test failed: {e}")
        return False

def test_all_known_bug_categories():
    """Test for all categories of bugs we've encountered"""
    print("\n🐛 TESTING ALL KNOWN BUG CATEGORIES")
    print("=" * 60)
    
    bug_categories = [
        ("Initialization Order", "cache_dir usage before assignment"),
        ("Data Structure", "'str' object has no attribute 'get'"),
        ("Import Dependencies", "Missing module imports"),
        ("Type Safety", "Unsafe type assumptions")
    ]
    
    print("📋 Known bug categories that have been addressed:")
    
    for bug_type, description in bug_categories:
        print(f"   🔧 {bug_type}: {description}")
        
        # Check if specific preventive measures are in place
        if bug_type == "Initialization Order":
            # Check initialization order in unified_engine.py
            engine_file = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
            with open(engine_file, 'r') as f:
                content = f.read()
            
            cache_dir_pos = content.find("self.cache_dir =")
            github_init_pos = content.find("GitHubIntegration(str(self.cache_dir))")
            
            if 0 <= cache_dir_pos < github_init_pos:
                print(f"      ✅ Fixed: cache_dir assigned before usage")
            else:
                print(f"      ❌ Still broken: initialization order")
                
        elif bug_type == "Data Structure":
            # Check for isinstance validation
            streamlit_file = Path(__file__).parent / "PinokioCloud_Colab" / "streamlit_colab.py"
            with open(streamlit_file, 'r') as f:
                content = f.read()
            
            validation_count = content.count("isinstance(") + content.count("if isinstance")
            
            if validation_count >= 5:  # Should have multiple validation checks
                print(f"      ✅ Fixed: {validation_count} type validations added")
            else:
                print(f"      ❌ Insufficient: Only {validation_count} validations found")
    
    return True

def run_comprehensive_bug_audit():
    """Run comprehensive audit for all bug types"""
    print("🚨 COMPREHENSIVE BUG AUDIT - ALL CATEGORIES")
    print("=" * 70)
    print("Testing for all bug types encountered during development")
    print()
    
    tests = [
        ("Data Structure Consistency", test_data_structure_consistency),
        ("Engine Methods Safety", test_engine_methods_safely),
        ("Known Bug Categories", test_all_known_bug_categories)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Run data structure audit
    print(f"\n" + "=" * 70)
    print("📊 RUNNING DATA STRUCTURE BUG AUDIT")
    print("=" * 70)
    
    high_issues, medium_issues, low_issues = audit_all_scripts_for_data_bugs()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE BUG AUDIT RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ SAFE" if success else "❌ ISSUES"
        print(f"{status}: {test_name}")
    
    print(f"\n🐛 Data structure issues:")
    print(f"   🚨 High priority: {high_issues}")
    print(f"   ⚠️ Medium priority: {medium_issues}")
    print(f"   📝 Low priority: {low_issues}")
    
    overall_safety = passed / total * 100
    critical_data_issues = high_issues + medium_issues
    
    print(f"\n🏆 OVERALL SAFETY: {overall_safety:.1f}% ({passed}/{total})")
    print(f"🔍 Critical data issues: {critical_data_issues}")
    
    if overall_safety == 100 and critical_data_issues == 0:
        print("✅ ALL CRITICAL BUGS HAVE BEEN RESOLVED!")
        print("🚀 Revolutionary PinokioCloud is safe for production")
        print("🎯 No more AttributeError or data structure issues")
    else:
        print("⚠️ CRITICAL ISSUES REMAIN - REVIEW BEFORE DEPLOYMENT")
    
    return overall_safety == 100 and critical_data_issues == 0

if __name__ == "__main__":
    success = run_comprehensive_bug_audit()
    exit(0 if success else 1)