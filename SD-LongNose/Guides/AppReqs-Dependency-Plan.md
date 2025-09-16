# THE DEFINITIVE PINOKIO DEPENDENCY MANAGEMENT GUIDE FOR AI AGENTS

## Executive Summary

After extensive research of official Pinokio documentation and real applications, **requirements.txt files are BOTH used AND not used** in Pinokio apps. The reality is more nuanced than initially understood.

## The Complete Truth About Pinokio Dependencies

### Method 1: Direct pip install (Most Common)
Installation scripts: pip install, npm install, etc. - this is the primary pattern where packages are installed individually via shell.run commands.

**Pattern:**
```javascript
{
  "method": "shell.run",
  "params": {
    "message": "pip install torch==2.1.0+cu121 --index-url https://download.pytorch.org/whl/cu121"
  }
}
```

### Method 2: requirements.txt Installation (Official Pattern)
Run pip install -r requirements.txt, which will install the gradio dependency into the env environment - this confirms that **requirements.txt IS used in official Pinokio examples**.

**Pattern:**
```javascript
{
  "method": "shell.run",
  "params": {
    "message": "pip install -r requirements.txt"
  }
}
```

### Method 3: Dynamic requirements.txt Generation
Apps create requirements.txt files during installation based on system detection.

**Pattern:**
```javascript
{
  "method": "fs.write",
  "params": {
    "path": "requirements.txt",
    "text": [
      "torch==2.1.0+cu121",
      "torchvision==0.16.0+cu121"
    ].join("\n")
  }
},
{
  "method": "shell.run",
  "params": {
    "message": "pip install -r requirements.txt"
  }
}
```

### Method 4: Git Clone + Setup Patterns  
Runs git clone to download repositories - many apps clone repositories and install them.

**Pattern:**
```javascript
{
  "method": "shell.run",
  "params": {
    "message": "git clone https://github.com/some-org/some-project.git"
  }
},
{
  "method": "shell.run",
  "params": {
    "message": "pip install -e ./some-project"
  }
}
```

### Method 5: System Package Installation
Runs brew install to install dependencies - system-level dependency installation.

**Pattern:**
```javascript
{
  "method": "shell.run",
  "params": {
    "message": "brew install ffmpeg"
  },
  "when": "{{platform}} === 'darwin'"
}
```

### Method 6: Pinokio Dependencies Array
Inter-app dependencies declared in pinokio.js files.

**Pattern:**
```javascript
// pinokio.js
module.exports = {
  dependencies: [
    "https://github.com/cocktailpeanutlabs/comfyui",
    "https://github.com/cocktailpeanutlabs/automatic1111"
  ]
}
```

### Method 7: Multiple Install Scripts
Platform-specific installations using different script files:
- `install.json` (default)
- `install_cuda.json` (NVIDIA specific)  
- `install_directml.json` (DirectML/AMD)
- `install_cpu.json` (CPU fallback)

### Method 8: Conda Environment Creation
Some advanced apps use conda for environment management:

**Pattern:**
```javascript
{
  "method": "shell.run",
  "params": {
    "message": "conda create -n myapp python=3.10 -y"
  }
},
{
  "method": "shell.run",
  "params": {
    "message": "conda activate myapp && pip install torch"
  }
}
```

## Complete Implementation Requirements for AI Agents

### PRIORITY 1: Core Pinokio Script Execution
1. **Parse install.js and install.json files** - both JavaScript and JSON formats
2. **Execute shell.run commands in sequence** - the fundamental Pinokio operation
3. **Handle conditional logic with when clauses** - platform/GPU specific installations
4. **Support complete Pinokio variable system** - {{gpu}}, {{platform}}, {{local}}, etc.
5. **Manage isolated virtual environments** - one venv per app in app directory

### PRIORITY 2: Dependency Installation Methods
6. **Direct pip install execution** - individual package installation commands
7. **requirements.txt processing** - both static files and dynamically generated
8. **Git repository cloning and installation** - git clone + pip install -e patterns
9. **System package installation** - brew, apt-get, etc. for system dependencies
10. **Index URL management** - PyTorch CUDA-specific package sources

### PRIORITY 3: Advanced Features
11. **Multiple install scripts per app** - install.json, install_cuda.json, install_directml.json
12. **Pinokio dependencies array processing** - inter-app dependency resolution
13. **Platform-specific installation logic** - Windows/Linux/macOS variations
14. **Conda environment creation** - some advanced apps use conda

### PRIORITY 4: Error Handling & Fallbacks
15. **GPU to CPU fallback strategies** - when CUDA packages fail
16. **Network failure recovery** - retry mechanisms for downloads
17. **Version conflict resolution** - handle incompatible package versions
18. **Installation validation** - verify successful package installation

## Critical Implementation Details

### Virtual Environment Management
- **Location**: Each app gets `{{local}}/venv` or similar
- **Isolation**: Complete dependency isolation between apps
- **Activation**: Must activate venv before all pip commands
- **Platform handling**: Different activation commands for Windows vs Unix

### Variable Substitution System
- **{{gpu}}**: Boolean indicating CUDA availability
- **{{platform}}**: "win32", "linux", "darwin"
- **{{local}}**: App installation directory absolute path
- **{{args.*}}**: Installation arguments passed to app
- **Custom variables**: Apps can define their own variables

### Script Processing Logic
1. **Detect script type**: .js vs .json format
2. **Parse conditional logic**: when clauses for system-specific steps
3. **Execute in sequence**: Commands must run in specified order
4. **Handle async operations**: Some commands are long-running
5. **Process output**: Handle on.event callbacks for command output

### Error Recovery Strategies
- **GPU package failures**: Try CPU equivalents automatically
- **Network timeouts**: Retry with exponential backoff
- **Version conflicts**: Try compatible version ranges
- **Missing system deps**: Provide clear error messages

## Real Pinokio App Examples

### Example 1: Direct pip install (VibeVoice-Pinokio)
```javascript
{
  "method": "shell.run",
  "params": {
    "message": "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
  },
  "when": "{{gpu}}"
}
```

### Example 2: Git clone pattern (ComfyUI variants)
```javascript
{
  "method": "shell.run",
  "params": {
    "message": "git clone https://github.com/comfyanonymous/ComfyUI.git"
  }
},
{
  "method": "shell.run",
  "params": {
    "message": "pip install -r ComfyUI/requirements.txt"
  }
}
```

### Example 3: Conditional installation (FaceFusion)
```javascript
{
  "method": "shell.run",
  "params": {
    "message": "pip install torch==2.1.0+cu121 --index-url https://download.pytorch.org/whl/cu121"
  },
  "when": "{{gpu}} && {{platform}} !== 'darwin'"
},
{
  "method": "shell.run",
  "params": {
    "message": "pip install torch==2.1.0"
  },
  "when": "!{{gpu}} || {{platform}} === 'darwin'"
}
```

## What NOT to Implement
- **Poetry/pipenv support**: Not used in Pinokio ecosystem
- **pyproject.toml parsing**: Not a Pinokio pattern
- **Docker integration**: Pinokio uses native virtual environments
- **Package managers other than pip/conda**: Outside Pinokio scope

## Testing Requirements
Your implementation must be tested against these real Pinokio app patterns:
1. **cocktailpeanutlabs apps**: Multiple install.json examples
2. **facefusion variants**: Complex multi-script installations  
3. **GPU-dependent apps**: CUDA package installation and fallbacks
4. **System dependency apps**: Apps requiring brew/apt packages
5. **Cross-platform apps**: Windows/Linux/macOS compatibility

## Architecture Requirements

### Engine Structure
```
PinokioEngine
├── ScriptParser (install.js/install.json)
├── VariableResolver ({{variable}} substitution)
├── EnvironmentManager (venv creation/activation)
├── DependencyInstaller (pip/conda/system packages)
├── ProcessManager (shell.run execution)
└── ErrorHandler (fallbacks/recovery)
```

### Key Modules Required
1. **Script Parser**: Parse both .js and .json install scripts
2. **Variable Resolver**: Handle all Pinokio variable substitution
3. **Environment Manager**: Create/manage isolated virtual environments
4. **Dependency Installer**: Execute all package installation methods
5. **Process Manager**: Run shell commands with proper error handling
6. **Error Handler**: Implement fallback strategies and recovery

## The Bottom Line for AI Agents

**You MUST implement BOTH direct pip install AND requirements.txt processing** because the Pinokio ecosystem uses both patterns. The official documentation confirms requirements.txt usage, while many apps use direct pip commands. A complete Pinokio implementation requires handling the full spectrum of dependency management methods found in real applications.

This is not about the broader Python ecosystem - this is specifically about the methods actually used by real Pinokio applications in production.

## Final Implementation Checklist

### ✅ Must Have
- [ ] Parse install.js and install.json files
- [ ] Execute shell.run commands with proper sequencing
- [ ] Handle when clause conditional logic
- [ ] Support complete {{variable}} substitution system
- [ ] Create isolated virtual environments per app
- [ ] Process both direct pip install and requirements.txt
- [ ] Handle git clone + pip install -e patterns
- [ ] Support multiple install scripts per app
- [ ] Implement GPU→CPU fallback strategies
- [ ] Handle system package installation (brew, apt-get)

### ⚡ Nice to Have
- [ ] Conda environment support
- [ ] Inter-app dependency resolution via pinokio.js
- [ ] Advanced error recovery mechanisms
- [ ] Installation progress tracking
- [ ] Parallel installation optimization

### ❌ Do NOT Implement
- [ ] Poetry/pipenv support
- [ ] Docker integration
- [ ] Non-Pinokio package management systems
