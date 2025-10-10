# 📜 Scripts Collection

Organized automation scripts for setup, deployment, maintenance, and testing.

---

## 📂 Structure

```
scripts/
├── setup/          # Initial setup and configuration
├── deployment/     # Build and deployment scripts
├── maintenance/    # System maintenance and fixes
│   ├── cleanup/    # Cleanup automation
│   └── backup/     # Backup scripts
└── testing/        # Test and validation scripts
```

---

## 🚀 Setup Scripts

**[setup-cli.sh](./setup/setup-cli.sh)**  
Initialize CLI environment and dependencies.

**[setup-vertice-cli.sh](./setup/setup-vertice-cli.sh)**  
Setup Vértice-specific CLI tools.

**[create-main-files.sh](./setup/create-main-files.sh)**  
Generate main project structure files.

---

## 📦 Deployment Scripts

**[build-categoria-a.sh](./deployment/build-categoria-a.sh)**  
Build Category A services (core consciousness).

**[start-maximus-ai3.sh](./deployment/start-maximus-ai3.sh)**  
Launch MAXIMUS AI v3 system.

---

## 🔧 Maintenance Scripts

**[quick-fix-docker.sh](./maintenance/quick-fix-docker.sh)**  
Rapid Docker issue resolution.

**[mass-fix.sh](./maintenance/mass-fix.sh)**  
Batch fixing across multiple services.

**[fix-all-numpy.sh](./maintenance/fix-all-numpy.sh)**  
Resolve NumPy-related issues across project.

### Cleanup
**[gemini-cleanup-executor.sh](./maintenance/cleanup/gemini-cleanup-executor.sh)**  
Automated cleanup using Gemini AI.

---

## 🧪 Testing Scripts

**[diagnose-all.sh](./testing/diagnose-all.sh)**  
Comprehensive system diagnostics.

**[validate-maximus.sh](./testing/validate-maximus.sh)**  
MAXIMUS system validation suite.

**[verify-ethical-ai.sh](./testing/verify-ethical-ai.sh)**  
Ethical AI framework verification.

---

## 📝 Script Standards

All scripts follow these principles:

### Header Template
```bash
#!/bin/bash
# Purpose: Clear one-line description
# Usage: ./script.sh [args]
# Author: MAXIMUS Team
# Date: YYYY-MM-DD
# Requires: List dependencies

set -e  # Exit on error
set -u  # Exit on undefined variable
```

### Quality Requirements
- ✅ Error handling (`set -e`, checks)
- ✅ Usage documentation
- ✅ Dependency validation
- ✅ Logging/output
- ✅ Exit codes (0=success)

### No Placeholders
- ❌ No `TODO` comments
- ❌ No incomplete logic
- ✅ Every script is production-ready
- ✅ Every script is tested

---

## 🎯 Usage Guidelines

### Running Scripts

```bash
# Always check help/usage first
./scripts/setup/setup-cli.sh --help

# Make executable if needed
chmod +x scripts/setup/setup-cli.sh

# Run with proper permissions
./scripts/deployment/build-categoria-a.sh
```

### Safety Practices
1. **Read the script** before running
2. **Understand what it does**
3. **Check prerequisites**
4. **Have backups** (especially maintenance scripts)
5. **Test in dev first** (never prod first)

---

## 🏆 Script Principles

### "Automate the Boring Stuff"
If it's done more than twice, script it.

### "Make it Obvious"
Script names and purposes should be crystal clear.

### "Fail Loudly"
Errors should be impossible to miss.

### "Document by Doing"
Scripts themselves are documentation of processes.

---

**Status**: 🟢 Active | **Total**: 13 scripts  
**Philosophy**: Automation with safety, clarity with power 🔧
