#!/usr/bin/env python3
"""
Debug engine state vs actual app directories
"""
import sys
import os
import json
from pathlib import Path
sys.path.append('.')

from pinokios.unified_engine import UnifiedPinokioEngine

def debug_engine_state():
    print("=== DEBUGGING ENGINE STATE ===")
    
    # Create engine instance
    engine = UnifiedPinokioEngine()
    print(f"Engine base_path: {engine.base_path}")
    
    # Check engine's installed_apps state
    print(f"\nEngine installed_apps: {engine.installed_apps}")
    
    # Check actual directories
    print(f"\nActual app directories in {engine.base_path}:")
    if engine.base_path.exists():
        for item in engine.base_path.iterdir():
            if item.is_dir() and item.name not in ['apps', 'cache', 'venvs', 'logs']:
                has_pinokio = any([
                    (item / 'install.js').exists(),
                    (item / 'install.json').exists(),
                    (item / 'start.js').exists(),
                    (item / 'start.json').exists(),
                    (item / 'pinokio.js').exists()
                ])
                print(f"  {item.name}: has_pinokio_files={has_pinokio}")
                
    # Check specific roop-unleashed state
    roop_path = engine.base_path / 'roop-unleashed'
    print(f"\nroop-unleashed directory check:")
    print(f"  Path exists: {roop_path.exists()}")
    print(f"  install.js exists: {(roop_path / 'install.js').exists()}")
    print(f"  start.js exists: {(roop_path / 'start.js').exists()}")
    print(f"  pinokio.js exists: {(roop_path / 'pinokio.js').exists()}")
    print(f"  In engine.installed_apps: {'roop-unleashed' in engine.installed_apps}")
    
    # Check cache file
    cache_file = engine.cache_dir / "engine_state.json"
    print(f"\nCache file: {cache_file}")
    print(f"  Exists: {cache_file.exists()}")
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        print(f"  Cache content: {cache_data}")

if __name__ == "__main__":
    debug_engine_state()
