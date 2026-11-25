"""
AgroSmart - roda o fluxo completo, do sensor ao arquivo do dashboard.

    1. sensores/ingestao_tinkercad.py  serial do TinkerCad -> leituras_tinkercad.csv
    2. src/processamento.py            limpeza e validação -> dataset_processado
    3. src/automacao.py                regras de decisão   -> resultado, resumo e insights
    4. dashboard/gerar_dashboard.py    painel analítico    -> dashboard/agrosmart_dashboard.html

Uso:
    python pipeline.py
"""

import runpy
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

ETAPAS = [
    ("Ingestão TinkerCad", RAIZ / "sensores/ingestao_tinkercad.py"),
    ("Processamento", RAIZ / "src/processamento.py"),
    ("Automação", RAIZ / "src/automacao.py"),
    ("Dashboard", RAIZ / "dashboard/gerar_dashboard.py"),
]

for nome, script in ETAPAS:
    if nome == "Ingestão TinkerCad" and not (RAIZ / "dados/brutos/serial_tinkercad.txt").exists():
        print(f"\n### {nome}: sem serial_tinkercad.txt, etapa pulada\n")
        continue
    print(f"\n### {nome}\n")
    runpy.run_path(str(script), run_name="__main__")

print("\nPipeline concluído. Abra dashboard/agrosmart_dashboard.html no navegador.")
