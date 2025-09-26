# backend/api_gateway/Dockerfile

# Usar uma imagem base oficial do Python
FROM python:3.11-slim

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar o arquivo de dependências e instalá-las
# O Dockerfile precisa do requirements.txt para funcionar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto do código da aplicação
COPY . .

# Comando para rodar a aplicação com Uvicorn na porta 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
