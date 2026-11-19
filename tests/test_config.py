"""Preferências gravadas pelo preparo e lidas pelo relatório."""

from __future__ import annotations

import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "relatorio-cronologico-obra" / "scripts"))
sys.path.insert(0, str(RAIZ / "skills" / "preparar-projeto-armanilux" / "scripts"))

from config_io import carregar, nome_pasta_obra, pasta_relatorios, salvar  # noqa: E402
from preparar import preparar  # noqa: E402
from run_pipeline import executar  # noqa: E402


class ConfigTeste(unittest.TestCase):
    def test_gravar_ler_e_mudar_de_novo(self):
        with TemporaryDirectory() as temporario:
            base = Path(temporario)
            config_path = base / "config.json"
            os.environ["ARMANILUX_CONFIG"] = str(config_path)
            try:
                self.assertIsNone(carregar())
                preparar(str(base / "Armanilux"), "Helena Duarte", "Operações", False, "{numero} - {cliente}")
                lido = carregar()
                self.assertEqual(lido["nome"], "Helena Duarte")
                self.assertEqual(lido["funcao"], "Operações")
                self.assertFalse(lido["gerar_pdf"])
                self.assertTrue((base / "Armanilux" / "LEIA-ME.txt").is_file())
                self.assertTrue((base / "Armanilux" / "Relatorios-de-Obra" / "_modelo" / "05-relatorios").is_dir())
                preparar(str(base / "Outra"), "Carlos Mendes", "Projetos", True, "{cliente} - {numero}")
                lido = carregar()
                self.assertEqual(lido["pasta_raiz"], str(base / "Outra"))
                self.assertTrue(lido["gerar_pdf"])
                self.assertEqual(nome_pasta_obra(lido, "1001", "Família Almeida"), "Família Almeida - 1001")
                self.assertEqual(pasta_relatorios(lido), base / "Outra" / "Relatorios-de-Obra")
                self.assertEqual(nome_pasta_obra({"modelo_pasta_obra": "{sala}"}, "1", "A"), "1 - A")
            finally:
                os.environ.pop("ARMANILUX_CONFIG", None)

    def test_entrega_por_link_acha_a_pasta_da_nuvem_e_sem_nuvem_vira_pdf(self):
        from preparar import main as preparar_main

        with TemporaryDirectory() as temporario:
            base = Path(temporario)
            onedrive = base / "OneDrive"
            onedrive.mkdir()
            os.environ["ARMANILUX_CONFIG"] = str(base / "config.json")
            try:
                with mock.patch.dict(os.environ, {"OneDrive": str(onedrive), "OneDriveCommercial": ""}):
                    preparar_main(["--pasta-raiz", str(base / "A"), "--entrega", "link", "--pasta-link", "auto"])
                lido = carregar()
                self.assertEqual(lido["formato_entrega"], "link")
                self.assertEqual(lido["pasta_link"], str(onedrive / "Armanilux" / "Relatorios"))
                self.assertIn("Entrega: link", (base / "A" / "LEIA-ME.txt").read_text(encoding="utf-8"))

                saida = io.StringIO()
                with mock.patch("preparar.pasta_da_nuvem", return_value=None), contextlib.redirect_stdout(saida):
                    preparar_main(["--pasta-raiz", str(base / "A"), "--entrega", "link", "--pasta-link", "auto"])
                self.assertEqual(carregar()["formato_entrega"], "pdf")
                self.assertIn("Não achei a pasta do OneDrive nem do Google Drive", saida.getvalue())

                preparar_main(["--pasta-raiz", str(base / "A"), "--pdf", "sim"])
                self.assertEqual(carregar()["formato_entrega"], "pdf")
            finally:
                os.environ.pop("ARMANILUX_CONFIG", None)

    def test_onedrive_e_google_drive_aparecem_os_dois_para_a_pessoa_escolher(self):
        from preparar import pastas_da_nuvem

        with TemporaryDirectory() as temporario:
            base = Path(temporario)
            onedrive, google = base / "OneDrive", base / "Meu Drive"
            onedrive.mkdir()
            google.mkdir()
            self.assertEqual(
                pastas_da_nuvem([onedrive, base / "nao-existe", google]),
                [onedrive / "Armanilux" / "Relatorios", google / "Armanilux" / "Relatorios"],
            )

    def test_pasta_link_digitada_que_nao_existe_nao_vira_pasta_fantasma(self):
        from preparar import main as preparar_main

        with TemporaryDirectory() as temporario:
            base = Path(temporario)
            with mock.patch.dict(os.environ, {"ARMANILUX_CONFIG": str(base / "config.json")}):
                saida = io.StringIO()
                with contextlib.redirect_stdout(saida):
                    preparar_main(["--pasta-raiz", str(base / "A"), "--entrega", "link", "--pasta-link", str(base / "OneDriv" / "x" / "y")])
                self.assertEqual(carregar()["formato_entrega"], "pdf")
                self.assertIn("Não achei a pasta", saida.getvalue())

    def test_relatorio_sem_config_pede_a_preparacao(self):
        with TemporaryDirectory() as temporario:
            os.environ["ARMANILUX_CONFIG"] = str(Path(temporario) / "ausente.json")
            try:
                codigo = executar([])
            finally:
                os.environ.pop("ARMANILUX_CONFIG", None)
        self.assertEqual(codigo, 2)

    def test_os_dois_modulos_de_config_sao_iguais(self):
        um = (RAIZ / "skills" / "preparar-projeto-armanilux" / "scripts" / "config_io.py").read_bytes()
        outro = (RAIZ / "skills" / "relatorio-cronologico-obra" / "scripts" / "config_io.py").read_bytes()
        self.assertEqual(um, outro)
        self.assertTrue(callable(salvar))


if __name__ == "__main__":
    unittest.main()
