"""Etapa J dividida por tipo, como no relatório aprovado (J.1 civil e terceiros, J.2 a frente
crítica, J.3 logística…), e o total de dias de equipe sem frente, quando o grupo permite contar."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import aplicar_ajustes, completar_relato, dias_sem_frente  # noqa: E402


def _j(data: str, ocorrencia: str, **extra) -> dict:
    base = {"data": data, "hora": "09:00", "etapa": "J", "autor": "Ana", "ocorrencia": ocorrencia, "impacto": "Equipe parada.", "midias": [], "documentos": []}
    base.update(extra)
    return base


def _documento(relato: dict):
    from docx import Document

    import build_docx

    with TemporaryDirectory() as pasta:
        return Document(str(build_docx.montar_docx(relato, Path(pasta) / "r.docx", None, None)))


def _secao_j(documento) -> list[tuple[str, list[str]]]:
    """(subtítulo, ocorrências da tabela logo abaixo) dentro da etapa J."""
    corpo = documento.element.body
    saida, dentro, titulo = [], False, ""
    for bloco in corpo.iterchildren():
        tag = bloco.tag.rsplit("}", 1)[-1]
        if tag == "p":
            texto = "".join(t.text or "" for t in bloco.iter() if t.tag.endswith("}t"))
            if texto.startswith("J – "):
                dentro = True
            elif texto.startswith("L – "):
                break
            elif dentro and texto.startswith("J."):
                titulo = texto
        elif tag == "tbl" and dentro:
            linhas = bloco.findall(".//{*}tr")[1:]
            textos = ["".join(t.text or "" for t in linha.findall(".//{*}tc")[1].iter() if t.tag.endswith("}t")) for linha in linhas]
            saida.append((titulo, textos))
    return saida


EVENTOS = [
    _j("2026-06-15", "Elevador de serviço inativo na entrega.", grupo="Logística"),
    _j("2026-06-15", "Base da banheira não construída.", grupo="Civil e terceiros", dias_sem_frente=1),
    _j("2026-07-10", "Contrapiso impede a instalação.", grupo="Civil e terceiros", dias_sem_frente=2),
    _j("2026-08-03", "Dreno da floreira em alteração.", dias_sem_frente=1),
]


class EtapaJTeste(unittest.TestCase):
    def test_tabela_j_dividida_por_tipo_na_ordem_do_primeiro_fato(self):
        secoes = _secao_j(_documento(completar_relato({"obra": {}, "eventos": EVENTOS})))
        self.assertEqual(
            secoes,
            [
                ("J.1 — Logística", ["Elevador de serviço inativo na entrega."]),
                ("J.2 — Civil e terceiros", ["Base da banheira não construída.", "Contrapiso impede a instalação."]),
                ("J.3 — Outras interferências", ["Dreno da floreira em alteração."]),
            ],
        )

    def test_sem_tipo_continua_uma_tabela_so(self):
        eventos = [{k: v for k, v in e.items() if k != "grupo"} for e in EVENTOS]
        secoes = _secao_j(_documento(completar_relato({"obra": {}, "eventos": eventos})))
        self.assertEqual(len(secoes), 1)
        self.assertEqual(secoes[0][0], "")

    def test_total_de_dias_sem_frente(self):
        self.assertEqual(dias_sem_frente(EVENTOS), {"dias": 4, "datas": 3, "inicio": "2026-06-15", "fim": "2026-08-03"})
        texto = " ".join(p.text for p in _documento(completar_relato({"obra": {}, "eventos": EVENTOS})).paragraphs)
        self.assertIn("Dias de equipe sem frente registrados no grupo: 4, em 3 datas, de 15/06/2026 a 03/08/2026.", texto)

    def test_sem_contagem_nao_inventa_total(self):
        eventos = [{k: v for k, v in e.items() if k != "dias_sem_frente"} for e in EVENTOS]
        self.assertEqual(dias_sem_frente(eventos), {})
        texto = " ".join(p.text for p in _documento(completar_relato({"obra": {}, "eventos": eventos})).paragraphs)
        self.assertNotIn("Dias de equipe sem frente", texto)

    def test_tipo_e_dias_vem_do_adicional_e_do_ajuste(self):
        lido = _j("2026-06-22", "Contrapisos fora de cota.")
        eventos = aplicar_ajustes([lido], [{"data": "2026-06-22", "etapa_original": "J", "grupo": "Civil e terceiros", "dias_sem_frente": 1}])
        extra = {"data": "2026-06-23", "hora": "10:00", "etapa": "J", "autor": "Ana", "ocorrencia": "Sem frente.", "grupo": "Civil e terceiros", "dias_sem_frente": 1}
        relato = completar_relato({"obra": {}, "eventos": eventos, "eventos_adicionais": [extra]})
        self.assertEqual([e.get("grupo") for e in relato["eventos"]], ["Civil e terceiros", "Civil e terceiros"])
        self.assertEqual(dias_sem_frente(relato["eventos"])["dias"], 2)

    def test_mesma_data_conta_uma_vez(self):
        # Duas mensagens do mesmo dia sobre a mesma equipe parada: 1 dia, não 2. Parada longa contada
        # numa mensagem só (7 dias) vale inteira.
        eventos = [_j("2026-08-03", "Sem frente nos banhos.", dias_sem_frente=1), _j("2026-08-03", "Dia perdido.", dias_sem_frente=1),
                   _j("2026-07-22", "Equipe fora de 13 a 21/07.", dias_sem_frente=7)]
        self.assertEqual(dias_sem_frente(eventos), {"dias": 8, "datas": 2, "inicio": "2026-07-22", "fim": "2026-08-03"})

    def test_ajuste_limpa_o_tipo_errado(self):
        lido = _j("2026-06-22", "Contrapisos fora de cota.", grupo="Logística", dias_sem_frente=1)
        eventos = aplicar_ajustes([lido], [{"data": "2026-06-22", "etapa_original": "J", "grupo": "", "dias_sem_frente": 0}])
        self.assertEqual((eventos[0]["grupo"], eventos[0]["dias_sem_frente"]), ("", 0))


if __name__ == "__main__":
    unittest.main()
