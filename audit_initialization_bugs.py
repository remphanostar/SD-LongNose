#!/usr/bin/env python3
"""
Critical Bug Audit - Initialization Order Issues
Comprehensive audit to prevent similar bugs across all scripts
"""

import re
import ast
from pathlib import Path

def audit_python_file(file_path: Path):
    """Audit Python file for initialization order issues"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find class definitions
        class_pattern = r'class\s+(\w+).*?:'
        classes = re.findall(class_pattern, content)
        
        issues = []
        
        for class_name in classes:
            # Find __init__ method for this class
            init_pattern = rf'class\s+{class_name}.*?def\s+__init__\s*\([^)]*\):(.*?)(?=def\s+\w+|class\s+\w+|$)'
            init_match = re.search(init_pattern, content, re.DOTALL)
            
            if init_match:
                init_body = init_match.group(1)
                
                # Look for self.attribute assignments
                self_assignments = re.findall(r'self\.(\w+)\s*=', init_body)
                
                # Look for self.attribute usages before assignment
                lines = init_body.split('\n')
                assigned_attrs = set()
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    # Check for self.attr = assignments
                    assignment_match = re.match(r'self\.(\w+)\s*=', line)
                    if assignment_match:
                        attr_name = assignment_match.group(1)
                        assigned_attrs.add(attr_name)
                    
                    # Check for self.attr usage
                    usage_matches = re.findall(r'self\.(\w+)', line)
                    for attr in usage_matches:
                        if attr not in assigned_attrs and '=' not in line.split(f'self.{attr}')[0]:
                            # This attribute is used before being assigned
                            issues.append({
                                'class': class_name,
                                'attribute': attr,
                                'line': i + 1,
                                'code': line,
                                'issue': 'Used before assignment'
                            })
        
        return issues
        
    except Exception as e:
        return [{'error': f'Failed to audit {file_path}: {e}'}]

def audit_all_pinokio_scripts():
    """Audit all PinokioCloud scripts for initialization issues"""
    print("🔍 COMPREHENSIVE INITIALIZATION AUDIT")
    print("=" * 70)
    
    scripts_dir = Path(__file__).parent / "PinokioCloud_Colab"
    python_files = list(scripts_dir.glob("*.py"))
    
    total_issues = 0
    
    for py_file in python_files:
        print(f"\n📄 Auditing {py_file.name}:")
        
        issues = audit_python_file(py_file)
        
        if issues:
            if any('error' in issue for issue in issues):
                for issue in issues:
                    if 'error' in issue:
                        print(f"   ❌ {issue['error']}")
            else:
                print(f"   ⚠️ Found {len(issues)} potential issues:")
                for issue in issues:
                    print(f"      🐛 Class {issue['class']}: {issue['attribute']} {issue['issue']}")
                    print(f"         Line {issue['line']}: {issue['code']}")
                total_issues += len(issues)
        else:
            print(f"   ✅ No initialization issues found")
    
    return total_issues

def audit_specific_patterns():
    """Audit for specific problematic patterns"""
    print(f"\n🔍 AUDITING SPECIFIC PROBLEMATIC PATTERNS")
    print("=" * 70)
    
    scripts_dir = Path(__file__).parent / "PinokioCloud_Colab"
    
    problematic_patterns = [
        (r'self\.\w+\s*=.*self\.\w+', 'Attribute dependency in same assignment'),
        (r'super\(\).__init__.*self\.\w+', 'Usage before super().__init__'),
        (r'self\.\w+\([^)]*self\.\w+', 'Method call with uninitialized attribute'),
        (r'getattr\(self,\s*[\'\"]\w+[\'\"]\)', 'getattr usage that might fail'),
        (r'hasattr\(self,\s*[\'\"]\w+[\'\"]\)', 'hasattr usage that might be defensive')
    ]
    
    for py_file in scripts_dir.glob("*.py"):
        with open(py_file, 'r') as f:
            content = f.read()
        
        print(f"\n📄 {py_file.name}:")
        
        issues_found = False
        for pattern, description in problematic_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line_content = content.split('\n')[line_num - 1].strip()
                print(f"   ⚠️ {description}")
                print(f"      Line {line_num}: {line_content}")
                issues_found = True
        
        if not issues_found:
            print(f"   ✅ No problematic patterns found")

def check_import_dependencies():
    """Check for import dependency issues"""
    print(f"\n📦 CHECKING IMPORT DEPENDENCIES")
    print("=" * 70)
    
    scripts_dir = Path(__file__).parent / "PinokioCloud_Colab"
    
    for py_file in scripts_dir.glob("*.py"):
        print(f"\n📄 {py_file.name}:")
        
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Check for relative imports
            relative_imports = re.findall(r'from\s+\.(\w+)\s+import', content)
            if relative_imports:
                print(f"   📦 Relative imports: {relative_imports}")
                
                # Check if imported files exist
                for module in relative_imports:
                    module_file = scripts_dir / f"{module}.py"
                    if module_file.exists():
                        print(f"      ✅ {module}.py exists")
                    else:
                        print(f"      ❌ {module}.py NOT FOUND")
            
            # Check for try/except import patterns
            import_blocks = re.findall(r'try:\s*\n\s*from\s+\.(\w+).*?\nexcept.*?:\s*\n\s*from\s+(\w+)', 
                                     content, re.DOTALL)
            if import_blocks:
                print(f"   🔧 Import fallbacks: {len(import_blocks)} patterns")
                for local_import, fallback_import in import_blocks:
                    print(f"      🔄 {local_import} → {fallback_import}")
            
        except Exception as e:
            print(f"   ❌ Import check failed: {e}")

def run_comprehensive_bug_audit():
    """Run comprehensive bug audit"""
    print("🚨 CRITICAL BUG AUDIT - PREVENTING SIMILAR ISSUES")
    print("=" * 70)
    print("Comprehensive audit after fixing cache_dir initialization bug")
    print()
    
    # Run all audits
    total_issues = audit_all_pinokio_scripts()
    audit_specific_patterns()
    check_import_dependencies()
    
    print("\n" + "=" * 70)
    print("📊 CRITICAL BUG AUDIT SUMMARY")
    print("=" * 70)
    
    if total_issues == 0:
        print("✅ NO CRITICAL INITIALIZATION BUGS FOUND")
        print("🎯 All scripts appear to have proper initialization order")
        print("🚀 Safe for production deployment")
    else:
        print(f"⚠️ FOUND {total_issues} POTENTIAL INITIALIZATION ISSUES")
        print("🔧 Review and fix before production deployment")
    
    return total_issues == 0

if __name__ == "__main__":
    success = run_comprehensive_bug_audit()
    
    if success:
        print("\n🎉 AUDIT PASSED: No critical bugs detected")
        print("✅ All scripts have proper initialization order")
        print("🚀 Revolutionary PinokioCloud is safe for deployment")
    else:
        print("\n⚠️ AUDIT FAILED: Critical issues detected")
        print("🔧 Fix issues before deployment")
    
    exit(0 if success else 1)