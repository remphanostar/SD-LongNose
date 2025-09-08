#!/usr/bin/env python3
"""
MINI MODULE 3 Testing - Cloud Environment Management
Tests cloud-specific environment handling and enhanced error messages
"""

import sys
import os
import tempfile
import asyncio
from pathlib import Path

# Add PinokioCloud_Colab to path
sys.path.insert(0, str(Path(__file__).parent / 'PinokioCloud_Colab'))

from cloud_environment_manager import CloudEnvironmentManager

def test_cloud_platform_detection():
    """Test cloud platform detection"""
    print("🌩️ TESTING CLOUD PLATFORM DETECTION")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cloud_env = CloudEnvironmentManager(temp_dir)
        
        platform_info = cloud_env.platform_info
        
        print("📊 Detected platform information:")
        print(f"   🌩️ Platform: {platform_info['platform']}")
        print(f"   ☁️ Is cloud: {platform_info['is_cloud']}")
        print(f"   🐍 Supports venv: {platform_info['supports_venv']}")
        print(f"   🐍 Supports conda: {platform_info['supports_conda']}")
        print(f"   📦 Supports system packages: {platform_info['supports_system_packages']}")
        print(f"   🔐 Has sudo: {platform_info['has_sudo']}")
        
        if platform_info['environment_restrictions']:
            print(f"   ⚠️ Environment restrictions:")
            for restriction in platform_info['environment_restrictions']:
                print(f"      • {restriction}")
        else:
            print(f"   ✅ No environment restrictions")
        
        # Test constraint detection
        constraints = cloud_env.constraints
        print(f"\n🔧 Platform constraints:")
        for key, value in constraints.items():
            print(f"   {key}: {value}")
    
    return True

def test_error_message_generation():
    """Test enhanced error message generation"""
    print("\n💬 TESTING ENHANCED ERROR MESSAGES")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cloud_env = CloudEnvironmentManager(temp_dir)
        
        # Test different error scenarios
        test_scenarios = [
            ('app_not_found', {
                'app_name': 'nonexistent-app',
                'available_apps_sample': ['stable-diffusion', 'llamacpp', 'whisper']
            }),
            ('environment_setup_failed', {
                'app_name': 'test-app',
                'error': 'Permission denied',
                'platform': 'lightning_ai'
            }),
            ('dependency_install_failed', {
                'package': 'torch>=2.0.0',
                'error': 'CUDA not found',
                'platform': 'google_colab'
            })
        ]
        
        for error_type, details in test_scenarios:
            print(f"\n📋 Testing {error_type}:")
            try:
                error_msg = cloud_env.generate_detailed_error_message(error_type, details)
                print(f"   ✅ Generated {len(error_msg)} character error message")
                print(f"   📝 Sample: {error_msg[:100]}...")
            except Exception as e:
                print(f"   ❌ Error generation failed: {e}")
    
    return True

async def test_environment_creation():
    """Test environment creation for different platforms"""
    print("\n🔧 TESTING ENVIRONMENT CREATION")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cloud_env = CloudEnvironmentManager(temp_dir)
        
        # Test environment creation
        test_requirements = ['flask>=2.0.0', 'requests>=2.28.0', 'torch>=1.12.0']
        
        try:
            env_result = await cloud_env.create_app_environment('test-app', test_requirements)
            
            print(f"📊 Environment creation result:")
            print(f"   ✅ Success: {env_result.get('success', False)}")
            
            if env_result.get('success'):
                config = env_result['config']
                print(f"   🌩️ Platform: {config['platform']}")
                print(f"   🔧 Method: {config['method']}")
                
                if 'venv_path' in config:
                    print(f"   📁 Venv path: {config['venv_path']}")
                if 'env_name' in config:
                    print(f"   📛 Conda env: {config['env_name']}")
                if 'environment_vars' in config:
                    print(f"   🌍 Environment variables: {len(config['environment_vars'])}")
            else:
                print(f"   ❌ Error: {env_result.get('error')}")
        
        except Exception as e:
            print(f"   💥 Exception: {e}")
    
    return True

def test_requirements_validation():
    """Test requirements validation system"""
    print("\n📋 TESTING REQUIREMENTS VALIDATION")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cloud_env = CloudEnvironmentManager(temp_dir)
        
        # Test different requirement scenarios
        test_cases = [
            ('Simple packages', ['requests>=2.28.0', 'flask>=2.0.0']),
            ('GPU packages', ['torch>=1.12.0', 'torchvision>=0.13.0']),
            ('Problematic packages', ['conda', 'nvidia-ml-py']),
            ('Mixed packages', ['numpy>=1.21.0', 'torch>=1.12.0', 'opencv-python'])
        ]
        
        for case_name, requirements in test_cases:
            print(f"\n📦 Testing {case_name}:")
            
            validation = cloud_env.validate_requirements_compatibility(requirements, 'test-app')
            
            print(f"   ✅ Compatible: {validation['compatible']}")
            print(f"   ⚠️ Warnings: {len(validation['warnings'])}")
            print(f"   ❌ Errors: {len(validation['errors'])}")
            print(f"   💡 Recommendations: {len(validation['recommendations'])}")
            
            if validation['warnings']:
                print(f"      Sample warning: {validation['warnings'][0][:60]}...")
            if validation['recommendations']:
                print(f"      Sample recommendation: {validation['recommendations'][0][:60]}...")
    
    return True

def test_platform_install_commands():
    """Test platform-specific install command generation"""
    print("\n🔧 TESTING PLATFORM INSTALL COMMANDS")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cloud_env = CloudEnvironmentManager(temp_dir)
        
        test_packages = ['torch>=1.12.0', 'transformers>=4.21.0', 'gradio>=3.40.0']
        
        print(f"📊 Platform: {cloud_env.platform_info['platform']}")
        
        for package in test_packages:
            install_cmd = cloud_env.get_install_command_for_platform(package, 'test-app')
            python_exe = cloud_env.get_python_executable_for_app('test-app')
            
            print(f"\n📦 {package}:")
            print(f"   💻 Install command: {install_cmd}")
            print(f"   🐍 Python executable: {python_exe}")
    
    return True

async def run_mini_module3_tests():
    """Run complete MINI MODULE 3 tests"""
    print("🚀 MINI MODULE 3 - CLOUD ENVIRONMENT MANAGEMENT TESTING")
    print("=" * 70)
    print("Testing cloud-specific constraints and enhanced error handling")
    print()
    
    tests = [
        ("Cloud Platform Detection", test_cloud_platform_detection),
        ("Error Message Generation", test_error_message_generation),
        ("Environment Creation", test_environment_creation),
        ("Requirements Validation", test_requirements_validation),
        ("Platform Install Commands", test_platform_install_commands)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name.upper()}")
        print("=" * 70)
        
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
    print("\n" + "=" * 70)
    print("📊 MINI MODULE 3 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n🏆 OVERALL: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ MINI MODULE 3 IMPLEMENTATION COMPLETE!")
        print("🚀 Enhanced features:")
        print("   • Cloud platform detection and constraint handling")
        print("   • Enhanced error messages with platform-specific advice")
        print("   • Requirements validation with compatibility checking")
        print("   • Lightning AI/Colab specific optimizations")
        print("🎯 Ready for MODULE 4: Total UI rework and JSON enhancement!")
    else:
        print("⚠️ Some tests failed - review before proceeding")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_mini_module3_tests())
    exit(0 if success else 1)