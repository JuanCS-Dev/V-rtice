# 🎬 Vértice - Sistema de Produção de Vídeo Operacional

## ✅ Status: PRONTO PARA EXECUÇÃO

### 📁 Estrutura Criada

```
vertice-dev/
├── check_ambiente.sh              # FASE 0: Validação de ambiente
├── MATERIALIZAR_VIDEO_SEGURO.sh   # Script diretor principal
└── vertice_video_producao/
    ├── roteiro.json               # Roteiro 180s (11 cenas)
    ├── package.json               # Dependências Playwright
    ├── playwright.config.ts       # Configuração de gravação
    ├── video_tour.spec.ts         # Script de navegação
    ├── gerar_narracao_gcp.sh      # Geração de voz (GCP TTS)
    └── montagem_final.sh          # Montagem com FFmpeg
```

### 🎯 Frontend Instrumentado

**data-testid** adicionados em:
- ✅ `[data-testid=nav-maximus-dashboard]` - Landing Page
- ✅ `[data-testid=nav-tom-engine]` - Landing Page  
- ✅ `[data-testid=nav-immune-system]` - Landing Page
- ✅ `[data-testid=nav-reactive-fabric]` - Landing Page
- ✅ `[data-testid=nav-monitoring]` - Landing Page
- ✅ `[data-testid=maximus-agents-list]` - MAXIMUS Core
- ✅ `[data-testid=tom-threat-map]` - ToM Engine Dashboard
- ✅ `[data-testid=immune-cells-activity]` - Immune System Dashboard
- ✅ `[data-testid=fabric-event-stream]` - Reactive Fabric Dashboard

### 🎞️ Roteiro Gerado

**Duração:** 180 segundos (3 minutos)
**Cenas:** 11 (15s cada, em média)

**Narrativa:**
1. **Intro (0-15s):** Apresentação Vértice
2. **MAXIMUS (15-45s):** AI Consciente + Multi-Agent Orchestration
3. **ToM Engine (45-75s):** Theory of Mind + Threat Prediction
4. **Adaptive Immunity (75-110s):** Biomimética + Honeypots
5. **Reactive Fabric (110-150s):** Real-time Event Processing
6. **Monitoring (150-165s):** Prometheus + Grafana + Jaeger
7. **Outro (165-180s):** Call to action

### 🔧 Dependências

**Instaladas:**
- ✅ Node.js + npm
- ✅ Frontend (Vite dev server rodando em :5173)
- ✅ Playwright (instalando Chromium...)

**Pendentes (usuário deve ter):**
- ⏳ FFmpeg (para montagem final)
- ⏳ jq (para parsing JSON)
- ⏳ Google Cloud SDK (para narração TTS)
- ⏳ Billing ativo no GCP (para Text-to-Speech API)

### 🚀 Como Executar

#### Opção 1: Script Automatizado (RECOMENDADO)
```bash
cd /home/juan/vertice-dev
./MATERIALIZAR_VIDEO_SEGURO.sh
```

O script executa:
1. **FASE 0:** Checkup de ambiente
2. **FASE 1:** Setup Playwright
3. **FASE 2:** Geração de narração (GCP)
4. **FASE 3:** Gravação com Playwright (requer frontend rodando)
5. **FASE 4:** Montagem final com FFmpeg

#### Opção 2: Manual (Debug)
```bash
# 1. Verificar ambiente
cd /home/juan/vertice-dev
./check_ambiente.sh

# 2. Gerar narração
cd vertice_video_producao
bash gerar_narracao_gcp.sh

# 3. Gravar vídeo (frontend DEVE estar em localhost:5173)
npx playwright test video_tour.spec.ts

# 4. Montar vídeo final
bash montagem_final.sh
```

### ⚙️ Configuração GCP Necessária

```bash
# 1. Autenticar
gcloud auth login

# 2. Configurar projeto
gcloud config set project projeto-vertice

# 3. Habilitar billing (se não estiver ativo)
# Acesse: https://console.cloud.google.com/billing/linkedaccount?project=projeto-vertice
```

### 📹 Output Esperado

```
vertice_video_producao/
├── audio_narracoes/
│   ├── cena_1.mp3
│   ├── cena_2.mp3
│   └── ... (11 cenas)
├── audio_completo.mp3
├── test-results/
│   └── video_tour-chromium/
│       └── video.webm
├── Roboto-Regular.ttf
└── video_final.mp4  ← RESULTADO FINAL
```

### 🛡️ Imunização Implementada

✅ **set -e** em todos os scripts bash
✅ **Validação prévia** de frontend availability
✅ **Try-catch** em Playwright para seletores faltantes
✅ **Fonte local** (download automático) para FFmpeg
✅ **Habilitação automática** da API Text-to-Speech

### 🎨 Features do Vídeo

- Navegação cinematográfica
- Overlays de texto animados
- Narração profissional (voz neural pt-BR)
- 1080p @ 30fps
- Música de fundo (futuro: adicionar trilha)
- Transições suaves entre cenas

### 📝 Notas

1. **Frontend DEVE estar rodando** antes da gravação (Fase 3)
2. **Chromium install** pode demorar ~5min (baixando browser)
3. **FFmpeg montagem** pode demorar ~2min (encoding)
4. **GCP TTS** consome API calls (Free Tier: 1M chars/mês)

---

**Status atual:** Frontend rodando em :5173, Playwright instalando Chromium...
**Próximo passo:** Aguardar instalação do Chromium, então executar `./MATERIALIZAR_VIDEO_SEGURO.sh`
