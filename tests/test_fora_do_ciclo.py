"""Fato realizado que não é marco do ciclo: reposição, peça extra, segunda instalação. Quando o fato
original (a entrega do piso) não está no grupo, a reposição entregue meses depois não pode virar a
"primeira entrega" da frente; a data que falta continua dado não identificado."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import aplicar_ajustes, completar_relato  # noqa: E402


def _evento(data: str, etapa: str, **extra) -> dict:
    base = {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": "x", "impacto": "", "midias": [], "documentos": [],
            "frente": "Living"}
    base.update(extra)
    return base


class ForaDoCicloTeste(unittest.TestCase):
    def test_reposicao_nao_e_a_entrega_da_frente(self):
        eventos = [_evento("2026-01-14", "G"), _evento("2026-08-03", "I"), _evento("2026-09-30", "H", marco=False)]
        relato = completar_relato({"obra": {}, "eventos": eventos})
        self.assertEqual([(m["de"], m["para"]) for m in relato["intervalos_marcos"]], [("G", "I")])
        self.assertIn(("Living", "G", "H"), [(p["frente"], p["de"], p["para"]) for p in relato["ciclos_incompletos"]])
        # A linha continua na tabela da etapa H.
        self.assertEqual([e["data"] for e in relato["eventos"] if e["etapa"] == "H"], ["2026-09-30"])

    def test_marca_vem_do_adicional_e_do_ajuste(self):
        lido = _evento("2026-09-30", "H")
        eventos = aplicar_ajustes([lido], [{"data": "2026-09-30", "etapa_original": "H", "marco": False}])
        self.assertIs(eventos[0]["marco"], False)
        extra = {"data": "2026-10-05", "hora": "10:00", "etapa": "H", "autor": "Ana", "ocorrencia": "Reposição.", "marco": False}
        relato = completar_relato({"obra": {}, "eventos": [], "eventos_adicionais": [extra]})
        self.assertIs(relato["eventos"][0]["marco"], False)
        self.assertEqual(relato["intervalos_marcos"], [])


if __name__ == "__main__":
    unittest.main()
