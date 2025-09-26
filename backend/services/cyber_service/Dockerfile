# /home/juan/vertice-dev/backend/services/cyber_service/Dockerfile

FROM python:3.11-slim

# Instalar ferramentas de sistema necessárias para verificações de segurança
RUN apt-get update && apt-get install -y \
    nmap \
    net-tools \
    procps \
    findutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Comando para rodar o serviço
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
