"""Gera o Relatório Cronológico de Obra a partir do export do WhatsApp.

Uso típico, no Windows, com o Python do instalador:

  %USERPROFILE%\\.armanilux-relatorio\\venv\\Scripts\\python.exe run_pipeline.py --zip "C:\\Users\\...\\WhatsApp.zip"

Tudo acontece neste computador. Não há chamada de API.
"""

from __future__ import annotations

import sys

import argparse
import time
from pathlib import Path

from analyze import (
    aplicar_ajustes,
    completar_relato,
    intervalos_marcos_de,
    juntar_lacunas,
    lacunas_automaticas,
    montar_analise,
)
from build_charts import grafico_barras, grafico_gantt
from build_docx import montar_docx, proxima_versao
from entrega import converter_pdf, copiar_para_link, formato_entrega
from common import configurar_saida, escrever_json, ler_json, nome_seguro
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
    "eventos_adicionais",
    "obra_ajustes",
    "pendencias_revisadas",
    "diagnostico_prompt",
    "gargalos_personalizados",
    "responsabilidades_personalizadas",
    "produtividade_personalizada",
    "lacunas_adicionais",
    "prazos_contratuais",
    "pontos_criticos",
    "impactos_prazo",
)


def instalador_do_preparo() -> Path:
    """O instalador da skill de preparo, que fica ao lado desta skill na mesma pasta de skills
    (Codex, Claude Code ou outra). Não depende de onde o aplicativo guarda as skills."""
    return Path(__file__).resolve().parents[2] / "preparar-projeto-armanilux" / "scripts" / "instalar.ps1"


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
        if instalador_do_preparo().is_file():
            print(f"Se ela já estiver instalada, o instalador é {instalador_do_preparo()}")
        return False
    return True


def _conversa_extraida(pasta_obra: Path, analise: dict | None = None) -> Path | None:
    """A conversa da última exportação lida. analise.json guarda qual é ("conversa").
    Sem essa marca (análise antiga), vale o .txt gravado por último, não o maior:
    exportar sem mídia deixa o arquivo novo menor que o antigo."""
    marcada = (analise or {}).get("conversa")
    if marcada and (pasta_obra / marcada).is_file():
        return pasta_obra / marcada
    pasta = pasta_obra / "01-conversas"
    if not pasta.exists():
        return None
    candidatos = [item for item in pasta.glob("*.txt") if item.name.lower() not in {"origem.txt", "leia-me.txt"}]
    if not candidatos:
        return None
    return max(candidatos, key=lambda item: (item.stat().st_mtime, item.stat().st_size))


def _conversa_do_zip(pasta_obra: Path, resumo: dict, nome_txt: str) -> Path | None:
    """Onde o .txt da exportação que acabou de ser lida foi parar dentro da obra."""
    for item in resumo["arquivos"]:
        if nome_seguro(item["origem"]) == nome_txt:
            return pasta_obra / item["destino"]
    return None


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
    """Conversa nova de uma obra que já tem análise: guarda o trabalho da revisão.
    "revisado" não passa adiante: há mensagens novas, então o relatório volta a ser rascunho."""
    if not antigo:
        return novo
    for chave in CHAVES_PRESERVAR:
        if antigo.get(chave):
            novo[chave] = antigo[chave]
    if antigo.get("revisado"):
        print(
            "Esta obra já tinha relatório revisado. Com a conversa nova, o relatório volta a ser rascunho: "
            "confira as mensagens novas e a conclusão, e grave \"revisado\": true de novo."
        )
    if novo.get("ajustes_eventos"):
        novo["eventos"] = aplicar_ajustes(novo["eventos"], novo["ajustes_eventos"])
    return completar_relato(novo)


def _conferir(pasta_obra: Path, analise: dict) -> None:
    """Confere cada fato contra a conversa e grava 04-transcricoes/verificacao.md."""
    from verificacao import confirmado, escrever_verificacao, verificar_eventos

    conversa = _conversa_extraida(pasta_obra, analise)
    if conversa is None:
        print("Aviso: sem a conversa em 01-conversas, a conferência dos fatos não rodou.")
        return
    try:
        itens = verificar_eventos(
            analise.get("eventos") or [],
            ler_conversa(conversa),
            analise.get("transcricoes") or [],
            [caminho.name for caminho in _arquivos_da_obra(pasta_obra)],
        )
        destino = escrever_verificacao(itens, pasta_obra / "04-transcricoes" / "verificacao.md")
    except Exception as erro:  # a conferência ajuda, mas não pode impedir o Word
        print(f"Aviso: não consegui conferir os fatos: {erro}")
        return
    problemas = sum(1 for item in itens if not confirmado(item))
    print(f"Conferência dos fatos: {len(itens) - problemas} de {len(itens)} batem com o grupo. Detalhes: {destino}")


def _lacunas_se_faltar(pasta_obra: Path, analise: dict) -> None:
    """analise.json de versão antiga não tem as lacunas automáticas: calcula a partir da conversa."""
    if "lacunas_automaticas" in analise:
        return
    conversa = _conversa_extraida(pasta_obra, analise)
    if conversa is None:
        return
    analise["lacunas_automaticas"] = lacunas_automaticas(
        ler_conversa(conversa), analise.get("documentos_texto") or [], analise.get("transcricoes") or []
    )
    analise["lacunas"] = juntar_lacunas(analise)


def mostrar_no_explorer(arquivo: Path) -> None:
    """Abre a pasta do relatório com o Word já selecionado, para ninguém precisar do caminho."""
    import subprocess

    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer", f"/select,{arquivo}"])
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(arquivo)])
    else:
        subprocess.Popen(["xdg-open", str(arquivo.parent)])


def _avisar_se_cortada(mensagens) -> None:
    from analyze import exportacao_parece_cortada
    from common import formatar_data

    if exportacao_parece_cortada(mensagens):
        print(
            f"Aviso: a conversa parece cortada. Ela começa em {formatar_data(mensagens[0].data.isoformat())}, "
            "sem o aviso de criptografia nem a criação do grupo. O WhatsApp corta conversas muito grandes "
            "(cerca de 10 mil mensagens com mídia, 40 mil sem mídia). Se o grupo começou antes, exporte de novo "
            "sem mídia. O relatório registra isso como lacuna."
        )


def _avisar_prazos(analise: dict) -> None:
    """Prazo precisa de fonte escrita antes do período que ele mede; senão não prova a regra da época."""
    from common import formatar_data

    fontes = {p.get("descricao", ""): p.get("fonte_data") for p in analise.get("prazos_contratuais") or []}
    for item in analise.get("confronto_contrato") or []:
        if item.get("fonte_posterior"):
            print(
                f"Aviso de prazo: \"{item['descricao']}\": fonte de {formatar_data(fontes.get(item['descricao']))}, "
                f"depois do início do período ({formatar_data(item['inicio'])})."
            )
        elif item.get("sem_data_da_fonte"):
            print(f"Aviso de prazo: \"{item['descricao']}\": sem fonte_data.")


def _gravar(pasta_obra: Path, analise: dict, config: dict | None = None, forcar_pdf: bool = False, mostrar: bool = False) -> Path:
    _conferir(pasta_obra, analise)
    _avisar_prazos(analise)
    figuras = pasta_obra / "05-relatorios" / "figuras"
    if "intervalos_marcos" in analise:
        marcos = analise["intervalos_marcos"]
    else:  # analise.json antigo, remontado sem --recalcular
        marcos = intervalos_marcos_de(analise.get("eventos") or [])[0]
    barras = grafico_barras(marcos, figuras / "dias-uteis.png")
    gantt = grafico_gantt(analise.get("eventos") or [], figuras / "gantt.png")
    pasta = pasta_obra / "05-relatorios"
    numero = analise["obra"].get("numero") or "sem-numero"
    rascunho = not analise.get("revisado")
    versao = analise.get("versao")
    copia = 1
    while True:
        destino = proxima_versao(pasta, numero, rascunho=rascunho, copia=copia, versao=versao)
        try:
            montar_docx(analise, destino, barras, gantt)
            break
        except PermissionError:
            if not rascunho:
                # A versão final é sempre o mesmo vN: não grava cópia ao lado, pede para fechar.
                raise RuntimeError(
                    f"o arquivo {destino.name} está aberto (provavelmente no Word). Feche o arquivo e remonte."
                ) from None
            # Rascunho aberto no Word: o Windows não deixa regravar. Grava uma cópia ao lado.
            if copia >= 20:
                raise
            print(f"O arquivo {destino.name} está aberto (provavelmente no Word). Gravei outra cópia.")
            copia += 1
    if versao is None:
        _guardar_versao(pasta_obra, analise, _numero_da_versao(destino))
    if not rascunho:
        _arquivar_rascunhos(pasta, destino)
    formato = formato_entrega(config)
    quer_pdf = forcar_pdf or formato in ("pdf", "link")
    pdf = None
    if quer_pdf:
        print("Fazendo o PDF (pode levar até 1 minuto)...", flush=True)
        pdf = converter_pdf(destino)
    print(f"Relatório gravado em:\n{destino}")
    if pdf:
        print(f"PDF gravado em:\n{pdf}")
    elif quer_pdf:
        print(
            "O PDF não saiu. O arquivo para enviar é o Word. Se o PDF estiver aberto, feche e remonte. "
            "Se o computador não tem o Microsoft Word nem o LibreOffice, rode de novo $preparar-projeto-armanilux "
            "e escolha PDF: ele instala o LibreOffice."
        )
    else:
        print("O arquivo para enviar é o Word.")
    pendencias = analise.get("pendencias") or []
    if pendencias:
        print(f"Pendências com status Pendente: {len(pendencias)}.")
    # Linha fixa para o agente achar o arquivo e entregá-lo na conversa.
    print(f"RELATORIO_WORD: {destino}")
    if pdf:
        print(f"RELATORIO_PDF: {pdf}")
    if formato == "link":
        _copiar_para_nuvem(pasta_obra, pdf or destino, (config or {}).get("pasta_link"), rascunho)
    if mostrar:
        try:
            mostrar_no_explorer(destino)
        except Exception as erro:  # abrir a pasta ajuda, mas não pode derrubar o relatório
            print(f"Aviso: não consegui abrir a pasta: {erro}")
    return destino


def _numero_da_versao(arquivo: Path) -> int:
    import re

    achado = re.search(r"-v(\d+)(?:-rascunho(?:-\d+)?)?\.docx$", arquivo.name, re.IGNORECASE)
    return int(achado.group(1)) if achado else 1


def _guardar_versao(pasta_obra: Path, analise: dict, versao: int) -> None:
    """Fixa o número da versão em analise.json: remontar depois de "revisado": true regrava o
    mesmo vN (corrigir um erro não gasta versão). Só uma conversa nova abre a versão seguinte."""
    analise["versao"] = versao
    caminho = pasta_obra / "04-transcricoes" / "analise.json"
    if caminho.exists():
        salvo = ler_json(caminho)
        salvo["versao"] = versao
        escrever_json(caminho, salvo)


def _arquivar_rascunhos(pasta: Path, final: Path) -> None:
    """Com a versão final gravada, os rascunhos dela saem de perto para ninguém enviar o errado."""
    import os

    prefixo = final.stem + "-rascunho"
    destino = pasta / "rascunhos"
    for antigo in pasta.glob(prefixo + "*"):
        if not antigo.is_file():
            continue
        destino.mkdir(exist_ok=True)
        alvo = destino / antigo.name
        indice = 2
        while alvo.exists():  # nada é apagado: rascunho com o mesmo nome ganha -2, -3...
            alvo = destino / f"{antigo.stem}-{indice}{antigo.suffix}"
            indice += 1
        try:
            os.rename(antigo, alvo)
        except OSError:
            print(f"Aviso: não consegui mover o rascunho {antigo.name} para a pasta rascunhos (está aberto?).")


def _copiar_para_nuvem(pasta_obra: Path, arquivo: Path, pasta_link: str | None, rascunho: bool) -> None:
    if rascunho:
        print("Rascunho não vai para a pasta da nuvem. Quando o relatório for revisado, a versão final vai.")
        return
    if not pasta_link:
        print("Aviso: a entrega por link não tem pasta da nuvem. Rode de novo $preparar-projeto-armanilux.")
        return
    try:
        copia = copiar_para_link(arquivo, Path(pasta_link), pasta_obra.name)
    except OSError:
        print(
            f"Aviso: não consegui copiar o relatório para a pasta da nuvem ({pasta_link}). "
            "Se o arquivo estiver aberto lá, feche e remonte. Se a pasta não existe mais, rode de novo $preparar-projeto-armanilux."
        )
        return
    print(
        "Cópia na pasta da nuvem. Para mandar por link: no OneDrive ou no Google Drive, "
        "clique com o botão direito no arquivo, Compartilhar, e escolha só as pessoas que podem ver."
    )
    print(f"RELATORIO_LINK: {copia}")


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
    if analise.get("ajustes_eventos"):
        # Correções feitas pela revisão (trocar etapa, remover) valem também na remontagem.
        analise["eventos"] = aplicar_ajustes(list(analise.get("eventos") or []), analise["ajustes_eventos"])
    _lacunas_se_faltar(pasta, analise)
    if args.recalcular:
        analise = completar_relato(analise)
        escrever_json(caminho, analise)
    _aplicar_preferencias(analise, config)
    _gravar(pasta, analise, config, args.pdf, args.mostrar)
    return 0


class _Relogio:
    """Mostra quanto cada etapa levou, para a pessoa ver que o programa não travou."""

    def __init__(self) -> None:
        self.inicio = self.ultimo = time.time()

    def marca(self, texto: str) -> None:
        agora = time.time()
        print(f"  [{agora - self.ultimo:.0f}s] {texto}", flush=True)
        self.ultimo = agora


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
    parser.add_argument("--pdf", action="store_true", help="Faz também o PDF, mesmo que o preparo tenha escolhido só Word")
    parser.add_argument("--mostrar", action="store_true", help="Abre a pasta do relatório com o Word selecionado")
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

    relogio = _Relogio()
    print(f"Exportação encontrada ({tipo}): {origem}", flush=True)
    if tipo == "zip":
        resumo = None
        # A extração de verdade ocorre depois que a pasta da obra existe.
        from organize_export import ler_txt_do_zip

        lido = ler_txt_do_zip(origem)
        if not lido:
            print("O zip abriu, mas não há conversa do WhatsApp dentro dele. Exporte de novo pelo celular.")
            return 2
        nome_txt, texto = lido
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
        conversa = _conversa_do_zip(pasta_obra, resumo, nome_txt)
        relogio.marca("arquivos extraídos")
        novos = len(resumo["arquivos"]) - resumo.get("ja_existiam", 0)
        print(f"Arquivos organizados: {len(resumo['arquivos'])} ({novos} novos, {resumo.get('ja_existiam', 0)} já estavam na obra).")
        if resumo["grande"]:
            print(
                "Aviso: o zip passa de 500 MB. A leitura é local e em partes. "
                "Se o computador ficar lento, na próxima vez exporte o grupo sem mídia "
                "e copie só as fotos que importam para a pasta 03-midias."
            )
        if resumo["ignorados"]:
            print(f"Itens ignorados por caminho inseguro: {len(resumo['ignorados'])}.")
    else:
        conversa = copiar_txt_avulso(origem, pasta_obra)

    if conversa and conversa.is_file():
        mensagens = ler_conversa(conversa)
        print(f"Conversa usada: {conversa.name}")
    _avisar_se_cortada(mensagens)

    documentos = extrair_pasta(pasta_obra / "02-projetos-pdf")
    relogio.marca(f"{len(documentos)} documentos lidos")
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

    try:
        from folhas_de_contato import gerar as gerar_folhas

        folhas = gerar_folhas(pasta_obra)
        if folhas:
            print(f"Folhas de contato para revisar as imagens: {len(folhas)} (em 04-transcricoes/folhas-de-contato).")
    except Exception as erro:
        print(f"Aviso: não consegui montar as folhas de contato: {erro}")
    relogio.marca("vídeos vistos")
    transcricoes = transcrever_pasta(
        pasta_obra / "03-midias",
        pasta_obra / "04-transcricoes",
        pular=args.skip_transcribe,
        modelo=args.whisper_model,
        progresso=lambda linha: print(linha, flush=True),
    )
    if transcricoes and all(item["status"] != "ok" for item in transcricoes):
        print("Transcrição local não executada. A fala dos áudios fica como dado não identificado.")

    relogio.marca("áudios e vídeos tratados")
    analise = montar_analise(
        mensagens,
        fonte=origem.name,
        arquivos=_arquivos_da_obra(pasta_obra),
        documentos=documentos,
        transcricoes=transcricoes,
        quadros=quadros,
        overrides=sobrepor,
    )
    if conversa and conversa.is_file():
        analise["conversa"] = conversa.relative_to(pasta_obra).as_posix()
    caminho_json = pasta_obra / "04-transcricoes" / "analise.json"
    antigo = ler_json(caminho_json) if caminho_json.exists() else None
    analise = _preservar(analise, antigo)
    _aplicar_preferencias(analise, config)
    escrever_json(caminho_json, analise)
    try:
        from candidatos import escrever as escrever_candidatos

        candidatos = escrever_candidatos(mensagens, pasta_obra / "04-transcricoes" / "candidatos-por-etapa.md")
        print(f"Candidatos por etapa, para revisar: {candidatos}")
    except Exception as erro:
        print(f"Aviso: não consegui montar os candidatos por etapa: {erro}")
    relogio.marca("conversa analisada")
    destino = _gravar(pasta_obra, analise, config, args.pdf, args.mostrar)
    relogio.marca("Word montado")
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
        for opcao, ligada in (("--skip-transcribe", args.skip_transcribe), ("--skip-keyframes", args.skip_keyframes), ("--pdf", args.pdf), ("--mostrar", args.mostrar)):
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
    import registro

    sha = sha or registro.sha256_arquivo(origem)
    registro.registrar_relatorio(sha, str(destino), _numero_da_versao(destino), str(pasta_obra))


def main(argv: list[str] | None = None) -> int:
    try:
        return executar(argv)
    except Exception as erro:
        print(f"Não foi possível concluir o relatório: {erro}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
