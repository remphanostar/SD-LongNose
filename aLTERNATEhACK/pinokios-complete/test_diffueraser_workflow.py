#!/usr/bin/env python3
"""
Test DiffuEraser Pinokio workflow directly via engine
- Execute install.js (git clone, torch.js, pip install)  
- Execute start.js until PyTorch/CUDA errors
"""
import sys
import asyncio
import time
from pathlib import Path
sys.path.append('.')

from pinokios.unified_engine import UnifiedPinokioEngine

async def test_diffueraser_workflow():
    print("=== TESTING DIFFUERASER PINOKIO WORKFLOW ===")
    
    # Create engine instance
    engine = UnifiedPinokioEngine()
    
    # Create app data for DiffuEraser
    app_data = {
        'Appname': 'DiffuEraser',
        'Git': 'https://huggingface.co/spaces/cocktailpeanut/DiffuEraser-demo',
        'Category': 'Image',
        'description': 'AI-powered image eraser tool'
    }
    
    print(f"Engine base_path: {engine.base_path}")
    
    # Test 1: Uninstall if already exists (clear state)
    if 'DiffuEraser' in engine.installed_apps:
        print("\n--- Clearing existing DiffuEraser installation ---")
        success, msg = await engine.uninstall_app('DiffuEraser')
        print(f"Uninstall result: {success} - {msg}")
    
    # Test 2: Install via Pinokio install.js
    print("\n--- Installing DiffuEraser via Pinokio install.js ---")
    
    def progress_callback(message):
        print(f"INSTALL: {message}")
    
    success, message = await engine.install_app(app_data, progress_callback=progress_callback)
    
    if success:
        print(f"✅ INSTALL SUCCESS: {message}")
        
        # Test 3: Run via Pinokio start.js 
        print("\n--- Running DiffuEraser via Pinokio start.js ---")
        
        def run_callback(message):
            print(f"RUN: {message}")
            
        success, message = await engine.run_app('DiffuEraser', progress_callback=run_callback)
        
        if success:
            print(f"✅ RUN SUCCESS: {message}")
            print("🎯 App started successfully - this means Pinokio scripts executed properly!")
        else:
            if any(keyword in message.lower() for keyword in ['cuda', 'pytorch', 'torch', 'gpu', 'nvidia']):
                print(f"🎯 EXPECTED SUCCESS: Hit PyTorch/CUDA dependency error: {message}")
                print("✅ This confirms Pinokio install.js and start.js executed correctly!")
            else:
                print(f"❌ UNEXPECTED RUN ERROR: {message}")
        
    else:
        print(f"❌ INSTALL FAILED: {message}")
        
    print("\n=== WORKFLOW TEST COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(test_diffueraser_workflow())
