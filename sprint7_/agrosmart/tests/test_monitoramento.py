"""Testes do executor e do monitoramento (Fase 7). Rodar após python pipeline.py:
python -m unittest discover -s tests -v
"""
import importlib.util
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("executor", RAIZ / "monitoramento/executor.py")
executor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(executor)

INDICADORES_OK = {
    "taxa_descarte_pct": 0.76, "sem_dados_pct": 0.0, "alertas_campo_pct": 23.33,
    "idade_dias": None, "idade_dados_dias": 80.0, "risco_campo": {"Alto": 38, "Moderado": 46},
}
ETAPAS_OK = [{"etapa": "Processamento", "status": "OK", "duracao_s": 0.3, "codigo": 0}]


def estados(verificacoes):
    return {nome: estado for nome, estado, _ in verificacoes}


class VerificacoesDeSaude(unittest.TestCase):
    def setUp(self):
        self.inicio = time.time() - 3600  # saídas do pipeline são mais novas que isso
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.arquivo = Path(self.dir.name) / "saida.csv"
        self.arquivo.write_text("x")
        self.saidas = {"Etapa": [self.arquivo]}

    def avaliar(self, etapas=ETAPAS_OK, indicadores=INDICADORES_OK, inicio=None):
        return estados(executor.avaliar_saude(etapas, indicadores, inicio or self.inicio, self.saidas))

    def test_execucao_saudavel(self):
        r = self.avaliar()
        self.assertFalse([n for n, e in r.items() if e == "ALERTA"])
        self.assertEqual(r["Atualidade dos dados"], "INFO")

    def test_etapa_com_falha_gera_alerta(self):
        falha = ETAPAS_OK + [{"etapa": "Automação", "status": "FALHA", "duracao_s": 0.1, "codigo": 1}]
        self.assertEqual(self.avaliar(falha)["Etapas do pipeline"], "ALERTA")

    def test_saida_desatualizada_gera_alerta(self):
        # início do ciclo posterior à última modificação do arquivo
        self.assertEqual(self.avaliar(inicio=time.time() + 60)["Arquivos de saída atualizados"], "ALERTA")

    def test_saida_ausente_gera_alerta(self):
        self.arquivo.unlink()
        self.assertEqual(self.avaliar()["Arquivos de saída atualizados"], "ALERTA")

    def test_limites_operacionais(self):
        for campo, verificacao in (("taxa_descarte_pct", "Taxa de descarte"),
                                   ("sem_dados_pct", "Leituras sem dados"),
                                   ("alertas_campo_pct", "Leituras de campo em alerta")):
            with self.subTest(campo=campo):
                ruim = {**INDICADORES_OK, campo: 99.0}
                self.assertEqual(self.avaliar(indicadores=ruim)[verificacao], "ALERTA")

    def test_limite_exato_nao_alerta(self):
        no_limite = {**INDICADORES_OK, "taxa_descarte_pct": executor.LIMITE_DESCARTE_PCT}
        self.assertEqual(self.avaliar(indicadores=no_limite)["Taxa de descarte"], "OK")

    def test_pipeline_lento(self):
        lento = [{"etapa": "Processamento", "status": "OK", "duracao_s": 61.0, "codigo": 0}]
        self.assertEqual(self.avaliar(lento)["Duração do pipeline"], "ALERTA")

    def test_indicadores_indisponiveis(self):
        r = self.avaliar(indicadores={"erro": "saídas indisponíveis"})
        self.assertEqual(r["Leitura dos indicadores"], "ALERTA")


class ExecucaoDeEtapas(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        p = patch.object(executor, "ARQ_EVENTOS", Path(self.dir.name) / "eventos.jsonl")
        p.start()
        self.addCleanup(p.stop)

    def script(self, conteudo):
        caminho = Path(self.dir.name) / "etapa.py"
        caminho.write_text(conteudo, encoding="utf-8")
        return caminho

    def test_etapa_ok(self):
        r = executor.executar_etapa("Teste", self.script("print('ok')"), 1)
        self.assertEqual((r["status"], r["codigo"]), ("OK", 0))

    def test_etapa_com_erro_registra_mensagem(self):
        r = executor.executar_etapa("Teste", self.script("raise ValueError('coluna ausente')"), 1)
        self.assertEqual(r["status"], "FALHA")
        self.assertIn("coluna ausente", r["erro"])

    def test_script_inexistente(self):
        r = executor.executar_etapa("Teste", Path(self.dir.name) / "nao_existe.py", 1)
        self.assertEqual(r["status"], "FALHA")

    def test_evento_jsonl_gravado(self):
        executor.executar_etapa("Teste", self.script("pass"), 7)
        linha = executor.ARQ_EVENTOS.read_text(encoding="utf-8").strip()
        self.assertIn('"ciclo": 7', linha)
        self.assertIn('"etapa": "Teste"', linha)


class TravaDeExecucao(unittest.TestCase):
    def test_segunda_execucao_simultanea_e_bloqueada(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(executor, "PASTA", Path(d)), \
                 patch.object(executor, "ARQ_TRAVA", Path(d) / ".lock"):
                self.assertTrue(executor.adquirir_trava())
                self.assertFalse(executor.adquirir_trava())
                executor.ARQ_TRAVA.unlink()
                self.assertTrue(executor.adquirir_trava())

    def test_trava_obsoleta_e_removida(self):
        with tempfile.TemporaryDirectory() as d:
            trava = Path(d) / ".lock"
            trava.write_text("1")
            antigo = time.time() - executor.TRAVA_OBSOLETA_S - 5
            import os
            os.utime(trava, (antigo, antigo))
            with patch.object(executor, "PASTA", Path(d)), patch.object(executor, "ARQ_TRAVA", trava):
                self.assertTrue(executor.adquirir_trava())


class IndicadoresEPainel(unittest.TestCase):
    def test_indicadores_batem_com_pipeline(self):
        ind = executor.calcular_indicadores()
        self.assertEqual((ind["leituras_brutas"], ind["leituras_validas"], ind["leituras_descartadas"]),
                         (397, 394, 3))
        self.assertEqual(ind["taxa_descarte_pct"], 0.76)
        self.assertEqual((ind["leituras_campo"], ind["leituras_bancada"]), (360, 34))
        self.assertEqual((ind["risco_campo"]["Alto"], ind["risco_campo"]["Moderado"]), (38, 46))
        self.assertEqual(ind["alertas_campo"], 84)
        self.assertEqual(ind["alertas_campo_pct"], 23.33)

    def test_indicadores_sem_saidas(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIn("erro", executor.calcular_indicadores(Path(d)))

    def test_painel_html_autonomo_e_escapado(self):
        status = {"ciclo": 1, "inicio": "2026-01-01T00:00:00Z", "duracao_total_s": 1.0,
                  "situacao": "ATENÇÃO", "etapas": [{"etapa": "<b>x</b>", "status": "FALHA", "duracao_s": 0.1}],
                  "verificacoes": [{"nome": "n", "status": "ALERTA", "detalhe": "<script>alert(1)</script>"}],
                  "indicadores": {"erro": "falhou"}}
        pagina = executor.gerar_html(status)
        self.assertNotIn("<script", pagina)
        self.assertNotIn("http://", pagina)
        self.assertNotIn("https://", pagina)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", pagina)


if __name__ == "__main__":
    unittest.main()
