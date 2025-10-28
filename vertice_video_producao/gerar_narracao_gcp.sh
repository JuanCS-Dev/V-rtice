#!/bin/bash
set -e

echo "🎤 VÉRTICE - GERAÇÃO DE NARRAÇÃO (Google Cloud TTS - English v3.0)"
echo "===================================================================="
echo ""

# Verificar autenticação
echo "🔐 Verificando autenticação Google Cloud..."

ACCOUNT=$(gcloud config get-value account 2>/dev/null)
PROJECT=$(gcloud config get-value project 2>/dev/null)

if [ -z "$ACCOUNT" ] || [ -z "$PROJECT" ]; then
  echo "❌ ERRO: Autenticação não configurada."
  echo "Execute: gcloud auth application-default login"
  exit 1
fi

echo "   ℹ️  Conta: $ACCOUNT"
echo "   ℹ️  Projeto: $PROJECT"

# Token será obtido via user credentials (gcloud auth login)
echo "   ✅ Usando credenciais de usuário"
echo ""

# Habilitar API
echo "🔧 Habilitando Text-to-Speech API..."
gcloud services enable texttospeech.googleapis.com --quiet 2>/dev/null || true
echo "   ✅ API habilitada"
echo ""

# Criar diretório
mkdir -p audio_narracoes

# Usar roteiro v4 ENGLISH (Constitution-compliant)
ROTEIRO="roteiro_v4_english_final.json"

if [ ! -f "$ROTEIRO" ]; then
  echo "❌ ERRO: Arquivo '$ROTEIRO' não encontrado."
  exit 1
fi

echo "📋 Processando roteiro v4 ENGLISH..."
echo ""

# Get access token (user auth - bypass ADC issue)
TOKEN=$(gcloud auth print-access-token)

# Add quota project to request headers
QUOTA_PROJECT="projeto-vertice"

# Processar cada cena
TOTAL_CENAS=$(jq '.cenas | length' "$ROTEIRO")

for ((i=0; i<$TOTAL_CENAS; i++)); do
  CENA_NUM=$((i + 1))
  NARRACAO=$(jq -r ".cenas[$i].texto" "$ROTEIRO")  # Campo correto: "texto" não "narracao"
  OUTPUT_FILE="audio_narracoes/cena_${CENA_NUM}.mp3"
  
  # Validação: texto não pode ser null
  if [ -z "$NARRACAO" ] || [ "$NARRACAO" = "null" ]; then
    echo "⚠️  Cena $CENA_NUM: Narração vazia. Pulando..."
    continue
  fi
  
  echo "🎙️  Cena $CENA_NUM: Gerando áudio (en-US-Neural2-J)..."
  
  # Criar JSON payload
  PAYLOAD=$(jq -n \
    --arg text "$NARRACAO" \
    '{
      input: { text: $text },
      voice: {
        languageCode: "en-US",
        name: "en-US-Neural2-J",
        ssmlGender: "MALE"
      },
      audioConfig: {
        audioEncoding: "MP3",
        speakingRate: 0.95,
        pitch: -1.0,
        volumeGainDb: 2.0
      }
    }')
  
  # Chamar REST API com quota project
  RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    -H "X-Goog-User-Project: $QUOTA_PROJECT" \
    -d "$PAYLOAD" \
    "https://texttospeech.googleapis.com/v1/text:synthesize")
  
  # Verificar erro
  if echo "$RESPONSE" | jq -e '.error' > /dev/null 2>&1; then
    ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message')
    echo "   ❌ Falha: $ERROR_MSG"
    continue
  fi
  
  # Extrair base64 e decodificar
  echo "$RESPONSE" | jq -r '.audioContent' | base64 -d > "$OUTPUT_FILE"
  
  if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo "   ✅ Salvo: $OUTPUT_FILE ($FILE_SIZE)"
  else
    echo "   ❌ Falha ao salvar"
  fi
done

echo ""
echo "===================================================================="
echo "✅ Narração completa. Áudios salvos em: audio_narracoes/"
echo "===================================================================="
echo ""
