"""O exemplo fictício percorre o pipeline e sai um .docx no formato da casa."""

from __future__ import annotations

import sys
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

from run_pipeline import executar  # noqa: E402


def _texto_docx(caminho: Path) -> str:
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(caminho) as arquivo:
        raiz = ElementTree.fromstring(arquivo.read("word/document.xml"))
        return "".join(no.text or "" for no in raiz.iter(f"{ns}t"))


class PipelineTeste(unittest.TestCase):
    def test_exemplo_ficticio_gera_docx(self):
        from gerar_exemplo import criar_exemplo

        with TemporaryDirectory() as temporario:
            base = Path(temporario)
            exemplo = criar_exemplo(base / "exemplo")
            workspace = base / "obras"
            codigo = executar(
                [
                    "--workspace",
                    str(workspace),
                    "--zip",
                    str(exemplo),
                    "--skip-transcribe",
                    "--downloads",
                    str(base / "vazio"),
                ]
            )
            self.assertEqual(codigo, 0)
            obra = workspace / "1001 - Família Almeida"
            self.assertTrue((obra / "01-conversas" / "_chat.txt").exists())
            self.assertTrue((obra / "02-projetos-pdf" / "Projeto-preliminar-cozinha.pdf").exists())
            self.assertTrue((obra / "03-midias" / "chapa-lote-3.jpg").exists())
            self.assertTrue((obra / "03-midias" / "audio-medicao.opus").exists())
            relatorios = list((obra / "05-relatorios").glob("Relatorio-Cronologico-Obra-1001-v1.docx"))
            self.assertEqual(len(relatorios), 1)
            from common import ler_json

            analise = ler_json(obra / "04-transcricoes" / "analise.json")
            self.assertEqual(analise["obra"]["cliente"], "Família Almeida")
            self.assertEqual(analise["obra"]["numero"], "1001")
            self.assertEqual(analise["obra"]["prazo_contratual"], "")
            self.assertEqual(analise["kpis"]["revisoes"], 2)
            self.assertEqual(analise["kpis"]["maior_intervalo"], 11)
            self.assertGreaterEqual(analise["kpis"]["interferencias"], 4)
            intervalo_medicao = next(
                item for item in analise["intervalos"] if item["inicio"] == "2026-01-13" and item["fim"] == "2026-01-20"
            )
            self.assertEqual(intervalo_medicao["dias_uteis"], 5)
            self.assertEqual(intervalo_medicao["leitura"], "Atenção")
            longo = next(item for item in analise["intervalos"] if item["dias_uteis"] == 11)
            self.assertEqual(longo["leitura"], "Intervalo longo")
            self.assertTrue(any(item["status"] == "Pendente" for item in analise["pendencias"]))
            self.assertNotIn("K", {item["etapa"] for item in analise["eventos"]})
            textos = " ".join(item.get("texto", "") for item in analise["documentos_texto"])
            self.assertIn("Projeto preliminar", textos)
            self.assertIn("cuba", textos.lower())

            texto = _texto_docx(relatorios[0])
            for trecho in (
                "RELATÓRIO CRONOLÓGICO DE OBRA",
                "A – Aprovação de chapas",
                "B – Solicitação de vistas",
                "C – Data da medição",
                "D – Envio do projeto preliminar",
                "E – Solicitações de revisões",
                "F – Envios de projetos preliminares",
                "G – Aprovações dos projetos",
                "H – Data das entregas",
                "I – Data da entrada da equipe",
                "J – Ocorrências e interferências",
                "L – Data da conclusão",
                "Marco",
                "Situação",
                "dado não identificado",
                "Mídia: chapa-lote-3.jpg",
                "Carnaval",
                "9 de julho",
                "25 de janeiro",
                "Corpus Christi",
                "Natureza",
                "Diagnóstico",
                "Pendente",
                "Intervalos relevantes",
                "Nota de rastreabilidade",
            ):
                self.assertIn(trecho, texto, trecho)
            self.assertNotIn("Etapa K", texto)
            with zipfile.ZipFile(relatorios[0]) as arquivo:
                midias = [nome for nome in arquivo.namelist() if nome.startswith("word/media/")]
            self.assertGreaterEqual(len(midias), 2)
            codigo_v2 = executar(
                ["--workspace", str(workspace), "--rebuild-only", "--obra-dir", str(obra)]
            )
            self.assertEqual(codigo_v2, 0)
            self.assertTrue((obra / "05-relatorios" / "Relatorio-Cronologico-Obra-1001-v2.docx").exists())


if __name__ == "__main__":
    unittest.main()
