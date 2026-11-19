"""O relatório diz o que não pôde ler (lacunas de contexto), em vez de calar."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import completar_relato, montar_analise  # noqa: E402
from parse_whatsapp import analisar_conversa  # noqa: E402

CHAT = (
    "05/09/2025 09:49 - As mensagens e as ligações são protegidas com a criptografia de ponta a ponta.\n"
    "05/09/2025 09:50 - Ana Lima: <Mídia oculta>\nProjeto R00.pdf\n"
    "05/09/2025 09:51 - Ana Lima: <Mídia oculta>\nPlanta.dwg\n"
    "05/09/2025 09:52 - Bruno Reis: <Mídia oculta>\n"
    "06/09/2025 10:00 - Bruno Reis: Medição in loco realizada hoje.\n"
)


def _analise(**extra):
    return montar_analise(
        analisar_conversa(CHAT),
        fonte="teste.zip",
        arquivos=[],
        documentos=[
            {"arquivo": "Corte.pdf", "texto": "", "erro": "nenhum texto identificado no arquivo"},
            {"arquivo": "Memorial.docx", "texto": "texto lido", "erro": ""},
        ],
        transcricoes=[
            {"arquivo": "PTT-1.opus", "status": "ok", "texto": "fala"},
            {"arquivo": "PTT-2.opus", "status": "erro", "texto": ""},
        ],
        quadros=[],
        overrides={"numero": "1001", "cliente": "Cliente Teste"},
        **extra,
    )


class LacunasTeste(unittest.TestCase):
    def test_lacunas_automaticas(self):
        analise = _analise()
        self.assertEqual(
            analise["lacunas"],
            [
                "2 arquivos enviados no grupo não vieram na exportação do WhatsApp.",
                "1 foto, áudio ou vídeo não veio na exportação.",
                "1 documento sem texto legível pelo computador.",
                "1 áudio ou vídeo sem transcrição; o conteúdo desses itens é dado não identificado.",
            ],
        )
        # Os nomes ficam no analise.json para o agente, não no Word.
        self.assertEqual(analise["arquivos_fora_da_exportacao"], ["Projeto R00.pdf", "Planta.dwg"])

    def test_lacuna_escrita_na_revisao_entra_e_nao_repete(self):
        analise = _analise()
        analise["lacunas_adicionais"] = ["O prazo contratual não foi declarado no grupo."]
        refeita = completar_relato(completar_relato(analise))
        self.assertEqual(refeita["lacunas"][-1], "O prazo contratual não foi declarado no grupo.")
        self.assertEqual(len(refeita["lacunas"]), 5)

    def test_lacunas_aparecem_na_nota_metodologica(self):
        from docx import Document

        import build_docx

        with TemporaryDirectory() as pasta:
            destino = build_docx.montar_docx(_analise(), Path(pasta) / "r.docx", None, None)
            textos = [p.text for p in Document(str(destino)).paragraphs]
        limites = next(t for t in textos if t.startswith("Limites do material:"))
        self.assertIn("2 arquivos enviados no grupo", limites)
        self.assertNotIn("Lacunas de contexto", textos)

    def test_analise_antiga_sem_lacunas_nao_afirma_que_nao_ha_lacuna(self):
        from docx import Document

        import build_docx

        analise = _analise()
        del analise["lacunas"]
        with TemporaryDirectory() as pasta:
            destino = build_docx.montar_docx(analise, Path(pasta) / "r.docx", None, None)
            textos = [p.text for p in Document(str(destino)).paragraphs]
        limites = next(t for t in textos if t.startswith("Limites do material:"))
        self.assertIn("dado não identificado", limites)


class PlanilhaTeste(unittest.TestCase):
    def test_planilha_e_lida_e_formato_desconhecido_vira_lacuna(self):
        import zipfile

        from extract_documents import extrair_pasta

        with TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            with zipfile.ZipFile(raiz / "Cronograma.xlsx", "w") as planilha:
                planilha.writestr(
                    "xl/sharedStrings.xml",
                    '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                    "<si><t>Entrega bancada</t></si><si><t>Medição cozinha</t></si></sst>",
                )
            (raiz / "Antigo.xls").write_bytes(b"\xd0\xcf\x11\xe0 binario")
            lidos = {item["arquivo"]: item for item in extrair_pasta(raiz)}
        self.assertIn("Entrega bancada", lidos["Cronograma.xlsx"]["texto"])
        self.assertIn("Medição cozinha", lidos["Cronograma.xlsx"]["texto"])
        self.assertEqual(lidos["Antigo.xls"]["texto"], "")


if __name__ == "__main__":
    unittest.main()
