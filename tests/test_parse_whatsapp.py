"""Parser de export Android e iPhone, inclusive data pt-BR, anexo e mojibake."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from common import corrigir_mojibake  # noqa: E402
from parse_whatsapp import analisar_conversa  # noqa: E402


ANDROID = """18/01/2026 09:15 - Lucas Ferreira: Aprovo as chapas do lote 3.
18/01/2026 09:16 - Lucas Ferreira: <anexado: medi\u00c3\u00a7\u00c3\u00a3o.pdf>
19/01/2026, 10:02 - Carlos Mendes: Solicito uma visita in loco.
Preciso ver a cozinha
e o banheiro.
20/01/2026 08:00 - As mensagens e as ligações são protegidas com a criptografia de ponta a ponta.
21/01/2026 14:32\u202f- Marina Costa: \u200eIMG-20260121-WA0001.jpg (arquivo anexado)
22/01/2026, 2:05 PM - Helena Duarte: Medição in loco realizada hoje.
"""

IPHONE = """[18/01/26, 09:15:02] Helena Duarte: \u200e<anexado: Projeto-preliminar.pdf>
[18/01/2026, 09:16:10] Carlos Mendes: Ok
continua na linha de baixo
[1/18/26, 9:20 AM] Paulo Ribeiro: Projeto aprovado pela engenharia.
"""


class ParserTeste(unittest.TestCase):
    def test_android_data_anexo_e_multilinha(self):
        mensagens = analisar_conversa(ANDROID)
        self.assertGreaterEqual(len(mensagens), 5)
        primeira = mensagens[0]
        self.assertEqual(primeira.quando, datetime(2026, 1, 18, 9, 15))
        self.assertEqual(primeira.autor, "Lucas Ferreira")
        self.assertFalse(primeira.sistema)
        segunda = mensagens[1]
        self.assertEqual(segunda.anexos, ["medição.pdf"])
        terceira = mensagens[2]
        self.assertIn("cozinha", terceira.texto)
        self.assertIn("banheiro", terceira.texto)
        self.assertEqual(terceira.autor, "Carlos Mendes")
        sistema = mensagens[3]
        self.assertTrue(sistema.sistema)
        self.assertIsNone(sistema.autor)
        foto = mensagens[4]
        self.assertEqual(foto.anexos, ["IMG-20260121-WA0001.jpg"])
        self.assertEqual(foto.autor, "Marina Costa")
        tarde = mensagens[5]
        self.assertEqual(tarde.quando, datetime(2026, 1, 22, 14, 5))

    def test_iphone_ano_curto_e_data_americana_quando_o_mes_nao_cabe(self):
        mensagens = analisar_conversa(IPHONE)
        self.assertEqual(mensagens[0].quando, datetime(2026, 1, 18, 9, 15, 2))
        self.assertEqual(mensagens[0].anexos, ["Projeto-preliminar.pdf"])
        self.assertIn("continua na linha de baixo", mensagens[1].texto)
        # 1/18/26 não cabe em dia/mês; o parser trata como mês/dia.
        self.assertEqual(mensagens[2].quando, datetime(2026, 1, 18, 9, 20))
        self.assertEqual(mensagens[2].autor, "Paulo Ribeiro")

    def test_midia_oculta_com_nome_do_arquivo_na_linha_seguinte(self):
        texto = (
            "29/08/2025 14:49 - Ana Lima: <Mídia oculta>\n"
            "CRONOGRAMA DE PRAZOS 2025.v2.pdf\n"
            "29/08/2025 14:50 - Ana Lima: <Mídia oculta>\n"
            "30/08/2025 10:48 - Bruno Reis: <Mídia oculta>\n"
            "estucado somente no box, correto?\n"
        )
        doc, sem_nome, legenda = analisar_conversa(texto)
        self.assertEqual(doc.anexos, ["CRONOGRAMA DE PRAZOS 2025.v2.pdf"])
        self.assertTrue(doc.midia_omitida)
        self.assertEqual(sem_nome.anexos, [])
        # Legenda de foto não é nome de arquivo.
        self.assertEqual(legenda.anexos, [])

    def test_reencaminhada_usa_data_e_autor_originais(self):
        texto = (
            "28/09/2026 15:55 - Paulo Ribeiro: [21/08, 08:54] Carla Nunes: Preciso da cozinha liberada\n"
            "para a civil\n"
            "[21/08, 08:55] Paulo Ribeiro: Registro de obra\n"
            "28/09/2026 16:00 - Ana Lima: Ok\n"
        )
        primeira, segunda, depois = analisar_conversa(texto)
        self.assertEqual(primeira.quando, datetime(2026, 8, 21, 8, 54))
        self.assertEqual(primeira.autor, "Carla Nunes")
        self.assertEqual(primeira.texto, "Preciso da cozinha liberada\npara a civil")
        self.assertEqual(primeira.encaminhada_por, "Paulo Ribeiro")
        self.assertEqual(primeira.encaminhada_em, datetime(2026, 9, 28, 15, 55))
        self.assertEqual(segunda.quando, datetime(2026, 8, 21, 8, 55))
        self.assertEqual(segunda.autor, "Paulo Ribeiro")
        self.assertEqual(depois.autor, "Ana Lima")
        self.assertIsNone(depois.encaminhada_por)

    def test_reencaminhada_de_dezembro_postada_em_janeiro_e_do_ano_anterior(self):
        texto = "05/01/2026 09:00 - Ana Lima: Segue o combinado\n[30/12, 17:10] Bruno Reis: Medimos a cozinha\n"
        propria, original = analisar_conversa(texto)
        self.assertEqual(propria.texto, "Segue o combinado")
        self.assertEqual(propria.autor, "Ana Lima")
        self.assertEqual(original.quando, datetime(2025, 12, 30, 17, 10))
        self.assertEqual(original.autor, "Bruno Reis")

    def test_reencaminhada_de_29_de_fevereiro_e_linha_sem_texto(self):
        texto = (
            "03/03/2025 09:00 - Ana Lima: [29/02, 10:00] Bruno Reis: Medimos a sala\n"
            "[01/03, 11:00] Carla Nunes:\n"
        )
        bissexto, vazia = analisar_conversa(texto)
        self.assertEqual(bissexto.quando, datetime(2024, 2, 29, 10, 0))
        self.assertEqual((vazia.autor, vazia.texto), ("Carla Nunes", ""))

    def test_colada_com_hora_antes_e_data_completa(self):
        texto = (
            "16/11/2026 18:02 - Paulo Ribeiro: Conversa com a arquiteta\n"
            "[12:25, 03/07/2026] Carla Nunes: Pode instalar a bancada amanhã\n"
            "segunda linha\n"
            "[12:31, 03/07/26] Paulo Ribeiro: Combinado\n"
        )
        propria, primeira, segunda = analisar_conversa(texto)
        self.assertEqual((propria.autor, propria.texto), ("Paulo Ribeiro", "Conversa com a arquiteta"))
        self.assertEqual(primeira.quando, datetime(2026, 7, 3, 12, 25))
        self.assertEqual(primeira.autor, "Carla Nunes")
        self.assertEqual(primeira.texto, "Pode instalar a bancada amanhã\nsegunda linha")
        self.assertEqual(primeira.encaminhada_por, "Paulo Ribeiro")
        self.assertEqual(primeira.encaminhada_em, datetime(2026, 11, 16, 18, 2))
        self.assertEqual(segunda.quando, datetime(2026, 7, 3, 12, 31))

    def test_colada_com_data_depois_do_envio_fica_no_texto(self):
        [mensagem] = analisar_conversa("03/07/2026 09:00 - Ana Lima: Lembrete\n[10:00, 05/07/2026] Bruno Reis: x\n")
        self.assertIn("[10:00, 05/07/2026] Bruno Reis: x", mensagem.texto)

    def test_nome_de_arquivo_com_extensao_fora_da_lista(self):
        [mensagem] = analisar_conversa("05/09/2025 09:50 - Ana Lima: <Mídia oculta>\nPlanilha medicao.xlsm\n")
        self.assertEqual(mensagem.anexos, ["Planilha medicao.xlsm"])

    def test_mojibake_simples_duplo_e_cp437_nao_estraga_texto_certo(self):
        uma = "medição".encode("utf-8").decode("latin-1")
        duas = uma.encode("utf-8").decode("latin-1")
        cp437 = "medição".encode("utf-8").decode("cp437")
        self.assertEqual(corrigir_mojibake(uma), "medição")
        self.assertEqual(corrigir_mojibake(duas), "medição")
        self.assertEqual(corrigir_mojibake(cp437), "medição")
        self.assertEqual(corrigir_mojibake("Família Almeida"), "Família Almeida")
        self.assertEqual(corrigir_mojibake("medição"), "medição")


class OrdemDaDataTeste(unittest.TestCase):
    """WhatsApp em inglês escreve mês/dia. A ordem é decidida uma vez por arquivo, não linha a linha,
    e só por um número acima de 12. Sem essa prova, vale dia/mês e as mensagens ficam com data_incerta."""

    def test_whatsapp_em_ingles_com_um_dia_acima_de_12(self):
        # Visto na avaliação de prontidão: "7/3/26" virava 07/03 e "7/15/26" 15/07, no mesmo arquivo.
        texto = (
            "7/3/26, 12:25 PM - Ana Lima: first\n"
            "7/4/26, 9:00 AM - Ana Lima: second\n"
            "[7/15/26, 1:05:00 PM] Ana Lima: third\n"
        )
        mensagens = analisar_conversa(texto)
        self.assertEqual(
            [m.quando for m in mensagens],
            [datetime(2026, 7, 3, 12, 25), datetime(2026, 7, 4, 9, 0), datetime(2026, 7, 15, 13, 5)],
        )
        self.assertFalse(any(m.data_incerta for m in mensagens))

    def test_um_dia_acima_de_12_decide_o_arquivo_todo(self):
        mes_dia = "7/15/26, 10:00 - Ana Lima: a\n7/3/26, 10:00 - Ana Lima: b\n"
        self.assertEqual([m.data.isoformat() for m in analisar_conversa(mes_dia)], ["2026-07-15", "2026-07-03"])
        dia_mes = "15/07/26, 10:00 - Ana Lima: a\n03/07/26, 10:00 - Ana Lima: b\n"
        self.assertEqual([m.data.isoformat() for m in analisar_conversa(dia_mes)], ["2026-07-15", "2026-07-03"])

    def test_am_pm_sozinho_nao_vira_mes_dia(self):
        # Celular brasileiro com relógio de 12 horas também mostra AM/PM. O zero na frente ("03/07")
        # prova dia/mês: o WhatsApp dos EUA escreve "7/3/26", sem zero.
        texto = "03/07/2026 12:25 PM - Ana Lima: a\n04/07/2026 1:00 PM - Ana Lima: b\n"
        mensagens = analisar_conversa(texto)
        self.assertEqual([m.data.isoformat() for m in mensagens], ["2026-07-03", "2026-07-04"])
        self.assertFalse(any(m.data_incerta for m in mensagens))
        sem_zero = analisar_conversa("3/7/26, 12:25 PM - Ana Lima: a\n")
        self.assertEqual(sem_zero[0].data.isoformat(), "2026-07-03")
        self.assertTrue(sem_zero[0].data_incerta)

    def test_sem_dia_acima_de_12_a_data_fica_incerta_e_vira_lacuna(self):
        from analyze import lacunas_automaticas

        texto = "3/7/2026 12:25 - Ana Lima: a\n[4/7/2026, 08:00:00] Ana Lima: b\n"
        mensagens = analisar_conversa(texto)
        self.assertEqual([m.data.isoformat() for m in mensagens], ["2026-07-03", "2026-07-04"])
        self.assertTrue(all(m.data_incerta for m in mensagens))
        self.assertTrue(any("dia/mês" in lacuna for lacuna in lacunas_automaticas(mensagens, [], [])))

        com_prova = texto + "15/7/2026 09:00 - Ana Lima: c\n"
        mensagens = analisar_conversa(com_prova)
        self.assertFalse(any(m.data_incerta for m in mensagens))
        self.assertFalse(any("dia/mês" in lacuna for lacuna in lacunas_automaticas(mensagens, [], [])))

    def test_arquivo_com_as_duas_ordens_fica_incerto(self):
        texto = "15/07/2026 09:00 - Ana Lima: a\n7/16/2026 09:00 - Ana Lima: b\n"
        mensagens = analisar_conversa(texto)
        self.assertTrue(all(m.data_incerta for m in mensagens))


class MensagemDeSistemaTeste(unittest.TestCase):
    def test_troca_do_nome_do_grupo_com_dois_pontos_nao_vira_autor(self):
        texto = (
            '03/07/2026 12:25 - Ana Lima alterou o nome do grupo de "Obra 1001: Silva" para "Obra 1001"\n'
            '03/07/2026 12:26 - Ana Lima changed the subject from "Obra: 1" to "Obra 1001"\n'
            "03/07/2026 12:27 - Ana Lima: Bom dia\n"
        )
        renomeado, em_ingles, mensagem = analisar_conversa(texto)
        for aviso in (renomeado, em_ingles):
            self.assertIsNone(aviso.autor)
            self.assertTrue(aviso.sistema)
        self.assertEqual(mensagem.autor, "Ana Lima")

    def test_apelido_entre_aspas_e_nome_parecido_com_verbo_continuam_autor(self):
        texto = (
            '03/07/2026 12:25 - Zé "Pedreiro": Cheguei na obra\n'
            "03/07/2026 12:26 - Saiu Silva: Ok\n"
        )
        self.assertEqual([m.autor for m in analisar_conversa(texto)], ['Zé "Pedreiro"', "Saiu Silva"])


if __name__ == "__main__":
    unittest.main()
