---
description: Project rules
globs:
alwaysApply: true
---
# PinokioCloud Development Rules

## Project Overview
PinokioCloud is a cloud-native Pinokio alternative for multi-cloud GPU environments (Google Colab, Vast.ai, Lightning.ai, Paperspace, RunPod) with Streamlit UI. The goal is to implement complete Pinokio functionality as specified in Pinokio.md with zero deviations, creating a production-ready system that rivals desktop Pinokio in capabilities while leveraging cloud advantages.

## Core Development Principles

### 1. Pinokio.md Compliance
- Follow Pinokio.md specifications exactly unless technically impossible
- Implement ALL Pinokio API methods: shell.run, fs.*, script.*, input, json.*, etc.
- Support complete variable substitution system: {{platform}}, {{gpu}}, {{args.*}}, {{local.*}}, {{env.*}}
- Honor daemon: true flag for background processes
- Implement proper error handling as specified

### 2. Repository Structure Rules
- GitHub repository holds all scripts and files
- Notebook file clones repository in Cell 1 into dynamic folder based on cloud GPU service
- Scripts are used by both notebook and Streamlit UI
- Maintain absolute paths for cloud compatibility (/content/, /workspace/, /teamspace/)
- Use new naming nomenclature that explains script's job and phase in 'search > venv > requirements > install > storage > run > launch > UI' workflow

### 3. Implementation Standards

#### Engine Development
- Always implement missing methods before calling them
- Use async/await for long-running operations
- Implement proper process tracking with PIDs
- Support both .js and .json Pinokio scripts
- Handle virtual environments exactly like desktop Pinokio
- NO PLACEHOLDERS OR INCOMPLETE IMPLEMENTATIONS - every function must be production-ready

#### Variable System
- Support full {{variable}} syntax with nested paths
- Implement all Pinokio memory variables (platform, gpu, cwd, port, args, local, env, cloud)
- Handle variable substitution in all string parameters
- Support conditional logic with 'when' clauses
- Add cloud-specific variables ({{cloud.base_path}}, {{cloud.platform}})

#### Process Management  
- Track all spawned processes
- Implement proper daemon management
- Support 'on' handlers for output monitoring
- Handle graceful shutdown and cleanup
- Show raw Python and pip output with no obfuscation or simplified catchalls

#### Error Handling
- Provide user-friendly error messages
- Log technical details for debugging
- Implement retry mechanisms where appropriate
- Never fail silently
- Show complete unobfuscated error output for debugging

### 4. Code Quality Standards
- Use type hints for all function parameters
- Add comprehensive docstrings
- Implement comprehensive structured logging (terminal, Streamlit, log files)
- Handle exceptions gracefully with specific error types
- Test edge cases (missing files, network issues, permission errors)
- NO PLACEHOLDERS - every line of code must be production-ready

### 5. Multi-Cloud Compatibility Rules
- Detect cloud platform automatically (Google Colab, Vast.ai, Lightning.ai, Paperspace, RunPod)
- Use appropriate paths for each cloud environment
- Handle missing system utilities gracefully
- Support all cloud platforms with initial testing on Colab
- Respect cloud resource limitations

### 6. Terminal Integration Rules
- Show literally everything happening during installation and app launches
- Display pure Python and pip output with no broad catches or obfuscation
- Provide complete debugging visibility for error fixing
- Ensure peace of mind that things are working, not running on placeholders
- Implement comprehensive logging in terminal, Streamlit, and stored log files

### 7. Testing Requirements
- Test with real apps from cleaned_pinokio_apps.json (284 applications)
- Validate both .js and .json script execution
- Test virtual environment isolation
- Verify daemon processes work correctly
- Test error conditions and recovery
- Internal testing after each phase completion
- Full testing session after each stage

## 12-Phase Development Structure

### Phase 1: Multi-Cloud Detection & Repository Cloning (Days 1-5)
- Intelligent cloud detection system for all supported platforms
- Environment-specific path mapping and configuration
- Resource assessment frameworks (GPU, storage, network, security)
- Platform-specific optimization profiles
- Foundation architecture setup with proper abstractions
- GitHub repository cloning into correct cloud folder

### Phase 2: Environment Management Engine (Days 6-8)
- Virtual environment creation and management
- File system operations (copy, move, delete, read, write)
- Shell command execution with output capture
- Variable substitution system for all {{variable}} syntax
- JSON file operations and configuration management

### Phase 3: Pinokio App Analysis Engine (Days 9-11)
- App characteristic detection (installer type, web UI, dependencies)
- Installer method detection (install.js, install.json, requirements.txt, environment.yml)
- Web UI detection (Gradio, Streamlit, Flask, FastAPI)
- Dependency system analysis (pip, conda, npm, system packages)
- Tunnel requirements determination (ngrok, gradio share, no tunneling)
- Complete app profiling for installation and running

### Phase 4: Dependency Detection & Installation Engine (Days 12-14)
- Comprehensive dependency file detection
- Multi-package manager support (pip, conda, npm, system)
- Dependency conflict resolution
- Installation verification and testing
- Cross-platform dependency compatibility

### Phase 5: Application Installation Engine (Days 15-17)
- Pinokio app installation using detected methods
- Script parsing and execution (.js and .json)
- User input handling and form management
- Installation state tracking and management
- Complete installation coordination

### Phase 6: Application Running Engine (Days 18-20)
- Process management and tracking
- Daemon process handling
- Health monitoring and automatic restart
- Virtual drive and storage management
- Application lifecycle management

### Phase 7: Web UI Discovery and Multi-Tunnel Management (Days 21-23)
- Comprehensive server detection for 15+ web frameworks
- Multi-provider tunnel orchestration (ngrok primary, Cloudflare backup)
- Gradio integration with automatic share parameter injection
- Advanced URL sharing with QR codes, analytics, and temporary links
- Health monitoring and automatic reconnection systems

### Phase 8: Cloud Platform Specialization (Days 24-26)
- Google Colab optimizations (Drive mounting, session management, GPU handling)
- Vast.ai professional features (certificates, Docker adaptation, billing optimization)
- Lightning.ai team integration (workspaces, collaboration, resource sharing)
- Cross-platform compatibility and performance optimization

### Phase 9: Advanced Features and Optimization (Days 27-29)
- Multi-layer caching system with intelligent prefetching
- Performance monitoring and resource optimization
- Error recovery and self-healing capabilities
- Advanced logging and analytics systems

### Phase 10: Comprehensive Testing and Validation (Days 30-32)
- Real-world application testing across all categories (video, text, image, audio)
- Multi-cloud testing matrix with different instance types
- Performance benchmarking and optimization
- Error condition testing and recovery validation

### Phase 11: Streamlit UI Development (Days 33-35)
- Dark cyberpunk theme implementation
- WebSocket integration for real-time updates
- Advanced terminal streaming with ANSI support
- Responsive design and mobile optimization
- User experience enhancements and accessibility

### Phase 12: Final Polish and Production Readiness (Days 36-38)
- Comprehensive error handling and user-friendly messages
- Final performance optimizations and cleanup
- User documentation and help file generation
- Backup and recovery systems
- Production readiness validation

## Testing Strategy

### Internal Testing After Each Phase
- Test recently completed stage and how it works with all previous steps
- Search > Test searching capabilities and accuracy
- venv > Test multiple apps installed in multiple environments
- requirements > Test that requirements installed in venvs are contained and not interfering
- install > Install 4 Pinokio apps (1 video, 1 text, 1 image, 1 audio) with varied installation methods
- storage > Test storage and extra features, configuration for individual apps
- run > Test running and initiation of each app, ensure it starts and launches correctly
- launch > Test final web UI link generation (Gradio or ngrok/Cloudflare)

### Final Testing
- Full project testing with complete workflow
- User testing of Streamlit UI
- Deep testing of apps and actual project usage
- Iteration and tightening of loose bolts

## Scoring System
- **+20 points**: Successful phase completion
- **+10 points**: Pass phase while keeping rules in mind and updating running documents
- **-10 points**: Fail to follow rules or create placeholders
- **-100 points**: Hit a placeholder or fake function during testing
- **0 points**: Termination or restart decision required

## Documentation Update Intervals
- **Changelog**: Update after every 5 functions created or edited
- **AI Handover Context**: Update throughout development (continuous)
- **Conflict Resolution**: Update before each development phase begins
- **Phase Specifications**: Read complete_phase_specifications.md after every 5 functions created or edited to stay on track
- **Production Quality Reminder**: Read production_quality_reminder.md after every 5 functions created or edited to maintain quality standards

## Forbidden Actions
- Do NOT create placeholder functions or incomplete implementations
- Do NOT modify the GitHub clone workflow
- Do NOT break backward compatibility with existing apps
- Do NOT deviate from Pinokio.md without justification
- Do NOT obfuscate or simplify Python/pip output
- Do NOT create fake functions or corner-cutting functions

## Development Approach
- Focus on core engine functionality first
- UI development comes in final phase
- Internal testing and emulation of Streamlit UI during development
- Use Jupyter notebook for testing when needed
- Create basic Streamlit app for testing aspects if required
- Comprehensive logging and debugging throughout