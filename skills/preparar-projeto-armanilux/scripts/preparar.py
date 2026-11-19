"""Grava as preferências e cria as pastas da Armanilux. Pode rodar de novo."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from config_io import SUBPASTAS, caminho_config, carregar, nome_pasta_obra, pasta_relatorios, salvar


_TEXTO_ENTREGA = {
    "word": "Word",
    "pdf": "PDF (com o Word junto)",
    "link": "link (PDF numa pasta do OneDrive ou do Google Drive, para compartilhar)",
}


def pasta_da_nuvem(candidatos: list[Path] | None = None) -> Path | None:
    """Pasta do OneDrive ou do Google Drive deste computador, onde ficam os relatórios para link."""
    if candidatos is None:
        candidatos = [Path(os.environ[v]) for v in ("OneDriveCommercial", "OneDrive") if os.environ.get(v)]
        candidatos += [Path(f"{letra}:/{nome}") for letra in "GHIJ" for nome in ("My Drive", "Meu Drive")]
        casa = Path.home()
        candidatos += [casa / "My Drive", casa / "Meu Drive", casa / "Google Drive" / "My Drive", casa / "Google Drive"]
    for candidato in candidatos:
        try:
            if candidato.is_dir():
                return candidato / "Armanilux" / "Relatorios"
        except OSError:
            continue
    return None


def texto_leia_me(config: dict) -> str:
    exemplo = nome_pasta_obra(config, "1001", "Família Exemplo")
    entrega = _TEXTO_ENTREGA.get(config.get("formato_entrega") or "", "Word")
    if config.get("formato_entrega") == "link" and config.get("pasta_link"):
        entrega += f" (pasta da nuvem: {config['pasta_link']})"
    nome = config.get("nome") or "não informado"
    funcao = config.get("funcao") or "não informada"
    return "\n".join(
        [
            "Pasta da Armanilux",
            "",
            f"Quem assina os relatórios: {nome}",
            f"Cargo: {funcao}",
            f"Entrega: {entrega}",
            f"Exemplo de pasta de obra: {exemplo}",
            "",
            "Os relatórios ficam na pasta Relatorios-de-Obra.",
            "Cada obra tem estas pastas:",
            "",
            *SUBPASTAS,
            "",
            "Coloque o arquivo do WhatsApp em Downloads ou na pasta da obra.",
            "O arquivo do Word fica em 05-relatorios.",
            "Os áudios e os vídeos são lidos só neste computador. Nada é enviado para a internet.",
            "Para mudar nome, pasta ou entrega (Word, PDF ou link), peça de novo a preparação no Codex.",
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
    formato_entrega: str | None = None,
    pasta_link: str = "",
) -> dict:
    atual = carregar() or {}
    formato = formato_entrega or ("pdf" if gerar_pdf else "word")
    config = {
        "pasta_raiz": str(Path(pasta_raiz)),
        "nome": nome.strip(),
        "funcao": funcao.strip(),
        # gerar_pdf continua para quem ainda tem a skill de relatório antiga.
        "gerar_pdf": formato in ("pdf", "link"),
        "formato_entrega": formato,
        "pasta_link": str(pasta_link) if formato == "link" else "",
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
    parser.add_argument("--pdf", default="nao", help="Antigo: sim é o mesmo que --entrega pdf")
    parser.add_argument("--entrega", choices=("word", "pdf", "link"))
    parser.add_argument("--pasta-link", default="auto", help="auto acha o OneDrive ou o Google Drive")
    parser.add_argument("--modelo", default="{numero} - {cliente}")
    parser.add_argument("--baixar-modelo", default="nao")
    args = parser.parse_args(argv)
    formato = args.entrega or ("pdf" if _sim(args.pdf) else "word")
    pasta_link = ""
    if formato == "link":
        achada = pasta_da_nuvem() if args.pasta_link.strip().lower() == "auto" else Path(args.pasta_link)
        if achada is None:
            print(
                "Não achei a pasta do OneDrive nem do Google Drive neste computador. "
                "Gravei a entrega em PDF. Instale e entre no OneDrive ou no Google Drive e rode a preparação de novo para ter link."
            )
            formato = "pdf"
        else:
            pasta_link = str(achada)
    config = preparar(
        args.pasta_raiz,
        args.nome,
        args.funcao,
        formato != "word",
        args.modelo,
        _sim(args.baixar_modelo),
        formato_entrega=formato,
        pasta_link=pasta_link,
    )
    print(f"Preferências gravadas em: {caminho_config()}")
    print(f"Pasta da Armanilux: {config['pasta_raiz']}")
    print(f"Relatórios: {pasta_relatorios(config)}")
    print(f"Entrega: {_TEXTO_ENTREGA[config['formato_entrega']]}")
    if config["pasta_link"]:
        print(f"Pasta da nuvem: {config['pasta_link']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
