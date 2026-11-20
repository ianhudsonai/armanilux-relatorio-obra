"""Gabarito de obra: confere um relatório contra respostas certas conferidas no grupo.

Uso:
    python tools/pontuar_relatorio.py --gabarito <gabarito.json> --obra-dir "<pasta da obra>" [--docx <arquivo.docx>]

O gabarito de obra real tem dados de cliente: fica FORA deste repositório público.
Sem --docx, usa o .docx mais novo de 05-relatorios. Os marcos, intervalos e somas são refeitos dos
eventos do analise.json com o código desta pasta, como o Word faz: a nota mede a revisão (os fatos e
marcas no analise.json) com o motor atual. Os itens "texto" e "quadro" leem o Word como ele está.

Tipos de conferência (campo "tipo" de cada item de "checks"):
- marco: "etapa", "frente" (opcional), "aceita": ["AAAA-MM-DD"] ou ["AAAA-MM-DD..AAAA-MM-DD"] (faixa)
- intervalo: "de", "para", "frente" (opcional), "aceita": ["30"] ou ["30-32"] (faixa de dias úteis)
- sem_conclusao: a obra não aparece como concluída
- texto: "contem" e "nao_contem" (trechos do Word, com tabelas)
- quadro: "linha" do Quadro-Resumo e "aceita" (trechos que o valor deve ter; basta um)
- evento: "etapa" (uma letra ou várias, ex. "EJ"), "data" (da mensagem ou do fato), "contem" (palavras; basta uma)
- soma_campo: "campo" da etapa J (dias_sem_frente ou dias_perdidos_armanilux, somado como no Word) e "aceita"
- confronto: "descricao" (trecho), "sem_estouro_interno": true e/ou "com_realizado": true
- gantt_sem: "rotulo" que não pode aparecer na linha do tempo
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "relatorio-cronologico-obra" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import analyze  # noqa: E402


def _normal(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def _texto_docx(caminho: Path) -> tuple[str, dict[str, str]]:
    from docx import Document

    documento = Document(str(caminho))
    partes = [p.text for p in documento.paragraphs]
    quadro: dict[str, str] = {}
    for tabela in documento.tables:
        for linha in tabela.rows:
            celulas = [c.text for c in linha.cells]
            partes.append(" | ".join(celulas))
            if len(celulas) == 2:
                quadro.setdefault(celulas[0].strip(), celulas[1].strip())
    return "\n".join(partes), quadro


def _faixa(eventos: list[dict], etapa: str, frente: str | None) -> str:
    faixa = analyze.faixas_dos_marcos(eventos, frente).get(etapa)
    if not faixa:
        return ""
    inicio, ate = faixa
    return inicio if inicio == ate else f"{inicio}..{ate}"


def _intervalo(eventos: list[dict], obra: dict, check: dict) -> str:
    marcos, _ = analyze.intervalos_marcos_de(eventos, obra)
    for item in marcos:
        if item["de"] == check["de"] and item["para"] == check["para"] and (item.get("frente") or None) == (check.get("frente") or None):
            maximo = item.get("dias_uteis_max", item["dias_uteis"])
            return str(item["dias_uteis"]) if maximo == item["dias_uteis"] else f"{item['dias_uteis']}-{maximo}"
    return "(sem esse intervalo)"


def _conferir(check: dict, analise: dict, texto: str, quadro: dict[str, str]) -> tuple[bool, str]:
    eventos = analise.get("eventos") or []
    tipo = check["tipo"]
    if tipo == "marco":
        achado = _faixa(eventos, check["etapa"], check.get("frente"))
        return achado in check["aceita"], achado or "(sem marco)"
    if tipo == "intervalo":
        achado = _intervalo(eventos, analise.get("obra") or {}, check)
        return achado in check["aceita"], achado
    if tipo == "sem_conclusao":
        data = analyze.data_da_conclusao(eventos)
        return not data, data or "sem conclusão"
    if tipo == "texto":
        normal = _normal(texto)
        faltam = [t for t in check.get("contem", []) if _normal(t) not in normal]
        sobram = [t for t in check.get("nao_contem", []) if _normal(t) in normal]
        achado = "; ".join([f"falta: {t}" for t in faltam] + [f"aparece: {t}" for t in sobram])
        return not faltam and not sobram, achado or "ok"
    if tipo == "quadro":
        valor = quadro.get(check["linha"], "")
        return any(_normal(a) in _normal(valor) for a in check["aceita"]), valor or "(linha não encontrada)"
    if tipo == "evento":
        achados = [
            e for e in eventos
            if e["etapa"] in check["etapa"] and check["data"] in (e["data"], e.get("data_evento"))
            and any(_normal(p) in _normal(e.get("ocorrencia") or "") for p in check["contem"])
        ]
        return bool(achados), achados[0]["ocorrencia"][:120] if achados else "(não achado)"
    if tipo == "soma_campo":
        soma = analyze.dias_sem_frente(eventos, check["campo"]).get("dias", 0)
        return soma in check["aceita"], str(soma)
    if tipo == "confronto":
        confronto = analyze.confronto_contrato(eventos, analise.get("prazos_contratuais") or [])
        itens = [c for c in confronto if _normal(check["descricao"]) in _normal(c["descricao"])]
        if not itens:
            return False, "(prazo não encontrado)"
        item = itens[0]
        ok = True
        if check.get("sem_estouro_interno") and item["excedeu"] and not item.get("externo"):
            ok = False
        if check.get("com_realizado") and item["realizado"] is None:
            ok = False
        maximo = item.get("realizado_max")
        realizado = item["realizado"] if not maximo or maximo == item["realizado"] else f"{item['realizado']}-{maximo}"
        return ok, f"realizado {realizado}, estourou {item['excedeu']}, externo {bool(item.get('externo'))}"
    if tipo == "gantt_sem":
        import build_charts

        rotulos = [linha["rotulo"] for linha in build_charts.linhas_gantt(eventos)]
        return not any(_normal(check["rotulo"]) in _normal(r) for r in rotulos), "; ".join(rotulos)
    raise ValueError(f"tipo desconhecido: {tipo}")


def pontuar(analise: dict, docx: Path | None, gabarito: dict) -> dict:
    texto, quadro = _texto_docx(docx) if docx else ("", {})
    itens = []
    for check in gabarito["checks"]:
        ok, achado = _conferir(check, analise, texto, quadro)
        itens.append({"id": check["id"], "ok": ok, "achado": achado, "esperado": check.get("aceita") or check.get("contem") or ""})
    return {"acertos": sum(1 for item in itens if item["ok"]), "total": len(itens), "itens": itens}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--gabarito", required=True, type=Path)
    parser.add_argument("--obra-dir", required=True, type=Path)
    parser.add_argument("--docx", type=Path)
    parser.add_argument("--analise", type=Path, help="padrão: 04-transcricoes/analise.json da obra")
    args = parser.parse_args(argv)
    caminho = args.analise or args.obra_dir / "04-transcricoes" / "analise.json"
    if not caminho.exists():
        print(f"Sem {caminho}: o relatório não foi feito pela skill, então só dá para conferir o Word à mão.")
        return 1
    analise = json.loads(caminho.read_text(encoding="utf-8"))
    analise = analyze.completar_relato(analise)
    docx = args.docx
    if docx is None:
        candidatos = sorted((args.obra_dir / "05-relatorios").glob("*.docx"), key=lambda p: p.stat().st_mtime)
        docx = candidatos[-1] if candidatos else None
    gabarito = json.loads(args.gabarito.read_text(encoding="utf-8"))
    resultado = pontuar(analise, docx, gabarito)
    print(f"Relatório: {docx.name if docx else '(sem Word)'}")
    for item in resultado["itens"]:
        marca = "OK  " if item["ok"] else "ERRO"
        print(f"{marca} {item['id']}: {item['achado']}" + ("" if item["ok"] else f"  (esperado: {item['esperado']})"))
    print(f"\nNota: {resultado['acertos']} de {resultado['total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
