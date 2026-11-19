"""O instalador só aceita Python que tem as bibliotecas prontas e instala versões testadas."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parents[1]
PREPARO = RAIZ / "skills" / "preparar-projeto-armanilux" / "scripts"
INSTALADOR = PREPARO / "instalar.ps1"


def _funcao_powershell(nome: str) -> str:
    texto = INSTALADOR.read_text(encoding="utf-8-sig")
    achado = re.search(rf"^function {re.escape(nome)}\b.*?^\}}", texto, re.MULTILINE | re.DOTALL)
    assert achado, f"função {nome} não encontrada em instalar.ps1"
    return achado.group(0)


class RequisitosTeste(unittest.TestCase):
    def test_bibliotecas_com_versao_fixa_e_as_duas_copias_iguais(self):
        raiz = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
        da_skill = (PREPARO / "requirements.txt").read_text(encoding="utf-8")
        self.assertEqual(raiz, da_skill)
        linhas = [linha.strip() for linha in da_skill.splitlines() if linha.strip() and not linha.startswith("#")]
        self.assertTrue(linhas)
        for linha in linhas:
            self.assertRegex(linha, r"^[A-Za-z0-9_.-]+==\d[\w.]*$")


@unittest.skipUnless(sys.platform.startswith("win"), "o instalador é do Windows")
class PythonAceitoTeste(unittest.TestCase):
    def _serve(self, versao: int) -> bool:
        with TemporaryDirectory() as temporario:
            falso = Path(temporario) / "python-falso.cmd"
            falso.write_text(f"@echo {versao}\n", encoding="ascii")
            script = _funcao_powershell("Python-Serve") + f"\nif (Python-Serve '{falso}') {{ 'SIM' }} else {{ 'NAO' }}\n"
            saida = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                capture_output=True,
                text=True,
                timeout=60,
            )
        self.assertEqual(saida.returncode, 0, saida.stderr)
        return saida.stdout.strip().splitlines()[-1] == "SIM"

    def test_aceita_so_python_3_10_a_3_13(self):
        self.assertFalse(self._serve(309))
        self.assertTrue(self._serve(310))
        self.assertTrue(self._serve(313))
        self.assertFalse(self._serve(314))


if __name__ == "__main__":
    unittest.main()
