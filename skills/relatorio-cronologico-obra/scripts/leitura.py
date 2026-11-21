"""Divide o material da obra em partes pequenas e mantém as listas do que a revisão já fez.

Num grupo grande a conversa, as transcrições e os textos dos documentos não cabem de uma vez
no que o agente consegue ler: no Codex, a saída de um comando que passa de ~10 KB ou 256
linhas perde o meio. Cada parte aqui cabe nesse limite, junta dias inteiros (quando o dia
cabe) e fica em `04-transcricoes/leitura/`.

- `04-transcricoes/revisao-progresso.md` lista as partes e as folhas de contato; o agente marca
  `[x]` em cada uma depois de ler (4.1) e a revisão continua de onde parou depois de um "continue".
- `04-transcricoes/conferencia.md` lista cada fato e cada texto do relatório, com a parte onde
  procurar a fonte; a conferência independente (4.4) marca `[x]` item por item.

Uma parte (ou um item) que não mudou continua marcada quando as listas são refeitas. Tudo fica
neste computador.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

LIMITE_CARACTERES = 8_000  # ~10 KB em UTF-8 com acentos, já com cabeçalho e rodapé
LIMITE_LINHAS = 150
_FOLGA_CARACTERES = 400  # cabeçalho e rodapé de cada parte
_FOLGA_LINHAS = 6
PASTA = "leitura"
PROGRESSO = "revisao-progresso.md"
CONFERENCIA = "conferencia.md"
INDICE = "indice.json"
MARCA_NOTAS = "## Notas"
COMO_CONFERIU = ("subagente", "segunda passada")
_ITEM = re.compile(r"^- \[([ xX])\] (.+)$", re.MULTILINE)
_DATA_DA_LINHA = re.compile(r"^\[(\d{2})/(\d{2})/(\d{4}) \d{2}:\d{2}\] ", re.MULTILINE)


# ---------- partes ----------


def linha_da_mensagem(mensagem) -> str:
    """A mensagem com data e hora já decididas (dia/mês), para o agente copiar sem adivinhar."""
    autor = mensagem.autor or "(aviso do WhatsApp)"
    extras = []
    if mensagem.encaminhada_por:
        quando = mensagem.encaminhada_em.strftime("%d/%m/%Y %H:%M") if mensagem.encaminhada_em else "data não identificada"
        extras.append(f"(colada no grupo por {mensagem.encaminhada_por} em {quando})")
    if mensagem.data_incerta:
        extras.append("(data incerta: dia e mês podem estar trocados)")
    sufixo = (" " + " ".join(extras)) if extras else ""
    return f"[{mensagem.quando.strftime('%d/%m/%Y %H:%M')}] {autor}: {(mensagem.texto or '').strip()}{sufixo}"


def _cabe(itens: list[str], limite_caracteres: int, limite_linhas: int) -> bool:
    texto = "\n".join(itens)
    return len(texto) <= limite_caracteres and texto.count("\n") + 1 <= limite_linhas


def _pedacos(texto: str, limite_caracteres: int, limite_linhas: int) -> list[str]:
    """Texto grande demais para uma parte (mensagem enorme, documento) em pedaços que cabem."""
    pedacos: list[str] = []
    atual: list[str] = []
    for linha in texto.split("\n"):
        while len(linha) > limite_caracteres:
            if atual:
                pedacos.append("\n".join(atual))
                atual = []
            pedacos.append(linha[:limite_caracteres])
            linha = linha[limite_caracteres:]
        if atual and not _cabe(atual + [linha], limite_caracteres, limite_linhas):
            pedacos.append("\n".join(atual))
            atual = []
        atual.append(linha)
    if atual:
        pedacos.append("\n".join(atual))
    return pedacos


def _paginar(dias: list[list[str]]) -> list[list[str]]:
    """Junta dias inteiros em páginas; dia que não cabe sozinho é partido por mensagem."""
    limite_caracteres = LIMITE_CARACTERES - _FOLGA_CARACTERES
    limite_linhas = LIMITE_LINHAS - _FOLGA_LINHAS

    def cabe(itens: list[str]) -> bool:
        return _cabe(itens, limite_caracteres, limite_linhas)

    paginas: list[list[str]] = []
    atual: list[str] = []
    for dia in dias:
        if cabe(atual + dia):
            atual += dia
            continue
        if atual:
            paginas.append(atual)
            atual = []
        if cabe(dia):
            atual = list(dia)
            continue
        for item in dia:
            for pedaco in [item] if cabe([item]) else _pedacos(item, limite_caracteres, limite_linhas):
                if atual and not cabe(atual + [pedaco]):
                    paginas.append(atual)
                    atual = []
                atual.append(pedaco)
    if atual:
        paginas.append(atual)
    return paginas


def _por_dia(itens: list[tuple[object, str]]) -> list[list[str]]:
    """(dia, texto) na ordem dada -> grupos de itens seguidos do mesmo dia."""
    dias: list[list[str]] = []
    anterior = object()
    for dia, texto in itens:
        if dia != anterior:
            dias.append([])
            anterior = dia
        dias[-1].append(texto)
    return dias


def _datas(pagina: list[str]) -> list[str]:
    """Datas (AAAA-MM-DD) das linhas de mensagem da página, na ordem."""
    return [f"{a}-{m}-{d}" for d, m, a in _DATA_DA_LINHA.findall("\n".join(pagina))]


def _br(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}"


def _partes_da_conversa(mensagens) -> list[dict]:
    paginas = _paginar(_por_dia([(m.quando.date(), linha_da_mensagem(m)) for m in mensagens]))
    partes = []
    for numero, pagina in enumerate(paginas, start=1):
        datas = _datas(pagina)
        de, ate = (min(datas), max(datas)) if datas else ("", "")
        descricao = f"conversa de {_br(de)} a {_br(ate)}, {len(datas)} mensagens" if datas else "conversa"
        partes.append({"nome": f"conversa-{numero:03d}.txt", "secao": "Conversa", "descricao": descricao, "linhas": pagina, "de": de, "ate": ate})
    return partes


def _partes_das_transcricoes(mensagens, transcricoes) -> list[dict]:
    """Cada áudio ou vídeo transcrito, com a data, a hora e o autor da mensagem que o anexou."""
    from common import nome_seguro

    origem: dict[str, object] = {}
    for mensagem in mensagens:
        for anexo in mensagem.anexos:
            origem.setdefault(nome_seguro(anexo).lower(), mensagem)
    citadas, soltas = [], []
    for item in transcricoes or []:
        texto = (item.get("texto") or "").strip()
        if item.get("status") != "ok" or not texto:
            continue  # sem texto: já é lacuna automática, não há o que ler
        arquivo = item.get("arquivo") or ""
        mensagem = origem.get(arquivo.lower())
        if mensagem is None:
            soltas.append((arquivo, f"{arquivo} (nenhuma mensagem cita este arquivo)\n{texto}\n"))
        else:
            cabecalho = f"[{mensagem.quando.strftime('%d/%m/%Y %H:%M')}] {mensagem.autor or ''} — {arquivo}"
            citadas.append(((mensagem.quando, arquivo), f"{cabecalho}\n{texto}\n"))
    itens = [(chave[0].date(), texto) for chave, texto in sorted(citadas, key=lambda par: par[0])]
    itens += [("sem mensagem", texto) for _, texto in sorted(soltas)]
    partes = []
    for numero, pagina in enumerate(_paginar(_por_dia(itens)), start=1):
        datas = _datas(pagina)
        periodo = f" de {_br(min(datas))} a {_br(max(datas))}" if datas else ""
        descricao = f"áudios e vídeos transcritos{periodo}, {len(pagina)} arquivos"
        partes.append({"nome": f"transcricoes-{numero:03d}.txt", "secao": "Áudios e vídeos transcritos", "descricao": descricao, "linhas": pagina})
    return partes


def _partes_dos_documentos(documentos) -> list[dict]:
    """O texto de cada documento em pedaços que cabem. Documento sem texto já é lacuna."""
    partes = []
    for documento in documentos or []:
        texto = (documento.get("texto") or "").strip()
        if not texto:
            continue
        pedacos = _pedacos(texto, LIMITE_CARACTERES - _FOLGA_CARACTERES, LIMITE_LINHAS - _FOLGA_LINHAS)
        for indice, pedaco in enumerate(pedacos, start=1):
            descricao = f"documento {documento.get('arquivo')} (parte {indice} de {len(pedacos)})"
            partes.append({"nome": f"documento-{len(partes) + 1:03d}.txt", "secao": "Documentos", "descricao": descricao, "linhas": [pedaco]})
    return partes


def _folhas(pasta_transcricoes: Path) -> list[dict]:
    pasta = pasta_transcricoes / "folhas-de-contato"
    try:
        indice = json.loads((pasta / "indice.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        indice = {}
    folhas = []
    for folha in sorted(pasta.glob("folha-*.jpg")):
        itens = indice.get(folha.name) or []
        datas = [item["data"].split(" ")[0] for item in itens if item.get("data")]
        periodo = f", de {datas[0]} a {datas[-1]}" if datas else ""
        descricao = f"folha de contato, {len(itens)} imagens{periodo}" if itens else "folha de contato"
        folhas.append({"chave": f"folhas-de-contato/{folha.name}", "descricao": descricao, "hash": _hash(folha.read_bytes())})
    return folhas


def _texto_da_parte(parte: dict) -> str:
    nome = parte["nome"].rsplit(".", 1)[0]
    return f"# {parte['descricao']}\n\n" + "\n".join(parte["linhas"]) + f"\n\n--- fim da parte {nome} ---\n"


# ---------- arquivos e marcas ----------


def _hash(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()[:16]


def _ler(caminho: Path) -> str:
    try:
        return caminho.read_text(encoding="utf-8-sig")
    except OSError:
        return ""


def _escrever(caminho: Path, texto: str) -> bytes:
    dados = ("﻿" + texto).encode("utf-8")  # com BOM: o PowerShell 5.1 lê os acentos certos
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if not caminho.is_file() or caminho.read_bytes() != dados:
        caminho.write_bytes(dados)
    return dados


def _itens(texto: str) -> list[tuple[bool, str]]:
    """(marcado, texto) de cada linha `- [ ] ...` antes das Notas."""
    return [(marca.lower() == "x", resto) for marca, resto in _ITEM.findall(texto.split(MARCA_NOTAS, 1)[0])]


def _notas(texto: str) -> str:
    if MARCA_NOTAS not in texto:
        return ""
    return texto.split(MARCA_NOTAS, 1)[1].partition("\n")[2].strip("\n")


def _guardar_antiga(caminho: Path) -> None:
    """Parte que deixou de existir sai da pasta de leitura sem ser apagada."""
    destino = caminho.parent / "antigas" / caminho.name
    destino.parent.mkdir(exist_ok=True)
    os.replace(caminho, destino)


def _contagem(caminho: Path) -> dict:
    itens = _itens(_ler(caminho))
    return {"feitos": sum(1 for marcado, _ in itens if marcado), "total": len(itens)}


# ---------- revisao-progresso.md ----------


def gerar(pasta_obra: Path, mensagens, transcricoes=None, documentos=None) -> list[Path]:
    """Grava as partes em 04-transcricoes/leitura/ e refaz revisao-progresso.md, mantendo o que já foi lido."""
    pasta_transcricoes = Path(pasta_obra) / "04-transcricoes"
    pasta = pasta_transcricoes / PASTA
    caminho_progresso = pasta_transcricoes / PROGRESSO
    texto_antigo = _ler(caminho_progresso)
    try:
        indice_antigo = json.loads(_ler(pasta / INDICE) or "{}")
    except ValueError:
        indice_antigo = {}
    lidas = {
        (indice_antigo.get(resto.split(" ")[0]) or {}).get("hash")
        for marcado, resto in _itens(texto_antigo)
        if marcado
    } - {None}

    partes = _partes_da_conversa(mensagens) + _partes_das_transcricoes(mensagens, transcricoes) + _partes_dos_documentos(documentos)
    indice: dict[str, dict] = {}
    linhas_por_secao: dict[str, list[str]] = {}
    gravadas = []
    for parte in partes:
        caminho = pasta / parte["nome"]
        chave = f"{PASTA}/{parte['nome']}"
        indice[chave] = {"hash": _hash(_escrever(caminho, _texto_da_parte(parte)))}
        if parte.get("de"):
            indice[chave].update({"de": parte["de"], "ate": parte["ate"]})
        gravadas.append(caminho)
        linhas_por_secao.setdefault(parte["secao"], []).append((chave, parte["descricao"]))
    for antiga in pasta.glob("*.txt"):
        if antiga not in gravadas:
            _guardar_antiga(antiga)
    for folha in _folhas(pasta_transcricoes):
        indice[folha["chave"]] = {"hash": folha["hash"]}
        linhas_por_secao.setdefault("Imagens (folhas de contato)", []).append((folha["chave"], folha["descricao"]))
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / INDICE).write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")

    total = sum(len(linhas) for linhas in linhas_por_secao.values())
    marcadas = sum(1 for linhas in linhas_por_secao.values() for chave, _ in linhas if indice[chave]["hash"] in lidas)
    corpo = [
        "# Revisão: o que já foi lido",
        "",
        "Leia cada parte inteira, uma por vez, e troque `[ ]` por `[x]` assim que terminar (references/revisao.md, 4.1).",
        "Os fatos que achar vão direto para o analise.json; o resto (quem é quem, prazo citado, dúvida) vai em Notas, no fim.",
        "",
        f"Leitura: {marcadas} de {total} partes lidas.",
        "",
    ]
    for secao, linhas in linhas_por_secao.items():
        corpo += [f"## {secao} ({len(linhas)})", ""]
        corpo += [f"- [{'x' if indice[chave]['hash'] in lidas else ' '}] {chave} — {descricao}" for chave, descricao in linhas]
        corpo.append("")
    corpo += [MARCA_NOTAS, "", _notas(texto_antigo)]
    _escrever(caminho_progresso, "\n".join(corpo).rstrip("\n") + "\n")
    return gravadas


def progresso(pasta_obra: Path) -> dict:
    """Quantas partes da lista estão marcadas como lidas."""
    contagem = _contagem(Path(pasta_obra) / "04-transcricoes" / PROGRESSO)
    return {"lidas": contagem["feitos"], "total": contagem["total"]}


# ---------- conferencia.md ----------

# Campos de texto que a conferência confere, na ordem do relatório.
_TEXTOS = (
    "diagnostico_temas",
    "interpretacao_intervalos",
    "diagnostico_prompt",
    "pontos_criticos",
    "impactos_prazo",
    "conclusao_personalizada",
    "recomendacoes_personalizadas",
    "pontos_de_controle",
    "obra_ajustes",
    "pendencias_revisadas",
    "lacunas_adicionais",
)


def _uma_linha(valor) -> str:
    if isinstance(valor, dict):
        valor = " | ".join(f"{chave}: {_uma_linha(item)}" for chave, item in valor.items() if item not in (None, "", [], {}))
    elif isinstance(valor, list):
        valor = "; ".join(_uma_linha(item) for item in valor)
    return re.sub(r"\s+", " ", str(valor)).strip()


def _textos(analise: dict) -> list[str]:
    linhas = []
    for etapa, comentario in sorted((analise.get("comentarios") or {}).items()):
        for campo, valor in (comentario or {}).items() if isinstance(comentario, dict) else []:
            if _uma_linha(valor):
                linhas.append(f"comentarios.{etapa}.{campo}: {_uma_linha(valor)}")
    for campo in _TEXTOS:
        valor = analise.get(campo)
        if isinstance(valor, dict) and campo == "diagnostico_prompt":
            for chave, itens in valor.items():
                for item in itens if isinstance(itens, list) else [itens]:
                    if _uma_linha(item):
                        linhas.append(f"{campo}.{chave}: {_uma_linha(item)}")
        elif isinstance(valor, list):
            linhas += [f"{campo}: {_uma_linha(item)}" for item in valor if _uma_linha(item)]
        elif _uma_linha(valor or ""):
            linhas.append(f"{campo}: {_uma_linha(valor)}")
    return linhas


def _onde_procurar(evento: dict, partes: dict[str, dict]) -> str:
    midias = evento.get("midias") or []
    if midias:
        return "procure " + ", ".join(Path(str(m)).name for m in midias) + " nas transcrições ou em 03-midias"
    data = str(evento.get("data") or "")
    achadas = [chave for chave, info in partes.items() if info.get("de") and info["de"] <= data <= info["ate"]]
    return "procure em " + ", ".join(achadas) if achadas else "procure no material"


def escrever_conferencia(pasta_obra: Path, analise: dict) -> dict:
    """Refaz conferencia.md com os fatos e textos atuais. Item igual a um já conferido continua marcado."""
    pasta_transcricoes = Path(pasta_obra) / "04-transcricoes"
    caminho = pasta_transcricoes / CONFERENCIA
    feitos = {resto.split(" → ")[0] for marcado, resto in _itens(_ler(caminho)) if marcado}
    try:
        partes = json.loads(_ler(pasta_transcricoes / PASTA / INDICE) or "{}")
    except ValueError:
        partes = {}

    fatos = []
    for evento in analise.get("eventos") or []:
        marca = " (programado)" if evento.get("programado") else ""
        texto = f"{evento.get('data', '')} {evento.get('hora', '')} | {evento.get('autor') or 'sem autor'} | etapa {evento.get('etapa', '')} | {_uma_linha(evento.get('ocorrencia', ''))}{marca}"
        fatos.append((texto, _onde_procurar(evento, partes)))
    prazos = [
        (f"prazo: {_uma_linha(item.get('descricao', ''))} | fonte: {_uma_linha(item.get('fonte', ''))} ({item.get('fonte_data', 'sem data')})", "procure a fonte e uma mensagem anterior com outro número ou unidade")
        for item in analise.get("prazos_contratuais") or []
        if isinstance(item, dict)
    ]
    textos = [(texto, "") for texto in _textos(analise)]

    def bloco(titulo: str, itens: list[tuple[str, str]]) -> list[str]:
        if not itens:
            return []
        linhas = [f"## {titulo} ({len(itens)})", ""]
        for texto, onde in itens:
            linhas.append(f"- [{'x' if texto in feitos else ' '}] {texto}" + (f" → {onde}" if onde else ""))
        return linhas + [""]

    todos = fatos + prazos + textos
    conferidos = sum(1 for texto, _ in todos if texto in feitos)
    corpo = [
        "# Conferência independente (references/revisao.md, 4.4)",
        "",
        "Para cada item, ache no material a mensagem, transcrição, documento ou imagem que sustenta o que está escrito.",
        "Marque [x] quando estiver sustentado, ou depois de corrigir, tirar ou virar lacuna no analise.json.",
        "Item corrigido volta para a lista sem marca na próxima remontagem: confira de novo.",
        "",
        f"Conferidos: {conferidos} de {len(todos)}.",
        "",
        *bloco("Fatos", fatos),
        *bloco("Prazos contratuais", prazos),
        *bloco("Textos do relatório", textos),
    ]
    _escrever(caminho, "\n".join(corpo).rstrip("\n") + "\n")
    return {"feitos": conferidos, "total": len(todos)}


def conferencia(pasta_obra: Path) -> dict:
    return _contagem(Path(pasta_obra) / "04-transcricoes" / CONFERENCIA)


def como_conferiu(analise: dict) -> str | None:
    """"subagente" ou "segunda passada", se a revisão registrou a conferência independente."""
    registro = analise.get("conferencia_independente")
    como = (registro or {}).get("como") if isinstance(registro, dict) else None
    return como if como in COMO_CONFERIU else None

