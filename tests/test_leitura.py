"""A revisão lê o material em partes pequenas e marca o que já leu.

No Codex, a saída de um comando que passa de ~10 KB ou 256 linhas perde o meio sem aviso
claro. Por isso cada parte cabe nesse limite, e `revisao-progresso.md` diz o que falta ler,
para a revisão continuar depois de "continue".
"""

from __future__ import annotations

import re
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from parse_whatsapp import Mensagem  # noqa: E402

import leitura  # noqa: E402

LIMITE_BYTES = 10_000  # o que o Codex mostra de uma vez, com folga para o aviso de corte
LIMITE_LINHAS = 200


def _mensagens(dias: int, por_dia: int, tamanho: int = 120) -> list[Mensagem]:
    inicio = datetime(2025, 6, 2, 8, 0)
    saida = []
    for dia in range(dias):
        for indice in range(por_dia):
            quando = inicio + timedelta(days=dia, minutes=7 * indice)
            texto = f"msg-{dia:03d}-{indice:02d} " + "pedra " * (tamanho // 6)
            saida.append(Mensagem(quando=quando, autor="Helena Duarte", texto=texto))
    return saida


def _ler(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8-sig")


class PartesDaConversaTeste(unittest.TestCase):
    def test_conversa_vira_partes_pequenas_sem_perder_mensagem_nem_partir_o_dia(self):
        mensagens = _mensagens(dias=60, por_dia=9)
        with TemporaryDirectory() as temporario:
            obra = Path(temporario)
            leitura.gerar(obra, mensagens)
            partes = sorted((obra / "04-transcricoes" / "leitura").glob("conversa-*.txt"))
            self.assertGreater(len(partes), 5)
            vistas: list[str] = []
            dias_por_parte: list[set[str]] = []
            for parte in partes:
                bruto = parte.read_bytes()
                self.assertLessEqual(len(bruto), LIMITE_BYTES, parte.name)
                self.assertLessEqual(bruto.count(b"\n"), LIMITE_LINHAS, parte.name)
                texto = _ler(parte)
                achadas = re.findall(r"msg-\d{3}-\d{2}", texto)
                vistas.extend(achadas)
                dias_por_parte.append({item[:7] for item in achadas})
                self.assertIn("[02/06/2025 08:00] Helena Duarte:", _ler(partes[0]))
            esperadas = [m.texto.split()[0] for m in mensagens]
            self.assertEqual(vistas, esperadas)  # cada mensagem uma vez, na ordem do arquivo
            for antes, depois in zip(dias_por_parte, dias_por_parte[1:]):
                self.assertFalse(antes & depois, "um dia ficou partido entre duas partes")

            progresso = _ler(obra / "04-transcricoes" / "revisao-progresso.md")
            for parte in partes:
                self.assertIn(f"- [ ] leitura/{parte.name}", progresso)
            self.assertEqual(leitura.progresso(obra), {"lidas": 0, "total": len(partes)})

    def test_refazer_mantem_o_que_ja_foi_lido_e_as_notas(self):
        mensagens = _mensagens(dias=30, por_dia=9)
        with TemporaryDirectory() as temporario:
            obra = Path(temporario)
            leitura.gerar(obra, mensagens)
            caminho = obra / "04-transcricoes" / "revisao-progresso.md"
            texto = _ler(caminho)
            partes = sorted((obra / "04-transcricoes" / "leitura").glob("conversa-*.txt"))
            ultima = f"leitura/{partes[-1].name}"
            texto = texto.replace("- [ ] leitura/conversa-001.txt", "- [x] leitura/conversa-001.txt")
            texto = texto.replace(f"- [ ] {ultima}", f"- [x] {ultima}")
            texto = texto.rstrip("\n") + "\nHelena Duarte é a arquiteta (conversa-001).\n"
            caminho.write_text(texto, encoding="utf-8")

            # Exportação nova: as mensagens antigas iguais e uma a mais no último dia.
            nova = mensagens + [
                Mensagem(quando=mensagens[-1].quando + timedelta(minutes=1), autor="Paulo", texto="mensagem nova")
            ]
            leitura.gerar(obra, nova)
            texto = _ler(caminho)
            self.assertIn("- [x] leitura/conversa-001.txt", texto)  # parte igual continua lida
            self.assertIn(f"- [ ] {ultima}", texto)  # parte que mudou volta para ler
            self.assertIn("Helena Duarte é a arquiteta (conversa-001).", texto)
            self.assertEqual(leitura.progresso(obra)["lidas"], 1)


class MarcasQueNaoSePerdemTeste(unittest.TestCase):
    def test_emoji_e_acento_nao_passam_do_limite_em_bytes(self):
        mensagens = _mensagens(dias=20, por_dia=9)
        for mensagem in mensagens:
            mensagem.texto += " 👍🏽 ação " * 12
        with TemporaryDirectory() as temporario:
            obra = Path(temporario)
            leitura.gerar(obra, mensagens)
            for parte in (obra / "04-transcricoes" / "leitura").glob("*.txt"):
                self.assertLessEqual(len(parte.read_bytes()), LIMITE_BYTES, parte.name)

    def test_lista_salva_com_quebra_de_linha_do_windows_continua_marcada(self):
        mensagens = _mensagens(dias=10, por_dia=9)
        with TemporaryDirectory() as temporario:
            obra = Path(temporario)
            leitura.gerar(obra, mensagens)
            caminho = obra / "04-transcricoes" / "revisao-progresso.md"
            texto = re.sub(r"^- \[ \]", "- [x]", _ler(caminho), flags=re.MULTILINE)
            caminho.write_bytes(texto.replace("\n", "\r\n").encode("utf-8"))
            leitura.gerar(obra, mensagens)
            progresso = leitura.progresso(obra)
            self.assertEqual(progresso["lidas"], progresso["total"])

    def test_transcricoes_continuam_lidas_quando_a_remontagem_ainda_nao_tem_as_novas(self):
        # Exportação nova: as partes são refeitas antes da transcrição, que só termina depois.
        mensagens = _mensagens(dias=3, por_dia=2)
        transcricoes = [{"arquivo": "PTT-1.opus", "status": "ok", "texto": "Áudio da medição."}]
        with TemporaryDirectory() as temporario:
            obra = Path(temporario)
            leitura.gerar(obra, mensagens, transcricoes=transcricoes)
            caminho = obra / "04-transcricoes" / "revisao-progresso.md"
            caminho.write_text(re.sub(r"^- \[ \]", "- [x]", _ler(caminho), flags=re.MULTILINE), encoding="utf-8")
            leitura.gerar(obra, mensagens)  # transcrições ainda não chegaram
            leitura.gerar(obra, mensagens, transcricoes=transcricoes)
            self.assertIn("- [x] leitura/transcricoes-001.txt", _ler(caminho))
            self.assertEqual(leitura.progresso(obra)["lidas"], leitura.progresso(obra)["total"])

    def test_item_conferido_com_seta_no_texto_continua_marcado(self):
        mensagens = _mensagens(dias=3, por_dia=2)
        analise = {
            "eventos": [{"data": "2025-06-02", "hora": "08:00", "autor": "Helena Duarte", "etapa": "C", "ocorrencia": "Medição 13/05 → 22/05."}],
            "impactos_prazo": "Living: 13/05 → 22/05, 7 d.u.",
        }
        with TemporaryDirectory() as temporario:
            obra = Path(temporario)
            leitura.gerar(obra, mensagens)
            leitura.escrever_conferencia(obra, analise)
            caminho = obra / "04-transcricoes" / "conferencia.md"
            caminho.write_text(re.sub(r"^- \[ \]", "- [x]", _ler(caminho), flags=re.MULTILINE), encoding="utf-8")
            self.assertEqual(leitura.escrever_conferencia(obra, analise), {"feitos": 2, "total": 2})

    def test_fato_de_audio_aponta_a_parte_da_transcricao(self):
        mensagens = [
            Mensagem(quando=datetime(2025, 9, 30, 10, 30), autor="Paulo Reis", texto="PTT-1.opus (arquivo anexado)", anexos=["PTT-1.opus"]),
        ]
        transcricoes = [{"arquivo": "PTT-1.opus", "status": "ok", "texto": "A medição fica para quinta."}]
        analise = {"eventos": [{"data": "2025-09-30", "hora": "10:30", "autor": "Paulo Reis", "etapa": "C", "ocorrencia": "Medição programada.", "midias": ["PTT-1.opus"]}]}
        with TemporaryDirectory() as temporario:
            obra = Path(temporario)
            leitura.gerar(obra, mensagens, transcricoes=transcricoes)
            leitura.escrever_conferencia(obra, analise)
            self.assertIn("leitura/transcricoes-001.txt", _ler(obra / "04-transcricoes" / "conferencia.md"))

    def test_parte_que_sai_duas_vezes_nao_apaga_a_copia_antiga(self):
        with TemporaryDirectory() as temporario:
            obra = Path(temporario)
            leitura.gerar(obra, _mensagens(dias=40, por_dia=9))
            leitura.gerar(obra, _mensagens(dias=2, por_dia=2))
            leitura.gerar(obra, _mensagens(dias=40, por_dia=9))
            leitura.gerar(obra, _mensagens(dias=2, por_dia=2))
            antigas = list((obra / "04-transcricoes" / "leitura" / "antigas").glob("conversa-002*.txt"))
            self.assertEqual(len(antigas), 2)


class TranscricoesDocumentosEImagensTeste(unittest.TestCase):
    def test_transcricoes_documentos_e_folhas_entram_na_lista(self):
        mensagens = [
            Mensagem(quando=datetime(2025, 9, 30, 10, 30), autor="Paulo Reis", texto="PTT-20250930-WA0017.opus (arquivo anexado)", anexos=["PTT-20250930-WA0017.opus"]),
            Mensagem(quando=datetime(2025, 10, 1, 9, 0), autor="Helena Duarte", texto="Bom dia"),
        ]
        transcricoes = [
            {"arquivo": "PTT-20250930-WA0017.opus", "status": "ok", "texto": "A medição fica para quinta."},
            {"arquivo": "VID-20251015-WA0015.mp4", "status": "ok", "texto": "Vídeo da bancada instalada."},
            {"arquivo": "PTT-20251020-WA0001.opus", "status": "erro", "texto": ""},
        ]
        paragrafo = "Bancada da cozinha em quartzito, espessura 2 cm, rebaixo para cuba. "
        documentos = [
            {"arquivo": "Orçamento 1001.2.pdf", "texto": "\n".join(f"item {i:03d} {paragrafo}" for i in range(300))},
            {"arquivo": "Desenho técnico.pdf", "texto": ""},
        ]
        with TemporaryDirectory() as temporario:
            obra = Path(temporario)
            folhas = obra / "04-transcricoes" / "folhas-de-contato"
            folhas.mkdir(parents=True)
            (folhas / "folha-01.jpg").write_bytes(b"jpg-1")
            (folhas / "folha-02.jpg").write_bytes(b"jpg-2")
            leitura.gerar(obra, mensagens, transcricoes=transcricoes, documentos=documentos)
            pasta = obra / "04-transcricoes" / "leitura"

            [transcritas] = sorted(pasta.glob("transcricoes-*.txt"))
            texto = _ler(transcritas)
            self.assertIn("[30/09/2025 10:30] Paulo Reis — PTT-20250930-WA0017.opus", texto)
            self.assertIn("A medição fica para quinta.", texto)
            self.assertIn("VID-20251015-WA0015.mp4 (nenhuma mensagem cita este arquivo)", texto)
            self.assertIn("Vídeo da bancada instalada.", texto)
            self.assertNotIn("PTT-20251020-WA0001", texto)  # falhou: já é lacuna, não há o que ler

            partes_doc = sorted(pasta.glob("documento-*.txt"))
            self.assertGreater(len(partes_doc), 2)
            juntas = "\n".join(_ler(p) for p in partes_doc)
            self.assertEqual(re.findall(r"item \d{3}", juntas), [f"item {i:03d}" for i in range(300)])
            self.assertIn("Orçamento 1001.2.pdf", _ler(partes_doc[0]))
            self.assertNotIn("Desenho técnico", juntas)
            for parte in partes_doc:
                self.assertLessEqual(len(parte.read_bytes()), LIMITE_BYTES)
                self.assertLessEqual(parte.read_bytes().count(b"\n"), LIMITE_LINHAS)

            progresso = _ler(obra / "04-transcricoes" / "revisao-progresso.md")
            self.assertIn(f"- [ ] leitura/{transcritas.name}", progresso)
            self.assertIn(f"- [ ] leitura/{partes_doc[0].name}", progresso)
            self.assertIn("- [ ] folhas-de-contato/folha-01.jpg", progresso)
            self.assertIn("- [ ] folhas-de-contato/folha-02.jpg", progresso)
            total = 1 + 1 + len(partes_doc) + 2
            self.assertEqual(leitura.progresso(obra), {"lidas": 0, "total": total})


if __name__ == "__main__":
    unittest.main()
