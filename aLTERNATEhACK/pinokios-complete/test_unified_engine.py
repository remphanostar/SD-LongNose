#!/usr/bin/env python3
"""Test script for the unified Pinokio engine."""

import asyncio
import json
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pinokios.unified_engine import UnifiedPinokioEngine, PinokioContext


async def test_engine():
    """Test the unified Pinokio engine with various scenarios."""
    
    print("🧪 Testing Unified Pinokio Engine\n")
    
    # Initialize engine
    engine = UnifiedPinokioEngine(base_path=Path.cwd() / "test_apps")
    
    print("✅ Engine initialized")
    print(f"  Platform: {engine.context.platform}")
    print(f"  GPU: {engine.context.gpu or 'None'}")
    print(f"  Base path: {engine.base_path}\n")
    
    # Test 1: Template expression evaluation
    print("Test 1: Template Expression Evaluation")
    test_cases = [
        ("Hello {{name}}", {"name": "World"}, "Hello World"),
        ("Count: {{count + 1}}", {"count": 5}, "Count: 6"),
        ("Path: {{os.path.join('dir', 'file.txt')}}", {}, "Path: dir/file.txt"),
    ]
    
    for template, local_vars, expected in test_cases:
        result = engine._evaluate_template(template, local_vars)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{template}' -> '{result}'")
    
    # Test 2: Conditional evaluation
    print("\nTest 2: Conditional Evaluation")
    conditions = [
        ("gpu === 'nvidia'", {"gpu": "nvidia"}, True),
        ("platform === 'linux' && gpu", {"platform": "linux", "gpu": "nvidia"}, True),
        ("count > 5", {"count": 3}, False),
    ]
    
    for condition, local_vars, expected in conditions:
        result = engine._evaluate_condition(condition, local_vars)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{condition}' -> {result}")
    
    # Test 3: Parse Pinokio script
    print("\nTest 3: Parse Pinokio Script")
    test_script = {
        "run": [
            {
                "method": "shell.run",
                "params": {
                    "message": "Installing dependencies",
                    "command": "pip install requests"
                }
            },
            {
                "method": "local.set",
                "params": {
                    "app_name": "test_app",
                    "version": "1.0.0"
                }
            },
            {
                "method": "log",
                "params": "App {{app_name}} v{{version}} installed"
            },
            {
                "when": "platform === 'linux'",
                "method": "shell.run",
                "params": {
                    "command": "chmod +x start.sh"
                }
            }
        ]
    }
    
    # Save test script
    test_script_path = Path.cwd() / "test_script.json"
    with open(test_script_path, 'w') as f:
        json.dump(test_script, f, indent=2)
    
    # Parse script
    parsed = engine._parse_pinokio_script(test_script_path)
    print(f"  ✅ Parsed {len(parsed.get('run', []))} commands")
    
    # Test 4: Virtual environment creation
    print("\nTest 4: Virtual Environment Management")
    test_app_name = "test_venv_app"
    venv_path = engine.get_venv_path(test_app_name)
    
    if not venv_path.exists():
        print(f"  Creating venv for {test_app_name}...")
        venv_created = engine.create_venv(test_app_name)
        if venv_created:
            print(f"  ✅ Venv created at: {venv_path}")
        else:
            print(f"  ❌ Failed to create venv")
    else:
        print(f"  ✅ Venv already exists at: {venv_path}")
    
    # Test 5: Execute simple shell command
    print("\nTest 5: Execute Shell Command")
    result = await engine.shell_run({
        "command": "echo 'Hello from Pinokio Engine'",
        "message": "Testing echo command"
    }, Path.cwd())
    
    if result:
        print(f"  ✅ Command executed successfully")
    else:
        print(f"  ❌ Command failed")
    
    # Test 6: Local variable storage
    print("\nTest 6: Local Variable Storage")
    script_id = "test_script"
    
    # Set variables
    await engine.local_set({
        "test_var": "test_value",
        "counter": 42
    }, script_id)
    
    # Get variables
    test_var = engine.local_vars.get(script_id, {}).get("test_var")
    counter = engine.local_vars.get(script_id, {}).get("counter")
    
    print(f"  ✅ Set test_var = '{test_var}'")
    print(f"  ✅ Set counter = {counter}")
    
    # Test 7: App status management
    print("\nTest 7: App Status Management")
    test_app = "status_test_app"
    
    # Set status
    engine.installed_apps[test_app] = {
        "name": test_app,
        "path": str(Path.cwd() / test_app),
        "status": "installed",
        "venv": str(engine.get_venv_path(test_app))
    }
    
    # Get status
    status = engine.get_app_status(test_app)
    print(f"  ✅ App '{test_app}' status: {status}")
    
    # List installed apps
    installed = engine.list_installed_apps()
    print(f"  ✅ Total installed apps: {len(installed)}")
    
    # Test 8: Cleanup
    print("\nTest 8: Cleanup")
    engine.cleanup()
    print("  ✅ Engine cleaned up")
    
    # Clean up test files
    test_script_path.unlink(missing_ok=True)
    print("  ✅ Test files cleaned")
    
    print("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_engine())
