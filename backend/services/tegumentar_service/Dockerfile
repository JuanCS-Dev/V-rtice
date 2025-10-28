# Tegumentar Service Dockerfile - CO-RE eBPF with privileged XDP
# Stage 1: Build eBPF program with CO-RE
FROM python:3.11-slim AS bpf-builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        clang \
        llvm \
        libbpf-dev \
        libelf-dev \
        gcc \
        make \
        linux-headers-generic \
        bpftool \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy BPF source
COPY backend/modules/tegumentar/epiderme/reflex_arc.c /build/

# Compile BPF program with CO-RE (BTF relocations)
RUN clang -O2 -g -target bpf -D__TARGET_ARCH_x86_64 \
    -I/usr/include/x86_64-linux-gnu \
    -c reflex_arc.c -o reflex_arc.o

# Generate BPF skeleton for runtime loading (CO-RE)
RUN bpftool gen skeleton reflex_arc.o > reflex_arc.skel.h || \
    echo "// BPF skeleton generation skipped" > reflex_arc.skel.h

# Stage 2: Runtime image
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        iproute2 \
        nftables \
        libbpf1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for dependency management
RUN pip install --no-cache-dir uv

COPY backend/services/tegumentar_service/requirements.txt /app/requirements.txt
RUN uv pip install --system --no-cache -r requirements.txt

# Copy service code
COPY backend/services/tegumentar_service /app

# Copy required backend modules
COPY backend/modules/tegumentar /app/backend/modules/tegumentar

# Copy pre-compiled BPF objects from builder
COPY --from=bpf-builder /build/reflex_arc.o /app/backend/modules/tegumentar/epiderme/
COPY --from=bpf-builder /build/reflex_arc.skel.h /app/backend/modules/tegumentar/epiderme/

# Create __init__.py files for package structure
RUN touch /app/backend/__init__.py && touch /app/backend/modules/__init__.py

CMD ["python", "main.py"]
