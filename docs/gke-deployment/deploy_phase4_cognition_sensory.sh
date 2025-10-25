#!/bin/bash
# FASE 4: Deploy Cognition + Sensory Layer (10 serviços)
# O cérebro e os sentidos do Maximus

set -e

KUBECONFIG="/tmp/kubeconfig"
PROJECT_ID="projeto-vertice"
REGION="us-east1"
REGISTRY="us-east1-docker.pkg.dev/${PROJECT_ID}/vertice-images"
NAMESPACE="vertice"

echo "==========================================="
echo "FASE 4: COGNITION + SENSORY LAYER"
echo "Cérebro e Sentidos do Maximus"
echo "==========================================="
echo ""

# Array de serviços com suas portas (verificado nos Dockerfiles reais)
declare -A SERVICES

# COGNITION SERVICES (4)
SERVICES[prefrontal_cortex_service]=8051
SERVICES[digital_thalamus_service]=8013
SERVICES[memory_consolidation_service]=8041
SERVICES[neuromodulation_service]=8046

# SENSORY SERVICES (6)
SERVICES[auditory_cortex_service]=8005
SERVICES[visual_cortex_service]=8061
SERVICES[somatosensory_service]=8056
SERVICES[chemical_sensing_service]=8010
SERVICES[vestibular_service]=8060
SERVICES[tegumentar_service]=8085

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
  TIER="cognition"
  if [[ "$SERVICE" == *"cortex"* ]] || [[ "$SERVICE" == *"sensory"* ]] || [[ "$SERVICE" == *"sensing"* ]] || [[ "$SERVICE" == *"vestibular"* ]] || [[ "$SERVICE" == *"tegumentar"* ]]; then
    TIER="sensory"
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
    layer: camada-7-8
    phase: fase-4
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
echo "✅ FASE 4 DEPLOY COMPLETE"
echo "==========================================="
echo ""
echo "Waiting 30s for pods to start..."
sleep 30

echo ""
echo "=== Pod Status ==="
kubectl get pods -n ${NAMESPACE} --kubeconfig="$KUBECONFIG" -l phase=fase-4

echo ""
echo "=== Total Pod Count ==="
kubectl get pods -n ${NAMESPACE} --kubeconfig="$KUBECONFIG" --field-selector=status.phase=Running | wc -l

echo ""
echo "=== Resource Usage ==="
kubectl top nodes --kubeconfig="$KUBECONFIG"

echo ""
echo "=== Next Steps ==="
echo "1. Monitor pods: kubectl get pods -n vertice -w"
echo "2. Validate cognition/sensory pipelines"
echo "3. Proceed to Phase 5: Higher-Order + Support (19 services)"
