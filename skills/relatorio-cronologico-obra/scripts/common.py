"""Funções compartilhadas pelos scripts da skill. Tudo local, sem rede."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

DADO = "dado não identificado"

SUBPASTAS = (
    "01-conversas",
    "02-projetos-pdf",
    "03-midias",
    "04-transcricoes",
    "05-relatorios",
)

# Largura das figuras no Word; os gráficos são desenhados nela para a letra não encolher.
LARGURA_FIGURA_CM = 16.2
EXT_DOCUMENTO = {".pdf", ".docx", ".doc", ".odt", ".xlsx", ".xls"}
EXT_AUDIO = {".opus", ".ogg", ".mp3", ".m4a", ".wav", ".aac"}
EXT_VIDEO = {".mp4", ".mov", ".3gp", ".avi", ".mkv"}
EXT_IMAGEM = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".gif", ".bmp"}
EXT_MIDIA = EXT_AUDIO | EXT_VIDEO | EXT_IMAGEM

CONVENCAO_DIAS_UTEIS = (
    "Os dias úteis são contados a partir do dia seguinte à data inicial, "
    "até a data final inclusive. Excluem-se sábados, domingos, feriados "
    "nacionais brasileiros, a segunda-feira e a terça-feira de Carnaval, "
    "o feriado estadual de São Paulo de 9 de julho e os feriados municipais "
    "de São Paulo de 25 de janeiro e de Corpus Christi. O cálculo é feito "
    "no próprio computador, com a biblioteca holidays, sem consulta a "
    "serviço externo. Quarta-feira de Cinzas não entra nessa exclusão. "
    "Intervalo em dias úteis não é soma de atraso e não é, por si só, "
    "falha da Armanilux."
)


def localizar_ferramenta(nome: str) -> str | None:
    """Acha um programa no PATH ou na pasta do winget do usuário.

    O winget grava o FFmpeg num diretório que só entra no PATH depois de reler
    o registro. Se o arquivo existir, a pasta dele passa a valer neste processo.
    """
    import os
    import shutil

    achado = shutil.which(nome)
    if achado:
        return achado
    local = os.environ.get("LOCALAPPDATA", "")
    if not local:
        return None
    base = Path(local) / "Microsoft" / "WinGet"
    candidatos = [base / "Links" / f"{nome}.exe"]
    pacotes = base / "Packages"
    if pacotes.is_dir():
        candidatos.extend(pacotes.glob(f"**/bin/{nome}.exe"))
    for candidato in candidatos:
        if candidato.is_file():
            os.environ["PATH"] = str(candidato.parent) + os.pathsep + os.environ.get("PATH", "")
            return str(candidato)
    return None


def configurar_saida() -> None:
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def pasta_padrao() -> Path:
    import os

    bruto = os.environ.get("ARMANILUX_OBRAS", "").strip()
    if bruto:
        return Path(bruto).expanduser()
    from config_io import pasta_documentos

    return pasta_documentos() / "Armanilux" / "Relatorios-de-Obra"


def _marcadores(texto: str) -> int:
    return texto.count("Ã") + texto.count("Â") + texto.count("├") + texto.count("�")


def corrigir_mojibake(texto: str) -> str:
    """Repara nomes em que UTF-8 foi lido como Latin-1, CP1252 ou CP437.

    Repete no máximo três vezes para cobrir o caso duplo (Ãƒ).
    Só aceita a troca quando os marcadores de mojibake diminuem, para não
    estragar texto que já está certo.
    """
    atual = texto
    for _ in range(3):
        melhor = None
        melhor_nota = _marcadores(atual)
        for codificacao in ("latin-1", "cp1252", "cp437"):
            try:
                candidato = atual.encode(codificacao).decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            nota = _marcadores(candidato)
            if candidato != atual and nota < melhor_nota:
                melhor = candidato
                melhor_nota = nota
        if melhor is None:
            break
        atual = melhor
    return atual


def sem_acento(texto: str) -> str:
    decomposicao = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposicao if not unicodedata.combining(c))


def normalizar(texto: str) -> str:
    limpo = sem_acento(texto).lower()
    limpo = limpo.replace("\u200e", "").replace("\u200f", "")
    limpo = re.sub(r"\s+", " ", limpo)
    return limpo.strip()


def sanitizar_pasta(nome: str) -> str:
    limpo = re.sub(r'[<>:"/\\|?*]', " ", nome)
    limpo = re.sub(r"\s+", " ", limpo).strip(" .")
    return limpo[:80] or "obra-sem-nome"


def nome_seguro(nome: str) -> str:
    nome = corrigir_mojibake(nome.replace("\\", "/").split("/")[-1])
    nome = re.sub(r'[<>:"/\\|?*]', "_", nome).strip().strip(".")
    return nome or "arquivo-sem-nome"


def decodificar_bytes(dados: bytes) -> str:
    if dados.startswith(b"\xff\xfe") or dados.startswith(b"\xfe\xff"):
        return dados.decode("utf-16")
    if dados.startswith(b"\xef\xbb\xbf"):
        return dados.decode("utf-8-sig")
    for codificacao in ("utf-8", "cp1252", "latin-1"):
        try:
            texto = dados.decode(codificacao)
        except UnicodeDecodeError:
            continue
        if "Ã" in texto or "├" in texto:
            return corrigir_mojibake(texto)
        return texto
    return dados.decode("utf-8", errors="replace")


def como_data(valor: date | datetime | str) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return date.fromisoformat(str(valor)[:10])


def formatar_data(valor: date | datetime | str | None) -> str:
    if valor in (None, ""):
        return DADO
    try:
        dia = como_data(valor)
    except ValueError:
        return DADO
    return dia.strftime("%d/%m/%Y")


def escrever_json(caminho: Path, conteudo: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def ler_json(caminho: Path) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def tipo_midia(nome: str) -> str:
    ext = Path(nome).suffix.lower()
    if ext in EXT_IMAGEM:
        return "foto"
    if ext in EXT_AUDIO:
        return "áudio"
    if ext in EXT_VIDEO:
        return "vídeo"
    if ext in EXT_DOCUMENTO:
        return "documento"
    return "arquivo"
