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


def _candidatos_de_nuvem() -> list[Path]:
    candidatos = [Path(os.environ[v]) for v in ("OneDriveCommercial", "OneDrive") if os.environ.get(v)]
    if os.name == "nt":
        # O Google Drive usa a primeira letra livre (G: é a mais comum).
        letras = "GHIJKLMNOPQRSTUVWXYZDEF"
        candidatos += [Path(f"{letra}:/{nome}") for letra in letras for nome in ("My Drive", "Meu Drive")]
    casa = Path.home()
    candidatos += [casa / "My Drive", casa / "Meu Drive", casa / "Google Drive" / "My Drive", casa / "Google Drive"]
    return candidatos


def pastas_da_nuvem(candidatos: list[Path] | None = None) -> list[Path]:
    """Pastas do OneDrive e do Google Drive deste computador onde os relatórios para link ficariam."""
    achadas: list[Path] = []
    for candidato in _candidatos_de_nuvem() if candidatos is None else candidatos:
        try:
            if candidato.is_dir():
                destino = candidato / "Armanilux" / "Relatorios"
                if destino not in achadas:
                    achadas.append(destino)
        except OSError:
            continue
    return achadas


def pasta_da_nuvem() -> Path | None:
    achadas = pastas_da_nuvem()
    return achadas[0] if achadas else None


def _pasta_digitada_serve(pasta: Path) -> bool:
    """A pasta escolhida existe, ou é `<pasta da nuvem>/Armanilux/Relatorios` ainda por criar."""
    return pasta.is_dir() or pasta.parent.parent.is_dir() and pasta.parent.parent != pasta.parent.parent.parent


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
            "Os áudios e os vídeos viram texto só neste computador.",
            "Para escrever o relatório, o ChatGPT (Codex) lê a conversa, o texto dos áudios, os documentos e as fotos da obra.",
            "No ChatGPT, em Configurações > Controles de dados, deixe desligado \"Melhorar o modelo para todos\".",
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
    parser.add_argument("--pasta-raiz")
    parser.add_argument("--listar-nuvens", action="store_true", help="Mostra as pastas do OneDrive e do Google Drive achadas")
    parser.add_argument("--nome", default="")
    parser.add_argument("--funcao", default="")
    parser.add_argument("--pdf", default="nao", help="Antigo: sim é o mesmo que --entrega pdf")
    parser.add_argument("--entrega", choices=("word", "pdf", "link"))
    parser.add_argument("--pasta-link", default="auto", help="auto acha o OneDrive ou o Google Drive")
    parser.add_argument("--modelo", default="{numero} - {cliente}")
    parser.add_argument("--baixar-modelo", default="nao")
    args = parser.parse_args(argv)
    if args.listar_nuvens:
        achadas = pastas_da_nuvem()
        for pasta in achadas:
            print(f"NUVEM: {pasta}")
        if not achadas:
            print("Nenhuma pasta do OneDrive ou do Google Drive neste computador.")
        return 0
    if not args.pasta_raiz:
        parser.error("informe --pasta-raiz")
    formato = args.entrega or ("pdf" if _sim(args.pdf) else "word")
    pasta_link = ""
    if formato == "link":
        if args.pasta_link.strip().lower() == "auto":
            achada = pasta_da_nuvem()
        else:
            achada = Path(args.pasta_link)
            if not _pasta_digitada_serve(achada):
                print(f"Não achei a pasta {achada}.")
                achada = None
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
