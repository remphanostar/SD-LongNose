# 🚀 PinokioCloud - Complete AI App Manager for Google Colab

## Overview

PinokioCloud brings the full power of Pinokio's AI app ecosystem to Google Colab and cloud GPU environments. Run 284+ verified AI apps with full JavaScript/JSON script execution, virtual environment isolation, and ngrok tunneling support.

## ✨ Features

- **Full Pinokio Compatibility**: Execute real Pinokio JS/JSON scripts with template evaluation, conditionals, and event handling
- **Virtual Environment Isolation**: Each app runs in its own isolated Python environment with `uv` for fast package management
- **GPU Optimization**: Automatic detection and configuration for NVIDIA GPUs (T4, V100, A100, etc.)
- **ngrok Tunneling**: Public URL access for web-based AI apps
- **284+ Verified Apps**: Pre-configured database of popular AI applications
- **Event-Driven Architecture**: Monitor app output for readiness events and automatic URL capture
- **Complete Lifecycle Management**: Install, run, stop, and uninstall apps with state persistence

## 🚀 Quick Start

### Option 1: Use the Final Notebook

1. Open `PinokioCloud_Final.ipynb` in Google Colab
2. Run all cells sequentially
3. Use the interactive UI to search and manage apps

### Option 2: Direct Python Usage

```python
from pinokios.unified_engine import UnifiedPinokioEngine

# Initialize engine
engine = UnifiedPinokioEngine(base_path='/content/pinokio_apps')

# Install an app
success, message = await engine.install_app(
    'stable-diffusion-webui',
    'https://github.com/AUTOMATIC1111/stable-diffusion-webui'
)

# Run the app
success, message = await engine.run_app('stable-diffusion-webui')
```

## 📁 Repository Structure

```
pinokios-complete/
├── pinokios/
│   └── unified_engine.py      # Core Pinokio engine with full JS execution
├── PinokioCloud_Final.ipynb   # Complete Colab notebook
├── cleaned_pinokio_apps.json  # Database of 284+ verified apps
├── docs/
│   └── Pinokio.md             # Complete API documentation
└── AppExample/                # Example Pinokio app structure
    ├── install.js
    ├── start.js
    └── pinokio.js
```

## 🛠️ Core Components

### UnifiedPinokioEngine

The heart of PinokioCloud - a complete Python implementation of Pinokio's runtime:

- **Script Execution**: Parse and execute JS/JSON scripts with full API support
- **Template Evaluation**: Process `{{variable}}` expressions and conditionals
- **Event Monitoring**: Detect app readiness patterns in output
- **Virtual Environments**: Create and manage isolated Python environments
- **Process Management**: Track and control running app processes
- **State Persistence**: Maintain app installation and configuration state

### Supported Pinokio APIs

- `shell.run` - Execute shell commands with event monitoring
- `script.start` - Run sub-scripts with parameter passing
- `local.set` - Set and get local variables
- `fs.download` - Download files with progress tracking
- `log` - Structured logging
- `input` - User input prompts
- Platform/GPU detection for conditional execution

## 🎯 Example Apps

### Stable Diffusion WebUI
```python
await engine.install_app(
    'stable-diffusion-webui',
    'https://github.com/AUTOMATIC1111/stable-diffusion-webui'
)
await engine.run_app('stable-diffusion-webui')
```

### ComfyUI
```python
await engine.install_app(
    'ComfyUI',
    'https://github.com/comfyanonymous/ComfyUI'
)
await engine.run_app('ComfyUI')
```

### Ollama
```python
await engine.install_app(
    'ollama',
    'https://github.com/ollama/ollama'
)
await engine.run_app('ollama')
```

## 🌐 ngrok Tunneling

Create public URLs for your AI apps:

```python
from pyngrok import ngrok

# Setup authentication (optional but recommended)
tunnel_manager.setup_ngrok('your_auth_token')

# Create tunnel
public_url = tunnel_manager.create_tunnel(7860, 'stable-diffusion-webui')
print(f"Access your app at: {public_url}")
```

## 📊 App Categories

- **Image Generation**: Stable Diffusion, ComfyUI, Fooocus
- **Language Models**: Ollama, Text Generation WebUI, LM Studio
- **Audio**: WhisperX, Bark, AudioCraft
- **Video**: AnimateDiff, Deforum, Stable Video Diffusion
- **3D**: Shap-E, Point-E, DreamGaussian
- **Tools**: Kohya SS, Training utilities, Model converters

## 🔧 Advanced Configuration

### Custom Virtual Environment
```python
engine = UnifiedPinokioEngine(
    base_path='/custom/path',
    venv_backend='conda',  # or 'venv'
    use_uv=True  # Fast pip alternative
)
```

### Event Pattern Matching
```python
# Custom readiness patterns
engine.run_app('my-app', event_patterns=[
    r'Server running on port \d+',
    r'Ready for connections'
])
```

### GPU Selection
```python
# Force specific GPU
engine.context.gpu = 'nvidia'
engine.context.gpu_model = 'A100'
```

## 🐛 Troubleshooting

### Common Issues

1. **GPU Not Detected**
   - Ensure GPU runtime is selected in Colab
   - Check CUDA availability: `!nvidia-smi`

2. **ngrok Tunnel Failed**
   - Authenticate with valid token
   - Check port availability
   - Ensure app is actually running

3. **Installation Fails**
   - Check available disk space
   - Verify repository URL
   - Review install.js for dependencies

4. **App Won't Start**
   - Check virtual environment activation
   - Review error logs in engine output
   - Verify all dependencies installed

## 📝 Development

### Running Tests
```bash
python -m pytest tests/
```

### Contributing
1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Original Pinokio by @cocktailpeanut
- Stable Diffusion WebUI by AUTOMATIC1111
- ComfyUI by comfyanonymous
- All app developers in the ecosystem

## 📞 Support

- GitHub Issues: [Report bugs](https://github.com/remphanostar/SD-LongNose/issues)
- Documentation: See `docs/Pinokio.md` for API reference

---

**Made with ❤️ for the AI community**
