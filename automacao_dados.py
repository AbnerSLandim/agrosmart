from pathlib import Path

import pandas as pd

base = Path(".")

arquivo_entrada = base / "dataset_processado_agrosmart.csv"
arquivo_saida = base / "resultado_automacao_agrosmart.csv"

sensores = pd.read_csv(
    arquivo_entrada
)

print("==========================================")
print("      AUTOMACAO AGROSMART")
print("==========================================")
print()

print("Arquivo de entrada:", arquivo_entrada)
print("Quantidade de registros:", len(sensores))
print()

def classificar_risco(linha):

    umidade = linha["umidade_solo_pct"]
    temperatura = linha["temperatura_solo_c"]

    # Não existem dados suficientes
    if pd.isna(umidade) and pd.isna(temperatura):
        return "Sem dados"

    # Risco alto:
    # Umidade abaixo de 30%
    # OU temperatura igual ou superior a 35°C
    if (
        (pd.notna(umidade) and umidade < 30)
        or
        (pd.notna(temperatura) and temperatura >= 35)
    ):
        return "Alto"

    # Risco moderado:
    # Umidade abaixo de 40%
    # OU temperatura igual ou superior a 30°C
    if (
        (pd.notna(umidade) and umidade < 40)
        or
        (pd.notna(temperatura) and temperatura >= 30)
    ):
        return "Moderado"

    # Caso não se enquadre nas situações anteriores
    return "Normal"

def gerar_recomendacao(linha):

    risco = linha["nivel_risco"]
    umidade = linha["umidade_solo_pct"]
    temperatura = linha["temperatura_solo_c"]

    if risco == "Alto":

        # Solo muito seco
        if pd.notna(umidade) and umidade < 30:
            return "Verificar necessidade de irrigação"

        # Temperatura muito alta
        if pd.notna(temperatura) and temperatura >= 35:
            return "Realizar inspeção do talhão"

        return "Realizar inspeção do talhão"

    if risco == "Moderado":
        return "Acompanhar condições do ambiente"

    if risco == "Sem dados":
        return "Verificar comunicação do sensor"

    return "Manter monitoramento"

def gerar_alerta(linha):

    risco = linha["nivel_risco"]

    if risco == "Alto":
        return "ALERTA: Situação de alto risco detectada"

    if risco == "Moderado":
        return "ATENÇÃO: Situação de risco moderado"

    if risco == "Sem dados":
        return "ALERTA: Dados insuficientes"

    return "Sem alerta"

print("Aplicando regras de decisão...")

sensores["nivel_risco"] = sensores.apply(
    classificar_risco,
    axis=1
)

sensores["recomendacao"] = sensores.apply(
    gerar_recomendacao,
    axis=1
)

sensores["alerta"] = sensores.apply(
    gerar_alerta,
    axis=1
)

def definir_acao(linha):

    risco = linha["nivel_risco"]

    if risco == "Alto":
        return "Intervenção recomendada"

    if risco == "Moderado":
        return "Monitoramento reforçado"

    if risco == "Sem dados":
        return "Verificar sensor"

    return "Nenhuma ação necessária"


sensores["acao_automatica"] = sensores.apply(
    definir_acao,
    axis=1
)

if "data_hora" in sensores.columns:

    sensores["data_hora"] = pd.to_datetime(
        sensores["data_hora"],
        errors="coerce"
    )

    sensores = sensores.sort_values(
        "data_hora"
    )

sensores.to_csv(
    arquivo_saida,
    index=False,
    encoding="utf-8-sig"
)

print()
print("==========================================")
print("       AUTOMAÇÃO CONCLUÍDA")
print("==========================================")
print()

print("Arquivo gerado:", arquivo_saida)
print()

print("Distribuição dos níveis de risco:")
print(
    sensores["nivel_risco"]
    .value_counts(dropna=False)
)

print()

print("Distribuição das ações automáticas:")
print(
    sensores["acao_automatica"]
    .value_counts(dropna=False)
)

print()

alertas = sensores[
    sensores["nivel_risco"].isin(
        ["Alto", "Moderado", "Sem dados"]
    )
]

print("==========================================")
print("        ALERTAS GERADOS")
print("==========================================")
print()

if len(alertas) == 0:

    print("Nenhum alerta foi gerado.")

else:

    for _, linha in alertas.iterrows():

        print(
            f"Sensor: {linha['sensor_id']}"
        )

        print(
            f"Fazenda: {linha['fazenda']}"
        )

        print(
            f"Talhão: {linha['talhao']}"
        )

        print(
            f"Umidade: {linha['umidade_solo_pct']}%"
        )

        print(
            f"Temperatura: {linha['temperatura_solo_c']}°C"
        )

        print(
            f"Risco: {linha['nivel_risco']}"
        )

        print(
            f"Alerta: {linha['alerta']}"
        )

        print(
            f"Recomendação: {linha['recomendacao']}"
        )

        print(
            f"Ação automática: {linha['acao_automatica']}"
        )

        print("------------------------------------------")

print()
print("Primeiros registros após a automação:")
print()

colunas_exibicao = [
    "sensor_id",
    "fazenda",
    "talhao",
    "umidade_solo_pct",
    "temperatura_solo_c",
    "nivel_risco",
    "alerta",
    "recomendacao",
    "acao_automatica"
]

# Mostra somente as colunas que realmente existem
colunas_exibicao = [
    coluna
    for coluna in colunas_exibicao
    if coluna in sensores.columns
]

print(
    sensores[colunas_exibicao].head(10)
)