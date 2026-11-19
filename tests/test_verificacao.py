"""Conferência mecânica: cada fato do relatório aponta para uma mensagem ou mídia real."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from parse_whatsapp import analisar_conversa  # noqa: E402
from verificacao import verificar_eventos  # noqa: E402

CHAT = (
    "10/01/2026 10:00 - Ana Souza: Medição in loco realizada hoje na cozinha.\n"
    "20/01/2026 11:00 - Beto Lima: O material chegou na obra hoje de manhã.\n"
)


def _evento(data, hora, autor, midias=None, ocorrencia="x"):
    return {"data": data, "hora": hora, "etapa": "C", "autor": autor, "ocorrencia": ocorrencia, "midias": midias or []}


class VerificacaoTeste(unittest.TestCase):
    def test_cada_fato_e_conferido_contra_a_conversa(self):
        eventos = [
            _evento("2026-01-10", "10:00", "Ana Souza"),  # existe
            _evento("2026-01-10", "", "Ana"),  # sem hora, nome curto: existe no dia
            _evento("2026-01-20", "15:00", "Beto Lima"),  # mesmo dia, outra hora
            _evento("2026-01-21", "09:00", "Ana Souza"),  # não existe
            _evento("2026-01-22", "", "", midias=["VID-1.mp4"], ocorrencia="Visita [fonte: vídeo transcrito, conferir]"),
            _evento("2026-01-23", "", "", midias=["VID-9.mp4"], ocorrencia="Visita [fonte: vídeo transcrito, conferir]"),
        ]
        transcricoes = [{"arquivo": "VID-1.mp4", "status": "ok", "texto": "fala"}]
        situacoes = [item["situacao"] for item in verificar_eventos(eventos, analisar_conversa(CHAT), transcricoes)]
        self.assertEqual(
            situacoes,
            ["confirmado", "confirmado", "hora diferente", "sem mensagem correspondente", "confirmado pela mídia", "mídia não encontrada"],
        )

    def test_nome_escrito_de_outro_jeito_ainda_e_o_mesmo_autor(self):
        chat = "15/06/2026 10:11 - Carla Nunes, Pedras ACME: O elevador de serviço parou.\n"
        eventos = [
            _evento("2026-06-15", "10:11", "Carla Nunes (Pedras ACME)"),
            _evento("2026-06-15", "10:11", "Daniel Prado"),
        ]
        situacoes = [item["situacao"] for item in verificar_eventos(eventos, analisar_conversa(chat), [])]
        self.assertEqual(situacoes, ["confirmado", "sem mensagem correspondente"])


if __name__ == "__main__":
    unittest.main()
