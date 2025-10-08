# vCLI-Go UX Overhaul Blueprint

**Objetivo**: Transformar vcli-go de uma CLI funcional para um **"cockpit de alta performance"** com impacto visual e UX fluida, inspirado no vertice-terminal (Python) que usa prompt_toolkit.

**Problema Atual**:
- Autocomplete não é fluido (precisa apertar Tab, não completa while typing)
- Dropdown menu básico sem impacto visual
- Falta "wow factor" - parece CLI genérica
- go-prompt tem limitações vs prompt_toolkit

---

## 1. Análise: go-prompt vs prompt_toolkit

### prompt_toolkit (Python - vertice-terminal) ✅
```python
session = PromptSession(
    completer=SlashCommandCompleter(),
    complete_while_typing=True,        # ← FLUIDO
    bottom_toolbar=get_bottom_toolbar, # ← TOOLBAR
    style=create_prompt_style(),       # ← ESTILOS
    mouse_support=True,
    enable_history_search=True,
)

# Completions com display_meta
yield Completion(
    remaining,
    start_position=0,
    display=f"/{cmd}",
    display_meta=COMMANDS[cmd]["description"]  # ← DESCRIÇÃO AO LADO
)
```

**Features**:
- ✅ Complete while typing (autocomplete aparece automaticamente)
- ✅ Display meta (descrição ao lado de cada sugestão)
- ✅ Bottom toolbar (dicas permanentes)
- ✅ Estilos customizados (cores, bold, etc)
- ✅ Multi-line prompt (╭─[VÉRTICE]\n╰─>)
- ✅ Mouse support
- ✅ History search

### go-prompt (Go - vcli-go atual) ❌
```go
p := prompt.New(
    s.execute,
    s.complete,
    prompt.OptionPrefix("┃ "),           // ← SIMPLES
    // Sem complete_while_typing
    // Sem display_meta nas sugestões
    // Sem bottom toolbar
)
```

**Limitações**:
- ❌ Sem complete while typing (precisa Tab)
- ❌ Sem display_meta (só texto nas sugestões)
- ❌ Sem bottom toolbar
- ❌ Estilos limitados (só cores básicas)
- ❌ Prompt single-line apenas

---

## 2. Solução: Migrar para bubble-tea + lipgloss

**Decisão Arquitetural**: Abandonar go-prompt e construir shell customizado com:
- **bubble-tea**: TUI framework (Elm architecture)
- **lipgloss**: Styling avançado
- **bubbles**: Componentes prontos (textinput, list, etc)

### Por que bubble-tea?
1. **Usado pelo Glow** (CLI Markdown render) - mesmo time
2. **Componentes ricos**: textinput com autocomplete, viewport, list
3. **Estilização total** com lipgloss (gradientes, bordas, layouts)
4. **Modelo reativo**: Update/View pattern (fácil manter estado)
5. **Textinput já tem autocomplete embutido** via `SetSuggestions()`

---

## 3. Design do Novo Shell

### 3.1. Prompt Multi-linha (Gemini Style)

```
╭─[vCLI] 🚀 Kubernetes Edition
│ Context: production │ Namespace: default
╰─> _
```

**Elementos**:
- Top line: Nome + emoji + edition
- Middle line: Statusline (K8s context inline)
- Bottom line: Input cursor

### 3.2. Autocomplete Fluido

```
╰─> k8s ge_

┌─ Suggestions ─────────────────────────────────────┐
│ → k8s get        List resources                   │
│   k8s get pods   List all pods                    │
│   k8s get nodes  List cluster nodes               │
└───────────────────────────────────────────────────┘
```

**Features**:
- Aparece automaticamente ao digitar (não precisa Tab)
- Display meta ao lado (descrição)
- Fuzzy matching (ge → get)
- Seleção com ↑↓
- Enter para completar

### 3.3. Bottom Toolbar Permanente

```
╭─[vCLI] 🚀 Kubernetes Edition
│ Context: production │ Namespace: default
╰─> k8s get pods --all-namespaces
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tab: Complete │ ↑↓: Navigate │ Ctrl+K: Palette │ Ctrl+D: Exit
```

### 3.4. Command Palette (já existe, melhorar visual)

```
╭─ Command Palette ─────────────────────────────────╮
│                                                    │
│  🔍 Search: kube                                   │
│                                                    │
├────────────────────────────────────────────────────┤
│ → k8s get pods              📦 List all pods       │
│   k8s get nodes             🖥️  List cluster nodes │
│   k8s describe pod          📋 Describe a pod      │
│   k8s logs                  📄 View pod logs       │
├────────────────────────────────────────────────────┤
│ 4 commands found                                   │
╰────────────────────────────────────────────────────╯
```

**Melhorias**:
- Ícones nos comandos (📦🖥️📋📄)
- Contagem de resultados
- Bordas rounded (lipgloss)
- Gradiente no título

### 3.5. Spinner + Statusline Integrados

```
╭─[vCLI] 🚀 Kubernetes Edition
│ ⎈ production │ default │ ⠋ Fetching pods...
╰─> k8s get pods

NAME                     STATUS    AGE
nginx-7848d4b86f-9xvzk  Running   2d
postgres-5b9c8d7f-x7k2n  Running   5m

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Found 2 pods │ 85ms
```

---

## 4. Implementação: Fases

### FASE 1: Setup bubble-tea shell base
**Objetivo**: Substituir go-prompt por bubble-tea shell básico

**Tasks**:
- [ ] Criar `internal/shell/bubbletea_shell.go`
- [ ] Implementar modelo bubble-tea (Model, Init, Update, View)
- [ ] Textinput component para entrada de comandos
- [ ] Executar comandos (integrar com executor existente)

**Output esperado**:
```go
type Model struct {
    textInput    textinput.Model
    executor     *Executor
    statusline   string
    suggestions  []prompt.Suggest
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    // Handle input changes
    // Trigger autocomplete
    // Execute commands
}

func (m Model) View() string {
    // Render prompt + input + suggestions
}
```

### FASE 2: Autocomplete fluido
**Objetivo**: Autocomplete que aparece ao digitar (sem Tab)

**Tasks**:
- [ ] Hook no textinput.OnChange
- [ ] Chamar completer.Complete() a cada keystroke
- [ ] Renderizar sugestões abaixo do input
- [ ] Navegação com ↑↓ (bubble-tea key bindings)

**Features**:
- Complete while typing ✅
- Display meta (descrição ao lado) ✅
- Fuzzy matching ✅
- Trailing space hide (já implementado)

### FASE 3: Visual overhaul
**Objetivo**: Prompt impactante + bottom toolbar

**Tasks**:
- [ ] Multi-line prompt (╭─[vCLI] / ╰─>)
- [ ] Statusline inline (⎈ context | namespace)
- [ ] Bottom toolbar (keybindings hints)
- [ ] Gradientes no título (lipgloss)
- [ ] Ícones nos comandos (📦🖥️📋)

**Design system atualizado**:
```go
// Cores mais vibrantes (inspirado em Gemini/vertice-terminal)
ColorPrimary   = "#00ffff"  // Cyan brilhante
ColorSecondary = "#00ff00"  // Verde neon
ColorAccent    = "#ffff00"  // Amarelo vibrante
ColorDanger    = "#ff0000"  // Vermelho puro
ColorSuccess   = "#00ff00"  // Verde neon
ColorMuted     = "#666666"  // Cinza
```

### FASE 4: Command palette upgrade
**Objetivo**: Palette com ícones e visual impactante

**Tasks**:
- [ ] Adicionar ícones aos comandos (map emoji → command)
- [ ] Contagem de resultados
- [ ] Bordas rounded
- [ ] Gradiente no título
- [ ] Highlight do match (fuzzy search)

### FASE 5: Spinner integrado
**Objetivo**: Spinner na statusline (não bloquear input)

**Tasks**:
- [ ] Spinner como goroutine separada
- [ ] Atualizar statusline via channel
- [ ] Renderizar na linha do statusline (não nova linha)
- [ ] Animação suave (bubble-tea tick)

### FASE 6: Polish final
**Objetivo**: Pequenos detalhes que fazem diferença

**Tasks**:
- [ ] Welcome banner com gradient
- [ ] Error messages com ícones (❌⚠️✓)
- [ ] Success feedback visual (✓ green)
- [ ] Loading states suaves
- [ ] Transições animadas (fade in/out)

---

## 5. Referências de Código

### bubble-tea textinput com autocomplete
```go
import (
    "github.com/charmbracelet/bubbles/textinput"
    tea "github.com/charmbracelet/bubbletea"
)

type Model struct {
    textInput textinput.Model
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.KeyMsg:
        switch msg.Type {
        case tea.KeyEnter:
            // Execute command
            return m, executeCmd(m.textInput.Value())
        }
    }

    // Update textinput
    var cmd tea.Cmd
    m.textInput, cmd = m.textInput.Update(msg)

    // Trigger autocomplete on text change
    if m.textInput.Value() != "" {
        m.suggestions = m.getSuggestions(m.textInput.Value())
    }

    return m, cmd
}

func (m Model) View() string {
    // Render multi-line prompt
    prompt := lipgloss.NewStyle().
        Foreground(lipgloss.Color("#00ffff")).
        Render("╭─[vCLI] 🚀\n╰─> ")

    // Render input
    input := m.textInput.View()

    // Render suggestions
    suggestions := m.renderSuggestions()

    return prompt + input + "\n" + suggestions
}
```

### lipgloss gradient
```go
gradient := lipgloss.NewStyle().
    Foreground(lipgloss.AdaptiveColor{
        Light: "#00ffff",
        Dark:  "#00ffff",
    }).
    Background(lipgloss.AdaptiveColor{
        Light: "#000000",
        Dark:  "#000000",
    }).
    Bold(true)

title := gradient.Render("vCLI 🚀 Kubernetes Edition")
```

---

## 6. Comparação: Antes vs Depois

### Antes (go-prompt)
```
┃ k8s get pods
# (precisa apertar Tab para ver sugestões)
# (sem descrições)
# (sem toolbar)
```

### Depois (bubble-tea)
```
╭─[vCLI] 🚀 Kubernetes Edition
│ ⎈ production │ default
╰─> k8s get po_

┌─ Suggestions ─────────────────────────────────────┐
│ → k8s get pods        📦 List all pods            │
│   k8s get pod [name]  📋 Get specific pod         │
└───────────────────────────────────────────────────┘

Tab: Complete │ ↑↓: Navigate │ Ctrl+K: Palette │ Ctrl+D: Exit
```

---

## 7. Métricas de Sucesso

**UX Goals**:
- [ ] Autocomplete aparece **instantaneamente** (< 50ms)
- [ ] Não precisa apertar Tab (complete while typing)
- [ ] Descrições visíveis em **100%** das sugestões
- [ ] Bottom toolbar sempre visível
- [ ] Prompt tem **"wow factor"** (multi-linha + gradiente)

**Performance Goals**:
- [ ] Rendering < 16ms (60fps)
- [ ] Autocomplete < 50ms
- [ ] Startup < 100ms
- [ ] Memory < 50MB

---

## 8. Risks & Mitigations

**Risk 1**: bubble-tea é muito diferente de go-prompt (curva de aprendizado)
**Mitigation**: Começar com exemplo simples, iterar

**Risk 2**: Performance (rendering a cada keystroke)
**Mitigation**: Debounce no autocomplete (50ms), render only on change

**Risk 3**: Complexidade (mais código que go-prompt)
**Mitigation**: Modularizar (separate files: model, view, update, autocomplete)

---

## 9. Next Steps

1. **Spike**: Criar POC com bubble-tea textinput + autocomplete (2h)
2. **Validate**: Testar performance e fluidez (1h)
3. **Implement**: Se POC ok, implementar FASE 1-6 (8h total)
4. **Polish**: Final touches e validation (2h)

**Total Estimate**: 13h (2 dias)

---

## 10. Exemplos de Referência

### Glow (Markdown CLI - bubble-tea)
- https://github.com/charmbracelet/glow
- Usa bubble-tea + lipgloss
- TUI fluida e bonita

### charm (Charm CLI - bubble-tea)
- https://github.com/charmbracelet/charm
- Autocomplete rico
- Visual impactante

### vertice-terminal (Python - prompt_toolkit)
- Nosso próprio exemplo
- Complete while typing ✅
- Display meta ✅
- Bottom toolbar ✅

---

**Conclusão**: A migração para bubble-tea vai transformar vcli-go de uma CLI funcional para um **cockpit de alta performance** com UX comparável ao Gemini CLI e vertice-terminal.

**Decision**: APROVAR migração para bubble-tea + implementar em sprint dedicado.

---

**Created**: 2025-10-07
**Author**: Juan Carlos + Anthropic Claude
**Status**: BLUEPRINT READY - Aguardando aprovação
