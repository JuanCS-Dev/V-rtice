# 🧠 LLM Configuration Guide

Complete guide for configuring multi-LLM support in Vértice-MAXIMUS.

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Supported Providers](#-supported-providers)
3. [Claude (Anthropic)](#-claude-anthropic)
4. [OpenAI (GPT)](#-openai-gpt)
5. [Google Gemini](#-google-gemini)
6. [Custom / Local LLMs](#-custom--local-llms)
7. [Multi-LLM Strategy](#-multi-llm-strategy)
8. [Best Practices](#-best-practices)
9. [Troubleshooting](#-troubleshooting)

---

## 🌟 Overview

Vértice-MAXIMUS supports **multiple LLM providers** to give you flexibility in choosing the AI that powers your cybersecurity immune system.

### Why Multi-LLM Support?

- **🎯 Choose the best model for your use case** - Claude for reasoning, GPT for speed, Gemini for cost
- **🔄 Failover resilience** - If one provider goes down, fallback to another
- **💰 Cost optimization** - Use cheaper models for simple tasks, premium for complex analysis
- **🌍 Regional availability** - Some providers work better in certain regions
- **🔒 Data sovereignty** - Use local models for sensitive data

---

## 🔌 Supported Providers

| Provider | Best For | Cost | Speed | Reasoning |
|----------|----------|------|-------|-----------|
| **Claude (Anthropic)** | Complex threat analysis, strategic planning | $$$ | Medium | ⭐⭐⭐⭐⭐ |
| **OpenAI (GPT)** | General-purpose, fast responses | $$ | Fast | ⭐⭐⭐⭐ |
| **Google Gemini** | Cost-effective, multimodal | $ | Fast | ⭐⭐⭐ |
| **Custom / Local** | Privacy, offline use, no API costs | Free | Varies | ⭐⭐ |

**Recommended**: Claude for production use (best reasoning and threat analysis)

---

## 🤖 Claude (Anthropic)

### Why Claude?

- **Superior reasoning** for complex threat patterns
- **Long context windows** (200K tokens) for analyzing large logs
- **Strong at following instructions** for precise security responses
- **Ethical AI alignment** - safer for security use cases

### Getting an API Key

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up for an account
3. Navigate to **API Keys** section
4. Click **Create Key**
5. Copy your key (starts with `sk-ant-api03-...`)

### Configuration

```bash
# .env
PRIMARY_LLM=claude
CLAUDE_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-3-sonnet-20240229
CLAUDE_MAX_TOKENS=4096
```

### Available Models

| Model | Context | Speed | Cost | Best For |
|-------|---------|-------|------|----------|
| `claude-3-opus-20240229` | 200K | Slow | $$$$ | Critical threat analysis |
| `claude-3-sonnet-20240229` | 200K | Medium | $$ | **Recommended** - Balanced |
| `claude-3-haiku-20240307` | 200K | Fast | $ | Quick scans, routine checks |

### Interactive Setup

```bash
vertice init
# Select: Claude (Anthropic)
# Enter your API key
# Choose model (sonnet recommended)
```

---

## 🌐 OpenAI (GPT)

### Why OpenAI?

- **Fast response times** for real-time threat detection
- **Wide adoption** with extensive documentation
- **Function calling** for tool integration
- **Multimodal** (vision) for analyzing screenshots

### Getting an API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up and add payment method
3. Navigate to **API Keys**
4. Click **Create new secret key**
5. Copy your key (starts with `sk-...`)

### Configuration

```bash
# .env
PRIMARY_LLM=openai
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=4096
```

### Available Models

| Model | Context | Speed | Cost | Best For |
|-------|---------|-------|------|----------|
| `gpt-4-turbo` | 128K | Fast | $$$ | **Recommended** - Fast + smart |
| `gpt-4` | 8K | Medium | $$$$ | Legacy, high quality |
| `gpt-3.5-turbo` | 16K | Very Fast | $ | Quick scans, high volume |

### Interactive Setup

```bash
vertice init
# Select: OpenAI (GPT)
# Enter your API key
# Choose model (gpt-4-turbo recommended)
```

---

## 🔷 Google Gemini

### Why Gemini?

- **Cost-effective** for high-volume processing
- **Fast responses** with good performance
- **Multimodal** (vision, audio) capabilities
- **Google ecosystem** integration

### Getting an API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy your key (starts with `AIzaSy...`)

### Configuration

```bash
# .env
PRIMARY_LLM=gemini
GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_MODEL=gemini-pro
GEMINI_MAX_TOKENS=4096
```

### Available Models

| Model | Context | Speed | Cost | Best For |
|-------|---------|-------|------|----------|
| `gemini-pro` | 32K | Fast | $ | **Recommended** - Balanced |
| `gemini-ultra` | 32K | Medium | $$ | Complex analysis (when available) |

### Interactive Setup

```bash
vertice init
# Select: Google Gemini
# Enter your API key
# Choose model (gemini-pro recommended)
```

---

## 🏠 Custom / Local LLMs

### Why Local LLMs?

- **Zero API costs** - Run inference locally
- **Data privacy** - No data leaves your infrastructure
- **Offline capability** - Works without internet
- **Full control** - Fine-tune models for your use case

### Supported Platforms

#### Ollama (Recommended)

**Installation**:
```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

**Usage**:
```bash
# Start Ollama
ollama serve

# Pull a model
ollama pull llama2
ollama pull mistral
ollama pull codellama

# Verify it's running
curl http://localhost:11434/api/tags
```

**Configuration**:
```bash
# .env
PRIMARY_LLM=custom
CUSTOM_LLM_ENDPOINT=http://localhost:11434
CUSTOM_LLM_MODEL=llama2
CUSTOM_LLM_API_KEY=  # Leave empty for Ollama
```

#### LM Studio

1. Download [LM Studio](https://lmstudio.ai/)
2. Load a model (e.g., Mistral 7B, Llama 2)
3. Start the local server
4. Configure endpoint:

```bash
# .env
PRIMARY_LLM=custom
CUSTOM_LLM_ENDPOINT=http://localhost:1234/v1
CUSTOM_LLM_MODEL=mistral-7b-instruct
```

#### vLLM (Advanced)

For high-performance local inference:

```bash
# Install vLLM
pip install vllm

# Start server
python -m vllm.entrypoints.api_server \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --host 0.0.0.0 \
  --port 8000

# Configure
CUSTOM_LLM_ENDPOINT=http://localhost:8000
```

### Recommended Local Models

| Model | Size | Quality | Speed | Best For |
|-------|------|---------|-------|----------|
| **Mistral 7B Instruct** | 7B | ⭐⭐⭐⭐ | Fast | **Recommended** - Balanced |
| **Llama 2 13B** | 13B | ⭐⭐⭐⭐⭐ | Medium | High quality analysis |
| **CodeLlama 34B** | 34B | ⭐⭐⭐⭐⭐ | Slow | Code analysis (if hardware allows) |
| **Phi-2** | 2.7B | ⭐⭐⭐ | Very Fast | Quick scans, low-end hardware |

---

## 🎯 Multi-LLM Strategy

Use multiple LLMs together for optimal performance:

### Strategy 1: Primary + Fallback

```bash
# .env
PRIMARY_LLM=claude
FALLBACK_LLM=openai

CLAUDE_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

If Claude fails or is rate-limited, automatically switch to OpenAI.

### Strategy 2: Task-Specific Routing

Configure different LLMs for different tasks:

```bash
# .env
# Strategic planning (needs best reasoning)
STRATEGIC_LLM=claude
CLAUDE_MODEL=claude-3-opus-20240229

# Quick threat detection (needs speed)
DETECTION_LLM=openai
OPENAI_MODEL=gpt-3.5-turbo

# OSINT analysis (needs cost efficiency)
OSINT_LLM=gemini
GEMINI_MODEL=gemini-pro

# Code analysis (can use local)
CODE_ANALYSIS_LLM=custom
CUSTOM_LLM_MODEL=codellama
```

### Strategy 3: Hybrid (Cloud + Local)

```bash
# Use Claude for critical analysis
PRIMARY_LLM=claude

# Use local LLM for routine checks (cost savings)
ROUTINE_LLM=custom
CUSTOM_LLM_ENDPOINT=http://localhost:11434
CUSTOM_LLM_MODEL=mistral
```

---

## 💡 Best Practices

### 1. Cost Optimization

```bash
# Use cheaper models for simple tasks
QUICK_SCAN_MODEL=gpt-3.5-turbo  # or gemini-pro or local
DEEP_ANALYSIS_MODEL=claude-3-opus

# Set reasonable token limits
CLAUDE_MAX_TOKENS=4096  # Don't use 200K unless needed
OPENAI_MAX_TOKENS=2048
```

### 2. Rate Limiting

```bash
# Configure rate limits to avoid API throttling
LLM_RATE_LIMIT=60  # Requests per minute
LLM_RETRY_ATTEMPTS=3
LLM_RETRY_DELAY=5  # Seconds
```

### 3. Security

```bash
# Store API keys securely
# ❌ Never commit .env to git
# ✅ Use environment variables or secrets manager

# Option 1: Environment variables
export CLAUDE_API_KEY="sk-ant-..."

# Option 2: Vault (production)
VAULT_ENABLED=true
VAULT_ADDR=http://localhost:8200
# API keys fetched from Vault at runtime
```

### 4. Monitoring

```bash
# Enable LLM usage metrics
ENABLE_LLM_METRICS=true
LLM_METRICS_PORT=9091

# Track costs and performance
# View at: http://localhost:3000/dashboards (Grafana)
```

---

## 🔧 Troubleshooting

### Issue: "Invalid API key"

**Claude**:
```bash
# Test your key
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $CLAUDE_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-sonnet-20240229","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}'
```

**OpenAI**:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Gemini**:
```bash
curl "https://generativelanguage.googleapis.com/v1/models?key=$GEMINI_API_KEY"
```

### Issue: "Rate limit exceeded"

**Solution**: Reduce request rate or upgrade API tier

```bash
# Add rate limiting
LLM_RATE_LIMIT=30  # Lower requests/min
LLM_BATCH_SIZE=5   # Process in smaller batches

# Or upgrade your API plan
```

### Issue: "Local LLM not responding"

**Ollama**:
```bash
# Check if running
ollama list

# Restart service
ollama serve

# Check logs
tail -f ~/.ollama/logs/server.log
```

**LM Studio**:
- Verify server is started in LM Studio UI
- Check port 1234 isn't blocked
- Try different model

### Issue: "Slow response times"

**Solutions**:

1. Use faster model:
   ```bash
   # Instead of claude-3-opus or gpt-4
   CLAUDE_MODEL=claude-3-haiku  # Much faster
   OPENAI_MODEL=gpt-3.5-turbo
   ```

2. Reduce context window:
   ```bash
   CLAUDE_MAX_TOKENS=2048  # Instead of 4096
   ```

3. Use local LLM for routine tasks:
   ```bash
   ROUTINE_LLM=custom
   CUSTOM_LLM_MODEL=mistral  # Fast local inference
   ```

---

## 📚 Additional Resources

- [Claude Documentation](https://docs.anthropic.com/claude/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Gemini AI Documentation](https://ai.google.dev/docs)
- [Ollama Documentation](https://github.com/jmorganca/ollama)
- [LM Studio Guide](https://lmstudio.ai/docs)

---

## 🆘 Need Help?

- 💬 Join [Discord](https://discord.gg/vertice-maximus) - Community support
- 🐛 [GitHub Issues](https://github.com/yourusername/vertice-dev/issues) - Report bugs
- 📖 [Documentation](https://vertice-maximus.web.app/docs) - Full docs
- 📧 Email: hello@vertice.dev

---

**Built with ❤️ by Juan and the Vértice Community**

*"Not just software. A living organism."*
