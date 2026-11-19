"""Nova exportação de uma obra que já tem relatório: a conversa nova vale e a revisão volta a ser exigida."""

from __future__ import annotations

import os
import sys
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "relatorio-cronologico-obra" / "scripts"))
sys.path.insert(0, str(RAIZ / "examples"))

from common import escrever_json, ler_json  # noqa: E402
from gerar_exemplo import CHAT  # noqa: E402
from run_pipeline import executar  # noqa: E402

FATO_NOVO = "[16/03/2026, 10:00:00] Helena Duarte: O cliente devolveu o termo assinado hoje. Obra encerrada.\n"
FATO_DA_REVISAO = {
    "data": "2026-03-13",
    "hora": "09:00",
    "etapa": "L",
    "autor": "Helena Duarte",
    "ocorrencia": "Vistoria final combinada por telefone, registrada na revisão.",
}


def _texto_docx(caminho: Path) -> str:
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(caminho) as arquivo:
        raiz = ElementTree.fromstring(arquivo.read("word/document.xml"))
        return "".join(no.text or "" for no in raiz.iter(f"{ns}t"))


def _zip(caminho: Path, conversa: str) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho, "w") as arquivo:
        arquivo.writestr("_chat.txt", conversa.encode("utf-8"))
    return caminho


def _sem_midia(conversa: str) -> str:
    """O WhatsApp sem mídia troca cada anexo por uma linha curta: o arquivo fica menor."""
    linhas = []
    for linha in conversa.splitlines(keepends=True):
        linhas.append("<Mídia oculta>\n" if "<anexado:" in linha else linha)
    return "".join(linhas)


class ReexportacaoTeste(unittest.TestCase):
    def setUp(self):
        self._temp = TemporaryDirectory()
        self.base = Path(self._temp.name)
        self._antigo = {k: os.environ.get(k) for k in ("ARMANILUX_REGISTRO", "ARMANILUX_CONFIG")}
        os.environ["ARMANILUX_REGISTRO"] = str(self.base / "registro.json")
        os.environ["ARMANILUX_CONFIG"] = str(self.base / "sem-config.json")
        self.workspace = self.base / "obras"
        self.obra = self.workspace / "1001 - Família Almeida"
        self.relatorios = self.obra / "05-relatorios"

    def tearDown(self):
        for chave, valor in self._antigo.items():
            if valor is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = valor
        self._temp.cleanup()

    def _rodar(self, zip_path: Path) -> None:
        codigo = executar(
            [
                "--workspace", str(self.workspace),
                "--zip", str(zip_path),
                "--obra", "1001",
                "--cliente", "Família Almeida",
                "--skip-transcribe",
                "--skip-keyframes",
                "--downloads", str(self.base / "vazio"),
            ]
        )
        self.assertEqual(codigo, 0)

    def _remontar(self) -> None:
        self.assertEqual(executar(["--workspace", str(self.workspace), "--rebuild-only", "--recalcular", "--obra-dir", str(self.obra)]), 0)

    def _revisar(self) -> None:
        caminho = self.obra / "04-transcricoes" / "analise.json"
        analise = ler_json(caminho)
        analise["revisado"] = True
        analise["eventos_adicionais"] = [FATO_DA_REVISAO]
        escrever_json(caminho, analise)

    def test_conversa_nova_de_obra_revisada_volta_a_ser_rascunho_com_os_fatos_da_revisao(self):
        self._rodar(_zip(self.base / "export1" / "WhatsApp Chat - Obra 1001.zip", CHAT))
        self._revisar()
        self._remontar()
        self.assertTrue((self.relatorios / "Relatorio-Cronologico-Obra-1001-v1.docx").exists())

        self._rodar(_zip(self.base / "export2" / "WhatsApp Chat - Obra 1001.zip", CHAT + FATO_NOVO))

        self.assertFalse((self.relatorios / "Relatorio-Cronologico-Obra-1001-v2.docx").exists())
        rascunho = self.relatorios / "Relatorio-Cronologico-Obra-1001-v2-rascunho.docx"
        self.assertTrue(rascunho.exists())
        analise = ler_json(self.obra / "04-transcricoes" / "analise.json")
        self.assertFalse(analise.get("revisado"))
        ocorrencias = [e.get("ocorrencia", "") for e in analise["eventos"]]
        self.assertIn(FATO_DA_REVISAO["ocorrencia"], ocorrencias)
        texto = _texto_docx(rascunho)
        self.assertIn("RASCUNHO NÃO REVISADO", texto)
        self.assertIn("Vistoria final combinada por telefone", texto)

    def test_exportacao_sem_midia_menor_que_a_antiga_e_a_conversa_usada(self):
        self._rodar(_zip(self.base / "export1" / "WhatsApp Chat - Obra 1001.zip", CHAT))

        nova = _sem_midia(CHAT) + FATO_NOVO
        self.assertLess(len(nova.encode("utf-8")), len(CHAT.encode("utf-8")))
        self._rodar(_zip(self.base / "export2" / "WhatsApp Chat - Obra 1001.zip", nova))

        analise = ler_json(self.obra / "04-transcricoes" / "analise.json")
        self.assertEqual(analise["obra"]["periodo_fim"], "2026-03-16")

        # A remontagem confere os fatos contra a mesma conversa nova, não contra a antiga (maior).
        caminho = self.obra / "04-transcricoes" / "analise.json"
        analise["eventos_adicionais"] = [
            {"data": "2026-03-16", "hora": "10:00", "etapa": "L", "autor": "Helena Duarte", "ocorrencia": "Termo assinado devolvido."}
        ]
        escrever_json(caminho, analise)
        self._remontar()
        conferencia = (self.obra / "04-transcricoes" / "verificacao.md").read_text(encoding="utf-8")
        self.assertNotIn("Termo assinado devolvido", conferencia)

    def test_analise_antiga_sem_marca_da_conversa_usa_a_conversa_mais_recente(self):
        self._rodar(_zip(self.base / "export1" / "WhatsApp Chat - Obra 1001.zip", CHAT))
        self._rodar(_zip(self.base / "export2" / "WhatsApp Chat - Obra 1001.zip", _sem_midia(CHAT) + FATO_NOVO))
        antiga = self.obra / "01-conversas" / "_chat.txt"
        os.utime(antiga, (antiga.stat().st_atime, antiga.stat().st_mtime - 3600))

        caminho = self.obra / "04-transcricoes" / "analise.json"
        analise = ler_json(caminho)
        analise.pop("conversa", None)  # analise.json de antes desta marca
        analise["eventos_adicionais"] = [
            {"data": "2026-03-16", "hora": "10:00", "etapa": "L", "autor": "Helena Duarte", "ocorrencia": "Termo assinado devolvido."}
        ]
        escrever_json(caminho, analise)
        self._remontar()
        conferencia = (self.obra / "04-transcricoes" / "verificacao.md").read_text(encoding="utf-8")
        self.assertNotIn("Termo assinado devolvido", conferencia)


if __name__ == "__main__":
    unittest.main()
