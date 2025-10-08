# vCLI GO - UX Audit Report
**Data**: 2025-10-07
**Auditor**: Claude-Code (Executor)
**Status**: Sprint 1 - Fase 1.1

---

## 1. FLUXOS DE INTERAÇÃO ATUAIS

### 1.1 Fluxo Principal: Shell Mode
```
Usuário executa: ./bin/vcli
  ↓
Banner ASCII renderizado (VCLI GO)
  ↓
Mensagem de help (Tab/↓: Complete | /help: Help | ...)
  ↓
Prompt aparece: ┃ (barra vertical cyan)
  ↓
Usuário digita comando
  ↓
[Autocomplete NÃO está funcionando conforme esperado]
  ↓
Comando executado via Cobra
```

**Problemas identificados**:
- ❌ Prompt é apenas uma barra `┃` - não há box ao redor
- ❌ Autocomplete suggestions não aparecem ao digitar `/`
- ❌ Não há feedback visual durante loading
- ❌ Sem indicação de contexto (cluster, namespace)

### 1.2 Fluxo Alternativo: Comandos Diretos
```
Usuário executa: ./bin/vcli k8s get pods
  ↓
Banner NÃO aparece
  ↓
Comando executado diretamente
  ↓
Output renderizado
```

**Problemas identificados**:
- ✓ Funciona bem para power users
- ❌ Sem feedback de progress em operações longas

### 1.3 Fluxo de Help
```
Usuário digita: /help
  ↓
[Funcionalidade existe mas não está visível]
```

**Problemas identificados**:
- ❌ Slash commands não são descobertos facilmente
- ❌ Não há lista visual ao digitar `/`

---

## 2. INCONSISTÊNCIAS VISUAIS

### 2.1 Alinhamento
**Arquivo**: `internal/visual/banner/renderer.go`

```go
// Banner ASCII - ATUAL
asciiArt := []string{
    " ██╗   ██╗ ██████╗██╗     ██╗       ██████╗  ██████╗ ",  // 56 chars visíveis
    " ██║   ██║██╔════╝██║     ██║      ██╔════╝ ██╔═══██╗", // 56 chars
    // ... continua
}
```

**Status**: ✅ **Banner está alinhado** (6 linhas, 56 chars cada)

**Problema**:
- ❌ Help line abaixo NÃO está em box
- ❌ Autoria não está em formato consistente

### 2.2 Cores
**Arquivo**: `internal/shell/shell.go`

```go
prompt.OptionSelectedSuggestionBGColor(prompt.Cyan),     // ✓ Correto
prompt.OptionPrefixTextColor(prompt.Cyan),               // ✓ Correto
```

**Status**: ✅ **Cores consistentes** (cyan para seleções)

**Problema**:
- ❌ Não há palette centralizada
- ❌ Cores hard-coded em vários arquivos

### 2.3 Espaçamento
**Problema geral**:
- ❌ Sem grid de espaçamento definido
- ❌ Espaços entre elementos variam arbitrariamente
- ❌ Sem padding consistente em boxes

---

## 3. FUNCIONALIDADES COM MÁ DESCOBERTA

### 3.1 Command Palette (`/palette`)
**Status**: ✅ **Implementado** (`internal/palette/palette.go`)
**Problema**: ❌ **Não está integrado ao shell mode**

Evidência:
```go
// internal/shell/executor.go linha 46-49
if strings.HasPrefix(input, "/") {
    e.handleSlashCommand(input)
    return
}
```

Slash commands existem, mas:
- ❌ Não há dropdown ao digitar `/`
- ❌ Lista de comandos não aparece
- ❌ Usuário precisa **adivinhar** quais existem

### 3.2 Autocomplete de Comandos K8s
**Status**: ✅ **90+ comandos** adicionados (`internal/shell/completer.go`)
**Problema**: ❌ **Não funcionam no shell**

Análise:
```go
// completer.go - linha 52-114
c.suggestions = append(c.suggestions, []prompt.Suggest{
    {Text: "k8s get pods", Description: "List pods"},
    // ... 90+ comandos
})
```

Comandos estão lá, MAS:
- ❌ go-prompt não os mostra ao digitar
- ❌ Filtragem não funciona corretamente
- ❌ Preview de descrição não aparece

### 3.3 Workflows do Orchestrator
**Status**: ✅ **8 workflows** adicionados
**Problema**: ❌ **Zero descoberta**

Usuário não sabe que pode fazer:
- `orchestrate offensive apt-simulation`
- `orchestrate defensive threat-hunting`
- etc.

---

## 4. PONTOS DE FRICÇÃO DO USUÁRIO

### 4.1 Primeira Experiência
```
Usuário roda: ./bin/vcli
  ↓
Banner aparece (bonito, mas...)
  ↓
Prompt: ┃
  ↓
"E agora? O que eu faço?"
```

**Fricção**:
- ❌ Não há tutorial
- ❌ Não há "Try typing k8s get pods"
- ❌ Não há indicação clara de funcionalidades

### 4.2 Descoberta de Comandos
**Usuário quer**: Listar pods
**Tenta**: `get pods` ❌
**Deveria**: `k8s get pods` ✓

**Fricção**:
- ❌ Sem sugestões inteligentes
- ❌ Erro genérico "command not found"
- ❌ Sem "Did you mean?"

### 4.3 Saída do Shell
**Usuário quer**: Sair
**Tenta**: `exit` ❌ (não funciona)
**Tenta**: `quit` ❌ (não funciona)
**Precisa**: `Ctrl+D` ✓

**Fricção**:
- ❌ Comandos intuitivos não funcionam
- ❌ Sem mensagem "Type 'exit' or Ctrl+D to quit"

---

## 5. COMPONENTES EXISTENTES (Inventário)

### 5.1 Shell System
```
internal/shell/
├── shell.go         (130 linhas) - Core shell loop
├── completer.go     (211 linhas) - Autocomplete logic
└── executor.go      (293 linhas) - Command execution
```

**Status**: ✅ Funcional mas **precisa refactor**

### 5.2 Visual System
```
internal/visual/
├── colors.go        - RGBColor primitives
├── gradients.go     - Gradient rendering
├── palette.go       - Color palette
└── banner/
    └── renderer.go  - Banner rendering
```

**Status**: ✅ Bem estruturado, **precisa componentes**

### 5.3 Palette (Command Palette)
```
internal/palette/
├── palette.go       - Bubble Tea model
└── fuzzy.go         - Fuzzy matching
```

**Status**: ✅ Implementado mas **não integrado**

---

## 6. GAPS CRÍTICOS (Prioridade Alta)

| Gap | Descrição | Impacto | Fase |
|-----|-----------|---------|------|
| **Prompt Box** | Prompt é só `┃`, deveria ser box completo | Alto | 3.1 |
| **Autocomplete Broken** | Suggestions não aparecem ao digitar | Crítico | 3.2 |
| **Slash Commands Hidden** | `/` não mostra dropdown | Alto | 3.2 |
| **No Feedback Visual** | Sem spinners/progress em operações | Médio | 3.3 |
| **Palette Não Integrado** | `/palette` existe mas não funciona | Alto | 3.4 |
| **Error Messages Ruins** | Sem "did you mean?" | Médio | 5.3 |
| **No Context Awareness** | Sem statusline (cluster, namespace) | Médio | 8.1 |

---

## 7. ANÁLISE DE CÓDIGO - Arquivos Críticos

### 7.1 `internal/shell/shell.go`
**Linhas críticas**:
```go
// Linha 46: Prompt prefix - PROBLEMA
prompt.OptionPrefix("┃ "),  // Deveria ser box dinâmico

// Linha 52-59: Cores OK
prompt.OptionSelectedSuggestionBGColor(prompt.Cyan),  // ✓

// Linha 66: MaxSuggestions OK
prompt.OptionMaxSuggestion(20),  // ✓
```

**Ação necessária**: Wrapper customizado para go-prompt

### 7.2 `internal/shell/completer.go`
**Linhas críticas**:
```go
// Linha 29-36: Complete() - PROBLEMA
func (c *Completer) Complete(d prompt.Document) []prompt.Suggest {
    if d.TextBeforeCursor() == "" {
        return []prompt.Suggest{}  // ❌ Retorna vazio!
    }

    args := strings.Split(d.TextBeforeCursor(), " ")
    return prompt.FilterHasPrefix(c.suggestions, args[len(args)-1], true)
}
```

**Problema**: Lógica de filtragem muito simples
**Ação**: Implementar fuzzy matching inteligente

### 7.3 `internal/visual/banner/renderer.go`
**Status**: ✅ Código limpo e bem estruturado

**Ação necessária**: Criar `RenderMinimal()` adicional

---

## 8. COMPARAÇÃO: Estado Atual vs Esperado

| Aspecto | Atual | Esperado (gemini-cli) | Gap |
|---------|-------|----------------------|-----|
| **Prompt** | `┃ ` | Box com bordas | Alto |
| **Autocomplete** | Não funciona | Dropdown cyan | Crítico |
| **Slash commands** | Ocultos | Lista ao digitar `/` | Alto |
| **Feedback** | Nenhum | Spinner + progress | Médio |
| **Error messages** | Generic | Smart suggestions | Médio |
| **Context** | Nenhum | Statusline bottom | Baixo |

---

## 9. RECOMENDAÇÕES IMEDIATAS (Sprint 1)

### Prioridade 1 (CRÍTICO - Esta semana)
1. ✅ **Fix autocomplete** - Revisar `completer.go` linha 29-36
2. ✅ **Prompt box** - Wrapper para go-prompt com bordas
3. ✅ **Slash dropdown** - Mostrar lista ao digitar `/`

### Prioridade 2 (ALTO - Próxima semana)
4. ✅ **Integrar palette** - `/palette` funcional
5. ✅ **Feedback visual** - Spinners em operações
6. ✅ **Error messages** - "Did you mean?" inteligente

### Prioridade 3 (MÉDIO - Semana 3)
7. ✅ **Statusline** - Context awareness
8. ✅ **Keyboard shortcuts** - Documentar e testar

---

## 10. BENCHMARKING NECESSÁRIO (Fase 1.2)

Próximo documento analisará:
- [ ] gemini-cli: Como eles fazem autocomplete
- [ ] VSCode CLI: Estrutura de help
- [ ] Claude Code: Feedback visual

---

**Conclusão**:
- ✅ **Fundação sólida** (634 LOC de shell bem estruturado)
- ❌ **UX incompleta** (features existem mas não funcionam)
- ⚠️ **Gap crítico**: Autocomplete precisa funcionar URGENTE

**Próximo passo**: FASE 1.2 - Benchmark dos melhores
