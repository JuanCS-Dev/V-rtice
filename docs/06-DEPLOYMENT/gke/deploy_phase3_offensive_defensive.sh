#!/bin/bash
# FASE 3: Deploy Offensive + Defensive Layer (15 serviços)
# Os tentáculos ofensivos e defensivos do Maximus

set -e

KUBECONFIG="/tmp/kubeconfig"
PROJECT_ID="projeto-vertice"
REGION="us-east1"
REGISTRY="us-east1-docker.pkg.dev/${PROJECT_ID}/vertice-images"
NAMESPACE="vertice"

echo "==========================================="
echo "FASE 3: OFFENSIVE + DEFENSIVE LAYER"
echo "Tentáculos de Ataque e Defesa"
echo "==========================================="
echo ""

# Array de serviços com suas portas (verificado nos Dockerfiles reais)
declare -A SERVICES

# OFFENSIVE SERVICES (8)
SERVICES[offensive_orchestrator_service]=8090
SERVICES[offensive_gateway]=8048
SERVICES[offensive_tools_service]=8010
SERVICES[web_attack_service]=8064
SERVICES[malware_analysis_service]=8035
SERVICES[c2_orchestration_service]=8009
SERVICES[social_eng_service]=8055
SERVICES[vuln_scanner_service]=8063

# DEFENSIVE SERVICES (7)
SERVICES[reactive_fabric_core]=8600
SERVICES[reactive_fabric_analysis]=8601
SERVICES[reflex_triage_engine]=8052
SERVICES[homeostatic_regulation]=8022
SERVICES[bas_service]=8008
SERVICES[rte_service]=8053
SERVICES[hsas_service]=8024

SERVICES_DIR="/home/juan/vertice-dev/backend/services"

# Contador
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

  # 1. Build image
  echo "📦 Building image..."
  cd "$SERVICE_DIR"
  docker build -t "${REGISTRY}/${SERVICE}:latest" . 2>&1 | tail -5

  if [ $? -ne 0 ]; then
    echo "❌ Build failed for $SERVICE"
    continue
  fi

  # 2. Push to Artifact Registry
  echo "📤 Pushing to registry..."
  docker push "${REGISTRY}/${SERVICE}:latest" 2>&1 | tail -3

  if [ $? -ne 0 ]; then
    echo "❌ Push failed for $SERVICE"
    continue
  fi

  # 3. Create K8s manifest dynamically
  echo "📝 Creating K8s manifest..."
  MANIFEST="/tmp/${SERVICE}-deployment.yaml"

  # Determine tier label
  TIER="offensive"
  if [[ "$SERVICE" == *"reactive"* ]] || [[ "$SERVICE" == *"reflex"* ]] || [[ "$SERVICE" == *"homeostatic"* ]] || [[ "$SERVICE" == *"bas"* ]] || [[ "$SERVICE" == *"rte"* ]] || [[ "$SERVICE" == *"hsas"* ]]; then
    TIER="defensive"
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
    layer: camada-5-6
    phase: fase-3
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
            memory: "1.5Gi"
            cpu: "500m"
          limits:
            memory: "1.5Gi"
            cpu: "1000m"
        readinessProbe:
          httpGet:
            path: /health
            port: ${PORT}
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: ${PORT}
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 5
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

  # 4. Apply manifest
  echo "🚀 Deploying to GKE..."
  kubectl apply -f "$MANIFEST" --kubeconfig="$KUBECONFIG"

  if [ $? -eq 0 ]; then
    echo "✅ $SERVICE deployed successfully"
  else
    echo "❌ Deployment failed for $SERVICE"
  fi

  # Small delay between deploys
  sleep 2
done

echo ""
echo "==========================================="
echo "✅ FASE 3 DEPLOY COMPLETE"
echo "==========================================="
echo ""
echo "Waiting 30s for pods to start..."
sleep 30

echo ""
echo "=== Pod Status ==="
kubectl get pods -n ${NAMESPACE} --kubeconfig="$KUBECONFIG" -l phase=fase-3

echo ""
echo "=== Total Pod Count ==="
kubectl get pods -n ${NAMESPACE} --kubeconfig="$KUBECONFIG" | grep -c Running || echo "0"

echo ""
echo "=== Next Steps ==="
echo "1. Monitor pods: kubectl get pods -n vertice -w"
echo "2. Validate offensive/defensive pipelines"
echo "3. Scale cluster to 10 nodes for Phase 4"
echo "4. Proceed to Phase 4: Cognition + Sensory (10 services)"
