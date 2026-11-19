"""A resposta do preparo sobre os áudios vale no relatório: "não" não baixa nada."""

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

from gerar_exemplo import CHAT  # noqa: E402
from run_pipeline import executar  # noqa: E402


class AudioDoPreparoTeste(unittest.TestCase):
    def setUp(self):
        self._temp = TemporaryDirectory()
        self.base = Path(self._temp.name)
        self._antigo = {k: os.environ.get(k) for k in ("ARMANILUX_REGISTRO", "ARMANILUX_CONFIG")}
        os.environ["ARMANILUX_REGISTRO"] = str(self.base / "registro.json")
        os.environ["ARMANILUX_CONFIG"] = str(self.base / "config.json")
        self.workspace = self.base / "obras"
        self.zip = self.base / "export" / "WhatsApp Chat - Obra 1001.zip"
        self.zip.parent.mkdir()
        with zipfile.ZipFile(self.zip, "w") as arquivo:
            arquivo.writestr("_chat.txt", CHAT.encode("utf-8"))
            arquivo.writestr("audio-medicao.opus", b"nao e um audio de verdade")

    def tearDown(self):
        for chave, valor in self._antigo.items():
            if valor is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = valor
        self._temp.cleanup()

    def _config(self, audio: bool) -> None:
        dados = {"pasta_raiz": str(self.base), "formato_entrega": "word", "baixar_modelo_whisper": audio}
        (self.base / "config.json").write_text(json.dumps(dados), encoding="utf-8")

    def _rodar(self, *extra: str) -> tuple[str, list[dict]]:
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = executar(
                [
                    "--workspace", str(self.workspace),
                    "--zip", str(self.zip),
                    "--obra", "1001",
                    "--cliente", "Família Almeida",
                    "--skip-keyframes",
                    "--downloads", str(self.base / "vazio"),
                    *extra,
                ]
            )
        self.assertEqual(codigo, 0, saida.getvalue())
        analise = json.loads(
            (self.workspace / "1001 - Família Almeida" / "04-transcricoes" / "analise.json").read_text(encoding="utf-8")
        )
        return saida.getvalue(), analise["transcricoes"]

    def test_nao_no_preparo_pula_a_transcricao_e_diz_como_ligar(self):
        self._config(audio=False)

        saida, transcricoes = self._rodar()

        self.assertEqual([t["status"] for t in transcricoes], ["ignorado"])
        self.assertNotIn("Carregando o modelo", saida)
        self.assertIn("--transcrever", saida)

    def test_transcrever_vale_mesmo_com_nao_no_preparo(self):
        self._config(audio=False)

        _saida, transcricoes = self._rodar("--transcrever")

        # Sem a biblioteca (CI) fica "indisponivel"; com ela, o áudio falso dá "erro". Nunca "ignorado".
        self.assertNotIn("ignorado", [t["status"] for t in transcricoes])


if __name__ == "__main__":
    unittest.main()
