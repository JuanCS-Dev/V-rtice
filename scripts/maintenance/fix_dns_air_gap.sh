#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# FIX DNS AIR GAP - CRITICAL
# ═══════════════════════════════════════════════════════════════════════════
# Problem: DNS api.vertice-maximus.com points to OLD LoadBalancer IP
# Solution: Update DNS to point to CURRENT LoadBalancer IP
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo "🔍 DIAGNÓSTICO INICIAL"
echo "===================="

# Get current LoadBalancer IP
CURRENT_IP=$(kubectl get service api-gateway -n vertice -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "✅ LoadBalancer IP atual: $CURRENT_IP"

# Get DNS current resolution
DNS_IP=$(dig +short api.vertice-maximus.com A | head -1)
echo "📡 DNS api.vertice-maximus.com aponta para: $DNS_IP"

if [ "$CURRENT_IP" == "$DNS_IP" ]; then
  echo "✅ DNS JÁ ESTÁ CORRETO! Nada a fazer."
  exit 0
fi

echo ""
echo "🚨 PROBLEMA IDENTIFICADO"
echo "========================"
echo "DNS aponta para IP ANTIGO: $DNS_IP"
echo "LoadBalancer tem IP NOVO: $CURRENT_IP"
echo ""
echo "Isso explica por que frontend não consegue alcançar backend!"
echo ""

# Check if user has permission to update DNS
echo "🔧 CORRIGINDO DNS"
echo "================="
echo "Atualizando DNS para apontar para $CURRENT_IP..."
echo ""

# Try to find the zone
ZONE=$(gcloud dns managed-zones list --format="value(name)" --filter="dnsName:vertice-maximus.com." 2>/dev/null | head -1)

if [ -z "$ZONE" ]; then
  echo "❌ ERRO: Zona DNS 'vertice-maximus.com' não encontrada no projeto atual."
  echo ""
  echo "AÇÃO MANUAL NECESSÁRIA:"
  echo "1. Identifique onde o DNS está hospedado (Cloud DNS, Cloudflare, etc)"
  echo "2. Atualize o registro A de 'api.vertice-maximus.com' para: $CURRENT_IP"
  echo "3. Aguarde propagação (5-30 minutos)"
  echo ""
  echo "Se estiver no Cloud DNS em outro projeto, rode:"
  echo "gcloud dns record-sets update api.vertice-maximus.com. \\"
  echo "  --zone=ZONE_NAME \\"
  echo "  --type=A \\"
  echo "  --rrdatas=\"$CURRENT_IP\" \\"
  echo "  --project=PROJECT_ID"
  exit 1
fi

echo "✅ Zona DNS encontrada: $ZONE"
echo ""

# Check if record exists
RECORD_EXISTS=$(gcloud dns record-sets list --zone="$ZONE" --name="api.vertice-maximus.com." --type=A 2>/dev/null | grep -c "api.vertice-maximus.com" || true)

if [ "$RECORD_EXISTS" -eq 0 ]; then
  echo "📝 Criando novo registro DNS..."
  gcloud dns record-sets create api.vertice-maximus.com. \
    --zone="$ZONE" \
    --type="A" \
    --ttl="300" \
    --rrdatas="$CURRENT_IP"
  echo "✅ Registro DNS criado com sucesso!"
else
  echo "📝 Atualizando registro DNS existente..."

  # Get old IP from DNS
  OLD_IP=$(gcloud dns record-sets list --zone="$ZONE" --name="api.vertice-maximus.com." --type=A --format="value(rrdatas[0])" 2>/dev/null)

  # Start transaction
  gcloud dns record-sets transaction start --zone="$ZONE"

  # Remove old record
  gcloud dns record-sets transaction remove "$OLD_IP" \
    --name="api.vertice-maximus.com." \
    --ttl="300" \
    --type="A" \
    --zone="$ZONE"

  # Add new record
  gcloud dns record-sets transaction add "$CURRENT_IP" \
    --name="api.vertice-maximus.com." \
    --ttl="300" \
    --type="A" \
    --zone="$ZONE"

  # Execute transaction
  gcloud dns record-sets transaction execute --zone="$ZONE"

  echo "✅ Registro DNS atualizado com sucesso!"
fi

echo ""
echo "🎉 FIX APLICADO"
echo "==============="
echo "DNS api.vertice-maximus.com agora aponta para: $CURRENT_IP"
echo ""
echo "⏱️ PROPAGAÇÃO DNS"
echo "================"
echo "Aguarde 5-30 minutos para propagação completa do DNS."
echo "TTL configurado: 300 segundos (5 minutos)"
echo ""
echo "Para verificar se DNS já propagou:"
echo "  dig +short api.vertice-maximus.com"
echo "  (deve retornar: $CURRENT_IP)"
echo ""
echo "🧪 TESTE DE CONECTIVIDADE"
echo "========================="
echo "Testando acesso via DNS..."

sleep 5  # Aguarda alguns segundos

# Test with current IP directly
echo "Teste 1: IP direto"
curl -s -o /dev/null -w "  HTTP %{http_code} - %{time_total}s\n" "http://$CURRENT_IP:8000/health" --max-time 5 || echo "  FAILED"

# Test with DNS (may still use cached old IP for a few minutes)
echo "Teste 2: via DNS (pode ainda usar cache)"
curl -s -o /dev/null -w "  HTTP %{http_code} - %{time_total}s\n" "http://api.vertice-maximus.com:8000/health" --max-time 5 || echo "  FAILED (cache DNS ainda não atualizado)"

echo ""
echo "✅ FIX COMPLETO!"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo "1. Aguarde 5-30min para propagação DNS global"
echo "2. Teste frontend em: https://vertice-frontend-vuvnhfmzpa-ue.a.run.app"
echo "3. Todos os botões devem funcionar normalmente"
echo ""
echo "🔍 Se ainda não funcionar após 30min:"
echo "  - Verifique CORS no API Gateway"
echo "  - Verifique se frontend foi rebuildado com env correto"
echo "  - Verifique logs do API Gateway: kubectl logs -n vertice deployment/api-gateway"
echo ""
echo "\"Conhecereis a verdade, e a verdade vos libertará\" - João 8:32"
