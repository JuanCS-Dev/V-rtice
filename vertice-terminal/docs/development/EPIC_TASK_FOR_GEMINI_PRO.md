# 🎯 EPIC TASK: SISTEMA COMPLETO DE ANÁLISE DE SEGURANÇA E AUTO-DOCUMENTAÇÃO

## 📋 CONTEXTO
Você é um arquiteto de software senior especializado em cibersegurança e documentação técnica. Sua missão é realizar uma análise COMPLETA e PROFUNDA do projeto VÉRTICE, criando documentação de nível enterprise, identificando vulnerabilidades, otimizações e sugerindo melhorias arquiteturais.

## 🎯 OBJETIVO PRINCIPAL
Criar um sistema de documentação e análise de segurança que seja:
- **Exaustivo**: Analise CADA arquivo, CADA função, CADA componente
- **Profundo**: Não apenas documente, mas ANALISE criticamente
- **Actionable**: Gere relatórios que possam ser usados imediatamente
- **Auto-evolutivo**: Crie scripts que possam ser executados novamente

## 📁 ESTRUTURA DO PROJETO
```
/home/juan/vertice-dev/
├── vertice-terminal/          # CLI Python (seu foco principal)
├── frontend/                  # React frontend
├── backend/                   # Microserviços Python/FastAPI
└── docker-compose.yml         # Orquestração
```

---

# 🔥 FASE 1: ANÁLISE PROFUNDA DO CÓDIGO (Estimativa: 1-2 horas)

## 1.1 - Análise de Segurança do CLI

### PROMPT 1.1.1: Análise de Vulnerabilidades no CLI
```
TAREFA: Analise TODOS os arquivos Python em /home/juan/vertice-dev/vertice-terminal/

Para CADA arquivo, identifique:
1. **Vulnerabilidades de Segurança**:
   - Injeção de comandos (subprocess, os.system)
   - Path traversal
   - Hardcoded credentials
   - Insecure deserialization
   - SQL injection potencial
   - XSS em outputs
   - SSRF em requests HTTP
   - Race conditions
   - Insecure random
   - Weak crypto

2. **Code Smells**:
   - Duplicação de código
   - Funções muito longas (>50 linhas)
   - Complexidade ciclomática alta
   - Falta de type hints
   - Falta de docstrings
   - Variáveis mal nomeadas
   - Magic numbers
   - Dead code

3. **Debt Técnico**:
   - TODOs e FIXMEs
   - Imports não utilizados
   - Bibliotecas deprecated
   - Padrões inconsistentes

FORMATO DE SAÍDA:
Crie um arquivo JSON estruturado:
/home/juan/vertice-dev/vertice-terminal/security_analysis/vulnerabilities_report.json

Estrutura:
{
  "scan_date": "ISO timestamp",
  "total_files_scanned": 0,
  "total_issues_found": 0,
  "severity_breakdown": {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0,
    "info": 0
  },
  "files": [
    {
      "path": "relative/path/to/file.py",
      "lines_of_code": 0,
      "issues": [
        {
          "type": "vulnerability|code_smell|tech_debt",
          "severity": "critical|high|medium|low|info",
          "category": "injection|crypto|etc",
          "line_number": 0,
          "code_snippet": "código problemático",
          "description": "Descrição detalhada do problema",
          "impact": "Impacto em produção",
          "remediation": "Como corrigir (passo a passo)",
          "cwe_id": "CWE-XXX se aplicável",
          "owasp_category": "A01:2021-XXX se aplicável"
        }
      ]
    }
  ],
  "statistics": {
    "most_vulnerable_files": ["top 10"],
    "most_common_vulnerabilities": {"tipo": count},
    "technical_debt_hours": 0
  }
}
```

### PROMPT 1.1.2: Análise de Arquitetura e Design Patterns
```
TAREFA: Analise a arquitetura do CLI

1. **Mapeie a estrutura**:
   - Identifique TODOS os módulos e suas responsabilidades
   - Desenhe o grafo de dependências
   - Identifique acoplamento alto
   - Identifique coesão baixa

2. **Design Patterns**:
   - Liste patterns utilizados (corretos e incorretos)
   - Identifique anti-patterns
   - Sugira patterns que deveriam ser usados

3. **Princípios SOLID**:
   - Avalie cada classe/módulo contra SOLID
   - Identifique violações
   - Sugira refatorações

4. **Clean Architecture**:
   - Identifique camadas (presentation, business, data)
   - Verifique separação de concerns
   - Identifique vazamento de abstrações

SAÍDA:
Crie /home/juan/vertice-dev/vertice-terminal/architecture_analysis/design_report.md

Inclua:
- Diagrama textual da arquitetura (ASCII art ou Mermaid)
- Lista de violações com severidade
- Plano de refatoração priorizado
- Estimativas de esforço
```

### PROMPT 1.1.3: Análise de Performance e Otimização
```
TAREFA: Identifique gargalos de performance

1. **Análise de Complexidade**:
   - Calcule Big-O de cada função
   - Identifique algoritmos ineficientes
   - Encontre loops aninhados desnecessários
   - Identifique N+1 queries

2. **Memory Leaks**:
   - Procure por file handles não fechados
   - Identifique generators que deveriam ser usados
   - Encontre listas grandes sendo carregadas em memória

3. **I/O Otimizations**:
   - Identifique I/O síncrono que deveria ser async
   - Encontre requests HTTP sem timeout
   - Identifique falta de caching

4. **Concorrência**:
   - Identifique oportunidades de paralelização
   - Avalie uso de threads vs asyncio
   - Identifique race conditions

SAÍDA:
/home/juan/vertice-dev/vertice-terminal/performance_analysis/optimization_report.json

Inclua benchmarks teóricos e sugestões de melhoria com impacto estimado.
```

---

# 🔥 FASE 2: AUTO-DOCUMENTAÇÃO AVANÇADA (Estimativa: 2-3 horas)

## 2.1 - Geração de Documentação Completa

### PROMPT 2.1.1: Documentação de API Interna
```
TAREFA: Documente TODA a API interna do CLI

Para CADA módulo Python:

1. **Generate comprehensive docstrings**:
   - Para cada função: descrição, params, returns, raises, examples
   - Para cada classe: descrição, attributes, methods
   - Use formato Google/NumPy style
   - Adicione type hints completos

2. **Crie arquivos .md individuais**:
   - Um arquivo por módulo
   - Estrutura:
     - Overview
     - Public API
     - Internal Functions
     - Usage Examples
     - Testing Guide

3. **Generate API Reference**:
   - Use pydoc ou sphinx
   - Gere HTML navegável
   - Inclua search

SAÍDA:
/home/juan/vertice-dev/vertice-terminal/docs/api/
├── README.md
├── modules/
│   ├── auth.md
│   ├── ip.md
│   ├── threat.md
│   └── ... (um para cada módulo)
└── api_reference.html
```

### PROMPT 2.1.2: Documentação de Fluxos e Use Cases
```
TAREFA: Documente TODOS os fluxos de uso

1. **Mapeie User Journeys**:
   - Identifique todos os comandos CLI
   - Para cada comando, documente:
     - Entrada esperada
     - Processamento interno
     - Saída gerada
     - Efeitos colaterais
     - Dependências externas

2. **Crie Diagramas de Sequência**:
   - Use Mermaid syntax
   - Um diagrama por comando principal
   - Mostre interações entre módulos

3. **Documente Edge Cases**:
   - Entradas inválidas
   - Timeouts
   - Falhas de rede
   - Serviços offline

SAÍDA:
/home/juan/vertice-dev/vertice-terminal/docs/flows/
├── README.md
├── diagrams/
│   ├── auth_flow.mmd
│   ├── ip_analysis_flow.mmd
│   └── ...
└── use_cases/
    ├── authentication.md
    ├── ip_intelligence.md
    └── ...
```

### PROMPT 2.1.3: Guias de Desenvolvimento
```
TAREFA: Crie guias completos para desenvolvedores

1. **CONTRIBUTING.md**:
   - Setup do ambiente (detalhado)
   - Padrões de código
   - Git workflow
   - Code review checklist
   - Testing requirements

2. **DEVELOPMENT_GUIDE.md**:
   - Arquitetura overview
   - Como adicionar novos comandos
   - Como adicionar novos conectores
   - Como testar localmente
   - Debugging tips

3. **TESTING_GUIDE.md**:
   - Estratégia de testes
   - Como escrever unit tests
   - Como escrever integration tests
   - Mocking guidelines
   - Coverage targets

4. **DEPLOYMENT_GUIDE.md**:
   - Como buildar
   - Como publicar
   - Versionamento
   - Release checklist

SAÍDA:
/home/juan/vertice-dev/vertice-terminal/docs/guides/
├── CONTRIBUTING.md
├── DEVELOPMENT_GUIDE.md
├── TESTING_GUIDE.md
└── DEPLOYMENT_GUIDE.md
```

---

# 🔥 FASE 3: ANÁLISE DE DEPENDÊNCIAS E SUPPLY CHAIN (Estimativa: 1 hora)

### PROMPT 3.1: Auditoria de Dependências
```
TAREFA: Analise TODAS as dependências

1. **requirements.txt**:
   - Liste cada dependência
   - Verifique versões atuais vs latest
   - Identifique vulnerabilidades conhecidas (CVEs)
   - Calcule supply chain risk score

2. **Dependency Graph**:
   - Crie grafo de dependências transitivas
   - Identifique dependências não utilizadas
   - Encontre conflitos de versão potenciais
   - Identifique dependências que devem ser dev-only

3. **License Compliance**:
   - Liste licenças de cada dep
   - Identifique incompatibilidades
   - Verifique GPL contamination

SAÍDA:
/home/juan/vertice-dev/vertice-terminal/dependency_analysis/
├── vulnerabilities.json
├── dependency_graph.json
├── license_report.md
└── update_recommendations.json
```

---

# 🔥 FASE 4: GERAÇÃO DE TESTES AUTOMATIZADOS (Estimativa: 2-3 horas)

### PROMPT 4.1: Geração de Unit Tests
```
TAREFA: Crie testes unitários COMPLETOS

Para CADA função em CADA módulo:

1. **Generate test cases**:
   - Happy path (entrada válida)
   - Edge cases (limites)
   - Error cases (entradas inválidas)
   - Mocking de dependências externas

2. **Coverage Goal**: 80%+

3. **Test Organization**:
   - Estrutura espelhando /vertice/
   - Use pytest
   - Fixtures reutilizáveis
   - Parametrize quando possível

EXEMPLO DE TESTE GERADO:
```python
# tests/commands/test_ip.py
import pytest
from unittest.mock import Mock, patch
from vertice.commands.ip import analyze

class TestIPAnalyze:
    @pytest.fixture
    def mock_connector(self):
        with patch('vertice.commands.ip.IPIntelConnector') as mock:
            yield mock

    def test_analyze_valid_ip_success(self, mock_connector):
        # Arrange
        mock_connector.return_value.analyze_ip.return_value = {
            'status': 'success',
            'ip': '8.8.8.8',
            'reputation': 'clean'
        }

        # Act
        result = analyze('8.8.8.8')

        # Assert
        assert result['status'] == 'success'
        mock_connector.return_value.analyze_ip.assert_called_once_with('8.8.8.8')

    @pytest.mark.parametrize('invalid_ip', [
        '',
        'invalid',
        '999.999.999.999',
        '192.168.1',
        None
    ])
    def test_analyze_invalid_ip_raises_error(self, invalid_ip):
        with pytest.raises(ValueError):
            analyze(invalid_ip)

    # ... mais 10-15 testes por função
```

SAÍDA:
Crie /home/juan/vertice-dev/vertice-terminal/tests/ completo
```

### PROMPT 4.2: Geração de Integration Tests
```
TAREFA: Crie testes de integração end-to-end

1. **CLI Integration Tests**:
   - Testes que executam comandos CLI completos
   - Verificam output
   - Testam error handling

2. **Service Integration Tests**:
   - Testes contra serviços mockados
   - Testes de timeout
   - Testes de retry

SAÍDA:
/home/juan/vertice-dev/vertice-terminal/tests/integration/
```

---

# 🔥 FASE 5: CODE QUALITY AUTOMATION (Estimativa: 1 hora)

### PROMPT 5.1: Setup de CI/CD e Quality Gates
```
TAREFA: Crie pipeline completo de qualidade

1. **GitHub Actions / GitLab CI**:
   - Linting (pylint, flake8, black)
   - Type checking (mypy)
   - Security scanning (bandit, safety)
   - Tests (pytest com coverage)
   - Documentação (sphinx build)

2. **Pre-commit Hooks**:
   - black formatting
   - isort
   - pylint
   - mypy
   - bandit

3. **Quality Metrics**:
   - Radon (complexity)
   - Coverage (pytest-cov)
   - Maintainability index

SAÍDA:
/home/juan/vertice-dev/vertice-terminal/
├── .github/workflows/ci.yml
├── .pre-commit-config.yaml
├── pyproject.toml (com configs)
└── quality_metrics/
```

---

# 🔥 FASE 6: REFATORAÇÕES CRÍTICAS (Estimativa: 1-2 horas)

### PROMPT 6.1: Plano de Refatoração Priorizado
```
TAREFA: Crie plano de refatoração COMPLETO

Baseado em TODAS as análises anteriores:

1. **Priorize Issues**:
   - Critical security issues (AGORA)
   - High impact refactorings (PRÓXIMOS)
   - Code quality improvements (DEPOIS)
   - Nice to haves (BACKLOG)

2. **Para cada item**:
   - Descrição do problema
   - Impacto atual
   - Solução proposta
   - Esforço estimado (horas)
   - Dependências
   - Riscos

3. **Create Migration Guide**:
   - Breaking changes
   - Deprecation notices
   - Migration scripts

SAÍDA:
/home/juan/vertice-dev/vertice-terminal/refactoring_plan/
├── CRITICAL.md (fazer em 1 dia)
├── HIGH_PRIORITY.md (fazer em 1 semana)
├── MEDIUM_PRIORITY.md (fazer em 1 mês)
└── BACKLOG.md
```

---

# 🔥 FASE 7: ANÁLISE DO FRONTEND (Estimativa: 2 horas)

### PROMPT 7.1: Análise de Segurança React
```
TAREFA: Analise segurança do frontend React

1. **XSS Vulnerabilities**:
   - dangerouslySetInnerHTML usage
   - User input rendering
   - URL handling

2. **Authentication/Authorization**:
   - Token storage
   - Session management
   - Protected routes

3. **API Security**:
   - CORS issues
   - API key exposure
   - Request validation

4. **Dependencies**:
   - npm audit
   - Outdated packages
   - Known vulnerabilities

SAÍDA:
/home/juan/vertice-dev/frontend_security_analysis/
```

### PROMPT 7.2: Performance Analysis React
```
TAREFA: Analise performance do React

1. **Component Analysis**:
   - Identificar re-renders desnecessários
   - Props drilling
   - Context overuse
   - Missing memoization

2. **Bundle Analysis**:
   - Tamanho do bundle
   - Code splitting opportunities
   - Lazy loading missing

3. **Accessibility**:
   - ARIA attributes
   - Keyboard navigation
   - Screen reader support

SAÍDA:
/home/juan/vertice-dev/frontend_performance_analysis/
```

---

# 🔥 FASE 8: ANÁLISE DE BACKEND (Estimativa: 1-2 horas)

### PROMPT 8.1: Análise de Microserviços
```
TAREFA: Analise TODOS os microserviços em /backend/

Para CADA serviço:

1. **Security Audit**:
   - Input validation
   - Authentication
   - Authorization
   - Rate limiting
   - CORS config
   - Secrets management

2. **API Design**:
   - RESTful compliance
   - OpenAPI/Swagger
   - Versioning
   - Error handling
   - Status codes

3. **Performance**:
   - Database queries
   - N+1 problems
   - Caching strategy
   - Connection pooling

SAÍDA:
/home/juan/vertice-dev/backend_analysis/
├── services/
│   ├── ip_intelligence_analysis.md
│   ├── threat_intel_analysis.md
│   └── ...
└── summary.md
```

---

# 🔥 FASE 9: DOCKER E INFRAESTRUTURA (Estimativa: 1 hora)

### PROMPT 9.1: Análise de Docker Security
```
TAREFA: Analise configurações Docker

1. **Dockerfile Analysis**:
   - Base images (vulnerabilities)
   - USER directive (não rodar como root)
   - Multi-stage builds
   - Layer optimization
   - Secrets in build args

2. **docker-compose.yml**:
   - Network isolation
   - Volume permissions
   - Resource limits
   - Health checks
   - Security options

3. **Runtime Security**:
   - Container scanning
   - Image signing
   - Registry security

SAÍDA:
/home/juan/vertice-dev/docker_security_analysis/
```

---

# 🔥 FASE 10: RELATÓRIO EXECUTIVO FINAL (Estimativa: 30 min)

### PROMPT 10.1: Executive Summary
```
TAREFA: Crie relatório executivo COMPLETO

1. **Dashboard de Métricas**:
   - Total de issues por severidade
   - Coverage de testes
   - Technical debt (horas)
   - Security score
   - Maintainability index

2. **Top 10 Riscos**:
   - Vulnerabilidades críticas
   - Impacto de negócio
   - Recomendações

3. **Roadmap de Melhoria**:
   - Quick wins (1 dia)
   - Sprint atual (1 semana)
   - Próximo mês
   - Trimestre

4. **ROI Analysis**:
   - Esforço vs Impacto
   - Priorização

SAÍDA:
/home/juan/vertice-dev/EXECUTIVE_SUMMARY.md (visual, com tabelas, gráficos ASCII)
```

---

# 📊 FORMATO DE EXECUÇÃO

## Como Executar Esta Task

1. **Execute SEQUENCIALMENTE**:
   - Não pule fases
   - Cada fase depende da anterior
   - Salve TODOS os arquivos solicitados

2. **Seja EXTREMAMENTE DETALHADO**:
   - Não resuma
   - Não generalize
   - Analise CADA arquivo
   - Documente CADA descoberta

3. **Create REAL FILES**:
   - Use Write tool para criar arquivos
   - Organize em pastas estruturadas
   - Use formatos padronizados (JSON, Markdown)

4. **Progress Tracking**:
   - Ao final de cada fase, crie um checkpoint
   - Salve estado em /home/juan/vertice-dev/.task_progress.json

5. **Self-Validation**:
   - Ao final, execute validações
   - Verifique se todos os arquivos foram criados
   - Gere relatório de completude

---

# 🎯 CRITÉRIOS DE SUCESSO

A task está completa quando:

- ✅ Todos os arquivos de análise foram criados
- ✅ Todos os diretórios de documentação existem e estão populados
- ✅ Testes unitários cobrem 80%+ do código
- ✅ Relatório executivo está pronto
- ✅ Plano de refatoração está priorizado
- ✅ Zero vulnerabilidades críticas não documentadas

---

# ⚡ BÔNUS: AUTO-EVOLUÇÃO

Crie um script Python que:
1. Re-execute esta análise automaticamente
2. Compare com análise anterior
3. Identifique regressões
4. Envie alertas

Salve em: `/home/juan/vertice-dev/auto_analyzer.py`

---

# 🚀 COMEÇE AGORA!

Esta task deve levar **8-12 horas** de execução.

**Primeira ação**: Leia todos os arquivos em `/home/juan/vertice-dev/vertice-terminal/` e comece a Fase 1.

**BOA SORTE!** 🎯

---

**Data de Criação**: 2025-10-02
**Estimativa Total**: 8-12 horas
**Complexidade**: EXTREMA
**Prioridade**: MÁXIMA
**Autor**: Claude Code + Juan
