"""Conclusão da obra só com registro de conclusão: um fato qualquer da etapa L (reclamação,
reparo) não fecha a obra. Sem o fato marcado "conclusao", o Quadro-Resumo e a tabela de marcos
dizem dado não identificado, como no relatório aprovado (8665.1 V3)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import aplicar_ajustes, completar_relato  # noqa: E402


def _evento(data: str, etapa: str, ocorrencia: str = "x", **extra) -> dict:
    base = {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": ocorrencia, "impacto": "", "midias": [], "documentos": []}
    base.update(extra)
    return base


RECLAMACAO = _evento("2026-03-16", "L", "Cliente aponta quinas vivas; Armanilux fará os reparos.")
BASE = [_evento("2026-03-02", "G"), _evento("2026-03-09", "I")]


def _linhas(documento, cabecalho: str) -> dict[str, str]:
    for tabela in documento.tables:
        if tabela.rows[0].cells[0].text == cabecalho:
            return {linha.cells[0].text: linha.cells[1].text for linha in tabela.rows[1:]}
    raise AssertionError(f"tabela {cabecalho!r} não está no Word")


def _word(relato: dict):
    from docx import Document

    import build_docx

    with TemporaryDirectory() as pasta:
        return Document(str(build_docx.montar_docx(relato, Path(pasta) / "r.docx", None, None)))


class ConclusaoTeste(unittest.TestCase):
    def test_reclamacao_na_etapa_l_nao_conclui_a_obra(self):
        relato = completar_relato({"obra": {"numero": "1001", "cliente": "Cliente Teste"}, "eventos": BASE + [RECLAMACAO]})
        marcos = {m["marco"]: m["situacao"] for m in relato["marcos"]}
        self.assertEqual(marcos["Conclusão dos serviços e validação final"], "dado não identificado (pendente)")
        self.assertNotIn("L", [m["para"] for m in relato["intervalos_marcos"]])

        documento = _word(relato)
        self.assertEqual(
            _linhas(documento, "Indicador")["Conclusão e validação final"],
            "DADO NÃO IDENTIFICADO (pendente — ver Etapa L)",
        )
        self.assertEqual(
            _linhas(documento, "Marco")["Conclusão dos serviços e validação final"],
            "dado não identificado (pendente)",
        )

    def test_fato_marcado_como_conclusao_fecha_a_obra(self):
        conclusao = {
            "data": "2026-03-20", "hora": "17:00", "etapa": "L", "autor": "Ana",
            "ocorrencia": "Serviços concluídos e validados pela cliente.", "conclusao": True,
        }
        relato = completar_relato(
            {"obra": {"numero": "1001", "cliente": "Cliente Teste"}, "eventos": BASE + [RECLAMACAO], "eventos_adicionais": [conclusao]}
        )
        marcos = {m["marco"]: m["situacao"] for m in relato["marcos"]}
        self.assertEqual(marcos["Conclusão dos serviços e validação final"], "Concluído")
        ultimo = relato["intervalos_marcos"][-1]
        self.assertEqual((ultimo["de"], ultimo["para"], ultimo["fim"]), ("I", "L", "2026-03-20"))
        self.assertEqual(_linhas(_word(relato), "Indicador")["Conclusão e validação final"], "20/03/2026")

    def test_ajuste_marca_fato_lido_do_grupo_como_conclusao(self):
        eventos = aplicar_ajustes(
            [dict(e) for e in BASE + [RECLAMACAO]],
            [{"data": "2026-03-16", "hora": "09:00", "etapa_original": "L", "conclusao": True}],
        )
        relato = completar_relato({"obra": {}, "eventos": eventos})
        marcos = {m["marco"]: m["situacao"] for m in relato["marcos"]}
        self.assertEqual(marcos["Conclusão dos serviços e validação final"], "Concluído")


if __name__ == "__main__":
    unittest.main()
