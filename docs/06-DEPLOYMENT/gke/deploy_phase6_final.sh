#!/bin/bash
# FASE 6: Deploy Final Services (29 remaining services)
# Completing the organism deployment

set -e

KUBECONFIG="/tmp/kubeconfig"
PROJECT_ID="projeto-vertice"
REGION="us-east1"
REGISTRY="us-east1-docker.pkg.dev/${PROJECT_ID}/vertice-images"
NAMESPACE="vertice"

echo "==========================================="
echo "FASE 6: FINAL SERVICES DEPLOYMENT"
echo "Completing Vértice Backend Deployment"
echo "==========================================="
echo ""

# Array of all remaining services with their ports
declare -A SERVICES

# Core services
SERVICES[adr_core_service]=8001
SERVICES[atlas_service]=8004
SERVICES[command_bus_service]=8092
SERVICES[verdict_engine_service]=8093
SERVICES[vertice_register]=8888

# Maximus services
SERVICES[maximus_dlq_monitor_service]=8220
SERVICES[maximus_integration_service]=8037
SERVICES[maximus_oraculo_v2]=8000

# Intelligence & Analysis
SERVICES[narrative_analysis_service]=8042
SERVICES[narrative_filter_service]=8000
SERVICES[narrative_manipulation_filter]=8043
SERVICES[predictive_threat_hunting_service]=8050
SERVICES[autonomous_investigation_service]=8007

# Infrastructure
SERVICES[cloud_coordinator_service]=8011
SERVICES[edge_agent_service]=8015
SERVICES[agent_communication]=8603
SERVICES[hpc_service]=8023

# Wargaming & Testing
SERVICES[wargaming_crisol]=8026
SERVICES[purple_team]=8604
SERVICES[mock_vulnerable_apps]=8000

# Support services
SERVICES[ethical_audit_service]=8350
SERVICES[hitl_patch_service]=8027
SERVICES[system_architect_service]=8297
SERVICES[threat_intel_bridge]=8000

# Data ingestion
SERVICES[tataca_ingestion]=8400
SERVICES[seriema_graph]=8300
SERVICES[sinesp_service]=8054

# Test service (skip if not needed)
# SERVICES[test_service_for_sidecar]=8080
# SERVICES[vertice_registry_sidecar]=NOT_FOUND

SERVICES_DIR="/home/juan/vertice-dev/backend/services"

TOTAL=${#SERVICES[@]}
COUNT=0

for SERVICE in "${!SERVICES[@]}"; do
  COUNT=$((COUNT + 1))
  PORT=${SERVICES[$SERVICE]}

  echo ""
  echo "=== [$COUNT/$TOTAL] $SERVICE (port $PORT) ==="

  SERVICE_DIR="$SERVICES_DIR/$SERVICE"

  if [ ! -d "$SERVICE_DIR" ]; then
    echo "❌ Directory not found: $SERVICE_DIR"
    continue
  fi

  if [ ! -f "$SERVICE_DIR/Dockerfile" ]; then
    echo "❌ Dockerfile not found"
    continue
  fi

  echo "📦 Building image..."
  cd "$SERVICE_DIR"
  docker build -t "${REGISTRY}/${SERVICE}:latest" . 2>&1 | tail -5

  if [ $? -ne 0 ]; then
    echo "❌ Build failed for $SERVICE"
    continue
  fi

  echo "📤 Pushing to registry..."
  docker push "${REGISTRY}/${SERVICE}:latest" 2>&1 | tail -3

  if [ $? -ne 0 ]; then
    echo "❌ Push failed for $SERVICE"
    continue
  fi

  echo "📝 Creating K8s manifest..."
  MANIFEST="/tmp/${SERVICE}-deployment.yaml"

  # Determine tier label based on service type
  TIER="support"
  if [[ "$SERVICE" == *"maximus"* ]]; then
    TIER="maximus"
  elif [[ "$SERVICE" == *"narrative"* ]] || [[ "$SERVICE" == *"predictive"* ]] || [[ "$SERVICE" == *"investigation"* ]]; then
    TIER="intelligence"
  elif [[ "$SERVICE" == *"wargaming"* ]] || [[ "$SERVICE" == *"purple"* ]]; then
    TIER="wargaming"
  elif [[ "$SERVICE" == *"cloud"* ]] || [[ "$SERVICE" == *"edge"* ]] || [[ "$SERVICE" == *"agent"* ]]; then
    TIER="infrastructure"
  fi

  cat > "$MANIFEST" <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${SERVICE//_/-}
  namespace: ${NAMESPACE}
  labels:
    app: ${SERVICE//_/-}
    tier: ${TIER}
    phase: fase-6
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${SERVICE//_/-}
  template:
    metadata:
      labels:
        app: ${SERVICE//_/-}
        tier: ${TIER}
    spec:
      containers:
      - name: ${SERVICE//_/-}
        image: ${REGISTRY}/${SERVICE}:latest
        ports:
        - containerPort: ${PORT}
          name: http
        env:
        - name: SERVICE_NAME
          value: "${SERVICE}"
        - name: SERVICE_HOST
          value: "0.0.0.0"
        - name: SERVICE_PORT
          value: "${PORT}"
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: vertice-global-config
              key: LOG_LEVEL
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: vertice-global-config
              key: ENVIRONMENT
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka:9092"
        - name: REDIS_HOST
          value: "redis"
        - name: REDIS_PORT
          value: "6379"
        - name: POSTGRES_HOST
          value: "postgres"
        - name: POSTGRES_PORT
          value: "5432"
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: vertice-core-secrets
              key: POSTGRES_USER
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: vertice-core-secrets
              key: POSTGRES_PASSWORD
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: vertice-core-secrets
              key: POSTGRES_DB
        - name: API_GATEWAY_URL
          value: "http://api-gateway:8000"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
        readinessProbe:
          httpGet:
            path: /health
            port: ${PORT}
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /health
            port: ${PORT}
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
---
apiVersion: v1
kind: Service
metadata:
  name: ${SERVICE//_/-}
  namespace: ${NAMESPACE}
  labels:
    app: ${SERVICE//_/-}
    tier: ${TIER}
spec:
  type: ClusterIP
  ports:
  - port: ${PORT}
    targetPort: ${PORT}
    protocol: TCP
    name: http
  selector:
    app: ${SERVICE//_/-}
EOF

  echo "🚀 Deploying to GKE..."
  kubectl apply -f "$MANIFEST" --kubeconfig="$KUBECONFIG"

  if [ $? -eq 0 ]; then
    echo "✅ $SERVICE deployed successfully"
  else
    echo "❌ Deployment failed for $SERVICE"
  fi

  sleep 2
done

echo ""
echo "==========================================="
echo "✅ FASE 6 DEPLOY COMPLETE"
echo "==========================================="
echo ""
echo "Waiting 45s for pods to start..."
sleep 45

echo ""
echo "=== Pod Status (Phase 6) ==="
kubectl get pods -n ${NAMESPACE} --kubeconfig="$KUBECONFIG" -l phase=fase-6

echo ""
echo "=== Total Running Pods ==="
kubectl get pods -n ${NAMESPACE} --kubeconfig="$KUBECONFIG" --field-selector=status.phase=Running | wc -l

echo ""
echo "=== Resource Usage ==="
kubectl top nodes --kubeconfig="$KUBECONFIG"

echo ""
echo "=== Next Steps ==="
echo "1. Fix any remaining CrashLoopBackOff pods"
echo "2. Deploy Frontend to GKE/Cloud Run"
echo "3. Full E2E integration testing!"
