"""Cria a pasta de trabalho da Armanilux e as subpastas de uma obra."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import SUBPASTAS, configurar_saida, pasta_padrao
from config_io import nome_pasta_obra

LEIA_ME = """Pasta de relatórios de obra da Armanilux

Cada obra fica numa subpasta com o número e o nome do cliente.
Dentro dela:

01-conversas      exportação do WhatsApp (o arquivo de texto)
02-projetos-pdf   projetos em PDF ou Word
03-midias         fotos, áudios, vídeos e quadros extraídos dos vídeos
04-transcricoes   textos dos áudios e a análise usada no relatório
05-relatorios     o relatório em Word (e o PDF, se o computador conseguir gerar)

O zip original do WhatsApp não é apagado.
Os áudios e os vídeos viram texto neste computador. Para escrever o relatório,
o ChatGPT (Codex) lê a conversa, as transcrições, os documentos e as fotos desta pasta.
Não coloque estas pastas dentro do repositório público da skill.
"""


def garantir_raiz(caminho: Path | None = None) -> Path:
    raiz = Path(caminho) if caminho else pasta_padrao()
    raiz.mkdir(parents=True, exist_ok=True)
    aviso = raiz / "LEIA-ME.txt"
    if not aviso.exists():
        aviso.write_text(LEIA_ME, encoding="utf-8")
    return raiz


def _pasta_da_mesma_obra(raiz: Path, numero: str, modelo: str) -> Path | None:
    """A pasta que já existe para este número de obra, com o cliente escrito de outro jeito.
    Só vale quando há exatamente uma: o número identifica a obra; o cliente varia na digitação."""
    if not numero or "{cliente}" not in modelo or not raiz.is_dir():
        return None
    # Monta o nome com uma marca no lugar do cliente para saber o que vem antes e depois dele.
    marca = "\x00"
    molde = nome_pasta_obra({"modelo_pasta_obra": modelo}, numero, marca)
    if marca not in molde:
        return None
    antes, depois = molde.split(marca, 1)
    iguais = [
        pasta
        for pasta in raiz.iterdir()
        if pasta.is_dir()
        and len(pasta.name) > len(antes) + len(depois)
        and pasta.name.startswith(antes)
        and pasta.name.endswith(depois)
    ]
    if len(iguais) > 1:
        nomes = ", ".join(sorted(pasta.name for pasta in iguais))
        print(f"Aviso: a obra {numero} tem {len(iguais)} pastas ({nomes}). Não escolhi uma sozinho; confira com a pessoa.")
    return iguais[0] if len(iguais) == 1 else None


def garantir_obra(raiz: Path, numero: str, cliente: str, modelo: str = "{numero} - {cliente}") -> Path:
    nome = nome_pasta_obra({"modelo_pasta_obra": modelo}, numero, cliente)
    obra = raiz / nome
    if not obra.exists():
        existente = _pasta_da_mesma_obra(raiz, numero, modelo)
        if existente:
            print(f"A obra {numero} já tem pasta: {existente.name}. Usei essa.")
            obra = existente
    for subpasta in SUBPASTAS:
        (obra / subpasta).mkdir(parents=True, exist_ok=True)
    (obra / "03-midias" / "quadros").mkdir(parents=True, exist_ok=True)
    return obra


def main(argv: list[str] | None = None) -> int:
    configurar_saida()
    parser = argparse.ArgumentParser(description="Cria a pasta de relatórios de obra.")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--obra", default=None)
    parser.add_argument("--cliente", default=None)
    args = parser.parse_args(argv)
    raiz = garantir_raiz(Path(args.workspace) if args.workspace else None)
    print(f"Pasta de trabalho: {raiz}")
    if args.obra and args.cliente:
        obra = garantir_obra(raiz, args.obra, args.cliente)
        print(f"Pasta da obra: {obra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
