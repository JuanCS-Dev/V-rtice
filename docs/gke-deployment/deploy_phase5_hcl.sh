#!/bin/bash
# FASE 5: Deploy Higher-Order Cognitive Loop (6 serviços prontos)
# Cognição avançada do Maximus

set -e

KUBECONFIG="/tmp/kubeconfig"
PROJECT_ID="projeto-vertice"
REGION="us-east1"
REGISTRY="us-east1-docker.pkg.dev/${PROJECT_ID}/vertice-images"
NAMESPACE="vertice"

echo "==========================================="
echo "FASE 5: HIGHER-ORDER COGNITIVE LOOP"
echo "Cognição Avançada do Maximus"
echo "==========================================="
echo ""

# Array de serviços HCL com Dockerfiles
declare -A SERVICES
SERVICES[hcl_analyzer_service]=8017
SERVICES[hcl_planner_service]=8021
SERVICES[hcl_executor_service]=8018
SERVICES[hcl_kb_service]=8019
SERVICES[hcl_monitor_service]=8020
SERVICES[strategic_planning_service]=8058

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

  cat > "$MANIFEST" <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${SERVICE//_/-}
  namespace: ${NAMESPACE}
  labels:
    app: ${SERVICE//_/-}
    tier: hcl
    layer: camada-9
    phase: fase-5
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${SERVICE//_/-}
  template:
    metadata:
      labels:
        app: ${SERVICE//_/-}
        tier: hcl
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
    tier: hcl
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
echo "✅ FASE 5 DEPLOY COMPLETE"
echo "==========================================="
echo ""
echo "Waiting 30s for pods to start..."
sleep 30

echo ""
echo "=== Pod Status ==="
kubectl get pods -n ${NAMESPACE} --kubeconfig="$KUBECONFIG" -l tier=hcl

echo ""
echo "=== Total Running Pods ==="
kubectl get pods -n ${NAMESPACE} --kubeconfig="$KUBECONFIG" --field-selector=status.phase=Running | wc -l

echo ""
echo "=== Resource Usage ==="
kubectl top nodes --kubeconfig="$KUBECONFIG"

echo ""
echo "=== Next Steps ==="
echo "1. Phase 6: Wargaming + HUB-AI (9 services)"
echo "2. Frontend deployment"
echo "3. Full integration!"
