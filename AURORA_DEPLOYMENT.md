# 🤖 AURORA CYBER INTEL HUB - Deployment Guide
## NSA-Grade Autonomous Investigation Platform - OFFLINE FIRST

---

## 🔒 **FILOSOFIA OFFLINE-FIRST**

**ZERO TRUST em APIs externas** - Todo o sistema foi projetado para funcionar 100% offline.

### **Por que Offline-First?**
- ✅ **Privacidade**: Seus dados nunca saem do seu servidor
- ✅ **Velocidade**: Análise instantânea sem rate limits
- ✅ **Confiabilidade**: Funciona mesmo sem internet
- ✅ **Custo zero**: Não precisa de API keys
- ✅ **Sem dependências**: Não confia em serviços de terceiros

### **Modo Híbrido (Opcional)**
Se você quiser complementar a análise offline com APIs externas:
- Configure `USE_EXTERNAL_APIS=true` no `.env`
- Adicione suas API keys
- O sistema usa: 60% offline + 40% APIs externas

---

## 📋 **O QUE FOI IMPLEMENTADO**

### **Frontend (React)**
✅ **AuroraCyberHub.jsx** - Interface de orquestração com:
- 4 tipos de investigação (Auto, Defensiva, Ofensiva, Completa)
- Timeline de execução em tempo real
- Status de 8+ serviços
- Relatório final automatizado
- UI moderna com gradientes roxo/cyan

### **Backend Services (FastAPI) - OFFLINE FIRST**

#### 1. **Threat Intelligence Aggregator** (Port 8013) - OFFLINE FIRST ⚡
- **Análise Offline (Primária)**:
  - Database SQLite local de IPs/domínios maliciosos
  - Heurísticas DNS (PTR records, patterns)
  - Análise de CIDR ranges
  - Detecção de typosquatting/homographs
  - Whitelists de serviços conhecidos (Google, Cloudflare, etc)
  - TLD risk analysis
  - Scan behavior detection
- **APIs Externas (Opcional)**: AbuseIPDB, VirusTotal, GreyNoise, OTX
- **Features**:
  - Threat score agregado (0-100)
  - Detecção automática de tipo de target
  - Reputação cross-referenciada
  - Recommendations baseadas em análise local + APIs (se habilitadas)

#### 2. **Malware Analysis Service** (Port 8014) - OFFLINE FIRST ⚡
- **Análise Offline (Primária)**:
  - Database SQLite local de hashes maliciosos
  - 30+ padrões comportamentais suspeitos
  - Análise de entropia (detecta empacotamento/crypto)
  - Detecção heurística por extensão/nome
  - Análise estrutural (PE, ELF headers)
  - Detecção de malware families por padrões
  - Sistema de scoring multi-dimensional
- **APIs Externas (Opcional)**: VirusTotal, Hybrid Analysis
- **Features**:
  - Análise de arquivos (upload)
  - Lookup de hashes (MD5/SHA1/SHA256)
  - Análise de URLs (heurísticas locais)
  - Identificação de malware families
  - Database expansível com novos hashes

#### 3. **SSL/TLS Monitor** (Port 8015)
- **Features** NSA-Grade:
  - Análise profunda de certificados
  - Detecção de vulnerabilidades (POODLE, BEAST, etc)
  - Compliance check: PCI-DSS, HIPAA, NIST, FIPS-140-2
  - Security score (0-100) e grade (A+ to F)
  - Detecção de MitM e certificados suspeitos
  - Análise de cipher suites
  - Validação de chain completa

#### 4. **Aurora Orchestrator** (Port 8016) 🧠
- **O Cérebro da Operação**:
  - Decision Engine que decide automaticamente o workflow
  - Detecção automática de tipo de target
  - Orquestração paralela/sequencial inteligente
  - Threat assessment agregado
  - Recommendations baseadas em IA
  - Real-time status tracking

---

## 🚀 **QUICK START**

### **Pré-requisitos**
```bash
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
```

### **1. Clone e Configure**
```bash
cd /home/juan/vertice-dev

# ========================================
# MODO OFFLINE (DEFAULT - RECOMENDADO) ✅
# ========================================
# Não precisa configurar nada! O sistema já funciona 100% offline.

# ========================================
# MODO HÍBRIDO (OPCIONAL)
# ========================================
# Se você quiser complementar com APIs externas:
# 1. Copie o arquivo de exemplo
cp backend/services/threat_intel_service/.env.example backend/services/threat_intel_service/.env

# 2. Edite o .env e adicione:
# USE_EXTERNAL_APIS=true
# ABUSEIPDB_API_KEY=your_key
# VIRUSTOTAL_API_KEY=your_key
# GREYNOISE_API_KEY=your_key
# OTX_API_KEY=your_key
```

### **2. Start Backend (Docker)**
```bash
# Build e start todos os serviços
docker-compose up -d api_gateway threat_intel_service malware_analysis_service ssl_monitor_service aurora_orchestrator_service

# Verificar logs
docker-compose logs -f aurora_orchestrator_service
```

### **3. Start Frontend**
```bash
cd frontend
npm run dev
```

### **4. Acessar**
```
Frontend: http://localhost:5173
API Gateway: http://localhost:8000
Aurora Orchestrator: http://localhost:8016
```

---

## 🎯 **COMO USAR**

### **Via Interface (Recomendado)**

1. **Acesse o Cyber Dashboard**
   - Navegue para: `Cyber Security Module`

2. **Clique em "AURORA AI HUB"** (botão roxo com ✨)

3. **Configure a Investigação**:
   - **Target**: IP, Domain, URL, Hash
   - **Tipo de Investigação**:
     - `Aurora Automático`: IA decide tudo
     - `Análise Defensiva`: Threat intel focus
     - `Red Team`: Offensive scanning (requer auth)
     - `Investigação Completa`: Todos os serviços

4. **Iniciar**: Clique em "INICIAR INVESTIGAÇÃO"

5. **Acompanhe em Tempo Real**:
   - Timeline mostra cada step
   - Services status atualiza em tempo real
   - Threat assessment ao final

### **Via API Direta**

#### **Start Investigation**
```bash
curl -X POST http://localhost:8016/api/aurora/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "target": "8.8.8.8",
    "investigation_type": "auto",
    "priority": 5,
    "stealth_mode": false,
    "deep_analysis": true
  }'
```

#### **Get Status**
```bash
curl http://localhost:8016/api/aurora/investigation/AURORA-20240929-123456
```

#### **List Services**
```bash
curl http://localhost:8016/api/aurora/services
```

---

## 📊 **SERVICE PORTS**

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 8000 | Unified entry point |
| IP Intelligence | 8002 | Geolocation & ASN |
| Threat Intel Aggregator | 8013 | Multi-source threat intel |
| Malware Analysis | 8014 | File/Hash/URL analysis |
| SSL/TLS Monitor | 8015 | Certificate analysis |
| Aurora Orchestrator | 8016 | AI Brain 🧠 |
| Nmap Scanner | 8010 | Port scanning |
| Vuln Scanner | 8011 | Vulnerability detection |
| Social Eng | 8012 | Phishing campaigns |

---

## 🔐 **API KEYS - OPCIONAL (Modo Híbrido)**

### **⚠️ IMPORTANTE: API Keys são OPCIONAIS**
O sistema funciona 100% sem nenhuma API key usando análise offline.

**Se você quiser habilitar modo híbrido** (offline + APIs externas):

### **VirusTotal** (Opcional)
1. Acesse: https://www.virustotal.com/gui/join-us
2. Crie conta gratuita
3. Vá em: Profile → API Key
4. **Limite**: 4 requests/minute (free tier)

### **AbuseIPDB** (Opcional)
1. Acesse: https://www.abuseipdb.com/register
2. Verifique email
3. API Keys → Create Key
4. **Limite**: 1000 requests/day (free tier)

### **GreyNoise** (Opcional)
1. Acesse: https://www.greynoise.io/
2. Sign up (Community account é free)
3. Dashboard → API Key
4. **Limite**: 500 requests/day (community)

### **AlienVault OTX** (Opcional)
1. Acesse: https://otx.alienvault.com/
2. Create account
3. Settings → OTX Key
4. **Limite**: Generous (free tier)

**Nota**:
- ✅ **Modo Offline (default)**: Funciona sem nenhuma API key
- ⚡ **Modo Híbrido**: Requer `USE_EXTERNAL_APIS=true` + API keys

---

## 🧪 **TESTING**

### **Test Individual Services**

#### **Threat Intel**
```bash
curl -X POST http://localhost:8013/api/threat-intel/check \
  -H "Content-Type: application/json" \
  -d '{"target": "1.1.1.1", "target_type": "ip"}'
```

#### **Malware Analysis**
```bash
curl -X POST http://localhost:8014/api/malware/analyze-hash \
  -H "Content-Type: application/json" \
  -d '{"hash_value": "44d88612fea8a8f36de82e1278abb02f", "hash_type": "md5"}'
```

#### **SSL Monitor**
```bash
curl -X POST http://localhost:8015/api/ssl/check \
  -H "Content-Type: application/json" \
  -d '{"target": "google.com", "port": 443}'
```

### **Test Aurora Orchestrator**
```bash
# Test IP Investigation
curl -X POST http://localhost:8016/api/aurora/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "target": "8.8.8.8",
    "investigation_type": "defensive",
    "priority": 8
  }'

# Test Domain Investigation
curl -X POST http://localhost:8016/api/aurora/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "target": "google.com",
    "investigation_type": "full",
    "deep_analysis": true
  }'

# Test Hash Lookup
curl -X POST http://localhost:8016/api/aurora/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "target": "44d88612fea8a8f36de82e1278abb02f",
    "investigation_type": "auto"
  }'
```

---

## 📈 **MONITORING**

### **Health Checks**
```bash
# Aurora Orchestrator
curl http://localhost:8016/health

# Threat Intel
curl http://localhost:8013/health

# Malware Analysis
curl http://localhost:8014/health

# SSL Monitor
curl http://localhost:8015/health
```

### **Logs**
```bash
# Aurora Orchestrator
docker logs vertice-aurora-orchestrator -f

# Threat Intel
docker logs vertice-threat-intel -f

# Malware Analysis
docker logs vertice-malware-analysis -f

# SSL Monitor
docker logs vertice-ssl-monitor -f
```

---

## 🛡️ **SECURITY**

### **Rate Limiting**
- Configurado no API Gateway
- Default: 30 requests/minute por IP
- Aurora investigations: 10/minute

### **Authentication**
- Frontend: Session-based
- API: JWT tokens
- Offensive tools: Require special authorization

### **Data Privacy**
- Nenhum target é persistido por padrão
- Logs rotativos a cada 7 dias
- API keys em environment variables apenas

---

## 🐛 **TROUBLESHOOTING**

### **Service não inicia**
```bash
# Check logs
docker-compose logs service_name

# Rebuild
docker-compose build service_name --no-cache
docker-compose up -d service_name
```

### **Frontend não conecta ao backend**
```bash
# Verifique se API Gateway está rodando
curl http://localhost:8000/

# Verifique CORS no API Gateway
# File: backend/api_gateway/main.py
# Linha ~61: origins = [...]
```

### **Aurora Orchestrator timeout**
```bash
# Aumentar timeout no orchestrator
# File: backend/services/aurora_orchestrator_service/main.py
# Linha ~30: timeout=30.0 (ajustar conforme necessário)
```

---

## 💾 **OFFLINE DATABASES**

### **Como Funciona**
Cada serviço offline mantém um database SQLite local:
- `threat_intel.db`: IPs/domínios maliciosos conhecidos
- `malware.db`: Hashes de malware e padrões comportamentais

### **Database Stats**
```bash
# Ver estatísticas do database de malware
curl http://localhost:8014/api/malware/database/stats

# Exemplo de resposta:
{
  "total_malicious_hashes": 1,
  "total_behavior_patterns": 32,
  "total_malware_families": 1,
  "database_path": "malware.db"
}
```

### **Expandindo os Databases**
Você pode adicionar seus próprios hashes/IPs conhecidos:

```python
# Adicionar hash malicioso
from offline_malware_engine import OfflineMalwareEngine

engine = OfflineMalwareEngine()
engine.add_malicious_hash(
    hash_value="abc123...",
    hash_type="sha256",
    malware_family="Trojan.Generic",
    severity="high",
    description="Detected in the wild"
)
```

```python
# Adicionar IP malicioso
from offline_engine import OfflineThreatIntel

engine = OfflineThreatIntel()
engine.add_malicious_ip(
    ip="1.2.3.4",
    threat_type="botnet",
    severity="high",
    description="C2 server"
)
```

### **Importar Feeds Externos**
Você pode criar scripts para importar feeds de threat intelligence:
- AlienVault OTX exports
- Abuse.ch feeds
- Custom threat feeds
- IOC lists de incidentes

---

## 🎓 **WORKFLOW EXAMPLES**

### **Example 1: IP Investigation (Offline Mode)**
```
Target: 8.8.8.8
Type: Defensive
Mode: Offline First

Aurora Decision:
1. Threat Intel Check (Priority 10) - Offline Engine
2. IP Intelligence Analysis (Priority 9)
3. Nmap Quick Scan (Priority 7)

Results:
- Threat Score: 0/100
- Level: CLEAN
- Source: Local whitelist (Google DNS)
- Confidence: Medium
- Recommendations: ✅ Monitor standard
```

### **Example 2: Domain Investigation**
```
Target: suspicious-site.com
Type: Full

Aurora Decision:
1. Threat Intel Check (Priority 10)
2. SSL Certificate Analysis (Priority 8)
3. Nmap Service Scan (Priority 7)
4. Vulnerability Scanner (Priority 6)

Results:
- Threat Score: 85/100
- Level: CRITICAL
- Recommendations: 🚨 Block immediately
```

### **Example 3: Malware Hash (Offline Mode)**
```
Target: 44d88612fea8a8f36de82e1278abb02f
Type: Auto
Mode: Offline First

Aurora Decision:
1. Malware Analysis (Priority 10) - Offline Engine

Results:
- Malicious: YES
- Family: EICAR-Test-File
- Source: Local Database
- Threat Score: 100/100
- Confidence: High
- Detection Method: Hash match (MD5)
```

---

## 📚 **ARCHITECTURE**

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│     Aurora Cyber Intel Hub UI           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│       API Gateway (Port 8000)           │
│  Rate Limiting │ Auth │ Routing         │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│   Aurora Orchestrator (Port 8016)       │
│        🧠 AI Decision Engine            │
│   - Target Detection                    │
│   - Workflow Planning                   │
│   - Threat Assessment                   │
│   - Recommendation Generation           │
└────────────┬────────────────────────────┘
             │
       ┌─────┴──────┬──────────┬───────────┐
       ▼            ▼          ▼           ▼
┌───────────┐  ┌─────────┐  ┌──────┐  ┌──────┐
│Threat Intel│ │Malware  │  │SSL   │  │Nmap  │
│(8013)     │  │Analysis │  │Monitor│ │(8010)│
└───────────┘  │(8014)   │  │(8015)│  └──────┘
               └─────────┘  └──────┘
```

---

## 🚀 **PRODUCTION DEPLOYMENT**

### **Environment Variables**
```bash
# Create .env file
cat > .env << EOF
ABUSEIPDB_API_KEY=your_key_here
VIRUSTOTAL_API_KEY=your_key_here
GREYNOISE_API_KEY=your_key_here
OTX_API_KEY=your_key_here
HYBRID_ANALYSIS_API_KEY=your_key_here

# Database
REDIS_URL=redis://redis:6379

# Security
JWT_SECRET=your_super_secret_key_change_in_production
EOF
```

### **Docker Compose Production**
```bash
# Start all services
docker-compose up -d

# Scale Aurora Orchestrator (if needed)
docker-compose up -d --scale aurora_orchestrator_service=3

# Monitor
docker-compose ps
docker stats
```

### **Reverse Proxy (Nginx)**
```nginx
server {
    listen 443 ssl;
    server_name aurora.yourdomain.com;

    location / {
        proxy_pass http://localhost:5173;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

---

## 📞 **SUPPORT**

Para dúvidas ou problemas:
1. Check logs first: `docker-compose logs -f`
2. Verify API keys are configured
3. Test individual services
4. Check network connectivity

---

## 🎯 **NEXT STEPS**

### **Phase 2 - Enhancements**
- [ ] OSINT Integration (Email, Phone, Username)
- [ ] IDS/IPS Detection
- [ ] SIEM Integration
- [ ] Automated Playbooks
- [ ] WebSocket real-time updates
- [ ] Report generation (PDF/JSON)
- [ ] Historical analysis
- [ ] ML-based anomaly detection

### **Phase 3 - Advanced Features**
- [ ] Multi-tenant support
- [ ] Role-based access control
- [ ] Custom workflows
- [ ] API usage analytics
- [ ] Threat intel feeds subscription
- [ ] Integration with MISP
- [ ] Incident response automation

---

## 📄 **LICENSE**

Projeto VÉRTICE - Internal Use Only
NSA-Grade Classification: Confidential

---

**Built with ❤️ by Juan Carlos & Claude Code**
**Aurora AI Engine v2.0 - Autonomous Cyber Security Platform**