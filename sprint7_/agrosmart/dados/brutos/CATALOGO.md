# Dataset base — catálogo

Cenário compartilhado pelos quatro itens da entrega. Gerado por `gerar_dataset.py`
(determinista: rodar de novo produz exatamente os mesmos arquivos).

**Fazenda Pedralva** · soja ciclo 2026/2027 · 4 talhões · 183,5 ha · 05/06/2026 a
02/09/2026.

| Talhão | Sensor | Área (ha) | Retenção do solo | Irrigação |
|---|---|---|---|---|
| Talhão 01 - Sul | SM-PED-001 | 42,0 | alta (1,00) | sim |
| Talhão 02 - Leste | SM-PED-002 | 38,5 | média (0,85) | sim |
| Talhão 03 - Norte | SM-PED-003 | 55,2 | baixa (0,70) | **não** |
| Talhão 04 - Oeste | SM-PED-004 | 47,8 | alta (0,95) | sim |

## Arquivos

**`leituras_sensores.csv`** — 363 linhas. Uma leitura diária por talhão, mais os três
registros defeituosos. Colunas: `sensor_id`, `data_hora` (ISO 8601, UTC), `fazenda`,
`talhao`, `cultura`, `umidade_solo_pct`, `temperatura_solo_c`, `condutividade_ds_m`,
`irrigacao_aplicada_mm`, `status_sensor`.

**`clima_estacao.csv`** — 90 linhas, uma por dia. Colunas: `data`, `estacao_id`,
`precipitacao_mm`, `temp_min_c`, `temp_max_c`, `umidade_ar_pct`, `vento_kmh`,
`radiacao_mj_m2`.

**`produtividade_talhoes.csv`** — 12 linhas (4 talhões × 3 safras). Colunas: `safra`,
`fazenda`, `talhao`, `area_ha`, `cultura`, `produtividade_kg_ha`, `producao_total_kg`,
`irrigacao`, `custo_producao_brl_ha`.

**`payload_sensor_mqtt.json`** — exemplo de payload cru, do jeito que chega do sensor
antes de virar linha de CSV: valor medido, coordenadas, metadados de fabricante,
firmware e última calibração.

## Defeitos injetados de propósito

A camada bruta precisa conter dado ruim, senão a camada de validação não tem o que fazer.
São três, e a validação do item 3 captura os três:

| Registro | Defeito | O que a validação faz |
|---|---|---|
| SM-PED-001 · 05/07 09:00 | duplicata (mesma leitura reenviada pelo gateway) | descarta a cópia |
| SM-PED-001 · 20/07 15:00 | umidade de 148,7% — fisicamente impossível | descarta por limite físico |
| SM-PED-003 · 24/08 21:00 | sensor em falha, sem valor medido | descarta e registra a lacuna |

Nenhum valor é interpolado no lugar dos descartes. Os motivos ficam em `dados/processados/registros_descartados.csv`.

## Como o cenário foi construído

Balanço hídrico simples por talhão: a água entra por chuva (proporcional à retenção do
solo) e por irrigação (disparada abaixo de 22% de umidade, só nos talhões irrigados), e
sai por evapotranspiração proporcional à água disponível e à temperatura máxima do dia.
A série atravessa o auge da estação seca, então a chance de chuva cai ao longo dos 90
dias.

O resultado é a assimetria que sustenta a análise da entrega: os três talhões irrigados
apresentam mínimos entre 20,3% e 21,7%, e o Talhão 03 — o único sem irrigação —
chega a 6,1%, com 18 leituras diárias seguidas abaixo do nível crítico de 18%.
São valores revalidados no dataset entregue, não estimativas do modelo.

**`serial_tinkercad.txt`** e **`leituras_tinkercad.csv`** — 34 observações da
simulação capturada em 03/10/2026. O CSV unificado atribui horários sintéticos
desde 02/09/2026 10h UTC em passos de 1 h; não usar esses horários como tempo real
de aquisição (o sketch usa 2 s). A bancada não entra nos KPIs de campo.

Os CSVs de campo, clima e produtividade são reproduzíveis pela semente fixa;
`gerado_em` do payload de exemplo também é um timestamp sintético fixo no gerador.
O payload é apenas documentação: não existe broker MQTT implementado nesta entrega.

**Os dados são sintéticos.** São coerentes entre si e plausíveis para o cenário, mas não
são medições reais de campo.
