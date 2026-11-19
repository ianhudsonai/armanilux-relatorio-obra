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
        lacunas = _analise()["lacunas"]
        self.assertEqual(
            lacunas,
            [
                "2 arquivos enviados no grupo não vieram na exportação do WhatsApp (Projeto R00.pdf, Planta.dwg); "
                "o conteúdo deles é dado não identificado.",
                "1 mídia sem nome (foto, áudio ou vídeo) não veio na exportação; o conteúdo é dado não identificado.",
                "1 documento sem texto legível pelo computador (Corte.pdf); conferir o arquivo original.",
                "1 áudio ou vídeo sem transcrição (PTT-2.opus); o que foi falado é dado não identificado.",
            ],
        )

    def test_lacuna_escrita_na_revisao_entra_e_nao_repete(self):
        analise = _analise()
        analise["lacunas_adicionais"] = ["O prazo contratual não foi declarado no grupo."]
        refeita = completar_relato(completar_relato(analise))
        self.assertEqual(refeita["lacunas"][-1], "O prazo contratual não foi declarado no grupo.")
        self.assertEqual(len(refeita["lacunas"]), 5)

    def test_word_tem_secao_de_lacunas(self):
        from docx import Document

        import build_docx

        with TemporaryDirectory() as pasta:
            destino = build_docx.montar_docx(_analise(), Path(pasta) / "r.docx", None, None)
            textos = [p.text for p in Document(str(destino)).paragraphs]
        indice = textos.index("Lacunas de contexto")
        self.assertTrue(textos[indice + 2].startswith("• 2 arquivos enviados no grupo"))


if __name__ == "__main__":
    unittest.main()
