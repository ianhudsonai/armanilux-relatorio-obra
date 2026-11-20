"""Gabarito: confere um relatório (analise.json e Word) contra respostas certas conferidas no grupo.
O gabarito de obra real fica fora do repositório; aqui, obra inventada."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "relatorio-cronologico-obra" / "scripts"))
sys.path.insert(0, str(RAIZ / "tools"))

from analyze import completar_relato  # noqa: E402
from build_docx import montar_docx  # noqa: E402
from pontuar_relatorio import pontuar  # noqa: E402


def _evento(data: str, etapa: str, ocorrencia: str = "x", **extra) -> dict:
    base = {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": ocorrencia, "impacto": "", "midias": [], "documentos": []}
    base.update(extra)
    return base


class PontuarTeste(unittest.TestCase):
    def setUp(self):
        eventos = [
            _evento("2026-01-05", "C", "Medição da piscina."),
            _evento("2026-01-20", "G", "Piscina aprovada."),
            _evento("2026-02-10", "H", "Entrega das bordas."),
        ]
        self.analise = completar_relato({"obra": {"numero": "1001", "periodo_inicio": "2026-01-02", "periodo_fim": "2026-02-20"}, "eventos": eventos})
        self.pasta = Path(tempfile.mkdtemp())
        self.docx = montar_docx(self.analise, self.pasta / "r.docx", None, None)

    def test_conta_acertos_e_mostra_o_que_errou(self):
        gabarito = {
            "checks": [
                {"id": "medicao", "tipo": "marco", "etapa": "C", "aceita": ["2026-01-05"]},
                {"id": "aprovacao", "tipo": "marco", "etapa": "G", "aceita": ["2026-01-21"]},
                {"id": "g-h", "tipo": "intervalo", "de": "G", "para": "H", "aceita": ["15"]},
                {"id": "sem-conclusao", "tipo": "sem_conclusao"},
                {"id": "texto", "tipo": "texto", "contem": ["Piscina aprovada"], "nao_contem": ["Bordas quebradas"]},
                {"id": "evento", "tipo": "evento", "etapa": "H", "data": "2026-02-10", "contem": ["bordas"]},
                {"id": "quadro", "tipo": "quadro", "linha": "Primeira medição in loco", "aceita": ["05/01/2026"]},
            ]
        }
        resultado = pontuar(self.analise, self.docx, gabarito)
        self.assertEqual((resultado["acertos"], resultado["total"]), (6, 7))
        errados = [item for item in resultado["itens"] if not item["ok"]]
        self.assertEqual([item["id"] for item in errados], ["aprovacao"])
        self.assertIn("2026-01-20", errados[0]["achado"])


if __name__ == "__main__":
    unittest.main()
