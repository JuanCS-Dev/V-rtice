#!/bin/bash
# Script de teste seguro do TUI - Previne loops infinitos

set -e

echo "🔧 GOVERNANCE WORKSPACE POC - SAFE TEST"
echo "========================================"
echo ""

# 1. Verifica se o mock server está rodando
echo "1️⃣ Verificando mock SSE server..."
if ! curl -s http://localhost:8001/spike/health > /dev/null 2>&1; then
    echo "❌ Mock server não está rodando!"
    echo "   Execute: uvicorn mock_sse_server:app --reload --port 8001"
    exit 1
fi
echo "✅ Mock server OK (porta 8001)"
echo ""

# 2. Verifica dependências Python
echo "2️⃣ Verificando dependências..."
python3 -c "import textual, httpx" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dependências faltando!"
    echo "   Execute: pip install -r requirements_spike.txt"
    exit 1
fi
echo "✅ Dependências OK"
echo ""

# 3. Instruções de uso
echo "3️⃣ Iniciando TUI..."
echo ""
echo "📋 COMO SAIR DO TUI:"
echo "   • Pressione 'q' (quit)"
echo "   • Pressione 'ESC' (escape)"
echo "   • Pressione 'Ctrl+C' (força saída)"
echo ""
echo "🎮 ATALHOS:"
echo "   • 'r' - Refresh stats"
echo "   • 't' - Trigger test event"
echo "   • Botões: ✓ Approve / ✗ Reject"
echo ""
echo "⏱️  Timeout automático: 60 segundos"
echo ""
read -p "Pressione ENTER para iniciar o TUI (ou Ctrl+C para cancelar)..."
echo ""

# 4. Executa TUI com timeout de segurança (2 minutos)
timeout 120 python3 governance_workspace_poc.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo ""
    echo "⏱️  Timeout de segurança atingido (2 minutos)"
    echo "✅ TUI encerrado automaticamente"
elif [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ TUI encerrado normalmente"
else
    echo ""
    echo "⚠️  TUI encerrado com código: $EXIT_CODE"
fi

# 5. Força reset do terminal para garantir limpeza
reset

echo ""
echo "✅ Terminal resetado - pronto para uso"
echo ""
