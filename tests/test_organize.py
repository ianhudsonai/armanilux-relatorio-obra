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


class ReextrairTeste(unittest.TestCase):
    def test_mesma_conversa_duas_vezes_nao_duplica(self):
        with TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            zip_path = raiz / "export.zip"
            with zipfile.ZipFile(zip_path, "w") as arquivo:
                arquivo.writestr("_chat.txt", b"conversa")
                arquivo.writestr("projeto.pdf", b"%PDF-1.4 a")
                arquivo.writestr("foto.jpg", b"jpg-bytes")
            obra = garantir_obra(raiz / "obras", "1001", "Cliente")
            primeiro = extrair_zip(zip_path, obra)
            segundo = extrair_zip(zip_path, obra)
            self.assertEqual(primeiro["ja_existiam"], 0)
            self.assertEqual(segundo["ja_existiam"], 3)
            self.assertEqual(sorted(p.name for p in (obra / "02-projetos-pdf").iterdir()), ["projeto.pdf"])
            self.assertEqual(sorted(p.name for p in (obra / "03-midias").iterdir() if p.is_file()), ["foto.jpg"])
            self.assertEqual(sorted(p.name for p in (obra / "01-conversas").glob("*.txt") if p.name != "origem.txt"), ["_chat.txt"])

    def test_arquivo_com_mesmo_nome_e_conteudo_diferente_ganha_outro_nome(self):
        with TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            obra = garantir_obra(raiz / "obras", "1001", "Cliente")
            for versao, conteudo in (("a", b"%PDF-1.4 versao antiga"), ("b", b"%PDF-1.4 versao nova mais longa")):
                zip_path = raiz / f"{versao}.zip"
                with zipfile.ZipFile(zip_path, "w") as arquivo:
                    arquivo.writestr("projeto.pdf", conteudo)
                extrair_zip(zip_path, obra)
            nomes = sorted(p.name for p in (obra / "02-projetos-pdf").iterdir())
            self.assertEqual(nomes, ["projeto-2.pdf", "projeto.pdf"])


class PastaDaObraTeste(unittest.TestCase):
    def test_mesma_obra_com_cliente_escrito_de_outro_jeito_usa_a_pasta_que_ja_existe(self):
        # Visto na avaliação de prontidão: "Silva" e depois "Silva Marmores" faziam duas pastas da obra 1001.
        with TemporaryDirectory() as temporario:
            raiz = Path(temporario)
            primeira = garantir_obra(raiz, "1001", "Silva")
            self.assertEqual(garantir_obra(raiz, "1001", "Silva Marmores"), primeira)
            invertido = "{cliente} - {numero}"
            outra = garantir_obra(raiz, "2002", "Costa", invertido)
            self.assertEqual(garantir_obra(raiz, "2002", "Família Costa", invertido), outra)
            # Número que só começa igual não é a mesma obra.
            self.assertNotEqual(garantir_obra(raiz, "100", "Silva"), primeira)
            self.assertEqual(len([p for p in raiz.iterdir() if p.is_dir()]), 3)


if __name__ == "__main__":
    unittest.main()
