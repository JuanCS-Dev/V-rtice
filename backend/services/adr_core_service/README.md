# 🛡️ ADR Core Service - Autonomous Detection & Response

## 🎨 Filosofia

**"Segurança de classe mundial não é privilégio. É direito."**

Este serviço democratiza capacidades de defesa cibernética que antes eram exclusivas de:
- Agências governamentais (NSA, CISA, FBI)
- Corporações bilionárias (Fortune 500)
- Plataformas enterprise ($100k+/ano)

Aurora ADR traz essa proteção para TODOS.

---

## 🎯 Missão

Proteger a sociedade através de:
1. **Detecção Autônoma** - Identifica ameaças em tempo real
2. **Resposta em Segundos** - Neutraliza antes de causar dano
3. **Transparência Total** - Open source, auditável, confiável
4. **Acessibilidade** - Grátis para comunidade, acessível para todos

---

## 🏗️ Arquitetura

```
ADR CORE
│
├── Detection Layer (ML-Based)
│   ├── Malware Detection Engine
│   ├── LOTL Behavior Analyzer
│   ├── Anomaly Detection
│   └── Threat Scoring
│
├── Response Layer (Autonomous)
│   ├── Playbook Engine
│   ├── Network Isolation
│   ├── Process Termination
│   └── Credential Rotation
│
└── Investigation Layer (Forensics)
    ├── Attack Path Reconstruction
    ├── IOC Extraction
    └── Impact Assessment
```

---

## 🎬 Como Começou

Aurora nasceu de uma pergunta simples:

**"Por que apenas os ricos merecem proteção de classe mundial?"**

A resposta: **Não merecem. Todos merecem.**

---

## 💪 Princípios

1. **Open Source First** - Transparência é segurança
2. **Privacy by Design** - Dados locais, controle total
3. **Community Driven** - Construído com e para a comunidade
4. **Zero Tolerance** - Zero-day, zero compromisso, zero dano

---

## 🌍 Impacto Social

Aurora ADR protege:
- 🏥 **Hospitais** (dados de pacientes)
- 🏫 **Escolas** (dados de estudantes)
- 🏛️ **Governos locais** (serviços públicos)
- 💼 **Pequenas empresas** (sobrevivência digital)
- 🏡 **Pessoas comuns** (privacidade digital)

**Pessoas que não podem pagar SentinelOne ou Darktrace.**
**Mas merecem a mesma proteção.**

---

## 🔥 Status: FASE 1 INICIADA

- [ ] ML Malware Detection Engine
- [ ] LOTL Detection System
- [ ] Autonomous Response Engine

**Data de início**: 2025-10-01
**Arquiteto**: Juan
**Equipe**: Claude (Oráculo) + Comunidade

---

## 🎨 Esta não é tecnologia. É arte.

**Arte que salva vidas.**
**Arte que protege sonhos.**
**Arte que molda a sociedade para melhor.**

Vamos começar. 🚀

---

## 📦 Dependency Management

This service follows **strict dependency governance** to ensure security, stability, and reproducibility.

### Quick Reference

**Check for vulnerabilities**:
```bash
bash scripts/dependency-audit.sh
```

**Add new dependency**:
```bash
echo "package==1.2.3" >> requirements.txt
pip-compile requirements.txt --output-file requirements.txt.lock
bash scripts/dependency-audit.sh  # Verify no CVEs
git add requirements.txt requirements.txt.lock
git commit -m "feat: add package for feature X"
```

### Policies & SLAs

📋 **[DEPENDENCY_POLICY.md](./DEPENDENCY_POLICY.md)** - Complete policy documentation

**Key SLAs**:
- **CRITICAL (CVSS >= 9.0)**: 24 hours
- **HIGH (CVSS >= 7.0)**: 72 hours
- **MEDIUM (CVSS >= 4.0)**: 2 weeks
- **LOW (CVSS < 4.0)**: 1 month

### Available Scripts

| Script | Purpose |
|--------|---------|
| `dependency-audit.sh` | Full CVE scan |
| `check-cve-whitelist.sh` | Validate whitelist |
| `audit-whitelist-expiration.sh` | Check expired CVEs |
| `generate-dependency-metrics.sh` | Generate metrics JSON |

See [Active Immune Core README](../active_immune_core/README.md#-dependency-management) for complete documentation.

