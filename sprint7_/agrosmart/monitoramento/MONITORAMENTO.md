# AgroSmart — Monitoramento e Execução Automatizada (Fase 7)

Responsável: Aldrin da Silva Rodrigues (RM551679)
Código: `monitoramento/executor.py` · Testes: `tests/test_monitoramento.py`

## 1. Objetivo

Mostrar que a plataforma não depende de alguém rodando scripts manualmente: um executor roda o pipeline completo (ingestão → processamento → automação → dashboard), repetidamente se necessário, **mede cada etapa, registra logs, calcula indicadores de funcionamento e avalia a saúde da execução**. Assim é possível saber, sem abrir o código, se a última rodada deu certo e se os dados estão dentro do esperado.

## 2. O que foi implementado

| Recurso | Como funciona | Arquivo gerado |
|---|---|---|
| Execução automatizada | Roda as 4 etapas em processos separados. Modos: 1 ciclo, `--ciclos N --intervalo S` ou `--continuo` (até Ctrl+C). | — |
| Logs da aplicação | Um log legível (UTC, níveis INFO/WARNING/ERROR) com rotação (3 arquivos de 500 KB). | `monitoramento/logs/agrosmart.log` |
| Eventos estruturados | Um JSON por etapa e por ciclo, para consumo por scripts/ferramentas. | `monitoramento/logs/eventos.jsonl` |
| Status de execução | Estado do último ciclo: etapas, duração, verificações e indicadores. | `monitoramento/status.json` |
| Histórico | Uma linha por ciclo (acumulativo). | `monitoramento/historico_execucoes.csv` |
| Painel de status | HTML offline, sem JavaScript, com situação, indicadores, etapas, verificações e últimas execuções. | `monitoramento/status.html` |
| Proteção contra execução simultânea | Arquivo de trava; um segundo ciclo disparado enquanto o primeiro roda é recusado (trava com mais de 10 min é tratada como abandonada). | `monitoramento/.execucao.lock` (temporário) |
| Código de saída | `0` saudável; `1` se alguma etapa falhou ou há verificação em ALERTA — permite integrar com agendadores e pipeline de CI. | — |

## 3. Indicadores de funcionamento

Calculados a partir das saídas reais do pipeline a cada ciclo:

- leituras brutas, válidas e descartadas; taxa e motivos de descarte;
- leituras de campo e de bancada (TinkerCad);
- distribuição de risco (alto/moderado/normal/sem dados), no campo e no total;
- alertas em campo (quantidade e %), ações automáticas propostas;
- sensores ativos e leituras de sensores com falha;
- duração por etapa e total; última leitura de campo e sua idade.

Resultado nas execuções de evidência: 397 leituras brutas, 394 válidas, 3 descartes (0,76%), 84/360 leituras de campo em alerta (38 altas + 46 moderadas, 23,33%), duração do pipeline ≈ 1,1 s.

## 4. Verificações de saúde

| Verificação | ALERTA quando… | Valor-limite |
|---|---|---|
| Etapas do pipeline | alguma etapa termina com erro | — |
| Arquivos de saída atualizados | algum CSV/HTML esperado não existe ou não foi regravado no ciclo | — |
| Taxa de descarte | acima do limite (sinal de problema na coleta) | 5% |
| Leituras sem dados | acima do limite (sensores sem medição) | 5% |
| Leituras de campo em alerta | acima do limite (muitos alertas simultâneos pedem atenção humana) | 30% |
| Duração do pipeline | acima do limite (lentidão com o volume atual) | 60 s |
| Atualidade dos dados | **apenas informativa** (INFO) | — |

Os limites são operacionais e ajustáveis nas constantes `LIMITE_*` do executor; foram escolhidos de forma didática, não calibrados com dados reais. A atualidade é só informativa porque a base de campo é sintética e histórica (termina em 02/09/2026); em produção seria uma verificação de ALERTA.

Se uma etapa falha, o executor interrompe o pipeline e **não calcula indicadores**, para não apresentar como atuais arquivos de uma execução anterior.

## 5. Como executar

Na pasta `agrosmart`:

```bash
python monitoramento/executor.py                              # 1 ciclo
python monitoramento/executor.py --ciclos 3 --intervalo 5     # 3 ciclos, 5 s entre eles
python monitoramento/executor.py --continuo --intervalo 900   # a cada 15 min, até Ctrl+C
python monitoramento/executor.py --status                     # resume o último estado
```

**Execução agendada (sem modo contínuo).** O executor roda um ciclo e termina, então pode ser disparado por qualquer agendador. Exemplos (não executados nesta entrega):

```
# Linux (crontab): a cada 15 minutos
*/15 * * * * cd /caminho/agrosmart && python monitoramento/executor.py >> /dev/null 2>&1

# Windows (Agendador de Tarefas)
schtasks /create /sc minute /mo 15 /tn "AgroSmart" /tr "python C:\caminho\agrosmart\monitoramento\executor.py"
```

## 6. Como acompanhar o sistema

1. **Situação rápida:** `python monitoramento/executor.py --status` (mostra SAUDÁVEL/ATENÇÃO, etapas e verificações).
2. **Painel visual:** abrir `monitoramento/status.html` no navegador (reflete o último ciclo; reabrir/recarregar após nova execução).
3. **Log em tempo real:** `tail -f monitoramento/logs/agrosmart.log` (Linux/macOS) ou `Get-Content monitoramento\logs\agrosmart.log -Wait` (PowerShell). Filtrar problemas: procurar `WARNING` e `ERROR`.
4. **Análise do histórico:** `historico_execucoes.csv` (duração, leituras e alertas por ciclo) e `eventos.jsonl` (cada etapa com duração e código de retorno).

Exemplo de evento (`eventos.jsonl`):

```json
{"momento": "2026-11-24T19:33:39Z", "evento": "etapa", "ciclo": 3, "etapa": "Processamento", "duracao_s": 0.35, "codigo": 0, "status": "OK"}
```

## 7. Evidências (pasta `monitoramento/evidencias/`)

| Arquivo | Conteúdo |
|---|---|
| `log_execucao_3_ciclos.log` | log real de 3 ciclos consecutivos, todos SAUDÁVEIS |
| `eventos_3_ciclos.jsonl` | eventos estruturados desses ciclos |
| `status_ultimo_ciclo.json` · `historico_execucoes.csv` | estado e histórico gerados |
| `print_painel_status_saudavel.png` | painel de status após os 3 ciclos |
| `print_terminal_windows_3_ciclos_inicio.png` · `print_terminal_windows_3_ciclos_fim.png` | **execução na máquina do autor (Windows, Prompt de Comando)** com `python monitoramento/executor.py --ciclos 3 --intervalo 2`: 3 ciclos com as 4 etapas, verificações em OK e `SAUDÁVEL` ao final |
| `log_falha_simulada.txt` · `status_falha_simulada.json` · `print_painel_status_falha_simulada.png` | **falha provocada de propósito** (coluna `umidade_solo_pct` removida do CSV bruto, em cópia descartável do projeto): o executor detectou o erro, interrompeu o pipeline, emitiu ALERTA e retornou código 1 |

Os prints do painel HTML foram capturados com Chromium; os prints de terminal são da máquina do autor. Os horários dos logs estão em UTC.

## 8. Testes

`tests/test_monitoramento.py` (17 testes): verificações de saúde (cada limite, limite exato, etapa com falha, saída ausente/desatualizada, pipeline lento), execução de etapas (sucesso, erro com mensagem, script inexistente, evento JSONL), trava de execução, indicadores batendo com o pipeline (397/394/3/84) e painel HTML autônomo e escapado. Com os testes da Fase 6, a suíte completa tem 30 testes (`python -m unittest discover -s tests -v`).

## 9. Relação com as demais partes

O executor roda as etapas que existem em `pipeline.py` e lê as saídas do pipeline (colunas `talhao`, `nivel_risco`, `acao_automatica`, `status_sensor`, `motivo_descarte`). As demais partes da equipe (execução da plataforma, DevSecOps, análise de processo, pitch) usam ou documentam esse fluxo sem alterá-lo. Se alguém mudar nomes de colunas ou de arquivos de saída, o monitoramento não quebra em silêncio: acusa ALERTA na verificação correspondente.

## 10. Limitações

- É monitoramento de **lotes**: cada ciclo reprocessa os CSVs; não há leitura de sensores em fluxo (MQTT) nem processo residente com métricas em tempo real.
- Alertas ficam em log, JSON e painel; **não há envio** por e-mail, mensagem ou ferramenta externa (Prometheus, Grafana etc.). Nenhum comando de atuador é executado.
- O painel é um arquivo estático; precisa de novo ciclo e recarga para atualizar.
- Dados de campo sintéticos; os limites de saúde são didáticos.
- Evoluções naturais: verificação de atualidade dos dados em produção, notificação de falhas, exportar métricas para uma ferramenta de observabilidade e rodar o executor de forma recorrente (ex.: `--continuo` em container). O `Dockerfile` e o CI do item 3 já executam um ciclo do executor, e o código de saída 1 faz o job falhar quando há ALERTA.
