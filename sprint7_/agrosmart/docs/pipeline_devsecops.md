# AgroSmart — Pipeline DevSecOps (item 3, Fase 7)

Contribuição do integrante responsável pelo pipeline (repositório da equipe, commits em `.github/workflows/ci.yml` e `Dockerfile`), adaptada à estrutura final do projeto.

## Arquivos

Os arquivos ficam na raiz do projeto, que é onde o GitHub Actions (`.github/workflows/`) e o `docker build` (`Dockerfile`) os procuram.

| Arquivo | Função |
|---|---|
| `.github/workflows/ci.yml` | Pipeline automatizado no GitHub Actions (push/PR na `main`) |
| `Dockerfile` | Imagem do projeto (Python 3.12-slim) que executa o pipeline completo |
| `.dockerignore` | Deixa fora da imagem vídeo, logs, caches e arquivos de entrega |
| `requirements.txt` | Dependências de execução (pandas) |
| `requirements-dev.txt` | Execução + ferramentas de CI (Ruff e Bandit) |
| `ruff.toml` | Regras do Ruff fixadas (E4, E7, E9, F), para o resultado não mudar com a versão da ferramenta |

## O que o pipeline faz

**Job `quality-and-security`**
1. **Build / preparação:** checkout, Python 3.12 e instalação das dependências.
2. **Qualidade de código:** `ruff check .`
3. **Vulnerabilidades no código:** `bandit -r . -x ./.venv,./tests -ll` (reporta severidade média ou alta; `tests/` fica de fora porque o único achado ali é um teste que lê o SVG gerado pelo próprio projeto).
4. **Execução:** `python monitoramento/executor.py` roda o pipeline completo com logs e verificações de saúde; falha o job se algo estiver em ALERTA (código de saída 1).
5. **Testes:** `python -m unittest discover -s tests -v`
6. **Evidência:** publica logs e status do monitoramento como artefato do job.

**Job `docker-build`**
1. `docker build -t agrosmart:ci .`
2. `docker run --rm agrosmart:ci`: executa o pipeline dentro do container, com usuário sem privilégios de administrador. O container termina com o código de saída do executor.

## Execução local

```bash
pip install -r requirements-dev.txt
ruff check .
bandit -r . -x ./.venv,./tests -ll
python monitoramento/executor.py
python -m unittest discover -s tests -v

docker build -t agrosmart:ci .
docker run --rm agrosmart:ci
```

## Mudanças em relação ao repositório original do colega

- O repositório antigo tinha uma estrutura plana (`processando_dados.py`, `automacao_dados.py`). O CI e o Dockerfile foram apontados para `monitoramento/executor.py` (que roda `processamento`, `automação` e `dashboard`).
- `ruff` e `bandit` saíram do `requirements.txt` (para a imagem Docker não carregar ferramentas de CI) e foram para `requirements-dev.txt`.
- Acrescentados: execução dos testes, upload dos logs, usuário não-root no container, `.dockerignore` e `ruff.toml`.
- O código do projeto precisou de 3 correções para passar no Ruff (nome de variável `l` e duas `lambda` em `dashboard/gerar_dashboard.py`); o HTML gerado ficou idêntico. O teste do empacotador deixou de depender do vídeo MP4 da Fase 6: agora verifica os arquivos da Fase 7 (inclusive `.dockerignore` e `ci.yml`).

## Evidência

`docs/evidencias_execucao/simulacao_local_ci.txt` traz a execução local, em cópia limpa do pacote final, das mesmas etapas do job `quality-and-security`: Ruff sem apontamentos, Bandit sem achados de severidade média ou alta, executor com ciclo SAUDÁVEL e 30 testes aprovados. **Não é uma execução do GitHub Actions nem do Docker**: o ambiente de verificação não tinha Docker. Para fechar a evidência, falta anexar o print da aba *Actions* do repositório com o workflow verde e a saída de `docker build` e `docker run` (ver `ESTADO_ENTREGA.md`).

## Limitações

- Não há varredura de dependências (ex.: `pip-audit`) nem de imagem (ex.: Trivy); a análise de vulnerabilidades cobre o código-fonte (Bandit).
- O pipeline não faz deploy; termina na construção e execução do container.
- Os dados de campo são sintéticos.
