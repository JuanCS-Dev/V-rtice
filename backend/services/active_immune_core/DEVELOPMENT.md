# 🛠️ Development Guide - Active Immune Core

Complete guide for local development with Docker Compose.

**Authors**: Juan & Claude
**Version**: 1.0.0
**Last Updated**: 2025-10-06

---

## 📋 Prerequisites

- Docker 20.10+ & Docker Compose 2.0+
- Git
- 8GB+ RAM recommended
- Ports available: 8200, 3000, 5432, 6379, 9090, 9092, 9094

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd backend/services/active_immune_core

# Copy environment file (first time only)
cp .env.example .env

# Review and customize .env if needed
vim .env
```

### 2. Start Development Environment

```bash
# Start all services (Kafka, Redis, PostgreSQL, Prometheus, Grafana, API)
./scripts/dev-up.sh
```

**First run**: Downloads images (~2-3 min)
**Subsequent runs**: Starts in ~30 seconds

### 3. Verify Services

```bash
# Check all services are healthy
docker-compose -f docker-compose.dev.yml ps

# Test API
curl http://localhost:8200/health
```

### 4. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:8200 | - |
| **API Docs** | http://localhost:8200/docs | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Kafka** | localhost:9094 | - |
| **Redis** | localhost:6379 | - |
| **PostgreSQL** | localhost:5432 | immunis / immunis_password |

---

## 🔧 Development Workflow

### Hot Reload (Automatic)

Code changes are automatically detected and reloaded:

```bash
# Edit any Python file
vim api/routes/agents.py

# Save → uvicorn auto-reloads → changes live in ~2s
```

**Mounted Directories** (hot reload enabled):
- `./api` → `/app/api`
- `./agents` → `/app/agents`
- `./communication` → `/app/communication`
- `./coordination` → `/app/coordination`
- `./homeostasis` → `/app/homeostasis`
- `./memory` → `/app/memory`
- `./monitoring` → `/app/monitoring`
- `./tests` → `/app/tests`

### View Logs

```bash
# Follow API logs
./scripts/dev-logs.sh

# Follow specific service logs
./scripts/dev-logs.sh kafka
./scripts/dev-logs.sh redis
./scripts/dev-logs.sh postgres

# Follow all services
./scripts/dev-logs.sh all
```

### Run Tests

```bash
# Run all tests
./scripts/dev-test.sh

# Run specific test file
./scripts/dev-test.sh api/tests/test_agents.py

# Run with coverage
./scripts/dev-test.sh --cov=api --cov-report=html

# Run specific test
./scripts/dev-test.sh api/tests/test_agents.py::test_create_agent_success -v
```

### Shell Access

```bash
# Open shell in API container
./scripts/dev-shell.sh

# Inside container:
$ python -m pytest api/tests/
$ python -m api.main
$ pip list
```

### Stop Environment

```bash
# Stop all services (preserve data)
./scripts/dev-down.sh

# Stop and remove volumes (delete all data)
docker-compose -f docker-compose.dev.yml down -v
```

---

## 📊 Monitoring & Debugging

### Prometheus Metrics

```bash
# Open Prometheus UI
open http://localhost:9090

# Example queries:
immunis_agents_active{status="active"}
rate(immunis_threats_detected_total[5m])
immunis_temperature_celsius
```

### Grafana Dashboards

```bash
# Open Grafana
open http://localhost:3000

# Login: admin / admin
# Dashboards are in ./monitoring/grafana/dashboards/
```

### Kafka Topics

```bash
# List topics
docker exec immunis_kafka kafka-topics --list --bootstrap-server localhost:9092

# Consume cytokine messages
docker exec immunis_kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic immunis.cytokines.TNF \
  --from-beginning
```

### Redis

```bash
# Connect to Redis CLI
docker exec -it immunis_redis redis-cli

# Example commands:
> KEYS hormonio:*
> GET hormonio:cortisol
> MONITOR  # Watch all commands in real-time
```

### PostgreSQL

```bash
# Connect to PostgreSQL
docker exec -it immunis_postgres psql -U immunis -d immunis_memory

# Example queries:
immunis_memory=# \dt  -- List tables
immunis_memory=# SELECT * FROM agents LIMIT 10;
```

---

## 🧪 Testing

### Unit Tests

```bash
# Run all unit tests
./scripts/dev-test.sh api/tests/test_*.py

# Run with verbose output
./scripts/dev-test.sh api/tests/ -v

# Run with short traceback
./scripts/dev-test.sh api/tests/ -v --tb=short
```

### E2E Tests

```bash
# Run E2E integration tests
./scripts/dev-test.sh api/tests/e2e/

# Run specific E2E test
./scripts/dev-test.sh api/tests/e2e/test_agent_flow.py -v
```

### WebSocket Tests

```bash
# Run WebSocket tests
./scripts/dev-test.sh api/tests/test_websocket.py -v
```

### Coverage Report

```bash
# Generate HTML coverage report
./scripts/dev-test.sh --cov=api --cov-report=html

# Open report
open htmlcov/index.html
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8200
lsof -i :8200

# Kill process
kill -9 <PID>

# Or change port in docker-compose.dev.yml:
# ports:
#   - "8201:8200"
```

### Container Won't Start

```bash
# Check container logs
docker logs active_immune_core_dev

# Rebuild from scratch
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml build --no-cache
./scripts/dev-up.sh
```

### Kafka Connection Issues

```bash
# Restart Kafka
docker-compose -f docker-compose.dev.yml restart kafka

# Check Kafka logs
./scripts/dev-logs.sh kafka

# Wait for Kafka to be ready (30-60s)
docker-compose -f docker-compose.dev.yml exec kafka \
  kafka-broker-api-versions --bootstrap-server localhost:9092
```

### Hot Reload Not Working

```bash
# Check volume mounts
docker inspect active_immune_core_dev | grep -A 10 Mounts

# Restart container
docker-compose -f docker-compose.dev.yml restart active_immune_core

# If still not working, rebuild
docker-compose -f docker-compose.dev.yml up -d --build
```

### Out of Memory

```bash
# Check Docker resources
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings → Resources → Memory → 8GB+

# Or reduce service resource usage in docker-compose.dev.yml
```

---

## 📦 Dependencies

### Add New Dependency

```bash
# Add to requirements.txt
echo "fastapi-limiter==0.1.5" >> requirements.txt

# Compile lock file
pip-compile requirements.txt --output-file requirements.txt.lock

# Audit for vulnerabilities
./scripts/dependency-audit.sh

# Rebuild container
docker-compose -f docker-compose.dev.yml up -d --build
```

### Update Dependency

```bash
# Update version in requirements.txt
vim requirements.txt

# Recompile
pip-compile requirements.txt --output-file requirements.txt.lock --upgrade

# Audit
./scripts/dependency-audit.sh

# Rebuild
docker-compose -f docker-compose.dev.yml up -d --build
```

---

## 🔒 Security

### CVE Scanning

```bash
# Full security audit
./scripts/dependency-audit.sh

# Check CVE whitelist
./scripts/check-cve-whitelist.sh

# Validate Dependabot PR
./scripts/validate-dependabot-pr.sh
```

### Secrets Management

**NEVER commit**:
- `.env` files
- API keys
- Passwords
- Tokens

**Always use**:
- `.env.example` for templates
- Environment variables
- Secrets managers in production

---

## 📁 Project Structure

```
active_immune_core/
├── api/                    # REST API + WebSocket
│   ├── core_integration/   # Core system integration
│   ├── models/             # Pydantic models
│   ├── routes/             # API endpoints
│   ├── websocket/          # WebSocket real-time events
│   └── tests/              # API tests (116 tests)
├── agents/                 # Immune agents (neutrophil, macrophage, nk_cell)
├── communication/          # Cytokines (Kafka) + Hormones (Redis)
├── coordination/           # Tasks, elections, consensus
├── homeostasis/            # Temperature control, homeostatic regulation
├── memory/                 # Long-term memory (PostgreSQL)
├── monitoring/             # Prometheus metrics + Grafana dashboards
├── scripts/                # Development & ops scripts
├── docker-compose.dev.yml  # Development environment
├── Dockerfile              # Production image
├── Dockerfile.dev          # Development image (hot reload)
└── requirements.txt        # Python dependencies
```

---

## 🚀 Performance Tips

### Faster Startup

```bash
# Keep containers running (don't down between sessions)
# Just restart when needed:
docker-compose -f docker-compose.dev.yml restart active_immune_core
```

### Faster Tests

```bash
# Run specific test files instead of full suite
./scripts/dev-test.sh api/tests/test_agents.py

# Use pytest markers (if implemented)
./scripts/dev-test.sh -m "not slow"

# Run in parallel (requires pytest-xdist)
./scripts/dev-test.sh -n auto
```

### Reduce Logs

```bash
# Change log level in .env
ACTIVE_IMMUNE_LOG_LEVEL=INFO  # Instead of DEBUG

# Restart to apply
docker-compose -f docker-compose.dev.yml restart active_immune_core
```

---

## 📚 Additional Resources

- **README.md** - Project overview
- **FASE_7_COMPLETE.md** - API test alignment
- **FASE_8_COMPLETE.md** - WebSocket implementation
- **DEPENDENCY_POLICY.md** - Dependency management
- **DEPENDENCY_EMERGENCY_RUNBOOK.md** - CVE response

---

## 🤝 Contributing

1. Create feature branch
2. Make changes with hot reload
3. Run tests: `./scripts/dev-test.sh`
4. Check coverage: `./scripts/dev-test.sh --cov=api`
5. Commit with descriptive message
6. Create PR

---

## 💡 Pro Tips

- **Alias scripts** in your shell:
  ```bash
  alias dev-up='./scripts/dev-up.sh'
  alias dev-down='./scripts/dev-down.sh'
  alias dev-logs='./scripts/dev-logs.sh'
  alias dev-test='./scripts/dev-test.sh'
  ```

- **Use tmux** for multiple panes:
  ```bash
  # Pane 1: dev-logs
  # Pane 2: dev-shell
  # Pane 3: code editor
  ```

- **Watch tests** during development:
  ```bash
  # Install pytest-watch
  pip install pytest-watch

  # Auto-run tests on file changes
  ./scripts/dev-shell.sh
  $ ptw api/tests/test_agents.py
  ```

---

**GOLDEN RULE COMPLIANCE**: ✅
- NO MOCK: Real Kafka, Redis, PostgreSQL
- NO PLACEHOLDER: All services production-ready
- NO TODO: Zero TODOs
- PRODUCTION-READY: Hot reload for dev, production Dockerfile separate
- QUALITY-FIRST: Scripts, docs, monitoring included

---

**Prepared by**: Claude & Juan
**Date**: 2025-10-06
