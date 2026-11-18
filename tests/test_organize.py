"""Extração em fluxo, nome com mojibake e bloqueio de caminho inseguro."""

from __future__ import annotations

import sys
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from organize_export import extrair_zip  # noqa: E402
from setup_workspace import garantir_obra  # noqa: E402


class OrganizarTeste(unittest.TestCase):
    def test_fluxo_mojibake_e_zip_slip(self):
        with TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            zip_path = raiz / "export.zip"
            carga = b"a" * (3 * 1024 * 1024)
            with zipfile.ZipFile(zip_path, "w") as arquivo:
                info = zipfile.ZipInfo("medi\u00c3\u00a7\u00c3\u00a3o.pdf")
                info.flag_bits |= 0x800
                arquivo.writestr(info, b"%PDF-1.4 exemplo")
                grande = zipfile.ZipInfo("video.mp4")
                arquivo.writestr(grande, carga)
                arquivo.writestr("../fora.txt", b"nao pode sair")
                arquivo.writestr("..\\tambem.txt", b"nao pode sair")
            obra = garantir_obra(raiz / "obras", "1001", "Familia Teste")
            resumo = extrair_zip(zip_path, obra)
            self.assertTrue((obra / "02-projetos-pdf" / "medição.pdf").exists())
            video = obra / "03-midias" / "video.mp4"
            self.assertEqual(video.stat().st_size, len(carga))
            self.assertFalse((raiz / "fora.txt").exists())
            self.assertFalse((raiz / "tambem.txt").exists())
            self.assertGreaterEqual(len(resumo["ignorados"]), 1)
            self.assertIn("origem.txt", (obra / "01-conversas" / "origem.txt").name)


if __name__ == "__main__":
    unittest.main()
