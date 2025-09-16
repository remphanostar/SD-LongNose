import asyncio
import sys
from pathlib import Path
sys.path.append('.')

from pinokios.unified_engine import UnifiedPinokioEngine

async def test_single_app():
    engine = UnifiedPinokioEngine(base_path="./pinokio_apps")
    
    # Test roop-unleashed first
    print("Testing roop-unleashed...")
    success, message = await engine.run_app("roop-unleashed")
    print(f"Success: {success}")
    print(f"Message: {message}")
    
    # Check logs
    log_file = Path("logs/roop-unleashed_run.log")
    if log_file.exists():
        print("\n=== LOG CONTENTS ===")
        print(log_file.read_text())

asyncio.run(test_single_app())
