#!/bin/bash
# QUICK FIX: Resolver problemas de dependências sem rebuild completo

set -e

echo "🔧 MAXIMUS Quick Fix - Resolvendo dependências"
echo "=============================================="

# 1. Fix maximus-core import
echo ""
echo "1️⃣ Fixando import do maximus_integrated..."
docker exec maximus-core pip install --no-cache-dir -e /app || echo "⚠️  Container não está rodando"

# 2. Fix hcl-monitor psutil
echo ""
echo "2️⃣ Instalando psutil no hcl-monitor..."
docker exec hcl-monitor pip install --no-cache-dir psutil || echo "⚠️  Container não está rodando"

# 3. Restart serviços corrigidos
echo ""
echo "3️⃣ Restartando serviços..."
docker restart maximus-core hcl-monitor 2>/dev/null || echo "⚠️  Alguns containers falharam"

# 4. Aguardar 10s e verificar status
echo ""
echo "4️⃣ Aguardando serviços iniciarem..."
sleep 10

# 5. Ver logs
echo ""
echo "5️⃣ Verificando logs..."
echo "--- maximus-core ---"
docker logs maximus-core --tail=5 2>&1 | grep -v "WARNING"

echo ""
echo "--- hcl-monitor ---"
docker logs hcl-monitor --tail=5 2>&1 | grep -v "WARNING"

# 6. Status final
echo ""
echo "6️⃣ Status dos containers:"
docker ps --filter "name=maximus-core" --filter "name=hcl-monitor" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "✅ Quick fix completo! Verifique os logs acima."
