"""Monta e verifica o pacote técnico local da Fase 7; não envia nem submete a entrega.

Uso: python entrega/montar_zip.py [AldrinDaSilvaRodrigues_RM551679_4ESOA]
Gera entrega/<prefixo>_fase7_atividade.zip. Aprovação e submissão ficam em ESTADO_ENTREGA.md.
"""

import re
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PREFIXO_PADRAO = "AldrinDaSilvaRodrigues_RM551679_4ESOA"
INCLUIR = [
    "README.md", "PITCH.md", "pipeline.py", "requirements.txt", "requirements-dev.txt",
    "ESTADO_ENTREGA.md", "REVISAO_ENTREGA.md", "AUTOAVALIACAO.md",
    "docs", "sensores", "dados", "src", "tests", "monitoramento",
    "dashboard/gerar_dashboard.py", "dashboard/agrosmart_dashboard.html",
    "dashboard/descricao_indicadores.md", "dashboard/prints",
    "dashboard/GUIA_POWERBI.md", "dashboard/powerbi_versao_inicial",
    "video/narracao.json", "video/gerar_audio.ps1", "video/render_video.py",
    "entrega/montar_zip.py",
    "Dockerfile", ".dockerignore", "ruff.toml", ".github/workflows",
]
# Nunca entram no pacote: controle de versão, caches, trava de execução e ZIPs.
IGNORAR_PARTES = {"__pycache__", ".git", ".ruff_cache", ".idea", ".venv"}
IGNORAR_NOMES = {".execucao.lock"}


def listar_arquivos(raiz):
    arquivos = []
    for item in INCLUIR:
        caminho = raiz / item
        if not caminho.exists():
            raise FileNotFoundError(f"Item obrigatório ausente: {item}")
        candidatos = [caminho] if caminho.is_file() else sorted(caminho.rglob("*"))
        itens = [p for p in candidatos if p.is_file()
                 and not IGNORAR_PARTES & set(p.relative_to(raiz).parts)
                 and p.name not in IGNORAR_NOMES and p.suffix not in {".pyc", ".zip", ".tmp"}]
        if not itens:
            raise ValueError(f"Item obrigatório vazio: {item}")
        for arquivo in itens:
            if arquivo.is_symlink() or not arquivo.resolve().is_relative_to(raiz.resolve()):
                raise ValueError(f"Arquivo fora da raiz permitida: {arquivo}")
        arquivos.extend(itens)
    return sorted(set(arquivos))


def montar(prefixo=PREFIXO_PADRAO, raiz=RAIZ):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", prefixo):
        raise ValueError("Prefixo deve usar apenas letras ASCII, números, _ ou -")
    arquivos = listar_arquivos(raiz)
    destino = raiz / "entrega" / f"{prefixo}_fase7_atividade.zip"
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporario, "w", zipfile.ZIP_DEFLATED) as pacote:
        for arquivo in arquivos:
            pacote.write(arquivo, Path("agrosmart") / arquivo.relative_to(raiz))
    with zipfile.ZipFile(temporario) as pacote:
        corrompido = pacote.testzip()
        if corrompido:
            raise ValueError(f"Falha CRC no ZIP: {corrompido}")
        if len(pacote.namelist()) != len(arquivos):
            raise ValueError("Quantidade de arquivos no ZIP não confere")
    temporario.replace(destino)
    return destino, len(arquivos)


if __name__ == "__main__":
    destino, quantidade = montar(sys.argv[1] if len(sys.argv) > 1 else PREFIXO_PADRAO)
    print(f"ZIP técnico gerado: {destino} ({destino.stat().st_size} bytes; {quantidade} arquivos)")
    print("Envio/submissão não realizados; veja ESTADO_ENTREGA.md.")
