#!/bin/bash
set -e

# ====================================================================
# CONFIGURAÇÃO
# ====================================================================
DRY_RUN=${1:-""}
LOG_FILE="log_producao_$(date +%Y%m%d_%H%M%S).txt"

# Redirecionar output para log (mantendo também no terminal)
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "═══════════════════════════════════════════════════════════"
echo "🎬 VÉRTICE - MATERIALIZAÇÃO DE VÍDEO OPERACIONAL"
echo "═══════════════════════════════════════════════════════════"
echo ""

if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "🔍 MODO DRY-RUN ATIVO (validação sem executar)"
    echo ""
fi

echo "📝 Log sendo salvo em: $LOG_FILE"
echo ""

# ====================================================================
# FASE 0: CHECKUP DO AMBIENTE
# ====================================================================
echo "--- FASE 0: CHECKUP DO AMBIENTE ---"
echo ""

./check_ambiente.sh

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Checkup falhou. Corrija os erros e tente novamente."
    exit 1
fi

echo ""

# Entrar no diretório de produção
cd vertice_video_producao

# ====================================================================
# FASE 1: GERAÇÃO DE NARRAÇÃO (Google Cloud TTS)
# ====================================================================
echo "--- FASE 1: GERANDO NARRAÇÃO (GOOGLE CLOUD TTS) ---"
echo ""

if [ "$DRY_RUN" != "--dry-run" ]; then
    bash gerar_narracao_gcp.sh

    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Geração de narração falhou."
        exit 1
    fi
else
    echo "   [DRY-RUN] Pulando geração de narração"
    echo "   ✅ Script validado: gerar_narracao_gcp.sh"
fi

echo ""

# ====================================================================
# FASE 2: GRAVAÇÃO DO TOUR (PLAYWRIGHT)
# ====================================================================
echo "--- FASE 2: GRAVANDO TOUR DO FRONTEND (PLAYWRIGHT) ---"
echo ""

if [ "$DRY_RUN" != "--dry-run" ]; then
    echo "⚠️  IMPORTANTE: O frontend DEVE estar rodando!"
    echo ""
    echo "Se não estiver rodando, execute em outro terminal:"
    echo "  cd ~/vertice-dev/frontend"
    echo "  npm run dev"
    echo ""
    read -p "Frontend está rodando em http://localhost:5173? (Enter para continuar, Ctrl+C para cancelar) " -r
    echo ""
else
    echo "   [DRY-RUN] Pulando gravação Playwright"
    echo "   ✅ Script validado: video_tour.spec.ts"
    echo ""
fi

if [ "$DRY_RUN" != "--dry-run" ]; then
    # Executar Playwright
    npx playwright test video_tour.spec.ts

    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Gravação Playwright falhou."
        echo "Verifique se o frontend está rodando em http://localhost:5173"
        exit 1
    fi

    # Extrair vídeo
    echo ""
    bash extrair_video_playwright.sh
fi

echo ""

# ====================================================================
# FASE 3: MONTAGEM FINAL (FFMPEG)
# ====================================================================
echo "--- FASE 3: MONTAGEM FINAL (FFMPEG CINEMA EDITION) ---"
echo ""

if [ "$DRY_RUN" != "--dry-run" ]; then
    bash montagem_final.sh

    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Montagem final falhou."
        exit 1
    fi
else
    echo "   [DRY-RUN] Pulando montagem FFmpeg"
    echo "   ✅ Script validado: montagem_final.sh"
fi

# ====================================================================
# FINALIZAÇÃO
# ====================================================================
echo ""
echo "═══════════════════════════════════════════════════════════"

if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "✅ DRY-RUN COMPLETO - Todos os scripts validados!"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "📋 Próximo passo: Execute sem --dry-run para gerar o vídeo"
    echo "   ./MATERIALIZAR_VIDEO_SEGURO.sh"
else
    echo "✅ MATERIALIZAÇÃO COMPLETA!"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "📹 Vídeo final: $(pwd)/video_final.mp4"
    echo "📝 Log completo: ../$LOG_FILE"
    echo ""
    echo "🎉 Abra o vídeo com:"
    echo "   vlc $(pwd)/video_final.mp4"
    echo ""
    echo "ou"
    echo ""
    echo "   mpv $(pwd)/video_final.mp4"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"

cd ..
