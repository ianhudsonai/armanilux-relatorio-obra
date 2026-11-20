"""Fato sem dia exato: quando o grupo só mostra que aconteceu entre duas datas ("entrega programada
para 09/06; em 11/06, 'na última entrega'"), o relatório diz a faixa e conta os dias úteis como
faixa (30–32 d.u.), em vez de escolher uma data que o grupo não dá."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import aplicar_ajustes, completar_relato, confronto_contrato, faixas_dos_marcos, primeiros_marcos  # noqa: E402


def _evento(data: str, etapa: str, ocorrencia: str = "x", **extra) -> dict:
    base = {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": ocorrencia, "impacto": "", "midias": [], "documentos": []}
    base.update(extra)
    return base


ENTREGA = _evento("2026-06-11", "H", "Banhos: entrega anterior já feita.", data_evento="2026-06-09", data_evento_ate="2026-06-11")
EVENTOS = [_evento("2026-04-24", "G", "Banhos aprovados."), ENTREGA, _evento("2026-06-15", "I", "Equipe na obra.")]


def _word(relato: dict):
    from docx import Document

    import build_docx

    with TemporaryDirectory() as pasta:
        return Document(str(build_docx.montar_docx(relato, Path(pasta) / "r.docx", None, None)))


def _texto(documento) -> str:
    partes = [p.text for p in documento.paragraphs]
    for tabela in documento.tables:
        partes.extend(" | ".join(c.text for c in linha.cells) for linha in tabela.rows)
    return "\n".join(partes)


class FaixaTeste(unittest.TestCase):
    def test_marco_tem_faixa_e_a_primeira_data_e_o_inicio(self):
        self.assertEqual(faixas_dos_marcos(EVENTOS)["H"], ("2026-06-09", "2026-06-11"))
        self.assertEqual(primeiros_marcos(EVENTOS)["H"], "2026-06-09")

    def test_outro_fato_com_dia_certo_encurta_a_faixa(self):
        outro = _evento("2026-06-10", "H", "Segunda entrega.")
        self.assertEqual(faixas_dos_marcos(EVENTOS + [outro])["H"], ("2026-06-09", "2026-06-10"))

    def test_intervalos_saem_em_faixa(self):
        relato = completar_relato({"obra": {}, "eventos": EVENTOS})
        intervalos = {(m["de"], m["para"]): (m["dias_uteis"], m["dias_uteis_max"]) for m in relato["intervalos_marcos"]}
        self.assertEqual(intervalos, {("G", "H"): (30, 32), ("H", "I"): (2, 4)})

    def test_confronto_em_faixa_nao_afirma_estouro(self):
        prazos = [{"descricao": "Bancadas: aprovação → início da entrega", "inicio": "2026-09-21", "fim": "2026-11-10", "fim_ate": "2026-11-16", "limite_du": 35, "fonte_data": "2025-08-29"}]
        item = confronto_contrato([], prazos)[0]
        self.assertEqual((item["realizado"], item["realizado_max"], item["excedeu"], item["talvez"]), (34, 38, False, True))

    def test_word_mostra_a_faixa(self):
        prazos = [{"descricao": "Banhos: aprovação → entrega", "de": "G", "para": "H", "limite_du": 25, "fonte_data": "2025-08-29"}]
        texto = _texto(_word(completar_relato({"obra": {}, "eventos": EVENTOS, "prazos_contratuais": prazos})))
        self.assertIn("H – Data das entregas dos materiais na obra (09/06/2026 a 11/06/2026) | 30–32 d.u.", texto)
        self.assertIn("Primeira entrega na obra | entre 09/06/2026 e 11/06/2026", texto)
        self.assertIn("Banhos: entrega anterior já feita. (fato entre 09/06/2026 e 11/06/2026)", texto)
        self.assertIn("30–32 d.u.", texto.split("Prazo contratual de referência")[1])

    def test_grafico_desenha_a_faixa(self):
        from build_charts import _dia_mes_ano, grafico_barras

        relato = completar_relato({"obra": {}, "eventos": EVENTOS})
        with TemporaryDirectory() as pasta:
            self.assertTrue(grafico_barras(relato["intervalos_marcos"], Path(pasta) / "b.png").exists())
        self.assertEqual(_dia_mes_ano("2026-06-09", "2026-06-11"), "09–11/06/26")
        self.assertEqual(_dia_mes_ano("2026-06-28", "2026-07-02"), "28/06–02/07/26")

    def test_faixa_vem_do_adicional_e_do_ajuste(self):
        lido = _evento("2026-06-11", "H")
        eventos = aplicar_ajustes([lido], [{"data": "2026-06-11", "etapa_original": "H", "data_evento": "2026-06-09", "data_evento_ate": "2026-06-11"}])
        self.assertEqual(eventos[0]["data_evento_ate"], "2026-06-11")
        relato = completar_relato({"obra": {}, "eventos": [], "eventos_adicionais": [dict(ENTREGA)]})
        self.assertEqual(relato["eventos"][0]["data_evento_ate"], "2026-06-11")


if __name__ == "__main__":
    unittest.main()
