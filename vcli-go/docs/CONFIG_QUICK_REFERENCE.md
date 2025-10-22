# vCLI Configuration Quick Reference

## 🚀 Quick Start

```bash
# 1. Initialize configuration
vcli configure init

# 2. View current config
vcli configure show

# 3. Set your backend endpoints
vcli configure set endpoints.maximus your-server:50051
vcli configure set endpoints.consciousness http://your-server:8022
```

---

## 📋 Common Commands

### Initialize Config
```bash
vcli configure init
```
Creates `~/.vcli/config.yaml` with defaults.

### View Configuration
```bash
vcli configure show
```
Displays current configuration in YAML format.

### Set Endpoints
```bash
# MAXIMUS Orchestrator
vcli configure set endpoints.maximus localhost:50051

# Consciousness API
vcli configure set endpoints.consciousness http://localhost:8022

# HITL Console
vcli configure set endpoints.hitl http://localhost:8000/api

# Active Immune Core
vcli configure set endpoints.immune localhost:50052

# AI Services
vcli configure set endpoints.eureka http://localhost:8024
vcli configure set endpoints.oraculo http://localhost:8026
vcli configure set endpoints.predict http://localhost:8028
```

### Set Global Options
```bash
vcli configure set global.debug true
vcli configure set global.output_format json
vcli configure set global.offline false
```

---

## 👤 Profile Management

### List Profiles
```bash
vcli configure profiles
```

### Create Profile
```bash
vcli configure create-profile production
# Then follow prompts for description and endpoints
```

### Switch Profile
```bash
vcli configure use-profile production
```

### Delete Profile
```bash
vcli configure delete-profile staging
```

---

## 🔧 Environment Variables

### Override Any Endpoint
```bash
# MAXIMUS
export VCLI_MAXIMUS_ENDPOINT=prod-server:50051

# Consciousness
export VCLI_CONSCIOUSNESS_ENDPOINT=https://prod.example.com:8022

# HITL
export VCLI_HITL_ENDPOINT=https://hitl.example.com/api

# Immune
export VCLI_IMMUNE_ENDPOINT=prod-immune:50052

# AI Services
export VCLI_EUREKA_ENDPOINT=http://eureka.example.com:8024
export VCLI_ORACULO_ENDPOINT=http://oraculo.example.com:8026
export VCLI_PREDICT_ENDPOINT=http://predict.example.com:8028
```

### Global Settings
```bash
export VCLI_DEBUG=true
export VCLI_OFFLINE=true
export VCLI_OUTPUT_FORMAT=json
```

### Redis (HITL Auth)
```bash
export VCLI_REDIS_ADDR=localhost:6379
export VCLI_REDIS_PASSWORD=secret
export VCLI_REDIS_MOCK=true  # Dev/test only
```

---

## 🎯 Configuration Precedence

Priority (highest to lowest):
1. **CLI Flags**: `--server`, `--endpoint`
2. **Environment Variables**: `VCLI_*_ENDPOINT`
3. **Config File**: `~/.vcli/config.yaml`
4. **Built-in Defaults**: `localhost:*`

### Example
```bash
# Uses config file (lowest priority)
vcli maximus list

# Overrides with env var (medium priority)
VCLI_MAXIMUS_ENDPOINT=dev:50051 vcli maximus list

# Overrides with flag (highest priority)
vcli maximus --server=prod:50051 list
```

---

## 📁 File Location

Default config file: `~/.vcli/config.yaml`

Use custom location:
```bash
vcli --config /path/to/config.yaml <command>
```

---

## 🐛 Debug Mode

Enable debug logging to see connection attempts:
```bash
VCLI_DEBUG=true vcli maximus list
```

Or set globally:
```bash
vcli configure set global.debug true
```

---

## 📊 Config File Structure

```yaml
current_profile: default

profiles:
  default:
    endpoints:
      maximus: localhost:50051
      consciousness: http://localhost:8022
      hitl: http://localhost:8000/api
      # ... other services

global:
  debug: false
  offline: false
  output_format: table

cache:
  enabled: true
  path: ~/.vcli/cache

plugins:
  enabled: true
  path: ~/.vcli/plugins
```

---

## 💡 Pro Tips

### Multi-Environment Setup
```bash
# Create profiles for each environment
vcli configure create-profile dev
vcli configure create-profile staging
vcli configure create-profile production

# Switch between them
vcli configure use-profile production
```

### Quick Debug Session
```bash
# One-off debug without changing config
VCLI_DEBUG=true vcli maximus list
```

### Development Mode
```bash
# Use all defaults with mock Redis
VCLI_REDIS_MOCK=true vcli hitl auth login
```

### Override Single Endpoint
```bash
# Test against different server without changing config
VCLI_MAXIMUS_ENDPOINT=test-server:50051 vcli maximus list
```

---

## 🆘 Troubleshooting

### Config Not Loading?
```bash
# Check file exists
ls -la ~/.vcli/config.yaml

# Reinitialize
vcli configure init
```

### Wrong Endpoint?
```bash
# Check current config
vcli configure show | grep maximus

# Enable debug to see what's being used
VCLI_DEBUG=true vcli maximus list
```

### Can't Connect?
```bash
# Verify endpoint in config
vcli configure show | grep endpoints -A 11

# Test with explicit override
VCLI_DEBUG=true VCLI_MAXIMUS_ENDPOINT=localhost:50051 vcli maximus list
```

---

## 📚 Related Documentation

- [FASE3_CONFIG_COMPLETE.md](./FASE3_CONFIG_COMPLETE.md) - Full implementation details
- [IMPLEMENTATION_ROADMAP_20250122.md](./IMPLEMENTATION_ROADMAP_20250122.md) - Overall plan
- [README.md](../README.md) - Main documentation

---

**Quick Reference Version**: 1.0
**Last Updated**: 2025-01-22
