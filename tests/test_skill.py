"""A skill cabe no instalador do Codex e o repositório público não traz obra real."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SKILL = RAIZ / "skills" / "relatorio-cronologico-obra"
# Os nomes ficam partidos para o próprio teste não gravar a obra real no arquivo.
_TRECHOS = (
    "Brand" + "ão",
    "Brand" + "ao",
    "Stew" + "art",
    "Den" + "ise",
    "And" + "ré",
    "And" + "re",
    "92" + "34",
)
PROIBIDOS = re.compile("|".join(re.escape(trecho) for trecho in _TRECHOS), re.IGNORECASE)


def _frontmatter_valido(pasta: Path, nome_esperado: str) -> bool:
    texto = (pasta / "SKILL.md").read_text(encoding="utf-8")
    if not texto.startswith("---\n"):
        return False
    fim = texto.find("\n---", 3)
    frente = texto[4:fim]
    nome = re.search(r"^name:\s*(\S+)\s*$", frente, re.MULTILINE)
    descricao = re.search(r"^description:\s*(.+)$", frente, re.MULTILINE)
    if not nome or not descricao:
        return False
    if nome.group(1) != nome_esperado or nome.group(1) != pasta.name:
        return False
    texto_descricao = descricao.group(1).strip()
    if not texto_descricao or len(texto_descricao) > 1024:
        return False
    if "<" in texto_descricao or ">" in texto_descricao:
        return False
    return True


class SkillTeste(unittest.TestCase):
    def test_frontmatter_compativel_com_o_validador_da_openai(self):
        texto = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(texto.startswith("---\n"))
        fim = texto.find("\n---", 3)
        self.assertGreater(fim, 0)
        frente = texto[4:fim]
        chaves = [
            linha.split(":", 1)[0]
            for linha in frente.splitlines()
            if linha.strip() and not linha.startswith((" ", "\t"))
        ]
        permitidas = {"name", "description", "license", "allowed-tools", "metadata"}
        self.assertTrue(set(chaves) <= permitidas)
        self.assertIn("name", chaves)
        self.assertIn("description", chaves)
        nome = re.search(r"^name:\s*(\S+)\s*$", frente, re.MULTILINE).group(1)
        self.assertEqual(nome, "relatorio-cronologico-obra")
        self.assertEqual(nome, SKILL.name)
        self.assertLessEqual(len(nome), 64)
        self.assertIsNone(re.search(r"[^a-z0-9-]", nome))
        self.assertFalse(nome.startswith("-") or nome.endswith("-") or "--" in nome)
        descricao = re.search(r"^description:\s*(.+)$", frente, re.MULTILINE).group(1).strip()
        self.assertTrue(descricao)
        self.assertLessEqual(len(descricao), 1024)
        self.assertNotIn("<", descricao)
        self.assertNotIn(">", descricao)
        self.assertIn("relatório", descricao.lower())
        self.assertIn("whatsapp", descricao.lower())

    def test_arquivos_que_o_instalador_e_o_windows_esperam(self):
        preparar = RAIZ / "skills" / "preparar-projeto-armanilux"
        self.assertTrue((SKILL / "scripts" / "run_pipeline.py").is_file())
        self.assertTrue((SKILL / "scripts" / "config_io.py").is_file())
        self.assertFalse((SKILL / "scripts" / "instalar.ps1").exists())
        self.assertTrue((preparar / "scripts" / "instalar.ps1").is_file())
        self.assertTrue((preparar / "scripts" / "preparar.py").is_file())
        self.assertTrue((RAIZ / "AGENTS.md").is_file())
        yaml = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$relatorio-cronologico-obra", yaml)
        curta = re.search(r'short_description:\s*"(.*)"', yaml).group(1)
        self.assertGreaterEqual(len(curta), 25)
        self.assertLessEqual(len(curta), 64)
        bat = (RAIZ / "instalar.bat").read_text(encoding="utf-8")
        self.assertIn(r"skills\preparar-projeto-armanilux\scripts\instalar.ps1", bat)
        self.assertTrue((RAIZ / "LICENSE").is_file())

    def test_as_duas_skills_e_o_instalador_interno(self):
        preparar = RAIZ / "skills" / "preparar-projeto-armanilux"
        for pasta, nome in ((SKILL, "relatorio-cronologico-obra"), (preparar, "preparar-projeto-armanilux")):
            self.assertTrue(_frontmatter_valido(pasta, nome))
        texto = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("$preparar-projeto-armanilux", texto)
        self.assertIn("config.json", texto)
        self.assertIn("preparar-projeto-armanilux\\scripts\\instalar.ps1", texto)
        preparo = (preparar / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Quer que eu também entenda os áudios e vídeos das conversas? Isso precisa de um download único (cerca de 484 MB), mas é seguro e fica só no seu computador. Sim ou não.",
            preparo,
        )
        self.assertNotIn("modelo de voz", preparo.lower())
        self.assertIn("scripts/instalar.ps1", preparo)
        self.assertIn("powershell -ExecutionPolicy Bypass -File", preparo)
        self.assertIn("Python.Python.3.12", preparo)
        self.assertIn("--scope user", preparo)
        self.assertNotIn("dois cliques em instalar.bat", preparo.lower())
        instalador = (preparar / "scripts" / "instalar.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("--scope user", instalador)
        self.assertIn("Python.Python.3.12", instalador)
        self.assertIn('Join-Path $PSScriptRoot "requirements.txt"', instalador)
        self.assertIn("GetEnvironmentVariable", instalador)
        agentes = (RAIZ / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("instale as skills", agentes)
        self.assertIn("skills/preparar-projeto-armanilux", agentes)
        self.assertIn("skills/relatorio-cronologico-obra", agentes)
        self.assertIn(".codex/skills", agentes)
        self.assertIn(".claude/skills", agentes)
        self.assertIn("Não instale em outro aplicativo", agentes)
        self.assertIn("Não procure outras ferramentas", agentes)
        self.assertNotIn("Se existir a pasta", agentes)
        self.assertIn("Missing --path", agentes)
        leia_me = (RAIZ / "README.md").read_text(encoding="utf-8")
        # Linha de colagem que o $skill-installer entende sem ler o AGENTS.md: um endereço por skill.
        colagem = (
            "$skill-installer instale estas skills:\n"
            "https://github.com/ianhudsonai/armanilux-relatorio-obra/tree/main/skills/preparar-projeto-armanilux\n"
            "https://github.com/ianhudsonai/armanilux-relatorio-obra/tree/main/skills/relatorio-cronologico-obra\n"
        )
        self.assertIn(colagem, leia_me)
        self.assertIn(colagem, agentes)
        self.assertNotIn("armanilux-relatorio-obra instale as skills\n```", leia_me)
        self.assertNotIn("the claude command exists", leia_me.lower())
        self.assertIn("only into the app", leia_me.lower())

    def test_acha_programa_instalado_pelo_winget_fora_do_path(self):
        import os
        import sys
        from tempfile import TemporaryDirectory

        sys.path.insert(0, str(SKILL / "scripts"))
        from common import localizar_ferramenta

        with TemporaryDirectory() as temporario:
            links = Path(temporario) / "Microsoft" / "WinGet" / "Links"
            links.mkdir(parents=True)
            executavel = links / "ffmpeg-teste-armanilux.exe"
            executavel.write_bytes(b"")
            caminho_antigo = os.environ.get("PATH", "")
            local_antigo = os.environ.get("LOCALAPPDATA")
            os.environ["LOCALAPPDATA"] = temporario
            try:
                achado = localizar_ferramenta("ffmpeg-teste-armanilux")
                self.assertEqual(Path(achado).resolve(), executavel.resolve())
            finally:
                os.environ["PATH"] = caminho_antigo
                if local_antigo is None:
                    os.environ.pop("LOCALAPPDATA", None)
                else:
                    os.environ["LOCALAPPDATA"] = local_antigo

    def test_repositorio_nao_traz_nome_de_obra_real(self):
        extensoes = {".md", ".py", ".txt", ".yml", ".yaml", ".ps1", ".bat", ".json"}
        for caminho in RAIZ.rglob("*"):
            if not caminho.is_file() or caminho.suffix.lower() not in extensoes:
                continue
            if any(parte in {".git", "__pycache__", ".venv"} for parte in caminho.parts):
                continue
            texto = caminho.read_text(encoding="utf-8", errors="ignore")
            self.assertIsNone(PROIBIDOS.search(texto), f"{caminho}: {PROIBIDOS.search(texto)}")


if __name__ == "__main__":
    unittest.main()
