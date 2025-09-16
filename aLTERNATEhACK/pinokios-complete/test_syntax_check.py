#!/usr/bin/env python3
"""
Quick syntax check for unified_engine.py
"""
import sys
import os
sys.path.append('.')

try:
    from pinokios.unified_engine import UnifiedPinokioEngine
    print("✅ unified_engine.py syntax and imports OK")
    
    # Try creating engine instance
    engine = UnifiedPinokioEngine()
    print("✅ Engine initialization OK")
    
except SyntaxError as e:
    print(f"❌ Syntax Error: {e}")
    print(f"File: {e.filename}, Line: {e.lineno}")
except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Other Error: {e}")
    import traceback
    traceback.print_exc()
