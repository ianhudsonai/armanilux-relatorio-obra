"""Os dois lados. Prazo que passou do limite porque se esperava o outro lado (aval da arquitetura,
frente da obra) diz quem segurou e não conta como atraso da Armanilux; e os dias perdidos do lado
da Armanilux (imprevisto, equipe doente) são somados ao lado dos dias sem frente da obra."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"))

from analyze import aplicar_ajustes, completar_relato, confronto_contrato, dias_sem_frente  # noqa: E402


def _evento(data: str, etapa: str, ocorrencia: str = "x", **extra) -> dict:
    base = {"data": data, "hora": "09:00", "etapa": etapa, "autor": "Ana", "ocorrencia": ocorrencia, "impacto": "", "midias": [], "documentos": []}
    base.update(extra)
    return base


PISOS = {
    "descricao": "Pisos: medição → projeto preliminar (até 6 d.u.)",
    "inicio": "2025-10-15",
    "fim": "2025-10-28",
    "limite_du": 6,
    "fonte_data": "2025-08-29",
    "quem_segurou": "Arquitetura: aval para iniciar só em 28/10; preliminar enviado no mesmo dia",
    "externo": True,
}
BANHOS = {"descricao": "Banhos: medição → preliminar (até 6 d.u.)", "inicio": "2026-03-12", "fim": "2026-03-30", "limite_du": 6, "fonte_data": "2025-08-29"}
EVENTOS = [
    _evento("2026-06-12", "J", "Entrega reagendada por imprevisto da Armanilux.", dias_perdidos_armanilux=1),
    _evento("2026-07-28", "J", "Instalador doente.", dias_perdidos_armanilux=1),
    _evento("2026-06-15", "J", "Equipe sem frente no Banho Master.", dias_sem_frente=1),
]


def _texto(relato: dict) -> str:
    from docx import Document

    import build_docx

    with TemporaryDirectory() as pasta:
        documento = Document(str(build_docx.montar_docx(relato, Path(pasta) / "r.docx", None, None)))
    partes = [p.text for p in documento.paragraphs]
    for tabela in documento.tables:
        partes.extend(" | ".join(c.text for c in linha.cells) for linha in tabela.rows)
    return "\n".join(partes)


class DoisLadosTeste(unittest.TestCase):
    def test_espera_do_outro_lado_nao_e_atraso_da_armanilux(self):
        pisos, banhos = confronto_contrato([], [PISOS, BANHOS])
        self.assertEqual((pisos["realizado"], pisos["excedeu"], pisos["externo"]), (9, True, True))
        self.assertEqual(pisos["quem_segurou"], PISOS["quem_segurou"])
        self.assertEqual((banhos["excedeu"], banhos["externo"]), (True, False))

    def test_word_mostra_quem_segurou_e_conta_separado(self):
        relato = completar_relato({"obra": {"periodo_inicio": "2025-08-29", "periodo_fim": "2026-08-01"}, "eventos": EVENTOS, "prazos_contratuais": [PISOS, BANHOS]})
        texto = _texto(relato)
        self.assertIn("Prazo contratual de referência | Contrato | Realizado | Quem segurou", texto)
        self.assertIn("9 d.u. | Arquitetura: aval para iniciar só em 28/10; preliminar enviado no mesmo dia", texto)
        self.assertIn("1 de 2 prazos contratuais com as duas datas passou do limite por causa da Armanilux; 1 por espera do outro lado", texto)

    def test_dias_perdidos_dos_dois_lados(self):
        self.assertEqual(dias_sem_frente(EVENTOS, "dias_perdidos_armanilux")["dias"], 2)
        self.assertEqual(dias_sem_frente(EVENTOS)["dias"], 1)
        texto = _texto(completar_relato({"obra": {}, "eventos": EVENTOS}))
        self.assertIn("Dias de equipe sem frente registrados no grupo: 1, em 1 data, de 15/06/2026 a 15/06/2026.", texto)
        self.assertIn("Dias perdidos do lado da Armanilux: 2, em 2 datas, de 12/06/2026 a 28/07/2026.", texto)

    def test_campo_vem_do_adicional_e_do_ajuste(self):
        lido = _evento("2026-08-25", "J")
        eventos = aplicar_ajustes([lido], [{"data": "2026-08-25", "etapa_original": "J", "dias_perdidos_armanilux": 1}])
        self.assertEqual(eventos[0]["dias_perdidos_armanilux"], 1)
        relato = completar_relato({"obra": {}, "eventos": [], "eventos_adicionais": [dict(EVENTOS[0])]})
        self.assertEqual(relato["eventos"][0]["dias_perdidos_armanilux"], 1)


if __name__ == "__main__":
    unittest.main()
