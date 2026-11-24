"""
AgroSmart - Parte 5: dashboard analítico.

Lê os arquivos gerados pela automação e monta um dashboard HTML
(dashboard/agrosmart_dashboard.html) com quatro seções: visão geral,
monitoramento ambiental, alertas e recomendações, e insights automáticos.

O HTML inclui gráficos SVG, tabelas e dados; abre offline sem bibliotecas,
JavaScript ou serviços externos. Roda sozinho ou ao final de pipeline.py.

Uso:
    python dashboard/gerar_dashboard.py
"""

import math
from html import escape
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PROCESSADOS = RAIZ / "dados/processados"
SAIDA = RAIZ / "dashboard/agrosmart_dashboard.html"

CORES_TALHAO = ["#2e7d32", "#1565c0", "#e65100", "#6a1b9a", "#00838f"]
CORES_RISCO = {"Normal": "#43a047", "Moderado": "#f9a825", "Alto": "#e53935"}


def carregar():
    resultado = pd.read_csv(PROCESSADOS / "resultado_automacao_agrosmart.csv")
    resultado["data_hora"] = pd.to_datetime(resultado["data_hora"], utc=True)
    resumo = pd.read_csv(PROCESSADOS / "resumo_talhoes.csv")
    insights = pd.read_csv(PROCESSADOS / "insights_automaticos.csv")
    return resultado, resumo, insights


def montar_dados(resultado, resumo, insights):
    # Monitoramento: só os talhões de campo têm série diária (o TinkerCad é uma bancada de teste)
    campo = resultado[~resultado["talhao"].str.contains("TinkerCad")].copy()
    campo["dia"] = campo["data_hora"].dt.strftime("%Y-%m-%d")
    dias = sorted(campo["dia"].unique())

    umidade_series, temperatura_series = [], []
    for i, (talhao, grupo) in enumerate(campo.groupby("talhao")):
        por_dia = grupo.groupby("dia")
        umid = por_dia["umidade_solo_pct"].mean().reindex(dias)
        temp = por_dia["temperatura_solo_c"].mean().reindex(dias)
        cor = CORES_TALHAO[i % len(CORES_TALHAO)]
        umidade_series.append({"label": talhao, "data": [None if pd.isna(v) else round(v, 1) for v in umid], "cor": cor})
        temperatura_series.append({"label": talhao, "data": [None if pd.isna(v) else round(v, 1) for v in temp], "cor": cor})

    # Alertas por talhão (empilhado por nível de risco)
    talhoes = list(resumo["talhao"])
    riscos = []
    for risco in ["Normal", "Moderado", "Alto"]:
        contagem = resultado[resultado["nivel_risco"] == risco].groupby("talhao").size()
        riscos.append({"label": risco, "data": [int(contagem.get(t, 0)) for t in talhoes], "cor": CORES_RISCO[risco]})

    # Últimos alertas de risco alto (tabela)
    alertas = campo[campo["nivel_risco"] == "Alto"].sort_values("data_hora", ascending=False).head(12)
    tabela = [
        {
            "data": r["data_hora"].strftime("%d/%m/%Y %H:%M"),
            "talhao": r["talhao"],
            "umidade": r["umidade_solo_pct"],
            "temperatura": r["temperatura_solo_c"],
            "alerta": r["tipo_alerta"],
            "acao": r["acao_automatica"],
            "recomendacao": r["recomendacao"],
        }
        for _, r in alertas.iterrows()
    ]

    # Indicadores da fazenda (campo); a bancada do TinkerCad aparece à parte
    total = len(campo)
    alto = int((campo["nivel_risco"] == "Alto").sum())
    moderado = int((campo["nivel_risco"] == "Moderado").sum())
    kpis = {
        "leituras": total,
        "talhoes": int(campo["talhao"].nunique()),
        "bancada": int(len(resultado) - len(campo)),
        "umidade_media": round(campo["umidade_solo_pct"].mean(), 1),
        "temperatura_media": round(campo["temperatura_solo_c"].mean(), 1),
        "alertas_alto": alto,
        "alertas_moderado": moderado,
        "pct_alerta": round(100 * (alto + moderado) / total),
        "periodo": f"{campo['data_hora'].min():%d/%m/%Y} a {campo['data_hora'].max():%d/%m/%Y}",
    }

    return {
        "kpis": kpis,
        "dias": dias,
        "umidade": umidade_series,
        "temperatura": temperatura_series,
        "talhoes": talhoes,
        "riscos": riscos,
        "tabela": tabela,
        "resumo": resumo.fillna("").to_dict(orient="records"),
        "insights": insights.to_dict(orient="records"),
    }


MODELO = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AgroSmart - Dashboard Analítico</title>
<style>
  :root { --verde:#2e7d32; --fundo:#f4f6f3; --card:#fff; --texto:#1f2a1f; --sutil:#5f6b5f; --borda:#dde3dc; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:"Segoe UI",Arial,sans-serif; background:var(--fundo); color:var(--texto); }
  header { background:var(--verde); color:#fff; padding:18px 28px; }
  header h1 { margin:0; font-size:24px; }
  header p { margin:4px 0 0; opacity:.85; font-size:14px; }
  main { max-width:1280px; margin:0 auto; padding:20px; }
  section { margin-bottom:28px; }
  h2 { font-size:18px; margin:0 0 12px; color:var(--verde); border-bottom:2px solid var(--borda); padding-bottom:6px; }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; }
  .kpi { background:var(--card); border:1px solid var(--borda); border-radius:10px; padding:14px 16px; }
  .kpi .rotulo { font-size:13px; color:var(--sutil); }
  .kpi .valor { font-size:28px; font-weight:700; margin-top:4px; }
  .kpi.alerta .valor { color:#e53935; }
  .kpi.atencao .valor { color:#f9a825; }
  .grade { display:grid; grid-template-columns:repeat(auto-fit,minmax(480px,1fr)); gap:16px; }
  .painel { background:var(--card); border:1px solid var(--borda); border-radius:10px; padding:14px; }
  .painel h3 { margin:0 0 8px; font-size:15px; }
  .painel svg { display:block; width:100%; height:auto; }
  .tabela-scroll { overflow-x:auto; }
  .nota { color:var(--sutil); font-size:13px; line-height:1.5; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th, td { text-align:left; padding:7px 8px; border-bottom:1px solid var(--borda); }
  th { background:#eef3ec; }
  .insights { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:12px; }
  .insight { background:var(--card); border-left:5px solid var(--verde); border-radius:8px; padding:12px 14px; }
  .insight b { display:block; margin-bottom:4px; }
  footer { text-align:center; font-size:12px; color:var(--sutil); padding:16px; }
  @media (max-width:560px){ .grade{ grid-template-columns:1fr; } }
</style>
</head>
<body>
<header>
  <h1>AgroSmart — Dashboard Analítico</h1>
  <p>Fazenda Pedralva · soja · __PERIODO__ · gerado automaticamente pelo pipeline</p>
</header>
<main>
  <section>
    <h2>1. Visão geral</h2>
    <div class="kpis">__KPIS__</div>
    <p class="nota">Cenário didático com dados de campo sintéticos. Indicadores e séries temporais de campo excluem a bancada TinkerCad. Horários exibidos em UTC. Painel estático: rode o pipeline e reabra o arquivo para atualizar.</p>
  </section>

  <section>
    <h2>2. Monitoramento ambiental</h2>
    <div class="grade">
      <div class="painel"><h3>Umidade do solo por talhão (%)</h3>__UMIDADE__</div>
      <div class="painel"><h3>Temperatura do solo por talhão (°C)</h3>__TEMPERATURA__</div>
    </div>
  </section>

  <section>
    <h2>3. Alertas e recomendações</h2>
    <div class="grade">
      <div class="painel"><h3>Leituras por nível de risco e talhão (inclui bancada)</h3>__RISCOS__</div>
      <div class="painel"><h3>Resumo por talhão (inclui bancada)</h3><div class="tabela-scroll">__RESUMO__</div></div>
    </div>
    <div class="painel" style="margin-top:16px"><h3>Últimos alertas de risco alto (talhões de campo)</h3><div class="tabela-scroll">__ALERTAS__</div><p class="nota">Ação automática é a saída do motor de regras em CSV. Este protótipo não executa comandos de irrigação nem envia notificações. Talhão irrigado = recebeu irrigação em algum momento do período; não é um cadastro de atuadores.</p></div>
  </section>

  <section>
    <h2>4. Insights automáticos</h2>
    <div class="insights">__INSIGHTS__</div>
  </section>
</main>
<footer>Dados de campo sintéticos (cenário da Fase 5) + leituras simuladas no TinkerCad. Regras didáticas: Alto se umidade &lt; 18% ou temperatura ≥ 35 °C; Moderado se umidade &lt; 22% ou temperatura ≥ 30 °C. Não são uma prescrição agronômica.</footer>
</body>
</html>
"""


def grafico_linhas(dias, series, limites, titulo):
    """SVG autônomo: datas e unidades explícitas, lacunas não interpoladas."""
    largura, altura = 620, 365
    esquerda, direita, topo, base = 45, 605, 20, 265
    valores = [v for s in series for v in s["data"] if v is not None]
    valores += [limite["valor"] for limite in limites]
    minimo = min(0, min(valores, default=0))
    maximo = max(5, math.ceil(max(valores, default=5) / 5) * 5)
    def x(i):
        return esquerda + i * (direita - esquerda) / max(1, len(dias) - 1)

    def y(v):
        return base - (v - minimo) * (base - topo) / (maximo - minimo)

    partes = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {altura}" role="img" aria-label="{escape(titulo)}"><title>{escape(titulo)}</title><g font-family="Segoe UI,Arial,sans-serif" font-size="11" fill="#5f6b5f">']
    for i in range(6):
        valor = minimo + (maximo - minimo) * i / 5
        partes.append(f'<line x1="{esquerda}" x2="{direita}" y1="{y(valor):.1f}" y2="{y(valor):.1f}" stroke="#dde3dc"/><text x="{esquerda-7}" y="{y(valor)+4:.1f}" text-anchor="end">{valor:g}</text>')
    passo = max(1, math.ceil(len(dias) / 8))
    indices = list(range(0, len(dias), passo))
    if dias and indices[-1] != len(dias) - 1:
        if len(dias) - 1 - indices[-1] < passo * 0.6:
            indices.pop()
        indices.append(len(dias) - 1)
    for i in indices:
        dia = dias[i]
        partes.append(f'<text x="{x(i):.1f}" y="285" text-anchor="middle">{dia[8:10]}/{dia[5:7]}</text>')
    for serie in series:
        segmentos, pontos = [], []
        for i, valor in enumerate(serie["data"]):
            if valor is None:
                if pontos:
                    segmentos.append(pontos)
                pontos = []
            else:
                pontos.append(f"{x(i):.1f},{y(valor):.1f}")
        if pontos:
            segmentos.append(pontos)
        for segmento in segmentos:
            partes.append(f'<polyline points="{" ".join(segmento)}" fill="none" stroke="{serie["cor"]}" stroke-width="2"><title>{escape(serie["label"])}</title></polyline>')
    for limite in limites:
        partes.append(f'<line x1="{esquerda}" x2="{direita}" y1="{y(limite["valor"]):.1f}" y2="{y(limite["valor"]):.1f}" stroke="{limite["cor"]}" stroke-dasharray="6 4"/>')
    for i, serie in enumerate(series + limites):
        coluna, linha = i % 2, i // 2
        lx, ly = 45 + coluna * 280, 307 + linha * 20
        partes.append(f'<line x1="{lx}" x2="{lx+16}" y1="{ly}" y2="{ly}" stroke="{serie["cor"]}" stroke-width="3"/><text x="{lx+22}" y="{ly+4}">{escape(serie["label"])}</text>')
    return "".join(partes) + "</g></svg>"


def grafico_riscos(dados):
    esquerda, direita = 220, 600
    maximo = max(sum(r["data"][i] for r in dados["riscos"]) for i in range(len(dados["talhoes"])))
    maximo = max(maximo, 1)
    partes = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 365" role="img" aria-label="Leituras por risco e talhão"><title>Leituras por risco e talhão, incluindo bancada</title><g font-family="Segoe UI,Arial,sans-serif" font-size="11" fill="#5f6b5f">']
    for i, talhao in enumerate(dados["talhoes"]):
        topo, inicio = 25 + i * 48, esquerda
        partes.append(f'<text x="{esquerda-8}" y="{topo+21}" text-anchor="end">{escape(talhao)}</text>')
        for risco in dados["riscos"]:
            valor = risco["data"][i]
            largura = valor * (direita - esquerda) / maximo
            partes.append(f'<rect x="{inicio:.1f}" y="{topo}" width="{largura:.1f}" height="32" fill="{risco["cor"]}"><title>{escape(talhao)} — {risco["label"]}: {valor}</title></rect>')
            if largura > 25:
                partes.append(f'<text x="{inicio+largura/2:.1f}" y="{topo+21}" text-anchor="middle" fill="#111">{valor}</text>')
            inicio += largura
    for i in range(6):
        valor = maximo * i / 5
        pos = esquerda + i * (direita - esquerda) / 5
        partes.append(f'<text x="{pos:.1f}" y="282" text-anchor="middle">{valor:g}</text>')
    partes.append('<text x="410" y="305" text-anchor="middle">Quantidade de leituras</text>')
    for i, risco in enumerate(dados["riscos"]):
        lx = 225 + i * 115
        partes.append(f'<rect x="{lx}" y="325" width="12" height="12" fill="{risco["cor"]}"/><text x="{lx+18}" y="336">{risco["label"]}</text>')
    return "".join(partes) + "</g></svg>"


def tabela(cabecalhos, linhas):
    return ("<table><thead><tr>" + "".join(f'<th scope="col">{escape(c)}</th>' for c in cabecalhos)
            + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{escape(str(v))}</td>" for v in linha) + "</tr>" for linha in linhas) + "</tbody></table>")


def renderizar(dados):
    k = dados["kpis"]
    kpis = [
        ("Leituras de campo", k["leituras"], ""),
        ("Talhões monitorados", k["talhoes"], ""),
        ("Umidade média do solo", f'{k["umidade_media"]}%', ""),
        ("Temperatura média do solo", f'{k["temperatura_media"]} °C', ""),
        ("Alertas de risco alto", k["alertas_alto"], "alerta"),
        ("Alertas de risco moderado", k["alertas_moderado"], "atencao"),
        ("Leituras com alerta", f'{k["pct_alerta"]}%', ""),
        ("Leituras do TinkerCad (bancada)", k["bancada"], ""),
    ]
    substituicoes = {
        "__PERIODO__": escape(k["periodo"]),
        "__KPIS__": "".join(f'<div class="kpi {cor}"><div class="rotulo">{rotulo}</div><div class="valor">{escape(str(valor))}</div></div>' for rotulo, valor, cor in kpis),
        "__UMIDADE__": grafico_linhas(dados["dias"], dados["umidade"], [{"label":"Crítico (18%)", "valor":18, "cor":"#e53935"}, {"label":"Gatilho (22%)", "valor":22, "cor":"#f9a825"}], "Umidade do solo (%) — médias diárias de campo"),
        "__TEMPERATURA__": grafico_linhas(dados["dias"], dados["temperatura"], [{"label":"Atenção (30 °C)", "valor":30, "cor":"#f9a825"}, {"label":"Alto (35 °C)", "valor":35, "cor":"#e53935"}], "Temperatura do solo (°C) — médias diárias de campo"),
        "__RISCOS__": grafico_riscos(dados),
        "__RESUMO__": tabela(["Talhão", "Irrigado", "Umidade média", "Umidade mínima", "Alertas alto", "Sequência crítica (leituras)"], [[r["talhao"], r["irrigado"], f'{r["umidade_media_pct"]}%', f'{r["umidade_minima_pct"]}%', r["alertas_alto"], r["maior_sequencia_critica"]] for r in dados["resumo"]]),
        "__ALERTAS__": tabela(["Data (UTC)", "Talhão", "Umidade", "Temp.", "Alerta", "Ação proposta", "Recomendação"], [[r["data"], r["talhao"], f'{r["umidade"]}%', f'{r["temperatura"]} °C', r["alerta"], r["acao"], r["recomendacao"]] for r in dados["tabela"]]),
        "__INSIGHTS__": "".join(f'<div class="insight"><b>{escape(i["indicador"])}</b>{escape(i["texto"])}</div>' for i in dados["insights"]),
    }
    html = MODELO
    for marcador, conteudo in substituicoes.items():
        html = html.replace(marcador, conteudo)
    return html


def main():
    resultado, resumo, insights = carregar()
    dados = montar_dados(resultado, resumo, insights)
    html = renderizar(dados)
    SAIDA.write_text(html, encoding="utf-8")
    print("Dashboard gerado:", SAIDA.relative_to(RAIZ))


if __name__ == "__main__":
    main()
