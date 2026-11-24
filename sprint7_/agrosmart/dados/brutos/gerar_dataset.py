"""
Gerador do dataset base da AgroSmart - Fase 5.

Cria um cenario unico e coerente (Fazenda Pedralva, soja ciclo 2026/2027)
usado por todos os artefatos da entrega: arquitetura do Data Lake, fluxo de
ingestao, IA generativa e modelo de negocio.

Os dados sao sinteticos e deterministas (semente fixa), gerados a partir de um
modelo simples de balanco hidrico do solo. De proposito o arquivo de leituras
inclui registros "sujos" (duplicata, outlier e sensor com falha), para que a
camada bruta do Data Lake tenha o que validar antes de virar camada confiavel.

Uso:
    python gerar_dataset.py
"""

import csv
import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SEMENTE = 20260905
INICIO = date(2026, 6, 5)
FIM = date(2026, 9, 2)

FAZENDA = "Fazenda Pedralva"
CULTURA = "Soja - Ciclo 2026/2027"

# talhao -> (id do sensor, area em ha, capacidade de retencao do solo, tem irrigacao)
TALHOES = {
    "Talhao 01 - Sul":   ("SM-PED-001", 42.0, 1.00, True),
    "Talhao 02 - Leste": ("SM-PED-002", 38.5, 0.85, True),
    "Talhao 03 - Norte": ("SM-PED-003", 55.2, 0.70, False),
    "Talhao 04 - Oeste": ("SM-PED-004", 47.8, 0.95, True),
}

RAIZ = Path(__file__).resolve().parent


def gerar_clima(rng):
    """Serie diaria da estacao meteorologica da fazenda (inverno seco -> primavera)."""
    linhas = []
    dia = INICIO
    while dia <= FIM:
        avanco = (dia - INICIO).days / max((FIM - INICIO).days, 1)
        # a chance de chuva cai: a serie atravessa o auge da estacao seca
        chance_chuva = 0.38 - 0.30 * avanco
        if rng.random() < chance_chuva:
            precipitacao = round(rng.uniform(1.5, 34.0) * (1.0 - 0.5 * avanco), 1)
        else:
            precipitacao = 0.0
        temp_min = round(rng.uniform(11.0, 17.0) + 4.0 * avanco, 1)
        temp_max = round(temp_min + rng.uniform(9.0, 15.0), 1)
        linhas.append({
            "data": dia.isoformat(),
            "estacao_id": "EM-PED-01",
            "precipitacao_mm": precipitacao,
            "temp_min_c": temp_min,
            "temp_max_c": temp_max,
            "umidade_ar_pct": round(rng.uniform(38.0, 88.0) - 10.0 * (precipitacao == 0.0), 1),
            "vento_kmh": round(rng.uniform(3.0, 22.0), 1),
            "radiacao_mj_m2": round(rng.uniform(9.0, 23.0), 1),
        })
        dia += timedelta(days=1)
    return linhas


def gerar_leituras(rng, clima):
    """Leituras diarias dos sensores de solo, via balanco hidrico simplificado."""
    por_data = {c["data"]: c for c in clima}
    linhas = []
    umidade = {t: rng.uniform(30.0, 40.0) for t in TALHOES}

    for dia_str in sorted(por_data):
        c = por_data[dia_str]
        for talhao, (sensor_id, _area, retencao, irrigado) in TALHOES.items():
            # entrada de agua: chuva (+ irrigacao quando o solo passa do gatilho)
            entrada = c["precipitacao_mm"] * 0.75 * retencao
            irrigacao_mm = 0.0
            if irrigado and umidade[talhao] < 22.0 and c["precipitacao_mm"] < 2.0:
                irrigacao_mm = round(rng.uniform(8.0, 14.0), 1)
                entrada += irrigacao_mm * 0.75
            # saida: evapotranspiracao proporcional a agua disponivel e ao calor
            saida = umidade[talhao] * (c["temp_max_c"] - 12.0) * 0.004 / retencao
            umidade[talhao] = max(5.0, min(58.0, umidade[talhao] + entrada - saida))

            linhas.append({
                "sensor_id": sensor_id,
                "data_hora": f"{dia_str}T09:00:00Z",
                "fazenda": FAZENDA,
                "talhao": talhao,
                "cultura": CULTURA,
                "umidade_solo_pct": round(umidade[talhao], 1),
                "temperatura_solo_c": round(c["temp_max_c"] - rng.uniform(1.5, 4.5), 1),
                "condutividade_ds_m": round(rng.uniform(0.8, 2.4), 2),
                "irrigacao_aplicada_mm": irrigacao_mm,
                "status_sensor": "operacional",
            })
    return linhas


def sujar(linhas):
    """Injeta os defeitos que a camada de validacao precisa capturar."""
    problemas = []

    # 1. registro duplicado (mesma leitura reenviada pelo gateway MQTT)
    alvo = linhas[len(linhas) // 3]
    linhas.append(dict(alvo))
    problemas.append(f"duplicata: {alvo['sensor_id']} em {alvo['data_hora']}")

    # 2. outlier fisicamente impossivel (umidade acima de 100%)
    alvo = dict(linhas[len(linhas) // 2])
    alvo["umidade_solo_pct"] = 148.7
    alvo["data_hora"] = alvo["data_hora"].replace("T09:00:00Z", "T15:00:00Z")
    linhas.append(alvo)
    problemas.append(f"outlier: umidade 148.7% em {alvo['talhao']}")

    # 3. sensor em falha, sem valor medido
    alvo = dict(linhas[-40])
    alvo["umidade_solo_pct"] = ""
    alvo["temperatura_solo_c"] = ""
    alvo["condutividade_ds_m"] = ""
    alvo["status_sensor"] = "falha_comunicacao"
    alvo["data_hora"] = alvo["data_hora"].replace("T09:00:00Z", "T21:00:00Z")
    linhas.append(alvo)
    problemas.append(f"falha de comunicacao: {alvo['sensor_id']} em {alvo['data_hora']}")

    linhas.sort(key=lambda r: (r["data_hora"], r["talhao"]))
    return problemas


def gerar_produtividade(rng):
    """Historico de produtividade por talhao (safras anteriores)."""
    linhas = []
    for safra, base in (("2023/2024", 3050), ("2024/2025", 3180), ("2025/2026", 3260)):
        for talhao, (_sid, area, retencao, irrigado) in TALHOES.items():
            prod = base * (0.86 + 0.18 * retencao) * (1.06 if irrigado else 1.0)
            prod = round(prod + rng.uniform(-140, 140))
            linhas.append({
                "safra": safra,
                "fazenda": FAZENDA,
                "talhao": talhao,
                "area_ha": area,
                "cultura": "Soja",
                "produtividade_kg_ha": prod,
                "producao_total_kg": round(prod * area),
                "irrigacao": "SIM" if irrigado else "NAO",
                "custo_producao_brl_ha": round(rng.uniform(3900, 4700), 2),
            })
    return linhas


def escrever_csv(caminho, linhas):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"  {caminho.name}: {len(linhas)} linhas")


def main():
    rng = random.Random(SEMENTE)

    clima = gerar_clima(rng)
    leituras = gerar_leituras(rng, clima)
    problemas = sujar(leituras)
    produtividade = gerar_produtividade(rng)

    print("Gerando dataset base da AgroSmart...")
    escrever_csv(RAIZ / "clima_estacao.csv", clima)
    escrever_csv(RAIZ / "leituras_sensores.csv", leituras)
    escrever_csv(RAIZ / "produtividade_talhoes.csv", produtividade)

    # exemplo de payload cru, do jeito que chega do sensor via MQTT
    exemplo = leituras[-1]
    payload = {
        "sensor_id": exemplo["sensor_id"],
        "tipo_sensor": "Umidade do Solo",
        "fazenda": exemplo["fazenda"],
        "talhao": exemplo["talhao"],
        "data_hora": exemplo["data_hora"],
        "valor_medido": exemplo["umidade_solo_pct"],
        "unidade": "%",
        "status_sensor": exemplo["status_sensor"],
        "localizacao": {"latitude": -21.7042, "longitude": -45.4558, "altitude": 872},
        "metadados": {
            "fabricante": "AgroSmart Tecnologia",
            "modelo": "SoloPro-X",
            "versao_firmware": "v2.3.1",
            "ultima_calibracao": "2026-08-15",
        },
        "condicoes_ambiente": {
            "temperatura_solo_c": exemplo["temperatura_solo_c"],
            "condutividade_ds_m": exemplo["condutividade_ds_m"],
        },
        "cultura_associada": exemplo["cultura"],
        # Data sintética do exemplo, fixa para a reprodução do dataset.
        "gerado_em": datetime.combine(FIM, datetime.min.time(), tzinfo=timezone.utc).isoformat(),
    }
    caminho_json = RAIZ / "payload_sensor_mqtt.json"
    caminho_json.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"  {caminho_json.name}: payload de exemplo")

    print("\nDefeitos injetados de proposito na camada bruta:")
    for p in problemas:
        print(f"  - {p}")


if __name__ == "__main__":
    main()
