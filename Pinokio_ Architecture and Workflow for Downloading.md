<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Pinokio: Architecture and Workflow for Downloading, Installing, and Running AI Tools

## 1. Overview

Pinokio functions as a **virtual AI computer** that automates the entire lifecycle of AI applications—download, installation, environment isolation, execution, and web-based access—using declarative JSON-RPC scripts and a unified filesystem layout. It abstracts away manual dependency management and ensures consistent, reproducible deployments of diverse AI tools.

## 2. Filesystem Layout

All Pinokio-managed resources reside under a single root directory, typically `~/pinokio/`, subdivided into:

- **api/**
Contains one subdirectory per application, each mirroring a Git repository:

```
~/pinokio/api/<app-name>.git/
├── install.json      # JSON-RPC installation script
└── server/           # Application code files after download
```

- **bin/**
Shared binaries maintained by Pinokio (e.g., Node.js, Python interpreters, Git).
- **cache/**
Temporary and caching storage:
    - Model checkpoints (`.ckpt`, `.safetensors`, `.bin`, `.gguf`)
    - Pip and HuggingFace caches
    - Gradio/Temp files
- **drive/**
Shared model and asset storage for cross-application reuse:

```
~/pinokio/drive/models/
├── checkpoints/
├── loras/
├── vae/
└── embeddings/
```

- **logs/**
Installation and runtime logs for debugging and audit.


## 3. Download Formats and Sources

Pinokio supports fetching AI tools and models in multiple formats:

- **Archive Formats**:
    - ZIP (`.zip`), TAR.GZ (`.tar.gz`) for application code
    - Unpacked automatically into `api/<app>/server/`
- **Model Files**:
    - Checkpoints (`.ckpt`, `.bin`)
    - Optimized tensors (`.safetensors`)
    - Quantized formats (`.gguf`)
    - HuggingFace format via HF Hub APIs
- **Data \& Assets**:
    - Embeddings (`.pt`, `.bin`)
    - LoRA adapters (`.safetensors`)
    - Auxiliary files (JSON/YAML configs, INI)

Sources include GitHub releases, HuggingFace repositories, Google Drive URLs, and custom HTTP(S) endpoints.

## 4. Declarative Installation with JSON-RPC

Each application’s install script (`install.json`) is a JSON-RPC command sequence that Pinokio’s engine interprets to perform filesystem and shell operations:

```json
{
  "run": [
    {
      "method": "fs.download",
      "params": {
        "url": "https://github.com/comfyanonymous/ComfyUI/archive/refs/heads/master.zip",
        "path": "server",
        "unzip": true
      }
    },
    {
      "method": "shell.run",
      "params": {
        "message": "python -m venv env",
        "path": "server"
      }
    },
    {
      "method": "shell.run",
      "params": {
        "message": "pip install -r requirements.txt",
        "path": "server",
        "venv": "env"
      }
    }
  ]
}
```

Key operations:

- **fs.download**: Fetch files or archives and optionally unpack them.
- **shell.run**: Execute shell commands within specified paths and virtual environments.
- **fs.write**: Create or modify configuration files.
- **process.daemonize**: Launch applications as background services.
- **browser.open**: Automatically open web UIs on local ports.

Scripts can self-modify or invoke other scripts, enabling complex orchestration and updates.

## 5. Environment Isolation and Execution

### Virtual Environments

- **Python venv** per application ensures dependency isolation.
- Shared binaries in `bin/` reduce redundant installations of Node.js or Git.


### Sandboxed Execution

- All operations are confined to subdirectories under `~/pinokio/api/<app-name>.git/`.
- Path validation prevents scripts from escaping their namespace.
- Resource sharing (GPU drivers, system libraries) is managed by Pinokio without full containerization overhead.


### Daemon and Headless Modes

- Applications can run headless with `--no-sandbox` flags.
- Pinokio can launch Electron-based web interfaces or pure web-server modes:

```bash
./Pinokio-linux.AppImage --headless --no-sandbox
```

- Supports Xvfb virtual displays for GUI components when needed.


## 6. Running Multiple AI Tools

Pinokio’s orchestration engine allows concurrent management of multiple applications:

- Each app runs on its own port (e.g., 7860, 8080, 3000).
- Central JSON-RPC API (`http://localhost:<port>/api`) controls installs, starts, stops, and status checks.
- Shared `drive/models` avoids redundant model downloads.
- Dynamic port allocation prevents conflicts.

Example to start two apps:

```json
{
  "run": [
    { "method": "shell.run", "params": { "message": "./run_comfyui.sh", "daemon": true } },
    { "method": "shell.run", "params": { "message": "./run_sd_webui.sh", "daemon": true } }
  ]
}
```


## 7. Summary

Pinokio’s combination of a structured filesystem layout, declarative JSON-RPC installation scripts, and lightweight isolation provides a seamless “one-click” experience for downloading, installing, and running diverse AI tools. Its modular architecture supports reproducibility, resource efficiency, and scalability across local and cloud GPU environments. continuous script-driven orchestration ensures that AI applications remain up-to-date and easily manageable without manual intervention.

