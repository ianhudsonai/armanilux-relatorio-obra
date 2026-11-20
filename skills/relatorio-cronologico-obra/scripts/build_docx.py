"""Monta o Relatório Cronológico de Obra em .docx, no formato da Armanilux."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from analyze import (
    LIMITE_INTERVALO_LONGO,
    ORDEM,
    TITULOS,
    aprovacoes_revistas,
    ciclos_incompletos,
    confronto_contrato,
    data_da_conclusao,
    dias_sem_frente,
    diz_programado,
    duracao_da_obra,
    frentes_da_obra,
    grupos_da_etapa_j,
    intervalos_marcos_de,
    marcos_de,
    primeira_programacao,
    primeiros_marcos,
)
from business_days import dias_uteis_entre
from common import DADO, LARGURA_FIGURA_CM, formatar_data
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

NAVY = RGBColor(0x44, 0x28, 0x19)  # marrom da marca Armanilux
DOURADO = RGBColor(0xC3, 0xA5, 0x6D)
DOURADO_HEX = "C3A56D"
GRAFITE = RGBColor(0x22, 0x22, 0x22)
CINZA = RGBColor(0x5C, 0x6B, 0x73)
BRANCO = RGBColor(0xFF, 0xFF, 0xFF)
LARGURA = 17.4


def _fonte(run, tamanho: int, negrito: bool = False, cor: RGBColor | None = None, italico: bool = False) -> None:
    run.font.name = "Calibri"
    run.font.size = Pt(tamanho)
    run.bold = negrito
    run.italic = italico
    run.font.color.rgb = cor or GRAFITE
    propriedades = run._element.get_or_add_rPr()
    fontes = propriedades.find(qn("w:rFonts"))
    if fontes is None:
        fontes = OxmlElement("w:rFonts")
        propriedades.append(fontes)
    for atributo in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fontes.set(qn(atributo), "Calibri")


def _sombrear(celula, preenchimento: str) -> None:
    propriedades = celula._tc.get_or_add_tcPr()
    sombra = OxmlElement("w:shd")
    sombra.set(qn("w:val"), "clear")
    sombra.set(qn("w:color"), "auto")
    sombra.set(qn("w:fill"), preenchimento)
    propriedades.append(sombra)


def _larguras(tabela, larguras_cm: list[float]) -> None:
    tabela.autofit = False
    tabela.allow_autofit = False
    grade = tabela._tbl.find(qn("w:tblGrid"))
    if grade is not None:
        for filho in list(grade):
            grade.remove(filho)
    else:
        grade = OxmlElement("w:tblGrid")
        tabela._tbl.tblPr.addnext(grade)
    for largura in larguras_cm:
        coluna = OxmlElement("w:gridCol")
        coluna.set(qn("w:w"), str(int(largura * 567)))
        grade.append(coluna)
    for linha in tabela.rows:
        for indice, celula in enumerate(linha.cells):
            celula.width = Cm(larguras_cm[indice])


def _texto_celula(celula, texto: str, *, negrito: bool = False, tamanho: int = 10, cor: RGBColor | None = None, centro: bool = False) -> None:
    celula.text = ""
    celula.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    paragrafo = celula.paragraphs[0]
    for vazio in list(paragrafo.runs):  # celula.text = "" deixa um trecho vazio antes do texto
        vazio._element.getparent().remove(vazio._element)
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER if centro else WD_ALIGN_PARAGRAPH.LEFT
    paragrafo.paragraph_format.space_after = Pt(0)
    paragrafo.paragraph_format.space_before = Pt(0)
    trecho = paragrafo.add_run(texto)
    _fonte(trecho, tamanho, negrito=negrito, cor=cor)


def _cabecalho_tabela(tabela, titulos: list[str]) -> None:
    for indice, titulo in enumerate(titulos):
        _texto_celula(tabela.rows[0].cells[indice], titulo, negrito=True, tamanho=10, cor=BRANCO, centro=True)
        _sombrear(tabela.rows[0].cells[indice], "442819")
    linha = tabela.rows[0]._tr
    propriedades = linha.get_or_add_trPr()
    repetir = OxmlElement("w:tblHeader")
    propriedades.append(repetir)


def _configurar_documento(documento: Document) -> None:
    normal = documento.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.font.color.rgb = GRAFITE
    propriedades = normal.element.get_or_add_rPr()
    fontes = propriedades.find(qn("w:rFonts"))
    if fontes is None:
        fontes = OxmlElement("w:rFonts")
        propriedades.append(fontes)
    for atributo in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fontes.set(qn(atributo), "Calibri")
    for nome, tamanho in (("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 12)):
        estilo = documento.styles[nome]
        estilo.font.name = "Calibri"
        estilo.font.color.rgb = NAVY
        estilo.font.size = Pt(tamanho)
        estilo.font.bold = True
    secao = documento.sections[0]
    secao.page_width = Cm(21.0)
    secao.page_height = Cm(29.7)
    secao.left_margin = Cm(1.8)
    secao.right_margin = Cm(1.8)
    secao.top_margin = Cm(1.6)
    secao.bottom_margin = Cm(1.6)
    cabecalho = secao.header.paragraphs[0]
    cabecalho.text = ""
    trecho = cabecalho.add_run("ARMANILUX  ·  Relatório cronológico de obra")
    _fonte(trecho, 9, cor=CINZA)
    rodape = secao.footer.paragraphs[0]
    rodape.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    trecho = rodape.add_run("Gerado no computador  ·  página ")
    _fonte(trecho, 9, cor=CINZA)
    _campo_pagina(rodape)


def _campo_pagina(paragrafo) -> None:
    trecho = paragrafo.add_run()
    inicio = OxmlElement("w:fldChar")
    inicio.set(qn("w:fldCharType"), "begin")
    instrucao = OxmlElement("w:instrText")
    instrucao.set(qn("xml:space"), "preserve")
    instrucao.text = " PAGE "
    fim = OxmlElement("w:fldChar")
    fim.set(qn("w:fldCharType"), "end")
    trecho._r.append(inicio)
    trecho._r.append(instrucao)
    trecho._r.append(fim)
    _fonte(trecho, 9, cor=CINZA)


def _paragrafo(documento: Document, texto: str, *, tamanho: int = 11, depois: int = 8, antes: int = 0, italico: bool = False, centro: bool = False) -> None:
    paragrafo = documento.add_paragraph()
    paragrafo.paragraph_format.space_after = Pt(depois)
    paragrafo.paragraph_format.space_before = Pt(antes)
    paragrafo.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    if centro:
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    trecho = paragrafo.add_run(texto)
    _fonte(trecho, tamanho, italico=italico)
    return paragrafo


def _valor(obra: dict, chave: str) -> str:
    valor = (obra.get(chave) or "").strip()
    return valor if valor else DADO


def _capa(documento: Document, analise: dict) -> None:
    obra = analise["obra"]
    for _ in range(5):
        documento.add_paragraph()
    titulo = documento.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _fonte(titulo.add_run("RELATÓRIO CRONOLÓGICO DE OBRA"), 24, negrito=True, cor=NAVY)
    sub = documento.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _fonte(sub.add_run("Análise de Fluxo Operacional, Prazos e Interferências"), 13, cor=DOURADO)
    _linha_dourada(documento)
    nome = documento.add_paragraph()
    nome.alignment = WD_ALIGN_PARAGRAPH.CENTER
    nome.paragraph_format.space_before = Pt(18)
    _fonte(nome.add_run(f"Obra {_valor(obra, 'numero')} — {_valor(obra, 'cliente')}"), 15, negrito=True)
    partes = [
        "Fornecedor: Armanilux",
        f"Construtora: {_valor(obra, 'construtora')}",
        f"Arquitetura: {_valor(obra, 'arquitetura')}",
    ]
    linhas = [
        "  |  ".join(partes),
        f"Endereço: {_valor(obra, 'endereco')}",
        f"Período coberto: {formatar_data(obra.get('periodo_inicio'))} a {formatar_data(obra.get('periodo_fim'))}",
        "Base documental: histórico do grupo de WhatsApp da obra, documentos anexos e transcrições locais",
        f"Emitido em: {date.today().strftime('%d/%m/%Y')}",
    ]
    if (obra.get("elaborado_por") or "").strip():
        funcao = f" — {obra['funcao']}" if (obra.get("funcao") or "").strip() else ""
        linhas.append(f"Elaborado por: {obra['elaborado_por']}{funcao}")
    for indice, texto in enumerate(linhas):
        paragrafo = documento.add_paragraph()
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragrafo.paragraph_format.space_after = Pt(2)
        _fonte(paragrafo.add_run(texto), 11 if indice < 3 else 10, negrito=indice == 2, cor=CINZA if indice > 2 else GRAFITE, italico=indice > 2)
    documento.add_page_break()


def _linha_dourada(documento: Document) -> None:
    paragrafo = documento.add_paragraph()
    propriedades = paragrafo._p.get_or_add_pPr()
    borda = OxmlElement("w:pBdr")
    inferior = OxmlElement("w:bottom")
    for chave, valor in (("w:val", "single"), ("w:sz", "12"), ("w:space", "1"), ("w:color", DOURADO_HEX)):
        inferior.set(qn(chave), valor)
    borda.append(inferior)
    propriedades.append(borda)


def _primeira(analise: dict, etapa: str) -> str:
    """Primeira data realizada da etapa: programação não conta; vale a data do fato."""
    eventos = analise.get("eventos") or []
    data = primeiros_marcos(eventos).get(etapa)
    if data:
        return formatar_data(data)
    programada = primeira_programacao(eventos, etapa)
    return f"não confirmada (programada em {formatar_data(programada)})" if programada else DADO


def _quadro_resumo(documento: Document, analise: dict) -> None:
    obra = analise["obra"]
    documento.add_heading("Quadro-Resumo da Obra", level=1)
    inicio, fim = obra.get("periodo_inicio"), obra.get("periodo_fim")
    corridos = DADO
    if inicio and fim:
        corridos = f"{(date.fromisoformat(fim) - date.fromisoformat(inicio)).days} dias corridos"
    conclusao = data_da_conclusao(analise.get("eventos") or [])
    linhas = [
        ["Início do grupo / das tratativas", formatar_data(inicio)],
        ["Primeira aprovação de chapas", _primeira(analise, "A")],
        ["Primeira medição in loco", _primeira(analise, "C")],
        ["Primeira aprovação de projeto", _primeira(analise, "G")],
        ["Primeira entrega na obra", _primeira(analise, "H")],
        ["Entrada da equipe de instalação", _primeira(analise, "I")],
        ["Último registro do grupo", formatar_data(fim)],
        ["Duração decorrida (corridos)", corridos],
        ["Duração decorrida (dias úteis)", f"{duracao_da_obra(obra, analise.get('eventos') or []).get('dias_uteis', 0)} dias úteis"],
        ["Conclusão e validação final", formatar_data(conclusao) if conclusao else "DADO NÃO IDENTIFICADO (pendente — ver Etapa L)"],
        [
            "Prazo contratual",
            "informado no grupo (ver Nota Metodológica)" if analise.get("prazos_contratuais") else _valor(obra, "prazo_contratual"),
        ],
    ]
    _tabela_simples(documento, ["Indicador", "Valor"], linhas, [10.4, 7.0])


def _titulo_marco(codigo: str) -> str:
    return TITULOS.get(codigo, codigo).replace("“", "").replace("”", "")


def _tabela_simples(documento: Document, cabecalhos: list[str], linhas: list[list[str]], larguras: list[float], cores: list[str | None] | None = None) -> None:
    tabela = documento.add_table(rows=1 + len(linhas), cols=len(cabecalhos))
    tabela.style = "Table Grid"
    _larguras(tabela, larguras)
    _cabecalho_tabela(tabela, cabecalhos)
    for indice, linha in enumerate(linhas):
        for coluna, texto in enumerate(linha):
            _texto_celula(tabela.rows[indice + 1].cells[coluna], texto, tamanho=10)
        if cores and cores[indice]:
            _sombrear(tabela.rows[indice + 1].cells[-1], cores[indice])
    documento.add_paragraph()


def _eventos_da_etapa(analise: dict, codigo: str) -> list[dict]:
    return [item for item in analise["eventos"] if item["etapa"] == codigo]


SALMAO = "FCE4D6"  # reprocesso ou retrabalho
AMARELO = "FFF2CC"  # tempo ocioso, espera ou pendência
VERMELHO = RGBColor(0xC0, 0x00, 0x00)
_COR_DESTAQUE = {"reprocesso": SALMAO, "ocioso": AMARELO}
_CAUDA_EVENTO = re.compile(r"\s+(?:Mídia:|Documento:|Transcrição:|\(encaminhada no grupo por)")
_FONTE = re.compile(r"\s*\[fonte:[^\]]*\]", re.IGNORECASE)
LIMITE_EVENTO = 260


def _texto_evento(evento: dict) -> str:
    """Uma frase objetiva por linha: sem nome de arquivo, trecho de transcrição nem marca de fonte."""
    texto = _FONTE.sub("", evento.get("ocorrencia") or "")
    corte = _CAUDA_EVENTO.search(texto)
    if corte:
        texto = texto[: corte.start()]
    texto = " ".join(texto.split()).rstrip(" :")
    if len(texto) > LIMITE_EVENTO:
        texto = texto[:LIMITE_EVENTO].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return texto or DADO


def _data_da_linha(evento: dict) -> str:
    """Data da mensagem; programação ganha a marca, se o texto ainda não diz."""
    data = formatar_data(evento["data"])
    if evento.get("programado") and not diz_programado(evento.get("ocorrencia") or ""):
        return f"{data} (programado)"
    return data


def _cor_do_evento(evento: dict) -> str | None:
    destaque = evento.get("destaque") or evento.get("destaque_auto") or ""
    return _COR_DESTAQUE.get(destaque)


def _tabela_linhas(documento: Document, cabecalhos: list[str], linhas: list[list[str]], larguras: list[float], cores: list[str | None]) -> None:
    """Tabela com a linha inteira sombreada quando há destaque, como no relatório aprovado."""
    tabela = documento.add_table(rows=1 + len(linhas), cols=len(cabecalhos))
    tabela.style = "Table Grid"
    _larguras(tabela, larguras)
    _cabecalho_tabela(tabela, cabecalhos)
    for indice, linha in enumerate(linhas):
        for coluna, texto in enumerate(linha):
            celula = tabela.rows[indice + 1].cells[coluna]
            _texto_celula(celula, texto, tamanho=9, negrito=coluna == 0)
            if cores[indice]:
                _sombrear(celula, cores[indice])
    documento.add_paragraph()


def _tabelas_da_etapa_j(documento: Document, analise: dict) -> None:
    """Uma tabela por tipo de interferência (J.1, J.2…), como no relatório aprovado; sem tipo
    marcado, uma tabela só. Depois, o total de dias de equipe sem frente, se a revisão contou."""
    grupos = grupos_da_etapa_j(analise.get("eventos") or []) or [("", [])]
    for numero, (nome, eventos) in enumerate(grupos, start=1):
        if nome:
            documento.add_heading(f"J.{numero} — {nome}", level=2)
        linhas = [[_data_da_linha(item), _texto_evento(item), item.get("impacto") or DADO] for item in eventos]
        cores = [_cor_do_evento(item) for item in eventos] or [None]
        _tabela_linhas(documento, ["Data", "Interferência", "Impacto"], linhas or [["—", DADO, DADO]], [2.6, 8.0, 6.8], cores)
    total = dias_sem_frente(analise.get("eventos") or [])
    if total:
        datas = "1 data" if total["datas"] == 1 else f"{total['datas']} datas"
        _leitura(
            documento,
            "Dias de equipe sem frente registrados no grupo",
            f"{total['dias']}, em {datas}, de {formatar_data(total['inicio'])} a {formatar_data(total['fim'])}.",
        )


def _leitura(documento: Document, rotulo: str, texto: str) -> None:
    paragrafo = documento.add_paragraph()
    paragrafo.paragraph_format.space_after = Pt(8)
    _fonte(paragrafo.add_run(f"{rotulo}: "), 10, negrito=True)
    _fonte(paragrafo.add_run(texto), 10)


def _comentario(analise: dict, codigo: str, chave: str) -> str:
    return ((analise.get("comentarios") or {}).get(codigo) or {}).get(chave, "").strip()


def _periodo_da_etapa(eventos: list[dict]) -> str:
    """Intervalo dentro da etapa (prompt.md: dias úteis "dentro de cada fase relevante")."""
    if not eventos:
        return ""
    datas = sorted(item["data"] for item in eventos)
    if datas[0] == datas[-1]:
        return f"registro único em {formatar_data(datas[0])}"
    dias = dias_uteis_entre(date.fromisoformat(datas[0]), date.fromisoformat(datas[-1]))
    return f"registros de {formatar_data(datas[0])} a {formatar_data(datas[-1])} ({dias} d.u.)"


def _texto_leitura(revisada: str, eventos: list[dict]) -> str:
    periodo = _periodo_da_etapa(eventos)
    if not revisada:
        return f"{periodo}." if periodo else "dado não identificado."
    if not periodo:
        return revisada
    return f"{revisada.rstrip()} {periodo[0].upper()}{periodo[1:]}."


def _escrever_etapa(documento: Document, analise: dict, codigo: str) -> None:
    documento.add_heading(TITULOS[codigo], level=1)
    introducao = _comentario(analise, codigo, "introducao")
    if introducao:
        _paragrafo(documento, introducao, tamanho=10)
    eventos = sorted(_eventos_da_etapa(analise, codigo), key=lambda e: (e["data"], e.get("hora") or ""))
    cores = [_cor_do_evento(item) for item in eventos] or [None]
    if codigo == "J":
        _tabelas_da_etapa_j(documento, analise)
    else:
        linhas = [[_data_da_linha(item), _texto_evento(item)] for item in eventos]
        _tabela_linhas(documento, ["Data", "Evento / Ocorrência"], linhas or [["—", DADO]], [2.6, 14.8], cores)
    if codigo == "L":
        # Refeito dos eventos, como o Quadro-Resumo: remontar sem --recalcular não pode contradizê-lo.
        marcos = marcos_de(analise.get("eventos") or [], analise.get("pendencias") or [])
        if marcos:
            _tabela_simples(documento, ["Marco", "Situação"], [[item["marco"], item["situacao"]] for item in marcos], [12.2, 5.2])
        pendencias = [item for item in analise.get("pendencias") or [] if (item.get("status") or "Pendente") == "Pendente"]
        if pendencias:
            _tabela_simples(documento, ["Pendência em aberto", "Status"], [[item["item"], "Pendente"] for item in pendencias], [13.4, 4.0])
    _leitura(documento, f"Leitura da Etapa {codigo}", _texto_leitura(_comentario(analise, codigo, "leitura"), eventos))


def _nota_metodologica(documento: Document, analise: dict) -> None:
    documento.add_heading("Nota Metodológica", level=1)
    _paragrafo(
        documento,
        "Este relatório foi elaborado a partir do histórico do grupo de WhatsApp da obra, dos documentos anexados "
        "e das transcrições de áudio e vídeo feitas neste computador, sem envio a serviço em nuvem. As datas e "
        "descrições refletem o que foi registrado no grupo; o que não consta é sinalizado como “dado não identificado”.",
        tamanho=10,
    )
    if "lacunas" not in analise:
        limites = "dado não identificado (análise anterior a esta versão)."
    else:
        limites = " ".join(analise["lacunas"]) or "nenhuma limitação registrada."
    _leitura(documento, "Limites do material", limites)
    frentes = frentes_da_obra(analise.get("eventos") or [])
    if len(frentes) > 1:
        _leitura(
            documento,
            "Obra multifrente",
            f"{', '.join(frentes[:-1])} e {frentes[-1]}. Cada frente percorreu o seu próprio ciclo de medição, projeto, "
            "aprovação, entrega e instalação, em paralelo e dependente da liberação pela obra. Os intervalos da Análise "
            "de Prazos são medidos dentro de cada frente.",
        )
    _leitura(documento, "Dias úteis", analise.get("convencao_dias_uteis") or DADO)
    prazos = analise.get("prazos_contratuais") or []
    if prazos:
        fontes = sorted({p.get("fonte", "") for p in prazos if p.get("fonte")})
        _leitura(
            documento,
            "Prazos contratuais de referência",
            "; ".join(p.get("descricao", "") for p in prazos) + "."
            + (f" Fonte: {'; '.join(fontes)}." if fontes else ""),
        )
    _leitura(
        documento,
        "Convenção de cores nas tabelas",
        "salmão = reprocesso ou retrabalho • amarelo = tempo ocioso, espera ou pendência • "
        "na Análise de Prazos, em vermelho o que passou do prazo contratual informado (tabela de confronto) e, "
        f"na tabela de marcos, os intervalos acima de {LIMITE_INTERVALO_LONGO} dias úteis.",
    )


def _confronto(analise: dict) -> list[dict]:
    """Confronto refeito dos eventos e dos prazos, como os marcos."""
    return confronto_contrato(analise.get("eventos") or [], analise.get("prazos_contratuais") or [])


def _confronto_contrato(documento: Document, confronto: list[dict]) -> None:
    """Só aparece quando o grupo informou prazo contratual. Vermelho = passou do prazo."""
    if not confronto:
        return
    tabela = documento.add_table(rows=1 + len(confronto), cols=3)
    tabela.style = "Table Grid"
    _larguras(tabela, [11.0, 3.2, 3.2])
    _cabecalho_tabela(tabela, ["Prazo contratual de referência", "Contrato", "Realizado"])
    for indice, item in enumerate(confronto, start=1):
        linha = tabela.rows[indice]
        sigla = "dias corridos" if item.get("unidade") == "dias_corridos" else "d.u."
        if item.get("programado"):
            realizado = "programado, sem confirmação"
        elif item["realizado"] is not None:
            realizado = f"{item['realizado']} {sigla}"
        else:
            realizado = DADO
        _texto_celula(linha.cells[0], item["descricao"] + (" *" if item.get("fonte_posterior") else ""), tamanho=9)
        _texto_celula(linha.cells[1], f"{item['limite_du']} {sigla}" if item["limite_du"] else DADO, tamanho=9)
        _texto_celula(linha.cells[2], realizado, tamanho=9, negrito=True, cor=VERMELHO if item["excedeu"] else None)
        if item["excedeu"]:
            for celula in linha.cells:
                _sombrear(celula, AMARELO)
    if any(item.get("fonte_posterior") for item in confronto):
        _paragrafo(
            documento,
            "* Fonte escrita no grupo depois do início do período medido: o prazo serve de referência, "
            "mas o grupo não mostra que já valia na época.",
            tamanho=9,
            italico=True,
        )
    documento.add_paragraph()


def _analise_de_prazos(documento: Document, analise: dict, grafico_barras: Path | None, grafico_gantt: Path | None) -> None:
    documento.add_heading("Análise de Prazos — Intervalos em Dias Úteis", level=1)
    marco = "primeiro fato realizado de cada etapa; na aprovação, a que valeu"
    if frentes_da_obra(analise.get("eventos") or []):
        abertura = f"Intervalos entre marcos medidos dentro de cada frente ({marco}), em dias úteis."
    else:
        abertura = f"Intervalos entre marcos ({marco}), em dias úteis."
    _paragrafo(documento, abertura + " Intervalo de calendário não é atraso atribuído a ninguém.", tamanho=10)
    # Sempre dos eventos: remontar sem --recalcular não deixa número antigo ao lado do Quadro-Resumo.
    eventos = analise.get("eventos") or []
    marcos, duracao = intervalos_marcos_de(eventos, analise.get("obra"))
    incompletos = ciclos_incompletos(eventos)
    if not marcos and not incompletos:
        _paragrafo(documento, "Intervalo entre marcos: dado não identificado.")
    else:
        # (rótulo, dias, vermelho, amarelo)
        linhas = [
            (
                _prefixo_frente(item)
                + f"{_titulo_marco(item['de'])} ({formatar_data(item['inicio'])}) → "
                f"{_titulo_marco(item['para'])} ({formatar_data(item['fim'])})",
                f"{item['dias_uteis']} d.u.",
                item["longo"],
                item["longo"],
            )
            for item in marcos
        ]
        # Ciclo que parou ou pulou uma etapa: a data que falta aparece como "dado não identificado".
        for item in incompletos:
            linhas.append(
                (
                    _prefixo_frente(item)
                    + f"{_titulo_marco(item['de'])} ({formatar_data(item['inicio'])}) → {_titulo_marco(item['para'])}: {DADO}",
                    "pendente",
                    False,
                    True,
                )
            )
        if duracao:
            rotulo = "DURAÇÃO TOTAL DA OBRA" if duracao["do_grupo"] else "DURAÇÃO TOTAL REGISTRADA"
            linhas.append(
                (
                    f"{rotulo} ({formatar_data(duracao['inicio'])} → {formatar_data(duracao['fim'])})",
                    f"{duracao['dias_uteis']} d.u.",
                    False,
                    True,
                )
            )
        tabela = documento.add_table(rows=1 + len(linhas), cols=2)
        tabela.style = "Table Grid"
        _larguras(tabela, [14.2, 3.2])
        _cabecalho_tabela(tabela, ["Intervalo entre marcos", "Dias úteis"])
        for indice, (rotulo, dias, vermelho, amarelo) in enumerate(linhas, start=1):
            linha = tabela.rows[indice]
            _texto_celula(linha.cells[0], rotulo, tamanho=9)
            _texto_celula(linha.cells[1], dias, tamanho=9, negrito=True, cor=VERMELHO if vermelho else None)
            if amarelo:
                for celula in linha.cells:
                    _sombrear(celula, AMARELO)
        documento.add_paragraph()
    _aprovacoes_revistas(documento, eventos)
    _confronto_contrato(documento, _confronto(analise))
    _inserir_figura(documento, grafico_barras, "Figura 1. Dias úteis entre marcos.")
    _inserir_figura(documento, grafico_gantt, "Figura 2. Linha do tempo das etapas, do primeiro ao último registro.")


def _aprovacoes_revistas(documento: Document, eventos: list[dict]) -> None:
    """Aprovação seguida de revisão e de nova aprovação: diz qual foi revista e qual valeu."""
    partes = []
    for item in aprovacoes_revistas(eventos):
        datas = [formatar_data(data) for data in item["revistas"]]
        lista = datas[0] if len(datas) == 1 else f"{', '.join(datas[:-1])} e {datas[-1]}"
        onde = f"{item['frente']}: " if item["frente"] else ""
        partes.append(f"{onde}{lista} (valeu a de {formatar_data(item['valeu'])})")
    if partes:
        _leitura(documento, "Aprovações revistas", "; ".join(partes) + ".")


def _itens(valor) -> list[str]:
    """Texto da revisão vira lista: aceita lista, ou texto com uma linha por item."""
    if isinstance(valor, list):
        return [str(item).strip() for item in valor if str(item).strip()]
    linhas = [linha.strip().lstrip("-•").strip() for linha in str(valor or "").splitlines()]
    return [linha for linha in linhas if linha]


def _marcadores(documento: Document, itens: list[str]) -> None:
    for item in itens or [f"{DADO} (preencher na revisão)."]:
        _paragrafo(documento, f"• {item}", tamanho=10, depois=3)


def _diagnostico(documento: Document, analise: dict) -> None:
    documento.add_heading("Análise Técnica — Diagnóstico", level=1)
    diagnostico = analise.get("diagnostico_prompt") or {}
    blocos = (
        ("1. Reprocessos identificados", diagnostico.get("reprocessos")),
        ("2. Tempos ociosos (intervalos sem avanço)", diagnostico.get("tempos_ociosos")),
        ("3. Atrasos operacionais internos", diagnostico.get("atrasos_internos")),
        ("4. Dependências externas", diagnostico.get("dependencias_externas")),
        (
            "5. Interferências de obra (Etapa J): impacto no cronograma e na produtividade",
            diagnostico.get("interferencias") or analise.get("produtividade_personalizada"),
        ),
    )
    for titulo, valor in blocos:
        documento.add_heading(titulo, level=2)
        _marcadores(documento, _itens(valor))


def _numerados(documento: Document, itens: list[str]) -> None:
    if not itens:
        _paragrafo(documento, f"{DADO} (preencher na revisão).", tamanho=10)
    for indice, item in enumerate(itens, start=1):
        _paragrafo(documento, f"{indice}. {item}", tamanho=10, depois=3)


def _prefixo_frente(item: dict) -> str:
    return f"{item['frente']} — " if item.get("frente") else ""


def _impacto_padrao(analise: dict) -> str:
    duracao = duracao_da_obra(analise.get("obra"), analise.get("eventos") or [])
    if not duracao:
        return DADO + "."
    corridos = (date.fromisoformat(duracao["fim"]) - date.fromisoformat(duracao["inicio"])).days
    origem = "Do início do grupo ao último registro" if duracao["do_grupo"] else "Do primeiro ao último registro classificado"
    texto = f"{origem}: {duracao['dias_uteis']} dias úteis ({corridos} dias corridos). "
    medidos = [item for item in _confronto(analise) if item["realizado"] is not None and item["limite_du"]]
    if not analise.get("prazos_contratuais"):
        return texto + "Prazo contratual não declarado no grupo: dado não identificado."
    excedidos = sum(1 for item in medidos if item["excedeu"])
    verbo = "passou" if excedidos == 1 else "passaram"
    return texto + (
        f"{excedidos} de {len(medidos)} prazos contratuais com as duas datas {verbo} do limite (ver Análise de Prazos)."
    )


def _conclusao_estrategica(documento: Document, analise: dict) -> None:
    documento.add_heading("Conclusão Estratégica", level=1)
    documento.add_heading("Diagnóstico da eficiência do fluxo operacional", level=2)
    _paragrafo(documento, (analise.get("conclusao_personalizada") or "").strip() or f"{DADO} (preencher na revisão).", tamanho=10)
    documento.add_heading("Principais pontos críticos de atraso", level=2)
    pontos = _itens(analise.get("pontos_criticos")) or [
        f"{item['titulo']}: {item['texto']}" for item in analise.get("gargalos_personalizados") or []
    ]
    _numerados(documento, pontos)
    documento.add_heading("Impactos no prazo final", level=2)
    _paragrafo(documento, (analise.get("impactos_prazo") or "").strip() or _impacto_padrao(analise), tamanho=10)
    documento.add_heading("Recomendações práticas", level=2)
    _numerados(documento, _itens(analise.get("recomendacoes_personalizadas")))
    fim = documento.add_paragraph()
    fim.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _fonte(fim.add_run("— Fim do relatório —"), 10, italico=True, cor=CINZA)


def _inserir_figura(documento: Document, caminho: Path | None, legenda: str) -> None:
    if caminho and Path(caminho).exists():
        documento.add_picture(str(caminho), width=Cm(LARGURA_FIGURA_CM))
        documento.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        _paragrafo(documento, "Figura: dado não identificado.")
    _paragrafo(documento, legenda, tamanho=9, italico=True)


def proxima_versao(pasta: Path, numero: str, rascunho: bool = False, copia: int = 1, versao: int | None = None) -> Path:
    """Próximo vN revisado. O rascunho leva o número da versão que ele vai virar
    (`-vN-rascunho.docx`) e é regravado a cada remontagem, sem gastar versão.
    `versao` já fixada (analise.json) é usada como está: a final vN é regravada.
    `copia` > 1 é para quando o rascunho está aberto no Word e não dá para regravar."""
    import re

    slug = re.sub(r"[^0-9A-Za-z.-]+", "", numero) or "sem-numero"
    if versao is None:
        versao = 1
        while (pasta / f"Relatorio-Cronologico-Obra-{slug}-v{versao}.docx").exists():
            versao += 1
    if not rascunho:
        return pasta / f"Relatorio-Cronologico-Obra-{slug}-v{versao}.docx"
    sufixo = "" if copia == 1 else f"-{copia}"
    return pasta / f"Relatorio-Cronologico-Obra-{slug}-v{versao}-rascunho{sufixo}.docx"


def montar_docx(analise: dict, destino: Path, grafico_barras: Path | None, grafico_gantt: Path | None) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    obra = analise["obra"]
    documento = Document()
    _configurar_documento(documento)
    documento.core_properties.title = f"Relatório Cronológico de Obra {obra.get('numero') or ''}".strip()
    documento.core_properties.author = "Armanilux"
    documento.core_properties.category = "Relatório de obra"
    documento.core_properties.language = "pt-BR"
    documento.core_properties.comments = "Gerado localmente. Histórico não enviado a serviço de transcrição em nuvem."

    if not analise.get("revisado"):
        aviso = documento.add_paragraph()
        trecho = aviso.add_run(
            "RASCUNHO NÃO REVISADO. Leitura automática da conversa, sem conferência de quem "
            "analisou o grupo. Não enviar a ninguém antes da revisão."
        )
        _fonte(trecho, 11, negrito=True, cor=RGBColor(0xC6, 0x28, 0x28))
    _capa(documento, analise)

    _nota_metodologica(documento, analise)
    _quadro_resumo(documento, analise)
    for codigo in ORDEM:
        _escrever_etapa(documento, analise, codigo)
    _analise_de_prazos(documento, analise, grafico_barras, grafico_gantt)
    _diagnostico(documento, analise)
    _conclusao_estrategica(documento, analise)

    documento.save(destino)
    return destino
