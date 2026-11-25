# Dashboard analítico — descrição dos indicadores

O painel é gerado por `dashboard/gerar_dashboard.py` a partir de `dados/processados/`. Arquivo: `agrosmart_dashboard.html`, com HTML + SVG nativo, sem JavaScript, bibliotecas externas ou conexão à internet. Atualiza ao rodar o pipeline e reabrir o arquivo. Capturas da versão anterior em `prints/`, com procedência em `prints/LEIA_ME.md`. Os dados são sintéticos (campo) e simulados (bancada).

## 1. Visão geral
| Indicador | Como é calculado |
|---|---|
| Leituras de campo | Leituras válidas dos 4 talhões, depois da limpeza |
| Talhões monitorados | Quantidade de talhões de campo com leitura |
| Umidade média do solo | Média de `umidade_solo_pct` no período |
| Temperatura média do solo | Média de `temperatura_solo_c` no período |
| Alertas de risco alto / moderado | Leituras classificadas pelo motor de regras como Alto / Moderado |
| Leituras com alerta | (alto + moderado) ÷ total de leituras de campo |
| Leituras do TinkerCad (bancada) | Leituras vindas da simulação do nó de sensores |

## 2. Monitoramento ambiental
- **Umidade do solo por talhão:** média diária de cada talhão, com as linhas de 18% (nível crítico) e 22% (gatilho de irrigação). Mostra o Talhão 03, que não tem irrigação, se afastando dos outros na seca.
- **Temperatura do solo por talhão:** média diária, com linhas de atenção em 30 °C e risco alto em 35 °C.

## 3. Alertas e recomendações
- **Leituras por nível de risco e talhão:** barras empilhadas Normal / Moderado / Alto, incluindo a bancada do TinkerCad.
- **Resumo por talhão:** irrigado ou não, umidade média e mínima, número de alertas de risco alto e maior sequência de leituras abaixo do nível crítico.
- **Últimos alertas de risco alto:** data, talhão, leituras, tipo de alerta (solo seco ou calor), ação automática (acionar irrigação ou notificar produtor) e recomendação.

## 4. Insights automáticos
Textos escritos pela automação a partir dos dados de campo: talhão mais crítico, comparação entre talhões, tendência da umidade, volume de alertas e recomendação principal. A comparação é descritiva, não demonstra causalidade. Médias ignoram valores ausentes. Percentual com alerta é arredondado para inteiro (84/360 = 23,33%, exibido como 23%).

Horários exibidos em UTC. "Irrigado" é inferido de volume aplicado positivo no período inteiro; sequência crítica conta leituras consecutivas (campo: uma por dia; bancada: observações ordenadas com horário sintético). "Ação automática" é uma proposta escrita em CSV, não um comando de bomba ou envio de mensagem. O gráfico de riscos e o resumo incluem bancada; os KPIs, séries temporais, últimos alertas e insights usam somente campo.
