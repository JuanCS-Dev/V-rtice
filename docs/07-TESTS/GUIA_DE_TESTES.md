# 🧪 GUIA COMPLETO DE TESTES - PROJETO VÉRTICE
## Manual Antiburro para Testers

> **Objetivo**: Este guia permite que QUALQUER pessoa (mesmo sem conhecimento técnico) consiga testar TODAS as funcionalidades do sistema.

---

## 📋 ÍNDICE

1. [Preparação do Ambiente](#1-preparação-do-ambiente)
2. [Módulo: Operações Gerais](#2-módulo-operações-gerais)
3. [Módulo: Cyber Security](#3-módulo-cyber-security)
4. [Módulo: Inteligência Social (OSINT)](#4-módulo-inteligência-social-osint)
5. [Módulo: Terminal CLI](#5-módulo-terminal-cli)
6. [Módulo: Administração](#6-módulo-administração)
7. [Testes de Temas](#7-testes-de-temas)
8. [Checklist Final](#8-checklist-final)

---

## 1. PREPARAÇÃO DO AMBIENTE

### 1.1. Iniciar os Serviços

**Passo a Passo:**

1. Abra o terminal no diretório do projeto: `/home/juan/vertice-dev`
2. Execute os comandos abaixo:

```bash
# Iniciar Backend (em um terminal)
cd backend
python main.py

# Iniciar Frontend (em OUTRO terminal)
cd frontend
npm run dev
```

3. Aguarde até ver as mensagens:
   - Backend: `Uvicorn running on http://0.0.0.0:8000`
   - Frontend: `Local: http://localhost:5173/`

4. Abra o navegador e acesse: `http://localhost:5173`

### 1.2. Verificações Iniciais

- [ ] A página carrega sem erros (F12 → Console → não deve ter erros vermelhos)
- [ ] O logo "PROJETO VÉRTICE" aparece no topo
- [ ] O relógio no canto superior direito está funcionando
- [ ] Há 5 botões de módulos na barra de navegação
- [ ] O seletor de temas (bolinha colorida) aparece ao lado do relógio

---

## 2. MÓDULO: OPERAÇÕES GERAIS

### 2.1. Interface Principal

**O que testar:**
- [ ] O módulo "OPERAÇÕES GERAIS" está selecionado (fundo verde claro)
- [ ] Há um campo de busca com texto ">>> INSERIR PLACA DO VEÍCULO"
- [ ] Há um botão "EXECUTAR CONSULTA"
- [ ] O mapa aparece na tela (deve mostrar o mapa do Brasil/São Paulo)

### 2.2. Consulta de Veículo (SINESP)

**Passo a Passo:**

1. Clique no campo de busca
2. Digite uma placa fictícia: `ABC1234`
3. Clique em "EXECUTAR CONSULTA"

**O que deve acontecer:**
- [ ] Botão muda para "PROCESSANDO..."
- [ ] Aparece um spinner (rodinha) de carregamento
- [ ] Após 2-5 segundos, um card aparece com os dados do veículo
- [ ] O mapa centraliza no veículo (com marcador verde pulsante)

### 2.3. Teste do Mapa (SINESP)

**O que testar:**
- [ ] O mapa tem camadas/tiles visíveis (ruas, cidades, etc.)
- [ ] Você consegue dar zoom (scroll do mouse ou botões +/-)
- [ ] Você consegue arrastar o mapa
- [ ] Os controles do mapa aparecem no canto esquerdo

### 2.4. Painel de Controle do Mapa

**Passo a Passo:**

1. Localize o painel de controle no lado esquerdo do mapa
2. Teste cada opção:

**Filtros de Tempo:**
- [ ] Selecione "7 dias" → verifique se atualiza
- [ ] Selecione "30 dias" → verifique se atualiza
- [ ] Selecione "90 dias" → verifique se atualiza

**Tipo de Crime:**
- [ ] Selecione "Todos"
- [ ] Selecione "Roubo de Veículos"
- [ ] Selecione "Furto Residencial"

**Visualizações:**
- [ ] Marque "Mapa de Calor" → deve aparecer camada vermelha/amarela
- [ ] Marque "Marcadores" → devem aparecer pontos vermelhos
- [ ] Marque "Hotspots Preditivos" → ainda vazio (OK)

**Botão "EXECUTAR ANÁLISE PREDITIVA":**
- [ ] Clique no botão
- [ ] Deve aparecer "AURORA AI PROCESSANDO..."
- [ ] Após 3-10 segundos, aparecem círculos coloridos no mapa (zonas de risco)

### 2.5. Histórico de Consultas

**O que testar:**
- [ ] Após fazer uma consulta, a placa aparece em "HISTÓRICO:"
- [ ] Clicar na placa do histórico preenche o campo novamente
- [ ] Múltiplas consultas aparecem no histórico (máx 5)

---

## 3. MÓDULO: CYBER SECURITY

### 3.1. Acessar o Módulo

**Passo a Passo:**

1. Clique no botão "CYBER SECURITY" (azul ciano)
2. A tela deve mudar completamente

**O que verificar:**
- [ ] Header muda para "CYBER SECURITY OPS"
- [ ] Botão "VOLTAR VÉRTICE" aparece no topo direito
- [ ] Aparecem 7 abas de módulos cyber

### 3.2. Overview (Visão Geral)

**O que testar:**
- [ ] Cards de estatísticas aparecem (Threat Intel, APIs Ativas, Feeds Ativos)
- [ ] Gráfico de métricas em tempo real atualiza
- [ ] Lista de alertas em tempo real aparece

### 3.3. Aurora AI Hub

**Passo a Passo:**

1. Clique na aba "AURORA AI HUB"

**Testar Execução de Comando:**
- [ ] Campo de input "Digite seu comando..." está visível
- [ ] Digite: `scan network 192.168.1.0/24`
- [ ] Clique em "EXECUTAR"
- [ ] Spinner aparece
- [ ] Resultado aparece na timeline de execução

**Testar Templates:**
- [ ] Clique em um dos templates rápidos (ex: "Port Scan")
- [ ] O campo deve preencher automaticamente
- [ ] Execute e verifique resultado

**Timeline de Execução:**
- [ ] Cada comando executado aparece na timeline
- [ ] Há um timestamp
- [ ] Há um status (success/error/warning)
- [ ] Há um botão para expandir detalhes

### 3.4. CVE Exploits

**Passo a Passo:**

1. Clique na aba "CVE EXPLOITS"

**Buscar Exploit:**
- [ ] Campo de busca está visível
- [ ] Digite: `apache`
- [ ] Clique em "BUSCAR"
- [ ] Lista de exploits aparece
- [ ] Cada item tem: ID, descrição, severidade, data

**Filtros:**
- [ ] Filtre por severidade "CRITICAL"
- [ ] Filtre por severidade "HIGH"
- [ ] Resultados mudam conforme filtro

### 3.5. Domain Intel

**Passo a Passo:**

1. Clique na aba "DOMAIN INTEL"

**Analisar Domínio:**
- [ ] Campo "Digite um domínio" está visível
- [ ] Digite: `google.com`
- [ ] Clique em "ANALISAR"
- [ ] Resultados aparecem:
  - [ ] Informações WHOIS
  - [ ] Registros DNS
  - [ ] Score de reputação
  - [ ] SSL/TLS info

### 3.6. IP Analysis

**Passo a Passo:**

1. Clique na aba "IP ANALYSIS"

**Analisar IP:**
- [ ] Campo "Digite um IP" está visível
- [ ] Digite: `8.8.8.8`
- [ ] Clique em "ANALISAR"
- [ ] Resultados aparecem:
  - [ ] Geolocalização
  - [ ] ISP/ASN
  - [ ] Blacklist check
  - [ ] Portas abertas

### 3.7. Network Monitor

**Passo a Passo:**

1. Clique na aba "NET MONITOR"

**Stream de Eventos:**
- [ ] Lista de eventos em tempo real está visível
- [ ] Eventos têm timestamp
- [ ] Eventos têm tipo (TCP/UDP/HTTP)
- [ ] Eventos têm origem e destino

**Controles:**
- [ ] Botão "PAUSAR" funciona
- [ ] Botão "LIMPAR" limpa a lista
- [ ] Filtros funcionam (TCP, UDP, HTTP)

### 3.8. NMAP Scan

**Passo a Passo:**

1. Clique na aba "+ NMAP SCAN"

**Executar Scan:**
- [ ] Campo "Target" está visível
- [ ] Digite: `scanme.nmap.org`
- [ ] Selecione tipo de scan (ex: "Quick Scan")
- [ ] Clique em "EXECUTAR SCAN"
- [ ] Status muda para "Scanning..."
- [ ] Resultados aparecem após conclusão

### 3.9. Vulnerability Scanner

**Passo a Passo:**

1. Clique na aba "VULN SCANNER" (com triângulo amarelo)

**Executar Scan:**
- [ ] Campo "Target URL/IP" está visível
- [ ] Digite: `http://testphp.vulnweb.com`
- [ ] Clique em "INICIAR SCAN"
- [ ] Progresso aparece (0% → 100%)
- [ ] Vulnerabilidades encontradas aparecem na lista

### 3.10. Social Engineering

**Passo a Passo:**

1. Clique na aba "SOCIAL ENG" (com triângulo laranja)

**Explorar Ferramentas:**
- [ ] Lista de ferramentas está visível
- [ ] Cada ferramenta tem descrição
- [ ] Clique em uma ferramenta → detalhes aparecem

### 3.11. Threat Map

**ATENÇÃO:** Este teste verifica o bug corrigido!

**Passo a Passo:**

1. Role a página para baixo até encontrar o card "CYBER THREAT MAP"

**O que testar:**
- [ ] O mapa tem camadas/tiles visíveis (ruas, países, etc.)
- [ ] Não está cinza/branco (bug!)
- [ ] Você consegue dar zoom
- [ ] Você consegue arrastar o mapa
- [ ] Aparecem marcadores de ameaças (pontos coloridos)

**Filtros:**
- [ ] Filtre por severidade "CRITICAL"
- [ ] Filtre por tipo "Malware"
- [ ] Marcadores mudam conforme filtro

### 3.12. Voltar ao Menu Principal

**Passo a Passo:**

1. Clique no botão "VOLTAR VÉRTICE" no topo direito

**O que verificar:**
- [ ] Volta para o módulo "OPERAÇÕES GERAIS"
- [ ] Mapa do SINESP está visível novamente
- [ ] Header volta ao padrão verde

---

## 4. MÓDULO: INTELIGÊNCIA SOCIAL (OSINT)

### 4.1. Acessar o Módulo

**Passo a Passo:**

1. Clique no botão "INTELIGÊNCIA SOCIAL" (roxo)

**O que verificar:**
- [ ] Header muda para "OSINT INTELLIGENCE"
- [ ] Aparecem widgets de investigação

### 4.2. Social Media Widget

**Passo a Passo:**

1. Localize o card "SOCIAL MEDIA ANALYSIS"

**Buscar Perfil:**
- [ ] Campo "Username" está visível
- [ ] Digite: `testuser123`
- [ ] Selecione plataforma: "Twitter"
- [ ] Clique em "BUSCAR"
- [ ] Resultados aparecem (perfil, posts, etc.)

**Testar Múltiplas Plataformas:**
- [ ] Teste Instagram
- [ ] Teste Facebook
- [ ] Teste LinkedIn

### 4.3. Breach Data Widget

**Passo a Passo:**

1. Localize o card "BREACH DATA SEARCH"

**Buscar Vazamentos:**
- [ ] Campo "Email/Username" está visível
- [ ] Digite: `test@example.com`
- [ ] Clique em "VERIFICAR"
- [ ] Resultados aparecem (vazamentos encontrados)

**Informações Exibidas:**
- [ ] Nome do vazamento
- [ ] Data
- [ ] Tipo de dados expostos
- [ ] Severidade

### 4.4. Voltar ao Menu Principal

- [ ] Clique em "VOLTAR VÉRTICE"
- [ ] Retorna ao menu principal

---

## 5. MÓDULO: TERMINAL CLI

### 5.1. Acessar o Módulo

**Passo a Passo:**

1. Clique no botão "TERMINAL CLI" (laranja)

**O que verificar:**
- [ ] Terminal em tela cheia aparece
- [ ] Prompt está visível: `vertice@system:~$`
- [ ] Cursor pisca

### 5.2. Comandos Básicos

**Testar Comandos:**

```bash
# Ajuda
help

# Limpar tela
clear

# Status do sistema
status

# Listar comandos
ls
```

**O que verificar:**
- [ ] Cada comando retorna output
- [ ] Output está colorido (verde/amarelo/vermelho)
- [ ] Histórico de comandos funciona (seta ↑)

### 5.3. Comandos Cyber

```bash
# Scan de rede
scan --target 192.168.1.0/24

# Análise de IP
ip --address 8.8.8.8

# Análise de domínio
domain --query google.com
```

**O que verificar:**
- [ ] Comandos executam sem erro
- [ ] Resultados aparecem formatados
- [ ] Indicadores de loading aparecem

### 5.4. Comandos OSINT

```bash
# Busca em redes sociais
social --username testuser --platform twitter

# Verificar vazamentos
breach --email test@example.com
```

**O que verificar:**
- [ ] Comandos retornam dados
- [ ] Formato de saída está correto

### 5.5. Navegação por Linguagem Natural

**Passo a Passo:**

1. Digite: `quero analisar o ip 8.8.8.8`
2. Pressione Enter

**O que verificar:**
- [ ] Sistema interpreta e executa o comando correto
- [ ] Resultado aparece

**Outros testes:**
- [ ] `me mostre informações sobre o domínio google.com`
- [ ] `faça um scan na rede 192.168.1.0/24`
- [ ] `busque o usuário testuser no twitter`

### 5.6. Voltar ao Menu Principal

- [ ] Digite: `exit`
- [ ] OU clique em "VOLTAR VÉRTICE"
- [ ] Retorna ao menu principal

---

## 6. MÓDULO: ADMINISTRAÇÃO

### 6.1. Acessar o Módulo

**Passo a Passo:**

1. Clique no botão "ADMINISTRAÇÃO" (amarelo)

**O que verificar:**
- [ ] Dashboard de admin aparece
- [ ] Cards de métricas aparecem

### 6.2. Monitoramento do Sistema

**Verificar Cards:**
- [ ] CPU Usage (%)
- [ ] Memory Usage (%)
- [ ] Active Services
- [ ] Uptime

**O que testar:**
- [ ] Valores atualizam em tempo real
- [ ] Gráficos aparecem
- [ ] Cores mudam conforme status (verde/amarelo/vermelho)

### 6.3. Logs do Sistema

**Passo a Passo:**

1. Localize a seção "SYSTEM LOGS"

**O que verificar:**
- [ ] Lista de logs em tempo real
- [ ] Filtros funcionam (INFO, WARNING, ERROR)
- [ ] Botão "LIMPAR" funciona
- [ ] Botão "EXPORTAR" funciona

### 6.4. Configurações

**Passo a Passo:**

1. Localize a seção "CONFIGURAÇÕES"

**O que testar:**
- [ ] Configurações de API aparecem
- [ ] Toggle switches funcionam
- [ ] Botão "SALVAR" aparece
- [ ] Alterações são persistidas

### 6.5. Voltar ao Menu Principal

- [ ] Clique em "VOLTAR VÉRTICE"
- [ ] Retorna ao menu principal

---

## 7. TESTES DE TEMAS

### 7.1. Acessar o Seletor de Temas

**Passo a Passo:**

1. Localize o ícone colorido ao lado do relógio (canto superior direito)
2. Clique no ícone

**O que verificar:**
- [ ] Dropdown aparece com lista de temas
- [ ] 6 temas estão listados

### 7.2. Testar Cada Tema

#### Tema 1: Matrix Green 🟢
- [ ] Clique em "Matrix Green"
- [ ] Interface muda para verde
- [ ] Bordas ficam verdes
- [ ] Textos ficam verdes
- [ ] Efeitos de brilho verde aparecem

#### Tema 2: Cyber Blue 🔵
- [ ] Clique em "Cyber Blue"
- [ ] Interface muda para azul ciano
- [ ] Bordas ficam azuis
- [ ] Textos ficam azuis
- [ ] Efeitos de brilho azul aparecem

#### Tema 3: Purple Haze 🟣
- [ ] Clique em "Purple Haze"
- [ ] Interface muda para roxo
- [ ] Bordas ficam roxas
- [ ] Textos ficam roxos
- [ ] Efeitos de brilho roxo aparecem

#### Tema 4: Amber Alert 🟠
- [ ] Clique em "Amber Alert"
- [ ] Interface muda para laranja/âmbar
- [ ] Bordas ficam laranjas
- [ ] Textos ficam laranjas
- [ ] Efeitos de brilho laranja aparecem

#### Tema 5: Red Alert 🔴
- [ ] Clique em "Red Alert"
- [ ] Interface muda para vermelho
- [ ] Bordas ficam vermelhas
- [ ] Textos ficam vermelhos
- [ ] Efeitos de brilho vermelho aparecem

#### Tema 6: Stealth Mode ⚫
- [ ] Clique em "Stealth Mode"
- [ ] Interface muda para tons de cinza
- [ ] Bordas ficam cinzas
- [ ] Textos ficam cinzas
- [ ] Efeitos de brilho cinza aparecem

### 7.3. Persistência de Tema

**Passo a Passo:**

1. Selecione um tema (ex: Cyber Blue)
2. Recarregue a página (F5)

**O que verificar:**
- [ ] Tema selecionado é mantido após reload
- [ ] Não volta para o tema padrão

### 7.4. Tema em Diferentes Módulos

**Passo a Passo:**

1. Selecione "Purple Haze"
2. Navegue para "CYBER SECURITY"
3. Navegue para "INTELIGÊNCIA SOCIAL"
4. Navegue para "TERMINAL CLI"

**O que verificar:**
- [ ] Tema roxo é mantido em todos os módulos
- [ ] Cores são consistentes

---

## 8. CHECKLIST FINAL

### 8.1. Testes de Performance

- [ ] Aplicação carrega em menos de 5 segundos
- [ ] Navegação entre módulos é instantânea
- [ ] Mapas carregam sem travamentos
- [ ] Não há erros no console (F12)

### 8.2. Testes de Responsividade

**Resize da Janela:**
- [ ] Diminua a largura da janela
- [ ] Interface se adapta (responsiva)
- [ ] Nada fica cortado ou sobreposto

### 8.3. Testes de Compatibilidade

**Navegadores:**
- [ ] Chrome (testado)
- [ ] Firefox (testar)
- [ ] Edge (testar)

### 8.4. Testes de Acessibilidade

- [ ] Todos os botões têm tooltips (hover)
- [ ] Textos são legíveis
- [ ] Contraste é adequado

### 8.5. Testes de Erros

**Cenários de Erro:**

1. Backend Offline:
   - [ ] Desligue o backend
   - [ ] Tente fazer uma consulta
   - [ ] Mensagem de erro amigável aparece

2. Placa Inválida:
   - [ ] Digite: `XXXXX`
   - [ ] Clique em "EXECUTAR CONSULTA"
   - [ ] Mensagem de erro aparece

3. IP Inválido:
   - [ ] No módulo Cyber → IP Analysis
   - [ ] Digite: `999.999.999.999`
   - [ ] Mensagem de erro aparece

---

## 🎯 RESUMO DE BUGS CONHECIDOS (CORRIGIDOS)

### ✅ Bugs Corrigidos Nesta Versão:

1. ✅ **Threat Map sem camadas** - CORRIGIDO
   - O mapa estava cinza/branco
   - Fix: Removido lazy loading do TileLayer

2. ✅ **Botão "VOLTAR VÉRTICE" não funcionava** - CORRIGIDO
   - Clique não retornava ao menu principal
   - Fix: Mudado de `setCurrentView('operator')` para `setCurrentView('main')`

---

## 📝 COMO REPORTAR BUGS

Se você encontrar um bug durante os testes:

1. **Anote:**
   - Módulo onde ocorreu
   - Passos para reproduzir
   - Mensagem de erro (se houver)
   - Screenshot (se possível)

2. **Console:**
   - Pressione F12
   - Vá em "Console"
   - Copie erros em vermelho

3. **Reporte:**
   - Crie um arquivo: `BUG_REPORT_[DATA].md`
   - Descreva detalhadamente

---

## 🚀 PRÓXIMOS PASSOS APÓS TESTES

Após completar todos os testes:

1. Marque todos os checkboxes ✅
2. Conte quantos bugs encontrou
3. Relate ao desenvolvedor
4. Faça testes de regressão após correções

---

**Data da Última Atualização:** 01/10/2025
**Versão do Sistema:** v2.1.0
**Testado por:** _____________
**Data do Teste:** _____________

---

## 💡 DICAS PARA TESTERS

- ✅ Teste SEMPRE com o console aberto (F12)
- ✅ Teste CADA funcionalidade ao menos 2x
- ✅ Tente "quebrar" o sistema (inputs inválidos)
- ✅ Teste em diferentes resoluções de tela
- ✅ Recarregue a página entre módulos
- ✅ Limpe o cache se algo estranho acontecer (Ctrl+Shift+Del)

---

**FIM DO GUIA DE TESTES**
