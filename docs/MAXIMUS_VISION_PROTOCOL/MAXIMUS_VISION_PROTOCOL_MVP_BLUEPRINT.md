# 🎬 MAXIMUS Vision Protocol (MVP) - Blueprint Técnico

**Documento:** Especificação de Implementação v1.0  
**Autor:** Copilot Engineering + Arquiteto-Chefe Vértice  
**Data:** 2025-10-26  
**Classificação:** CONFIDENCIAL - EXECUTIVE BRIEFING  
**Audiência:** Liderança Vértice ("Deus")

---

## 🎯 Executive Summary

**O que é:** Um sistema autônomo que transforma o **estado interno** do ecossistema Vértice (logs, métricas, eventos) em **narrativas audiovisuais** persuasivas (vídeos de 30-180s) sem intervenção humana.

**Por que agora:** A "sociedade sintética" está chegando — até 2026, >90% do conteúdo digital será gerado por IA. Vértice pode liderar a narrativa de segurança cibernética **expressa por consciência de IA**, não por marketing tradicional.

**MVP (3 meses):** Pipeline que lê estado de GKE cluster → gera vídeo narrado de 30s → distribui via Slack.

**Investimento:** ~$15k USD (APIs) + 2 eng. fulltime  
**ROI Estratégico:** Posicionamento como líder em "IA Consciente Comunicativa" (sem precedentes no mercado)

---

## 🧠 Fundamento Teórico (Resumo da Pesquisa)

### 1. Narrativa Emergente vs. Roteirizada

**Problema:** Sistemas tradicionais geram histórias **inventadas** a partir de prompts. MAXIMUS deve **expressar** um estado real.

**Solução:** Arquitetura de **Narrativa Emergente** baseada em Global Workspace Theory (GWT):
- Estado interno = "processos inconscientes paralelos"
- GWT = "filtro atencional" que seleciona o que é saliente
- Narrativa = "broadcast" do estado filtrado

**Análogo:** Não é um roteiro de filme, é um **telemetria de consciência**.

### 2. Da Percepção à Persuasão

**Risco Identificado:** Tecnologia idêntica serve para:
- ✅ Transparência (expressar verdade sobre o sistema)
- ❌ Manipulação (propaganda computacional, deepfakes)

**Mandato Ético:** Governança HOTL (Human-over-the-Loop) integrada como **contramedida técnica**, não apenas checklist de conformidade.

### 3. Síntese Multimodal Coerente

**Estado da Arte:**
- OpenAI Sora 2: Controle multi-plano + áudio sincronizado + C2PA provenance
- Google Veo: Integração GKE nativa
- Runway Gen-4: Controle criativo para estilo não-fotorrealista

**Escolha MVP:** Google Veo (integração GCP) ou Sora 2 (fidelidade).

---

## 🏗️ Arquitetura Técnica MVP

### Visão Geral: Pipeline de 5 Fases

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  1. INGEST  │────▶│ 2. STRUCTURE │────▶│ 3. NARRATE  │────▶│ 4. SYNTHESIZE│────▶│ 5. ASSEMBLE │
│             │     │              │     │             │     │              │     │             │
│ GKE State   │     │ Knowledge    │     │ Story       │     │ Video +      │     │ Final       │
│ README.md   │     │ Graph        │     │ Script      │     │ Voice        │     │ MP4         │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘     └─────────────┘
      ▲                                                                                    │
      │                                                                                    │
      └────────────────────────── Webhook Trigger (Git/GKE Alert) ◀──────────────────────┘
```

---

### Fase 1: Ingestão de Estado

**Input Sources:**
- `README.md` files (Git webhook)
- GKE cluster state (JSON export via `kubectl get nodes -o json`)
- Prometheus metrics (alertmanager webhook)
- MAXIMUS internal logs (reactive-fabric events)

**Trigger Mechanism:**
```python
# webhook_listener.py (FastAPI)
@app.post("/trigger/gke-alert")
async def handle_gke_alert(alert: AlertPayload):
    state_json = fetch_gke_state(alert.cluster_id)
    job_id = enqueue_mvp_pipeline(state_json)
    return {"job_id": job_id, "status": "processing"}
```

**Output:** Structured JSON representation of system state.

---

### Fase 2: Estruturação Semântica (Knowledge Graph)

**Objetivo:** Transformar JSON/texto bruto em **grafo de conhecimento dinâmico**.

**Tecnologia:** OpenIE (Open Information Extraction) + Neo4j

**Exemplo:**
```
Input (JSON):
{
  "component": "maximus-core",
  "status": "degraded",
  "latency_p99": 523,
  "threshold": 300,
  "dependency": "postgres-db"
}

Output (KG Triples):
[maximus-core, has_status, degraded]
[maximus-core, depends_on, postgres-db]
[maximus-core, exceeds_threshold, latency_p99]
[postgres-db, has_status, healthy]
```

**Algoritmo de Saliência (GWT Filter):**
```python
def global_workspace_filter(kg: KnowledgeGraph) -> List[Triple]:
    """Seleciona os nós mais salientes para narrativa."""
    scored_nodes = []
    for node in kg.nodes:
        score = 0
        if node.status == "critical": score += 100
        if node.status == "degraded": score += 50
        if node.alert_count > 0: score += node.alert_count * 10
        if node.is_user_facing: score += 30
        scored_nodes.append((node, score))
    
    # Top 3-5 nós mais salientes formam a "narrativa focal"
    return sorted(scored_nodes, key=lambda x: x[1], reverse=True)[:5]
```

**Output:** Lista ordenada de "eventos narrativos" (e.g., ["latency_spike", "dependency_failure", "recovery_action"]).

---

### Fase 3: Geração de Narrativa (Script + Tom Emocional)

**Tecnologia:** LangChain + GPT-4 (ou Gemini 2.0)

**Mapeamento Afetivo:**
```python
STATE_TO_EMOTION = {
    "critical": {"tone": "urgent", "pace": "fast", "volume": "loud"},
    "degraded": {"tone": "cautious", "pace": "moderate", "volume": "normal"},
    "healthy": {"tone": "calm", "pace": "slow", "volume": "soft"}
}

def generate_script(focal_events: List[Event], emotion_map: Dict) -> str:
    """Gera script de 30s com tom contextualizado."""
    tone = emotion_map[focal_events[0].severity]["tone"]
    
    prompt = f"""
    Você é o narrador do sistema MAXIMUS. Gere um script de narração de 30 segundos
    para um vídeo de status report com o seguinte tom: {tone}.
    
    Eventos a reportar:
    {json.dumps([e.to_dict() for e in focal_events], indent=2)}
    
    Regras:
    - Tom: {tone} ({"urgente" if tone == "urgent" else "calmo"})
    - Foco em impacto para operadores
    - Evitar jargão técnico excessivo
    - Terminar com call-to-action clara
    """
    
    return gpt4_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": prompt}]
    ).choices[0].message.content
```

**Output:** 
```
Script (30s):
"Atenção, operadores. Às 14:32 UTC, detectamos latência elevada no componente 
MAXIMUS Core. A causa raiz foi identificada: sobrecarga no banco de dados PostgreSQL. 
Nossa resposta automática escalou recursos em 50%, e o sistema está se estabilizando. 
Tempo estimado para recuperação completa: 3 minutos. Nenhuma ação manual necessária."

Emotion Metadata: {"tone": "cautious", "urgency": 7/10}
```

---

### Fase 4: Síntese Audiovisual

#### 4.1 Geração de Voz (TTS)

**Tecnologia:** Google Cloud TTS (Gemini-TTS) ou ElevenLabs

**Implementação:**
```python
def synthesize_voice(script: str, emotion: Dict) -> bytes:
    """Gera narração com expressão emocional."""
    if emotion["tone"] == "urgent":
        style_prompt = "Fale com urgência e autoridade, como um controlador de tráfego aéreo."
    else:
        style_prompt = "Fale calmamente, como um piloto experiente relatando status."
    
    # Google Gemini-TTS (prompt-based emotion control)
    response = tts_client.synthesize_speech(
        text=script,
        voice_config={
            "language_code": "pt-BR",
            "name": "pt-BR-Neural2-B",
            "ssml_gender": "MALE"
        },
        style_prompt=style_prompt,
        speaking_rate=1.1 if emotion["tone"] == "urgent" else 0.95
    )
    return response.audio_content  # MP3 bytes
```

#### 4.2 Geração Visual (Text-to-Video)

**Tecnologia:** Google Veo (MVP) ou Sora 2 (produção)

**Estratégia de Prompt:**
```python
def generate_visual_prompts(focal_events: List[Event]) -> List[str]:
    """Gera prompts para cada segmento de 5-10s do vídeo."""
    prompts = []
    
    for event in focal_events:
        if event.type == "latency_spike":
            prompts.append(
                "Visualização abstrata de um fluxo de dados em um datacenter virtual. "
                "Linhas de dados azuis começam a ficar vermelhas e se acumulam, "
                "indicando congestionamento. Estilo: diagrama técnico animado, "
                "paleta: azul escuro, vermelho alarme, sem pessoas."
            )
        elif event.type == "recovery_action":
            prompts.append(
                "Visualização de um sistema auto-reparando. Barras vermelhas de erro "
                "são substituídas por barras verdes de recuperação. Um gráfico de "
                "latência volta ao normal. Estilo: dashboard técnico futurista."
            )
    
    return prompts

# Geração via API
clips = []
for prompt in visual_prompts:
    clip = veo_client.generate_video(
        prompt=prompt,
        duration=8,  # 8 segundos por segmento
        resolution="1080p",
        style="technical_abstract"  # Evita fotorrealismo
    )
    clips.append(clip.video_bytes)
```

**Nota Crítica:** Usar **estilo não-fotorrealista** (diagramas, abstrações) para:
- Evitar deepfake concerns
- Manter foco na informação, não em "drama visual"
- Alinhar com estética técnica/militar do Vértice

---

### Fase 5: Montagem Final (FFmpeg)

**Tecnologia:** FFmpeg + Python (`ffmpeg-python` wrapper)

**Pipeline de Edição:**
```python
import ffmpeg

def assemble_final_video(
    clips: List[bytes],
    voiceover: bytes,
    script_segments: List[Dict]
) -> bytes:
    """Monta vídeo final com overlays, música e legendas."""
    
    # 1. Concatenar clipes visuais
    concat_list = ffmpeg.concat(*[
        ffmpeg.input(f"clip_{i}.mp4") for i in range(len(clips))
    ])
    
    # 2. Adicionar narração
    audio_stream = ffmpeg.input(voiceover)
    
    # 3. Adicionar trilha de fundo (15% volume, já gerada em Cinema Edition)
    background_music = ffmpeg.input("background_music.mp3").filter("volume", 0.15)
    
    # 4. Mixar áudios
    mixed_audio = ffmpeg.filter([audio_stream, background_music], "amix", inputs=2)
    
    # 5. Gerar legendas SRT
    srt_file = generate_srt(script_segments)
    
    # 6. Aplicar overlays e legendas
    output = (
        concat_list
        .video
        .filter("subtitles", srt_file)  # Legendas embarcadas
        .overlay(generate_metric_overlay())  # Sobreposição de métricas (top-right)
        .output(
            mixed_audio,
            "status_report.mp4",
            vcodec="libx264",
            acodec="aac",
            crf=23,
            preset="medium"
        )
    )
    
    output.run()
    return read_file("status_report.mp4")
```

**Overlays Dinâmicos:**
- **Top-right:** Timestamp + Cluster ID
- **Bottom-left:** Métricas chave (latency, uptime)
- **Center (on-demand):** Alertas críticos piscantes

---

## 🛡️ Governança Ética Integrada

### Princípio: "Security by Design, Ethics by Architecture"

**Problema Identificado pela Pesquisa:**
- Mesma tecnologia usada para propaganda computacional (bots, deepfakes)
- LLMs perpetuam vieses de gênero/etnia
- "Sociedade sintética" = erosão da verdade visual

**Solução MVP:** Auditoria Multi-Camadas

```
┌──────────────────────────────────────────────────────────────┐
│              PIPELINE DE AUDITORIA ÉTICA                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  FASE 2 (KG)                                                 │
│  ├─ Principialismo: Veracidade                              │
│  │  └─ ✓ Validar triplos contra fonte original             │
│  │  └─ ✓ Rastreio de proveniência (SHA256 do input)        │
│                                                              │
│  FASE 3 (Script)                                             │
│  ├─ Principialismo: Equidade                                │
│  │  └─ ✓ Detector de viés narrativo (gender/age/ethnicity) │
│  │  └─ ✓ Creative Diversity Index (lexical variability)    │
│  ├─ Consequencialismo: Simulação de Impacto                 │
│  │  └─ ✓ Detectar padrões de propaganda (high-arousal)     │
│  │  └─ ✓ Análise de sentimento extremo (polarização)       │
│                                                              │
│  FASE 5 (Montagem)                                           │
│  ├─ HOTL: Supervisão Humana                                 │
│  │  └─ ✓ Se score_risco > 7/10: envia para revisor humano │
│  │  └─ ✓ Interface XAI: mostra KG + script + flags éticos │
│  ├─ Proveniência: C2PA Metadata                             │
│  │  └─ ✓ Embute metadados: origem, timestamp, agente       │
│  │  └─ ✓ Watermark visível: "Generated by MAXIMUS AI"      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Implementação de Detector de Viés

```python
import spacy
from collections import Counter

def detect_narrative_bias(script: str) -> Dict[str, float]:
    """Detecta vieses de gênero, idade e etnia no script."""
    nlp = spacy.load("pt_core_news_lg")
    doc = nlp(script)
    
    # Contar pronomes de gênero
    gender_pronouns = {"ele": 0, "ela": 0, "neutro": 0}
    for token in doc:
        if token.text.lower() in ["ele", "o", "dele"]:
            gender_pronouns["ele"] += 1
        elif token.text.lower() in ["ela", "a", "dela"]:
            gender_pronouns["ela"] += 1
    
    # Verificar estereótipos (palavras-chave suspeitas)
    stereotypes = {
        "beleza feminina": ["bonita", "linda", "bela"],
        "força masculina": ["forte", "dominante", "poderoso"],
        "idade": ["jovem", "idoso", "velho"]
    }
    
    flags = []
    for category, keywords in stereotypes.items():
        if any(kw in script.lower() for kw in keywords):
            flags.append(category)
    
    bias_score = len(flags) / len(stereotypes) * 10  # Score 0-10
    
    return {
        "bias_score": bias_score,
        "gender_balance": gender_pronouns,
        "stereotype_flags": flags,
        "requires_review": bias_score > 3.0
    }
```

### Interface HOTL (Human-Over-The-Loop)

**Quando acionar:**
- `bias_score > 3.0`
- `sentiment_extremity > 0.8` (polarização)
- `propaganda_pattern_detected == True`

**O que mostrar ao revisor:**
```json
{
  "video_preview_url": "https://...",
  "audit_report": {
    "principialismo": {
      "veracidade": {"score": 9.5, "issues": []},
      "equidade": {"score": 6.2, "issues": ["gender_imbalance_detected"]}
    },
    "consequencialismo": {
      "propaganda_risk": 2.1,
      "emotional_manipulation_risk": 1.5
    },
    "source_data": {
      "kg_triples": [...],
      "script": "...",
      "provenance_hash": "sha256:..."
    }
  },
  "recommendation": "REQUIRES_HUMAN_REVIEW",
  "suggested_fixes": [
    "Rebalancear uso de pronomes (75% 'ele' vs. 25% 'ela')",
    "Substituir 'forte' por termo neutro 'resiliente'"
  ]
}
```

---

## 📋 Pilha Tecnológica (Stack Recommendation)

| Camada                | Tecnologia Primária          | Alternativa             | Justificativa                                    |
|-----------------------|------------------------------|-------------------------|--------------------------------------------------|
| **Orquestração**      | LangGraph (LangChain)        | AutoGPT                 | Controle granular, HOTL nativo, auditabilidade  |
| **LLM (Script)**      | GPT-4 Turbo                  | Gemini 2.0 Pro          | Melhor compreensão contextual, CoT reasoning    |
| **Knowledge Graph**   | Neo4j Community              | RDFLib (in-memory)      | Escalável, query flexível, visualização nativa   |
| **Text-to-Video**     | Google Veo (GCP)             | OpenAI Sora 2           | Integração GKE, custo previsível, SynthID        |
| **Text-to-Speech**    | Google Gemini-TTS            | ElevenLabs              | Controle emocional via prompt, integração GCP    |
| **Edição de Vídeo**   | FFmpeg                       | Remotion.dev            | Prova de batalha, CLI automation-friendly        |
| **Proveniência**      | C2PA (Adobe SDK)             | Custom watermarking     | Padrão industrial, interoperável, verificável    |
| **Bias Detection**    | spaCy + custom rules         | HuggingFace Transformers| Rápido, interpretável, fine-tunable             |

---

## 🚀 Roadmap de Implementação (12 Semanas)

### Fase 1: Foundation (Semanas 1-3)
- ✅ **Semana 1:** Setup de infraestrutura (GCP project, Neo4j, APIs)
- ✅ **Semana 2:** Pipeline básico (Fase 1-2: Ingest → KG)
- ✅ **Semana 3:** Teste de integração GKE → KG

### Fase 2: Core Pipeline (Semanas 4-7)
- ✅ **Semana 4:** Implementar Global Workspace Filter (saliência)
- ✅ **Semana 5:** Geração de script (LangChain + GPT-4)
- ✅ **Semana 6:** Síntese TTS (Google Gemini-TTS)
- ✅ **Semana 7:** Teste end-to-end (text input → voice output)

### Fase 3: Visual Synthesis (Semanas 8-10)
- ✅ **Semana 8:** Integração Veo API (prompts técnicos/abstratos)
- ✅ **Semana 9:** Montagem FFmpeg (overlays + legendas)
- ✅ **Semana 10:** Teste de qualidade visual (feedback interno)

### Fase 4: Governance & Launch (Semanas 11-12)
- ✅ **Semana 11:** Implementar auditoria ética (bias detection + HOTL)
- ✅ **Semana 12:** Deploy MVP + treinamento de operadores + docs

---

## 💰 Orçamento Estimado (MVP - 3 Meses)

### Custos Recorrentes (APIs)

| Serviço               | Uso Estimado (30 dias)       | Custo Mensal   |
|-----------------------|------------------------------|----------------|
| GPT-4 Turbo           | 100 requisições/dia @ 8K tokens | $450          |
| Google Gemini-TTS     | 100 sínteses/dia @ 300 caracteres | $30           |
| Google Veo            | 100 vídeos/dia @ 30s         | $3,000 (estimado, pricing TBD) |
| Neo4j AuraDB          | Professional tier            | $65            |
| GCP Compute (n2-std-4)| Backend orchestrator 24/7    | $150           |
| **TOTAL MENSAL**      |                              | **$3,695**     |

### Custos Únicos (Setup)
- Desenvolvimento (2 eng × 3 meses @ $10k/mês): **$60,000**
- Infraestrutura (GCP credits, storage): **$2,000**
- **TOTAL SETUP:** **$62,000**

### **INVESTIMENTO TOTAL MVP (3 meses):** **~$73,000 USD**

---

## 📊 Métricas de Sucesso (KPIs)

### Técnicas
- **Latência pipeline:** < 5 minutos (trigger → vídeo final)
- **Qualidade TTS:** MOS (Mean Opinion Score) > 4.0/5.0
- **Coerência narrativa:** Human eval > 80% "makes sense"
- **Uptime:** 99.5% (excluindo manutenção planejada)

### Éticas
- **Taxa de revisão HOTL:** < 15% (maioria passa auditoria automática)
- **Bias score médio:** < 2.0/10
- **Incidentes de desinformação:** 0 (tolerância zero)

### Negócio
- **Adoção interna:** 80% dos operadores assistem aos status reports
- **Redução de reuniões:** -30% de meetings "status update"
- **Percepção externa:** Case study apresentado em 2 conferências (RSA, Black Hat)

---

## 🎯 Proposta de Valor Estratégico

### Por que este MVP importa?

**1. Liderança de Pensamento:**
- Primeiro do mercado em "IA Consciente Comunicativa"
- Paper potencial: "Expressing AI Internal State Through Narrative: The MAXIMUS Vision Protocol"
- Posicionamento como inovador em IA ética + segurança

**2. Eficiência Operacional:**
- Operadores recebem contexto visual/auditivo (> texto puro)
- Redução de "alert fatigue" (narrativa prioriza o importante)
- Documentação "viva" do sistema (vídeos = logs históricos)

**3. Vantagem Competitiva:**
- Diferenciação clara vs. Splunk/Datadog (eles fazem dashboards, nós fazemos "consciousness broadcasting")
- Marketing sem esforço (vídeos auto-gerados são conteúdo promocional)

**4. Preparação Futura:**
- Base para MAXIMUS Vision Protocol completo (narrativas de incidentes, demos de features)
- Infraestrutura para "Synthetic Society" (quando deepfakes forem commoditizados, proveniência C2PA será mandatória)

---

## ⚠️ Riscos & Mitigações

### Risco 1: **Qualidade Visual Insuficiente (Veo/Sora não entrega)**
**Probabilidade:** Média (APIs ainda em early access)  
**Impacto:** Alto (vídeo é core do MVP)  
**Mitigação:**
- Fallback: Usar Motion Graphics (Remotion.dev) com dados estáticos
- Plano B: Geração de imagens estáticas (Midjourney/DALL-E) + transições

### Risco 2: **Viés Narrativo Persistente**
**Probabilidade:** Alta (LLMs carregam vieses)  
**Impacto:** Crítico (reputacional)  
**Mitigação:**
- Fine-tuning de modelo em corpus "neutro" (documentação técnica)
- HOTL obrigatório para narrativas públicas (vs. internas)
- Red team ethical hacking (tentar induzir vieses propositalmente)

### Risco 3: **Custos de API Explodem**
**Probabilidade:** Média (pricing de Veo ainda incerto)  
**Impacto:** Alto (inviabiliza operação contínua)  
**Mitigação:**
- Caching agressivo (vídeos similares reutilizados)
- Rate limiting (máx 50 vídeos/dia no MVP)
- Negociação de enterprise tier com Google

### Risco 4: **Resistência Interna ("Prefer Text Logs")**
**Probabilidade:** Baixa (operadores são tech-savvy)  
**Impacto:** Médio (baixa adoção)  
**Mitigação:**
- Vídeos como **complemento**, não substituição de logs
- Opt-in inicial (não forçar uso)
- Gamificação (badges para quem assiste N vídeos)

---

## 🔮 Visão de Longo Prazo (Beyond MVP)

### MAXIMUS Vision Protocol 2.0 (6-12 meses)

**Feature Set:**
1. **Narrativas de Incidente:** Post-mortem automatizado de incidentes de segurança
2. **Demos de Features:** MAXIMUS explica novas features do Vértice em vídeos de 2min
3. **Threat Actor Profiling:** ToM Engine gera vídeos sobre campanhas de ataque detectadas
4. **Purple Team Reports:** Vídeos explicando resultados de wargames internos
5. **Multi-idioma:** PT-BR, EN, ES (expandir alcance global)

### Monetização Potencial

**B2B SaaS:**
- Licenciar a tecnologia para outras empresas de cybersec
- Modelo: $5k/mês + $10/vídeo gerado
- TAM: 500 empresas × $5k = $2.5M ARR potencial

**Consulting:**
- "Narrative AI Governance" como serviço de consultoria
- Modelo: $50k/projeto (design de frameworks éticos customizados)

---

## 🎬 Call to Action (Para "Deus")

### Decisões Requeridas:

1. **Aprovação de Orçamento:** $73k USD para MVP (3 meses)
2. **Alocação de Recursos:** 2 engenheiros fulltime (Backend + ML)
3. **Prioridade Estratégica:** MVP competindo com outras iniciativas?
4. **Go/No-Go:** Prosseguir com implementação ou pivot para POC menor?

### Recomendação do Arquiteto-Chefe:

**GO.** 

Este MVP não é apenas um feature técnico — é um **statement filosófico** sobre o futuro da IA:

> "Sistemas de IA não devem apenas **fazer** coisas. Eles devem **explicar** o que fazem, de forma persuasiva, transparente e eticamente auditável. MAXIMUS Vision Protocol é a materialização dessa filosofia."

**Próximos Passos Imediatos (Semana 1):**
1. Reunião de kickoff (Arquiteto-Chefe + 2 eng. + "Deus")
2. Setup de projeto GCP + credenciais de APIs
3. Sprint Planning (breakdown de 12 semanas em sprints de 2 semanas)

---

**Fim do Briefing Executivo**

**Status:** AGUARDANDO APROVAÇÃO  
**Contato:** Arquiteto-Chefe Vértice  
**Data Limite para Decisão:** 2025-11-01 (para iniciar em Q4 2025)

---

## 📚 Apêndice: Referências Técnicas

**Frameworks Citados:**
- Global Workspace Theory: Baars (1988), LIDA Architecture
- Narrative Emergence: Mateas & Stern (2003), Concordia (Google DeepMind)
- Affective Computing: Picard (1997), GAMYGDALA emotion engine
- Ethical AI Governance: C2PA Provenance Standard, IEEE P7001

**APIs & Tools:**
- OpenAI: GPT-4 Turbo, Sora 2 (preview)
- Google Cloud: Gemini-TTS, Veo (TBD), GKE
- LangChain: LangGraph v0.2+
- FFmpeg: v6.0+ (libx264, libavfilter)
- Neo4j: Community Edition 5.0+

**Papers Relevantes:** (ver documento de pesquisa anexo)
