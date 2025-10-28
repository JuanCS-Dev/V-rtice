#!/bin/bash
# Setup Ingress/Load Balancer for Vértice Backend on GKE

set -e

KUBECONFIG="/tmp/kubeconfig"
NAMESPACE="vertice"
PROJECT_ID="projeto-vertice"

echo "==========================================="
echo "VÉRTICE GKE INGRESS SETUP"
echo "Exposing Backend Services via Load Balancer"
echo "==========================================="
echo ""

# 1. Create Ingress for API Gateway
echo "=== 1. Creating Ingress for API Gateway ==="

cat > /tmp/api-gateway-ingress.yaml <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vertice-api-ingress
  namespace: ${NAMESPACE}
  annotations:
    kubernetes.io/ingress.class: "gce"
    kubernetes.io/ingress.global-static-ip-name: "vertice-api-ip"
    networking.gke.io/managed-certificates: "vertice-api-cert"
    kubernetes.io/ingress.allow-http: "true"
spec:
  rules:
  - http:
      paths:
      - path: /*
        pathType: ImplementationSpecific
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  namespace: ${NAMESPACE}
spec:
  type: NodePort
  selector:
    app: api-gateway
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
EOF

echo "Applying Ingress configuration..."
kubectl apply -f /tmp/api-gateway-ingress.yaml --kubeconfig="$KUBECONFIG"

echo ""
echo "=== 2. Reserve Static IP ==="
gcloud compute addresses create vertice-api-ip \
  --global \
  --project=$PROJECT_ID || echo "IP already exists"

STATIC_IP=$(gcloud compute addresses describe vertice-api-ip --global --project=$PROJECT_ID --format="value(address)")
echo "Static IP: $STATIC_IP"

echo ""
echo "=== 3. Wait for Ingress to be Ready ==="
echo "This can take 5-10 minutes..."
kubectl get ingress vertice-api-ingress -n $NAMESPACE --kubeconfig="$KUBECONFIG" -w &
WATCH_PID=$!
sleep 300  # Wait 5 minutes
kill $WATCH_PID 2>/dev/null || true

echo ""
echo "=== 4. Get Ingress IP ==="
INGRESS_IP=$(kubectl get ingress vertice-api-ingress -n $NAMESPACE --kubeconfig="$KUBECONFIG" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Ingress IP: $INGRESS_IP"

echo ""
echo "==========================================="
echo "✅ INGRESS SETUP COMPLETE"
echo "==========================================="
echo ""
echo "API Gateway URL: http://$INGRESS_IP"
echo "Static IP: $STATIC_IP"
echo ""
echo "Next Steps:"
echo "1. Update Frontend environment variables with API Gateway URL"
echo "2. Optionally configure custom domain"
echo "3. Test API endpoints"
