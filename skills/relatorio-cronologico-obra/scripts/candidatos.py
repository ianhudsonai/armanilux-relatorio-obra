"""Separa, por etapa, as mensagens do grupo que provavelmente falam dela.

A leitura automática das etapas é conservadora e perde muita coisa num grupo
grande e informal. Este arquivo ajuda quem revisa (o agente) a achar o que o
grupo realmente diz de cada etapa, sem ler milhares de mensagens. Não decide nada:
quem decide é quem lê. Tudo fica neste computador.
"""

from __future__ import annotations

import re
from pathlib import Path

from common import normalizar
from parse_whatsapp import Mensagem, texto_util

# Palavras largas de propósito: aqui vale recall, quem revisa filtra.
PADROES = {
    "A": ("Aprovação de chapas", r"\b(chapa|chapas|lote|amostra|pedra|granito|marmore|quartzito|quartzo|material)\b.*\b(aprov|escolh|fechad|defin|ok)|\b(aprov|escolh|fechad|defin)\w*.*\b(chapa|chapas|lote|amostra|pedra|granito|marmore|quartzito|material|materiais)\b"),
    "B": ("Solicitação de vistas e visitas in loco", r"\b(visita|vistoria|in loco|ir (na|a) obra|passar na obra|liberac\w+ (para|das) medic)"),
    "C": ("Medição in loco", r"\b(medi(r|mos|u|cao|coes)|medida|folha de medicao|ficha de medicao|levantamento)\b"),
    "D": ("Envio do projeto preliminar", r"\b(projeto|desenho|layout|planta|render|proposta)\b.*\b(segue|enviei|enviado|anexo|preliminar|primeira versao|encaminh)|\b(segue|enviei|encaminh\w+)\b.*\b(projeto|desenho|layout|planta|render)"),
    "E": ("Solicitações de revisão de projeto", r"\b(revis\w+|alterac\w+|ajuste|ajustar|mudanca|mudar|trocar|trocamos|corrigir|corrigido)\b"),
    "F": ("Envio de projeto revisado", r"\b(revisad[oa]|nova versao|versao atualizada|projeto atualizado|r[0-9]|v[0-9]+ do projeto)\b|\b(segue|enviei|encaminh\w+)\b.*\b(revis|atualizad|ajustad)"),
    "G": ("Aprovação do projeto", r"\b(aprov\w+|de acordo|pode (seguir|produzir|cortar|fabricar)|liberado para (producao|corte))\b.*\b(projeto|desenho|layout|planta|producao|corte)|\bprojeto\b.*\b(aprov\w+|de acordo|liberad\w+)"),
    "H": ("Entrega dos materiais na obra", r"\b(entreg\w+|chegou|chegaram|descarreg\w+|recebid[oa]s?|recebemos)\b.*\b(obra|material|chapa|pedra|pecas|bancada|cuba|local)|\b(material|chapas?|pecas|bancadas?)\b.*\b(entreg\w+|chegou|chegaram|descarreg\w+)"),
    "I": ("Entrada da equipe de instalação", r"\b(equipe|marmorista|instaladores?|montadores?)\b.*\b(entr\w+|inicio|iniciou|comeca\w*|esta na obra|amanha)|\b(inicio|comeco|comecamos|iniciamos)\b.*\b(instala\w+|assentamento|montagem)"),
    "J": ("Ocorrências e interferências de obra", r"\b(nao (foi|esta|estava|da|deu)|impediu|impossivel|atrasou|atraso|aguardando|falta de|sem acesso|nao liberou|erro|errado|desnivel|contrapiso|ponto de agua|marcenaria|esgoto|hidraulic\w+|infiltrac\w+|quebr\w+)\b"),
    "L": ("Conclusão e validação final", r"\b(conclu\w+|finaliz\w+|terminamos|terminou|entregue|aceite|aprovad[oa] (pelo|pela) cliente|termo (de )?(entrega|aceite)|vistoria final|obra pronta)\b"),
}
PORTAO_TAMANHO = 150
LIMITE_POR_ETAPA = 30


def _resumo(msg: Mensagem) -> str:
    texto = texto_util(msg)
    if len(texto) > PORTAO_TAMANHO:
        texto = texto[:PORTAO_TAMANHO].rstrip() + "…"
    anexos = f" [anexos: {', '.join(msg.anexos)}]" if msg.anexos else ""
    autor = (msg.autor or "").split(",")[0][:30]
    return f"{msg.data.isoformat()} {msg.hora} | {autor} | {texto}{anexos}"


def selecionar(mensagens: list[Mensagem]) -> dict[str, list[Mensagem]]:
    """Mensagens candidatas por etapa. Passa de 40? Fica com as de texto mais informativo."""
    saida: dict[str, list[Mensagem]] = {codigo: [] for codigo in PADROES}
    for msg in mensagens:
        if msg.sistema:
            continue
        base = normalizar(msg.texto)
        if len(base) < 12:
            continue
        for codigo, (_, padrao) in PADROES.items():
            if re.search(padrao, base):
                saida[codigo].append(msg)
    for codigo, itens in saida.items():
        if len(itens) > LIMITE_POR_ETAPA:
            # Mantém a ordem do tempo, mas só as mais ricas em informação.
            ricas = sorted(itens, key=lambda m: len(m.texto), reverse=True)[:LIMITE_POR_ETAPA]
            saida[codigo] = sorted(ricas, key=lambda m: m.quando)
    return saida


def escrever(mensagens: list[Mensagem], destino: Path) -> Path:
    por_etapa = selecionar(mensagens)
    linhas = [
        "# Candidatos por etapa",
        "",
        "Mensagens do grupo que provavelmente falam de cada etapa. Lista larga de propósito:",
        "confira cada uma. Para acrescentar um fato ao relatório, use `eventos_adicionais` no",
        "analise.json. Para tirar um fato errado, use `ajustes_eventos` com `\"remover\": true`.",
        "",
    ]
    for codigo, (titulo, _) in PADROES.items():
        itens = por_etapa[codigo]
        linhas.append(f"## {codigo} – {titulo} ({len(itens)})")
        linhas.extend(f"- {_resumo(m)}" for m in itens) if itens else linhas.append("- nenhuma mensagem candidata")
        linhas.append("")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return destino
