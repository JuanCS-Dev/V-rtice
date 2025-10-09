# Sistema de Validação de Contratos - Interface Charter

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Data**: 2024-10-08  
**Doutrina Vértice**: Artigo VIII - Validação Contínua

---

## Visão Geral

Sistema automatizado de validação de contratos de API da Plataforma Vértice, garantindo qualidade, consistência e aderência à Doutrina Vértice.

## Componentes

### 1. Interface Charter (`interface-charter.yaml`)
Especificação OpenAPI 3.1 unificada de todos os endpoints da plataforma.

**Localização**: `docs/contracts/interface-charter.yaml`

### 2. Endpoint Inventory (`endpoint-inventory.md`)
Inventário completo de 115+ endpoints catalogados em produção.

**Localização**: `docs/contracts/endpoint-inventory.md`

### 3. Spectral Ruleset (`spectral.yaml`)
Conjunto de regras customizadas para validação do Interface Charter.

**Localização**: `docs/cGPT/session-01/thread-a/lint/spectral.yaml`

### 4. CI/CD Workflow
Workflow automatizado no GitHub Actions para validação contínua.

**Localização**: `.github/workflows/interface-charter-validation.yml`

---

## Regras de Validação

### Regras Obrigatórias (Error)

#### Informações Básicas
- ✅ `info-contact`: Contato do responsável obrigatório
- ✅ `info-contact-name`: Nome do responsável
- ✅ `info-contact-email`: Email do responsável
- ✅ `info-description`: Descrição com mínimo 50 caracteres
- ✅ `info-version-semantic`: Versionamento semântico (x.y.z)

#### Organização
- ✅ `tags-defined`: Tags declaradas no array global
- ✅ `operation-tags`: Toda operação com pelo menos uma tag

#### Operações
- ✅ `operation-operationId`: OperationId único obrigatório
- ✅ `operation-description`: Descrição mínima de 20 caracteres
- ✅ `operation-summary`: Resumo obrigatório
- ✅ `operation-success-response`: Resposta de sucesso (2xx) obrigatória
- ✅ `response-description`: Todas as respostas com descrição

### Regras de Aviso (Warning)

#### Segurança
- ⚠️ `operation-security`: Esquemas de segurança recomendados

#### Schemas
- ⚠️ `component-schema-description`: Schemas com descrição

#### Doutrina Vértice
- ⚠️ `doutrina-vertice-marker`: Marcador `x-doutrina-vertice` presente
- ⚠️ `consciousness-project-marker`: Marcador `x-consciousness-project` presente

### Regras de Dica (Hint)

#### Observabilidade
- 💡 `x-trace-id-documented`: Header X-Trace-Id documentado

#### Documentação
- 💡 `schema-examples`: Exemplos nos schemas

---

## Uso Local

### Pré-requisitos

```bash
npm install -g @stoplight/spectral-cli
```

### Validação Manual

```bash
# Validar Interface Charter
spectral lint \
  docs/contracts/interface-charter.yaml \
  --ruleset docs/cGPT/session-01/thread-a/lint/spectral.yaml

# Validar com formato específico
spectral lint \
  docs/contracts/interface-charter.yaml \
  --ruleset docs/cGPT/session-01/thread-a/lint/spectral.yaml \
  --format pretty

# Gerar relatório JSON
spectral lint \
  docs/contracts/interface-charter.yaml \
  --ruleset docs/cGPT/session-01/thread-a/lint/spectral.yaml \
  --format json \
  --output spectral-report.json
```

### Script de Validação

Também pode usar o script bash existente:

```bash
./scripts/lint-interface-charter.sh
```

---

## CI/CD Pipeline

### Triggers

O workflow é executado automaticamente quando:

1. **Pull Request** modificando:
   - `docs/contracts/**`
   - `docs/cGPT/session-01/thread-a/lint/**`
   - `.github/workflows/interface-charter-validation.yml`

2. **Push** para `main` ou `develop` modificando os mesmos caminhos

### Jobs Executados

#### 1. `validate-charter`
- Instala Spectral CLI
- Valida estrutura OpenAPI
- Executa Spectral lint
- Verifica compliance com Doutrina Vértice
- Gera relatório e artefatos

#### 2. `validate-endpoint-inventory`
- Valida existência do inventário
- Verifica completude das seções
- Confirma informações do autor

#### 3. `validate-sync`
- Verifica sincronização entre charter e inventory
- Compara versões
- Gera sumário final

### Artefatos Gerados

- **spectral-report.txt**: Relatório completo de validação
- **Retenção**: 30 dias

### Comentários em PRs

O workflow comenta automaticamente em Pull Requests com:
- Resultados da validação Spectral
- Status de compliance
- Sugestões de correção

---

## Exemplos de Uso

### Adicionar Novo Endpoint

1. Edite `docs/contracts/interface-charter.yaml`:

```yaml
paths:
  /new/endpoint:
    post:
      summary: "Breve descrição do endpoint"
      description: "Descrição detalhada com pelo menos 20 caracteres explicando o propósito."
      operationId: createNewResource
      tags:
        - MAXIMUS-AI
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/NewResourceRequest'
      responses:
        '201':
          description: "Recurso criado com sucesso"
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/NewResourceResponse'
```

2. Execute validação local:

```bash
spectral lint docs/contracts/interface-charter.yaml \
  --ruleset docs/cGPT/session-01/thread-a/lint/spectral.yaml
```

3. Corrija erros/warnings

4. Commit e push:

```bash
git add docs/contracts/interface-charter.yaml
git commit -m "feat(api): add new endpoint for resource creation

Technical: Implements /new/endpoint POST operation
Validation: Spectral lint passed ✅
Doutrina: Compliance verified

Refs: #123"
```

### Atualizar Endpoint Existente

1. Localize o endpoint em `interface-charter.yaml`
2. Faça as alterações necessárias
3. Execute validação local
4. Atualize também `endpoint-inventory.md` se necessário
5. Commit com mensagem descritiva

---

## Tratamento de Erros

### Erro: "Missing required field 'contact'"

**Solução**: Adicione informações de contato no `info`:

```yaml
info:
  title: "API Name"
  version: "1.0.0"
  contact:
    name: Juan Carlo de Souza (JuanCS-DEV)
    email: juan.brainfarma@gmail.com
    url: https://github.com/JuanCS-DEV
```

### Erro: "Operation must have at least one success response"

**Solução**: Adicione pelo menos uma resposta 2xx:

```yaml
responses:
  '200':
    description: "Operação bem-sucedida"
```

### Warning: "Consider documenting X-Trace-Id header"

**Solução**: Adicione o header aos parâmetros:

```yaml
parameters:
  - name: X-Trace-Id
    in: header
    description: "ID único para rastreamento distribuído"
    required: true
    schema:
      type: string
      format: uuid
```

---

## Métricas de Qualidade

### Objetivos

- ✅ **0 erros** Spectral em `main`
- ✅ **< 5 warnings** por endpoint
- ✅ **100% compliance** com tags definidas
- ✅ **100% operações** com security scheme
- ✅ **100% schemas** com descrição

### Status Atual

| Métrica | Target | Atual | Status |
|---------|--------|-------|--------|
| Erros Spectral | 0 | TBD | 🔄 |
| Warnings | < 50 | TBD | 🔄 |
| Endpoints Documentados | 115+ | 115+ | ✅ |
| Compliance Doutrina | 100% | 100% | ✅ |

---

## Manutenção

### Adicionar Nova Regra Spectral

1. Edite `docs/cGPT/session-01/thread-a/lint/spectral.yaml`
2. Adicione a regra no formato:

```yaml
rules:
  rule-name:
    description: "Descrição da regra."
    message: "Mensagem de erro/aviso."
    given: "$.json.path"
    severity: error|warn|info|hint
    then:
      field: fieldName
      function: functionName
      functionOptions:
        option: value
```

3. Teste localmente
4. Commit e push

### Atualizar Tags Permitidas

Edite a regra `tags-defined` em `spectral.yaml`:

```yaml
tags-defined:
  # ...
  then:
    function: enumeration
    functionOptions:
      values:
        - MAXIMUS-AI
        - Nova-Tag
        # ... outras tags
```

---

## Referências

### Spectral
- [Documentação Oficial](https://stoplight.io/open-source/spectral)
- [Built-in Rulesets](https://docs.stoplight.io/docs/spectral/4dec24461f3af-open-api-rules)
- [Custom Functions](https://docs.stoplight.io/docs/spectral/eb68e7afd463e-custom-functions)

### OpenAPI
- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
- [OpenAPI Examples](https://github.com/OAI/OpenAPI-Specification/tree/main/examples)

### Doutrina Vértice
- `docs/.claude/DOUTRINA_VERTICE.md`
- Artigo VIII: Princípio da Validação Contínua

---

## Suporte

**Issues**: Abra uma issue no GitHub  
**Documentação**: `docs/cGPT/`  
**Contato**: juan.brainfarma@gmail.com

---

## Changelog

### v1.0.0 (2024-10-08)
- ✅ Sistema de validação implementado
- ✅ Spectral ruleset completo com 20+ regras
- ✅ CI/CD workflow automatizado
- ✅ Documentação completa

---

**"Cada linha deste código ecoará pelas eras."**  
— Doutrina Vértice, Artigo VI

---

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Doutrina Vértice**: Compliance 100% ✅
