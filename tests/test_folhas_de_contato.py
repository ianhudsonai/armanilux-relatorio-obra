"""Nas folhas de contato, a data de cada foto é a da mensagem que a anexou, não a do nome do arquivo."""

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

from run_pipeline import executar  # noqa: E402

# O celular reaproveitou uma foto antiga: o nome diz 2024, o grupo recebeu em 13/01/2026.
CHAT = (
    "[08/01/2026, 07:59:00] As mensagens e as ligações são protegidas com a criptografia de ponta a ponta.\n"
    "[13/01/2026, 10:30:18] Helena Duarte: Foto da bancada.\n"
    "‎<anexado: IMG-20240305-WA0007.jpg>\n"
    "[14/01/2026, 09:00:00] Helena Duarte: Foto que ninguém citou no texto segue no zip.\n"
    "[15/01/2026, 08:00:00] Helena Duarte: Outra foto.\n"
    "\u200e<anexado: IMG-20240101-WA0002.jpg>\n"
)


def _jpg() -> bytes:
    from PIL import Image

    saida = io.BytesIO()
    Image.new("RGB", (40, 30), (120, 90, 60)).save(saida, format="JPEG")
    return saida.getvalue()


class DatasDasFotosTeste(unittest.TestCase):
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

    def test_data_da_mensagem_que_anexou_a_foto(self):
        zip_path = self.base / "export" / "WhatsApp Chat - Obra 1001.zip"
        zip_path.parent.mkdir()
        with zipfile.ZipFile(zip_path, "w") as arquivo:
            arquivo.writestr("_chat.txt", CHAT.encode("utf-8"))
            arquivo.writestr("IMG-20240305-WA0007.jpg", _jpg())
            arquivo.writestr("IMG-20251120-WA0001.jpg", _jpg())
            arquivo.writestr("IMG-20240101-WA0002.JPG", _jpg())  # a mensagem cita ".jpg", minúsculo
        workspace = self.base / "obras"
        with redirect_stdout(io.StringIO()):
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
        self.assertEqual(codigo, 0)
        indice = json.loads(
            (workspace / "1001 - Família Almeida" / "04-transcricoes" / "folhas-de-contato" / "indice.json").read_text(encoding="utf-8")
        )
        datas = {item["arquivo"]: item["data"] for folha in indice.values() for item in folha}
        self.assertEqual(datas["IMG-20240305-WA0007.jpg"], "13/01/2026")
        self.assertEqual(datas["IMG-20240101-WA0002.JPG"], "15/01/2026")
        # Sem mensagem que cite o arquivo, sobra o nome; a folha diz de onde veio a data.
        self.assertEqual(datas["IMG-20251120-WA0001.jpg"], "20/11/2025 (nome do arquivo)")


if __name__ == "__main__":
    unittest.main()
