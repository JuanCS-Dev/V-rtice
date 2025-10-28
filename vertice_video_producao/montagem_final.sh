#!/bin/bash
set -e

echo "🎬 VÉRTICE - MONTAGEM FINAL (FFmpeg Cinema Edition)"
echo "===================================================="
echo ""

# Verificar dependências
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ERRO: 'ffmpeg' não encontrado."
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "❌ ERRO: 'jq' não encontrado."
    exit 1
fi

# Verificar arquivos necessários
if [ ! -f "roteiro_v3_english.json" ]; then
    echo "❌ ERRO: 'roteiro_v3_english.json' não encontrado."
    exit 1
fi

if [ ! -f "video_tour.webm" ]; then
    echo "❌ ERRO: 'video_tour.webm' não encontrado. Execute Playwright primeiro."
    exit 1
fi

echo "📋 Carregando configurações do roteiro..."

# Extrair informações do roteiro
DURACAO_ROTEIRO=$(jq -r '.duration_seconds' roteiro_v3_english.json)
NUM_CENAS=$(jq '.cenas | length' roteiro_v3_english.json)

# Se duração no roteiro for null, detectar do vídeo
if [ "$DURACAO_ROTEIRO" = "null" ] || [ -z "$DURACAO_ROTEIRO" ]; then
    echo "   ⚙️  Detectando duração do vídeo automaticamente..."
    DURACAO_TOTAL=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 video_tour.webm | cut -d. -f1)
else
    DURACAO_TOTAL=$DURACAO_ROTEIRO
fi

echo "   ℹ️  Duração total: ${DURACAO_TOTAL}s"
echo "   ℹ️  Número de cenas: $NUM_CENAS"
echo ""

# ====================================================================
# FASE 1: BAIXAR FONTE (previne erro de fonte não encontrada)
# ====================================================================
echo "📦 FASE 1: Preparando fonte para overlay de texto..."

FONT_FILE="Roboto-Regular.ttf"
if [ ! -f "$FONT_FILE" ]; then
    echo "   ⬇️  Baixando Roboto-Regular.ttf..."
    curl -sL -o "$FONT_FILE" "https://github.com/google/fonts/raw/main/apache/roboto/static/Roboto-Regular.ttf"
    if [ -f "$FONT_FILE" ]; then
        echo "   ✅ Fonte baixada"
    else
        echo "   ❌ Falha ao baixar fonte"
        exit 1
    fi
else
    echo "   ✅ Fonte já existe"
fi

echo ""

# ====================================================================
# FASE 2: CONCATENAR ÁUDIOS DE NARRAÇÃO
# ====================================================================
echo "🎵 FASE 2: Concatenando áudios de narração..."

# Criar lista de arquivos para concat demuxer
# Ref: https://trac.ffmpeg.org/wiki/Concatenate
echo "file 'audio_narracoes/cena_1.mp3'" > audio_list.txt
for i in $(seq 2 $NUM_CENAS); do
    echo "file 'audio_narracoes/cena_${i}.mp3'" >> audio_list.txt
done

# Concatenar usando concat demuxer (método oficial)
ffmpeg -f concat -safe 0 -i audio_list.txt -c copy audio_completo.mp3 -y \
    2>&1 | grep -E '(Duration|Output|error)' || true

if [ -f "audio_completo.mp3" ]; then
    SIZE=$(du -h audio_completo.mp3 | cut -f1)
    echo "   ✅ Áudio completo: audio_completo.mp3 ($SIZE)"
else
    echo "   ❌ Falha na concatenação de áudio"
    exit 1
fi

echo ""

# ====================================================================
# FASE 3: CONVERTER VÍDEO WEBM → MP4 (sem áudio)
# ====================================================================
echo "🎥 FASE 3: Convertendo vídeo Playwright (WebM → MP4)..."

ffmpeg -i video_tour.webm -an -c:v libx264 -preset fast -crf 23 video_sem_audio.mp4 -y \
    2>&1 | grep -E '(Duration|Output|error)' || true

if [ -f "video_sem_audio.mp4" ]; then
    echo "   ✅ Vídeo convertido"
else
    echo "   ❌ Falha na conversão"
    exit 1
fi

echo ""

# ====================================================================
# FASE 4: MIXAR VÍDEO + ÁUDIO
# ====================================================================
echo "🔊 FASE 4: Mixando vídeo + narração..."

# Método oficial: map streams separados
# Ref: https://www.mux.com/articles/merge-audio-and-video-files-with-ffmpeg
ffmpeg -i video_sem_audio.mp4 -i audio_completo.mp3 \
    -c:v copy -c:a aac -b:a 192k \
    -map 0:v:0 -map 1:a:0 \
    -shortest \
    video_com_audio.mp4 -y \
    2>&1 | grep -E '(Duration|Output|error)' || true

if [ -f "video_com_audio.mp4" ]; then
    echo "   ✅ Áudio mixado"
else
    echo "   ❌ Falha no mix"
    exit 1
fi

echo ""

# ====================================================================
# FASE 5: APLICAR EFEITOS CINEMATOGRÁFICOS
# ====================================================================
echo "✨ FASE 5: Aplicando fade in/out e overlays de texto..."

# Construir filter_complex para cada cena
# Ref: https://ffmpeg.org/ffmpeg-filters.html#drawtext
# Ref: https://ottverse.com/ffmpeg-drawtext-filter-dynamic-overlays-timecode-scrolling-text-credits/

FILTER_CHAIN=""

# Fade in no início (1s)
FILTER_CHAIN+="fade=t=in:st=0:d=1"

# Fade out no final (1s antes do fim)
FADE_OUT_START=$(echo "$DURACAO_TOTAL - 1" | bc | awk '{printf "%.2f", $0}')
FILTER_CHAIN+=",fade=t=out:st=${FADE_OUT_START}:d=1"

# Adicionar drawtext para cada cena
for i in $(seq 0 $((NUM_CENAS - 1))); do
    TITULO=$(jq -r ".cenas[$i].texto_overlay" roteiro_v3_english.json)
    TIMESTAMP=$(jq -r ".cenas[$i].timestamp_inicio" roteiro_v3_english.json)
    
    # Validação: Se timestamp for null/vazio, usar índice da cena
    if [ "$TIMESTAMP" = "null" ] || [ -z "$TIMESTAMP" ]; then
        echo "   ⚠️  Cena $((i+1)): timestamp_inicio ausente, usando índice"
        TIMESTAMP=$((i * 15))
    fi
    
    # Duração do texto na tela (3s)
    TEXTO_FADE_IN_START=$TIMESTAMP
    TEXTO_FADE_IN_END=$(echo "$TIMESTAMP + 0.5" | bc | awk '{printf "%.2f", $0}')
    TEXTO_VISIBLE_END=$(echo "$TIMESTAMP + 2.5" | bc | awk '{printf "%.2f", $0}')
    TEXTO_FADE_OUT_END=$(echo "$TIMESTAMP + 3" | bc | awk '{printf "%.2f", $0}')
    
    # Expression para fade in/out do texto
    # Ref: https://www.braydenblackwell.com/blog/ffmpeg-text-rendering
    ALPHA_EXPR="if(lt(t,${TEXTO_FADE_IN_START}),0,if(lt(t,${TEXTO_FADE_IN_END}),(t-${TEXTO_FADE_IN_START})/0.5,if(lt(t,${TEXTO_VISIBLE_END}),1,if(lt(t,${TEXTO_FADE_OUT_END}),(${TEXTO_FADE_OUT_END}-t)/0.5,0))))"
    
    FILTER_CHAIN+=",drawtext=fontfile=${FONT_FILE}:text='${TITULO}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h-100:alpha='${ALPHA_EXPR}'"
done

# Aplicar todos os filtros
ffmpeg -i video_com_audio.mp4 \
    -vf "$FILTER_CHAIN" \
    -c:a copy \
    video_final.mp4 -y \
    2>&1 | grep -E '(Duration|Output|error)' || true

if [ -f "video_final.mp4" ] && [ -s "video_final.mp4" ]; then
    SIZE=$(du -h video_final.mp4 | cut -f1)
    echo "   ✅ Efeitos aplicados"
    echo ""
    echo "===================================================="
    echo "✅ VÍDEO FINAL PRONTO: video_final.mp4 ($SIZE)"
    echo "===================================================="
    echo ""
    
    # Limpeza apenas se vídeo final for válido
    echo "🧹 Limpando arquivos temporários..."
    rm -f audio_list.txt audio_completo.mp3 video_sem_audio.mp4 video_com_audio.mp4
    echo "   ✅ Limpeza concluída"
else
    echo "   ❌ Falha na aplicação de efeitos"
    echo "   ⚠️  Preservando arquivos intermediários para debug:"
    echo "      - video_sem_audio.mp4"
    echo "      - video_com_audio.mp4"
    echo "      - audio_completo.mp3"
    exit 1
fi

echo ""

