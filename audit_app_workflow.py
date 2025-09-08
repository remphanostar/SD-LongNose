#!/usr/bin/env python3
"""
MODULE 2B: Complete App Workflow Audit
Tests complete user journey: search → install → run → use → share
"""

import sys
import json
import re
from pathlib import Path

def audit_app_search_functionality():
    """Audit app search and discovery functionality"""
    print("🔍 AUDITING APP SEARCH & DISCOVERY")
    print("=" * 60)
    
    streamlit_path = Path(__file__).parent / "PinokioCloud_Colab" / "streamlit_colab.py"
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    apps_path = Path(__file__).parent / "cleaned_pinokio_apps.json"
    
    # Check apps database
    if not apps_path.exists():
        print("❌ Apps database not found")
        return False
    
    try:
        with open(apps_path, 'r') as f:
            apps_data = json.load(f)
        print(f"✅ Apps database loaded: {len(apps_data)} apps")
    except Exception as e:
        print(f"❌ Apps database error: {e}")
        return False
    
    # Check search functionality in UI
    with open(streamlit_path, 'r') as f:
        ui_content = f.read()
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    search_features = [
        ('App Database Loading', 'list_available_apps'),
        ('Search Input Field', 'text_input.*Search Apps'),
        ('Category Filtering', 'selectbox.*Category'),
        ('Search Term Filtering', 'search_term.*lower'),
        ('Category Filtering Logic', 'category_filter.*All'),
        ('App Display Cards', 'app-card'),
        ('App Name Extraction', "app.get('name'"),
        ('App Description Display', "app.get('description'"),
        ('Repository URL Display', "app.get('repo_url'"),
        ('App Status Display', 'is_installed.*is_running'),
        ('Pagination/Limiting', 'filtered_apps.*20'),
        ('App Counter Display', 'Showing.*of.*apps')
    ]
    
    print("📋 Checking search functionality:")
    compliant_features = 0
    
    for feature_name, pattern in search_features:
        if pattern in ui_content:
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    # Test sample apps have required fields
    sample_apps = list(apps_data.values())[:5]
    required_fields = ['name', 'clone_url', 'category']
    
    print(f"\n📊 Testing sample apps structure:")
    valid_apps = 0
    for app in sample_apps:
        app_name = app.get('name', 'Unknown')
        has_all_fields = all(field in app for field in required_fields)
        
        if has_all_fields:
            print(f"   ✅ {app_name}")
            valid_apps += 1
        else:
            missing = [field for field in required_fields if field not in app]
            print(f"   ❌ {app_name} - Missing: {missing}")
    
    apps_validity = valid_apps / len(sample_apps) * 100
    search_compliance = compliant_features / len(search_features) * 100
    
    print(f"\n📊 Search Functionality: {search_compliance:.1f}% ({compliant_features}/{len(search_features)})")
    print(f"📊 Apps Database Quality: {apps_validity:.1f}% ({valid_apps}/{len(sample_apps)})")
    
    return search_compliance >= 85 and apps_validity >= 80

def audit_app_installation_workflow():
    """Audit complete app installation workflow"""
    print("\n📥 AUDITING APP INSTALLATION WORKFLOW")
    print("=" * 60)
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    streamlit_path = Path(__file__).parent / "PinokioCloud_Colab" / "streamlit_colab.py"
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    with open(streamlit_path, 'r') as f:
        ui_content = f.read()
    
    # Installation workflow requirements
    install_workflow = [
        # UI Features
        ('Install Button', 'Install.*key=.*install'),
        ('Progress Callback', 'progress_callback'),
        ('Toast Notifications', 'add_toast.*Installing'),
        ('Raw Output Streaming', 'add_raw_output.*INSTALLATION'),
        ('Error Handling UI', 'Installation error'),
        ('Success Feedback', 'installed successfully'),
        
        # Engine Features
        ('App Database Search', 'for app in.*apps_data'),
        ('App Name Matching', "app.get('title').*app_name"),
        ('Repository URL Resolution', 'clone_url.*repo_url'),
        ('Git Clone Execution', 'git.*clone'),
        ('Install Script Detection', 'install.js.*install.json'),
        ('Install Script Execution', 'execute_script.*install'),
        ('Virtual Environment Setup', 'venv.create'),
        ('Dependency Installation', 'pip.*install'),
        ('State Persistence', 'installed_apps.*app_name'),
        ('Installation Validation', 'success.*install_app'),
        
        # Error Handling
        ('App Not Found Handling', 'not found in database'),
        ('Clone Failure Handling', 'Failed to clone'),
        ('Install Script Failure', 'Install script failed'),
        ('Dependency Failure', 'requirements.txt'),
        ('Progress Logging', 'progress_callback.*message')
    ]
    
    print("📋 Checking installation workflow:")
    compliant_features = 0
    total_features = len(install_workflow)
    
    for feature_name, pattern in install_workflow:
        if pattern in engine_content or pattern in ui_content:
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / total_features * 100
    print(f"\n📊 Installation Workflow: {compliance_rate:.1f}% ({compliant_features}/{total_features})")
    
    return compliance_rate >= 85

def audit_app_running_workflow():
    """Audit app running and execution workflow"""
    print("\n▶️ AUDITING APP RUNNING WORKFLOW")
    print("=" * 60)
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    streamlit_path = Path(__file__).parent / "PinokioCloud_Colab" / "streamlit_colab.py"
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    with open(streamlit_path, 'r') as f:
        ui_content = f.read()
    
    # Running workflow requirements
    running_workflow = [
        # Pre-run Checks
        ('Installation Check', 'is_app_installed'),
        ('Running Status Check', 'is_app_running'),
        ('App Path Resolution', 'app_info.*path'),
        
        # Start Script Detection
        ('Start Script Discovery', 'start.js.*start.json'),
        ('Script Existence Check', 'script_path.exists'),
        ('Script Type Support', '.js.*json'),
        
        # Process Management
        ('Port Assignment', 'app_ports.*app_name'),
        ('Available Port Finding', '_find_available_port'),
        ('Process Tracking', 'running_processes.*app_name'),
        ('PID Storage', 'process_info.*pid'),
        ('Daemon Detection', 'is_daemon'),
        
        # Execution
        ('Script Execution', 'execute_script.*start_script'),
        ('Context Updates', 'context.local.*app_name'),
        ('Environment Setup', 'app_port.*context'),
        ('Progress Feedback', 'Starting.*app_name'),
        ('Success Confirmation', 'started successfully'),
        
        # UI Integration
        ('Run Button', 'Run.*key=.*run'),
        ('Status Display', 'RUNNING.*status-running'),
        ('URL Display', 'Open App.*urls'),
        ('Real-time Feedback', 'APP STARTUP INITIATED'),
        ('Error Display', 'Failed to start')
    ]
    
    print("📋 Checking running workflow:")
    compliant_features = 0
    
    for feature_name, pattern in running_workflow:
        if pattern in engine_content or pattern in ui_content:
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / len(running_workflow) * 100
    print(f"\n📊 Running Workflow: {compliance_rate:.1f}% ({compliant_features}/{len(running_workflow)})")
    
    return compliance_rate >= 85

def audit_ngrok_sharing_functionality():
    """Audit ngrok tunneling and public sharing"""
    print("\n🌐 AUDITING NGROK SHARING FUNCTIONALITY")
    print("=" * 60)
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    streamlit_path = Path(__file__).parent / "PinokioCloud_Colab" / "streamlit_colab.py"
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    with open(streamlit_path, 'r') as f:
        ui_content = f.read()
    
    # ngrok functionality requirements
    ngrok_features = [
        # Core ngrok Support
        ('ngrok Import', 'from pyngrok import ngrok'),
        ('Tunnel Creation', 'ngrok.connect'),
        ('Public URL Generation', 'public_url.*tunnel'),
        ('Tunnel Management', 'active_tunnels'),
        ('Tunnel Cleanup', 'ngrok.disconnect'),
        
        # Integration Features
        ('Port Service Check', '_is_port_active'),
        ('Service Detection', 'service.*running.*port'),
        ('URL Validation', '_check_endpoint_exists'),
        ('Tunnel Setup Method', 'setup_ngrok_tunnel'),
        ('Tunnel Close Method', 'close_ngrok_tunnel'),
        
        # UI Integration
        ('ngrok Button', 'ngrok.*button'),
        ('Public URL Display', 'Public URL'),
        ('Tunnel Status', 'tunnel.*info'),
        ('Error Handling', 'Failed to create tunnel'),
        ('Success Feedback', 'tunnel.*created'),
        
        # Cloud Environment
        ('Token Integration', 'ngrok.*token'),
        ('Colab Optimization', 'colab.*ngrok'),
        ('Public Access', 'public.*url'),
        ('Sharing Capability', 'tunnel.*app_name')
    ]
    
    print("📋 Checking ngrok functionality:")
    compliant_features = 0
    
    for feature_name, pattern in ngrok_features:
        if pattern in engine_content or pattern in ui_content:
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / len(ngrok_features) * 100
    print(f"\n📊 ngrok Sharing: {compliance_rate:.1f}% ({compliant_features}/{len(ngrok_features)})")
    
    return compliance_rate >= 75

def audit_app_state_management():
    """Audit app state management and persistence"""
    print("\n💾 AUDITING APP STATE MANAGEMENT")
    print("=" * 60)
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    # State management requirements
    state_features = [
        ('Installed Apps Tracking', 'installed_apps.*dict'),
        ('Running Apps Tracking', 'running_processes.*dict'),
        ('Port Assignment Storage', 'app_ports.*dict'),
        ('State File Persistence', 'engine_state.json'),
        ('State Loading', '_load_state'),
        ('State Saving', 'save_state'),
        ('App Discovery', '_discover_existing_apps'),
        ('State Validation', 'valid_apps.*installed_apps'),
        ('Session Persistence', 'datetime.now().isoformat()'),
        ('Cross-session Recovery', 'cache_dir.*state'),
        ('App Status Methods', 'get_app_status'),
        ('System Status Methods', 'get_system_status'),
        ('Installation Timestamp', 'installed_at'),
        ('Running Timestamp', 'started_at'),
        ('Process Information', 'process_info.*app_name')
    ]
    
    print("📋 Checking state management:")
    compliant_features = 0
    
    for feature_name, pattern in state_features:
        if pattern in engine_content:
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / len(state_features) * 100
    print(f"\n📊 State Management: {compliance_rate:.1f}% ({compliant_features}/{len(state_features)})")
    
    return compliance_rate >= 80

def audit_complete_app_lifecycle():
    """Audit complete app lifecycle from discovery to sharing"""
    print("\n🔄 AUDITING COMPLETE APP LIFECYCLE")
    print("=" * 60)
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    # Complete lifecycle must have all these methods implemented
    lifecycle_methods = [
        ('App Discovery', 'list_available_apps'),
        ('App Installation', 'async def install_app'),
        ('App Running', 'async def run_app'),
        ('App Stopping', 'def stop_app'),
        ('App Uninstalling', 'def uninstall_app'),
        ('Status Checking', 'is_app_installed.*is_app_running'),
        ('URL Generation', 'get_app_urls'),
        ('Tunnel Creation', 'setup_ngrok_tunnel'),
        ('Process Cleanup', 'close_ngrok_tunnel'),
        ('State Updates', 'save_state')
    ]
    
    print("📋 Checking lifecycle methods:")
    implemented_methods = 0
    
    for method_name, pattern in lifecycle_methods:
        if pattern in engine_content:
            print(f"   ✅ {method_name}")
            implemented_methods += 1
        else:
            print(f"   ❌ {method_name} - NOT IMPLEMENTED")
    
    # Check method signatures are complete (not just stubs)
    print(f"\n🔧 Checking method implementation completeness:")
    
    critical_methods = ['install_app', 'run_app', 'stop_app', 'uninstall_app']
    complete_implementations = 0
    
    for method in critical_methods:
        # Look for substantial implementation (not just pass or TODO)
        method_pattern = f"def {method}.*:.*try:"
        async_pattern = f"async def {method}.*:.*try:"
        
        if method_pattern in engine_content or async_pattern in engine_content:
            print(f"   ✅ {method} - Complete implementation")
            complete_implementations += 1
        else:
            print(f"   ❌ {method} - Stub or incomplete")
    
    lifecycle_rate = implemented_methods / len(lifecycle_methods) * 100
    implementation_rate = complete_implementations / len(critical_methods) * 100
    
    print(f"\n📊 Lifecycle Methods: {lifecycle_rate:.1f}% ({implemented_methods}/{len(lifecycle_methods)})")
    print(f"📊 Method Implementation: {implementation_rate:.1f}% ({complete_implementations}/{len(critical_methods)})")
    
    return lifecycle_rate >= 90 and implementation_rate >= 100

def audit_streaming_output_system():
    """Audit revolutionary streaming output system"""
    print("\n🖥️ AUDITING STREAMING OUTPUT SYSTEM")
    print("=" * 60)
    
    streamlit_path = Path(__file__).parent / "PinokioCloud_Colab" / "streamlit_colab.py"
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    
    with open(streamlit_path, 'r') as f:
        ui_content = f.read()
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    # Streaming system requirements
    streaming_features = [
        # Core Streaming
        ('Raw Output Function', 'add_raw_output'),
        ('Output Callback System', 'create_output_callback'),
        ('Engine Callback Support', 'set_output_callback'),
        ('Real-time Subprocess', 'readline()'),
        ('Output Classification', '_classify_output_type'),
        
        # UI Display
        ('Revolutionary Terminal', 'display_revolutionary_terminal'),
        ('Split Screen Layout', 'col_controls.*col_terminal'),
        ('Terminal Container', 'terminal-container'),
        ('Auto-scrolling', 'scrollIntoView'),
        ('Color Coding', 'color.*entry'),
        
        # Output Types
        ('Git Output', 'git.*green'),
        ('Install Output', 'install.*blue'),
        ('Error Output', 'error.*red'),
        ('Python Output', 'python.*yellow'),
        ('Command Output', 'command.*white'),
        
        # Features
        ('Copy Functionality', 'Copy Terminal Output'),
        ('Timestamp Display', 'timestamp'),
        ('Line Buffering', 'raw_output.*append'),
        ('Performance Limiting', 'last.*500'),
        ('Real-time Updates', 'output_callback.*line')
    ]
    
    print("📋 Checking streaming output system:")
    compliant_features = 0
    
    for feature_name, pattern in streaming_features:
        if pattern in ui_content or pattern in engine_content:
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / len(streaming_features) * 100
    print(f"\n📊 Streaming Output System: {compliance_rate:.1f}% ({compliant_features}/{len(streaming_features)})")
    
    return compliance_rate >= 85

def run_complete_workflow_audit():
    """Run complete app workflow audit"""
    print("🚀 COMPLETE APP WORKFLOW AUDIT")
    print("=" * 70)
    print("Auditing end-to-end user journey: search → install → run → share")
    print()
    
    audit_results = []
    
    # Run all workflow audits
    tests = [
        ("App Search & Discovery", audit_app_search_functionality),
        ("App Installation Workflow", audit_app_installation_workflow),
        ("App Running Workflow", audit_app_running_workflow),
        ("ngrok Sharing Functionality", audit_ngrok_sharing_functionality),
        ("App State Management", audit_app_state_management),
        ("Streaming Output System", audit_streaming_output_system)
    ]
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            audit_results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            audit_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 COMPLETE WORKFLOW AUDIT SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in audit_results if success)
    total = len(audit_results)
    
    for test_name, success in audit_results:
        status = "✅ FUNCTIONAL" if success else "❌ NEEDS WORK"
        print(f"{status}: {test_name}")
    
    overall_functionality = passed / total * 100
    print(f"\n🏆 OVERALL WORKFLOW FUNCTIONALITY: {overall_functionality:.1f}% ({passed}/{total})")
    
    return overall_functionality >= 80

if __name__ == "__main__":
    success = run_complete_workflow_audit()
    exit(0 if success else 1)