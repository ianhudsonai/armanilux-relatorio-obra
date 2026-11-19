"""Lê e grava as preferências da Armanilux.

O arquivo fica em %USERPROFILE%\\.armanilux-relatorio\\config.json,
ou no caminho de ARMANILUX_CONFIG quando um teste aponta outro lugar.
Este módulo é copiado igual nas duas skills, porque cada pasta instalada
precisa funcionar sozinha.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

MODELO_PADRAO = "{numero} - {cliente}"
SUBPASTAS = (
    "01-conversas",
    "02-projetos-pdf",
    "03-midias",
    "04-transcricoes",
    "05-relatorios",
)


def _sanitizar(nome: str) -> str:
    limpo = re.sub(r'[<>:"/\\|?*]', " ", nome)
    limpo = re.sub(r"\s+", " ", limpo).strip(" .")
    return limpo[:80] or "obra-sem-nome"


def caminho_config() -> Path:
    bruto = os.environ.get("ARMANILUX_CONFIG", "").strip()
    if bruto:
        return Path(bruto)
    return Path.home() / ".armanilux-relatorio" / "config.json"


def padroes() -> dict:
    return {
        "pasta_raiz": str(Path.home() / "Documents" / "Armanilux"),
        "nome": "",
        "funcao": "",
        "gerar_pdf": False,
        "modelo_pasta_obra": MODELO_PADRAO,
        "baixar_modelo_whisper": False,
    }


def carregar() -> dict | None:
    caminho = caminho_config()
    if not caminho.is_file():
        return None
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    if not isinstance(dados, dict):
        return None
    completo = padroes()
    for chave in completo:
        if chave in dados:
            completo[chave] = dados[chave]
    return completo


def salvar(dados: dict) -> Path:
    completo = padroes()
    for chave in completo:
        if chave in dados and dados[chave] is not None:
            completo[chave] = dados[chave]
    caminho = caminho_config()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(completo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return caminho


def pasta_relatorios(config: dict) -> Path:
    return Path(config["pasta_raiz"]) / "Relatorios-de-Obra"


def nome_pasta_obra(config: dict, numero: str, cliente: str) -> str:
    modelo = str(config.get("modelo_pasta_obra") or MODELO_PADRAO).strip() or MODELO_PADRAO
    valores = {"numero": numero or "sem-numero", "cliente": cliente or "cliente"}
    try:
        texto = modelo.format(**valores)
    except (KeyError, IndexError, ValueError):
        texto = MODELO_PADRAO.format(**valores)
    return _sanitizar(texto)
