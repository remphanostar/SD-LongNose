#!/usr/bin/env python3
"""
MODULE 2B: Cloud GPU Environment Compatibility Audit
Tests compatibility with Colab, Vast.AI, Lightning AI, and other cloud platforms
"""

import sys
import os
import json
from pathlib import Path
import tempfile
import subprocess

def audit_colab_compatibility():
    """Audit Google Colab specific compatibility"""
    print("☁️ AUDITING GOOGLE COLAB COMPATIBILITY")
    print("=" * 60)
    
    # Check Colab-specific implementations
    streamlit_path = Path(__file__).parent / "PinokioCloud_Colab" / "streamlit_colab.py"
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    
    if not streamlit_path.exists():
        print("❌ streamlit_colab.py not found")
        return False
    
    with open(streamlit_path, 'r') as f:
        streamlit_content = f.read()
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    combined_content = streamlit_content + engine_content
    
    # Colab-specific features that must be implemented
    colab_features = [
        ('Google Colab Detection', "'google.colab' in sys.modules"),
        ('Colab Path Handling', '/content/'),
        ('Colab Base Path Setup', 'BASE_PATH.*content'),
        ('Colab Apps Path', '/content/SD-LongNose/'),
        ('Colab JSON Path', '/content/SD-LongNose/PinokioCloud_Colab/cleaned_pinokio_apps.json'),
        ('Colab GPU Environment', "COLAB.*=.*'1'"),
        ('CUDA Environment Setup', 'CUDA_VISIBLE_DEVICES'),
        ('Colab Directory Structure', '/content/pinokio_apps'),
        ('Absolute Path Support', 'is_absolute()'),
        ('Colab Initialization', 'if.*google.colab')
    ]
    
    print("📋 Checking Colab-specific features:")
    compliant_features = 0
    
    for feature_name, pattern in colab_features:
        if pattern in combined_content:
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / len(colab_features) * 100
    print(f"\n📊 Colab Compatibility: {compliance_rate:.1f}% ({compliant_features}/{len(colab_features)})")
    
    return compliance_rate >= 80

def audit_vast_ai_compatibility():
    """Audit Vast.AI and similar cloud platform compatibility"""
    print("\n🖥️ AUDITING VAST.AI/CLOUD PLATFORM COMPATIBILITY")
    print("=" * 60)
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    
    with open(engine_path, 'r') as f:
        engine_content = f.read()
    
    # Features needed for cloud platforms
    cloud_features = [
        ('Environment Detection', 'platform.system()'),
        ('GPU Detection', 'nvidia-smi'),
        ('Flexible Base Paths', 'base_path.*=.*Path'),
        ('Environment Variables', 'os.environ'),
        ('Process Management', 'subprocess'),
        ('Port Management', '_find_available_port'),
        ('Virtual Environment', 'venv.create'),
        ('Dependency Installation', 'pip.*install'),
        ('Git Clone Support', 'git.*clone'),
        ('Network Requests', 'requests.get'),
        ('File System Operations', 'shutil'),
        ('Cross-platform Paths', 'Path.*/')
    ]
    
    print("📋 Checking cloud platform features:")
    compliant_features = 0
    
    for feature_name, pattern in cloud_features:
        if pattern in engine_content:
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / len(cloud_features) * 100
    print(f"\n📊 Cloud Platform Compatibility: {compliance_rate:.1f}% ({compliant_features}/{len(cloud_features)})")
    
    return compliance_rate >= 85

def audit_jupyter_notebook_integration():
    """Audit Jupyter notebook integration"""
    print("\n📔 AUDITING JUPYTER NOTEBOOK INTEGRATION")
    print("=" * 60)
    
    # Check the actual notebook file
    notebook_path = Path(__file__).parent / "PinokioCloud_Colab_Generated.ipynb"
    
    if not notebook_path.exists():
        print("❌ PinokioCloud_Colab_Generated.ipynb not found")
        return False
    
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook_content = f.read()
            notebook_data = json.loads(notebook_content)
    except Exception as e:
        print(f"❌ Failed to load notebook: {e}")
        return False
    
    # Notebook structure requirements
    notebook_features = [
        ('Notebook Format', 'cells' in notebook_data),
        ('GitHub Clone Cell', 'git clone' in notebook_content),
        ('Dependency Install Cell', 'pip install' in notebook_content),
        ('Streamlit Launch Cell', 'streamlit run' in notebook_content),
        ('ngrok Setup', 'ngrok' in notebook_content),
        ('Base Path Setup', '/content/' in notebook_content),
        ('Colab Detection', 'google.colab' in notebook_content),
        ('Repository URL', 'github.com' in notebook_content),
        ('Auto-execution Flow', '#@title' in notebook_content),
        ('Error Handling', 'try:' in notebook_content or 'except' in notebook_content)
    ]
    
    print("📋 Checking notebook integration:")
    compliant_features = 0
    
    for feature_name, condition in notebook_features:
        if condition:
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    # Check cell count and structure
    if 'cells' in notebook_data:
        cell_count = len(notebook_data['cells'])
        print(f"\n📊 Notebook structure: {cell_count} cells")
        
        # Check for proper cell types
        code_cells = sum(1 for cell in notebook_data['cells'] if cell.get('cell_type') == 'code')
        markdown_cells = sum(1 for cell in notebook_data['cells'] if cell.get('cell_type') == 'markdown')
        
        print(f"   📝 Code cells: {code_cells}")
        print(f"   📄 Markdown cells: {markdown_cells}")
        
        if code_cells >= 2:  # Should have setup + launch cells minimum
            print(f"   ✅ Sufficient code cells for workflow")
        else:
            print(f"   ⚠️ May need more code cells for complete workflow")
    
    compliance_rate = compliant_features / len(notebook_features) * 100
    print(f"\n📊 Notebook Integration: {compliance_rate:.1f}% ({compliant_features}/{len(notebook_features)})")
    
    return compliance_rate >= 80

def audit_github_workflow():
    """Audit GitHub repository cloning and import workflow"""
    print("\n🐙 AUDITING GITHUB WORKFLOW INTEGRATION")
    print("=" * 60)
    
    # Check all files for GitHub workflow support
    files_to_check = [
        "PinokioCloud_Colab/unified_engine.py",
        "PinokioCloud_Colab/streamlit_colab.py", 
        "PinokioCloud_Colab_Generated.ipynb"
    ]
    
    github_workflow_features = []
    
    for file_path in files_to_check:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for GitHub-related features
            if 'github.com' in content:
                github_workflow_features.append(f"GitHub URL handling in {file_path}")
            if 'git clone' in content:
                github_workflow_features.append(f"Git clone support in {file_path}")
            if 'clone_url' in content:
                github_workflow_features.append(f"Clone URL processing in {file_path}")
            if 'repo_url' in content:
                github_workflow_features.append(f"Repository URL handling in {file_path}")
    
    print("📋 GitHub workflow features found:")
    for feature in github_workflow_features:
        print(f"   ✅ {feature}")
    
    # Check specific GitHub integration requirements
    github_requirements = [
        ('Repository Cloning', len([f for f in github_workflow_features if 'clone' in f]) > 0),
        ('URL Processing', len([f for f in github_workflow_features if 'url' in f]) > 0),
        ('Multi-file Integration', len(github_workflow_features) >= 3),
        ('Notebook Integration', any('ipynb' in f for f in github_workflow_features)),
        ('Engine Integration', any('unified_engine' in f for f in github_workflow_features))
    ]
    
    compliant_reqs = 0
    print("\n📋 GitHub integration requirements:")
    
    for req_name, is_met in github_requirements:
        if is_met:
            print(f"   ✅ {req_name}")
            compliant_reqs += 1
        else:
            print(f"   ❌ {req_name} - NOT MET")
    
    compliance_rate = compliant_reqs / len(github_requirements) * 100
    print(f"\n📊 GitHub Workflow: {compliance_rate:.1f}% ({compliant_reqs}/{len(github_requirements)})")
    
    return compliance_rate >= 80

def audit_gpu_optimization():
    """Audit GPU detection and optimization features"""
    print("\n🎮 AUDITING GPU OPTIMIZATION")
    print("=" * 60)
    
    engine_path = Path(__file__).parent / "PinokioCloud_Colab" / "unified_engine.py"
    parser_path = Path(__file__).parent / "PinokioCloud_Colab" / "pinokio_parser.py"
    
    gpu_content = ""
    for path in [engine_path, parser_path]:
        if path.exists():
            with open(path, 'r') as f:
                gpu_content += f.read()
    
    # GPU optimization features required for cloud environments
    gpu_features = [
        ('NVIDIA GPU Detection', 'nvidia-smi'),
        ('GPU Memory Detection', 'memory.total'),
        ('GPU Model Detection', 'query-gpu=name'),
        ('CUDA Environment', 'CUDA_VISIBLE_DEVICES'),
        ('GPU Context Variables', 'gpu.*gpu_model'),
        ('Multiple GPU Support', 'gpus.*detected'),
        ('GPU Type Classification', 'nvidia.*amd.*apple'),
        ('Hardware Context', '_detect_hardware'),
        ('GPU Fallback', 'Fallback.*CPU'),
        ('Cloud GPU Optimization', 'google.colab.*gpu')
    ]
    
    print("📋 Checking GPU optimization features:")
    compliant_features = 0
    
    for feature_name, pattern in gpu_features:
        if pattern in gpu_content:
            print(f"   ✅ {feature_name}")
            compliant_features += 1
        else:
            print(f"   ❌ {feature_name} - NOT IMPLEMENTED")
    
    compliance_rate = compliant_features / len(gpu_features) * 100
    print(f"\n📊 GPU Optimization: {compliance_rate:.1f}% ({compliant_features}/{len(gpu_features)})")
    
    return compliance_rate >= 75

def run_cloud_compatibility_audit():
    """Run complete cloud environment compatibility audit"""
    print("🚀 CLOUD GPU ENVIRONMENT COMPATIBILITY AUDIT")
    print("=" * 70)
    print("Auditing compatibility with Colab, Vast.AI, Lightning AI, etc.")
    print()
    
    audit_results = []
    
    # Run all cloud audits
    tests = [
        ("Google Colab Compatibility", audit_colab_compatibility),
        ("Cloud Platform Compatibility", audit_vast_ai_compatibility),
        ("Jupyter Notebook Integration", audit_jupyter_notebook_integration),
        ("GitHub Workflow", audit_github_workflow),
        ("GPU Optimization", audit_gpu_optimization)
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
    print("📊 CLOUD COMPATIBILITY AUDIT SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in audit_results if success)
    total = len(audit_results)
    
    for test_name, success in audit_results:
        status = "✅ COMPATIBLE" if success else "❌ ISSUES DETECTED"
        print(f"{status}: {test_name}")
    
    overall_compatibility = passed / total * 100
    print(f"\n🏆 OVERALL CLOUD COMPATIBILITY: {overall_compatibility:.1f}% ({passed}/{total})")
    
    return overall_compatibility >= 80

if __name__ == "__main__":
    success = run_cloud_compatibility_audit()
    exit(0 if success else 1)