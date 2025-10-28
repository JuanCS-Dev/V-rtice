#!/bin/bash
set -e

echo "🎬 MONTAGEM FINAL v2.0 (Constitution Compliant)"
echo "==============================================="
echo ""

# Validar inputs ANTES de iniciar FFmpeg
echo "🔍 Validando inputs..."

# 1. Verificar vídeo bruto
if [ ! -f "video_bruto.mp4" ]; then
  echo "❌ ERRO: video_bruto.mp4 não encontrado."
  echo "Execute extrair_video_v2.sh primeiro."
  exit 1
fi

echo "   ✅ video_bruto.mp4 encontrado"

# 2. Verificar áudios (deve ter 11 cenas)
ROTEIRO="roteiro_v4_english_final.json"
if [ ! -f "$ROTEIRO" ]; then
  echo "❌ ERRO: $ROTEIRO não encontrado."
  exit 1
fi

TOTAL_CENAS=$(jq '.cenas | length' "$ROTEIRO")
echo "   📋 Roteiro: $TOTAL_CENAS cenas esperadas"

AUDIOS_MISSING=0
for ((i=1; i<=TOTAL_CENAS; i++)); do
  AUDIO_FILE="audio_narracoes/cena_${i}.mp3"
  if [ ! -f "$AUDIO_FILE" ]; then
    echo "   ❌ FALTANDO: $AUDIO_FILE"
    AUDIOS_MISSING=$((AUDIOS_MISSING + 1))
  else
    echo "   ✅ $AUDIO_FILE"
  fi
done

if [ $AUDIOS_MISSING -gt 0 ]; then
  echo "❌ ERRO: $AUDIOS_MISSING áudios faltando."
  echo "Execute gerar_narracao_gcp.sh primeiro."
  exit 1
fi

# 3. Criar filtro de áudio SEQUENCIAL (não sobreposto)
echo ""
echo "🔧 Gerando filtro de concatenação SEQUENCIAL..."

# Criar lista de arquivos para concat demuxer (método correto)
echo "# Lista de áudios em ordem sequencial" > audio_list.txt
for ((i=1; i<=TOTAL_CENAS; i++)); do
  echo "file 'audio_narracoes/cena_${i}.mp3'" >> audio_list.txt
done

echo "   ✅ Lista de concatenação criada"

# 4. Executar FFmpeg - CONCAT MÉTODO CORRETO
echo ""
echo "🎵 Executando montagem final..."

# Primeiro: concatenar áudios em sequência
ffmpeg -y \
  -f concat \
  -safe 0 \
  -i audio_list.txt \
  -c copy \
  audio_completo.mp3 \
  -loglevel error

if [ ! -f "audio_completo.mp3" ]; then
  echo "❌ ERRO: Falha na concatenação de áudio."
  exit 1
fi

# Segundo: combinar vídeo com áudio concatenado
ffmpeg -y \
  -i video_bruto.mp4 \
  -i audio_completo.mp3 \
  -c:v copy \
  -c:a aac \
  -b:a 192k \
  -shortest \
  video_final_v2.mp4 \
  -loglevel error

# Validar output
if [ ! -f "video_final_v2.mp4" ]; then
  echo "❌ ERRO: Falha na montagem FFmpeg."
  exit 1
fi

DURACAO_FINAL=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 video_final_v2.mp4 2>/dev/null)
TAMANHO_FINAL=$(du -h video_final_v2.mp4 | cut -f1)

echo "   ✅ video_final_v2.mp4 criado"
echo "   📏 Duração: ${DURACAO_FINAL}s"
echo "   📦 Tamanho: $TAMANHO_FINAL"

# Gerar thumbnail
echo ""
echo "🖼️  Gerando thumbnail..."

ffmpeg -y -i video_final_v2.mp4 \
  -ss 30 \
  -vframes 1 \
  -q:v 2 \
  thumbnail.jpg \
  -loglevel error

echo "   ✅ thumbnail.jpg criado"

echo ""
echo "==============================================="
echo "🎉 MONTAGEM COMPLETA!"
echo "   📹 Vídeo: video_final_v2.mp4"
echo "   🖼️  Thumb: thumbnail.jpg"
echo "==============================================="
echo ""