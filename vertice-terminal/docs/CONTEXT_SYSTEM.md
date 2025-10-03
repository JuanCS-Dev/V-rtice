# 🎯 Sistema de Contextos - Vértice CLI

**Status:** ✅ **IMPLEMENTADO** (Sprint 1.1 - P0)
**Data:** 2025-10-02
**Inspiração:** kubectl contexts

---

## 📋 Visão Geral

O Sistema de Contextos permite gerenciar múltiplos engagements/projetos simultaneamente, cada um com suas configurações isoladas, evitando erros como "executar comando no cliente errado".

### Características Principais:

✅ **Isolamento de Projetos:** Cada contexto tem seu próprio diretório de output
✅ **Persistência em TOML:** Configuração legível e versionável
✅ **Auto-save de Resultados:** Scans salvos automaticamente no contexto ativo
✅ **Estrutura Organizada:** Diretórios pré-criados (scans, recon, exploits, loot, reports)
✅ **Metadados Flexíveis:** Notas, proxy, targets customizáveis

---

## 🚀 Uso Rápido

### Criar e ativar contexto:
```bash
vcli context create pentest-acme --target 10.0.0.0/24 --notes "Acme Corp Pentest"
```

### Listar contextos:
```bash
vcli context list
```

### Mudar contexto:
```bash
vcli context use pentest-acme
```

### Ver contexto ativo:
```bash
vcli context current
```

### Executar scan (salva automaticamente no contexto):
```bash
vcli scan ports 10.0.0.1
# Resultado salvo em: ~/vertice-engagements/pentest-acme/scans/
```

---

## 📚 Comandos Disponíveis

### `context create`

Cria um novo contexto de engajamento.

**Sintaxe:**
```bash
vcli context create <name> --target <target> [OPTIONS]
```

**Parâmetros:**
- `name` (obrigatório): Nome do contexto (ex: `pentest-acme`)
- `--target, -t` (obrigatório): Alvo do engagement (IP, range, domain)
- `--output-dir, -o` (opcional): Diretório de output personalizado
- `--proxy, -p` (opcional): Proxy HTTP (ex: `http://127.0.0.1:8080`)
- `--notes, -n` (opcional): Notas sobre o engagement
- `--no-auto-use` (flag): Não ativar automaticamente

**Exemplo:**
```bash
vcli context create pentest-acme \
  --target 10.0.0.0/24 \
  --proxy http://127.0.0.1:8080 \
  --notes "Acme Corp Q4 2025 Pentest"
```

**Output:**
```
✓ Contexto 'pentest-acme' criado com sucesso!

                   📋 Contexto: pentest-acme
╭───────────────┬─────────────────────────────────────────────╮
│ 🎯 Target     │ 10.0.0.0/24                                 │
│ 📁 Output Dir │ /home/user/vertice-engagements/pentest-acme │
│ 🌐 Proxy      │ http://127.0.0.1:8080                       │
│ 📝 Notes      │ Acme Corp Q4 2025 Pentest                   │
│ 🕒 Created    │ 2025-10-02T20:00:00                         │
╰───────────────┴─────────────────────────────────────────────╯

📂 Estrutura criada:
  /home/user/vertice-engagements/pentest-acme/
    ├── scans/
    ├── recon/
    ├── exploits/
    ├── loot/
    └── reports/
```

---

### `context list`

Lista todos os contextos disponíveis.

**Sintaxe:**
```bash
vcli context list
```

**Output:**
```
                          🎯 Contextos de Engajamento
╭────────┬──────────────┬─────────────┬───────────────────┬───────┬────────────╮
│ Status │ Nome         │ Target      │ Output Dir        │ Proxy │ Created    │
├────────┼──────────────┼─────────────┼───────────────────┼───────┼────────────┤
│   ✓    │ pentest-acme │ 10.0.0.0/24 │ ~/vertice-enga... │ -     │ 2025-10-02 │
│        │ pentest-beta │ 192.168.1.0 │ ~/vertice-enga... │ http  │ 2025-09-15 │
╰────────┴──────────────┴─────────────┴───────────────────┴───────┴────────────╯

✓ Contexto ativo: pentest-acme
```

---

### `context use`

Ativa um contexto existente.

**Sintaxe:**
```bash
vcli context use <name>
```

**Exemplo:**
```bash
vcli context use pentest-beta
```

**Output:**
```
✓ Contexto 'pentest-beta' ativado!

🎯 Target     │ 192.168.1.0/24
📁 Output     │ ~/vertice-engagements/pentest-beta
```

---

### `context current`

Mostra o contexto ativo atual.

**Sintaxe:**
```bash
vcli context current
```

**Output:**
```
╭────────────────────── 🎯 Contexto Ativo: pentest-acme ───────────────────────╮
│ Nome: pentest-acme                                                           │
│ Target: 10.0.0.0/24                                                          │
│ Output Dir: ~/vertice-engagements/pentest-acme                               │
│ Notes: Acme Corp Q4 2025 Pentest                                             │
│ Created: 2025-10-02T20:00:00                                                 │
│ Updated: 2025-10-02T20:30:00                                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

### `context delete`

Deleta um contexto.

**Sintaxe:**
```bash
vcli context delete <name> [OPTIONS]
```

**Parâmetros:**
- `--delete-files, -f` (flag): Deletar também os arquivos do output_dir
- `--yes, -y` (flag): Confirmar sem perguntar

**Exemplo:**
```bash
vcli context delete old-project --delete-files --yes
```

**Segurança:**
- Não permite deletar o contexto ativo
- Pede confirmação por padrão
- Mostra aviso ao deletar arquivos

---

### `context update`

Atualiza informações de um contexto.

**Sintaxe:**
```bash
vcli context update <name> [OPTIONS]
```

**Parâmetros:**
- `--target, -t`: Novo target
- `--proxy, -p`: Novo proxy
- `--notes, -n`: Novas notas

**Exemplo:**
```bash
vcli context update pentest-acme --target 10.0.0.0/16
vcli context update pentest-acme --notes "Fase 2: Post-exploitation"
```

---

### `context info`

Mostra informações detalhadas de um contexto.

**Sintaxe:**
```bash
vcli context info [name]
```

Se `name` não for fornecido, mostra informações do contexto ativo.

---

## 🗂️ Estrutura de Arquivos

### Diretórios de Contexto

Cada contexto cria automaticamente a seguinte estrutura:

```
~/vertice-engagements/<context-name>/
├── scans/           # Resultados de port scans, vuln scans
├── recon/           # Dados de reconhecimento
├── exploits/        # Scripts e payloads de exploitation
├── loot/            # Credenciais, dados extraídos
└── reports/         # Relatórios finais
```

### Arquivo de Configuração

**Localização:** `~/.config/vertice/contexts.toml`

**Formato:**
```toml
[contexts.pentest-acme]
name = "pentest-acme"
target = "10.0.0.0/24"
output_dir = "/home/user/vertice-engagements/pentest-acme"
created_at = "2025-10-02T20:00:00"
updated_at = "2025-10-02T20:30:00"
proxy = "http://127.0.0.1:8080"
notes = "Acme Corp Q4 2025 Pentest"

[contexts.pentest-acme.metadata]
client = "Acme Corp"
phase = "reconnaissance"
```

### Ponteiro de Contexto Ativo

**Localização:** `~/.config/vertice/current-context`

**Conteúdo:** Nome do contexto ativo (texto puro)

---

## 🔗 Integração com Comandos

### Auto-save de Resultados

Comandos integrados salvam automaticamente resultados no contexto ativo:

✅ **`vcli scan ports`** → `scans/port_<target>_<timestamp>.json`
✅ **`vcli scan vulns`** → `scans/vuln_<target>_<timestamp>.json`
✅ **`vcli scan network`** → `scans/network_<target>_<timestamp>.json`

**Exemplo de arquivo salvo:**
```json
{
  "scan_type": "port",
  "target": "10.0.0.1",
  "timestamp": "2025-10-02T20:45:00",
  "context": "pentest-acme",
  "result": {
    "target": "10.0.0.1",
    "status": "completed",
    "open_ports": [
      {"port": 22, "state": "open", "service": "ssh"},
      {"port": 80, "state": "open", "service": "http"}
    ]
  }
}
```

### Comandos sem Contexto

Se nenhum contexto estiver ativo, os comandos ainda funcionam normalmente, mas **não salvam resultados automaticamente**.

---

## 🛠️ Casos de Uso

### Caso 1: Múltiplos Clientes Simultâneos

```bash
# Cliente A
vcli context create client-a --target 10.0.0.0/24
vcli scan ports 10.0.0.1
vcli scan vulns 10.0.0.1

# Cliente B
vcli context create client-b --target 192.168.1.0/24
vcli context use client-b
vcli scan ports 192.168.1.1

# Voltar para Cliente A
vcli context use client-a
vcli context current  # Confirma contexto ativo
```

### Caso 2: Fases de Engagement

```bash
# Criar contexto inicial
vcli context create pentest-acme --target example.com

# Fase de Recon
vcli scan network --network 10.0.0.0/24
vcli context update pentest-acme --notes "Fase 1: Recon completa"

# Fase de Exploitation
vcli context update pentest-acme --notes "Fase 2: Exploitation"
vcli scan vulns 10.0.0.15

# Fase de Post-Exploitation
vcli context update pentest-acme --notes "Fase 3: Post-exploitation"
```

### Caso 3: Proxy Testing

```bash
# Criar contexto com proxy Burp
vcli context create webapp-test \
  --target https://app.example.com \
  --proxy http://127.0.0.1:8080 \
  --notes "Web Application Pentest - Burp Proxy"

# Todos os comandos usarão o proxy configurado
vcli scan vulns https://app.example.com
```

---

## 🔒 Segurança e Boas Práticas

### Prevenção de Erros

✅ **Não permite deletar contexto ativo** → Evita deletar dados por acidente
✅ **Validação de nomes** → Apenas alfanuméricos, hífens e underscores
✅ **Confirmação antes de deletar** → Proteção contra deleção acidental de arquivos

### Organização

✅ **Nomes descritivos:** Use `client-projeto-fase` (ex: `acme-webapp-2025`)
✅ **Notas detalhadas:** Documente fase, objetivos, achados
✅ **Atualização frequente:** Use `context update` para manter histórico

### Backup

```bash
# Backup manual de contextos
cp ~/.config/vertice/contexts.toml ~/backups/contexts-$(date +%Y%m%d).toml

# Backup de dados
tar -czf ~/backups/vertice-data-$(date +%Y%m%d).tar.gz ~/vertice-engagements/
```

---

## 🐛 Troubleshooting

### Erro: "Nenhum contexto ativo"

**Problema:** Comando requer contexto mas nenhum está ativo.

**Solução:**
```bash
vcli context list  # Ver contextos disponíveis
vcli context use <name>  # Ativar um
```

### Contexto não aparece em `list`

**Problema:** Arquivo TOML corrompido.

**Solução:**
```bash
cat ~/.config/vertice/contexts.toml  # Verificar sintaxe
# Se necessário, recriar manualmente ou restaurar backup
```

### Resultados não sendo salvos

**Problema:** Contexto existe mas scans não salvam.

**Verificar:**
```bash
vcli context current  # Confirma contexto ativo
ls -la ~/vertice-engagements/<context>/scans/  # Verifica permissões
```

---

## 🎯 Próximas Evoluções

### Em Desenvolvimento:

- [ ] **Templates de Contexto:** Pré-configurações para tipos de engagement
- [ ] **Compartilhamento:** Exportar/importar contextos (YAML)
- [ ] **Hooks:** Comandos customizados ao ativar contexto
- [ ] **Timetracking:** Rastreamento de tempo gasto por contexto
- [ ] **Reporting:** Geração automática de relatórios do contexto

### Roadmap:

- **Sprint 1.2:** Modo interativo para criar contextos
- **Sprint 2.3:** Workflows integrados com contextos
- **Sprint 3.1:** Plugins podem estender contextos

---

## 📖 Referências

- **Inspiração:** Kubernetes `kubectl` contexts
- **Formato:** TOML (Tom's Obvious, Minimal Language)
- **Libs:** `tomli` (leitura), `tomli-w` (escrita)

---

**Desenvolvido com 🔥 por Juan + Claude**
**Parte do Vértice CLI Upgrade Plan (VERTICE_UPGRADE_PLAN.md)**
**Sprint 1.1 - PRIORIDADE P0 ✅**
