# 🔢 MAPEAMENTO SEQUENCIAL DE PORTAS - VÉRTICE/MAXIMUS AI

**Data**: 04 de Outubro de 2025
**Objetivo**: Eliminar conflitos de porta com indexação sequencial
**Range**: 9000-9100 (100 portas disponíveis)

---

## 🎯 PORTAS CRÍTICAS (Fixas - Não mudar)

| Porta | Serviço | Motivo |
|-------|---------|--------|
| 5432 | PostgreSQL | Padrão PostgreSQL |
| 6379 | Redis | Padrão Redis |
| 6333 | Qdrant | Vector DB |

---

## 🔢 SERVIÇOS MAPEADOS SEQUENCIALMENTE

### Core & API (9000-9009)
| Porta | Serviço | Container | Original |
|-------|---------|-----------|----------|
| 9000 | API Gateway | api_gateway | 8099 |
| 9001 | Maximus Core | maximus_core_service | 8001 |
| 9002 | Maximus Orchestrator | maximus_orchestrator_service | 8016 |
| 9003 | Maximus Predict | maximus_predict | 8008 |
| 9004 | ADR Core | adr_core_service | 8010 |
| 9005 | Auth Service | auth_service | - |

### Cyber Security Services (9010-9029)
| Porta | Serviço | Container | Original |
|-------|---------|-----------|----------|
| 9010 | IP Intelligence | ip_intelligence_service | 8000 |
| 9011 | Network Monitor | network_monitor_service | 8008 |
| 9012 | Nmap Service | nmap_service | 8006 |
| 9013 | Domain Service | domain_service | 8007 |
| 9014 | Vuln Scanner | vuln_scanner_service | - |
| 9015 | Threat Intel | threat_intel_service | 8013 |
| 9016 | Malware Analysis | malware_analysis_service | 8011 |
| 9017 | SSL Monitor | ssl_monitor_service | 8012 |
| 9018 | Social Engineering | social_eng_service | 8009 |
| 9019 | Cyber Service | cyber_service | - |

### OSINT Services (9030-9039)
| Porta | Serviço | Container | Original |
|-------|---------|-----------|----------|
| 9030 | OSINT Service | osint-service | 8002 |
| 9031 | Google OSINT | google_osint_service | 8003 |
| 9032 | SINESP | sinesp_service | 8004 |

### Offensive Arsenal (9040-9049)
| Porta | Serviço | Container | Original |
|-------|---------|-----------|----------|
| 9040 | Network Recon | network_recon_service | 8032 |
| 9041 | Vuln Intel | vuln_intel_service | 8033 |
| 9042 | Web Attack | web_attack_service | 8034 |
| 9043 | C2 Orchestration | c2_orchestration_service | 8035 |
| 9044 | BAS | bas_service | 8036 |
| 9045 | Offensive Gateway | offensive_gateway | 8037 |

### HCL Platform (9050-9059)
| Porta | Serviço | Container | Original |
|-------|---------|-----------|----------|
| 9050 | HCL Analyzer | hcl-analyzer | 8020 |
| 9051 | HCL Executor | hcl_executor_service | 8021 |
| 9052 | HCL KB/Planner | hcl_kb_service | 8022 |
| 9053 | HCL Monitor | hcl-monitor | 8023 |
| 9054 | HCL Planner | hcl-planner | 8024 |

### Maximus Subsystems (9060-9069)
| Porta | Serviço | Container | Original |
|-------|---------|-----------|----------|
| 9060 | EUREKA | maximus-eureka | 8200 |
| 9061 | ORÁCULO | maximus-oraculo | 8201 |
| 9062 | PREDICT | maximus-models | 8202 |
| 9063 | Integration | maximus_integration_service | - |

### ASA & Cognitive Services (9070-9089)
| Porta | Serviço | Container | Original |
|-------|---------|-----------|----------|
| 9070 | Prefrontal Cortex | prefrontal_cortex_service | - |
| 9071 | Visual Cortex | visual_cortex_service | 8017 |
| 9072 | Auditory Cortex | auditory_cortex_service | 8018 |
| 9073 | Somatosensory | somatosensory_service | - |
| 9074 | Chemical Sensing | chemical_sensing_service | - |
| 9075 | Vestibular | vestibular_service | - |
| 9076 | Digital Thalamus | digital_thalamus_service | - |
| 9077 | Narrative Filter | narrative_manipulation_filter | - |

### Immunis System (9080-9089)
| Porta | Serviço | Container | Original |
|-------|---------|-----------|----------|
| 9080 | Immunis API | immunis_api_service | 8005 |
| 9081 | Macrophage | immunis_macrophage_service | - |
| 9082 | Neutrophil | immunis_neutrophil_service | - |
| 9083 | Dendritic Cell | immunis_dendritic_service | - |
| 9084 | B Cell | immunis_bcell_service | - |
| 9085 | Helper T Cell | immunis_helper_t_service | - |
| 9086 | Cytotoxic T | immunis_cytotoxic_t_service | - |
| 9087 | NK Cell | immunis_nk_cell_service | - |
| 9088 | AI Immune System | ai_immune_system | - |
| 9089 | Homeostatic Regulation | homeostatic_regulation | - |

### Infrastructure & Misc (9090-9099)
| Porta | Serviço | Container | Original |
|-------|---------|-----------|----------|
| 9090 | Prometheus | prometheus | 9090 |
| 9091 | Grafana | grafana | 3000 |
| 9092 | Atlas | atlas_service | - |
| 9093 | RTE Service | rte-service | - |
| 9094 | HPC Service | hpc-service | - |
| 9095 | Tatacá Ingestion | tataca_ingestion | - |
| 9096 | Seriema Graph | seriema_graph | - |

---

## 📝 COMANDOS PARA APLICAR

```bash
# Backup do docker-compose.yml original
cp docker-compose.yml docker-compose.yml.backup

# Aplicar novo mapeamento (será feito por script)
# ...

# Restart limpo
docker compose down
docker compose up -d

# Verificar portas
./scripts/port-manager.sh check
```

---

## ✅ VANTAGENS

1. **Zero Conflitos**: Range 9000-9099 raramente usado
2. **Fácil Debug**: Portas sequenciais, fácil de lembrar
3. **Documentação Clara**: Cada porta tem propósito definido
4. **Reversível**: Backup do docker-compose.yml original

---

## 🔄 REVERTER

```bash
# Restaurar original
cp docker-compose.yml.backup docker-compose.yml
docker compose down
docker compose up -d
```

---

**Status**: ⏳ Aguardando aplicação no docker-compose.yml
