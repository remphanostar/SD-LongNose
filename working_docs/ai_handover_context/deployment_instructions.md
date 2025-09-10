# PinokioCloud Deployment Instructions

## Overview
This document provides comprehensive deployment instructions for PinokioCloud across all target cloud platforms. Deployment procedures are optimized for each platform while maintaining consistency and reliability.

## Pre-Deployment Requirements

### System Requirements
- **Python**: 3.8-3.11 (3.13.3 recommended)
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Storage**: Minimum 20GB available space (50GB+ recommended)
- **Network**: Stable internet connection for downloads and tunneling
- **GPU**: Optional but recommended for AI applications

### Cloud Platform Requirements
- **Google Colab**: Free or Pro tier account
- **Vast.ai**: Account with GPU instance access
- **Lightning.ai**: Studio account with team workspace
- **Paperspace**: Gradient account with GPU access
- **RunPod**: Account with serverless or persistent instances

### Dependencies
- **Core Packages**: Streamlit, Jupyter, pyngrok, requests, psutil
- **Cloud Packages**: Platform-specific packages as needed
- **Development Tools**: Git, curl, wget, build-essential
- **Tunneling**: ngrok account with authentication token

## Deployment Procedures by Platform

### Google Colab Deployment

#### Step 1: Environment Setup
```python
# Cell 1: Environment Detection and Setup
import sys
import os
import platform
import subprocess

# Detect Colab environment
is_colab = 'google.colab' in sys.modules
if is_colab:
    print("✅ Google Colab environment detected")
    base_path = "/content"
else:
    print("⚠️ Non-Colab environment detected")
    base_path = os.getcwd()

# Install system packages
!apt update
!apt install -y git curl wget build-essential

# Install Python packages
!pip install --upgrade pip setuptools wheel
!pip install streamlit jupyter pyngrok requests psutil
```

#### Step 2: Repository Cloning
```python
# Cell 2: Repository Management
import git
import os

# Clone repository
repo_url = "https://github.com/your-org/cloud-pinokio.git"
repo_path = f"{base_path}/cloud-pinokio"

if os.path.exists(repo_path):
    print("✅ Repository already exists, updating...")
    !cd {repo_path} && git pull
else:
    print("📥 Cloning repository...")
    !git clone {repo_url} {repo_path}

# Set working directory
os.chdir(repo_path)
print(f"✅ Working directory: {os.getcwd()}")
```

#### Step 3: Environment Configuration
```python
# Cell 3: Environment Configuration
import json
import os

# Create configuration
config = {
    "platform": "google_colab",
    "base_path": base_path,
    "storage_path": f"{base_path}/pinokio_storage",
    "venv_path": f"{base_path}/pinokio_venvs",
    "tunnel_provider": "ngrok",
    "session_timeout": 3600
}

# Save configuration
config_path = f"{base_path}/pinokio_config.json"
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Configuration saved")
```

#### Step 4: Service Launch
```python
# Cell 4: Service Launch
import subprocess
import time
import threading

# Launch Streamlit
def launch_streamlit():
    subprocess.run([
        "streamlit", "run", "app/app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ])

# Launch in background
streamlit_thread = threading.Thread(target=launch_streamlit)
streamlit_thread.daemon = True
streamlit_thread.start()

# Wait for startup
time.sleep(5)
print("✅ Streamlit launched")
```

#### Step 5: Tunnel Setup
```python
# Cell 5: Tunnel Setup
from pyngrok import ngrok
import time

# Set ngrok token (replace with your token)
ngrok.set_auth_token("your_ngrok_token_here")

# Create tunnel
tunnel = ngrok.connect(8501)
public_url = tunnel.public_url

print(f"✅ Public URL: {public_url}")
print(f"🔗 Access your PinokioCloud at: {public_url}")
```

### Vast.ai Deployment

#### Step 1: Instance Setup
```bash
# SSH into Vast.ai instance
ssh root@your-instance-ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y git curl wget build-essential python3-pip

# Install Python packages
pip3 install --upgrade pip setuptools wheel
pip3 install streamlit jupyter pyngrok requests psutil
```

#### Step 2: Repository Setup
```bash
# Clone repository
git clone https://github.com/your-org/cloud-pinokio.git
cd cloud-pinokio

# Create configuration
cat > config.json << EOF
{
  "platform": "vastai",
  "base_path": "/workspace",
  "storage_path": "/workspace/pinokio_storage",
  "venv_path": "/workspace/pinokio_venvs",
  "tunnel_provider": "ngrok",
  "instance_type": "gpu",
  "auto_shutdown": true
}
EOF
```

#### Step 3: Certificate Setup (Optional)
```bash
# Install certificates for direct HTTPS access
# Follow Vast.ai documentation for certificate installation
# This enables direct access without tunneling
```

#### Step 4: Service Launch
```bash
# Launch Streamlit
streamlit run app/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true &

# Set up ngrok tunnel
ngrok authtoken your_ngrok_token_here
ngrok http 8501 &

# Get public URL
sleep 5
curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | cut -d'"' -f4
```

### Lightning.ai Deployment

#### Step 1: Studio Setup
```python
# In Lightning Studio
import os
import subprocess

# Install dependencies
subprocess.run(["pip", "install", "streamlit", "jupyter", "pyngrok", "requests", "psutil"])

# Clone repository
subprocess.run(["git", "clone", "https://github.com/your-org/cloud-pinokio.git"])
os.chdir("cloud-pinokio")
```

#### Step 2: Team Configuration
```python
# Configure for team workspace
config = {
    "platform": "lightning_ai",
    "base_path": "/teamspace/studios/current_studio",
    "storage_path": "/teamspace/studios/current_studio/pinokio_storage",
    "venv_path": "/teamspace/studios/current_studio/pinokio_venvs",
    "tunnel_provider": "ngrok",
    "team_workspace": True,
    "collaboration": True
}

# Save configuration
import json
with open("config.json", "w") as f:
    json.dump(config, f, indent=2)
```

#### Step 3: Service Launch
```python
# Launch Streamlit
import subprocess
import threading

def launch_streamlit():
    subprocess.run([
        "streamlit", "run", "app/app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])

# Launch in background
thread = threading.Thread(target=launch_streamlit)
thread.daemon = True
thread.start()
```

### Paperspace Deployment

#### Step 1: Gradient Setup
```bash
# In Gradient notebook
pip install streamlit jupyter pyngrok requests psutil

# Clone repository
git clone https://github.com/your-org/cloud-pinokio.git
cd cloud-pinokio
```

#### Step 2: Configuration
```python
# Configure for Paperspace
config = {
    "platform": "paperspace",
    "base_path": "/notebooks",
    "storage_path": "/notebooks/pinokio_storage",
    "venv_path": "/notebooks/pinokio_venvs",
    "tunnel_provider": "ngrok",
    "gpu_available": True
}

import json
with open("config.json", "w") as f:
    json.dump(config, f, indent=2)
```

#### Step 3: Service Launch
```python
# Launch Streamlit
import subprocess
import threading

def launch_streamlit():
    subprocess.run([
        "streamlit", "run", "app/app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])

thread = threading.Thread(target=launch_streamlit)
thread.daemon = True
thread.start()
```

### RunPod Deployment

#### Step 1: Instance Setup
```bash
# SSH into RunPod instance
ssh root@your-instance-ip

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y git curl wget build-essential python3-pip

# Install Python packages
pip3 install --upgrade pip setuptools wheel
pip3 install streamlit jupyter pyngrok requests psutil
```

#### Step 2: Repository Setup
```bash
# Clone repository
git clone https://github.com/your-org/cloud-pinokio.git
cd cloud-pinokio

# Create configuration
cat > config.json << EOF
{
  "platform": "runpod",
  "base_path": "/workspace",
  "storage_path": "/workspace/pinokio_storage",
  "venv_path": "/workspace/pinokio_venvs",
  "tunnel_provider": "ngrok",
  "instance_type": "gpu",
  "persistent": true
}
EOF
```

#### Step 3: Service Launch
```bash
# Launch Streamlit
streamlit run app/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true &

# Set up ngrok tunnel
ngrok authtoken your_ngrok_token_here
ngrok http 8501 &

# Get public URL
sleep 5
curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*' | cut -d'"' -f4
```

## Post-Deployment Configuration

### Environment Validation
```python
# Validate deployment
import sys
import os
import json

# Check Python version
python_version = sys.version_info
print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")

# Check required packages
required_packages = ["streamlit", "jupyter", "pyngrok", "requests", "psutil"]
for package in required_packages:
    try:
        __import__(package)
        print(f"✅ {package} installed")
    except ImportError:
        print(f"❌ {package} not installed")

# Check configuration
config_path = "config.json"
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
    print(f"✅ Configuration loaded: {config['platform']}")
else:
    print("❌ Configuration file not found")

# Check storage
storage_path = config.get("storage_path", "/tmp")
if os.path.exists(storage_path):
    print(f"✅ Storage path exists: {storage_path}")
else:
    print(f"❌ Storage path not found: {storage_path}")
```

### Service Health Check
```python
# Health check
import requests
import time

# Check Streamlit service
try:
    response = requests.get("http://localhost:8501", timeout=5)
    if response.status_code == 200:
        print("✅ Streamlit service running")
    else:
        print(f"❌ Streamlit service error: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"❌ Streamlit service not accessible: {e}")

# Check ngrok tunnel
try:
    response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
    if response.status_code == 200:
        tunnels = response.json()
        if tunnels.get("tunnels"):
            print("✅ ngrok tunnel active")
        else:
            print("❌ No ngrok tunnels active")
    else:
        print(f"❌ ngrok API error: {response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"❌ ngrok not accessible: {e}")
```

## Troubleshooting

### Common Issues

#### Issue 1: Streamlit Not Starting
**Symptoms**: Streamlit service fails to start
**Causes**: Port conflicts, missing dependencies, configuration errors
**Solutions**:
1. Check port availability: `netstat -tlnp | grep 8501`
2. Install missing dependencies: `pip install streamlit`
3. Check configuration file: `cat config.json`
4. Restart service: `pkill streamlit && streamlit run app/app.py`

#### Issue 2: ngrok Tunnel Not Working
**Symptoms**: No public URL generated, tunnel connection failed
**Causes**: Invalid token, network issues, ngrok service down
**Solutions**:
1. Verify ngrok token: `ngrok authtoken your_token_here`
2. Check network connectivity: `ping ngrok.com`
3. Restart ngrok: `pkill ngrok && ngrok http 8501`
4. Check ngrok status: `curl http://localhost:4040/api/tunnels`

#### Issue 3: Repository Clone Failed
**Symptoms**: Git clone operation fails
**Causes**: Network issues, authentication problems, repository access
**Solutions**:
1. Check network connectivity: `ping github.com`
2. Verify repository URL and access
3. Use HTTPS instead of SSH: `git clone https://github.com/...`
4. Check git configuration: `git config --list`

#### Issue 4: Dependencies Installation Failed
**Symptoms**: pip install fails for required packages
**Causes**: Network issues, package conflicts, insufficient permissions
**Solutions**:
1. Update pip: `pip install --upgrade pip`
2. Use alternative package sources: `pip install -i https://pypi.org/simple/ package_name`
3. Install packages individually: `pip install streamlit && pip install jupyter`
4. Check system dependencies: `apt install python3-dev build-essential`

#### Issue 5: Configuration Errors
**Symptoms**: Application fails to start, configuration not found
**Causes**: Missing configuration file, invalid JSON, wrong paths
**Solutions**:
1. Check configuration file exists: `ls -la config.json`
2. Validate JSON syntax: `python -m json.tool config.json`
3. Verify paths exist: `ls -la /path/to/storage`
4. Recreate configuration: Follow deployment steps

### Performance Optimization

#### Memory Optimization
```python
# Monitor memory usage
import psutil
import os

def monitor_memory():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.2f} MB")
    
    if memory_mb > 2000:  # 2GB threshold
        print("⚠️ High memory usage detected")
        # Implement cleanup procedures
        cleanup_temp_files()
        gc.collect()

# Cleanup temporary files
def cleanup_temp_files():
    import shutil
    temp_dirs = ["/tmp", "/var/tmp"]
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            for item in os.listdir(temp_dir):
                if item.startswith("pinokio_"):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                    except Exception as e:
                        print(f"Error cleaning {item_path}: {e}")
```

#### Storage Optimization
```python
# Monitor storage usage
import shutil

def monitor_storage():
    total, used, free = shutil.disk_usage("/")
    free_gb = free // (1024**3)
    print(f"Free storage: {free_gb} GB")
    
    if free_gb < 5:  # 5GB threshold
        print("⚠️ Low storage space detected")
        # Implement cleanup procedures
        cleanup_old_models()
        cleanup_logs()

# Cleanup old models and logs
def cleanup_old_models():
    import time
    import os
    
    models_path = "storage/models"
    if os.path.exists(models_path):
        current_time = time.time()
        for item in os.listdir(models_path):
            item_path = os.path.join(models_path, item)
            if os.path.isfile(item_path):
                file_age = current_time - os.path.getmtime(item_path)
                if file_age > 7 * 24 * 3600:  # 7 days
                    try:
                        os.remove(item_path)
                        print(f"Removed old model: {item}")
                    except Exception as e:
                        print(f"Error removing {item}: {e}")
```

## Maintenance Procedures

### Regular Maintenance
```bash
# Daily maintenance script
#!/bin/bash

# Update system packages
apt update && apt upgrade -y

# Clean package cache
apt autoremove -y
apt autoclean

# Clean temporary files
find /tmp -type f -name "pinokio_*" -mtime +1 -delete
find /var/tmp -type f -name "pinokio_*" -mtime +1 -delete

# Clean log files
find /var/log -name "pinokio_*" -mtime +7 -delete

# Restart services if needed
systemctl restart pinokio-cloud
```

### Backup Procedures
```bash
# Backup configuration and data
#!/bin/bash

BACKUP_DIR="/backup/pinokio-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp config.json "$BACKUP_DIR/"

# Backup storage
tar -czf "$BACKUP_DIR/storage.tar.gz" storage/

# Backup logs
tar -czf "$BACKUP_DIR/logs.tar.gz" logs/

# Cleanup old backups (keep 7 days)
find /backup -name "pinokio-*" -mtime +7 -exec rm -rf {} \;
```

### Update Procedures
```bash
# Update PinokioCloud
#!/bin/bash

# Backup current installation
./backup.sh

# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Restart services
systemctl restart pinokio-cloud

# Verify update
./health_check.sh
```

This deployment instruction provides comprehensive guidance for deploying PinokioCloud across all target cloud platforms with proper configuration, validation, and maintenance procedures.