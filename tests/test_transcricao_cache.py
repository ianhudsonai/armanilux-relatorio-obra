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
        self.assertEqual(linhas, ["Transcrevendo 1/1: PTT-2.opus"])

    def test_audio_e_video_com_o_mesmo_nome_guardam_cada_um_a_sua_fala(self):
        (self.midias / "PTT-1.mp4").write_bytes(b"video com o mesmo nome")
        primeiro = TranscritorFalso()
        self._rodar(primeiro)
        self.assertEqual(primeiro.chamados, ["PTT-1.mp4", "PTT-1.opus", "VID-1.mp4"])
        textos = {item["arquivo"]: item["texto"] for item in self._rodar(TranscritorFalso())}
        self.assertEqual(textos["PTT-1.mp4"], "fala de PTT-1.mp4")
        self.assertEqual(textos["PTT-1.opus"], "fala de PTT-1.opus")

    def test_cache_estragado_refaz_em_vez_de_confiar_no_txt(self):
        self._rodar(TranscritorFalso())
        (self.saida / "transcricoes-cache.json").write_text("[1, 2", encoding="utf-8")
        segundo = TranscritorFalso()
        self._rodar(segundo)
        self.assertEqual(segundo.chamados, ["PTT-1.opus", "VID-1.mp4"])

    def test_txt_sem_registro_depois_do_cache_existir_e_refeito(self):
        # Ex.: o computador desligou no meio da gravação do .txt.
        self._rodar(TranscritorFalso())
        (self.midias / "PTT-2.opus").write_bytes(b"audio novo")
        (self.saida / "PTT-2.txt").write_text("fala cort", encoding="utf-8")
        segundo = TranscritorFalso()
        resultados = self._rodar(segundo)
        self.assertEqual(segundo.chamados, ["PTT-2.opus"])
        self.assertEqual(resultados[1]["texto"], "fala de PTT-2.opus")

    def test_tudo_ja_transcrito_nao_carrega_o_whisper(self):
        self._rodar(TranscritorFalso())
        # Sem transcritor: se precisasse do Whisper, viria "indisponivel" (CI não tem faster-whisper).
        resultados = transcrever_pasta(self.midias, self.saida)
        self.assertEqual([item["status"] for item in resultados], ["ok", "ok"])

    def test_avisa_que_carregar_pode_levar_minutos_antes_de_carregar(self):
        # Carregar o modelo leva minutos sem nenhuma linha nova: parece travado sem este aviso.
        linhas: list[str] = []
        transcrever_pasta(self.midias, self.saida, progresso=linhas.append)
        self.assertTrue(linhas)
        self.assertIn("pode levar alguns minutos", linhas[0])
        self.assertIn("não travou", linhas[0])


if __name__ == "__main__":
    unittest.main()
