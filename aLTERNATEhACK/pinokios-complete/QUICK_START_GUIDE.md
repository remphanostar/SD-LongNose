# PinokioCloud Quick Start Guide

## 📋 Project Files Overview

### `Pinokio.md` (85KB)
**Purpose**: Complete technical reference documentation for the original Pinokio platform
- Comprehensive API documentation and script format specifications
- JS/JSON execution patterns and variable substitution rules
- Platform architecture and command structure details
- **Use when**: Understanding how Pinokio scripts work internally or debugging execution issues

### `PROJECT_HANDOVER_GUIDE.md` (4KB)
**Purpose**: Minimized AI agent handover document for project takeover
- Essential technical architecture and component breakdown
- Critical implementation rules and constraints
- Complete testing setup with mock environment instructions
- Database file relationships (AppData.json vs cleaned_pinokio_apps.json)
- **Use when**: Taking over the project or setting up development environment

### `AppData.json` vs `cleaned_pinokio_apps.json`
- **AppData.json**: Original 162KB raw database file (reference only)
- **cleaned_pinokio_apps.json**: Active 206KB processed database with verified URLs and standardized fields

---

## 🚀 Optimal Startup Workflow

### For Immediate Deployment (Recommended)
1. **Open Google Colab**: https://colab.research.google.com
2. **Load deployment notebook**: `PinokioCloud_Colab_Generated.ipynb`
3. **Run all cells** - automatically clones repo and launches UI
4. **Access via ngrok URL** - provided in cell output

### For Development Setup
1. **Read handover guide**: `PROJECT_HANDOVER_GUIDE.md` (start here)
2. **Install dependencies**: 
   ```bash
   pip install streamlit>=1.28.0 pyngrok>=7.0.0 psutil>=5.9.0 gitpython>=3.1.0 nest_asyncio>=1.5.0 pandas>=1.5.0 requests>=2.28.0 nbformat>=5.0.0 jupyter
   ```
3. **Set up mock environment**: Follow testing setup in handover guide
4. **Test core components**: 
   ```bash
   python -c "from PinokioCloud_Colab.unified_engine import UnifiedPinokioEngine; print('Engine loaded')"
   streamlit run PinokioCloud_Colab/streamlit_colab.py
   ```

### For Understanding Pinokio Scripts
1. **Read Pinokio.md**: Comprehensive technical reference
2. **Examine sample apps**: Check `cleaned_pinokio_apps.json` structure
3. **Study engine code**: `PinokioCloud_Colab/unified_engine.py`

---

## ⚡ Priority Reading Order
1. **PROJECT_HANDOVER_GUIDE.md** - Essential project overview
2. **This file** - Quick orientation  
3. **README.md** - Basic project info
4. **Pinokio.md** - Deep technical reference (as needed)

---

**Repository**: https://github.com/remphanostar/SD-LongNose  
**Main Deployment**: `PinokioCloud_Colab_Generated.ipynb`  
**Development Files**: `PinokioCloud_Colab/` directory
