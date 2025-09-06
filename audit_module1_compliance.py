#!/usr/bin/env python3
"""
MODULE 1 COMPLIANCE AUDIT - Against Pinokio.md Specifications
Systematic audit of Script Parser implementation against official specs
"""

import sys
import json
import re
from pathlib import Path

def audit_memory_variables():
    """Audit memory variables implementation against Pinokio.md specs"""
    print("🔍 AUDITING MEMORY VARIABLES COMPLIANCE")
    print("=" * 60)
    
    # Official Pinokio memory variables from Pinokio.md
    official_variables = [
        'input',      # The value passed from the previous step
        'args',       # Parameters passed to the script at launch
        'local',      # Local variables for the current script execution
        'self',       # The script object itself
        'uri',        # The URI of the current script
        'port',       # The next available port
        'cwd',        # The current working directory
        'platform',   # The operating system (darwin, linux, win32)
        'arch',       # The system architecture
        'gpus',       # An array of available GPUs
        'gpu',        # The first available GPU
        'current',    # The index of the current step
        'next',       # The index of the next step
        'envs',       # Environment variables
        'which',      # A utility to check if a command exists
        'kernel',     # The Pinokio kernel JavaScript API
        '_',          # The lodash utility library
        'os',         # The Node.js os module
        'path'        # The Node.js path module
    ]
    
    # Check PinokioContext implementation
    parser_path = Path(__file__).parent / "PinokioCloud_Colab" / "pinokio_parser.py"
    
    if not parser_path.exists():
        print("❌ pinokio_parser.py not found")
        return False
    
    with open(parser_path, 'r') as f:
        parser_content = f.read()
    
    # Check PinokioContext class
    if 'class PinokioContext:' not in parser_content:
        print("❌ PinokioContext class not found")
        return False
    
    print("📋 Checking memory variables implementation:")
    
    implemented_vars = []
    missing_vars = []
    
    for var in official_variables:
        # Check if variable is implemented in context
        patterns = [
            f"self.{var} =",
            f"'{var}':",
            f'"{var}":',
            f"context.{var}",
            f"self.context.{var}"
        ]
        
        found = any(pattern in parser_content for pattern in patterns)
        
        if found:
            implemented_vars.append(var)
            print(f"   ✅ {var}")
        else:
            missing_vars.append(var)
            print(f"   ❌ {var} - NOT IMPLEMENTED")
    
    # Check variable substitution system
    print(f"\n🔧 Variable substitution compliance:")
    substitution_features = [
        'substitute_variables(',     # Main substitution function
        '_resolve_variable_path(',   # Variable path resolution
        'substitute_variables',      # Variable substitution
        'split(.)',                  # Dot notation support
    ]
    
    for feature in substitution_features:
        if feature in parser_content:
            print(f"   ✅ {feature}")
        else:
            print(f"   ❌ {feature} - MISSING")
    
    compliance_rate = len(implemented_vars) / len(official_variables) * 100
    print(f"\n📊 Memory Variables Compliance: {compliance_rate:.1f}% ({len(implemented_vars)}/{len(official_variables)})")
    
    return compliance_rate >= 90  # 90% threshold for compliance

def audit_api_methods():
    """Audit API methods implementation against Pinokio.md specs"""
    print("\n🔍 AUDITING API METHODS COMPLIANCE")
    print("=" * 60)
    
    # Official Pinokio API methods from Pinokio.md
    official_methods = [
        'shell.run',        # Execute shell commands
        'input',            # User input prompts
        'filepicker.open',  # File picker dialog
        'fs.write',         # Write file
        'fs.read',          # Read file
        'fs.rm',            # Remove file/folder
        'fs.copy',          # Copy file/folder
        'fs.download',      # Download file
        'fs.link',          # Virtual drives
        'fs.open',          # Open file in explorer
        'fs.cat',           # Print file contents
        'jump',             # Jump to step
        'local.set',        # Set local variable
        'json.set',         # Set JSON value
        'json.get',         # Get JSON value
        'json.rm',          # Remove JSON key
        'log',              # Print log message
        'net',              # Network requests
        'notify',           # System notification
        'script.download',  # Download script
        'script.start',     # Start script
        'script.stop',      # Stop script
        'script.return',    # Return value
        'web.open',         # Open URL
        'hf.download'       # Hugging Face download
    ]
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    
    if not engine_path.exists():
        print("❌ unified_engine.py not found")
        return False
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    print("📋 Checking API methods implementation:")
    
    implemented_methods = []
    missing_methods = []
    
    for method in official_methods:
        # Check if method is handled in _execute_method
        method_patterns = [
            f"method == '{method}'",
            f'method == "{method}"',
            f"'{method}':",
            f'"{method}":',
            f"method.startswith('{method.split('.')[0]}.')" if '.' in method else f"method == '{method}'"
        ]
        
        found = any(pattern in engine_content for pattern in method_patterns)
        
        if found:
            implemented_methods.append(method)
            print(f"   ✅ {method}")
        else:
            missing_methods.append(method)
            print(f"   ❌ {method} - NOT IMPLEMENTED")
    
    compliance_rate = len(implemented_methods) / len(official_methods) * 100
    print(f"\n📊 API Methods Compliance: {compliance_rate:.1f}% ({len(implemented_methods)}/{len(official_methods)})")
    
    return compliance_rate >= 80  # 80% threshold for API methods

def audit_script_parsing():
    """Audit script parsing compliance"""
    print("\n🔍 AUDITING SCRIPT PARSING COMPLIANCE")
    print("=" * 60)
    
    parser_path = Path(__file__).parent / "PinokioCloud_Colab" / "pinokio_parser.py"
    
    with open(parser_path, 'r') as f:
        parser_content = f.read()
    
    # Check script parsing features from Pinokio.md
    parsing_features = [
        ('JSON Script Support', 'parse_json_script'),
        ('JS Script Support', 'parse_js_script'),
        ('Module.exports Parsing', 'module.exports'),
        ('Version 4.0 Support', '4.0'),
        ('Run Array Processing', 'run.*in.*script_data'),
        ('Daemon Flag Support', 'daemon'),
        ('Env Variables Support', 'env_requirements.*=.*script_data'),
        ('When Conditions', 'evaluate_when_condition'),
        ('Returns Clause', 'returns.*in.*cmd'),
        ('Step Validation', '_validate_run_step'),
        ('Error Handling', 'errors.append'),
        ('Warning System', 'warnings.append')
    ]
    
    print("📋 Checking script parsing features:")
    
    compliant_features = 0
    for feature_name, pattern in parsing_features:
        if re.search(pattern, parser_content):
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / len(parsing_features) * 100
    print(f"\n📊 Script Parsing Compliance: {compliance_rate:.1f}% ({compliant_features}/{len(parsing_features)})")
    
    return compliance_rate >= 90

def audit_shell_run_compliance():
    """Audit shell.run method compliance against Pinokio.md specs"""
    print("\n🔍 AUDITING SHELL.RUN COMPLIANCE")
    print("=" * 60)
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    # Official shell.run parameters from Pinokio.md
    shell_run_params = [
        ('message parameter', 'message.*=.*params\\.get'),
        ('path parameter', 'path.*=.*params\\.get'),
        ('env parameter', 'env.*dict'),
        ('venv parameter', 'venv.*=.*params\\.get'),
        ('conda parameter', 'conda'),
        ('on parameter', 'on.*=.*params\\.get'),
        ('sudo parameter', 'sudo.*=.*params\\.get'),
        ('Array message support', 'isinstance.*messages.*list'),
        ('Working directory', 'cwd.*=.*str'),
        ('Virtual environment', '_execute_in_venv'),
        ('Process execution', 'subprocess')
    ]
    
    print("📋 Checking shell.run parameters:")
    
    compliant_params = 0
    for param_name, pattern in shell_run_params:
        if re.search(pattern, engine_content):
            print(f"   ✅ {param_name}")
            compliant_params += 1
        else:
            print(f"   ❌ {param_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_params / len(shell_run_params) * 100
    print(f"\n📊 Shell.run Compliance: {compliance_rate:.1f}% ({compliant_params}/{len(shell_run_params)})")
    
    return compliance_rate >= 85

def audit_daemon_compliance():
    """Audit daemon process compliance"""
    print("\n🔍 AUDITING DAEMON PROCESS COMPLIANCE")
    print("=" * 60)
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    # Daemon requirements from Pinokio.md
    daemon_features = [
        ('Daemon Flag Recognition', "'daemon'.*script_data\\.get"),
        ('Process Detachment', 'start_new_session.*True'),
        ('Background Execution', 'is_daemon'),
        ('On Handlers', "'on'.*handlers"),
        ('Process Continuation', 'daemon.*true'),
        ('Event Monitoring', 'event.*done'),
        ('PID Tracking', '_last_process_pid'),
        ('Process Management', 'running_processes')
    ]
    
    print("📋 Checking daemon features:")
    
    compliant_features = 0
    for feature_name, pattern in daemon_features:
        if re.search(pattern, engine_content):
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / len(daemon_features) * 100
    print(f"\n📊 Daemon Compliance: {compliance_rate:.1f}% ({compliant_features}/{len(daemon_features)})")
    
    return compliance_rate >= 80

def run_module1_compliance_audit():
    """Run complete MODULE 1 compliance audit"""
    print("🚀 MODULE 1 PINOKIO.MD COMPLIANCE AUDIT")
    print("=" * 70)
    print("Auditing Script Parser implementation against official specifications")
    print()
    
    audit_results = []
    
    # Run all audits
    tests = [
        ("Memory Variables", audit_memory_variables),
        ("API Methods", audit_api_methods),
        ("Script Parsing", audit_script_parsing),
        ("Shell.run Method", audit_shell_run_compliance),
        ("Daemon Processes", audit_daemon_compliance)
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
    print("📊 MODULE 1 COMPLIANCE AUDIT SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in audit_results if success)
    total = len(audit_results)
    
    for test_name, success in audit_results:
        status = "✅ COMPLIANT" if success else "❌ NON-COMPLIANT"
        print(f"{status}: {test_name}")
    
    overall_compliance = passed / total * 100
    print(f"\n🏆 OVERALL MODULE 1 COMPLIANCE: {overall_compliance:.1f}% ({passed}/{total})")
    
    if overall_compliance >= 85:
        print("✅ MODULE 1 MEETS PINOKIO.MD COMPLIANCE STANDARDS!")
        print("🎯 Script Parser follows official Pinokio specifications")
    else:
        print("⚠️ MODULE 1 COMPLIANCE ISSUES DETECTED")
        print("🔧 Requires fixes to meet Pinokio.md standards")
    
    return overall_compliance >= 85

if __name__ == "__main__":
    success = run_module1_compliance_audit()
    exit(0 if success else 1)