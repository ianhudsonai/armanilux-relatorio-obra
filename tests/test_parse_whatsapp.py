"""Parser de export Android e iPhone, inclusive data pt-BR, anexo e mojibake."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from common import corrigir_mojibake  # noqa: E402
from parse_whatsapp import analisar_conversa  # noqa: E402


ANDROID = """18/01/2026 09:15 - Lucas Ferreira: Aprovo as chapas do lote 3.
18/01/2026 09:16 - Lucas Ferreira: <anexado: medi\u00c3\u00a7\u00c3\u00a3o.pdf>
19/01/2026, 10:02 - Carlos Mendes: Solicito uma visita in loco.
Preciso ver a cozinha
e o banheiro.
20/01/2026 08:00 - As mensagens e as ligações são protegidas com a criptografia de ponta a ponta.
21/01/2026 14:32\u202f- Marina Costa: \u200eIMG-20260121-WA0001.jpg (arquivo anexado)
22/01/2026, 2:05 PM - Helena Duarte: Medição in loco realizada hoje.
"""

IPHONE = """[18/01/26, 09:15:02] Helena Duarte: \u200e<anexado: Projeto-preliminar.pdf>
[18/01/2026, 09:16:10] Carlos Mendes: Ok
continua na linha de baixo
[1/18/26, 9:20 AM] Paulo Ribeiro: Projeto aprovado pela engenharia.
"""


class ParserTeste(unittest.TestCase):
    def test_android_data_anexo_e_multilinha(self):
        mensagens = analisar_conversa(ANDROID)
        self.assertGreaterEqual(len(mensagens), 5)
        primeira = mensagens[0]
        self.assertEqual(primeira.quando, datetime(2026, 1, 18, 9, 15))
        self.assertEqual(primeira.autor, "Lucas Ferreira")
        self.assertFalse(primeira.sistema)
        segunda = mensagens[1]
        self.assertEqual(segunda.anexos, ["medição.pdf"])
        terceira = mensagens[2]
        self.assertIn("cozinha", terceira.texto)
        self.assertIn("banheiro", terceira.texto)
        self.assertEqual(terceira.autor, "Carlos Mendes")
        sistema = mensagens[3]
        self.assertTrue(sistema.sistema)
        self.assertIsNone(sistema.autor)
        foto = mensagens[4]
        self.assertEqual(foto.anexos, ["IMG-20260121-WA0001.jpg"])
        self.assertEqual(foto.autor, "Marina Costa")
        tarde = mensagens[5]
        self.assertEqual(tarde.quando, datetime(2026, 1, 22, 14, 5))

    def test_iphone_ano_curto_e_data_americana_quando_o_mes_nao_cabe(self):
        mensagens = analisar_conversa(IPHONE)
        self.assertEqual(mensagens[0].quando, datetime(2026, 1, 18, 9, 15, 2))
        self.assertEqual(mensagens[0].anexos, ["Projeto-preliminar.pdf"])
        self.assertIn("continua na linha de baixo", mensagens[1].texto)
        # 1/18/26 não cabe em dia/mês; o parser trata como mês/dia.
        self.assertEqual(mensagens[2].quando, datetime(2026, 1, 18, 9, 20))
        self.assertEqual(mensagens[2].autor, "Paulo Ribeiro")

    def test_mojibake_simples_duplo_e_cp437_nao_estraga_texto_certo(self):
        uma = "medição".encode("utf-8").decode("latin-1")
        duas = uma.encode("utf-8").decode("latin-1")
        cp437 = "medição".encode("utf-8").decode("cp437")
        self.assertEqual(corrigir_mojibake(uma), "medição")
        self.assertEqual(corrigir_mojibake(duas), "medição")
        self.assertEqual(corrigir_mojibake(cp437), "medição")
        self.assertEqual(corrigir_mojibake("Família Almeida"), "Família Almeida")
        self.assertEqual(corrigir_mojibake("medição"), "medição")


if __name__ == "__main__":
    unittest.main()
