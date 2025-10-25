# ═══════════════════════════════════════════════════════════════════════════
# Vértice Frontend - Cloud Run Dockerfile
# ═══════════════════════════════════════════════════════════════════════════
# Multi-stage build for optimized production deployment
# Stage 1: Build the React/Vite application
# Stage 2: Serve with nginx (optimized for Cloud Run)

# ───────────────────────────────────────────────────────────────────────────
# STAGE 1: BUILD
# ───────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (production + dev for build)
RUN npm ci

# Copy source code
COPY . .

# Build for production (uses .env.production)
RUN npm run build

# ───────────────────────────────────────────────────────────────────────────
# STAGE 2: PRODUCTION
# ───────────────────────────────────────────────────────────────────────────
FROM nginx:1.25-alpine

# Install gettext for envsubst (environment variable substitution)
RUN apk add --no-cache gettext

# Copy custom nginx config
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy startup script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Cloud Run expects port 8080
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Use custom entrypoint for env var substitution
ENTRYPOINT ["/docker-entrypoint.sh"]

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
