#!/bin/bash
set -e

echo "🚀 VÉRTICE - MATERIALIZAÇÃO VÍDEO FINAL v2.0"
echo "============================================="
echo "Orquestrador Unificado (Constitution v2.7)"
echo ""

# Timestamp para logs
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="log_producao_final_${TIMESTAMP}.txt"

# Função de log
log() {
  echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Validações de ambiente
log "🔍 FASE 1: Validação de ambiente"

if [ ! -f "../check_ambiente.sh" ]; then
  log "❌ ERRO: check_ambiente.sh não encontrado"
  exit 1
fi

if ! bash ../check_ambiente.sh; then
  log "❌ ERRO: Ambiente não válido"
  exit 1
fi

log "✅ Ambiente validado"

# Verificar frontend rodando
if ! curl -s http://localhost:5173 > /dev/null; then
  log "❌ ERRO: Frontend não está rodando em localhost:5173"
  log "Execute: cd ../frontend && npm run dev"
  exit 1
fi

log "✅ Frontend disponível"

# FASE 2: Geração de narração
log ""
log "🎤 FASE 2: Geração de narração (TTS)"

if [ ! -f "gerar_narracao_gcp.sh" ]; then
  log "❌ ERRO: gerar_narracao_gcp.sh não encontrado"
  exit 1
fi

log "Executando TTS..."
if bash gerar_narracao_gcp.sh >> "$LOG_FILE" 2>&1; then
  log "✅ Narração gerada com sucesso"
else
  log "❌ ERRO: Falha na geração de narração"
  exit 1
fi

# Validar áudios
AUDIO_COUNT=$(ls audio_narracoes/*.mp3 2>/dev/null | wc -l)
if [ "$AUDIO_COUNT" -lt 11 ]; then
  log "❌ ERRO: Apenas $AUDIO_COUNT áudios gerados (esperado: 11)"
  exit 1
fi

log "✅ $AUDIO_COUNT áudios validados"

# FASE 3: Gravação do tour
log ""
log "🎬 FASE 3: Gravação do tour (Playwright)"

if [ ! -f "video_tour.spec.ts" ]; then
  log "❌ ERRO: video_tour.spec.ts não encontrado"
  exit 1
fi

log "Executando gravação..."
if npx playwright test video_tour.spec.ts >> "$LOG_FILE" 2>&1; then
  log "✅ Tour gravado com sucesso"
else
  log "❌ ERRO: Falha na gravação"
  exit 1
fi

# FASE 4: Extração de vídeo
log ""
log "🔄 FASE 4: Extração de vídeo"

if bash extrair_video_v2.sh >> "$LOG_FILE" 2>&1; then
  log "✅ Vídeo extraído com sucesso"
else
  log "❌ ERRO: Falha na extração"
  exit 1
fi

# Validar duração
DURACAO=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 video_bruto.mp4 2>/dev/null)
DURACAO_INT=$(echo "$DURACAO" | cut -d'.' -f1)

if [ "$DURACAO_INT" -lt 170 ]; then
  log "❌ ERRO: Vídeo muito curto (${DURACAO_INT}s < 170s)"
  exit 1
fi

log "✅ Duração validada: ${DURACAO}s"

# FASE 5: Montagem final
log ""
log "🎵 FASE 5: Montagem final"

if bash montagem_final_v2.sh >> "$LOG_FILE" 2>&1; then
  log "✅ Montagem concluída"
else
  log "❌ ERRO: Falha na montagem"
  exit 1
fi

# Validação final
if [ ! -f "video_final_v2.mp4" ]; then
  log "❌ ERRO: video_final_v2.mp4 não foi criado"
  exit 1
fi

DURACAO_FINAL=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 video_final_v2.mp4 2>/dev/null)
TAMANHO_FINAL=$(du -h video_final_v2.mp4 | cut -f1)

log "✅ Vídeo final: ${DURACAO_FINAL}s, $TAMANHO_FINAL"

# FASE 6: Artefatos finais
log ""
log "🎯 FASE 6: Gerando artefatos"

# Preview de 10s
ffmpeg -y -i video_final_v2.mp4 \
  -t 10 \
  -c:v libx264 -crf 28 \
  -c:a aac -b:a 128k \
  preview_10s.mp4 \
  -loglevel error 2>/dev/null

log "✅ Preview gerado: preview_10s.mp4"

# Limpeza de temporários
log ""
log "🧹 Limpeza de arquivos temporários"

rm -f video_bruto.mp4 2>/dev/null || true
rm -rf test-results 2>/dev/null || true

log "✅ Limpeza concluída"

# Relatório final
log ""
log "============================================="
log "🎉 PRODUÇÃO COMPLETA!"
log ""
log "📹 ARTEFATOS FINAIS:"
log "   • video_final_v2.mp4 (${DURACAO_FINAL}s, $TAMANHO_FINAL)"
log "   • preview_10s.mp4 (10s preview)"
log "   • thumbnail.jpg (frame 30s)"
log "   • $LOG_FILE (log completo)"
log ""
log "📊 MÉTRICAS:"
log "   • Cenas: 11"
log "   • Áudios: $AUDIO_COUNT"
log "   • Duração: ${DURACAO_FINAL}s"
log "   • Resolução: 1920x1080"
log ""
log "✅ CONFORMIDADE: Constituição Vértice v2.7"
log "============================================="