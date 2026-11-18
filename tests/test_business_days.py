"""Dias úteis: fim de semana, feriado nacional, Carnaval, 9 de julho, 25 de janeiro e Corpus Christi."""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from business_days import carnaval, dias_uteis_entre, eh_dia_util, pascoa  # noqa: E402


class DiasUteisTeste(unittest.TestCase):
    def test_pascoa_e_carnaval_conhecidos(self):
        self.assertEqual(pascoa(2024), date(2024, 3, 31))
        self.assertEqual(pascoa(2026), date(2026, 4, 5))
        self.assertEqual(carnaval(2024), (date(2024, 2, 12), date(2024, 2, 13)))
        self.assertEqual(carnaval(2026), (date(2026, 2, 16), date(2026, 2, 17)))

    def test_fim_de_semana_e_mesmo_dia(self):
        self.assertEqual(dias_uteis_entre(date(2024, 3, 4), date(2024, 3, 5)), 1)
        self.assertEqual(dias_uteis_entre(date(2024, 3, 8), date(2024, 3, 11)), 1)
        self.assertEqual(dias_uteis_entre(date(2024, 3, 9), date(2024, 3, 10)), 0)
        self.assertEqual(dias_uteis_entre(date(2024, 3, 6), date(2024, 3, 6)), 0)
        self.assertEqual(dias_uteis_entre(date(2024, 3, 8), date(2024, 3, 7)), 0)

    def test_feriados_de_sao_paulo_e_nacionais(self):
        # 25/01/2024, quinta, aniversário da cidade.
        self.assertFalse(eh_dia_util(date(2024, 1, 25)))
        self.assertEqual(dias_uteis_entre(date(2024, 1, 24), date(2024, 1, 26)), 1)
        # 09/07/2024, terça, Revolução Constitucionalista.
        self.assertFalse(eh_dia_util(date(2024, 7, 9)))
        self.assertEqual(dias_uteis_entre(date(2024, 7, 8), date(2024, 7, 10)), 1)
        # Corpus Christi 30/05/2024, quinta.
        self.assertFalse(eh_dia_util(date(2024, 5, 30)))
        self.assertEqual(dias_uteis_entre(date(2024, 5, 29), date(2024, 5, 31)), 1)
        # Proclamação da República 15/11/2024, sexta.
        self.assertFalse(eh_dia_util(date(2024, 11, 15)))
        self.assertEqual(dias_uteis_entre(date(2024, 11, 14), date(2024, 11, 18)), 1)

    def test_carnaval_entra_e_quarta_de_cinzas_nao(self):
        self.assertFalse(eh_dia_util(date(2024, 2, 12)))
        self.assertFalse(eh_dia_util(date(2024, 2, 13)))
        self.assertTrue(eh_dia_util(date(2024, 2, 14)))
        self.assertEqual(dias_uteis_entre(date(2024, 2, 9), date(2024, 2, 14)), 1)
        self.assertFalse(eh_dia_util(date(2026, 2, 16)))
        self.assertFalse(eh_dia_util(date(2026, 2, 17)))
        self.assertTrue(eh_dia_util(date(2026, 2, 18)))
        self.assertEqual(dias_uteis_entre(date(2026, 2, 11), date(2026, 3, 2)), 11)
        self.assertEqual(dias_uteis_entre(date(2026, 1, 13), date(2026, 1, 20)), 5)

    def test_contagem_exclui_o_dia_inicial(self):
        # Sexta 8/3/2024 até sexta 15/3/2024: 5 dias úteis (11 a 15), sem incluir a sexta inicial.
        self.assertEqual(dias_uteis_entre(date(2024, 3, 8), date(2024, 3, 15)), 5)


if __name__ == "__main__":
    unittest.main()
