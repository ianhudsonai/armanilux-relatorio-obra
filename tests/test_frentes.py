"""Obra multifrente: os intervalos entre marcos são medidos dentro de cada frente (banhos, living,
bancadas), como no relatório aprovado (8665.1 V3). Encadear o primeiro registro de cada etapa da
obra inteira mistura frentes (aprovação do piso → entrega dos banhos = 97 d.u. no v13).
Interferência (etapa J) não é passo do fluxo."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import aplicar_ajustes, completar_relato  # noqa: E402


def _evento(data: str, etapa: str, frente: str = "", **extra) -> dict:
    base = {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": "x", "impacto": "", "midias": [], "documentos": []}
    if frente:
        base["frente"] = frente
    base.update(extra)
    return base


def _tabela(relato: dict, cabecalho: str):
    from docx import Document

    import build_docx

    with TemporaryDirectory() as pasta:
        documento = Document(str(build_docx.montar_docx(relato, Path(pasta) / "r.docx", None, None)))
    for tabela in documento.tables:
        if tabela.rows[0].cells[0].text == cabecalho:
            return [[celula.text for celula in linha.cells] for linha in tabela.rows[1:]]
    raise AssertionError(f"tabela {cabecalho!r} não está no Word")


# 2026: 05/01 e 02/03 são segundas-feiras.
EVENTOS = [
    _evento("2026-01-05", "G", "Living"),
    _evento("2026-03-02", "G", "Banhos"),
    _evento("2026-03-09", "J", "Banhos"),
    _evento("2026-03-16", "H", "Banhos"),
    _evento("2026-03-23", "I", "Banhos"),
    _evento("2026-04-06", "H", "Living"),
]


class FrentesTeste(unittest.TestCase):
    def test_intervalos_dentro_de_cada_frente(self):
        relato = completar_relato({"obra": {}, "eventos": EVENTOS})
        resumo = [(m["frente"], m["de"], m["para"], m["dias_uteis"]) for m in relato["intervalos_marcos"]]
        # Contado no calendário: 02/03→16/03 = 10 d.u.; 16/03→23/03 = 5; 05/01→06/04 = 13 semanas = 65, menos Carnaval (16 e 17/02) e
        # Sexta-feira Santa 03/04 fora).
        self.assertEqual(resumo, [("Living", "G", "H", 62), ("Banhos", "G", "H", 10), ("Banhos", "H", "I", 5)])

    def test_interferencia_nao_e_passo_mesmo_sem_frentes(self):
        eventos = [_evento("2026-03-02", "C"), _evento("2026-03-04", "J"), _evento("2026-03-09", "D")]
        relato = completar_relato({"obra": {}, "eventos": eventos})
        self.assertEqual([(m["de"], m["para"], m["dias_uteis"]) for m in relato["intervalos_marcos"]], [("C", "D", 5)])

    def test_word_mostra_a_frente_em_cada_intervalo(self):
        relato = completar_relato({"obra": {"numero": "1001", "cliente": "Cliente Teste"}, "eventos": EVENTOS})
        linhas = _tabela(relato, "Intervalo entre marcos")
        self.assertTrue(linhas[0][0].startswith("Living — "), linhas[0][0])
        self.assertTrue(linhas[1][0].startswith("Banhos — "), linhas[1][0])
        self.assertEqual(linhas[1][1], "10 d.u.")

    def test_prazo_por_etapas_usa_a_frente_indicada(self):
        prazo = {"descricao": "Banhos: aprovação → entrega", "frente": "Banhos", "de": "G", "para": "H",
                 "limite_du": 25, "fonte": "abertura", "fonte_data": "2025-12-01"}
        relato = completar_relato({"obra": {}, "eventos": EVENTOS, "prazos_contratuais": [prazo]})
        item = relato["confronto_contrato"][0]
        self.assertEqual((item["inicio"], item["fim"], item["realizado"]), ("2026-03-02", "2026-03-16", 10))

    def test_frente_vem_do_evento_adicional_e_do_ajuste(self):
        lido = _evento("2026-03-02", "G")
        eventos = aplicar_ajustes([lido], [{"data": "2026-03-02", "etapa_original": "G", "frente": "Banhos"}])
        extra = {"data": "2026-03-16", "hora": "10:00", "etapa": "H", "autor": "Ana", "ocorrencia": "Entregue.", "frente": "Banhos"}
        relato = completar_relato({"obra": {}, "eventos": eventos, "eventos_adicionais": [extra]})
        self.assertEqual([(m["frente"], m["de"], m["para"]) for m in relato["intervalos_marcos"]], [("Banhos", "G", "H")])


if __name__ == "__main__":
    unittest.main()
