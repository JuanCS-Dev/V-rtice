# Usar uma imagem base oficial do Python
FROM python:3.11-slim

# Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar o arquivo de dependências e instalá-las
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto do código da aplicação
COPY . .

# Comando para rodar a aplicação com Uvicorn
# A porta 8001 aqui corresponde ao que o docker-compose espera
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
