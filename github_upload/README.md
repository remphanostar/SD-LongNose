# 🚀 Pinokio Cloud GPU

Deploy and run Pinokio AI tool environment on cloud GPU platforms with automatic platform detection, tunneling, and AI tool management.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Features

- **Automatic Platform Detection**: Detects and configures for Google Colab, Kaggle, Paperspace, Lightning.ai, RunPod, Vast.ai, and more
- **Dynamic Path Configuration**: Automatically sets up paths based on detected platform
- **Headless Operation**: Runs Pinokio in headless mode with virtual display support
- **Multiple Tunneling Options**: Supports ngrok, Cloudflare Tunnel, and LocalTunnel
- **AI Tool Management**: Install and manage popular AI tools via JSON-RPC API
- **GPU Detection**: Automatic GPU detection and CUDA configuration
- **Persistent Storage**: Support for persistent storage on compatible platforms

## 🚀 Quick Start

### Option 1: One-Click Setup (Recommended)

```python
# Clone and run
!git clone https://github.com/yourusername/pinokio-cloud-gpu.git
%cd pinokio-cloud-gpu
!pip install -r requirements.txt

# Quick start
from pinokio_cloud_main import quick_start_notebook
pinokio, url = quick_start_notebook()
print(f"🎉 Access Pinokio at: {url}")
```

### Option 2: Manual Setup

```python
from pinokio_cloud_main import PinokioCloudGPU

# Initialize and setup
pinokio = PinokioCloudGPU()
pinokio.setup()
pinokio.install_pinokio()
pinokio.start_pinokio()

# Setup tunnel
url = pinokio.setup_tunnel(service="cloudflare")  # No auth required
# OR with ngrok (requires token)
# url = pinokio.setup_tunnel(service="ngrok", ngrok_token="YOUR_TOKEN")

print(f"🎉 Access Pinokio at: {url}")
```

## 📁 Project Structure

```
pinokio-cloud-gpu/
├── modules/
│   ├── __init__.py                 # Package initialization
│   ├── platform_detector.py       # Platform detection and configuration
│   ├── pinokio_installer.py       # Pinokio installation and setup
│   ├── tunnel_manager.py          # Tunneling services management
│   └── pinokio_controller.py      # JSON-RPC API controller
├── scripts/                       # AI tool installation scripts
├── pinokio_cloud_main.py          # Main orchestrator
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🔧 Configuration

### Supported Platforms

| Platform | Status | Persistent Storage |
|----------|--------|-------------------|
| Google Colab | ✅ | Google Drive |
| Kaggle | ✅ | Local storage |
| Paperspace | ✅ | Persistent volume |
| Lightning.ai | ✅ | Studio storage |
| RunPod | ✅ | Network volume |
| Vast.ai | ✅ | Container volume |
| AWS/GCP | ✅ | Instance storage |

### Environment Variables

```python
# Force platform detection
os.environ['FORCE_PLATFORM'] = 'colab'

# Custom paths
os.environ['PINOKIO_PATH'] = '/custom/path'

# API configuration
os.environ['PINOKIO_API_PORT'] = '42000'
```

## 🤖 AI Tool Installation

### Quick Install Popular Tools

```python
# Install and launch Stable Diffusion
url = pinokio.install_ai_tool("stable-diffusion")

# Available tools:
# - stable-diffusion (AUTOMATIC1111)
# - comfyui (ComfyUI)
# - text-generation (Oobabooga)
# - kohya-ss (Training)
# - invokeai (InvokeAI)
```

### Using the Controller API

```python
controller = pinokio.controller

# List available apps
apps = controller.list_apps()

# Install custom tool
controller.install_app("https://github.com/user/repo", "tool-name")

# Launch installed tool
result = controller.launch_app("tool-name")
```

## 🌐 Tunneling Options

### Cloudflare Tunnel (No Authentication)
```python
url = pinokio.setup_tunnel(service="cloudflare")
```

### ngrok (Requires Free Account)
```python
# Get token from https://ngrok.com/
url = pinokio.setup_tunnel(service="ngrok", ngrok_token="YOUR_TOKEN")
```

### LocalTunnel (Open Source)
```python
url = pinokio.setup_tunnel(service="localtunnel")
```

### Auto-Select Best Available
```python
url = pinokio.setup_tunnel(service="auto")  # Tries all services
```

## 📊 System Information

```python
# Get platform info
status = pinokio.get_status()
print(f"Platform: {status['platform']}")
print(f"Tunnel URL: {status['tunnel_url']}")

# Get detailed system info
info = pinokio.detector.get_system_info()
print(f"GPU: {info['gpu']['available']}")
print(f"Memory: {info['memory']['total']}")
```

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| GPU not detected | Enable GPU runtime in your cloud platform |
| Tunnel fails | Try different service: `service="cloudflare"` |
| Import errors | Run: `pip install -r requirements.txt` |
| Pinokio won't start | Check virtual display setup |
| Out of memory | Use smaller models or reduce batch size |

### Debug Commands

```python
# Check if services are running
print(f"Pinokio running: {pinokio.controller.is_running()}")
print(f"Active tunnels: {pinokio.tunnel.get_active_tunnels()}")

# View logs
import subprocess
result = subprocess.run(['ls', '-la', f"{pinokio.paths['pinokio']}/logs"])
```

## 🧹 Cleanup

```python
# Stop all services
pinokio.cleanup()

# Or manually
pinokio.controller.stop_server()
pinokio.tunnel.stop_all_tunnels()
```

## 📚 Command Line Usage

```bash
# Run with specific configuration
python pinokio_cloud_main.py --platform colab --port 42000 --tunnel cloudflare

# Install specific AI tool
python pinokio_cloud_main.py --install-tool stable-diffusion

# Use ngrok with token
python pinokio_cloud_main.py --tunnel ngrok --ngrok-token YOUR_TOKEN
```

## 🎯 Examples

### Basic Jupyter Notebook Usage

```python
# Cell 1: Setup
!git clone https://github.com/yourusername/pinokio-cloud-gpu.git
%cd pinokio-cloud-gpu
!pip install -r requirements.txt

# Cell 2: Quick start
from pinokio_cloud_main import quick_start_notebook
pinokio, url = quick_start_notebook()

# Cell 3: Install AI tool
tool_url = pinokio.install_ai_tool("stable-diffusion")
print(f"Stable Diffusion: {tool_url}")
```

### Custom Installation

```python
from pinokio_cloud_main import PinokioCloudGPU

pinokio = PinokioCloudGPU()
pinokio.setup()
pinokio.install_pinokio()
pinokio.start_pinokio(port=8080)

# Custom tunnel setup
url = pinokio.setup_tunnel(service="ngrok", ngrok_token="your_token")

# Install multiple tools
tools = ["stable-diffusion", "comfyui", "text-generation"]
for tool in tools:
    pinokio.install_ai_tool(tool)
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Pinokio](https://pinokio.computer/) - The AI browser
- [AUTOMATIC1111](https://github.com/AUTOMATIC1111/stable-diffusion-webui) - Stable Diffusion WebUI
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - Node-based UI
- All open-source AI tool creators

---

**🎉 Ready to deploy Pinokio on any cloud GPU platform!**

For support, open an issue or check the [documentation](https://github.com/yourusername/pinokio-cloud-gpu/wiki).
