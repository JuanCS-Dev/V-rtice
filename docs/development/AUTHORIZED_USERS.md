# 🔐 Vértice Frontend - Usuários Autorizados

**Projeto**: projeto-vertice
**Service**: vertice-frontend
**Region**: us-east1
**Última atualização**: 2025-10-25

---

## 👑 SUPER USERS (Owners)

### 1. Juan Carlos (Owner/Developer)
- **Email**: `juan.brainfarma@gmail.com`
- **Role**: `roles/run.invoker`
- **Acesso**: Total
- **Status**: ✅ AUTORIZADO

**Comando para adicionar**:
```bash
gcloud run services add-iam-policy-binding vertice-frontend \
  --region=us-east1 \
  --member="user:juan.brainfarma@gmail.com" \
  --role="roles/run.invoker" \
  --project=projeto-vertice
```

### 2. juan-dev (Service Account / Superuser PostgreSQL)
- **Email**: `juan-dev@projeto-vertice.iam.gserviceaccount.com`
- **Role**: `roles/run.invoker`
- **Acesso**: Backend integration
- **Status**: ✅ AUTORIZADO

**Comando para adicionar**:
```bash
gcloud run services add-iam-policy-binding vertice-frontend \
  --region=us-east1 \
  --member="serviceAccount:juan-dev@projeto-vertice.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --project=projeto-vertice
```

---

## 🧪 TESTERS (Beta Access)

### Como adicionar novos testadores:

```bash
# Template
gcloud run services add-iam-policy-binding vertice-frontend \
  --region=us-east1 \
  --member="user:EMAIL_DO_TESTER@gmail.com" \
  --role="roles/run.invoker" \
  --project=projeto-vertice
```

### Lista de testadores aprovados:
- [ ] (Aguardando seleção)

---

## 🔍 Verificar Acesso

### Listar todos os usuários autorizados:
```bash
gcloud run services get-iam-policy vertice-frontend \
  --region=us-east1 \
  --project=projeto-vertice
```

### Remover acesso de um usuário:
```bash
gcloud run services remove-iam-policy-binding vertice-frontend \
  --region=us-east1 \
  --member="user:EMAIL@gmail.com" \
  --role="roles/run.invoker" \
  --project=projeto-vertice
```

---

## 🚀 Como Testar Acesso

### 1. Acessar URL do frontend:
```bash
# Após deploy, obter URL:
gcloud run services describe vertice-frontend \
  --region=us-east1 \
  --project=projeto-vertice \
  --format='value(status.url)'
```

### 2. Usuário acessa no browser:
- Será redirecionado para login Google
- Faz login com email autorizado
- Se estiver na whitelist: ✅ Acesso permitido
- Se NÃO estiver: ❌ 403 Forbidden

### 3. Teste via curl (com autenticação):
```bash
# Gerar token de identidade
TOKEN=$(gcloud auth print-identity-token)

# Fazer request autenticado
curl -H "Authorization: Bearer $TOKEN" \
  https://vertice-frontend-XXXXX-ue.a.run.app/health
```

---

## 📊 Auditoria

### Ver logs de acesso:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertice-frontend" \
  --limit=50 \
  --format=json
```

### Filtrar tentativas de acesso negado:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vertice-frontend AND httpRequest.status=403" \
  --limit=20
```

---

## ⚠️ IMPORTANTE

- **NUNCA** use `--allow-unauthenticated` em produção
- Revise a lista de autorizados mensalmente
- Remova acessos de ex-testadores imediatamente
- Use grupos do Google Workspace para gerenciar múltiplos testadores
- Monitore logs de acesso regularmente

---

**Documentação completa**: `frontend/SECURITY_ARCHITECTURE.md`
