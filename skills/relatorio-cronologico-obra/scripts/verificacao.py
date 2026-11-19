"""Conferência mecânica dos fatos do relatório contra a conversa e as transcrições.

Não julga o sentido do texto: só confere se cada fato aponta para uma mensagem
(mesmo dia, mesma hora, mesmo autor) ou para uma mídia que foi transcrita.
O que não bater vai para 04-transcricoes/verificacao.md, para o agente corrigir
antes de gravar "revisado": true.
"""

from __future__ import annotations

import re
from pathlib import Path

from common import formatar_data, normalizar
from parse_whatsapp import Mensagem


def _palavras(nome: str | None) -> list[str]:
    return re.findall(r"\w+", normalizar(nome or ""))


def _mesmo_autor(do_evento: str, da_mensagem: str | None) -> bool:
    """O agente reescreve o nome ("Ana (Empresa)" para "Ana, Empresa", ou só "Ana").
    Basta o primeiro nome bater; no mesmo dia e minuto isso já identifica a mensagem."""
    if not do_evento:
        return True
    a, b = _palavras(do_evento), _palavras(da_mensagem)
    return bool(a) and bool(b) and a[0] == b[0]


CONFIRMADO = "confirmado"
CONFIRMADO_MIDIA = "confirmado pela mídia"


def confirmado(item: dict) -> bool:
    return item["situacao"] in (CONFIRMADO, CONFIRMADO_MIDIA)


def _situacao(evento: dict, mensagens: list[Mensagem], conhecidas: set[str]) -> tuple[str, str]:
    if "[fonte:" in (evento.get("ocorrencia") or "") and evento.get("midias"):
        faltando = [nome for nome in evento["midias"] if nome.lower() not in conhecidas]
        if faltando:
            return "mídia não encontrada", ", ".join(faltando)
        return CONFIRMADO_MIDIA, ", ".join(evento["midias"])
    # Fato acrescentado na revisão sem hora fica gravado como 00:00.
    hora = "" if (evento.get("hora") or "") in ("", "00:00") else evento["hora"]
    autor = evento.get("autor") or ""
    if not autor and not hora:
        return "sem autor nem hora", "sem dado para achar a mensagem"
    do_dia = [
        mensagem
        for mensagem in mensagens
        if mensagem.data.isoformat() == evento.get("data") and _mesmo_autor(autor, mensagem.autor)
    ]
    if not do_dia:
        return "sem mensagem correspondente", ""
    if not hora or any(mensagem.hora == hora for mensagem in do_dia):
        return CONFIRMADO, ""
    return "hora diferente", "mensagens do autor nesse dia: " + ", ".join(sorted({m.hora for m in do_dia}))


def verificar_eventos(
    eventos: list[dict],
    mensagens: list[Mensagem],
    transcricoes: list[dict],
    arquivos: list[str] | tuple[str, ...] = (),
) -> list[dict]:
    """`arquivos`: nomes das fotos e documentos da pasta da obra (fonte de fato visual)."""
    conhecidas = {
        (item.get("arquivo") or "").lower()
        for item in transcricoes
        if item.get("status") == "ok" and item.get("texto")
    } | {Path(nome).name.lower() for nome in arquivos}
    saida = []
    for evento in eventos:
        situacao, detalhe = _situacao(evento, mensagens, conhecidas)
        saida.append(
            {
                "data": evento.get("data", ""),
                "hora": evento.get("hora", ""),
                "etapa": evento.get("etapa", ""),
                "autor": evento.get("autor", ""),
                "ocorrencia": evento.get("ocorrencia", ""),
                "situacao": situacao,
                "detalhe": detalhe,
            }
        )
    return saida


def escrever_verificacao(itens: list[dict], destino: Path) -> Path:
    problemas = [item for item in itens if not confirmado(item)]
    linhas = [
        "# Conferência dos fatos do relatório",
        "",
        f"{len(itens)} fatos conferidos; {len(itens) - len(problemas)} batem com a conversa ou com uma mídia transcrita; "
        f"{len(problemas)} precisam de conferência.",
        "",
        "Corrija cada item abaixo em `analise.json` (data, hora, autor ou etapa) ou tire o fato com `ajustes_eventos`. "
        "Fato que só existe na sua leitura e não no grupo não entra no relatório.",
        "",
    ]
    for item in problemas:
        trecho = " ".join(item["ocorrencia"].split())[:160]
        linhas.append(
            f"- **{item['situacao']}** — {formatar_data(item['data'])} {item['hora']} | etapa {item['etapa']} | "
            f"{item['autor'] or 'sem autor'} | {trecho}" + (f" ({item['detalhe']})" if item["detalhe"] else "")
        )
    if not problemas:
        linhas.append("Nenhum fato sem correspondência.")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return destino
