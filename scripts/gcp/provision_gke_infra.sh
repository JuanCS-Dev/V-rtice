#!/bin/bash
set -e

# Configurações adaptadas ao projeto existente
export PROJECT_ID="projeto-vertice"
export GCP_REGION="southamerica-east1"
export CLUSTER_NAME="vertice-organism-cluster"
export ARTIFACT_REPO="vertice-images"

echo "🧬 FASE 1: Provisionando Infraestrutura GKE"
echo "Project: $PROJECT_ID"
echo "Region: $GCP_REGION"

# Step 1: Configurar projeto
gcloud config set project $PROJECT_ID

# Step 2: Habilitar APIs
echo "📡 Habilitando APIs necessárias..."
gcloud services enable \
  container.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# Step 3: Criar Artifact Registry
echo "🗄️ Criando Artifact Registry..."
gcloud artifacts repositories create $ARTIFACT_REPO \
  --repository-format=docker \
  --location=$GCP_REGION \
  --description="Vertice Organism Docker Images" \
  || echo "Registry já existe"

# Step 4: Criar GKE Cluster
echo "☸️ Criando GKE Cluster (pode levar 5-10 min)..."
gcloud container clusters create $CLUSTER_NAME \
  --region=$GCP_REGION \
  --num-nodes=1 \
  --node-locations=$GCP_REGION-a \
  --machine-type=n1-standard-4 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=3 \
  --enable-autorepair \
  --enable-autoupgrade \
  --disk-size=50GB \
  || echo "Cluster já existe"

# Step 5: Configurar kubectl
echo "🔧 Configurando kubectl..."
gcloud container clusters get-credentials $CLUSTER_NAME \
  --region=$GCP_REGION

# Step 6: Validar acesso
echo "✅ Validando cluster..."
kubectl cluster-info
kubectl get nodes

# Step 7: Configurar Docker auth
echo "🔐 Configurando Docker authentication..."
gcloud auth configure-docker $GCP_REGION-docker.pkg.dev

echo ""
echo "✅ FASE 1 COMPLETA"
echo "Cluster: $CLUSTER_NAME"
echo "Registry: $GCP_REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REPO"
echo "Nodes: $(kubectl get nodes --no-headers | wc -l)"
