# Usa uma imagem base oficial do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências para o diretório de trabalho
COPY requirements.txt .

# Instala as dependências
RUN pip install -r requirements.txt

# Copia o restante do código da sua aplicação para o diretório de trabalho
COPY . .

# Comando para rodar a aplicação quando o container iniciar
# Altere 'bot.py' se o nome do seu arquivo principal for diferente
CMD ["python", "bot.py"]