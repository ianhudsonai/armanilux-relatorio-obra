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
            self.assertEqual(indice["folha-01.jpg"][0]["data"], "01/01/2026 (nome do arquivo)")  # sem mensagem: a data vem do nome, marcada
            self.assertTrue(indice["folha-02.jpg"][-1]["video"])


if __name__ == "__main__":
    unittest.main()
