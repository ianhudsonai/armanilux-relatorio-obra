"""Busca de conversas, registro por SHA-256, lista de pendentes e relatório v2."""

from __future__ import annotations

import json
import os
import sys
import unicodedata
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "relatorio-cronologico-obra" / "scripts"))
sys.path.insert(0, str(RAIZ / "skills" / "preparar-projeto-armanilux" / "scripts"))

import registro  # noqa: E402
from descoberta import descobrir_em, examinar_arquivo, inferir_identidade, nome_parece_exportacao  # noqa: E402
from preparar import preparar  # noqa: E402
from run_pipeline import executar  # noqa: E402

CONVERSA = (
    "[08/01/2026, 08:00:01] Helena Duarte: Registro inicial da Obra 1001. Cliente: Família Almeida.\n"
    "[09/01/2026, 11:00:04] Carlos Mendes: Solicito uma visita in loco para conferir o ambiente.\n"
    "[13/01/2026, 10:30:18] Helena Duarte: Medição in loco realizada hoje.\n"
)
NOVA = CONVERSA + "[20/01/2026, 16:40:33] Lucas Ferreira: Envio o projeto preliminar da cozinha.\n"
SEM_IDENTIDADE = (
    "[08/01/2026, 08:00:01] Helena Duarte: Bom dia pessoal.\n"
    "[09/01/2026, 11:00:04] Carlos Mendes: Bom dia, tudo certo.\n"
)


def zip_com(caminho: Path, conversa: str, nome_txt: str = "_chat.txt") -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho, "w") as arquivo:
        arquivo.writestr(nome_txt, conversa.encode("utf-8"))
    return caminho


class Ambiente(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.antigos = {k: os.environ.get(k) for k in ("ARMANILUX_CONFIG", "ARMANILUX_REGISTRO")}
        os.environ["ARMANILUX_CONFIG"] = str(self.base / "config.json")
        os.environ["ARMANILUX_REGISTRO"] = str(self.base / "registro.json")

    def tearDown(self):
        for chave, valor in self.antigos.items():
            if valor is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = valor
        self.temp.cleanup()


class BuscaTeste(Ambiente):
    def test_nome_longo_com_acento_e_parenteses(self):
        nome = "Conversa do WhatsApp com 8977.1.v10 - Família Água Clara (OBRA Ç).zip"
        zip_path = zip_com(self.base / "Downloads" / nome, CONVERSA.replace("Obra 1001", "Obra 8977"))
        achados = descobrir_em([self.base / "Downloads"])
        self.assertEqual([Path(a["caminho"]).name for a in achados], [nome])
        self.assertTrue(zip_path.exists())
        self.assertEqual(achados[0]["ultima_mensagem"], "2026-01-13")
        self.assertEqual(achados[0]["primeira_mensagem"], "2026-01-08")

    def test_nome_em_nfd_e_nome_ilegivel_achados_pelo_conteudo(self):
        nfd = unicodedata.normalize("NFD", "Conversa do WhatsApp com 9100 - José Ávila.zip")
        zip_com(self.base / "Desktop" / nfd, CONVERSA)
        zip_com(self.base / "Desktop" / "arquivo-qualquer.zip", NOVA)
        zip_com(self.base / "Desktop" / "fotos.zip", "isto não é conversa")
        achados = descobrir_em([self.base / "Desktop"])
        self.assertEqual(len(achados), 2)
        self.assertTrue(nome_parece_exportacao(nfd))
        self.assertTrue(nome_parece_exportacao("WhatsApp Chat - Obra 12.zip"))
        self.assertTrue(nome_parece_exportacao("Conversa do WhatsApp com X".encode("utf-8").decode("latin-1")))

    def test_txt_solto_vale_mas_o_chat_arquivado_na_obra_nao(self):
        (self.base / "Downloads").mkdir()
        (self.base / "Downloads" / "Conversa do WhatsApp com 55 - Ana.txt").write_text(CONVERSA, encoding="utf-8")
        (self.base / "Downloads" / "lista.txt").write_text("compras: pão", encoding="utf-8")
        arquivada = self.base / "Armanilux" / "Relatorios-de-Obra" / "1 - X" / "01-conversas"
        arquivada.mkdir(parents=True)
        (arquivada / "_chat.txt").write_text(CONVERSA, encoding="utf-8")
        achados = descobrir_em([self.base / "Downloads", self.base / "Armanilux"])
        self.assertEqual([a["tipo"] for a in achados], ["txt"])

    def test_identidade_pelo_nome_e_pelo_grupo(self):
        a = inferir_identidade("Conversa do WhatsApp com 8977.1.v10 - Cliente Teste (OBRA 8977).zip")
        self.assertEqual(a, {"numero": "8977.1", "cliente": "Cliente Teste"})
        b = inferir_identidade("Conversa do WhatsApp com 8977 - Família Silva.zip", "Obra 9000. Cliente: Outro.")
        # O número do nome do arquivo (nome do grupo) vale mais que um "Obra 02" solto no texto.
        self.assertEqual(b, {"numero": "8977", "cliente": "Outro"})
        self.assertEqual(inferir_identidade("Conversa do WhatsApp com Ana.zip", "falei da Obra 02 ontem")["numero"], "")
        self.assertEqual(inferir_identidade("Conversa do WhatsApp com Ana.zip", "Obra 9000. Cliente: Ana.")["numero"], "9000")
        c = inferir_identidade("Conversa do WhatsApp com Ana Lima (OBRA 4321).zip")
        self.assertEqual(c, {"numero": "4321", "cliente": "Ana Lima"})
        d = inferir_identidade("WhatsApp Chat - 1001 - Família Almeida.zip")
        self.assertEqual(d, {"numero": "1001", "cliente": "Família Almeida"})
        e = inferir_identidade("sem-pista.zip")
        self.assertEqual(e["numero"], "")

    def test_numero_depois_de_obra_vale_mais_que_outro_numero_do_nome(self):
        # "apto 302" é o apartamento; a obra é a 8977.
        self.assertEqual(inferir_identidade("Conversa do WhatsApp com apto 302 - Obra 8977.zip")["numero"], "8977")

    def test_zip_corrompido_nao_derruba_a_busca(self):
        (self.base / "Downloads").mkdir()
        (self.base / "Downloads" / "Conversa do WhatsApp com 1.zip").write_bytes(b"nao e zip")
        self.assertEqual(descobrir_em([self.base / "Downloads"]), [])


class RegistroTeste(Ambiente):
    def _achar(self, *pastas):
        return registro.sincronizar(descobrir_em([self.base / p for p in pastas]))

    def test_duplicata_renomeada_nao_entra_de_novo(self):
        zip_com(self.base / "Downloads" / "Conversa do WhatsApp com 1001 - Família Almeida.zip", CONVERSA)
        dados = self._achar("Downloads")
        self.assertEqual(len(dados["fila"]), 1)
        zip_com(self.base / "Downloads" / "Conversa do WhatsApp com 1001 - Família Almeida (1).zip", CONVERSA)
        dados = self._achar("Downloads")
        self.assertEqual(len(dados["exportacoes"]), 1)
        self.assertEqual(len(dados["fila"]), 1)
        self.assertGreaterEqual(dados["repetidos"], 1)
        self.assertIn("Achei 1 conversa sem relatório", registro.formatar_lista(dados))

    def test_lista_mostra_o_nome_do_arquivo_para_a_pessoa_conferir_obra_e_cliente(self):
        zip_com(self.base / "Downloads" / "Conversa do WhatsApp com apto 302 - Obra 8977.zip", SEM_IDENTIDADE)
        lista = registro.formatar_lista(self._achar("Downloads"))
        self.assertIn("Obra 8977", lista)
        self.assertIn("arquivo: Conversa do WhatsApp com apto 302 - Obra 8977.zip", lista)

    def test_estados_ate_concluido_e_zip_vai_para_a_obra(self):
        zip_path = zip_com(self.base / "Downloads" / "Conversa do WhatsApp com 1001.zip", CONVERSA)
        sha = self._achar("Downloads")["fila"][0]
        item = registro.carregar()["exportacoes"][sha]
        self.assertEqual(item["status"], registro.PENDENTE)
        self.assertEqual((item["numero"], item["cliente"]), ("1001", "Família Almeida"))
        self.assertEqual((item["primeira_mensagem"], item["ultima_mensagem"]), ("2026-01-08", "2026-01-13"))
        registro.marcar_andamento(sha)
        self.assertEqual(registro.carregar()["exportacoes"][sha]["status"], registro.ANDAMENTO)
        self.assertEqual(registro.carregar()["fila"], [sha])
        obra = self.base / "obras" / "1001 - Família Almeida"
        registro.registrar_relatorio(sha, str(obra / "05-relatorios" / "r-v1.docx"), 1, str(obra))
        dados = registro.carregar()
        self.assertEqual(dados["exportacoes"][sha]["status"], registro.GERADO)
        self.assertEqual(dados["fila"], [])
        self.assertTrue(zip_path.exists(), "o zip fica no lugar até a pessoa aprovar")
        destino = registro.concluir(sha)
        self.assertFalse(zip_path.exists())
        self.assertEqual(destino, obra / "01-conversas" / zip_path.name)
        self.assertTrue(destino.exists())
        item = registro.carregar()["exportacoes"][sha]
        self.assertEqual(item["status"], registro.CONCLUIDO)
        self.assertEqual(item["caminho"], str(destino))
        with self.assertRaises(RuntimeError):
            registro.concluir(sha)

    def test_nao_conclui_sem_relatorio(self):
        zip_com(self.base / "Downloads" / "Conversa do WhatsApp com 1001.zip", CONVERSA)
        sha = self._achar("Downloads")["fila"][0]
        with self.assertRaises(RuntimeError):
            registro.concluir(sha)

    def test_copiar_mantem_o_original(self):
        zip_path = zip_com(self.base / "Downloads" / "Conversa do WhatsApp com 1001.zip", CONVERSA)
        sha = self._achar("Downloads")["fila"][0]
        obra = self.base / "obras" / "o"
        registro.registrar_relatorio(sha, "x", 1, str(obra))
        registro.concluir(sha, copiar=True)
        self.assertTrue(zip_path.exists())
        self.assertTrue((obra / "01-conversas" / zip_path.name).exists())

    def test_exportacao_nova_da_mesma_obra_oferece_atualizacao(self):
        zip_com(self.base / "Downloads" / "Conversa do WhatsApp com 1001.zip", CONVERSA)
        sha1 = self._achar("Downloads")["fila"][0]
        registro.registrar_relatorio(sha1, "r-v1.docx", 1, str(self.base / "obra"))
        zip_com(self.base / "Downloads" / "Conversa do WhatsApp com 1001 (2).zip", NOVA)
        dados = self._achar("Downloads")
        self.assertEqual(len(dados["fila"]), 1)
        sha2 = dados["fila"][0]
        self.assertNotEqual(sha1, sha2)
        self.assertTrue(dados["exportacoes"][sha2]["atualiza_relatorio"])
        self.assertIn("próxima versão", registro.formatar_lista(dados))

    def test_lista_vazia_e_escolha_invalida(self):
        self.assertIn("Não achei", registro.formatar_lista(registro.carregar()))
        with self.assertRaises(IndexError):
            registro.escolher({"fila": ["a"]}, [2], False)
        self.assertEqual(registro.escolher({"fila": ["a", "b"]}, None, True), ["a", "b"])


class FluxoTeste(Ambiente):
    def _preparar(self):
        preparar(str(self.base / "Armanilux"), "Teste", "Testador", False, "{numero} - {cliente}")

    def test_lista_gera_v1_depois_v2_e_conclui(self):
        self._preparar()
        downloads = self.base / "Downloads"
        zip_com(downloads / "Conversa do WhatsApp com 1001 - Família Almeida.zip", CONVERSA)
        base = ["--downloads", str(downloads), "--skip-transcribe", "--skip-keyframes"]
        self.assertEqual(executar(["--listar", *base]), 0)
        self.assertEqual(executar(["--indice", "1", *base]), 0)
        obra = self.base / "Armanilux" / "Relatorios-de-Obra" / "1001 - Família Almeida"
        self.assertTrue((obra / "05-relatorios" / "Relatorio-Cronologico-Obra-1001-v1-rascunho.docx").exists())
        dados = registro.carregar()
        self.assertEqual(list(dados["exportacoes"].values())[0]["status"], registro.GERADO)

        zip_com(downloads / "Conversa do WhatsApp com 1001 - Família Almeida (novo).zip", NOVA)
        executar(["--listar", *base])
        dados = registro.carregar()
        self.assertEqual(len(dados["fila"]), 1)
        self.assertTrue(dados["exportacoes"][dados["fila"][0]]["atualiza_relatorio"])
        self.assertEqual(executar(["--todas", *base]), 0)
        self.assertTrue((obra / "05-relatorios" / "Relatorio-Cronologico-Obra-1001-v1-rascunho.docx").exists())

        self.assertEqual(executar(["--concluir", "--todas"]), 0)
        estados = sorted(i["status"] for i in registro.carregar()["exportacoes"].values())
        self.assertEqual(estados, [registro.CONCLUIDO, registro.CONCLUIDO])
        self.assertEqual(len(list((obra / "01-conversas").glob("*.zip"))), 2)
        self.assertEqual(list(downloads.glob("*.zip")), [])

    def test_lote_gera_varias_em_sequencia(self):
        self._preparar()
        downloads = self.base / "Downloads"
        zip_com(downloads / "Conversa do WhatsApp com 1001 - Família Almeida.zip", CONVERSA)
        zip_com(downloads / "Conversa do WhatsApp com 2002 - Cliente Dois.zip", CONVERSA.replace("1001", "2002").replace("Família Almeida", "Cliente Dois"))
        base = ["--downloads", str(downloads), "--skip-transcribe", "--skip-keyframes"]
        self.assertEqual(executar(["--todas", *base]), 0)
        pasta = self.base / "Armanilux" / "Relatorios-de-Obra"
        self.assertTrue((pasta / "1001 - Família Almeida" / "05-relatorios" / "Relatorio-Cronologico-Obra-1001-v1-rascunho.docx").exists())
        self.assertTrue((pasta / "2002 - Cliente Dois" / "05-relatorios" / "Relatorio-Cronologico-Obra-2002-v1-rascunho.docx").exists())

    def test_identidade_vem_do_nome_quando_o_grupo_nao_diz(self):
        self._preparar()
        downloads = self.base / "Downloads"
        zip_com(downloads / "Conversa do WhatsApp com 8977.1.v10 - Cliente Teste (OBRA 8977).zip", SEM_IDENTIDADE)
        base = ["--downloads", str(downloads), "--skip-transcribe", "--skip-keyframes"]
        self.assertEqual(executar(["--indice", "1", *base]), 0)
        obra = self.base / "Armanilux" / "Relatorios-de-Obra" / "8977.1 - Cliente Teste"
        self.assertTrue(obra.is_dir())

    def test_obra_e_cliente_corrigidos_pela_pessoa_valem_na_escolha_da_lista(self):
        self._preparar()
        downloads = self.base / "Downloads"
        zip_com(downloads / "Conversa do WhatsApp com apto 302 - Obra 8977.zip", SEM_IDENTIDADE)
        base = ["--downloads", str(downloads), "--skip-transcribe", "--skip-keyframes"]
        self.assertEqual(executar(["--indice", "1", "--obra", "8977", "--cliente", "Família Souza", *base]), 0)
        pasta = self.base / "Armanilux" / "Relatorios-de-Obra"
        self.assertEqual([p.name for p in pasta.iterdir() if p.is_dir() and p.name != "_modelo"], ["8977 - Família Souza"])

    def test_remontagem_atualiza_o_registro_com_o_word_novo(self):
        self._preparar()
        downloads = self.base / "Downloads"
        zip_com(downloads / "Conversa do WhatsApp com 1001 - Família Almeida.zip", CONVERSA)
        base = ["--downloads", str(downloads), "--skip-transcribe", "--skip-keyframes"]
        self.assertEqual(executar(["--indice", "1", *base]), 0)
        obra = self.base / "Armanilux" / "Relatorios-de-Obra" / "1001 - Família Almeida"
        caminho = obra / "04-transcricoes" / "analise.json"
        analise = json.loads(caminho.read_text(encoding="utf-8"))
        analise["revisado"] = True
        caminho.write_text(json.dumps(analise, ensure_ascii=False), encoding="utf-8")

        self.assertEqual(executar(["--rebuild-only", "--obra-dir", str(obra)]), 0)

        [item] = registro.carregar()["exportacoes"].values()
        self.assertEqual(item["status"], registro.GERADO)
        self.assertEqual(Path(item["relatorios"][-1]["caminho"]).name, "Relatorio-Cronologico-Obra-1001-v1.docx")

    def test_sem_nenhuma_pista_pede_so_numero_e_cliente(self):
        self._preparar()
        downloads = self.base / "Downloads"
        zip_com(downloads / "Conversa do WhatsApp com.zip", SEM_IDENTIDADE)
        base = ["--downloads", str(downloads), "--skip-transcribe", "--skip-keyframes"]
        self.assertEqual(executar(["--indice", "1", *base]), 2)


if __name__ == "__main__":
    unittest.main()
