import pandas as pd
from pathlib import Path

base = Path(".")

arquivo_entrada = base / "dados-base/leituras_sensores.csv"
arquivo_saida = base / "dataset_processado_agrosmart.csv"


sensores = pd.read_csv(arquivo_entrada)

print("Quantidade de registros:", len(sensores))
print("Colunas:", list(sensores.columns))

# Remove linhas completamente vazias
sensores = sensores.dropna(how="all")

# Remove registros duplicados
sensores = sensores.drop_duplicates()

sensores["data_hora"] = pd.to_datetime(
    sensores["data_hora"],
    errors="coerce"
)

colunas_numericas = [
    "umidade_solo_pct",
    "temperatura_solo_c",
    "condutividade_ds_m",
    "irrigacao_aplicada_mm"
]

for coluna in colunas_numericas:
    sensores[coluna] = pd.to_numeric(
        sensores[coluna],
        errors="coerce"
    )

colunas_texto = [
    "sensor_id",
    "fazenda",
    "talhao",
    "cultura",
    "status_sensor"
]

for coluna in colunas_texto:
    sensores[coluna] = (
        sensores[coluna]
        .astype("string")
        .str.strip()
    )

def classificar_umidade(valor):

    if pd.isna(valor):
        return "Sem dados"

    if valor < 30:
        return "Baixa"

    if valor < 60:
        return "Adequada"

    return "Alta"


sensores["classificacao_umidade"] = (
    sensores["umidade_solo_pct"]
    .apply(classificar_umidade)
)

def classificar_risco(linha):

    umidade = linha["umidade_solo_pct"]
    temperatura = linha["temperatura_solo_c"]

    # Não existem dados suficientes
    if pd.isna(umidade) and pd.isna(temperatura):
        return "Sem dados"

    # Situação de alto risco
    if (
        (pd.notna(umidade) and umidade < 30)
        or
        (pd.notna(temperatura) and temperatura >= 35)
    ):
        return "Alto"

    # Situação de risco moderado
    if (
        (pd.notna(umidade) and umidade < 40)
        or
        (pd.notna(temperatura) and temperatura >= 30)
    ):
        return "Moderado"

    # Situação normal
    return "Normal"


sensores["nivel_risco"] = sensores.apply(
    classificar_risco,
    axis=1
)

def gerar_recomendacao(linha):

    risco = linha["nivel_risco"]
    umidade = linha["umidade_solo_pct"]

    if risco == "Alto":

        if pd.notna(umidade) and umidade < 30:
            return "Verificar necessidade de irrigação"

        return "Realizar inspeção do talhão"

    if risco == "Moderado":
        return "Acompanhar condições do ambiente"

    if risco == "Sem dados":
        return "Verificar comunicação do sensor"

    return "Manter monitoramento"


sensores["recomendacao"] = sensores.apply(
    gerar_recomendacao,
    axis=1
)

sensores["irrigacao_realizada"] = (
    sensores["irrigacao_aplicada_mm"]
    .fillna(0)
    .gt(0)
    .map({
        True: "Sim",
        False: "Não"
    })
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
print("Processamento concluído!")
print("Arquivo gerado:", arquivo_saida)

print()
print("Distribuição dos níveis de risco:")

print(
    sensores["nivel_risco"]
    .value_counts(dropna=False)
)

print()
print("Primeiros registros processados:")

print(
    sensores.head(10)
)