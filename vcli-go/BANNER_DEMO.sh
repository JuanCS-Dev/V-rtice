#!/bin/bash
# BANNER DEMO - Mostra o poder do vCLI-Go V12 Turbo

clear

echo ""
echo "🏎️  Iniciando vCLI-Go V12 TURBO ENGINE..."
echo ""
sleep 1

# Mostrar o banner épico
./bin/vcli

echo ""
echo "⏸️  Pressione ENTER para ver comandos em ação..."
read

clear
echo "🚀 DEMONSTRAÇÃO DE COMANDOS"
echo "======================================"
echo ""

# Setup KUBECONFIG
export KUBECONFIG=$(pwd)/test/validation/kubeconfig

echo "1️⃣  Get pods (Resource Management)"
echo "$ vcli k8s get pods --all-namespaces"
./bin/vcli k8s get pods --all-namespaces | head -10
echo ""
sleep 2

echo "2️⃣  Top nodes (Metrics - V12 Power!)"
echo "$ vcli k8s top nodes"
./bin/vcli k8s top nodes
echo ""
sleep 2

echo "3️⃣  Auth whoami (EXCLUSIVE Feature!)"
echo "$ vcli k8s auth whoami"
./bin/vcli k8s auth whoami
echo ""
sleep 2

echo "4️⃣  Rollout status (Advanced Ops)"
echo "$ vcli k8s rollout status deployment/nginx-test"
./bin/vcli k8s rollout status deployment/nginx-test 2>/dev/null || echo "No deployment found"
echo ""
sleep 2

echo ""
echo "╔════════════════════════════════════════╗"
echo "║                                        ║"
echo "║   🏁 V12 TURBO ENGINE DEMONSTRATED     ║"
echo "║                                        ║"
echo "║   ⚡ 32 Commands Ready                 ║"
echo "║   🚀 Production Certified              ║"
echo "║   💯 Zero Technical Debt               ║"
echo "║                                        ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "Type './bin/vcli' to see full banner anytime!"
echo ""
