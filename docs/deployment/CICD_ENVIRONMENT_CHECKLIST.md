# CI/CD Environment Variables Checklist
# Vértice MAXIMUS Frontend - Production Deployment

**Version:** 1.0
**Last Updated:** 2025-10-28
**Purpose:** Ensure all required environment variables are properly injected during CI/CD deployment

---

## ⚠️ CRITICAL - NEVER COMMIT REAL VALUES TO VERSION CONTROL

All production values MUST be:
- Stored in CI/CD secrets (GitHub Actions Secrets, GitLab CI Variables, etc.)
- Injected at build time
- NEVER hardcoded in `.env.production` or any tracked file

---

## 📋 REQUIRED ENVIRONMENT VARIABLES (PRODUCTION)

### 1. Core API Configuration

| Variable | Description | Example Value | Status |
|----------|-------------|---------------|--------|
| `VITE_API_GATEWAY_URL` | Main API Gateway endpoint | `https://api.vertice.yourdomain.com` | ⚠️ REQUIRED |
| `VITE_API_KEY` | API authentication key | `prod_key_xxxxxxxxxxxxx` | ⚠️ REQUIRED |

**Validation:**
- MUST use `https://` protocol (not `http://`)
- MUST be a valid domain name (not IP address)
- API key MUST be at least 32 characters

---

### 2. MAXIMUS AI Services

| Variable | Description | Example Value | Status |
|----------|-------------|---------------|--------|
| `VITE_MAXIMUS_CORE_URL` | MAXIMUS Core AI Engine | `https://api.vertice.yourdomain.com` | ⚠️ REQUIRED |
| `VITE_MAXIMUS_ORCHESTRATOR_URL` | Task orchestration | `https://api.vertice.yourdomain.com` | Optional |
| `VITE_MAXIMUS_EUREKA_URL` | Pattern recognition | `https://api.vertice.yourdomain.com` | Optional |
| `VITE_MAXIMUS_ORACULO_URL` | Threat prediction | `https://api.vertice.yourdomain.com` | Optional |

**Note:** All MAXIMUS services typically route through the API Gateway in production.

---

### 3. WebSocket Endpoints

| Variable | Description | Example Value | Status |
|----------|-------------|---------------|--------|
| `VITE_MAXIMUS_WS_URL` | MAXIMUS real-time stream | `wss://api.vertice.yourdomain.com/ws/stream` | ⚠️ REQUIRED |
| `VITE_DEFENSIVE_WS_URL` | Defensive alerts stream | `wss://api.vertice.yourdomain.com/ws/alerts` | ⚠️ REQUIRED |
| `VITE_CONSCIOUSNESS_WS_URL` | AI consciousness stream | `wss://api.vertice.yourdomain.com/stream/consciousness/ws` | Optional |
| `VITE_APV_WS_URL` | APV threat stream | `wss://api.vertice.yourdomain.com/stream/apv/ws` | Optional |
| `VITE_HITL_WS_URL` | HITL decisions stream | `wss://api.vertice.yourdomain.com/hitl/ws` | Optional |
| `VITE_OFFENSIVE_WS_URL` | Offensive executions | `wss://api.vertice.yourdomain.com/ws/executions` | Optional |
| `VITE_VERDICT_ENGINE_WS` | Verdict stream | `wss://api.vertice.yourdomain.com/ws/verdicts` | Optional |

**Validation:**
- MUST use `wss://` protocol (WebSocket Secure - not `ws://`)
- MUST match the domain of `VITE_API_GATEWAY_URL`

---

### 4. Authentication Configuration

| Variable | Description | Example Value | Status |
|----------|-------------|---------------|--------|
| `VITE_SUPER_ADMIN_EMAIL` | Super admin email address | `admin@yourdomain.com` | ⚠️ REQUIRED |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth Client ID | `xxxxx.apps.googleusercontent.com` | Optional |
| `VITE_AUTH_SERVICE_URL` | Auth service endpoint | `https://api.vertice.yourdomain.com` | Optional |

**Security:**
- Super admin email MUST be a verified, controlled email address
- Google Client ID should be specific to production domain

---

### 5. Service-Specific URLs (Optional)

All these typically default to API Gateway, but can be overridden if services are deployed separately:

| Variable | Default | Override Example |
|----------|---------|------------------|
| `VITE_DEFENSIVE_CORE_URL` | API Gateway | `https://defensive.vertice.yourdomain.com` |
| `VITE_OFFENSIVE_GATEWAY_URL` | API Gateway | `https://offensive.vertice.yourdomain.com` |
| `VITE_IMMUNIS_API_URL` | API Gateway | `https://immunis.vertice.yourdomain.com` |
| `VITE_HITL_API_URL` | API Gateway | `https://hitl.vertice.yourdomain.com` |
| `VITE_OSINT_API_URL` | API Gateway | `https://osint.vertice.yourdomain.com` |
| `VITE_REACTIVE_FABRIC_API_URL` | API Gateway | `https://fabric.vertice.yourdomain.com` |
| `VITE_NARRATIVE_FILTER_API` | API Gateway | `https://narrative.vertice.yourdomain.com` |
| `VITE_VERDICT_ENGINE_API` | API Gateway | `https://verdicts.vertice.yourdomain.com` |
| `VITE_COMMAND_BUS_API` | API Gateway | `https://commands.vertice.yourdomain.com` |

---

### 6. Feature Flags

| Variable | Description | Production Value | Status |
|----------|-------------|------------------|--------|
| `VITE_USE_MOCK_AUTH` | Enable mock authentication | `false` | ⚠️ MUST BE FALSE |
| `VITE_ENABLE_REAL_TIME_THREATS` | Enable real-time threat streaming | `true` | Recommended |
| `VITE_ENV` | Environment identifier | `production` | ⚠️ REQUIRED |

**Critical:**
- `VITE_USE_MOCK_AUTH` MUST be `false` in production
- Never enable mock auth in production builds

---

## 🔒 SECURITY VALIDATION CHECKLIST

Before deploying to production, verify:

- [ ] All URLs use HTTPS/WSS protocols (no HTTP/WS)
- [ ] No IP addresses in configuration (use domain names)
- [ ] API key is at least 32 characters
- [ ] Super admin email is verified and controlled
- [ ] Mock authentication is disabled (`VITE_USE_MOCK_AUTH=false`)
- [ ] `.env` and `.env.local` are in `.gitignore`
- [ ] No secrets are committed to version control
- [ ] CI/CD secrets are properly configured
- [ ] SSL/TLS certificates are valid and not expired
- [ ] CORS is properly configured on backend
- [ ] Rate limiting is enabled on backend

---

## 🚀 CI/CD PIPELINE INTEGRATION

### GitHub Actions Example

```yaml
name: Deploy Frontend to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Create .env.production
        run: |
          cat > .env.production << EOF
          VITE_API_GATEWAY_URL=${{ secrets.VITE_API_GATEWAY_URL }}
          VITE_API_KEY=${{ secrets.VITE_API_KEY }}
          VITE_MAXIMUS_CORE_URL=${{ secrets.VITE_MAXIMUS_CORE_URL }}
          VITE_MAXIMUS_WS_URL=${{ secrets.VITE_MAXIMUS_WS_URL }}
          VITE_DEFENSIVE_WS_URL=${{ secrets.VITE_DEFENSIVE_WS_URL }}
          VITE_SUPER_ADMIN_EMAIL=${{ secrets.VITE_SUPER_ADMIN_EMAIL }}
          VITE_USE_MOCK_AUTH=false
          VITE_ENV=production
          EOF

      - name: Build
        run: |
          npm ci
          npm run build:prod

      - name: Deploy
        # Deploy dist/ to hosting
```

### GitLab CI Example

```yaml
deploy:production:
  stage: deploy
  only:
    - main
  script:
    - |
      cat > .env.production << EOF
      VITE_API_GATEWAY_URL=${VITE_API_GATEWAY_URL}
      VITE_API_KEY=${VITE_API_KEY}
      VITE_MAXIMUS_CORE_URL=${VITE_MAXIMUS_CORE_URL}
      VITE_MAXIMUS_WS_URL=${VITE_MAXIMUS_WS_URL}
      VITE_DEFENSIVE_WS_URL=${VITE_DEFENSIVE_WS_URL}
      VITE_SUPER_ADMIN_EMAIL=${VITE_SUPER_ADMIN_EMAIL}
      VITE_USE_MOCK_AUTH=false
      VITE_ENV=production
      EOF
    - npm ci
    - npm run build:prod
    - # Deploy dist/
```

### Docker Build Example

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .

# Environment variables injected at build time
ARG VITE_API_GATEWAY_URL
ARG VITE_API_KEY
ARG VITE_MAXIMUS_CORE_URL
ARG VITE_MAXIMUS_WS_URL
ARG VITE_DEFENSIVE_WS_URL
ARG VITE_SUPER_ADMIN_EMAIL

ENV VITE_API_GATEWAY_URL=${VITE_API_GATEWAY_URL}
ENV VITE_API_KEY=${VITE_API_KEY}
ENV VITE_MAXIMUS_CORE_URL=${VITE_MAXIMUS_CORE_URL}
ENV VITE_MAXIMUS_WS_URL=${VITE_MAXIMUS_WS_URL}
ENV VITE_DEFENSIVE_WS_URL=${VITE_DEFENSIVE_WS_URL}
ENV VITE_SUPER_ADMIN_EMAIL=${VITE_SUPER_ADMIN_EMAIL}
ENV VITE_USE_MOCK_AUTH=false
ENV VITE_ENV=production

RUN npm run build:prod

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

---

## 🧪 VALIDATION AFTER DEPLOYMENT

After deployment, verify in browser console:

```javascript
// Check API Gateway URL
console.log('API Gateway:', import.meta.env.VITE_API_GATEWAY_URL);

// Verify HTTPS
console.log('Uses HTTPS:', import.meta.env.VITE_API_GATEWAY_URL.startsWith('https://'));

// Verify Mock Auth is disabled
console.log('Mock Auth Disabled:', import.meta.env.VITE_USE_MOCK_AUTH === 'false');

// Check environment
console.log('Environment:', import.meta.env.VITE_ENV);
```

**Expected output:**
```
API Gateway: https://api.vertice.yourdomain.com
Uses HTTPS: true
Mock Auth Disabled: true
Environment: production
```

---

## ❌ COMMON MISTAKES TO AVOID

1. **Using HTTP instead of HTTPS**
   - ❌ `VITE_API_GATEWAY_URL=http://api.domain.com`
   - ✅ `VITE_API_GATEWAY_URL=https://api.domain.com`

2. **Using WS instead of WSS**
   - ❌ `VITE_MAXIMUS_WS_URL=ws://api.domain.com/ws/stream`
   - ✅ `VITE_MAXIMUS_WS_URL=wss://api.domain.com/ws/stream`

3. **Hardcoding IP addresses**
   - ❌ `VITE_API_GATEWAY_URL=https://34.148.161.131:8000`
   - ✅ `VITE_API_GATEWAY_URL=https://api.vertice.yourdomain.com`

4. **Committing secrets to git**
   - ❌ Real API keys in `.env.production`
   - ✅ Placeholders in `.env.production`, real values in CI/CD secrets

5. **Enabling mock auth in production**
   - ❌ `VITE_USE_MOCK_AUTH=true`
   - ✅ `VITE_USE_MOCK_AUTH=false`

---

## 📞 TROUBLESHOOTING

### Issue: "Configuration Error - Missing required environment variables"

**Solution:** Ensure all REQUIRED variables are set in CI/CD secrets and properly injected.

### Issue: WebSocket connections failing with SSL errors

**Solution:**
- Verify WSS protocol is used (not WS)
- Check SSL certificate is valid
- Ensure WebSocket endpoint supports WSS

### Issue: CORS errors on API calls

**Solution:**
- Verify backend CORS configuration allows production domain
- Check API Gateway CORS headers
- Ensure credentials are included in requests

### Issue: "Super admin email not configured"

**Solution:**
- Set `VITE_SUPER_ADMIN_EMAIL` in CI/CD secrets
- Verify email matches expected super admin account

---

## ✅ PRE-DEPLOYMENT CHECKLIST

Before each production deployment:

- [ ] All REQUIRED variables configured in CI/CD
- [ ] All URLs use HTTPS/WSS protocols
- [ ] No hardcoded secrets in repository
- [ ] Mock auth is disabled
- [ ] SSL certificates are valid
- [ ] Backend services are healthy
- [ ] API Gateway is accessible
- [ ] WebSocket endpoints are reachable
- [ ] Database migrations are complete
- [ ] Monitoring and logging are configured
- [ ] Rollback plan is prepared

---

**Document Version:** 1.0
**Maintained by:** DevOps Team
**Review Frequency:** Every major deployment or quarterly
