#!/bin/bash
set -e

echo "🎵 VÉRTICE - COMPILAÇÃO ÁUDIO ÚNICO (English)"
echo "=============================================="
echo ""

# Verificar roteiro
ROTEIRO="roteiro_v4_english_final.json"
if [ ! -f "$ROTEIRO" ]; then
  echo "❌ ERRO: $ROTEIRO não encontrado."
  exit 1
fi

# Verificar áudios
echo "🔍 Validando áudios..."
TOTAL_CENAS=$(jq '.cenas | length' "$ROTEIRO")
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

# Criar lista de concatenação
echo ""
echo "🔧 Criando lista de concatenação..."
echo "# Lista de áudios Vértice (English)" > audio_list.txt
for ((i=1; i<=TOTAL_CENAS; i++)); do
  echo "file 'audio_narracoes/cena_${i}.mp3'" >> audio_list.txt
done

echo "   ✅ Lista criada ($TOTAL_CENAS cenas)"

# Concatenar em sequência
echo ""
echo "🎵 Compilando áudio único..."

ffmpeg -y \
  -f concat \
  -safe 0 \
  -i audio_list.txt \
  -c copy \
  -metadata title="Vértice - The Living Cybersecurity Organism" \
  -metadata artist="Vértice AI" \
  -metadata album="Product Demo" \
  -metadata date="2025" \
  vertice_narration_complete.mp3 \
  -loglevel error

# Validar resultado
if [ ! -f "vertice_narration_complete.mp3" ]; then
  echo "❌ ERRO: Falha na compilação."
  exit 1
fi

DURACAO=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 vertice_narration_complete.mp3 2>/dev/null)
TAMANHO=$(du -h vertice_narration_complete.mp3 | cut -f1)

echo "   ✅ vertice_narration_complete.mp3 criado"
echo "   📏 Duração: ${DURACAO}s"
echo "   📦 Tamanho: $TAMANHO"

# Limpeza
rm -f audio_list.txt

echo ""
echo "=============================================="
echo "🎉 ÁUDIO COMPILADO COM SUCESSO!"
echo ""
echo "📁 ARQUIVO FINAL:"
echo "   🎵 vertice_narration_complete.mp3"
echo "   📏 ${DURACAO}s de narração contínua"
echo "   🎙️  11 cenas em inglês (en-US-Neural2-J)"
echo "=============================================="
echo ""