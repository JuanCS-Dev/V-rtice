#!/bin/bash
set -e

echo "🎤 VÉRTICE - GERAÇÃO DE NARRAÇÃO (Google Cloud Text-to-Speech)"
echo "==============================================================="
echo ""

# Verificar se jq está instalado
if ! command -v jq &> /dev/null; then
    echo "❌ ERRO: 'jq' não encontrado. Instale: sudo apt install jq"
    exit 1
fi

echo "🔐 Verificando autenticação Google Cloud..."

# Obter projeto ativo
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1)

if [ -z "$ACTIVE_ACCOUNT" ]; then
    echo "❌ ERRO: Nenhuma conta GCloud autenticada."
    exit 1
fi

if [ -z "$PROJECT_ID" ]; then
    echo "❌ ERRO: Nenhum projeto GCloud configurado."
    exit 1
fi

echo "   ℹ️  Conta: $ACTIVE_ACCOUNT"
echo "   ℹ️  Projeto: $PROJECT_ID"

# Obter token de acesso
ACCESS_TOKEN=$(gcloud auth print-access-token 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ ERRO: Não foi possível obter token."
    exit 1
fi

echo "   ✅ Token obtido"
echo ""

# Habilitar API Text-to-Speech
echo "🔧 Habilitando Text-to-Speech API..."
gcloud services enable texttospeech.googleapis.com --quiet 2>/dev/null || true
echo "   ✅ API habilitada"
echo ""

# Carregar roteiro
ROTEIRO_JSON="roteiro.json"

if [ ! -f "$ROTEIRO_JSON" ]; then
    echo "❌ ERRO: Arquivo 'roteiro.json' não encontrado."
    exit 1
fi

echo "📋 Processando roteiro..."
echo ""

# Criar diretório de áudios
mkdir -p audio_narracoes

# Contar cenas
NUM_CENAS=$(jq '.cenas | length' "$ROTEIRO_JSON")

# Função para gerar áudio usando REST API (método oficial)
gerar_audio() {
    local cena_id=$1
    local texto=$2
    local output_file="audio_narracoes/cena_${cena_id}.mp3"
    
    echo "🎙️  Cena ${cena_id}: Gerando áudio..."
    
    # ============================================================
    # VALIDAÇÃO TRIPLA (Artigo I, Cláusula 3.3)
    # ============================================================
    
    # Validação 1: Texto não pode ser null/vazio
    if [ -z "$texto" ] || [ "$texto" = "null" ]; then
        echo "   ⚠️  Texto vazio/null - pulando TTS"
        return 0
    fi
    
    # Validação 2: Tamanho do texto (limite TTS: 5000 chars)
    local texto_len=${#texto}
    if [ $texto_len -gt 5000 ]; then
        echo "   ⚠️  Texto muito longo ($texto_len chars) - truncando para 5000"
        texto="${texto:0:5000}"
    fi
    
    # Validação 3: Texto tem caracteres imprimíveis
    if ! echo "$texto" | grep -q '[[:alnum:]]'; then
        echo "   ⚠️  Texto sem caracteres válidos - pulando TTS"
        return 0
    fi
    
    # ============================================================
    
    # Escapar texto para JSON
    local texto_escaped=$(echo "$texto" | sed 's/"/\\"/g' | tr -d '\n\r')
    
    # Request JSON
    local request_json=$(cat <<EOF
{
  "input": {
    "text": "$texto_escaped"
  },
  "voice": {
    "languageCode": "pt-BR",
    "name": "pt-BR-Neural2-B",
    "ssmlGender": "MALE"
  },
  "audioConfig": {
    "audioEncoding": "MP3",
    "pitch": 0.0,
    "speakingRate": 0.95
  }
}
EOF
)
    
    # Chamada REST API com quota project no header
    # Ref: https://cloud.google.com/docs/authentication/adc-troubleshooting/user-creds
    local response=$(curl -s -X POST \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json; charset=utf-8" \
        -H "X-Goog-User-Project: $PROJECT_ID" \
        --data "$request_json" \
        "https://texttospeech.googleapis.com/v1/text:synthesize")
    
    # Verificar se houve erro
    if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
        local error_msg=$(echo "$response" | jq -r '.error.message')
        echo "   ❌ Falha: $error_msg"
        return 1
    fi
    
    # Extrair audioContent (base64) e decodificar
    echo "$response" | jq -r '.audioContent' | base64 -d > "$output_file"
    
    if [ -f "$output_file" ] && [ -s "$output_file" ]; then
        local size=$(du -h "$output_file" | cut -f1)
        echo "   ✅ Salvo: $output_file ($size)"
    else
        echo "   ❌ Falha ao salvar áudio"
        return 1
    fi
}

# Processar todas as cenas
for i in $(seq 0 $((NUM_CENAS - 1))); do
    TEXTO=$(jq -r ".cenas[$i].narracao" "$ROTEIRO_JSON")  # CORRIGIDO: narracao (pt)
    gerar_audio $((i + 1)) "$TEXTO"
done

echo ""
echo "==============================================================="
echo "✅ Narração completa. Áudios salvos em: audio_narracoes/"
echo ""

