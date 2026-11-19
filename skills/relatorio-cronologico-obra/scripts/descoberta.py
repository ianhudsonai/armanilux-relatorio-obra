"""Acha exportações do WhatsApp sem usar o glob do shell.

Varre com pathlib (nome com acento, NFC e NFD, parênteses, mojibake) e
confere o conteúdo, não só o nome. Só lê arquivos neste computador.
"""

from __future__ import annotations

import os
import re
import unicodedata
import zipfile
from pathlib import Path

from common import corrigir_mojibake, decodificar_bytes, nome_seguro, normalizar
from parse_whatsapp import analisar_conversa, parece_conversa

PROFUNDIDADE = 4
LIMITE_TXT = 30 * 1024 * 1024
IGNORAR_DIR = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "03-midias",
    "quadros",
    "05-relatorios",
    "01-conversas",  # já arquivado na obra; o _chat.txt extraído não é conversa nova
    "appdata",
}
_PREFIXO = re.compile(
    r"^(?:conversa do whatsapp com|conversa do whatsapp|whatsapp chat(?: with| -)?)\s*[-–:]?\s*",
    re.IGNORECASE,
)
_PAREN = re.compile(r"\(([^)]*)\)")
# 8977, 8977.1 ou 8977.1.v10. A parte ".vN" é versão do grupo, não da obra.
_NUMERO = re.compile(r"\b(\d{3,}(?:\.\d+)*)(?:\.v\d+)?\b", re.IGNORECASE)
# "apto 302 - Obra 8977": o número depois de "Obra" é o da obra.
_NUMERO_DA_OBRA = re.compile(r"\bobra\s*(\d{3,}(?:\.\d+)*(?:\.v\d+)?)\b", re.IGNORECASE)


def normalizar_nome(nome: str) -> str:
    texto = unicodedata.normalize("NFC", corrigir_mojibake(nome))
    return normalizar(texto)


def nome_parece_exportacao(nome: str) -> bool:
    base = normalizar_nome(Path(nome).name)
    return "conversa do whatsapp" in base or "whatsapp chat" in base


def chave_obra(numero: str) -> str:
    """Número da obra sem o sufixo de versão do grupo (8977.1.v10 -> 8977.1)."""
    return re.sub(r"\.v\d+$", "", (numero or "").strip(), flags=re.IGNORECASE)


def _limpar_cliente(texto: str) -> str:
    texto = " ".join(texto.split()).strip(" -–_.,:")
    return texto


def _do_nome(nome_arquivo: str) -> tuple[str, str]:
    base = corrigir_mojibake(unicodedata.normalize("NFC", Path(nome_arquivo).stem))
    base = _PREFIXO.sub("", base).strip()
    entre_parenteses = _PAREN.findall(base)
    sem_parenteses = _PAREN.sub(" ", base)
    numero = ""
    achado = _NUMERO_DA_OBRA.search(sem_parenteses) or _NUMERO.search(sem_parenteses)
    if achado:
        numero = chave_obra(achado.group(achado.lastindex or 0))
        resto = sem_parenteses.replace(achado.group(0), " ", 1)
    else:
        resto = sem_parenteses
        for conteudo in entre_parenteses:
            dentro = _NUMERO.search(conteudo)
            if dentro:
                numero = chave_obra(dentro.group(0))
                break
    cliente = _limpar_cliente(re.sub(r"^\s*obra\b", "", resto, flags=re.IGNORECASE))
    if not cliente:
        for conteudo in entre_parenteses:
            limpo = re.sub(r"^\s*obra\s*", "", conteudo, flags=re.IGNORECASE)
            limpo = _limpar_cliente(_NUMERO.sub(" ", limpo))
            if limpo:
                cliente = limpo
                break
    return numero, cliente


def _do_texto(texto: str) -> tuple[str, str]:
    if not texto:
        return "", ""
    numero = ""
    cliente = ""
    achado = re.search(r"Obra\s+(\d{3,}[\d.]*(?:\.v\d+)?)", texto, re.IGNORECASE)
    if achado:
        numero = chave_obra(achado.group(1).rstrip("."))
    achado = re.search(r"Cliente:\s*([^.\n]+)", texto, re.IGNORECASE)
    if achado:
        cliente = _limpar_cliente(achado.group(1))
    return numero, cliente


def inferir_identidade(nome_arquivo: str, texto: str = "") -> dict:
    """Número da obra e cliente.

    O número vem do nome do arquivo (é o nome do grupo); "Obra 02" solta numa mensagem
    não vale. O texto só entra se o nome não tiver número. Já "Cliente: ..." escrito
    no grupo vale mais que o nome do arquivo, que pode vir sem acento.
    """
    n_nome, c_nome = _do_nome(nome_arquivo)
    n_texto, c_texto = _do_texto(texto)
    return {"numero": n_nome or n_texto, "cliente": c_texto or c_nome}


def _datas(texto: str) -> tuple[str, str]:
    if not texto:
        return "", ""
    mensagens = [item for item in analisar_conversa(texto) if not item.sistema] or analisar_conversa(texto)
    if not mensagens:
        return "", ""
    datas = [item.data.isoformat() for item in mensagens if not item.encaminhada_por] or [item.data.isoformat() for item in mensagens]
    return min(datas), max(datas)


def _nome_no_zip(info: zipfile.ZipInfo) -> str:
    nome = info.filename
    if not (info.flag_bits & 0x800):
        try:
            nome = info.filename.encode("cp437").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return nome_seguro(corrigir_mojibake(nome))


def _txt_do_zip(caminho: Path) -> tuple[str, str]:
    """Lê só o .txt de conversa. Não toca nas mídias, mesmo num zip de 600 MB."""
    melhor_nome = ""
    melhor_texto = ""
    with zipfile.ZipFile(caminho) as arquivo:
        for info in arquivo.infolist():
            if info.is_dir() or info.file_size > LIMITE_TXT:
                continue
            nome = _nome_no_zip(info)
            if Path(nome).suffix.lower() != ".txt":
                continue
            with arquivo.open(info, "r") as origem:
                texto = decodificar_bytes(origem.read())
            if parece_conversa(texto) and len(texto) > len(melhor_texto):
                melhor_nome, melhor_texto = nome, texto
    return melhor_nome, melhor_texto


def examinar_arquivo(caminho: Path) -> dict | None:
    """Dados da exportação, ou None se não for conversa do WhatsApp."""
    caminho = Path(caminho)
    sufixo = caminho.suffix.lower()
    nome_bate = nome_parece_exportacao(caminho.name)
    nome_txt = ""
    texto = ""
    if sufixo == ".zip":
        try:
            nome_txt, texto = _txt_do_zip(caminho)
        except (zipfile.BadZipFile, OSError):
            return None
        if not texto:
            return None
    elif sufixo == ".txt":
        if caminho.name.lower() in {"origem.txt", "leia-me.txt"}:
            return None
        try:
            if caminho.stat().st_size > LIMITE_TXT:
                return None
            texto = decodificar_bytes(caminho.read_bytes())
        except OSError:
            return None
        if not parece_conversa(texto):
            return None
        nome_txt = caminho.name
    else:
        return None
    identidade = inferir_identidade(caminho.name, texto)
    inicio, fim = _datas(texto)
    return {
        "tipo": "zip" if sufixo == ".zip" else "txt",
        "caminho": str(caminho),
        "nome": unicodedata.normalize("NFC", caminho.name),
        "nome_bate": nome_bate,
        "conversa": nome_txt,
        "numero": identidade["numero"],
        "cliente": identidade["cliente"],
        "primeira_mensagem": inicio,
        "ultima_mensagem": fim,
    }


def caminhar(raiz: Path, profundidade: int = PROFUNDIDADE):
    """Lista arquivos com iterdir. Sem glob, para acento e colchete não atrapalharem."""

    def visitar(pasta: Path, nivel: int):
        if nivel > profundidade:
            return
        try:
            filhos = list(pasta.iterdir())
        except OSError:
            return
        for filho in filhos:
            try:
                if filho.is_symlink():
                    continue
                if filho.is_dir():
                    if filho.name.lower() in IGNORAR_DIR:
                        continue
                    yield from visitar(filho, nivel + 1)
                elif filho.is_file():
                    yield filho
            except OSError:
                continue

    if Path(raiz).is_dir():
        yield from visitar(Path(raiz), 0)


def descobrir_em(raizes: list[Path], profundidade: int = PROFUNDIDADE) -> list[dict]:
    achados: list[dict] = []
    vistos: set[str] = set()
    for raiz in raizes:
        for arquivo in caminhar(Path(raiz), profundidade):
            if arquivo.suffix.lower() not in {".zip", ".txt"}:
                continue
            try:
                chave = os.path.normcase(str(arquivo.resolve()))
            except OSError:
                chave = os.path.normcase(str(arquivo))
            if chave in vistos:
                continue
            vistos.add(chave)
            item = examinar_arquivo(arquivo)
            if item:
                achados.append(item)
    return achados


def _pastas_do_windows() -> list[Path]:
    if os.name != "nt":
        return []
    try:
        import winreg
    except ImportError:
        return []
    saida: list[Path] = []
    nomes = ("Desktop", "{374DE290-123F-4565-9164-39C4925E467B}", "Personal")
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
        ) as chave:
            for nome in nomes:
                try:
                    valor, _ = winreg.QueryValueEx(chave, nome)
                except OSError:
                    continue
                saida.append(Path(os.path.expandvars(str(valor))))
    except OSError:
        pass
    return saida


def pastas_de_busca(home: Path | None = None, config: dict | None = None) -> list[Path]:
    home = Path(home) if home else Path.home()
    simples = ("Downloads", "Desktop", "Área de Trabalho", "Area de Trabalho")
    nuvem = simples + ("Documentos", "Documents")
    candidatos = [home / nome for nome in simples]
    bases = [home / "OneDrive"]
    for variavel in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        valor = os.environ.get(variavel, "").strip()
        if valor:
            bases.append(Path(valor))
    for base in bases:
        candidatos += [base / nome for nome in nuvem]
    candidatos += _pastas_do_windows()
    if config and config.get("pasta_raiz"):
        candidatos.append(Path(config["pasta_raiz"]))
    saida: list[Path] = []
    vistos: set[str] = set()
    for candidato in candidatos:
        try:
            if not candidato.is_dir():
                continue
            chave = os.path.normcase(str(candidato.resolve()))
        except OSError:
            continue
        if chave not in vistos:
            vistos.add(chave)
            saida.append(candidato)
    # Evita ler a mesma pasta duas vezes quando uma está dentro da outra.
    return [p for p in saida if not any(o != p and _dentro(p, o) for o in saida)]


def _dentro(filho: Path, pai: Path) -> bool:
    try:
        filho.resolve().relative_to(pai.resolve())
        return True
    except (ValueError, OSError):
        return False
