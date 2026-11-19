"""O texto de privacidade diz a verdade: a transcrição é local, mas a revisão manda o material ao ChatGPT."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "relatorio-cronologico-obra" / "scripts"))
sys.path.insert(0, str(RAIZ / "skills" / "preparar-projeto-armanilux" / "scripts"))

from preparar import texto_leia_me  # noqa: E402
from setup_workspace import LEIA_ME  # noqa: E402

PROMESSAS_FALSAS = (
    "Nada é enviado para a internet",
    "Nada desta pasta é enviado",
    "A conversa não vai para um serviço",
)


class PrivacidadeTeste(unittest.TestCase):
    def _honesto(self, texto: str, onde: str) -> None:
        for promessa in PROMESSAS_FALSAS:
            self.assertNotIn(promessa, texto, onde)
        self.assertIn("ChatGPT", texto, onde)

    def test_leia_me_da_pasta_da_armanilux(self):
        texto = texto_leia_me({"nome": "Ana", "funcao": "Projetos", "formato_entrega": "word"})
        self._honesto(texto, "LEIA-ME do preparo")

    def test_leia_me_da_pasta_de_relatorios(self):
        self._honesto(LEIA_ME, "LEIA-ME de Relatorios-de-Obra")

    def test_readme_e_preparo_mandam_desligar_melhorar_o_modelo(self):
        readme = (RAIZ / "README.md").read_text(encoding="utf-8")
        self._honesto(readme, "README")
        self.assertIn("Melhorar o modelo para todos", readme)
        preparo = (RAIZ / "skills" / "preparar-projeto-armanilux" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Melhorar o modelo para todos", preparo)


if __name__ == "__main__":
    unittest.main()
