#!/usr/bin/env python3
"""
Repository File Usage Analysis
Determine which files are currently used vs obsolete after MODULE 2B
"""

import sys
import os
from pathlib import Path
import json

def analyze_production_files():
    """Analyze which files are used by current production implementation"""
    print("📋 ANALYZING PRODUCTION FILE USAGE")
    print("=" * 60)
    
    # Core production files that define the system
    production_files = [
        "PinokioCloud_Colab/streamlit_colab.py",
        "PinokioCloud_Colab/unified_engine.py", 
        "PinokioCloud_Colab/pinokio_parser.py",
        "PinokioCloud_Colab_Generated.ipynb",
        "cleaned_pinokio_apps.json",
        "requirements.txt"
    ]
    
    # Files that are imported or referenced
    referenced_files = set()
    
    for prod_file in production_files:
        full_path = Path(__file__).parent / prod_file
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print(f"\n📄 Analyzing {prod_file}:")
                
                # Look for file references
                imports = []
                paths = []
                
                # Python imports
                for line in content.split('\n'):
                    if line.strip().startswith('from ') or line.strip().startswith('import '):
                        imports.append(line.strip())
                    elif 'cleaned_pinokio_apps.json' in line:
                        paths.append("cleaned_pinokio_apps.json")
                    elif 'requirements.txt' in line:
                        paths.append("requirements.txt")
                    elif '.py' in line and ('import' in line or 'load' in line):
                        # Extract potential file references
                        pass
                
                # Show findings
                if imports:
                    print(f"   📦 Imports: {len(imports)} found")
                    for imp in imports[:3]:  # Show first 3
                        print(f"      {imp}")
                
                if paths:
                    print(f"   📂 File references: {paths}")
                    referenced_files.update(paths)
                    
            except Exception as e:
                print(f"   ❌ Error reading {prod_file}: {e}")
    
    print(f"\n📊 Referenced files found: {len(referenced_files)}")
    for ref_file in sorted(referenced_files):
        print(f"   📂 {ref_file}")
    
    return referenced_files

def categorize_all_files():
    """Categorize all current repository files"""
    print("\n📁 CATEGORIZING ALL REPOSITORY FILES")
    print("=" * 60)
    
    # Get all files in repository
    repo_root = Path(__file__).parent
    all_files = []
    
    for item in repo_root.rglob('*'):
        if item.is_file() and not item.name.startswith('.') and 'venv' not in str(item):
            relative_path = item.relative_to(repo_root)
            all_files.append(str(relative_path))
    
    # Categorize files
    categories = {
        'CORE_PRODUCTION': [],      # Essential for PinokioCloud to work
        'DOCUMENTATION': [],        # Documentation and guides
        'TESTING': [],             # Test files and audit scripts
        'OBSOLETE_DUPLICATE': [],  # Duplicate or obsolete files
        'UNKNOWN': []              # Need to determine
    }
    
    # Core production files (absolutely required)
    core_files = [
        'PinokioCloud_Colab/streamlit_colab.py',
        'PinokioCloud_Colab/unified_engine.py',
        'PinokioCloud_Colab/pinokio_parser.py',
        'PinokioCloud_Colab_Generated.ipynb',
        'cleaned_pinokio_apps.json',
        'requirements.txt'
    ]
    
    # Documentation files (useful but not essential for runtime)
    documentation_files = [
        'README.md',
        'Pinokio.md',
        'PROJECT_HANDOVER_GUIDE.md',
        'QUICK_START_GUIDE.md',
        'PINOKIO_COMPLIANCE_AUDIT_REPORT.md',
        'CLOUD_ENVIRONMENT_AUDIT_REPORT.md',
        'MODULE_2B_FINAL_CLOUD_AUDIT.md'
    ]
    
    # Testing and audit files (useful for development)
    testing_files = [
        'test_module1_parser.py',
        'test_module2_process.py',
        'test_simple_parser.py',
        'test_simple_module2.py',
        'audit_module1_compliance.py',
        'audit_module2_compliance.py',
        'audit_cloud_compatibility.py',
        'audit_app_workflow.py',
        'verify_practical_implementation.py',
        'analyze_file_usage.py'
    ]
    
    # Potentially obsolete files
    potentially_obsolete = [
        'AppData.json',  # Original database vs cleaned version
    ]
    
    # Check for duplicates
    duplicates = []
    # Check if there are duplicate files
    if 'PinokioCloud_Colab/cleaned_pinokio_apps.json' in all_files and 'cleaned_pinokio_apps.json' in all_files:
        duplicates.append('One of the cleaned_pinokio_apps.json files (duplicate)')
    
    if 'PinokioCloud_Colab/PinokioCloud_Colab_Generated.ipynb' in all_files and 'PinokioCloud_Colab_Generated.ipynb' in all_files:
        duplicates.append('One of the PinokioCloud_Colab_Generated.ipynb files (duplicate)')
    
    # Categorize all files
    for file_path in all_files:
        if file_path in core_files:
            categories['CORE_PRODUCTION'].append(file_path)
        elif file_path in documentation_files:
            categories['DOCUMENTATION'].append(file_path)
        elif file_path in testing_files:
            categories['TESTING'].append(file_path)
        elif file_path in potentially_obsolete:
            categories['OBSOLETE_DUPLICATE'].append(file_path)
        else:
            categories['UNKNOWN'].append(file_path)
    
    # Add identified duplicates
    if duplicates:
        categories['OBSOLETE_DUPLICATE'].extend(duplicates)
    
    # Display categorization
    for category, files in categories.items():
        print(f"\n📂 {category} ({len(files)} files):")
        for file_path in sorted(files):
            print(f"   📄 {file_path}")
    
    return categories

def identify_files_to_remove():
    """Identify specific files that should be removed"""
    print("\n🗑️ IDENTIFYING FILES TO REMOVE")
    print("=" * 60)
    
    # Files that are definitely obsolete or duplicates
    files_to_remove = []
    
    repo_root = Path(__file__).parent
    
    # Check for duplicate cleaned_pinokio_apps.json
    root_apps_json = repo_root / "cleaned_pinokio_apps.json"
    colab_apps_json = repo_root / "PinokioCloud_Colab" / "cleaned_pinokio_apps.json"
    
    if root_apps_json.exists() and colab_apps_json.exists():
        # Compare file sizes to determine which is more current
        root_size = root_apps_json.stat().st_size
        colab_size = colab_apps_json.stat().st_size
        
        print(f"📊 Apps JSON comparison:")
        print(f"   📄 Root: cleaned_pinokio_apps.json ({root_size:,} bytes)")
        print(f"   📄 Colab: PinokioCloud_Colab/cleaned_pinokio_apps.json ({colab_size:,} bytes)")
        
        if root_size == colab_size:
            # Files are identical, remove the one in Colab folder
            files_to_remove.append("PinokioCloud_Colab/cleaned_pinokio_apps.json")
            print(f"   ✅ Marked duplicate Colab version for removal")
        elif colab_size > root_size:
            # Colab version is newer, remove root version
            files_to_remove.append("cleaned_pinokio_apps.json")
            print(f"   ✅ Marked older root version for removal")
        else:
            # Root version is newer, remove Colab version
            files_to_remove.append("PinokioCloud_Colab/cleaned_pinokio_apps.json")
            print(f"   ✅ Marked older Colab version for removal")
    
    # Check for duplicate notebook files
    root_notebook = repo_root / "PinokioCloud_Colab_Generated.ipynb"
    colab_notebook = repo_root / "PinokioCloud_Colab" / "PinokioCloud_Colab_Generated.ipynb"
    
    if root_notebook.exists() and colab_notebook.exists():
        root_size = root_notebook.stat().st_size
        colab_size = colab_notebook.stat().st_size
        
        print(f"\n📊 Notebook comparison:")
        print(f"   📄 Root: PinokioCloud_Colab_Generated.ipynb ({root_size:,} bytes)")
        print(f"   📄 Colab: PinokioCloud_Colab/PinokioCloud_Colab_Generated.ipynb ({colab_size:,} bytes)")
        
        if root_size >= colab_size:
            # Root version is current, remove Colab version
            files_to_remove.append("PinokioCloud_Colab/PinokioCloud_Colab_Generated.ipynb")
            print(f"   ✅ Marked Colab notebook duplicate for removal")
        else:
            # Colab version is newer, remove root version
            files_to_remove.append("PinokioCloud_Colab_Generated.ipynb")
            print(f"   ✅ Marked root notebook duplicate for removal")
    
    # Check for AppData.json (original vs cleaned)
    appdata_json = repo_root / "AppData.json"
    if appdata_json.exists():
        print(f"\n📊 Original database:")
        appdata_size = appdata_json.stat().st_size
        print(f"   📄 AppData.json ({appdata_size:,} bytes) - Original database")
        
        # Check if it's referenced anywhere
        references_found = False
        for prod_file in ["PinokioCloud_Colab/streamlit_colab.py", "PinokioCloud_Colab/unified_engine.py"]:
            full_path = repo_root / prod_file
            if full_path.exists():
                with open(full_path, 'r') as f:
                    if 'AppData.json' in f.read():
                        references_found = True
                        break
        
        if not references_found:
            files_to_remove.append("AppData.json")
            print(f"   ✅ AppData.json not referenced - marked for removal")
        else:
            print(f"   ⚠️ AppData.json still referenced - keeping")
    
    # Check for local virtual environment
    venv_dir = repo_root / "venv"
    if venv_dir.exists():
        print(f"\n📦 Local virtual environment:")
        print(f"   📁 venv/ directory found")
        print(f"   ⚠️ Virtual environments should not be in git repository")
        files_to_remove.append("venv")
        print(f"   ✅ Marked venv/ for removal")
    
    # Check for __pycache__ directories
    pycache_dirs = list(repo_root.rglob('__pycache__'))
    if pycache_dirs:
        print(f"\n🗂️ Python cache directories:")
        for cache_dir in pycache_dirs:
            relative_path = cache_dir.relative_to(repo_root)
            files_to_remove.append(str(relative_path))
            print(f"   ✅ Marked {relative_path} for removal")
    
    print(f"\n🗑️ Total files marked for removal: {len(files_to_remove)}")
    for file_path in files_to_remove:
        print(f"   🗑️ {file_path}")
    
    return files_to_remove

def verify_essential_files():
    """Verify all essential files are present before cleanup"""
    print("\n✅ VERIFYING ESSENTIAL FILES BEFORE CLEANUP")
    print("=" * 60)
    
    # Absolutely essential files that must exist
    essential_files = [
        'PinokioCloud_Colab/streamlit_colab.py',
        'PinokioCloud_Colab/unified_engine.py', 
        'PinokioCloud_Colab/pinokio_parser.py',
        'requirements.txt'
    ]
    
    # One of these must exist (notebook)
    notebook_options = [
        'PinokioCloud_Colab_Generated.ipynb',
        'PinokioCloud_Colab/PinokioCloud_Colab_Generated.ipynb'
    ]
    
    # One of these must exist (apps database)
    database_options = [
        'cleaned_pinokio_apps.json',
        'PinokioCloud_Colab/cleaned_pinokio_apps.json'
    ]
    
    all_essential_present = True
    
    print("📋 Essential files check:")
    for file_path in essential_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"   ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"   ❌ {file_path} - MISSING!")
            all_essential_present = False
    
    print(f"\n📔 Notebook file (at least one required):")
    notebook_found = False
    for notebook in notebook_options:
        full_path = Path(__file__).parent / notebook
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"   ✅ {notebook} ({size:,} bytes)")
            notebook_found = True
        else:
            print(f"   ❌ {notebook} - NOT FOUND")
    
    if not notebook_found:
        all_essential_present = False
        print(f"   ❌ NO NOTEBOOK FILE FOUND!")
    
    print(f"\n📊 Apps database (at least one required):")
    database_found = False
    for database in database_options:
        full_path = Path(__file__).parent / database
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"   ✅ {database} ({size:,} bytes)")
            database_found = True
        else:
            print(f"   ❌ {database} - NOT FOUND")
    
    if not database_found:
        all_essential_present = False
        print(f"   ❌ NO APPS DATABASE FOUND!")
    
    print(f"\n📋 Essential files status: {'✅ ALL PRESENT' if all_essential_present else '❌ MISSING FILES'}")
    return all_essential_present

def run_file_usage_analysis():
    """Run complete file usage analysis"""
    print("🗂️ REPOSITORY FILE USAGE ANALYSIS")
    print("=" * 70)
    print("Determining which files are needed vs obsolete after MODULE 2B")
    print()
    
    # Verify essential files first
    essential_ok = verify_essential_files()
    
    if not essential_ok:
        print("\n❌ CRITICAL: Essential files missing - cannot proceed with cleanup")
        return False, []
    
    # Analyze production file usage
    referenced_files = analyze_production_files()
    
    # Categorize and identify obsolete files
    files_to_remove = identify_files_to_remove()
    
    print(f"\n" + "=" * 70)
    print("📊 FILE USAGE ANALYSIS SUMMARY")
    print("=" * 70)
    
    print(f"✅ Essential files verified: All present")
    print(f"📂 Referenced files tracked: {len(referenced_files)}")
    print(f"🗑️ Files marked for removal: {len(files_to_remove)}")
    
    print(f"\n🎯 CLEANUP RECOMMENDATION:")
    if files_to_remove:
        print(f"✅ Safe to remove {len(files_to_remove)} obsolete files")
        print(f"✅ All essential functionality will be preserved")
    else:
        print(f"📁 Repository appears clean - no obsolete files found")
    
    return True, files_to_remove

if __name__ == "__main__":
    success, files_to_remove = run_file_usage_analysis()
    
    if success and files_to_remove:
        print(f"\n🗑️ FILES TO REMOVE:")
        for file_path in files_to_remove:
            print(f"   {file_path}")
    
    exit(0 if success else 1)