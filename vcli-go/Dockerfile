# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM golang:1.24-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git make

# Set working directory
WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build optimized binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -o vcli \
    -ldflags="-w -s" \
    -trimpath

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM alpine:3.19

# Install runtime dependencies
RUN apk add --no-cache \
    ca-certificates \
    tzdata \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 1001 vcli && \
    adduser -D -u 1001 -G vcli vcli

# Set working directory
WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/vcli /usr/local/bin/vcli

# Set ownership
RUN chown -R vcli:vcli /app

# Switch to non-root user
USER vcli

# Expose port (if needed for future HTTP endpoints)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD vcli version || exit 1

# Default command - HTTP server mode for Cloud Run
ENTRYPOINT ["sh", "-c"]
CMD ["while true; do nc -l -p 8080 -e vcli version; done"]
