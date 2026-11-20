"""Aprovação revista não é o marco. Quando a uma aprovação seguem revisão (E ou F) e nova aprovação
da mesma frente, a aprovação que valeu é a nova: é dela que contam a entrega e a instalação. Uma
mudança depois da última aprovação (já na produção) não desfaz a aprovação."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import aprovacoes_revistas, completar_relato, confronto_contrato, primeiros_marcos  # noqa: E402


def _evento(data: str, etapa: str, hora: str = "09:00", **extra) -> dict:
    base = {"data": data, "hora": hora, "etapa": etapa, "autor": "Ana", "ocorrencia": "x", "impacto": "", "midias": [], "documentos": [], "frente": "Banhos"}
    base.update(extra)
    return base


BANHOS = [
    _evento("2026-04-17", "G", "10:37"),
    _evento("2026-04-20", "E", "11:12"),
    _evento("2026-04-24", "F", "01:03"),
    _evento("2026-04-24", "G", "11:12"),
    _evento("2026-04-27", "G", "12:30"),
    _evento("2026-05-06", "E"),  # mudança já na produção: não desfaz a aprovação de 24/04
    _evento("2026-06-09", "H"),
]
OUTRA_FRENTE = [_evento("2026-01-14", "G", frente="Living"), _evento("2026-03-02", "F", frente="Living"), _evento("2026-03-10", "I", frente="Living")]


class AprovacaoRevistaTeste(unittest.TestCase):
    def test_marco_da_frente_e_a_aprovacao_que_valeu(self):
        self.assertEqual(primeiros_marcos(BANHOS, "Banhos")["G"], "2026-04-24")
        relato = completar_relato({"obra": {}, "eventos": BANHOS + OUTRA_FRENTE})
        banhos = [m for m in relato["intervalos_marcos"] if m["frente"] == "Banhos"]
        self.assertEqual([(m["de"], m["inicio"], m["para"], m["dias_uteis"]) for m in banhos], [("G", "2026-04-24", "H", 30)])

    def test_revisao_no_mesmo_dia_depois_da_aprovacao_tambem_revisa(self):
        eventos = [_evento("2026-04-17", "G", "10:00"), _evento("2026-04-17", "E", "15:00"), _evento("2026-04-22", "G"), _evento("2026-06-09", "H")]
        self.assertEqual(primeiros_marcos(eventos, "Banhos")["G"], "2026-04-22")

    def test_aprovacao_repetida_antes_da_revisao_tambem_e_revista(self):
        eventos = [_evento("2026-04-10", "G"), _evento("2026-04-14", "G"), _evento("2026-04-20", "E"), _evento("2026-04-24", "G"), _evento("2026-06-09", "H")]
        self.assertEqual(primeiros_marcos(eventos, "Banhos")["G"], "2026-04-24")
        self.assertEqual(aprovacoes_revistas(eventos)[0]["revistas"], ["2026-04-10", "2026-04-14"])

    def test_sem_nova_aprovacao_a_primeira_vale(self):
        eventos = [_evento("2026-04-17", "G"), _evento("2026-04-20", "E"), _evento("2026-06-09", "H")]
        self.assertEqual(primeiros_marcos(eventos, "Banhos")["G"], "2026-04-17")

    def test_nova_aprovacao_marcada_fora_do_ciclo_deixa_a_primeira(self):
        eventos = [_evento("2026-04-17", "G"), _evento("2026-04-20", "E"), _evento("2026-04-24", "G", marco=False)]
        self.assertEqual(primeiros_marcos(eventos, "Banhos")["G"], "2026-04-17")

    def test_quadro_da_obra_multifrente_mostra_a_primeira_aprovacao(self):
        self.assertEqual(primeiros_marcos(BANHOS + OUTRA_FRENTE)["G"], "2026-01-14")

    def test_obra_sem_frentes_usa_a_aprovacao_que_valeu(self):
        sem_frente = [dict(e, frente="") for e in BANHOS]
        self.assertEqual(primeiros_marcos(sem_frente)["G"], "2026-04-24")

    def test_confronto_da_frente_usa_a_aprovacao_que_valeu(self):
        prazos = [{"descricao": "Banhos: aprovação → entrega", "de": "G", "para": "H", "frente": "Banhos", "limite_du": 25, "fonte_data": "2025-08-29"}]
        self.assertEqual(confronto_contrato(BANHOS, prazos)[0]["realizado"], 30)

    def test_lista_e_word_dizem_qual_aprovacao_foi_revista(self):
        revistas = aprovacoes_revistas(BANHOS + OUTRA_FRENTE)
        # Living tem revisão depois da aprovação, mas nenhuma aprovação nova: não entra.
        self.assertEqual(revistas, [{"frente": "Banhos", "revistas": ["2026-04-17"], "valeu": "2026-04-24"}])
        from docx import Document

        import build_docx

        relato = completar_relato({"obra": {}, "eventos": BANHOS + OUTRA_FRENTE})
        with TemporaryDirectory() as pasta:
            texto = "\n".join(p.text for p in Document(str(build_docx.montar_docx(relato, Path(pasta) / "r.docx", None, None))).paragraphs)
        self.assertIn("Aprovações revistas: Banhos: 17/04/2026 (valeu a de 24/04/2026).", texto)


if __name__ == "__main__":
    unittest.main()
