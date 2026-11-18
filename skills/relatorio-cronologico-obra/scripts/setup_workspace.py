"""Cria a pasta de trabalho da Armanilux e as subpastas de uma obra."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import SUBPASTAS, configurar_saida, pasta_padrao, sanitizar_pasta

LEIA_ME = """Pasta de relatórios de obra da Armanilux

Cada obra fica numa subpasta com o número e o nome do cliente.
Dentro dela:

01-conversas      exportação do WhatsApp (o arquivo de texto)
02-projetos-pdf   projetos em PDF ou Word
03-midias         fotos, áudios, vídeos e quadros extraídos dos vídeos
04-transcricoes   textos dos áudios e a análise usada no relatório
05-relatorios     o relatório em Word (e o PDF, se o computador conseguir gerar)

O zip original do WhatsApp não é apagado.
Nada desta pasta é enviado para um serviço de transcrição na internet.
Não coloque estas pastas dentro do repositório público da skill.
"""


def garantir_raiz(caminho: Path | None = None) -> Path:
    raiz = Path(caminho) if caminho else pasta_padrao()
    raiz.mkdir(parents=True, exist_ok=True)
    aviso = raiz / "LEIA-ME.txt"
    if not aviso.exists():
        aviso.write_text(LEIA_ME, encoding="utf-8")
    return raiz


def garantir_obra(raiz: Path, numero: str, cliente: str) -> Path:
    nome = sanitizar_pasta(f"{numero} - {cliente}")
    obra = raiz / nome
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
