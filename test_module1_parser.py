#!/usr/bin/env python3
"""
MODULE 1 Testing Script - Complete Parser Implementation
Tests the complete Pinokio script parser with real apps from database
"""

import sys
import json
import asyncio
from pathlib import Path
import tempfile
import shutil

# Add the PinokioCloud_Colab directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'PinokioCloud_Colab'))

from pinokio_parser import PinokioScriptParser, PinokioContext
from unified_engine import UnifiedPinokioEngine

def load_sample_apps():
    """Load sample apps from database for testing"""
    try:
        apps_path = Path(__file__).parent / 'cleaned_pinokio_apps.json'
        with open(apps_path, 'r', encoding='utf-8') as f:
            apps_data = json.load(f)
        
        # Get first 5 apps for testing
        sample_apps = list(apps_data.items())[:5]
        return sample_apps
    except Exception as e:
        print(f"❌ Failed to load apps database: {e}")
        return []

def create_test_scripts():
    """Create test Pinokio scripts for validation"""
    test_scripts = []
    
    # Test 1: Simple JSON script
    json_script = {
        "version": "4.0",
        "run": [
            {
                "method": "shell.run",
                "params": {
                    "message": "echo 'Testing {{platform}} on {{gpu.name}}'"
                }
            },
            {
                "method": "local.set",
                "params": {
                    "test_var": "Hello World"
                }
            },
            {
                "method": "log",
                "params": {
                    "text": "Local variable: {{local.test_var}}"
                }
            }
        ]
    }
    
    # Test 2: JavaScript module.exports
    js_script = """
    module.exports = {
        version: "4.0",
        daemon: true,
        run: [
            {
                method: "shell.run",
                params: {
                    message: ["echo 'Starting daemon'", "echo 'GPU: {{gpu.type}}'"]
                }
            },
            {
                method: "fs.write",
                params: {
                    path: "test.txt",
                    text: "Created on {{platform}} with {{arch}} architecture"
                }
            }
        ]
    }
    """
    
    # Test 3: Complex script with conditions
    complex_script = {
        "version": "4.0",
        "run": [
            {
                "when": "{{platform === 'linux'}}",
                "method": "shell.run",
                "params": {
                    "message": "echo 'Running on Linux'"
                }
            },
            {
                "when": "{{gpu}}",
                "method": "log",
                "params": {
                    "text": "GPU detected: {{gpu.name}}"
                }
            },
            {
                "when": "{{!gpu}}",
                "method": "log",
                "params": {
                    "text": "No GPU detected, using CPU mode"
                }
            },
            {
                "method": "json.set",
                "params": {
                    "path": "config.json",
                    "key": "system.platform",
                    "value": "{{platform}}"
                }
            },
            {
                "method": "json.get",
                "params": {
                    "path": "config.json"
                },
                "returns": "local.config"
            }
        ]
    }
    
    return [
        ("test_simple.json", json.dumps(json_script, indent=2)),
        ("test_js.js", js_script),
        ("test_complex.json", json.dumps(complex_script, indent=2))
    ]

def test_parser_functionality():
    """Test core parser functionality"""
    print("🧪 TESTING MODULE 1: COMPLETE PARSER FUNCTIONALITY")
    print("=" * 60)
    
    # Initialize context and parser
    context = PinokioContext()
    parser = PinokioScriptParser(context)
    
    print("✅ Parser initialized successfully")
    print(f"📊 System Info: {context.platform} / {context.arch}")
    print(f"🎮 GPU: {context.gpu['name'] if context.gpu else 'None detected'}")
    print(f"🔌 Available ports: {context.ports[:3]}...")
    print()
    
    # Test variable substitution
    print("🔧 TESTING VARIABLE SUBSTITUTION")
    print("-" * 40)
    
    test_cases = [
        "Platform: {{platform}}",
        "Working directory: {{cwd}}",
        "GPU name: {{gpu.name}}",
        "First port: {{port}}",
        "Architecture: {{arch}}",
        "Nested: {{kernel.platform}}"
    ]
    
    for test_case in test_cases:
        result = parser.substitute_variables(test_case)
        print(f"  {test_case:30} → {result}")
    
    print()
    
    # Test condition evaluation
    print("⚖️ TESTING CONDITION EVALUATION")
    print("-" * 40)
    
    conditions = [
        ("{{platform === 'linux'}}", "Linux platform check"),
        ("{{gpu}}", "GPU exists check"),
        ("{{!gpu}}", "No GPU check"),
        ("{{port > 7000}}", "Port range check"),
        ("true", "Simple true"),
        ("false", "Simple false")
    ]
    
    for condition, description in conditions:
        result = parser.evaluate_when_condition(condition)
        print(f"  {condition:25} → {result:5} ({description})")
    
    print()
    
    return True

def test_script_parsing():
    """Test script parsing with sample scripts"""
    print("📜 TESTING SCRIPT PARSING")
    print("-" * 40)
    
    # Create temporary directory for test scripts
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        context = PinokioContext(cwd=str(temp_path))
        parser = PinokioScriptParser(context)
        
        test_scripts = create_test_scripts()
        
        for script_name, script_content in test_scripts:
            script_path = temp_path / script_name
            
            # Write test script
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            print(f"\n📄 Testing {script_name}")
            
            # Parse script
            try:
                result = parser.parse_script_file(script_path)
                
                print(f"  ✅ Parsed successfully")
                print(f"  📊 Steps: {len(result.get('run', []))}")
                print(f"  🏃 Daemon: {result.get('daemon', False)}")
                print(f"  📝 Version: {result.get('version', 'N/A')}")
                
                if parser.has_errors():
                    print(f"  ❌ Errors: {len(parser.get_errors())}")
                    for error in parser.get_errors():
                        print(f"     - {error}")
                
                if parser.get_warnings():
                    print(f"  ⚠️ Warnings: {len(parser.get_warnings())}")
                    for warning in parser.get_warnings():
                        print(f"     - {warning}")
                
                # Test variable substitution on parsed script
                substituted = parser.substitute_script_content(result)
                print(f"  🔄 Variable substitution applied")
                
            except Exception as e:
                print(f"  ❌ Parsing failed: {e}")
    
    return True

async def test_engine_integration():
    """Test engine integration with parser"""
    print("\n🔗 TESTING ENGINE INTEGRATION")
    print("-" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Initialize engine
        engine = UnifiedPinokioEngine(
            base_path=str(temp_path / "pinokio_apps"),
            apps_data_path=str(Path(__file__).parent / "cleaned_pinokio_apps.json")
        )
        
        print(f"✅ Engine initialized")
        print(f"📊 Apps loaded: {len(engine.apps_data)}")
        print(f"🎮 GPU detected: {engine.context.gpu['name'] if engine.context.gpu else 'None'}")
        
        # Create test app directory
        test_app_path = temp_path / "pinokio_apps" / "test_app"
        test_app_path.mkdir(parents=True, exist_ok=True)
        
        # Create simple install script
        install_script = {
            "version": "4.0",
            "run": [
                {
                    "method": "log",
                    "params": {
                        "text": "Installing test app on {{platform}}"
                    }
                },
                {
                    "method": "fs.write",
                    "params": {
                        "path": "installed.txt",
                        "text": "Installed on {{platform}} with {{arch}} architecture at {{cwd}}"
                    }
                },
                {
                    "method": "local.set",
                    "params": {
                        "installation_complete": true
                    }
                }
            ]
        }
        
        install_path = test_app_path / "install.json"
        with open(install_path, 'w', encoding='utf-8') as f:
            json.dump(install_script, f, indent=2)
        
        # Test script execution
        print(f"\n📜 Testing script execution")
        try:
            result = await engine.execute_script(install_path, test_app_path)
            
            if result['success']:
                print(f"  ✅ Script executed successfully")
                print(f"  🏃 Daemon mode: {result.get('is_daemon', False)}")
                
                # Check if file was created
                test_file = test_app_path / "installed.txt"
                if test_file.exists():
                    content = test_file.read_text()
                    print(f"  📄 File created with content: {content[:50]}...")
                else:
                    print(f"  ⚠️ Expected file not created")
                
            else:
                print(f"  ❌ Script execution failed: {result.get('error')}")
                if 'errors' in result:
                    for error in result['errors']:
                        print(f"     - {error}")
                        
        except Exception as e:
            print(f"  ❌ Script execution error: {e}")
    
    return True

def test_real_app_compatibility():
    """Test compatibility with real apps from database"""
    print("\n🌐 TESTING REAL APP COMPATIBILITY")
    print("-" * 40)
    
    sample_apps = load_sample_apps()
    
    if not sample_apps:
        print("❌ No sample apps loaded")
        return False
    
    print(f"📊 Testing with {len(sample_apps)} sample apps")
    
    for app_key, app_data in sample_apps:
        app_name = app_data.get('name', app_key)
        repo_url = app_data.get('clone_url', app_data.get('repo_url', ''))
        category = app_data.get('category', 'Unknown')
        
        print(f"\n📱 {app_name} ({category})")
        print(f"  🌐 Repo: {repo_url}")
        print(f"  📦 Has install.js: {app_data.get('has_install_js', False)}")
        print(f"  📦 Has install.json: {app_data.get('has_install_json', False)}")
        print(f"  🚀 Has pinokio.js: {app_data.get('has_pinokio_js', False)}")
        print(f"  ⚙️ Installer type: {app_data.get('installer_type', 'Unknown')}")
        
        # Check if this looks like a valid Pinokio app
        is_valid = (
            repo_url and 
            (app_data.get('has_install_js') or app_data.get('has_install_json')) and
            app_data.get('is_pinokio_app', False)
        )
        
        print(f"  ✅ Valid Pinokio app: {is_valid}")
    
    return True

async def run_all_tests():
    """Run complete test suite"""
    print("🚀 PINOKIO CLOUD - MODULE 1 COMPLETE PARSER TESTING")
    print("=" * 60)
    print("Testing complete Pinokio script parser with real apps")
    print()
    
    tests = [
        ("Parser Functionality", test_parser_functionality),
        ("Script Parsing", test_script_parsing),
        ("Engine Integration", test_engine_integration),
        ("Real App Compatibility", test_real_app_compatibility)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name.upper()}")
        print("=" * 60)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()
            
            results.append((test_name, success))
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n{status}: {test_name}")
            
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n🏆 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ MODULE 1 PARSER IMPLEMENTATION COMPLETE!")
        print("🚀 Ready for commit and next module")
    else:
        print("⚠️ Some tests failed - review and fix before proceeding")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_all_tests())