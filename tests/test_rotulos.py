"""O que o leitor vê tem de dizer o que aconteceu: a linha do tempo não chama de "Conclusão" uma
reclamação da etapa L, e um fato realizado (cobrança, pedido, checklist enviado, medição não
realizada) marcado como programado vira aviso na remontagem."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import avisos_de_programado  # noqa: E402
from build_charts import linhas_gantt  # noqa: E402


def _evento(data: str, etapa: str, ocorrencia: str = "x", **extra) -> dict:
    base = {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": ocorrencia, "impacto": "", "midias": [], "documentos": []}
    base.update(extra)
    return base


class LinhaDoTempoTeste(unittest.TestCase):
    def test_etapa_l_sem_conclusao_nao_se_chama_conclusao(self):
        eventos = [_evento("2026-03-02", "G"), _evento("2026-03-16", "L", "Cliente aponta quinas vivas.")]
        rotulos = [linha["rotulo"] for linha in linhas_gantt(eventos)]
        self.assertEqual(rotulos[-1], "L  Pendências finais (sem conclusão)")

    def test_etapa_l_com_conclusao_marcada_continua_conclusao(self):
        eventos = [_evento("2026-03-02", "G"), _evento("2026-03-16", "L", "Termo de aceite assinado.", conclusao=True)]
        self.assertEqual(linhas_gantt(eventos)[-1]["rotulo"], "L  Conclusão")


class ProgramadoRealizadoTeste(unittest.TestCase):
    def test_cobranca_pedido_e_envio_marcados_como_programado_viram_aviso(self):
        eventos = [
            _evento("2026-04-14", "G", "Banhos: Armanilux volta a cobrar posição sobre a aprovação.", programado=True),
            _evento("2026-07-03", "H", "Living: checklist enviado para iniciar a entrega.", programado=True),
            _evento("2026-03-12", "C", "Living: medição não realizada; trecho não demolido.", programado=True),
            _evento("2026-06-08", "H", "Banhos: início da entrega programado para 09/06.", programado=True),
        ]
        avisos = avisos_de_programado(eventos)
        self.assertEqual(len(avisos), 3)
        self.assertTrue(all("marco\": false" in aviso for aviso in avisos))
        self.assertIn("14/04/2026", avisos[0])


if __name__ == "__main__":
    unittest.main()
