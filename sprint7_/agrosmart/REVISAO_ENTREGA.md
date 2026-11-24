# Revisão técnica AgroSmart — Fase 7 — 24/11/2026

Revisão feita em cópia de trabalho do pacote, com Python 3.12.3. Nenhum entregável foi enviado ao grupo e nenhuma submissão foi realizada. O enunciado e o prazo da Fase 7 não foram conferidos no portal nesta revisão.

## Matriz requisito × evidência

| Item | Evidência presente no ZIP técnico | Verificação e estado |
|---|---|---|
| 1. Arquitetura final | `docs/arquitetura.md`, `arquitetura.svg`, `arquitetura.png` | Diagrama com sete faixas, incluindo execução monitorada e CI/CD; SVG parseado e PNG renderizado e inspecionado. Clima e produtividade continuam fora das regras, e MQTT é só exemplo, ambos declarados. Pronto. |
| 2. Execução da plataforma | `docs/execucao_plataforma.md`, `docs/evidencias_execucao/` (log, exemplos de entrada e saída), `pipeline.py`, `dados/processados/` | `python pipeline.py` executado em cópia limpa: 397 entradas, 394 válidas, 3 descartes; Normal 289, Moderado 56, Alto 49. Exemplos são linhas reais dos CSVs. Pronto. |
| 3. Pipeline DevSecOps | `.github/workflows/ci.yml`, `Dockerfile`, `.dockerignore`, `ruff.toml`, `requirements*.txt`, `docs/pipeline_devsecops.md`, `docs/evidencias_execucao/simulacao_local_ci.txt` | Ruff sem apontamentos; Bandit sem achados médios ou altos em 1.402 linhas; executor SAUDÁVEL; 30 testes. **Pendente:** workflow verde no GitHub Actions e `docker build`/`docker run`, não executados aqui. |
| 4. Monitoramento e execução automatizada | `monitoramento/executor.py`, `MONITORAMENTO.md`, `TUTORIAL_como_testar.md`, `evidencias/`, `tests/test_monitoramento.py` | 17 testes aprovados. Ciclo executado também com `pandas 2.3.3` (versão do `requirements.txt`): SAUDÁVEL em cerca de 1,1 s. Evidências: 3 ciclos saudáveis, prints do terminal Windows e do painel, e falha provocada (coluna removida) com ALERTA e código 1. Pronto. |
| 5. Análise de processo e demonstração final | `docs/analise_processo.md` | Problemas, resultados medidos, aprendizados e roteiro de 4 minutos, todos ligados a fatos do pacote. Roteiro não ensaiado. Pronto como documento. |
| 6. Pitch | `PITCH.md` | Roteiro de 3 minutos, seis slides sugeridos e perguntas prováveis. Números conferidos nos CSVs e logs. Slides e gravação não produzidos. Pronto como roteiro. |
| Identidade e organização final | `entrega/montar_zip.py`, `ESTADO_ENTREGA.md`, `AUTOAVALIACAO.md` | Empacotador valida itens obrigatórios, prefixo e CRC; exclui Git, caches, trava de execução e ZIPs aninhados. Aprovação, composição do grupo, envio e submissão pendentes. |

## Execução e critérios verificados

```bash
python -m pip install -r requirements.txt
python pipeline.py
python monitoramento/executor.py
python -m unittest discover -s tests -v
python entrega/montar_zip.py
```

Resultado: 394 leituras válidas (360 campo + 34 bancada), 3 descartes. Campo: 38 altos e 46 moderados, 84/360 = 23,33%. Umidade média de campo 32,1%; Talhão 03 - Norte com mínimo de 6,1% e 18 leituras diárias críticas consecutivas. Insights e KPIs excluem a bancada; barras e resumo a identificam.

**30 testes executados e aprovados**: os 13 da Fase 6 (dados e descartes, colunas, datas, limites físicos, reprodução dos CSVs, regras de risco, concordância serial/Python, totais, SVG/HTML offline, escape de conteúdo, empacotador) e 17 do monitoramento (cada verificação de saúde e seu limite exato, etapa com falha, saída ausente ou desatualizada, pipeline lento, evento JSONL, trava, indicadores contra o pipeline e painel HTML autônomo e escapado).

Na primeira execução da suíte nesta revisão, o teste do empacotador falhou por exigir os documentos finais ainda não escritos, e passou depois deles. Em outro ponto, o texto do README citava pandas 3.0.6, fora do intervalo do `requirements.txt` (`<3.0`); a validação foi refeita com pandas 2.3.3 e o texto corrigido.

## Correções feitas nesta consolidação

- Exemplos de entrada/saída e log de execução do item 2 não correspondiam aos dados reais (talhões, valores e datas). Foram substituídos por linhas e saída reais.
- O empacotador listava arquivos da Fase 6, dependia do vídeo MP4 e descartaria `.dockerignore`. Foi reescrito para a Fase 7, e o teste correspondente também.
- A cópia duplicada dos arquivos de configuração e o cache do Ruff saíram do pacote; os arquivos reais ficam na raiz.
- Documentação da Fase 6 movida para `docs/fase6/` sem alteração de conteúdo.

## Contribuições e preservação

Joy: base revisada no repositório `AbnerSLandim/agrosmart`, commit `0c6cbfe8a52a42c8a99b4428da243a0dbcac6665`; estrutura adaptada ao cenário local, com limiares próprios de 18/22% e 30/35 °C. Os parâmetros originais de Joy não foram mantidos nem revalidados nesta revisão. Zerlin: `dashboard/powerbi_versao_inicial/` preservado, com outro dataset, sem ser apresentado como painel final.

## Limitações e checklist restante

Dados de campo sintéticos, bancada simulada com horários sintéticos, ingestão manual, `talhao_irrigado` inferido do lote, regras e limites de saúde didáticos, ações só propostas em CSV, monitoramento em lote e painel estático. O CI cobre o código-fonte e não varre dependências nem imagem. As capturas do dashboard em `dashboard/prints/` são da versão anterior. Pendências em `ESTADO_ENTREGA.md`: print do Actions verde, saída do Docker, gravação do pitch e da demonstração, composição do grupo, voto da autoavaliação, aprovação, envio e submissão.
