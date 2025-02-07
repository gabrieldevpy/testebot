FROM python:3.12-slim

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta onde o bot vai rodar
EXPOSE 8080

# Comando de inicialização
CMD ["python", "main.py"]
