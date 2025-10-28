# 🗺️ ROADMAP - Sistema Imunológico Adaptativo Oráculo-Eureka

**Data**: 2025-10-10
**Status**: 🟢 **ROADMAP APROVADO**
**Timeline**: 12 semanas (3 meses)
**Equipe**: 1 dev full-time (Juan) + 1 AI pair (Claude)

---

## 🎯 VISÃO GERAL

### Objetivo Final
Implementar ciclo completo Oráculo→Eureka→Crisol→HITL com MTTR < 45min e taxa de sucesso > 70%.

### Estrutura do Roadmap
- **6 Sprints** de 2 semanas cada
- Cada sprint termina com **validação funcional end-to-end**
- Entregáveis incrementais (cada sprint adiciona camada funcional)
- Métricas de sucesso claras por sprint

---

## 📅 TIMELINE DETALHADO

```
Semana 1-2  ████████░░░░░░░░░░░░  Sprint 1: Fundação Oráculo-Eureka
Semana 3-4  ░░░░░░░░████████░░░░  Sprint 2: Remediação Eureka
Semana 5-6  ░░░░░░░░░░░░░░░░████  Sprint 3: Crisol de Wargaming
Semana 7-8  ████████████████████  Sprint 4: Interface HITL
Semana 9-10 ████████████████████  Sprint 5: Otimização & Performance
Semana 11-12 ███████████████████  Sprint 6: Production Readiness
```

---

## 🏃 SPRINT 1: FUNDAÇÃO (Semanas 1-2)

### Objetivo
Estabelecer pipeline básico Oráculo→Eureka com confirmação de vulnerabilidades.

### Entregáveis

#### Oráculo Core
- [x] Integração API OSV.dev
  - Client Python com retry logic
  - Rate limiting handling
  - Parsing de schema OSV
- [x] Parser pyproject.toml
  - Uso de `tomllib` (Python 3.11+)
  - Extração de dependencies + dev-dependencies
  - Suporte a version specifiers (>=, ~=, etc)
- [x] Dependency Graph Builder
  - Walk directory tree para todos pyproject.toml
  - Construção de grafo serviço→dependências
  - Detecção de versões instaladas (via pip list)
- [x] Relevance Filter
  - Cross-reference CVE packages com grafo
  - Verificação de version ranges
  - Logging de CVEs descartados
- [x] APV Schema & Validation
  - Pydantic model para APV
  - Validação contra CVE JSON 5.1.1
  - Unit tests para schema

#### Eureka Core
- [x] APV Consumer (Kafka)
  - Setup Kafka topic: `maximus.adaptive-immunity.apv`
  - Consumer com error handling
  - Dead letter queue para falhas
- [x] ast-grep Wrapper
  - Subprocess wrapper Python
  - JSON output parsing
  - Suporte a múltiplas linguagens (Python primary)
- [x] Vulnerability Confirmation Engine
  - Extração de code signature do APV
  - Execução de ast-grep na codebase
  - Geração de ConfirmedThreat object

#### Infraestrutura
- [x] Kafka Topics Setup
  - Topic: maximus.adaptive-immunity.apv (partições: 3)
  - Topic: maximus.adaptive-immunity.patches (partições: 3)
  - Retention: 7 dias
- [x] Redis Pub/Sub
  - Canal: oraculo-events
  - Canal: eureka-events
  - TTL configurável
- [x] PostgreSQL Schema
  - Tabela: apvs (histórico de APVs)
  - Tabela: patches (histórico de patches)
  - Tabela: audit_log (auditoria completa)
  - Índices otimizados

### Testes de Validação Sprint 1

```python
# test_sprint1_e2e.py

async def test_oraculo_to_eureka_flow():
    """Test end-to-end: CVE → APV → Eureka confirmation"""
    
    # 1. Simula CVE fake para requests com TLS bypass
    fake_cve = {
        'id': 'CVE-2025-FAKE-001',
        'summary': 'TLS certificate verification bypass in requests',
        'affected': [{
            'package': {'name': 'requests', 'ecosystem': 'PyPI'},
            'ranges': [{'type': 'SEMVER', 'events': [
                {'introduced': '0'},
                {'fixed': '2.31.0'}
            ]}]
        }]
    }
    
    # 2. Oráculo processa CVE
    apv = await oraculo_engine.process_cve(fake_cve)
    
    # 3. Valida APV gerado
    assert apv is not None
    assert apv.cve_id == 'CVE-2025-FAKE-001'
    assert apv.maximus_extensions is not None
    assert apv.maximus_extensions.vulnerable_code_signature is not None
    
    # 4. Publica APV no Kafka
    await apv_publisher.publish(apv)
    
    # 5. Eureka consome e confirma
    await asyncio.sleep(2)  # Aguarda processamento
    confirmed_threats = await eureka_engine.get_confirmed_threats()
    
    # 6. Valida confirmação
    assert len(confirmed_threats) > 0
    threat = confirmed_threats[0]
    assert threat.apv.cve_id == 'CVE-2025-FAKE-001'
    assert len(threat.vulnerable_files) > 0
    
    print(f"✅ Sprint 1 E2E: {len(threat.vulnerable_files)} vulnerabilidades confirmadas")

async def test_relevance_filter():
    """Test filtro de relevância (evitar CVEs irrelevantes)"""
    
    # CVE para package não usado no MAXIMUS
    irrelevant_cve = {
        'id': 'CVE-2025-FAKE-002',
        'affected': [{'package': {'name': 'obscure-package', 'ecosystem': 'PyPI'}}]
    }
    
    apv = await oraculo_engine.process_cve(irrelevant_cve)
    
    # NÃO deve gerar APV
    assert apv is None
    
    # Log deve conter descarte
    logs = await get_oraculo_logs(since=datetime.now() - timedelta(minutes=1))
    assert any('discarded' in log.message.lower() for log in logs)
    
    print("✅ Sprint 1 Relevance Filter: CVE irrelevante descartado corretamente")
```

### Critérios de Sucesso Sprint 1
- [ ] CVE do OSV.dev ingerido e parseado com sucesso
- [ ] Dependency graph construído para ≥10 serviços MAXIMUS
- [ ] Filtro de relevância descarta ≥90% de CVEs irrelevantes
- [ ] APV gerado válido segundo schema
- [ ] Eureka recebe APV via Kafka em <5s
- [ ] ast-grep confirma vulnerabilidade em código de teste
- [ ] Todos unit tests passando (coverage ≥80%)

---

## 🏃 SPRINT 2: REMEDIAÇÃO EUREKA (Semanas 3-4)

### Objetivo
Implementar geração de contramedidas (dependency upgrade + code patch LLM-powered).

### Entregáveis

#### Eureka Strategies

**Estratégia 1: Dependency Upgrade**
- [x] Version Diff Fetcher
  - Fetch source code via PyPI/GitHub
  - Git diff entre versões
  - Parsing de CHANGELOG quando disponível
- [x] LLM Breaking Changes Analyzer
  - Prompt engineering para análise de diffs
  - Identificação de breaking changes
  - Geração de migration steps
  - Modelo: Gemini 2.5 Pro (cost-effective)
- [x] Dependency Patch Generator
  - Atualização de pyproject.toml
  - Update de lock files (requirements.txt.lock)
  - Geração de testes de compatibilidade

**Estratégia 2: Code Patch (APPATCH)**
- [x] APPATCH Prompt Builder
  - Template estruturado APPATCH
  - Few-shot examples (database de fixes conhecidos)
  - Context injection (vulnerable code + CWE + attack vector)
- [x] LLM Integration
  - Cliente Claude 3.7 Sonnet (primary)
  - Fallback para GPT-4.1 / Gemini 2.5 Pro
  - Token usage tracking
  - Confidence scoring
- [x] Code Patch Validator
  - Syntax validation (ast.parse)
  - Linting (mypy, black)
  - Security scan (bandit)
  - Reject patches com issues
- [x] Few-Shot Database
  - SQLite database: vulnerability_fixes
  - Schema: cwe_id, vulnerable_code, fixed_code, explanation
  - Seeding inicial com 50+ exemplos

**Estratégia 3: Coagulation Integration**
- [x] Attack Vector Parser
  - Extração de info do APV.attack_vector_summary
  - Identificação de vector type (HTTP, network, etc)
- [x] WAF Rule Generator
  - Template rules para mod_security / cloud WAF
  - Rule validation
  - Priority assignment
- [x] Coagulation Publisher
  - Publicação em canal Redis: coagulation-rules
  - TTL: 24h (rules são temporárias)
  - Monitoring de eficácia

#### Git Integration
- [x] Automated Branch Creation
  - Nome: `auto-remediation/{cve-id}`
  - Base: main branch
  - Protection: block direct push
- [x] Secure Patch Application
  - Apply diff via `git apply`
  - Nunca executa código gerado
  - Tratamento de conflitos
- [x] Commit Message Generator
  - Template rico com metadata
  - Inclui: CVE ID, affected services, LLM model used
  - Co-authored-by: MAXIMUS AI

### Testes de Validação Sprint 2

```python
async def test_dependency_upgrade_strategy():
    """Test upgrade inteligente de dependência"""
    
    threat = create_test_threat(
        cve_id='CVE-2024-REQUESTS',
        package='requests',
        current_version='2.28.0',
        fixed_version='2.31.0'
    )
    
    patch = await eureka_engine.generate_patch(
        threat,
        strategy='dependency_upgrade'
    )
    
    assert patch is not None
    assert patch.package == 'requests'
    assert patch.to_version == '2.31.0'
    assert len(patch.breaking_changes) >= 0  # Pode ter ou não
    assert patch.llm_analysis is not None
    
    print(f"✅ Dependency Upgrade: {patch.package} {patch.from_version}→{patch.to_version}")

async def test_code_patch_llm():
    """Test geração de code patch via LLM"""
    
    threat = create_test_threat_with_code(
        cve_id='CVE-2024-TLS-BYPASS',
        cwe_id='CWE-295',
        vulnerable_code='''
def fetch_data(url):
    response = requests.get(url, verify=False)  # VULNERABLE
    return response.json()
        ''',
        attack_vector={'type': 'mitm', 'description': 'TLS bypass'}
    )
    
    patch = await eureka_engine.generate_patch(
        threat,
        strategy='code_patch'
    )
    
    assert patch is not None
    assert 'verify=True' in patch.patched_code or 'verify=False' not in patch.patched_code
    assert is_valid_python_syntax(patch.patched_code)
    assert patch.llm_model in ['claude-3-7-sonnet', 'gpt-4-1', 'gemini-2-5-pro']
    
    print(f"✅ Code Patch LLM: {len(patch.patch_diff)} linhas modificadas")

async def test_coagulation_integration():
    """Test geração de regra WAF temporária"""
    
    threat = create_test_threat(
        cve_id='CVE-2024-XSS',
        cwe_id='CWE-79',
        attack_vector={
            'type': 'http_request',
            'method': 'POST',
            'malicious_header': 'X-Forwarded-For',
            'malicious_pattern': '<script>'
        }
    )
    
    coag_rule = await eureka_engine.generate_coagulation_rule(threat)
    
    assert coag_rule is not None
    assert coag_rule.action == 'BLOCK'
    assert 'X-Forwarded-For' in str(coag_rule.conditions)
    assert coag_rule.duration == timedelta(hours=24)
    
    # Verifica publicação
    redis_value = await redis_client.get(f'coagulation-rule:{threat.cve_id}')
    assert redis_value is not None
    
    print(f"✅ Coagulation Rule: {coag_rule.id} ativada")
```

### Critérios de Sucesso Sprint 2
- [ ] Dependency upgrade gerado com análise LLM de breaking changes
- [ ] Code patch LLM valida sintaxe Python (100% dos casos)
- [ ] Few-shot database populado com ≥50 exemplos
- [ ] Coagulation rule gerado para ≥3 tipos de attack vectors
- [ ] Git branch criado automaticamente com patch aplicado
- [ ] LLM cost tracking funcional (<$1 por patch em média)
- [ ] Todos unit tests + integration tests passando (coverage ≥85%)

---

## 🏃 SPRINT 3: CRISOL DE WARGAMING (Semanas 5-6)

### Objetivo
Implementar validação empírica via staging environment e attack simulation.

_(Roadmap continua por mais 70KB...)_

**✅ Roadmap completo em construção...**
