"""Lê export de conversa do WhatsApp no formato Android e no formato iPhone.

Cobre data em pt-BR (dia/mês/ano, com ou sem vírgula, com ou sem segundos),
ano com dois dígitos, horário de 12 horas quando aparece, mensagem de várias
linhas, aviso de criptografia e marcadores de anexo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from common import corrigir_mojibake, decodificar_bytes, normalizar

_ESPACO = re.compile(r"\s+")
_DATA_HORA_ANDROID = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+"
    r"(\d{1,2}:\d{2}(?::\d{2})?)"
    r"(?:\s*([AaPp][Mm]))?\s*[-–—]\s*(.*)$"
)
_DATA_HORA_IPHONE = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+"
    r"(\d{1,2}:\d{2}(?::\d{2})?)"
    r"(?:\s*([AaPp][Mm]))?\]\s*(.*)$"
)
_ANEXO_EXPLICITO = re.compile(
    r"<(?:anexad[oa]|anexo|attached):\s*([^>]+)>",
    re.IGNORECASE,
)
_ANEXO_SUFIXO = re.compile(
    r"([^\s<>\"]+\.(?:pdf|docx?|xlsx?|jpe?g|png|webp|heic|gif|opus|ogg|mp3|m4a|wav|aac|mp4|mov|3gp|avi|mkv))"
    r"\s+\((?:arquivo anexado|file attached)\)",
    re.IGNORECASE,
)
_MIDIA_OCULTA = re.compile(
    r"(m[ií]dia oculta|media omitted|áudio ocultado|audio omitted|"
    r"vídeo omitido|video omitted|imagem ocultada|image omitted|"
    r"documento omitido|document omitted|sticker omitido|figurinha omitida|"
    r"<mídia oculta>)",
    re.IGNORECASE,
)
# Documento exportado "sem mídia": o nome do arquivo vem na linha logo abaixo
# de "<Mídia oculta>". Legenda de foto não termina em extensão e fica de fora.
# Qualquer extensão que comece por letra (pdf, dwg, xlsm, skp…); "R$ 1.500" não casa.
MARCADOR_MIDIA_OCULTA = re.compile(r"<m[ií]dia oculta>", re.IGNORECASE)
_NOME_APOS_MIDIA_OCULTA = re.compile(
    r"^<m[ií]dia oculta>\s*\n\s*([^<>\n/\\]+\.[A-Za-z][A-Za-z0-9]{1,4})\s*(?:\n|$)",
    re.IGNORECASE,
)
# Linha de mensagem colada de outra conversa: "[21/08, 08:54] Nome: texto" (sem ano).
_LINHA_ENCAMINHADA = re.compile(
    r"^\[(\d{1,2})/(\d{1,2}),?\s+(\d{1,2}):(\d{2})\]\s*([^:\]\n]{1,80}?):(?:\s(.*))?$"
)
# O outro formato de colagem: "[12:25, 03/07/2026] Nome: texto" (hora antes, data com ano).
_LINHA_ENCAMINHADA_HORA_ANTES = re.compile(
    r"^\[(\d{1,2}):(\d{2}),?\s+(\d{1,2})/(\d{1,2})/(\d{2,4})\]\s*([^:\]\n]{1,80}?):(?:\s(.*))?$"
)


# Aviso do WhatsApp com ":" no meio ("Ana alterou o nome do grupo de "Obra 1001: Silva"...").
# Frases inteiras, não verbos soltos: apelido entre aspas ou "Saiu Silva" continuam autor.
_CARA_DE_SISTEMA = re.compile(
    r"\b(?:alterou|mudou) (?:o nome|a descrição|a imagem|o assunto|as configurações)"
    r"|\bchanged (?:the subject|the group|this group|the description)"
    r"|\bfixou uma mensagem|\bpinned a message",
    re.IGNORECASE,
)


@dataclass
class Mensagem:
    quando: datetime
    autor: str | None
    texto: str
    anexos: list[str] = field(default_factory=list)
    midia_omitida: bool = False
    sistema: bool = False
    # Mensagem colada/reencaminhada: quem colou no grupo e quando.
    encaminhada_por: str | None = None
    encaminhada_em: datetime | None = None
    # A ordem dia/mês do arquivo não foi provada por um número acima de 12 (ou a data só coube
    # na outra ordem): o dia e o mês podem estar trocados.
    data_incerta: bool = False

    @property
    def data(self):
        return self.quando.date()

    @property
    def hora(self) -> str:
        return self.quando.strftime("%H:%M")


def _limpar_linha(linha: str) -> str:
    linha = linha.replace("\ufeff", "").replace("\u200e", "").replace("\u200f", "")
    caracteres = []
    for caractere in linha:
        if unicodedata_espaco(caractere):
            caracteres.append(" ")
        else:
            caracteres.append(caractere)
    return "".join(caracteres).strip()


def unicodedata_espaco(caractere: str) -> bool:
    import unicodedata

    return unicodedata.category(caractere) == "Zs"


DIA_MES = "dm"  # export brasileiro
MES_DIA = "md"  # WhatsApp em inglês (EUA)


def _ordem_das_datas(linhas: list[str]) -> tuple[str, bool]:
    """(ordem, confirmada) para o arquivo todo: decidir linha a linha mistura as duas ordens.
    Prova a ordem um número acima de 12, ou o zero na frente (dia/mês). AM/PM não prova (celular brasileiro com relógio de
    12 horas também mostra). Sem prova, ou com prova das duas ordens, vale dia/mês sem confirmação."""
    dia_primeiro = mes_primeiro = False
    for linha in linhas:
        casou = _DATA_HORA_ANDROID.match(linha) or _DATA_HORA_IPHONE.match(linha)
        if not casou:
            continue
        texto_a, texto_b = casou.group(1).split("/")[:2]
        # O zero na frente ("03/07") é do formato dia/mês (Brasil, Reino Unido); o WhatsApp dos EUA
        # escreve "7/3/26", sem zero.
        dia_primeiro = dia_primeiro or int(texto_a) > 12 or texto_a.startswith("0") or texto_b.startswith("0")
        mes_primeiro = mes_primeiro or int(texto_b) > 12
    if dia_primeiro != mes_primeiro:
        return (DIA_MES if dia_primeiro else MES_DIA), True
    return DIA_MES, False


def _interpretar_data(data_texto: str, hora_texto: str, periodo: str | None, ordem: str = DIA_MES) -> datetime:
    parte_a, parte_b, ano = (int(pedaço) for pedaço in data_texto.split("/"))
    if ano < 100:
        ano += 2000
    dia, mes = (parte_b, parte_a) if ordem == MES_DIA else (parte_a, parte_b)
    pedacos_hora = hora_texto.split(":")
    hora = int(pedacos_hora[0])
    minuto = int(pedacos_hora[1])
    segundo = int(pedacos_hora[2]) if len(pedacos_hora) > 2 else 0
    if periodo:
        marcador = periodo.lower()
        if marcador == "pm" and hora < 12:
            hora += 12
        if marcador == "am" and hora == 12:
            hora = 0
    return datetime(ano, mes, dia, hora, minuto, segundo)


def _data_da_linha(casou: re.Match, ordem: str, confirmada: bool) -> tuple[datetime | None, bool]:
    """(quando, incerta). Data impossível na ordem do arquivo (1/18/26 num arquivo dia/mês) é lida
    na outra ordem e fica incerta: o arquivo mistura as duas ordens."""
    try:
        return _interpretar_data(casou.group(1), casou.group(2), casou.group(3), ordem), not confirmada
    except ValueError:
        pass
    outra = MES_DIA if ordem == DIA_MES else DIA_MES
    try:
        return _interpretar_data(casou.group(1), casou.group(2), casou.group(3), outra), True
    except ValueError:
        return None, True


def _separar_autor(resto: str) -> tuple[str | None, str]:
    if ": " not in resto:
        return None, resto.strip()
    autor, texto = resto.split(": ", 1)
    autor = corrigir_mojibake(autor.strip())
    if not autor or len(autor) > 80 or _CARA_DE_SISTEMA.search(autor):
        return None, resto.strip()
    return autor, texto.strip()


def _anexos_do_texto(texto: str) -> list[str]:
    encontrados: list[str] = []
    for padrao in (_ANEXO_EXPLICITO, _ANEXO_SUFIXO):
        for achado in padrao.findall(texto):
            nome = corrigir_mojibake(achado.strip().strip("."))
            if nome and nome not in encontrados:
                encontrados.append(nome)
    oculta = _NOME_APOS_MIDIA_OCULTA.match(texto)
    if oculta:
        nome = corrigir_mojibake(oculta.group(1).strip())
        if nome not in encontrados:
            encontrados.append(nome)
    return encontrados


def _data_encaminhada(achado: re.Match, postada: datetime) -> datetime | None:
    """Sem ano no colchete: é a data mais recente, até a de envio (29/02 volta ao último ano bissexto)."""
    dia, mes, hora, minuto = (int(achado.group(i)) for i in range(1, 5))
    for ano in range(postada.year, postada.year - 5, -1):
        try:
            original = datetime(ano, mes, dia, hora, minuto)
        except ValueError:
            continue
        if original <= postada:
            return original
    return None


def _linha_colada(linha: str, postada: datetime) -> tuple[datetime, str, str] | None:
    """(quando, autor, texto) da linha colada, nos dois formatos do WhatsApp.
    Data depois do envio não é colagem: a linha fica no texto de quem postou."""
    achado = _LINHA_ENCAMINHADA.match(linha)
    if achado:
        quando = _data_encaminhada(achado, postada)
        return (quando, achado.group(5).strip(), achado.group(6) or "") if quando else None
    achado = _LINHA_ENCAMINHADA_HORA_ANTES.match(linha)
    if not achado:
        return None
    hora, minuto, dia, mes, ano = (int(achado.group(i)) for i in range(1, 6))
    try:
        quando = datetime(ano + 2000 if ano < 100 else ano, mes, dia, hora, minuto)
    except ValueError:
        return None
    if quando > postada:
        return None
    return quando, achado.group(6).strip(), achado.group(7) or ""


def _desmembrar(mensagem: Mensagem) -> list[Mensagem]:
    """Separa as mensagens coladas, cada uma com a data e o autor originais."""
    if mensagem.sistema or not mensagem.autor:
        return [mensagem]
    propria: list[str] = []
    coladas: list[Mensagem] = []
    for linha in mensagem.texto.split("\n"):
        colada = _linha_colada(linha, mensagem.quando)
        if colada is not None:
            quando, autor, texto = colada
            coladas.append(
                Mensagem(
                    quando=quando,
                    autor=autor,
                    texto=texto,
                    encaminhada_por=mensagem.autor,
                    encaminhada_em=mensagem.quando,
                )
            )
        elif coladas:
            coladas[-1].texto += "\n" + linha
        else:
            propria.append(linha)
    if not coladas:
        return [mensagem]
    for colada in coladas:
        colada.texto = colada.texto.strip()
    mensagem.texto = "\n".join(propria).strip()
    return ([mensagem] if mensagem.texto else []) + coladas


def analisar_conversa(texto: str) -> list[Mensagem]:
    mensagens: list[Mensagem] = []
    atual: Mensagem | None = None

    def fechar() -> None:
        nonlocal atual
        if atual is None:
            return
        atual.texto = corrigir_mojibake(atual.texto).strip()
        for parte in _desmembrar(atual):
            parte.anexos = _anexos_do_texto(parte.texto)
            parte.midia_omitida = bool(_MIDIA_OCULTA.search(parte.texto))
            mensagens.append(parte)
        atual = None

    linhas = [_limpar_linha(bruta) for bruta in texto.splitlines()]
    ordem, confirmada = _ordem_das_datas(linhas)
    for linha in linhas:
        if not linha:
            if atual is not None:
                atual.texto += "\n"
            continue
        casou = _DATA_HORA_ANDROID.match(linha) or _DATA_HORA_IPHONE.match(linha)
        if not casou:
            if atual is not None:
                atual.texto += ("\n" if atual.texto else "") + linha
            continue
        quando, incerta = _data_da_linha(casou, ordem, confirmada)
        if quando is None:
            if atual is not None:
                atual.texto += ("\n" if atual.texto else "") + linha
            continue
        fechar()
        autor, corpo = _separar_autor(casou.group(4))
        atual = Mensagem(
            quando=quando,
            autor=autor,
            texto=corpo,
            sistema=autor is None,
            data_incerta=incerta,
        )
    fechar()
    return mensagens


def ler_conversa(caminho: Path) -> list[Mensagem]:
    return analisar_conversa(decodificar_bytes(Path(caminho).read_bytes()))


def texto_util(mensagem: Mensagem) -> str:
    return _ESPACO.sub(" ", mensagem.texto).strip()


def parece_conversa(texto: str) -> bool:
    mensagens = analisar_conversa(texto)
    return any(not item.sistema and item.autor for item in mensagens)
