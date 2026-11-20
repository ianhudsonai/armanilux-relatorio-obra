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


class InstalacaoTeste(unittest.TestCase):
    def test_linha_de_colagem_tem_saida_sem_python(self):
        # O $skill-installer é um script Python; PC novo não tem Python antes do preparo.
        for arquivo in ("README.md", "AGENTS.md"):
            texto = (RAIZ / arquivo).read_text(encoding="utf-8")
            bloco = texto.split("$skill-installer instale estas skills:", 1)[1].split("```", 1)[0]
            self.assertIn("Python", bloco, arquivo)
            self.assertIn("zip", bloco, arquivo)
        agentes = (RAIZ / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Invoke-WebRequest", agentes)
        self.assertIn("archive/refs/heads/main.zip", agentes)
        self.assertIn("Expand-Archive", agentes)

    def test_link_do_repositorio_basta_para_o_agente_instalar(self):
        # A pessoa cola só o link do repositório e "instale aqui": o agente lê o topo do README e segue o INSTALL.md.
        leia_me = (RAIZ / "README.md").read_text(encoding="utf-8")
        topo = leia_me[:1500]
        self.assertIn("Para o agente", topo)
        self.assertIn("raw.githubusercontent.com/ianhudsonai/armanilux-relatorio-obra/main/INSTALL.md", topo)
        instalar = (RAIZ / "INSTALL.md").read_text(encoding="utf-8")
        for trecho in (".claude\\skills", ".agents\\skills", ".codex\\skills", "Invoke-WebRequest", "Expand-Archive",
                       "archive/refs/heads/main.zip", "SKILL.md", "$preparar-projeto-armanilux", "Nunca nos dois"):
            self.assertIn(trecho, instalar)
        self.assertNotIn("três linhas", leia_me)
        self.assertNotIn("tres linhas", (RAIZ / "instalar.bat").read_text(encoding="utf-8"))
        self.assertIn("INSTALL.md", (RAIZ / "AGENTS.md").read_text(encoding="utf-8"))

    def test_instalador_do_preparo_e_achado_pela_pasta_da_skill(self):
        import sys

        sys.path.insert(0, str(SKILL / "scripts"))
        from run_pipeline import instalador_do_preparo

        self.assertEqual(
            instalador_do_preparo(),
            (RAIZ / "skills" / "preparar-projeto-armanilux" / "scripts" / "instalar.ps1").resolve(),
        )
        self.assertTrue(instalador_do_preparo().is_file())
        for arquivo in (SKILL / "SKILL.md", SKILL / "scripts" / "run_pipeline.py"):
            texto = arquivo.read_text(encoding="utf-8")
            self.assertNotIn(".codex\\skills\\preparar", texto, arquivo.name)
            self.assertNotIn(".codex\\\\skills\\\\preparar", texto, arquivo.name)


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

    def test_skill_manda_confirmar_obra_e_cliente_antes_de_gerar(self):
        texto = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("Só pergunte se o script disser que não conseguiu", texto)
        self.assertIn("certo?", texto)
        self.assertIn('--indice 1 --obra "8977" --cliente', texto)

    def test_comandos_longos_com_tempo_limite_longo_ou_em_segundo_plano(self):
        preparar = RAIZ / "skills" / "preparar-projeto-armanilux"
        for pasta in (SKILL, preparar):
            texto = (pasta / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("tempo limite", texto, pasta.name)
            self.assertIn("segundo plano", texto, pasta.name)
            self.assertIn("rode de novo", texto, pasta.name)

    def test_agente_espera_a_instalacao_terminar_e_avisa_se_o_turno_acabar(self):
        # Visto no Codex: o agente encerrou o turno no meio da instalação e a pessoa não sabia que devia escrever "continue".
        preparar = RAIZ / "skills" / "preparar-projeto-armanilux"
        for pasta in (SKILL, preparar):
            texto = (pasta / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("código de saída", texto, pasta.name)
            self.assertIn('Escreva "continue" para eu terminar.', texto, pasta.name)

    def test_skill_do_relatorio_e_curta_e_os_detalhes_da_revisao_ficam_em_references(self):
        # Ian: o passo a passo fica curto; regras de cada campo da revisão ficam em references/revisao.md.
        texto = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        corpo = texto.split("\n---", 1)[1]
        self.assertLessEqual(len(corpo.split()), 2000)
        self.assertIn("references/revisao.md", texto)
        self.assertTrue((SKILL / "references" / "revisao.md").is_file())
        # A skill acha o zip sozinha: nunca pede o caminho.
        self.assertIn("Nunca peça o caminho do zip", texto)
        self.assertIn("--listar", texto)

    def test_coladas_descritas_como_aparecem_no_txt(self):
        texto = (SKILL / "references" / "revisao.md").read_text(encoding="utf-8")
        coladas = next(linha for linha in texto.splitlines() if "**Mensagens coladas.**" in linha)
        self.assertIn("[12:25, 03/07/2026] Nome:", coladas)
        self.assertIn("analise.json", coladas)

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


class PreparoTeste(unittest.TestCase):
    def test_pergunta_do_nome_da_pasta_mostra_exemplo_em_cada_opcao(self):
        # Só "número e depois cliente" é difícil de entender: cada opção leva um exemplo.
        texto = (RAIZ / "skills" / "preparar-projeto-armanilux" / "SKILL.md").read_text(encoding="utf-8")
        for exemplo in ('"1001 - Família Almeida"', '"Família Almeida - 1001"', '"1001"'):
            self.assertIn(exemplo, texto)


if __name__ == "__main__":
    unittest.main()
