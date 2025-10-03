# RTE Service Dockerfile
# Includes Intel Hyperscan library compiled from source

FROM python:3.11-slim AS builder

# Install build dependencies for Hyperscan
RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    git \
    libboost-dev \
    libpcap-dev \
    ragel \
    pkg-config \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Build Intel Hyperscan from source
WORKDIR /tmp
RUN git clone --depth 1 --branch v5.4.2 https://github.com/intel/hyperscan.git && \
    cd hyperscan && \
    mkdir build && \
    cd build && \
    cmake \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DBUILD_SHARED_LIBS=ON \
        .. && \
    make -j$(nproc) && \
    make install && \
    ldconfig

# Build Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --user -r /tmp/requirements.txt


# ============================================================================
# Production Image
# ============================================================================

FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libboost-system1.74.0 \
    libboost-filesystem1.74.0 \
    libpcap0.8 \
    iptables \
    iproute2 \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Hyperscan library from builder
COPY --from=builder /usr/local/lib/libhs* /usr/local/lib/
COPY --from=builder /usr/local/include/hs /usr/local/include/hs
RUN ldconfig

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Create application directory
WORKDIR /app

# Create directories for patterns, models, and quarantine
RUN mkdir -p /app/patterns /app/models /var/quarantine && \
    chmod 700 /var/quarantine

# Copy application code
COPY hyperscan_matcher.py /app/
COPY fast_ml.py /app/
COPY fusion_engine.py /app/
COPY playbooks.py /app/
COPY main.py /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    RTE_HOST=0.0.0.0 \
    RTE_PORT=8005

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:8005/health || exit 1

# Run service
CMD ["python", "main.py"]
