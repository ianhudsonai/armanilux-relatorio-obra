"""Ninguém precisa decorar o caminho: --mostrar abre a pasta com o Word selecionado."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import run_pipeline  # noqa: E402


class EntregaTeste(unittest.TestCase):
    def _obra(self, base: Path) -> Path:
        from gerar_exemplo import criar_exemplo

        workspace = base / "obras"
        exemplo = criar_exemplo(base / "exemplo")
        codigo = run_pipeline.executar(
            ["--workspace", str(workspace), "--zip", str(exemplo), "--skip-transcribe", "--downloads", str(base / "vazio")]
        )
        self.assertEqual(codigo, 0)
        # O nome da pasta segue o modelo do config.json deste computador.
        [analise] = list(workspace.rglob("analise.json"))
        return analise.parent.parent

    def test_mostrar_abre_a_pasta_com_o_relatorio_novo(self):
        with TemporaryDirectory() as temporario:
            obra = self._obra(Path(temporario))
            with mock.patch.object(run_pipeline, "mostrar_no_explorer") as mostrar:
                run_pipeline.executar(["--rebuild-only", "--obra-dir", str(obra), "--mostrar"])
            mostrar.assert_called_once_with(obra / "05-relatorios" / "Relatorio-Cronologico-Obra-1001-v2.docx")

    def test_sem_mostrar_nao_abre_nada(self):
        with TemporaryDirectory() as temporario:
            obra = self._obra(Path(temporario))
            with mock.patch.object(run_pipeline, "mostrar_no_explorer") as mostrar:
                run_pipeline.executar(["--rebuild-only", "--obra-dir", str(obra)])
            mostrar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
