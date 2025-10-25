# Tegumentar Service Dockerfile - requires privileged host for XDP

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        clang \
        llvm \
        libbpf-dev \
        libelf-dev \
        gcc \
        make \
        iproute2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["python", "main.py"]
