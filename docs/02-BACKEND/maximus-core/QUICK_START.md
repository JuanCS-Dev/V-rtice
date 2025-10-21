# MAXIMUS AI 3.0 - Quick Start Guide 🚀

**Get up and running in 5 minutes!**

---

## 🎯 Prerequisites

- Docker 20.10+ & Docker Compose 2.0+
- 8GB RAM minimum
- 10GB disk space
- Internet connection (for pulling images)

---

## ⚡ 1-Minute Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd backend/services/maximus_core_service

# 2. Create environment file
cp .env.example .env
# Edit .env if you have API keys (optional for demo)

# 3. Start the stack
./scripts/start_stack.sh

# Wait ~60 seconds for all services to start
```

---

## 🎬 2-Minute Demo

```bash
# Run complete demo with 50 events
python demo/demo_maximus_complete.py --max-events 50
```

**Expected Output:**
- ✅ Detects malware executions
- ✅ Identifies C2 communications
- ✅ Catches lateral movement
- ✅ Spots data exfiltration
- ✅ Neuromodulation adapts learning rate
- ✅ Free Energy shows surprise levels

---

## 📊 3-Minute Monitoring

### Access Dashboards

**Grafana:** http://localhost:3000
- Username: `admin`
- Password: `maximus_admin_2025`

**Navigate to:** MAXIMUS AI 3.0 - Overview dashboard

**You'll see:**
- Event throughput (real-time)
- Pipeline latency (p50, p95, p99)
- Detection accuracy gauge
- Free Energy by layer
- Neuromodulation state (dopamine, ACh, NE, 5-HT)
- Skill execution metrics

### Check Prometheus

**Prometheus:** http://localhost:9090

**Try these queries:**
```promql
# Event rate
rate(maximus_events_processed_total[5m])

# Free energy by layer
avg(rate(maximus_free_energy_sum[5m])) by (layer)

# Dopamine level
maximus_dopamine_level
```

---

## 🧪 4-Minute Testing

```bash
# Run all tests (44 tests)
pytest test_*.py -v                    # 30 tests
python demo/test_demo_execution.py     # 5 tests
python tests/test_docker_stack.py      # 3 tests
python tests/test_metrics_export.py    # 6 tests

# Expected: 44/44 tests passing ✅
```

---

## 🔍 5-Minute Exploration

### Check Services

```bash
# View running services
docker-compose -f docker-compose.maximus.yml ps

# Expected services:
# - maximus-core (port 8150)
# - maximus-hsas (port 8023)
# - maximus-postgres (port 5432)
# - maximus-redis (port 6379)
# - maximus-prometheus (port 9090)
# - maximus-grafana (port 3000)
```

### View Logs

```bash
# MAXIMUS Core logs
docker-compose -f docker-compose.maximus.yml logs -f maximus_core

# All services logs
docker-compose -f docker-compose.maximus.yml logs -f
```

### Check Health

```bash
# MAXIMUS Core
curl http://localhost:8150/health

# HSAS Service
curl http://localhost:8023/health

# Metrics endpoint
curl http://localhost:8150/metrics
```

---

## 📚 Next Steps

### Learn More

1. **Architecture:** Read [MAXIMUS_3.0_COMPLETE.md](MAXIMUS_3.0_COMPLETE.md)
2. **Deployment:** See [DEPLOYMENT.md](DEPLOYMENT.md)
3. **Monitoring:** Check [monitoring/README_MONITORING.md](monitoring/README_MONITORING.md)
4. **Metrics:** Review [monitoring/METRICS.md](monitoring/METRICS.md)

### Customize

1. **Add API Keys:** Edit `.env` file
   ```bash
   GEMINI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   ```

2. **Enable Features:**
   ```bash
   ENABLE_PREDICTIVE_CODING=true
   ENABLE_SKILL_LEARNING=true
   ```

3. **Adjust Resources:** Edit `docker-compose.maximus.yml`
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 4G
   ```

### Run Custom Scenarios

```bash
# Full dataset (100 events)
python demo/demo_maximus_complete.py

# Show all events (not just threats)
python demo/demo_maximus_complete.py --show-all

# Custom dataset
python demo/demo_maximus_complete.py --dataset path/to/events.json
```

---

## 🛑 Stop Services

```bash
# Stop stack (preserve data)
docker-compose -f docker-compose.maximus.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.maximus.yml down -v
```

---

## 🆘 Troubleshooting

### Services Won't Start

**Issue:** Container exits immediately

**Solutions:**
```bash
# Check logs
docker-compose -f docker-compose.maximus.yml logs <service>

# Verify .env file
cat .env

# Check port conflicts
netstat -tulpn | grep -E "8150|8023|9090|3000"
```

### Dashboard Shows "No Data"

**Issue:** Grafana dashboard empty

**Solutions:**
```bash
# 1. Check Prometheus targets
open http://localhost:9090/targets

# 2. Verify metrics endpoint
curl http://localhost:8150/metrics

# 3. Restart Grafana
docker-compose -f docker-compose.maximus.yml restart grafana
```

### Demo Fails

**Issue:** Demo script errors

**Solutions:**
```bash
# 1. Check dataset exists
ls demo/synthetic_events.json

# 2. Generate dataset if missing
python demo/synthetic_dataset.py

# 3. Run in simulation mode (no dependencies)
# Demo automatically falls back to simulation
```

---

## 🎯 Success Checklist

After setup, verify:

- [ ] All 6 services running (`docker ps | grep maximus`)
- [ ] Grafana accessible (http://localhost:3000)
- [ ] Prometheus accessible (http://localhost:9090)
- [ ] Demo runs successfully
- [ ] 44/44 tests passing
- [ ] Metrics being collected
- [ ] Dashboard shows data

If all checked ✅ → **You're ready to go!**

---

## 📞 Need Help?

- **Deployment Issues:** See [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting)
- **Monitoring Issues:** See [monitoring/README_MONITORING.md](monitoring/README_MONITORING.md#troubleshooting)
- **Architecture Questions:** Read [MAXIMUS_3.0_COMPLETE.md](MAXIMUS_3.0_COMPLETE.md)

---

## 🏁 What's Next?

**For Development:**
1. Explore the codebase
2. Run tests: `pytest test_*.py -v`
3. Modify and extend

**For Production:**
1. Follow [DEPLOYMENT.md](DEPLOYMENT.md) production checklist
2. Configure secrets and SSL
3. Set up monitoring alerts
4. Train models with real data (see [PROXIMOS_PASSOS.md](PROXIMOS_PASSOS.md))

**For Learning:**
1. Read scientific papers (cited in code)
2. Understand Free Energy Principle
3. Explore Predictive Coding implementation
4. Study Neuromodulation system

---

**MAXIMUS AI 3.0** - Up and running in 5 minutes! ✅

*Questions? Check README.md or documentation/*
