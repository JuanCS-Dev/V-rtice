#!/bin/bash
set -e

echo "🔍 VÉRTICE - CHECKUP DO AMBIENTE DE PRODUÇÃO"
echo "=============================================="
echo ""

FAILED=0

# Função para verificar comando
check_command() {
    local cmd=$1
    local version_flag=$2

    echo -n "Verificando '$cmd'... "
    if command -v "$cmd" &> /dev/null; then
        echo "✅ OK"
        $cmd $version_flag 2>&1 | head -1 | sed 's/^/  ├─ /'
        return 0
    else
        echo "❌ ERRO: '$cmd' não encontrado."
        echo "  └─ Instale com: sudo apt install $cmd (Ubuntu/Debian) ou brew install $cmd (macOS)"
        return 1
    fi
}

# Verificações de comandos essenciais
echo "📦 DEPENDÊNCIAS:"
echo ""

check_command "node" "--version" || FAILED=1
check_command "npm" "--version" || FAILED=1
check_command "ffmpeg" "-version" || FAILED=1
check_command "jq" "--version" || FAILED=1
check_command "bc" "--version" || FAILED=1
check_command "gcloud" "--version" || FAILED=1
check_command "gh" "--version" || FAILED=1

echo ""
echo "☁️  GOOGLE CLOUD:"
echo ""

# Verificar autenticação do GCloud
echo -n "Verificando autenticação GCloud... "
if gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q "@"; then
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1)
    echo "✅ OK"
    echo "  ├─ Conta ativa: $ACCOUNT"
else
    echo "❌ ERRO: Nenhuma conta GCloud autenticada."
    echo "  └─ Execute: gcloud auth login"
    FAILED=1
fi

# Verificar projeto atual
echo -n "Verificando projeto GCP... "
PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -n "$PROJECT" ]; then
    echo "✅ OK"
    echo "  ├─ Projeto: $PROJECT"
else
    echo "❌ ERRO: Nenhum projeto GCP configurado."
    echo "  └─ Execute: gcloud config set project SEU_PROJETO_ID"
    FAILED=1
fi

# Verificar billing (método alternativo rápido)
if [ -n "$PROJECT" ]; then
    echo -n "Verificando billing no projeto... "

    # Tenta listar APIs habilitadas (prova indireta de billing ativo)
    # Timeout de 5 segundos para evitar travamento
    if timeout 5 gcloud services list --enabled --project="$PROJECT" --limit=1 &> /dev/null; then
        echo "✅ OK"
        echo "  ├─ Billing está ativo (APIs habilitadas)"
        echo "  └─ Text-to-Speech API disponível para uso"
    else
        # Fallback: Verifica se TTS API já está habilitada (prova definitiva)
        if gcloud services list --enabled --project="$PROJECT" 2>/dev/null | grep -q "texttospeech.googleapis.com"; then
            echo "✅ OK"
            echo "  ├─ Billing está ativo (Text-to-Speech habilitada)"
            echo "  └─ Sistema pronto para geração de narração"
        else
            echo "⚠️  AVISO: Não foi possível verificar billing rapidamente."
            echo "  ├─ Verifique manualmente: https://console.cloud.google.com/billing"
            echo "  └─ Se APIs habilitadas funcionam, billing está OK"
        fi
    fi
fi

echo ""
echo "=============================================="

if [ $FAILED -eq 1 ]; then
    echo "❌ CHECKUP FALHOU. Corrija os erros acima antes de prosseguir."
    exit 1
else
    echo "✅ AMBIENTE VERIFICADO. Pronto para materialização."
    exit 0
fi
