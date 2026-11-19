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


if __name__ == "__main__":
    unittest.main()
