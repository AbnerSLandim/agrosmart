"""
AgroSmart - Parte 3: processamento e preparação dos dados.

Lê as leituras brutas dos sensores (dataset base + leituras do TinkerCad),
limpa, valida e salva o dataset processado usado pela automação.

Uso:
    python src/processamento.py
"""

import pandas as pd
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

arquivo_entrada = RAIZ / "dados/brutos/leituras_sensores.csv"
arquivo_tinkercad = RAIZ / "dados/brutos/leituras_tinkercad.csv"
arquivo_saida = RAIZ / "dados/processados/dataset_processado_agrosmart.csv"
arquivo_descartes = RAIZ / "dados/processados/registros_descartados.csv"

# Limites físicos dos sensores: fora disso a leitura é erro, não medição
LIMITES = {
    "umidade_solo_pct": (0, 100),
    "temperatura_solo_c": (-10, 60),
}
COLUNAS_OBRIGATORIAS = [
    "sensor_id", "data_hora", "fazenda", "talhao", "cultura",
    "umidade_solo_pct", "temperatura_solo_c", "condutividade_ds_m",
    "irrigacao_aplicada_mm", "status_sensor",
]


def carregar():
    sensores = pd.read_csv(arquivo_entrada)
    validar_esquema(sensores, arquivo_entrada.name)
    print("Leituras do dataset base:", len(sensores))

    # Leituras vindas da simulação no TinkerCad (geradas por ingestao_tinkercad.py)
    if arquivo_tinkercad.exists():
        tinkercad = pd.read_csv(arquivo_tinkercad)
        validar_esquema(tinkercad, arquivo_tinkercad.name)
        print("Leituras do TinkerCad:", len(tinkercad))
        sensores = pd.concat([sensores, tinkercad], ignore_index=True)

    return sensores


def validar_esquema(sensores, origem):
    ausentes = set(COLUNAS_OBRIGATORIAS) - set(sensores.columns)
    if ausentes:
        raise ValueError(f"{origem}: colunas obrigatórias ausentes: {sorted(ausentes)}")


def classificar_umidade(valor):
    if pd.isna(valor):
        return "Sem dados"
    if valor < 18:
        return "Crítica"
    if valor < 22:
        return "Baixa"
    if valor < 40:
        return "Adequada"
    return "Alta"


def processar(sensores):
    """Valida sem alterar a entrada; devolve leituras válidas e descartes auditáveis."""
    validar_esquema(sensores, "dataset")
    sensores = sensores.copy()
    descartes = []

    # Remove linhas completamente vazias
    sensores = sensores.dropna(how="all")

    # Remove registros duplicados (gateway reenviando a mesma leitura)
    for _, linha in sensores[sensores.duplicated()].iterrows():
        descartes.append({**linha.to_dict(), "motivo_descarte": "duplicata"})
    sensores = sensores.drop_duplicates()

    sensores["data_hora"] = pd.to_datetime(sensores["data_hora"], errors="coerce", utc=True)

    colunas_numericas = [
        "umidade_solo_pct",
        "temperatura_solo_c",
        "condutividade_ds_m",
        "irrigacao_aplicada_mm",
    ]
    for coluna in colunas_numericas:
        sensores[coluna] = pd.to_numeric(sensores[coluna], errors="coerce")

    colunas_texto = ["sensor_id", "fazenda", "talhao", "cultura", "status_sensor"]
    for coluna in colunas_texto:
        sensores[coluna] = sensores[coluna].astype("string").str.strip()

    # Sem instante ou identificação não existe leitura rastreável para o painel.
    sem_identificacao = sensores[["sensor_id", "talhao"]].isna().any(axis=1)
    sem_identificacao |= sensores[["sensor_id", "talhao"]].eq("").any(axis=1)
    invalida = sensores["data_hora"].isna() | sem_identificacao
    for _, linha in sensores[invalida].iterrows():
        motivo = "data/hora inválida" if pd.isna(linha["data_hora"]) else "identificação ausente"
        descartes.append({**linha.to_dict(), "motivo_descarte": motivo})
    sensores = sensores[~invalida].copy()

    # Valores fisicamente impossíveis: descarta (não interpola)
    fora_do_limite = pd.Series(False, index=sensores.index)
    for coluna, (minimo, maximo) in LIMITES.items():
        fora_do_limite |= sensores[coluna].notna() & ~sensores[coluna].between(minimo, maximo)
    for _, linha in sensores[fora_do_limite].iterrows():
        descartes.append({**linha.to_dict(), "motivo_descarte": "fora do limite físico"})
    sensores = sensores[~fora_do_limite]

    # Sensor sem nenhum valor medido: descarta e registra a lacuna
    sem_medicao = sensores["umidade_solo_pct"].isna() & sensores["temperatura_solo_c"].isna()
    for _, linha in sensores[sem_medicao].iterrows():
        descartes.append({**linha.to_dict(), "motivo_descarte": "sensor sem medição"})
    sensores = sensores[~sem_medicao].copy()

    sensores["classificacao_umidade"] = sensores["umidade_solo_pct"].apply(classificar_umidade)
    sensores["irrigacao_realizada"] = (
        sensores["irrigacao_aplicada_mm"].fillna(0).gt(0).map({True: "Sim", False: "Não"})
    )

    # Colunas separadas de data e hora facilitam o Power BI
    sensores["data"] = sensores["data_hora"].dt.date
    sensores["hora"] = sensores["data_hora"].dt.strftime("%H:%M")

    sensores = sensores.sort_values(["data_hora", "talhao"])
    descartes = pd.DataFrame(descartes, columns=COLUNAS_OBRIGATORIAS + ["motivo_descarte"])
    return sensores, descartes


def main():
    entrada = carregar()
    print("Colunas:", list(entrada.columns))
    sensores, descartes = processar(entrada)

    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
    sensores.to_csv(arquivo_saida, index=False, encoding="utf-8-sig")
    descartes.to_csv(arquivo_descartes, index=False, encoding="utf-8-sig")

    print()
    print("Processamento concluído!")
    print("Registros válidos:", len(sensores))
    print("Registros descartados:", len(descartes))
    for d in descartes.to_dict(orient="records"):
        print(f"  - {d['sensor_id']} {d['data_hora']}: {d['motivo_descarte']}")
    print("Arquivo gerado:", arquivo_saida.relative_to(RAIZ))
    print()
    print("Classificação da umidade:")
    print(sensores["classificacao_umidade"].value_counts())


if __name__ == "__main__":
    main()
