#!/usr/bin/env python3
"""
Advanced Usage Example - Pinokio Cloud GPU

This example shows step-by-step setup with error handling and custom configurations.
"""

import sys
import time
sys.path.append('..')
from pinokio_cloud_simple import PinokioCloudSimple

def advanced_setup():
    print("🚀 Pinokio Cloud GPU - Advanced Usage Example")
    print("=" * 50)
    
    # Create instance with custom path
    pinokio = PinokioCloudSimple(base_path="/tmp/custom_pinokio")
    
    try:
        # Step 1: Setup directory
        print("\n📁 Step 1: Setting up directory")
        pinokio.setup_directory()
        
        # Step 2: Download Pinokio
        print("\n📥 Step 2: Downloading Pinokio")
        if not pinokio.download_pinokio():
            raise Exception("Download failed")
        
        # Step 3: Start server
        print("\n🚀 Step 3: Starting server")
        if not pinokio.start_pinokio_server():
            raise Exception("Server startup failed")
        
        # Step 4: Setup tunnel (optional)
        print("\n🌐 Step 4: Setting up tunnel")
        tunnel_url = pinokio.setup_tunnel()
        
        # Step 5: Monitor status
        print("\n📊 Step 5: Final status check")
        pinokio.print_status()
        
        # Keep running for a while
        print("\n⏳ Keeping service running for 30 seconds...")
        time.sleep(30)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Advanced setup failed: {e}")
        return False
        
    finally:
        # Always cleanup
        print("\n🧹 Cleaning up...")
        pinokio.cleanup()

if __name__ == "__main__":
    advanced_setup()
