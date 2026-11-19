"""O que a conversa vira na linha do relatório (extrair_eventos)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import extrair_eventos  # noqa: E402
from parse_whatsapp import analisar_conversa  # noqa: E402


class EventosTeste(unittest.TestCase):
    def test_documento_em_midia_oculta_aparece_pelo_nome(self):
        texto = "05/09/2025 09:50 - Ana Lima: <Mídia oculta>\nProjeto preliminar cozinha R00.pdf\n"
        [evento] = extrair_eventos(analisar_conversa(texto), [], [])
        self.assertEqual(evento["etapa"], "D")
        self.assertEqual(evento["documentos"], ["Projeto preliminar cozinha R00.pdf"])
        self.assertEqual(
            evento["ocorrencia"],
            "Ana Lima: Documento: Projeto preliminar cozinha R00.pdf",
        )

    def test_reencaminhada_entra_na_data_original_e_diz_quem_encaminhou(self):
        texto = "28/09/2026 15:55 - Rogerio Lima: [21/08, 08:54] Bruno Reis: Medimos a cozinha hoje\n"
        [evento] = extrair_eventos(analisar_conversa(texto), [], [])
        self.assertEqual((evento["data"], evento["hora"], evento["etapa"]), ("2026-08-21", "08:54", "C"))
        self.assertEqual(evento["autor"], "Bruno Reis")
        self.assertEqual(
            evento["ocorrencia"],
            "Bruno Reis: Medimos a cozinha hoje (encaminhada no grupo por Rogerio Lima em 28/09/2026 15:55)",
        )


if __name__ == "__main__":
    unittest.main()
