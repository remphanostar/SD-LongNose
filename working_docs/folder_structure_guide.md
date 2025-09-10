# PinokioCloud Folder Structure Guide

## Repository Organization

### **Final GitHub Repository** (`/workspace/github_repo/`)
**Purpose**: Clean, production-ready repository for public release
**Contents**:
- Core application code
- Production documentation
- README.md
- requirements.txt
- License and legal files
- **NO temporary files, working docs, or development artifacts**

### **Working Documentation** (`/workspace/working_docs/`)
**Purpose**: Active development documentation and handover context
**Contents**:
- `ai_handover_context/` - Complete AI handover documentation
- `changelog.md` - Development progress tracking
- `folder_structure_guide.md` - This file
- All active development documentation

### **Temporary Documentation** (`/workspace/temp_docs/`)
**Purpose**: Analysis documents and temporary research
**Contents**:
- `conflict_analysis_and_clarifications.md` - Conflict analysis
- `notebook_vs_desktop_differences.md` - Implementation differences
- Any temporary analysis documents

### **Temporary Scripts** (`/workspace/temp_scripts/`)
**Purpose**: Development scripts and temporary tools
**Contents**:
- Development helper scripts
- Testing scripts
- Temporary automation tools
- **NO production code**

### **Guides** (`/workspace/Guides/`)
**Purpose**: Original development guides and specifications
**Contents**:
- All original development plans
- Implementation guides
- Reference documentation

### **Data** (`/workspace/`)
**Purpose**: Core data files
**Contents**:
- `cleaned_pinokio_apps.json` - Application database
- Virtual environment (`venv/`)
- Git repository (`.git/`)

## Documentation Update Schedule

### **Changelog Updates**
- **Frequency**: After every 5 functions created or edited
- **Location**: `/workspace/working_docs/changelog.md`
- **Content**: Timestamps, rationale, impact assessment

### **AI Handover Context Updates**
- **Frequency**: Throughout development (continuous)
- **Location**: `/workspace/working_docs/ai_handover_context/`
- **Content**: All decisions, progress, lessons learned

### **Conflict Resolution Updates**
- **Frequency**: Before each development phase
- **Location**: `/workspace/working_docs/ai_handover_context/conflict_resolution_history.md`
- **Content**: All conflicts and resolutions

## File Movement Rules

### **To GitHub Repository**
- Only production-ready code
- Final documentation
- Clean, reviewed files
- **NO temporary or working files**

### **To Working Docs**
- Active development documentation
- Progress tracking
- Handover context
- **Updated continuously**

### **To Temp Docs**
- Analysis documents
- Research files
- Temporary investigations
- **Archived after use**

### **To Temp Scripts**
- Development tools
- Testing scripts
- Helper utilities
- **Not for production**

## Clean Repository Strategy

### **Development Phase**
- All work happens in appropriate folders
- GitHub repo remains clean
- Documentation updated in working_docs
- Temporary files in temp folders

### **Release Phase**
- Copy only production files to github_repo
- Update final documentation
- Clean up temporary files
- Commit clean repository

### **Maintenance**
- Continue using folder structure
- Keep github_repo clean
- Maintain working documentation
- Archive completed temp files

This structure ensures a clean, professional GitHub repository while maintaining comprehensive development documentation and temporary files for development purposes.