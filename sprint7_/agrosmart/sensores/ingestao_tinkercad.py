"""
AgroSmart - ingestão das leituras do TinkerCad.

O TinkerCad não grava arquivo: o Arduino escreve linhas CSV no Monitor Serial.
Copie o conteúdo do Monitor Serial para dados/brutos/serial_tinkercad.txt e
rode este script. Ele converte as linhas para o mesmo formato das leituras
de campo (dados/brutos/leituras_sensores.csv), para que o processamento trate
as duas fontes do mesmo jeito.

O simulador não fornece data/hora no CSV. Para ordenar a bancada, cada leitura
recebe um horário SINTÉTICO a partir de INICIO, separado por uma hora. Esses
horários não representam a data da captura nem o intervalo real de 2 s do sketch.

Uso:
    python sensores/ingestao_tinkercad.py
"""

import csv
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

arquivo_serial = RAIZ / "dados/brutos/serial_tinkercad.txt"
arquivo_saida = RAIZ / "dados/brutos/leituras_tinkercad.csv"

INICIO = datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc)
INTERVALO = timedelta(hours=1)

FAZENDA = "Fazenda Pedralva"
TALHAO = "Talhao 05 - Bancada TinkerCad"
CULTURA = "Soja - Ciclo 2026/2027"

COLUNAS = [
    "sensor_id", "data_hora", "fazenda", "talhao", "cultura",
    "umidade_solo_pct", "temperatura_solo_c", "condutividade_ds_m",
    "irrigacao_aplicada_mm", "status_sensor",
]


def ler_serial():
    leituras = []
    ignoradas = 0
    for linha in arquivo_serial.read_text(encoding="utf-8").splitlines():
        partes = [p.strip() for p in linha.split(",")]
        # Ignora cabeçalho e qualquer linha que não seja uma leitura completa
        if len(partes) != 4 or not partes[0] or partes[0] == "sensor_id":
            ignoradas += 1 if linha.strip() else 0
            continue
        try:
            umidade = float(partes[1])
            temperatura = float(partes[2])
        except ValueError:
            ignoradas += 1
            continue
        if not (math.isfinite(umidade) and math.isfinite(temperatura)):
            ignoradas += 1
            continue
        leituras.append((partes[0], umidade, temperatura))
    return leituras, ignoradas


def main():
    leituras, ignoradas = ler_serial()

    with open(arquivo_saida, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS)
        escritor.writeheader()
        for i, (sensor_id, umidade, temperatura) in enumerate(leituras):
            escritor.writerow({
                "sensor_id": sensor_id,
                "data_hora": (INICIO + i * INTERVALO).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "fazenda": FAZENDA,
                "talhao": TALHAO,
                "cultura": CULTURA,
                "umidade_solo_pct": umidade,
                "temperatura_solo_c": temperatura,
                "condutividade_ds_m": "",
                "irrigacao_aplicada_mm": 0.0,
                "status_sensor": "operacional",
            })

    print(f"Leituras do TinkerCad convertidas: {len(leituras)} (linhas ignoradas: {ignoradas})")
    print("Arquivo gerado:", arquivo_saida.relative_to(RAIZ))


if __name__ == "__main__":
    main()
