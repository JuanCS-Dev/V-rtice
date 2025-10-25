#!/bin/bash
# FASE 1: Deploy Immune System Complete (10 serviços)
# Padrão Pagani + PPBP Methodology

set -e

KUBECONFIG="/tmp/kubeconfig"
PROJECT_ID="projeto-vertice"
REGION="us-east1"
REGISTRY="us-east1-docker.pkg.dev/${PROJECT_ID}/vertice-images"
NAMESPACE="vertice"

echo "==========================================="
echo "FASE 1: IMMUNE SYSTEM COMPLETE"
echo "==========================================="
echo ""

# Array de serviços com suas portas (verificado nos Dockerfiles reais)
declare -A SERVICES
SERVICES[immunis_bcell_service]=8026
SERVICES[immunis_cytotoxic_t_service]=8027
SERVICES[immunis_dendritic_service]=8028
SERVICES[immunis_helper_t_service]=8029
SERVICES[immunis_macrophage_service]=8030
SERVICES[immunis_neutrophil_service]=8031
SERVICES[immunis_nk_cell_service]=8032
SERVICES[immunis_treg_service]=8033
SERVICES[adaptive_immunity_service]=8000
SERVICES[adaptive_immunity_db]=8602

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
    tier: imunologia
    layer: camada-3
    phase: fase-1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${SERVICE//_/-}
  template:
    metadata:
      labels:
        app: ${SERVICE//_/-}
        tier: imunologia
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
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "1Gi"
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
    tier: imunologia
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
echo "✅ FASE 1 DEPLOY COMPLETE"
echo "==========================================="
echo ""
echo "Waiting 30s for pods to start..."
sleep 30

echo ""
echo "=== Pod Status ==="
kubectl get pods -n ${NAMESPACE} --kubeconfig="$KUBECONFIG" | grep -E "(immunis|adaptive)"

echo ""
echo "=== Next Steps ==="
echo "1. Monitor pods: kubectl get pods -n vertice -w"
echo "2. Check logs if any issues: kubectl logs <pod-name> -n vertice"
echo "3. Proceed to Phase 2 once all pods are 1/1 Running"
