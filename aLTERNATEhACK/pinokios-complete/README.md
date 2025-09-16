# 🚀 CloudPinokio Complete - Cloud-Native Pinokio System

**284 Verified Apps | Cloud GPU Optimized | Real Pinokio Functionality**

A cloud-native Pinokio system built from official AppData.json with 284 verified applications, optimized for GPU cloud environments like Google Colab, Lightning AI, and Kaggle.

## ✨ Key Features

- **284 Verified Apps** - From official Pinokio AppData.json, fully validated
- **Cloud GPU Optimized** - Auto-detects and optimizes for T4, A100, V100 GPUs  
- **Real Pinokio Execution** - Executes actual install.js/pinokio.js scripts
- **Multi-Platform Support** - Google Colab, Lightning AI, Kaggle, Local
- **Modern Web UI** - Beautiful Streamlit interfaces for app management
- **Virtual Environment Isolation** - Safe dependency management per app
- **Streamlit Web Interface** - Beautiful, responsive UI
- **Cloud Environment Ready** - Works in Colab, Kaggle, local environments

## 📊 Database Stats

- **Total Apps**: 284 verified applications from official AppData.json
- **Categories**: Audio (86), Image (122), LLM (38), 3D (11), Video, Utility, and more
- **All Verified**: Every app validated with proper install.js/pinokio.js files
- **Official Source**: Built from Pinokio's official AppData.json

## 🚀 Quick Start

### Option 1: Streamlit Cloud Interface
```bash
# Launch the modern web interface
streamlit run ui/streamlit_cloud_pinokio.py
```

### Option 2: Google Colab
```python
# Use the provided Jupyter notebook
# Open: PinokiOS_Complete_Colab.ipynb

# Import and use
from pinokios import PinokioSystem, search_apps
from pinokios.ui import launch_streamlit

# Launch system
system = PinokioSystem()
launch_streamlit()
```

### Local Installation:
```bash
git clone https://github.com/your-username/pinokios-complete.git
cd pinokios-complete
pip install -r requirements.txt
python -m pinokios.ui
```

## 📁 Structure

```
pinokios-complete/
├── pinokios/           # Core system modules
├── examples/           # Usage examples  
├── notebooks/          # Ready-to-run notebooks
├── scripts/            # Utility scripts
└── docs/              # Documentation
```

## 🔍 Search Examples

```python
from pinokios import search_apps

# Find image generation apps
image_apps = search_apps(category="IMAGE", min_stars=5)

# Find high-VRAM apps  
gpu_apps = search_apps(min_vram="8GB")

# Search by tags
audio_apps = search_apps(tags=["audio", "tts"])
```

## 📋 Categories

- **AUDIO** - TTS, voice cloning, audio processing
- **IMAGE** - Stable Diffusion, image generation, editing  
- **VIDEO** - Video processing, face swap, animation
- **LLM** - Language models, chat interfaces
- **UTILITY** - Development tools, converters
- **3D** - 3D generation, mesh processing

## 🛠️ Requirements

- Python 3.8+
- Git
- 4GB+ RAM recommended
- GPU optional (for AI apps)

## 📖 Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [API Reference](docs/API.md) 
- [Contributing](docs/CONTRIBUTING.md)

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## 📜 License

MIT License - see LICENSE file for details.

---

**Made with ❤️ for the Pinokio Community**
