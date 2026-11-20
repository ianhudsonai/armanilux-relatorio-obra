"""Formato de entrega escolhido no preparo: Word, PDF ou link (pasta do OneDrive/Google Drive)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "relatorio-cronologico-obra" / "scripts"))
sys.path.insert(0, str(RAIZ / "examples"))

import entrega  # noqa: E402
import run_pipeline  # noqa: E402
from gerar_exemplo import REVISAO_COMPLETA  # noqa: E402


def _pdf_falso(docx: Path) -> Path:
    pdf = docx.with_suffix(".pdf")
    pdf.write_bytes(b"%PDF-1.4 falso")
    return pdf


class FormatoTeste(unittest.TestCase):
    def test_config_antigo_com_pdf_continua_pdf_e_sem_nada_e_word(self):
        self.assertEqual(entrega.formato_entrega({"gerar_pdf": True}), "pdf")
        self.assertEqual(entrega.formato_entrega({"gerar_pdf": False}), "word")
        self.assertEqual(entrega.formato_entrega(None), "word")
        self.assertEqual(entrega.formato_entrega({"formato_entrega": "Link", "gerar_pdf": False}), "link")


class ConverterPdfTeste(unittest.TestCase):
    def test_sem_word_usa_o_libreoffice_e_sem_nenhum_devolve_nada(self):
        with TemporaryDirectory() as temporario:
            docx = Path(temporario) / "r.docx"
            docx.write_bytes(b"docx")

            def sem_word(_docx):
                raise OSError("Word não instalado")

            usados = []

            def libreoffice(arquivo):
                usados.append("libreoffice")
                return _pdf_falso(arquivo)

            self.assertEqual(entrega.converter_pdf(docx, [sem_word, libreoffice]), docx.with_suffix(".pdf"))
            self.assertEqual(usados, ["libreoffice"])
            docx.with_suffix(".pdf").unlink()
            self.assertIsNone(entrega.converter_pdf(docx, [sem_word, lambda _d: None]))

    def test_pdf_velho_do_rascunho_anterior_nao_passa_por_novo(self):
        with TemporaryDirectory() as temporario:
            docx = Path(temporario) / "r.docx"
            pdf = docx.with_suffix(".pdf")
            pdf.write_bytes(b"%PDF velho")
            docx.write_bytes(b"docx novo")
            os.utime(pdf, (docx.stat().st_mtime - 60, docx.stat().st_mtime - 60))
            # O conversor falhou em silêncio e só devolveu o caminho do arquivo que já estava lá.
            self.assertIsNone(entrega.converter_pdf(docx, [lambda arquivo: arquivo.with_suffix(".pdf")]))

    def test_libreoffice_instalado_pelo_winget_fora_do_path_e_achado(self):
        with TemporaryDirectory() as temporario:
            programa = Path(temporario) / "LibreOffice" / "program"
            programa.mkdir(parents=True)
            (programa / "soffice.exe").write_bytes(b"")
            with mock.patch.dict(os.environ, {"ProgramFiles": temporario, "PATH": ""}):
                self.assertEqual(entrega.localizar_libreoffice(), str(programa / "soffice.exe"))


class EntregaPorLinkTeste(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.nuvem = self.base / "OneDrive" / "Armanilux" / "Relatorios"
        config = {
            "pasta_raiz": str(self.base / "Armanilux"),
            "nome": "Ana",
            "funcao": "Gerente",
            "modelo_pasta_obra": "{numero} - {cliente}",
            "formato_entrega": "link",
            "pasta_link": str(self.nuvem),
        }
        caminho = self.base / "config.json"
        caminho.write_text(json.dumps(config), encoding="utf-8")
        self._env = mock.patch.dict(
            os.environ,
            {"ARMANILUX_CONFIG": str(caminho), "ARMANILUX_REGISTRO": str(self.base / "registro.json")},
        )
        self._env.start()
        self._pdf = mock.patch.object(run_pipeline, "converter_pdf", side_effect=_pdf_falso)
        self._pdf.start()

    def tearDown(self):
        self._pdf.stop()
        self._env.stop()
        self._tmp.cleanup()

    def _executar(self, argv: list[str]) -> str:
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            self.assertEqual(run_pipeline.executar(argv), 0)
        return saida.getvalue()

    def test_rascunho_nao_vai_para_a_nuvem_e_a_versao_revisada_vai_em_pdf(self):
        from gerar_exemplo import criar_exemplo

        exemplo = criar_exemplo(self.base / "exemplo")
        workspace = self.base / "obras"
        texto = self._executar(
            ["--workspace", str(workspace), "--zip", str(exemplo), "--skip-transcribe", "--downloads", str(self.base / "vazio")]
        )
        self.assertFalse(self.nuvem.exists())
        self.assertNotIn("RELATORIO_LINK:", texto)
        self.assertIn("RELATORIO_PDF:", texto)

        [caminho] = list(workspace.rglob("analise.json"))
        obra = caminho.parent.parent
        analise = json.loads(caminho.read_text(encoding="utf-8"))
        analise.update(REVISAO_COMPLETA)
        analise["revisado"] = True
        caminho.write_text(json.dumps(analise, ensure_ascii=False), encoding="utf-8")
        texto = self._executar(["--rebuild-only", "--obra-dir", str(obra)])

        copia = self.nuvem / obra.name / "Relatorio-Cronologico-Obra-1001-v1.pdf"
        self.assertTrue(copia.exists())
        self.assertIn(f"RELATORIO_LINK: {copia}", texto)


if __name__ == "__main__":
    unittest.main()
