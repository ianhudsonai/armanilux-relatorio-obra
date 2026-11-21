"""A versão final só sai depois de tudo lido e da conferência independente registrada.

Sem subagentes, ou com pouco contexto por turno, o agente lê o material em partes e marca
cada uma em revisao-progresso.md; a conferência (4.4) vai item por item em conferencia.md.
O script segura a versão final enquanto falta alguma marca, e diz quanto já foi lido.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import run_pipeline  # noqa: E402
from gerar_exemplo import REVISAO_COMPLETA, criar_exemplo  # noqa: E402


def _marcar_tudo(caminho: Path) -> None:
    texto = caminho.read_text(encoding="utf-8-sig")
    caminho.write_text(re.sub(r"^- \[ \]", "- [x]", texto, flags=re.MULTILINE), encoding="utf-8")


class RevisaoEmPartesTeste(unittest.TestCase):
    def setUp(self):
        self._temp = TemporaryDirectory()
        self._antigo = {k: os.environ.get(k) for k in ("ARMANILUX_REGISTRO", "ARMANILUX_CONFIG")}
        os.environ["ARMANILUX_REGISTRO"] = str(Path(self._temp.name) / "registro.json")
        os.environ["ARMANILUX_CONFIG"] = str(Path(self._temp.name) / "sem-config.json")

    def tearDown(self):
        for chave, valor in self._antigo.items():
            if valor is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = valor
        self._temp.cleanup()

    def _rodar(self, argv: list[str]) -> str:
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            self.assertEqual(run_pipeline.executar(argv), 0)
        return saida.getvalue()

    def test_final_espera_a_leitura_inteira_e_a_conferencia(self):
        base = Path(self._temp.name)
        workspace = base / "obras"
        exemplo = criar_exemplo(base / "exemplo")
        texto = self._rodar(["--workspace", str(workspace), "--zip", str(exemplo), "--skip-transcribe", "--downloads", str(base / "vazio")])
        [caminho] = list(workspace.rglob("analise.json"))
        obra = caminho.parent.parent
        transcricoes = obra / "04-transcricoes"
        self.assertTrue(list((transcricoes / "leitura").glob("conversa-*.txt")))
        self.assertRegex(texto, r"LEITURA: 0 de \d+ partes lidas")

        analise = json.loads(caminho.read_text(encoding="utf-8"))
        analise.update(REVISAO_COMPLETA)
        analise.pop("conferencia_independente", None)
        analise["revisado"] = True
        caminho.write_text(json.dumps(analise, ensure_ascii=False), encoding="utf-8")
        relatorios = obra / "05-relatorios"
        final = relatorios / "Relatorio-Cronologico-Obra-1001-v1.docx"

        texto = self._rodar(["--rebuild-only", "--obra-dir", str(obra)])
        self.assertFalse(final.exists())
        self.assertIn("revisao-progresso.md", texto)
        self.assertIn("partes ainda não foram lidas", texto)

        _marcar_tudo(transcricoes / "revisao-progresso.md")
        texto = self._rodar(["--rebuild-only", "--obra-dir", str(obra)])
        self.assertFalse(final.exists())
        self.assertRegex(texto, r"LEITURA: (\d+) de \1 partes lidas")
        self.assertIn("conferencia.md", texto)

        conferencia = transcricoes / "conferencia.md"
        lista = conferencia.read_text(encoding="utf-8-sig")
        self.assertIn("- [ ] ", lista)
        self.assertIn("contrapiso", lista.lower())  # um fato do exemplo, para achar a fonte
        self.assertIn("leitura/conversa-001.txt", lista)  # a parte onde está a data do fato
        _marcar_tudo(conferencia)
        texto = self._rodar(["--rebuild-only", "--obra-dir", str(obra)])
        self.assertFalse(final.exists())  # as marcas sozinhas não bastam: falta dizer como foi feita
        self.assertIn("conferencia_independente", texto)

        analise = json.loads(caminho.read_text(encoding="utf-8"))
        analise["conferencia_independente"] = {"como": "segunda passada", "data": "2026-11-21"}
        caminho.write_text(json.dumps(analise, ensure_ascii=False), encoding="utf-8")
        texto = self._rodar(["--rebuild-only", "--obra-dir", str(obra)])
        self.assertTrue(final.exists(), texto)
        self.assertRegex(texto, r"CONFERENCIA: (\d+) de \1 itens; segunda passada")


if __name__ == "__main__":
    unittest.main()
