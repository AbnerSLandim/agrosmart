
# Imagem base do Python
FROM python:3.12-slim

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Evita arquivos .pyc e mantém os logs no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copia o arquivo de dependências
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia os arquivos do projeto
COPY . .

# Executa o processamento e depois a automação
CMD ["sh", "-c", "python processando_dados.py && python automacao_dados.py"]
