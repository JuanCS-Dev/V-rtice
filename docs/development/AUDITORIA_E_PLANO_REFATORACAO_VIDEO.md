# 🔍 AUDITORIA CONSTITUCIONAL + PLANO DE REFATORAÇÃO
## Sistema de Produção de Vídeo Vértice

**Data:** 2025-10-26  
**Executor:** Co-Arquiteto Cético (IA)  
**Status:** ⏸️ PAUSE MODE (Artigo I, Cláusula 3.4)  
**Conformidade:** Artigo I (Célula de Desenvolvimento Híbrida)

---

## 📊 RESUMO EXECUTIVO

**Status Atual:** ❌ PIPELINE INOPERANTE  
**Causa Raiz:** Múltiplos field name mismatches entre roteiro.json e scripts  
**Impacto:** Vídeo final gerado com 0 bytes (inválido)  
**Quota Gasta:** ~11 chamadas Google TTS (dentro do Free Tier)  
**Gaps Críticos:** 5 identificados

---

## 🔴 GAPS CRÍTICOS IDENTIFICADOS

### **GAP-001: Field Name Mismatch (timestamp)** 🔥 CRÍTICO
**Componente:** `montagem_final.sh` (Linha 166)  
**Problema:**
- Script busca: `.cenas[].timestamp`
- Roteiro possui: `.cenas[].timestamp_inicio` e `.cenas[].timestamp_fim`
- Resultado: `jq` retorna `null` → expressões alpha quebram → FFmpeg falha

**Impacto:** 
- ❌ Fase 5 (overlay de texto) falha completamente
- ❌ `video_final.mp4` gerado vazio (8KB, moov atom not found)

**Evidência:**
```bash
$ jq -r '.cenas[0].timestamp' roteiro.json
null
$ jq -r '.cenas[0].timestamp_inicio' roteiro.json
0
```

---

### **GAP-002: Arquivos Intermediários Não Persistem** 🔥 CRÍTICO
**Componente:** `montagem_final.sh` (Linha 189 - cleanup)  
**Problema:**
- Script limpa `video_sem_audio.mp4` e `video_com_audio.mp4` AO FINAL
- Mas se FASE 5 falha, esses arquivos são deletados ANTES de debug
- Impossível diagnosticar onde pipeline quebrou

**Impacto:**
- ❌ Debugging cego (arquivos intermediários perdidos)
- ❌ Re-execução custosa (precisa rodar FASES 1-4 novamente)

**Solução:** Mover cleanup para DEPOIS de confirmação de sucesso

---

### **GAP-003: Sem Validação de Texto Antes de TTS** ⚠️ MODERADO
**Componente:** `gerar_narracao_gcp.sh` (loop linha 125)  
**Problema:**
- Script NÃO valida se `$TEXTO` é null/vazio antes de chamar API
- Se roteiro tiver `.narracao: null` → gasta quota gerando silêncio

**Impacto:**
- 💰 Desperdício de quota GCP
- ⏱️ Tempo perdido (esperando API responder "null")

**Validação Ausente:**
```bash
# DEVERIA ter (mas NÃO tem):
if [ -z "$TEXTO" ] || [ "$TEXTO" = "null" ]; then
    echo "   ⚠️  Cena ${cena_id}: Texto vazio, pulando..."
    return 0
fi
```

---

### **GAP-004: Drawtext Alpha Expression Syntax** ⚠️ MODERADO
**Componente:** `montagem_final.sh` (Linha 168)  
**Problema:**
- Expressões alpha usam valores de `bc` que retornam floats com `.` (ex: `.5`)
- FFmpeg pode interpretar `.5` como erro de sintaxe (dependendo da versão)
- Melhor prática: sempre usar `0.5` (zero explícito)

**Evidência:**
```bash
$ echo "0 + 0.5" | bc
.5   # ❌ Sem zero à esquerda
```

**Fix:** Adicionar `| awk '{printf "%.2f", $0}'` após `bc`

---

### **GAP-005: Playwright Locators Não-Determinísticos** ⚠️ BAIXO
**Componente:** `video_tour.spec.ts` (Linhas 32-88)  
**Problema:**
- Locators usam regex genéricos: `text=/dashboard/i`
- Se múltiplos elementos têm "dashboard" no texto → ambiguidade
- `.first()` pega o primeiro, mas pode ser o errado

**Impacto:**
- 🎥 Vídeo grava elementos errados (não crítico para MVP)
- 🔄 Falta de idempotência (cada run pode gravar diferente)

**Solução Ideal:** Adicionar `data-testid` no frontend (fora de escopo desta refatoração)

---

## ✅ PONTOS FORTES IDENTIFICADOS

1. **✅ Autenticação GCP Correta**
   - Header `X-Goog-User-Project` presente
   - Token via `gcloud auth print-access-token` funcional

2. **✅ Campo `.narracao` Correto**
   - Script TTS corrigido (usa `.narracao` pt-BR)
   - Todos os 11 áudios gerados com sucesso (~0.79s cada)

3. **✅ Download Automático de Fonte**
   - Previne erro `Font file not found` do FFmpeg
   - Usa Google Fonts (Roboto)

4. **✅ Detecção de Duração Automática**
   - Se `duration_seconds: null` → usa `ffprobe` no vídeo
   - Fallback inteligente implementado

5. **✅ Playwright Config Correto**
   - `video: { mode: 'on' }` ativo
   - Output em `test-results/` funcional

---

## 📋 PLANO DE REFATORAÇÃO ESTRUTURADO

### **FASE 1: Correções Críticas (GAP-001, GAP-002)**
**Tempo Estimado:** 15 minutos  
**Custo:** 0 tokens GCP (só código)

#### **1.1 Corrigir Field Name: timestamp**
**Arquivo:** `montagem_final.sh`  
**Ação:**
```bash
# ANTES (Linha ~166):
TIMESTAMP=$(jq -r ".cenas[$i].timestamp" roteiro.json)

# DEPOIS:
TIMESTAMP=$(jq -r ".cenas[$i].timestamp_inicio" roteiro.json)
```

**Validação:**
```bash
# Adicionar após extração:
if [ "$TIMESTAMP" = "null" ] || [ -z "$TIMESTAMP" ]; then
    echo "   ⚠️  Cena $((i+1)): timestamp_inicio ausente, usando 0"
    TIMESTAMP=0
fi
```

---

#### **1.2 Preservar Arquivos Intermediários para Debug**
**Arquivo:** `montagem_final.sh`  
**Ação:**
```bash
# ANTES (Linha ~189):
echo "🧹 Limpando arquivos temporários..."
rm -f audio_list.txt audio_completo.mp3 video_sem_audio.mp4 video_com_audio.mp4

# DEPOIS:
if [ -f "video_final.mp4" ] && [ -s "video_final.mp4" ]; then
    echo "🧹 Limpando arquivos temporários..."
    rm -f audio_list.txt audio_completo.mp3 video_sem_audio.mp4 video_com_audio.mp4
    echo "   ✅ Limpeza concluída"
else
    echo "⚠️  video_final.mp4 vazio/ausente - preservando intermediários para debug"
    echo "   Arquivos mantidos: video_sem_audio.mp4, video_com_audio.mp4"
fi
```

---

### **FASE 2: Validações Mandatórias (GAP-003)**
**Tempo Estimado:** 10 minutos  
**Custo:** 0 tokens GCP

#### **2.1 Validar Texto Antes de TTS**
**Arquivo:** `gerar_narracao_gcp.sh`  
**Ação:**
```bash
# Adicionar ANTES da linha 83 (dentro de gerar_audio()):
# Validação tripla conforme Artigo I, Cláusula 3.3
if [ -z "$texto" ] || [ "$texto" = "null" ]; then
    echo "   ⚠️  Texto vazio/null - pulando TTS"
    return 0
fi

local texto_len=${#texto}
if [ $texto_len -gt 5000 ]; then
    echo "   ⚠️  Texto muito longo ($texto_len chars) - truncando para 5000"
    texto="${texto:0:5000}"
fi
```

---

### **FASE 3: Robustez Matemática (GAP-004)**
**Tempo Estimado:** 5 minutos  
**Custo:** 0 tokens GCP

#### **3.1 Normalizar Floats do bc**
**Arquivo:** `montagem_final.sh`  
**Ação:**
```bash
# ANTES (Linha ~175):
TEXTO_FADE_IN_END=$(echo "$TIMESTAMP + 0.5" | bc)

# DEPOIS:
TEXTO_FADE_IN_END=$(echo "$TIMESTAMP + 0.5" | bc | awk '{printf "%.2f", $0}')
```

**Aplicar em TODAS as 4 linhas que usam `bc` (linhas ~175-178)**

---

### **FASE 4: Logging Diagnóstico**
**Tempo Estimado:** 10 minutos  
**Custo:** 0 tokens GCP

#### **4.1 Adicionar Dry-Run Mode**
**Arquivo:** `MATERIALIZAR_VIDEO_SEGURO.sh`  
**Ação:**
```bash
# Adicionar no topo:
DRY_RUN=${1:-""}  # Aceita argumento --dry-run

if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "🔍 MODO DRY-RUN ATIVO (sem executar, só validar)"
    echo ""
fi
```

**Modificar cada fase para checar dry-run:**
```bash
if [ "$DRY_RUN" != "--dry-run" ]; then
    bash gerar_narracao_gcp.sh
else
    echo "   [DRY-RUN] Pulando geração de narração"
fi
```

---

#### **4.2 Log Estruturado**
**Criar:** `vertice_video_producao/log_producao.txt`  
**Ação:** Redirecionar output crítico:
```bash
exec > >(tee -a log_producao.txt)
exec 2>&1
```

---

### **FASE 5: Testes de Regressão**
**Tempo Estimado:** 20 minutos  
**Custo:** ~11 chamadas GCP TTS (re-gerar narrações)

#### **5.1 Teste Unitário: TTS**
```bash
# Testar com cena isolada
cd vertice_video_producao
jq '.cenas[0]' roteiro.json > /tmp/test_cena.json
# Modificar script para aceitar input alternativo
bash gerar_narracao_gcp.sh --single-scene /tmp/test_cena.json
```

#### **5.2 Teste Unitário: FFmpeg Drawtext**
```bash
# Testar drawtext com valores hardcoded
ffmpeg -i video_tour.webm -vf \
  "drawtext=fontfile=Roboto-Regular.ttf:text='TESTE':x=100:y=100:fontcolor=white:fontsize=48:alpha='if(lt(t,1),t,1)'" \
  -t 5 /tmp/test_drawtext.mp4 -y
```

#### **5.3 Teste End-to-End**
```bash
# Executar pipeline completo em modo dry-run primeiro
./MATERIALIZAR_VIDEO_SEGURO.sh --dry-run

# Se passar, executar real:
./MATERIALIZAR_VIDEO_SEGURO.sh
```

---

## 🎯 CRITÉRIOS DE ACEITAÇÃO

### **Definição de "DONE":**
✅ `video_final.mp4` gerado com tamanho >1MB  
✅ Duração do vídeo = duração do áudio (±0.5s)  
✅ Overlays de texto visíveis em todas as 11 cenas  
✅ Fade in/out suave (1s início + 1s final)  
✅ Áudio sincronizado com vídeo  
✅ Nenhum arquivo intermediário deletado se falhar  
✅ Log de produção gravado em `log_producao.txt`  

### **Checklist de Validação Tripla (Artigo I, Cláusula 3.3):**
- [ ] Análise estática: `shellcheck *.sh` (0 erros)
- [ ] Teste unitário: Cada fase isolada funciona
- [ ] Conformidade doutrinária: `grep -r "TODO\|FIXME\|mock" *.sh` (0 resultados)

---

## 💰 ESTIMATIVA DE CUSTO

### **Google Cloud TTS API:**
- **Teste (FASE 5.1):** 1 chamada = ~100 caracteres
- **Produção (re-run completo):** 11 chamadas = ~1500 caracteres
- **Total:** ~1600 caracteres
- **Quota Free Tier:** 1.000.000 chars/mês
- **% Usado:** 0.16% (insignificante)

### **Tempo de Execução:**
- Refatoração: ~40 minutos (coding)
- Testes: ~20 minutos (validação)
- **Total:** ~1 hora (work humano + IA)

---

## 📈 PRIORIZAÇÃO (Método MoSCoW)

### **MUST (Obrigatório para funcionar):**
- ✅ GAP-001: Corrigir field name `timestamp`
- ✅ GAP-002: Preservar arquivos intermediários

### **SHOULD (Altamente recomendado):**
- ✅ GAP-003: Validar texto antes de TTS
- ✅ GAP-004: Normalizar floats do bc

### **COULD (Nice to have):**
- ⚪ GAP-005: Melhorar locators Playwright
- ⚪ FASE 4: Dry-run mode + logging

### **WON'T (Fora de escopo):**
- ❌ Adicionar `data-testid` no frontend (requer mudança em outro repo)
- ❌ Implementar retry logic na API TTS (complexidade desnecessária para MVP)

---

## 🔄 ROLLBACK PLAN

**Se refatoração falhar:**
1. Restaurar scripts originais: `git checkout HEAD -- vertice_video_producao/`
2. Áudios já gerados em `audio_narracoes/` são preservados
3. `video_tour.webm` (1.8MB) já está OK, pode ser reutilizado
4. Custo de re-tentar: 0 GCP calls (só FFmpeg local)

---

## 📝 NOTAS TÉCNICAS

### **Decisões de Design:**

**1. Por que não usar `duration_seconds` do roteiro?**
- Roteiro tem `duracao_total: 180` (planejado 3 minutos)
- Vídeo real tem `16.12s` (Playwright gravou menos)
- Solução: `ffprobe` detecta duração REAL → mais confiável

**2. Por que preservar intermediários?**
- Debugging: Ver ONDE pipeline quebra (qual fase)
- Re-execução seletiva: Rodar só FASE 5 sem re-gerar tudo
- Conformidade: Artigo VI (eficiência de tokens)

**3. Por que não refatorar Playwright locators?**
- Requer mudança no frontend (adicionar `data-testid`)
- Fora de escopo desta refatoração (pipeline de vídeo)
- Impacto baixo (vídeo ainda grava, só pode pegar elemento errado)

---

## 🎬 PRÓXIMOS PASSOS (Aguardando GO do Arquiteto-Chefe)

**Opção A - Refatoração Completa:**
```bash
# 1. Aplicar correções (FASES 1-4)
# 2. Executar testes (FASE 5)
# 3. Gerar vídeo final
# Tempo: ~1h | Custo: ~11 TTS calls
```

**Opção B - Correção Mínima (MUST only):**
```bash
# 1. Corrigir apenas GAP-001 e GAP-002
# 2. Re-executar montagem_final.sh
# 3. Validar video_final.mp4
# Tempo: ~15min | Custo: 0 TTS calls
```

**Opção C - Abort:**
```bash
# Preservar estado atual
# Documentar gaps para futura iteração
```

---

## 📚 REFERÊNCIAS TÉCNICAS

**Documentação Oficial Consultada:**
- Google Cloud TTS REST API: https://cloud.google.com/text-to-speech/docs/create-audio-text-command-line
- FFmpeg Drawtext Filter: https://ffmpeg.org/ffmpeg-filters.html#drawtext
- FFmpeg Concat Demuxer: https://trac.ffmpeg.org/wiki/Concatenate
- Playwright Video Recording: https://playwright.dev/docs/videos
- Constituição Vértice v2.7: `/home/juan/vertice-dev/.github/copilot-instructions.md`

---

**Gerado por:** Co-Arquiteto Cético (IA)  
**Conformidade:** Artigo I, Cláusula 3.4 (Obrigação da Verdade)  
**Status:** ⏸️ AGUARDANDO APROVAÇÃO DO ARQUITETO-CHEFE
