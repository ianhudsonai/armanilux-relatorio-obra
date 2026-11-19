"""Formato compacto do relatório aprovado (8665.1 V3): tabelas curtas, cores de destaque, sem texto de enchimento."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import TITULOS, completar_relato, destaque_automatico  # noqa: E402


def _evento(data, etapa, ocorrencia, **extra):
    base = {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": ocorrencia, "impacto": "", "midias": [], "documentos": []}
    base.update(extra)
    return base


EVENTOS = [
    _evento("2026-01-05", "A", "Ana: Aprovo as chapas do lote 3."),
    _evento("2026-01-07", "C", "Bruno: Medição da piscina não realizada, área sem liberação."),
    _evento("2026-02-20", "D", "Ana: Envio o projeto preliminar. Mídia: IMG-1.jpg Transcrição: fala longa [fonte: foto, conferir]"),
    _evento("2026-02-25", "E", "Arquitetura pede nova revisão do banho."),
    _evento("2026-02-26", "G", "Projeto aprovado.", destaque="ocioso"),
]


def _sombra(celula) -> str:
    from docx.oxml.ns import qn

    sombra = celula._tc.find(".//" + qn("w:shd"))
    return (sombra.get(qn("w:fill")) or "").upper() if sombra is not None else ""


def _montar(analise: dict):
    from docx import Document

    import build_docx

    with TemporaryDirectory() as pasta:
        destino = build_docx.montar_docx(analise, Path(pasta) / "r.docx", None, None)
        return Document(str(destino))


class DestaqueTeste(unittest.TestCase):
    def test_reprocesso_e_ocioso_pelo_texto(self):
        self.assertEqual(destaque_automatico("E", "Arquitetura pede nova revisão do banho."), "reprocesso")
        self.assertEqual(destaque_automatico("J", "Peça trincada, será refeita."), "reprocesso")
        self.assertEqual(destaque_automatico("C", "Medição da piscina não realizada."), "ocioso")
        self.assertEqual(destaque_automatico("H", "Ainda aguardando liberação da obra."), "ocioso")
        self.assertEqual(destaque_automatico("A", "Aprovo as chapas do lote 3."), "")
        # Enviar o projeto revisado é a etapa F andando, não reprocesso; pedir nova revisão é.
        self.assertEqual(destaque_automatico("F", "Envio do projeto revisado R1 dos banhos."), "")
        self.assertEqual(destaque_automatico("J", "Cliente pede nova revisão depois de aprovado."), "reprocesso")


class FormatoTeste(unittest.TestCase):
    def setUp(self):
        self.relato = completar_relato({"obra": {"numero": "1001", "cliente": "Cliente Teste"}, "eventos": [dict(e) for e in EVENTOS], "revisado": True})
        self.doc = _montar(self.relato)
        self.textos = [p.text for p in self.doc.paragraphs]

    def test_secoes_na_ordem_do_relatorio_aprovado(self):
        titulos = [p.text for p in self.doc.paragraphs if p.style.name == "Heading 1"]
        esperado = (
            ["Nota Metodológica", "Quadro-Resumo da Obra"]
            + [TITULOS[c] for c in "ABCDEFGHIJL"]
            + ["Análise de Prazos — Intervalos em Dias Úteis", "Análise Técnica — Diagnóstico", "Conclusão Estratégica"]
        )
        self.assertEqual(titulos, esperado)
        self.assertEqual(self.textos[-1], "— Fim do relatório —")

    def test_sem_blocos_de_enchimento(self):
        for proibido in ("Ponto crítico", "Gargalo:", "Avaliação:", "Conclusão da etapa", "Registro fotográfico", "Nota de rastreabilidade"):
            self.assertFalse([t for t in self.textos if t.startswith(proibido)], proibido)
        self.assertTrue([t for t in self.textos if t.startswith("Leitura da Etapa A:")])

    def test_linha_do_evento_e_curta_e_colorida(self):
        tabela = next(t for t in self.doc.tables if t.rows[0].cells[1].text == "Evento / Ocorrência" and "Envio o projeto" in t.rows[1].cells[1].text)
        texto = tabela.rows[1].cells[1].text
        self.assertEqual(tabela.rows[1].cells[0].text, "20/02/2026")
        self.assertNotIn("Mídia:", texto)
        self.assertNotIn("[fonte:", texto)
        medicao = next(t for t in self.doc.tables if "não realizada" in t.rows[-1].cells[1].text)
        self.assertEqual(_sombra(medicao.rows[1].cells[1]), "FFF2CC")  # amarelo: ocioso
        revisao = next(t for t in self.doc.tables if "nova revisão" in t.rows[-1].cells[1].text)
        self.assertEqual(_sombra(revisao.rows[1].cells[1]), "FCE4D6")  # salmão: reprocesso
        aprovado = next(t for t in self.doc.tables if t.rows[-1].cells[1].text == "Projeto aprovado.")
        self.assertEqual(_sombra(aprovado.rows[1].cells[0]), "FFF2CC")  # destaque escrito na revisão vale

    def test_intervalo_longo_em_vermelho(self):
        tabela = next(t for t in self.doc.tables if t.rows[0].cells[0].text == "Intervalo entre marcos")
        longa = next(r for r in tabela.rows[1:] if "(07/01/2026)" in r.cells[0].text and "(20/02/2026)" in r.cells[0].text)
        corrida = longa.cells[1].paragraphs[0].runs[0]
        self.assertTrue(corrida.bold)
        self.assertEqual(str(corrida.font.color.rgb), "C00000")
        curta = next(r for r in tabela.rows[1:] if "(05/01/2026)" in r.cells[0].text)
        self.assertNotEqual(str(curta.cells[1].paragraphs[0].runs[0].font.color.rgb), "C00000")

    def test_rascunho_sem_revisao_nao_inventa_diagnostico(self):
        relato = dict(self.relato, revisado=False)
        textos = [p.text for p in _montar(relato).paragraphs]
        indice = textos.index("1. Reprocessos identificados")
        self.assertIn("dado não identificado", textos[indice + 1])


if __name__ == "__main__":
    unittest.main()
