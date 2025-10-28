#!/bin/bash
# Script para testar geração de música sozinho

echo "🎵 Teste de Geração de Trilha Sonora"
echo "======================================"

ffmpeg -f lavfi -i "sine=frequency=40:duration=10" \
       -f lavfi -i "sine=frequency=120:duration=10" \
       -f lavfi -i "sine=frequency=440:duration=10" \
       -filter_complex "[0:a]volume=0.05[a1];[1:a]volume=0.03[a2];[2:a]volume=0.01[a3];[a1][a2][a3]amix=inputs=3,aecho=0.8:0.9:1000:0.3,afade=t=in:d=2:curve=esin,afade=t=out:st=8:d=2:curve=esin[aout]" \
       -map "[aout]" -y test_music.mp3

echo ""
echo "✅ Música de teste gerada: test_music.mp3 (10s)"
echo "   Execute: vlc test_music.mp3"
