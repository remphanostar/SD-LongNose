#!/usr/bin/env python3
"""
Test auto-discovery functionality
"""
import sys
sys.path.append('.')

from pinokios.unified_engine import UnifiedPinokioEngine

def test_auto_discovery():
    print("=== TESTING ENGINE AUTO-DISCOVERY ===")
    
    # Create fresh engine instance
    engine = UnifiedPinokioEngine()
    
    print(f"Engine base_path: {engine.base_path}")
    print(f"Discovered installed apps: {list(engine.installed_apps.keys())}")
    
    # Check specific roop-unleashed
    if 'roop-unleashed' in engine.installed_apps:
        print("✅ roop-unleashed auto-discovered successfully!")
        app_info = engine.installed_apps['roop-unleashed']
        print(f"App info: {app_info}")
        
        # Test uninstall
        print("\n--- Testing uninstall ---")
        import asyncio
        
        async def test_uninstall():
            success, message = await engine.uninstall_app('roop-unleashed')
            print(f"Uninstall result: success={success}, message='{message}'")
            return success, message
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success, message = loop.run_until_complete(test_uninstall())
        loop.close()
        
        if success:
            print("✅ Uninstall successful - engine can now handle auto-discovered apps!")
        else:
            print(f"❌ Uninstall failed: {message}")
            
    else:
        print("❌ roop-unleashed not auto-discovered")
        print("Available apps:", list(engine.installed_apps.keys()))

if __name__ == "__main__":
    test_auto_discovery()
