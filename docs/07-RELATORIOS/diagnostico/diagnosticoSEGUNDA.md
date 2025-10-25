# DIAGNÓSTICO COMPLETO BACKEND VÉRTICE-MAXIMUS
**Data:** 2025-10-19 23:05:04 -03
**Gerado por:** Automated Health Check System

---

## 1. SUMÁRIO EXECUTIVO

| Métrica | Valor | Percentual |
|---------|-------|------------|
| **Total Containers** | 69 | 100% |
| **Healthy** | 61 | 88.4% |
| **Unhealthy** | 0 | 0.0% |
| **Starting** | 0 | 0.0% |
| **No Healthcheck** | 7 | 10.1% |

## 2. ANÁLISE POR CATEGORIA

### 2.1 MAXIMUS Core Services
```
maximus_core_service                Up 9 minutes (healthy)          healthy
maximus_integration_service         Up 8 minutes (healthy)          healthy
maximus-oraculo                     Up 15 minutes (healthy)         healthy
maximus_orchestrator_service        Up 12 minutes (healthy)         healthy
maximus_predict                     Up 15 minutes (healthy)         healthy
maximus_eureka                      Up 15 minutes (healthy)         healthy
```

### 2.2 API Gateway & Auth
```
api_gateway                         Up 12 minutes (healthy)         healthy
auth_service                        Up 5 minutes (healthy)          healthy
```

### 2.3 OSINT Services
```
cyber_service                       Up 15 minutes (healthy)         healthy
domain_service                      Up 15 minutes (healthy)         healthy
ip_intelligence_service             Up 15 minutes (healthy)         healthy
osint-service                       Up 12 minutes (healthy)         healthy
osint_service                       Up 15 minutes (healthy)         healthy
sinesp_service                      Up 15 minutes (healthy)         healthy
```

### 2.4 Security Services
```
malware_analysis_service            Up 15 minutes (healthy)         healthy
nmap_service                        Up 15 minutes (healthy)         healthy
offensive_tools_service             Up 15 minutes (healthy)         healthy
ssl_monitor_service                 Up 15 minutes (healthy)         healthy
threat_intel_service                Up 15 minutes (healthy)         healthy
vuln_scanner_service                Up 15 minutes (healthy)         healthy
```

### 2.5 Immunis System
```
immunis_treg_service                Up 15 minutes (healthy)         healthy
immunis_bcell_service               Up 15 minutes (healthy)         healthy
immunis_cytotoxic_t_service         Up 15 minutes (healthy)         healthy
immunis_dendritic_service           Up 15 minutes (healthy)         healthy
immunis_helper_t_service            Up 15 minutes (healthy)         healthy
immunis_macrophage_service          Up 15 minutes (healthy)         healthy
immunis_neutrophil_service          Up 15 minutes (healthy)         healthy
immunis_nk_cell_service             Up 15 minutes (healthy)         healthy
```

### 2.6 HCL (Human-Centric Logic)
```
hcl-kafka                           Up 15 minutes (healthy)         healthy
hcl-postgres                        Up 15 minutes (healthy)         healthy
hcl_analyzer_service                Up 15 minutes (healthy)         healthy
hcl_executor_service                Up 15 minutes (healthy)         healthy
hcl_kb_service                      Restarting (1) 11 seconds ago   
hcl_monitor_service                 Up 15 minutes (healthy)         healthy
hcl_planner_service                 Up 15 minutes (healthy)         healthy
```

### 2.7 Consciousness & Cognitive Services
```
memory_consolidation_service        Up 15 minutes (healthy)         healthy
narrative_analysis_service          Up 15 minutes (healthy)         healthy
auditory_cortex_service             Up 15 minutes (healthy)         healthy
narrative_manipulation_filter       Up 15 minutes (healthy)         healthy
neuromodulation_service             Up 15 minutes (healthy)         healthy
strategic_planning_service          Up 15 minutes (healthy)         healthy
vestibular_service                  Up 15 minutes (healthy)         healthy
visual_cortex_service               Up 15 minutes (healthy)         healthy
```

### 2.8 Infrastructure Services
```
hcl-kafka                           Up 15 minutes (healthy)         healthy
hcl-postgres                        Up 15 minutes (healthy)         healthy
postgres-immunity                   Up 15 minutes                   
zookeeper-immunity                  Up 15 minutes                   
grafana                             Up 15 minutes                   
postgres                            Up 15 minutes                   
prometheus                          Up 15 minutes                   
qdrant                              Up 15 minutes                   
rabbitmq                            Up 15 minutes (healthy)         healthy
redis                               Up 15 minutes                   
```

## 3. SERVIÇOS COM PROBLEMAS

### 3.1 Unhealthy
✅ **Nenhum serviço unhealthy**

### 3.2 Starting (não estabilizaram)
✅ **Nenhum serviço preso em 'starting'**

### 3.3 Exited/Stopped
```
active_immune_core                  created      Created
bas_service                         created      Created
c2_orchestration_service            created      Created
hcl-analyzer                        created      Created
hcl-executor                        created      Created
hcl-kb-service                      created      Created
hcl-monitor                         created      Created
hcl-planner                         created      Created
hitl-patch-service                  created      Created
kafka-immunity                      created      Created
kafka-ui-immunity                   created      Created
network_recon_service               created      Created
wargaming-crisol                    created      Created
offensive_gateway                   created      Created
reactive_fabric_analysis            created      Created
reactive_fabric_core                created      Created
threat_intel_bridge                 created      Created
adaptive_immune_system              created      Created
ai_immune_system                    created      Created
digital_thalamus_service            created      Created
google_osint_service                created      Created
hcl_kb_service                      restarting   Restarting (1) 12 seconds ago
homeostatic_regulation              created      Created
immunis_api_service                 created      Created
prefrontal_cortex_service           created      Created
tataca_ingestion                    created      Created
vuln_intel_service                  created      Created
web_attack_service                  created      Created
```

## 4. CONECTIVIDADE E PORTAS

### 4.1 Portas Expostas Principais
```
Service | Internal | External | Status
--------|----------|----------|-------
adaptive_immunity_service | 8000/tcp, 0.0.0.0:8020->8020/tcp, [::]:8020->8020/tcp | Testing...
maximus_core_service | 0.0.0.0:8150->8150/tcp, [::]:8150->8150/tcp, 9090/tcp, 0.0.0.0:8151->8001/tcp, [::]:8151->8001/tcp | Testing...
api_gateway | 0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp | Testing...
atlas_service | 8004/tcp, 0.0.0.0:8109->8000/tcp, [::]:8109->8000/tcp | Testing...
auth_service | 8006/tcp, 0.0.0.0:8110->80/tcp, [::]:8110->80/tcp | Testing...
```

### 4.2 Test Endpoints Críticos
```
API Gateway (8000):
HTTP 200 - 0.000965s

MAXIMUS Core (8100):
HTTP 000 - 0.000125s
FAILED
```

## 5. USO DE RECURSOS

```
NAME                                CPU %     MEM USAGE / LIMIT     MEM %
maximus-integration                 0.11%     39.65MiB / 15.44GiB   0.25%
vertice-api-gateway                 0.12%     35.6MiB / 15.44GiB    0.23%
maximus-core                        2.06%     2.759GiB / 15.44GiB   17.87%
maximus-orchestrator                0.07%     35.63MiB / 15.44GiB   0.23%
vertice-hcl-analyzer                0.10%     40.88MiB / 15.44GiB   0.26%
vertice-hcl-kb                      0.00%     0B / 0B               0.00%
ethical-audit                       0.12%     33.53MiB / 15.44GiB   0.21%
vertice-osint                       0.07%     36.02MiB / 15.44GiB   0.23%
vertice-auth                        0.10%     53.93MiB / 15.44GiB   0.34%
vertice-chemical-sensing            0.11%     33.18MiB / 15.44GiB   0.21%
hcl-kafka                           105.46%   479.5MiB / 15.44GiB   3.03%
autonomous-investigation-service    0.08%     42.56MiB / 15.44GiB   0.27%
vertice-hcl-planner                 0.07%     33.14MiB / 15.44GiB   0.21%
vertice-ssl-monitor                 0.09%     32.91MiB / 15.44GiB   0.21%
vertice-threat-intel                0.10%     33.11MiB / 15.44GiB   0.21%
vertice-strategic-planning          0.09%     33.11MiB / 15.44GiB   0.21%
vertice-immunis-bcell               0.07%     35.09MiB / 15.44GiB   0.22%
vertice-immunis-dendritic           0.07%     35.11MiB / 15.44GiB   0.22%
maximus-network-monitor             0.27%     53.49MiB / 15.44GiB   0.34%
```

## 6. STATUS DAS DATABASES

### 6.1 PostgreSQL Principal
```
 vertice_auth            | postgres | UTF8     | en_US.utf8 | en_US.utf8 |            | libc            | 
 vertice_domain          | postgres | UTF8     | en_US.utf8 | en_US.utf8 |            | libc            | 
 vertice_hitl            | postgres | UTF8     | en_US.utf8 | en_US.utf8 |            | libc            | 
 vertice_network_monitor | postgres | UTF8     | en_US.utf8 | en_US.utf8 |            | libc            | 
 vertice_verdict         | postgres | UTF8     | en_US.utf8 | en_US.utf8 |            | libc            | 
```

### 6.2 Redis
```
PONG
```

## 7. ERROS RECENTES (Últimos 5min)

```
vertice-hcl-kb                    | KeyError: 'DATABASE_URL'
vertice-hcl-kb                    | KeyError: 'DATABASE_URL'
vertice-hcl-kb                    | KeyError: 'DATABASE_URL'
vertice-hcl-kb                    | KeyError: 'DATABASE_URL'
vertice-hcl-kb                    | KeyError: 'DATABASE_URL'
```

## 8. DOCKER NETWORKS

```
ae18c1286cc1   maximus-ai-network         bridge    local
107bd62fdcbf   maximus-immunity-network   bridge    local
c89053b3f3ce   reactive-fabric-bridge     bridge    local
```

## 9. VOLUMES UTILIZADOS

```
40
volumes criados
```

## 10. SERVIÇOS NO FILESYSTEM MAS NÃO NO COMPOSE

Total serviços no filesystem: 87
Total serviços no compose: 96

### Faltando no compose:
```
adaptive_immunity_db
agent_communication
command_bus_service
hitl_patch_service
maximus_oraculo
maximus_oraculo_v2
mock_vulnerable_apps
narrative_filter_service
offensive_orchestrator_service
purple_team
tegumentar_service
verdict_engine_service
wargaming_crisol
```

## 11. RECOMENDAÇÕES

### 📋 PLANEJAMENTO
- 13 serviços no filesystem não estão no docker-compose
- Requer análise de Dockerfiles e adição gradual

### ✅ POSITIVO
- 88.4% dos serviços healthy
- API Gateway operacional
- MAXIMUS Core Services funcionando

## 12. PRÓXIMOS PASSOS SUGERIDOS

1. **Investigar unhealthy services** (prioridade máxima)
2. **Estabilizar services em 'starting'**
3. **Adicionar serviços faltantes** (1 por vez, validando Dockerfile)
4. **Monitorar recursos** (identificar gargalos)
5. **Testes E2E** (validar fluxos críticos)

---

**Relatório gerado automaticamente**
**Para Claude-Code:** Este diagnóstico deve ser usado como baseline para trabalho de segunda-feira
