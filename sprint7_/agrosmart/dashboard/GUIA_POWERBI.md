# Guia pra refazer o Power BI com os dados novos (Zerlin)

O `.pbix` em `powerbi_versao_inicial/` lia outro dataset: 21 leituras, com temperatura do ar e luminosidade. O dashboard agora precisa ler a **saída da automação**. É isso que fecha a integração sensor → Python → dashboard que o enunciado cobra.

O painel integrado entregue é `agrosmart_dashboard.html` (HTML + SVG offline, gerado por `gerar_dashboard.py`). O portal aceita ferramenta equivalente: PBIX atualizado é opcional. A versão inicial de Zerlin está preservada como contribuição histórica, sem representar os dados finais. Este guia serve caso a equipe escolha atualizar o Power BI; o HTML já cumpre o requisito técnico de dashboard.

## 1. Fontes (Obter dados → Texto/CSV), todas em `dados/processados/`

| Arquivo | Uma linha por | Colunas principais |
|---|---|---|
| `resultado_automacao_agrosmart.csv` | leitura | `data`, `hora`, `talhao`, `umidade_solo_pct`, `temperatura_solo_c`, `irrigacao_aplicada_mm`, `talhao_irrigado`, `nivel_risco` (Normal/Moderado/Alto), `tipo_alerta` (Solo seco/Calor), `alerta`, `recomendacao`, `acao_automatica` |
| `resumo_talhoes.csv` | talhão | `talhao`, `irrigado`, `umidade_media_pct`, `umidade_minima_pct`, `temperatura_maxima_c`, `alertas_alto`, `alertas_moderado`, `maior_sequencia_critica` |
| `insights_automaticos.csv` | insight | `indicador`, `texto` (textos gerados pela automação; **não** escrever à mão) |

Dicas:
- O arquivo é UTF-8. Se aparecer "Ã§" no lugar de "ç", troca a "Origem do arquivo" pra 65001: Unicode (UTF-8).
- `data` tem que ficar com o tipo **Data**.
- O "Talhao 05 - Bancada TinkerCad" é a simulação do Arduino. Nos indicadores da fazenda, filtra `talhao` **não contém** "TinkerCad". No gráfico de risco por talhão pode deixar aparecer.

## 2. Páginas (mesma ideia das suas 4)

**Visão geral (cartões)**, com o filtro sem TinkerCad:
- Leituras de campo = contagem de linhas → hoje dá **360**
- Umidade média do solo = média de `umidade_solo_pct` → **32,1%**
- Temperatura média do solo = média de `temperatura_solo_c` → **25 °C**
- Alertas de risco alto = contagem onde `nivel_risco` = "Alto" → **38**
- Alertas de risco moderado = contagem onde `nivel_risco` = "Moderado" → **46**

Se os seus números baterem com esses, a fonte está certa.

**Monitoramento:** gráfico de linhas com eixo `data`, valor média de `umidade_solo_pct` e legenda `talhao`. Faz outro igual pra `temperatura_solo_c`. Se der, coloca uma linha constante em 18 (crítico) e outra em 22 (irrigar).

**Alertas e recomendações:**
- Barras empilhadas: eixo `talhao`, contagem, legenda `nivel_risco`. Cores: verde Normal, amarelo Moderado, vermelho Alto.
- Tabela com `data`, `talhao`, `umidade_solo_pct`, `temperatura_solo_c`, `tipo_alerta`, `acao_automatica`, `recomendacao`, filtrada em `nivel_risco` = "Alto".
- Tabela do `resumo_talhoes.csv`.

**Insights:** tabela ou cartão de várias linhas com `indicador` e `texto` do `insights_automaticos.csv`. Isso substitui os textos escritos à mão, que não batiam com os dados.

## 3. Acabamento (o que o professor nota)
- Renomear todos os campos nos visuais em PT-BR. Nada de "Average of…" ou "Count of…" (botão direito no campo → Renomear para este visual).
- Nenhuma soma de temperatura ou umidade: usar **média**.
- Não repetir o mesmo cartão em várias páginas.
- Nome do arquivo: `dashboard.pbix`, salvo em `dashboard/`. Depois atualiza os prints em `dashboard/prints/` e o `descricao_indicadores.md`, se mudar algo.

Pra atualizar os dados depois de rodar `python pipeline.py`, é só clicar em **Atualizar** no Power BI.
