"""Grava as preferências e cria as pastas da Armanilux. Pode rodar de novo."""

from __future__ import annotations

import argparse
from pathlib import Path

from config_io import SUBPASTAS, caminho_config, carregar, nome_pasta_obra, pasta_relatorios, salvar


def texto_leia_me(config: dict) -> str:
    exemplo = nome_pasta_obra(config, "1001", "Família Exemplo")
    pdf = "sim" if config.get("gerar_pdf") else "não"
    nome = config.get("nome") or "não informado"
    funcao = config.get("funcao") or "não informada"
    return "\n".join(
        [
            "Pasta da Armanilux",
            "",
            f"Responsável pelos relatórios: {nome}",
            f"Função: {funcao}",
            f"Gerar PDF além do Word: {pdf}",
            f"Nome de cada obra: {config.get('modelo_pasta_obra')}",
            f"Exemplo: {exemplo}",
            "",
            "Os relatórios ficam em Relatorios-de-Obra.",
            "Cada obra tem estas pastas:",
            "",
            *SUBPASTAS,
            "",
            "Coloque o zip do WhatsApp em Downloads ou na pasta da obra.",
            "O Word sai em 05-relatorios.",
            "Nada daqui é enviado para um serviço de transcrição na internet.",
            "As preferências estão em %USERPROFILE%\\.armanilux-relatorio\\config.json.",
            "Para mudar nome, pasta ou PDF, rode de novo a preparação no Codex.",
            "",
        ]
    )


def preparar(
    pasta_raiz: str,
    nome: str,
    funcao: str,
    gerar_pdf: bool,
    modelo: str,
    baixar_modelo_whisper: bool = False,
) -> dict:
    atual = carregar() or {}
    config = {
        "pasta_raiz": str(Path(pasta_raiz)),
        "nome": nome.strip(),
        "funcao": funcao.strip(),
        "gerar_pdf": bool(gerar_pdf),
        "modelo_pasta_obra": modelo.strip() or atual.get("modelo_pasta_obra") or "{numero} - {cliente}",
        "baixar_modelo_whisper": bool(baixar_modelo_whisper),
    }
    salvar(config)
    raiz = Path(config["pasta_raiz"])
    relatorios = pasta_relatorios(config)
    modelo_dir = relatorios / "_modelo"
    for subpasta in SUBPASTAS:
        (modelo_dir / subpasta).mkdir(parents=True, exist_ok=True)
    (raiz / "LEIA-ME.txt").write_text(texto_leia_me(config), encoding="utf-8")
    return config


def _sim(valor: str) -> bool:
    return valor.strip().lower() in {"1", "s", "sim", "true", "yes"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Grava as preferências da Armanilux e cria as pastas.")
    parser.add_argument("--pasta-raiz", required=True)
    parser.add_argument("--nome", default="")
    parser.add_argument("--funcao", default="")
    parser.add_argument("--pdf", default="nao")
    parser.add_argument("--modelo", default="{numero} - {cliente}")
    parser.add_argument("--baixar-modelo", default="nao")
    args = parser.parse_args(argv)
    config = preparar(
        args.pasta_raiz,
        args.nome,
        args.funcao,
        _sim(args.pdf),
        args.modelo,
        _sim(args.baixar_modelo),
    )
    print(f"Preferências gravadas em: {caminho_config()}")
    print(f"Pasta da Armanilux: {config['pasta_raiz']}")
    print(f"Relatórios: {pasta_relatorios(config)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
