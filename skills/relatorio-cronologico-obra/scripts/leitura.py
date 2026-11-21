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

LIMITE_BYTES = 9_000  # em UTF-8, já com cabeçalho e rodapé: abaixo dos ~10 KB que o Codex mostra
LIMITE_LINHAS = 150
_FOLGA_BYTES = 600  # cabeçalho e rodapé de cada parte
_FOLGA_LINHAS = 6
PASTA = "leitura"
PROGRESSO = "revisao-progresso.md"
CONFERENCIA = "conferencia.md"
INDICE = "indice.json"
MARCA_NOTAS = "## Notas"
COMO_CONFERIU = ("subagente", "segunda passada")
_ITEM = re.compile(r"^- \[([ xX])\] (.*?)\r?$", re.MULTILINE)
_ONDE = " → procure"  # separa o item da conferência da indicação de onde procurar
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


def _bytes(texto: str) -> int:
    return len(texto.encode("utf-8"))


def _cabe(itens: list[str], limite_bytes: int, limite_linhas: int) -> bool:
    texto = "\n".join(itens)
    return _bytes(texto) <= limite_bytes and texto.count("\n") + 1 <= limite_linhas


def _inicio_que_cabe(linha: str, limite_bytes: int) -> str:
    pedaco = linha[:limite_bytes]
    while _bytes(pedaco) > limite_bytes:  # acento e emoji ocupam mais de um byte
        pedaco = pedaco[: max(1, len(pedaco) * 9 // 10)]
    return pedaco


def _pedacos(texto: str, limite_bytes: int, limite_linhas: int) -> list[str]:
    """Texto grande demais para uma parte (mensagem enorme, documento) em pedaços que cabem."""
    pedacos: list[str] = []
    atual: list[str] = []
    for linha in texto.split("\n"):
        while _bytes(linha) > limite_bytes:
            if atual:
                pedacos.append("\n".join(atual))
                atual = []
            pedaco = _inicio_que_cabe(linha, limite_bytes)
            pedacos.append(pedaco)
            linha = linha[len(pedaco):]
        if atual and not _cabe(atual + [linha], limite_bytes, limite_linhas):
            pedacos.append("\n".join(atual))
            atual = []
        atual.append(linha)
    if atual:
        pedacos.append("\n".join(atual))
    return pedacos


def _paginar(dias: list[list[str]]) -> list[list[str]]:
    """Junta dias inteiros em páginas; dia que não cabe sozinho é partido por mensagem."""
    limite_bytes = LIMITE_BYTES - _FOLGA_BYTES
    limite_linhas = LIMITE_LINHAS - _FOLGA_LINHAS

    def cabe(itens: list[str]) -> bool:
        return _cabe(itens, limite_bytes, limite_linhas)

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
            for pedaco in [item] if cabe([item]) else _pedacos(item, limite_bytes, limite_linhas):
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


SECAO_TRANSCRICOES = "Áudios e vídeos transcritos"
_CABECALHO_CITADA = re.compile(r"^\[\d{2}/\d{2}/\d{4} \d{2}:\d{2}\] .*? — (.+)$", re.MULTILINE)
_CABECALHO_SOLTA = re.compile(r"^(.+) \(nenhuma mensagem cita este arquivo\)$", re.MULTILINE)


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
        texto = "\n".join(pagina)
        arquivos = _CABECALHO_CITADA.findall(texto) + _CABECALHO_SOLTA.findall(texto)
        descricao = f"áudios e vídeos transcritos{periodo}, {len(arquivos)} arquivos"
        partes.append({"nome": f"transcricoes-{numero:03d}.txt", "secao": SECAO_TRANSCRICOES, "descricao": descricao, "linhas": pagina, "arquivos": arquivos})
    return partes


def _partes_dos_documentos(documentos) -> list[dict]:
    """O texto de cada documento em pedaços que cabem. Documento sem texto já é lacuna."""
    partes = []
    for documento in documentos or []:
        texto = (documento.get("texto") or "").strip()
        if not texto:
            continue
        pedacos = _pedacos(texto, LIMITE_BYTES - _FOLGA_BYTES, LIMITE_LINHAS - _FOLGA_LINHAS)
        for indice, pedaco in enumerate(pedacos, start=1):
            descricao = f"documento {documento.get('arquivo')} (parte {indice} de {len(pedacos)})"
            partes.append({"nome": f"documento-{len(partes) + 1:03d}.txt", "secao": "Documentos", "descricao": descricao, "linhas": [pedaco], "arquivos": [str(documento.get("arquivo"))]})
    return partes


def _folhas(pasta_transcricoes: Path) -> list[dict]:
    pasta = pasta_transcricoes / "folhas-de-contato"
    try:
        indice = json.loads((pasta / "indice.json").read_text(encoding="utf-8-sig"))
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
    dados = ("\ufeff" + texto).encode("utf-8")  # com BOM: o PowerShell 5.1 lê os acentos certos
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
    """Parte que deixou de existir sai da pasta de leitura sem ser apagada (nem a cópia anterior)."""
    pasta = caminho.parent / "antigas"
    pasta.mkdir(exist_ok=True)
    destino = pasta / caminho.name
    indice = 2
    while destino.exists():
        destino = pasta / f"{caminho.stem}-{indice}{caminho.suffix}"
        indice += 1
    os.replace(caminho, destino)


def _indice(pasta_transcricoes: Path) -> dict:
    try:
        return json.loads(_ler(pasta_transcricoes / PASTA / INDICE) or "{}")
    except ValueError:
        return {}


def _contagem(caminho: Path) -> dict:
    itens = _itens(_ler(caminho))
    return {"feitos": sum(1 for marcado, _ in itens if marcado), "total": len(itens)}


# ---------- revisao-progresso.md ----------


def _gravar_parte(pasta: Path, parte: dict, indice: dict, linhas_por_secao: dict, gravadas: list) -> None:
    caminho = pasta / parte["nome"]
    chave = f"{PASTA}/{parte['nome']}"
    indice[chave] = {"hash": _hash(_escrever(caminho, _texto_da_parte(parte)))}
    for campo in ("de", "ate", "arquivos"):
        if parte.get(campo):
            indice[chave][campo] = parte[campo]
    gravadas.append(caminho)
    linhas_por_secao.setdefault(parte["secao"], []).append((chave, parte["descricao"]))


def gerar(pasta_obra: Path, mensagens, transcricoes=None, documentos=None) -> list[Path]:
    """Grava as partes em 04-transcricoes/leitura/ e refaz revisao-progresso.md, mantendo o que já foi lido."""
    pasta_transcricoes = Path(pasta_obra) / "04-transcricoes"
    pasta = pasta_transcricoes / PASTA
    caminho_progresso = pasta_transcricoes / PROGRESSO
    texto_antigo = _ler(caminho_progresso)
    indice_antigo = _indice(pasta_transcricoes)
    itens_antigos = _itens(texto_antigo)
    lidas = {(indice_antigo.get(resto.split(" ")[0]) or {}).get("hash") for marcado, resto in itens_antigos if marcado} - {None}

    indice: dict[str, dict] = {}
    linhas_por_secao: dict[str, list[str]] = {}
    gravadas = []
    for parte in _partes_da_conversa(mensagens):
        _gravar_parte(pasta, parte, indice, linhas_por_secao, gravadas)
    if transcricoes is None:
        # Exportação nova: as partes são refeitas antes da transcrição terminar. As de transcrição
        # que já existem ficam como estão (e marcadas), até a remontagem trazer as transcrições.
        descricoes = dict(resto.split(" — ", 1) for _, resto in itens_antigos if " — " in resto)
        for chave, info in indice_antigo.items():
            if chave.startswith(f"{PASTA}/transcricoes-") and (pasta_transcricoes / chave).is_file():
                indice[chave] = info
                gravadas.append(pasta_transcricoes / chave)
                linhas_por_secao.setdefault(SECAO_TRANSCRICOES, []).append((chave, descricoes.get(chave, "áudios e vídeos transcritos")))
    else:
        for parte in _partes_das_transcricoes(mensagens, transcricoes):
            _gravar_parte(pasta, parte, indice, linhas_por_secao, gravadas)
    for parte in _partes_dos_documentos(documentos):
        _gravar_parte(pasta, parte, indice, linhas_por_secao, gravadas)
    for antiga in pasta.glob("*.txt"):
        if antiga not in gravadas:
            _guardar_antiga(antiga)
    for folha in _folhas(pasta_transcricoes):
        indice[folha["chave"]] = {"hash": folha["hash"]}
        linhas_por_secao.setdefault("Imagens (folhas de contato)", []).append((folha["chave"], folha["descricao"]))
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / INDICE).write_bytes(json.dumps(indice, ensure_ascii=False, indent=1).encode("utf-8"))

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
    """Começa sempre com "procure": é o que separa a indicação do texto do item."""
    midias = [Path(str(m)).name for m in evento.get("midias") or []]
    if midias:
        nomes = {nome.lower() for nome in midias}
        achadas = [chave for chave, info in partes.items() if nomes & {a.lower() for a in info.get("arquivos") or []}]
        if achadas:
            return "procure em " + ", ".join(achadas) + f" ({', '.join(midias)})"
        return "procure " + ", ".join(midias) + " nas folhas de contato ou em 03-midias"
    data = str(evento.get("data") or "")
    achadas = [chave for chave, info in partes.items() if info.get("de") and info["de"] <= data <= info["ate"]]
    return "procure em " + ", ".join(achadas) if achadas else "procure no material"


def _sem_onde(resto: str) -> str:
    return resto.rsplit(_ONDE, 1)[0] if _ONDE in resto else resto


def escrever_conferencia(pasta_obra: Path, analise: dict) -> dict:
    """Refaz conferencia.md com os fatos e textos atuais. Item igual a um já conferido continua marcado."""
    pasta_transcricoes = Path(pasta_obra) / "04-transcricoes"
    caminho = pasta_transcricoes / CONFERENCIA
    feitos = {_sem_onde(resto) for marcado, resto in _itens(_ler(caminho)) if marcado}
    partes = _indice(pasta_transcricoes)

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


def o_que_falta(pasta_obra: Path, analise: dict) -> list[str]:
    """O que ainda segura a versão final do lado da leitura (4.1) e da conferência independente (4.4)."""
    motivos = []
    lidas = progresso(pasta_obra)
    if lidas["total"] == 0 or lidas["lidas"] < lidas["total"]:
        motivos.append(
            f"{lidas['total'] - lidas['lidas']} de {lidas['total']} partes ainda não foram lidas "
            "(04-transcricoes/revisao-progresso.md; references/revisao.md, 4.1)"
        )
    conferidos = conferencia(pasta_obra)
    if conferidos["feitos"] < conferidos["total"]:
        motivos.append(
            f"a conferência independente ainda não marcou {conferidos['total'] - conferidos['feitos']} "
            f"de {conferidos['total']} itens (04-transcricoes/conferencia.md; references/revisao.md, 4.4)"
        )
    if not como_conferiu(analise):
        motivos.append(
            'falta registrar no analise.json como a conferência independente foi feita: '
            '"conferencia_independente": {"como": "subagente" ou "segunda passada", "data": "AAAA-MM-DD"}'
        )
    return motivos
