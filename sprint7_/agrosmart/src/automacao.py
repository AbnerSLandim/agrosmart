"""
AgroSmart - Parte 4: automação inteligente baseada em regras.

Lê o dataset processado, aplica as regras de decisão (motor de regras),
classifica o risco de cada leitura, gera alerta, recomendação e ação
automática, e produz os arquivos consumidos pelo dashboard:

    dados/processados/resultado_automacao_agrosmart.csv  (uma linha por leitura)
    dados/processados/resumo_talhoes.csv                 (indicadores por talhão)
    dados/processados/insights_automaticos.csv           (textos gerados a partir dos dados)

Uso:
    python src/automacao.py
"""

import pandas as pd
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

arquivo_entrada = RAIZ / "dados/processados/dataset_processado_agrosmart.csv"
arquivo_saida = RAIZ / "dados/processados/resultado_automacao_agrosmart.csv"
arquivo_resumo = RAIZ / "dados/processados/resumo_talhoes.csv"
arquivo_insights = RAIZ / "dados/processados/insights_automaticos.csv"

# Limites das regras. Umidade segue o cenário da fazenda (CATALOGO.md):
# irrigação dispara abaixo de 22% e o nível crítico para a soja é 18%.
UMIDADE_CRITICA = 18.0
UMIDADE_BAIXA = 22.0
TEMPERATURA_ALTA = 35.0
TEMPERATURA_ATENCAO = 30.0


def classificar_risco(linha):
    umidade = linha["umidade_solo_pct"]
    temperatura = linha["temperatura_solo_c"]

    if pd.isna(umidade) and pd.isna(temperatura):
        return "Sem dados"

    # Risco alto: solo abaixo do nível crítico OU temperatura muito alta
    if (pd.notna(umidade) and umidade < UMIDADE_CRITICA) or (
        pd.notna(temperatura) and temperatura >= TEMPERATURA_ALTA
    ):
        return "Alto"

    # Risco moderado: solo abaixo do gatilho de irrigação OU temperatura elevada
    if (pd.notna(umidade) and umidade < UMIDADE_BAIXA) or (
        pd.notna(temperatura) and temperatura >= TEMPERATURA_ATENCAO
    ):
        return "Moderado"

    # Uma leitura parcial sem condição de alerta não garante normalidade.
    if pd.isna(umidade) or pd.isna(temperatura):
        return "Sem dados"

    return "Normal"


def tipo_alerta(linha):
    umidade = linha["umidade_solo_pct"]
    temperatura = linha["temperatura_solo_c"]
    tipos = []
    if pd.notna(umidade) and umidade < UMIDADE_BAIXA:
        tipos.append("Solo seco")
    if pd.notna(temperatura) and temperatura >= TEMPERATURA_ATENCAO:
        tipos.append("Calor")
    return " + ".join(tipos) if tipos else "Nenhum"


def gerar_recomendacao(linha):
    risco = linha["nivel_risco"]
    umidade = linha["umidade_solo_pct"]
    irrigado = linha["talhao_irrigado"]

    if risco == "Alto":
        if pd.notna(umidade) and umidade < UMIDADE_CRITICA:
            if irrigado:
                return "Irrigar imediatamente e verificar o sistema de irrigação"
            return "Talhão sem irrigação: avaliar irrigação emergencial ou cobertura do solo"
        return "Realizar inspeção do talhão (estresse térmico)"

    if risco == "Moderado":
        if pd.notna(umidade) and umidade < UMIDADE_BAIXA:
            if not irrigado:
                return "Talhão sem irrigação: avaliar disponibilidade de água e acompanhar umidade"
            return "Programar irrigação nas próximas 24 h"
        return "Acompanhar temperatura nos horários de pico"

    if risco == "Sem dados":
        return "Verificar comunicação do sensor"

    return "Manter monitoramento"


def gerar_alerta(linha):
    risco = linha["nivel_risco"]
    if risco == "Alto":
        return f"ALERTA: risco alto ({linha['tipo_alerta']})"
    if risco == "Moderado":
        return f"ATENÇÃO: risco moderado ({linha['tipo_alerta']})"
    if risco == "Sem dados":
        return "ALERTA: dados insuficientes"
    return "Sem alerta"


def definir_acao(linha):
    risco = linha["nivel_risco"]
    if risco == "Alto":
        return "Acionar irrigação" if linha["talhao_irrigado"] else "Notificar produtor"
    if risco == "Moderado":
        return "Monitoramento reforçado"
    if risco == "Sem dados":
        return "Verificar sensor"
    return "Nenhuma ação necessária"


def maior_sequencia(serie_booleana):
    """Maior número de leituras seguidas em que a condição é verdadeira."""
    maior = atual = 0
    for valor in serie_booleana:
        atual = atual + 1 if valor else 0
        maior = max(maior, atual)
    return maior


def resumir_talhoes(sensores):
    linhas = []
    for talhao, grupo in sensores.groupby("talhao"):
        grupo = grupo.sort_values("data_hora")
        linhas.append({
            "talhao": talhao,
            "irrigado": "Sim" if grupo["talhao_irrigado"].iloc[0] else "Não",
            "leituras": len(grupo),
            "umidade_media_pct": round(grupo["umidade_solo_pct"].mean(), 1),
            "umidade_minima_pct": grupo["umidade_solo_pct"].min(),
            "temperatura_maxima_c": grupo["temperatura_solo_c"].max(),
            "alertas_alto": int((grupo["nivel_risco"] == "Alto").sum()),
            "alertas_moderado": int((grupo["nivel_risco"] == "Moderado").sum()),
            "maior_sequencia_critica": maior_sequencia(grupo["umidade_solo_pct"] < UMIDADE_CRITICA),
            "irrigacao_total_mm": round(grupo["irrigacao_aplicada_mm"].sum(), 1),
        })
    return pd.DataFrame(linhas)


def gerar_insights(sensores, resumo):
    """Textos do painel gerados a partir dos dados, não escritos à mão."""
    insights = []

    pior = resumo.sort_values("alertas_alto", ascending=False).iloc[0]
    insights.append((
        "Talhão mais crítico",
        f"{pior['talhao']} teve {pior['alertas_alto']} leituras de risco alto e "
        f"chegou a {pior['umidade_minima_pct']}% de umidade "
        f"({pior['maior_sequencia_critica']} leituras seguidas abaixo de {UMIDADE_CRITICA:.0f}%).",
    ))

    irrigados = resumo[resumo["irrigado"] == "Sim"]
    nao_irrigados = resumo[resumo["irrigado"] == "Não"]
    if len(irrigados) and len(nao_irrigados):
        insights.append((
        "Comparação entre talhões",
            f"Talhões irrigados ficaram com umidade mínima entre "
            f"{irrigados['umidade_minima_pct'].min()}% e {irrigados['umidade_minima_pct'].max()}%; "
            f"o talhão sem irrigação chegou a {nao_irrigados['umidade_minima_pct'].min()}%.",
        ))

    sensores = sensores.copy()
    sensores["mes"] = sensores["data_hora"].dt.strftime("%Y-%m")
    por_mes = sensores.groupby("mes")["umidade_solo_pct"].mean().round(1)
    insights.append((
        "Tendência da umidade",
        f"A umidade média do solo foi de {por_mes.iloc[0]}% em {por_mes.index[0]} "
        f"para {por_mes.iloc[-1]}% em {por_mes.index[-1]}.",
    ))

    total = len(sensores)
    alto = int((sensores["nivel_risco"] == "Alto").sum())
    moderado = int((sensores["nivel_risco"] == "Moderado").sum())
    insights.append((
        "Alertas no período",
        f"{alto} leituras de risco alto e {moderado} de risco moderado, "
        f"de {total} leituras válidas ({(alto + moderado) / total:.0%}).",
    ))

    if alto:
        insights.append((
            "Recomendação principal",
            f"Priorizar {pior['talhao']}: "
            + gerar_recomendacao(sensores[sensores["talhao"] == pior["talhao"]]
                                 .sort_values("nivel_risco").iloc[0]),
        ))

    return pd.DataFrame(insights, columns=["indicador", "texto"])


def main():
    sensores = pd.read_csv(arquivo_entrada)
    sensores["data_hora"] = pd.to_datetime(sensores["data_hora"], errors="coerce", utc=True)

    print("==========================================")
    print("      AUTOMAÇÃO AGROSMART")
    print("==========================================")
    print("Registros de entrada:", len(sensores))
    print("Aplicando regras de decisão...")

    # Talhão irrigado = já recebeu irrigação em algum momento do período
    irrigados = sensores.groupby("talhao")["irrigacao_aplicada_mm"].sum().gt(0)
    sensores["talhao_irrigado"] = sensores["talhao"].map(irrigados)

    sensores["nivel_risco"] = sensores.apply(classificar_risco, axis=1)
    sensores["tipo_alerta"] = sensores.apply(tipo_alerta, axis=1)
    sensores["recomendacao"] = sensores.apply(gerar_recomendacao, axis=1)
    sensores["alerta"] = sensores.apply(gerar_alerta, axis=1)
    sensores["acao_automatica"] = sensores.apply(definir_acao, axis=1)

    sensores = sensores.sort_values(["data_hora", "talhao"])
    sensores.to_csv(arquivo_saida, index=False, encoding="utf-8-sig")

    resumo = resumir_talhoes(sensores)
    resumo.to_csv(arquivo_resumo, index=False, encoding="utf-8-sig")

    # Insights falam da fazenda: a bancada do TinkerCad é teste do nó de sensores
    campo = ~sensores["talhao"].str.contains("TinkerCad")
    resumo_campo = resumo[~resumo["talhao"].str.contains("TinkerCad")]
    insights = gerar_insights(sensores[campo], resumo_campo)
    insights.to_csv(arquivo_insights, index=False, encoding="utf-8-sig")

    print()
    print("Distribuição dos níveis de risco:")
    print(sensores["nivel_risco"].value_counts())
    print()
    print("Ações automáticas:")
    print(sensores["acao_automatica"].value_counts())
    print()
    print("Resumo por talhão:")
    print(resumo.to_string(index=False))
    print()
    print("Insights gerados:")
    for _, linha in insights.iterrows():
        print(f"  - {linha['indicador']}: {linha['texto']}")

    print()
    print("Últimos alertas de risco alto:")
    colunas = ["data_hora", "talhao", "umidade_solo_pct", "temperatura_solo_c",
               "alerta", "acao_automatica"]
    print(sensores[sensores["nivel_risco"] == "Alto"][colunas].tail(5).to_string(index=False))

    print()
    print("Arquivos gerados:")
    for arquivo in (arquivo_saida, arquivo_resumo, arquivo_insights):
        print("  -", arquivo.relative_to(RAIZ))


if __name__ == "__main__":
    main()
