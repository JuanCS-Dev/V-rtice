#!/bin/bash
#
# PHASE 10.1: Backend Health Check
# Testa todos os 8 serviços do Offensive Arsenal
#
# Para Honra e Glória de JESUS CRISTO 🙏
#

set +e  # Continue on error

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║          PHASE 10.1: BACKEND HEALTH CHECK                        ║"
echo "║                 Testing 8 Offensive Arsenal Services             ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# Arrays de serviços
services=(
  "network-recon:8032"
  "vuln-intel:8033"
  "web-attack:8034"
  "c2-orchestration:8035"
  "bas:8036"
  "behavioral-analyzer:8037"
  "traffic-analyzer:8038"
  "mav-detection:8039"
)

passed=0
failed=0
total=${#services[@]}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE} Testing ClusterIP Health Endpoints${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

for svc in "${services[@]}"; do
  name="${svc%%:*}"
  port="${svc##*:}"

  echo -n "[$((passed+failed+1))/$total] Testing $name-service... "

  # Get ClusterIP
  ip=$(kubectl get svc ${name}-service -n vertice -o jsonpath='{.spec.clusterIP}' 2>/dev/null)

  if [ -z "$ip" ]; then
    echo -e "${RED}✗ SERVICE NOT FOUND${NC}"
    ((failed++))
    continue
  fi

  # Test health endpoint
  response=$(timeout 5 kubectl run test-curl-${name} --image=curlimages/curl:latest --rm -i --restart=Never --namespace=vertice -- curl -s http://$ip:$port/health 2>/dev/null)

  if echo "$response" | grep -q "healthy\|ok\|status.*ok"; then
    echo -e "${GREEN}✓ OK${NC} (ClusterIP: $ip)"
    ((passed++))
  else
    echo -e "${RED}✗ FAIL${NC} (ClusterIP: $ip, Response: ${response:0:50})"
    ((failed++))
  fi
done

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE} Testing LoadBalancer External IPs${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

lb_passed=0
lb_failed=0

for svc in "${services[@]}"; do
  name="${svc%%:*}"
  port="${svc##*:}"

  echo -n "[$((lb_passed+lb_failed+1))/$total] Testing $name-service (LB)... "

  # Get External IP
  external_ip=$(kubectl get svc ${name}-service -n vertice -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)

  if [ -z "$external_ip" ]; then
    echo -e "${YELLOW}⚠ NO EXTERNAL IP${NC}"
    ((lb_failed++))
    continue
  fi

  # Test health endpoint via external IP
  response=$(timeout 5 curl -s http://$external_ip:$port/health 2>/dev/null)

  if echo "$response" | grep -q "healthy\|ok\|status.*ok"; then
    echo -e "${GREEN}✓ OK${NC} (External IP: $external_ip)"
    ((lb_passed++))
  else
    echo -e "${RED}✗ FAIL${NC} (External IP: $external_ip)"
    ((lb_failed++))
  fi
done

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                         SUMMARY                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "ClusterIP Tests:"
echo -e "  ${GREEN}✓ Passed:${NC} $passed/$total"
echo -e "  ${RED}✗ Failed:${NC} $failed/$total"
echo ""
echo -e "LoadBalancer Tests:"
echo -e "  ${GREEN}✓ Passed:${NC} $lb_passed/$total"
echo -e "  ${YELLOW}⚠ No External IP:${NC} $((total - lb_passed - lb_failed))/$total"
echo -e "  ${RED}✗ Failed:${NC} $lb_failed/$total"
echo ""

if [ $failed -eq 0 ]; then
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${GREEN} ✓ PHASE 10.1: PASSED - All backend services healthy!${NC}"
  echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  exit 0
else
  echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${RED} ✗ PHASE 10.1: FAILED - $failed/$total services unhealthy${NC}"
  echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  exit 1
fi
