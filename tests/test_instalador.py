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


class ConferenciasDoInstaladorTeste(unittest.TestCase):
    """Visto na avaliação de prontidão: o instalador não olhava o disco nem testava as bibliotecas."""

    def setUp(self):
        self.texto = INSTALADOR.read_text(encoding="utf-8-sig")

    def test_confere_espaco_livre_antes_de_instalar(self):
        self.assertIn("function Conferir-Espaco", self.texto)
        self.assertLess(self.texto.index("\nConferir-Espaco"), self.texto.index("Winget-Instalar \"Python.Python.3.12\""))

    def test_testa_as_bibliotecas_depois_do_pip_e_tenta_o_vc_redist(self):
        depois_do_pip = self.texto.split("pip install -r $requisitos", 1)[1]
        self.assertIn("import docx, faster_whisper, matplotlib, holidays, PIL, numpy", depois_do_pip)
        self.assertIn("Microsoft.VCRedist.2015+.x64", depois_do_pip)

    def test_skill_avisa_quanto_tempo_leva(self):
        skill = (PREPARO.parent / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("até 40 minutos", skill)
        self.assertIn("não feche o ChatGPT", skill)


@unittest.skipUnless(sys.platform.startswith("win"), "o instalador é do Windows")
class EspacoTeste(unittest.TestCase):
    def _suficiente(self, livre_gb: float) -> bool:
        script = _funcao_powershell("Espaco-Suficiente") + f"\nif (Espaco-Suficiente {livre_gb}) {{ 'SIM' }} else {{ 'NAO' }}\n"
        saida = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(saida.returncode, 0, saida.stderr)
        return saida.stdout.strip().splitlines()[-1] == "SIM"

    def test_pede_pelo_menos_3_gb(self):
        self.assertFalse(self._suficiente(2.5))
        self.assertTrue(self._suficiente(3))


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
