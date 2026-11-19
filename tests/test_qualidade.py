"""Qualidade do relatório: endereço, pendências, eventos acrescentados à mão e candidatos."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import _endereco, _pendencias, aplicar_ajustes, completar_relato, montar_analise  # noqa: E402
from candidatos import escrever, selecionar  # noqa: E402
from transcribe_media import _ler_amostras  # noqa: E402
from parse_whatsapp import analisar_conversa  # noqa: E402

CHAT = (
    "[08/01/2026, 08:00:01] Ana Souza: Aprovamos as chapas do lote 3 em pessoa hoje.\n"
    "[09/01/2026, 09:00:00] Beto Lima: Vamos fazer a visita na obra amanhã para medir.\n"
    "[10/01/2026, 10:00:00] Ana Souza: Medição in loco realizada hoje na cozinha.\n"
    "[20/01/2026, 11:00:00] Beto Lima: O material chegou na obra hoje de manhã.\n"
    "[25/01/2026, 12:00:00] Ana Souza: Ainda falta o ponto de água da cozinha.\n"
    "[26/01/2026, 12:00:00] Beto Lima: " + "Texto muito longo sobre outro assunto, ainda falta resolver. " * 8 + "\n"
    "[30/01/2026, 12:00:00] Ana Souza: Serviços concluídos hoje.\n"
)


class EnderecoTeste(unittest.TestCase):
    def test_abreviacao_nao_corta_o_endereco(self):
        self.assertEqual(_endereco("Endereço: R. das Flores, 120. O prazo"), "R. das Flores, 120")
        self.assertEqual(_endereco("Endereço: Av. Paulista, 1000"), "Av. Paulista, 1000")
        self.assertEqual(_endereco("Endereço: Rua das Acácias, 120, São Paulo. O prazo não foi"), "Rua das Acácias, 120, São Paulo")
        self.assertEqual(_endereco("sem nada"), "")


class PendenciasTeste(unittest.TestCase):
    def test_so_mensagem_curta_e_clara_vira_pendencia(self):
        itens = _pendencias([m for m in analisar_conversa(CHAT)])
        textos = [i["item"] for i in itens]
        self.assertEqual(len(textos), 1)
        self.assertIn("ponto de água", textos[0])
        self.assertTrue(all(i["status"] == "Pendente" for i in itens))
        pergunta = analisar_conversa("[08/01/2026, 08:00:01] Ana Souza: Ficou pendente algo?\n")
        self.assertEqual(_pendencias(pergunta), [])


class EventosATeste(unittest.TestCase):
    def _analise(self):
        return montar_analise(
            analisar_conversa(CHAT),
            fonte="teste.zip",
            arquivos=[],
            documentos=[],
            transcricoes=[],
            quadros=[],
            overrides={"numero": "1001", "cliente": "Cliente Teste"},
        )

    def test_evento_adicionado_a_mao_entra_e_nao_repete(self):
        analise = self._analise()
        antes = len([e for e in analise["eventos"] if e["etapa"] == "C"])
        analise["eventos_adicionais"] = [
            {"data": "2026-01-10", "hora": "10:00", "etapa": "C", "autor": "Ana", "ocorrencia": "Medição in loco realizada."},
            {"data": "2026-01-10", "hora": "10:00", "etapa": "K", "ocorrencia": "etapa K não existe"},
            {"hora": "10:00", "etapa": "C", "ocorrencia": "sem data"},
        ]
        refeita = completar_relato(analise)
        medicoes = [e for e in refeita["eventos"] if e["etapa"] == "C"]
        self.assertEqual(len(medicoes), antes + 1)
        self.assertNotIn("K", {e["etapa"] for e in refeita["eventos"]})
        de_novo = completar_relato(refeita)
        self.assertEqual(len([e for e in de_novo["eventos"] if e["etapa"] == "C"]), antes + 1)
        self.assertEqual(refeita["etapas"]["C"]["situacao"], "Atividade realizada")

    def test_remover_e_trocar_etapa(self):
        eventos = [
            {"data": "2026-01-10", "hora": "10:00", "autor": "A", "etapa": "J", "ocorrencia": "x"},
            {"data": "2026-01-11", "hora": "10:00", "autor": "A", "etapa": "J", "ocorrencia": "y"},
        ]
        saida = aplicar_ajustes(
            eventos,
            [
                {"data": "2026-01-10", "etapa_original": "J", "remover": True},
                {"data": "2026-01-11", "etapa": "C"},
            ],
        )
        self.assertEqual([(e["data"], e["etapa"]) for e in saida], [("2026-01-11", "C")])


class RemontagemTeste(unittest.TestCase):
    def test_ajustes_e_eventos_da_revisao_valem_na_remontagem(self):
        import json
        import os
        import zipfile

        from run_pipeline import executar

        with TemporaryDirectory() as temporario:
            base = Path(temporario)
            antigos = {k: os.environ.get(k) for k in ("ARMANILUX_CONFIG", "ARMANILUX_REGISTRO")}
            os.environ["ARMANILUX_CONFIG"] = str(base / "sem-config.json")
            os.environ["ARMANILUX_REGISTRO"] = str(base / "registro.json")
            try:
                zip_path = base / "Conversa do WhatsApp com 1001 - Cliente Teste.zip"
                with zipfile.ZipFile(zip_path, "w") as arquivo:
                    arquivo.writestr("_chat.txt", CHAT.encode("utf-8"))
                oficina = base / "obras"
                argv = ["--workspace", str(oficina), "--skip-transcribe", "--skip-keyframes"]
                self.assertEqual(executar(["--zip", str(zip_path), *argv]), 0)
                obra = oficina / "1001 - Cliente Teste"
                caminho = obra / "04-transcricoes" / "analise.json"
                analise = json.loads(caminho.read_text(encoding="utf-8"))
                antes = [(e["data"], e["etapa"]) for e in analise["eventos"]]
                self.assertTrue(antes)
                primeiro = analise["eventos"][0]
                analise["ajustes_eventos"] = [{"data": primeiro["data"], "hora": primeiro["hora"], "etapa_original": primeiro["etapa"], "remover": True}]
                analise["eventos_adicionais"] = [{"data": "2026-01-15", "hora": "09:00", "etapa": "H", "autor": "Ana", "ocorrencia": "Material entregue."}]
                caminho.write_text(json.dumps(analise, ensure_ascii=False), encoding="utf-8")
                self.assertEqual(executar(["--rebuild-only", "--recalcular", "--obra-dir", str(obra), *argv]), 0)
                depois = json.loads(caminho.read_text(encoding="utf-8"))
                datas = [(e["data"], e["hora"], e["etapa"]) for e in depois["eventos"]]
                self.assertNotIn((primeiro["data"], primeiro["hora"], primeiro["etapa"]), datas)
                self.assertIn(("2026-01-15", "09:00", "H"), datas)
                # Remontar de novo não repete nada.
                self.assertEqual(executar(["--rebuild-only", "--recalcular", "--obra-dir", str(obra), *argv]), 0)
                de_novo = json.loads(caminho.read_text(encoding="utf-8"))
                self.assertEqual(len(de_novo["eventos"]), len(depois["eventos"]))
                from docx import Document

                def _texto(docx):
                    return " ".join(p.text for p in Document(str(docx)).paragraphs)

                rascunho = sorted((obra / "05-relatorios").glob("*.docx"))[-1]
                self.assertIn("RASCUNHO NÃO REVISADO", _texto(rascunho))
                de_novo["revisado"] = True
                caminho.write_text(json.dumps(de_novo, ensure_ascii=False), encoding="utf-8")
                self.assertEqual(executar(["--rebuild-only", "--recalcular", "--obra-dir", str(obra), *argv]), 0)
                final = sorted((obra / "05-relatorios").glob("*.docx"), key=lambda x: int(x.stem.rsplit("-v", 1)[1]))[-1]
                self.assertNotIn("RASCUNHO NÃO REVISADO", _texto(final))
            finally:
                for chave, valor in antigos.items():
                    if valor is None:
                        os.environ.pop(chave, None)
                    else:
                        os.environ[chave] = valor


class CandidatosTeste(unittest.TestCase):
    def test_candidatos_cobrem_as_etapas_que_a_leitura_automatica_perde(self):
        por_etapa = selecionar(analisar_conversa(CHAT))
        datas = {codigo: {m.data.isoformat() for m in msgs} for codigo, msgs in por_etapa.items()}
        self.assertIn("2026-01-08", datas["A"])
        self.assertIn("2026-01-10", datas["C"])
        self.assertIn("2026-01-20", datas["H"])
        self.assertIn("2026-01-30", datas["L"])

    def test_arquivo_gerado_e_curto_e_legivel(self):
        with TemporaryDirectory() as temporario:
            destino = escrever(analisar_conversa(CHAT), Path(temporario) / "04" / "candidatos-por-etapa.md")
            texto = destino.read_text(encoding="utf-8")
        self.assertIn("## A –", texto)
        self.assertIn("## L –", texto)
        self.assertIn("eventos_adicionais", texto)
        self.assertLess(len(texto), 20000)


class AmostrasTeste(unittest.TestCase):
    def test_wav_vira_amostras_sem_depender_do_pyav(self):
        import struct
        import wave

        with TemporaryDirectory() as temporario:
            caminho = Path(temporario) / "a.wav"
            with wave.open(str(caminho), "wb") as arquivo:
                arquivo.setnchannels(1)
                arquivo.setsampwidth(2)
                arquivo.setframerate(16000)
                arquivo.writeframes(struct.pack("<4h", 0, 16384, -16384, 32767))
            amostras = _ler_amostras(caminho)
        self.assertEqual(amostras.dtype.name, "float32")
        self.assertEqual(len(amostras), 4)
        self.assertAlmostEqual(float(amostras[1]), 0.5, places=3)
        self.assertAlmostEqual(float(amostras[2]), -0.5, places=3)


if __name__ == "__main__":
    unittest.main()
