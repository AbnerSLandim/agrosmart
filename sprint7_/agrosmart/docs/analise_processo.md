# AgroSmart — Análise de processo e demonstração final (item 5, Fase 7)

## 1. Como o trabalho foi organizado

O projeto evoluiu em camadas, e cada fase manteve o que a anterior entregou.

| Camada | O que existe | Origem |
|---|---|---|
| Processamento e automação | `src/processamento.py`, `src/automacao.py` | Base de Joy, adaptada e integrada por Aldrin (limiares 18/22%, validação física, rastreabilidade, testes) |
| Dashboard Power BI inicial | `dashboard/powerbi_versao_inicial/` | Zerlin, preservado como histórico (outro dataset) |
| Arquitetura, TinkerCad, pipeline e dashboard HTML + SVG | `docs/`, `sensores/`, `pipeline.py`, `dashboard/` | Aldrin (Fase 6) |
| Execução e monitoramento | `monitoramento/executor.py` e `tests/test_monitoramento.py` | Fase 7 |
| CI/CD DevSecOps | `.github/workflows/ci.yml`, `Dockerfile`, `ruff.toml` | Fase 7, adaptado de um repositório anterior da equipe de estrutura plana |

A regra que guiou a Fase 7 foi **não alterar o fluxo de dados da Fase 6**. O monitoramento chama os mesmos quatro scripts do `pipeline.py`, em processos separados, e lê as saídas deles. Conferido em dois pontos: os cinco CSVs de `dados/processados/` e o dashboard HTML gerados na Fase 7 são idênticos aos entregues na Fase 6 (comparação byte a byte, desconsiderando só a quebra de linha).

## 2. Evolução da solução

| Fase 6 | Fase 7 |
|---|---|
| `python pipeline.py` roda as etapas e imprime no terminal | O executor roda as mesmas etapas e registra log, eventos JSON, status, histórico e painel HTML |
| Sucesso significa "o script não quebrou" | Sucesso significa seis verificações de saúde em OK (etapas, saídas atualizadas, descarte, sem dados, alertas, duração) |
| Falha em uma etapa aparece como erro de Python | Falha interrompe o pipeline, aponta a etapa, não calcula indicadores sobre arquivos antigos e devolve código de saída 1 |
| CI com Ruff, Bandit, pipeline e testes | CI executa o executor monitorado, publica logs e status como artefato e roda o container Docker sem privilégios de administrador |
| 13 testes | 30 testes (17 novos do monitoramento) |

## 3. Problemas encontrados e como foram tratados

| Problema | Tratamento |
|---|---|
| O Ruff acusou três apontamentos em `dashboard/gerar_dashboard.py` (variável chamada `l` e duas `lambda`) | Corrigidos sem mudar o resultado: o HTML gerado ficou idêntico |
| O único achado do Bandit estava num teste que lê o SVG gerado pelo próprio projeto | `tests/` fica fora da varredura do Bandit (`-x ./.venv,./tests`) e o comentário `nosec` saiu do teste. A justificativa está em `docs/pipeline_devsecops.md` |
| `ruff` e `bandit` estavam em `requirements.txt` e engordariam a imagem Docker | Foram para `requirements-dev.txt`; a imagem instala só o pandas |
| O container rodava como administrador | O `Dockerfile` cria o usuário `agrosmart` e executa com ele |
| Um teste do empacotador dependia do vídeo MP4 da Fase 6 | O empacotador e o teste foram reescritos para os arquivos da Fase 7 |
| Dois ciclos disparados ao mesmo tempo poderiam gravar os mesmos arquivos | Arquivo de trava; um segundo ciclo é recusado, e trava com mais de 10 minutos é tratada como abandonada |
| Um pipeline falho poderia exibir indicadores de uma execução anterior como se fossem atuais | O executor não calcula indicadores quando uma etapa falha, e a verificação de saídas atualizadas acusa ALERTA |
| Documentação anterior da execução (item 2) trazia exemplos e um log que não correspondiam aos dados reais | Substituídos por linhas e saída reais da execução, em `docs/evidencias_execucao/` |

## 4. Resultados medidos

- Pipeline completo em cerca de 1,1 a 1,4 s por ciclo (4 etapas; Processamento, Automação e Dashboard respondem pela maior parte).
- 397 leituras brutas, 394 válidas, 3 descartes (0,76%), 84 de 360 leituras de campo em alerta (23,33%).
- 3 ciclos consecutivos SAUDÁVEIS registrados em `monitoramento/evidencias/` (log, eventos, status, histórico e prints do terminal Windows e do painel).
- Falha provocada de propósito (coluna `umidade_solo_pct` removida do CSV bruto, em cópia descartável): o executor detectou, interrompeu em Processamento, emitiu três ALERTAS e retornou código 1.
- Ruff sem apontamentos; Bandit sem achados médios ou altos em 1.402 linhas; 30 testes aprovados.

## 5. Limites e riscos

- Dados de campo sintéticos; bancada simulada; ações apenas propostas em CSV, sem atuador.
- Monitoramento em lote, sem leitura em fluxo, sem notificação externa e com painel estático.
- Limites de saúde (5%, 5%, 30%, 60 s) são didáticos, não calibrados com dados reais.
- A verificação de atualidade dos dados é só informativa porque a base termina em 02/09/2026. Em produção seria ALERTA.
- O CI não varre dependências nem imagem e não faz deploy.
- A execução do GitHub Actions e do Docker ainda precisa ser comprovada com prints (ver `ESTADO_ENTREGA.md`).

## 6. Aprendizados

1. Monitorar uma execução de lote exige definir o que é "saudável" antes de medir. Seis verificações objetivas deram uma resposta única (SAUDÁVEL ou ATENÇÃO) sem abrir o código.
2. Provocar a falha é parte da prova. Só o teste com a coluna removida mostrou que o monitoramento não falha em silêncio.
3. Evidência precisa ser reproduzível. Trocamos exemplos escritos à mão por saídas reais, que qualquer pessoa regenera com `python pipeline.py`.
4. Separar dependências de execução e de desenvolvimento mantém a imagem Docker enxuta e o CI explícito.
5. Documentar o que o sistema **não** faz (sem atuador, sem MQTT, sem notificação) evita promessas maiores que a entrega.

## 7. Roteiro da demonstração final ao vivo (cerca de 4 minutos)

Prepare um terminal na pasta `agrosmart` e o navegador com duas abas vazias.

| Tempo | Ação | O que mostrar e dizer |
|---|---|---|
| 0:00–0:30 | Abrir `docs/arquitetura.png` | Fluxo de sete faixas: fontes, ingestão, processamento, automação, visualização, execução monitorada e CI/CD. Dados sintéticos de 4 talhões mais bancada TinkerCad |
| 0:30–1:15 | `python pipeline.py` | Quatro etapas; 397 entradas, 394 válidas, 3 descartes auditáveis; 49 altos e 56 moderados no total |
| 1:15–2:00 | Abrir `dashboard/agrosmart_dashboard.html` | KPIs de campo (360 leituras, 38 altos, 46 moderados), Talhão 03 - Norte a 6,1% de umidade, ações propostas; funciona offline |
| 2:00–3:00 | `python monitoramento/executor.py --ciclos 3 --intervalo 2`, depois `--status` e abrir `monitoramento/status.html` | Seis verificações em OK, `SAUDÁVEL` nos três ciclos, histórico com três linhas |
| 3:00–3:30 | Em cópia descartável, remover a coluna `umidade_solo_pct` de `dados/brutos/leituras_sensores.csv` e rodar o executor | Erro em Processamento, pipeline interrompido, três ALERTAS, código de saída 1 (`echo %errorlevel%` no Windows) |
| 3:30–4:00 | Abrir `.github/workflows/ci.yml` e a aba *Actions* do repositório | Ruff, Bandit, executor, testes, `docker build` e `docker run`; workflow verde |

Antes de gravar, confirme que o workflow está verde na aba *Actions* e tenha pronta a saída de `docker build` e `docker run`. O pacote não traz esses dois prints.
