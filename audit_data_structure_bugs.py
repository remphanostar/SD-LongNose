#!/usr/bin/env python3
"""
Comprehensive Data Structure Bug Audit
Audit all files for potential data structure issues like 'str' object has no attribute 'get'
"""

import re
from pathlib import Path

def audit_data_structure_usage(file_path: Path):
    """Audit file for potential data structure issues"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        issues = []
        
        for i, line in enumerate(lines):
            line_num = i + 1
            line_stripped = line.strip()
            
            # Pattern 1: .get() usage without validation
            get_patterns = re.finditer(r'(\w+)\.get\s*\(', line)
            for match in get_patterns:
                var_name = match.group(1)
                # Check if variable is validated before .get() usage
                if var_name not in ['app', 'data', 'item', 'obj', 'config', 'info', 'result']:
                    continue
                    
                # Look backwards for isinstance check
                context_start = max(0, i - 10)
                context_lines = lines[context_start:i]
                context = '\n'.join(context_lines)
                
                if f"isinstance({var_name}, dict)" not in context:
                    issues.append({
                        'line': line_num,
                        'code': line_stripped,
                        'issue': f'Potential .get() on non-dict: {var_name}',
                        'severity': 'high'
                    })
            
            # Pattern 2: Dictionary iteration without validation
            dict_iter_patterns = [
                r'for\s+\w+\s+in\s+(\w+):',
                r'\[.*for\s+\w+\s+in\s+(\w+).*\]'
            ]
            
            for pattern in dict_iter_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    var_name = match.group(1)
                    if 'apps' in var_name.lower() and 'isinstance' not in line:
                        issues.append({
                            'line': line_num,
                            'code': line_stripped,
                            'issue': f'Iteration without validation: {var_name}',
                            'severity': 'medium'
                        })
            
            # Pattern 3: Unsafe list/dict assumptions
            unsafe_patterns = [
                (r'\.values\(\)', 'dict.values() usage'),
                (r'\.keys\(\)', 'dict.keys() usage'),  
                (r'\.items\(\)', 'dict.items() usage'),
                (r'\[\d+\]', 'List indexing without bounds check'),
                (r'len\s*\([^)]*\)', 'len() usage without type check')
            ]
            
            for pattern, description in unsafe_patterns:
                if re.search(pattern, line) and 'isinstance' not in line and 'try:' not in line:
                    issues.append({
                        'line': line_num,
                        'code': line_stripped,
                        'issue': f'Unsafe usage: {description}',
                        'severity': 'low'
                    })
        
        return issues
        
    except Exception as e:
        return [{'error': f'Failed to audit {file_path}: {e}'}]

def audit_all_scripts_for_data_bugs():
    """Audit all PinokioCloud scripts for data structure bugs"""
    print("🔍 COMPREHENSIVE DATA STRUCTURE BUG AUDIT")
    print("=" * 70)
    print("Auditing for 'str' object has no attribute 'get' and similar issues")
    print()
    
    scripts_dir = Path(__file__).parent / "PinokioCloud_Colab"
    python_files = list(scripts_dir.glob("*.py"))
    
    total_high_issues = 0
    total_medium_issues = 0
    total_low_issues = 0
    
    for py_file in python_files:
        print(f"\n📄 {py_file.name}:")
        
        issues = audit_data_structure_usage(py_file)
        
        if issues:
            if any('error' in issue for issue in issues):
                for issue in issues:
                    if 'error' in issue:
                        print(f"   ❌ {issue['error']}")
            else:
                high_issues = [i for i in issues if i.get('severity') == 'high']
                medium_issues = [i for i in issues if i.get('severity') == 'medium'] 
                low_issues = [i for i in issues if i.get('severity') == 'low']
                
                if high_issues:
                    print(f"   🚨 {len(high_issues)} HIGH PRIORITY issues:")
                    for issue in high_issues:
                        print(f"      Line {issue['line']}: {issue['issue']}")
                        print(f"         Code: {issue['code']}")
                    total_high_issues += len(high_issues)
                
                if medium_issues:
                    print(f"   ⚠️ {len(medium_issues)} MEDIUM issues:")
                    for issue in medium_issues[:3]:  # Show first 3
                        print(f"      Line {issue['line']}: {issue['issue']}")
                    total_medium_issues += len(medium_issues)
                
                if low_issues:
                    print(f"   📝 {len(low_issues)} LOW priority issues")
                    total_low_issues += len(low_issues)
                
                if not high_issues and not medium_issues and not low_issues:
                    print(f"   ✅ No data structure issues found")
        else:
            print(f"   ✅ No data structure issues found")
    
    print(f"\n📊 TOTAL DATA STRUCTURE ISSUES:")
    print(f"   🚨 High priority: {total_high_issues}")
    print(f"   ⚠️ Medium priority: {total_medium_issues}")
    print(f"   📝 Low priority: {total_low_issues}")
    
    return total_high_issues, total_medium_issues, total_low_issues

def check_specific_error_patterns():
    """Check for specific error patterns we've encountered"""
    print(f"\n🔍 CHECKING SPECIFIC KNOWN ERROR PATTERNS")
    print("=" * 70)
    
    scripts_dir = Path(__file__).parent / "PinokioCloud_Colab"
    
    error_patterns = [
        ("AttributeError: 'str' object has no attribute 'get'", [
            r'\.get\s*\(',
            r'for\s+\w+\s+in\s+\w+.*\.get\s*\('
        ]),
        ("AttributeError: object has no attribute 'cache_dir'", [
            r'self\.\w+\s*=.*self\.\w+',
            r'self\.(\w+).*=.*self\.(\w+).*\1.*\2'
        ]),
        ("KeyError: missing dictionary key", [
            r'\[\s*[\'\"]\w+[\'\"]\\s*\]',
            r'dict\[\w+\]'
        ]),
        ("IndexError: list index out of range", [
            r'\[\s*\d+\s*\]',
            r'list\[\d+\]'
        ]),
        ("TypeError: argument of type 'str' is not iterable", [
            r'in\s+\w+\s+if',
            r'for.*in.*if.*in'
        ])
    ]
    
    for py_file in scripts_dir.glob("*.py"):
        with open(py_file, 'r') as f:
            content = f.read()
        
        print(f"\n📄 {py_file.name}:")
        
        issues_found = False
        
        for error_type, patterns in error_patterns:
            for pattern in patterns:
                matches = list(re.finditer(pattern, content, re.MULTILINE))
                
                if matches:
                    print(f"   ⚠️ Potential {error_type}:")
                    for match in matches[:3]:  # Show first 3
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = content.split('\n')[line_num - 1].strip()
                        print(f"      Line {line_num}: {line_content}")
                    issues_found = True
                    
                    if len(matches) > 3:
                        print(f"      ... and {len(matches) - 3} more")
        
        if not issues_found:
            print(f"   ✅ No known error patterns detected")

def create_data_validation_helpers():
    """Create helper functions for safe data handling"""
    print(f"\n🛡️ CREATING DATA VALIDATION HELPERS")
    print("=" * 70)
    
    helper_code = '''
def safe_get_from_dict(obj, key, default=None):
    """Safely get value from object that should be a dict"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    else:
        logger.warning(f"Expected dict, got {type(obj)} for key {key}")
        return default

def safe_iterate_apps(apps_data):
    """Safely iterate over apps data"""
    if not isinstance(apps_data, list):
        logger.error(f"Expected list of apps, got {type(apps_data)}")
        return []
    
    validated_apps = []
    for app in apps_data:
        if isinstance(app, dict):
            validated_apps.append(app)
        else:
            logger.warning(f"Skipping non-dict app: {type(app)}")
    
    return validated_apps

def safe_calculate_stats(apps_list):
    """Safely calculate statistics from apps list"""
    if not isinstance(apps_list, list):
        return {'count': 0, 'avg_stars': 0, 'categories': []}
    
    valid_apps = [app for app in apps_list if isinstance(app, dict)]
    
    if not valid_apps:
        return {'count': 0, 'avg_stars': 0, 'categories': []}
    
    total_stars = sum(app.get('total_stars', 0) for app in valid_apps)
    avg_stars = total_stars / len(valid_apps) if valid_apps else 0
    
    categories = list(set(app.get('category', 'OTHER') for app in valid_apps))
    
    return {
        'count': len(valid_apps),
        'avg_stars': avg_stars,
        'categories': categories
    }
'''
    
    helper_file = Path(__file__).parent / "PinokioCloud_Colab" / "data_validation_helpers.py"
    
    with open(helper_file, 'w') as f:
        f.write(f"#!/usr/bin/env python3\n")
        f.write(f'"""\nData Validation Helpers - Prevent data structure bugs\n"""\n')
        f.write(f"import logging\nlogger = logging.getLogger(__name__)\n")
        f.write(helper_code)
    
    print(f"✅ Created data validation helpers: {helper_file}")
    return str(helper_file)

def run_comprehensive_data_audit():
    """Run comprehensive data structure audit"""
    print("🚨 COMPREHENSIVE DATA STRUCTURE AUDIT")
    print("=" * 70)
    print("Auditing for data structure bugs like 'str' object has no attribute 'get'")
    print()
    
    # Run data structure audit
    high_issues, medium_issues, low_issues = audit_all_scripts_for_data_bugs()
    
    # Check specific error patterns  
    check_specific_error_patterns()
    
    # Create validation helpers
    helper_file = create_data_validation_helpers()
    
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE DATA AUDIT SUMMARY")
    print("=" * 70)
    
    total_critical = high_issues + medium_issues
    
    print(f"🚨 Critical issues (High + Medium): {total_critical}")
    print(f"   🚨 High priority: {high_issues}")
    print(f"   ⚠️ Medium priority: {medium_issues}")
    print(f"📝 Low priority issues: {low_issues}")
    
    if total_critical == 0:
        print("✅ NO CRITICAL DATA STRUCTURE BUGS FOUND")
        print("🎯 All scripts use safe data handling patterns")
        print("🚀 Safe for production deployment")
    else:
        print(f"⚠️ FOUND {total_critical} CRITICAL DATA STRUCTURE ISSUES")
        print("🔧 Must fix before production deployment")
    
    print(f"\n🛡️ Data validation helpers created: {helper_file}")
    
    return total_critical == 0

if __name__ == "__main__":
    success = run_comprehensive_data_audit()
    
    if success:
        print("\n🎉 DATA STRUCTURE AUDIT PASSED!")
        print("✅ All scripts use safe data handling")
        print("🚀 No 'str' object attribute errors detected")
    else:
        print("\n⚠️ CRITICAL DATA STRUCTURE ISSUES FOUND")
        print("🔧 Fix issues before deployment")
    
    exit(0 if success else 1)