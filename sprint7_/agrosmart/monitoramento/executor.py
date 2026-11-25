"""
AgroSmart - Fase 7: execução automatizada e monitoramento do pipeline.

Executa as etapas do pipeline (ingestão, processamento, automação, dashboard),
mede cada uma, registra logs e, ao final, calcula indicadores de funcionamento
e verificações de saúde. Pode rodar uma vez, em N ciclos ou continuamente.

Saídas (pasta monitoramento/):
    logs/agrosmart.log           log legível, com rotação (3 arquivos de 500 KB)
    logs/eventos.jsonl           um evento JSON por etapa/ciclo (para ferramentas)
    status.json                  estado da última execução (sobrescrito a cada ciclo)
    historico_execucoes.csv      uma linha por ciclo (acumulativo)
    status.html                  painel de status offline, sem JavaScript

Uso (a partir da pasta agrosmart):
    python monitoramento/executor.py                          # 1 ciclo
    python monitoramento/executor.py --ciclos 3 --intervalo 5 # 3 ciclos, 5 s entre eles
    python monitoramento/executor.py --continuo --intervalo 900  # a cada 15 min, até Ctrl+C
    python monitoramento/executor.py --status                 # mostra o último estado

Código de saída: 0 = saudável; 1 = alguma etapa falhou ou há verificação em ALERTA.
Nenhuma ação externa é executada (sem bomba, API ou mensagem): o pipeline só gera arquivos.
"""

import argparse
import csv
import html
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "monitoramento"
PASTA_LOGS = PASTA / "logs"
ARQ_LOG = PASTA_LOGS / "agrosmart.log"
ARQ_EVENTOS = PASTA_LOGS / "eventos.jsonl"
ARQ_STATUS = PASTA / "status.json"
ARQ_HISTORICO = PASTA / "historico_execucoes.csv"
ARQ_HTML = PASTA / "status.html"
ARQ_TRAVA = PASTA / ".execucao.lock"

PROC = RAIZ / "dados/processados"
SAIDAS_ESPERADAS = {
    "Processamento": [PROC / "dataset_processado_agrosmart.csv", PROC / "registros_descartados.csv"],
    "Automação": [PROC / "resultado_automacao_agrosmart.csv", PROC / "resumo_talhoes.csv",
                  PROC / "insights_automaticos.csv"],
    "Dashboard": [RAIZ / "dashboard/agrosmart_dashboard.html"],
}

ETAPAS = [
    ("Ingestão TinkerCad", RAIZ / "sensores/ingestao_tinkercad.py"),
    ("Processamento", RAIZ / "src/processamento.py"),
    ("Automação", RAIZ / "src/automacao.py"),
    ("Dashboard", RAIZ / "dashboard/gerar_dashboard.py"),
]

# Limites das verificações de saúde (operacionais, não agronômicos)
LIMITE_DESCARTE_PCT = 5.0       # descartes acima disso indicam problema de coleta
LIMITE_SEM_DADOS_PCT = 5.0      # leituras sem condição de classificar
LIMITE_ALERTA_CAMPO_PCT = 30.0  # muitos alertas ao mesmo tempo merecem atenção humana
LIMITE_DURACAO_S = 60.0         # pipeline lento demais para o volume atual
TRAVA_OBSOLETA_S = 600          # trava com mais de 10 min é considerada abandonada

log = logging.getLogger("agrosmart")


def agora_utc():
    return datetime.now(timezone.utc)


def iso(momento):
    return momento.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- logging

def configurar_logs(pasta_logs=PASTA_LOGS):
    pasta_logs.mkdir(parents=True, exist_ok=True)
    log.handlers.clear()
    log.setLevel(logging.INFO)
    formato = logging.Formatter("[%(asctime)s] %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")
    formato.converter = time.gmtime  # horários do log em UTC
    arquivo = RotatingFileHandler(pasta_logs / "agrosmart.log", maxBytes=500_000,
                                  backupCount=3, encoding="utf-8")
    console = logging.StreamHandler(sys.stdout)
    for handler in (arquivo, console):
        handler.setFormatter(formato)
        log.addHandler(handler)


def registrar_evento(tipo, **campos):
    """Linha JSON por evento: fácil de ler por scripts e ferramentas de log."""
    evento = {"momento": iso(agora_utc()), "evento": tipo, **campos}
    ARQ_EVENTOS.parent.mkdir(parents=True, exist_ok=True)
    with open(ARQ_EVENTOS, "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- execução

def executar_etapa(nome, script, ciclo):
    """Roda um script em processo separado e mede duração e código de retorno."""
    if not Path(script).exists():
        log.error("%s: script não encontrado (%s)", nome, script)
        resultado = {"etapa": nome, "status": "FALHA", "duracao_s": 0.0, "codigo": -1,
                     "erro": "script não encontrado"}
        registrar_evento("etapa", ciclo=ciclo, **resultado)
        return resultado

    inicio = time.monotonic()
    log.info("%s: iniciada", nome)
    processo = subprocess.run([sys.executable, str(script)], cwd=RAIZ, capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
    duracao = round(time.monotonic() - inicio, 2)
    resultado = {"etapa": nome, "duracao_s": duracao, "codigo": processo.returncode}
    if processo.returncode == 0:
        resultado["status"] = "OK"
        log.info("%s: concluída em %.2f s", nome, duracao)
    else:
        resultado["status"] = "FALHA"
        resultado["erro"] = (processo.stderr.strip().splitlines() or ["sem mensagem"])[-1]
        log.error("%s: FALHOU (código %s) em %.2f s - %s", nome, processo.returncode,
                  duracao, resultado["erro"])
    registrar_evento("etapa", ciclo=ciclo, **resultado)
    return resultado


# ---------------------------------------------------------------- indicadores

def calcular_indicadores(raiz=RAIZ):
    """Lê as saídas do pipeline e resume o funcionamento. Vazio se ainda não existem."""
    proc = raiz / "dados/processados"
    try:
        validos = pd.read_csv(proc / "dataset_processado_agrosmart.csv")
        descartes = pd.read_csv(proc / "registros_descartados.csv")
        resultado = pd.read_csv(proc / "resultado_automacao_agrosmart.csv")
    except (FileNotFoundError, pd.errors.EmptyDataError) as erro:
        return {"erro": f"saídas indisponíveis: {erro}"}

    brutas = len(validos) + len(descartes)
    campo = ~resultado["talhao"].str.contains("TinkerCad")
    r_campo = resultado[campo]
    contagem = resultado["nivel_risco"].value_counts()
    contagem_campo = r_campo["nivel_risco"].value_counts()
    alertas_campo = int(contagem_campo.get("Alto", 0) + contagem_campo.get("Moderado", 0))

    ultima = pd.to_datetime(r_campo["data_hora"], utc=True, errors="coerce").max()
    idade_dias = round((pd.Timestamp(agora_utc()) - ultima).total_seconds() / 86400, 1) \
        if pd.notna(ultima) else None

    return {
        "leituras_brutas": brutas,
        "leituras_validas": len(validos),
        "leituras_descartadas": len(descartes),
        "taxa_descarte_pct": round(100 * len(descartes) / brutas, 2) if brutas else 0.0,
        "motivos_descarte": descartes["motivo_descarte"].value_counts().to_dict(),
        "leituras_campo": int(campo.sum()),
        "leituras_bancada": int((~campo).sum()),
        "risco_total": {k: int(v) for k, v in contagem.items()},
        "risco_campo": {k: int(v) for k, v in contagem_campo.items()},
        "alertas_campo": alertas_campo,
        "alertas_campo_pct": round(100 * alertas_campo / max(len(r_campo), 1), 2),
        "sem_dados_pct": round(100 * contagem.get("Sem dados", 0) / max(len(resultado), 1), 2),
        "acoes_automaticas": {k: int(v) for k, v in resultado["acao_automatica"].value_counts().items()},
        "sensores_ativos": int(validos["sensor_id"].nunique()),
        "sensores_com_falha": int((pd.concat([validos["status_sensor"], descartes["status_sensor"]])
                                   != "operacional").sum()),
        "ultima_leitura_campo": iso(ultima) if pd.notna(ultima) else None,
        "idade_dados_dias": idade_dias,
    }


def avaliar_saude(etapas, indicadores, inicio_ciclo, saidas=SAIDAS_ESPERADAS):
    """Lista de verificações [(nome, status, detalhe)]; status: OK, ALERTA ou INFO."""
    verificacoes = []

    falhas = [e["etapa"] for e in etapas if e["status"] == "FALHA"]
    verificacoes.append(("Etapas do pipeline", "ALERTA" if falhas else "OK",
                         f"falharam: {', '.join(falhas)}" if falhas
                         else f"{sum(e['status'] == 'OK' for e in etapas)} etapas concluídas"))

    ausentes = [a.name for lista in saidas.values() for a in lista
                if not a.exists() or a.stat().st_mtime < inicio_ciclo]
    verificacoes.append(("Arquivos de saída atualizados", "ALERTA" if ausentes else "OK",
                         f"ausentes/desatualizados: {', '.join(ausentes)}" if ausentes
                         else "todos gerados neste ciclo"))

    if "erro" in indicadores:
        verificacoes.append(("Leitura dos indicadores", "ALERTA", indicadores["erro"]))
        return verificacoes

    taxa = indicadores["taxa_descarte_pct"]
    verificacoes.append(("Taxa de descarte", "ALERTA" if taxa > LIMITE_DESCARTE_PCT else "OK",
                         f"{taxa:.2f}% (limite {LIMITE_DESCARTE_PCT:.0f}%)"))
    sd = indicadores["sem_dados_pct"]
    verificacoes.append(("Leituras sem dados", "ALERTA" if sd > LIMITE_SEM_DADOS_PCT else "OK",
                         f"{sd:.2f}% (limite {LIMITE_SEM_DADOS_PCT:.0f}%)"))
    al = indicadores["alertas_campo_pct"]
    verificacoes.append(("Leituras de campo em alerta", "ALERTA" if al > LIMITE_ALERTA_CAMPO_PCT else "OK",
                         f"{al:.2f}% (limite {LIMITE_ALERTA_CAMPO_PCT:.0f}%)"))
    duracao = sum(e["duracao_s"] for e in etapas)
    verificacoes.append(("Duração do pipeline", "ALERTA" if duracao > LIMITE_DURACAO_S else "OK",
                         f"{duracao:.2f} s (limite {LIMITE_DURACAO_S:.0f} s)"))
    verificacoes.append(("Atualidade dos dados", "INFO",
                         f"última leitura de campo há {indicadores['idade_dados_dias']} dias "
                         "(base sintética histórica; em produção seria um limite de alerta)"))
    return verificacoes


# ---------------------------------------------------------------- saídas

def gravar_status(ciclo, inicio, fim, etapas, indicadores, verificacoes):
    saudavel = all(v[1] != "ALERTA" for v in verificacoes)
    status = {
        "ciclo": ciclo,
        "inicio": iso(inicio),
        "fim": iso(fim),
        "duracao_total_s": round((fim - inicio).total_seconds(), 2),
        "situacao": "SAUDÁVEL" if saudavel else "ATENÇÃO",
        "etapas": etapas,
        "verificacoes": [{"nome": n, "status": s, "detalhe": d} for n, s, d in verificacoes],
        "indicadores": indicadores,
    }
    ARQ_STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")

    novo = not ARQ_HISTORICO.exists()
    with open(ARQ_HISTORICO, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["ciclo_inicio", "duracao_s", "situacao", "etapas_ok", "leituras_validas",
                        "descartes", "taxa_descarte_pct", "alertas_campo", "alertas_campo_pct"])
        ind = indicadores if "erro" not in indicadores else {}
        w.writerow([iso(inicio), status["duracao_total_s"], status["situacao"],
                    f"{sum(e['status'] == 'OK' for e in etapas)}/{len(etapas)}",
                    ind.get("leituras_validas", ""), ind.get("leituras_descartadas", ""),
                    ind.get("taxa_descarte_pct", ""), ind.get("alertas_campo", ""),
                    ind.get("alertas_campo_pct", "")])
    return status


def gerar_html(status):
    """Painel de status autônomo (HTML + CSS, sem JavaScript ou CDN)."""
    e = html.escape
    cor = {"OK": "#1b7f3b", "ALERTA": "#b3261e", "INFO": "#5f6b7a", "FALHA": "#b3261e"}

    def selo(texto):
        return f'<span class="selo" style="background:{cor.get(texto, "#5f6b7a")}">{e(texto)}</span>'

    linhas_etapas = "".join(
        f"<tr><td>{e(x['etapa'])}</td><td>{selo(x['status'])}</td><td>{x['duracao_s']:.2f} s</td></tr>"
        for x in status["etapas"])
    linhas_verif = "".join(
        f"<tr><td>{e(v['nome'])}</td><td>{selo(v['status'])}</td><td>{e(v['detalhe'])}</td></tr>"
        for v in status["verificacoes"])

    ind = status["indicadores"]
    if "erro" in ind:
        cartoes = f'<p class="erro">{e(ind["erro"])}</p>'
    else:
        itens = [("Leituras válidas", ind["leituras_validas"]),
                 ("Descartes", f"{ind['leituras_descartadas']} ({ind['taxa_descarte_pct']:.2f}%)"),
                 ("Sensores ativos", ind["sensores_ativos"]),
                 ("Alertas em campo", f"{ind['alertas_campo']} ({ind['alertas_campo_pct']:.1f}%)"),
                 ("Risco alto (campo)", ind["risco_campo"].get("Alto", 0)),
                 ("Risco moderado (campo)", ind["risco_campo"].get("Moderado", 0))]
        cartoes = "".join(f'<div class="cartao"><span>{e(str(r))}</span><b>{e(str(v))}</b></div>'
                          for r, v in itens)

    historico = ""
    if ARQ_HISTORICO.exists():
        recentes = pd.read_csv(ARQ_HISTORICO, dtype=str, keep_default_na=False).tail(10).iloc[::-1].replace("", "-")
        historico = "".join(
            f"<tr><td>{e(str(r.ciclo_inicio))}</td><td>{float(r.duracao_s):.2f} s</td>"
            f"<td>{selo('OK' if r.situacao == 'SAUDÁVEL' else 'ALERTA')} {e(str(r.situacao))}</td>"
            f"<td>{e(str(r.etapas_ok))}</td><td>{r.leituras_validas}</td><td>{r.alertas_campo}</td></tr>"
            for r in recentes.itertuples())

    ok = status["situacao"] == "SAUDÁVEL"
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AgroSmart - Status da execução</title>
<style>
body{{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;background:#f4f6f4;color:#1c2a1f}}
main{{max-width:980px;margin:0 auto;padding:24px 16px}}
h1{{margin:0 0 4px;font-size:1.5rem}} h2{{font-size:1.1rem;margin:28px 0 8px}}
.sub{{color:#5f6b7a;margin:0 0 16px}}
.situacao{{display:inline-block;padding:6px 14px;border-radius:6px;color:#fff;font-weight:700;
background:{'#1b7f3b' if ok else '#b3261e'}}}
.cartoes{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:14px}}
.cartao{{background:#fff;border:1px solid #d9e0d9;border-radius:8px;padding:12px}}
.cartao span{{display:block;font-size:.8rem;color:#5f6b7a}} .cartao b{{font-size:1.4rem}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #d9e0d9;border-radius:8px}}
th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid #eef1ee;font-size:.9rem}}
th{{background:#e9eee9}}
.selo{{color:#fff;border-radius:4px;padding:1px 8px;font-size:.75rem;font-weight:700}}
.erro{{color:#b3261e}} footer{{margin-top:28px;color:#5f6b7a;font-size:.8rem}}
</style></head><body><main>
<h1>AgroSmart - Status da execução</h1>
<p class="sub">Ciclo {status['ciclo']} · início {e(status['inicio'])} · duração {status['duracao_total_s']:.2f} s (UTC)</p>
<span class="situacao">{e(status['situacao'])}</span>
<div class="cartoes">{cartoes}</div>
<h2>Etapas do pipeline</h2>
<table><tr><th>Etapa</th><th>Status</th><th>Duração</th></tr>{linhas_etapas}</table>
<h2>Verificações de saúde</h2>
<table><tr><th>Verificação</th><th>Status</th><th>Detalhe</th></tr>{linhas_verif}</table>
<h2>Últimas execuções</h2>
<table><tr><th>Início (UTC)</th><th>Duração</th><th>Situação</th><th>Etapas OK</th><th>Leituras válidas</th><th>Alertas campo</th></tr>{historico}</table>
<footer>Gerado por monitoramento/executor.py. Arquivo estático: reflete o último ciclo executado. Dados de campo sintéticos.</footer>
</main></body></html>"""


# ---------------------------------------------------------------- ciclo

def adquirir_trava():
    """Evita dois ciclos simultâneos (ex.: cron disparando antes do anterior terminar)."""
    PASTA.mkdir(parents=True, exist_ok=True)
    if ARQ_TRAVA.exists() and time.time() - ARQ_TRAVA.stat().st_mtime > TRAVA_OBSOLETA_S:
        log.warning("Trava obsoleta removida (%s)", ARQ_TRAVA.name)
        ARQ_TRAVA.unlink()
    try:
        descritor = os.open(ARQ_TRAVA, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    os.write(descritor, str(os.getpid()).encode())
    os.close(descritor)
    return True


def executar_ciclo(ciclo):
    if not adquirir_trava():
        log.error("Ciclo %d não iniciado: outra execução em andamento (%s)", ciclo, ARQ_TRAVA.name)
        return None
    try:
        inicio = agora_utc()
        marca = time.time()
        log.info("===== Ciclo %d: início da execução do AgroSmart =====", ciclo)
        registrar_evento("ciclo_inicio", ciclo=ciclo)

        etapas = []
        for nome, script in ETAPAS:
            if nome == "Ingestão TinkerCad" and not (RAIZ / "dados/brutos/serial_tinkercad.txt").exists():
                log.warning("%s: sem serial_tinkercad.txt, etapa pulada", nome)
                continue
            etapa = executar_etapa(nome, script, ciclo)
            etapas.append(etapa)
            if etapa["status"] == "FALHA":
                log.error("Pipeline interrompido em '%s'; etapas seguintes não executadas", nome)
                break

        if any(e["status"] == "FALHA" for e in etapas):
            # As saídas em disco seriam de uma execução anterior: não as apresentar como atuais.
            indicadores = {"erro": "indicadores não calculados: pipeline falhou "
                                   "(arquivos em disco são de execução anterior)"}
        else:
            indicadores = calcular_indicadores()
        verificacoes = avaliar_saude(etapas, indicadores, marca)
        for nome, estado, detalhe in verificacoes:
            nivel = {"ALERTA": log.warning, "OK": log.info, "INFO": log.info}[estado]
            nivel("Verificação [%s] %s: %s", estado, nome, detalhe)

        fim = agora_utc()
        status = gravar_status(ciclo, inicio, fim, etapas, indicadores, verificacoes)
        ARQ_HTML.write_text(gerar_html(status), encoding="utf-8")
        registrar_evento("ciclo_fim", ciclo=ciclo, situacao=status["situacao"],
                         duracao_s=status["duracao_total_s"])
        log.info("===== Ciclo %d: %s em %.2f s =====", ciclo, status["situacao"],
                 status["duracao_total_s"])
        return status
    finally:
        ARQ_TRAVA.unlink(missing_ok=True)


def mostrar_status():
    if not ARQ_STATUS.exists():
        print("Nenhuma execução registrada ainda. Rode: python monitoramento/executor.py")
        return 1
    s = json.loads(ARQ_STATUS.read_text(encoding="utf-8"))
    print(f"Situação: {s['situacao']}  (ciclo {s['ciclo']}, {s['inicio']}, {s['duracao_total_s']} s)")
    for et in s["etapas"]:
        print(f"  etapa {et['etapa']:<20} {et['status']:<6} {et['duracao_s']:.2f} s")
    for v in s["verificacoes"]:
        print(f"  [{v['status']:<6}] {v['nome']}: {v['detalhe']}")
    return 0 if s["situacao"] == "SAUDÁVEL" else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Executa e monitora o pipeline AgroSmart.")
    ap.add_argument("--ciclos", type=int, default=1, help="quantidade de ciclos (padrão: 1)")
    ap.add_argument("--intervalo", type=float, default=0, help="segundos entre ciclos")
    ap.add_argument("--continuo", action="store_true", help="repete até Ctrl+C")
    ap.add_argument("--status", action="store_true", help="mostra o último status e sai")
    args = ap.parse_args(argv)

    if args.status:
        return mostrar_status()

    configurar_logs()
    ciclo, pior = 0, 0
    try:
        while True:
            ciclo += 1
            status = executar_ciclo(ciclo)
            if status is None or status["situacao"] != "SAUDÁVEL":
                pior = 1
            if not args.continuo and ciclo >= args.ciclos:
                break
            log.info("Próximo ciclo em %.0f s (Ctrl+C encerra)", args.intervalo)
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        log.info("Execução encerrada pelo usuário após %d ciclo(s)", ciclo)
    return pior


if __name__ == "__main__":
    sys.exit(main())
