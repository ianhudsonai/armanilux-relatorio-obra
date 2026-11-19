"""Monta o Relatório Cronológico de Obra em .docx, no formato da Armanilux."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from analyze import ORDEM
from business_days import cor_leitura
from common import DADO, EXT_IMAGEM, formatar_data
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

NAVY = RGBColor(0x1F, 0x3A, 0x5F)
GRAFITE = RGBColor(0x22, 0x22, 0x22)
CINZA = RGBColor(0x5C, 0x6B, 0x73)
BRANCO = RGBColor(0xFF, 0xFF, 0xFF)
LARGURA = 17.4
_PREENCHIMENTO = {
    "Fluxo contínuo": "CDE9D6",
    "Atenção": "FFE8A3",
    "Intervalo longo": "F6C9C6",
}


def _rgb(hexadecimal: str) -> RGBColor:
    hexadecimal = hexadecimal.lstrip("#")
    return RGBColor(int(hexadecimal[0:2], 16), int(hexadecimal[2:4], 16), int(hexadecimal[4:6], 16))


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
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER if centro else WD_ALIGN_PARAGRAPH.LEFT
    paragrafo.paragraph_format.space_after = Pt(0)
    paragrafo.paragraph_format.space_before = Pt(0)
    trecho = paragrafo.add_run(texto)
    _fonte(trecho, tamanho, negrito=negrito, cor=cor)


def _cabecalho_tabela(tabela, titulos: list[str]) -> None:
    for indice, titulo in enumerate(titulos):
        _texto_celula(tabela.rows[0].cells[indice], titulo, negrito=True, tamanho=10, cor=BRANCO, centro=True)
        _sombrear(tabela.rows[0].cells[indice], "1F3A5F")
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
    trecho = cabecalho.add_run("Armanilux  ·  Relatório cronológico de obra  ·  uso interno")
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


def _rotulo(documento: Document, rotulo: str, texto: str) -> None:
    paragrafo = documento.add_paragraph()
    paragrafo.paragraph_format.space_after = Pt(4)
    paragrafo.paragraph_format.space_before = Pt(2)
    chamada = paragrafo.add_run(f"{rotulo}: ")
    _fonte(chamada, 11, negrito=True, cor=NAVY)
    corpo = paragrafo.add_run(texto)
    _fonte(corpo, 11)


def _valor(obra: dict, chave: str) -> str:
    valor = (obra.get(chave) or "").strip()
    return valor if valor else DADO


def _observacao(analise: dict, arquivo: str) -> str:
    for item in analise.get("observacoes_visuais") or []:
        nome = item.get("arquivo") or ""
        if nome == arquivo or Path(nome).name == Path(arquivo).name:
            texto = (item.get("observacao") or "").strip()
            if texto:
                return texto
    pasta = "02-projetos-pdf" if Path(arquivo).suffix.lower() in {".pdf", ".docx", ".doc", ".odt"} else "03-midias"
    return f"dado não identificado (conferir o arquivo na pasta {pasta})."


def _campo_etapa(analise: dict, codigo: str, chave: str, padrao: str) -> str:
    bloco = (analise.get("comentarios") or {}).get(codigo) or {}
    texto = (bloco.get(chave) or "").strip()
    return texto or padrao


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


def _kpis(documento: Document, analise: dict) -> None:
    kpis = analise["kpis"]
    cartoes = [
        (str(kpis["dias_uteis_periodo"]), "Dias úteis no período"),
        (str(kpis["revisoes"]), "Revisões de projeto"),
        (str(kpis["interferencias"]), "Interferências registradas"),
        (str(kpis["maior_intervalo"]), "Maior intervalo sem registro (dias úteis)"),
    ]
    tabela = documento.add_table(rows=1, cols=4)
    tabela.style = "Table Grid"
    _larguras(tabela, [LARGURA / 4] * 4)
    for indice, (numero, legenda) in enumerate(cartoes):
        celula = tabela.rows[0].cells[indice]
        celula.text = ""
        _sombrear(celula, "F7F5F2")
        celula.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        primeiro = celula.paragraphs[0]
        primeiro.alignment = WD_ALIGN_PARAGRAPH.CENTER
        primeiro.paragraph_format.space_after = Pt(0)
        trecho = primeiro.add_run(numero)
        _fonte(trecho, 26, negrito=True, cor=NAVY)
        segundo = celula.add_paragraph()
        segundo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        chamada = segundo.add_run(legenda)
        _fonte(chamada, 9, cor=CINZA)
    documento.add_paragraph()


def _eventos_da_etapa(analise: dict, codigo: str) -> list[dict]:
    return [item for item in analise["eventos"] if item["etapa"] == codigo]


def _escrever_etapa(documento: Document, analise: dict, codigo: str) -> None:
    etapa = analise["etapas"][codigo]
    documento.add_heading(etapa["titulo"], level=2)
    eventos = _eventos_da_etapa(analise, codigo)
    if codigo == "J":
        if eventos:
            linhas = [
                [f"{formatar_data(item['data'])} {item['hora']}", item["ocorrencia"], item.get("impacto") or DADO]
                for item in eventos
            ]
        else:
            linhas = [["—", DADO, DADO]]
        _tabela_simples(
            documento,
            ["Data", "Interferência", "Impacto"],
            linhas,
            [3.2, 7.1, 7.1],
        )
        documento.add_heading("J.1 Pendências por item", level=3)
        pendencias = analise.get("pendencias") or []
        if pendencias:
            _tabela_simples(
                documento,
                ["Item", "Status"],
                [[item["item"], item.get("status") or "Pendente"] for item in pendencias],
                [13.4, 4.0],
            )
        else:
            _paragrafo(documento, "Pendência residual: dado não identificado.")
        documento.add_heading("J.2 Impacto na produtividade", level=3)
        _paragrafo(documento, analise.get("produtividade") or DADO)
    else:
        if eventos:
            linhas = [[f"{formatar_data(item['data'])} {item['hora']}", item["ocorrencia"]] for item in eventos]
        else:
            linhas = [["—", DADO]]
        _tabela_simples(documento, ["Data", "Ocorrência"], linhas, [3.6, 13.8])
    if codigo == "L":
        marcos = analise.get("marcos") or []
        if marcos:
            _tabela_simples(
                documento,
                ["Marco", "Situação"],
                [[item["marco"], item["situacao"]] for item in marcos],
                [12.2, 5.2],
            )
        else:
            _paragrafo(documento, "Marco: dado não identificado.")

    _rotulo(documento, "Intervalos relevantes", _campo_etapa(analise, codigo, "intervalos_relevantes", etapa["intervalos_relevantes"]))
    _rotulo(documento, "Situação", _campo_etapa(analise, codigo, "situacao", etapa["situacao"]))
    _rotulo(documento, "Ponto crítico", _campo_etapa(analise, codigo, "ponto_critico", etapa["ponto_critico"]))
    _rotulo(documento, "Gargalo", _campo_etapa(analise, codigo, "gargalo", etapa["gargalo"]))
    _rotulo(documento, "Avaliação", _campo_etapa(analise, codigo, "avaliacao", etapa["avaliacao"]))
    _rotulo(documento, "Conclusão da etapa", _campo_etapa(analise, codigo, "conclusao", etapa["conclusao"]))


def _inserir_figura(documento: Document, caminho: Path | None, legenda: str) -> None:
    if caminho and Path(caminho).exists():
        documento.add_picture(str(caminho), width=Cm(16.2))
        documento.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        _paragrafo(documento, "Figura: dado não identificado.")
    _paragrafo(documento, legenda, tamanho=9, italico=True)


def _anexar_imagens(documento: Document, analise: dict) -> None:
    inseridas = 0
    for item in analise.get("anexo") or []:
        if inseridas >= 12:
            break
        caminho = Path(item.get("caminho") or "")
        if item["tipo"] not in {"foto", "quadro de vídeo"}:
            continue
        if caminho.suffix.lower() not in EXT_IMAGEM or not caminho.exists():
            continue
        try:
            documento.add_picture(str(caminho), width=Cm(12.5))
        except Exception:
            continue
        documento.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        _paragrafo(documento, f"Mídia: {item['arquivo']}", tamanho=9, italico=True)
        inseridas += 1
    if inseridas == 0:
        _paragrafo(documento, "Imagem incorporada: dado não identificado. Os nomes seguem na tabela do anexo.")


def proxima_versao(pasta: Path, numero: str) -> Path:
    import re

    slug = re.sub(r"[^0-9A-Za-z.-]+", "", numero) or "sem-numero"
    versao = 1
    while True:
        candidato = pasta / f"Relatorio-Cronologico-Obra-{slug}-v{versao}.docx"
        if not candidato.exists():
            return candidato
        versao += 1


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
    titulo = documento.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    trecho = titulo.add_run("RELATÓRIO CRONOLÓGICO DE OBRA")
    _fonte(trecho, 20, negrito=True, cor=NAVY)
    subtitulo = documento.add_paragraph()
    trecho = subtitulo.add_run("Armanilux")
    _fonte(trecho, 12, cor=RGBColor(0x8C, 0x73, 0x4B))
    _paragrafo(
        documento,
        f"Obra {_valor(obra, 'numero')}  ·  {_valor(obra, 'cliente')}",
        tamanho=12,
    )

    identificacao = [
        ["Obra", _valor(obra, "numero")],
        ["Cliente", _valor(obra, "cliente")],
        ["Construtora", _valor(obra, "construtora")],
        ["Engenheiro", _valor(obra, "engenheiro")],
        ["Arquitetura", _valor(obra, "arquitetura")],
        ["Responsável Armanilux", _valor(obra, "responsavel_armanilux")],
        *(
            [["Elaborado por", obra["elaborado_por"]]]
            if (obra.get("elaborado_por") or "").strip()
            else []
        ),
        *(
            [["Função", obra["funcao"]]]
            if (obra.get("funcao") or "").strip()
            else []
        ),
        ["Endereço", _valor(obra, "endereco")],
        ["Período", f"{formatar_data(obra.get('periodo_inicio'))} a {formatar_data(obra.get('periodo_fim'))}"],
        ["Fonte", _valor(obra, "fonte")],
        ["Prazo contratual", _valor(obra, "prazo_contratual")],
    ]
    _tabela_simples(documento, ["Campo", "Informação"], identificacao, [5.2, 12.2])

    documento.add_heading("1. Objetivo e critérios", level=1)
    _paragrafo(
        documento,
        "Este relatório organiza o histórico da obra na ordem das etapas A, B, C, D, E, F, G, H, I, J e L. "
        "Três categorias classificam cada constatação. Atividade realizada: o histórico mostra o fato, com data. "
        "Pendência identificada: o histórico mostra um item ainda aberto; o status usado é Pendente. "
        "Dado não identificado: o histórico não traz a informação, e o relatório não a completa por suposição.",
    )
    _paragrafo(documento, analise.get("convencao_dias_uteis") or "")
    _paragrafo(
        documento,
        "Leitura do intervalo: até 2 dias úteis, fluxo contínuo; de 3 a 5, atenção; 6 ou mais, intervalo longo. "
        "A cor usada na tabela e no gráfico segue essa leitura. Intervalos não são somados para fabricar um atraso total.",
    )

    documento.add_heading("2. Resumo executivo", level=1)
    _paragrafo(
        documento,
        "Os quatro indicadores abaixo saem das datas do grupo e da regra de dias úteis. "
        "O quarto cartão é o maior intervalo sem registro, não um atraso atribuído.",
    )
    _kpis(documento, analise)

    documento.add_heading("3. Etapas do processo", level=1)
    _paragrafo(
        documento,
        "Cada etapa lista somente o que o histórico sustenta. A ordem dentro da etapa é cronológica.",
    )
    for codigo in ORDEM:
        _escrever_etapa(documento, analise, codigo)

    documento.add_heading("4. Dias úteis entre marcos", level=1)
    _paragrafo(
        documento,
        "A tabela destaca, em cor, o intervalo entre datas em que houve registro classificado. "
        "Verde é fluxo contínuo, amarelo é atenção, vermelho é intervalo longo.",
    )
    intervalos = analise.get("intervalos") or []
    if intervalos:
        linhas = [
            [
                formatar_data(item["inicio"]),
                formatar_data(item["fim"]),
                item["rotulo"],
                str(item["dias_uteis"]),
                item["leitura"],
            ]
            for item in intervalos
        ]
        cores = [_PREENCHIMENTO.get(item["leitura"], "F4F6F8") for item in intervalos]
        _tabela_simples(
            documento,
            ["De", "Até", "Marcos", "Dias úteis", "Leitura"],
            linhas,
            [2.6, 2.6, 5.4, 2.6, 4.2],
            cores,
        )
    else:
        _paragrafo(documento, "Intervalo entre marcos: dado não identificado.")
    _inserir_figura(
        documento,
        grafico_barras,
        "Figura 1. Dias úteis entre registros. A cor é a leitura do intervalo, não um veredito de culpa.",
    )
    _inserir_figura(
        documento,
        grafico_gantt,
        "Figura 2. Linha do tempo das etapas. A borda vermelha marca etapa precedida por intervalo longo.",
    )

    documento.add_heading("5. Diagnóstico", level=1)
    diagnostico = analise.get("diagnostico_prompt") or {}
    for chave, rotulo in (
        ("reprocessos", "Reprocessos"),
        ("tempos_ociosos", "Tempos ociosos"),
        ("atrasos_internos", "Atrasos operacionais internos"),
        ("dependencias_externas", "Dependências externas"),
    ):
        if diagnostico:
            _rotulo(documento, rotulo, (diagnostico.get(chave) or "").strip() or DADO + ".")
    gargalos = analise.get("gargalos") or []
    if not gargalos:
        _paragrafo(documento, "Gargalo: dado não identificado.")
    for item in gargalos:
        _paragrafo(documento, f"{item['numero']}. {item['titulo']}. {item['texto']}")
    _paragrafo(documento, "Leitura de responsabilidades. A coluna Natureza nomeia o tipo de fato; o diagnóstico fica no que o grupo registrou.")
    responsabilidades = analise.get("responsabilidades") or []
    _tabela_simples(
        documento,
        ["Natureza", "Diagnóstico"],
        [[item["natureza"], item["diagnostico"]] for item in responsabilidades] or [[DADO, DADO]],
        [5.2, 12.2],
    )

    documento.add_heading("6. Recomendações", level=1)
    recomendacoes = analise.get("recomendacoes_personalizadas") or analise.get("recomendacoes") or []
    if not recomendacoes:
        _paragrafo(documento, "dado não identificado.")
    for indice, texto in enumerate(recomendacoes, start=1):
        _paragrafo(documento, f"{indice}. {texto}")

    documento.add_heading("7. Conclusão", level=1)
    conclusao = (analise.get("conclusao_personalizada") or "").strip() or analise.get("conclusao") or DADO
    _paragrafo(documento, conclusao)

    documento.add_heading("Anexo de mídias", level=1)
    _paragrafo(
        documento,
        "Cada arquivo ligado a um registro, e cada quadro extraído de vídeo, aparece abaixo. "
        "A observação visual fica como dado não identificado até que seja conferida na imagem.",
    )
    anexo = analise.get("anexo") or []
    if anexo:
        _tabela_simples(
            documento,
            ["Arquivo", "Tipo", "Data", "Etapa", "Observação"],
            [
                [
                    item["arquivo"],
                    item["tipo"],
                    formatar_data(item["data"]) if item.get("data") else DADO,
                    item.get("etapa") or DADO,
                    _observacao(analise, item["arquivo"]),
                ]
                for item in anexo
            ],
            [4.6, 2.4, 2.6, 1.6, 6.2],
        )
    else:
        _paragrafo(documento, "Anexo: dado não identificado.")
    _anexar_imagens(documento, analise)

    documento.add_heading("Nota de rastreabilidade", level=1)
    _paragrafo(documento, analise.get("rastreabilidade") or DADO)

    documento.save(destino)
    return destino


def tentar_pdf(docx: Path) -> Path | None:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None
    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx)],
            capture_output=True,
            timeout=120,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    pdf = docx.with_suffix(".pdf")
    return pdf if pdf.exists() else None
