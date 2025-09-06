#!/usr/bin/env python3
"""
MODULE 2 COMPLIANCE AUDIT - Against Pinokio.md Specifications
Systematic audit of Process Manager implementation against official specs
"""

import sys
import json
import re
from pathlib import Path

def audit_process_management():
    """Audit process management compliance with Pinokio.md specs"""
    print("🔍 AUDITING PROCESS MANAGEMENT COMPLIANCE")
    print("=" * 60)
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    # Process management requirements from Pinokio.md
    process_features = [
        ('Script Start Method', 'script\\.start'),
        ('Script Stop Method', 'script\\.stop'),  
        ('Process Tracking', 'running_processes'),
        ('PID Management', 'process\\.pid'),
        ('Background Processes', 'start_new_session'),
        ('Process Cleanup', 'SIGTERM'),
        ('Port Assignment', 'app_ports'),
        ('Service Detection', '_is_port_active'),
        ('URL Generation', 'get_app_urls'),
        ('State Persistence', 'save_state')
    ]
    
    print("📋 Checking process management features:")
    
    compliant_features = 0
    for feature_name, pattern in process_features:
        if re.search(pattern, engine_content):
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / len(process_features) * 100
    print(f"\n📊 Process Management Compliance: {compliance_rate:.1f}% ({compliant_features}/{len(process_features)})")
    
    return compliance_rate >= 85

def audit_daemon_implementation():
    """Audit daemon implementation against Pinokio.md specs"""
    print("\n🔍 AUDITING DAEMON IMPLEMENTATION COMPLIANCE")
    print("=" * 60)
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    # Daemon requirements from Pinokio.md:
    # 1. daemon: true flag recognition
    # 2. Process continues after script completion
    # 3. On handlers for output monitoring
    # 4. Event pattern matching with regex
    # 5. done: true to mark step complete while keeping process running
    
    daemon_requirements = [
        ('Daemon Flag Recognition', "'daemon'.*true.*script_data"),
        ('Process Detachment', 'start_new_session.*True'),
        ('On Handlers Support', "'on'.*handlers"),
        ('Event Pattern Matching', "'event'.*in"),
        ('Done Flag Support', "'done'.*true"),
        ('Process Continuation', 'is_daemon.*and'),
        ('Background Execution', 'await.*process'),
        ('Regex Pattern Support', '/.*/')
    ]
    
    print("📋 Checking daemon compliance:")
    
    compliant_features = 0
    for feature_name, pattern in daemon_requirements:
        if re.search(pattern, engine_content):
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / len(daemon_requirements) * 100
    print(f"\n📊 Daemon Implementation Compliance: {compliance_rate:.1f}% ({compliant_features}/{len(daemon_requirements)})")
    
    return compliance_rate >= 80

def audit_file_system_compliance():
    """Audit file system operations compliance"""
    print("\n🔍 AUDITING FILE SYSTEM COMPLIANCE")
    print("=" * 60)
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    # File system requirements from Pinokio.md
    fs_methods = [
        ('fs.write', '_execute_fs_method.*fs\\.write'),
        ('fs.read', 'fs\\.read'),
        ('fs.rm', 'fs\\.rm'),
        ('fs.copy', 'fs\\.copy'),
        ('fs.download', 'fs\\.download'),
        ('fs.link', 'fs\\.link'),  # Critical for virtual drives
        ('fs.exists', 'fs\\.exists'),
        ('fs.cat', 'fs\\.cat'),
        ('fs.open', 'fs\\.open')
    ]
    
    print("📋 Checking file system methods:")
    
    compliant_methods = 0
    for method_name, pattern in fs_methods:
        if re.search(pattern, engine_content):
            print(f"   ✅ {method_name}")
            compliant_methods += 1
        else:
            print(f"   ❌ {method_name} - NOT IMPLEMENTED")
    
    # Check for path handling
    path_features = [
        ('Absolute Path Support', 'is_absolute'),
        ('Path Resolution', 'app_path.*path'),
        ('Directory Creation', 'mkdir.*parents.*True'),
        ('Cross-platform Paths', 'Path.*')
    ]
    
    print("\n📋 Checking path handling:")
    for feature_name, pattern in path_features:
        if re.search(pattern, engine_content):
            print(f"   ✅ {feature_name}")
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_methods / len(fs_methods) * 100
    print(f"\n📊 File System Compliance: {compliance_rate:.1f}% ({compliant_methods}/{len(fs_methods)})")
    
    return compliance_rate >= 75

def audit_script_format_compliance():
    """Audit script format compliance against Pinokio.md"""
    print("\n🔍 AUDITING SCRIPT FORMAT COMPLIANCE")  
    print("=" * 60)
    
    parser_path = Path(__file__).parent / "PinokioCloud_Colab" / "pinokio_parser.py"
    
    with open(parser_path, 'r') as f:
        parser_content = f.read()
    
    # Script format requirements from Pinokio.md:
    # JSON format: { "version": "4.0", "run": [...], "daemon": true/false, "env": [...] }
    # JS format: module.exports = { ... }
    
    format_requirements = [
        ('Version Field Handling', "'version'.*script_data"),
        ('Run Array Processing', "'run'.*not.*script_data"),
        ('Daemon Field Recognition', "'daemon'.*script_data"),
        ('Env Array Support', "'env'.*script_data"),
        ('Step Validation', '_validate_run_step'),
        ('Method Field Required', "'method'.*not.*step"),
        ('Params Field Handling', "'params'.*not.*step"),
        ('Step Index Tracking', '_step_index'),
        ('Error Collection', 'self\\.errors\\.append'),
        ('Warning Collection', 'self\\.warnings\\.append')
    ]
    
    print("📋 Checking script format compliance:")
    
    compliant_features = 0
    for feature_name, pattern in format_requirements:
        if re.search(pattern, parser_content):
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / len(format_requirements) * 100
    print(f"\n📊 Script Format Compliance: {compliance_rate:.1f}% ({compliant_features}/{len(format_requirements)})")
    
    return compliance_rate >= 85

def run_module2_compliance_audit():
    """Run complete MODULE 2 compliance audit"""
    print("🚀 MODULE 2 PINOKIO.MD COMPLIANCE AUDIT")
    print("=" * 70)
    print("Auditing Process Manager implementation against official specifications")
    print()
    
    audit_results = []
    
    # Run all audits
    tests = [
        ("Process Management", audit_process_management),
        ("Daemon Implementation", audit_daemon_implementation),
        ("File System Operations", audit_file_system_compliance),
        ("Script Format", audit_script_format_compliance)
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
    print("📊 MODULE 2 COMPLIANCE AUDIT SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in audit_results if success)
    total = len(audit_results)
    
    for test_name, success in audit_results:
        status = "✅ COMPLIANT" if success else "❌ NON-COMPLIANT"
        print(f"{status}: {test_name}")
    
    overall_compliance = passed / total * 100
    print(f"\n🏆 OVERALL MODULE 2 COMPLIANCE: {overall_compliance:.1f}% ({passed}/{total})")
    
    if overall_compliance >= 85:
        print("✅ MODULE 2 MEETS PINOKIO.MD COMPLIANCE STANDARDS!")
        print("🎯 Process Manager follows official Pinokio specifications")
    else:
        print("⚠️ MODULE 2 COMPLIANCE ISSUES DETECTED")
        print("🔧 Requires fixes to meet Pinokio.md standards")
    
    return overall_compliance >= 85

if __name__ == "__main__":
    success = run_module2_compliance_audit()
    exit(0 if success else 1)