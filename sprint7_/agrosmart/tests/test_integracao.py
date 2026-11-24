"""Contratos, limites de risco e integração. Rodar após python pipeline.py:
python -m unittest discover -s tests -v
"""
import copy
import importlib.util
import random
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]


def importar(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


processamento = importar("processamento", "src/processamento.py")
automacao = importar("automacao", "src/automacao.py")
ingestao = importar("ingestao", "sensores/ingestao_tinkercad.py")
dashboard = importar("dashboard", "dashboard/gerar_dashboard.py")
gerador = importar("gerador", "dados/brutos/gerar_dataset.py")
empacotador = importar("empacotador", "entrega/montar_zip.py")


class ContratosDeDados(unittest.TestCase):
    def test_base_entregue_e_descartes(self):
        brutos = pd.read_csv(RAIZ / "dados/brutos/leituras_sensores.csv")
        bancada = pd.read_csv(RAIZ / "dados/brutos/leituras_tinkercad.csv")
        validos, descartes = processamento.processar(pd.concat([brutos, bancada], ignore_index=True))
        self.assertEqual((len(brutos), len(bancada), len(validos), len(descartes)), (363, 34, 394, 3))
        self.assertEqual(set(descartes["motivo_descarte"]), {"duplicata", "fora do limite físico", "sensor sem medição"})
        self.assertFalse(validos["data_hora"].isna().any())

    def test_datas_e_identificadores_invalidos(self):
        base = pd.read_csv(RAIZ / "dados/brutos/leituras_sensores.csv").iloc[[0]].copy()
        for coluna, valor, motivo in [("data_hora", "impossivel", "data/hora inválida"), ("sensor_id", " ", "identificação ausente"), ("talhao", None, "identificação ausente")]:
            with self.subTest(coluna=coluna):
                dado = base.copy()
                dado[coluna] = valor
                validos, descartes = processamento.processar(dado)
                self.assertEqual(len(validos), 0)
                self.assertEqual(descartes.iloc[0]["motivo_descarte"], motivo)

    def test_limites_fisicos(self):
        base = pd.read_csv(RAIZ / "dados/brutos/leituras_sensores.csv").iloc[[0]].copy()
        for coluna, valor, esperado in [("umidade_solo_pct", 0, 1), ("umidade_solo_pct", 100, 1), ("umidade_solo_pct", -0.1, 0), ("umidade_solo_pct", 100.1, 0), ("temperatura_solo_c", -10, 1), ("temperatura_solo_c", 60, 1), ("temperatura_solo_c", -10.1, 0), ("temperatura_solo_c", 60.1, 0)]:
            with self.subTest(coluna=coluna, valor=valor):
                dado = base.copy()
                dado[coluna] = valor
                self.assertEqual(len(processamento.processar(dado)[0]), esperado)

    def test_coluna_ausente_falha_explicitamente(self):
        with self.assertRaisesRegex(ValueError, "colunas obrigatórias"):
            processamento.processar(pd.DataFrame({"sensor_id": ["x"]}))

    def test_gerador_reproduz_campos_csv(self):
        rng = random.Random(gerador.SEMENTE)
        clima = gerador.gerar_clima(rng)
        leituras = gerador.gerar_leituras(rng, clima)
        gerador.sujar(leituras)
        produtividade = gerador.gerar_produtividade(rng)
        for arquivo, linhas in [("clima_estacao.csv", clima), ("leituras_sensores.csv", leituras), ("produtividade_talhoes.csv", produtividade)]:
            with self.subTest(arquivo=arquivo):
                pd.testing.assert_frame_equal(pd.read_csv(RAIZ / "dados/brutos" / arquivo), pd.DataFrame(linhas).replace("", float("nan")), check_dtype=False)


class RegrasEAcoes(unittest.TestCase):
    def test_limites_risco_e_dados_parciais(self):
        sketch = (RAIZ / "sensores/tinkercad/agrosmart_sensores.ino").read_text(encoding="utf-8")
        for constante in ["UMIDADE_CRITICA", "UMIDADE_BAIXA", "TEMPERATURA_ALTA", "TEMPERATURA_ATENCAO"]:
            valor = float(re.search(rf"const float {constante} = ([0-9.]+);", sketch).group(1))
            self.assertEqual(valor, getattr(automacao, constante))
        for u, t, risco in [(17.9, 25, "Alto"), (18, 25, "Moderado"), (21.9, 25, "Moderado"), (22, 29.9, "Normal"), (40, 30, "Moderado"), (40, 34.9, "Moderado"), (40, 35, "Alto"), (None, 25, "Sem dados"), (None, 35, "Alto"), (40, None, "Sem dados"), (None, None, "Sem dados")]:
            with self.subTest(u=u, t=t):
                self.assertEqual(automacao.classificar_risco(pd.Series({"umidade_solo_pct": u, "temperatura_solo_c": t})), risco)

    def test_saida_dos_dois_caminhos_de_acao(self):
        self.assertEqual(automacao.definir_acao({"nivel_risco":"Alto", "talhao_irrigado":True}), "Acionar irrigação")
        self.assertEqual(automacao.definir_acao({"nivel_risco":"Alto", "talhao_irrigado":False}), "Notificar produtor")
        self.assertEqual(automacao.definir_acao({"nivel_risco":"Sem dados", "talhao_irrigado":False}), "Verificar sensor")
        self.assertIn("Talhão sem irrigação", automacao.gerar_recomendacao({"nivel_risco":"Moderado", "talhao_irrigado":False, "umidade_solo_pct":20}))

    def test_serial_e_python_concordam(self):
        linhas = (RAIZ / "dados/brutos/serial_tinkercad.txt").read_text(encoding="utf-8").splitlines()[1:]
        self.assertEqual(len(linhas), 34)
        for linha in linhas:
            sensor, umidade, temperatura, esperado = linha.split(",")
            self.assertEqual(automacao.classificar_risco({"umidade_solo_pct":float(umidade), "temperatura_solo_c":float(temperatura)}), esperado)

    def test_ingestao_rejeita_linhas_malformadas(self):
        with tempfile.TemporaryDirectory() as pasta:
            serial = Path(pasta) / "serial.txt"
            serial.write_text("sensor_id,umidade_solo_pct,temperatura_solo_c,nivel_risco\nx,20,25,Moderado\nx,nan,25,Normal\nx,20,inf,Alto\n,20,25,Normal\nx,20,25\n", encoding="utf-8")
            with patch.object(ingestao, "arquivo_serial", serial):
                leituras, ignoradas = ingestao.ler_serial()
            self.assertEqual(leituras, [("x", 20.0, 25.0)])
            self.assertEqual(ignoradas, 5)


class IntegracaoDoPainel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resultado, cls.resumo, cls.insights = dashboard.carregar()
        cls.dados = dashboard.montar_dados(cls.resultado, cls.resumo, cls.insights)

    def test_totais_campo_e_bancada(self):
        k = self.dados["kpis"]
        self.assertEqual((k["leituras"], k["bancada"], k["talhoes"], k["alertas_alto"], k["alertas_moderado"]), (360, 34, 4, 38, 46))
        self.assertEqual(self.resultado["nivel_risco"].value_counts().to_dict(), {"Normal":289, "Moderado":56, "Alto":49})
        self.assertEqual(k["umidade_media"], 32.1)
        self.assertEqual(k["pct_alerta"], 23)
        self.assertEqual(len(self.dados["dias"]), 90)
        self.assertEqual(len(self.dados["tabela"]), 12)
        self.assertEqual(len(self.dados["insights"]), 5)
        self.assertTrue(all("TinkerCad" not in r["talhao"] for r in self.dados["tabela"]))

    def test_html_offline_e_svg_validos(self):
        html = dashboard.renderizar(self.dados)
        self.assertNotIn("<script", html)
        self.assertNotIn("https://", html)
        self.assertNotRegex(html, r"__[A-Z_]+__")
        svgs = re.findall(r"<svg\b.*?</svg>", html, re.S)
        self.assertEqual(len(svgs), 3)
        for svg in svgs:
            ET.fromstring(svg)
        self.assertEqual((RAIZ / "dashboard/agrosmart_dashboard.html").read_text(encoding="utf-8"), html)

    def test_texto_externo_escapado(self):
        dados = copy.deepcopy(self.dados)
        dados["insights"][0]["texto"] = "<script>alert('x')</script>"
        self.assertNotIn("<script", dashboard.renderizar(dados))
        self.assertIn("&lt;script&gt;", dashboard.renderizar(dados))

    def test_conteudo_empacotador_e_prefixo(self):
        with self.assertRaises(ValueError):
            empacotador.montar("../fora")
        arquivos = empacotador.listar_arquivos(RAIZ)
        self.assertTrue(any(p.name == "PITCH.md" for p in arquivos))
        self.assertTrue(any(p.name == "executor.py" for p in arquivos))
        self.assertTrue(any(p.name == ".dockerignore" for p in arquivos))
        self.assertTrue(any(p.name == "ci.yml" for p in arquivos))
        self.assertFalse(any(p.name == ".execucao.lock" for p in arquivos))
        self.assertTrue(any(p.name == "dashboard.pbix" for p in arquivos))
        self.assertFalse(any(p.suffix in {".zip", ".pyc"} or "__pycache__" in p.parts for p in arquivos))
        with tempfile.TemporaryDirectory() as pasta:
            with self.assertRaisesRegex(FileNotFoundError, "Item obrigatório ausente"):
                empacotador.listar_arquivos(Path(pasta))


if __name__ == "__main__":
    unittest.main()
