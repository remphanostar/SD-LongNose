# AI Agent Project Handover: PinokioCloud

## Project Overview
Cloud-native Pinokio AI app manager for Google Colab. Executes JS/JSON Pinokio scripts, manages 284+ AI apps via Streamlit UI with ngrok tunneling.

**Repository**: https://github.com/remphanostar/SD-LongNose
**Deployment**: `PinokioCloud_Colab_Generated.ipynb` (single-file Colab solution)

## Core Architecture
```
unified_engine.py -> Pinokio JS/JSON executor (install/run apps)  
streamlit_colab.py -> Web UI (browse/manage apps)
cleaned_pinokio_apps.json -> 284+ app database
generate_notebook.py -> Creates deployment notebook
```

## Critical Implementation Rules
1. Full implementation only - no placeholders
2. Never claim non-existent functionality  
3. Use absolute paths (`/content/...`)
4. Add `#@title` to notebook cells
5. Try alternatives before terminal commands

## Key Technical Details

### App Database Files
**AppData.json** (Original): User's original 162KB database file containing raw app data
**cleaned_pinokio_apps.json** (Active): 206KB processed database used by the system

The cleaned version is a 1:1 replication of app details with:
- Verified repository URLs and clone endpoints
- Standardized field names (`clone_url`, `repo_url`, `url`)
- Consistent app name mappings (`title`, `name`, `Appname`)
- Quality-checked install methods and categories

```json
{
  "app-key": {
    "name": "Display Name",
    "clone_url": "https://github.com/author/repo.git", 
    "category": "IMAGE|AUDIO|VIDEO|LLM|UTILITY",
    "has_install_js": true,
    "installer_type": "js|json"
  }
}
```

### Engine Methods
- `install_app()`: Clone repo + execute install scripts
- `run_app()`: Execute start scripts  
- `execute_script()`: Parse JS/JSON Pinokio format
- App name matching: `title`, `name`, `Appname` fields
- URL resolution: `clone_url`, `repo_url`, `url` fields

### Colab Integration  
- Base path: `/content/SD-LongNose/PinokioCloud_Colab/`
- Apps JSON: `/content/SD-LongNose/PinokioCloud_Colab/cleaned_pinokio_apps.json`
- ngrok token: `31hXIA9IPUsFAnKFrZ92A7jgwj3_5zwfYZfiJRYGacXizWs9K`

---

## Internal Testing Setup

### Required Downloads/Installs
```bash
pip install streamlit>=1.28.0 pyngrok>=7.0.0 psutil>=5.9.0 
pip install gitpython>=3.1.0 nest_asyncio>=1.5.0 pandas>=1.5.0 requests>=2.28.0
pip install nbformat>=5.0.0 jupyter
```

### Mock Colab Environment Setup

#### 1. Directory Structure  
```
/content/
├── SD-LongNose/
│   └── PinokioCloud_Colab/
│       ├── unified_engine.py
│       ├── streamlit_colab.py  
│       ├── cleaned_pinokio_apps.json
│       └── generate_notebook.py
└── pinokio_apps/ (created by engine)
```

#### 2. Mock CUDA/PyTorch Detection
Create fake nvidia-smi:
```python
# mock_nvidia_smi.py
import sys
if len(sys.argv) > 1 and '--query-gpu=name' in sys.argv:
    print("Tesla T4")
    sys.exit(0)
```
Make executable and add to PATH before testing.

#### 3. Environment Variables
```python
import sys
sys.modules['google.colab'] = type(sys)('google.colab')  # Mock Colab detection
os.environ['COLAB_GPU'] = '1'
```

### Test Notebook Creation
Convert `PinokioCloud_Colab/generate_notebook.py` to `.ipynb`:

```python  
import nbformat as nbf

# Load generate_notebook.py content
with open('generate_notebook.py', 'r') as f:
    code = f.read()

# Create notebook  
nb = nbf.v4.new_notebook()
nb.cells = [nbf.v4.new_code_cell(code)]

# Save as .ipynb
with open('test_notebook.ipynb', 'w') as f:
    nbf.write(nb, f)
```

### Critical File Paths to Replicate
- `/content/SD-LongNose/PinokioCloud_Colab/cleaned_pinokio_apps.json`
- `/content/pinokio_apps/` (app installation directory)
- `/content/SD-LongNose/PinokioCloud_Colab/unified_engine.py`
- `/content/SD-LongNose/PinokioCloud_Colab/streamlit_colab.py`

### Testing Commands
```bash
# Test engine directly
python -c "from unified_engine import UnifiedPinokioEngine; print('Engine loaded')"

# Test Streamlit UI  
streamlit run streamlit_colab.py --server.port 8501

# Test notebook generation
python generate_notebook.py
```

### Recent Fixes Applied
- Fixed JSON path: `/content/SD-LongNose/PinokioCloud_Colab/cleaned_pinokio_apps.json`
- Enhanced app name matching (multiple fields)
- Added verbose logging with emoji status
- Fixed git clone URL resolution

### Common Issues
- `Apps data file not found` → Check JSON file path
- `App not found in database` → Name field mismatch  
- Git clone failures → URL field mapping fixed
- Missing verbose logs → Added comprehensive logging

**Deployment**: Run generated notebook in Colab, auto-clones repo and launches UI with ngrok tunnel.
