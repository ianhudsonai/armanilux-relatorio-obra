"""Classifica a conversa nas etapas A–L (não existe etapa K) e monta o relato.

A classificação por palavras é a primeira versão. O Codex revisa `analise.json`
e pode corrigir a etapa de um registro. Os números de dias úteis saem sempre
do script, não de conta de cabeça.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from business_days import dias_uteis_entre, leitura_intervalo
from common import (
    CONVENCAO_DIAS_UTEIS,
    DADO,
    EXT_DOCUMENTO,
    EXT_IMAGEM,
    EXT_VIDEO,
    formatar_data,
    normalizar,
    tipo_midia,
)
from parse_whatsapp import MARCADOR_MIDIA_OCULTA, Mensagem, texto_util

ORDEM = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "L")


def _posicao(codigo: str) -> int:
    try:
        return ORDEM.index(codigo)
    except ValueError:
        return 99

TITULOS = {
    "A": "A – Aprovação de chapas",
    "B": "B – Solicitação de vistas e/ou visitas “in loco”",
    "C": "C – Data da medição “in loco”",
    "D": "D – Envio do projeto preliminar",
    "E": "E – Solicitações de revisões de projetos",
    "F": "F – Envios de projetos preliminares (revisados)",
    "G": "G – Aprovações dos projetos (cliente / engenharia / arquitetura)",
    "H": "H – Data das entregas dos materiais na obra",
    "I": "I – Data da entrada da equipe de instalações",
    "J": "J – Ocorrências e interferências de obra que impactaram a instalação",
    "L": "L – Data da conclusão dos serviços e validação final",
}

# A primeira etapa principal que casar é a escolhida. J pode acompanhar outra.
_PRINCIPAL = (
    ("L", ("validacao final", "servicos de instalacao concluid", "conclusao dos servicos", "instalacao concluida")),
    ("G", ("projeto aprovado", "aprovado pela engenharia", "aprovado pela arquitetura", "aprovamos o projeto")),
    ("F", ("projeto revisado", "envio o projeto revisado", "revisado r1", "revisado r2")),
    ("E", ("solicito revis", "solicito nova revis", "pedido de revis", "revisao do projeto")),
    ("D", ("projeto preliminar", "envio o projeto")),
    ("C", ("medicao in loco", "medicao realizada", "medimos ")),
    ("I", ("equipe de instalacao entrou", "entrada da equipe", "equipe entrou na obra", "inicio da instalacao")),
    ("H", ("material entregue", "entrega do material", "entrega das chapas", "chegou o material")),
    ("B", ("visita in loco", "solicito uma visita", "agendar visita", "vistoria")),
    ("A", ("aprovo as chapas", "aprovacao das chapas", "chapas do lote", "amostra de pedra")),
)
_INTERFERENCIA = (
    "interferencia",
    "nao liberou",
    "contrapiso irregular",
    "ponto de agua",
    "ponto hidraulico",
    "aguardando a marcenaria",
    "frente liberada",
    "instalacao ficou impedida",
    "impediu a instalacao",
)


# Cor de fundo da linha, como no relatório aprovado: salmão = reprocesso, amarelo = ocioso.
_REPROCESSO = (
    # "revis" sozinho pegaria "projeto revisado" (etapa F andando); só o pedido de nova revisão é reprocesso.
    "nova revis", "outra revis", "revisao apos", "solicito revis", "refaz", "refeit", "refacao", "retrabalho", "quebr", "trinc", "danific",
    "retirad", "substitui", "corrig", "mudanca apos", "alteracao apos",
)
_OCIOSO = (
    "nao realizad", "nao foi realizad", "aguardand", "pendente", "sem frente", "nao liber",
    "parad", "adiad", "remarc", "sem retorno", "cancelad",
)
# Mensagem que só programa o fato ("programado para amanhã"): não é data realizada.
_PROGRAMADO = (
    "programad", "programando", "agendad", "agendando", "agendament", "agendar",
    "previst", "previsao", "para amanha", "para a proxima",
)
_ETAPAS_COM_PROGRAMACAO = {"A", "C", "H", "I", "L"}


def diz_programado(texto: str) -> bool:
    """O texto fala em programação ("programado para amanhã", "agendamento da visita")."""
    return bool(_COMECA_PALAVRA(_PROGRAMADO).search(normalizar(texto or "")))
# Intervalo entre marcos acima disto sai em vermelho na Análise de Prazos.
LIMITE_INTERVALO_LONGO = 20


def destaque_automatico(etapa: str, texto: str) -> str:
    """Primeira leitura da cor da linha. A revisão pode trocar com "destaque" no evento."""
    # Etapa E é, por definição, pedido de revisão: sempre reprocesso.
    base = normalizar(texto)
    if etapa == "E" or _COMECA_PALAVRA(_REPROCESSO).search(base):
        return "reprocesso"
    if _COMECA_PALAVRA(_OCIOSO).search(base):
        return "ocioso"
    return ""


def _COMECA_PALAVRA(chaves: tuple[str, ...]) -> re.Pattern:
    """Chave casa no começo de uma palavra: "parad" pega "parada", não "preparada"."""
    return re.compile(r"\b(?:" + "|".join(re.escape(chave) for chave in chaves) + ")")


def classificar_etapas(texto: str) -> list[str]:
    base = normalizar(texto)
    etapas: list[str] = []
    for codigo, chaves in _PRINCIPAL:
        if any(chave in base for chave in chaves):
            etapas.append(codigo)
            break
    if any(chave in base for chave in _INTERFERENCIA):
        etapas.append("J")
    return etapas


def _campo(texto: str, padrao: str) -> str:
    achado = re.search(padrao, texto, flags=re.IGNORECASE)
    if not achado:
        return ""
    return " ".join(achado.group(1).split()).strip(" .")


def _endereco(texto: str) -> str:
    """Endereço até o fim da frase, sem cortar em 'R.' ou 'Av.' (abreviação)."""
    achado = re.search(r"Endere[cç]o:\s*([^\n]+)", texto, flags=re.IGNORECASE)
    if not achado:
        return ""
    linha = achado.group(1)
    corte = re.search(r"(?:(?<=[A-Za-zÀ-ÿ]{4})|(?<=\d))\.(?:\s|$)", linha)
    if corte:
        linha = linha[: corte.start()]
    return " ".join(linha.split()).strip(" .")


def metadados_da_conversa(mensagens: list[Mensagem], fonte: str, overrides: dict | None = None) -> dict:
    texto = "\n".join(item.texto for item in mensagens)
    obra = {
        "numero": _campo(texto, r"Obra\s+([0-9]+(?:\.[0-9]+)*)"),
        "cliente": _campo(texto, r"Cliente:\s*([^.\n]+)"),
        "construtora": _campo(texto, r"Construtora:\s*([^.\n]+)"),
        "engenheiro": _campo(texto, r"Engenheiro:\s*([^.\n]+)"),
        "arquitetura": _campo(texto, r"Arquitetura:\s*([^.\n]+)"),
        "responsavel_armanilux": _campo(texto, r"Respons[aá]vel Armanilux:\s*([^.\n]+)"),
        "endereco": _endereco(texto),
        "prazo_contratual": "",
        "fonte": fonte,
    }
    for chave, valor in (overrides or {}).items():
        if valor:
            obra[chave] = valor
    # Mensagem colada de outra conversa não muda o período do grupo.
    datas = [item.data for item in mensagens if not item.encaminhada_por]
    if datas:
        obra["periodo_inicio"] = min(datas).isoformat()
        obra["periodo_fim"] = max(datas).isoformat()
    else:
        obra["periodo_inicio"] = ""
        obra["periodo_fim"] = ""
    return obra


def _impacto(texto: str) -> str:
    base = normalizar(texto)
    if "frente liberada" in base:
        return (
            "A frente voltou a permitir a instalação. O grupo não informa quantas "
            "horas a equipe ficou parada; essa duração é dado não identificado."
        )
    if "contrapiso irregular" in base or "instalacao ficou impedida" in base:
        return (
            "O assentamento da pedra nesse trecho ficou impedido até a regularização "
            "do contrapiso. O efeito é localizado na produtividade da área citada."
        )
    if "ponto de agua" in base or "ponto hidraulico" in base:
        return (
            "A peça ligada a esse ponto ficou condicionada ao reposicionamento feito "
            "pela obra. Sem o ponto no lugar, a instalação da peça não fecha."
        )
    if "nao liberou" in base or "aguardando a marcenaria" in base:
        return (
            "Não havia frente livre nesse ambiente. A espera decorre da condição "
            "registrada no grupo (marcenaria ou liberação da obra)."
        )
    if "interferencia" in base:
        return (
            "A interferência afetou o ritmo da instalação no trecho citado. "
            "Dia que o grupo não quantifica permanece dado não identificado."
        )
    return "Impacto registrado no grupo, sem quantificação além das datas."


def _pendencias(mensagens: list[Mensagem]) -> list[dict]:
    """Só o que o grupo diz claramente que está em aberto. Mensagem longa não vira pendência."""
    itens: list[dict] = []
    vistos: set[str] = set()
    for mensagem in mensagens:
        base = normalizar(mensagem.texto)
        texto_curto = texto_util(mensagem)
        if "termo assinado" in base or "devolver o termo" in base:
            texto = "Devolução do termo de entrega assinado pelo cliente."
        elif len(texto_curto) <= 140 and not texto_curto.endswith("?") and re.search(r"\b(ainda )?falta(m)?\b|\bpendente\b|\bpendencia\b", base):
            texto = texto_curto
        else:
            continue
        if texto not in vistos:
            vistos.add(texto)
            itens.append({"item": texto, "status": "Pendente"})
    return itens[:12]


def _indice_arquivos(caminhos: list[Path]) -> dict[str, Path]:
    return {caminho.name.lower(): caminho for caminho in caminhos}


def _ligar_anexos(mensagem: Mensagem, indice: dict[str, Path]) -> list[str]:
    nomes = []
    for anexo in mensagem.anexos:
        caminho = indice.get(anexo.lower())
        nomes.append(caminho.name if caminho else anexo)
    return nomes


def _transcricao_de(nome: str, transcricoes: list[dict]) -> dict | None:
    for item in transcricoes:
        if item.get("arquivo", "").lower() == nome.lower():
            return item
    return None


_MARCADOR_ANEXO = re.compile(
    r"<(?:anexad[oa]|anexo|attached):\s*[^>]+>|"
    r"\S+\.(?:pdf|docx?|xlsx?|jpe?g|png|webp|opus|ogg|mp3|m4a|wav|mp4|mov)"
    r"\s+\((?:arquivo anexado|file attached)\)",
    re.IGNORECASE,
)
_FORA_DA_EXPORTACAO = "(arquivo não incluído na exportação; conteúdo: dado não identificado)."


def _so_o_nome(mensagem: Mensagem) -> bool:
    """Documento exportado sem mídia: o texto é só '<Mídia oculta>' e o nome do arquivo."""
    return mensagem.midia_omitida and bool(mensagem.anexos) and bool(
        MARCADOR_MIDIA_OCULTA.match(mensagem.texto)
    )


def _ocorrencia(mensagem: Mensagem, arquivos: list[str], transcricoes: list[dict]) -> str:
    if _so_o_nome(mensagem):
        corpo = MARCADOR_MIDIA_OCULTA.sub("", texto_util(mensagem), count=1).replace(mensagem.anexos[0], "", 1)

    else:
        corpo = _MARCADOR_ANEXO.sub("", texto_util(mensagem))
    corpo = " ".join(corpo.split())
    if len(corpo) > 700:
        corpo = corpo[:700].rstrip() + "…"
    if mensagem.autor:
        partes = [f"{mensagem.autor}: {corpo}" if corpo else f"{mensagem.autor}:"]
    else:
        partes = [corpo] if corpo else []
    if mensagem.encaminhada_por and mensagem.encaminhada_em:
        quando = mensagem.encaminhada_em.strftime("%d/%m/%Y %H:%M")
        partes.append(f"(encaminhada no grupo por {mensagem.encaminhada_por} em {quando})")
    midias = []
    documentos = []
    for nome in arquivos:
        if Path(nome).suffix.lower() in EXT_DOCUMENTO:
            documentos.append(nome)
        else:
            midias.append(nome)
    if midias:
        partes.append("Mídia: " + ", ".join(midias))
    for nome in documentos:
        partes.append("Documento: " + nome)
    if _so_o_nome(mensagem):
        rotulo = "Documento" if Path(mensagem.anexos[0]).suffix.lower() in EXT_DOCUMENTO else "Mídia"
        partes.append(f"{rotulo}: {mensagem.anexos[0]} {_FORA_DA_EXPORTACAO}")
    elif mensagem.midia_omitida and not arquivos:
        partes.append("Mídia: dado não identificado (mídia omitida na exportação).")
    for nome in midias:
        transcricao = _transcricao_de(nome, transcricoes)
        if not transcricao:
            continue
        if transcricao.get("status") == "ok" and transcricao.get("texto"):
            trecho = transcricao["texto"]
            if len(trecho) > 400:
                trecho = trecho[:400].rstrip() + "…"
            partes.append(f"Transcrição: {trecho}")
        elif transcricao.get("status") == "ok":
            partes.append("Transcrição: dado não identificado (áudio sem fala reconhecida).")
        else:
            partes.append("Transcrição: dado não identificado (transcrição local não executada).")
    return " ".join(partes)


def extrair_eventos(
    mensagens: list[Mensagem],
    arquivos: list[Path],
    transcricoes: list[dict],
) -> list[dict]:
    indice = _indice_arquivos(arquivos)
    eventos = []
    for mensagem in mensagens:
        if mensagem.sistema:
            continue
        etapas = classificar_etapas(mensagem.texto)
        if not etapas:
            continue
        nomes = [] if _so_o_nome(mensagem) else _ligar_anexos(mensagem, indice)
        ocorrencia = _ocorrencia(mensagem, nomes, transcricoes)
        for etapa in etapas:
            eventos.append(
                {
                    "data": mensagem.data.isoformat(),
                    "hora": mensagem.hora,
                    "etapa": etapa,
                    "autor": mensagem.autor or "",
                    "ocorrencia": ocorrencia,
                    "impacto": _impacto(mensagem.texto) if etapa == "J" else "",
                    "midias": [nome for nome in nomes if Path(nome).suffix.lower() not in EXT_DOCUMENTO],
                    "documentos": [nome for nome in nomes if Path(nome).suffix.lower() in EXT_DOCUMENTO],
                }
            )
            if etapa in _ETAPAS_COM_PROGRAMACAO and diz_programado(mensagem.texto):
                eventos[-1]["programado"] = True
    eventos.sort(key=lambda item: (item["data"], item["hora"], _posicao(item["etapa"])))
    return eventos


def _intervalos(eventos: list[dict]) -> list[dict]:
    por_data: dict[str, set[str]] = {}
    for evento in eventos:
        por_data.setdefault(evento["data"], set()).add(evento["etapa"])
    datas = sorted(por_data)
    saida = []
    for esquerda, direita in zip(datas, datas[1:]):
        dias = dias_uteis_entre(date.fromisoformat(esquerda), date.fromisoformat(direita))
        if dias <= 0:
            continue
        leitura = leitura_intervalo(dias)
        origem = "/".join(sorted(por_data[esquerda], key=_posicao))
        destino = "/".join(sorted(por_data[direita], key=_posicao))
        saida.append(
            {
                "inicio": esquerda,
                "fim": direita,
                "dias_uteis": dias,
                "leitura": leitura,
                "rotulo": f"{origem}→{destino}",
                "de_etapas": sorted(por_data[esquerda], key=_posicao),
                "para_etapas": sorted(por_data[direita], key=_posicao),
            }
        )
    return saida


def data_do_fato(evento: dict) -> str:
    """Data em que o fato aconteceu: "data_evento" quando a mensagem conta um fato de outro dia,
    senão a data da mensagem. A tabela da etapa mostra a data da mensagem (rastreável no grupo)."""
    return evento.get("data_evento") or evento["data"]


def conta_como_marco(evento: dict) -> bool:
    """Fato realizado que pode marcar a etapa: não é só programação nem interferência,
    e na etapa L só a conclusão marcada."""
    if evento.get("programado"):
        return False
    if evento["etapa"] == "L":
        return fecha_a_obra(evento)
    return True


def primeira_programacao(eventos: list[dict], etapa: str) -> str:
    """Data da primeira mensagem que só programou a etapa, ou ""."""
    datas = sorted(e["data"] for e in eventos if e["etapa"] == etapa and e.get("programado"))
    return datas[0] if datas else ""


def primeiros_marcos(eventos: list[dict]) -> dict[str, str]:
    """Primeira data realizada de cada etapa."""
    primeiros: dict[str, str] = {}
    for evento in eventos:
        if conta_como_marco(evento) and data_do_fato(evento) < primeiros.get(evento["etapa"], "9999"):
            primeiros[evento["etapa"]] = data_do_fato(evento)
    return primeiros


def intervalos_marcos_de(eventos: list[dict]) -> tuple[list[dict], dict]:
    """Marco = primeiro registro de cada etapa. Intervalos entre marcos em ordem de data,
    como na tabela do relatório aprovado, e a duração do primeiro ao último registro."""
    primeiros = primeiros_marcos(eventos)
    marcos = sorted(primeiros.items(), key=lambda par: (par[1], _posicao(par[0])))
    saida = []
    for (de, inicio), (para, fim) in zip(marcos, marcos[1:]):
        saida.append(
            {
                "de": de,
                "para": para,
                "inicio": inicio,
                "fim": fim,
                "dias_uteis": dias_uteis_entre(date.fromisoformat(inicio), date.fromisoformat(fim)),
            }
        )
        saida[-1]["longo"] = saida[-1]["dias_uteis"] > LIMITE_INTERVALO_LONGO
    datas = sorted(evento["data"] for evento in eventos)
    duracao = {}
    if datas:
        duracao = {
            "inicio": datas[0],
            "fim": datas[-1],
            "dias_uteis": dias_uteis_entre(date.fromisoformat(datas[0]), date.fromisoformat(datas[-1])),
        }
    return saida, duracao


def confronto_contrato(eventos: list[dict], prazos: list[dict]) -> list[dict]:
    """Cada prazo informado no grupo contra o realizado. Sem as duas datas, realizado é None
    (dado não identificado). O período vem de "inicio"/"fim" escritos na revisão ou do
    primeiro registro das etapas "de" e "para"."""
    primeiros = primeiros_marcos(eventos)
    saida = []
    for prazo in prazos or []:
        inicio = prazo.get("inicio") or primeiros.get(prazo.get("de", ""))
        fim = prazo.get("fim") or primeiros.get(prazo.get("para", ""))
        # Contrato que diz só "dias" conta dias corridos; a revisão marca "unidade": "dias_corridos".
        unidade = "dias_corridos" if prazo.get("unidade") == "dias_corridos" else "dias_uteis"
        realizado = None
        programado = bool(prazo.get("programado"))  # o fim só foi programado: sem realizado
        if inicio and fim and fim >= inicio and not programado:
            de, ate = date.fromisoformat(inicio), date.fromisoformat(fim)
            realizado = (ate - de).days if unidade == "dias_corridos" else dias_uteis_entre(de, ate)
        try:
            limite = int(float(str(prazo.get("limite_du")).replace(",", "."))) or None
        except ValueError:
            limite = None  # "a combinar", vazio: sem número, não há o que confrontar
        saida.append(
            {
                "descricao": prazo.get("descricao", ""),
                "limite_du": limite,
                "unidade": unidade,
                "inicio": inicio or "",
                "fim": fim or "",
                "realizado": realizado,
                "programado": programado,
                "excedeu": realizado is not None and limite is not None and realizado > limite,
                "fonte": prazo.get("fonte", ""),
                # Regra escrita depois do início do período não prova que valia na época.
                "fonte_posterior": bool(prazo.get("fonte_data") and inicio and prazo["fonte_data"] > inicio),
                "sem_data_da_fonte": not prazo.get("fonte_data"),
            }
        )
    return saida


def _desde_etapa_anterior(eventos: list[dict]) -> dict[str, dict]:
    resultado: dict[str, dict] = {}
    anterior: tuple[str, date] | None = None
    for codigo in ORDEM:
        datas = [date.fromisoformat(item["data"]) for item in eventos if item["etapa"] == codigo]
        if not datas:
            continue
        inicio = min(datas)
        fim = max(datas)
        if anterior is None:
            resultado[codigo] = {"tipo": "primeira"}
        elif inicio <= anterior[1]:
            resultado[codigo] = {
                "tipo": "sobreposicao",
                "etapa": anterior[0],
                "inicio_desta": inicio.isoformat(),
                "fim_anterior": anterior[1].isoformat(),
            }
        else:
            dias = dias_uteis_entre(anterior[1], inicio)
            resultado[codigo] = {
                "tipo": "intervalo",
                "etapa": anterior[0],
                "inicio": anterior[1].isoformat(),
                "fim": inicio.isoformat(),
                "dias_uteis": dias,
                "leitura": leitura_intervalo(dias),
            }
        anterior = (codigo, fim)
    return resultado


def _internos(eventos: list[dict], codigo: str) -> list[dict]:
    datas = sorted({item["data"] for item in eventos if item["etapa"] == codigo})
    saida = []
    for esquerda, direita in zip(datas, datas[1:]):
        dias = dias_uteis_entre(date.fromisoformat(esquerda), date.fromisoformat(direita))
        saida.append(
            {
                "inicio": esquerda,
                "fim": direita,
                "dias_uteis": dias,
                "leitura": leitura_intervalo(dias),
            }
        )
    return saida


def _rotulo_dias(dias: int) -> str:
    if dias == 1:
        return "1 dia útil"
    return f"{dias} dias úteis"


def _frase_intervalo(inicio: str, fim: str, dias: int, leitura: str) -> str:
    return f"de {formatar_data(inicio)} a {formatar_data(fim)}, {_rotulo_dias(dias)} ({leitura})"


def _texto_intervalos(codigo: str, internos: list[dict], desde: dict | None) -> str:
    partes = []
    if internos:
        partes.append(
            "Dentro da etapa: "
            + "; ".join(
                _frase_intervalo(item["inicio"], item["fim"], item["dias_uteis"], item["leitura"])
                for item in internos
            )
            + "."
        )
    else:
        partes.append("Dentro da etapa há um único marco; intervalo interno: dado não identificado.")
    if not desde or desde.get("tipo") == "primeira":
        partes.append("Não há etapa anterior com registro para comparar.")
    elif desde.get("tipo") == "sobreposicao":
        partes.append(
            f"A etapa {codigo} se entrelaça com a etapa {desde['etapa']}: "
            f"começa em {formatar_data(desde['inicio_desta'])} e a etapa {desde['etapa']} "
            f"ainda tem registro em {formatar_data(desde['fim_anterior'])}. "
            "Isso é intercalação de fluxo (em geral reprocesso ou interferência), "
            "não um intervalo de espera para somar."
        )
    else:
        partes.append(
            f"Desde a etapa {desde['etapa']}: "
            + _frase_intervalo(desde["inicio"], desde["fim"], desde["dias_uteis"], desde["leitura"])
            + ". Esse número é intervalo de calendário útil, não lançamento de atraso."
        )
    return " ".join(partes)


def _comentarios_etapa(
    codigo: str,
    eventos: list[dict],
    internos: list[dict],
    pendencias: list[dict],
) -> dict[str, str]:
    quantidade = len(eventos)
    intervalo_longo = any(item["dias_uteis"] >= 6 for item in internos)
    if codigo == "A":
        return {
            "ponto_critico": "dado não identificado.",
            "gargalo": "dado não identificado.",
            "avaliacao": (
                "A aprovação das chapas está datada e atribuída a quem escreveu no grupo. "
                "Lote não citado no texto é dado não identificado."
            ),
            "conclusao": "A chapa do lote informado foi aprovada no histórico e passa a ser a referência do projeto.",
        }
    if codigo == "B":
        return {
            "ponto_critico": "dado não identificado.",
            "gargalo": "dado não identificado.",
            "avaliacao": "O pedido de vista ou visita está separado da data em que a medição de fato ocorreu.",
            "conclusao": "Há solicitação de visita in loco. A medição, se ocorreu, está na etapa C.",
        }
    if codigo == "C":
        return {
            "ponto_critico": "dado não identificado.",
            "gargalo": "dado não identificado.",
            "avaliacao": (
                "A medição in loco está datada. Cota que só tenha sido dita em áudio, "
                "sem transcrição nesta versão, é dado não identificado."
            ),
            "conclusao": "Medição registrada na data do grupo.",
        }
    if codigo == "D":
        return {
            "ponto_critico": "dado não identificado.",
            "gargalo": "dado não identificado.",
            "avaliacao": (
                "O preliminar saiu depois da medição. O intervalo correspondente está "
                "na seção de dias úteis e não deve ser lido como culpa já atribuída."
            ),
            "conclusao": "Projeto preliminar enviado.",
        }
    if codigo == "E":
        reprocesso = quantidade >= 2 or intervalo_longo
        return {
            "ponto_critico": (
                "Houve mais de uma solicitação de revisão. Isso caracteriza reprocesso de projeto."
                if reprocesso
                else "Há pedido de revisão pontual."
            ),
            "gargalo": (
                "Pedidos em datas diferentes reabrem o desenho e empurram a aprovação."
                if reprocesso
                else "dado não identificado."
            ),
            "avaliacao": "Cada pedido ficou datado. Alteração que não está escrita no grupo é dado não identificado.",
            "conclusao": "As revisões pedidas estão identificadas e devem ser lidas junto com os envios da etapa F.",
        }
    if codigo == "F":
        return {
            "ponto_critico": (
                "Houve mais de um envio de projeto revisado."
                if quantidade >= 2
                else "dado não identificado."
            ),
            "gargalo": "dado não identificado." if quantidade < 2 else "Cada reenvio consome um ciclo de conferência.",
            "avaliacao": "O arquivo citado no grupo é a evidência do que foi enviado. Conteúdo que o arquivo não contenha é dado não identificado.",
            "conclusao": "Projeto revisado encaminhado, em resposta aos pedidos da etapa E.",
        }
    if codigo == "G":
        return {
            "ponto_critico": "dado não identificado.",
            "gargalo": "dado não identificado.",
            "avaliacao": (
                "A aprovação vale para quem a registrou (cliente, engenharia ou arquitetura). "
                "Aprovação ausente do texto é dado não identificado."
            ),
            "conclusao": "Projeto aprovado na data do registro. A espera até a entrega, se existir, aparece no intervalo seguinte.",
        }
    if codigo == "H":
        junto_com_interferencia = any("não liberou" in item["ocorrencia"] or "nao liberou" in normalizar(item["ocorrencia"]) for item in eventos)
        return {
            "ponto_critico": (
                "A entrega coincidiu com frente ainda não liberada."
                if junto_com_interferencia
                else "dado não identificado."
            ),
            "gargalo": "Material na obra, sem frente livre, não se converte em instalação.",
            "avaliacao": "A data de entrega está no grupo. Condição de recebimento que o texto não descreve é dado não identificado.",
            "conclusao": "Entrega de material registrada.",
        }
    if codigo == "I":
        return {
            "ponto_critico": "A entrada da equipe precisa ser lida junto com a etapa J, quando houver frente incompleta.",
            "gargalo": "Mobilizar a equipe com parte da obra sem frente reduz a produtividade do dia.",
            "avaliacao": "A data de entrada está no grupo. Nomes de instaladores não citados são dado não identificado.",
            "conclusao": "Equipe de instalação entrou na data registrada, no trecho em que havia condição de trabalhar.",
        }
    if codigo == "J":
        return {
            "ponto_critico": "As interferências abaixo saíram do texto do grupo e tiveram efeito direto na instalação.",
            "gargalo": "Frente incompleta (marcenaria, contrapiso ou ponto hidráulico) segura a produtividade mesmo com equipe presente.",
            "avaliacao": (
                "O impacto não inventa dias além das datas do grupo. "
                "Onde o histórico não quantifica a parada, fica dado não identificado."
            ),
            "conclusao": (
                "Interferências registradas. Item que segue aberto está em J.1 com status Pendente."
                if pendencias
                else "Interferências registradas. Pendência residual em aberto: dado não identificado."
            ),
        }
    if codigo == "L" and not any(fecha_a_obra(item) for item in eventos):
        return {
            "ponto_critico": "Não há registro de conclusão dos serviços e validação final no histórico.",
            "gargalo": "dado não identificado.",
            "avaliacao": "Os registros desta etapa (reparos, pendências, entregas parciais) não fecham a obra.",
            "conclusao": "Conclusão e validação final: dado não identificado (pendente).",
        }
    if codigo == "L":
        return {
            "ponto_critico": (
                "A validação dos serviços ocorreu, e permanece pendência documental citada no grupo."
                if pendencias
                else "dado não identificado."
            ),
            "gargalo": "dado não identificado.",
            "avaliacao": "A conclusão está datada. Documento não anexado no histórico é dado não identificado.",
            "conclusao": (
                "Serviços concluídos e validados no local. O termo assinado pelo cliente segue com status Pendente."
                if pendencias
                else "Conclusão e validação final registradas no grupo."
            ),
        }
    return {
        "ponto_critico": "dado não identificado.",
        "gargalo": "dado não identificado.",
        "avaliacao": "dado não identificado.",
        "conclusao": "dado não identificado.",
    }


def _montar_etapas(eventos: list[dict], desde_map: dict[str, dict], pendencias: list[dict]) -> dict:
    etapas = {}
    for codigo in ORDEM:
        do_codigo = [item for item in eventos if item["etapa"] == codigo]
        if not do_codigo:
            etapas[codigo] = {
                "codigo": codigo,
                "titulo": TITULOS[codigo],
                "situacao": "Dado não identificado",
                "intervalos_relevantes": "dado não identificado.",
                "ponto_critico": "dado não identificado.",
                "gargalo": "dado não identificado.",
                "avaliacao": "dado não identificado.",
                "conclusao": "Não há registro desta etapa no histórico analisado.",
            }
            continue
        internos = _internos(eventos, codigo)
        comentarios = _comentarios_etapa(codigo, do_codigo, internos, pendencias)
        if codigo == "L" and not data_da_conclusao(eventos):
            situacao = "Conclusão não registrada"
        elif codigo == "L" and pendencias:
            situacao = "Pendência identificada"
        elif codigo == "J" and pendencias:
            situacao = "Pendência identificada"
        else:
            situacao = "Atividade realizada"
        etapas[codigo] = {
            "codigo": codigo,
            "titulo": TITULOS[codigo],
            "situacao": situacao,
            "intervalos_relevantes": _texto_intervalos(codigo, internos, desde_map.get(codigo)),
            **comentarios,
        }
    return etapas


def _produtividade(eventos: list[dict]) -> str:
    texto = normalizar(" ".join(item["ocorrencia"] for item in eventos if item["etapa"] in {"I", "J"}))
    if not any(item["etapa"] == "J" for item in eventos):
        return "dado não identificado."
    if "banheir" in texto and "marcenaria" in texto:
        return (
            "A equipe executou o trecho liberado e permaneceu sem frente no ambiente "
            "citado como dependente de marcenaria. A produtividade foi parcial: houve "
            "avanço onde a obra permitiu e espera onde a frente não estava livre. "
            "Esse fato não é convertido em um total de atraso da Armanilux."
        )
    return (
        "As interferências da etapa J reduziram o ritmo nos trechos citados. "
        "A duração que o grupo não mediu permanece dado não identificado, "
        "e os intervalos do calendário não são somados como atraso interno."
    )


def _gargalos(eventos: list[dict], intervalos: list[dict], pendencias: list[dict]) -> list[dict]:
    itens = []
    revisoes = [item for item in eventos if item["etapa"] == "E"]
    if len(revisoes) >= 2:
        itens.append(
            {
                "titulo": "Reprocesso de projeto",
                "texto": (
                    f"O grupo registra {len(revisoes)} solicitações de revisão, em datas diferentes, "
                    "com novo envio depois dos pedidos. O ciclo foi atendido. Não se soma "
                    "esse reprocesso ao intervalo de espera da obra."
                ),
            }
        )
    longos = [item for item in intervalos if item["dias_uteis"] >= 6]
    if longos:
        maior = max(longos, key=lambda item: item["dias_uteis"])
        itens.append(
            {
                "titulo": "Intervalo longo entre marcos",
                "texto": (
                    f"Entre {formatar_data(maior['inicio'])} e {formatar_data(maior['fim'])} "
                    f"transcorreram {_rotulo_dias(maior['dias_uteis'])} sem novo marco classificado nas etapas "
                    f"({maior['rotulo']}). O número já exclui fins de semana, feriados e o Carnaval, "
                    "quando caíram no meio. O histórico não explica cada um desses dias; "
                    "a causa não escrita é dado não identificado. O intervalo não é lançado "
                    "como atraso da Armanilux."
                ),
            }
        )
    if any(item["etapa"] == "J" for item in eventos):
        itens.append(
            {
                "titulo": "Dependência de condição da obra",
                "texto": (
                    "O grupo descreve frente de marcenaria, contrapiso ou ponto hidráulico "
                    "como condição para instalar. Enquanto a condição não existia, a equipe "
                    "não tinha como produzir naquele trecho. A evidência é a mensagem, "
                    "não uma inferência."
                ),
            }
        )
    if pendencias:
        itens.append(
            {
                "titulo": "Pendência ainda aberta",
                "texto": "Há item com status Pendente na seção J.1. Ele não está encerrado por este relatório.",
            }
        )
    for indice, item in enumerate(itens, start=1):
        item["numero"] = indice
    return itens


def _responsabilidades(obra: dict, eventos: list[dict], intervalos: list[dict]) -> list[dict]:
    linhas = []
    revisoes = sum(1 for item in eventos if item["etapa"] == "E")
    if revisoes:
        linhas.append(
            {
                "natureza": "Projeto e revisão interna",
                "diagnostico": (
                    f"Foram identificadas {revisoes} solicitações de revisão, respondidas com novo envio "
                    "quando o envio consta do grupo. O reprocesso está no fluxo de projeto e foi tratado "
                    "dentro do histórico, sem ser somado como atraso de instalação."
                ),
            }
        )
    if any(item["etapa"] == "J" for item in eventos):
        linhas.append(
            {
                "natureza": "Dependência de condições da obra",
                "diagnostico": (
                    "Marcenaria, contrapiso ou ponto hidráulico aparecem no texto como condição "
                    "da instalação. A espera ligada a esses fatos é da frente de obra. "
                    "O relatório não converte essa espera em falha da equipe de instalação."
                ),
            }
        )
    if any(item["dias_uteis"] >= 6 for item in intervalos):
        linhas.append(
            {
                "natureza": "Intervalo longo entre marcos",
                "diagnostico": (
                    "O maior intervalo entre marcos está destacado na seção 4. "
                    "Ele mede dias úteis de calendário. Causa não escrita no grupo é "
                    "dado não identificado, e o valor não é apresentado como atraso da Armanilux."
                ),
            }
        )
    if any(item["etapa"] == "I" for item in eventos):
        linhas.append(
            {
                "natureza": "Instalação em campo",
                "diagnostico": (
                    "A entrada da equipe está datada. A produção ocorreu no trecho liberado. "
                    "Onde a frente não estava livre, a limitação está descrita na etapa J."
                ),
            }
        )
    if not obra.get("prazo_contratual"):
        linhas.append(
            {
                "natureza": "Informação ausente no histórico",
                "diagnostico": (
                    "O prazo contratual é dado não identificado. Sem essa data no grupo, "
                    "o relatório não declara atraso contratual nem cumprimento de prazo."
                ),
            }
        )
    if not linhas:
        linhas.append(
            {
                "natureza": "Informação ausente no histórico",
                "diagnostico": "Não há base, no histórico analisado, para diagnóstico de responsabilidade. dado não identificado.",
            }
        )
    return linhas


def _recomendacoes(eventos: list[dict], intervalos: list[dict], pendencias: list[dict]) -> list[str]:
    revisoes = sum(1 for item in eventos if item["etapa"] == "E")
    maior = max((item["dias_uteis"] for item in intervalos), default=0)
    texto_revisao = (
        f"Nesta obra houve {revisoes} solicitações de revisão. "
        "Nas próximas, reunir arquitetura e cliente num único retorno antes de reabrir o desenho."
        if revisoes
        else "Manter o hábito de concentrar pedidos de revisão num único retorno, antes de reabrir o desenho."
    )
    itens = [
        "Registrar no grupo, no dia da medição, o que foi medido e o que ficou de fora, para o preliminar não nascer incompleto.",
        texto_revisao,
        "Antes de fabricar e antes de mobilizar a equipe, pedir no grupo a confirmação explícita de frente liberada: contrapiso, marcenaria e pontos de água e esgoto.",
        (
            f"Tratar intervalo longo como ponto de controle, sem somar os intervalos como atraso da Armanilux. "
            f"O maior intervalo sem registro nesta obra foi de {_rotulo_dias(maior)}."
        ),
        "Guardar o zip e as mídias na pasta da obra e citar o nome do arquivo no relatório, para qualquer leitor conferir a origem.",
        "Enviar o Word apenas às pessoas do grupo interno ou do grupo da obra. Não publicar o relatório em link aberto.",
    ]
    if pendencias:
        itens.append(
            "Encerrar a pendência de status Pendente (termo ou item equivalente) antes de tratar a obra como arquivada."
        )
    return itens


def _conclusao(obra: dict, eventos: list[dict], intervalos: list[dict], pendencias: list[dict], dias_periodo: int) -> str:
    numero = obra.get("numero") or DADO
    cliente = obra.get("cliente") or DADO
    inicio = formatar_data(obra.get("periodo_inicio"))
    fim = formatar_data(obra.get("periodo_fim"))
    if intervalos:
        maior = max(intervalos, key=lambda item: item["dias_uteis"])
        trecho_intervalo = (
            f"O maior intervalo sem registro foi de {_rotulo_dias(maior['dias_uteis'])}, "
            f"entre {formatar_data(maior['inicio'])} e {formatar_data(maior['fim'])} "
            f"({maior['rotulo']}, leitura {maior['leitura']}). "
            "Esse número não é um atraso atribuído à Armanilux."
        )
    else:
        trecho_intervalo = "Não houve intervalo entre registros para destacar. dado não identificado para ociosidade."
    if any(item["etapa"] == "J" for item in eventos):
        trecho_j = (
            "As interferências de obra descritas na etapa J condicionaram a produtividade "
            "e estão apoiadas em mensagem do grupo."
        )
    else:
        trecho_j = "Interferência de obra com impacto na instalação: dado não identificado."
    if pendencias:
        trecho_p = "Permanece pendência com status Pendente, listada em J.1, fora do que já foi validado no local."
    else:
        trecho_p = "Não restou pendência identificada no histórico."
    return (
        f"O fluxo da obra {numero}, cliente {cliente}, percorreu os registros do grupo "
        f"entre {inicio} e {fim}, em {_rotulo_dias(dias_periodo)} de calendário. "
        "Aprovação de chapas, medição, projetos e instalação entram no relatório só quando "
        "há data no histórico. "
        f"{trecho_intervalo} {trecho_j} "
        "Revisões pedidas foram tratadas como reprocesso de projeto, com resposta por novo envio "
        "quando o envio existe no grupo, e não foram somadas aos intervalos de espera. "
        f"{trecho_p} "
        "Recomendação final: na próxima obra, obter a liberação de frente por escrito "
        "antes da mobilização e concentrar a revisão de projeto num único ciclo."
    )


def _anexo(
    eventos: list[dict],
    arquivos: list[Path],
    quadros: list[Path],
    documentos: list[dict],
) -> list[dict]:
    por_nome: dict[str, dict] = {}
    for evento in eventos:
        for nome in evento.get("midias", []) + evento.get("documentos", []):
            por_nome.setdefault(
                nome,
                {"arquivo": nome, "data": evento["data"], "etapa": evento["etapa"]},
            )
    linhas = []
    vistos = set()

    def acrescentar(nome: str, caminho: Path | None, data: str, etapa: str, tipo: str = "") -> None:
        if nome in vistos:
            return
        vistos.add(nome)
        linhas.append(
            {
                "arquivo": nome,
                "tipo": tipo or tipo_midia(nome),
                "data": data,
                "etapa": etapa,
                "caminho": str(caminho) if caminho else "",
                "existe": bool(caminho and caminho.exists()),
            }
        )

    for caminho in arquivos:
        meta = por_nome.get(caminho.name, {})
        if caminho.suffix.lower() in {*EXT_IMAGEM, *EXT_VIDEO} or caminho.suffix.lower() in {".opus", ".ogg", ".mp3", ".m4a", ".wav", ".aac"} or meta:
            acrescentar(caminho.name, caminho, meta.get("data", ""), meta.get("etapa", ""))
    for nome, meta in por_nome.items():
        if Path(nome).suffix.lower() in EXT_DOCUMENTO:
            caminho = next((item for item in arquivos if item.name == nome), None)
            acrescentar(nome, caminho, meta.get("data", ""), meta.get("etapa", ""))
    for documento in documentos:
        nome = documento["arquivo"]
        meta = por_nome.get(nome, {})
        bruto = documento.get("caminho") or ""
        acrescentar(nome, Path(bruto) if bruto else None, meta.get("data", ""), meta.get("etapa", ""))
    for quadro in quadros:
        video = quadro.parent.name
        meta_video = next(
            (
                por_nome[nome]
                for nome in por_nome
                if Path(nome).stem == video and Path(nome).suffix.lower() in EXT_VIDEO
            ),
            {},
        )
        nome_quadro = f"{quadro.parent.name}/{quadro.name}"
        acrescentar(
            nome_quadro,
            quadro,
            meta_video.get("data", ""),
            meta_video.get("etapa", ""),
            "quadro de vídeo",
        )
    return linhas


def _plural(quantidade: int, singular: str, plural: str) -> str:
    return singular if quantidade == 1 else plural


def juntar_lacunas(base: dict) -> list[str]:
    """Lacunas automáticas mais as que a revisão escreveu, sem repetir."""
    automaticas = list(base.get("lacunas_automaticas") or [])
    return automaticas + [item for item in (base.get("lacunas_adicionais") or []) if item and item not in automaticas]


def arquivos_fora_da_exportacao(mensagens: list[Mensagem]) -> list[str]:
    """Nomes dos arquivos enviados no grupo que o WhatsApp não pôs no zip (para o agente, não para o Word)."""
    return [mensagem.anexos[0] for mensagem in mensagens if _so_o_nome(mensagem)]


# Toda exportação completa começa pelo aviso de criptografia ou pela criação do grupo.
_INICIO_DO_GRUPO = (
    "criptografia de ponta a ponta",
    "end-to-end encrypted",
    "criou o grupo",
    "criou este grupo",
    "created group",
    "created this group",
)


def exportacao_parece_cortada(mensagens: list[Mensagem]) -> bool:
    """O WhatsApp corta conversa muito grande (cerca de 10 mil mensagens com mídia, 40 mil sem)
    e não avisa: o que sobra começa no meio, sem o aviso de criptografia nem a criação do grupo."""
    if not mensagens:
        return False
    # O autor entra também: um ":" no nome do grupo ("Obra: 1001") manda o começo da linha para o autor.
    comeco = " ".join(normalizar(f"{mensagem.autor or ''} {mensagem.texto}") for mensagem in mensagens[:3])
    return not any(marca in comeco for marca in _INICIO_DO_GRUPO)


def lacunas_automaticas(mensagens: list[Mensagem], documentos: list[dict], transcricoes: list[dict]) -> list[str]:
    """O que o computador sabe que não conseguiu ler, em frases curtas para a Nota Metodológica."""
    cortada = []
    if exportacao_parece_cortada(mensagens):
        cortada.append(
            f"A exportação do WhatsApp parece cortada: a conversa começa em {formatar_data(mensagens[0].data.isoformat())}, "
            "sem o início do grupo. O que veio antes é dado não identificado."
        )
    lacunas = []
    fora = len(arquivos_fora_da_exportacao(mensagens))
    if fora:
        lacunas.append(
            f"{fora} {_plural(fora, 'arquivo enviado', 'arquivos enviados')} no grupo "
            f"{_plural(fora, 'não veio', 'não vieram')} na exportação do WhatsApp."
        )
    sem_nome = sum(1 for mensagem in mensagens if mensagem.midia_omitida and not mensagem.anexos)
    if sem_nome:
        lacunas.append(
            f"{sem_nome} {_plural(sem_nome, 'foto, áudio ou vídeo', 'fotos, áudios ou vídeos')} "
            f"{_plural(sem_nome, 'não veio', 'não vieram')} na exportação."
        )
    ilegiveis = sum(1 for item in documentos if not (item.get("texto") or "").strip())
    if ilegiveis:
        lacunas.append(f"{ilegiveis} {_plural(ilegiveis, 'documento', 'documentos')} sem texto legível pelo computador.")
    sem_fala = sum(1 for item in transcricoes if item.get("status") != "ok")
    if sem_fala:
        lacunas.append(f"{sem_fala} {_plural(sem_fala, 'áudio ou vídeo', 'áudios ou vídeos')} sem transcrição.")
    if lacunas:
        lacunas[-1] = lacunas[-1][:-1] + "; o conteúdo desses itens é dado não identificado."
    return cortada + lacunas


def _nota_rastreabilidade(mensagens: list[Mensagem], eventos: list[dict], anexo: list[dict], documentos: list[dict], transcricoes: list[dict]) -> str:
    midias = sum(1 for item in anexo if item["tipo"] in {"foto", "áudio", "vídeo", "quadro de vídeo"})
    # quadros are tipo from suffix jpg -> foto. Count files instead.
    total_anexo = len(anexo)
    if any(item.get("status") == "ok" and item.get("texto") for item in transcricoes):
        fala = f"Transcrições locais concluídas: {sum(1 for item in transcricoes if item.get('status') == 'ok')}."
    elif transcricoes:
        fala = "A transcrição automática não foi executada nesta versão; o conteúdo falado dos áudios e vídeos é dado não identificado."
    else:
        fala = "Não havia áudio ou vídeo de fala para transcrever."
    return (
        "Nota de rastreabilidade: este relatório foi elaborado no computador, a partir do arquivo "
        "de exportação indicado no campo Fonte, dos documentos lidos na pasta 02-projetos-pdf e das "
        "transcrições locais da pasta 04-transcricoes. Não houve envio do histórico para serviço de "
        "transcrição em nuvem. Trechos marcados como dado não identificado não constavam do histórico "
        "analisado. As mídias citadas permanecem na pasta da obra. "
        f"Contagem desta versão: {len(mensagens)} mensagens lidas, {len(eventos)} lançamentos nas etapas, "
        f"{total_anexo} itens no anexo e {len(documentos)} documentos com tentativa de leitura. {fala} "
        f"Arquivos de mídia considerados: {midias}."
    )


def _juntar_adicionais(base: dict) -> list[dict]:
    """Eventos lidos do grupo mais os que o agente acrescentou à mão, sem repetir.
    Os acrescentados levam "origem": "revisao" e são refeitos a cada remontagem a partir de
    eventos_adicionais: editar ou tirar um item da lista muda o relatório sem deixar a cópia antiga."""
    def _chave(item: dict) -> tuple:
        return (item.get("data"), item.get("hora") or "00:00", item.get("etapa"), item.get("ocorrencia", ""))

    # analise.json de antes desta marca: o fato igual a um acrescentado também é da revisão.
    da_revisao = {_chave(extra) for extra in base.get("eventos_adicionais") or []}
    eventos = [e for e in base.get("eventos") or [] if e.get("origem") != "revisao" and _chave(e) not in da_revisao]
    vistos = {(e["data"], e.get("hora", ""), e["etapa"], e.get("ocorrencia", "")) for e in eventos}
    for extra in base.get("eventos_adicionais") or []:
        if extra.get("etapa") not in ORDEM or not extra.get("data"):
            continue
        item = {
            "data": extra["data"],
            "hora": extra.get("hora") or "00:00",
            "etapa": extra["etapa"],
            "autor": extra.get("autor", ""),
            "ocorrencia": extra.get("ocorrencia", ""),
            "impacto": extra.get("impacto", ""),
            "midias": list(extra.get("midias") or []),
            "documentos": list(extra.get("documentos") or []),
            "origem": "revisao",
        }
        if extra.get("destaque"):
            item["destaque"] = extra["destaque"]
        if extra.get("conclusao") and item["etapa"] == "L":
            item["conclusao"] = True
        if extra.get("programado"):
            item["programado"] = True
        if extra.get("data_evento"):
            item["data_evento"] = extra["data_evento"]
        chave = (item["data"], item["hora"], item["etapa"], item["ocorrencia"])
        if chave not in vistos:
            vistos.add(chave)
            eventos.append(item)
    return eventos


def completar_relato(base: dict) -> dict:
    """Recalcula intervalos, textos e indicadores a partir dos eventos já classificados."""
    eventos = _juntar_adicionais(base)
    eventos.sort(key=lambda item: (item["data"], item["hora"], _posicao(item["etapa"])))
    for evento in eventos:
        evento["destaque_auto"] = destaque_automatico(evento["etapa"], evento.get("ocorrencia") or "")
    obra = dict(base["obra"])
    obra.update({k: v for k, v in (base.get("obra_ajustes") or {}).items() if v})
    pendencias = list(base.get("pendencias_revisadas") or base.get("pendencias") or [])
    intervalos = _intervalos(eventos)
    desde = _desde_etapa_anterior(eventos)
    datas = sorted({item["data"] for item in eventos})
    if obra.get("periodo_inicio") and obra.get("periodo_fim"):
        # O período do relatório é o do grupo, o mesmo que aparece no cabeçalho.
        dias_periodo = dias_uteis_entre(date.fromisoformat(obra["periodo_inicio"]), date.fromisoformat(obra["periodo_fim"]))
    elif len(datas) >= 2:
        dias_periodo = dias_uteis_entre(date.fromisoformat(datas[0]), date.fromisoformat(datas[-1]))
    else:
        dias_periodo = 0
    maior = max((item["dias_uteis"] for item in intervalos), default=0)
    relato = dict(base)
    relato["obra"] = obra
    relato["pendencias"] = pendencias
    relato["eventos"] = eventos
    relato["convencao_dias_uteis"] = CONVENCAO_DIAS_UTEIS
    relato["intervalos"] = intervalos
    relato["intervalos_marcos"], relato["duracao_marcos"] = intervalos_marcos_de(eventos)
    relato["confronto_contrato"] = confronto_contrato(eventos, base.get("prazos_contratuais") or [])
    if "lacunas_automaticas" in base:
        relato["lacunas"] = juntar_lacunas(base)
    relato["kpis"] = {
        "dias_uteis_periodo": dias_periodo,
        "revisoes": sum(1 for item in eventos if item["etapa"] == "E"),
        "interferencias": sum(1 for item in eventos if item["etapa"] == "J"),
        "maior_intervalo": maior,
    }
    relato["etapas"] = _montar_etapas(eventos, desde, pendencias)
    relato["produtividade"] = _produtividade(eventos)
    relato["gargalos"] = _gargalos(eventos, intervalos, pendencias)
    relato["responsabilidades"] = _responsabilidades(obra, eventos, intervalos)
    relato["recomendacoes"] = _recomendacoes(eventos, intervalos, pendencias)
    relato["conclusao"] = _conclusao(obra, eventos, intervalos, pendencias, dias_periodo)
    relato["marcos"] = marcos_de(eventos, pendencias)
    # Textos escritos por quem revisou o grupo substituem os textos automáticos.
    if base.get("produtividade_personalizada"):
        relato["produtividade"] = base["produtividade_personalizada"]
    if base.get("gargalos_personalizados"):
        relato["gargalos"] = [
            {"numero": indice, "titulo": item["titulo"], "texto": item["texto"]}
            for indice, item in enumerate(base["gargalos_personalizados"], start=1)
        ]
    if base.get("responsabilidades_personalizadas"):
        relato["responsabilidades"] = list(base["responsabilidades_personalizadas"])
    return relato


def montar_analise(
    mensagens: list[Mensagem],
    *,
    fonte: str,
    arquivos: list[Path],
    documentos: list[dict],
    transcricoes: list[dict],
    quadros: list[Path],
    overrides: dict | None = None,
) -> dict:
    obra = metadados_da_conversa(mensagens, fonte, overrides)
    eventos = extrair_eventos(mensagens, arquivos, transcricoes)
    pendencias = _pendencias(mensagens)
    anexo = _anexo(eventos, arquivos, quadros, documentos)
    base = {
        "obra": obra,
        "eventos": eventos,
        "pendencias": pendencias,
        "anexo": anexo,
        "documentos_texto": [
            {"arquivo": item["arquivo"], "texto": item.get("texto", ""), "erro": item.get("erro", "")}
            for item in documentos
        ],
        "transcricoes": transcricoes,
        "observacoes_visuais": [],
        "comentarios": {},
        "recomendacoes_personalizadas": [],
        "conclusao_personalizada": "",
        "ajustes_eventos": [],
        "eventos_adicionais": [],
        "rastreabilidade": _nota_rastreabilidade(mensagens, eventos, anexo, documentos, transcricoes),
        "lacunas_automaticas": lacunas_automaticas(mensagens, documentos, transcricoes),
        "arquivos_fora_da_exportacao": arquivos_fora_da_exportacao(mensagens),
        "lacunas_adicionais": [],
    }
    return completar_relato(base)


def fecha_a_obra(evento: dict) -> bool:
    """Só o fato da etapa L que a revisão marcou com "conclusao": true fecha a obra.
    Outro fato da etapa L (reclamação, reparo, entrega parcial) não fecha."""
    return evento["etapa"] == "L" and bool(evento.get("conclusao"))


def data_da_conclusao(eventos: list[dict]) -> str:
    """Data do último fato que fecha a obra, ou "" (conclusão: dado não identificado)."""
    datas = sorted(item["data"] for item in eventos if fecha_a_obra(item))
    return datas[-1] if datas else ""


def _situacao_marco(eventos: list[dict], codigo: str) -> str:
    if codigo == "L":
        return "Concluído" if data_da_conclusao(eventos) else "dado não identificado (pendente)"
    if any(item["etapa"] == codigo and conta_como_marco(item) for item in eventos):
        return "Concluído"
    if any(item["etapa"] == codigo for item in eventos):
        return "Programado, sem confirmação"
    return "dado não identificado"


def marcos_de(eventos: list[dict], pendencias: list[dict]) -> list[dict]:
    return [
        {"marco": "Aprovação de chapas", "situacao": _situacao_marco(eventos, "A")},
        {"marco": "Medição in loco", "situacao": _situacao_marco(eventos, "C")},
        {"marco": "Aprovação do projeto", "situacao": _situacao_marco(eventos, "G")},
        {"marco": "Entrega do material na obra", "situacao": _situacao_marco(eventos, "H")},
        {"marco": "Entrada da equipe de instalação", "situacao": _situacao_marco(eventos, "I")},
        {"marco": "Conclusão dos serviços e validação final", "situacao": _situacao_marco(eventos, "L")},
        {
            "marco": "Termo de entrega assinado pelo cliente",
            "situacao": "Pendente" if pendencias else "dado não identificado",
        },
    ]


def aplicar_ajustes(eventos: list[dict], ajustes: list[dict]) -> list[dict]:
    """Corrige etapa, texto ou impacto de eventos já lidos, ou remove ("remover": true)."""
    for ajuste in ajustes or []:
        for evento in list(eventos):
            if ajuste.get("data") and evento["data"] != ajuste["data"]:
                continue
            if ajuste.get("hora") and evento["hora"] != ajuste["hora"]:
                continue
            if ajuste.get("autor") and evento["autor"] != ajuste["autor"]:
                continue
            if ajuste.get("etapa_original") and evento["etapa"] != ajuste["etapa_original"]:
                continue
            if ajuste.get("remover"):
                eventos.remove(evento)
                continue
            if ajuste.get("etapa"):
                evento["etapa"] = ajuste["etapa"]
            if ajuste.get("ocorrencia"):
                evento["ocorrencia"] = ajuste["ocorrencia"]
            if ajuste.get("impacto"):
                evento["impacto"] = ajuste["impacto"]
            if ajuste.get("destaque"):
                evento["destaque"] = ajuste["destaque"]
            for marca in ("conclusao", "programado"):
                if marca in ajuste:  # aceita false, para desmarcar
                    evento[marca] = bool(ajuste[marca])
            if ajuste.get("data_evento"):
                evento["data_evento"] = ajuste["data_evento"]
    return eventos
