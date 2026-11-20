"""Partes do relatório que o Rogério está acostumado a ler, acrescentadas ao formato compacto (20/11/2026):
legenda da classificação, Status por etapa, o que falta provar na etapa L, interpretação dos intervalos,
avaliação por tema no diagnóstico e recomendações com prioridade."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import completar_relato  # noqa: E402


def _evento(data, etapa, ocorrencia, **extra):
    base = {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": ocorrencia, "impacto": "", "midias": [], "documentos": []}
    base.update(extra)
    return base


EVENTOS = [
    _evento("2026-01-05", "A", "Aprovo as chapas do lote 3."),
    _evento("2026-01-07", "C", "Medição da cozinha realizada."),
    _evento("2026-01-20", "D", "Envio o projeto preliminar."),
    _evento("2026-01-26", "G", "Projeto aprovado."),
    _evento("2026-02-10", "H", "Entrega programada para 23/02.", programado=True),
]


def _montar(analise: dict):
    from docx import Document

    import build_docx

    with TemporaryDirectory() as pasta:
        return Document(str(build_docx.montar_docx(analise, Path(pasta) / "r.docx", None, None)))


def _relato(**extra) -> dict:
    return completar_relato({"obra": {"numero": "1001", "cliente": "Cliente Teste"}, "eventos": [dict(e) for e in EVENTOS], **extra})


def _textos(documento) -> list[str]:
    return [p.text for p in documento.paragraphs]


def _depois(textos: list[str], titulo: str) -> list[str]:
    return textos[textos.index(titulo) + 1 :]


class ClassificacaoEStatusTeste(unittest.TestCase):
    def test_nota_metodologica_explica_a_classificacao(self):
        textos = _textos(_montar(_relato()))
        [legenda] = [t for t in textos if t.startswith("Classificação usada:")]
        for termo in ("fato documentado", "programado", "dependência externa", "dado não identificado", "impacto potencial"):
            self.assertIn(termo, legenda)

    def test_status_escrito_na_revisao_fecha_a_etapa(self):
        relato = _relato(comentarios={"C": {"status": "medição realizada em 07/01/2026."}})
        textos = _textos(_montar(relato))
        etapa_c = _depois(textos, "C – Data da medição “in loco”")
        self.assertTrue(etapa_c[0].startswith("Leitura da Etapa C:") or any(t.startswith("Leitura da Etapa C:") for t in etapa_c[:3]))
        self.assertIn("Status: medição realizada em 07/01/2026.", etapa_c[:4])

    def test_sem_status_escrito_etapa_vazia_ou_so_programada_diz_isso(self):
        textos = _textos(_montar(_relato()))
        self.assertIn("Status: sem registro no grupo – dado não identificado.", _depois(textos, "B – Solicitação de vistas e/ou visitas “in loco”")[:4])
        self.assertIn("Status: programado, sem confirmação no grupo.", _depois(textos, "H – Data das entregas dos materiais na obra")[:4])
        # Etapa com fato realizado e sem status escrito não ganha linha inventada.
        self.assertFalse([t for t in _depois(textos, "A – Aprovação de chapas")[:3] if t.startswith("Status:")])


class EtapaLEIntervalosTeste(unittest.TestCase):
    def test_etapa_l_lista_o_que_o_grupo_ainda_nao_comprova(self):
        textos = _textos(_montar(_relato()))
        [falta] = [t for t in textos if t.startswith("Sem comprovação no grupo até 10/02/2026:")]
        for marco in ("entrega do material na obra", "entrada da equipe de instalação", "conclusão dos serviços e validação final"):
            self.assertIn(marco, falta)
        self.assertNotIn("medição in loco", falta)

    def test_interpretacao_escrita_na_revisao_vira_coluna_dos_intervalos(self):
        relato = _relato(interpretacao_intervalos=[{"de": "D", "para": "G", "texto": "Análise e aprovação pelo cliente."}])
        tabela = next(t for t in _montar(relato).tables if t.rows[0].cells[0].text == "Intervalo entre marcos")
        self.assertEqual([c.text for c in tabela.rows[0].cells], ["Intervalo entre marcos", "Dias úteis", "Interpretação"])
        linha = next(r for r in tabela.rows[1:] if "(20/01/2026)" in r.cells[0].text and "(26/01/2026)" in r.cells[0].text)
        self.assertEqual(linha.cells[2].text, "Análise e aprovação pelo cliente.")
        sem = next(t for t in _montar(_relato()).tables if t.rows[0].cells[0].text == "Intervalo entre marcos")
        self.assertEqual(len(sem.rows[0].cells), 2)


def _tabela(documento, primeiro_titulo: str) -> list[list[str]]:
    tabela = next(t for t in documento.tables if t.rows[0].cells[0].text == primeiro_titulo)
    return [[c.text for c in r.cells] for r in tabela.rows]


class DiagnosticoERecomendacoesTeste(unittest.TestCase):
    def test_diagnostico_abre_com_a_avaliacao_de_cada_tema(self):
        temas = [
            {"tema": "Projeto executivo da marcenaria", "avaliacao": "Gargalo documentado", "leitura": "Chegou em 20/01/2026."},
            {"tema": "Preliminar da Armanilux", "avaliacao": "Fluxo eficiente", "leitura": "Enviado no mesmo dia."},
        ]
        documento = _montar(_relato(diagnostico_temas=temas))
        self.assertEqual(
            _tabela(documento, "Tema"),
            [
                ["Tema", "Avaliação", "Leitura"],
                ["Projeto executivo da marcenaria", "Gargalo documentado", "Chegou em 20/01/2026."],
                ["Preliminar da Armanilux", "Fluxo eficiente", "Enviado no mesmo dia."],
            ],
        )
        textos = _textos(documento)
        self.assertLess(textos.index("Análise Técnica — Diagnóstico"), textos.index("1. Reprocessos identificados"))

    def test_recomendacoes_com_prioridade_viram_tabela_e_pontos_de_controle_seguem(self):
        recomendacoes = [
            {"prioridade": "Alta", "medida": "Exigir o executivo da marcenaria antes de medir.", "resultado": "Evitar incompatibilidades."},
            "Atualizar o grupo toda semana.",
        ]
        controle = ["Liberação para medição: condições físicas confirmadas.", "Encerramento: vistoria e aceite final."]
        documento = _montar(_relato(recomendacoes_personalizadas=recomendacoes, pontos_de_controle=controle))
        self.assertEqual(
            _tabela(documento, "Prioridade"),
            [
                ["Prioridade", "Medida proposta", "Resultado esperado"],
                ["Alta", "Exigir o executivo da marcenaria antes de medir.", "Evitar incompatibilidades."],
                ["—", "Atualizar o grupo toda semana.", ""],
            ],
        )
        textos = _textos(documento)
        depois = _depois(textos, "Pontos de controle recomendados")
        self.assertEqual(depois[:2], [f"• {item}" for item in controle])

    def test_recomendacao_so_em_texto_continua_lista_numerada(self):
        documento = _montar(_relato(recomendacoes_personalizadas=["Atualizar o grupo toda semana."]))
        self.assertIn("1. Atualizar o grupo toda semana.", _textos(documento))
        self.assertFalse([t for t in documento.tables if t.rows[0].cells[0].text == "Prioridade"])
        self.assertNotIn("Pontos de controle recomendados", _textos(documento))

    def test_recomendacao_em_tabela_conta_como_escrita_para_a_versao_final(self):
        import build_docx

        relato = _relato(recomendacoes_personalizadas=[{"prioridade": "Alta", "medida": "Exigir o executivo.", "resultado": ""}])
        self.assertNotIn("recomendacoes_personalizadas", build_docx.textos_que_faltam(relato))


if __name__ == "__main__":
    unittest.main()
