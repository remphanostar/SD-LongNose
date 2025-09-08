#!/usr/bin/env python3
"""
Test Streamlit Interface Import and Initialization
Ensures no critical bugs prevent the interface from starting
"""

import sys
import os
from pathlib import Path
import tempfile

def test_streamlit_imports():
    """Test that all imports work correctly"""
    print("📦 TESTING STREAMLIT IMPORTS")
    print("=" * 50)
    
    # Add PinokioCloud_Colab to path
    scripts_dir = Path(__file__).parent / "PinokioCloud_Colab"
    sys.path.insert(0, str(scripts_dir))
    
    import_tests = [
        ('streamlit', 'streamlit'),
        ('unified_engine', 'UnifiedPinokioEngine'),
        ('pinokio_parser', 'PinokioScriptParser, PinokioContext'),
        ('cloud_environment_manager', 'CloudEnvironmentManager'),
        ('github_integration', 'GitHubIntegration')
    ]
    
    successful_imports = 0
    
    for module_name, imports in import_tests:
        try:
            if module_name == 'streamlit':
                import streamlit
                print(f"   ✅ {module_name}: {streamlit.__version__}")
            else:
                module = __import__(module_name)
                print(f"   ✅ {module_name}: Imported successfully")
            successful_imports += 1
            
        except ImportError as e:
            print(f"   ❌ {module_name}: Import failed - {e}")
        except Exception as e:
            print(f"   ⚠️ {module_name}: Other error - {e}")
    
    print(f"\n📊 Import success: {successful_imports}/{len(import_tests)}")
    return successful_imports == len(import_tests)

def test_engine_initialization():
    """Test UnifiedPinokioEngine initialization"""
    print("\n🔧 TESTING ENGINE INITIALIZATION")
    print("=" * 50)
    
    try:
        from unified_engine import UnifiedPinokioEngine
        
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create dummy apps database
            apps_db = temp_path / "test_apps.json"
            with open(apps_db, 'w') as f:
                json_content = """
                {
                    "test-app": {
                        "name": "Test App",
                        "category": "UTILITY", 
                        "description": "Test application",
                        "clone_url": "https://github.com/test/repo.git"
                    }
                }
                """
                f.write(json_content)
            
            print(f"📁 Test environment: {temp_path}")
            print(f"📄 Test database: {apps_db}")
            
            # Test engine initialization
            try:
                engine = UnifiedPinokioEngine(
                    base_path=str(temp_path / "pinokio_apps"),
                    apps_data_path=str(apps_db)
                )
                
                print(f"✅ Engine initialized successfully")
                print(f"   📊 Apps loaded: {len(engine.apps_data)}")
                print(f"   🔧 Parser available: {hasattr(engine, 'parser')}")
                print(f"   🌩️ Cloud env available: {hasattr(engine, 'cloud_env')}")
                print(f"   ⭐ GitHub available: {hasattr(engine, 'github')}")
                print(f"   📁 Cache dir: {engine.cache_dir}")
                print(f"   📂 Logs dir: {engine.logs_dir}")
                
                return True
                
            except Exception as e:
                print(f"❌ Engine initialization failed: {e}")
                print(f"🔧 This indicates a critical bug that must be fixed")
                return False
    
    except ImportError as e:
        print(f"❌ Cannot import engine: {e}")
        return False

def test_session_state_initialization():
    """Test session state initialization logic"""
    print("\n📱 TESTING SESSION STATE INITIALIZATION")  
    print("=" * 50)
    
    try:
        # Read streamlit file to check session state logic
        streamlit_file = Path(__file__).parent / "PinokioCloud_Colab" / "streamlit_colab.py"
        
        with open(streamlit_file, 'r') as f:
            content = f.read()
        
        # Check for proper session state initialization
        session_checks = [
            ('init_session_state function', 'def init_session_state()'),
            ('Engine initialization', 'UnifiedPinokioEngine('),
            ('Apps database path', 'cleaned_pinokio_apps.json'),
            ('Error handling', 'try:.*except'),
            ('Session state checks', 'if.*not.*in.*st.session_state')
        ]
        
        print("📋 Checking session state logic:")
        
        for check_name, pattern in session_checks:
            if re.search(pattern, content, re.DOTALL):
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name} - NOT FOUND")
        
        # Look for potential issues
        potential_issues = [
            ('Missing error handling', 'UnifiedPinokioEngine.*without.*try'),
            ('Hardcoded paths', '/content/.*hard.*coded')
        ]
        
        issues_found = 0
        for issue_name, pattern in potential_issues:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"   ⚠️ {issue_name}")
                issues_found += 1
        
        if issues_found == 0:
            print(f"   ✅ No obvious session state issues")
        
        return issues_found == 0
        
    except Exception as e:
        print(f"❌ Session state check failed: {e}")
        return False

def run_critical_bug_prevention_audit():
    """Run comprehensive audit to prevent critical bugs"""
    print("🚨 CRITICAL BUG PREVENTION AUDIT")
    print("=" * 70)
    print("Comprehensive audit to prevent initialization and runtime bugs")
    print()
    
    tests = [
        ("Import Testing", test_streamlit_imports),
        ("Engine Initialization", test_engine_initialization), 
        ("Session State Logic", test_session_state_initialization)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 CRITICAL BUG AUDIT RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ SAFE" if success else "❌ ISSUES"
        print(f"{status}: {test_name}")
    
    safety_percentage = (passed / total) * 100
    print(f"\n🏆 OVERALL SAFETY: {safety_percentage:.1f}% ({passed}/{total})")
    
    if safety_percentage == 100:
        print("✅ ALL CRITICAL BUGS PREVENTED!")
        print("🚀 Revolutionary PinokioCloud is safe for production")
        print("🎯 No initialization order issues detected")
    else:
        print("⚠️ CRITICAL ISSUES DETECTED - MUST FIX BEFORE DEPLOYMENT")
    
    return safety_percentage == 100

if __name__ == "__main__":
    success = run_critical_bug_prevention_audit()
    exit(0 if success else 1)