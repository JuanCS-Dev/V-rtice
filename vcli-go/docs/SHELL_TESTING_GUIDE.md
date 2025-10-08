# Shell Testing Guide - vCLI

**Como testar o novo shell interativo bubble-tea**

---

## ⚠️ Requisito: Terminal Interativo (TTY)

O shell interativo **requer um TTY** (terminal real). Não funciona via:
- ❌ Pipes (`echo | vcli shell`)
- ❌ SSH sem `-t` flag
- ❌ Automação/scripts
- ❌ Claude Code terminal (não é TTY real)

---

## ✅ Como Testar Corretamente

### Opção 1: Terminal Local (Recomendado)

Abra um terminal real no seu sistema e execute:

```bash
cd /home/juan/vertice-dev/vcli-go
./bin/vcli shell
```

**Você verá**:
```
╭─[vCLI] 🚀 Kubernetes Edition
╰─> _

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tab: Complete │ ↑↓: Navigate │ Ctrl+K: Palette │ Ctrl+D: Exit
```

### Opção 2: SSH com TTY Allocation

Se estiver em SSH, force alocação de TTY:

```bash
ssh -t user@server "cd /path && ./bin/vcli shell"
```

### Opção 3: tmux/screen

Dentro de tmux ou screen (que emulam TTY):

```bash
tmux
./bin/vcli shell
```

---

## 🎮 Features para Testar

### 1. Autocomplete Fluido
1. Digite: `k8s get p`
2. **Veja sugestões aparecerem automaticamente** (sem Tab!)
3. Use ↑↓ para navegar
4. Enter ou Tab para aceitar

### 2. Ícones nos Comandos
- `k8s` → 📦
- `orchestrate` → 🚀
- `data` → 💾
- `investigate` → 🔍
- `maximus` → 🧠

### 3. Statusline K8s
Se houver `~/.kube/config`:
```
╭─[vCLI] 🚀 Kubernetes Edition │ ⎈ production │ default
```

### 4. Bottom Toolbar
Sempre visível:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tab: Complete │ ↑↓: Navigate │ Ctrl+K: Palette │ Ctrl+D: Exit
```

### 5. Comandos
- `k8s get pods` - Lista pods
- `k8s get nodes` - Lista nodes
- `/help` - Ajuda
- `/palette` - Command palette
- Ctrl+D - Sair

---

## 🐛 Troubleshooting

### Erro: "Interactive shell requires a terminal (TTY)"

**Causa**: Você está rodando sem TTY (pipe, SSH sem -t, etc.)

**Solução**:
1. Use terminal local real
2. SSH: adicione `-t` flag
3. Ou use comandos individuais: `vcli k8s get pods`

### Shell Legacy (Fallback)

Se tiver problemas com bubble-tea:
```bash
./bin/vcli shell --legacy
```

---

## 📝 Diferenças: Novo vs Legacy

| Feature | Bubble-tea (Novo) | go-prompt (Legacy) |
|---------|-------------------|-------------------|
| Complete while typing | ✅ | ❌ (precisa Tab) |
| Display meta | ✅ | ❌ |
| Ícones | ✅ | ❌ |
| Bottom toolbar | ✅ | ❌ |
| Multi-line prompt | ✅ | ❌ |
| Gradientes | ✅ | ❌ |
| Statusline inline | ✅ | ❌ |

---

## 🎬 Demo Workflow

```bash
# 1. Abrir shell
./bin/vcli shell

# 2. Ver K8s pods (autocomplete aparece ao digitar)
k8s get pods

# 3. Ver nodes
k8s get nodes

# 4. Abrir palette
/palette

# 5. Buscar comando
# Digite: kube
# Veja filtrar em tempo real

# 6. Sair
Ctrl+D
```

---

## 📊 Visual Comparison

### Antes (go-prompt)
```
┃ k8s get pods
# (sem visual, precisa Tab)
```

### Depois (bubble-tea)
```
╭─[vCLI] 🚀 Kubernetes Edition │ ⎈ production │ default
╰─> k8s get po_

╭────────────────────────────────────────────────╮
│ → 📦 k8s get pods        List all pods         │
│   📦 k8s get pod [name]  Get specific pod      │
╰────────────────────────────────────────────────╯

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tab: Complete │ ↑↓: Navigate │ Ctrl+K: Palette │ Ctrl+D: Exit
```

---

## ✅ Checklist de Teste

- [ ] Shell abre sem erros
- [ ] Welcome banner aparece
- [ ] Statusline K8s (se houver config)
- [ ] Autocomplete aparece ao digitar (sem Tab)
- [ ] Ícones visíveis nos comandos
- [ ] Navegação ↑↓ funciona
- [ ] Enter aceita sugestão
- [ ] Bottom toolbar sempre visível
- [ ] /palette abre command palette
- [ ] Ctrl+D sai corretamente

---

## 📌 Nota Importante

**Você NÃO pode testar via Claude Code terminal** porque não é um TTY real.

**Opções válidas**:
1. ✅ Terminal local (GNOME Terminal, iTerm2, etc.)
2. ✅ tmux/screen
3. ✅ SSH com `-t`

**Opções inválidas**:
1. ❌ Pipes/redirecionamento
2. ❌ Automação
3. ❌ Claude Code terminal
4. ❌ SSH sem `-t`

---

**Created**: 2025-10-07
**Author**: Juan Carlos + Anthropic Claude
**Status**: Ready for Testing
