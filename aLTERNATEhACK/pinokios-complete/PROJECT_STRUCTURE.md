# CloudPinokio Complete - Project Structure

## 📁 Project Organization

```
pinokios-complete/
├── 📄 AppData.json                     # ⭐ OFFICIAL Pinokio AppData (PRESERVED)
├── 📄 cleaned_pinokio_apps.json        # 284 verified apps from AppData.json
├── 📄 README.md                        # Main project documentation
├── 📄 requirements.txt                 # Python dependencies
├── 📄 PinokiOS_Complete_Colab.ipynb   # Jupyter notebook for Colab
│
├── 📁 pinokios/                        # 🚀 CORE SYSTEM
│   ├── __init__.py
│   ├── database.py                     # App database (now loads cleaned data)
│   ├── engine.py                       # Main Pinokio engine
│   ├── core.py                        # Core Pinokio functionality
│   └── ui.py                          # UI components
│
├── 📁 ui/                              # 🎨 USER INTERFACES
│   ├── streamlit_app.py                # Main Streamlit interface
│   └── streamlit_cloud_pinokio.py      # Cloud-enhanced Streamlit UI
│
├── 📁 utils/                           # 🔧 UTILITIES
│   └── conversion_scripts/
│       ├── convert_appdata_to_dict.py  # AppData.json converter
│       ├── validate_dictionary.py      # Dictionary validation
│       └── js_to_python_converter.py   # JS to Python converter
│
├── 📁 docs/                            # 📚 DOCUMENTATION
│   ├── Pinokio.md                      # Official Pinokio documentation
│   ├── program.pinokio.md              # Pinokio programming guide
│   ├── COLAB_SETUP_INSTRUCTIONS.md    # Setup instructions for Colab
│   ├── architecture/
│   │   └── cloud_pinokio_architecture.md
│   └── reports/
│       ├── appdata_conversion_report.md
│       └── dictionary_audit_results.md
│
├── 📁 archive/                         # 🗄️ ARCHIVED FILES
│   └── legacy_databases/
│       ├── 267.py                      # Original 267 apps database
│       └── cleaned_pinokio_apps.py     # Python version of cleaned data
│
├── 📁 AppExample/                      # 📋 EXAMPLE APP
└── 📁 pinokio_apps/                    # 🎯 INSTALLED APPS DIRECTORY
```

## 🚀 Core Components

### Main System (`pinokios/`)
- **database.py**: Integrated app database that loads from `cleaned_pinokio_apps.json`
- **engine.py**: Core Pinokio engine with cloud adaptations
- **core.py**: Enhanced Pinokio functionality
- **ui.py**: UI helper components

### Cloud Integration Files (Root Level)
- **pinokio_emulator.py**: Pinokio API emulator for cloud environments
- **pinokio_app_manager.py**: App lifecycle management with venv isolation

### User Interfaces (`ui/`)
- **streamlit_app.py**: Feature-rich Streamlit interface for local/cloud use
- **streamlit_cloud_pinokio.py**: Cloud-optimized Streamlit interface

## 📊 Data Files

### ⭐ Primary Data Sources
- **AppData.json**: Original official Pinokio app data (PRESERVED)
- **cleaned_pinokio_apps.json**: 284 verified apps with validated structure

### 🗄️ Archived Data
- **267.py**: Legacy database (moved to archive)
- **cleaned_pinokio_apps.py**: Python format of cleaned data (archived)

## 🛠️ Development Workflow

1. **Core System**: Use `pinokios/` for main functionality
2. **UI Development**: Work in `ui/` directory
3. **Data Processing**: Use `utils/conversion_scripts/`
4. **Documentation**: Update files in `docs/`
5. **Testing**: Installed apps go to `pinokio_apps/`

## 🌐 Cloud Deployment

### Google Colab
1. Use `PinokiOS_Complete_Colab.ipynb`
2. Follow `docs/COLAB_SETUP_INSTRUCTIONS.md`

### Streamlit Cloud
1. Use `ui/streamlit_cloud_pinokio.py`
2. Ensure `requirements.txt` is updated

### Lightning AI / Other Platforms
1. Use `pinokio_emulator.py` for cloud adaptations
2. Reference `docs/architecture/cloud_pinokio_architecture.md`

## 🔧 Key Features

- ✅ 284 verified Pinokio apps from official AppData.json
- ✅ Cloud environment detection and adaptation
- ✅ Virtual environment isolation per app
- ✅ Real Pinokio script execution (JS/JSON → Python)
- ✅ Modern web UI with Streamlit
- ✅ GPU optimization for cloud platforms
- ✅ App lifecycle management (install/run/stop/uninstall)
