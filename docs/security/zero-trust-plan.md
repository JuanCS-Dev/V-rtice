# Plano Zero Trust – Plataforma Vértice v1.0

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Data**: 2024-10-08  
**Status**: ✅ Production Ready

---

## 1. Princípios Fundamentais

### 1.1 Identidade Sobre Rede
Toda requisição deve ser autenticada com identidade forte, independente da origem na rede.

**Implementação**:
- SPIFFE/SPIRE para comunicação serviço-a-serviço
- JWT assinado (Keycloak/Auth0) para clientes (CLI, Frontend)
- Mutual TLS (mTLS) obrigatório para conexões críticas

### 1.2 Least Privilege
Cada identidade recebe apenas as permissões mínimas necessárias.

**Implementação**:
- Políticas RBAC por serviço
- Escopos JWT granulares (e.g., `cli.command.write`, `dashboard.read`)
- Service accounts com permissões específicas

### 1.3 Rotação Contínua
Credenciais e certificados são renovados automaticamente antes da expiração.

**Implementação**:
- Certificados SPIFFE: TTL 24h, renovação automática a 50% do TTL
- JWT tokens: TTL 1h, refresh tokens TTL 24h
- API Keys: TTL 7 dias com rotação programada

### 1.4 Auditoria Total
Todas as autenticações e autorizações são logadas com correlação.

**Implementação**:
- Logs de auth com claims relevantes (sem PII)
- IDs de correlação (X-Trace-Id, X-Request-Id)
- Métricas de falhas de autenticação
- Audit trail imutável (append-only)

---

## 2. Arquitetura de Identidade

### 2.1 Escopos de Proteção

| Domínio | Protocolo | Identidade | Autorização | Rotação |
|---------|-----------|------------|-------------|---------|
| **vcli-go → API Gateway** | HTTPS | JWT (Keycloak) | Scopes: `cli.command.write`, `cli.telemetry.read` | 1h + refresh 24h |
| **Frontend → API Gateway** | HTTPS | JWT OIDC | Scopes: `dashboard.read`, `governance.approve` | 1h + refresh 24h |
| **MAXIMUS ↔ Satellites** | gRPC/HTTPS | SPIFFE SVID | mTLS + RBAC | 24h auto-renew |
| **Gateway → MAXIMUS** | HTTPS/gRPC | JWT + mTLS | Dual auth: token + cert | JWT: 1h, Cert: 24h |
| **Observability Pipelines** | OTLP gRPC | API Key rotativa | Write-only scope | 7 dias programado |
| **Immune Core ↔ Agents** | gRPC | SPIFFE SVID | Agent-specific permissions | 24h auto-renew |

### 2.2 SPIFFE ID Templates

```
# MAXIMUS Core
spiffe://vertice.platform/maximus-core/{hostname}

# Immune Core
spiffe://vertice.platform/immune-core/{hostname}

# Satellites
spiffe://vertice.platform/service/{service-name}/{hostname}

# vcli-go Bridge
spiffe://vertice.platform/vcli-bridge/{hostname}

# API Gateway
spiffe://vertice.platform/api-gateway/{hostname}
```

### 2.3 JWT Claims Structure

**vcli-go**:
```json
{
  "sub": "user-{uuid}",
  "iss": "https://auth.vertice.platform",
  "aud": "api-gateway",
  "exp": 1696777200,
  "iat": 1696773600,
  "scope": "cli.command.write cli.telemetry.read",
  "session_id": "uuid",
  "trace_id": "uuid",
  "client_version": "1.0.0"
}
```

**Frontend**:
```json
{
  "sub": "user-{uuid}",
  "iss": "https://auth.vertice.platform",
  "aud": "api-gateway",
  "exp": 1696777200,
  "iat": 1696773600,
  "scope": "dashboard.read governance.approve",
  "roles": ["operator", "analyst"],
  "trace_id": "uuid"
}
```

---

## 3. Plano de Implementação

### Fase 1: Inventário e Preparação (Semana 1) ✅

**Tarefas Concluídas**:
- ✅ Inventário de identidades e certificados vigentes
- ✅ Mapeamento de fluxos de comunicação
- ✅ Identificação de pontos críticos
- ✅ Definição de templates SPIFFE ID

**Entregáveis**:
- ✅ Documento de arquitetura de identidade
- ✅ Diagrama de fluxos de autenticação
- ✅ Lista de escopos e permissões

### Fase 2: Configuração SPIRE/Vault (Semana 2)

**Atividades**:
1. **Deploy SPIRE Server** (2 dias)
   - Deploy em cluster K8s com HA
   - Configurar backend de armazenamento (etcd/PostgreSQL)
   - Configurar Node Attestation (K8s Workload API)
   - Implementar SPIRE Agent em todos os nós

2. **Configurar Registration Entries** (1 dia)
   - Criar entries para MAXIMUS, Immune Core, Satellites
   - Definir parent-child relationships
   - Configurar federations se necessário

3. **Vault Integration** (1 dia)
   - Deploy Vault (se não existir)
   - Configurar PKI secrets engine
   - Integrar com SPIRE para emissão de certificados
   - Configurar dynamic secrets para databases

4. **Testing** (1 dia)
   - Validar emissão de SVIDs
   - Testar rotação automática
   - Verificar revogação de certificados

**Entregáveis**:
- ⏳ SPIRE Server operacional
- ⏳ Todos os serviços com SVIDs
- ⏳ Vault integrado e configurado
- ⏳ Documentação de operação

### Fase 3: Implementação mTLS (Semana 3)

**Atividades**:
1. **Gateway ↔ MAXIMUS** (2 dias)
   - Configurar mTLS no API Gateway (Envoy/Nginx)
   - Atualizar MAXIMUS para aceitar apenas mTLS
   - Implementar certificate validation
   - Testar conectividade

2. **MAXIMUS ↔ Satellites** (2 dias)
   - Atualizar clientes gRPC para usar mTLS
   - Configurar servers para require client certs
   - Implementar authorization policies baseado em SPIFFE ID
   - Migration gradual (feature flag)

3. **Chaos Day Validation** (1 dia)
   - Simular revogação de certificados
   - Testar rotação durante carga
   - Validar fallback e error handling
   - Documentar comportamento

**Entregáveis**:
- ⏳ mTLS implementado em conexões críticas
- ⏳ Chaos Day report
- ⏳ Métricas de performance impact
- ⏳ Runbook de troubleshooting

### Fase 4: Revisão e Documentação (Semana 4)

**Atividades**:
1. **Policy Review** (1 dia)
   - Revisar e ajustar políticas RBAC
   - Validar least privilege
   - Audit de permissões excessivas

2. **Monitoring & Alerting** (1 dia)
   - Configurar métricas de auth
   - Implementar alertas de falhas
   - Dashboard de security metrics

3. **Documentation** (1 dia)
   - Atualizar Livro Branco
   - Criar runbooks operacionais
   - Documentar incident response

4. **Training** (1 dia)
   - Treinar ops team
   - Criar guias de troubleshooting
   - Simulated incident exercises

**Entregáveis**:
- ⏳ Documentação completa no Livro Branco
- ⏳ Runbooks operacionais
- ⏳ Training materials
- ⏳ Security dashboard

---

## 4. Rotacionamento de Credenciais

### 4.1 Certificados SPIFFE

**Lifecycle**:
- **TTL**: 24 horas
- **Renovação**: Automática a 50% do TTL (12h)
- **Método**: SPIRE Agent renova via SPIRE Server
- **Fallback**: Retry exponencial se falha

**Monitoring**:
```promql
# Certificate expiry time
spire_agent_svid_expiry_time_seconds

# Renewal failures
rate(spire_agent_svid_renewal_failures_total[5m])

# Alert if cert expires < 6h
spire_agent_svid_expiry_time_seconds - time() < 21600
```

### 4.2 JWT Tokens

**Lifecycle**:
- **Access Token TTL**: 1 hora
- **Refresh Token TTL**: 24 horas
- **Renovação**: Cliente deve refresh antes de expiração
- **Revogação**: Via blacklist em Redis (TTL = token TTL)

**Implementation**:
```python
# Token refresh logic
def refresh_token(refresh_token: str) -> Tuple[str, str]:
    # Validate refresh token
    claims = jwt.decode(refresh_token, verify=True)
    
    # Check blacklist
    if redis.exists(f"revoked:{claims['jti']}"):
        raise TokenRevokedException()
    
    # Issue new tokens
    new_access = create_access_token(claims['sub'])
    new_refresh = create_refresh_token(claims['sub'])
    
    # Blacklist old refresh token
    redis.setex(f"revoked:{claims['jti']}", 
                claims['exp'] - time(), 
                "1")
    
    return new_access, new_refresh
```

### 4.3 API Keys (Observability)

**Lifecycle**:
- **TTL**: 7 dias
- **Renovação**: Programada (automation)
- **Método**: Vault dynamic secrets
- **Overlap**: 24h overlap durante transição

**Automation**:
```bash
#!/bin/bash
# API Key rotation script
# Run daily via cron

NEW_KEY=$(vault write -field=key \
  observability/apikeys/generate \
  ttl=168h)

# Deploy new key (overlap)
kubectl create secret generic otel-apikey-new \
  --from-literal=key=$NEW_KEY

# Update deployments gradual
kubectl set env deployment/otel-collector \
  OTEL_API_KEY=$NEW_KEY

# Wait 24h, then delete old key
sleep 86400
kubectl delete secret otel-apikey-old
```

---

## 5. Instrumentação e Auditoria

### 5.1 Logging

**Auth Logs Format**:
```json
{
  "timestamp": "2024-10-08T14:30:00.000Z",
  "level": "INFO",
  "event": "authentication_success",
  "user_id": "uuid",
  "service": "api-gateway",
  "method": "jwt",
  "scope": ["cli.command.write"],
  "trace_id": "uuid",
  "span_id": "uuid",
  "source_ip": "10.0.1.5",
  "user_agent": "vcli-go/1.0.0"
}
```

**Failure Logs**:
```json
{
  "timestamp": "2024-10-08T14:30:05.000Z",
  "level": "WARN",
  "event": "authentication_failure",
  "reason": "expired_token",
  "trace_id": "uuid",
  "source_ip": "10.0.1.5",
  "user_agent": "vcli-go/1.0.0"
}
```

### 5.2 Métricas

**Prometheus Metrics**:
```
# Authentication attempts
auth_attempts_total{method="jwt|spiffe|apikey",result="success|failure"}

# Authentication latency
auth_latency_seconds{method="jwt|spiffe|apikey"}

# Certificate rotation
cert_rotation_attempts_total{result="success|failure"}
cert_rotation_latency_seconds

# Token validations
token_validation_total{result="valid|invalid|expired"}
```

**Grafana Dashboard**:
- Authentication rate by method
- Success/failure ratio
- Certificate expiry timeline
- Token validation latency

### 5.3 Alertas

```yaml
- alert: HighAuthFailureRate
  expr: |
    rate(auth_attempts_total{result="failure"}[5m]) /
    rate(auth_attempts_total[5m]) > 0.10
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High authentication failure rate"

- alert: CertificateExpiringProblema: "Certificado expirando em breve"

- alert: CertRotationFailing
  expr: |
    rate(cert_rotation_attempts_total{result="failure"}[10m]) > 0
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "Certificate rotation failures detected"
```

---

## 6. Incident Response

### 6.1 Compromised Credentials

**Procedure**:
1. **Identify** scope (which credential, when, what access)
2. **Revoke** immediately (blacklist JWT, revoke SVID)
3. **Rotate** all potentially affected credentials
4. **Audit** access logs for suspicious activity
5. **Notify** affected users/services
6. **Document** in incident report

**Commands**:
```bash
# Revoke JWT (add to blacklist)
redis-cli SETEX "revoked:${JTI}" ${TTL} "1"

# Revoke SPIFFE ID
spire-server entry delete -entryID ${ENTRY_ID}

# Force rotation for service
kubectl rollout restart deployment/${SERVICE}
```

### 6.2 SPIRE Server Outage

**Impact**: No new SVIDs issued, existing continue working until expiry

**Response**:
1. **Immediate**: Extend TTL of existing certs (if possible)
2. **Parallel**: Restore SPIRE Server from backup
3. **Monitor**: Certificate expiry times
4. **Communicate**: Warn services of potential issues

**Prevention**:
- HA deployment (3+ servers)
- Regular backups
- Monitoring and alerting

---

## 7. Compliance e Auditoria

### 7.1 Requirements

- **GDPR**: Logs não contêm PII
- **SOC 2**: Audit trail de todas as autenticações
- **ISO 27001**: Rotação de credenciais documentada
- **Doutrina Vértice**: Transparência radical

### 7.2 Audit Trail

**Armazenamento**:
- Formato: JSON Lines append-only
- Retenção: 7 anos (compliance)
- Storage: S3 com bucket versioning
- Encryption: AES-256 at rest

**Query Interface**:
```bash
# Search auth events
aws s3 select \
  --bucket vertice-audit \
  --key "auth-logs/2024-10-08.json.gz" \
  --expression "SELECT * FROM s3object WHERE event='authentication_failure'"

# Generate compliance report
./scripts/generate-auth-report.sh \
  --start-date 2024-10-01 \
  --end-date 2024-10-08 \
  --output report.pdf
```

---

## 8. Próximos Passos

### Imediato (Esta Semana)
- ✅ Plano Zero Trust v1.0 aprovado
- ⏳ Iniciar Deploy SPIRE Server (Fase 2)
- ⏳ Provisionar Vault (se necessário)

### Semana 2-3
- ⏳ Configurar SPIRE para todos os serviços
- ⏳ Implementar mTLS em conexões críticas
- ⏳ Executar Chaos Day de validação

### Semana 4
- ⏳ Documentar no Livro Branco
- ⏳ Training da equipe ops
- ⏳ Go-live production

---

## 9. Referências

### Ferramentas
- [SPIFFE/SPIRE Documentation](https://spiffe.io/docs/)
- [HashiCorp Vault](https://www.vaultproject.io/)
- [Keycloak](https://www.keycloak.org/)

### Standards
- [SPIFFE Standard](https://github.com/spiffe/spiffe)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [JWT RFC 7519](https://tools.ietf.org/html/rfc7519)
- [mTLS Best Practices](https://www.rfc-editor.org/rfc/rfc8705.html)

---

**Versão**: 1.0  
**Promovido**: 2024-10-08  
**v0.1 → v1.0**: Plano completo e production-ready  
**Compliance**: Doutrina Vértice ✅
