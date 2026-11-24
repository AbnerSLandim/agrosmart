# Imagem base do Python
FROM python:3.12-slim

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Evita arquivos .pyc e mantém os logs no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala somente as dependências de execução (ruff/bandit ficam no CI)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o projeto e roda sem privilégios de administrador
COPY . .
RUN useradd --create-home agrosmart && chown -R agrosmart /app
USER agrosmart

# Executa o pipeline completo pelo executor monitorado (logs, indicadores e
# verificações de saúde). O código de saída é 1 se algo falhar.
CMD ["python", "monitoramento/executor.py"]
