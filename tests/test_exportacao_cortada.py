"""O WhatsApp corta exportações muito grandes sem avisar: o relatório avisa e registra a lacuna."""

from __future__ import annotations

import io
import json
import os
import sys
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "relatorio-cronologico-obra" / "scripts"))
sys.path.insert(0, str(RAIZ / "examples"))

from analyze import lacunas_automaticas  # noqa: E402
from gerar_exemplo import CHAT  # noqa: E402
from parse_whatsapp import analisar_conversa  # noqa: E402
from run_pipeline import executar  # noqa: E402

# O exemplo começa com o aviso de criptografia; sem essa linha, parece uma exportação cortada.
CORTADA = CHAT.split("\n", 1)[1]


class LacunaTeste(unittest.TestCase):
    def test_conversa_sem_o_inicio_do_grupo_vira_lacuna_com_a_primeira_data(self):
        lacunas = lacunas_automaticas(analisar_conversa(CORTADA), [], [])
        self.assertEqual(
            lacunas,
            [
                "A exportação do WhatsApp parece cortada: a conversa começa em 08/01/2026, sem o início do grupo. "
                "O que veio antes é dado não identificado."
            ],
        )

    def test_conversa_completa_nao_tem_essa_lacuna(self):
        self.assertEqual(lacunas_automaticas(analisar_conversa(CHAT), [], []), [])

    def test_criacao_do_grupo_tambem_marca_o_inicio(self):
        android = (
            "05/09/2025 09:40 - Ana Lima criou o grupo \"Obra 1001\"\n"
            "05/09/2025 09:41 - Ana Lima: Bom dia a todos.\n"
        )
        self.assertEqual(lacunas_automaticas(analisar_conversa(android), [], []), [])


class AvisoNaExecucaoTeste(unittest.TestCase):
    def setUp(self):
        self._temp = TemporaryDirectory()
        self.base = Path(self._temp.name)
        self._antigo = {k: os.environ.get(k) for k in ("ARMANILUX_REGISTRO", "ARMANILUX_CONFIG")}
        os.environ["ARMANILUX_REGISTRO"] = str(self.base / "registro.json")
        os.environ["ARMANILUX_CONFIG"] = str(self.base / "sem-config.json")

    def tearDown(self):
        for chave, valor in self._antigo.items():
            if valor is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = valor
        self._temp.cleanup()

    def test_pipeline_avisa_e_o_relatorio_registra(self):
        zip_path = self.base / "export" / "WhatsApp Chat - Obra 1001.zip"
        zip_path.parent.mkdir()
        with zipfile.ZipFile(zip_path, "w") as arquivo:
            arquivo.writestr("_chat.txt", CORTADA.encode("utf-8"))
        workspace = self.base / "obras"
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = executar(
                [
                    "--workspace", str(workspace),
                    "--zip", str(zip_path),
                    "--obra", "1001",
                    "--cliente", "Família Almeida",
                    "--skip-transcribe",
                    "--skip-keyframes",
                    "--downloads", str(self.base / "vazio"),
                ]
            )
        self.assertEqual(codigo, 0, saida.getvalue())
        self.assertIn("parece cortada", saida.getvalue())
        self.assertIn("sem mídia", saida.getvalue())
        analise = json.loads((workspace / "1001 - Família Almeida" / "04-transcricoes" / "analise.json").read_text(encoding="utf-8"))
        self.assertTrue(any("parece cortada" in lacuna for lacuna in analise["lacunas"]))


if __name__ == "__main__":
    unittest.main()
