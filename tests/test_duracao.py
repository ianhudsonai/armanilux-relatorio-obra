"""Um total só: a duração da Análise de Prazos é a mesma do Quadro-Resumo (período do grupo), não
"do primeiro fato classificado" (no v13: 304 d.u. no Quadro, 302 na Análise). E cada ciclo que
para no meio mostra a data que falta como dado não identificado (fim da instalação, entrega)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import completar_relato  # noqa: E402


def _evento(data: str, etapa: str, frente: str = "", **extra) -> dict:
    base = {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": "x", "impacto": "", "midias": [], "documentos": []}
    if frente:
        base["frente"] = frente
    base.update(extra)
    return base


def _documento(relato: dict):
    from docx import Document

    import build_docx

    with TemporaryDirectory() as pasta:
        return Document(str(build_docx.montar_docx(relato, Path(pasta) / "r.docx", None, None)))


def _tabela(documento, cabecalho: str):
    for tabela in documento.tables:
        if tabela.rows[0].cells[0].text == cabecalho:
            return [[celula.text for celula in linha.cells] for linha in tabela.rows[1:]]
    raise AssertionError(f"tabela {cabecalho!r} não está no Word")


# Grupo de 02/01 a 10/02/2026; o primeiro fato classificado é de 05/01.
OBRA = {"numero": "1001", "cliente": "Cliente Teste", "periodo_inicio": "2026-01-02", "periodo_fim": "2026-02-10"}


class DuracaoTeste(unittest.TestCase):
    def test_total_da_analise_de_prazos_e_o_do_quadro(self):
        eventos = [_evento("2026-01-05", "C"), _evento("2026-01-12", "D")]
        relato = completar_relato({"obra": OBRA, "eventos": eventos})
        # 02/01 (sexta) → 10/02 (terça), contando do dia seguinte: 20 dias úteis em janeiro (05 a 30)
        # e 7 em fevereiro (02 a 10) = 27; 25/01 cai num domingo.
        self.assertEqual(relato["duracao_marcos"], {"inicio": "2026-01-02", "fim": "2026-02-10", "dias_uteis": 27, "do_grupo": True})
        documento = _documento(relato)
        self.assertEqual(dict(_tabela(documento, "Indicador"))["Duração decorrida (dias úteis)"], "27 dias úteis")
        self.assertEqual(_tabela(documento, "Intervalo entre marcos")[-1], ["DURAÇÃO TOTAL DA OBRA (02/01/2026 → 10/02/2026)", "27 d.u."])
        texto = " ".join(p.text for p in documento.paragraphs)
        self.assertIn("Do início do grupo ao último registro: 27 dias úteis (39 dias corridos).", texto)

    def test_sem_periodo_do_grupo_vale_o_primeiro_e_o_ultimo_registro(self):
        eventos = [_evento("2026-01-05", "C"), _evento("2026-01-12", "D")]
        relato = completar_relato({"obra": {}, "eventos": eventos})
        self.assertEqual(relato["duracao_marcos"], {"inicio": "2026-01-05", "fim": "2026-01-12", "dias_uteis": 5, "do_grupo": False})

    def test_ciclo_incompleto_mostra_a_data_que_falta(self):
        eventos = [
            _evento("2026-01-05", "G", "Living"),
            _evento("2026-01-07", "G", "Banhos"),
            _evento("2026-01-14", "H", "Banhos"),
            _evento("2026-01-21", "I", "Banhos"),
        ]
        relato = completar_relato({"obra": OBRA, "eventos": eventos})
        self.assertEqual(
            [(p["frente"], p["de"], p["para"]) for p in relato["ciclos_incompletos"]],
            [("Living", "G", "H"), ("Banhos", "I", "L")],
        )
        linhas = _tabela(_documento(relato), "Intervalo entre marcos")
        pendentes = [linha for linha in linhas if linha[1] == "pendente"]
        self.assertEqual(len(pendentes), 2)
        self.assertTrue(pendentes[0][0].startswith("Living — "), pendentes[0][0])
        self.assertIn("(05/01/2026) → H – Data das entregas dos materiais na obra: dado não identificado", pendentes[0][0])
        self.assertIn("→ L – Data da conclusão dos serviços e validação final: dado não identificado", pendentes[1][0])

    def test_ciclo_concluido_nao_tem_pendente(self):
        eventos = [
            _evento("2026-01-07", "G"),
            _evento("2026-01-14", "H"),
            _evento("2026-01-21", "I"),
            _evento("2026-02-02", "L", conclusao=True),
        ]
        self.assertEqual(completar_relato({"obra": OBRA, "eventos": eventos})["ciclos_incompletos"], [])

    def test_lacuna_no_meio_do_ciclo_e_sem_marco_entre_datas(self):
        # Living: aprovado e com equipe, sem data de entrega; Banhos: só aprovado. Nenhuma frente tem
        # dois marcos seguidos para medir, e as lacunas aparecem mesmo assim.
        eventos = [_evento("2026-01-05", "G", "Living"), _evento("2026-01-20", "I", "Living"), _evento("2026-01-07", "G", "Banhos"),
                   _evento("2026-01-08", "H")]
        relato = completar_relato({"obra": OBRA, "eventos": eventos})
        self.assertEqual(
            [(p["frente"], p["de"], p["para"]) for p in relato["ciclos_incompletos"]],
            [("Living", "G", "H"), ("Banhos", "G", "H"), ("Living", "I", "L")],
        )
        linhas = _tabela(_documento(relato), "Intervalo entre marcos")
        self.assertEqual([linha[1] for linha in linhas].count("pendente"), 3)
        self.assertFalse(any(linha[0].startswith("Obra em geral") for linha in linhas))

    def test_conclusao_de_uma_frente_fecha_o_ciclo_e_nao_a_obra(self):
        eventos = [
            _evento("2026-01-07", "G", "Banhos"), _evento("2026-01-14", "H", "Banhos"), _evento("2026-01-21", "I", "Banhos"),
            _evento("2026-02-02", "L", "Banhos", conclusao=True),
        ]
        relato = completar_relato({"obra": OBRA, "eventos": eventos})
        self.assertEqual(relato["ciclos_incompletos"], [])
        self.assertEqual(relato["intervalos_marcos"][-1]["para"], "L")
        marcos = {m["marco"]: m["situacao"] for m in relato["marcos"]}
        self.assertEqual(marcos["Conclusão dos serviços e validação final"], "dado não identificado (pendente)")


if __name__ == "__main__":
    unittest.main()
