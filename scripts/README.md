# 🛠️ VÉRTICE - Scripts de Gerenciamento

Scripts utilitários para gerenciar o ambiente Vértice/Maximus AI sem dor de cabeça.

---

## 🚀 SOLUÇÃO DEFINITIVA PARA CONFLITOS DE PORTA

### Problema Resolvido
✅ **NUNCA MAIS** conflitos de porta ao iniciar o Vértice
✅ Detecção automática de portas em uso
✅ Liberação automática com confirmação
✅ Validação antes de iniciar serviços
✅ Health checks integrados

---

## 📁 Scripts Disponíveis

### 1. `vertice-start.sh` ⭐ **RECOMENDADO**

**O QUE FAZ**: Wrapper inteligente que substitui `docker compose up`

**USO**:
```bash
# Uso normal - inicia tudo com validação
./scripts/vertice-start.sh

# Modo força - reinicia tudo
./scripts/vertice-start.sh --force

# Só verifica portas, não inicia
./scripts/vertice-start.sh --check
```

**FLUXO**:
1. ✅ Verifica todas as portas críticas
2. ✅ Libera automaticamente se houver conflito
3. ✅ Para containers existentes
4. ✅ Inicia serviços
5. ✅ Aguarda inicialização
6. ✅ Executa health check
7. ✅ Mostra status final

**OUTPUT ESPERADO**:
```
╔════════════════════════════════════════════════════════════════╗
║          🚀 VÉRTICE/MAXIMUS AI - STARTER v2.0 🤖              ║
╚════════════════════════════════════════════════════════════════╝

▶ Passo 1/5: Validação de Portas

✓ Porta 8099 disponível
✓ Porta 8001 disponível
✓ Todas as portas estão livres!

▶ Passo 2/5: Parando Containers Existentes
...

✓ VÉRTICE INICIADO COM SUCESSO!
```

---

### 2. `port-manager.sh` - Gerenciador Avançado

**O QUE FAZ**: Ferramenta completa de gerenciamento de portas

**USO**:
```bash
# Menu interativo
./scripts/port-manager.sh

# Comandos diretos
./scripts/port-manager.sh check    # Verifica conflitos
./scripts/port-manager.sh free     # Libera portas
./scripts/port-manager.sh report   # Gera relatório
./scripts/port-manager.sh start    # Inicia com validação
./scripts/port-manager.sh health   # Health check
```

**FUNCIONALIDADES**:
- 🔍 Detecta todas as 30+ portas críticas
- 🔨 Libera portas em conflito (com confirmação)
- 📊 Gera relatório detalhado com timestamp
- 🚀 Inicia serviços com validação completa
- 🏥 Health check de serviços críticos
- 💬 Menu interativo user-friendly

**EXEMPLO DE RELATÓRIO**:
```
═══════════════════════════════════════════════════════════
  VÉRTICE - RELATÓRIO DE PORTAS
  Gerado em: 2025-10-04 01:30:00
═══════════════════════════════════════════════════════════

[LIVRE]   Porta 8099 - API Gateway
[LIVRE]   Porta 8001 - Maximus Core
[OCUPADA] Porta 8016 - Maximus Orchestrator
          Processo: 12345|python|uvicorn main:app
...
```

---

## 🎯 CASOS DE USO

### Cenário 1: Iniciar o Vértice (Uso Diário)
```bash
# EM VEZ DE: docker compose up -d
# USE:
./scripts/vertice-start.sh
```

**Vantagens**:
- Resolve conflitos automaticamente
- Valida tudo antes de iniciar
- Mostra status claro

### Cenário 2: Debugar Problemas de Porta
```bash
./scripts/port-manager.sh check
```

Mostra exatamente qual processo está usando cada porta.

### Cenário 3: Liberar Portas Manualmente
```bash
./scripts/port-manager.sh free
```

Libera TODAS as portas do Vértice de uma vez.

### Cenário 4: Gerar Relatório para Documentação
```bash
./scripts/port-manager.sh report
```

Cria arquivo `port-report-TIMESTAMP.txt` com estado completo.

### Cenário 5: Verificar se Serviços Estão Rodando
```bash
./scripts/port-manager.sh health
```

Testa conexão HTTP com serviços críticos.

---

## 🔧 INSTALAÇÃO

### 1. Scripts já estão prontos!
Não precisa instalar nada, basta executar:

```bash
cd /home/juan/vertice-dev
./scripts/vertice-start.sh
```

### 2. (Opcional) Criar Alias Global

Adicione ao seu `~/.bashrc` ou `~/.zshrc`:

```bash
# Vértice Shortcuts
alias vertice-start='/home/juan/vertice-dev/scripts/vertice-start.sh'
alias vertice-ports='/home/juan/vertice-dev/scripts/port-manager.sh'
alias vertice-check='/home/juan/vertice-dev/scripts/port-manager.sh check'
alias vertice-health='/home/juan/vertice-dev/scripts/port-manager.sh health'
```

Depois execute:
```bash
source ~/.bashrc
```

Agora você pode usar em qualquer lugar:
```bash
vertice-start
vertice-check
vertice-health
```

---

## 📋 PORTAS GERENCIADAS

O script monitora **30+ portas críticas**:

| Range | Categoria | Exemplos |
|-------|-----------|----------|
| 8001-8037 | Core & Arsenal | Maximus Core, Offensive Tools |
| 6000-6999 | Databases | Redis, PostgreSQL, Qdrant |
| 3000-9999 | Monitoring | Grafana, Prometheus |

Ver lista completa em: `/PORTAS_E_SERVICOS_MAPEAMENTO.md`

---

## 🛡️ SEGURANÇA

**Scripts são seguros**:
- ✅ Sempre pedem confirmação antes de matar processos
- ✅ Mostram qual processo será morto
- ✅ Não alteram configurações do sistema
- ✅ Apenas liberam portas do Vértice (lista definida)
- ✅ Logs completos de todas as ações

**Nunca matam**:
- Processos de sistema
- Serviços não relacionados ao Vértice
- Processos sem confirmação (exceto no modo --force)

---

## 🐛 TROUBLESHOOTING

### "Permission denied"
```bash
chmod +x scripts/*.sh
```

### "docker: command not found"
Instale Docker e Docker Compose.

### "Port still in use after free"
```bash
# Tente manualmente
lsof -ti:8001 | xargs kill -9
```

### "Health check failed"
Serviço pode estar iniciando ainda. Aguarde 30s e tente:
```bash
./scripts/port-manager.sh health
```

---

## 📚 DOCUMENTAÇÃO RELACIONADA

- `/PORTAS_E_SERVICOS_MAPEAMENTO.md` - Lista completa de portas
- `/docker-compose.yml` - Configuração de serviços
- `/MAXIMUS_AI_FRONTEND_INTEGRATION_COMPLETE.md` - Integração frontend

---

## 🎉 BENEFÍCIOS

**ANTES** (docker compose tradicional):
```bash
$ docker compose up -d
Error: port 8001 already allocated
$ # 😤 Frustração, debugar manualmente, kill -9, tentar de novo...
```

**DEPOIS** (com scripts):
```bash
$ ./scripts/vertice-start.sh
✓ Porta 8001 disponível
✓ Porta 8016 disponível
✓ Todas as portas estão livres!
✓ VÉRTICE INICIADO COM SUCESSO!
# 😎 Tudo funciona de primeira!
```

---

**NUNCA MAIS** conflitos de porta! 🎯✨

---

**Criado em**: 04 de Outubro de 2025
**Versão**: 2.0
**Autor**: Claude (Anthropic)
