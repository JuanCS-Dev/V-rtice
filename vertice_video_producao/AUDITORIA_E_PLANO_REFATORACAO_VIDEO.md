# 🔍 AUDITORIA E PLANO DE REFATORAÇÃO - VÉRTICE VIDEO PRODUCTION

**Data:** 2025-10-26  
**Status:** DIAGNÓSTICO COMPLETO  
**Aderência:** Constituição Vértice v2.7 (Artigo I, VI, Anexo E)

---

## 📊 DIAGNÓSTICO - ESTADO ATUAL

### ✅ O QUE ESTÁ FUNCIONANDO:

1. **Text-to-Speech (GCP):**
   - ✅ API habilitada e autenticada
   - ✅ Roteiro com textos válidos (inglês, 11 cenas)
   - ✅ Script usando credenciais corretas (`gcloud auth print-access-token`)
   - ✅ Formato JSON do payload conforme docs Google Cloud

2. **Frontend:**
   - ✅ Rodando em `localhost:5173`
   - ✅ Título correto: "Vértice - Cybersecurity Platform"

3. **Playwright:**
   - ✅ Chromium instalado (build v1194)
   - ✅ Config com gravação em Full HD (1920x1080)
   - ✅ Timeout adequado (240s)

---

## ❌ GAPS CRÍTICOS IDENTIFICADOS

### **GAP #1: Vídeo com 14s em vez de 180s**

**Sintoma:**
```
duration=14.120000 (esperado: 180.0)
```

**Causa-raiz:**
- Playwright grava vídeo corretamente, MAS o arquivo final está sendo cortado/comprimido incorretamente
- O script `montagem_final.sh` não está usando o vídeo bruto correto

**Evidência:**
```bash
# Vídeo do Playwright é salvo em:
test-results/vertice-frontend-tour-chromium/video.webm

# Mas script montagem_final.sh procura por:
video_bruto.mp4  # ❌ ARQUIVO INEXISTENTE
```

---

### **GAP #2: Roteiro desalinhado com arquitetura real**

**Esperado (baseado em POSTER):**
1. Landing Page (Vértice intro)
2. MAXIMUS Dashboard (AI Consciousness)
3. Consciousness Tab (ToM, metrics)
4. Offensive Dashboard (penetration testing)
5. Offensive Modules (exploits, vulns)
6. Defensive Dashboard (immune system)
7. Defensive Metrics (threat neutralization)
8. Chat NLP (natural language interface)
9. Monitoring Overview (observability)
10. Return to Landing (finale)

**Atual (roteiro_FINAL.json):**
- ❌ Menciona módulos inexistentes: `purple`, `cockpit`, `osint`
- ❌ Não menciona: Chat NLP, Monitoring

**Impacto:**
- Playwright tenta clicar em `[data-testid="nav-purple-dashboard"]` → **FALHA**
- Timeout → Vídeo é cortado

---

### **GAP #3: Extração de vídeo do Playwright**

**Problema:**
- `extrair_video_playwright.sh` procura vídeo em path errado
- Não verifica se o arquivo foi realmente extraído antes de passar para montagem

---

### **GAP #4: Montagem FFmpeg não tem validação de inputs**

**Problema:**
- `montagem_final.sh` assume que `video_bruto.mp4` e todos os `cena_N.mp3` existem
- Se 1 áudio faltar → FFmpeg falha silenciosamente

---

## 🛠️ PLANO DE REFATORAÇÃO (EXECUÇÃO)

### **FASE 1: Corrigir roteiro (alinhamento com POSTER)**

**Ação:**
- Reescrever `roteiro_FINAL.json` com:
  - 10 cenas (180s total)
  - Módulos existentes no frontend: `maximus`, `offensive`, `defensive`
  - Landing page com scrolls cinematográficos

**Output:** `roteiro_v4_aligned.json`

---

### **FASE 2: Corrigir script Playwright**

**Ação:**
- Remover navegação para módulos inexistentes
- Adicionar navegação para Chat e Monitoring
- Garantir que TODAS as cenas esperem o tempo exato do roteiro

**Output:** `video_tour_v4.spec.ts`

---

### **FASE 3: Corrigir extração de vídeo**

**Ação:**
- Script deve:
  1. Procurar vídeo em `test-results/.../video.webm`
  2. Converter para MP4 com FFmpeg
  3. Validar duração (deve ser ~180s)
  4. Se duração < 170s → ERRO e abortar

**Output:** `extrair_video_v2.sh`

---

### **FASE 4: Corrigir montagem final**

**Ação:**
- Validar que todos os inputs existem ANTES de iniciar FFmpeg
- Usar filtro `concat` para áudios com padding de silêncio se necessário
- Aplicar `drawtext` apenas se houver texto na cena

**Output:** `montagem_final_v2.sh`

---

### **FASE 5: Script orchestrator unificado**

**Ação:**
- Criar `MATERIALIZAR_VIDEO_FINAL.sh` que:
  1. Valida ambiente (`check_ambiente.sh`)
  2. Gera narração (TTS)
  3. Grava tour (Playwright)
  4. Extrai vídeo (validação de duração)
  5. Monta vídeo final (validação de inputs)
  6. Gera thumbnail e preview

**Output:** `MATERIALIZAR_VIDEO_FINAL.sh`

---

## 🎯 MÉTRICAS DE SUCESSO

**Validação tripla (Cláusula 3.3):**

1. **Análise estática:**
   - ✅ Bash scripts com `shellcheck`
   - ✅ TypeScript com compilação sem erros

2. **Testes:**
   - ✅ Vídeo final com duração entre 178-182s
   - ✅ 11 arquivos de áudio gerados (1 por cena)
   - ✅ Resolução 1920x1080

3. **Conformidade doutrinária:**
   - ✅ Sem TODOs ou placeholders
   - ✅ Todos os módulos mencionados existem no frontend
   - ✅ Roteiro alinhado com POSTER

---

## 🚨 BLOQUEADORES

**Nenhum.** Todos os problemas têm solução técnica clara.

---

**PRÓXIMO PASSO:** Aguardar aprovação do Arquiteto-Chefe para iniciar refatoração.
