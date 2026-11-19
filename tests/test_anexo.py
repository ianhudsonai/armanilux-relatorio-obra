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


class AnexoTeste(unittest.TestCase):
    def _analise(self):
        return {
            "eventos": [
                {"data": "2026-01-10", "hora": "10:00", "etapa": "C", "midias": ["VID-20260110-WA0001.mp4"], "documentos": []},
                {"data": "2026-01-05", "hora": "09:00", "etapa": "A", "midias": ["IMG-20260105-WA0001.jpg"], "documentos": ["projeto.pdf"]},
            ],
            "transcricoes": [{"arquivo": "VID-20260110-WA0001.mp4", "status": "ok", "texto": "Estou medindo o banho master agora."}],
            "observacoes_visuais": [{"arquivo": "IMG-20260105-WA0001.jpg", "observacao": "Chapa de pedra clara no depósito."}],
            "anexo": [{"arquivo": f"IMG-{i}.jpg"} for i in range(300)],
        }

    def test_so_midia_citada_em_ordem_e_com_transcricao(self):
        analise = self._analise()
        linhas = build_docx._midias_citadas(analise)
        self.assertEqual([l["arquivo"] for l in linhas], ["IMG-20260105-WA0001.jpg", "projeto.pdf", "VID-20260110-WA0001.mp4"])
        self.assertIn("Estou medindo o banho master", build_docx._observacao(analise, "VID-20260110-WA0001.mp4"))
        self.assertIn("conferir", build_docx._observacao(analise, "VID-20260110-WA0001.mp4"))
        self.assertEqual(build_docx._observacao(analise, "IMG-20260105-WA0001.jpg"), "Chapa de pedra clara no depósito.")

    def test_quadro_de_video_do_ffmpeg_entra_no_word(self):
        from docx import Document

        with TemporaryDirectory() as temporario:
            obra = Path(temporario)
            _foto(obra / "03-midias" / "IMG-20260105-WA0001.jpg")
            # JPEG sem cabeçalho JFIF, como o FFmpeg grava: o Word comum recusa, a skill regrava.
            from PIL import Image

            quadro = obra / "03-midias" / "quadros" / "VID-20260110-WA0001" / "quadro-02.jpg"
            quadro.parent.mkdir(parents=True)
            Image.new("RGB", (64, 48), (10, 120, 10)).save(quadro, format="JPEG", jfif=False)
            documento = Document()
            build_docx._anexar_imagens(documento, self._analise(), obra)
            self.assertGreaterEqual(len(documento.inline_shapes), 2)
            legendas = [p.text for p in documento.paragraphs if p.text.startswith("Mídia:")]
            self.assertTrue(legendas[0].startswith("Mídia: IMG-20260105-WA0001.jpg — Chapa"))
            self.assertTrue(any("quadro do vídeo" in l for l in legendas))


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
