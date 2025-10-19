# MAXIMUS Control Center v3.0 - PRIMOSO EDITION

**Dedicado a:** Maximus & Penélope ❤️

---

## O Que Mudou (v2.0 → v3.0)

### ✨ Visual Completamente Renovado
- 🎨 Header ASCII art profissional
- 📊 Barra de progresso de health
- 🎯 Dashboard com cores e emojis bonitos
- 💬 Diálogos entre Maximus & Penélope

### 🚀 Melhorias de Performance
- ⚡ Spinner animado durante operações
- 📦 Contagem precisa de containers (não depende de JSON)
- 🔄 Reinício mais suave e visual

### 🧠 Features Novas
- 📊 Health score visual (barra de progresso)
- 🎯 Dashboard de serviços críticos
- 💬 Mensagens contextuais baseadas em health
- 🎨 Cores dinâmicas (verde/amarelo/vermelho)

---

## Comandos

```bash
maximus start         # Inicia sistema completo
maximus stop          # Para todos os serviços
maximus restart       # Reinicia tudo
maximus status        # Dashboard completo (DEFAULT)
maximus logs [nome]   # Ver logs de um serviço
maximus help          # Esta ajuda
```

---

## Exemplos de Uso

### Para os filhos iniciarem o servidor:
```bash
maximus start
```

Verão:
- ✨ Animação de loading bonitinha
- 🎉 Mensagem "Maximus: Todos os sistemas operacionais!"
- 📊 Contadores de containers

### Ver se está tudo funcionando:
```bash
maximus status
```

Mostra:
- 📊 Health score com barra visual
- ✅ Serviços críticos (API Gateway, Auth, Postgres, Redis)
- 💬 Diálogos entre Maximus & Penélope
- 🎨 Cores indicando estado do sistema

### Ver logs de um serviço:
```bash
maximus logs api_gateway
maximus logs postgres
maximus logs redis
```

---

## Detalhes Técnicos

### Health Score
Calculado como: `(healthy / (healthy + unhealthy)) * 100`

**Interpretação:**
- 90-100%: Sistema em capacidade máxima 🔥
- 70-89%: Tudo certo ✅
- 50-69%: Alguns serviços precisam de atenção ⚠️
- 0-49%: Problemas críticos ❌

### Serviços Críticos Monitorados
1. `api_gateway` - Porta de entrada do sistema
2. `auth_service` - Autenticação
3. `postgres` - Banco de dados
4. `redis` - Cache
5. `maximus_core_service` - Núcleo do sistema

---

## Para Adicionar ao Alias

Adicione ao `~/.bashrc`:

```bash
alias maximus='/home/juan/vertice-dev/scripts/maximus.sh'
```

Recarregue:
```bash
source ~/.bashrc
```

Agora pode usar de qualquer lugar:
```bash
maximus start
maximus status
```

---

## Changelog

### v3.0 - PRIMOSO EDITION (2025-10-19)
- ✨ Visual completamente renovado
- 🎨 ASCII art header profissional
- 📊 Health score com barra de progresso
- 💬 Diálogos interativos Maximus & Penélope
- 🎯 Dashboard de serviços críticos
- ⚡ Spinner animado
- 🎨 Cores dinâmicas baseadas em health
- 🔄 Código refatorado e otimizado

### v2.0 (2025-10-18)
- 🎯 Dashboard de status por tier
- 🔍 Healthcheck detalhado
- 📋 Logs por serviço

### v1.0 (2025-09-14)
- 🚀 Start/stop básico
- 📊 Status simples

---

**Feito com ❤️ para Maximus & Penélope**

"Porque grandes sistemas precisam de grandes nomes"
