"""Dias úteis entre marcos nomeados (primeiro registro de cada etapa) e gráficos legíveis."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import completar_relato  # noqa: E402


def _evento(data: str, etapa: str) -> dict:
    return {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": "x", "impacto": "", "midias": [], "documentos": []}


EVENTOS = [
    _evento("2026-01-05", "A"),
    _evento("2026-01-07", "C"),
    _evento("2026-01-12", "D"),
    _evento("2026-01-20", "C"),  # segunda medição: não é marco novo
    _evento("2026-02-02", "G"),
]


class MarcosTeste(unittest.TestCase):
    def test_um_intervalo_por_marco_e_a_duracao_total(self):
        relato = completar_relato({"obra": {}, "eventos": EVENTOS})
        resumo = [(m["de"], m["para"], m["inicio"], m["fim"], m["dias_uteis"]) for m in relato["intervalos_marcos"]]
        # Contado à mão no calendário de 2026: 5/1 é segunda-feira; 25/1 cai num domingo.
        self.assertEqual(
            resumo,
            [
                ("A", "C", "2026-01-05", "2026-01-07", 2),
                ("C", "D", "2026-01-07", "2026-01-12", 3),
                ("D", "G", "2026-01-12", "2026-02-02", 15),
            ],
        )
        self.assertEqual(relato["duracao_marcos"], {"inicio": "2026-01-05", "fim": "2026-02-02", "dias_uteis": 20})


class TabelaWordTeste(unittest.TestCase):
    def test_tabela_tem_um_marco_por_linha_e_a_duracao_total(self):
        from docx import Document

        import build_docx

        relato = completar_relato({"obra": {"numero": "1001", "cliente": "Cliente Teste"}, "eventos": EVENTOS})
        with TemporaryDirectory() as pasta:
            destino = build_docx.montar_docx(relato, Path(pasta) / "r.docx", None, None)
            tabelas = [t for t in Document(str(destino)).tables if t.rows[0].cells[0].text == "Intervalo entre marcos"]
        self.assertEqual(len(tabelas), 1)
        linhas = [[celula.text for celula in linha.cells] for linha in tabelas[0].rows[1:]]
        self.assertEqual(len(linhas), 5)
        # O ciclo parou na aprovação (G): a entrega aparece como dado não identificado.
        self.assertEqual(linhas[3][1], "pendente")
        self.assertEqual(linhas[0][1], "2 d.u.")
        self.assertIn("(05/01/2026)", linhas[0][0])
        self.assertIn("(07/01/2026)", linhas[0][0])
        self.assertEqual(linhas[-1], ["DURAÇÃO TOTAL REGISTRADA (05/01/2026 → 02/02/2026)", "20 d.u."])


class GraficosTeste(unittest.TestCase):
    """O Word põe a figura com 16,2 cm. Desenhada nessa largura, a letra sai no tamanho escolhido."""

    def _largura_cm(self, caminho: Path) -> float:
        from PIL import Image

        with Image.open(caminho) as imagem:
            dpi = imagem.info["dpi"][0]
            return imagem.width / dpi * 2.54

    def test_graficos_ja_saem_na_largura_da_pagina(self):
        from build_charts import grafico_barras, grafico_gantt

        relato = completar_relato({"obra": {}, "eventos": EVENTOS})
        with TemporaryDirectory() as pasta:
            barras = grafico_barras(relato["intervalos_marcos"], Path(pasta) / "b.png")
            gantt = grafico_gantt(relato["eventos"], Path(pasta) / "g.png")
            self.assertAlmostEqual(self._largura_cm(barras), 16.2, delta=0.3)
            self.assertAlmostEqual(self._largura_cm(gantt), 16.2, delta=0.3)


if __name__ == "__main__":
    unittest.main()
