# PFC Consciousness API - Deployment Guide

**Production deployment guide for PFC Consciousness API**

Author: Juan Carlos de Souza + Claude Code
Lei Governante: Constituição Vértice v2.7

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Deployment](#docker-deployment)
3. [Manual Deployment](#manual-deployment)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

### One-Command Deploy

```bash
# Clone and deploy
git clone <repository-url>
cd backend/consciousness

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Deploy full stack
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f pfc-api
```

API available at: `http://localhost:8001/docs`

---

## 🐳 Docker Deployment

### Full Stack (Recommended)

Includes PFC API + PostgreSQL + PGAdmin:

```bash
# Start all services
docker-compose up -d

# Start with PGAdmin
docker-compose --profile tools up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (data loss!)
docker-compose down -v
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| pfc-api | 8001 | PFC Consciousness API |
| postgres | 5432 | PostgreSQL database |
| pgadmin | 5050 | PGAdmin (optional) |

### Health Checks

```bash
# API health
curl http://localhost:8001/health

# Database health
docker-compose exec postgres pg_isready

# View all health status
docker-compose ps
```

### Scaling

```bash
# Scale API workers
docker-compose up -d --scale pfc-api=3

# Or edit docker-compose.yml:
services:
  pfc-api:
    deploy:
      replicas: 3
```

---

## 🔧 Manual Deployment

### 1. Install Dependencies

```bash
# Install Python 3.11+
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv postgresql-client

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Setup Database

```bash
# Install PostgreSQL 16
sudo apt-get install postgresql-16 postgresql-contrib-16

# Create database
sudo -u postgres psql -c "CREATE DATABASE vertice_consciousness;"

# Create user (optional)
sudo -u postgres psql -c "CREATE USER pfc_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE vertice_consciousness TO pfc_user;"
```

### 3. Configure Environment

```bash
# Copy environment file
cp .env.example .env

# Edit configuration
nano .env

# Set production values:
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=<your_secure_password>
ENVIRONMENT=production
DEBUG=false
```

### 4. Run Application

```bash
# Development
uvicorn consciousness.api.app:app --host 0.0.0.0 --port 8001 --reload

# Production (with Gunicorn)
gunicorn consciousness.api.app:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8001 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info
```

### 5. Setup Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/pfc-api.service
```

```ini
[Unit]
Description=PFC Consciousness API
After=network.target postgresql.service

[Service]
Type=notify
User=appuser
Group=appuser
WorkingDirectory=/opt/consciousness
Environment="PATH=/opt/consciousness/venv/bin"
ExecStart=/opt/consciousness/venv/bin/gunicorn consciousness.api.app:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8001 \
    --access-logfile /var/log/pfc-api/access.log \
    --error-logfile /var/log/pfc-api/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable pfc-api
sudo systemctl start pfc-api

# Check status
sudo systemctl status pfc-api

# View logs
sudo journalctl -u pfc-api -f
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | localhost | PostgreSQL host |
| `POSTGRES_PORT` | 5432 | PostgreSQL port |
| `POSTGRES_DB` | vertice_consciousness | Database name |
| `POSTGRES_USER` | postgres | Database user |
| `POSTGRES_PASSWORD` | - | **REQUIRED** Database password |
| `API_HOST` | 0.0.0.0 | API bind host |
| `API_PORT` | 8001 | API port |
| `API_WORKERS` | 4 | Number of workers |
| `MIP_ENABLED` | true | Enable MIP integration |
| `CORS_ORIGINS` | * | Allowed CORS origins |
| `LOG_LEVEL` | info | Logging level |
| `ENVIRONMENT` | development | Environment mode |

### Production Checklist

- [ ] Change default passwords
- [ ] Configure CORS origins
- [ ] Set `DEBUG=false`
- [ ] Use strong `SECRET_KEY`
- [ ] Enable SSL/TLS
- [ ] Configure firewall
- [ ] Setup log rotation
- [ ] Enable monitoring
- [ ] Configure backups

---

## 📊 Monitoring

### Health Endpoints

```bash
# API health
curl http://localhost:8001/health

# Response:
{
  "status": "healthy",
  "service": "PFC Consciousness API",
  "version": "1.0.0",
  "pfc_initialized": true,
  "persistence_enabled": true,
  "mip_enabled": true
}
```

### Metrics

```bash
# Decision statistics
curl http://localhost:8001/statistics

# Suffering analytics
curl http://localhost:8001/analytics/suffering
```

### Logs

```bash
# Docker logs
docker-compose logs -f pfc-api

# Systemd logs
sudo journalctl -u pfc-api -f

# Application logs
tail -f logs/pfc-api.log
```

### Prometheus (Optional)

Add to docker-compose.yml:

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - consciousness-network
```

---

## 🔍 Troubleshooting

### API won't start

```bash
# Check logs
docker-compose logs pfc-api

# Common issues:
# 1. Database not ready
docker-compose ps postgres

# 2. Port already in use
sudo lsof -i :8001
sudo kill -9 <PID>

# 3. Permission issues
sudo chown -R appuser:appuser /app
```

### Database connection failed

```bash
# Test connection
docker-compose exec postgres pg_isready

# Check environment variables
docker-compose exec pfc-api env | grep POSTGRES

# Restart database
docker-compose restart postgres
```

### High memory usage

```bash
# Reduce workers
# Edit docker-compose.yml:
environment:
  API_WORKERS: 2

# Or reduce replicas
docker-compose up -d --scale pfc-api=1
```

### Slow response times

```bash
# Check database performance
docker-compose exec postgres psql -U postgres -d vertice_consciousness -c "SELECT * FROM pg_stat_activity;"

# Add database indexes (if needed)
# Check query service performance
curl http://localhost:8001/statistics
```

---

## 🔒 Security

### SSL/TLS Configuration

Use reverse proxy (Nginx/Traefik):

```nginx
# Nginx example
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Database Security

```bash
# Change default password
docker-compose exec postgres psql -U postgres -c "ALTER USER postgres PASSWORD 'new_secure_password';"

# Limit connections
# Edit postgresql.conf:
max_connections = 100
```

---

## 📦 Backup & Recovery

### Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U postgres vertice_consciousness > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U postgres vertice_consciousness < backup_20250101.sql

# Automated backups
cat > backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec postgres pg_dump -U postgres vertice_consciousness > $BACKUP_DIR/consciousness_$DATE.sql
# Keep only last 7 days
find $BACKUP_DIR -name "consciousness_*.sql" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

---

## 🎯 Production Best Practices

1. **Use environment-specific configs**
   - Development: `.env.development`
   - Staging: `.env.staging`
   - Production: `.env.production`

2. **Enable log rotation**
   ```bash
   # /etc/logrotate.d/pfc-api
   /var/log/pfc-api/*.log {
       daily
       rotate 14
       compress
       delaycompress
       notifempty
       create 0640 appuser appuser
       sharedscripts
       postrotate
           systemctl reload pfc-api
       endscript
   }
   ```

3. **Monitor resource usage**
   - Setup alerts for CPU/memory/disk
   - Monitor database connections
   - Track API response times

4. **Regular updates**
   ```bash
   # Update containers
   docker-compose pull
   docker-compose up -d

   # Update application
   git pull
   docker-compose build --no-cache
   docker-compose up -d
   ```

---

## 📞 Support

For issues or questions:
- Check logs first
- Review troubleshooting section
- Check GitHub issues
- Contact: support@vertice.com

---

*Deployment guide validated for production use*
*Padrão: PAGANI ABSOLUTO*
