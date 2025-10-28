#!/bin/bash
set -e

echo "🔧 EXTRAÇÃO VÍDEO PLAYWRIGHT v2.0 (Constitution Compliant)"
echo "============================================================="
echo ""

# Validações pré-requisitos
echo "🔍 Validando ambiente..."

if [ ! -d "test-results" ]; then
  echo "❌ ERRO: Diretório test-results não encontrado."
  echo "Execute o teste Playwright primeiro."
  exit 1
fi

# Procurar vídeo mais recente
VIDEO_PATH=$(find test-results -name "video.webm" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)

if [ -z "$VIDEO_PATH" ] || [ ! -f "$VIDEO_PATH" ]; then
  echo "❌ ERRO: Arquivo video.webm não encontrado em test-results/"
  ls -la test-results/ 2>/dev/null || echo "   (diretório vazio)"
  exit 1
fi

echo "   ✅ Vídeo encontrado: $VIDEO_PATH"

# Verificar duração do vídeo bruto
echo ""
echo "📊 Analisando vídeo bruto..."

DURACAO_BRUTA=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$VIDEO_PATH" 2>/dev/null)

if [ -z "$DURACAO_BRUTA" ]; then
  echo "❌ ERRO: Não foi possível ler duração do vídeo."
  exit 1
fi

DURACAO_INT=$(echo "$DURACAO_BRUTA" | cut -d'.' -f1)

echo "   📏 Duração bruta: ${DURACAO_BRUTA}s"

# VALIDAÇÃO CRÍTICA: Duração mínima
if [ "$DURACAO_INT" -lt 170 ]; then
  echo "❌ FALHA CRÍTICA: Vídeo muito curto (${DURACAO_INT}s < 170s)"
  echo "   Playwright pode ter falhado ou timeout."
  echo "   Execute novamente o tour e verifique logs."
  exit 1
fi

if [ "$DURACAO_INT" -gt 190 ]; then
  echo "⚠️  AVISO: Vídeo mais longo que esperado (${DURACAO_INT}s > 190s)"
  echo "   Pode precisar de ajuste no roteiro."
fi

# Converter para MP4 (compatibilidade FFmpeg)
echo ""
echo "🔄 Convertendo WebM → MP4..."

ffmpeg -y -i "$VIDEO_PATH" \
  -c:v libx264 \
  -preset medium \
  -crf 23 \
  -c:a aac \
  -b:a 192k \
  -movflags +faststart \
  video_bruto.mp4 \
  -loglevel error

if [ ! -f "video_bruto.mp4" ]; then
  echo "❌ ERRO: Falha na conversão FFmpeg."
  exit 1
fi

# Validar vídeo final
DURACAO_FINAL=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 video_bruto.mp4 2>/dev/null)
TAMANHO_FILE=$(du -h video_bruto.mp4 | cut -f1)

echo "   ✅ video_bruto.mp4 criado (${DURACAO_FINAL}s, ${TAMANHO_FILE})"

echo ""
echo "============================================================="
echo "✅ EXTRAÇÃO COMPLETA - video_bruto.mp4 pronto para montagem"
echo "============================================================="
echo ""