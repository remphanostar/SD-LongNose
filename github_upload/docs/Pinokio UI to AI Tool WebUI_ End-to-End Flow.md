<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Pinokio UI to AI Tool WebUI: End-to-End Flow

## 1. Pinokio Initialization

1. **Application Launch**
    - Execute the Pinokio AppImage or binary with GUI or headless flags:

```bash
./Pinokio-linux.AppImage --no-sandbox
```

    - Internally, Pinokio’s **main process** (Electron or headless mode) starts.
2. **Filesystem and Configuration Setup**
    - Create or verify `~/pinokio/` directory structure.
    - Load global configuration from `~/pinokio/config.json`.
    - Initialize shared binaries in `~/pinokio/bin/` (ensure Node.js, Python, Git present).
3. **Server and IPC Bridge**
    - Start an internal web server on default port `42000`.
    - Establish IPC channels between Electron main process and Chromium renderer.
    - Expose JSON-RPC API endpoints at `/api`.
4. **Discovery and UI Rendering**
    - Renderer process fetches `/api/apps/list` to populate the UI with available tools.
    - Display **Discover**, **Installed**, and **Settings** tabs in the GUI.

***

## 2. Selecting and Installing an AI Tool

1. **User Action: Install Request**
    - Click “Install” on a tool entry in the Discover tab (e.g., ComfyUI).
    - Renderer sends JSON-RPC request:

```json
{ "id":1, "method":"install", "params":{"app":"comfyui"} }
```

2. **Installation Script Execution**
    - Pinokio core retrieves `install.json` from the app’s Git repository under `api/comfyui.git/`.
    - Execute `fs.download` steps:
        - Download code archive (ZIP/TAR).
        - Unzip into `~/pinokio/api/comfyui.git/server/`.
    - Execute `shell.run` steps:
        - Create Python virtual environment: `python -m venv env`.
        - Activate venv and install dependencies from `requirements.txt` via `pip install`.
    - **Cache Management**
        - Model files referenced in install script (`.ckpt`, `.safetensors`, `.bin`) are downloaded into `~/pinokio/cache/` or `~/pinokio/drive/models/` for reuse.
3. **Post-Install Hooks**
    - Run optional `process.daemonize` to pre-launch required background services.
    - Update `~/pinokio/logs/installation.log` with success or error details.
    - Notify renderer of completion via JSON-RPC event.

***

## 3. Launching the AI Tool WebUI

1. **User Action: Launch Request**
    - Click “Start” on the Installed tab for ComfyUI.
    - Renderer sends JSON-RPC request:

```json
{ "id":2, "method":"start", "params":{"app":"comfyui"} }
```

2. **Process Daemonization**
    - Pinokio core executes `process.daemonize` entry in `install.json` or `run.json`:

```json
{
  "method":"process.daemonize",
  "params":{
    "command":"python server.py",
    "path":"server",
    "venv":"env",
    "port":7860
  }
}
```

    - Creates a background process group, capturing stdout/stderr to `~/pinokio/logs/comfyui.log`.
3. **Port Allocation and Monitoring**
    - Assign dynamic port (default 7860) or user-configured port.
    - Continuously poll `http://localhost:7860` until ready (status 200).
4. **WebUI Injection**
    - Pinokio core informs renderer of the tool’s URL:

```json
{ "event":"app_started", "params":{"app":"comfyui","url":"http://localhost:7860"} }
```

    - Renderer embeds an `<iframe>` or new window pointing to the tool’s WebUI.

***

## 4. Runtime Management and User Interaction

1. **UI Controls**
    - **Start/Stop**: Buttons trigger JSON-RPC `start` and `stop` methods.
    - **Status**: Periodic JSON-RPC `status` calls check process health.
    - **Logs**: Fetch `~/pinokio/logs/comfyui.log` via JSON-RPC `fs.read` for display.
2. **File and Model Operations**
    - Within the WebUI, users request model downloads or uploads.
    - Pinokio intercepts these via RPC hooks and routes them through `fs.download` or `fs.upload` modules, storing in `cache/` or `drive/`.
3. **Dependency and Resource Sharing**
    - Common dependencies (e.g., PyTorch, CUDA libraries) are maintained in `bin/` and shared across apps.
    - Models in `drive/models/` are symlinked into each app’s `server/models/` as needed.
4. **Stopping and Cleanup**
    - Clicking “Stop” triggers JSON-RPC `stop` method to send SIGTERM to the process group.
    - Pinokio core calls cleanup hooks to remove temporary files in `cache/Temp/`.
    - Logs updated with shutdown events.

***

## 5. Summary of Core Functions

| Function Module | Purpose |
| :-- | :-- |
| fs.download | Download archives or files; supports unzip/tar extraction |
| fs.read / fs.write | Read and write configuration or log files |
| shell.run | Execute shell commands in specified path and virtual environment |
| process.daemonize | Launch commands as background services with process group management |
| browser.open | Open or embed WebUI URLs in the renderer process |
| install (JSON-RPC) | High-level entry for installation workflow, orchestrating fs.download and shell.run calls |
| start / stop (RPC) | Control app lifecycle—start, stop, and check status |
| cache management | Centralized storage of model files and package caches for reuse |
| logging | Capture installation and runtime logs into `~/pinokio/logs/` |

This end-to-end flow illustrates each function—from booting the Pinokio UI to installing and running AI tool WebUIs—clarifying how Pinokio automates downloads, environment setup, process management, and user interaction.

