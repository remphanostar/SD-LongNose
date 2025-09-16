#!/usr/bin/env python3
"""
Basic Usage Example - Pinokio Cloud GPU

This example shows the simplest way to use the PinokioCloudSimple class.
"""

import sys
sys.path.append('..')
from pinokio_cloud_simple import PinokioCloudSimple

def main():
    print("🚀 Pinokio Cloud GPU - Basic Usage Example")
    print("=" * 50)
    
    # Create instance
    pinokio = PinokioCloudSimple()
    
    # Run complete setup
    success = pinokio.run_full_setup()
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("📊 Final status:")
        pinokio.print_status()
    else:
        print("\n❌ Setup failed. Check error messages above.")
    
    return success

if __name__ == "__main__":
    main()
