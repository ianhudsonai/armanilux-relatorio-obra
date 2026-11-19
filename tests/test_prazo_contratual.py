"""Prazo contratual: só quando o grupo ou um documento informa; aí o relatório confronta, como no 8665.1 V3."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import completar_relato  # noqa: E402


def _evento(data, etapa):
    return {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": "x", "impacto": "", "midias": [], "documentos": []}


EVENTOS = [_evento("2026-01-05", "C"), _evento("2026-01-09", "D"), _evento("2026-01-12", "G"), _evento("2026-03-02", "H")]
PRAZOS = [
    {"descricao": "Projeto executivo até 6 d.u. da medição", "de": "C", "para": "D", "limite_du": 6, "fonte": "Paulo Ribeiro, 02/01/2026"},
    {"descricao": "Entrega do material até 25 d.u. da aprovação", "de": "G", "para": "H", "limite_du": 25, "fonte": "Paulo Ribeiro, 02/01/2026"},
    {"descricao": "Entrega da piscina (frente medida na revisão)", "inicio": "2026-01-12", "fim": "2026-01-20", "limite_du": 25, "fonte": "Paulo Ribeiro, 02/01/2026"},
    {"descricao": "Instalação até 5 d.u. da entrega", "de": "H", "para": "I", "limite_du": 5, "fonte": "Paulo Ribeiro, 02/01/2026"},
]


class ConfrontoTeste(unittest.TestCase):
    def test_confronto_com_o_prazo_informado(self):
        relato = completar_relato({"obra": {}, "eventos": EVENTOS, "prazos_contratuais": PRAZOS})
        resumo = [(c["limite_du"], c["realizado"], c["excedeu"]) for c in relato["confronto_contrato"]]
        # Contado à mão: 5/1 (seg) a 9/1 = 4 d.u.; 12/1 a 2/3 = 14 + 18 + 1 = 33 d.u. (Carnaval 16 e 17/2 fora; 25/1 é domingo); 12/1 a 20/1 = 6.
        self.assertEqual(resumo, [(6, 4, False), (25, 33, True), (25, 6, False), (5, None, False)])

    def test_sem_prazo_informado_nao_ha_confronto(self):
        relato = completar_relato({"obra": {}, "eventos": EVENTOS})
        self.assertEqual(relato["confronto_contrato"], [])

    def test_word_mostra_o_confronto_e_o_prazo_na_nota(self):
        from docx import Document

        import build_docx

        relato = completar_relato({"obra": {"numero": "1001", "cliente": "Cliente Teste"}, "eventos": EVENTOS, "prazos_contratuais": PRAZOS})
        with TemporaryDirectory() as pasta:
            documento = Document(str(build_docx.montar_docx(relato, Path(pasta) / "r.docx", None, None)))
        tabela = next(t for t in documento.tables if t.rows[0].cells[0].text == "Prazo contratual de referência")
        linhas = [[c.text for c in r.cells] for r in tabela.rows[1:]]
        self.assertEqual(linhas[1], ["Entrega do material até 25 d.u. da aprovação", "25 d.u.", "33 d.u."])
        self.assertEqual(linhas[3][2], "dado não identificado")
        excedido = tabela.rows[2].cells[2].paragraphs[0].runs[0]
        self.assertEqual(str(excedido.font.color.rgb), "C00000")
        nota = next(p.text for p in documento.paragraphs if p.text.startswith("Prazos contratuais de referência:"))
        self.assertIn("Projeto executivo até 6 d.u. da medição", nota)
        self.assertIn("Paulo Ribeiro, 02/01/2026", nota)

    def test_prazo_em_dias_corridos_conta_dias_corridos(self):
        from docx import Document

        import build_docx

        prazo = {"descricao": "Entrega em 7 dias", "inicio": "2026-01-12", "fim": "2026-01-20", "limite_du": 7, "unidade": "dias_corridos", "fonte": "Orçamento"}
        relato = completar_relato({"obra": {"numero": "1001"}, "eventos": EVENTOS, "prazos_contratuais": [prazo]})
        [item] = relato["confronto_contrato"]
        # 12/1 a 20/1 = 8 dias corridos (em dias úteis seriam 6, e o prazo pareceria cumprido).
        self.assertEqual((item["realizado"], item["excedeu"], item["unidade"]), (8, True, "dias_corridos"))
        with TemporaryDirectory() as pasta:
            documento = Document(str(build_docx.montar_docx(relato, Path(pasta) / "r.docx", None, None)))
        tabela = next(t for t in documento.tables if t.rows[0].cells[0].text == "Prazo contratual de referência")
        self.assertEqual([c.text for c in tabela.rows[1].cells], ["Entrega em 7 dias", "7 dias corridos", "8 dias corridos"])

    def test_sem_unidade_continua_em_dias_uteis(self):
        relato = completar_relato({"obra": {}, "eventos": EVENTOS, "prazos_contratuais": PRAZOS[2:3]})
        self.assertEqual(relato["confronto_contrato"][0]["unidade"], "dias_uteis")

    def test_prazo_sem_numero_nao_vira_zero(self):
        relato = completar_relato(
            {"obra": {}, "eventos": EVENTOS, "prazos_contratuais": [{"descricao": "Entrega conforme cronograma", "de": "G", "para": "H", "limite_du": "a combinar"}]}
        )
        [item] = relato["confronto_contrato"]
        self.assertIsNone(item["limite_du"])
        self.assertFalse(item["excedeu"])

    def test_impacto_no_prazo_nao_diz_que_nao_ha_contrato_quando_ha(self):
        from docx import Document

        import build_docx

        relato = completar_relato({"obra": {"numero": "1001", "cliente": "Cliente Teste"}, "eventos": EVENTOS, "prazos_contratuais": PRAZOS})
        with TemporaryDirectory() as pasta:
            textos = [p.text for p in Document(str(build_docx.montar_docx(relato, Path(pasta) / "r.docx", None, None))).paragraphs]
        impacto = textos[textos.index("Impactos no prazo final") + 1]
        self.assertNotIn("não declarado", impacto)
        self.assertIn("1 de 3 prazos contratuais com as duas datas passou do limite", impacto)


if __name__ == "__main__":
    unittest.main()
