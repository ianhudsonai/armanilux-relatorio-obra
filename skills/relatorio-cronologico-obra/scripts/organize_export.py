"""Localiza o zip (ou o txt) do WhatsApp e distribui os arquivos nas subpastas.

A extração é em fluxo: cada item é copiado em blocos de 1 MB, sem carregar
o zip inteiro na memória. Nomes com mojibake são reparados. Caminho com
'..' é ignorado.
"""

from __future__ import annotations

import argparse
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from common import (
    EXT_DOCUMENTO,
    EXT_MIDIA,
    configurar_saida,
    corrigir_mojibake,
    decodificar_bytes,
    nome_seguro,
)
from parse_whatsapp import parece_conversa

BLOCO = 1024 * 1024
AVISO_TAMANHO = 500 * 1024 * 1024


class ExportacaoNaoEncontrada(FileNotFoundError):
    """Não há zip nem conversa .txt onde o script procurou."""


def _nome_do_item(info: zipfile.ZipInfo) -> str:
    nome = info.filename
    if not (info.flag_bits & 0x800):
        # O zipfile já decodificou como CP437. Tenta recuperar UTF-8 original.
        try:
            nome = info.filename.encode("cp437").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            nome = info.filename
    return corrigir_mojibake(nome)


def _caminho_inseguro(nome: str) -> bool:
    bruto = nome.replace("\\", "/")
    if bruto.startswith("/") or (len(bruto) >= 2 and bruto[1] == ":"):
        return True
    return ".." in Path(bruto).parts


def _subpasta_de(nome: str) -> str:
    extensao = Path(nome).suffix.lower()
    if extensao == ".txt":
        return "01-conversas"
    if extensao in EXT_DOCUMENTO:
        return "02-projetos-pdf"
    if extensao in EXT_MIDIA:
        return "03-midias"
    return "01-conversas/outros"


def _destino_unico(pasta: Path, nome: str) -> Path:
    candidato = pasta / nome
    if not candidato.exists():
        return candidato
    stem = Path(nome).stem
    sufixo = Path(nome).suffix
    indice = 2
    while True:
        alternativo = pasta / f"{stem}-{indice}{sufixo}"
        if not alternativo.exists():
            return alternativo
        indice += 1


def extrair_zip(caminho_zip: Path, pasta_obra: Path) -> dict:
    """Extrai o zip para as subpastas da obra. Devolve um resumo."""
    caminho_zip = Path(caminho_zip)
    tamanho = caminho_zip.stat().st_size
    copiados: list[dict] = []
    ignorados: list[str] = []
    ja_existiam = 0
    with zipfile.ZipFile(caminho_zip) as arquivo:
        for info in arquivo.infolist():
            if info.is_dir():
                continue
            original = _nome_do_item(info)
            if _caminho_inseguro(original):
                ignorados.append(original)
                continue
            nome = nome_seguro(original)
            destino_dir = pasta_obra / _subpasta_de(nome)
            destino_dir.mkdir(parents=True, exist_ok=True)
            existente = destino_dir / nome
            if existente.is_file() and existente.stat().st_size == info.file_size:
                # Mesmo arquivo de uma rodada anterior (ex.: conversa nova da mesma obra).
                # Não duplica; só conta.
                destino = existente
                ja_existiam += 1
            else:
                destino = _destino_unico(destino_dir, nome)
                with arquivo.open(info, "r") as origem, destino.open("wb") as saida:
                    shutil.copyfileobj(origem, saida, length=BLOCO)
            copiados.append(
                {
                    "origem": original,
                    "destino": str(destino.relative_to(pasta_obra)).replace("\\", "/"),
                    "bytes": destino.stat().st_size,
                }
            )
    origem_txt = pasta_obra / "01-conversas" / "origem.txt"
    with origem_txt.open("a", encoding="utf-8") as registro:
        registro.write(
            "\n".join(
                [
                    f"Zip de origem: {caminho_zip}",
                    f"Tamanho em bytes: {tamanho}",
                    f"Extraído em: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                    f"Arquivos novos: {len(copiados) - ja_existiam}. Já existiam: {ja_existiam}.",
                    "",
                    "",
                ]
            )
        )
    return {
        "zip": str(caminho_zip),
        "bytes": tamanho,
        "grande": tamanho > AVISO_TAMANHO,
        "arquivos": copiados,
        "ja_existiam": ja_existiam,
        "ignorados": ignorados,
    }


def ler_txt_do_zip(caminho_zip: Path) -> tuple[str, str] | None:
    """Lê só os .txt (pequenos) para identificar a obra antes de extrair o resto."""
    melhor_nome = ""
    melhor_texto = ""
    with zipfile.ZipFile(caminho_zip) as arquivo:
        for info in arquivo.infolist():
            if info.is_dir():
                continue
            nome = nome_seguro(_nome_do_item(info))
            if Path(nome).suffix.lower() != ".txt":
                continue
            with arquivo.open(info, "r") as origem:
                dados = origem.read()
            texto = decodificar_bytes(dados)
            if parece_conversa(texto) and len(texto) > len(melhor_texto):
                melhor_nome = nome
                melhor_texto = texto
    if not melhor_texto:
        return None
    return melhor_nome, melhor_texto


def _candidatos_zip(pastas: list[Path]) -> list[Path]:
    achados: list[Path] = []
    for pasta in pastas:
        if not pasta or not pasta.exists():
            continue
        achados.extend(item for item in pasta.glob("*.zip") if item.is_file())
    return sorted(achados, key=lambda item: item.stat().st_mtime, reverse=True)


def _candidatos_txt(pastas: list[Path]) -> list[Path]:
    achados: list[Path] = []
    for pasta in pastas:
        if not pasta or not pasta.exists():
            continue
        for item in pasta.glob("*.txt"):
            if item.name.lower() in {"origem.txt", "leia-me.txt"}:
                continue
            achados.append(item)
    return sorted(achados, key=lambda item: item.stat().st_mtime, reverse=True)


def localizar_exportacao(
    pasta_obra: Path | None,
    downloads: Path | None,
    zip_explicito: Path | None = None,
    chat_explicito: Path | None = None,
) -> tuple[str, Path]:
    """Devolve ('zip'|'txt', caminho). Procura na obra e em Downloads."""
    if zip_explicito:
        caminho = Path(zip_explicito)
        if not caminho.is_file():
            raise ExportacaoNaoEncontrada(f"Não encontrei o zip informado: {caminho}")
        return "zip", caminho
    if chat_explicito:
        caminho = Path(chat_explicito)
        if not caminho.is_file():
            raise ExportacaoNaoEncontrada(f"Não encontrei a conversa informada: {caminho}")
        return "txt", caminho

    pastas: list[Path] = []
    if pasta_obra:
        pastas.extend(
            [
                pasta_obra,
                pasta_obra / "01-conversas",
            ]
        )
    if downloads:
        pastas.append(downloads)

    for candidato in _candidatos_zip(pastas):
        try:
            if ler_txt_do_zip(candidato):
                return "zip", candidato
        except zipfile.BadZipFile:
            continue

    for candidato in _candidatos_txt(pastas):
        try:
            texto = decodificar_bytes(candidato.read_bytes())
        except OSError:
            continue
        if parece_conversa(texto):
            return "txt", candidato

    raise ExportacaoNaoEncontrada(
        "Não encontrei um zip de exportação do WhatsApp.\n"
        "Procurei na pasta da obra e em Downloads.\n"
        "No celular: abra o grupo, toque no nome do grupo, escolha Exportar conversa "
        "e inclua a mídia. Se o arquivo ficar grande demais (o WhatsApp e o e-mail "
        "reclamam perto de 500 MB), exporte sem mídia e salve o zip em Downloads."
    )


def copiar_txt_avulso(origem: Path, pasta_obra: Path) -> Path:
    destino_dir = pasta_obra / "01-conversas"
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino = _destino_unico(destino_dir, nome_seguro(origem.name))
    if origem.resolve() != destino.resolve():
        with origem.open("rb") as entrada, destino.open("wb") as saida:
            shutil.copyfileobj(entrada, saida, length=BLOCO)
    return destino


def main(argv: list[str] | None = None) -> int:
    configurar_saida()
    parser = argparse.ArgumentParser(description="Descompacta e organiza um export do WhatsApp.")
    parser.add_argument("--zip", dest="zip_path", required=True)
    parser.add_argument("--obra-dir", required=True)
    args = parser.parse_args(argv)
    resumo = extrair_zip(Path(args.zip_path), Path(args.obra_dir))
    print(f"Arquivos organizados: {len(resumo['arquivos'])}")
    if resumo["grande"]:
        print(
            "Aviso: o zip passa de 500 MB. A extração é local e em partes, "
            "mas vídeos longos deixam a transcrição lenta. Se precisar só do "
            "relatório escrito, exporte o grupo sem mídia."
        )
    if resumo["ignorados"]:
        print(f"Itens ignorados por caminho inseguro: {len(resumo['ignorados'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
