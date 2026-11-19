"""Gera o Relatório Cronológico de Obra a partir do export do WhatsApp.

Uso típico, no Windows, com o Python do instalador:

  %USERPROFILE%\\.armanilux-relatorio\\venv\\Scripts\\python.exe run_pipeline.py --zip "C:\\Users\\...\\WhatsApp.zip"

Tudo acontece neste computador. Não há chamada de API.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from analyze import aplicar_ajustes, completar_relato, montar_analise
from build_charts import grafico_barras, grafico_gantt
from build_docx import montar_docx, proxima_versao, tentar_pdf
from common import configurar_saida, escrever_json, ler_json
from config_io import carregar, pasta_relatorios
from extract_documents import extrair_pasta
from extract_keyframes import extrair_pasta as extrair_quadros
from organize_export import ExportacaoNaoEncontrada, copiar_txt_avulso, extrair_zip, localizar_exportacao
from parse_whatsapp import ler_conversa
from setup_workspace import garantir_obra, garantir_raiz
from transcribe_media import transcrever_pasta

CHAVES_PRESERVAR = (
    "observacoes_visuais",
    "comentarios",
    "recomendacoes_personalizadas",
    "conclusao_personalizada",
    "ajustes_eventos",
)


def _checar_bibliotecas() -> bool:
    faltando = []
    for nome, modulo in (
        ("python-docx", "docx"),
        ("matplotlib", "matplotlib"),
        ("holidays", "holidays"),
        ("Pillow", "PIL"),
        ("numpy", "numpy"),
    ):
        try:
            __import__(modulo)
        except ImportError:
            faltando.append(nome)
    tem_pdf = False
    for modulo in ("pdfplumber", "pypdf"):
        try:
            __import__(modulo)
            tem_pdf = True
        except ImportError:
            continue
    if not tem_pdf:
        faltando.append("pdfplumber ou pypdf")
    if faltando:
        print("Faltam bibliotecas: " + ", ".join(faltando) + ".")
        print("Rode a skill $preparar-projeto-armanilux.")
        print(
            "Se ela já estiver instalada, o instalador é "
            "%USERPROFILE%\\.codex\\skills\\preparar-projeto-armanilux\\scripts\\instalar.ps1"
        )
        return False
    return True


def _conversa_extraida(pasta_obra: Path) -> Path | None:
    pasta = pasta_obra / "01-conversas"
    if not pasta.exists():
        return None
    melhor: Path | None = None
    melhor_tamanho = -1
    for item in pasta.glob("*.txt"):
        if item.name.lower() in {"origem.txt", "leia-me.txt"}:
            continue
        tamanho = item.stat().st_size
        if tamanho > melhor_tamanho:
            melhor = item
            melhor_tamanho = tamanho
    return melhor


def _arquivos_da_obra(pasta_obra: Path) -> list[Path]:
    arquivos = []
    for subpasta in ("02-projetos-pdf", "03-midias"):
        raiz = pasta_obra / subpasta
        if not raiz.exists():
            continue
        for caminho in raiz.rglob("*"):
            if caminho.is_file() and "quadros" not in caminho.parts:
                arquivos.append(caminho)
    return arquivos


def _preservar(novo: dict, antigo: dict | None) -> dict:
    if not antigo:
        return novo
    for chave in CHAVES_PRESERVAR:
        if antigo.get(chave):
            novo[chave] = antigo[chave]
    if novo.get("ajustes_eventos"):
        aplicar_ajustes(novo["eventos"], novo["ajustes_eventos"])
        novo = completar_relato(novo)
    return novo


def _gravar(pasta_obra: Path, analise: dict, gerar_pdf: bool = False) -> Path:
    figuras = pasta_obra / "05-relatorios" / "figuras"
    barras = grafico_barras(analise.get("intervalos") or [], figuras / "dias-uteis.png")
    gantt = grafico_gantt(analise.get("eventos") or [], analise.get("intervalos") or [], figuras / "gantt.png")
    destino = proxima_versao(pasta_obra / "05-relatorios", analise["obra"].get("numero") or "sem-numero")
    montar_docx(analise, destino, barras, gantt)
    pdf = tentar_pdf(destino) if gerar_pdf else None
    print(f"Relatório gravado em:\n{destino}")
    if pdf:
        print(f"PDF gravado em:\n{pdf}")
    elif gerar_pdf:
        print("O PDF não saiu. O arquivo para enviar é o Word. O PDF só aparece se o LibreOffice estiver instalado.")
    else:
        print("O arquivo para enviar é o Word.")
    pendencias = analise.get("pendencias") or []
    if pendencias:
        print(f"Pendências com status Pendente: {len(pendencias)}.")
    return destino


def _aplicar_preferencias(analise: dict, config: dict | None) -> None:
    if not config:
        return
    obra = analise.setdefault("obra", {})
    if config.get("nome"):
        obra["elaborado_por"] = config["nome"]
        if not (obra.get("responsavel_armanilux") or "").strip():
            obra["responsavel_armanilux"] = config["nome"]
    if config.get("funcao"):
        obra["funcao"] = config["funcao"]


def _reconstruir(args, raiz: Path, config: dict | None) -> int:
    if args.obra_dir:
        pasta = Path(args.obra_dir)
    elif args.obra and args.cliente:
        modelo = (config or {}).get("modelo_pasta_obra") or "{numero} - {cliente}"
        pasta = garantir_obra(raiz, args.obra, args.cliente, modelo)
    else:
        print("Para remontar o Word, informe --obra-dir ou --obra e --cliente.")
        return 2
    caminho = pasta / "04-transcricoes" / "analise.json"
    if not caminho.exists():
        print("Não encontrei a análise desta obra. Rode primeiro com o zip do WhatsApp.")
        return 2
    analise = ler_json(caminho)
    if args.recalcular:
        analise = completar_relato(analise)
        escrever_json(caminho, analise)
    _aplicar_preferencias(analise, config)
    _gravar(pasta, analise, bool(args.pdf or (config or {}).get("gerar_pdf")))
    return 0


def executar(argv: list[str] | None = None) -> int:
    configurar_saida()
    parser = argparse.ArgumentParser(description="Gera o Relatório Cronológico de Obra da Armanilux.")
    parser.add_argument("--workspace", default=None, help="Pasta raiz. Padrão: Documentos/Armanilux/Relatorios-de-Obra")
    parser.add_argument("--obra-dir", default=None, help="Pasta já criada da obra")
    parser.add_argument("--obra", default=None)
    parser.add_argument("--cliente", default=None)
    parser.add_argument("--zip", dest="zip_path", default=None)
    parser.add_argument("--chat", default=None)
    parser.add_argument("--downloads", default=None)
    parser.add_argument("--skip-transcribe", action="store_true")
    parser.add_argument("--skip-keyframes", action="store_true")
    parser.add_argument("--whisper-model", default="small")
    parser.add_argument("--rebuild-only", action="store_true")
    parser.add_argument("--recalcular", action="store_true", help="Recalcula dias úteis e textos a partir dos eventos já salvos")
    parser.add_argument("--pdf", action="store_true", help="Mantido por compatibilidade; o PDF é tentado sempre que o LibreOffice existe")
    parser.add_argument("--listar", action="store_true", help="Só mostra as conversas sem relatório")
    parser.add_argument("--indice", action="append", default=None, help="Número(s) da lista, como 1 ou 1,3")
    parser.add_argument("--todas", action="store_true", help="Gera de todas as conversas da lista, uma por vez")
    parser.add_argument("--concluir", action="store_true", help="A pessoa aprovou o relatório: guarda o zip na obra")
    parser.add_argument("--copiar", action="store_true", help="Ao concluir, copia o zip em vez de mover")
    parser.add_argument("--sha", default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if args.concluir:
        return _concluir(args)

    config = carregar()
    if not args.workspace and not args.obra_dir and config is None:
        print("Não encontrei as preferências da Armanilux (config.json).")
        print("Abra um chat novo e rode a skill $preparar-projeto-armanilux.")
        return 2

    sem_origem = not (args.zip_path or args.chat or args.rebuild_only or args.obra_dir)
    if args.listar or args.indice or args.todas or sem_origem:
        if args.indice or args.todas:
            return _processar_escolha(args, config)
        return _listar(config, args.downloads)

    if not _checar_bibliotecas():
        return 1

    if args.workspace:
        raiz = garantir_raiz(Path(args.workspace))
    elif config:
        raiz = garantir_raiz(pasta_relatorios(config))
    else:
        raiz = garantir_raiz(None)
    print(f"Pasta de trabalho: {raiz}")
    modelo = (config or {}).get("modelo_pasta_obra") or "{numero} - {cliente}"
    gerar_pdf = bool(args.pdf or (config or {}).get("gerar_pdf"))
    if args.rebuild_only:
        return _reconstruir(args, raiz, config)

    pasta_conhecida = Path(args.obra_dir) if args.obra_dir else None
    if pasta_conhecida is None and args.obra and args.cliente:
        pasta_conhecida = garantir_obra(raiz, args.obra, args.cliente, modelo)
    downloads = Path(args.downloads) if args.downloads else Path.home() / "Downloads"
    if not downloads.exists():
        downloads = None

    try:
        tipo, origem = localizar_exportacao(
            pasta_conhecida,
            downloads,
            Path(args.zip_path) if args.zip_path else None,
            Path(args.chat) if args.chat else None,
        )
    except ExportacaoNaoEncontrada as erro:
        print(erro)
        return 2

    print(f"Exportação encontrada ({tipo}): {origem}")
    if tipo == "zip":
        resumo = None
        # A extração de verdade ocorre depois que a pasta da obra existe.
        from organize_export import ler_txt_do_zip

        lido = ler_txt_do_zip(origem)
        if not lido:
            print("O zip abriu, mas não há conversa do WhatsApp dentro dele. Exporte de novo pelo celular.")
            return 2
        _nome_txt, texto = lido
        from parse_whatsapp import analisar_conversa

        mensagens = analisar_conversa(texto)
    else:
        mensagens = ler_conversa(origem)
        resumo = None

    if not mensagens:
        print("A conversa foi lida, mas nenhuma mensagem tinha data reconhecível.")
        return 2

    from analyze import metadados_da_conversa
    from descoberta import inferir_identidade

    texto_grupo = "\n".join(m.texto for m in mensagens[:60])
    identidade = inferir_identidade(origem.name, texto_grupo)
    sobrepor = {
        "numero": args.obra or identidade["numero"],
        "cliente": args.cliente or identidade["cliente"],
    }
    if not sobrepor["numero"] or not sobrepor["cliente"]:
        print(
            "Não consegui descobrir sozinho o número da obra e o nome do cliente "
            "pelo nome do arquivo nem pelo grupo. Pergunte só isso à pessoa e rode de novo "
            "com --obra e --cliente."
        )
        return 2
    meta = metadados_da_conversa(mensagens, origem.name, sobrepor)
    numero = meta.get("numero") or sobrepor["numero"]
    cliente = meta.get("cliente") or sobrepor["cliente"]
    pasta_obra = garantir_obra(raiz, numero, cliente, modelo)
    try:
        _marcar_andamento(origem, args.sha, sobrepor)
    except Exception as erro:
        print(f"Aviso: o registro local não foi atualizado: {erro}")
    print(f"Pasta da obra: {pasta_obra}")

    if tipo == "zip":
        resumo = extrair_zip(origem, pasta_obra)
        print(f"Arquivos organizados: {len(resumo['arquivos'])}.")
        if resumo["grande"]:
            print(
                "Aviso: o zip passa de 500 MB. A leitura é local e em partes. "
                "Se o computador ficar lento, na próxima vez exporte o grupo sem mídia "
                "e copie só as fotos que importam para a pasta 03-midias."
            )
        if resumo["ignorados"]:
            print(f"Itens ignorados por caminho inseguro: {len(resumo['ignorados'])}.")
    else:
        copiar_txt_avulso(origem, pasta_obra)

    conversa = _conversa_extraida(pasta_obra)
    if conversa:
        mensagens = ler_conversa(conversa)

    documentos = extrair_pasta(pasta_obra / "02-projetos-pdf")
    if args.skip_keyframes:
        quadros: list[Path] = []
        print("Extração de quadros de vídeo não executada nesta rodada.")
    else:
        resultado_quadros = extrair_quadros(pasta_obra / "03-midias")
        quadros = [Path(item) for item in resultado_quadros.get("quadros", [])]
        if resultado_quadros.get("aviso"):
            print(resultado_quadros["aviso"])
        elif resultado_quadros.get("videos"):
            print(f"Quadros de vídeo: {len(quadros)}.")

    transcricoes = transcrever_pasta(
        pasta_obra / "03-midias",
        pasta_obra / "04-transcricoes",
        pular=args.skip_transcribe,
        modelo=args.whisper_model,
    )
    if transcricoes and all(item["status"] != "ok" for item in transcricoes):
        print("Transcrição local não executada. A fala dos áudios fica como dado não identificado.")

    analise = montar_analise(
        mensagens,
        fonte=origem.name,
        arquivos=_arquivos_da_obra(pasta_obra),
        documentos=documentos,
        transcricoes=transcricoes,
        quadros=quadros,
        overrides=sobrepor,
    )
    caminho_json = pasta_obra / "04-transcricoes" / "analise.json"
    antigo = ler_json(caminho_json) if caminho_json.exists() else None
    analise = _preservar(analise, antigo)
    _aplicar_preferencias(analise, config)
    escrever_json(caminho_json, analise)
    destino = _gravar(pasta_obra, analise, gerar_pdf)
    try:
        _anotar_relatorio(origem, args.sha, destino, pasta_obra)
    except Exception as erro:
        print(f"Aviso: o relatório foi gravado, mas o registro local não atualizou: {erro}")
    print("Análise gravada em:")
    print(caminho_json)
    return 0


def _listar(config: dict | None, downloads: str | None) -> int:
    import registro
    from descoberta import descobrir_em, pastas_de_busca

    if downloads:
        # Pasta indicada na linha de comando: procura só nela (e na pasta da Armanilux).
        raizes = [Path(downloads)] if Path(downloads).is_dir() else []
        if config and config.get("pasta_raiz") and Path(config["pasta_raiz"]).is_dir():
            raizes.append(Path(config["pasta_raiz"]))
    else:
        raizes = pastas_de_busca(config=config)
    dados = registro.sincronizar(descobrir_em(raizes))
    print(registro.formatar_lista(dados))
    return 0


def _numeros(valores: list[str] | None) -> list[int]:
    saida: list[int] = []
    for valor in valores or []:
        for pedaco in str(valor).replace(" ", ",").split(","):
            if pedaco.strip():
                saida.append(int(pedaco))
    return saida


def _processar_escolha(args, config: dict | None) -> int:
    """Gera o relatório das conversas escolhidas, uma de cada vez."""
    import registro

    dados = registro.carregar()
    if not dados["fila"]:
        _listar(config, args.downloads)
        dados = registro.carregar()
    try:
        shas = registro.escolher(dados, _numeros(args.indice), args.todas)
    except (IndexError, ValueError):
        print("Esse número não está na lista. Rode --listar e escolha um número que apareceu.")
        return 2
    if not shas:
        print("Nenhuma conversa escolhida.")
        return 2
    resultado = 0
    for posicao, sha in enumerate(shas, start=1):
        item = dados["exportacoes"][sha]
        print(f"\n=== Conversa {posicao} de {len(shas)}: Obra {item.get('numero') or '?'} – {item.get('cliente') or '?'} ===")
        argv = ["--sha", sha]
        argv += ["--chat" if item.get("tipo") == "txt" else "--zip", item["caminho"]]
        for opcao, valor in (("--workspace", args.workspace), ("--downloads", args.downloads)):
            if valor:
                argv += [opcao, valor]
        for opcao, ligada in (("--skip-transcribe", args.skip_transcribe), ("--skip-keyframes", args.skip_keyframes), ("--pdf", args.pdf)):
            if ligada:
                argv.append(opcao)
        if item.get("numero"):
            argv += ["--obra", item["numero"]]
        if item.get("cliente"):
            argv += ["--cliente", item["cliente"]]
        try:
            codigo = executar(argv)
        except Exception as erro:
            print(f"Não foi possível concluir esta conversa: {erro}")
            codigo = 1
        resultado = resultado or codigo
    return resultado


def _concluir(args) -> int:
    import registro

    dados = registro.carregar()
    prontos = [s for s, i in dados["exportacoes"].items() if i.get("status") == registro.GERADO]
    prontos.sort(key=lambda s: dados["exportacoes"][s].get("atualizado_em", ""))
    try:
        numeros = _numeros(args.indice)
        shas = prontos if args.todas else [prontos[n - 1] for n in numeros]
    except (IndexError, ValueError):
        print("Esse número não está na lista de relatórios prontos.")
        return 2
    if not shas:
        print("Não há relatório gerado para concluir. Diga qual conversa a pessoa aprovou.")
        return 2
    for sha in shas:
        destino = registro.concluir(sha, copiar=args.copiar)
        print(f"Concluída. Conversa guardada em:\n{destino}")
    return 0


def _marcar_andamento(origem: Path, sha: str | None, identidade: dict) -> None:
    import registro
    from descoberta import examinar_arquivo

    sha = sha or registro.sha256_arquivo(origem)
    if sha not in registro.carregar()["exportacoes"]:
        achado = examinar_arquivo(origem) or {
            "tipo": "zip" if origem.suffix.lower() == ".zip" else "txt",
            "caminho": str(origem),
            "nome": origem.name,
        }
        achado["numero"] = identidade["numero"]
        achado["cliente"] = identidade["cliente"]
        registro.sincronizar([achado])
    registro.marcar_andamento(sha)


def _anotar_relatorio(origem: Path, sha: str | None, destino: Path, pasta_obra: Path) -> None:
    import re

    import registro

    sha = sha or registro.sha256_arquivo(origem)
    achado = re.search(r"-v(\d+)\.docx$", destino.name, re.IGNORECASE)
    registro.registrar_relatorio(sha, str(destino), int(achado.group(1)) if achado else 1, str(pasta_obra))


def main(argv: list[str] | None = None) -> int:
    try:
        return executar(argv)
    except Exception as erro:
        print(f"Não foi possível concluir o relatório: {erro}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
