#!/bin/bash
# FASE 2: Deploy Intelligence Layer (11 serviços)
# Os olhos e ouvidos do Maximus

set -e

KUBECONFIG="/tmp/kubeconfig"
PROJECT_ID="projeto-vertice"
REGION="us-east1"
REGISTRY="us-east1-docker.pkg.dev/${PROJECT_ID}/vertice-images"
NAMESPACE="vertice"

echo "==========================================="
echo "FASE 2: INTELLIGENCE LAYER"
echo "OSINT, Threat Intel, Network Recon"
echo "==========================================="
echo ""

# Array de serviços com suas portas (do Dockerfile real)
declare -A SERVICES
SERVICES[osint_service]=8049
SERVICES[threat_intel_service]=8059
SERVICES[google_osint_service]=8016
SERVICES[network_recon_service]=8045
SERVICES[domain_service]=8014
SERVICES[ip_intelligence_service]=8034
SERVICES[vuln_intel_service]=8062
SERVICES[cyber_service]=8012
SERVICES[network_monitor_service]=8044
SERVICES[ssl_monitor_service]=8057
SERVICES[nmap_service]=8047

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

  cat > "$MANIFEST" <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${SERVICE//_/-}
  namespace: ${NAMESPACE}
  labels:
    app: ${SERVICE//_/-}
    tier: intelligence
    layer: camada-4
    phase: fase-2
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${SERVICE//_/-}
  template:
    metadata:
      labels:
        app: ${SERVICE//_/-}
        tier: intelligence
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
    tier: intelligence
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
echo "✅ FASE 2 DEPLOY COMPLETE"
echo "==========================================="
echo ""
echo "Waiting 30s for pods to start..."
sleep 30

echo ""
echo "=== Pod Status ==="
kubectl get pods -n ${NAMESPACE} --kubeconfig="$KUBECONFIG" | grep -E "tier=intelligence|osint|threat|intel|recon|domain|vuln|cyber|nmap|ssl|monitor" || kubectl get pods -n ${NAMESPACE} -l tier=intelligence --kubeconfig="$KUBECONFIG"

echo ""
echo "=== Next Steps ==="
echo "1. Monitor pods: kubectl get pods -n vertice -w"
echo "2. Validate intelligence pipelines working"
echo "3. Proceed to Phase 3: Offensive + Defensive (15 services)"
