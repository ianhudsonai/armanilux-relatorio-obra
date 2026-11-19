"""Data programada não é data realizada. "Programado para 10/11" não entra como entrega feita no
Quadro-Resumo, nos marcos nem no confronto com o contrato. E quando a mensagem conta um fato de
outro dia ("aprovados em 23/09", escrita em 24/09), o marco usa a data do fato (data_evento)."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import aplicar_ajustes, completar_relato, extrair_eventos  # noqa: E402
from parse_whatsapp import Mensagem  # noqa: E402


def _evento(data: str, etapa: str, ocorrencia: str = "x", **extra) -> dict:
    base = {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": ocorrencia, "impacto": "", "midias": [], "documentos": []}
    base.update(extra)
    return base


def _word(relato: dict):
    from docx import Document

    import build_docx

    with TemporaryDirectory() as pasta:
        return Document(str(build_docx.montar_docx(relato, Path(pasta) / "r.docx", None, None)))


def _tabela(documento, cabecalho: str):
    for tabela in documento.tables:
        if tabela.rows[0].cells[0].text == cabecalho:
            return [[celula.text for celula in linha.cells] for linha in tabela.rows[1:]]
    raise AssertionError(f"tabela {cabecalho!r} não está no Word")


OBRA = {"numero": "1001", "cliente": "Cliente Teste"}


class ProgramadoTeste(unittest.TestCase):
    def test_entrega_programada_nao_e_a_primeira_entrega(self):
        eventos = [
            _evento("2026-03-02", "G"),
            _evento("2026-03-09", "H", "Banhos: entrega programada para 10/03.", programado=True),
            _evento("2026-03-16", "H", "Banhos: peças entregues na obra."),
        ]
        relato = completar_relato({"obra": OBRA, "eventos": eventos})
        self.assertEqual([(m["de"], m["para"], m["fim"]) for m in relato["intervalos_marcos"]], [("G", "H", "2026-03-16")])
        quadro = dict(_tabela(_word(relato), "Indicador"))
        self.assertEqual(quadro["Primeira entrega na obra"], "16/03/2026")

    def test_so_programado_nao_conta_como_concluido(self):
        eventos = [_evento("2026-03-02", "G"), _evento("2026-03-09", "H", "Banhos: entrega das peças em 10/03.", programado=True)]
        relato = completar_relato({"obra": OBRA, "eventos": eventos})
        marcos = {m["marco"]: m["situacao"] for m in relato["marcos"]}
        self.assertEqual(marcos["Entrega do material na obra"], "Programado, sem confirmação")
        self.assertEqual(relato["intervalos_marcos"], [])
        documento = _word(relato)
        self.assertEqual(dict(_tabela(documento, "Indicador"))["Primeira entrega na obra"], "dado não identificado")
        # Na tabela da etapa a linha continua, com a marca de programado na data.
        linhas_h = [
            [celula.text for celula in linha.cells]
            for tabela in documento.tables
            if tabela.rows[0].cells[0].text == "Data"
            for linha in tabela.rows[1:]
            if "entrega das peças" in linha.cells[1].text
        ]
        self.assertEqual(linhas_h, [["09/03/2026 (programado)", "Banhos: entrega das peças em 10/03."]])

    def test_marco_usa_a_data_do_fato_e_nao_a_da_mensagem(self):
        eventos = [
            _evento("2026-03-02", "A", "Pedido de visita para aprovar as chapas.", programado=True),
            _evento("2026-03-10", "A", "Chapas aprovadas com a cliente em 09/03.", data_evento="2026-03-09"),
            _evento("2026-03-12", "C"),
        ]
        relato = completar_relato({"obra": OBRA, "eventos": eventos})
        self.assertEqual(
            [(m["de"], m["inicio"], m["para"], m["fim"], m["dias_uteis"]) for m in relato["intervalos_marcos"]],
            [("A", "2026-03-09", "C", "2026-03-12", 3)],
        )
        self.assertEqual(dict(_tabela(_word(relato), "Indicador"))["Primeira aprovação de chapas"], "09/03/2026")

    def test_prazo_com_fim_programado_nao_tem_realizado(self):
        prazo = {
            "descricao": "Bancadas: aprovação → início da entrega (até 35 d.u.)",
            "inicio": "2026-03-02", "fim": "2026-04-17", "limite_du": 35, "fonte": "mensagem de abertura",
            "fonte_data": "2026-01-05", "programado": True,
        }
        relato = completar_relato({"obra": OBRA, "eventos": [_evento("2026-03-02", "G")], "prazos_contratuais": [prazo]})
        item = relato["confronto_contrato"][0]
        self.assertIsNone(item["realizado"])
        self.assertTrue(item["programado"])
        linha = _tabela(_word(relato), "Prazo contratual de referência")[0]
        self.assertEqual(linha[2], "programado, sem confirmação")

    def test_leitura_do_grupo_marca_programado_na_entrega(self):
        mensagem = Mensagem(
            quando=datetime(2026, 11, 9, 16, 26), autor="Bruna",
            texto="Estamos programando para amanhã a entrega do material das bancadas.",
        )
        eventos = extrair_eventos([mensagem], [], [])
        self.assertEqual([(e["etapa"], e.get("programado")) for e in eventos], [("H", True)])

    def test_ajuste_desmarca_programado_e_corrige_a_data(self):
        lido = _evento("2026-03-09", "H", "Entrega programada.", programado=True)
        eventos = aplicar_ajustes([lido], [{"data": "2026-03-09", "etapa_original": "H", "programado": False, "data_evento": "2026-03-10"}])
        self.assertEqual((eventos[0]["programado"], eventos[0]["data_evento"]), (False, "2026-03-10"))

    def test_evento_adicional_leva_as_marcas(self):
        extra = {"data": "2026-03-09", "hora": "10:00", "etapa": "H", "autor": "Ana", "ocorrencia": "Entrega programada.", "programado": True}
        relato = completar_relato({"obra": OBRA, "eventos": [], "eventos_adicionais": [extra]})
        self.assertTrue(relato["eventos"][0]["programado"])


if __name__ == "__main__":
    unittest.main()
