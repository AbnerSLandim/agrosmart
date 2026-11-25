# AgroSmart — Execução da plataforma (item 2, Fase 7)

Escopo: Fazenda Pedralva, soja (ciclo 2026/2027), 4 talhões de campo mais uma bancada TinkerCad. Todos os números abaixo vêm de uma execução real do pacote final; a saída completa está em `docs/evidencias_execucao/log_pipeline.txt`.

## Como o sistema funciona

Um comando, `python pipeline.py`, executa quatro etapas em sequência. Para a execução com logs, indicadores e verificações de saúde, use `python monitoramento/executor.py` (item 4).

| Etapa | Script | O que faz | Resultado real |
|---|---|---|---|
| 1. Ingestão | `sensores/ingestao_tinkercad.py` | Converte a saída do Monitor Serial do TinkerCad para o formato das leituras de campo | 34 leituras de bancada convertidas, 1 linha ignorada |
| 2. Processamento | `src/processamento.py` | Remove duplicatas, descarta umidade fora de 0–100% e sensor sem medição, valida datas e identificação, classifica a umidade | 397 entradas (363 campo + 34 bancada): 394 válidas e 3 descartes (0,76%) |
| 3. Automação | `src/automacao.py` | Aplica as regras de risco e gera ação proposta, resumo por talhão e insights | Normal 289, Moderado 56, Alto 49 no total |
| 4. Dashboard | `dashboard/gerar_dashboard.py` | Gera o painel HTML + SVG offline a partir dos CSVs da automação | `dashboard/agrosmart_dashboard.html` |

Regras: risco alto com umidade abaixo de 18% ou temperatura a partir de 35 °C; moderado com umidade abaixo de 22% ou temperatura a partir de 30 °C. Em risco alto, a ação proposta é *Acionar irrigação* se o talhão foi irrigado no período e *Notificar produtor* caso contrário. As ações ficam registradas em CSV: nenhuma bomba é acionada e nenhuma mensagem é enviada.

Descartes registrados em `dados/processados/registros_descartados.csv`: uma duplicata (SM-PED-001), um valor fora do limite físico (SM-PED-001, 20/07/2026) e um sensor sem medição (SM-PED-003, 24/08/2026). Nenhum valor descartado é substituído ou interpolado.

## Resultado da execução

- Campo (360 leituras): 38 riscos altos e 46 moderados, 84/360 em alerta (23,33%). O Talhão 03 - Norte, sem irrigação, concentra os 38 altos, chegou a 6,1% de umidade e teve 18 leituras diárias seguidas abaixo de 18%.
- Bancada TinkerCad (34 leituras): 11 altos e 10 moderados, identificados à parte. Com a bancada, o total é 49 altos e 56 moderados.
- Os três talhões irrigados ficaram com umidade mínima entre 20,3% e 21,7%. É uma comparação descritiva de um cenário sintético, sem afirmação de causalidade.

## Exemplo de entrada e saída (linhas reais)

Entrada, `docs/evidencias_execucao/exemplo_entrada.csv`:

| sensor_id | data_hora | talhao | irrigado | umidade (%) | temperatura (°C) | status |
|---|---|---|---|---|---|---|
| SM-PED-003 | 2026-07-23 09:00 UTC | Talhao 03 - Norte | não | 6,1 | 22,0 | operacional |
| SM-PED-002 | 2026-07-14 09:00 UTC | Talhao 02 - Leste | sim | 21,0 | 26,0 | operacional |
| SM-PED-001 | 2026-06-05 09:00 UTC | Talhao 01 - Sul | sim | 36,9 | 22,1 | operacional |

Saída da automação, `docs/evidencias_execucao/exemplo_saida.csv`:

| talhão | risco | tipo de alerta | ação proposta |
|---|---|---|---|
| Talhao 03 - Norte | Alto | Solo seco | Notificar produtor |
| Talhao 02 - Leste | Moderado | Solo seco | Monitoramento reforçado |
| Talhao 01 - Sul | Normal | Nenhum | Nenhuma ação necessária |

## Como reproduzir

```bash
python -m pip install -r requirements.txt
python pipeline.py
python -m unittest discover -s tests -v   # 30 testes
```

Abra `dashboard/agrosmart_dashboard.html` no navegador: arquivo único, sem internet nem JavaScript. Os CSVs de `dados/processados/` são regenerados a cada execução e, com os mesmos dados de entrada, saem idênticos.

## Limites

Dados de campo sintéticos; bancada simulada, com horários sintéticos só para ordenação; ingestão serial manual (o MQTT existe apenas como exemplo de payload); clima e produtividade ficam na camada bruta e não entram nas regras; `talhao_irrigado` é inferido de qualquer volume de irrigação no período, não de um cadastro físico.
