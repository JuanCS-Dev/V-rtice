#!/bin/bash
set -e

echo "📦 Extraindo vídeo do Playwright..."

# Playwright salva vídeos em test-results/
VIDEO_DIR="test-results"

if [ ! -d "$VIDEO_DIR" ]; then
    echo "❌ Diretório test-results/ não encontrado."
    echo "Execute 'npx playwright test' primeiro."
    exit 1
fi

# Encontrar o vídeo mais recente (Playwright cria subpastas por teste)
VIDEO_FILE=$(find "$VIDEO_DIR" -name "*.webm" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)

if [ -z "$VIDEO_FILE" ]; then
    echo "❌ Nenhum vídeo .webm encontrado em test-results/"
    exit 1
fi

echo "   ✅ Vídeo encontrado: $VIDEO_FILE"

# Copiar para raiz com nome padronizado
cp "$VIDEO_FILE" video_tour.webm

SIZE=$(du -h video_tour.webm | cut -f1)
echo "   ✅ Copiado para: video_tour.webm ($SIZE)"
echo ""

