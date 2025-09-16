---
description:  Porject rules
globs:
alwaysApply: true
---
# PinokioCloud Development Rules

## Project Overview
PinokioCloud is a cloud-native Pinokio alternative for Google Colab environments with Streamlit UI. 
The goal is to implement Pinokio functionality as specified in Pinokio.md with minimal deviations.

## Core Development Principles

### 1. Pinokio.md Compliance
- Follow Pinokio.md specifications exactly unless technically impossible
- Implement ALL Pinokio API methods: shell.run, fs.*, script.*, input, json.*, etc.
- Support complete variable substitution system: {{platform}}, {{gpu}}, {{args.*}}, {{local.*}}
- Honor daemon: true flag for background processes
- Implement proper error handling as specified

### 2. File Structure Rules
- Keep existing notebook structure unchanged (PinokioCloud_Colab_Generated.ipynb)
- All core logic in unified_engine.py
- UI logic in streamlit_colab.py  
- Do NOT modify the Colab clone > install > launch workflow
- Maintain absolute paths for Colab compatibility (/content/...)

### 3. Implementation Standards

#### Engine Development
- Always implement missing methods before calling them
- Use async/await for long-running operations
- Implement proper process tracking with PIDs
- Support both .js and .json Pinokio scripts
- Handle virtual environments exactly like desktop Pinokio

#### Variable System
- Support full {{variable}} syntax with nested paths
- Implement all Pinokio memory variables (platform, gpu, cwd, port, args, local, env)
- Handle variable substitution in all string parameters
- Support conditional logic with 'when' clauses

#### Process Management  
- Track all spawned processes
- Implement proper daemon management
- Support 'on' handlers for output monitoring
- Handle graceful shutdown and cleanup

#### Error Handling
- Provide user-friendly error messages
- Log technical details for debugging
- Implement retry mechanisms where appropriate
- Never fail silently

### 4. Code Quality Standards
- Use type hints for all function parameters
- Add comprehensive docstrings
- Implement proper logging with structured messages
- Handle exceptions gracefully with specific error types
- Test edge cases (missing files, network issues, permission errors)

### 5. Colab Compatibility Rules
- Always check for 'google.colab' in sys.modules
- Use /content/ paths for Colab environment
- Handle missing system utilities (git, python versions)
- Support both Colab and local development
- Respect Colab resource limitations

### 6. UI Integration Rules
- Update Streamlit UI to reflect engine capabilities
- Maintain existing dark cyberpunk theme
- Provide real-time feedback through progress_callback
- Show process status accurately in UI
- Handle async operations in Streamlit properly

### 7. Testing Requirements
- Test with real apps from cleaned_pinokio_apps.json
- Validate both .js and .json script execution
- Test virtual environment isolation
- Verify daemon processes work correctly
- Test error conditions and recovery

## Forbidden Actions
- Do NOT change the notebook deployment structure
- Do NOT modify the ngrok token setup
- Do NOT alter the GitHub clone workflow  
- Do NOT break backward compatibility with existing apps
- Do NOT deviate from Pinokio.md without justification

## Development Priority Order
1. Complete missing engine methods (run_app, stop_app, uninstall_app)
2. Implement core Pinokio API (shell.run, fs.*, script.*)
3. Add complete variable substitution system
4. Implement daemon process management
5. Add advanced features (virtual drives, error recovery)
6. Optimize performance and polish UI