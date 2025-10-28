# 🚀 Vértice-MAXIMUS Installation Guide

Complete guide for installing and configuring Vértice-MAXIMUS, the living cybersecurity organism.

---

## 📋 Table of Contents

1. [Prerequisites](#-prerequisites)
2. [Quick Installation (npm)](#-quick-installation-npm)
3. [Manual Installation](#-manual-installation)
4. [Docker Installation](#-docker-installation)
5. [Configuration](#-configuration)
6. [First Run](#-first-run)
7. [Troubleshooting](#-troubleshooting)

---

## 📦 Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows (WSL2 recommended)
- **Node.js**: 18.0.0 or higher
- **npm**: 9.0.0 or higher
- **Docker**: 20.10.0 or higher (for backend services)
- **Docker Compose**: 2.0.0 or higher
- **Python**: 3.11 or higher (for AI/ML services)
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Disk Space**: 10GB free space minimum

### Required Accounts & API Keys

You'll need at least **one** LLM API key from:

- **Claude (Anthropic)** - [Get API key](https://console.anthropic.com/)
- **OpenAI (GPT)** - [Get API key](https://platform.openai.com/api-keys)
- **Google Gemini** - [Get API key](https://makersuite.google.com/app/apikey)
- **Custom/Local LLM** - e.g., Ollama, LM Studio (no API key required)

---

## ⚡ Quick Installation (npm)

The fastest way to get started:

```bash
# Install globally via npm
npm install -g vertice-maximus

# Initialize and configure
vertice init

# Start the immune system
vertice start
```

That's it! The `vertice init` wizard will guide you through:
- ✅ LLM provider selection (Claude, OpenAI, Gemini, or custom)
- ✅ API key configuration
- ✅ Defense profile selection (paranoid, balanced, lightweight)
- ✅ Optional features (OSINT, offensive tools)

---

## 🛠️ Manual Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/vertice-dev.git
cd vertice-dev
```

### 2. Install Node.js Dependencies

```bash
# Install npm dependencies for CLI
npm install

# Link the CLI globally (optional)
npm link
```

### 3. Install Python Dependencies

```bash
# Install backend dependencies
cd backend
pip install -r requirements.txt

# Or use uv for faster installation (recommended)
pip install uv
uv pip sync requirements.txt
```

### 4. Configure PYTHONPATH

**⚠️ CRITICAL**: Required for running tests and some services.

```bash
# Add to your .bashrc or .zshrc to persist:
export PYTHONPATH=/path/to/vertice-dev:$PYTHONPATH

# Or set temporarily in current shell:
export PYTHONPATH=$(pwd):$PYTHONPATH
```

### 5. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration (add your API keys)
nano .env  # or your preferred editor
```

See [Configuration](#-configuration) section for detailed setup.

---

## 🐳 Docker Installation

Deploy Vértice-MAXIMUS using Docker Compose:

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/vertice-dev.git
cd vertice-dev
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Start Services

```bash
# Start core services
docker-compose up -d

# Or start all services (including offensive tools)
docker-compose --profile all up -d

# View logs
docker-compose logs -f
```

### 4. Verify Deployment

```bash
# Check service health
docker-compose ps

# Run validation script
./deployment/validation/validate_complete_system.sh
```

### 5. Access Dashboards

- **Frontend Cockpit**: http://localhost:5173
- **API Server**: http://localhost:8080
- **Grafana Monitoring**: http://localhost:3000 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090

---

## ⚙️ Configuration

### Interactive Configuration (Recommended)

```bash
vertice init
```

This wizard will:
1. Ask you to select your primary LLM provider
2. Request API key(s)
3. Let you choose a defense profile
4. Configure optional features (OSINT, offensive tools)

Configuration is saved to `~/.vertice/.env`

### Manual Configuration

Edit `/home/juan/vertice-dev/.env` (or `~/.vertice/.env` for global install):

```bash
# ═══════════════════════════════════════════════════════════════
# LLM CONFIGURATION
# ═══════════════════════════════════════════════════════════════

# Choose one: claude, openai, gemini, custom
PRIMARY_LLM=claude

# Claude API Key
CLAUDE_API_KEY=sk-ant-api03-xxxxx
CLAUDE_MODEL=claude-3-sonnet-20240229

# OpenAI API Key (optional)
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4

# Google Gemini API Key (optional)
GEMINI_API_KEY=AIzaSyxxxxx
GEMINI_MODEL=gemini-pro

# ═══════════════════════════════════════════════════════════════
# DEFENSE PROFILE
# ═══════════════════════════════════════════════════════════════

# Options: paranoid, balanced, lightweight, custom
DEFENSE_PROFILE=balanced

# Enable/disable individual immune layers
ENABLE_FIREWALL=true
ENABLE_REFLEX_DEFENSE=true
ENABLE_NEUTROPHILS=true
ENABLE_MACROPHAGES=true
ENABLE_ADAPTIVE_IMMUNITY=true
ENABLE_MEMORY=true
ENABLE_CONSCIOUSNESS=true

# ═══════════════════════════════════════════════════════════════
# OPTIONAL FEATURES
# ═══════════════════════════════════════════════════════════════

# OSINT intelligence gathering
ENABLE_OSINT=true

# Offensive security tools (requires authorization)
ENABLE_OFFENSIVE=false
```

See [`.env.example`](../.env.example) for complete configuration reference.

---

## 🎯 First Run

### 1. Verify Installation

```bash
# Check version
vertice --version

# Show help
vertice --help

# Check system status
vertice status
```

### 2. Start Services

```bash
# Start all immune system layers
vertice start

# Or run in background
vertice start --detach
```

You should see output like:

```
  ╔══════════════════════════════════════════════════════════════════╗
  ║   🧬  VÉRTICE-MAXIMUS  🧬                                        ║
  ║   A Living Cybersecurity Organism                                ║
  ╚══════════════════════════════════════════════════════════════════╝

🚀 Starting Vértice-MAXIMUS immune system...

✅ Layer 1: Firewall (Tegumentar) - Active
✅ Layer 2: Reflex Defense - Active
✅ Layer 3: Neutrophils - Active
...
✅ Layer 9: Consciousness (MAXIMUS AI) - Online

✅ All immune layers operational!

🧬 Vértice-MAXIMUS is now protecting your infrastructure.
```

### 3. Run First Security Scan

```bash
# Scan localhost
vertice scan

# Scan specific target
vertice scan --target example.com
```

### 4. Access Web Interfaces

Open your browser:

- **Landing Page**: https://vertice-maximus.web.app
- **Architecture Visualization**: https://vertice-maximus.web.app/architecture
- **Local Dashboard**: http://localhost:5173 (if frontend is running)
- **Grafana**: http://localhost:3000 (default: admin/admin)

---

## 🧪 Running Tests

Verify your installation with the test suite:

```bash
# Configure PYTHONPATH first (IMPORTANT!)
export PYTHONPATH=$(pwd):$PYTHONPATH

# Run core immune system tests (386 tests, 99.73% coverage)
cd backend
pytest modules/tegumentar/tests -v

# Run with coverage report
pytest modules/tegumentar/tests --cov=modules/tegumentar --cov-report=html
# Open: backend/htmlcov/index.html

# Run all backend tests
pytest -v

# Run library tests
pytest libs/vertice_db/tests -v
pytest libs/vertice_core/tests -v
pytest libs/vertice_api/tests -v
```

See [Testing Guide](testing/TESTING_GUIDE.md) for comprehensive documentation.

---

## 🔧 Troubleshooting

### Issue: "Command not found: vertice"

**Solution**:

```bash
# If installed globally
npm link

# If installed locally
npm install
export PATH="$PATH:$(pwd)/node_modules/.bin"
```

### Issue: "ImportError: No module named 'backend.modules.tegumentar'"

**Solution**: Configure PYTHONPATH

```bash
export PYTHONPATH=/path/to/vertice-dev:$PYTHONPATH
```

### Issue: "Docker containers won't start"

**Solutions**:

1. Check Docker is running:
   ```bash
   docker --version
   docker-compose --version
   ```

2. Check ports aren't in use:
   ```bash
   lsof -i :8080  # API port
   lsof -i :5173  # Frontend port
   ```

3. View logs:
   ```bash
   docker-compose logs -f
   ```

### Issue: "LLM API key invalid"

**Solution**:

1. Verify your API key is correct in `.env`
2. Check API key has proper permissions
3. Test API key directly:

   ```bash
   # Claude
   curl https://api.anthropic.com/v1/messages \
     -H "x-api-key: $CLAUDE_API_KEY" \
     -H "anthropic-version: 2023-06-01"

   # OpenAI
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

### Issue: "Services showing unhealthy status"

**Solution**:

```bash
# Check service status
vertice status

# Check Docker health
docker-compose ps

# Restart specific service
docker-compose restart <service-name>

# Full restart
vertice stop
vertice start
```

### Getting Help

If you're still stuck:

1. 📖 Check [Documentation](https://vertice-maximus.web.app/docs)
2. 💬 Join [Discord](https://discord.gg/vertice-maximus) for community support
3. 🐛 Report issues on [GitHub](https://github.com/yourusername/vertice-dev/issues)
4. 📧 Email support: hello@vertice.dev

---

## 📚 Next Steps

- 🔧 [LLM Configuration Guide](llm-configuration.md) - Configure multi-LLM support
- 🧪 [Testing Guide](testing/TESTING_GUIDE.md) - Run and write tests
- 🏗️ [Architecture Overview](architecture/) - Understand the biological system
- 🤝 [Contributing Guide](development/CONTRIBUTING.md) - Contribute to the project
- 🐛 [Debugging Guide](development/DEBUGGING_GUIDE.md) - Troubleshoot issues

---

**Built with ❤️ by Juan and the Vértice Community**

*"Not just software. A living organism."*
