# 🧠 VÉRTICE AI-FIRST ARCHITECTURE
## A IA no Coração da Plataforma

---

## 🎯 **FILOSOFIA AI-FIRST**

**"A IA não é um add-on. A IA É o sistema."**

O Vértice foi refatorado para ser **AI-FIRST**. A IA não é apenas um chatbot - é um agente autônomo com acesso maestro a TODOS os serviços da plataforma através de **tool calling (function calling)**.

### **O que é Tool Calling?**
Igual ao Claude Code, a IA pode:
- ✅ **Chamar funções/ferramentas** para executar ações reais
- ✅ **Acessar todos os serviços** (threat intel, malware analysis, nmap, osint, etc)
- ✅ **Tomar decisões autônomas** sobre quais tools usar
- ✅ **Executar investigações completas** sem intervenção humana
- ✅ **Aprender e adaptar** baseado em resultados

---

## 🏗️ **ARQUITETURA**

```
┌─────────────────────────────────────────────────────┐
│                    USUÁRIO                          │
│              (Frontend React)                       │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              API GATEWAY (Port 8000)                │
│         Rate Limiting │ Auth │ Routing              │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│          🧠 AI AGENT SERVICE (Port 8017)           │
│                  THE BRAIN                          │
│                                                      │
│  ┌──────────────────────────────────────────────┐  │
│  │       LLM (Claude/GPT)                       │  │
│  │   with Tool Calling Support                  │  │
│  └──────────────────────────────────────────────┘  │
│                     │                                │
│                     ▼                                │
│  ┌──────────────────────────────────────────────┐  │
│  │         TOOL REGISTRY                        │  │
│  │    10+ Tools para acessar serviços          │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
  ┌─────────┐  ┌─────────┐  ┌──────────┐
  │Threat   │  │Malware  │  │  Nmap    │
  │Intel    │  │Analysis │  │  Scan    │
  │(8013)   │  │(8014)   │  │  (8010)  │
  └─────────┘  └─────────┘  └──────────┘
        │            │            │
        └────────────┼────────────┘
                     │
      [+ 10 outros serviços: SSL, OSINT, Vuln Scanner, etc]
```

---

## 🛠️ **TOOLS DISPONÍVEIS**

A AI tem acesso a **10 ferramentas principais**:

### **1. analyze_threat_intelligence**
- **O que faz**: Analisa ameaças de IPs, domínios, hashes, URLs
- **Sistema**: Offline-first com database local
- **Retorna**: Threat score (0-100), reputação, recomendações
- **Exemplo**: "Analise o IP 8.8.8.8"

### **2. analyze_malware**
- **O que faz**: Analisa malware via hash (MD5/SHA1/SHA256)
- **Sistema**: Offline-first com heurísticas avançadas
- **Retorna**: Malicioso ou não, família de malware, severidade
- **Exemplo**: "Verifique se este hash é malware: 44d88612..."

### **3. check_ssl_certificate**
- **O que faz**: Análise profunda de certificados SSL/TLS
- **Verifica**: Vulnerabilidades, compliance (PCI-DSS, HIPAA, NIST)
- **Retorna**: Security score, grade (A+ a F), problemas encontrados
- **Exemplo**: "Analise o certificado SSL de google.com"

### **4. get_ip_intelligence**
- **O que faz**: Intelligence completo de IP
- **Retorna**: Geolocalização, ISP, ASN, hostname, organização
- **Exemplo**: "Onde fica localizado o IP 1.1.1.1?"

### **5. scan_ports_nmap**
- **O que faz**: Scan de portas com Nmap
- **Modos**: Quick (top 100), Full (todas), Stealth (furtivo)
- **Retorna**: Portas abertas, serviços, versões, vulnerabilidades
- **Exemplo**: "Faça um scan rápido em scanme.nmap.org"

### **6. scan_vulnerabilities**
- **O que faz**: Scan de vulnerabilidades conhecidas
- **Retorna**: CVEs, severidade, exploits conhecidos, patches
- **Exemplo**: "Escaneie vulnerabilidades em example.com"

### **7. lookup_domain**
- **O que faz**: Lookup completo de domínio
- **Retorna**: WHOIS, DNS records, subdomains, histórico
- **Exemplo**: "Faça lookup completo de github.com"

### **8. predict_crime_hotspots**
- **O que faz**: Predição de criminalidade com IA
- **Usa**: Machine Learning (DBSCAN clustering)
- **Retorna**: Hotspots de risco, scores, locais críticos
- **Exemplo**: "Analise estes dados de crime e preveja hotspots"

### **9. osint_username**
- **O que faz**: Investigação OSINT de username
- **Busca em**: Múltiplas plataformas sociais
- **Retorna**: Perfis encontrados, informações públicas
- **Exemplo**: "Investigue o username 'johndoe123'"

### **10. investigate_comprehensive**
- **O que faz**: Investigação COMPLETA automatizada
- **Usa**: Aurora Orchestrator (orquestra múltiplos serviços)
- **Executa**: Threat intel, malware, SSL, nmap, vulns em paralelo
- **Retorna**: Análise agregada com threat assessment final
- **Exemplo**: "Faça uma investigação completa de suspicious-site.com"

---

## 💬 **COMO USAR**

### **Endpoint Principal: `/api/ai/chat`**

```bash
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Analise o IP 8.8.8.8 e me diga se é seguro"
      }
    ]
  }'
```

**O que acontece:**
1. A AI recebe sua pergunta
2. Decide autonomamente usar a tool `analyze_threat_intelligence`
3. Executa a análise offline-first
4. Retorna resposta humanizada com dados REAIS

### **Exemplo de Resposta:**
```json
{
  "response": "Analisei o IP 8.8.8.8 (Google Public DNS). \n\nResultados:\n- Threat Score: 0/100\n- Reputação: CLEAN\n- Status: Whitelisted (Google)\n- Recomendação: ✅ IP seguro, não representa ameaça\n\nO IP está na whitelist de serviços conhecidos e não apresenta nenhuma atividade maliciosa.",
  "tools_used": [
    {
      "tool_name": "analyze_threat_intelligence",
      "tool_input": {"target": "8.8.8.8"},
      "result": { ... }
    }
  ],
  "timestamp": "2025-09-30T03:30:00"
}
```

---

## 🚀 **CASOS DE USO**

### **Caso 1: Análise Conversacional**
```
User: "Esse IP 1.2.3.4 é suspeito?"
AI: [usa tool analyze_threat_intelligence]
AI: "Sim, detectei atividade maliciosa..."
```

### **Caso 2: Investigação Completa Autônoma**
```
User: "Investigue completamente o domínio malware-site.com"
AI: [usa tool investigate_comprehensive]
AI: [executa 8+ análises em paralelo]
AI: "Análise completa concluída. CRÍTICO: Site malicioso detectado..."
```

### **Caso 3: Multi-Tool Reasoning**
```
User: "Analise esta URL: http://suspicious.tk/download.exe"
AI: [decide autonomamente]
AI: [usa check_ssl_certificate - SSL inválido]
AI: [usa analyze_threat_intelligence - domínio suspeito]
AI: [usa analyze_malware para o hash do arquivo]
AI: "ALERTA: Esta URL é ALTAMENTE SUSPEITA..."
```

### **Caso 4: Predição de Criminalidade**
```
User: "Analise estes crimes e me diga onde teremos mais problemas"
AI: [usa predict_crime_hotspots com ML]
AI: "Identifiquei 3 hotspots críticos. O mais perigoso é..."
```

---

## 🔧 **CONFIGURAÇÃO**

### **1. Obter API Key do LLM**

**Anthropic Claude (Recomendado):**
```bash
# Acesse: https://console.anthropic.com/
# Crie uma API key
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Ou OpenAI GPT:**
```bash
# Acesse: https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-..."
```

### **2. Configurar no Docker**
```bash
# Edite .env na raiz do projeto
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env
echo "LLM_PROVIDER=anthropic" >> .env
```

### **3. Iniciar o Serviço**
```bash
docker compose up -d ai_agent_service
```

### **4. Testar**
```bash
# Verificar se está online
curl http://localhost:8017/

# Listar tools disponíveis
curl http://localhost:8017/tools

# Fazer uma pergunta
curl -X POST http://localhost:8000/api/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{
      "role": "user",
      "content": "Analise o hash EICAR: 44d88612fea8a8f36de82e1278abb02f"
    }]
  }'
```

---

## 📊 **MÉTRICAS E MONITORAMENTO**

### **Service Health**
```bash
curl http://localhost:8017/health
```

### **Tools Disponíveis**
```bash
curl http://localhost:8017/tools
```

### **Via API Gateway**
```bash
curl http://localhost:8000/api/ai/
curl http://localhost:8000/api/ai/tools
```

---

## 🎓 **EXEMPLOS DE PROMPTS**

### **Análise de Ameaças**
- "Analise o IP 192.168.1.1"
- "Este hash é malware? 44d88612fea8a8f36de82e1278abb02f"
- "Verifique se suspicious-site.com é seguro"

### **Scanning**
- "Faça um scan de portas em scanme.nmap.org"
- "Escaneie vulnerabilidades em meu servidor"
- "Verifique o certificado SSL de google.com"

### **OSINT**
- "Investigue o username 'hacker123'"
- "Busque informações sobre o domínio example.com"
- "Faça uma busca completa sobre este email"

### **Predição**
- "Analise estes crimes e preveja hotspots"
- "Onde teremos mais problemas de segurança?"

### **Investigação Completa**
- "Investigue completamente 1.2.3.4"
- "Faça uma análise full de malware-domain.com"
- "Preciso de um relatório completo sobre este target"

---

## 🔒 **SEGURANÇA E PRIVACIDADE**

### **Dados Sensíveis**
- ✅ A AI **NÃO armazena** conversas permanentemente
- ✅ Todas as análises usam **offline-first** (dados não saem do servidor)
- ✅ APIs externas são **OPCIONAIS**

### **Rate Limiting**
- 10 requests/minuto no endpoint `/api/ai/chat`
- 30 requests/minuto nos outros endpoints

### **Authentication**
- Integrado com sistema de auth do API Gateway
- JWT tokens obrigatórios para uso em produção

---

## 🚧 **ROADMAP**

### **Fase 1: ✅ COMPLETO**
- [x] Tool calling framework
- [x] 10 tools principais
- [x] Integração com Claude/GPT
- [x] API conversacional

### **Fase 2: Em Desenvolvimento**
- [ ] WebSocket para streaming de respostas
- [ ] Memória de conversação (context persistence)
- [ ] Custom tools definidas pelo usuário
- [ ] Fine-tuning com dados do Vértice

### **Fase 3: Futuro**
- [ ] Multi-agent collaboration
- [ ] Automated playbooks
- [ ] Self-learning from investigations
- [ ] Integration with SIEM

---

## 💡 **DIFERENCIAL DO VÉRTICE**

### **Outras Plataformas:**
- 🤷 AI como chatbot básico
- 🤷 Respostas genéricas sem dados reais
- 🤷 Sem acesso aos serviços
- 🤷 Apenas FAQ e suporte

### **Vértice AI-FIRST:**
- ✅ AI como agente autônomo
- ✅ Respostas com dados REAIS dos serviços
- ✅ Acesso maestro a 10+ ferramentas
- ✅ Executa investigações completas
- ✅ Toma decisões inteligentes
- ✅ Offline-first (privacidade)

---

## 📞 **SUPPORT**

### **Troubleshooting**
```bash
# AI não responde
docker logs vertice-ai-agent

# Verificar se LLM está configurado
curl http://localhost:8017/ | grep llm_configured
```

### **API Key Issues**
Se não houver API key configurada, o serviço retorna:
```
⚠️ LLM não configurado. Configure ANTHROPIC_API_KEY ou OPENAI_API_KEY
```

---

**Built with 🧠 by Juan Carlos & Claude Code**
**Vértice AI-FIRST - A IA no Coração da Plataforma**