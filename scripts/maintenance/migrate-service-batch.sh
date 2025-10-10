#!/bin/bash
# 🚀 Batch Service Migration Script - uv Edition
# Automatiza migração completa de Docker + CI/CD para uv
# Usage: ./migrate_service_batch.sh SERVICE_NAME SERVICE_PORT

set -e

SERVICE_NAME="${1}"
SERVICE_PORT="${2:-8000}"
SERVICE_DIR="/home/juan/vertice-dev/backend/services/${SERVICE_NAME}"

if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Usage: $0 SERVICE_NAME [SERVICE_PORT]"
    exit 1
fi

if [ ! -d "$SERVICE_DIR" ]; then
    echo "❌ Service not found: $SERVICE_DIR"
    exit 1
fi

echo "🚀 Migrating $SERVICE_NAME (port $SERVICE_PORT)..."
cd "$SERVICE_DIR"

# Backup existing files
echo "📦 Creating backups..."
[ -f Dockerfile ] && cp Dockerfile Dockerfile.old
[ -f .github/workflows/ci.yml ] && cp .github/workflows/ci.yml .github/workflows/ci.old.yml 2>/dev/null || true
[ -f .github/workflows/ci-cd.yaml ] && mv .github/workflows/ci-cd.yaml .github/workflows/ci-cd.old.yaml 2>/dev/null || true

# Create Dockerfile
echo "🐳 Creating Dockerfile..."
cat > Dockerfile << 'DOCKERFILE_EOF'
FROM vertice/python311-uv:latest AS builder
USER root
WORKDIR /build
COPY pyproject.toml requirements.txt ./
RUN python -m venv /opt/venv && . /opt/venv/bin/activate && uv pip sync requirements.txt

FROM python:3.11-slim
LABEL maintainer="Juan & Claude" version="2.0.0"
RUN apt-get update && apt-get install -y --no-install-recommends curl libpq5 ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN groupadd -r appuser && useradd -r -g appuser --uid 1000 appuser
WORKDIR /app
COPY --chown=appuser:appuser . .
USER appuser
HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:SERVICE_PORT_PLACEHOLDER/health || exit 1
EXPOSE SERVICE_PORT_PLACEHOLDER
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "SERVICE_PORT_PLACEHOLDER"]
DOCKERFILE_EOF

sed -i "s/SERVICE_PORT_PLACEHOLDER/${SERVICE_PORT}/g" Dockerfile

# Create .dockerignore
echo "🗑️  Creating .dockerignore..."
cat > .dockerignore << 'DOCKERIGNORE_EOF'
__pycache__/
*.py[cod]
.Python
venv/
.venv
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/
dist/
build/
*.egg-info/
.git/
.github/
.vscode/
.idea/
*.md
*.log
logs/
*.tmp
*.bak
*.old
.env
.env.*
!.env.example
Dockerfile.old
docker-compose*.yml
DOCKERIGNORE_EOF

# Create CI/CD workflow
echo "⚙️  Creating CI/CD workflow..."
mkdir -p .github/workflows
sed "s/my-service/${SERVICE_NAME}/g; s/SERVICE_PORT: 8000/SERVICE_PORT: ${SERVICE_PORT}/g" \
    /home/juan/vertice-dev/.github/workflows/templates/service-ci.yml > .github/workflows/ci.yml

echo "✅ Migration complete for $SERVICE_NAME!"
echo "   - Dockerfile: ✅"
echo "   - .dockerignore: ✅"
echo "   - CI/CD: ✅"
echo "   - Backups: ✅ (*.old files)"
