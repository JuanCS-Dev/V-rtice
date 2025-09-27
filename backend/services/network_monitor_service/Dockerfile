# backend/services/network_monitor_service/Dockerfile

FROM python:3.11-slim

# Instala dependências do sistema necessárias para ss (iproute2)
RUN apt-get update && \
    apt-get install -y iproute2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código da aplicação
COPY . .

# Expõe a porta do serviço
EXPOSE 8005

# Comando para iniciar o serviço
CMD ["python", "main.py"]
