"""Anexo só com mídia citada, transcrição no anexo, quadros de vídeo e folhas de contato."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "relatorio-cronologico-obra" / "scripts"))

import build_docx  # noqa: E402
from folhas_de_contato import gerar, listar_imagens  # noqa: E402


def _foto(caminho: Path, cor=(90, 90, 90)) -> None:
    from PIL import Image

    caminho.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 48), cor).save(caminho, format="JPEG")


class RegistroFotograficoTeste(unittest.TestCase):
    """Anexo legível: só imagens que a revisão descreveu, com data, etapa e o que mostram."""

    def _analise(self):
        return {
            "eventos": [
                {"data": "2026-01-05", "hora": "09:00", "etapa": "A", "autor": "Ana", "ocorrencia": "x", "midias": ["IMG-20260105-WA0001.jpg"], "documentos": ["projeto.pdf"]},
                {"data": "2026-01-06", "hora": "09:00", "etapa": "B", "autor": "Ana", "ocorrencia": "x", "midias": ["IMG-20260106-WA0002.jpg"], "documentos": []},
            ],
            "transcricoes": [],
            "observacoes_visuais": [
                {"arquivo": "VID-20260110-WA0001.mp4", "observacao": "Medição do banho master."},
                {"arquivo": "IMG-20260105-WA0001.jpg", "observacao": "Chapa de pedra clara no depósito."},
            ],
        }

    def _obra(self, temporario: str) -> Path:
        from PIL import Image

        obra = Path(temporario)
        _foto(obra / "03-midias" / "IMG-20260105-WA0001.jpg")
        _foto(obra / "03-midias" / "IMG-20260106-WA0002.jpg")
        # JPEG sem cabeçalho JFIF, como o FFmpeg grava: o Word comum recusa, a skill regrava.
        quadro = obra / "03-midias" / "quadros" / "VID-20260110-WA0001" / "quadro-02.jpg"
        quadro.parent.mkdir(parents=True)
        Image.new("RGB", (64, 48), (10, 120, 10)).save(quadro, format="JPEG", jfif=False)
        return obra

    def test_so_imagem_descrita_em_ordem_de_data(self):
        from docx import Document

        with TemporaryDirectory() as temporario:
            documento = Document()
            build_docx._registro_fotografico(documento, self._analise(), self._obra(temporario))
        self.assertEqual(len(documento.inline_shapes), 2)
        legendas = [p.text for p in documento.paragraphs if p.text[:2].isdigit()]
        self.assertEqual(
            legendas,
            [
                "05/01/2026 · Etapa A — Chapa de pedra clara no depósito. (IMG-20260105-WA0001.jpg)",
                "10/01/2026 — Medição do banho master. (quadro do vídeo VID-20260110-WA0001.mp4)",
            ],
        )

    def test_word_sem_tabela_de_nomes_de_arquivo(self):
        from docx import Document

        analise = self._analise()
        analise["obra"] = {"numero": "1001", "cliente": "Cliente Teste"}
        from analyze import completar_relato

        with TemporaryDirectory() as temporario:
            obra = self._obra(temporario)
            destino = build_docx.montar_docx(completar_relato(analise), obra / "05-relatorios" / "r.docx", None, None)
            lido = Document(str(destino))
        self.assertFalse([t for t in lido.tables if t.rows[0].cells[0].text == "Arquivo"])
        self.assertIn("Registro fotográfico", [p.text for p in lido.paragraphs])


class FolhasTeste(unittest.TestCase):
    def test_folhas_de_12_com_indice_e_sem_figurinha(self):
        with TemporaryDirectory() as temporario:
            obra = Path(temporario)
            for i in range(14):
                _foto(obra / "03-midias" / f"IMG-202601{i + 1:02d}-WA0001.jpg")
            _foto(obra / "03-midias" / "STK-20260101-WA0001.jpg")
            (obra / "03-midias" / "VID-20260120-WA0001.mp4").write_bytes(b"x")
            _foto(obra / "03-midias" / "quadros" / "VID-20260120-WA0001" / "quadro-02.jpg")
            itens = listar_imagens(obra / "03-midias")
            self.assertEqual(len(itens), 15)
            self.assertNotIn("STK-20260101-WA0001.jpg", [n for n, _ in itens])
            folhas = gerar(obra)
            self.assertEqual([f.name for f in folhas], ["folha-01.jpg", "folha-02.jpg"])
            indice = json.loads((obra / "04-transcricoes" / "folhas-de-contato" / "indice.json").read_text(encoding="utf-8"))
            self.assertEqual(len(indice["folha-01.jpg"]), 12)
            self.assertEqual(indice["folha-01.jpg"][0]["data"], "01/01/2026")
            self.assertTrue(indice["folha-02.jpg"][-1]["video"])


if __name__ == "__main__":
    unittest.main()
