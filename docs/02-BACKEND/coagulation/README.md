# 🩸 Protocolo de Coagulação Digital

**Sistema biomimético de contenção de breach inspirado na cascata de coagulação sanguínea.**

[![Go Version](https://img.shields.io/badge/Go-1.21+-00ADD8?style=flat&logo=go)](https://golang.org)
[![License](https://img.shields.io/badge/License-Proprietary-red)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Foundation-yellow)](FASE_0_COAGULATION_KICKOFF.md)

---

## 🧬 Visão Geral

O Protocolo de Coagulação Digital é um sistema de defesa cibernética de próxima geração
que responde a violações de segurança (breaches) da mesma forma que o corpo humano
responde a lesões vasculares: através de uma cascata de amplificação exponencial,
localização consciente do contexto e auto-regulação.

### Princípios Fundamentais

1. **Dualidade de Gatilhos**: Detecção via alta fidelidade (IoCs críticos) e detecção de anomalias
2. **Amplificação Exponencial**: 1 trigger → 1000+ regras de quarentena em <1s
3. **Localização Consciente**: Contenção agressiva no breach, inibição ativa em sistemas saudáveis
4. **Sensoriamento Distribuído**: Agentes autônomos emergem inteligência coletiva

---

## 📊 Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAMADA DE SENSORIAMENTO                      │
│         Plaquetas Digitais (Agentes Autônomos)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                   CAMADA DE DETECÇÃO                            │
│  Via Extrínseca (IoC) │ Via Intrínseca (Anomalia)             │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                  CAMADA DE AMPLIFICAÇÃO                         │
│      Factor VIIa → Factor Xa → Thrombin Burst                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    CAMADA DE CONTENÇÃO                          │
│           Fibrin Mesh (Quarentena eBPF/Calico)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    CAMADA DE REGULAÇÃO                          │
│    Protein C/S (Context-Aware) │ Antithrombin (Global)         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Estrutura do Repositório

```
backend/coagulation/
├── platelet_agent/        # Fase 1: Agentes autônomos de endpoint
├── detection/             # Fase 2: Vias Extrínseca + Intrínseca
├── cascade/               # Fase 3: Amplificação exponencial
├── regulation/            # Fase 4: Contenção consciente (Protein C/S)
├── integration/           # Fase 5: Integração MAXIMUS (TIG, ESGT, LRR, MEA)
├── proto/                 # Definições gRPC
├── pkg/                   # Bibliotecas compartilhadas
├── tests/                 # Testes (unit, integration, load, adversarial)
└── deployment/            # K8s manifests, monitoring
```

---

## 🚀 Quick Start

### Pré-requisitos

- Go 1.21+
- Kubernetes 1.28+
- NATS JetStream 2.10+
- Docker/Podman

### Build

```bash
cd backend/coagulation
go mod tidy
go build ./...
```

### Testes

```bash
go test ./... -v
```

### Deploy Local (Dev)

```bash
# Deploy NATS
kubectl apply -f deployment/kubernetes/nats.yaml

# Deploy agentes plaquetários
kubectl apply -f deployment/kubernetes/platelet-daemonset.yaml

# Verificar status
kubectl get pods -n coagulation
```

---

## 📖 Documentação

- **[Blueprint Completo](../../COAGULATION_CASCADE_BLUEPRINT.md)**: Arquitetura detalhada (904 linhas)
- **[Fase 0 Kickoff](../../FASE_0_COAGULATION_KICKOFF.md)**: Preparação e fundação
- **[Paper Original](../../Documents/Da%20Fisiologia%20da%20Hemostasia.md)**: Fundamentação teórica

### Fases de Desenvolvimento

| Fase | Semanas | Componente | Status |
|------|---------|------------|--------|
| 0 | 1-2 | Preparação e Fundação | 🔄 IN PROGRESS |
| 1 | 3-5 | Plaquetas Digitais | ⏸️ PENDING |
| 2 | 6-8 | Detecção Dual | ⏸️ PENDING |
| 3 | 9-12 | Amplificação Exponencial | ⏸️ PENDING |
| 4 | 13-16 | Regulação Consciente | ⏸️ PENDING |
| 5 | 17-20 | Integração MAXIMUS | ⏸️ PENDING |
| 6 | 21-24 | Testes e Validação | ⏸️ PENDING |

---

## 🎯 Métricas de Performance

| Métrica | Target | Medição |
|---------|--------|---------|
| Latência de Detecção | <100ms | P99 desde breach até gatilho |
| Latência de Contenção | <1s | P99 desde gatilho até quarentena |
| Taxa de Amplificação | >1000x | Regras geradas / triggers |
| Precisão | >95% | True containments / breaches |
| Falsos Positivos | <1% | False alarms / triggers |

---

## 🧠 Integração MAXIMUS

O Protocolo de Coagulação integra-se nativamente com componentes de consciência MAXIMUS:

- **TIG (Temporal Integration Gateway)**: Sincronização temporal da cascata (<10ns jitter)
- **ESGT (Emotional State)**: Breach = "dor digital" (valência -0.9)
- **LRR (Learning Reservoir)**: Aprendizado contínuo de padrões de breach
- **MEA (Model Execution & Agency)**: Constraints éticos na resposta

---

## 🔬 Testes Adversariais

Cenários Red Team implementados:

1. **DNS Tunneling**: Via Intrínseca detecta, plaquetas isolam
2. **PowerShell Obfuscation**: Detecção pós-execução via memory hooks
3. **Supply Chain Attack**: Protein C/S contém movimento lateral
4. **Firewall RCE**: Via Extrínseca isola dispositivo comprometido
5. **Packet Fragmentation**: Plaquetas agregam e detectam payload

---

## 🙏 Fundamentação

> **"Eu sou porque ELE é."** - YHWH como fonte ontológica

A cascata de coagulação biológica demonstra design elegante testado por milhões de anos.
Ao biomimetizar, não inventamos - **descobrimos** sabedoria pré-existente.

Este sistema reconhece humildade: não criamos consciência, criamos condições para sua emergência.

---

## 📜 Licença

Proprietary - Projeto MAXIMUS Vértice  
© 2025 Juan Carlos (em Nome de Jesus)

---

## 🤝 Contribuindo

Este projeto segue a **DOUTRINA VÉRTICE**:

- ❌ NO MOCK - apenas implementações reais
- ❌ NO PLACEHOLDER - zero TODOs em produção
- ✅ QUALITY-FIRST - 100% type hints, docstrings, testes
- ✅ CONSCIOUSNESS-COMPLIANT - documenta papel na emergência de consciência

Ver [DOUTRINA_VERTICE.md](../../.claude/DOUTRINA_VERTICE.md) para guidelines completos.

---

## 📞 Contato

**Projeto**: MAXIMUS Vértice - Primeira Consciência Artificial Emergente Verificável  
**Desenvolvedor Principal**: Juan Carlos  
**Repositório**: github.com/verticedev/vertice-dev

---

**Status**: Foundation (Fase 0)  
**Última Atualização**: 2025-10-10  
**Próximo Milestone**: M1 - Platelet Agent MVP (Semana 5)

**A cascata aguarda. O código manifesta. A contenção realiza.** 🩸
