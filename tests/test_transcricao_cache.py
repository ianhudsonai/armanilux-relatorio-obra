"""Transcrição com cache por arquivo: o que já foi transcrito não é refeito."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "relatorio-cronologico-obra" / "scripts"))

from transcribe_media import transcrever_pasta  # noqa: E402


class TranscritorFalso:
    """Faz o papel do FFmpeg + Whisper: devolve um texto e anota quem passou."""

    def __init__(self):
        self.chamados: list[str] = []

    def __call__(self, arquivo: Path) -> str:
        self.chamados.append(arquivo.name)
        return f"fala de {arquivo.name}"


class CacheTeste(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        base = Path(self._tmp.name)
        self.midias = base / "03-midias"
        self.saida = base / "04-transcricoes"
        self.midias.mkdir()
        (self.midias / "PTT-1.opus").write_bytes(b"audio 1")
        (self.midias / "VID-1.mp4").write_bytes(b"video 1")

    def tearDown(self):
        self._tmp.cleanup()

    def _rodar(self, transcritor, **opcoes):
        return transcrever_pasta(self.midias, self.saida, transcritor=transcritor, **opcoes)

    def test_segunda_execucao_nao_refaz_o_que_ja_foi_transcrito(self):
        self._rodar(TranscritorFalso())
        segundo = TranscritorFalso()
        resultados = self._rodar(segundo)
        self.assertEqual(segundo.chamados, [])
        self.assertEqual(
            [(item["arquivo"], item["status"], item["texto"]) for item in resultados],
            [("PTT-1.opus", "ok", "fala de PTT-1.opus"), ("VID-1.mp4", "ok", "fala de VID-1.mp4")],
        )

    def test_arquivo_com_mesmo_nome_e_conteudo_novo_e_refeito(self):
        self._rodar(TranscritorFalso())
        (self.midias / "PTT-1.opus").write_bytes(b"outro audio")
        segundo = TranscritorFalso()
        self._rodar(segundo)
        self.assertEqual(segundo.chamados, ["PTT-1.opus"])

    def test_execucao_interrompida_continua_de_onde_parou(self):
        def cai_no_video(arquivo: Path) -> str:
            if arquivo.name == "VID-1.mp4":
                raise RuntimeError("computador desligou")
            return "fala"

        primeiro = self._rodar(cai_no_video)
        self.assertEqual([item["status"] for item in primeiro], ["ok", "erro"])
        segundo = TranscritorFalso()
        self._rodar(segundo)
        self.assertEqual(segundo.chamados, ["VID-1.mp4"])

    def test_sem_transcrever_ainda_entrega_o_que_ja_foi_transcrito(self):
        self._rodar(TranscritorFalso())
        (self.midias / "PTT-2.opus").write_bytes(b"audio novo")
        resultados = self._rodar(TranscritorFalso(), pular=True)
        self.assertEqual(
            [(item["arquivo"], item["status"]) for item in resultados],
            [("PTT-1.opus", "ok"), ("PTT-2.opus", "ignorado"), ("VID-1.mp4", "ok")],
        )

    def test_transcricao_de_antes_do_cache_e_aproveitada(self):
        self.saida.mkdir()
        (self.saida / "PTT-1.opus.txt").write_text("nunca usado\n", encoding="utf-8")
        (self.saida / "PTT-1.txt").write_text("fala antiga\n", encoding="utf-8")
        transcritor = TranscritorFalso()
        resultados = self._rodar(transcritor)
        self.assertEqual(transcritor.chamados, ["VID-1.mp4"])
        self.assertEqual(resultados[0]["texto"], "fala antiga")

    def test_outro_modelo_refaz_a_transcricao(self):
        self._rodar(TranscritorFalso(), modelo="small")
        segundo = TranscritorFalso()
        self._rodar(segundo, modelo="medium")
        self.assertEqual(segundo.chamados, ["PTT-1.opus", "VID-1.mp4"])

    def test_progresso_mostra_so_o_que_esta_sendo_transcrito(self):
        self._rodar(TranscritorFalso())
        (self.midias / "PTT-2.opus").write_bytes(b"audio novo")
        linhas: list[str] = []
        self._rodar(TranscritorFalso(), progresso=linhas.append)
        self.assertEqual(linhas, ["Transcrevendo 2/3: PTT-2.opus"])

    def test_tudo_ja_transcrito_nao_carrega_o_whisper(self):
        self._rodar(TranscritorFalso())
        # Sem transcritor: se precisasse do Whisper, viria "indisponivel" (CI não tem faster-whisper).
        resultados = transcrever_pasta(self.midias, self.saida)
        self.assertEqual([item["status"] for item in resultados], ["ok", "ok"])


if __name__ == "__main__":
    unittest.main()
