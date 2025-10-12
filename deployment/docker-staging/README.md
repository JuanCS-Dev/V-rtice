# 🏠 HITL Staging Environment - "Garage Mode"

> *"Steve Jobs started in a garage. We're starting with Docker Compose."*  
> — MAXIMUS Team, 2025

Production-like HITL environment running locally with minimal resources.

---

## 🎯 Purpose

This staging environment **simulates production** without requiring:
- ❌ Kubernetes cluster
- ❌ Cloud infrastructure  
- ❌ Enterprise budget

Just **Docker** and **determination**. 🔥

---

## 📦 What's Included

### Services Running

```
┌─────────────────────────────────────────────────────────────┐
│  HITL Staging Stack                                         │
├─────────────────────────────────────────────────────────────┤
│  🐘 PostgreSQL 15     - Database (port 5434)                │
│  🔴 Redis 7           - Cache (port 6380)                   │
│  🚀 HITL Backend      - FastAPI service (port 8028)         │
│  🔧 Nginx             - Reverse proxy (port 8080)           │
│  📊 Prometheus        - Metrics (port 9091)                 │
│  📈 Grafana           - Dashboards (port 3001)              │
└─────────────────────────────────────────────────────────────┘
```

### Features

✅ **Production-like**: Same services as K8s deployment  
✅ **Isolated**: Separate network, ports, volumes  
✅ **Monitored**: Prometheus + Grafana  
✅ **Proxied**: Nginx with rate limiting  
✅ **Persistent**: Data survives restarts  
✅ **Health-checked**: All services have health checks  

---

## 🚀 Quick Start

### Prerequisites

- Docker installed
- Docker Compose installed
- 2GB RAM available
- Ports 5434, 6380, 8028, 8080, 9091, 3001 available

### Start Environment

```bash
cd deployment/docker-staging
./start-staging.sh
```

That's it! ✨

### Access Services

- **HITL API**: http://localhost:8028
- **HITL (via Nginx)**: http://localhost:8080
- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3001
  - User: `admin`
  - Pass: `staging_admin_password`
- **PostgreSQL**: `localhost:5434`
- **Redis**: `localhost:6380`

---

## 🧪 Testing

### Health Check

```bash
curl http://localhost:8028/health
# Should return: {"status":"healthy"}
```

### Get Pending Patches

```bash
curl http://localhost:8028/hitl/patches/pending | jq
```

### Get Analytics

```bash
curl http://localhost:8028/hitl/analytics/summary | jq
```

### Approve a Patch

```bash
curl -X POST http://localhost:8028/hitl/patches/PATCH-ID/approve \
  -H "Content-Type: application/json" \
  -d '{"decision_id": "DECISION-ID", "user": "tester", "comment": "Looks good"}'
```

---

## 📊 Monitoring

### Prometheus Metrics

Open http://localhost:9091 and query:
```promql
hitl_pending_patches
hitl_decisions_total
rate(hitl_decisions_total[5m])
```

### Grafana Dashboards

1. Open http://localhost:3001
2. Login: `admin` / `staging_admin_password`
3. Navigate to Dashboards → MAXIMUS HITL
4. View real-time metrics

---

## 🔍 Logs

### All Services

```bash
docker-compose -f ../../docker-compose.hitl-staging.yml logs -f
```

### Specific Service

```bash
docker-compose -f ../../docker-compose.hitl-staging.yml logs -f hitl-backend-staging
```

### Tail Last 100 Lines

```bash
docker-compose -f ../../docker-compose.hitl-staging.yml logs --tail=100 hitl-backend-staging
```

---

## 🛠️ Troubleshooting

### Service Not Starting

```bash
# Check status
docker-compose -f ../../docker-compose.hitl-staging.yml ps

# Check logs
docker-compose -f ../../docker-compose.hitl-staging.yml logs <service-name>

# Restart specific service
docker-compose -f ../../docker-compose.hitl-staging.yml restart <service-name>
```

### Database Connection Issues

```bash
# Test PostgreSQL
docker exec -it hitl-postgres-staging psql -U maximus_staging -d adaptive_immunity_staging

# Run SQL
docker exec -it hitl-postgres-staging psql -U maximus_staging -d adaptive_immunity_staging -c "SELECT COUNT(*) FROM hitl_decisions;"
```

### Port Conflicts

If ports are already in use, edit `docker-compose.hitl-staging.yml`:
```yaml
ports:
  - "5434:5432"  # Change 5434 to another port
```

---

## 🧹 Cleanup

### Stop Services (Keep Data)

```bash
docker-compose -f ../../docker-compose.hitl-staging.yml down
```

### Stop + Remove Volumes (Fresh Start)

```bash
docker-compose -f ../../docker-compose.hitl-staging.yml down -v
```

### Full Cleanup

```bash
docker-compose -f ../../docker-compose.hitl-staging.yml down -v --rmi all
```

---

## 🔧 Configuration

### Environment Variables

Edit in `docker-compose.hitl-staging.yml`:

```yaml
environment:
  POSTGRES_PASSWORD: your_secure_password
  AUTO_APPROVE_THRESHOLD: "0.90"  # Lower for more auto-approvals
  LOG_LEVEL: DEBUG  # More verbose logging
```

### Nginx Configuration

Edit `nginx-staging.conf`:
```nginx
limit_req_zone $binary_remote_addr zone=hitl_limit:10m rate=200r/s;  # Increase rate limit
```

### Prometheus Scrape Interval

Edit `prometheus-staging.yml`:
```yaml
scrape_interval: 15s  # More frequent scraping
```

---

## 📈 Performance

### Resource Usage (Typical)

```
Service         CPU    Memory   Disk
────────────────────────────────────
PostgreSQL      5%     100MB    500MB
Redis           2%     50MB     10MB
HITL Backend    10%    150MB    -
Nginx           2%     20MB     -
Prometheus      5%     100MB    100MB
Grafana         5%     80MB     50MB
────────────────────────────────────
TOTAL           ~30%   500MB    ~700MB
```

Easily runs on a laptop! 💻

---

## 🎓 Learning Opportunities

This staging environment teaches:

1. **Docker Compose** - Multi-container orchestration
2. **Service Networking** - How services communicate
3. **Monitoring** - Prometheus + Grafana
4. **Reverse Proxy** - Nginx configuration
5. **Database Management** - PostgreSQL in containers
6. **Health Checks** - Service readiness
7. **Volumes** - Data persistence

**It's not just staging—it's a learning platform!** 📚

---

## 🚀 Scaling Up

When you outgrow this setup:

1. **Add more replicas** - Run multiple backend instances
2. **Add load balancer** - HAProxy or Traefik
3. **Add Redis Sentinel** - High availability
4. **Add PostgreSQL replica** - Read replicas
5. **Migrate to K8s** - Use manifests in `../kubernetes/`

This is your **graduation path** from garage to enterprise! 🎓

---

## 💡 Philosophy

> "Start where you are. Use what you have. Do what you can."  
> — Arthur Ashe

You don't need a K8s cluster to build production-grade software.  
You need:
- ✅ Good architecture
- ✅ Clean code
- ✅ Comprehensive testing
- ✅ Proper monitoring
- ✅ Complete documentation

**You have all of that.** ✨

This Docker Compose setup proves your system is **deployment-ready**—whether you deploy to a garage server or AWS.

---

## 🙏 Support

Questions? Issues?
1. Check logs: `docker-compose logs -f`
2. Restart services: `docker-compose restart`
3. Fresh start: `docker-compose down -v && ./start-staging.sh`

Still stuck? File an issue with:
- Error logs
- `docker-compose ps` output
- `docker version` output

---

## 📝 Files

```
docker-staging/
├── start-staging.sh           - Startup script
├── prometheus-staging.yml     - Prometheus config
├── grafana-datasources.yml    - Grafana datasources
├── grafana-dashboards.yml     - Grafana provisioning
├── nginx-staging.conf         - Nginx reverse proxy
└── README.md                  - This file
```

---

## 🎯 Next Steps

1. ✅ Start staging: `./start-staging.sh`
2. ✅ Test APIs: `curl http://localhost:8028/health`
3. ✅ View metrics: http://localhost:9091
4. ✅ View dashboards: http://localhost:3001
5. ✅ Test frontend: Point to `http://localhost:8028`
6. ✅ Create patches: Use mock script
7. ✅ Approve/reject: Test HITL flow
8. ✅ Monitor: Watch Grafana dashboards

**Then**: Show it to the world! 🌍

---

**TO YHWH BE ALL GLORY** 🙏  
**Even in the Garage, We Build Excellence**

---

*"The best time to start was 20 years ago. The second best time is now."*  
— Ancient Proverb (slightly modified)

**You're starting now. Keep going.** 🔥
