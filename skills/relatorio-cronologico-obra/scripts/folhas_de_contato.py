"""Junta as fotos e um quadro de cada vídeo em folhas de 12 miniaturas numeradas.

Assim quem revisa (o agente, ou subagentes em paralelo, se o aplicativo permitir)
olha uma dúzia de folhas em vez de centenas de arquivos e não deixa imagem de lado.
O índice de cada folha diz o arquivo e a data de cada miniatura. Tudo neste computador.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from common import EXT_IMAGEM, EXT_VIDEO

POR_FOLHA = 12
COLUNAS = 4
LADO = 360


def _data_do_nome(nome: str) -> str:
    achado = re.search(r"(20\d{2})(\d{2})(\d{2})", nome)
    return f"{achado.group(3)}/{achado.group(2)}/{achado.group(1)}" if achado else ""


def listar_imagens(pasta_midias: Path) -> list[tuple[str, Path]]:
    """Fotos da pasta e o quadro do meio de cada vídeo, em ordem de nome (que segue a data)."""
    itens: list[tuple[str, Path]] = []
    if not pasta_midias.is_dir():
        return itens
    for arquivo in sorted(pasta_midias.iterdir()):
        if not arquivo.is_file() or arquivo.name.upper().startswith("STK-"):
            continue  # figurinha do WhatsApp não é registro de obra
        sufixo = arquivo.suffix.lower()
        if sufixo in EXT_IMAGEM and sufixo not in {".gif"}:
            itens.append((arquivo.name, arquivo))
        elif sufixo in EXT_VIDEO:
            pasta = pasta_midias / "quadros" / arquivo.stem
            quadro = next((q for q in (pasta / "quadro-02.jpg", pasta / "quadro-01.jpg") if q.is_file()), None)
            if quadro:
                itens.append((arquivo.name, quadro))
    return itens


def gerar(pasta_obra: Path) -> list[Path]:
    from PIL import Image, ImageDraw

    itens = listar_imagens(pasta_obra / "03-midias")
    destino = pasta_obra / "04-transcricoes" / "folhas-de-contato"
    destino.mkdir(parents=True, exist_ok=True)
    folhas: list[Path] = []
    indice: dict[str, list[dict]] = {}
    linhas = (POR_FOLHA + COLUNAS - 1) // COLUNAS
    for inicio in range(0, len(itens), POR_FOLHA):
        grupo = itens[inicio : inicio + POR_FOLHA]
        folha = Image.new("RGB", (COLUNAS * LADO, linhas * (LADO + 34)), "white")
        desenho = ImageDraw.Draw(folha)
        numero_folha = len(folhas) + 1
        nome_folha = f"folha-{numero_folha:02d}.jpg"
        indice[nome_folha] = []
        for posicao, (nome, caminho) in enumerate(grupo):
            numero = inicio + posicao + 1
            x = (posicao % COLUNAS) * LADO
            y = (posicao // COLUNAS) * (LADO + 34)
            try:
                miniatura = Image.open(caminho).convert("RGB")
                miniatura.thumbnail((LADO - 10, LADO - 10))
                folha.paste(miniatura, (x + 5, y + 5))
            except Exception:
                desenho.text((x + 10, y + 10), "imagem ilegível", fill="red")
            rotulo = f"{numero}. {nome[:34]} {_data_do_nome(nome)}"
            desenho.text((x + 6, y + LADO + 6), rotulo, fill="black")
            indice[nome_folha].append({"numero": numero, "arquivo": nome, "data": _data_do_nome(nome), "video": Path(nome).suffix.lower() in EXT_VIDEO})
        caminho_folha = destino / nome_folha
        folha.save(caminho_folha, format="JPEG", quality=80)
        folhas.append(caminho_folha)
    (destino / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=2), encoding="utf-8")
    return folhas
