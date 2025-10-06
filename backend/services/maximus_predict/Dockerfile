# Usar uma imagem base de Python moderna e leve
FROM python:3.11-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /code

# Copiar o ficheiro de dependências primeiro para aproveitar o cache do Docker
COPY ./requirements.txt /code/requirements.txt

# Instalar as dependências
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copiar o ficheiro principal da aplicação
COPY ./api.py /code/api.py

# Expor a porta que a aplicação vai usar
EXPOSE 8080

# Comando para iniciar a aplicação (caminho ajustado para 'api:app')
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
