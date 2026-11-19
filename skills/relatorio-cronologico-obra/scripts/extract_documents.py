"""Extrai texto de PDF e de Word. A leitura é local."""

from __future__ import annotations

from pathlib import Path


import logging

# PDF de desenho técnico gera centenas de avisos inofensivos; não mostrar para a pessoa.
for _nome in ("pypdf", "pdfminer", "pdfplumber"):
    logging.getLogger(_nome).setLevel(logging.CRITICAL)

PAGINAS_MAX = 15
PDFPLUMBER_ATE = 300 * 1024


def _texto_pdf(caminho: Path) -> str:
    """Texto do PDF. O pypdf é rápido; o pdfplumber trava em desenho técnico pesado,
    então só entra para arquivo pequeno, quando o pypdf não achou texto."""
    try:
        from pypdf import PdfReader

        leitor = PdfReader(str(caminho))
        paginas = leitor.pages[:PAGINAS_MAX]
        texto = "\n".join((pagina.extract_text() or "") for pagina in paginas).strip()
        if texto:
            return texto
    except Exception:
        pass
    if caminho.stat().st_size > PDFPLUMBER_ATE:
        return ""
    try:
        import pdfplumber

        with pdfplumber.open(caminho) as pdf:
            return "\n".join((pagina.extract_text() or "") for pagina in pdf.pages[:PAGINAS_MAX]).strip()
    except Exception:
        return ""


def _texto_docx(caminho: Path) -> str:
    from docx import Document

    documento = Document(str(caminho))
    partes = [paragrafo.text for paragrafo in documento.paragraphs if paragrafo.text.strip()]
    for tabela in documento.tables:
        for linha in tabela.rows:
            celulas = [celula.text.strip() for celula in linha.cells if celula.text.strip()]
            if celulas:
                partes.append(" | ".join(celulas))
    return "\n".join(partes).strip()


def extrair_documento(caminho: Path) -> dict:
    caminho = Path(caminho)
    registro = {"arquivo": caminho.name, "caminho": str(caminho), "texto": "", "erro": ""}
    try:
        extensao = caminho.suffix.lower()
        if extensao == ".pdf":
            registro["texto"] = _texto_pdf(caminho)
        elif extensao == ".docx":
            registro["texto"] = _texto_docx(caminho)
        else:
            registro["erro"] = "formato sem extração de texto nesta versão"
        if extensao in {".pdf", ".docx"} and not registro["texto"]:
            registro["erro"] = registro["erro"] or "nenhum texto identificado no arquivo"
    except Exception as erro:
        registro["erro"] = str(erro)
    return registro


def extrair_pasta(pasta: Path) -> list[dict]:
    if not pasta.exists():
        return []
    saida = []
    for caminho in sorted(pasta.iterdir()):
        if caminho.is_file() and caminho.suffix.lower() in {".pdf", ".docx", ".doc", ".odt"}:
            saida.append(extrair_documento(caminho))
    return saida
