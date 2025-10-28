# Vértice Frontend - Cloud Run Deployment Guide

## Overview

The Vértice frontend is now fully configured for deployment to **Google Cloud Run**. This guide covers local testing, CI/CD setup, and manual deployment options.

---

## Files Created

### Docker Infrastructure
- `Dockerfile` - Multi-stage build (Node.js build + Nginx serve)
- `nginx.conf` - Nginx configuration optimized for Cloud Run
- `docker-entrypoint.sh` - Entrypoint script for environment variable substitution
- `.dockerignore` - Optimized build context

### CI/CD & Deployment
- `cloudbuild.yaml` - Google Cloud Build configuration for automated deployments
- `deploy.sh` - Manual deployment script (supports dev/staging/production)
- `.env.production` - Production environment variables template

### Configuration Files (Already Existed)
- `firebase.json` - Firebase Hosting config (optional, if you still want Firebase)
- `.firebaserc` - Firebase project configuration

---

## Quick Start - Local Testing

### 1. Build Docker Image
```bash
cd frontend
docker build -t vertice-frontend:latest .
```

### 2. Run Locally
```bash
docker run -d \
  -p 8080:8080 \
  -e PORT=8080 \
  --name vertice-frontend \
  vertice-frontend:latest
```

### 3. Test
```bash
# Health check
curl http://localhost:8080/health

# Frontend
curl http://localhost:8080/

# Or open in browser
open http://localhost:8080
```

### 4. Stop & Clean Up
```bash
docker stop vertice-frontend
docker rm vertice-frontend
```

---

## Deployment Options

### Option 1: Manual Deployment (Recommended for first deploy)

The `deploy.sh` script handles build, push, and deployment to Cloud Run.

#### Prerequisites
```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set project
gcloud config set project vertice-cybersecurity

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### Deploy to Development
```bash
cd frontend
./deploy.sh dev
```

#### Deploy to Staging
```bash
./deploy.sh staging
```

#### Deploy to Production
```bash
./deploy.sh production
```

#### Environment Variables
The deploy script uses these environment variables (customize before deploying):
- `VITE_API_GATEWAY_URL` - Backend API Gateway URL
- `VITE_MAXIMUS_CORE_URL` - MAXIMUS Core service URL
- And more... (see deploy.sh for full list)

Set them before running:
```bash
export VITE_API_GATEWAY_URL=https://api.vertice.example.com
export VITE_MAXIMUS_CORE_URL=https://maximus-core.vertice.example.com
./deploy.sh production
```

---

### Option 2: Google Cloud Build (CI/CD)

Automated deployment via Cloud Build trigger on git push.

#### Setup
```bash
# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# Connect GitHub repository
gcloud builds triggers create github \
  --name="vertice-frontend-deploy" \
  --repo-name="vertice-dev" \
  --repo-owner="YOUR_GITHUB_USERNAME" \
  --branch-pattern="^main$" \
  --build-config="frontend/cloudbuild.yaml"
```

#### Configure Substitutions
In Google Cloud Console > Cloud Build > Triggers > Edit Trigger:
- `_REGION`: us-central1 (or your preferred region)
- `_API_GATEWAY_URL`: https://api.your-domain.com
- `_MAXIMUS_CORE_URL`: https://maximus-core.your-domain.com
- etc. (see cloudbuild.yaml for full list)

#### Manual Trigger
```bash
cd frontend
gcloud builds submit --config=cloudbuild.yaml
```

---

### Option 3: Firebase Hosting (Alternative)

If you prefer Firebase Hosting instead of Cloud Run:

```bash
cd frontend

# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Deploy
npm run firebase:deploy

# Or deploy to preview channel
npm run firebase:deploy:preview
```

---

## Architecture

### Multi-Stage Docker Build

**Stage 1: Builder (Node.js 20 Alpine)**
- Copies package.json and package-lock.json
- Runs `npm ci` for reproducible builds
- Builds production assets with `npm run build`
- Output: `/app/dist` directory

**Stage 2: Production (Nginx 1.25 Alpine)**
- Minimal image size (~50MB)
- Copies built assets from Stage 1
- Configures Nginx with environment variable substitution
- Health check endpoint at `/health`
- Serves on port 8080 (Cloud Run standard)

### Nginx Configuration

- **SPA Routing**: All routes serve `index.html`
- **Compression**: Gzip enabled for text/js/css
- **Security Headers**: X-Frame-Options, CSP, etc.
- **Caching**:
  - Static assets (JS/CSS/images): 1 year cache
  - index.html: No cache (always fresh)
- **Health Check**: `/health` endpoint for Cloud Run

---

## Environment Variables

### Development (.env)
Used for `npm run dev`:
```bash
VITE_API_GATEWAY_URL=http://localhost:8000
VITE_MAXIMUS_CORE_URL=http://localhost:8151
# ... (real backend ports from docker-compose.yml)
```

### Production (.env.production)
Template for production deployment - **REPLACE ALL PLACEHOLDERS**:
```bash
VITE_API_GATEWAY_URL=https://api.vertice.example.com
VITE_MAXIMUS_CORE_URL=https://maximus-core.vertice.example.com
VITE_GOOGLE_CLIENT_ID=your-production-google-client-id.apps.googleusercontent.com
# ... (all production URLs)
```

---

## Cloud Run Configuration

### Service Settings
- **Memory**: 512Mi (sufficient for static site)
- **CPU**: 1
- **Min Instances**:
  - Production: 1 (always warm)
  - Staging: 0 (scale to zero)
  - Dev: 0 (scale to zero)
- **Max Instances**:
  - Production: 10
  - Staging: 5
  - Dev: 3
- **Port**: 8080
- **Authentication**: Allow unauthenticated (public frontend)

### Custom Domain (Optional)
```bash
gcloud run services update vertice-frontend-production \
  --region=us-central1 \
  --add-cloudsql-instances=INSTANCE_CONNECTION_NAME
```

---

## Troubleshooting

### Build Fails: "npm ci requires package-lock.json"
Ensure package-lock.json is NOT in .dockerignore:
```bash
# ✅ CORRECT (.dockerignore)
# package-lock.json - INCLUDE for reproducible builds

# ❌ WRONG
package-lock.json
```

### Container Won't Start
Check logs:
```bash
# Local
docker logs vertice-frontend

# Cloud Run
gcloud run logs tail vertice-frontend-production --region=us-central1
```

### Health Check Failing
Test health endpoint:
```bash
curl http://localhost:8080/health
# Should return: "healthy"
```

### Environment Variables Not Working
Verify they're set in Cloud Run:
```bash
gcloud run services describe vertice-frontend-production \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

---

## Performance Optimization

### Build Size
Current build creates ~673KB main bundle (MaximusDashboard).

Consider code splitting:
```javascript
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'maximus': ['./src/components/dashboards/MaximusDashboard'],
          'defensive': ['./src/components/dashboards/DefensiveDashboard'],
          'vendor': ['react', 'react-dom', 'react-router-dom']
        }
      }
    }
  }
}
```

### Image Size
Current image: ~150MB (optimized with multi-stage build)

Further optimization:
- Use `nginx:alpine` base (already doing this)
- Minimize dependencies in package.json
- Use `.dockerignore` to exclude unnecessary files (already configured)

---

## Security Best Practices

### 1. Environment Variables
- **NEVER** commit real API keys to git
- Use Cloud Run environment variables or Secret Manager
- Rotate credentials regularly

### 2. Content Security Policy
Frontend includes strict CSP headers in index.html - update for production domains.

### 3. HTTPS
Cloud Run automatically provides HTTPS - use it exclusively in production.

### 4. Authentication
Currently configured for Google OAuth - ensure client IDs are environment-specific.

---

## Next Steps

1. **Update .env.production** with real URLs
2. **Deploy backend services** to Cloud Run first
3. **Test deployment** to dev environment
4. **Configure custom domain** (optional)
5. **Set up monitoring** (Cloud Monitoring, Prometheus)
6. **Configure CI/CD** for automated deployments

---

## Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vite Build Optimization](https://vitejs.dev/guide/build.html)
- [Nginx Docker Best Practices](https://docs.nginx.com/nginx/admin-guide/installing-nginx/installing-nginx-docker/)
- [Firebase Hosting Guide](https://firebase.google.com/docs/hosting)

---

## Support

For issues or questions:
1. Check Cloud Run logs: `gcloud run logs tail SERVICE_NAME`
2. Test locally with Docker first
3. Verify environment variables are set correctly
4. Review nginx logs inside container: `docker exec -it CONTAINER_NAME cat /var/log/nginx/error.log`
