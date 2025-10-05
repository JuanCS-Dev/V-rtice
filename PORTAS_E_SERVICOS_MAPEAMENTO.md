# 🗺️ MAPEAMENTO COMPLETO DE PORTAS E SERVIÇOS - VÉRTICE/MAXIMUS AI

**Data**: 04 de Outubro de 2025
**Tipo**: Portas Estáticas (Definidas no docker-compose.yml)
**Segurança**: Rede Docker isolada + Firewall + Autenticação

---

## 🎯 PORTAS PRINCIPAIS (Expostas ao Host)

### Core Services
| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `8001` | Maximus Core Service | maximus-core | **AI Core** - Chat, Tools, Orchestration |
| `8016` | Maximus Orchestrator | maximus-orchestrator | Orchestração de workflows |
| `8008` | Maximus Predict | maximus-predict | Análise preditiva |
| `8010` | ADR Core | vertice-adr-core | Anomaly Detection & Response |
| `8099` | API Gateway | vertice-api-gateway | Gateway principal (frontend) |

### Database & Cache
| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `6379` | Redis | vertice-redis | Cache e pub/sub |
| `5432` | PostgreSQL | vertice-postgres | Database principal |
| `6333` | Qdrant | vertice-qdrant | Vector database (embeddings) |

### Monitoring
| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `9090` | Prometheus | vertice-prometheus | Métricas |
| `3000` | Grafana | vertice-grafana | Dashboards |

---

## 🔒 OFFENSIVE SECURITY ARSENAL (Portas 8032-8037)

| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `8032` | Network Recon | vertice-network-recon | Masscan + Nmap |
| `8033` | Vuln Intel | vertice-vuln-intel | CVE Intelligence |
| `8034` | Web Attack | vertice-web-attack | OWASP Scanner |
| `8035` | C2 Orchestration | c2_orchestration_service | Cobalt Strike + Metasploit |
| `8036` | BAS | bas_service | MITRE ATT&CK Simulation |
| `8037` | Offensive Gateway | offensive_gateway | Workflow Gateway |

---

## 🕵️ OSINT & INTELLIGENCE

| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `8002` | OSINT Service | vertice-osint | OSINT multi-source |
| `8003` | Google OSINT | vertice-google-osint | Google dorking |
| `8004` | SINESP | vertice-sinesp | Vehicle data (Brazil) |

---

## 🛡️ CYBER SECURITY SERVICES

| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `8000` | IP Intelligence | vertice-ip-intel | IP analysis |
| `8013` | Threat Intel | vertice-threat-intel | Threat intelligence |
| `8006` | Nmap Service | vertice-nmap | Port scanning |
| `8007` | Domain Service | vertice-domain | Domain/DNS analysis |
| `8008` | Network Monitor | vertice-network-monitor | Real-time monitoring |
| `8012` | SSL Monitor | vertice-ssl-monitor | SSL/TLS analysis |
| `8011` | Malware Analysis | vertice-malware-analysis | Malware detection |
| `8009` | Social Engineering | vertice-social-eng | SE campaigns |
| `????` | Vuln Scanner | vertice-vuln-scanner | Vulnerability scanner |

---

## 🧠 ASA (AUTONOMIC SAFETY ARCHITECTURE)

| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `8010` | ADR Core | vertice-adr-core | Anomaly Detection |
| `8011` | Prefrontal Cortex | vertice-prefrontal-cortex | Decision-making |
| `8014` | Strategic Planning | (TBD) | Goal planning |
| `8015` | Memory Consolidation | (TBD) | Long-term memory |
| `8016` | Neuromodulation | (TBD) | System optimization |

---

## 🦠 IMMUNIS (AI IMMUNE SYSTEM)

| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `8005` | Immunis API | vertice-immunis-api | Main API |
| `????` | Macrophage | vertice-immunis-macrophage | Threat engulfment |
| `????` | Neutrophil | vertice-immunis-neutrophil | Fast response |
| `????` | Dendritic Cell | vertice-immunis-dendritic | Pattern recognition |
| `????` | B Cell | vertice-immunis-bcell | Antibody generation |
| `????` | Helper T Cell | vertice-immunis-helper-t | Coordination |
| `????` | Cytotoxic T Cell | vertice-immunis-cytotoxic-t | Infected cell killing |
| `????` | NK Cell | vertice-immunis-nk-cell | Innate immunity |

---

## 👁️ COGNITIVE SERVICES (SENSORY CORTEX)

| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `8017` | Visual Cortex | vertice-visual-cortex | Image analysis |
| `8018` | Auditory Cortex | vertice-auditory-cortex | Audio analysis |
| `????` | Somatosensory | vertice-somatosensory | Touch/pressure |
| `????` | Chemical Sensing | vertice-chemical-sensing | Smell/taste |
| `????` | Vestibular | vertice-vestibular | Balance/orientation |

---

## 🗣️ HCL (HUMAN-CENTRIC LANGUAGE)

| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `8020` | HCL Analyzer | hcl-analyzer | Intent analysis |
| `8021` | HCL Executor | hcl-executor | Command execution |
| `8022` | HCL KB (Planner) | hcl-kb-service | Knowledge base |
| `8023` | HCL Monitor | hcl-monitor | Monitoring |
| `8024` | HCL Planner | hcl-planner | Execution planning |

**HCL Infrastructure**:
- PostgreSQL: porta interna
- Kafka: porta interna

---

## 🔬 MAXIMUS SUB-SYSTEMS

| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `8200` | EUREKA | maximus-eureka | Deep malware analysis |
| `8201` | ORÁCULO | maximus-oraculo | Self-improvement engine |
| `8202` | PREDICT | maximus-predict | Predictive analytics |

---

## 🌐 ATLAS & RTE (REAL-TIME ENGINES)

| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `????` | Atlas | vertice-atlas | Graph engine |
| `????` | RTE Service | rte-service | Real-time processing |
| `????` | HPC Service | hpc-service | High-performance computing |

---

## 🦜 TATACÁ & SERIEMA (GRAPH)

| Porta | Serviço | Container | Descrição |
|-------|---------|-----------|-----------|
| `????` | Tatacá Ingestion | vertice-tataca-ingestion | Data ingestion |
| `????` | Seriema Graph | vertice-seriema-graph | Graph analytics |

---

## 🔐 PORTAS INTERNAS (Não expostas ao host)

Serviços que rodam **apenas na rede Docker interna** e não são acessíveis externamente:

- Todos os serviços Immunis (exceto API)
- Kafka (HCL)
- PostgreSQL (HCL)
- Serviços cognitive sem porta definida
- Digital Thalamus
- Narrative Filter
- AI Immune System
- Homeostatic Regulation

---

## 🛡️ RECOMENDAÇÕES DE SEGURANÇA

### 1. **Firewall Configuration** (iptables/ufw)
```bash
# Permitir apenas API Gateway externamente
ufw allow 8099/tcp comment "API Gateway"
ufw allow 3000/tcp comment "Grafana Dashboard"

# Bloquear todas as outras portas backend
ufw deny 8001:8037/tcp
ufw deny 6379/tcp  # Redis
ufw deny 5432/tcp  # Postgres
```

### 2. **Docker Network Isolation**
✅ Já está implementado - todos os serviços usam `vertice-network`
✅ Comunicação interna apenas

### 3. **Reverse Proxy (Nginx/Traefik)**
```nginx
# Expor apenas via proxy com TLS
server {
    listen 443 ssl;
    server_name api.vertice.local;

    location / {
        proxy_pass http://localhost:8099;
    }
}
```

### 4. **Service Mesh (Opcional - Alta Segurança)**
- **Istio** ou **Linkerd** para mTLS entre serviços
- Criptografia end-to-end mesmo na rede interna

### 5. **API Authentication**
✅ Cada serviço deve ter:
- JWT tokens
- Rate limiting
- IP whitelisting (se aplicável)

### 6. **Monitoring & Alerting**
✅ Prometheus + Grafana já implementados
- Alertas para portas abertas inesperadamente
- Detecção de port scanning

---

## 📊 MAPA VISUAL DE ARQUITETURA

```
                    ┌─────────────────┐
                    │  INTERNET/USER  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  FIREWALL/UFW   │
                    │  (Porta 8099)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  API GATEWAY    │
                    │  (Port 8099)    │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐      ┌──────▼──────┐      ┌─────▼──────┐
   │ MAXIMUS  │      │ OFFENSIVE   │      │   OSINT    │
   │   CORE   │      │  ARSENAL    │      │  SERVICES  │
   │ (8001)   │      │ (8032-8037) │      │ (8002-8004)│
   └────┬─────┘      └──────┬──────┘      └─────┬──────┘
        │                   │                    │
        └───────────────────┼────────────────────┘
                            │
                ┌───────────▼───────────┐
                │  VERTICE NETWORK      │
                │  (Docker Internal)    │
                │                       │
                │  • Database (5432)    │
                │  • Redis (6379)       │
                │  • Qdrant (6333)      │
                │  • ASA Services       │
                │  • Immunis System     │
                │  • Cognitive Services │
                │  • HCL Platform       │
                └───────────────────────┘
```

---

## ❓ FAQ - PERGUNTAS FREQUENTES

### **"Posso mudar para portas aleatórias?"**
**Sim**, mas precisaria:
1. Service discovery (Consul/Eureka)
2. Atualizar docker-compose para usar `expose:` em vez de `ports:`
3. Configurar DNS interno ou service mesh
4. Frontend precisaria descobrir portas dinamicamente

**Recomendação**: Para seu caso (desenvolvimento/interno), **portas estáticas são OK** com firewall adequado.

### **"É inseguro ter portas conhecidas?"**
**Não**, se você seguir:
1. Firewall bloqueando acesso externo direto
2. Autenticação em todas as APIs
3. Rate limiting
4. Monitoramento de acesso

**"Security through obscurity"** (portas aleatórias) **não é segurança real**.

### **"Como resolvo conflito na porta 8001?"**
Opção 1: Matar processo usando 8001
```bash
lsof -ti:8001 | xargs kill -9
```

Opção 2: Mudar porta do Maximus Core
```yaml
# docker-compose.yml
ports:
  - "8001:8001"  # Mudar para "8101:8001"
```

Opção 3: Usar Docker host network mode (não recomendado)

---

## 🎯 CONCLUSÃO

✅ **Portas estáticas são ADEQUADAS** para seu sistema
✅ **NÃO quebra segurança** se bem configurado
✅ **Vantagens**: Documentação clara, debugging fácil
✅ **Firewall + Auth + Network Isolation** = Segurança real

**Lista completa documentada para referência rápida**!

---

**Atualizado em**: 04 de Outubro de 2025
**Versão**: 1.0
**Autor**: Claude (Anthropic) + Juan (Vértice Team)
