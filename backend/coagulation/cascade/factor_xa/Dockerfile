# Multi-stage build for Factor Xa Service
# Bio-inspired quarantine activator

# Stage 1: Builder
FROM golang:1.21-alpine AS builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Copy go module files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the service
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags="-w -s" \
    -o /app/factor-xa \
    ./cascade/factor_xa/main.go

# Stage 2: Runtime
FROM alpine:3.19

WORKDIR /app

# Install runtime dependencies
RUN apk add --no-cache ca-certificates tzdata

# Copy binary from builder
COPY --from=builder /app/factor-xa /app/factor-xa

# Create non-root user
RUN addgroup -g 1000 coagulation && \
    adduser -D -u 1000 -G coagulation coagulation && \
    chown -R coagulation:coagulation /app

USER coagulation

# Expose service port
EXPOSE 8050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=20s \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8050/health || exit 1

ENTRYPOINT ["/app/factor-xa"]
