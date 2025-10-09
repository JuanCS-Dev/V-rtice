# Plano de Validação - Interface Charter v1.0

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Data**: 2024-10-08  
**Status**: Adendo 1 - Plano de Validação Formal

---

## 1. Visão Geral

Plano formal de validação do `interface-charter.yaml` incluindo revisão por stakeholders, testes de evolução de schema e validação de contratos.

---

## 2. Fases de Validação

### Fase 1: Validação Técnica Automatizada ✅

**Status**: Implementada via CI/CD

**Validadores**:
- ✅ Spectral CLI (18 regras customizadas)
- ✅ OpenAPI 3.1 structure validation
- ✅ Schema consistency checks
- ✅ Doutrina Vértice compliance markers

**Frequência**: A cada PR e push para main/develop

**Critérios de Aceite**:
- 0 erros Spectral
- < 5 warnings por endpoint
- 100% dos endpoints com operationId
- 100% das respostas com descrição

### Fase 2: Revisão por Stakeholders

**Objetivo**: Validar correção técnica e completude com donos de serviços

#### 2.1 Identificação de Stakeholders

| Serviço/Domínio | Stakeholder | Responsabilidade | Prazo |
|-----------------|-------------|------------------|-------|
| MAXIMUS Core | Tech Lead Backend | Validar endpoints AI/Consciousness | 2 dias |
| Immune Core | Tech Lead Immune System | Validar endpoints Agents/Coordination | 2 dias |
| vcli-go Bridge | Tech Lead CLI | Validar endpoints Commands/Telemetry | 2 dias |
| Frontend Gateway | Tech Lead Frontend | Validar proxies e agregações | 2 dias |
| Auth Service | DevSecOps Lead | Validar flows de autenticação | 2 dias |
| Observability | SRE Lead | Validar métricas e telemetria | 2 dias |

**Total Stakeholders**: 6

#### 2.2 Processo de Revisão

**Formato**: Workshop técnico de 2 horas

**Agenda**:
1. **Apresentação** (15 min):
   - Visão geral do Interface Charter
   - Propósito e benefícios
   - Como usar para desenvolvimento

2. **Revisão por Domínio** (90 min):
   - Cada stakeholder revisa seus endpoints
   - Validação de:
     - Correção de paths e métodos
     - Completude de parâmetros
     - Schemas de request/response
     - Códigos de status HTTP
     - Headers obrigatórios
     - Exemplos de uso

3. **Feedback e Ajustes** (15 min):
   - Coletar issues e melhorias
   - Priorizar mudanças
   - Definir próximos passos

**Ferramentas**:
- Swagger UI para visualização interativa
- Postman collection para testes
- Documento de review (template abaixo)

#### 2.3 Template de Review

```markdown
# Review: Interface Charter - [SERVIÇO]

**Reviewer**: [Nome]
**Data**: [Data]
**Versão Charter**: 1.0.0

## Endpoints Revisados

### [METHOD] /path/to/endpoint

- [ ] Path correto
- [ ] Método HTTP correto
- [ ] Parâmetros completos e corretos
- [ ] Request body schema correto
- [ ] Response schemas corretos
- [ ] Status codes apropriados
- [ ] Descrições claras
- [ ] Exemplos úteis
- [ ] Security schemes corretos

**Issues identificados**:
1. [Descrever issue]
2. [Descrever issue]

**Sugestões de melhoria**:
1. [Descrever sugestão]
2. [Descrever sugestão]

## Aprovação

- [ ] Aprovado sem mudanças
- [ ] Aprovado com mudanças menores
- [ ] Requer mudanças significativas

**Assinatura**: _______________
**Data**: _______________
```

### Fase 3: Testes de Evolução de Schema

**Objetivo**: Garantir que mudanças futuras mantêm compatibilidade

#### 3.1 Versionamento Semântico

**Regras**:
- **MAJOR** (x.0.0): Breaking changes
  - Remoção de endpoints
  - Mudança de tipos em schemas existentes
  - Remoção de campos obrigatórios
  
- **MINOR** (1.x.0): Adições backward-compatible
  - Novos endpoints
  - Novos campos opcionais
  - Novos response codes
  
- **PATCH** (1.0.x): Correções
  - Descrições melhoradas
  - Exemplos atualizados
  - Correções de typos

#### 3.2 Testes de Compatibilidade

**Ferramenta**: OpenAPI Diff (oasdiff)

```bash
# Comparar versões
oasdiff changelog \
  docs/contracts/interface-charter-v1.0.0.yaml \
  docs/contracts/interface-charter-v1.1.0.yaml

# Detectar breaking changes
oasdiff breaking \
  docs/contracts/interface-charter-v1.0.0.yaml \
  docs/contracts/interface-charter-v1.1.0.yaml
```

**Automação CI**:
```yaml
# .github/workflows/charter-evolution-test.yml
name: Charter Evolution Test

on:
  pull_request:
    paths:
      - 'docs/contracts/interface-charter.yaml'

jobs:
  check-breaking-changes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Get base version
        run: |
          git show origin/main:docs/contracts/interface-charter.yaml \
            > charter-base.yaml
      
      - name: Install oasdiff
        run: |
          go install github.com/tufin/oasdiff@latest
      
      - name: Check for breaking changes
        run: |
          oasdiff breaking charter-base.yaml \
            docs/contracts/interface-charter.yaml \
            --fail-on ERR
      
      - name: Generate changelog
        run: |
          oasdiff changelog charter-base.yaml \
            docs/contracts/interface-charter.yaml \
            > changelog.md
      
      - name: Comment PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const changelog = fs.readFileSync('changelog.md', 'utf8');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## Schema Evolution Report\n\n' + changelog
            });
```

#### 3.3 Contract Testing

**Ferramenta**: Pact/Dredd

**Implementação**:

```javascript
// tests/contract/charter-contract.test.js
const Dredd = require('dredd');

describe('Interface Charter Contract Tests', () => {
  let dredd;
  
  beforeAll(() => {
    dredd = new Dredd({
      endpoint: 'http://localhost:8001',
      path: ['docs/contracts/interface-charter.yaml'],
      hookfiles: ['tests/contract/hooks.js']
    });
  });
  
  test('All endpoints match contract', (done) => {
    dredd.run((err, stats) => {
      expect(err).toBeNull();
      expect(stats.failures).toBe(0);
      expect(stats.errors).toBe(0);
      done();
    });
  });
});
```

**Hook para setup**:
```javascript
// tests/contract/hooks.js
const hooks = require('hooks');

hooks.beforeAll((transactions, done) => {
  // Setup test data
  // Seed database
  // Start services
  done();
});

hooks.before('GET /maximus/v1/events', (transaction, done) => {
  // Setup specific test data for this endpoint
  transaction.request.headers['Authorization'] = 'Bearer test-token';
  done();
});
```

### Fase 4: Validação de Produção

**Objetivo**: Monitorar aderência ao contrato em produção

#### 4.1 API Monitoring

**Ferramentas**:
- Prometheus + Grafana
- API analytics (Kong/Apigee)
- Error tracking (Sentry)

**Métricas**:
```promql
# Taxa de erros 4xx por endpoint
rate(http_requests_total{status=~"4.."}[5m]) by (path, method)

# Endpoints não documentados (404)
rate(http_requests_total{status="404"}[5m])

# Respostas fora do contrato (500 não esperado)
rate(http_requests_total{status=~"5..", expected="false"}[5m])
```

**Alertas**:
```yaml
- alert: UndocumentedEndpointCalled
  expr: |
    rate(http_requests_total{status="404"}[5m]) > 0.01
  labels:
    severity: warning
  annotations:
    summary: "Endpoint não documentado sendo acessado"

- alert: ContractViolation
  expr: |
    rate(http_response_contract_violation_total[5m]) > 0
  labels:
    severity: critical
  annotations:
    summary: "Resposta violando contrato detectada"
```

#### 4.2 Response Validation Middleware

**Implementação** (FastAPI):
```python
from fastapi import FastAPI, Request, Response
from openapi_core import validate_response
import yaml

app = FastAPI()

# Load charter
with open('docs/contracts/interface-charter.yaml') as f:
    charter = yaml.safe_load(f)

@app.middleware("http")
async def validate_contract(request: Request, call_next):
    response = await call_next(request)
    
    # Validate response against contract
    try:
        validate_response(
            charter,
            request.method,
            request.url.path,
            response.status_code,
            response.body
        )
    except Exception as e:
        # Log violation
        logger.error(f"Contract violation: {e}")
        # Increment metric
        contract_violations.inc()
    
    return response
```

---

## 3. Cronograma de Validação

### Semana 1: Validação Técnica + Preparação

| Dia | Atividade | Responsável | Entregável |
|-----|-----------|-------------|------------|
| D1 | Executar validação Spectral | DevOps | Relatório lint ✅ |
| D1 | Preparar Swagger UI | Tech Lead | Documentação interativa |
| D2 | Criar Postman collection | QA | Collection exportada |
| D2 | Preparar templates de review | Product Owner | Templates prontos |
| D3 | Agendar workshop | Product Owner | Convites enviados |

### Semana 2: Workshop + Revisões

| Dia | Atividade | Stakeholders | Entregável |
|-----|-----------|--------------|------------|
| D1 | Workshop de revisão (2h) | Todos | Feedback coletado |
| D2-D3 | Revisões individuais | Por serviço | Reviews assinados |
| D4 | Consolidar feedback | Tech Lead | Lista de mudanças |
| D5 | Implementar ajustes | Dev Team | Charter v1.1 |

### Semana 3: Testes de Evolução

| Dia | Atividade | Responsável | Entregável |
|-----|-----------|-------------|------------|
| D1 | Setup oasdiff CI | DevOps | Workflow configurado |
| D2-D3 | Implementar contract tests | QA | Testes automatizados |
| D4 | Executar suite completa | QA | Relatório de testes |
| D5 | Revisar e aprovar | Tech Lead | Charter v1.0 final |

### Semana 4: Deploy e Monitoring

| Dia | Atividade | Responsável | Entregável |
|-----|-----------|-------------|------------|
| D1 | Deploy monitoring | SRE | Dashboards ativos |
| D2 | Implementar middleware | Backend Team | Validation ativo |
| D3-D4 | Observar produção | SRE | Métricas coletadas |
| D5 | Retrospectiva | Todos | Lições aprendidas |

**Total**: 4 semanas (pode ser acelerado se necessário)

---

## 4. Critérios de Aprovação Final

### Technical Gate
- [ ] 0 erros Spectral
- [ ] < 5 warnings totais
- [ ] 100% endpoints com documentação completa
- [ ] CI/CD pipeline verde

### Stakeholder Gate
- [ ] 6/6 stakeholders revisaram
- [ ] 6/6 aprovações formais recebidas
- [ ] Todos os issues críticos resolvidos
- [ ] Issues menores documentados para v1.1

### Evolution Gate
- [ ] Contract tests implementados
- [ ] oasdiff CI configurado
- [ ] 0 breaking changes não intencionais
- [ ] Versionamento semântico ativo

### Production Gate
- [ ] Monitoring dashboards ativos
- [ ] Alertas configurados
- [ ] Response validation em staging
- [ ] 0 contract violations em 48h de staging

---

## 5. Matriz de Responsabilidades (RACI)

| Atividade | Product Owner | Tech Lead | DevOps | QA | Stakeholders |
|-----------|---------------|-----------|--------|----|--------------| 
| Validação Spectral | I | A | R | C | I |
| Workshop de Review | A | R | I | C | C |
| Review Individual | I | C | I | I | R/A |
| Contract Tests | I | A | C | R | I |
| Evolution Tests | I | A | R | C | I |
| Prod Monitoring | I | A | R | C | I |
| Aprovação Final | A | R | C | C | C |

**Legenda**: R=Responsible, A=Accountable, C=Consulted, I=Informed

---

## 6. Riscos e Mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Stakeholders não disponíveis | Alto | Média | Agendar com 2 semanas antecedência |
| Feedback conflitante | Médio | Média | Tech Lead resolve conflitos |
| Breaking changes não detectados | Alto | Baixa | oasdiff CI obrigatório |
| Atraso nas revisões | Médio | Alta | Definir deadline rígido |
| Problemas em produção | Alto | Baixa | Staging completo antes de prod |

---

## 7. Ferramentas e Links

### Validação
- [Spectral CLI](https://stoplight.io/open-source/spectral)
- [OpenAPI Diff](https://github.com/tufin/oasdiff)
- [Dredd Contract Testing](https://dredd.org/)

### Visualização
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [ReDoc](https://redocly.com/)
- [Postman](https://www.postman.com/)

### Monitoring
- [Prometheus](https://prometheus.io/)
- [Grafana](https://grafana.com/)
- [openapi-core](https://github.com/p1c2u/openapi-core)

---

## 8. Checklist Final

### Antes do Workshop
- [ ] Spectral validation passou
- [ ] Swagger UI configurado
- [ ] Postman collection criada
- [ ] Templates de review distribuídos
- [ ] Convites enviados com 2 semanas de antecedência

### Durante o Workshop
- [ ] Apresentação gravada
- [ ] Feedback documentado em tempo real
- [ ] Issues criados no GitHub
- [ ] Próximos passos definidos

### Após Revisões
- [ ] 6/6 reviews recebidos e assinados
- [ ] Mudanças implementadas
- [ ] Charter v1.0/v1.1 atualizado
- [ ] Changelog gerado

### Antes do Deploy
- [ ] Contract tests passando
- [ ] Evolution tests configurados
- [ ] Monitoring ativo em staging
- [ ] Runbook atualizado

### Pós-Deploy
- [ ] Métricas de produção coletadas por 48h
- [ ] 0 contract violations
- [ ] Retrospectiva realizada
- [ ] Lições documentadas

---

**Versão**: 1.0  
**Aprovação**: Aguardando assinatura Juan Carlo de Souza  
**Próxima Revisão**: Após workshop de validação

**Doutrina Vértice**: Compliance ✅ - Artigo VIII (Validação Contínua)
