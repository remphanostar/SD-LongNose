# 🔧 PinokioCloud API Compliance Guide - Complete Implementation Reference

## 🎯 CORE DEVELOPMENT RULES INFUSION

**MANDATORY COMPLIANCE CHECKPOINTS** (Must verify at each step):
- ✅ **Full Implementation Only**: NEVER create placeholders or shortcut files
- ✅ **Honesty and Accuracy**: NEVER claim capabilities that don't exist
- ✅ **Context Gathering**: Consult all MD files in workspace when unsure
- ✅ **Terminal Avoidance**: Always try other methods before terminal (30s timeout if forced)
- ✅ **MCP Tools First**: Use available MCP tools before alerting limitations
- ✅ **Jupyter Format**: Always put `#@title` at header of notebook cells
- ✅ **No False Claims**: Never claim "fully functional" for non-functional demos
- ✅ **Pinokio.md API Compliance**: Every feature MUST implement exact Pinokio API methods
- ✅ **Variable Substitution**: Support {{platform}}, {{gpu}}, {{args.*}}, {{local.*}}, {{env.*}}
- ✅ **Daemon Process Support**: Honor daemon: true flag for background processes
- ✅ **Virtual Environment Isolation**: Handle venv/conda exactly like desktop Pinokio
- ✅ **Error Handling**: Never fail silently, provide user-friendly messages
- ✅ **Cloud Compatibility**: Support /content/, /workspace/, /teamspace/ paths
- ✅ **Process Tracking**: Track all spawned processes with PIDs
- ✅ **No Placeholders**: Fully implement everything attempted

---

## 📋 EXECUTIVE SUMMARY

**Source Document**: `Guides/OriginalPinokioDocumentation.md` (957 lines analyzed)
**Analysis Date**: December 2024
**Purpose**: Provide exact API implementation requirements for 100% Pinokio compatibility

**Critical Compliance Requirements**:
1. **Exact API Signatures**: All methods must match desktop Pinokio exactly
2. **Variable Substitution**: Complete {{variable}} system implementation
3. **Process Management**: Daemon support and process lifecycle management
4. **File System**: Cloud-aware path handling with security
5. **Error Handling**: Consistent error reporting and recovery mechanisms

---

## 🏗️ CORE API IMPLEMENTATION REQUIREMENTS

### **1. SHELL.RUN API - PROCESS EXECUTION ENGINE**

**API Signature** (MUST MATCH EXACTLY):
```javascript
shell.run({
  message: "string",           // Required: Command to execute
  cwd: "string",              // Optional: Working directory
  env: {},                    // Optional: Environment variables
  daemon: boolean,            // Optional: Background process flag
  on: [{                      // Optional: Event handlers
    event: "string",          // "stdout", "stderr", "end"
    return: "string"          // Action to take
  }],
  return: "string"            // Optional: Return value path
})
```

**Implementation Requirements**:
```python
class ShellRunner:
    def run(self, config):
        # 1. MANDATORY: Command validation and sanitization
        if not config.get('message'):
            raise PinokioError("shell.run requires 'message' parameter")
        
        # 2. MANDATORY: Working directory handling
        cwd = config.get('cwd', os.getcwd())
        if not os.path.exists(cwd):
            os.makedirs(cwd, exist_ok=True)
        
        # 3. MANDATORY: Environment variable merging
        env = os.environ.copy()
        env.update(config.get('env', {}))
        
        # 4. MANDATORY: Daemon process support
        if config.get('daemon', False):
            return self._start_daemon_process(config, cwd, env)
        
        # 5. MANDATORY: Real-time output streaming
        return self._execute_with_streaming(config, cwd, env)
    
    def _start_daemon_process(self, config, cwd, env):
        """CRITICAL: Must track daemon processes for cleanup"""
        process = subprocess.Popen(
            config['message'],
            cwd=cwd,
            env=env,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Create process group
        )
        
        # MANDATORY: Register daemon for cleanup
        self.daemon_processes[process.pid] = process
        return {"pid": process.pid, "status": "started"}
```

**Cloud Environment Adaptations**:
- **Path Translation**: Convert Windows paths to Unix paths for cloud platforms
- **Resource Limits**: Implement CPU/memory limits for cloud environments
- **Process Cleanup**: Automatic cleanup on notebook shutdown
- **Output Buffering**: Handle network latency in output streaming

### **2. FILE SYSTEM APIS - FS.* OPERATIONS**

**API Signatures** (MUST MATCH EXACTLY):
```javascript
// File operations
fs.write({path: "string", text: "string"})
fs.read({path: "string"})
fs.copy({src: "string", dest: "string"})
fs.move({src: "string", dest: "string"})
fs.remove({path: "string"})
fs.exists({path: "string"})

// Directory operations  
fs.mkdir({path: "string"})
fs.readdir({path: "string"})
fs.rmdir({path: "string"})

// Advanced operations
fs.download({url: "string", path: "string"})
fs.unzip({src: "string", dest: "string"})
```

**Implementation Requirements**:
```python
class FileSystemAPI:
    def __init__(self, cloud_platform):
        self.cloud_platform = cloud_platform
        self.path_mapper = CloudPathMapper(cloud_platform)
    
    def write(self, config):
        """CRITICAL: Atomic write operations with cloud path mapping"""
        path = self.path_mapper.translate_path(config['path'])
        
        # MANDATORY: Create parent directories
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # MANDATORY: Atomic write operation
        temp_path = path + '.tmp'
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(config['text'])
            os.rename(temp_path, path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise PinokioError(f"fs.write failed: {e}")
    
    def download(self, config):
        """CRITICAL: Resumable downloads with progress tracking"""
        url = config['url']
        path = self.path_mapper.translate_path(config['path'])
        
        # MANDATORY: Progress tracking for large files
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # MANDATORY: Progress callback
                    self._report_progress(downloaded, total_size)
```

**Cloud Security Requirements**:
- **Path Validation**: Prevent directory traversal attacks
- **File Size Limits**: Enforce reasonable file size limits
- **Permission Checks**: Validate read/write permissions
- **Quota Management**: Track disk usage against cloud limits

### **3. VARIABLE SUBSTITUTION SYSTEM**

**Variable Types** (MUST SUPPORT ALL):
```javascript
// Platform variables
{{platform}}          // "linux", "darwin", "win32"
{{arch}}              // "x64", "arm64"
{{gpu}}               // GPU model string
{{cuda}}              // CUDA version

// User arguments
{{args.model}}        // Command line argument
{{args.batch_size}}   // Numeric arguments

// Local variables (persistent)
{{local.api_key}}     // User-set persistent variables
{{local.model_path}}  // Installation-specific paths

// Environment variables
{{env.HOME}}          // System environment variables
{{env.CUDA_VISIBLE_DEVICES}}  // GPU configuration

// Runtime variables
{{cwd}}               // Current working directory  
{{app}}               // Current app name
{{timestamp}}         // Current timestamp
```

**Implementation Requirements**:
```python
class VariableSubstitution:
    def __init__(self, cloud_platform):
        self.platform_vars = self._detect_platform_vars(cloud_platform)
        self.local_vars = self._load_local_vars()
        self.env_vars = os.environ.copy()
    
    def substitute(self, text):
        """CRITICAL: Complete variable substitution with error handling"""
        if not isinstance(text, str):
            return text
        
        # MANDATORY: Platform variable substitution
        for var, value in self.platform_vars.items():
            text = text.replace(f"{{{{{var}}}}}", str(value))
        
        # MANDATORY: Local variable substitution
        for var, value in self.local_vars.items():
            text = text.replace(f"{{{{local.{var}}}}}", str(value))
        
        # MANDATORY: Environment variable substitution
        import re
        env_pattern = r'\{\{env\.([^}]+)\}\}'
        def replace_env(match):
            env_var = match.group(1)
            return os.environ.get(env_var, f"{{{{env.{env_var}}}}}")
        text = re.sub(env_pattern, replace_env, text)
        
        # MANDATORY: Arguments substitution
        args_pattern = r'\{\{args\.([^}]+)\}\}'
        def replace_args(match):
            arg_name = match.group(1)
            return str(self.args.get(arg_name, f"{{{{args.{arg_name}}}}}"))
        text = re.sub(args_pattern, replace_args, text)
        
        return text
    
    def _detect_platform_vars(self, cloud_platform):
        """CRITICAL: Accurate platform detection for cloud environments"""
        return {
            'platform': 'linux',  # All cloud platforms are linux
            'arch': platform.machine(),
            'gpu': self._detect_gpu(),
            'cuda': self._detect_cuda_version(),
            'cloud_platform': cloud_platform
        }
```

### **4. INPUT SYSTEM - USER INTERACTION**

**API Signatures** (MUST MATCH EXACTLY):
```javascript
input({
  message: "string",         // Prompt message
  type: "string",           // "text", "password", "number", "select"
  placeholder: "string",    // Input placeholder
  options: ["string"],      // For select type
  return: "string"         // Variable to store result
})
```

**Implementation Requirements**:
```python
class InputSystem:
    def __init__(self, ui_framework):
        self.ui = ui_framework
        self.input_history = {}
    
    def input(self, config):
        """CRITICAL: Jupyter/Streamlit compatible input handling"""
        input_type = config.get('type', 'text')
        message = config['message']
        placeholder = config.get('placeholder', '')
        
        if input_type == 'text':
            result = self.ui.text_input(message, placeholder=placeholder)
        elif input_type == 'password':
            result = self.ui.text_input(message, type='password')
        elif input_type == 'number':
            result = self.ui.number_input(message)
        elif input_type == 'select':
            options = config.get('options', [])
            result = self.ui.selectbox(message, options)
        else:
            raise PinokioError(f"Unsupported input type: {input_type}")
        
        # MANDATORY: Store result in return variable
        if config.get('return'):
            self.set_local_variable(config['return'], result)
        
        return result
```

### **5. JSON OPERATIONS - DATA MANIPULATION**

**API Signatures** (MUST MATCH EXACTLY):
```javascript
json.write({path: "string", json: object})
json.read({path: "string"})
json.set({path: "string", key: "string", value: any})
json.get({path: "string", key: "string"})
json.merge({path: "string", json: object})
```

**Implementation Requirements**:
```python
class JSONOperations:
    def write(self, config):
        """CRITICAL: Atomic JSON write with validation"""
        path = self.path_mapper.translate_path(config['path'])
        data = config['json']
        
        # MANDATORY: Validate JSON serializable
        try:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
        except TypeError as e:
            raise PinokioError(f"JSON serialization failed: {e}")
        
        # MANDATORY: Atomic write
        self.fs_api.write({'path': path, 'text': json_str})
    
    def set(self, config):
        """CRITICAL: Deep key setting with dot notation support"""
        path = config['path']
        key = config['key']
        value = config['value']
        
        # Load existing data
        try:
            data = self.read({'path': path})
        except:
            data = {}
        
        # MANDATORY: Support dot notation for nested keys
        keys = key.split('.')
        current = data
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        
        # Write back
        self.write({'path': path, 'json': data})
```

### **6. LOGGING SYSTEM - STRUCTURED LOGGING**

**API Signatures** (MUST MATCH EXACTLY):
```javascript
log({
  message: "string",       // Log message
  level: "string",        // "info", "warn", "error", "debug"
  category: "string",     // Log category
  timestamp: boolean      // Include timestamp
})
```

**Implementation Requirements**:
```python
class LoggingSystem:
    def __init__(self, log_dir):
        self.log_dir = log_dir
        self.setup_logging()
    
    def log(self, config):
        """CRITICAL: Structured logging with file and UI output"""
        message = config['message']
        level = config.get('level', 'info')
        category = config.get('category', 'general')
        
        # MANDATORY: Format log entry
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level.upper(),
            'category': category,
            'message': message
        }
        
        # MANDATORY: Write to log file
        log_file = os.path.join(self.log_dir, f"{category}.log")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # MANDATORY: Display in UI
        self.ui.write_log(log_entry)
```

---

## 🔧 ADVANCED API IMPLEMENTATIONS

### **7. NETWORK OPERATIONS - NET.* APIS**

**API Signatures** (MUST MATCH EXACTLY):
```javascript
net.download({url: "string", path: "string", headers: {}})
net.request({url: "string", method: "string", headers: {}, data: object})
net.upload({url: "string", file: "string", headers: {}})
```

**Implementation Requirements**:
```python
class NetworkOperations:
    def download(self, config):
        """CRITICAL: Resumable downloads with retry logic"""
        url = config['url']
        path = config['path']
        headers = config.get('headers', {})
        
        # MANDATORY: Resume capability
        resume_pos = 0
        if os.path.exists(path):
            resume_pos = os.path.getsize(path)
            headers['Range'] = f'bytes={resume_pos}-'
        
        # MANDATORY: Retry logic with exponential backoff
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, stream=True)
                if response.status_code in [200, 206]:
                    mode = 'ab' if resume_pos > 0 else 'wb'
                    with open(path, mode) as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    return {"status": "success", "path": path}
            except Exception as e:
                if attempt == 2:
                    raise PinokioError(f"Download failed after 3 attempts: {e}")
                time.sleep(2 ** attempt)
```

### **8. SCRIPT EXECUTION - SCRIPT.* APIS**

**API Signatures** (MUST MATCH EXACTLY):
```javascript
script.start({path: "string", args: [], env: {}})
script.stop({id: "string"})
script.status({id: "string"})
script.output({id: "string", lines: number})
```

**Implementation Requirements**:
```python
class ScriptManager:
    def __init__(self):
        self.running_scripts = {}
    
    def start(self, config):
        """CRITICAL: Script execution with process tracking"""
        script_path = config['path']
        args = config.get('args', [])
        env = config.get('env', {})
        
        # MANDATORY: Validate script exists
        if not os.path.exists(script_path):
            raise PinokioError(f"Script not found: {script_path}")
        
        # MANDATORY: Determine script type and executor
        if script_path.endswith('.py'):
            cmd = ['python']
        elif script_path.endswith('.js'):
            cmd = ['node']
        elif script_path.endswith('.sh'):
            cmd = ['bash']
        else:
            raise PinokioError(f"Unsupported script type: {script_path}")
        
        cmd.extend([script_path] + args)
        
        # MANDATORY: Start process with tracking
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, **env},
            bufsize=1,
            universal_newlines=True
        )
        
        script_id = str(uuid.uuid4())
        self.running_scripts[script_id] = {
            'process': process,
            'start_time': time.time(),
            'output_buffer': []
        }
        
        return {"id": script_id, "status": "started"}
```

### **9. NOTIFICATION SYSTEM - NOTIFY.* APIS**

**API Signatures** (MUST MATCH EXACTLY):
```javascript
notify({
  message: "string",        // Notification message
  type: "string",          // "info", "success", "warning", "error"
  duration: number,        // Display duration in seconds
  persistent: boolean      // Whether to persist across sessions
})
```

**Implementation Requirements**:
```python
class NotificationSystem:
    def notify(self, config):
        """CRITICAL: Multi-channel notification system"""
        message = config['message']
        notify_type = config.get('type', 'info')
        duration = config.get('duration', 5)
        persistent = config.get('persistent', False)
        
        # MANDATORY: UI notification
        self.ui.show_notification(message, notify_type, duration)
        
        # MANDATORY: Log notification
        self.logger.log({
            'message': f"NOTIFICATION: {message}",
            'level': notify_type,
            'category': 'notifications'
        })
        
        # OPTIONAL: Browser notification for cloud environments
        if self.is_cloud_environment():
            self._send_browser_notification(message, notify_type)
```

---

## 🚀 CLOUD ENVIRONMENT SPECIFIC IMPLEMENTATIONS

### **10. CLOUD PATH MAPPING**

**Path Translation Rules**:
```python
class CloudPathMapper:
    PLATFORM_PATHS = {
        'colab': {
            'root': '/content',
            'drive': '/content/drive/MyDrive',
            'temp': '/tmp',
            'apps': '/content/pinokios/apps'
        },
        'vastai': {
            'root': '/workspace',
            'temp': '/tmp',
            'apps': '/workspace/pinokios/apps'
        },
        'lightning': {
            'root': '/teamspace',
            'temp': '/tmp',
            'apps': '/teamspace/pinokios/apps'
        }
    }
    
    def translate_path(self, path):
        """CRITICAL: Convert Windows/Mac paths to cloud paths"""
        # Handle absolute Windows paths
        if path.startswith('C:\\'):
            path = path.replace('C:\\', '/content/')
            path = path.replace('\\', '/')
        
        # Handle relative paths
        if not path.startswith('/'):
            path = os.path.join(self.get_root_path(), path)
        
        return os.path.normpath(path)
```

### **11. PROCESS LIFECYCLE MANAGEMENT**

**Daemon Process Handling**:
```python
class ProcessManager:
    def __init__(self):
        self.daemon_processes = {}
        self.cleanup_registered = False
        self._register_cleanup()
    
    def _register_cleanup(self):
        """CRITICAL: Ensure all processes are cleaned up"""
        if not self.cleanup_registered:
            import atexit
            atexit.register(self.cleanup_all_processes)
            self.cleanup_registered = True
    
    def cleanup_all_processes(self):
        """CRITICAL: Clean shutdown of all processes"""
        for pid, process in self.daemon_processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
```

### **12. ERROR HANDLING & RECOVERY**

**Standardized Error System**:
```python
class PinokioError(Exception):
    def __init__(self, message, code=None, context=None):
        self.message = message
        self.code = code
        self.context = context or {}
        super().__init__(message)
    
    def to_dict(self):
        return {
            'error': True,
            'message': self.message,
            'code': self.code,
            'context': self.context,
            'timestamp': datetime.now().isoformat()
        }

class ErrorHandler:
    def handle_api_error(self, api_name, error, config):
        """CRITICAL: Consistent error handling across all APIs"""
        error_context = {
            'api': api_name,
            'config': config,
            'platform': self.cloud_platform
        }
        
        # Log error
        self.logger.log({
            'message': f"{api_name} error: {error}",
            'level': 'error',
            'category': 'api_errors'
        })
        
        # Notify user
        self.notify({
            'message': f"Operation failed: {error}",
            'type': 'error',
            'persistent': True
        })
        
        # Return standardized error response
        return PinokioError(str(error), context=error_context).to_dict()
```

---

## 🎯 VALIDATION & TESTING REQUIREMENTS

### **API Compatibility Testing**:
```python
class APICompatibilityTests:
    def test_shell_run_compatibility(self):
        """Test shell.run matches desktop Pinokio exactly"""
        test_cases = [
            {'message': 'echo "hello"', 'expected': 'hello\n'},
            {'message': 'pwd', 'cwd': '/tmp', 'expected_contains': '/tmp'},
            {'message': 'echo $TEST_VAR', 'env': {'TEST_VAR': 'test'}, 'expected': 'test\n'}
        ]
        
        for case in test_cases:
            result = self.shell_api.run(case)
            assert self.validate_result(result, case)
    
    def test_variable_substitution(self):
        """Test all variable types are supported"""
        test_vars = [
            '{{platform}}', '{{gpu}}', '{{args.test}}',
            '{{local.setting}}', '{{env.HOME}}', '{{cwd}}'
        ]
        
        for var in test_vars:
            result = self.variable_system.substitute(var)
            assert result != var, f"Variable {var} not substituted"
```

### **Performance Benchmarks**:
- **API Response Time**: <100ms for simple operations
- **File Operations**: <1s for files under 100MB
- **Process Startup**: <2s for typical applications
- **Memory Usage**: <500MB base overhead
- **Network Operations**: Proper timeout and retry handling

### **Security Validations**:
- **Path Traversal**: Prevent access outside allowed directories
- **Command Injection**: Sanitize all shell commands
- **Resource Limits**: Enforce CPU/memory/disk quotas
- **Network Security**: Validate URLs and limit external access

---

## 🏁 IMPLEMENTATION CHECKLIST

### **Core APIs** (MUST IMPLEMENT ALL):
- [ ] **shell.run**: Complete process execution with daemon support
- [ ] **fs.***: All file system operations with cloud path mapping
- [ ] **input**: User input handling in notebook environment
- [ ] **json.***: Complete JSON manipulation suite
- [ ] **log**: Structured logging system
- [ ] **net.***: Network operations with retry logic
- [ ] **notify**: Multi-channel notification system
- [ ] **script.***: Script execution and management
- [ ] **web.open**: Browser integration for cloud environments
- [ ] **hf.download**: Hugging Face model downloads

### **Variable System** (MUST SUPPORT ALL):
- [ ] **Platform variables**: {{platform}}, {{arch}}, {{gpu}}, {{cuda}}
- [ ] **Arguments**: {{args.*}} with type conversion
- [ ] **Local variables**: {{local.*}} with persistence
- [ ] **Environment**: {{env.*}} with secure access
- [ ] **Runtime variables**: {{cwd}}, {{app}}, {{timestamp}}

### **Cloud Adaptations** (MUST IMPLEMENT ALL):
- [ ] **Path mapping**: Windows/Mac to Linux path conversion
- [ ] **Process management**: Daemon cleanup and monitoring
- [ ] **Resource limits**: CPU/memory/disk quotas
- [ ] **Network tunneling**: Public access via ngrok/cloudflare
- [ ] **Storage optimization**: Caching and cleanup strategies

### **Error Handling** (MUST IMPLEMENT ALL):
- [ ] **Standardized errors**: Consistent error format across APIs
- [ ] **Recovery mechanisms**: Automatic retry and fallback
- [ ] **User feedback**: Clear error messages and guidance
- [ ] **Logging integration**: All errors logged with context

---

## 🎯 SUCCESS CRITERIA

**100% API Compatibility**: Every Pinokio script must work identically in cloud environment
**Performance Requirements**: Meet or exceed desktop Pinokio performance benchmarks
**Security Compliance**: Pass all security audits for cloud deployment
**User Experience**: Seamless transition from desktop to cloud Pinokio
**Documentation Coverage**: Complete API documentation with examples and edge cases

This guide provides the complete specification for implementing a fully compatible PinokioCloud system that maintains 100% API compatibility with desktop Pinokio while optimizing for cloud environments.
