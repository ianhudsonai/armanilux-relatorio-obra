"""Preferências gravadas pelo preparo e lidas pelo relatório."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

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
