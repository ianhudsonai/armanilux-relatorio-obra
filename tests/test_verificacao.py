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

    def test_fato_de_mensagem_colada_confere_pelo_autor_e_hora_originais(self):
        conversa = analisar_conversa(
            "16/11/2026 18:02 - Paulo Ribeiro: Conversa com a arquiteta\n"
            "[12:25, 03/07/2026] Carla Nunes: Pode instalar a bancada amanhã\n"
        )
        [item] = verificar_eventos([_evento("2026-07-03", "12:25", "Carla Nunes")], conversa, [])
        self.assertEqual(item["situacao"], "confirmado")

    def test_nome_escrito_de_outro_jeito_ainda_e_o_mesmo_autor(self):
        chat = "15/06/2026 10:11 - Carla Nunes, Pedras ACME: O elevador de serviço parou.\n"
        eventos = [
            _evento("2026-06-15", "10:11", "Carla Nunes (Pedras ACME)"),
            _evento("2026-06-15", "10:11", "Daniel Prado"),
        ]
        situacoes = [item["situacao"] for item in verificar_eventos(eventos, analisar_conversa(chat), [])]
        self.assertEqual(situacoes, ["confirmado", "sem mensagem correspondente"])

    def test_fato_sem_hora_sem_autor_e_de_foto(self):
        eventos = [
            _evento("2026-01-10", "00:00", "Ana Souza"),  # revisão sem hora grava 00:00
            _evento("2026-01-10", "", ""),  # sem autor nem hora: não dá para conferir
            _evento("2026-01-11", "", "", midias=["IMG-1.jpg"], ocorrencia="Trinca na base [fonte: foto, conferir]"),
        ]
        itens = verificar_eventos(eventos, analisar_conversa(CHAT), [], arquivos=["IMG-1.jpg"])
        self.assertEqual(
            [item["situacao"] for item in itens],
            ["confirmado", "sem autor nem hora", "confirmado pela mídia"],
        )


if __name__ == "__main__":
    unittest.main()
