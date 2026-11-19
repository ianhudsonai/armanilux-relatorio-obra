"""Como o relatório chega à pessoa: Word, PDF ou link.

- word: só o `.docx`.
- pdf: o `.docx` e um PDF feito dele, pelo Microsoft Word (se instalado) ou pelo LibreOffice.
- link: como pdf, e a versão revisada é copiada para uma pasta do OneDrive ou do
  Google Drive (`pasta_link`). De lá a pessoa cria o link no próprio aplicativo,
  só para quem pode ver. Rascunho nunca vai para a nuvem.

Nada é enviado para a internet por estes scripts: quem sincroniza é o aplicativo da nuvem.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

FORMATOS = ("word", "pdf", "link")

_SCRIPT_WORD = (
    "$ErrorActionPreference = 'Stop'; "
    "$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
    "try { $d = $w.Documents.Open($env:ARMANILUX_DOCX, $false, $true); "
    "$d.ExportAsFixedFormat($env:ARMANILUX_PDF, 17); $d.Close($false) } "
    "finally { $w.Quit() }"
)


def formato_entrega(config: dict | None) -> str:
    """Formato pedido no preparo. Config antigo com `gerar_pdf` vira pdf."""
    config = config or {}
    formato = str(config.get("formato_entrega") or "").strip().lower()
    if formato in FORMATOS:
        return formato
    return "pdf" if config.get("gerar_pdf") else "word"


def _pdf_pelo_word(docx: Path) -> Path | None:
    if os.name != "nt":
        return None
    pdf = docx.with_suffix(".pdf")
    ambiente = dict(os.environ, ARMANILUX_DOCX=str(docx), ARMANILUX_PDF=str(pdf))
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", _SCRIPT_WORD],
            env=ambiente,
            capture_output=True,
            timeout=180,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    return pdf if pdf.exists() else None


def localizar_libreoffice() -> str | None:
    """O winget instala o LibreOffice fora do PATH; procura também nas pastas de programas."""
    for nome in ("soffice", "libreoffice"):
        achado = shutil.which(nome)
        if achado:
            return achado
    for variavel in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(variavel)
        if base:
            candidato = Path(base) / "LibreOffice" / "program" / "soffice.exe"
            if candidato.is_file():
                return str(candidato)
    return None


def _pdf_pelo_libreoffice(docx: Path) -> Path | None:
    soffice = localizar_libreoffice()
    if not soffice:
        return None
    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx)],
            capture_output=True,
            timeout=180,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    pdf = docx.with_suffix(".pdf")
    return pdf if pdf.exists() else None


def converter_pdf(docx: Path, conversores=None) -> Path | None:
    """PDF ao lado do `.docx`: tenta o Word e depois o LibreOffice. None se nenhum funcionar."""
    for conversor in conversores or (_pdf_pelo_word, _pdf_pelo_libreoffice):
        try:
            pdf = conversor(docx)
        except Exception:
            continue
        if pdf and Path(pdf).exists():
            return Path(pdf)
    return None


def copiar_para_link(arquivo: Path, pasta_link: Path, pasta_da_obra: str) -> Path:
    """Copia a versão revisada para `<pasta_link>/<pasta da obra>/` e devolve o caminho da cópia."""
    destino = Path(pasta_link) / pasta_da_obra / arquivo.name
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(arquivo, destino)
    return destino
