#!/bin/bash
# Validation script for Vértice GKE deployment

KUBECONFIG="/tmp/kubeconfig"
NAMESPACE="vertice"

echo "==========================================="
echo "VÉRTICE GKE DEPLOYMENT VALIDATION"
echo "==========================================="
echo ""

# 1. Cluster Status
echo "=== 1. CLUSTER STATUS ==="
kubectl cluster-info --kubeconfig="$KUBECONFIG" | head -3
echo ""

# 2. Node Status
echo "=== 2. NODE STATUS ==="
kubectl get nodes --kubeconfig="$KUBECONFIG"
echo ""

# 3. Total Pods Count
echo "=== 3. POD COUNTS ==="
TOTAL_PODS=$(kubectl get pods -n $NAMESPACE --kubeconfig="$KUBECONFIG" | wc -l)
RUNNING_PODS=$(kubectl get pods -n $NAMESPACE --kubeconfig="$KUBECONFIG" --field-selector=status.phase=Running | wc -l)
PENDING_PODS=$(kubectl get pods -n $NAMESPACE --kubeconfig="$KUBECONFIG" --field-selector=status.phase=Pending | wc -l)
FAILED_PODS=$(kubectl get pods -n $NAMESPACE --kubeconfig="$KUBECONFIG" --field-selector=status.phase=Failed | wc -l)

echo "Total Pods: $TOTAL_PODS"
echo "Running: $RUNNING_PODS"
echo "Pending: $PENDING_PODS"
echo "Failed: $FAILED_PODS"
echo ""

# 4. Pods by Phase
echo "=== 4. PODS BY DEPLOYMENT PHASE ==="
for phase in fase-1 fase-2 fase-3 fase-4 fase-5 fase-6; do
  count=$(kubectl get pods -n $NAMESPACE --kubeconfig="$KUBECONFIG" -l phase=$phase 2>/dev/null | grep -v NAME | wc -l)
  running=$(kubectl get pods -n $NAMESPACE --kubeconfig="$KUBECONFIG" -l phase=$phase --field-selector=status.phase=Running 2>/dev/null | wc -l)
  echo "$phase: $running/$count running"
done
echo ""

# 5. Pods by Tier
echo "=== 5. PODS BY TIER ==="
for tier in immune intelligence offensive defensive cognition sensory hcl maximus wargaming infrastructure support; do
  count=$(kubectl get pods -n $NAMESPACE --kubeconfig="$KUBECONFIG" -l tier=$tier 2>/dev/null | grep -v NAME | wc -l)
  if [ $count -gt 0 ]; then
    running=$(kubectl get pods -n $NAMESPACE --kubeconfig="$KUBECONFIG" -l tier=$tier --field-selector=status.phase=Running 2>/dev/null | wc -l)
    echo "$tier: $running/$count running"
  fi
done
echo ""

# 6. Resource Usage
echo "=== 6. RESOURCE USAGE ==="
kubectl top nodes --kubeconfig="$KUBECONFIG"
echo ""

# 7. Failed/Crashing Pods
echo "=== 7. PROBLEMATIC PODS ==="
kubectl get pods -n $NAMESPACE --kubeconfig="$KUBECONFIG" | grep -E "Error|CrashLoop|ImagePull|Pending" || echo "No problematic pods found ✅"
echo ""

# 8. Services
echo "=== 8. SERVICES ==="
SERVICE_COUNT=$(kubectl get svc -n $NAMESPACE --kubeconfig="$KUBECONFIG" | grep -v NAME | wc -l)
echo "Total Services: $SERVICE_COUNT"
echo ""

# 9. ConfigMaps and Secrets
echo "=== 9. CONFIGURATION ==="
kubectl get configmap -n $NAMESPACE --kubeconfig="$KUBECONFIG" | grep vertice
kubectl get secret -n $NAMESPACE --kubeconfig="$KUBECONFIG" | grep vertice
echo ""

# 10. Summary
echo "==========================================="
echo "DEPLOYMENT SUMMARY"
echo "==========================================="
echo "Target: 93 services"
echo "Deployed: $RUNNING_PODS pods running"
PERCENTAGE=$((RUNNING_PODS * 100 / 93))
echo "Progress: ${PERCENTAGE}%"
echo ""

if [ $RUNNING_PODS -ge 85 ]; then
  echo "Status: ✅ EXCELLENT - Ready for frontend integration"
elif [ $RUNNING_PODS -ge 70 ]; then
  echo "Status: ✅ GOOD - Minor fixes needed"
elif [ $RUNNING_PODS -ge 50 ]; then
  echo "Status: ⚠️ PARTIAL - Significant work needed"
else
  echo "Status: ❌ INCOMPLETE - Major deployment required"
fi
echo ""

# 11. Next Steps
echo "=== NEXT STEPS ==="
if [ $RUNNING_PODS -ge 85 ]; then
  echo "1. ✅ Backend deployment complete"
  echo "2. 🔜 Deploy Frontend"
  echo "3. 🔜 E2E Integration Testing"
else
  echo "1. Fix CrashLoopBackOff pods"
  echo "2. Investigate ImagePullBackOff issues"
  echo "3. Complete remaining service deployments"
fi
echo ""
