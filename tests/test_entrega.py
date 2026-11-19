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
            mostrar.assert_called_once_with(obra / "05-relatorios" / "Relatorio-Cronologico-Obra-1001-v1-rascunho.docx")

    def test_remontar_rascunho_nao_gasta_versao(self):
        import json

        with TemporaryDirectory() as temporario:
            obra = self._obra(Path(temporario))
            relatorios = obra / "05-relatorios"
            rascunho = relatorios / "Relatorio-Cronologico-Obra-1001-v1-rascunho.docx"
            self.assertEqual(sorted(p.name for p in relatorios.glob("*.docx")), [rascunho.name])
            run_pipeline.executar(["--rebuild-only", "--obra-dir", str(obra)])
            run_pipeline.executar(["--rebuild-only", "--obra-dir", str(obra)])
            self.assertEqual(sorted(p.name for p in relatorios.glob("*.docx")), [rascunho.name])

            [caminho] = list(obra.rglob("analise.json"))
            analise = json.loads(caminho.read_text(encoding="utf-8"))
            analise["revisado"] = True
            caminho.write_text(json.dumps(analise, ensure_ascii=False), encoding="utf-8")
            run_pipeline.executar(["--rebuild-only", "--obra-dir", str(obra)])
            self.assertTrue((relatorios / "Relatorio-Cronologico-Obra-1001-v1.docx").exists())
            run_pipeline.executar(["--rebuild-only", "--obra-dir", str(obra)])
            # Remontar depois de revisado regrava o mesmo v1; v2 só com conversa nova.
            self.assertFalse((relatorios / "Relatorio-Cronologico-Obra-1001-v2.docx").exists())
            self.assertEqual(sorted(p.name for p in relatorios.glob("*.docx")), ["Relatorio-Cronologico-Obra-1001-v1.docx"])

    def test_rascunho_aberto_no_word_nao_derruba(self):
        with TemporaryDirectory() as temporario:
            obra = self._obra(Path(temporario))
            relatorios = obra / "05-relatorios"
            original = run_pipeline.montar_docx
            chamadas = []

            def montar(analise, destino, *resto):
                chamadas.append(destino)
                if len(chamadas) == 1:
                    raise PermissionError("arquivo aberto no Word")
                return original(analise, destino, *resto)

            with mock.patch.object(run_pipeline, "montar_docx", side_effect=montar):
                self.assertEqual(run_pipeline.executar(["--rebuild-only", "--obra-dir", str(obra)]), 0)
            self.assertTrue((relatorios / "Relatorio-Cronologico-Obra-1001-v1-rascunho-2.docx").exists())

    def test_avisa_prazo_com_fonte_posterior_ou_sem_data(self):
        import contextlib
        import io
        import json

        with TemporaryDirectory() as temporario:
            obra = self._obra(Path(temporario))
            [caminho] = list(obra.rglob("analise.json"))
            analise = json.loads(caminho.read_text(encoding="utf-8"))
            analise["prazos_contratuais"] = [
                {"descricao": "Instalação até 5 d.u.", "inicio": "2026-01-12", "fim": "2026-01-16", "limite_du": 5, "fonte": "orçamento", "fonte_data": "2026-02-01"},
                {"descricao": "Medição até 6 d.u.", "inicio": "2026-01-12", "fim": "2026-01-14", "limite_du": 6, "fonte": "mensagem"},
            ]
            caminho.write_text(json.dumps(analise, ensure_ascii=False), encoding="utf-8")
            saida = io.StringIO()
            with contextlib.redirect_stdout(saida):
                run_pipeline.executar(["--rebuild-only", "--recalcular", "--obra-dir", str(obra)])
            texto = saida.getvalue()
            self.assertIn("Aviso de prazo: \"Instalação até 5 d.u.\": fonte de 01/02/2026, depois do início do período (12/01/2026).", texto)
            self.assertIn("Aviso de prazo: \"Medição até 6 d.u.\": sem fonte_data.", texto)

    def test_sem_mostrar_nao_abre_nada(self):
        with TemporaryDirectory() as temporario:
            obra = self._obra(Path(temporario))
            with mock.patch.object(run_pipeline, "mostrar_no_explorer") as mostrar:
                run_pipeline.executar(["--rebuild-only", "--obra-dir", str(obra)])
            mostrar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
