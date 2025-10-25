# Instruções de Deploy - vcli-go Cloud Run

## Pré-requisitos
- gcloud CLI configurado
- Docker instalado
- Projeto GCP com APIs habilitadas
- Billing ativo no projeto

## Deploy Inicial (via gcloud)

### 1. Autenticar
```bash
gcloud auth login
gcloud config set project projeto-vertice
gcloud auth configure-docker
```

### 2. Build e Push
```bash
cd /home/maximus/Documentos/V-rtice/vcli-go

# Build imagem
docker build -t gcr.io/projeto-vertice/vcli-go:latest .

# Push para GCR
docker push gcr.io/projeto-vertice/vcli-go:latest
```

### 3. Deploy no Cloud Run
```bash
gcloud run deploy vcli-go \
  --image gcr.io/projeto-vertice/vcli-go:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300s
```

## Redeploy (via script)

Após alterações no código:
```bash
./scripts/redeploy.sh
```

## Comandos Úteis

### Verificar status
```bash
gcloud run services describe vcli-go --region us-central1
```

### Ver logs
```bash
gcloud run services logs read vcli-go --region us-central1 --limit 50
```

### Testar endpoint
```bash
curl https://vcli-go-172846394274.us-central1.run.app/
```

## Informações do Deploy

- **Projeto**: projeto-vertice
- **Region**: us-central1
- **Service URL**: https://vcli-go-172846394274.us-central1.run.app
- **Image**: gcr.io/projeto-vertice/vcli-go
- **Memory**: 512Mi
- **CPU**: 1 vCPU
- **Timeout**: 300s

## Troubleshooting

### Container não inicia
```bash
# Ver logs detalhados
gcloud run services logs read vcli-go --region us-central1 --limit 100
```

### Push falha
```bash
# Reautenticar Docker
gcloud auth configure-docker
```

### Deploy timeout
```bash
# Aumentar timeout
gcloud run deploy vcli-go --timeout 600s
```
